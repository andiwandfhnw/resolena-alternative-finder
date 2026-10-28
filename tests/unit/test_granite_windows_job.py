import ctypes
from pathlib import Path

import pytest

from scripts.uc001_granite_controller.windows_job import (
    JOB_OBJECT_LIMIT_JOB_MEMORY,
    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
    JobError,
    WindowsJob,
    structure_layout,
)


class FakeApi:
    def __init__(self):
        self.calls = []
        self.processes = {}
        self.next_pid = 100
        self.assignment_fails = False
        self.membership_fails = False
        self.controller_member = False
        self.keep_descendant_alive = False
        self.memory = 1024
        self.events = []
        self.job_closed = False
        self.outside = {'pid': 900, 'alive': True, 'job': False}

    def create_job(self, memory_limit):
        self.calls.append(('create_job', memory_limit))
        self.limit = memory_limit
        return 'private-job'

    def job_configuration(self, job):
        return {'limit_flags': JOB_OBJECT_LIMIT_JOB_MEMORY | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
                'memory_limit_bytes': self.limit, 'inheritable': False}

    def controller_in_job(self, job):
        return self.controller_member

    def job_pids(self, job):
        return [v['pid'] for v in self.processes.values() if v['job'] and v['alive']]

    def create_suspended(self, argv, cwd, env, stdoutfile, stderrfile, stdin_pipe=False, private_job=None):
        self.next_pid += 1
        pid = self.next_pid
        handle = f'p-{pid}'
        self.processes[handle] = {'pid': pid, 'created': pid*1000, 'alive': True,
                                  'job': False, 'suspended': True, 'exit_code': 0}
        self.calls.append(('create_suspended', pid))
        return {'process': handle, 'thread': f't-{pid}', 'pid': pid,
                'stdin': f'stdin-{pid}' if stdin_pipe else None}

    def creation_time(self, handle):
        return self.processes[handle]['created']

    def assign(self, job, handle):
        self.calls.append(('assign', self.processes[handle]['pid']))
        if self.assignment_fails:
            raise OSError('synthetic assignment failure')
        self.processes[handle]['job'] = True

    def in_job(self, handle, job):
        self.calls.append(('in_job', self.processes[handle]['pid']))
        return self.processes[handle]['job'] and not self.membership_fails

    def resume(self, thread):
        pid = int(thread.split('-')[1])
        self.calls.append(('resume', pid))
        self.processes[f'p-{pid}']['suspended'] = False
        return 1

    def close_handle(self, handle):
        self.calls.append(('close_handle', handle))
        if handle == 'private-job':
            self.job_closed = True
            self.terminate_job(handle)

    def exit_code(self, handle):
        value = self.processes[handle]
        return None if value['alive'] else value['exit_code']

    def terminate_process(self, handle):
        self.calls.append(('terminate_process', self.processes[handle]['pid']))
        self.processes[handle]['alive'] = False
        self.processes[handle]['exit_code'] = 0xE001

    def terminate_job(self, job):
        self.calls.append(('terminate_job', job))
        for value in self.processes.values():
            if value['job'] and not self.keep_descendant_alive:
                value['alive'] = False
                value['exit_code'] = 0xE002

    def open_process(self, pid):
        if pid == 900:
            self.processes['outside'] = dict(self.outside, created=900000, suspended=False, exit_code=0)
            return 'outside'
        return f'p-{pid}'

    def job_state(self, job):
        return {'active_processes': len(self.job_pids(job)), 'job_committed_bytes': self.memory,
                'peak_committed_job_bytes': self.memory, 'total_processes': len(self.processes)}

    def notifications(self, job):
        result, self.events = self.events, []
        return result

    def write_pipe(self, handle, data):
        self.calls.append(('write_pipe', handle, data))

    def host_resources(self, drive_path):
        return {'disk_free_bytes': 60*1024**3, 'host_free_bytes': 8*1024**3}


@pytest.fixture
def api():
    return FakeApi()


def launch(job, tmp_path, **kwargs):
    return job.launch(['C:\\Python\\python.exe', '-I', 'worker.py'], str(tmp_path), {},
                      str(tmp_path/'stdout.log'), str(tmp_path/'stderr.log'), **kwargs)


def test_worker_is_created_suspended_assigned_verified_then_resumed(api, tmp_path):
    job = WindowsJob(api=api)
    child = launch(job, tmp_path)
    calls = [v[0] for v in api.calls]
    assert calls.index('create_suspended') < calls.index('assign') < calls.index('in_job') < calls.index('resume')
    assert child.pid == 101 and child.creation_time_100ns == 101000
    assert child.assigned and child.resumed
    assert job.list_owned()[0]['in_job'] is True
    job.terminate()
    assert job.cleanup()['verified']
    job.close()


def test_assignment_failure_never_resumes_and_kills_only_created_worker(api, tmp_path):
    api.assignment_fails = True
    job = WindowsJob(api=api)
    with pytest.raises(JobError):
        launch(job, tmp_path)
    assert not any(v[0] == 'resume' for v in api.calls)
    assert ('terminate_process', 101) in api.calls
    assert api.outside['alive']
    job.close()


def test_failed_membership_prevents_resume(api, tmp_path):
    api.membership_fails = True
    job = WindowsJob(api=api)
    with pytest.raises(JobError):
        launch(job, tmp_path)
    assert not any(v[0] == 'resume' for v in api.calls)
    job.close()


def test_controller_cannot_belong_to_private_job(api):
    api.controller_member = True
    with pytest.raises(JobError):
        WindowsJob(api=api)
    assert api.job_closed


def test_limit_readback_rejects_breakaway_or_wrong_memory(api):
    api.job_configuration = lambda _: {'limit_flags': 0x800 | JOB_OBJECT_LIMIT_JOB_MEMORY | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
                                     'memory_limit_bytes': 1, 'inheritable': True}
    with pytest.raises(JobError):
        WindowsJob(api=api)
    assert api.job_closed


def test_nested_job_members_die_and_unrelated_process_survives(api, tmp_path):
    job = WindowsJob(api=api)
    launch(job, tmp_path)
    api.processes['p-102'] = {'pid':102,'created':102000,'alive':True,'job':True,'suspended':False,'exit_code':0}
    sample = job.snapshot()
    assert {p['pid'] for p in sample['owned']} == {101,102}
    job.terminate()
    result = job.cleanup()
    assert result['verified'] and result['active_processes'] == 0
    assert all(p['exit_code'] is not None for p in result['owned_exits'])
    assert api.outside['alive']
    job.close()


def test_unrelated_pid_validation_is_rejected_without_termination(api):
    job = WindowsJob(api=api)
    with pytest.raises(JobError):
        job.validate_pid(900)
    assert not any(v[0] == 'terminate_process' and v[1] == 900 for v in api.calls)
    assert api.outside['alive']
    job.close()


def test_creation_identity_mismatch_is_not_accepted(api, tmp_path):
    job = WindowsJob(api=api)
    process = launch(job, tmp_path)
    with pytest.raises(JobError):
        job.validate_pid(process.pid, process.creation_time_100ns + 1)
    job.terminate()
    job.cleanup()
    job.close()


def test_memory_sample_is_native_job_commit_not_rss(api, tmp_path):
    job = WindowsJob(api=api)
    launch(job, tmp_path)
    sample = job.snapshot()
    assert sample['job_committed_bytes'] == 1024
    assert sample['memory_metric'] == 'job_committed_bytes'
    assert 'rss' not in sample
    job.terminate(); job.cleanup(); job.close()


def test_memory_limit_notification_is_retained_as_failure_signal(api):
    job = WindowsJob(api=api)
    api.events = [{'message': 10, 'pid':101}]
    assert job.snapshot()['memory_limit_event'] is True
    assert job.snapshot()['memory_limit_event'] is True
    job.close()


def test_cleanup_cannot_report_success_with_active_descendant(api, tmp_path):
    job = WindowsJob(api=api)
    launch(job, tmp_path)
    api.keep_descendant_alive = True
    job.terminate()
    result = job.cleanup(timeout_seconds=0)
    assert result['verified'] is False
    assert result['active_processes'] == 1
    assert result['errors']
    job.close()


def test_process_exit_is_bound_to_retained_handle(api, tmp_path):
    job = WindowsJob(api=api)
    child = launch(job, tmp_path)
    assert job.process_exit(child) is None
    api.processes[child.handle]['alive'] = False
    api.processes[child.handle]['exit_code'] = 7
    assert job.process_exit(child) == 7
    assert job.process_exit(child) == 7
    job.cleanup(); job.close()


def test_private_stdin_pipe_is_owned_and_closed(api, tmp_path):
    job = WindowsJob(api=api)
    child = launch(job, tmp_path, stdin_pipe=True)
    job.write_stdin(child, b'CLOSE\n')
    assert ('write_pipe','stdin-101',b'CLOSE\n') in api.calls
    job.close_stdin(child)
    assert ('close_handle','stdin-101') in api.calls
    job.terminate(); job.cleanup(); job.close()


def test_host_resources_failures_propagate_instead_of_zero(api):
    job = WindowsJob(api=api)
    assert job.host_resources('C:\\')['disk_free_bytes'] > 0
    api.host_resources = lambda _: (_ for _ in ()).throw(OSError('measurement failed'))
    with pytest.raises(JobError):
        job.host_resources('C:\\')
    job.close()


def test_windows_x64_structure_layouts_are_explicit_and_portable():
    layout = structure_layout()
    assert ctypes.sizeof(ctypes.c_void_p) == 8
    assert layout == {'basic_limit':64,'extended_limit':144,'basic_accounting':48,
                      'memory_usage':16,'startup_info':104,'startup_info_ex':112,
                      'process_information':24,'memory_status':64}


def test_every_native_function_call_has_explicit_pointer_safe_signature(monkeypatch):
    import ast
    from types import SimpleNamespace
    from scripts.uc001_granite_controller import windows_job as module
    class Function:
        argtypes = None
        restype = None
    class Library:
        def __init__(self):
            self.functions = {}
        def __getattr__(self, name):
            return self.functions.setdefault(name, Function())
    library = Library()
    monkeypatch.setattr(module, 'os', SimpleNamespace(name='nt'))
    monkeypatch.setattr(module.c, 'WinDLL', lambda *args, **kwargs: library, raising=False)
    module.NativeApi()
    tree = ast.parse(Path(module.__file__).read_text())
    calls = {node.func.attr for node in ast.walk(tree) if isinstance(node,ast.Call)
             and isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Attribute)
             and isinstance(node.func.value.value,ast.Name) and node.func.value.value.id=='self'
             and node.func.value.attr=='k'}
    assert calls <= set(library.functions)
    assert all(library.functions[name].argtypes is not None for name in calls)


def test_invalid_windows_file_handle_is_failure_not_truthy_success(monkeypatch):
    from scripts.uc001_granite_controller import windows_job as module
    monkeypatch.setattr(module.c,'WinError',lambda code:OSError(code,'synthetic native failure'),raising=False)
    monkeypatch.setattr(module.c,'get_last_error',lambda:6,raising=False)
    api = object.__new__(module.NativeApi)
    with pytest.raises(JobError):
        api.checked(ctypes.c_void_p(-1).value,'create fresh log')


def test_termination_and_event_drain_do_not_wait_for_sampler_lock(api, tmp_path):
    import threading
    job = WindowsJob(api=api)
    launch(job, tmp_path)
    locked, release = threading.Event(), threading.Event()
    def hold_measurement_lock():
        with job.lock:
            locked.set()
            release.wait(2)
    thread = threading.Thread(target=hold_measurement_lock)
    thread.start()
    assert locked.wait(1)
    job.terminate()
    events_result = []
    drain = threading.Thread(target=lambda: events_result.extend(job.drain_events()))
    drain.start()
    drain.join(0.1)
    try:
        assert not drain.is_alive(), 'Event logging blocked behind stale resource observation'
        assert any(v['event']=='private_job_terminated' for v in events_result)
    finally:
        release.set(); thread.join(); drain.join()
        job.cleanup(); job.close()


def test_close_stdin_rejects_an_unowned_control_handle(api):
    from scripts.uc001_granite_controller.windows_job import OwnedProcess
    job = WindowsJob(api=api)
    outside = OwnedProcess(900,900000,'outside',stdin='unrelated-pipe')
    with pytest.raises(JobError):
        job.close_stdin(outside)
    assert ('close_handle','unrelated-pipe') not in api.calls
    job.close()


def test_snapshot_aborts_if_cleanup_begins_during_native_observation(api):
    job = WindowsJob(api=api)
    original = api.job_state
    def cleaning_during_query(handle):
        result = original(handle)
        job.cleaning = True
        return result
    api.job_state = cleaning_during_query
    with pytest.raises(JobError):
        job.snapshot()
    job.close()


def test_closed_job_never_queries_membership_against_implicit_current_job(api):
    job = WindowsJob(api=api)
    job.close()
    api.open_process = lambda _: (_ for _ in ()).throw(AssertionError('must not open process after close'))
    with pytest.raises(JobError):
        job.validate_pid(900)


@pytest.mark.parametrize('interruption_point',['create','assign'])
def test_watchdog_abort_during_launch_never_resumes_or_retries(api, tmp_path, interruption_point):
    job = WindowsJob(api=api)
    if interruption_point == 'create':
        original = api.create_suspended
        def interrupted(*args, **kwargs):
            job.terminate()
            return original(*args, **kwargs)
        api.create_suspended = interrupted
    else:
        original = api.assign
        def interrupted(*args, **kwargs):
            result = original(*args, **kwargs)
            job.terminate()
            return result
        api.assign = interrupted
    with pytest.raises(JobError):
        launch(job,tmp_path)
    assert not any(call[0]=='resume' for call in api.calls)
    assert not api.processes['p-101']['alive']
    with pytest.raises(JobError):
        launch(job,tmp_path)
    assert sum(call[0]=='create_suspended' for call in api.calls)==1
    job.cleanup(); job.close()


def test_atomic_assignment_is_verified_without_duplicate_assignment(api,tmp_path):
    job = WindowsJob(api=api)
    original = api.create_suspended
    def atomic_create(*args,private_job=None,**kwargs):
        assert private_job == 'private-job'
        raw = original(*args,private_job=private_job,**kwargs)
        api.assign(private_job,raw['process'])
        raw['assigned_at_creation'] = True
        return raw
    api.create_suspended = atomic_create
    child = launch(job,tmp_path)
    assert child.assigned and child.resumed
    assert sum(value[0]=='assign' for value in api.calls)==1
    job.terminate(); job.cleanup(); job.close()


def test_production_backend_never_falls_back_to_nonatomic_assignment(api,tmp_path):
    api.requires_atomic_assignment = True
    job = WindowsJob(api=api)
    with pytest.raises(JobError):
        launch(job,tmp_path)
    assert not any(value[0] in ('assign','resume') for value in api.calls)
    assert not api.processes['p-101']['alive']
    job.cleanup(); job.close()


def test_unknown_created_identity_cannot_be_reported_as_verified_cleanup(api,tmp_path):
    job = WindowsJob(api=api)
    api.creation_time = lambda _: (_ for _ in ()).throw(OSError('creation time unavailable'))
    with pytest.raises(JobError):
        launch(job,tmp_path)
    assert not any(call[0]=='resume' for call in api.calls)
    assert not api.processes['p-101']['alive']
    result = job.cleanup()
    assert result['verified'] is False
    assert any('identity' in error for error in result['errors'])
    job.close()


@pytest.mark.parametrize('environment_values',[{}, {'=C:':'C:\\Resolena\\gn1-20261025','SystemRoot':'C:\\Windows'}])
def test_native_create_inserts_exact_handle_and_job_lists_before_suspended_creation(tmp_path,environment_values):
    from types import SimpleNamespace
    from scripts.uc001_granite_controller import windows_job as module
    calls = []
    next_handle = iter((1001,1002,1003))
    def create_file(*args):
        return next(next_handle)
    def initialize(attributes,count,flags,size):
        assert count == 2
        ctypes.cast(size,ctypes.POINTER(module.SIZE_T))[0] = 256
        return int(attributes is not None)
    def update(attributes,flags,key,value,size,previous,returned):
        pointer = ctypes.cast(value,ctypes.POINTER(module.HANDLE))
        values = [pointer[i] for i in range(size//ctypes.sizeof(module.HANDLE))]
        calls.append(('attribute',key,values))
        return 1
    def create_process(application,command,process_security,thread_security,inherit,flags,environment,cwd,startup,result):
        assert application == 'C:\\Python\\python.exe'
        actual_environment = ctypes.wstring_at(environment,len(environment)).rstrip('\0').split('\0')
        expected_environment = [key+'='+value for key,value in sorted(environment_values.items(),key=lambda item:item[0].upper())]
        assert actual_environment == (expected_environment or [''])
        assert process_security is None and thread_security is None
        assert inherit is True
        assert flags & 0x4 and flags & 0x80000 and not flags & 0x01000000
        info = ctypes.cast(startup,ctypes.POINTER(module.StartupInfoEx)).contents
        assert info.StartupInfo.cb == 112 and info.StartupInfo.dwFlags == 0x100
        output = ctypes.cast(result,ctypes.POINTER(module.ProcessInformation)).contents
        output.hProcess,output.hThread,output.dwProcessId,output.dwThreadId = 2001,2002,1234,1235
        calls.append(('create_suspended',))
        return 1
    api = object.__new__(module.NativeApi)
    api.k = SimpleNamespace(CreateFileW=create_file,InitializeProcThreadAttributeList=initialize,
        UpdateProcThreadAttribute=update,DeleteProcThreadAttributeList=lambda *_:None,
        CreateProcessW=create_process,GetProcessId=lambda _:1234,CloseHandle=lambda _:1)
    result = api.create_suspended(['C:\\Python\\python.exe','-I','worker.py'],str(tmp_path),environment_values,
                                  str(tmp_path/'out'),str(tmp_path/'err'),private_job=333)
    assert calls == [('attribute',0x20002,[1003,1001,1002]),('attribute',0x2000D,[333]),('create_suspended',)]
    assert result['assigned_at_creation'] is True


@pytest.mark.parametrize('environment_values',[
    {'A=B':'value'},{'=1:':'C:\\Windows'},{'=CC:':'C:\\Windows'},
    {'=C:':'D:\\Windows'},{'=C:':'C:relative'},{'=C:':'C:\\bad\0value'},
])
def test_malformed_or_unsafe_windows_pseudo_environment_is_rejected(tmp_path,environment_values):
    from scripts.uc001_granite_controller import windows_job as module
    api = object.__new__(module.NativeApi)
    with pytest.raises(JobError):
        api.create_suspended(['C:\\Python\\python.exe'],str(tmp_path),environment_values,
                              str(tmp_path/'out'),str(tmp_path/'err'),private_job=333)


def parent_query_api(monkeypatch, *, status=0, returned_size=48, returned_pid=61020,
                     parent=61196, times=(134374354509736275, 134374354509736275)):
    from types import SimpleNamespace
    from scripts.uc001_granite_controller import windows_job as module
    api = object.__new__(module.NativeApi)
    api.k = SimpleNamespace(GetProcessId=lambda _:61020)
    values = iter(times)
    api.creation_time = lambda _:next(values)
    def query(handle, information_class, output, size, length):
        assert handle == 'retained-interpreter' and information_class == 0 and size == 48
        info = ctypes.cast(output,ctypes.POINTER(module.ProcessBasicInformation)).contents
        info.UniqueProcessId = returned_pid
        info.InheritedFromUniqueProcessId = parent
        ctypes.cast(length,ctypes.POINTER(module.DWORD))[0] = returned_size
        return status
    api.n = SimpleNamespace(NtQueryInformationProcess=query)
    return api


def test_retained_interpreter_parent_is_read_without_filetime_precision_loss(monkeypatch):
    api=parent_query_api(monkeypatch)
    assert api.process_id('retained-interpreter') == 61020
    assert api.parent_pid('retained-interpreter') == 61196


@pytest.mark.parametrize('changes',[
    {'status':-1073741822},{'returned_size':47},{'returned_pid':61196},{'parent':0},
    {'times':(134374354509736275,134374354509736276)},
])
def test_unknown_or_changed_native_parent_identity_is_rejected(monkeypatch,changes):
    api=parent_query_api(monkeypatch,**changes)
    with pytest.raises(JobError):
        api.parent_pid('retained-interpreter')


def test_native_process_basic_information_x64_offsets_are_exact():
    from scripts.uc001_granite_controller import windows_job as module
    assert ctypes.sizeof(module.ProcessBasicInformation)==48
    assert module.ProcessBasicInformation.UniqueProcessId.offset==32
    assert module.ProcessBasicInformation.InheritedFromUniqueProcessId.offset==40


def test_process_id_requires_nonzero_native_identity():
    from types import SimpleNamespace
    from scripts.uc001_granite_controller import windows_job as module
    api=object.__new__(module.NativeApi);api.k=SimpleNamespace(GetProcessId=lambda _:0)
    with pytest.raises(JobError):
        api.process_id('retained')


def test_interpreter_termination_access_is_explicit_and_not_a_default():
    from types import SimpleNamespace
    from scripts.uc001_granite_controller import windows_job as module
    calls=[]
    api=object.__new__(module.NativeApi)
    api.k=SimpleNamespace(OpenProcess=lambda access,inherit,pid:calls.append((access,inherit,pid)) or 77)
    assert api.open_process(61020)==77
    assert api.open_process(61020,can_terminate=True)==77
    assert calls==[(0x101000,False,61020),(0x101001,False,61020)]


@pytest.mark.parametrize('pid',[0,-1,True,2**32])
def test_native_process_open_rejects_ambiguous_pid(pid):
    from scripts.uc001_granite_controller import windows_job as module
    api=object.__new__(module.NativeApi)
    with pytest.raises(JobError):
        api.open_process(pid)


def child_snapshot_api(monkeypatch,rows,*,next_error=18):
    from types import SimpleNamespace
    from scripts.uc001_granite_controller import windows_job as module
    api=object.__new__(module.NativeApi);closed=[];index=[0]
    def fill(pointer):
        value=ctypes.cast(pointer,ctypes.POINTER(module.ProcessEntry)).contents
        assert value.dwSize==ctypes.sizeof(module.ProcessEntry)
        if index[0]>=len(rows):
            return 0
        value.th32ProcessID,value.th32ParentProcessID=rows[index[0]]
        index[0]+=1
        return 1
    api.k=SimpleNamespace(CreateToolhelp32Snapshot=lambda flags,pid:99 if (flags,pid)==(2,0) else 0,
                          Process32FirstW=lambda handle,pointer:fill(pointer),
                          Process32NextW=lambda handle,pointer:fill(pointer),
                          CloseHandle=lambda handle:closed.append(handle) or 1)
    monkeypatch.setattr(module.c,'get_last_error',lambda:next_error,raising=False)
    monkeypatch.setattr(module.c,'WinError',lambda code:OSError(code,'synthetic native error'),raising=False)
    return api,closed


def test_child_snapshot_returns_only_explicit_parent_edges_and_closes_handle(monkeypatch):
    api,closed=child_snapshot_api(monkeypatch,[(1,0),(61196,60320),(61020,61196),(17,8),(61021,61020)])
    assert api.children_of({61196,61020})=={(61020,61196),(61021,61020)}
    assert closed==[99]


def test_child_snapshot_unknown_extra_is_returned_for_fail_closed_caller(monkeypatch):
    api,closed=child_snapshot_api(monkeypatch,[(61020,61196),(70000,61196)])
    assert api.children_of({61196,61020})=={(61020,61196),(70000,61196)}
    assert closed==[99]


def test_child_snapshot_failure_cannot_be_an_empty_safe_tree(monkeypatch):
    api,closed=child_snapshot_api(monkeypatch,[],next_error=5)
    with pytest.raises(JobError):
        api.children_of({61196})
    assert closed==[99]


def test_child_snapshot_timeout_closes_handle_and_fails(monkeypatch):
    from scripts.uc001_granite_controller import windows_job as module
    api,closed=child_snapshot_api(monkeypatch,[(61020,61196)])
    moments=iter([0.0,2.0])
    monkeypatch.setattr(module.time,'monotonic',lambda:next(moments))
    with pytest.raises(JobError):
        api.children_of({61196},timeout_seconds=1)
    assert closed==[99]


def test_process_entry_layout_does_not_depend_on_linux_wchar_width():
    from scripts.uc001_granite_controller import windows_job as module
    assert ctypes.sizeof(module.ProcessEntry)==568
    assert module.ProcessEntry.th32ParentProcessID.offset==32


def test_native_parent_query_is_dynamically_bound_with_pointer_safe_signature(monkeypatch):
    from types import SimpleNamespace
    from scripts.uc001_granite_controller import windows_job as module
    class Function:
        argtypes=None
        restype=None
    class Library:
        def __init__(self):
            self.functions={}
        def __getattr__(self,name):
            return self.functions.setdefault(name,Function())
    kernel,ntdll=Library(),Library()
    monkeypatch.setattr(module,'os',SimpleNamespace(name='nt'))
    monkeypatch.setattr(module.c,'WinDLL',lambda name,**kwargs: ntdll if name=='ntdll' else kernel,raising=False)
    module.NativeApi()
    query=ntdll.functions['NtQueryInformationProcess']
    assert query.restype is ctypes.c_int32
    assert query.argtypes == [module.HANDLE,ctypes.c_int,ctypes.c_void_p,module.DWORD,ctypes.POINTER(module.DWORD)]
    assert kernel.functions['Process32FirstW'].argtypes==[module.HANDLE,ctypes.POINTER(module.ProcessEntry)]


def test_scoped_snapshot_handle_failure_stops_before_enumeration(monkeypatch):
    from scripts.uc001_granite_controller import windows_job as module
    api,closed=child_snapshot_api(monkeypatch,[])
    api.k.CreateToolhelp32Snapshot=lambda *_:ctypes.c_void_p(-1).value
    with pytest.raises(JobError):
        api.children_of({61196})
    assert closed==[]


def test_cleanup_preserves_total_processes_after_all_owned_processes_exit(api,tmp_path):
    job=WindowsJob(api=api)
    launch(job,tmp_path)
    api.processes['unobserved-short-lived'] = dict(pid=707,created=707000,alive=False,
                                                  job=True,suspended=False,exit_code=0)
    job.terminate()
    result=job.cleanup()
    assert result['verified'] is True
    assert result['active_processes']==0
    assert result['total_processes']==2
    job.close()


def test_identity_query_open_uses_only_limited_query_rights_without_inheritance():
    from types import SimpleNamespace
    from scripts.uc001_granite_controller import windows_job as module
    calls=[]
    api=object.__new__(module.NativeApi)
    api.k=SimpleNamespace(OpenProcess=lambda access,inherit,pid:calls.append((access,inherit,pid)) or 77)
    assert api.open_query_process(38564)==77
    assert calls==[(0x1000,False,38564)]


@pytest.mark.parametrize('pid',[0,-1,True,2**32])
def test_identity_query_open_rejects_invalid_pid_without_native_call(pid):
    from scripts.uc001_granite_controller import windows_job as module
    api=object.__new__(module.NativeApi)
    with pytest.raises(JobError):
        api.open_query_process(pid)


@pytest.mark.parametrize('error_code',[5,87])
def test_identity_query_open_preserves_native_failure_code(monkeypatch,error_code):
    from types import SimpleNamespace
    from scripts.uc001_granite_controller import windows_job as module
    api=object.__new__(module.NativeApi)
    api.k=SimpleNamespace(OpenProcess=lambda *_:0)
    error=OSError('synthetic query-only open failure');error.winerror=error_code
    monkeypatch.setattr(module.c,'get_last_error',lambda:error_code,raising=False)
    monkeypatch.setattr(module.c,'WinError',lambda value:error if value==error_code else None,raising=False)
    with pytest.raises(OSError) as caught:
        api.open_query_process(38564)
    assert caught.value.winerror==error_code


def image_query_api(monkeypatch,*,path=r'C:\Windows\System32\conhost.exe',length=None,success=1):
    from types import SimpleNamespace
    from scripts.uc001_granite_controller import windows_job as module
    api=object.__new__(module.NativeApi);calls=[]
    def query(handle,flags,buffer,size):
        incoming=ctypes.cast(size,ctypes.POINTER(module.DWORD))
        calls.append((handle,flags,incoming[0],len(buffer)))
        if path is not None:
            buffer.value=path
        incoming[0]=len(path) if length is None else length
        return success
    api.k=SimpleNamespace(QueryFullProcessImageNameW=query)
    monkeypatch.setattr(module.c,'get_last_error',lambda:122,raising=False)
    monkeypatch.setattr(module.c,'WinError',lambda code:OSError(code,'synthetic path query failure'),raising=False)
    return api,calls


def test_identity_query_image_path_is_full_unicode_win32_path_with_fixed_bound(monkeypatch):
    path=r'C:\Windows\System32\conhost.exe'
    api,calls=image_query_api(monkeypatch,path=path)
    assert api.image_path('query-only')==path
    assert calls==[('query-only',0,32768,32768)]


@pytest.mark.parametrize('changes',[
    {'success':0},{'length':0},{'length':32768},{'length':32769},
    {'length':2},{'path':'conhost.exe'},{'path':r'\Windows\conhost.exe'},
    {'path':r'C:conhost.exe'},{'path':'C:/Windows/'},
])
def test_identity_query_image_failure_or_malformed_path_is_unknown(monkeypatch,changes):
    api,calls=image_query_api(monkeypatch,**changes)
    with pytest.raises(JobError):
        api.image_path('query-only')
    assert len(calls)==1


@pytest.mark.parametrize('raw_code',[0,259,57345,0xFFFFFFFF])
def test_identity_query_exit_code_uses_no_wait_rights_and_retains_raw_status(raw_code):
    from types import SimpleNamespace
    from scripts.uc001_granite_controller import windows_job as module
    def get_code(handle,pointer):
        assert handle=='query-only'
        ctypes.cast(pointer,ctypes.POINTER(module.DWORD))[0]=raw_code
        return 1
    api=object.__new__(module.NativeApi)
    api.k=SimpleNamespace(GetExitCodeProcess=get_code)
    assert api.query_exit_code('query-only')==raw_code


def test_identity_query_exit_code_failure_cannot_be_a_live_or_zero_status(monkeypatch):
    from types import SimpleNamespace
    from scripts.uc001_granite_controller import windows_job as module
    api=object.__new__(module.NativeApi)
    api.k=SimpleNamespace(GetExitCodeProcess=lambda *_:0)
    monkeypatch.setattr(module.c,'get_last_error',lambda:5,raising=False)
    monkeypatch.setattr(module.c,'WinError',lambda code:OSError(code,'synthetic status query failure'),raising=False)
    with pytest.raises(JobError):
        api.query_exit_code('query-only')


def test_identity_query_image_binding_has_pointer_safe_unicode_signature(monkeypatch):
    from types import SimpleNamespace
    from scripts.uc001_granite_controller import windows_job as module
    class Function:
        argtypes=None
        restype=None
    class Library:
        def __init__(self):self.functions={}
        def __getattr__(self,name):return self.functions.setdefault(name,Function())
    kernel,ntdll=Library(),Library()
    monkeypatch.setattr(module,'os',SimpleNamespace(name='nt'))
    monkeypatch.setattr(module.c,'WinDLL',lambda name,**kwargs:ntdll if name=='ntdll' else kernel,raising=False)
    module.NativeApi()
    function=kernel.functions['QueryFullProcessImageNameW']
    assert function.restype is module.BOOL
    assert function.argtypes==[module.HANDLE,module.DWORD,ctypes.POINTER(ctypes.c_wchar),ctypes.POINTER(module.DWORD)]


def test_identity_query_image_utf16_units_allow_non_bmp_path(monkeypatch):
    path='C:\\Synthetic\\\U0001f6b2.exe'
    units=len(path.encode('utf-16-le'))//2
    api,calls=image_query_api(monkeypatch,path=path,length=units)
    assert api.image_path('query-only')==path
    assert len(calls)==1


def console_system_api(monkeypatch,*,directory=r'C:\Windows\System32',length=None):
    from types import SimpleNamespace
    from scripts.uc001_granite_controller import windows_job as module
    calls=[]
    api=object.__new__(module.NativeApi)
    def get_directory(buffer,capacity):
        calls.append((len(buffer),capacity))
        buffer.value=directory
        return len(directory.encode('utf-16-le','surrogatepass'))//2 if length is None else length
    api.k=SimpleNamespace(GetSystemDirectoryW=get_directory)
    monkeypatch.setattr(module.c,'get_last_error',lambda:5,raising=False)
    monkeypatch.setattr(module.c,'WinError',lambda code:OSError(code,'synthetic system-directory failure'),raising=False)
    return api,calls


@pytest.mark.parametrize('directory',[r'C:\Windows\System32',r'D:\CurrentWindows\System32','D:\\Windows\\\U0001f6b2'])
def test_console_system_path_comes_only_from_bounded_native_system_directory(monkeypatch,directory):
    import ntpath
    monkeypatch.setenv('SystemRoot',r'Z:\FakeWindows')
    monkeypatch.setenv('windir',r'Z:\FakeWindows')
    api,calls=console_system_api(monkeypatch,directory=directory)
    assert api.system_console_path()==ntpath.join(directory,'conhost.exe')
    assert calls==[(32768,32768)]


@pytest.mark.parametrize('changes',[
    {'length':0},{'length':32768},{'length':32769},{'length':2},
    {'directory':'System32'},{'directory':r'\Windows\System32'},
    {'directory':r'C:System32'},{'directory':r'C:\Windows\System32\..\Other'},
])
def test_console_system_path_unavailable_relative_or_truncated_is_rejected(monkeypatch,changes):
    api,calls=console_system_api(monkeypatch,**changes)
    with pytest.raises(JobError):
        api.system_console_path()
    assert len(calls)==1


def test_console_system_directory_binding_has_pointer_safe_unicode_signature(monkeypatch):
    from types import SimpleNamespace
    from scripts.uc001_granite_controller import windows_job as module
    class Function:
        argtypes=None
        restype=None
    class Library:
        def __init__(self):self.functions={}
        def __getattr__(self,name):return self.functions.setdefault(name,Function())
    kernel,ntdll=Library(),Library()
    monkeypatch.setattr(module,'os',SimpleNamespace(name='nt'))
    monkeypatch.setattr(module.c,'WinDLL',lambda name,**kwargs:ntdll if name=='ntdll' else kernel,raising=False)
    module.NativeApi()
    function=kernel.functions['GetSystemDirectoryW']
    assert function.restype is module.DWORD
    assert function.argtypes==[ctypes.POINTER(ctypes.c_wchar),module.DWORD]
