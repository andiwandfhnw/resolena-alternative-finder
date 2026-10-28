$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$path = Join-Path $PSScriptRoot 'Diagnose-Capacity.ps1'
if (-not (Test-Path -LiteralPath $path)) { throw 'Capacity diagnostic is absent (RED).' }
$tokens=$null; $errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($path,[ref]$tokens,[ref]$errors)
if ($errors.Count) { throw $errors[0] }
foreach ($definition in $ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst]},$true)) {
    Invoke-Expression $definition.Extent.Text
}
function Assert-CapacityEnvironment {}
$script:case='normal'
function Get-CimInstance {
    if($script:case -eq 'cim_failure'){throw 'Synthetic CIM query failure'}
    if($script:case -eq 'cim_missing'){return}
    $item=[pscustomobject]@{Name='AMD Radeon RX 6800 XT';PNPDeviceID='PCI\VEN_1002&DEV_73BF&SUBSYS_12341002&REV_C1\synthetic'}
    if($script:case -eq 'bad_pnp'){$item.PNPDeviceID='unresolved'}
    $item
    if($script:case -eq 'cim_duplicate'){$item}
}
function Get-ItemProperty($LiteralPath) {
    if($LiteralPath -like '*\Enum\*') {return [pscustomobject]@{Driver='{4d36e968-e325-11ce-bfc1-08002be10318}\0000'}}
    if($script:case -eq 'registry_failure'){throw 'Synthetic registry query failure'}
    if($script:case -eq 'registry_missing'){return [pscustomobject]@{Other=1}}
    $value=[long]900
    switch($script:case) {
        'zero' {$value=[long]0}
        'maximum_positive' {$value=[long]0}
        'maximum_negative' {$value=[uint64]::MaxValue}
        'binary' {$value=[BitConverter]::GetBytes([uint64]900)}
        'null' {$value=$null}
        'invalid_type' {$value='900'}
        'negative' {$value=[long]-1}
    }
    [pscustomobject]@{'HardwareInformation.qwMemorySize'=$value}
}
function Read-CapacityDxgi {
    if($script:case -eq 'dxgi_failure'){throw 'Synthetic native query failure'}
    $adapter=[pscustomobject]@{Status='ok';Error=$null;Description='AMD Radeon RX 6800 XT';Vendor=[uint32]0x1002;Device=[uint32]0x73BF
        Subsystem=[uint32]0x12341002;Revision=[uint32]0xC1;Flags=[uint32]0;CounterKey='luid_0x00000000_0x0000000A';DedicatedBytes=[uint64]1000}
    switch($script:case) {
        'zero' {$adapter.DedicatedBytes=[uint64]0}
        'maximum_positive' {$adapter.DedicatedBytes=[uint64]::MaxValue}
        'maximum_negative' {$adapter.DedicatedBytes=[uint64]0}
        'wrong_pci' {$adapter.Subsystem=[uint32]1}
        'software' {$adapter.Flags=[uint32]2}
    }
    $rows=@($adapter)
    if($script:case -eq 'dxgi_missing'){$rows=@()}
    if($script:case -eq 'dxgi_duplicate'){$rows=@($adapter,$adapter)}
    [pscustomobject]@{Status=$(if($script:case -eq 'dxgi_partial'){'partial'}else{'ok'});Error=$null;Adapters=$rows}
}
function Get-ReadOnlyContractAdapter {throw 'Forbidden equality guard invoked'}
function Assert-ContractResources {throw 'Forbidden resource acceptance invoked'}
function Get-ContractAssets {throw 'Forbidden asset hashing invoked'}
function Require($condition,$message) {if(-not $condition){throw $message}}
$cases=@('normal','zero','maximum_positive','maximum_negative','binary','registry_missing','registry_failure','null','invalid_type','negative',
    'cim_failure','cim_missing','cim_duplicate','bad_pnp','dxgi_failure','dxgi_missing','dxgi_duplicate','dxgi_partial','wrong_pci','software')
foreach($script:case in $cases) {
    $report=Get-CapacityDiagnostic 'synthetic-unused-directory'
    switch($script:case) {
        'normal' {Require ($report.difference.bytes -eq '100' -and $report.registry.capacity.raw_type -eq 'System.Int64' -and $report.dxgi.capacity.raw_type -eq 'System.UInt64') 'Wrong exact comparison/types'}
        'zero' {Require ($report.difference.bytes -eq '0') 'Measured zero was substituted'}
        'maximum_positive' {Require ($report.difference.bytes -eq '18446744073709551615') 'Positive difference overflow'}
        'maximum_negative' {Require ($report.difference.bytes -eq '-18446744073709551615') 'Negative difference overflow'}
        'binary' {Require ($report.difference.bytes -eq '100' -and $report.registry.capacity.raw_type -eq 'System.Byte[]' -and $report.registry.capacity.raw_value.Count -eq 8) 'Binary raw data lost'}
        'registry_missing' {Require ($report.registry.capacity.state -eq 'missing' -and $report.dxgi.capacity.state -eq 'ok') 'Missing registry value conflated with DXGI failure'}
        'registry_failure' {Require ($report.registry.state -eq 'query_failed' -and $report.dxgi.capacity.state -eq 'ok') 'Registry failure concealed fresh DXGI data'}
        'null' {Require ($report.registry.capacity.state -eq 'unavailable') 'Null became a measurement'}
        'invalid_type' {Require ($report.registry.capacity.state -eq 'invalid_type') 'String became a measurement'}
        'negative' {Require ($report.registry.capacity.state -eq 'invalid_value' -and $report.registry.capacity.raw_value -eq -1) 'Negative raw value not preserved'}
        'cim_failure' {Require ($report.cim.state -eq 'query_failed') 'CIM failure state lost'}
        'cim_missing' {Require ($report.cim.state -eq 'missing') 'Missing CIM state lost'}
        'cim_duplicate' {Require ($report.cim.state -eq 'ambiguous') 'Ambiguous CIM state lost'}
        'bad_pnp' {Require ($report.cim.state -eq 'invalid_identity') 'Invalid PNP state lost'}
        'dxgi_failure' {Require ($report.dxgi.state -eq 'query_failed') 'Native failure state lost'}
        'dxgi_missing' {Require ($report.dxgi.state -eq 'missing') 'Missing native adapter state lost'}
        'dxgi_duplicate' {Require ($report.dxgi.state -eq 'ambiguous') 'Duplicate native adapter state lost'}
        'dxgi_partial' {Require ($report.dxgi.state -eq 'query_failed') 'Partial query accepted'}
        default {Require ($report.dxgi.state -eq 'missing') 'Mismatched/software identity accepted'}
    }
    if($script:case -notin @('normal','zero','maximum_positive','maximum_negative','binary')) {
        Require ($report.difference.state -eq 'unavailable' -and $null -eq $report.difference.bytes) 'Unavailable data produced a difference'
    }
}
$reader=Join-Path (Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent) 'scripts/uc001_preflight_association_v1_1_0/AdapterIdentity.cs'
Add-Type -Path $reader
$desc=New-Object Uc001PreflightAssociationV110.Desc1
Require ([Runtime.InteropServices.Marshal]::SizeOf($desc) -eq 312) 'Wrong x64 size'
foreach($field in @{Vendor=256;Device=260;Subsystem=264;Revision=268;DedicatedVideo=272;DedicatedSystem=280;SharedSystem=288;Id=296;Flags=304}.GetEnumerator()) {
    Require ([Runtime.InteropServices.Marshal]::OffsetOf($desc.GetType(),$field.Key).ToInt32() -eq $field.Value) ('Wrong offset '+$field.Key)
}
$desc.DedicatedVideo=New-Object UIntPtr -ArgumentList ([uint64]::MaxValue)
Require ([Uc001PreflightAssociationV110.Reader]::Describe($desc,0).DedicatedBytes -eq [uint64]::MaxValue) 'Unsigned capacity conversion truncated'
Write-Output ('PASS '+$cases.Count+' synthetic cases; x64 layout and unsigned conversion; no native reader called')
