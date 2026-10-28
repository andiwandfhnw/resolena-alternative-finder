using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
namespace Uc001PreflightAssociationV110 {
    [StructLayout(LayoutKind.Sequential)] public struct Luid { public uint Low; public int High; }
    [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)] public struct Desc1 {
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst=128)] public string Description;
        public uint Vendor, Device, Subsystem, Revision;
        public UIntPtr DedicatedVideo, DedicatedSystem, SharedSystem;
        public Luid Id; public uint Flags;
    }
    public class Adapter {
        public string Status="ok", Error, Description, CounterKey;
        public uint Index, Vendor, Device, Subsystem, Revision, Flags;
        public ulong DedicatedBytes;
    }
    public class Scan {
        public string Status="ok", Error;
        public List<Adapter> Adapters=new List<Adapter>();
    }
    public static class Reader {
        [DllImport("dxgi.dll", ExactSpelling=true)] static extern int CreateDXGIFactory1(ref Guid id, out IntPtr factory);
        [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int EnumAdapters1(IntPtr self, uint index, out IntPtr adapter);
        [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int GetDesc1(IntPtr self, out Desc1 description);
        static Delegate Method(IntPtr self, int slot, Type type) {
            return Marshal.GetDelegateForFunctionPointer(Marshal.ReadIntPtr(Marshal.ReadIntPtr(self),slot*IntPtr.Size),type);
        }
        static string Error(string operation, int hr) { return operation+": HRESULT 0x"+unchecked((uint)hr).ToString("X8"); }
        public static Adapter Describe(Desc1 d, uint index) {
            return new Adapter { Index=index, Description=d.Description, Vendor=d.Vendor, Device=d.Device,
                Subsystem=d.Subsystem, Revision=d.Revision, Flags=d.Flags, DedicatedBytes=d.DedicatedVideo.ToUInt64(),
                CounterKey=String.Format("luid_0x{0:X8}_0x{1:X8}",unchecked((uint)d.Id.High),d.Id.Low) };
        }
        public static Scan Read() {
            Scan scan=new Scan(); IntPtr factory=IntPtr.Zero;
            try {
                Guid id=new Guid("770aae78-f26f-4dba-a829-253c83d1b387");
                int hr=CreateDXGIFactory1(ref id,out factory);
                if(hr!=0 || factory==IntPtr.Zero) throw new InvalidOperationException(Error("CreateDXGIFactory1",hr));
                EnumAdapters1 enumerate=(EnumAdapters1)Method(factory,12,typeof(EnumAdapters1));
                for(uint index=0;;index++) {
                    IntPtr adapter; hr=enumerate(factory,index,out adapter);
                    if(hr==unchecked((int)0x887A0002)) break;
                    if(hr!=0 || adapter==IntPtr.Zero) throw new InvalidOperationException(Error("EnumAdapters1",hr));
                    try {
                        Desc1 description;
                        GetDesc1 get=(GetDesc1)Method(adapter,10,typeof(GetDesc1));
                        hr=get(adapter,out description);
                        if(hr!=0) {
                            scan.Status="partial";
                            scan.Adapters.Add(new Adapter {Index=index,Status="failed",Error=Error("GetDesc1",hr)});
                        } else { scan.Adapters.Add(Describe(description,index)); }
                    } finally { Marshal.Release(adapter); }
                }
            } catch(Exception error) { scan.Status="failed"; scan.Error=error.ToString(); }
            finally { if(factory!=IntPtr.Zero) Marshal.Release(factory); }
            return scan;
        }
    }
}
