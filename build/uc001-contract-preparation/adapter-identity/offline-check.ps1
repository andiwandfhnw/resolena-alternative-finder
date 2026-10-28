$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$path = Join-Path $PSScriptRoot 'Diagnose-DxgiWddmIdentity.ps1'
$tokens=$null; $errors=$null
$null=[System.Management.Automation.Language.Parser]::ParseFile($path,[ref]$tokens,[ref]$errors)
if($errors.Count){throw ($errors|Out-String)}
. $path
Add-Type -TypeDefinition $script:IdentityNativeSource -ErrorAction Stop
$desc=[Uc001IdentityDiagnostic.Desc1]
if([Runtime.InteropServices.Marshal]::SizeOf((New-Object Uc001IdentityDiagnostic.Desc1)) -ne 312 -or
    [Runtime.InteropServices.Marshal]::OffsetOf($desc,'Flags').ToInt32() -ne 304 -or
    [Runtime.InteropServices.Marshal]::OffsetOf($desc,'Id').ToInt32() -ne 296) {throw 'Unexpected x64 DXGI_ADAPTER_DESC1 layout'}
$mapped=[Uc001IdentityDiagnostic.Reader]::Describe((New-Object Uc001IdentityDiagnostic.Desc1 -Property @{
    Description='Synthetic hardware';Vendor=0x1002;Device=0x1234;Subsystem=0x56781234;Revision=1
    Id=(New-Object Uc001IdentityDiagnostic.Luid -Property @{Low=10;High=-1});Flags=0
}),0)
if($mapped.CounterKey -ne 'luid_0xFFFFFFFF_0x0000000A'){throw 'Signed high LUID formatting changed'}
function Adapter($key,$flags=0) {
    [pscustomobject]@{Status='ok';Error=$null;Index=0;Description='Synthetic';Vendor=4098;Device=1;Subsystem=2;Revision=3;Flags=$flags;CounterKey=$key}
}
function Scan($rows,$status='ok') { [pscustomobject]@{Status=$status;Error=$null;Adapters=@($rows)} }
function Check($condition,$message) {if(-not $condition){throw $message}}
$a='luid_0x00000000_0x0000000A';$b='luid_0x00000000_0x0000000B'
$counters=@([pscustomobject]@{Name=($a+'_phys_0');DedicatedUsage=[uint64]0},[pscustomobject]@{Name=($b+'_phys_0');DedicatedUsage=[uint64]99})
$scan=Scan @((Adapter $a),(Adapter $b 2))
$r=New-IdentityReport $scan $counters 'ok' $null
Check ($r.adapters.Count -eq 2) 'Adapters were selected or discarded'
Check ($r.adapters[0].classification -eq 'hardware' -and $r.adapters[1].classification -eq 'software') 'Classification must use flag 2'
Check ($r.adapters[0].counter_matches[0].DedicatedUsage.value -eq 0) 'Zero usage was treated as missing or used to select a different adapter'
Check ($r.adapters[1].counter_matches[0].DedicatedUsage.value -eq 99) 'Exact LUID association was lost'
Check ($r.adapters[0].identity_matches -eq 1 -and $r.adapters[0].counter_state -eq 'single') 'Unique identity state missing'
Write-Output 'PASS: both hardware/software identities, exact LUID matches and zero/nonzero values retained'
$r=New-IdentityReport (Scan @((Adapter $a))) @([pscustomobject]@{Name=($a+'1_phys_0');DedicatedUsage=99}) 'ok' $null
Check ($r.adapters[0].counter_state -eq 'missing' -and $r.unmatched_counters.Count -eq 1) 'Prefix lookalike incorrectly matched'
$r=New-IdentityReport (Scan @((Adapter $a))) @() 'ok' $null
Check ($r.adapters[0].counter_state -eq 'missing') 'Zero counter state lost'
$r=New-IdentityReport (Scan @()) $counters 'ok' $null
Check ($r.dxgi_state -eq 'none' -and $r.unmatched_counters.Count -eq 2) 'Missing DXGI adapters hidden'
Write-Output 'PASS: exact full-name match, no counter and no adapter remain distinct'
$duplicate=@($counters[0],$counters[0])
$r=New-IdentityReport (Scan @((Adapter $a))) $duplicate 'ok' $null
Check ($r.adapters[0].counter_state -eq 'ambiguous' -and $r.adapters[0].counter_matches.Count -eq 2) 'Duplicate counters were collapsed'
$r=New-IdentityReport (Scan @((Adapter $a),(Adapter $a))) $counters 'ok' $null
Check ($r.adapters[0].identity_matches -eq 2 -and $r.adapters[0].identity_state -eq 'ambiguous') 'Duplicate DXGI identities hidden'
$r=New-IdentityReport (Scan @((Adapter $a))) @([pscustomobject]@{Name=($a+'_phys_1');DedicatedUsage=1}) 'ok' $null
Check ($r.adapters[0].counter_state -eq 'missing' -and $r.unmatched_counters.Count -eq 1) 'Unexpected physical index silently treated as phys_0'
Write-Output 'PASS: ambiguous counters/identities and unmatched physical index preserved'
foreach($usage in @([pscustomobject]@{Name=($a+'_phys_0')},[pscustomobject]@{Name=($a+'_phys_0');DedicatedUsage=$null})) {
    $r=New-IdentityReport (Scan @((Adapter $a))) @($usage) 'ok' $null
    Check ($r.adapters[0].counter_matches[0].DedicatedUsage.status -ne 'present') 'Unavailable measurement became zero'
}
$r=New-IdentityReport (Scan @((Adapter $a))) @() 'failed' 'Synthetic query failure'
Check ($r.adapters[0].counter_state -eq 'query_failed' -and $r.wddm_error -eq 'Synthetic query failure') 'WDDM failure relabelled as missing'
$r=New-IdentityReport (Scan @() 'failed') $counters 'ok' $null
Check ($r.dxgi_state -eq 'failed' -and $r.unmatched_counters.Count -eq 2) 'DXGI failure relabelled as no adapters'
$failed=[pscustomobject]@{Status='failed';Error='Synthetic GetDesc1 failure';Index=0}
$r=New-IdentityReport (Scan @($failed) 'partial') $counters 'ok' $null
Check ($r.adapters[0].identity_state -eq 'query_failed' -and $r.dxgi_state -eq 'partial') 'Per-adapter description failure hidden'
Write-Output 'PASS: missing/null usage and global/per-adapter query failure states preserved'
Write-Output 'PASS: PowerShell syntax, C# compilation and x64 layout; no native calls or Windows queries executed'
