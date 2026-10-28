param([Parameter(Mandatory=$true)][string]$Case)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')
$script:reads=0; $script:key='luid_0x00000000_0x0000000A'
$script:started=0; $script:closed=0; $script:disposed=0
$owner=[pscustomobject]@{Id=[int]123;HasExited=$false;StartTime=[DateTime]'2026-10-17T00:00:00Z';WorkingSet64=[long]1GB}
$owner | Add-Member ScriptMethod Refresh {}
$owner | Add-Member ScriptMethod WaitForExit {param($milliseconds) return ($Case -ne 'flow_cleanup_unconfirmed')}
$owner | Add-Member ScriptMethod Dispose {$script:disposed++}
$inputStream=[pscustomobject]@{}; $inputStream | Add-Member ScriptMethod Close {}
$owner | Add-Member NoteProperty StandardInput $inputStream
function Read-AssociationDxgi {
    $script:reads++
    $item=[pscustomobject]@{Status='ok';Description='AMD Radeon RX 6800 XT';Vendor=[uint32]0x1002;Device=[uint32]0x73BF;Subsystem=[uint32]0x12341002
        Revision=[uint32]0xC1;Flags=[uint32]0;CounterKey=$script:key;DedicatedBytes=[uint64]16GB}
    if($script:reads -gt 1) {
        switch($Case) {
            'adapter_luid_changes' {$item.CounterKey='luid_0x00000000_0x0000000B'}
            'adapter_pci_changes' {$item.Subsystem=[uint32]1}
            'adapter_capacity_changes' {$item.DedicatedBytes=[uint64]15GB}
        }
    }
    if($Case -eq 'flow_runtime_identity' -and $script:reads -gt 2){$item.CounterKey='luid_0x00000000_0x0000000B'}
    if($Case -eq 'flow_startup_identity'){return [pscustomobject]@{Status='ok';Adapters=@($item,$item)}}
    [pscustomobject]@{Status='ok';Adapters=@($item)}
}
function Get-ItemProperty {return [pscustomobject]@{Other='registry diagnostic unavailable'}}
function Get-CimClass {return [pscustomobject]@{CimClassProperties=@([pscustomobject]@{Name='DedicatedUsage'})}}
function Get-CimInstance($ClassName) {
    switch($ClassName) {
        'Win32_VideoController' {return [pscustomobject]@{Name='AMD Radeon RX 6800 XT';PNPDeviceID='PCI\VEN_1002&DEV_73BF&SUBSYS_12341002&REV_C1\synthetic'}}
        'Win32_OperatingSystem' {
            $free=[long](24GB/1024)
            if($Case -eq 'ram_invalid'){$free='25165824'}
            if($Case -eq 'ram_bounds'){$free=[long](40GB/1024)}
            return [pscustomobject]@{FreePhysicalMemory=$free;TotalVisibleMemorySize=[long](32GB/1024)}
        }
        'Win32_PerfRawData_GPUPerformanceCounters_GPUAdapterMemory' {
            $item=[pscustomobject]@{Name=($script:key+'_phys_0');DedicatedUsage=[uint64]1GB}
            if($Case -eq 'flow_resource_floor' -and $script:started -gt 0){$item.DedicatedUsage=[uint64]15GB}
            if($Case -eq 'gpu_missing'){return}
            if($Case -eq 'gpu_negative'){$item.DedicatedUsage=[long]-1}
            $item
            if($Case -eq 'gpu_duplicate'){$item}
        }
        'Win32_PerfRawData_GPUPerformanceCounters_GPUProcessMemory' {
            if($Case -eq 'query_failed'){throw 'Synthetic owned-counter query failure'}
            if($Case -in @('owned_missing','flow_missing')){return}
            $item=[pscustomobject]@{Name=('pid_123_'+$script:key+'_phys_0');DedicatedUsage=[uint64]512MB}
            switch($Case) {
                'owned_zero' {$item.DedicatedUsage=[uint64]0}
                'flow_zero' {$item.DedicatedUsage=[uint64]0}
                'owned_other_pid' {$item.Name='pid_124_'+$script:key+'_phys_0'}
                'owned_other_luid' {$item.Name='pid_123_luid_0x00000000_0x0000000B_phys_0'}
                'owned_lookalike' {$item.Name='pid_123_'+$script:key+'1_phys_0'}
                'owned_phys1' {$item.Name='pid_123_'+$script:key+'_phys_1'}
                'owned_null' {$item.DedicatedUsage=$null}
                'owned_string' {$item.DedicatedUsage='0'}
                'owned_negative' {$item.DedicatedUsage=[long]-1}
                'owned_fraction' {$item.DedicatedUsage=0.5}
                'owned_capacity' {$item.DedicatedUsage=[uint64]17GB}
                'flow_capacity' {$item.DedicatedUsage=[uint64]17GB}
                'process_exits_during_sample' {$owner.HasExited=$true}
                'process_pid_changes' {$owner.Id=[int]124}
                'process_start_changes' {$owner.StartTime=$owner.StartTime.AddSeconds(1)}
            }
            $item
            if($Case -eq 'owned_duplicate'){$item}
            if($Case -eq 'owned_multiple_phys'){[pscustomobject]@{Name=('pid_123_'+$script:key+'_phys_1');DedicatedUsage=[uint64]0}}
            if($Case -eq 'foreign_rows') {
                [pscustomobject]@{Name=('pid_1234_'+$script:key+'_phys_0');DedicatedUsage=[uint64]10GB}
                [pscustomobject]@{Name='pid_123_luid_0x00000000_0x0000000B_phys_0';DedicatedUsage=[uint64]10GB}
            }
        }
        'Win32_Process' {return}
        default {throw ('Unexpected class '+$ClassName)}
    }
}
function Get-ContractDrive {
    $free=[long]10GB
    if($Case -eq 'disk_invalid'){$free=$null}
    if($Case -eq 'disk_bounds'){$free=[long]30GB}
    return [pscustomobject]@{AvailableFreeSpace=$free;TotalSize=[long]20GB}
}
switch($Case) {
    'rss_null' {$owner.WorkingSet64=$null}
    'rss_string' {$owner.WorkingSet64='1'}
    'rss_negative' {$owner.WorkingSet64=[long]-1}
    'rss_capacity' {$owner.WorkingSet64=[long]40GB}
    'pid_invalid' {$owner.Id='123'}
    'process_exited' {$owner.HasExited=$true}
}
function Require($condition,$message){if(-not $condition){throw $message}}
$tempRoot=Join-Path ([IO.Path]::GetTempPath()) ('uc001-monitor-test-'+[guid]::NewGuid())
try {
    if($Case.StartsWith('flow_')) {
        $tokens=$null;$errors=$null
        $ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'Run-Windows.ps1'),[ref]$tokens,[ref]$errors)
        if($errors.Count){throw $errors[0]}
        if(-not $ast.Find({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Invoke-ContractExecution'},$true)){throw 'Testable launcher entry with corrected policy is absent (RED).'}
        . (Join-Path $PSScriptRoot 'Run-Windows.ps1') -Codespace offline
        if(-not (Test-Path Function:\Invoke-ContractExecution)){throw 'Testable launcher entry with corrected policy is absent (RED).'}
        function Assert-ContractWindows {}
        function Assert-ContractBundle {}
        function Get-ContractAssets {}
        function Get-ContractTools {return [pscustomobject]@{gh_pin_available=$true;ssh='synthetic';gh='synthetic'}}
        function Get-NetTCPConnection {return}
        function Read-ContractJson($Path) {
            if($Path.EndsWith('freeze.json')) {return [pscustomobject]@{attempt_identity='bda2015c0ffbe89ab1a612fb4003b2b12f254871cf32f2e47dbbbe9d45cf0f52'}}
            $config=([IO.File]::ReadAllText((Join-Path $PSScriptRoot 'config.json'))|ConvertFrom-Json)
            $config.reuse_root=Join-Path $tempRoot 'assets'; return $config
        }
        function Get-ContractHash {return ('f'*64)}
        function Initialize-ContractProcessSupport {}
        function New-ContractJob {return 'synthetic-owned-job'}
        function Close-ContractJob($Job) {$script:closed++;return ($Case -ne 'flow_job_close_failed')}
        function Start-ContractProcess {
            $script:started++
            if($script:started -gt 1){throw 'Unexpected transport/second startup'}
            return $owner
        }
        function New-ContractHttpClient {
            $client=[pscustomobject]@{}
            $client | Add-Member ScriptMethod Dispose {if($Case -eq 'flow_client_cleanup_error'){throw 'Synthetic client cleanup failure'}}
            return $client
        }
        function Get-Http {throw 'Synthetic stop after valid runtime sample; no HTTP request sent'}
        $attempt=Join-Path $tempRoot 'uc001-contract-runs/bda2015c0ffbe89ab1a612fb4003b2b12f254871cf32f2e47dbbbe9d45cf0f52'
        if($Case -eq 'flow_existing_attempt'){$null=New-Item -ItemType Directory -Path $attempt -Force}
        $message=$null
        try {Invoke-ContractExecution 'offline'} catch {$message=$_.Exception.Message}
        Require ($null -ne $message) 'Synthetic abort did not stop launcher'
        if($Case -eq 'flow_startup_identity') {
            Require ($script:started -eq 0 -and $message -match 'Exactly one hardware') 'Startup bypassed unique hardware policy'
        } elseif($Case -eq 'flow_existing_attempt') {
            Require ($script:started -eq 0 -and $message -match 'already started/attempted') ('Existing attempt identity was reset by versioning: '+$message)
        } else {
            Require ($script:started -eq 1 -and $script:closed -eq 1 -and $script:disposed -eq 1) ('Abort did not clean exactly the owned job/process: '+$message+'; counts '+$script:started+'/'+$script:closed+'/'+$script:disposed)
            Require ($script:reads -ge 3) 'Startup and runtime did not invoke complete identity policy'
            Require (Test-Path -LiteralPath (Join-Path $attempt 'stopped.txt')) 'Stopped attempt evidence missing'
            $cleanup=([IO.File]::ReadAllText((Join-Path $attempt 'cleanup.json'))|ConvertFrom-Json)
            Require ($cleanup.owned_job_closed -eq ($Case -ne 'flow_job_close_failed')) 'Job closure state not recorded'
            if($Case -eq 'flow_cleanup_unconfirmed'){Require (-not $cleanup.owned_exits[0].exit_confirmed -and $message -match 'cleanup') 'Unconfirmed exit reported success'}
            if($Case -eq 'flow_client_cleanup_error'){Require ($message -match 'cleanup') 'Client disposal failure concealed'}
            if($Case -eq 'flow_job_close_failed'){Require ($message -match 'cleanup') 'Failed job closure reported success'}
            if($Case -eq 'flow_resource_floor'){Require ($message -match 'resource floor/cap') 'Runtime resource floor failure concealed'}
            if($Case -eq 'flow_zero') {
                $line=Get-Content -LiteralPath (Join-Path $attempt 'resources.jsonl') | Select-Object -First 1 | ConvertFrom-Json
                Require ($line.owned_gpu -eq 0 -and $line.owned_gpu_state -eq 'measured') 'Zero runtime sample not recorded honestly'
            }
        }
    } elseif($Case -eq 'cleanup_two_owned') {
        function Close-ContractJob {$script:closed++;return $true}
        $owner | Add-Member ScriptMethod Dispose {$script:disposed++;throw 'Synthetic server disposal failure'} -Force
        $tunnel=[pscustomobject]@{Id=456}
        $tunnel | Add-Member ScriptMethod WaitForExit {param($milliseconds) return $true}
        $tunnel | Add-Member ScriptMethod Dispose {$script:disposed++}
        $null=New-Item -ItemType Directory -Path $tempRoot
        $failed=$false
        try {Complete-ContractCleanup $null 'synthetic' $owner $tunnel $tempRoot} catch {$failed=$true}
        $cleanup=([IO.File]::ReadAllText((Join-Path $tempRoot 'cleanup.json'))|ConvertFrom-Json)
        Require ($failed -and $script:closed -eq 1 -and $script:disposed -eq 2 -and $cleanup.owned_exits.Count -eq 2) 'One cleanup failure skipped the other owned process'
    } else {
        $rejected=$false;$sample=$null
        try {$adapter=Get-ContractAdapter;$sample=Get-ContractResources $adapter $tempRoot $owner} catch {$rejected=$true}
        if($Case -in @('owned_zero','owned_valid','foreign_rows')) {
            Require (-not $rejected) 'Valid owned measurement rejected'
            Require ($script:reads -ge 2) 'Runtime did not revalidate complete native identity'
            Require ($sample.owned_gpu_state -eq 'measured' -and $sample.owned_pid -eq 123) 'Owned attribution/measurement state absent'
            $expected=$(if($Case -eq 'owned_zero'){0}else{512MB})
            Require ($sample.owned_gpu -eq $expected) 'Owned measurement substituted or foreign process/adapter included'
        } else {Require $rejected ('Invalid/missing sample accepted: '+$Case)}
    }
} finally {if(Test-Path -LiteralPath $tempRoot){Remove-Item -LiteralPath $tempRoot -Recurse -Force}}
Write-Output ('PASS '+$Case)
