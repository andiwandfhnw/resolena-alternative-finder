"""Windows x64 private Job Object backend; imports are safe on other platforms."""
import ctypes as c
import ntpath
import os
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone

DWORD = c.c_uint32
WORD = c.c_uint16
BOOL = c.c_int32
HANDLE = c.c_void_p
SIZE_T = c.c_size_t
U64 = c.c_uint64
JOB_OBJECT_LIMIT_JOB_MEMORY = 0x200
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
BREAKAWAY_FLAGS = 0x800 | 0x1000
MEMORY_LIMIT = 25769803776


class JobError(RuntimeError):
    pass


class BasicLimit(c.Structure):
    _fields_ = [('PerProcessUserTimeLimit',c.c_int64),('PerJobUserTimeLimit',c.c_int64),
                ('LimitFlags',DWORD),('MinimumWorkingSetSize',SIZE_T),('MaximumWorkingSetSize',SIZE_T),
                ('ActiveProcessLimit',DWORD),('Affinity',SIZE_T),('PriorityClass',DWORD),('SchedulingClass',DWORD)]


class IoCounters(c.Structure):
    _fields_ = [(name,U64) for name in ('ReadOperationCount','WriteOperationCount','OtherOperationCount',
                                      'ReadTransferCount','WriteTransferCount','OtherTransferCount')]


class ExtendedLimit(c.Structure):
    _fields_ = [('BasicLimitInformation',BasicLimit),('IoInfo',IoCounters),
                ('ProcessMemoryLimit',SIZE_T),('JobMemoryLimit',SIZE_T),
                ('PeakProcessMemoryUsed',SIZE_T),('PeakJobMemoryUsed',SIZE_T)]


class BasicAccounting(c.Structure):
    _fields_ = [(name,c.c_int64) for name in ('TotalUserTime','TotalKernelTime','ThisPeriodTotalUserTime','ThisPeriodTotalKernelTime')] + [
        (name,DWORD) for name in ('TotalPageFaultCount','TotalProcesses','ActiveProcesses','TotalTerminatedProcesses')]


class MemoryUsage(c.Structure):
    _fields_ = [('JobMemory',U64),('PeakJobMemoryUsed',U64)]


class StartupInfo(c.Structure):
    _fields_ = [('cb',DWORD),('lpReserved',c.c_wchar_p),('lpDesktop',c.c_wchar_p),('lpTitle',c.c_wchar_p)] + [
        (name,DWORD) for name in ('dwX','dwY','dwXSize','dwYSize','dwXCountChars','dwYCountChars','dwFillAttribute','dwFlags')] + [
        ('wShowWindow',WORD),('cbReserved2',WORD),('lpReserved2',c.c_void_p),
        ('hStdInput',HANDLE),('hStdOutput',HANDLE),('hStdError',HANDLE)]


class StartupInfoEx(c.Structure):
    _fields_ = [('StartupInfo',StartupInfo),('lpAttributeList',c.c_void_p)]


class ProcessInformation(c.Structure):
    _fields_ = [('hProcess',HANDLE),('hThread',HANDLE),('dwProcessId',DWORD),('dwThreadId',DWORD)]


class MemoryStatus(c.Structure):
    _fields_ = [('dwLength',DWORD),('dwMemoryLoad',DWORD)] + [(name,U64) for name in (
        'ullTotalPhys','ullAvailPhys','ullTotalPageFile','ullAvailPageFile','ullTotalVirtual','ullAvailVirtual','ullAvailExtendedVirtual')]


class FileTime(c.Structure):
    _fields_ = [('low',DWORD),('high',DWORD)]


class ProcessBasicInformation(c.Structure):
    _fields_ = [('ExitStatus',c.c_int32),('PebBaseAddress',c.c_void_p),
                ('AffinityMask',SIZE_T),('BasePriority',c.c_int32),
                ('UniqueProcessId',SIZE_T),('InheritedFromUniqueProcessId',SIZE_T)]


class ProcessEntry(c.Structure):
    _fields_ = [('dwSize',DWORD),('cntUsage',DWORD),('th32ProcessID',DWORD),
                ('th32DefaultHeapID',SIZE_T),('th32ModuleID',DWORD),('cntThreads',DWORD),
                ('th32ParentProcessID',DWORD),('pcPriClassBase',c.c_int32),
                ('dwFlags',DWORD),('szExeFile',WORD*260)]


class SecurityAttributes(c.Structure):
    _fields_ = [('nLength',DWORD),('lpSecurityDescriptor',c.c_void_p),('bInheritHandle',BOOL)]


class CompletionPort(c.Structure):
    _fields_ = [('CompletionKey',c.c_void_p),('CompletionPort',HANDLE)]


def structure_layout():
    return dict(basic_limit=c.sizeof(BasicLimit),extended_limit=c.sizeof(ExtendedLimit),
                basic_accounting=c.sizeof(BasicAccounting),memory_usage=c.sizeof(MemoryUsage),
                startup_info=c.sizeof(StartupInfo),startup_info_ex=c.sizeof(StartupInfoEx),
                process_information=c.sizeof(ProcessInformation),memory_status=c.sizeof(MemoryStatus))


class NativeApi:
    requires_atomic_assignment = True

    def __init__(self):
        if os.name != 'nt' or c.sizeof(HANDLE) != 8:
            raise JobError('Windows x64 is required; no native operation performed')
        self.k = c.WinDLL('kernel32',use_last_error=True)
        self.ports = {}
        signatures = {
            'CreateJobObjectW': (HANDLE,[c.c_void_p,c.c_wchar_p]),
            'SetInformationJobObject': (BOOL,[HANDLE,c.c_int,c.c_void_p,DWORD]),
            'QueryInformationJobObject': (BOOL,[HANDLE,c.c_int,c.c_void_p,DWORD,c.POINTER(DWORD)]),
            'SetHandleInformation': (BOOL,[HANDLE,DWORD,DWORD]),
            'GetHandleInformation': (BOOL,[HANDLE,c.POINTER(DWORD)]),
            'GetCurrentProcess': (HANDLE,[]),
            'GetProcessId': (DWORD,[HANDLE]),
            'CreateToolhelp32Snapshot': (HANDLE,[DWORD,DWORD]),
            'Process32FirstW': (BOOL,[HANDLE,c.POINTER(ProcessEntry)]),
            'Process32NextW': (BOOL,[HANDLE,c.POINTER(ProcessEntry)]),
            'IsProcessInJob': (BOOL,[HANDLE,HANDLE,c.POINTER(BOOL)]),
            'AssignProcessToJobObject': (BOOL,[HANDLE,HANDLE]),
            'CreateIoCompletionPort': (HANDLE,[HANDLE,HANDLE,SIZE_T,DWORD]),
            'GetQueuedCompletionStatus': (BOOL,[HANDLE,c.POINTER(DWORD),c.POINTER(SIZE_T),c.POINTER(c.c_void_p),DWORD]),
            'CreateFileW': (HANDLE,[c.c_wchar_p,DWORD,DWORD,c.POINTER(SecurityAttributes),DWORD,DWORD,HANDLE]),
            'CreatePipe': (BOOL,[c.POINTER(HANDLE),c.POINTER(HANDLE),c.POINTER(SecurityAttributes),DWORD]),
            'InitializeProcThreadAttributeList': (BOOL,[c.c_void_p,DWORD,DWORD,c.POINTER(SIZE_T)]),
            'UpdateProcThreadAttribute': (BOOL,[c.c_void_p,DWORD,SIZE_T,c.c_void_p,SIZE_T,c.c_void_p,c.c_void_p]),
            'DeleteProcThreadAttributeList': (None,[c.c_void_p]),
            'CreateProcessW': (BOOL,[c.c_wchar_p,c.c_wchar_p,c.c_void_p,c.c_void_p,BOOL,DWORD,c.c_void_p,c.c_wchar_p,c.POINTER(StartupInfoEx),c.POINTER(ProcessInformation)]),
            'ResumeThread': (DWORD,[HANDLE]),
            'GetProcessTimes': (BOOL,[HANDLE,c.POINTER(FileTime),c.POINTER(FileTime),c.POINTER(FileTime),c.POINTER(FileTime)]),
            'OpenProcess': (HANDLE,[DWORD,BOOL,DWORD]),
            'WaitForSingleObject': (DWORD,[HANDLE,DWORD]),
            'GetExitCodeProcess': (BOOL,[HANDLE,c.POINTER(DWORD)]),
            'TerminateProcess': (BOOL,[HANDLE,DWORD]),
            'TerminateJobObject': (BOOL,[HANDLE,DWORD]),
            'CloseHandle': (BOOL,[HANDLE]),
            'WriteFile': (BOOL,[HANDLE,c.c_void_p,DWORD,c.POINTER(DWORD),c.c_void_p]),
            'GlobalMemoryStatusEx': (BOOL,[c.POINTER(MemoryStatus)]),
            'GetDiskFreeSpaceExW': (BOOL,[c.c_wchar_p,c.POINTER(U64),c.POINTER(U64),c.POINTER(U64)]),
        }
        for name,(restype,argtypes) in signatures.items():
            function = getattr(self.k,name)
            function.restype, function.argtypes = restype,argtypes
        try:
            self.n = c.WinDLL('ntdll',use_last_error=True)
            self.n.NtQueryInformationProcess.restype = c.c_int32
            self.n.NtQueryInformationProcess.argtypes = [HANDLE,c.c_int,c.c_void_p,DWORD,c.POINTER(DWORD)]
        except (OSError,AttributeError) as error:
            raise JobError('native retained-handle parent query unavailable') from error

    def checked(self, value, operation):
        if not value or value == c.c_void_p(-1).value:
            raise JobError(f'{operation}: {c.WinError(c.get_last_error())}')
        return value

    def query(self, job, information_class, value):
        if not job:
            raise JobError('explicit private job handle required')
        length = DWORD()
        self.checked(self.k.QueryInformationJobObject(job,information_class,c.byref(value),c.sizeof(value),c.byref(length)),
                     f'QueryInformationJobObject({information_class})')
        if length.value != c.sizeof(value):
            raise JobError(f'query length mismatch for class {information_class}')
        return value

    def create_job(self, memory_limit):
        job = self.checked(self.k.CreateJobObjectW(None,None),'CreateJobObjectW')
        port = None
        try:
            self.checked(self.k.SetHandleInformation(job,1,0),'private job handle')
            info = ExtendedLimit()
            info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_JOB_MEMORY | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            info.JobMemoryLimit = memory_limit
            self.checked(self.k.SetInformationJobObject(job,9,c.byref(info),c.sizeof(info)),'set private job limits')
            port = self.checked(self.k.CreateIoCompletionPort(HANDLE(-1),None,0,1),'CreateIoCompletionPort')
            self.checked(self.k.SetHandleInformation(port,1,0),'private completion port')
            association = CompletionPort(job,port)
            self.checked(self.k.SetInformationJobObject(job,7,c.byref(association),c.sizeof(association)),'associate job completion port')
            self.ports[job] = port
            return job
        except BaseException:
            self.k.CloseHandle(job)
            if port:
                self.k.CloseHandle(port)
            raise

    def job_configuration(self, job):
        flags = DWORD()
        self.checked(self.k.GetHandleInformation(job,c.byref(flags)),'GetHandleInformation')
        info = self.query(job,9,ExtendedLimit())
        return dict(limit_flags=int(info.BasicLimitInformation.LimitFlags),memory_limit_bytes=int(info.JobMemoryLimit),
                    inheritable=bool(flags.value & 1))

    def controller_in_job(self, job):
        return self.in_job(self.k.GetCurrentProcess(),job)

    def in_job(self, process, job):
        if not job:
            raise JobError('explicit private job membership required')
        result = BOOL()
        self.checked(self.k.IsProcessInJob(process,job,c.byref(result)),'IsProcessInJob')
        return bool(result.value)

    def job_pids(self, job):
        if not job:
            raise JobError('explicit private job PID query required')
        capacity = 64
        while capacity <= 65536:
            class PidList(c.Structure):
                _fields_ = [('assigned',DWORD),('count',DWORD),('pids',SIZE_T*capacity)]
            value = PidList()
            length = DWORD()
            ok = self.k.QueryInformationJobObject(job,3,c.byref(value),c.sizeof(value),c.byref(length))
            if ok and value.count <= capacity and value.assigned <= value.count:
                return [int(value.pids[i]) for i in range(value.count)]
            if not ok and c.get_last_error() != 234:
                self.checked(ok,'job PID list')
            capacity = max(capacity*2,int(value.assigned))
        raise JobError('job PID list exceeds bounded observation capacity')

    def create_suspended(self, argv, cwd, env, stdoutfile, stderrfile, stdin_pipe=False, private_job=None):
        if not private_job:
            raise JobError('atomic create-time private Job Object assignment required')
        if not argv or not ntpath.isabs(str(argv[0])):
            raise JobError('explicit absolute executable path required')
        if any('\0' in str(arg) for arg in argv):
            raise JobError('NUL in command')
        env_strings = []
        for key,value in sorted(env.items(),key=lambda item:item[0].upper()):
            if not key or '\0' in key or '\0' in value:
                raise JobError('invalid environment block')
            if '=' in key:
                drive_key = len(key)==3 and key[0]=='=' and key[1] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz' and key[2]==':'
                if not drive_key or not ntpath.isabs(value) or ntpath.splitdrive(value)[0].upper()!=key[1:].upper():
                    raise JobError('invalid drive-current-directory environment entry')
            env_strings.append(key+'='+value)
        block = '\0'.join(env_strings)+'\0\0'
        environment = c.create_unicode_buffer(block,len(block))
        command = c.create_unicode_buffer(subprocess.list2cmdline([str(arg) for arg in argv]))
        security = SecurityAttributes(c.sizeof(SecurityAttributes),None,True)
        handles = []
        parent_stdin = None
        attributes = None
        initialized = False
        try:
            output = self.checked(self.k.CreateFileW(str(stdoutfile),0x40000000,1,c.byref(security),1,0x80,None),'create fresh stdout log')
            handles.append(output)
            error = self.checked(self.k.CreateFileW(str(stderrfile),0x40000000,1,c.byref(security),1,0x80,None),'create fresh stderr log')
            handles.append(error)
            if stdin_pipe:
                input_handle,parent_stdin = HANDLE(),HANDLE()
                self.checked(self.k.CreatePipe(c.byref(input_handle),c.byref(parent_stdin),c.byref(security),4096),'CreatePipe')
                input_handle,parent_stdin = input_handle.value,parent_stdin.value
                handles.append(input_handle)
                self.checked(self.k.SetHandleInformation(parent_stdin,1,0),'noninherited private stdin writer')
            else:
                input_handle = self.checked(self.k.CreateFileW('NUL',0x80000000,3,c.byref(security),3,0x80,None),'open NUL stdin')
                handles.append(input_handle)
            size = SIZE_T()
            self.k.InitializeProcThreadAttributeList(None,2,0,c.byref(size))
            if not size.value:
                raise JobError('attribute-list size unavailable')
            attributes = c.create_string_buffer(size.value)
            self.checked(self.k.InitializeProcThreadAttributeList(attributes,2,0,c.byref(size)),'initialize handle whitelist')
            initialized = True
            inherited = (HANDLE*3)(input_handle,output,error)
            self.checked(self.k.UpdateProcThreadAttribute(attributes,0,0x20002,c.byref(inherited),c.sizeof(inherited),None,None),'set exact inherited handle whitelist')
            jobs = (HANDLE*1)(private_job)
            self.checked(self.k.UpdateProcThreadAttribute(attributes,0,0x2000D,c.byref(jobs),c.sizeof(jobs),None,None),
                         'set atomic private Job Object attribute (Windows 10+)')
            startup = StartupInfoEx()
            startup.StartupInfo.cb = c.sizeof(StartupInfoEx)
            startup.StartupInfo.dwFlags = 0x100
            startup.StartupInfo.hStdInput, startup.StartupInfo.hStdOutput, startup.StartupInfo.hStdError = input_handle,output,error
            startup.lpAttributeList = c.cast(attributes,c.c_void_p)
            result = ProcessInformation()
            flags = 0x4 | 0x400 | 0x80000 | 0x08000000
            self.checked(self.k.CreateProcessW(str(argv[0]),command,None,None,True,flags,
                                              environment,str(cwd),c.byref(startup),c.byref(result)),'CreateProcessW suspended')
            if self.k.GetProcessId(result.hProcess) != result.dwProcessId:
                self.k.TerminateProcess(result.hProcess,0xE001)
                self.k.CloseHandle(result.hProcess); self.k.CloseHandle(result.hThread)
                raise JobError('created process handle/PID mismatch')
            return dict(process=result.hProcess,thread=result.hThread,pid=int(result.dwProcessId),stdin=parent_stdin,assigned_at_creation=True)
        except BaseException:
            if parent_stdin:
                self.k.CloseHandle(parent_stdin)
            raise
        finally:
            if initialized:
                self.k.DeleteProcThreadAttributeList(attributes)
            for handle in handles:
                self.k.CloseHandle(handle)

    def creation_time(self, handle):
        values = [FileTime() for _ in range(4)]
        self.checked(self.k.GetProcessTimes(handle,*[c.byref(v) for v in values]),'GetProcessTimes')
        return (int(values[0].high)<<32) | int(values[0].low)

    def assign(self, job, process):
        self.checked(self.k.AssignProcessToJobObject(job,process),'AssignProcessToJobObject')

    def resume(self, thread):
        result = int(self.k.ResumeThread(thread))
        if result == 0xFFFFFFFF:
            raise JobError(f'ResumeThread: {c.WinError(c.get_last_error())}')
        return result

    def process_id(self, handle):
        pid = int(self.k.GetProcessId(handle))
        if not 0 < pid <= 0xFFFFFFFF:
            raise JobError('retained process PID unavailable')
        return pid

    def parent_pid(self, handle):
        pid, created = self.process_id(handle), self.creation_time(handle)
        value = ProcessBasicInformation()
        length = DWORD()
        status = int(self.n.NtQueryInformationProcess(handle,0,c.byref(value),c.sizeof(value),c.byref(length)))
        if (status != 0 or length.value != c.sizeof(value) or value.UniqueProcessId != pid
                or not 0 < value.InheritedFromUniqueProcessId <= 0xFFFFFFFF):
            raise JobError('native retained-handle parent identity unavailable')
        if self.process_id(handle) != pid or self.creation_time(handle) != created:
            raise JobError('retained process identity changed during parent query')
        return int(value.InheritedFromUniqueProcessId)

    def open_process(self, pid, can_terminate=False):
        if type(pid) is not int or not 0 < pid <= 0xFFFFFFFF or type(can_terminate) is not bool:
            raise JobError('explicit valid process identity/access required')
        access = 0x1000 | 0x100000 | (0x1 if can_terminate else 0)
        return self.checked(self.k.OpenProcess(access,False,pid),'OpenProcess for retained identity')

    def children_of(self, parent_pids, timeout_seconds=1.0):
        parents = set(parent_pids)
        if (not parents or any(type(pid) is not int or not 0 < pid <= 0xFFFFFFFF for pid in parents)
                or type(timeout_seconds) not in (int,float) or not 0 < timeout_seconds <= 1):
            raise JobError('explicit bounded process-parent query required')
        deadline = time.monotonic() + timeout_seconds
        snapshot = self.checked(self.k.CreateToolhelp32Snapshot(2,0),'CreateToolhelp32Snapshot for scoped parent edges')
        result = set()
        try:
            value = ProcessEntry(); value.dwSize = c.sizeof(value)
            found = self.k.Process32FirstW(snapshot,c.byref(value))
            for _ in range(65536):
                if time.monotonic() >= deadline:
                    raise JobError('scoped process-parent observation deadline')
                if not found:
                    if c.get_last_error() != 18:
                        self.checked(found,'scoped process-parent observation')
                    return result
                pid, parent = int(value.th32ProcessID), int(value.th32ParentProcessID)
                if parent in parents:
                    if not pid:
                        raise JobError('scoped child identity unavailable')
                    result.add((pid,parent))
                value.dwSize = c.sizeof(value)
                found = self.k.Process32NextW(snapshot,c.byref(value))
            raise JobError('scoped process-parent observation capacity exceeded')
        finally:
            self.checked(self.k.CloseHandle(snapshot),'close scoped process-parent snapshot')

    def exit_code(self, handle):
        status = int(self.k.WaitForSingleObject(handle,0))
        if status == 258:
            return None
        if status != 0:
            raise JobError('identity process wait failed')
        code = DWORD()
        self.checked(self.k.GetExitCodeProcess(handle,c.byref(code)),'GetExitCodeProcess')
        return int(code.value)

    def terminate_process(self, handle):
        self.checked(self.k.TerminateProcess(handle,0xE001),'terminate owned suspended process')

    def terminate_job(self, job):
        self.checked(self.k.TerminateJobObject(job,0xE002),'TerminateJobObject')

    def close_handle(self, handle):
        self.checked(self.k.CloseHandle(handle),'CloseHandle')
        port = self.ports.pop(handle,None)
        if port:
            self.checked(self.k.CloseHandle(port),'CloseHandle completion port')

    def job_state(self, job):
        accounting = self.query(job,1,BasicAccounting())
        memory = self.query(job,28,MemoryUsage())
        return dict(active_processes=int(accounting.ActiveProcesses),total_processes=int(accounting.TotalProcesses),
                    job_committed_bytes=int(memory.JobMemory),peak_committed_job_bytes=int(memory.PeakJobMemoryUsed))

    def notifications(self, job):
        events = []
        for _ in range(65536):
            message,key,pid = DWORD(),SIZE_T(),c.c_void_p()
            ok = self.k.GetQueuedCompletionStatus(self.ports[job],c.byref(message),c.byref(key),c.byref(pid),0)
            if not ok:
                if c.get_last_error() == 258:
                    return events
                self.checked(ok,'job completion notification')
            if key.value != job:
                raise JobError('unexpected completion ownership key')
            events.append(dict(message=int(message.value),pid=int(pid.value or 0)))
        raise JobError('job notification observation capacity exceeded')

    def write_pipe(self, handle, data):
        if len(data) > 16:
            raise JobError('private control message too large')
        buffer = c.create_string_buffer(data)
        written = DWORD()
        self.checked(self.k.WriteFile(handle,buffer,len(data),c.byref(written),None),'private stdin write')
        if written.value != len(data):
            raise JobError('partial private stdin write')

    def host_resources(self, drive_path):
        status = MemoryStatus(); status.dwLength = c.sizeof(status)
        self.checked(self.k.GlobalMemoryStatusEx(c.byref(status)),'GlobalMemoryStatusEx')
        available,total,free = U64(),U64(),U64()
        self.checked(self.k.GetDiskFreeSpaceExW(str(drive_path),c.byref(available),c.byref(total),c.byref(free)),
                     'GetDiskFreeSpaceExW')
        return dict(disk_free_bytes=min(int(available.value),int(free.value)),host_free_bytes=int(status.ullAvailPhys))


@dataclass
class OwnedProcess:
    pid: int
    creation_time_100ns: int
    handle: object
    thread: object = None
    stdin: object = None
    assigned: bool = False
    resumed: bool = False
    exit_code: int | None = None


class WindowsJob:
    def __init__(self, memory_limit_bytes=MEMORY_LIMIT, api=None):
        if type(memory_limit_bytes) is not int or memory_limit_bytes <= 0:
            raise JobError('invalid committed-memory limit')
        self.api = api or NativeApi()
        self.lock = threading.RLock()
        self.resume_terminate_lock = threading.RLock()
        self.aborted = False
        self.owned = {}
        self.events = []
        self.event_lock = threading.Lock()
        self.memory_event = False
        self.identity_failure = False
        self.launch_cleanup_errors = []
        self.handle = None
        self.cleaning = False
        try:
            self.handle = self.api.create_job(memory_limit_bytes)
            expected = JOB_OBJECT_LIMIT_JOB_MEMORY | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            config = self.api.job_configuration(self.handle)
            if (config['limit_flags'] != expected or config['limit_flags'] & BREAKAWAY_FLAGS
                    or config['memory_limit_bytes'] != memory_limit_bytes or config['inheritable']
                    or self.api.controller_in_job(self.handle) or self.api.job_pids(self.handle)):
                raise JobError('private job isolation/limit readback failed')
            self._event('private_job_created',memory_metric='job_committed_bytes',memory_limit_bytes=memory_limit_bytes)
        except BaseException:
            if self.handle is not None:
                self.api.close_handle(self.handle)
                self.handle = None
            raise

    def _event(self, event, **values):
        value = dict(event=event,utc=datetime.now(timezone.utc).isoformat(),monotonic_ns=time.monotonic_ns(),**values)
        with self.event_lock:
            self.events.append(value)

    def drain_events(self):
        with self.event_lock:
            result,self.events = self.events,[]
            return result

    def launch(self, argv, cwd, env, stdoutfile, stderrfile, stdin_pipe=False):
        with self.lock:
            if self.handle is None or self.cleaning or self.aborted:
                raise JobError('job closed, cleaning or permanently aborted')
            job = self.handle
            raw = None
            child = None
            try:
                raw = self.api.create_suspended(argv,cwd,env,stdoutfile,stderrfile,stdin_pipe,private_job=job)
                child = OwnedProcess(raw['pid'],self.api.creation_time(raw['process']),raw['process'],raw['thread'],raw['stdin'])
                self.owned[(child.pid,child.creation_time_100ns)] = child
                self._event('worker_created_suspended',pid=child.pid,creation_time_100ns=child.creation_time_100ns)
                if self.aborted or self.cleaning or self.handle != job:
                    raise JobError('launch aborted before assignment')
                if not raw.get('assigned_at_creation'):
                    if getattr(self.api,'requires_atomic_assignment',False):
                        raise JobError('atomic assignment unavailable; no non-atomic fallback')
                    self.api.assign(job,child.handle)
                if not self.api.in_job(child.handle,job):
                    raise JobError('suspended worker private membership not verified')
                child.assigned = True
                self._event('worker_assigned',pid=child.pid,creation_time_100ns=child.creation_time_100ns)
                with self.resume_terminate_lock:
                    if self.aborted or self.cleaning or self.handle != job:
                        raise JobError('launch aborted before resume')
                    if self.api.resume(child.thread) != 1:
                        raise JobError('unexpected initial suspend count')
                    child.resumed = True
                    self._event('worker_resumed',pid=child.pid,creation_time_100ns=child.creation_time_100ns)
                self.api.close_handle(child.thread); child.thread = None
                return child
            except BaseException as error:
                if raw is not None:
                    if child is None:
                        self.identity_failure = True
                    try:
                        if self.api.exit_code(raw['process']) is None:
                            self.api.terminate_process(raw['process'])
                    except BaseException as cleanup_error:
                        self.launch_cleanup_errors.append(str(cleanup_error))
                    for attribute,key in (('thread','thread'),('stdin','stdin')):
                        handle = raw[key]
                        if handle is not None:
                            try:
                                self.api.close_handle(handle)
                                if child:
                                    setattr(child,attribute,None)
                            except BaseException as cleanup_error:
                                self.launch_cleanup_errors.append(str(cleanup_error))
                    if child is None:
                        try:
                            self.api.close_handle(raw['process'])
                        except BaseException as cleanup_error:
                            self.launch_cleanup_errors.append(str(cleanup_error))
                self._event('worker_launch_failed',pid=raw['pid'] if raw else None,
                            identity_known=child is not None,reason=str(error))
                raise JobError(f'worker launch failed without retry: {error}') from error

    def validate_pid(self, pid, creation_time_100ns=None):
        with self.lock:
            job = self.handle
            if job is None or self.cleaning:
                raise JobError('job closed or cleaning')
            for (known_pid,created),owned in self.owned.items():
                if known_pid == pid and owned.handle is not None and self.api.exit_code(owned.handle) is None:
                    if creation_time_100ns is not None and created != creation_time_100ns:
                        raise JobError('expected creation identity differs')
                    if not self.api.in_job(owned.handle,job):
                        raise JobError('expected process is outside private job')
                    return owned
            handle = self.api.open_process(pid)
            try:
                created = self.api.creation_time(handle)
                if creation_time_100ns is not None and created != creation_time_100ns:
                    raise JobError('expected creation identity differs')
                if not self.api.in_job(handle,job):
                    raise JobError('observed process is outside private job')
                child = OwnedProcess(pid,created,handle,assigned=True,resumed=True)
                self.owned[(pid,created)] = child
                self._event('owned_process_observed',pid=pid,creation_time_100ns=created)
                return child
            except BaseException:
                self.api.close_handle(handle)
                raise

    def process_exit(self, owned):
        with self.lock:
            if self.owned.get((owned.pid,owned.creation_time_100ns)) is not owned:
                raise JobError('process identity not owned')
            if owned.handle is None:
                return owned.exit_code
            if self.api.creation_time(owned.handle) != owned.creation_time_100ns:
                raise JobError('retained process creation identity differs')
            code = self.api.exit_code(owned.handle)
            if code is not None:
                owned.exit_code = code
            return code

    def list_owned(self):
        with self.lock:
            return [dict(pid=p.pid,creation_time_100ns=p.creation_time_100ns,in_job=p.assigned,
                         resumed=p.resumed,exit_code=self.process_exit(p)) for p in self.owned.values()]

    def snapshot(self):
        with self.lock:
            if self.handle is None or self.cleaning:
                raise JobError('job closed or cleaning')
            try:
                job = self.handle
                state = self.api.job_state(job)
                if self.cleaning or self.handle != job:
                    raise JobError('observation invalidated by cleanup')
                notifications = self.api.notifications(job)
                self.memory_event |= any(v['message'] in (9,10) for v in notifications)
                for event in notifications:
                    self._event('job_notification',**event)
                for pid in self.api.job_pids(job):
                    self.validate_pid(pid)
                return dict(state,memory_metric='job_committed_bytes',memory_limit_event=self.memory_event,
                            owned=self.list_owned(),notifications=notifications)
            except BaseException as error:
                raise JobError(f'job observation failed: {error}') from error

    def host_resources(self, drive_path):
        try:
            return self.api.host_resources(drive_path)
        except BaseException as error:
            raise JobError(f'host observation failed: {error}') from error

    def write_stdin(self, owned, data):
        with self.lock:
            if owned.stdin is None or self.owned.get((owned.pid,owned.creation_time_100ns)) is not owned:
                raise JobError('private control channel not owned')
            self.api.write_pipe(owned.stdin,data)

    def close_stdin(self, owned):
        with self.lock:
            if self.owned.get((owned.pid,owned.creation_time_100ns)) is not owned:
                raise JobError('private control channel identity not owned')
            if owned.stdin is not None:
                self.api.close_handle(owned.stdin); owned.stdin = None

    def terminate(self):
        self.aborted = True
        with self.resume_terminate_lock:
            handle = self.handle
            if handle is None:
                raise JobError('private job handle is closed')
            self.api.terminate_job(handle)
            self._event('private_job_terminated')

    def cleanup(self, timeout_seconds=5):
        deadline = time.monotonic()+max(0,timeout_seconds)
        self.cleaning = True
        errors = list(self.launch_cleanup_errors)
        if self.identity_failure:
            errors.append('created worker identity was not observed')
        acquired = self.lock.acquire(timeout=max(0,deadline-time.monotonic()))
        if not acquired:
            return dict(verified=False,active_processes=None,total_processes=None,owned_exits=[],errors=['backend observation remains in flight'])
        exits = []
        active = total = None
        try:
            while True:
                pending = False
                for owned in self.owned.values():
                    try:
                        code = self.process_exit(owned)
                        pending |= code is None
                    except BaseException as error:
                        errors.append(str(error)); pending = True
                if not pending or time.monotonic() >= deadline:
                    break
                time.sleep(0.01)
            for owned in self.owned.values():
                exits.append(dict(pid=owned.pid,creation_time_100ns=owned.creation_time_100ns,exit_code=owned.exit_code))
                for attribute in ('thread','stdin','handle'):
                    handle = getattr(owned,attribute)
                    if handle is not None:
                        try:
                            self.api.close_handle(handle)
                            setattr(owned,attribute,None)
                        except BaseException as error:
                            errors.append(str(error))
            while True:
                try:
                    state = self.api.job_state(self.handle)
                    active = state['active_processes']
                    total = state.get('total_processes')
                except BaseException as error:
                    total = None
                    errors.append(str(error)); break
                if active == 0 or time.monotonic() >= deadline:
                    break
                time.sleep(0.01)
            if active != 0:
                errors.append('private job still active or observation unknown')
            if any(value['exit_code'] is None for value in exits):
                errors.append('owned identity-bound exit unverified')
            return dict(verified=not errors and active==0,active_processes=active,total_processes=total,owned_exits=exits,errors=errors)
        finally:
            self.lock.release()

    def close(self):
        self.aborted = True
        with self.resume_terminate_lock:
            if self.handle is not None:
                handle,self.handle = self.handle,None
                self.api.close_handle(handle)
