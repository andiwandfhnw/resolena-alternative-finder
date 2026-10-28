param([string]$Case)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$source=Join-Path $PSScriptRoot '../../scripts/uc001_combined_ownership_v1_1_0'
function Require($Value,$Reason){if(-not $Value){throw $Reason}}
if($Case -in @('combined','helper_before_interpreter','python_interpreter_parent','wrong_parent','wrong_path','unknown','ambiguous_python','duplicate_branch','server_parent','server_path','server_time')) {
    Add-Type -Path (Join-Path $source 'PythonOwnership.cs')
    function Identity($PidValue,$Parent,$Created,$Image) {
        $row=New-Object ContractPython+Identity;$row.pid=$PidValue;$row.parent_pid=$Parent;$row.created=$Created;$row.image=$Image;return $row
    }
    $supervisor=Identity 100 99 1000 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
    $shell=$supervisor.image
    $server=Identity 101 100 1500 $shell
    $root=Identity 200 100 2000 'C:\ResolenaExperiments\uc001-validator-env\Scripts\python.exe'
    $python=Identity 300 200 3000 'C:\ResolenaExperiments\tools\python-3.12.10\python.exe'
    $console='C:\Windows\System32\conhost.exe'
    $left=Identity 501 101 1600 $console;$right=Identity 401 200 2500 $console
    $rows=@($left,$right,$python);$reason=$null
    switch($Case) {
        helper_before_interpreter {$rows=@($left,$right)}
        python_interpreter_parent {$right.parent_pid=300;$right.created=3100}
        wrong_parent {$left.parent_pid=999;$reason='console_helper_constraints'}
        wrong_path {$left.image='C:\fake\conhost.exe';$reason='unexpected_owned_process'}
        unknown {$rows+=@(Identity 601 101 3500 'C:\unknown.exe');$reason='unexpected_owned_process'}
        ambiguous_python {$rows+=@(Identity 301 200 3100 $python.image);$reason='interpreter_ambiguous'}
        duplicate_branch {$left.parent_pid=300;$left.created=3100;$reason='console_helper_ambiguous'}
        server_parent {$server.parent_pid=99;$reason='server_identity_mismatch'}
        server_path {$server.image='C:\fake\powershell.exe';$reason='server_identity_mismatch'}
        server_time {$server.created=500;$reason='server_identity_mismatch'}
    }
    $accepted=New-Object 'Collections.Generic.List[string]'
    $accept=[Action[ContractPython+Identity,string]]{param($Identity,$Role)$accepted.Add($Role)}
    $failed=$false
    try {
        [ContractPython]::ValidateServer($server,$supervisor,$shell)
        $roles=[ContractPython]::AccountMembers($root,$rows,$console,$accept,$server)
        Require ($roles.console_helpers.Count -eq 2) 'Both branch helpers not classified'
        Require (($null -eq $roles.interpreter) -eq ($Case -eq 'helper_before_interpreter')) 'Interpreter readiness differs'
    } catch {
        if($null -eq $reason){throw}
        Require ($_.Exception.ToString().Contains('ownership/'+$reason)) ('Unexpected rejection: '+$_.Exception.Message);$failed=$true
    }
    Require ($failed -eq ($null -ne $reason)) 'Invalid role/identity accepted'
    'PASS '+$Case;return
}
$parent=Join-Path $source '../uc001_execution_v1_3_0'
. (Join-Path $parent 'Common.ps1')
. (Join-Path $source 'Python-Ownership.ps1')
function Owner($Number,$Created) {
    $p=[pscustomobject]@{Id=$Number;StartTime=[datetime]::FromFileTimeUtc($Created);WaitCalls=0}
    $p|Add-Member ScriptMethod WaitForExit {param($Milliseconds)$this.WaitCalls++;return ($this.Id -ne 501 -or $Case -ne 'unconfirmed_exit')}
    $p|Add-Member ScriptMethod Dispose {}
    return $p
}
$temp=Join-Path ([IO.Path]::GetTempPath()) ('uc001-branches-synthetic-'+[guid]::NewGuid());$null=New-Item -ItemType Directory -Path $temp
try {
    $serverIdentity=[pscustomobject]@{pid=101;created=[long]1500;parent_pid=$PID;image='C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'}
    if($Case -in @('both_validators','validator_failure','deadline_failure','primary_cleanup_deadline')) {
        $script:serverFixture=$serverIdentity
        . (Join-Path $source 'Check-CombinedOwnership.ps1')
        $null=New-Item -ItemType Directory -Path (Join-Path $temp 'private')
        function Initialize-PythonOwnership {}
        function New-ContractJob {return 'explicit synthetic job'}
        function New-CombinedGuard($Job) {
            $value=[pscustomobject]@{Job=$Job;Expired=($Case -in @('deadline_failure','primary_cleanup_deadline'))};$value|Add-Member ScriptMethod Arm {param($Milliseconds)};return $value
        }
        function Get-CombinedShell {return $script:serverFixture.image}
        function Read-CombinedSupervisor {return [pscustomobject]@{pid=$PID;created=500;parent_pid=99;image=(Get-CombinedShell)}}
        function Read-CombinedRoot {return $script:serverFixture}
        function Start-ContractProcess {
            $process=Owner 101 1500;$stdin=[pscustomobject]@{};$stdin|Add-Member ScriptMethod Close {}
            $process|Add-Member NoteProperty StandardInput $stdin;return $process
        }
        $script:binds=0;$script:cleanupCalls=0;$script:writes=0
        $script:combinedProof=[pscustomobject]@{supervisor=(Read-CombinedSupervisor);server=$script:serverFixture;server_pid=101
            redirector=[pscustomobject]@{pid=200;created=2000;parent_pid=$PID;image='C:\ResolenaExperiments\uc001-validator-env\Scripts\python.exe'}
            interpreter=[pscustomobject]@{pid=300;created=3000;parent_pid=200;image='C:\ResolenaExperiments\tools\python-3.12.10\python.exe'}
            console_helpers=@([pscustomobject]@{pid=501;created=1600;parent_pid=101;image='C:\Windows\System32\conhost.exe'},[pscustomobject]@{pid=401;created=2500;parent_pid=200;image='C:\Windows\System32\conhost.exe'})
            job_verified_pids=@(101,200,300,401,501);job_membership_verified=$true}
        function Start-OwnedPython {
            Write-CombinedJson (Join-Path $temp 'private/python-ready.json') @{pid=300;parent_pid=200}
            $stdin=[pscustomobject]@{}
            $stdin|Add-Member ScriptMethod WriteLine {param($Text)
                $script:writes++;$parsed=$Text|ConvertFrom-Json
                $worker=@{outcome=$(if($Case -in @('validator_failure','primary_cleanup_deadline')){'failed'}else{'python_combined_ownership_verified'});validator='verify_python_ownership';pid=300;parent_pid=200;proof=$parsed}
                Write-CombinedJson (Join-Path $temp 'python-result.json') $worker
            }
            $stdin|Add-Member ScriptMethod Flush {}
            $launch=[pscustomobject]@{Id=200;LastJobMembers=$script:combinedProof.job_verified_pids;RedirectorIdentity=$script:combinedProof.redirector;ConsoleHostPath='C:\Windows\System32\conhost.exe';StandardInput=$stdin
                ObservedMembers=@([pscustomobject]@{pid=300;identity=$script:combinedProof.interpreter;identity_verified=$true;job_verified=$true})}
            $launch|Add-Member ScriptMethod Observe {param($Job,$ServerPid)}
            $launch|Add-Member ScriptMethod Bind {param($Job,$Supervisor,$Server,$Expected,$Path)
                Require ($Server.Id -eq 101 -and $Expected.created -eq 1500 -and $Expected.parent_pid -eq $PID -and $Path -ceq $script:serverFixture.image) 'Full server identity not passed to native binder'
                $script:binds++;return $script:combinedProof
            }
            return $launch
        }
        function Complete-OwnedPythonCleanup {param($Client,$Job,$Server,$Launch,$Root,$FullServer)
            $script:cleanupCalls++;Require ($FullServer.created -eq 1500) 'Full server identity not retained for cleanup'
            if($Case -eq 'primary_cleanup_deadline'){throw 'cleanup/exit_unconfirmed'}
            Write-CombinedJson (Join-Path $Root 'cleanup.json') @{owned_job_closed=$true;errors=@();owned_exits=@()}
        }
        $result=Invoke-CombinedCheck $temp
        if($script:writes -ne 1){$result|ConvertTo-Json -Depth 14;Get-Content -LiteralPath (Join-Path $temp 'private/primary.txt')}
        Require ($script:writes -eq 1 -and $script:cleanupCalls -eq 1) 'Python proof handshake or unconditional cleanup omitted'
        Require ($script:binds -ge 1) 'Native binding omitted'
        if($Case -eq 'primary_cleanup_deadline') {
            Require ($result.primary_failure.reason -eq 'python_validation_failed' -and $result.cleanup_failures[0].reason -eq 'exit_unconfirmed' -and $result.deadline_failures.Count -gt 0) 'Independent failure channels overwritten'
        } elseif($Case -eq 'validator_failure') {
            Require ($result.outcome -eq 'failed' -and $result.primary_failure.reason -eq 'python_validation_failed') 'Native-only pass hid Python failure'
        } elseif($Case -eq 'deadline_failure') {
            Require ($result.outcome -eq 'failed' -and $result.deadline_failures.Count -gt 0) 'Deadline failure hidden by native/Python passes'
        } else {
            Require ($result.outcome -eq 'combined_native_python_and_cleanup_passed' -and $script:binds -ge 2) 'Final fresh native binding or combined acceptance missing'
            Require ($result.python_validator.validator -eq 'verify_python_ownership') 'Python result omitted'
        }
        'PASS '+$Case;return
    }
    function Complete-ContractCleanup($Client,$Job,$Server,$Launch,$Root) {
        [IO.File]::WriteAllText((Join-Path $Root 'cleanup.json'),(@{owned_job_closed=$true;owned_exits=@(@{pid=101;exit_confirmed=$true},@{pid=200;exit_confirmed=$true});errors=@()}|ConvertTo-Json -Depth 8))
    }
    $observations=@()
    foreach($number in @(300,401,501)) {
        $identity=[pscustomobject]@{pid=$number;created=([long]$number*10);parent_pid=$(if($number -eq 501){101}else{200});image='explicit synthetic identity'}
        $observations+=@([pscustomobject]@{pid=$number;identity=$identity;process=(Owner $number $identity.created);handle_held=$true;identity_verified=$true;job_verified=$true})
    }
    if($Case -eq 'missing_identity'){$observations[2].identity=$null;$observations[2].identity_verified=$false}
    $launch=[pscustomobject]@{RedirectorIdentity=[pscustomobject]@{pid=200;created=2000};ServerIdentity=$serverIdentity;InterpreterIdentity=$null;Interpreter=$null;ConsoleHelpers=@();ObservedMembers=$observations;LastJobMembers=@(101,200,300,401,501)}
    if($Case -in @('combined_cleanup','unconfirmed_exit')) {
        $launch.InterpreterIdentity=$observations[0].identity;$launch.Interpreter=$observations[0].process
        $launch.ConsoleHelpers=@([pscustomobject]@{identity=$observations[1].identity;process=$observations[1].process},[pscustomobject]@{identity=$observations[2].identity;process=$observations[2].process})
    }
    $failed=$false
    try {Complete-OwnedPythonCleanup $null 'explicit synthetic job' (Owner 101 1500) $launch $temp $serverIdentity} catch {$failed=$true}
    $cleanup=Read-ContractJson (Join-Path $temp 'cleanup.json')
    Require ($failed -eq ($Case -ne 'combined_cleanup')) 'Cleanup acceptance weakened'
    $serverRow=@($cleanup.owned_exits|Where-Object {$_.pid -eq 101})
    Require ($serverRow.Count -eq 1 -and $serverRow[0].created -eq 1500 -and $serverRow[0].role -eq 'server') 'Server lifetime missing in cleanup proof'
    if($Case -eq 'combined_cleanup') {
        Require ($cleanup.owned_exits.Count -eq 5) 'Both helpers not accounted in cleanup'
        foreach($row in $observations){Require ($row.process.WaitCalls -eq 1) 'Held process wait missing or duplicated'}
    } elseif($Case -eq 'partial_cleanup') {
        $rows=@($cleanup.owned_exits|Where-Object {$_.PSObject.Properties['role_approved']})
        Require ($rows.Count -eq 3 -and @($rows|Where-Object {$_.role_approved}).Count -eq 0 -and @($rows|Where-Object {-not $_.exit_confirmed}).Count -eq 0) 'Partial binding lost independent exits or approved unknown roles'
        Require ($cleanup.errors -contains 'cleanup/interpreter_not_identified') 'Missing interpreter role turned into successful cleanup'
    }
    'PASS '+$Case
} finally {Remove-Item -LiteralPath $temp -Recurse -Force}
