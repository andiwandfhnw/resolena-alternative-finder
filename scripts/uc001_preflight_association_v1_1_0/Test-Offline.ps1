param([Parameter(Mandatory=$true)][string]$Case)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'Common.ps1')
$script:readCount=0
$script:capacity=16GB
$script:usage=[uint64]1GB
$script:key='luid_0x00000000_0x0000000A'
$script:softwareKey='luid_0x00000000_0x0000000B'
function Fixture-Adapter($key,$flags=0) {
    [pscustomobject]@{Status='ok';Error=$null;Description='AMD Radeon RX 6800 XT';Vendor=[uint32]0x1002;Device=[uint32]0x73BF
        Subsystem=[uint32]0x12341002;Revision=[uint32]0xC1;Flags=[uint32]$flags;CounterKey=$key;DedicatedBytes=[uint64]$script:capacity}
}
function Read-AssociationDxgi {
    $script:readCount++
    if($Case -eq 'failed_dxgi'){throw 'Synthetic DXGI failure'}
    $a=Fixture-Adapter $script:key
    $s=Fixture-Adapter $script:softwareKey 2
    $s.Description='Microsoft Basic Render Driver';$s.Vendor=[uint32]0x1414;$s.Device=[uint32]0x008C
    $rows=@($s,$a)
    switch($Case) {
        'fresh_luid' {$a.CounterKey=('luid_0x00000000_0x{0:X8}' -f $script:readCount)}
        'null_flags' {$a.Flags=$null}
        'invalid_flags' {$a.Flags='0'}
        'wrong_descriptor' {$a.Description='Different hardware'}
        'wrong_pci' {$a.Device=[uint32]1}
        'wrong_subsystem' {$a.Subsystem=[uint32]1}
        'wrong_revision' {$a.Revision=[uint32]1}
        'missing_dxgi' {$rows=@()}
        'duplicate_dxgi' {$rows=@($a,$a,$s)}
        'duplicate_luid' {$s.CounterKey=$a.CounterKey}
        'software_only' {$rows=@($s)}
        'software_impersonation' {$a.Flags=[uint32]2;$rows=@($a)}
        'capacity_mismatch' {$a.DedicatedBytes=[uint64]($script:capacity-1)}
    }
    [pscustomobject]@{Status=$(if($Case -eq 'partial_dxgi'){'partial'}else{'ok'});Error=$null;Adapters=$rows}
}
function Get-CimInstance($ClassName) {
    switch($ClassName) {
        'Win32_VideoController' {
            if($Case -eq 'failed_cim'){throw 'Synthetic CIM failure'}
            if($Case -eq 'missing_cim'){return}
            $a=[pscustomobject]@{Name='AMD Radeon RX 6800 XT';PNPDeviceID='PCI\VEN_1002&DEV_73BF&SUBSYS_12341002&REV_C1\synthetic'}
            if($Case -eq 'bad_pnp'){$a.PNPDeviceID='unresolved'}
            $a
            if($Case -eq 'duplicate_cim'){$a}
        }
        'Win32_PerfRawData_GPUPerformanceCounters_GPUAdapterMemory' {
            if($Case -eq 'failed_counter'){throw 'Synthetic WDDM failure'}
            if($Case -eq 'missing_counter'){return}
            $name=$script:key+'_phys_0'
            if($Case -eq 'fresh_luid'){$name=('luid_0x00000000_0x{0:X8}_phys_0' -f $script:readCount)}
            if($Case -eq 'counter_name_lookalike'){$name=$script:key+'1_phys_0'}
            if($Case -eq 'unexpected_physical_index'){$name=$script:key+'_phys_1'}
            $row=[pscustomobject]@{Name=$name;DedicatedUsage=$script:usage}
            if($Case -eq 'missing_usage'){$row=[pscustomobject]@{Name=$name}}
            if($Case -eq 'null_usage'){$row.DedicatedUsage=$null}
            if($Case -eq 'invalid_usage'){$row.DedicatedUsage='0'}
            if($Case -eq 'usage_over_capacity'){$row.DedicatedUsage=[uint64]($script:capacity+1)}
            if($Case -eq 'counter_order') {[pscustomobject]@{Name=($script:softwareKey+'_phys_0');DedicatedUsage=[uint64]0}}
            $row
            if($Case -eq 'duplicate_counter'){$row}
            if($Case -eq 'multiple_physical_counters'){[pscustomobject]@{Name=($script:key+'_phys_1');DedicatedUsage=[uint64]0}}
            if($Case -ne 'counter_order'){[pscustomobject]@{Name=($script:softwareKey+'_phys_0');DedicatedUsage=[uint64]0}}
        }
        'Win32_OperatingSystem' {[pscustomobject]@{FreePhysicalMemory=([long](24GB/1024));TotalVisibleMemorySize=([long](32GB/1024))}}
        default {throw ('Unexpected synthetic class '+$ClassName)}
    }
}
function Get-CimClass($ClassName) {[pscustomobject]@{CimClassProperties=@([pscustomobject]@{Name='DedicatedUsage'})}}
function Get-ItemProperty($LiteralPath) {
    if($Case -eq 'failed_registry'){throw 'Synthetic registry query failure'}
    if($LiteralPath -like '*\Enum\*') {
        if($Case -eq 'missing_driver'){return [pscustomobject]@{Other='synthetic'}}
        return [pscustomobject]@{Driver='{synthetic}\0000'}
    }
    if($Case -eq 'missing_registry' -or $Case -eq 'missing_capacity'){return [pscustomobject]@{Other='synthetic'}}
    [pscustomobject]@{'HardwareInformation.qwMemorySize'=$(if($Case -eq 'invalid_capacity'){'17179869184'}else{[long]$script:capacity})}
}
function Require($condition,$message) {if(-not $condition){throw $message}}
$success=@('hardware_and_software','counter_order','zero_usage','fresh_luid','headroom_below','headroom_exact','all_resource_limits','preflight_routing','native_layout')
if($Case -notin $success) {
    $rejected=$false
    try {$null=Get-ReadOnlyContractAdapter} catch {$rejected=$true}
    Require $rejected ('Failed to stop on '+$Case)
} else {
    if($Case -eq 'zero_usage'){$script:usage=[uint64]0}
    $adapter=Get-ReadOnlyContractAdapter
    Require ($adapter.Name -eq 'AMD Radeon RX 6800 XT') 'Wrong descriptor selected'
    Require ($script:readCount -eq 1) 'Fresh DXGI identity was not queried'
    if($Case -eq 'fresh_luid') {
        $again=Get-ReadOnlyContractAdapter
        Require ($script:readCount -eq 2 -and $adapter.CounterKey -ne $again.CounterKey) 'LUID was cached or hard-coded'
    } else {Require ($adapter.CounterKey -eq $script:key) 'Selected by order/usage instead of identity'}
    if($Case -eq 'zero_usage') {
        $sample=Get-ContractResources $adapter $PSScriptRoot
        Require ($sample.gpu_free -eq $script:capacity) 'Measured zero became unknown or was substituted'
    }
    if($Case -in @('headroom_below','headroom_exact','all_resource_limits')) {
        $limits=(Read-ContractJson (Join-Path $PSScriptRoot 'config.json')).limits
        $good=@{ram_free=24GB;gpu_free=14GB;disk_free=10GB;owned_gpu=1GB;owned_rss=1GB;artifact_bytes=0}
        if($Case -eq 'headroom_below') {
            $good.gpu_free=[long](13.651*1GB)
            $rejected=$false;try {Assert-ContractResources $good $limits $true} catch {$rejected=$true}
            Require $rejected 'Below-14-GiB start headroom incorrectly passed'
        } elseif($Case -eq 'headroom_exact') {Assert-ContractResources $good $limits $true}
        else {
            Assert-ContractResources $good $limits $true
            foreach($field in @('ram_free','gpu_free','disk_free','owned_gpu','owned_rss','artifact_bytes')) {
                $bad=$good.Clone();if($field -in @('ram_free','gpu_free','disk_free')){$bad[$field]=0}else{$bad[$field]=32GB}
                $rejected=$false;try {Assert-ContractResources $bad $limits} catch {$rejected=$true}
                Require $rejected ('Resource guard changed: '+$field)
            }
        }
    }
    if($Case -eq 'preflight_routing') {
        . (Join-Path $PSScriptRoot 'Preflight-Adapter.ps1')
        function Assert-ContractWindows {}
        function Assert-ContractBundle {}
        function Get-ContractAssets {throw 'Asset hashing must not be invoked'}
        function Read-ContractJson($Path) {
            $config=([IO.File]::ReadAllText($Path) | ConvertFrom-Json)
            $config.reuse_root=$PSScriptRoot
            return $config
        }
        $script:usage=[uint64](3GB)
        $report=Invoke-AdapterPreflight
        Require ($report.association -eq 'verified' -and $report.outcome -eq 'resource_guard_failed') 'Association and headroom were conflated'
    }
    if($Case -eq 'native_layout') {
        Add-Type -Path (Join-Path $PSScriptRoot 'AdapterIdentity.cs')
        $type=[Uc001PreflightAssociationV110.Desc1]
        Require ([Runtime.InteropServices.Marshal]::SizeOf((New-Object Uc001PreflightAssociationV110.Desc1)) -eq 312) 'Wrong x64 layout'
        Require ([Runtime.InteropServices.Marshal]::OffsetOf($type,'Flags').ToInt32() -eq 304) 'Wrong flags offset'
        Require ([Runtime.InteropServices.Marshal]::OffsetOf($type,'Id').ToInt32() -eq 296) 'Wrong LUID offset'
        $description=New-Object Uc001PreflightAssociationV110.Desc1 -Property @{
            Description='Synthetic';DedicatedVideo=(New-Object UIntPtr -ArgumentList ([uint64]16GB))
            Id=(New-Object Uc001PreflightAssociationV110.Luid -Property @{Low=10;High=-1})
        }
        $native=[Uc001PreflightAssociationV110.Reader]::Describe($description,0)
        Require ($native.CounterKey -eq 'luid_0xFFFFFFFF_0x0000000A' -and $native.DedicatedBytes -eq 16GB) 'Native LUID/capacity mapping changed'
    }
}
Write-Output ('PASS '+$Case)
