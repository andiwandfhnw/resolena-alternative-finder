using System;
using System.Collections;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32.SafeHandles;

public sealed class ContractPython : IDisposable {
    [StructLayout(LayoutKind.Sequential)] struct Security { public int Length; public IntPtr Descriptor; public int Inherit; }
    [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)] struct Startup {
        public int Size; public string Reserved, Desktop, Title;
        public int X,Y,Width,Height,CountX,CountY,Fill,Flags; public short Show,ReservedLength;
        public IntPtr ReservedBytes,Input,Output,Error;
    }
    [StructLayout(LayoutKind.Sequential)] struct StartupEx { public Startup Startup; public IntPtr Attributes; }
    [StructLayout(LayoutKind.Sequential)] struct Created { public IntPtr Process,Thread; public int Pid,Tid; }
    [StructLayout(LayoutKind.Sequential)] struct Basic { public IntPtr Reserved,Peb,A,B,Pid,Parent; }
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool CreatePipe(out IntPtr read,out IntPtr write,ref Security security,int size);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool SetHandleInformation(IntPtr handle,int mask,int flags);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool InitializeProcThreadAttributeList(IntPtr list,int count,int flags,ref IntPtr size);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool UpdateProcThreadAttribute(IntPtr list,uint flags,IntPtr attribute,IntPtr value,IntPtr size,IntPtr previous,IntPtr result);
    [DllImport("kernel32.dll")] static extern void DeleteProcThreadAttributeList(IntPtr list);
    [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool CreateProcessW(string exe,StringBuilder command,IntPtr pa,IntPtr ta,bool inherit,uint flags,IntPtr environment,string directory,ref StartupEx startup,out Created created);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool AssignProcessToJobObject(IntPtr job,IntPtr process);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool IsProcessInJob(IntPtr process,IntPtr job,out bool member);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool QueryInformationJobObject(IntPtr job,int kind,IntPtr data,uint size,IntPtr returned);
    [DllImport("kernel32.dll",SetLastError=true)] static extern uint ResumeThread(IntPtr thread);
    [DllImport("kernel32.dll")] static extern bool TerminateProcess(IntPtr process,uint code);
    [DllImport("kernel32.dll")] static extern uint WaitForSingleObject(IntPtr handle,uint milliseconds);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr handle);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetProcessTimes(IntPtr process,out long created,out long exit,out long kernel,out long user);
    [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool QueryFullProcessImageNameW(IntPtr process,uint flags,StringBuilder path,ref int size);
    [DllImport("ntdll.dll")] static extern int NtQueryInformationProcess(IntPtr process,int kind,ref Basic basic,int size,IntPtr returned);
    public sealed class Identity { public int pid; public long created; public long parent_pid; public string image; }
    public sealed class Ownership {
        public Identity supervisor,redirector,interpreter;
        public Identity[] console_helpers;
        public int[] job_verified_pids; public bool job_membership_verified; public int server_pid;
    }
    public sealed class Helper { public Identity identity; public Process process; }
    public sealed class Roles { public Identity interpreter; public Identity[] console_helpers; }
    public sealed class Observation {
        public int pid; public Identity identity; public Process process;
        public bool handle_held,job_verified,identity_verified;
    }
    readonly List<Observation> observations=new List<Observation>();
    IntPtr ownedJob;
    public Observation[] ObservedMembers { get { return observations.ToArray(); } }
    readonly List<Helper> helpers=new List<Helper>();
    public Helper[] ConsoleHelpers { get { return helpers.ToArray(); } }
    public string ConsoleHostPath { get { return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System),"conhost.exe"); } }
    public Process Redirector { get; private set; }
    public Process Interpreter { get; private set; }
    public StreamWriter StandardInput { get; private set; }
    public Ownership LastProof { get; private set; }
    public Identity InterpreterIdentity { get; private set; }
    public string BindingStage { get; private set; }
    public int[] LastJobMembers { get; private set; }
    public Identity LastCandidate { get; private set; }
    public Identity RedirectorIdentity { get { return initial; } }
    public int Id { get { return Redirector.Id; } }
    public DateTime StartTime { get { return Redirector.StartTime; } }
    public IntPtr Handle { get { return Redirector.Handle; } }
    public bool HasExited { get { return Redirector.HasExited; } }
    public int ExitCode { get { return Redirector.ExitCode; } }
    public void Refresh() { Redirector.Refresh(); }
    public bool WaitForExit(int milliseconds) { return Redirector.WaitForExit(milliseconds); }
    Identity initial;
    static Exception Stop(string code) { return new IOException("ownership/"+code); }
    static void Require(bool condition,string code) { if (!condition) throw Stop(code); }
    static void NativeRequire(bool condition,string code) {if(!condition)throw new IOException("ownership/"+code,new Win32Exception(Marshal.GetLastWin32Error()));}
    static bool Same(Identity a,Identity b) { return a.pid==b.pid && a.created==b.created && a.parent_pid==b.parent_pid && String.Equals(a.image,b.image,StringComparison.OrdinalIgnoreCase); }
    public static Identity Read(Process process) {
        process.Refresh(); Require(!process.HasExited,"process_exited");
        long created,exit,kernel,user; Basic basic=new Basic(); StringBuilder image=new StringBuilder(32768); int length=image.Capacity;
        NativeRequire(GetProcessTimes(process.Handle,out created,out exit,out kernel,out user),"process_times_query_failed");
        Require(created>0,"process_creation_invalid");
        int status=NtQueryInformationProcess(process.Handle,0,ref basic,Marshal.SizeOf(basic),IntPtr.Zero);
        if(status!=0) {var error=new IOException("ownership/process_basic_query_failed");error.Data["ntstatus"]=status;throw error;}
        NativeRequire(QueryFullProcessImageNameW(process.Handle,0,image,ref length),"process_image_query_failed");
        Require(basic.Pid.ToInt64()==process.Id,"process_pid_mismatch");
        process.Refresh(); Require(!process.HasExited,"process_exited");
        return new Identity {pid=process.Id,created=created,parent_pid=basic.Parent.ToInt64(),image=image.ToString()};
    }
    static int[] Members(IntPtr job) {
        IntPtr data=Marshal.AllocHGlobal(8+IntPtr.Size*8);
        try {
            NativeRequire(QueryInformationJobObject(job,3,data,(uint)(8+IntPtr.Size*8),IntPtr.Zero),"job_query_failed");
            int assigned=Marshal.ReadInt32(data),count=Marshal.ReadInt32(data,4);
            Require(count==assigned && count>0 && count<=8,"job_members_ambiguous");
            int[] result=new int[count]; var unique=new HashSet<int>();
            for(int i=0;i<count;i++) {long pid=Marshal.ReadIntPtr(data,8+i*IntPtr.Size).ToInt64(); Require(pid>0 && pid<=Int32.MaxValue && unique.Add((int)pid),"job_pid_invalid");result[i]=(int)pid;}
            return result;
        } finally {Marshal.FreeHGlobal(data);}
    }
    static void Member(Process process,IntPtr job) {bool member;NativeRequire(IsProcessInJob(process.Handle,job,out member),"job_membership_query_failed");Require(member,"job_membership_failed");}
    public static Identity ReadInJob(Process process,IntPtr job) {
        Identity value=Read(process);Member(process,job);
        Require(Same(value,Read(process)),"candidate_identity_changed");return value;
    }
    public Identity[] Observe(IntPtr job,int serverPid) {
        Require(job==ownedJob,"job_identity_changed");
        Require(Same(initial,Read(Redirector)),"redirector_identity_changed");Member(Redirector,job);
        BindingStage="job_members";LastJobMembers=Members(job);
        var memberSet=new HashSet<int>(LastJobMembers);
        Require(memberSet.Contains(Id) && (serverPid==0 || (serverPid!=Id && memberSet.Contains(serverPid))),"job_members_ambiguous");
        var rows=new List<Identity>();
        foreach(int pid in LastJobMembers) {
            if(pid==Id || pid==serverPid)continue;
            BindingStage="candidate_handle";
            Observation record=observations.Find(delegate(Observation row){return row.pid==pid;});
            if(record==null) {
                record=new Observation {pid=pid,process=Process.GetProcessById(pid)};
                observations.Add(record);
            }
            record.handle_held=false;record.job_verified=false;record.identity_verified=false;
            var held=record.process.Handle;record.handle_held=true;
            BindingStage="candidate_identity";Identity value=Read(record.process);LastCandidate=value;
            if(record.identity!=null)Require(Same(record.identity,value),"candidate_identity_changed");
            BindingStage="candidate_job";Member(record.process,job);record.job_verified=true;
            Require(Same(value,Read(record.process)),"candidate_identity_changed");
            record.identity=value;record.identity_verified=true;rows.Add(value);
        }
        return rows.ToArray();
    }
    static bool Image(Identity value,string path) {return String.Equals(value.image,path,StringComparison.OrdinalIgnoreCase);}
    public static Roles AccountMembers(Identity root,Identity[] rows,string consolePath,Action<Identity,string> accept) {
        const string python=@"C:\ResolenaExperiments\tools\python-3.12.10\python.exe";
        var interpreters=new List<Identity>();var consoles=new List<Identity>();var ids=new HashSet<int>();
        foreach(Identity row in rows) {
            Require(row!=null && row.pid>0 && row.pid!=root.pid && ids.Add(row.pid),"job_pid_invalid");
            if(Image(row,python)) {
                Require(row.parent_pid==root.pid && row.created>=root.created && row.created>0,"unexpected_owned_process");
                interpreters.Add(row);
            } else if(Image(row,consolePath))consoles.Add(row);
        }
        Require(consoles.Count<=1,"console_helper_ambiguous");
        foreach(Identity helper in consoles) {
            Identity parent=helper.parent_pid==root.pid?root:(interpreters.Count==1 && helper.parent_pid==interpreters[0].pid?interpreters[0]:null);
            Require(parent!=null && helper.created>0 && helper.created>=parent.created,"console_helper_constraints");
            accept(helper,"console_helper");
        }
        Require(interpreters.Count<=1,"interpreter_ambiguous");
        if(interpreters.Count==1)accept(interpreters[0],"interpreter");
        Require(rows.Length==interpreters.Count+consoles.Count,"unexpected_owned_process");
        return new Roles {interpreter=interpreters.Count==1?interpreters[0]:null,console_helpers=consoles.ToArray()};
    }
    public Ownership Bind(IntPtr job,int supervisorPid,int serverPid) {
        BindingStage="redirector_identity";LastJobMembers=null;LastCandidate=null;LastProof=null;
        Require(Same(initial,Read(Redirector)),"redirector_identity_changed");
        BindingStage="redirector_job";Member(Redirector,job);
        var rows=Observe(job,serverPid);var members=LastJobMembers;
        var memberSet=new HashSet<int>(members);var opened=new Dictionary<int,Process>();
        foreach(Observation record in observations)if(memberSet.Contains(record.pid))opened.Add(record.pid,record.process);
        {
            BindingStage="candidate_constraints";
            Roles roles=AccountMembers(initial,rows,ConsoleHostPath,delegate(Identity value,string role) {
                Process process=opened[value.pid];
                if(role=="console_helper") {
                    Helper existing=helpers.Find(delegate(Helper h){return h.identity.pid==value.pid;});
                    if(existing!=null)Require(Same(existing.identity,value) && Same(existing.identity,Read(existing.process)),"console_helper_identity_changed");
                    else {Require(helpers.Count==0,"console_helper_identity_changed");helpers.Add(new Helper {identity=value,process=process});opened.Remove(value.pid);}
                } else {
                    if(Interpreter!=null)Require(Same(InterpreterIdentity,value) && Same(InterpreterIdentity,Read(Interpreter)),"interpreter_identity_changed");
                    else {InterpreterIdentity=value;Interpreter=process;opened.Remove(value.pid);}
                }
            });
            Require(helpers.Count==roles.console_helpers.Length,"console_helper_identity_changed");
            if(roles.interpreter==null) {Require(Interpreter==null,"interpreter_identity_changed");BindingStage="interpreter_pending";return null;}
            BindingStage="supervisor_identity";
            using(Process supervisor=Process.GetProcessById(supervisorPid)) {
                Identity parent=Read(supervisor);
                Require(initial.parent_pid==parent.pid && parent.created<=initial.created,"supervisor_identity_mismatch");
                BindingStage="complete_proof";
                Member(Interpreter,job);
                var helperProof=new List<Identity>();
                foreach(Helper helper in helpers) {Member(helper.process,job);Identity current=Read(helper.process);Require(Same(helper.identity,current),"console_helper_identity_changed");helperProof.Add(current);}
                Require(Same(initial,Read(Redirector)) && Same(InterpreterIdentity,Read(Interpreter)),"interpreter_identity_changed");
                var freshMembers=new HashSet<int>(Members(job));
                if(!freshMembers.SetEquals(memberSet)) {BindingStage="job_members_changed";return null;}
                LastProof=new Ownership {supervisor=parent,redirector=Read(Redirector),interpreter=Read(Interpreter),console_helpers=helperProof.ToArray(),job_verified_pids=members,job_membership_verified=true,server_pid=serverPid};
                BindingStage="bound";
                return LastProof;
            }
        }
    }
    public static ContractPython Start(IntPtr job,string executable,string arguments,string stdout,string stderr) {
        Require(String.Equals(executable,@"C:\ResolenaExperiments\uc001-validator-env\Scripts\python.exe",StringComparison.OrdinalIgnoreCase),"redirector_path_mismatch");
        Security security=new Security {Length=Marshal.SizeOf(typeof(Security)),Inherit=1};
        IntPtr input=IntPtr.Zero,write=IntPtr.Zero,list=IntPtr.Zero,handles=IntPtr.Zero,environment=IntPtr.Zero;
        Created created=new Created(); bool initialized=false,started=false,processCreated=false; ContractPython launch=null;
        using(FileStream output=new FileStream(stdout,FileMode.CreateNew,FileAccess.Write,FileShare.ReadWrite))
        using(FileStream error=new FileStream(stderr,FileMode.CreateNew,FileAccess.Write,FileShare.ReadWrite)) {
            try {
                Require(CreatePipe(out input,out write,ref security,0) && SetHandleInformation(write,1,0),"stdin_pipe_failed");
                IntPtr outHandle=output.SafeFileHandle.DangerousGetHandle(),errHandle=error.SafeFileHandle.DangerousGetHandle();
                Require(SetHandleInformation(outHandle,1,1) && SetHandleInformation(errHandle,1,1),"stdio_handles_failed");
                IntPtr size=IntPtr.Zero;InitializeProcThreadAttributeList(IntPtr.Zero,1,0,ref size);
                Require(size!=IntPtr.Zero,"handle_list_failed");list=Marshal.AllocHGlobal(size);
                Require(InitializeProcThreadAttributeList(list,1,0,ref size),"handle_list_failed");initialized=true;
                handles=Marshal.AllocHGlobal(IntPtr.Size*3);Marshal.WriteIntPtr(handles,0,input);Marshal.WriteIntPtr(handles,IntPtr.Size,outHandle);Marshal.WriteIntPtr(handles,IntPtr.Size*2,errHandle);
                Require(UpdateProcThreadAttribute(list,0,(IntPtr)0x20002,handles,(IntPtr)(IntPtr.Size*3),IntPtr.Zero,IntPtr.Zero),"handle_list_failed");
                var variables=new SortedDictionary<string,string>(StringComparer.OrdinalIgnoreCase);
                foreach(DictionaryEntry entry in Environment.GetEnvironmentVariables()) {
                    string name=(string)entry.Key;
                    if(!name.StartsWith("LLAMA_",StringComparison.OrdinalIgnoreCase) && !name.StartsWith("HF_",StringComparison.OrdinalIgnoreCase) && !name.StartsWith("VK_",StringComparison.OrdinalIgnoreCase))variables[name]=(string)entry.Value;
                }
                var block=new StringBuilder();foreach(var entry in variables)block.Append(entry.Key).Append('=').Append(entry.Value).Append('\0');block.Append('\0');
                environment=Marshal.StringToHGlobalUni(block.ToString());
                StartupEx startup=new StartupEx();startup.Startup.Size=Marshal.SizeOf(startup);startup.Startup.Flags=0x100;
                startup.Startup.Input=input;startup.Startup.Output=outHandle;startup.Startup.Error=errHandle;startup.Attributes=list;
                processCreated=CreateProcessW(executable,new StringBuilder('"'+executable+'"'+" "+arguments),IntPtr.Zero,IntPtr.Zero,true,0x08080404,environment,Path.GetDirectoryName(executable),ref startup,out created);
                Require(processCreated,"create_suspended_failed");
                // Assignment precedes the first instruction, so redirected children inherit this exact job.
                Require(AssignProcessToJobObject(job,created.Process),"job_assignment_failed");
                Process process=Process.GetProcessById(created.Pid);var held=process.Handle;
                launch=new ContractPython {ownedJob=job,Redirector=process,StandardInput=new StreamWriter(new FileStream(new SafeFileHandle(write,true),FileAccess.Write),new UTF8Encoding(false))};
                write=IntPtr.Zero;launch.initial=Read(process);
                Require(ResumeThread(created.Thread)==1,"resume_failed");started=true;
                return launch;
            } finally {
                bool cleanupFailed=false;
                if(!started && processCreated && WaitForSingleObject(created.Process,0)!=0) {cleanupFailed=!(TerminateProcess(created.Process,1) && WaitForSingleObject(created.Process,5000)==0);}
                if(!started && launch!=null) {try {launch.Dispose();}catch {cleanupFailed=true;}}
                if(processCreated) {CloseHandle(created.Thread);CloseHandle(created.Process);}
                if(input!=IntPtr.Zero)CloseHandle(input);if(write!=IntPtr.Zero)CloseHandle(write);
                if(initialized)DeleteProcThreadAttributeList(list);if(list!=IntPtr.Zero)Marshal.FreeHGlobal(list);
                if(handles!=IntPtr.Zero)Marshal.FreeHGlobal(handles);if(environment!=IntPtr.Zero)Marshal.FreeHGlobal(environment);
                Require(!cleanupFailed,"suspended_cleanup_unconfirmed");
            }
        }
    }
    public void Dispose() {if(StandardInput!=null)StandardInput.Dispose();if(Redirector!=null)Redirector.Dispose();}
}
