[CmdletBinding()]
param()

$script:IdentityNativeSource = @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
namespace Uc001IdentityDiagnostic {
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
                Subsystem=d.Subsystem, Revision=d.Revision, Flags=d.Flags,
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
'@

function Read-IdentityField($Object, $Name) {
    $property=$Object.PSObject.Properties[$Name]
    if($null -eq $property){return @{status='missing_property';value=$null}}
    if($null -eq $property.Value){return @{status='null_value';value=$null}}
    return @{status='present';type=$property.Value.GetType().FullName;value=$property.Value}
}

function New-IdentityReport($Scan, $Counters, $WddmState, $WddmError) {
    $adapters=@($Scan.Adapters | ForEach-Object {$_})
    $valid=@($adapters | Where-Object {$_.Status -eq 'ok'})
    $counterRows=@(foreach($c in $Counters) {
        [pscustomobject]@{Name=(Read-IdentityField $c 'Name');DedicatedUsage=(Read-IdentityField $c 'DedicatedUsage')}
    })
    $rows=@(foreach($a in $adapters) {
        if($a.Status -ne 'ok') {
            [pscustomobject]@{enumeration_index=$a.Index;identity_state='query_failed';error=$a.Error}
            continue
        }
        $expected=$a.CounterKey+'_phys_0'
        $same=@($valid | Where-Object {[string]::Equals($_.CounterKey,$a.CounterKey,[StringComparison]::OrdinalIgnoreCase)})
        $matches=@($counterRows | Where-Object {[string]::Equals($_.Name.value,$expected,[StringComparison]::OrdinalIgnoreCase)})
        $state=if($WddmState -ne 'ok'){'query_failed'}elseif($matches.Count -eq 0){'missing'}elseif($matches.Count -eq 1){'single'}else{'ambiguous'}
        [pscustomobject]@{
            enumeration_index=$a.Index;description=$a.Description
            identifiers=@{kind=$(if($a.Vendor -le 65535){'PCI'}else{'ACPI'});vendor_id=('0x{0:X4}' -f $a.Vendor)
                device_id=('0x{0:X4}' -f $a.Device);subsystem_id=('0x{0:X8}' -f $a.Subsystem);revision=('0x{0:X2}' -f $a.Revision)}
            flags=('0x{0:X8}' -f $a.Flags);classification=$(if(($a.Flags -band 2) -ne 0){'software'}else{'hardware'})
            luid=$a.CounterKey;identity_matches=$same.Count;identity_state=$(if($same.Count -eq 1){'single'}else{'ambiguous'})
            expected_counter_name=$expected;counter_state=$state;counter_matches=$matches
        }
    })
    $expectedNames=@($valid | ForEach-Object {$_.CounterKey+'_phys_0'})
    $unmatched=@($counterRows | Where-Object {$_.Name.status -ne 'present' -or $_.Name.value -notin $expectedNames})
    return [pscustomobject]@{
        dxgi_state=$(if($Scan.Status -eq 'ok' -and $adapters.Count -eq 0){'none'}else{$Scan.Status});dxgi_error=$Scan.Error
        wddm_state=$WddmState;wddm_error=$WddmError;adapters=$rows;wddm_instances=$counterRows;unmatched_counters=$unmatched
    }
}

function Invoke-IdentityDiagnostic {
    $started=[DateTime]::UtcNow.ToString('o')
    try {
        Add-Type -TypeDefinition $script:IdentityNativeSource -ErrorAction Stop
        $scan=[Uc001IdentityDiagnostic.Reader]::Read()
    } catch { $scan=[pscustomobject]@{Status='failed';Error=$_.Exception.ToString();Adapters=@()} }
    $counterTime=[DateTime]::UtcNow.ToString('o')
    $counters=@();$state='ok';$errorText=$null
    try { $counters=@(Get-CimInstance Win32_PerfRawData_GPUPerformanceCounters_GPUAdapterMemory -ErrorAction Stop) }
    catch { $state='failed';$errorText=$_.Exception.ToString() }
    $report=New-IdentityReport $scan $counters $state $errorText
    $report | Add-Member NoteProperty dxgi_started_utc $started
    $report | Add-Member NoteProperty wddm_started_utc $counterTime
    $report | ConvertTo-Json -Depth 10
}

if($MyInvocation.InvocationName -ne '.') {
    if($PSVersionTable.PSEdition -ne 'Desktop' -or $PSVersionTable.PSVersion -lt [version]'5.1' -or -not [Environment]::Is64BitProcess) {
        throw 'Use existing 64-bit Windows PowerShell 5.1. Do not install or change execution policy for this diagnostic.'
    }
    Invoke-IdentityDiagnostic
}
