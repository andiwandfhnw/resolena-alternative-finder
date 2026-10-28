[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$SavedReceipt)

function Assert-HarnessBundle {
    $freeze=Read-ContractJson (Join-Path $PSScriptRoot 'freeze.json')
    foreach($item in $freeze.files.PSObject.Properties) {
        if((Get-ContractHash (Join-Path $PSScriptRoot $item.Name)) -cne $item.Value){throw 'bundle/source_mismatch'}
    }
}
function Assert-HarnessDeadline($Clock,[long]$Limit,[string]$Reason) {
    if($Clock.ElapsedMilliseconds -ge $Limit){throw ('deadline/'+$Reason)}
}
function Invoke-ModelFreeHarnessCheck([string]$Receipt,[string]$Root) {
    $clock=[Diagnostics.Stopwatch]::StartNew()
    $job=$null;$launch=$null;$guard=$null;$proof=$null;$worker=$null;$stop=$null;$cleanupPassed=$false;$stage='bundle'
    try {
        Assert-ContractWindows
        Assert-ContractBundle
        Assert-HarnessBundle
        $stage='native_setup';Initialize-PythonOwnership
        $job=New-ContractJob
        $guard=New-LocalDeadline $job
        function Close-ContractJob($Job) {if($null -eq $guard){return [ContractProcesses]::CloseHandle($Job)};if($Job -ne $guard.Job){throw 'cleanup/unowned_job'};return $guard.Close()}
        Assert-HarnessDeadline $clock 10000 'setup_expired'
        $guard.Arm(45000)
        $arguments=@('-I','-X','utf8','-B',(Join-Path $PSScriptRoot 'verify.py'),'--saved-receipt',$Receipt,'--result',(Join-Path $Root 'worker-result.json'))
        $stage='owned_start';$launch=Start-OwnedPython $job (($arguments|ForEach-Object {Quoted $_})-join ' ') $Root
        $stage='ownership'
        while($null -eq $proof) {
            Assert-HarnessDeadline $clock 45000 'ownership_expired'
            $proof=Get-OwnedPythonProof $launch $job $PID
            if($null -eq $proof){Start-Sleep -Milliseconds 20}
        }
        $launch.StandardInput.WriteLine(($proof|ConvertTo-Json -Depth 8 -Compress));$launch.StandardInput.Flush();$stage='worker'
        while(-not (Test-Path -LiteralPath (Join-Path $Root 'worker-result.json'))) {
            Assert-HarnessDeadline $clock 45000 'worker_expired'
            $launch.Refresh();if($launch.HasExited){throw 'worker/exited_without_result'}
            Start-Sleep -Milliseconds 20
        }
        $worker=Read-ContractJson (Join-Path $Root 'worker-result.json')
        if($worker.outcome -ne 'model_free_worker_checks_passed'){throw 'worker/check_failed'}
        $fresh=Get-OwnedPythonProof $launch $job $PID
        if($null -eq $fresh -or $fresh.interpreter.pid -ne $proof.interpreter.pid -or $fresh.interpreter.created -ne $proof.interpreter.created){throw 'ownership/identity_changed'}
    } catch {
        $stop=@{stage=$stage;reason='unexpected_failure'}
        $cause=$_.Exception
        while($null -ne $cause.InnerException){$cause=$cause.InnerException}
        if($cause.Message -match '^(ownership|worker|deadline|cleanup|bundle)/([a-z_]+)$'){$stop=@{stage=$Matches[1];reason=$Matches[2]}}
    } finally {
        try {Complete-OwnedPythonCleanup $null $job $null $launch $Root;$cleanupPassed=$true}
        catch {$stop=@{stage='cleanup';reason='exit_unconfirmed'}}
    }
    if($clock.ElapsedMilliseconds -ge 60000){$stop=@{stage='deadline';reason='overall_expired'}}
    $result=@{version='uc001-contract-local-1.2.0';outcome=$(if($null -eq $stop -and $cleanupPassed){'model_free_harness_checks_passed'}else{'failed'})
        ownership=$proof;worker=$worker;stop=$stop;cleanup_confirmed=$cleanupPassed;elapsed_ms=$clock.ElapsedMilliseconds;deadline_ms=60000
        startup_authorized=$false;startup_allowance_consumed=$true;model_attempt_ledger_touched=$false;model_readiness_verified=$false;semantic_review='pending';expected_meanings_approved=$false}
    [IO.File]::WriteAllText((Join-Path $Root 'result.json'),($result|ConvertTo-Json -Depth 12))
    return $result
}

if($MyInvocation.InvocationName -ne '.') {
    $ErrorActionPreference='Stop';Set-StrictMode -Version Latest
    $parent=Join-Path (Split-Path $PSScriptRoot -Parent) 'uc001_execution_v1_3_0'
    . (Join-Path $parent 'Common.ps1')
    . (Join-Path $parent 'Run-Windows.ps1') -Codespace model-free
    . (Join-Path $PSScriptRoot 'Run-Windows.ps1')
    . (Join-Path $PSScriptRoot 'Python-Ownership.ps1')
    $base=Join-Path $PSScriptRoot 'results';$root=Join-Path $base ([guid]::NewGuid().ToString())
    $null=New-Item -ItemType Directory -Path $root
    Set-LocalPrivateDirectory $root
    $result=Invoke-ModelFreeHarnessCheck $SavedReceipt $root
    $result|ConvertTo-Json -Depth 12
    if($result.outcome -ne 'model_free_harness_checks_passed'){exit 1}
}
