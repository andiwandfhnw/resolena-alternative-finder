[CmdletBinding()]
param()

function Write-CombinedJson($Path,$Value){[IO.File]::WriteAllText($Path,($Value|ConvertTo-Json -Depth 14))}
function Get-CombinedElapsed($Clock){return $Clock.ElapsedMilliseconds}
function Get-CombinedShell {return (Join-Path ([Environment]::SystemDirectory) 'WindowsPowerShell\v1.0\powershell.exe')}
function Quote-Combined([string]$Text) {
    if($Text.Contains('"') -or $Text.Contains("`n") -or $Text.Contains("`r")){throw 'diagnostic/unsafe_argument'}
    return '"'+$Text+'"'
}
function Read-CombinedRoot($Process,$Job){return [ContractPython]::ReadInJob($Process,$Job)}
function Read-CombinedSupervisor {
    $process=[Diagnostics.Process]::GetCurrentProcess()
    try {return [ContractPython]::Read($process)} finally {$process.Dispose()}
}
function New-CombinedGuard($Job){return [Uc001Local.DeadlineGuard]::new($Job,[ContractProcesses].GetMethod('CloseHandle'))}
function Set-CombinedPrivateDirectory($Path) {
    $acl=New-Object Security.AccessControl.DirectorySecurity;$acl.SetAccessRuleProtection($true,$false)
    foreach($sid in @([Security.Principal.WindowsIdentity]::GetCurrent().User,(New-Object Security.Principal.SecurityIdentifier 'S-1-5-18'))) {
        $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule $sid,'FullControl','ContainerInherit,ObjectInherit','None','Allow'))
    }
    [IO.Directory]::SetAccessControl($Path,$acl)
}
function Get-CombinedFailure($Record,[string]$Stage) {
    $known=@('ownership/console_helper_ambiguous','ownership/console_helper_constraints','ownership/unexpected_owned_process',
        'ownership/interpreter_ambiguous','ownership/job_identity_changed','ownership/candidate_identity_changed',
        'ownership/job_query_failed','ownership/job_membership_failed','ownership/process_exited',
        'ownership/server_identity_mismatch','ownership/supervisor_identity_mismatch','ownership/interpreter_identity_changed',
        'ownership/identity_mismatch','diagnostic/python_validation_failed','diagnostic/combined_topology_missing',
        'cleanup/exit_unconfirmed','diagnostic/readiness_mismatch','diagnostic/identity_changed',
        'deadline/setup_expired','deadline/observation_expired','deadline/overall_expired')
    $cause=$Record.Exception;$value=@{stage=$Stage;reason='unexpected_failure'}
    while($null -ne $cause) {
        if($cause.Message -cin $known){$parts=$cause.Message.Split('/');$value=@{stage=$parts[0];reason=$parts[1]};break}
        $cause=$cause.InnerException
    }
    return $value
}
function Save-CombinedPrivateError($Root,$Name,$Record) {
    try {$text=$Record.Exception.ToString();if($text.Length -gt 4096){$text=$text.Substring(0,4096)};[IO.File]::WriteAllText((Join-Path $Root ('private\'+$Name+'.txt')),$text)} catch {}
}
function Get-CombinedSnapshot($Launch,$ServerIdentity,$RedirectorIdentity,$Ready,$SupervisorIdentity) {
    $rows=@()
    foreach($record in $Launch.ObservedMembers) {
        $row=@{requested_pid=$record.pid;identity_verified=$record.identity_verified;job_verified=$record.job_verified;role_approved=$false;identity=$null;parent_observation='unresolved'}
        if($null -ne $record.identity) {
            $value=$record.identity;$image='<private unknown image>'
            if([string]::Equals($value.image,$Launch.ConsoleHostPath,[StringComparison]::OrdinalIgnoreCase)){$image=$Launch.ConsoleHostPath}
            elseif([string]::Equals($value.image,'C:\ResolenaExperiments\tools\python-3.12.10\python.exe',[StringComparison]::OrdinalIgnoreCase)){$image='C:\ResolenaExperiments\tools\python-3.12.10\python.exe'}
            $row.identity=@{pid=$value.pid;created=$value.created;parent_pid=$value.parent_pid;image=$image}
            if($value.parent_pid -eq $ServerIdentity.pid){$row.parent_observation='server_standin'}
            elseif($value.parent_pid -eq $RedirectorIdentity.pid){$row.parent_observation='python_redirector'}
            elseif($null -ne $Ready -and $value.parent_pid -eq $Ready.pid){$row.parent_observation='python_interpreter_ready_hint'}
            elseif($null -ne $SupervisorIdentity -and $value.parent_pid -eq $SupervisorIdentity.pid){$row.parent_observation='powershell_supervisor'}
        }
        $rows+=@($row)
    }
    return @{supervisor=$SupervisorIdentity;server=$ServerIdentity;redirector=$RedirectorIdentity;python_readiness_hint=$Ready
        job_member_pids=$Launch.LastJobMembers;observed_members=$rows;role_acceptance='branch-specific policy; observation labels alone are not approval'}
}
function Invoke-CombinedCheck([string]$Root,$Clock=$null) {
    if($null -eq $Clock){$Clock=[Diagnostics.Stopwatch]::StartNew()}
    $job=$null;$guard=$null;$server=$null;$launch=$null;$serverIdentity=$null;$supervisorIdentity=$null;$snapshot=$null;$proof=$null;$pythonResult=$null
    $primary=$null;$cleanupFailures=@();$deadlineFailures=@();$observationFailures=@();$cleanupPassed=$false;$stage='native_setup';$ready=$null;$serverAttempted=$false;$pythonAttempted=$false
    try {
        Initialize-PythonOwnership
        if((Get-CombinedElapsed $clock) -ge 10000){throw 'deadline/setup_expired'}
        $supervisorIdentity=Read-CombinedSupervisor
        $job=New-ContractJob;$guard=New-CombinedGuard $job
        $guard.Arm([int][Math]::Max(1,30000-(Get-CombinedElapsed $clock)))
        function Close-ContractJob($Job){if($Job -ne $guard.Job){throw 'cleanup/exit_unconfirmed'};return $guard.Close()}
        $stage='server_standin'
        $idle=[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes('[Threading.Thread]::Sleep(45000)'))
        $serverAttempted=$true
        $server=Start-ContractProcess $job (Get-CombinedShell) ('-NoLogo -NoProfile -NonInteractive -EncodedCommand '+$idle) (Join-Path $Root 'private\server.stdout.log') (Join-Path $Root 'private\server.stderr.log') $null
        $server.StandardInput.Close();$serverIdentity=Read-CombinedRoot $server $job
        if($serverIdentity.parent_pid -ne $supervisorIdentity.pid -or $serverIdentity.created -lt $supervisorIdentity.created -or -not [string]::Equals($serverIdentity.image,(Get-CombinedShell),[StringComparison]::OrdinalIgnoreCase)){throw 'diagnostic/identity_changed'}
        $stage='python_standin'
        $readyPath=Join-Path $Root 'private\python-ready.json'
        $pythonResultPath=Join-Path $Root 'python-result.json'
        $arguments=@('-I','-X','utf8','-B',(Join-Path $PSScriptRoot 'idle.py'),$readyPath,$pythonResultPath)
        $pythonAttempted=$true
        $launch=Start-OwnedPython $job (($arguments|ForEach-Object {Quote-Combined $_})-join ' ') $Root
        $stage='observation';$ready=$null;$previous=$null;$stable=[Diagnostics.Stopwatch]::StartNew()
        while($true) {
            if((Get-CombinedElapsed $clock) -ge 30000){throw 'deadline/observation_expired'}
            $freshServer=Read-CombinedRoot $server $job
            if($freshServer.pid -ne $serverIdentity.pid -or $freshServer.created -ne $serverIdentity.created){throw 'diagnostic/identity_changed'}
            $null=$launch.Observe($job,$server.Id)
            if(Test-Path -LiteralPath $readyPath){$ready=Read-ContractJson $readyPath}
            $members=($launch.LastJobMembers|Sort-Object)-join ','
            if($members -cne $previous){$stable.Restart();$previous=$members}
            $snapshot=Get-CombinedSnapshot $launch $serverIdentity $launch.RedirectorIdentity $ready $supervisorIdentity
            Write-CombinedJson (Join-Path $Root 'observation.json') $snapshot
            Write-CombinedJson (Join-Path $Root 'private\observed-identities.json') @($launch.ObservedMembers|ForEach-Object {@{requested_pid=$_.pid;identity=$_.identity;identity_verified=$_.identity_verified;job_verified=$_.job_verified}})
            if($null -ne $ready -and $stable.ElapsedMilliseconds -ge 200) {
                $matching=@($launch.ObservedMembers|Where-Object {$_.identity_verified -and $_.identity.pid -eq $ready.pid -and $_.identity.parent_pid -eq $ready.parent_pid})
                if($matching.Count -ne 1 -or $ready.parent_pid -ne $launch.Id){throw 'diagnostic/readiness_mismatch'}
                break
            }
            Start-Sleep -Milliseconds 20
        }
        $stage='ownership'
        $proof=Get-OwnedPythonProof $launch $job $PID $server $serverIdentity (Get-CombinedShell)
        if($null -eq $proof){throw 'diagnostic/readiness_mismatch'}
        if(@($proof.console_helpers|Where-Object {$_.parent_pid -eq $serverIdentity.pid}).Count -ne 1 -or
            @($proof.console_helpers|Where-Object {$_.parent_pid -eq $proof.redirector.pid}).Count -ne 1){throw 'diagnostic/combined_topology_missing'}
        Write-CombinedJson (Join-Path $Root 'ownership.json') $proof
        $proofText=$proof|ConvertTo-Json -Depth 14 -Compress
        $stage='python_validation'
        $launch.StandardInput.WriteLine($proofText);$launch.StandardInput.Flush()
        while(-not (Test-Path -LiteralPath $pythonResultPath)) {
            if((Get-CombinedElapsed $clock) -ge 30000){throw 'deadline/observation_expired'}
            $fresh=Get-OwnedPythonProof $launch $job $PID $server $serverIdentity (Get-CombinedShell)
            if($null -eq $fresh){throw 'diagnostic/identity_changed'}
            Start-Sleep -Milliseconds 20
        }
        $pythonResult=Read-ContractJson $pythonResultPath
        if($pythonResult.outcome -ne 'python_combined_ownership_verified' -or $pythonResult.validator -ne 'verify_python_ownership' -or
            $pythonResult.pid -ne $proof.interpreter.pid -or $pythonResult.parent_pid -ne $proof.redirector.pid -or
            ($pythonResult.proof|ConvertTo-Json -Depth 14 -Compress) -cne $proofText){throw 'diagnostic/python_validation_failed'}
        $stage='final_native_validation'
        $fresh=Get-OwnedPythonProof $launch $job $PID $server $serverIdentity (Get-CombinedShell)
        if($null -eq $fresh -or ($fresh|ConvertTo-Json -Depth 14 -Compress) -cne $proofText){throw 'diagnostic/identity_changed'}
    } catch {
        $primary=Get-CombinedFailure $_ $stage
        if($primary.stage -eq 'deadline'){$deadlineFailures+=@($primary)}
        Save-CombinedPrivateError $Root 'primary' $_
    } finally {
        if($null -ne $launch -and $null -ne $serverIdentity) {
            try {
                $snapshot=Get-CombinedSnapshot $launch $serverIdentity $launch.RedirectorIdentity $ready $supervisorIdentity
                Write-CombinedJson (Join-Path $Root 'observation.json') $snapshot
                Write-CombinedJson (Join-Path $Root 'private\observed-identities.json') @($launch.ObservedMembers|ForEach-Object {@{requested_pid=$_.pid;identity=$_.identity;identity_verified=$_.identity_verified;job_verified=$_.job_verified}})
            } catch {$observationFailures+=@(@{stage='diagnostic';reason='snapshot_unavailable'});Save-CombinedPrivateError $Root 'observation' $_}
        }
        function Get-OwnedCleanupWaitMilliseconds {return [int][Math]::Max(0,[Math]::Min(5000,45000-(Get-CombinedElapsed $clock)))}
        try {Complete-OwnedPythonCleanup $null $job $server $launch $Root $serverIdentity;$cleanupPassed=$true}
        catch {$cleanupFailures+=@(Get-CombinedFailure $_ 'cleanup');Save-CombinedPrivateError $Root 'cleanup' $_}
        if($serverAttempted -and $null -eq $serverIdentity){$cleanupPassed=$false;$cleanupFailures+=@(@{stage='cleanup';reason='server_identity_unavailable'})}
        if($pythonAttempted -and $null -eq $launch){$cleanupPassed=$false;$cleanupFailures+=@(@{stage='cleanup';reason='python_identity_unavailable'})}
    }
    if($null -ne $guard -and $guard.Expired){$deadlineFailures+=@(@{stage='deadline';reason='owned_job_expired'})}
    if((Get-CombinedElapsed $clock) -ge 45000){$deadlineFailures+=@(@{stage='deadline';reason='overall_expired'})}
    $result=@{version='uc001-combined-ownership-1.1.0';outcome=$(if($null -eq $primary -and $cleanupPassed -and -not $deadlineFailures.Count -and -not $observationFailures.Count){'combined_native_python_and_cleanup_passed'}else{'failed'})
        primary_failure=$primary;cleanup_failures=$cleanupFailures;deadline_failures=$deadlineFailures;observation_failures=$observationFailures;observation=$snapshot;ownership=$proof;python_validator=$pythonResult
        cleanup_confirmed=$cleanupPassed;elapsed_ms=(Get-CombinedElapsed $clock);deadline_ms=45000;model_attempt_ledger_touched=$false;model_startup_authorized=$false
        result_directory=$Root;reported_ambiguity_reproduced=($null -ne $primary -and $primary.reason -eq 'console_helper_ambiguous')
        standin_launches=@{server_attempted=$serverAttempted;python_attempted=$pythonAttempted}
        original_and_additional_model_allowances='consumed';role_policy_changed=$true;failed_run_helper_legitimacy='not_established';semantic_review='pending';expected_meanings_approved=$false}
    Write-CombinedJson (Join-Path $Root 'result.json') $result
    return $result
}
if($MyInvocation.InvocationName -ne '.') {
    $ErrorActionPreference='Stop';Set-StrictMode -Version Latest
    $clock=[Diagnostics.Stopwatch]::StartNew()
    $manifest=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'freeze.json') -Raw|ConvertFrom-Json
    foreach($entry in $manifest.files.PSObject.Properties) {
        if((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $entry.Name) -Algorithm SHA256).Hash.ToLowerInvariant() -cne $entry.Value){throw 'diagnostic/source_mismatch'}
    }
    $parent=Join-Path (Split-Path $PSScriptRoot -Parent) 'uc001_execution_v1_3_0'
    . (Join-Path $parent 'Common.ps1')
    Assert-ContractWindows
    . (Join-Path $PSScriptRoot 'Python-Ownership.ps1')
    $root=Join-Path (Join-Path $PSScriptRoot 'results') ([guid]::NewGuid().ToString())
    $null=New-Item -ItemType Directory -Path $root
    Set-CombinedPrivateDirectory $root
    $null=New-Item -ItemType Directory -Path (Join-Path $root 'private')
    Add-Type -Path (Join-Path $PSScriptRoot 'DeadlineGuard.cs')
    $result=Invoke-CombinedCheck $root $clock
    $result|ConvertTo-Json -Depth 14
    if($result.outcome -ne 'combined_native_python_and_cleanup_passed'){exit 1}
}
