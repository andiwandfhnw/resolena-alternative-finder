param([string]$Case,[switch]$LegacyCleanup)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$source=Join-Path $PSScriptRoot '../../scripts/uc001_combined_ownership'
function Require($Value,$Reason){if(-not $Value){throw $Reason}}
if($Case -in @('combined_rejected','server_parent_rejected','unexpected_rejected')) {
    Add-Type -Path (Join-Path $source 'PythonOwnership.cs')
    function Identity($PidValue,$Parent,$Created,$Image) {
        $row=New-Object ContractPython+Identity;$row.pid=$PidValue;$row.parent_pid=$Parent;$row.created=$Created;$row.image=$Image;return $row
    }
    $redirector=Identity 200 100 2000 'C:\ResolenaExperiments\uc001-validator-env\Scripts\python.exe'
    $python=Identity 300 200 3000 'C:\ResolenaExperiments\tools\python-3.12.10\python.exe'
    $console='C:\Windows\System32\conhost.exe'
    $serverHelper=Identity 501 101 1500 $console
    $pythonHelper=Identity 401 200 2500 $console
    $rows=@($serverHelper,$pythonHelper,$python);$reason='console_helper_ambiguous'
    if($Case -eq 'server_parent_rejected'){$rows=@($serverHelper,$python);$reason='console_helper_constraints'}
    if($Case -eq 'unexpected_rejected'){$rows=@((Identity 601 200 2500 'C:\unknown.exe'),$python);$reason='unexpected_owned_process'}
    $accept=[Action[ContractPython+Identity,string]]{param($Identity,$Role)}
    $failed=$false
    try {$null=[ContractPython]::AccountMembers($redirector,$rows,$console,$accept)} catch {
        Require ($_.Exception.ToString().Contains('ownership/'+$reason)) 'Unexpected rejection';$failed=$true
    }
    Require $failed 'Synthetic branch identities were approved without Windows evidence'
    'PASS '+$Case;return
}
if($Case -eq 'retained_before_classification') {
    $code=Get-Content -LiteralPath (Join-Path $source 'PythonOwnership.cs') -Raw
    Require ($code.Contains('public Observation[] ObservedMembers')) 'Observed handles not retained independently of roles'
    Require ($code.IndexOf('observations.Add(record)') -lt $code.IndexOf('public Ownership Bind(')) 'Retention not in observation path'
    Require ($code.IndexOf('record.identity_verified=false') -lt $code.IndexOf('Identity value=Read(record.process)')) 'Stale identity verification survives a failed fresh query'
    $bind=$code.Substring($code.IndexOf('public Ownership Bind('))
    Require ($bind.IndexOf('Observe(job,serverPid)') -lt $bind.IndexOf('Roles roles=AccountMembers')) 'Classification precedes job observation'
    Require (-not $bind.Contains('finally {foreach(Process process in opened.Values)process.Dispose();}')) 'Rejected handles still disposed before cleanup'
    'PASS '+$Case;return
}
$parent=Join-Path $source '../uc001_execution_v1_3_0'
. (Join-Path $parent 'Common.ps1')
if($LegacyCleanup){. (Join-Path $source '../uc001_contract_local_v1_3_0/Python-Ownership.ps1')}
else {. (Join-Path $source 'Python-Ownership.ps1')}
function Owner($Number) {
    $p=[pscustomobject]@{Id=$Number;WaitCalls=0}
    $p|Add-Member ScriptMethod WaitForExit {param($Milliseconds)$this.WaitCalls++;return ($this.Id -ne 501 -or $Case -ne 'unconfirmed_exit')}
    $p|Add-Member ScriptMethod Dispose {}
    return $p
}
if($Case -eq 'production_dispatch') {
    $code=Get-Content -LiteralPath (Join-Path $source 'Check-CombinedOwnership.ps1') -Raw
    Require ($code.Contains('Start-ContractProcess $job') -and $code.Contains('Start-OwnedPython $job')) 'Not the production combined launching primitives'
    Require ($code.Contains('$launch.Observe($job,$server.Id)') -and $code.Contains('Get-OwnedPythonProof $launch $job $PID $server.Id')) 'Real observation/binding dispatch bypassed'
    Require (-not $code.Contains('llama-server.exe')) 'Diagnostic can launch a model'
    'PASS '+$Case;return
}
$temp=Join-Path ([IO.Path]::GetTempPath()) ('uc001-combined-synthetic-'+[guid]::NewGuid());$null=New-Item -ItemType Directory -Path $temp
function Complete-ContractCleanup($Client,$Job,$Server,$Launch,$Root) {
    [IO.File]::WriteAllText((Join-Path $Root 'cleanup.json'),(@{owned_job_closed=$true;owned_exits=@(@{pid=101;exit_confirmed=$true},@{pid=200;exit_confirmed=$true});errors=@()}|ConvertTo-Json -Depth 8))
}
try {
    if($Case -in @('primary_cleanup_deadline','missing_server_identity')) {
        . (Join-Path $source 'Check-CombinedOwnership.ps1')
        $null=New-Item -ItemType Directory -Path (Join-Path $temp 'private')
        function Initialize-PythonOwnership {}
        function New-ContractJob {return 'explicit synthetic job'}
        function New-CombinedGuard($Job) {
            $value=[pscustomobject]@{Job=$Job;Expired=$false};$value|Add-Member ScriptMethod Arm {param($Milliseconds)};return $value
        }
        function Get-CombinedShell {return 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'}
        function Read-CombinedSupervisor {return [pscustomobject]@{pid=$PID;created=500;parent_pid=99;image=(Get-CombinedShell)}}
        function Read-CombinedRoot {return [pscustomobject]@{pid=101;created=1000;parent_pid=$PID;image=(Get-CombinedShell)}}
        function Start-ContractProcess {
            if($Case -eq 'missing_server_identity'){throw 'Explicit synthetic failure before returned identity'}
            $process=Owner 101;$stdin=[pscustomobject]@{};$stdin|Add-Member ScriptMethod Close {}
            $process|Add-Member NoteProperty StandardInput $stdin;return $process
        }
        function Start-OwnedPython {
            $value=[pscustomobject]@{};$value|Add-Member ScriptMethod Observe {param($Job,$ServerPid)throw 'ownership/console_helper_ambiguous'};return $value
        }
        function Complete-OwnedPythonCleanup {if($Case -ne 'missing_server_identity'){throw 'cleanup/exit_unconfirmed'}}
        $script:elapsedReads=0
        function Get-CombinedElapsed {$script:elapsedReads++;if($script:elapsedReads -le 3){return 0};return 45000}
        $result=Invoke-CombinedCheck $temp
        if($Case -eq 'missing_server_identity') {
            Require (-not $result.cleanup_confirmed -and $result.cleanup_failures[0].reason -eq 'server_identity_unavailable') 'Failed startup with missing identity became confirmed cleanup'
            'PASS '+$Case;return
        }
        Require ($result.primary_failure.stage -eq 'ownership' -and $result.primary_failure.reason -eq 'console_helper_ambiguous') 'Primary ownership rejection lost'
        Require ($result.cleanup_failures.Count -eq 1 -and $result.cleanup_failures[0].reason -eq 'exit_unconfirmed') 'Independent cleanup failure lost'
        Require ($result.deadline_failures.Count -eq 1 -and $result.deadline_failures[0].reason -eq 'overall_expired') 'Independent deadline failure lost'
        'PASS '+$Case;return
    }
    $observations=@()
    foreach($number in @(300,401,501)) {
        $identity=[pscustomobject]@{pid=$number;created=([long]$number*10);parent_pid=$(if($number -eq 501){101}else{200});image='explicit synthetic identity'}
        $observations+=@([pscustomobject]@{pid=$number;identity=$identity;process=(Owner $number);handle_held=$true;identity_verified=$true;job_verified=$true})
    }
    if($Case -eq 'unknown_cleanup'){$observations[1].identity.image='C:\unknown.exe'}
    if($Case -eq 'missing_identity'){$observations[2].identity=$null;$observations[2].identity_verified=$false}
    if($Case -eq 'missing_handle'){$observations[2].handle_held=$false}
    if($Case -eq 'foreign_job'){$observations[2].job_verified=$false}
    $launch=[pscustomobject]@{RedirectorIdentity=[pscustomobject]@{pid=200;created=2000};InterpreterIdentity=$null;Interpreter=$null;ConsoleHelpers=@();ObservedMembers=$observations;LastJobMembers=@(101,200,300,401,501)}
    if($Case -eq 'approved_cleanup') {
        $launch.InterpreterIdentity=$observations[0].identity;$launch.Interpreter=$observations[0].process
        $launch.ConsoleHelpers=@([pscustomobject]@{identity=$observations[1].identity;process=$observations[1].process})
    }
    $failed=$false
    try {Complete-OwnedPythonCleanup $null 'explicit synthetic job' (Owner 101) $launch $temp} catch {$failed=$true}
    $cleanup=Read-ContractJson (Join-Path $temp 'cleanup.json')
    $rows=@($cleanup.owned_exits|Where-Object {$_.PSObject.Properties['role'] -and $_.role -eq 'observed_job_member'})
    if($Case -eq 'approved_cleanup') {
        Require (-not $failed -and $rows.Count -eq 1 -and $rows[0].pid -eq 501 -and -not $rows[0].role_approved) 'Retained unclassified member was omitted or promoted to approved'
        foreach($record in $observations){Require ($record.process.WaitCalls -eq 1) 'Known/observed alias was waited on twice or omitted'}
        'PASS '+$Case;return
    }
    Require $failed 'Missing approved interpreter identity was accepted as ownership success'
    Require ($rows.Count -eq 3) 'Observed handles lost when role classification failed'
    Require (@($rows|Where-Object {$_.role_approved}).Count -eq 0) 'Unknown roles became approved during cleanup'
    if($Case -in @('missing_identity','missing_handle','foreign_job')){Require (-not $rows[2].exit_confirmed -and $rows[2].identity_state -eq 'not_verified') 'Missing identity/handle/job verification turned into confirmed exit'}
    elseif($Case -eq 'unconfirmed_exit'){Require (-not $rows[2].exit_confirmed) 'Unconfirmed observed exit hidden'}
    else {Require (@($rows|Where-Object {-not $_.exit_confirmed}).Count -eq 0) 'Retained native identity exits were not waited on'}
    'PASS '+$Case
} finally {Remove-Item -LiteralPath $temp -Recurse -Force}
