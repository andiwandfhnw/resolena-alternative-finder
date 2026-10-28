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
function Get-HarnessElapsedMilliseconds($Clock) {return $Clock.ElapsedMilliseconds}
function Get-HarnessFailure($ErrorRecord,[string]$Stage) {
    $failure=@{stage=$Stage;reason='unexpected_failure'}
    $known=@(
        'bundle/source_mismatch','worker/exited_without_result','worker/check_failed',
        'deadline/setup_expired','deadline/ownership_expired','deadline/worker_expired','deadline/overall_expired',
        'cleanup/unowned_job','cleanup/exit_unconfirmed',
        'ownership/process_exited','ownership/process_times_query_failed','ownership/process_creation_invalid',
        'ownership/process_basic_query_failed','ownership/process_image_query_failed','ownership/process_pid_mismatch',
        'ownership/job_query_failed','ownership/job_members_ambiguous','ownership/job_pid_invalid',
        'ownership/job_membership_query_failed','ownership/job_membership_failed','ownership/redirector_identity_changed',
        'ownership/unexpected_owned_process','ownership/interpreter_ambiguous','ownership/interpreter_identity_changed',
        'ownership/candidate_identity_changed','ownership/console_helper_ambiguous',
        'ownership/console_helper_constraints','ownership/console_helper_identity_changed',
        'ownership/supervisor_identity_mismatch','ownership/redirector_path_mismatch','ownership/stdin_pipe_failed',
        'ownership/stdio_handles_failed','ownership/handle_list_failed','ownership/create_suspended_failed',
        'ownership/job_assignment_failed','ownership/resume_failed','ownership/suspended_cleanup_unconfirmed',
        'ownership/identity_changed','ownership/interpreter_unavailable')
    $cause=$ErrorRecord.Exception
    while($null -ne $cause) {
        if($failure.reason -eq 'unexpected_failure' -and $cause.Message -cin $known){$parts=$cause.Message.Split('/');$failure.stage=$parts[0];$failure.reason=$parts[1]}
        if(-not $failure.ContainsKey('native_status')) {
            if($cause -is [ComponentModel.Win32Exception]){$failure.native_status=@{domain='win32';code=$cause.NativeErrorCode}}
            elseif($cause.Data.Contains('ntstatus') -and $cause.Data['ntstatus'] -is [int]){$failure.native_status=@{domain='ntstatus';code=$cause.Data['ntstatus']}}
        }
        $cause=$cause.InnerException
    }
    return $failure
}
function Write-HarnessPrivateFailure([string]$Root,[string]$Phase,$ErrorRecord) {
    try {
        $private=Join-Path $Root 'private'
        if(-not (Test-Path -LiteralPath $private)){$null=New-Item -ItemType Directory -Path $private}
        $text=$ErrorRecord.Exception.ToString()+[Environment]::NewLine+$ErrorRecord.ScriptStackTrace
        if($text.Length -gt 4096){$text=$text.Substring(0,4096)}
        [IO.File]::WriteAllText((Join-Path $private ($Phase+'-error.txt')),$text)
        return $true
    } catch {return $false}
}
function Get-HarnessBindingObservation($Launch) {
    if($null -eq $Launch){return @{step='not_started';job_member_pids=$null;candidate=$null;interpreter_identified=$false}}
    $candidate=$null
    if($null -ne $Launch.LastCandidate) {
        $row=$Launch.LastCandidate
        $imageClass=$(if([string]::Equals($row.image,'C:\ResolenaExperiments\tools\python-3.12.10\python.exe',[StringComparison]::OrdinalIgnoreCase)){'expected_interpreter'}elseif([string]::Equals($row.image,$Launch.ConsoleHostPath,[StringComparison]::OrdinalIgnoreCase)){'expected_console_helper'}else{'unexpected_image'})
        $candidate=@{pid=$row.pid;created=$row.created;parent_pid=$row.parent_pid;image_class=$imageClass}
    }
    return @{step=$(if($Launch.BindingStage){$Launch.BindingStage}else{'bind_not_entered'});job_member_pids=$Launch.LastJobMembers
        candidate=$candidate;interpreter_identified=($null -ne $Launch.InterpreterIdentity)
        console_helpers=@($Launch.ConsoleHelpers|ForEach-Object {@{pid=$_.identity.pid;created=$_.identity.created;parent_pid=$_.identity.parent_pid}})}
}
function Invoke-ModelFreeHarnessCheck([string]$Receipt,[string]$Root) {
    $clock=[Diagnostics.Stopwatch]::StartNew()
    $job=$null;$launch=$null;$guard=$null;$proof=$null;$worker=$null;$primary=$null;$cleanupFailures=@();$deadlineFailures=@();$observationFailures=@();$cleanupPassed=$false;$stage='bundle';$observation=$null
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
        $stage='ownership'
        $fresh=Get-OwnedPythonProof $launch $job $PID
        if($null -eq $fresh -or $fresh.interpreter.pid -ne $proof.interpreter.pid -or $fresh.interpreter.created -ne $proof.interpreter.created){throw 'ownership/identity_changed'}
    } catch {
        $primary=Get-HarnessFailure $_ $stage
        if($primary.stage -eq 'deadline'){$deadlineFailures+=@($primary)}
        if(-not (Write-HarnessPrivateFailure $Root 'primary' $_)){$observationFailures+=@(@{stage='diagnostic';reason='private_error_record_unavailable'})}
    } finally {
        try {
            $observation=Get-HarnessBindingObservation $launch
            if($null -ne $launch) {
                $private=Join-Path $Root 'private'
                if(-not (Test-Path -LiteralPath $private)){$null=New-Item -ItemType Directory -Path $private}
                $binding=@{step=$launch.BindingStage;job_member_pids=$launch.LastJobMembers;candidate=$launch.LastCandidate;interpreter_identity=$launch.InterpreterIdentity;console_helpers=@($launch.ConsoleHelpers|ForEach-Object {$_.identity})}
                [IO.File]::WriteAllText((Join-Path $private 'binding.json'),($binding|ConvertTo-Json -Depth 6))
            }
        } catch {$observationFailures+=@(@{stage='diagnostic';reason='binding_observation_unavailable'})}
        try {Complete-OwnedPythonCleanup $null $job $null $launch $Root;$cleanupPassed=$true}
        catch {
            $cleanupFailures+=@(Get-HarnessFailure $_ 'cleanup')
            if(-not (Write-HarnessPrivateFailure $Root 'cleanup' $_)){$observationFailures+=@(@{stage='diagnostic';reason='private_error_record_unavailable'})}
        }
    }
    $elapsed=Get-HarnessElapsedMilliseconds $clock
    if($elapsed -ge 60000){$deadlineFailures+=@(@{stage='deadline';reason='overall_expired'})}
    $stop=$(if($null -ne $primary){$primary}elseif($cleanupFailures.Count){$cleanupFailures[0]}elseif($deadlineFailures.Count){$deadlineFailures[0]}elseif($observationFailures.Count){$observationFailures[0]}else{$null})
    $result=@{version='uc001-contract-local-1.2.2';outcome=$(if($null -eq $stop -and $cleanupPassed){'model_free_harness_checks_passed'}else{'failed'})
        ownership=$proof;worker=$worker;stop=$stop;primary_failure=$primary;cleanup_failures=$cleanupFailures;deadline_failures=$deadlineFailures;observation_failures=$observationFailures
        binding_observation=$observation;cleanup_confirmed=$cleanupPassed;elapsed_ms=$elapsed;deadline_ms=60000
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
