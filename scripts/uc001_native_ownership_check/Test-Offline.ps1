param([Parameter(Mandatory=$true)][string]$Case)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$bundle=Join-Path (Split-Path $PSScriptRoot -Parent) 'uc001_execution_v1_3_0'
. (Join-Path $bundle 'Common.ps1')
. (Join-Path $PSScriptRoot 'Check-NativeOwnership.ps1') -BundleDirectory $bundle
$script:closed=0;$script:killed=0;$script:disposed=0;$script:reads=0
$script:waits=@()
function Require($Condition,[string]$Message) {if(-not $Condition){throw $Message}}
function New-FakeOwner {
    $owner=[pscustomobject]@{Id=[int]123;HasExited=$false;StartTime=[DateTime]'2026-10-17T00:00:00Z';Handle=[IntPtr]42;ExitCode=0}
    $owner|Add-Member ScriptMethod Refresh {}
    $owner|Add-Member ScriptMethod Kill {$script:killed++;$this.HasExited=$true}
    $owner|Add-Member ScriptMethod WaitForExit {
        param($Milliseconds)
        $script:waits+=@($Milliseconds)
        if($Case -in @('exit_unconfirmed','supervisor_exit_unconfirmed')){return $false}
        if($Case -eq 'supervisor_timeout' -and $script:killed -eq 0){return $false}
        $this.HasExited=$true;return $true
    }
    $owner|Add-Member ScriptMethod Dispose {$script:disposed++;if($Case -eq 'dispose_failed'){throw 'Synthetic dispose failure'}}
    $stream=[pscustomobject]@{};$stream|Add-Member ScriptMethod Close {}
    $owner|Add-Member NoteProperty StandardInput $stream
    return $owner
}
$owner=New-FakeOwner
function Initialize-ContractProcessSupport {}
function New-ContractJob {return [IntPtr]99}
function Close-ContractJob {$script:closed++;return ($Case -ne 'job_close_failed')}
function Start-ContractProcess {if($Case -eq 'start_failed'){throw 'Synthetic start failure'};return $owner}
function Open-OwnershipProcess {
    if($Case -eq 'identity_failed'){throw 'Synthetic identity read failure'}
    if($Case -eq 'recover_query_failed'){throw 'Synthetic process query denied'}
    if($Case -eq 'recover_pid_absent'){throw [ArgumentException]::new('Synthetic PID absent')}
    $lookup=New-FakeOwner
    if($Case -eq 'pid_changed'){$lookup.Id=124}
    if($Case -in @('creation_changed','recover_wrong_creation')){$lookup.StartTime=$lookup.StartTime.AddSeconds(1)}
    return $lookup
}
if($Case -ne 'deadline_boundaries') {
    function Assert-OwnershipDeadline($Clock,$Milliseconds) {if($Case -eq 'worker_deadline' -and $Milliseconds -eq 35000){throw 'Synthetic deadline expired'}}
}
$root=Join-Path ([IO.Path]::GetTempPath()) ('uc001-ownership-offline-'+[guid]::NewGuid())
try {
    $null=New-Item -ItemType Directory -Path $root
    foreach($name in @('worker','supervisor','recovery')){$null=New-Item -ItemType Directory -Path (Join-Path $root $name)}
    if($Case -eq 'deadline_boundaries') {
        foreach($limit in @(2000,35000,40000,45000,60000)) {
            Assert-OwnershipDeadline ([pscustomobject]@{ElapsedMilliseconds=($limit-1)}) $limit
            $failed=$false
            try {Assert-OwnershipDeadline ([pscustomobject]@{ElapsedMilliseconds=$limit}) $limit} catch {$failed=$true}
            Require $failed 'Exact deadline boundary accepted'
        }
    } elseif($Case.StartsWith('supervisor_') -or $Case -in @('bad_worker_receipt','cleanup_receipt_mismatch')) {
        function Start-OwnershipSupervisorProcess {return $owner}
        if($Case -eq 'supervisor_identity_failed'){$owner.StartTime=$null}
        if($Case -eq 'bad_worker_receipt'){Write-OwnershipJson (Join-Path $root 'worker/worker-result.json') @{outcome='native_ownership_cleanup_passed';expected_abort_exercised=$false}}
        if($Case -in @('supervisor_success','cleanup_receipt_mismatch')) {
            Write-OwnershipJson (Join-Path $root 'worker/worker-result.json') @{outcome='native_ownership_cleanup_passed';expected_abort_exercised=$true
                identity=@{Id=456};errors=@();cleanup=@{owned_job_created=$true;owned_job_closed=$true;owned_exits=@(@{pid=$(if($Case -eq 'supervisor_success'){456}else{789});exit_confirmed=$true});errors=@()}}
        }
        $report=Invoke-OwnershipSupervisor 'unused' $bundle $root ([Diagnostics.Stopwatch]::StartNew())
        if($Case -eq 'supervisor_success') {Require ($report.outcome -eq 'native_ownership_cleanup_passed' -and $script:killed -eq 0) 'Valid worker/cleanup rejected'}
        else {Require ($report.outcome -eq 'failed') 'Supervisor falsely passed failure/timeout'}
        if($Case -in @('supervisor_timeout','supervisor_exit_unconfirmed','supervisor_identity_failed')){Require ($script:killed -eq 1) 'Supervisor did not terminate exactly its retained owned worker'}
        Require ($script:disposed -ge 1) 'Supervisor did not attempt owned process disposal'
        Require (@($script:waits|Where-Object {$_ -gt 45000}).Count -eq 0) 'Unbounded supervisor wait'
        Require ($script:waits[-1] -eq 5000) 'Frozen exit-confirmation path not called'
    } elseif($Case.StartsWith('recover_') -or $Case -eq 'missing_child_identity') {
        if($Case -eq 'missing_child_identity') {Write-OwnershipJson (Join-Path $root 'worker/child-start-attempt.json') @{attempted=$true}}
        else {Write-OwnershipJson (Join-Path $root 'worker/child-identity.json') @{pid=123;started_ticks=$owner.StartTime.ToUniversalTime().Ticks}}
        $failed=$false
        try {Complete-OwnershipChildCleanup $root} catch {$failed=$true}
        if($Case -eq 'recover_owned') {Require (-not $failed -and $script:killed -eq 1) 'Known owned recovery did not terminate/confirm exit'}
        elseif($Case -eq 'recover_pid_absent'){Require (-not $failed -and $script:killed -eq 0 -and (Test-Path -LiteralPath (Join-Path $root 'recovery.json'))) 'Absent process was substituted or not recorded'}
        else {Require ($failed -and $script:killed -eq 0) 'Recovery killed an unproven identity or hid missing data'}
    } else {
        $report=Invoke-OwnershipWorker (Join-Path $root 'worker')
        if($Case -eq 'owned_abort') {
            Require ($report.outcome -eq 'native_ownership_cleanup_passed' -and $report.expected_abort_exercised) ('Valid owned abort rejected: '+($report|ConvertTo-Json -Depth 8))
            Require ($script:closed -eq 1 -and $report.cleanup.owned_exits[0].exit_confirmed) 'Frozen cleanup path not exercised'
        } else {Require ($report.outcome -eq 'failed') ('Failure concealed: '+$Case)}
        if($Case -ne 'worker_deadline'){Require ($script:closed -eq 1) 'Failure skipped job closure'}
        Require (-not $report.owned_gpu_counter_verified -and -not $report.model_allocation_verified) 'Native ownership diagnostic fabricated GPU/model proof'
    }
} finally {if(Test-Path -LiteralPath $root){Remove-Item -LiteralPath $root -Recurse -Force}}
Write-Output ('PASS '+$Case)
