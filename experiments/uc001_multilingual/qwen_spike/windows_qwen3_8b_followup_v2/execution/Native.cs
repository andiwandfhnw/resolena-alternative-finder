using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Diagnostics;
using System.IO;
using System.Text;

public static class ResolenaDxgi {
    [StructLayout(LayoutKind.Sequential)] public struct Luid {
        public uint Low; public int High;
    }
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    struct Description {
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)] public string Name;
        public uint Vendor, Device, Subsystem, Revision;
        public UIntPtr DedicatedVideo, DedicatedSystem, SharedSystem;
        public Luid Id;
    }
    public class Adapter {
        public string Name, CounterKey;
        public uint Vendor;
        public ulong DedicatedBytes;
    }
    [DllImport("dxgi.dll")] static extern int CreateDXGIFactory(ref Guid id, out IntPtr factory);
    [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int EnumAdapter(IntPtr self, uint index, out IntPtr adapter);
    [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int GetDescription(IntPtr self, out Description description);
    static Delegate Method(IntPtr instance, int index, Type type) {
        IntPtr table = Marshal.ReadIntPtr(instance);
        return Marshal.GetDelegateForFunctionPointer(Marshal.ReadIntPtr(table, index * IntPtr.Size), type);
    }
    public static Adapter[] ReadAdapters() {
        Guid id = new Guid("7b7166ec-21c7-44ae-b21a-c9ae321ae369");
        IntPtr factory;
        Marshal.ThrowExceptionForHR(CreateDXGIFactory(ref id, out factory));
        List<Adapter> adapters = new List<Adapter>();
        try {
            EnumAdapter enumerate = (EnumAdapter)Method(factory, 7, typeof(EnumAdapter));
            for (uint index = 0; index < 32; index++) {
                IntPtr adapter;
                int result = enumerate(factory, index, out adapter);
                if (result == unchecked((int)0x887A0002)) break;
                Marshal.ThrowExceptionForHR(result);
                try {
                    Description description;
                    GetDescription get = (GetDescription)Method(adapter, 8, typeof(GetDescription));
                    Marshal.ThrowExceptionForHR(get(adapter, out description));
                    adapters.Add(new Adapter {
                        Name = description.Name, Vendor = description.Vendor,
                        DedicatedBytes = description.DedicatedVideo.ToUInt64(),
                        CounterKey = String.Format("luid_0x{0:X8}_0x{1:X8}", unchecked((uint)description.Id.High), description.Id.Low)
                    });
                } finally { Marshal.Release(adapter); }
            }
        } finally { Marshal.Release(factory); }
        return adapters.ToArray();
    }
}

public static class ResolenaProcess {
    static object logLock = new object();
    public static Process Start(string executable, string arguments, string stdout, string stderr) {
        if (File.Exists(stdout) || File.Exists(stderr)) throw new IOException("Preserved process logs already exist");
        File.WriteAllText(stdout, "", new UTF8Encoding(false));
        File.WriteAllText(stderr, "", new UTF8Encoding(false));
        ProcessStartInfo info = new ProcessStartInfo(executable, arguments);
        info.UseShellExecute = false; info.CreateNoWindow = true;
        info.RedirectStandardOutput = true; info.RedirectStandardError = true;
        info.WorkingDirectory = Path.GetDirectoryName(executable);
        info.StandardOutputEncoding = Encoding.UTF8; info.StandardErrorEncoding = Encoding.UTF8;
        List<string> remove = new List<string>();
        foreach (string key in info.EnvironmentVariables.Keys) {
            if (key.StartsWith("LLAMA_", StringComparison.OrdinalIgnoreCase) ||
                key.StartsWith("HF_", StringComparison.OrdinalIgnoreCase) ||
                key.StartsWith("VK_", StringComparison.OrdinalIgnoreCase)) remove.Add(key);
        }
        foreach (string key in remove) info.EnvironmentVariables.Remove(key);
        Process process = new Process(); process.StartInfo = info;
        process.OutputDataReceived += delegate(object sender, DataReceivedEventArgs e) {
            if (e.Data != null) lock(logLock) File.AppendAllText(stdout, e.Data + "\n", new UTF8Encoding(false));
        };
        process.ErrorDataReceived += delegate(object sender, DataReceivedEventArgs e) {
            if (e.Data != null) lock(logLock) File.AppendAllText(stderr, e.Data + "\n", new UTF8Encoding(false));
        };
        process.Start(); process.BeginOutputReadLine(); process.BeginErrorReadLine();
        return process;
    }
}
