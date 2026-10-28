using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;

public static class ContractProcesses {
    [StructLayout(LayoutKind.Sequential)] struct Basic {
        public long ProcessTime, JobTime; public uint Flags;
        public UIntPtr Minimum, Maximum; public uint Active;
        public UIntPtr Affinity; public uint Priority, Scheduling;
    }
    [StructLayout(LayoutKind.Sequential)] struct Counters {
        public ulong ReadOps, WriteOps, OtherOps, ReadBytes, WriteBytes, OtherBytes;
    }
    [StructLayout(LayoutKind.Sequential)] struct Extended {
        public Basic Basic; public Counters Io;
        public UIntPtr ProcessMemory, JobMemory, PeakProcess, PeakJob;
    }
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode)] static extern IntPtr CreateJobObject(IntPtr attributes, string name);
    [DllImport("kernel32.dll")] static extern bool SetInformationJobObject(IntPtr job, int kind, IntPtr data, uint length);
    [DllImport("kernel32.dll")] static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);
    [DllImport("kernel32.dll")] public static extern bool CloseHandle(IntPtr handle);
    public static IntPtr NewJob() {
        IntPtr job = CreateJobObject(IntPtr.Zero, null);
        if (job == IntPtr.Zero) throw new IOException("Cannot create owned process job");
        Extended value = new Extended(); value.Basic.Flags = 0x2000; // kill owned subtree when handle closes
        int length = Marshal.SizeOf(value); IntPtr data = Marshal.AllocHGlobal(length);
        try {
            Marshal.StructureToPtr(value, data, false);
            if (!SetInformationJobObject(job, 9, data, (uint)length)) { CloseHandle(job); throw new IOException("Cannot enforce process cleanup"); }
        } finally { Marshal.FreeHGlobal(data); }
        return job;
    }
    static object sync = new object();
    public static Process Start(IntPtr job, string executable, string arguments, string stdout, string stderr, string key) {
        if (File.Exists(stdout) || File.Exists(stderr)) throw new IOException("Preserved logs already exist");
        File.WriteAllText(stdout, ""); File.WriteAllText(stderr, "");
        ProcessStartInfo info = new ProcessStartInfo(executable, arguments);
        info.UseShellExecute = false; info.CreateNoWindow = true;
        info.RedirectStandardOutput = true; info.RedirectStandardError = true; info.RedirectStandardInput = true;
        info.WorkingDirectory = Path.GetDirectoryName(executable);
        var remove = new System.Collections.Generic.List<string>();
        foreach (string name in info.EnvironmentVariables.Keys) {
            if (name.StartsWith("LLAMA_", StringComparison.OrdinalIgnoreCase) || name.StartsWith("HF_", StringComparison.OrdinalIgnoreCase) ||
                name.StartsWith("VK_", StringComparison.OrdinalIgnoreCase)) remove.Add(name);
        }
        foreach (string name in remove) info.EnvironmentVariables.Remove(name);
        if (key != null) info.EnvironmentVariables["LLAMA_API_KEY"] = key;
        Process process = new Process(); process.StartInfo = info;
        process.OutputDataReceived += (sender, e) => { if (e.Data != null) lock(sync) File.AppendAllText(stdout, e.Data + "\n", Encoding.UTF8); };
        process.ErrorDataReceived += (sender, e) => { if (e.Data != null) lock(sync) File.AppendAllText(stderr, e.Data + "\n", Encoding.UTF8); };
        process.Start();
        if (!AssignProcessToJobObject(job, process.Handle)) { process.Kill(); throw new IOException("Cannot assign owned process job"); }
        process.BeginOutputReadLine(); process.BeginErrorReadLine();
        return process;
    }
}
