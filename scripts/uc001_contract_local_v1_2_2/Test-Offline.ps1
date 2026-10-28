param([Parameter(Mandatory=$true)][string]$Case)
$selected=$Case;$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$parent=Join-Path (Split-Path $PSScriptRoot -Parent) 'uc001_execution_v1_3_0'
. (Join-Path $parent 'Common.ps1')
. (Join-Path $parent 'Run-Windows.ps1') -Codespace synthetic
. (Join-Path $PSScriptRoot 'Run-Windows.ps1')
. (Join-Path $PSScriptRoot 'Python-Ownership.ps1')
. (Join-Path $PSScriptRoot 'Check-Windows.ps1') -SavedReceipt 'synthetic-unused.json'
$Case=$selected;$script:starts=0;$script:closed=0;$script:reads=0
function Require($Value,$Reason){if(-not $Value){throw $Reason}}
if($Case -like 'role_*') {
    Add-Type -Path (Join-Path $PSScriptRoot 'PythonOwnership.cs')
    function Identity($Number,$Parent,$Time,$Image) {
        $value=New-Object ContractPython+Identity
        $value.pid=$Number;$value.parent_pid=$Parent;$value.created=$Time;$value.image=$Image
        return $value
    }
    $redirector=Identity 200 100 2000 'C:\ResolenaExperiments\uc001-validator-env\Scripts\python.exe'
    $python=Identity 300 200 3000 'C:\ResolenaExperiments\tools\python-3.12.10\python.exe'
    $helper=Identity 400 200 2500 'C:\Windows\System32\conhost.exe'
    $rows=@($helper,$python);$expected=$null
    switch($Case) {
        role_helper_pending {$rows=@($helper)}
        role_no_helper {$rows=@($python)}
        role_helper_python_parent {$helper.parent_pid=300;$helper.created=3500}
        role_wrong_path {$helper.image='C:\other\conhost.exe';$expected='unexpected_owned_process'}
        role_wrong_python {$python.image='C:\other\python.exe';$expected='unexpected_owned_process'}
        role_unknown {$rows+=@(Identity 500 200 2500 'C:\other.exe');$expected='unexpected_owned_process'}
        role_ambiguous {$rows+=@(Identity 301 200 3100 $python.image);$expected='interpreter_ambiguous'}
        role_bad_parent {$helper.parent_pid=999;$expected='console_helper_constraints'}
        role_bad_time {$helper.created=1500;$expected='console_helper_constraints'}
        role_duplicate_helper {$rows+=@(Identity 401 200 2600 $helper.image);$expected='console_helper_ambiguous'}
        role_reused_helper {$helper.created=0;$expected='console_helper_constraints'}
    }
    $accepted=New-Object 'System.Collections.Generic.List[string]'
    $accept=[Action[ContractPython+Identity,string]]{param($Identity,$Role)$accepted.Add($Role)}
    try {
        $roles=[ContractPython]::AccountMembers($redirector,$rows,'C:\Windows\System32\conhost.exe',$accept)
        Require ($null -eq $expected) 'Invalid roles accepted'
        if($Case -eq 'role_helper_pending'){Require ($null -eq $roles.interpreter -and $accepted.Contains('console_helper')) 'Helper substituted for interpreter'}
        else {Require ($roles.interpreter.pid -eq 300) 'Interpreter not uniquely identified'}
    } catch {
        if($null -eq $expected -or $_.Exception.ToString() -notmatch ('ownership/'+$expected)){throw}
        if($Case -eq 'role_unknown'){Require ($accepted.Contains('console_helper')) 'Verified helper lost before partial failure'}
    }
    'PASS '+$Case;return
}
if($Case -eq 'layout') {
    Add-Type -Path (Join-Path $PSScriptRoot 'PythonOwnership.cs')
    foreach($pair in @(@('Startup',104),@('StartupEx',112),@('Basic',48),@('Security',24))) {
        $type=[ContractPython].GetNestedType($pair[0],[Reflection.BindingFlags]::NonPublic)
        Require ([Runtime.InteropServices.Marshal]::SizeOf([Activator]::CreateInstance($type)) -eq $pair[1]) ('Wrong x64 layout '+$pair[0])
    }
    'PASS '+$Case;return
}
function Assert-ContractWindows {}
function Assert-ContractBundle {}
function Assert-HarnessBundle {}
function Initialize-PythonOwnership {}
function New-ContractJob {return 'synthetic-only-job'}
function New-LocalDeadline($Job) {
    $value=[pscustomobject]@{Job=$Job}
    $value|Add-Member ScriptMethod Arm {param($Milliseconds) Require ($Milliseconds -eq 45000) 'Diagnostic timer changed'}
    $value|Add-Member ScriptMethod Close {$script:closed++;return ($Case -ne 'job_close_failure')}
    return $value
}
function Owner([int]$Number) {
    $value=[pscustomobject]@{Id=$Number;HasExited=$false}
    $value|Add-Member ScriptMethod Refresh {}
    $value|Add-Member ScriptMethod WaitForExit {param($Milliseconds) return (($this.Id -ne 300 -or $Case -notin @('cleanup_failure','identified_exit_unconfirmed')) -and ($this.Id -ne 400 -or $Case -ne 'helper_cleanup_unconfirmed'))}
    $value|Add-Member ScriptMethod Dispose {}
    return $value
}
function Assert-HarnessDeadline($Clock,$Limit,$Reason) {if(($Case -eq 'deadline' -or ($Case -eq 'helper_deadline' -and $script:reads -gt 0)) -and $Limit -eq 45000){throw 'deadline/ownership_expired'}}
function Get-HarnessElapsedMilliseconds($Clock) {if($Case -eq 'primary_cleanup_deadline'){return 60000};return $Clock.ElapsedMilliseconds}
function Start-OwnedPython($Job,$Arguments,$Root) {
    $script:starts++
    Require ($Arguments.Contains('"-I" "-X" "utf8" "-B"')) 'Wrong isolated interpreter arguments'
    $rootProcess=Owner 200;$child=Owner 300
    $rootProcess|Add-Member NoteProperty Interpreter $child
    $rootProcess|Add-Member NoteProperty RedirectorIdentity ([pscustomobject]@{pid=200;created=2000})
    $rootProcess|Add-Member NoteProperty LastProof ([pscustomobject]@{interpreter=@{pid=300;created=3000}})
    $rootProcess|Add-Member NoteProperty InterpreterIdentity ([pscustomobject]@{pid=300;created=3000})
    $rootProcess|Add-Member NoteProperty BindingStage 'job_members'
    $rootProcess|Add-Member NoteProperty LastJobMembers @(200,300)
    $rootProcess|Add-Member NoteProperty LastCandidate ([pscustomobject]@{pid=300;created=3000;parent_pid=200;image='C:\synthetic-private-image'})
    $rootProcess|Add-Member NoteProperty ConsoleHelpers @()
    $rootProcess|Add-Member NoteProperty ConsoleHostPath 'C:\Windows\System32\conhost.exe'
    if($Case -like 'helper_*') {
        $helperIdentity=[pscustomobject]@{pid=400;created=2500;parent_pid=200;image='C:\Windows\System32\conhost.exe'}
        $rootProcess.ConsoleHelpers=@([pscustomobject]@{identity=$helperIdentity;process=(Owner 400)})
        $rootProcess.LastJobMembers=@(200,300,400)
        if($Case -in @('helper_cleanup_partial','helper_deadline')) {
            $rootProcess.Interpreter=$null;$rootProcess.InterpreterIdentity=$null;$rootProcess.LastProof=$null
            $rootProcess.LastJobMembers=@(200,400);$rootProcess.BindingStage='interpreter_pending'
        }
        if($Case -eq 'helper_missing_identity'){$rootProcess.ConsoleHelpers[0].identity=$null}
        if($Case -eq 'helper_unknown_member'){$rootProcess.LastJobMembers+=@(999)}
    }
    if($Case -in @('primary_cleanup','primary_cleanup_deadline','private_error','private_code_error','wrapped_native_error')) {
        $rootProcess.Interpreter=$null;$rootProcess.InterpreterIdentity=$null;$rootProcess.LastProof=$null
    }
    if($Case -in @('identified_before_proof','identified_exit_unconfirmed')) {$rootProcess.LastProof=$null}
    $stdin=[pscustomobject]@{};$stdin|Add-Member ScriptMethod WriteLine {param($Text)};$stdin|Add-Member ScriptMethod Flush {}
    $rootProcess|Add-Member NoteProperty StandardInput $stdin
    [IO.File]::WriteAllText((Join-Path $Root 'worker-result.json'),(@{outcome=$(if($Case -eq 'worker_failure'){'failed'}else{'model_free_worker_checks_passed'});cli_execution_verified=$false}|ConvertTo-Json))
    return $rootProcess
}
function Get-OwnedPythonProof {
    $script:reads++
    if($Case -eq 'helper_deadline'){return $null}
    if($Case -eq 'helper_cleanup_partial'){throw 'ownership/supervisor_identity_mismatch'}
    if($Case -eq 'membership_failure'){throw 'ownership/job_membership_failed'}
    if($Case -in @('primary_cleanup','primary_cleanup_deadline')){throw 'ownership/job_query_failed'}
    if($Case -eq 'private_error'){throw 'SyntheticSecret raw details; never share'}
    if($Case -eq 'private_code_error'){throw 'ownership/syntheticsecrettoken'}
    if($Case -eq 'wrapped_native_error'){throw [IO.IOException]::new('ownership/job_query_failed',[ComponentModel.Win32Exception]::new(5))}
    if($Case -in @('identified_before_proof','identified_exit_unconfirmed')){throw 'ownership/supervisor_identity_mismatch'}
    return [pscustomobject]@{interpreter=@{pid=$(if($Case -eq 'wrong_identity' -and $script:reads -gt 1){301}else{300});created=3000}}
}
$temp=Join-Path ([IO.Path]::GetTempPath()) ('uc001-harness-synthetic-'+[guid]::NewGuid())
$null=New-Item -ItemType Directory -Path $temp
try {
    $result=Invoke-ModelFreeHarnessCheck 'synthetic-unused.json' $temp
    Require ($script:starts -eq 1 -and $script:closed -eq 1) ('Owned launch/close path bypassed; starts='+$script:starts+' closed='+$script:closed+' stop='+($result.stop|ConvertTo-Json -Compress))
    Require (-not $result.startup_authorized -and -not $result.model_attempt_ledger_touched) 'Model allowance changed'
    $cleanup=Read-ContractJson (Join-Path $temp 'cleanup.json')
    if($Case -like 'helper_*') {
        Require ($cleanup.owned_exits.Count -eq 3) 'Helper omitted from cleanup'
        Require ($result.outcome -eq $(if($Case -eq 'helper_success'){'model_free_harness_checks_passed'}else{'failed'})) 'Unexpected helper outcome'
        $helper=$cleanup.owned_exits[2]
        Require ($helper.role -eq 'console_helper') 'Helper role missing'
        if($Case -ne 'helper_missing_identity'){Require ($helper.pid -eq 400 -and $helper.created -eq 2500) 'Verified helper lifetime lost'}
        if($Case -eq 'helper_success'){Require ($result.cleanup_confirmed -and $helper.exit_confirmed) 'Helper cleanup not confirmed'}
        if($Case -in @('helper_cleanup_partial','helper_deadline')) {
            Require ($helper.exit_confirmed -and $cleanup.owned_exits[1].identity_state -eq 'not_identified') 'Helper-only cleanup invented Python identity'
            Require ($result.primary_failure.reason -eq $(if($Case -eq 'helper_deadline'){'ownership_expired'}else{'supervisor_identity_mismatch'})) 'Primary failure lost'
            Require ($result.cleanup_failures.Count -eq 1) 'Missing interpreter cleanup accepted'
            if($Case -eq 'helper_deadline'){Require ($script:reads -eq 1 -and $result.deadline_failures.Count -eq 1) 'Helper caused success or bypassed deadline'}
        }
        if($Case -eq 'helper_cleanup_unconfirmed'){Require (-not $helper.exit_confirmed -and $helper.identity_state -eq 'identified') 'Unconfirmed helper exit hidden'}
        if($Case -eq 'helper_missing_identity'){Require ($helper.identity_state -eq 'not_identified' -and -not $helper.exit_confirmed) 'Missing helper identity accepted'}
        if($Case -eq 'helper_unknown_member'){Require ($cleanup.unidentified_job_pids -contains 999 -and $cleanup.errors -contains 'cleanup/member_identity_unavailable') 'Unidentified extra member silently accepted'}
        'PASS '+$Case;return
    }
    Require ($cleanup.owned_exits.Count -eq 2) 'Actual interpreter was omitted from cleanup'
    if($Case -in @('primary_cleanup','primary_cleanup_deadline','private_error','private_code_error','wrapped_native_error','identified_before_proof','identified_exit_unconfirmed')) {
        Require ($result.outcome -eq 'failed') 'Primary binding failure was accepted'
        if($Case -eq 'identified_before_proof'){Require ($cleanup.owned_exits[1].exit_confirmed) 'Retained interpreter ignored because LastProof is absent'}
        Require ($null -ne $result.primary_failure -and $result.primary_failure.stage -eq 'ownership') 'Primary failure lost to cleanup'
        Require ($result.stop.reason -eq $result.primary_failure.reason) 'Compatibility stop discarded initiating failure'
        Require ($result.ownership -eq $null) 'Failed binding was reported as verified ownership'
        Require ($result.binding_observation.step -eq 'job_members') 'Binding observation was lost'
        if($Case -eq 'identified_before_proof') {
            Require ($result.cleanup_failures.Count -eq 0 -and $result.cleanup_confirmed) 'Identified interpreter ignored because LastProof is absent'
            Require ($cleanup.owned_exits[1].identity_state -eq 'identified' -and $cleanup.owned_exits[1].exit_confirmed) 'Identified interpreter exit not confirmed'
        } elseif($Case -eq 'identified_exit_unconfirmed') {
            Require ($cleanup.owned_exits[1].identity_state -eq 'identified' -and $cleanup.owned_exits[1].pid -eq 300 -and -not $cleanup.owned_exits[1].exit_confirmed) 'Known identity lost on exit failure'
            Require ($result.cleanup_failures.Count -eq 1) 'Cleanup failure lost'
        } else {
            Require ($cleanup.owned_exits[1].identity_state -eq 'not_identified' -and $null -eq $cleanup.owned_exits[1].pid) 'Unknown interpreter identity was invented'
            Require ($cleanup.owned_exits[1].exit_confirmation -eq 'unavailable' -and $result.cleanup_failures.Count -eq 1) 'Missing identity conflated with measured failed exit'
        }
        if($Case -eq 'primary_cleanup_deadline') {Require ($result.deadline_failures.Count -eq 1) 'Independent deadline failure lost'}
        if($Case -eq 'private_error') {
            Require (-not ([IO.File]::ReadAllText((Join-Path $temp 'result.json')).Contains('SyntheticSecret'))) 'Raw details leaked publicly'
            Require ([IO.File]::ReadAllText((Join-Path $temp 'private\primary-error.txt')).Contains('SyntheticSecret')) 'Raw failure not retained privately'
        }
        if($Case -eq 'private_code_error') {
            Require ($result.primary_failure.reason -eq 'unexpected_failure') 'Unknown code-shaped raw message was exposed as a reason'
            Require (-not ([IO.File]::ReadAllText((Join-Path $temp 'result.json')).Contains('syntheticsecrettoken'))) 'Code-shaped raw details leaked publicly'
            Require ([IO.File]::ReadAllText((Join-Path $temp 'private\primary-error.txt')).Contains('syntheticsecrettoken')) 'Code-shaped raw error not preserved privately'
        }
        if($Case -eq 'wrapped_native_error') {
            Require ($result.primary_failure.reason -eq 'job_query_failed') 'Outer safe API code discarded for raw inner error'
            Require ($result.primary_failure.native_status.domain -eq 'win32' -and $result.primary_failure.native_status.code -eq 5) 'Native status missing from sanitized result'
        }
        'PASS '+$Case;return
    }
    Require ($cleanup.owned_exits[0].created -eq 2000 -and $cleanup.owned_exits[1].created -eq 3000) 'Creation-time cleanup evidence omitted'
    if($Case -eq 'success'){Require ($result.outcome -eq 'model_free_harness_checks_passed') 'Synthetic model-free path failed'}
    else {Require ($result.outcome -eq 'failed') 'Synthetic failure was accepted'}
    if($Case -eq 'cleanup_failure'){Require (-not $cleanup.owned_exits[1].exit_confirmed) 'Unconfirmed interpreter cleanup hidden'}
    if($Case -eq 'job_close_failure'){Require (-not $cleanup.owned_job_closed) 'Failed job closure hidden'}
    'PASS '+$Case
} finally {Remove-Item -LiteralPath $temp -Recurse -Force}
