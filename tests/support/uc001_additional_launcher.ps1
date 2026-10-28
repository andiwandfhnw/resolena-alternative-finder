param([string]$Case,[switch]$Corrected)
$selected=$Case;$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$source=Join-Path $PSScriptRoot '../../scripts/uc001_contract_local_v1_3_0'
if($Corrected){$source=Join-Path $PSScriptRoot '../../scripts/uc001_contract_local_v1_4_0'}
$parent=Join-Path $source '../uc001_execution_v1_3_0'
. (Join-Path $parent 'Common.ps1')
. (Join-Path $parent 'Run-Windows.ps1') -Codespace synthetic
. (Join-Path $source 'Run-Windows.ps1')
. (Join-Path $source 'Python-Ownership.ps1')
$Case=$selected;$script:starts=0;$script:workers=0;$script:closed=0;$script:assets=0;$script:proofs=0;$script:now=0
$script:state=[pscustomobject]@{case=1;phase='ready'}
$temp=Join-Path ([IO.Path]::GetTempPath()) ('uc001-additional-synthetic-'+[guid]::NewGuid())
function Require($Value,$Reason){if(-not $Value){throw $Reason}}
function Owner([int]$Number) {
    $value=[pscustomobject]@{Id=$Number;StartTime=[DateTime]::UtcNow;HasExited=$false;ExitCode=0}
    $value|Add-Member ScriptMethod Refresh {}
    $value|Add-Member ScriptMethod WaitForExit {param($Milliseconds)return ($this.Id -ne 400 -or $Case -ne 'cleanup_failure')}
    $value|Add-Member ScriptMethod Dispose {}
    $stdin=[pscustomobject]@{};$stdin|Add-Member ScriptMethod Close {};$stdin|Add-Member ScriptMethod Flush {}
    $stdin|Add-Member ScriptMethod WriteLine {
        param($Text)
        if($Text -match '^begin (\d+)$') {
            Require ($script:guard.Arms -eq [int]$Matches[1]) 'Generation began without independent timer'
            $script:state=[pscustomobject]@{case=[int]$Matches[1];phase='validated'}
            if($Case -eq 'late_validation'){$script:now=90000}
        } elseif($Text -match '^advance (\d+)$') {
            $id=[int]$Matches[1];Require ($script:guard.Disarms -eq $id) 'Next generation acknowledged before validation'
            $script:state=[pscustomobject]@{case=$(if($id -eq 14){14}else{$id+1});phase=$(if($id -eq 14){'complete'}else{'ready'})}
            if($id -eq 14){$script:worker.HasExited=$true}
        }
    }
    $value|Add-Member NoteProperty StandardInput $stdin
    return $value
}
function Assert-ContractWindows {}
function Assert-ContractBundle {}
function Set-LocalPrivateDirectory {}
function Invoke-LocalPythonPreflight($ReviewPath,$ApprovalPath) {
    Require ($ApprovalPath -eq 'explicit-synthetic-approval.json') 'Approval not wired to preflight'
    if($Case -eq 'approval_pending'){throw 'startup/approval_or_preflight_failed'}
}
function Get-ContractAssets {$script:assets++}
function Get-ContractAdapter {return [pscustomobject]@{Name='synthetic-only'}}
function Get-CimInstance {return}
function Get-NetTCPConnection {if($script:starts){return [pscustomobject]@{LocalAddress='127.0.0.1';LocalPort=49187;OwningProcess=101}}}
function Read-ContractJson($Path) {
    $value=[IO.File]::ReadAllText($Path)|ConvertFrom-Json
    if($Path.EndsWith('config.json')){$value.reuse_root=Join-Path $temp 'assets'}
    return $value
}
function Get-ContractResources {
    return @{ram_free=24GB;gpu_free=$(if($Case -eq 'resource_failure' -and $script:starts){0}else{15GB});disk_free=10GB;owned_gpu=1GB;owned_rss=1GB;artifact_bytes=0}
}
function Initialize-PythonOwnership {}
function New-ContractJob {return 'explicit-synthetic-job'}
function New-LocalDeadline($Job) {
    $value=[pscustomobject]@{Job=$Job;Arms=0;Disarms=0}
    $value|Add-Member ScriptMethod Arm {param($Milliseconds)Require ($Milliseconds -eq 90000) 'Request limit changed';$this.Arms++}
    $value|Add-Member ScriptMethod Disarm {$this.Disarms++}
    $value|Add-Member ScriptMethod Close {$script:closed++;return $true}
    $script:guard=$value;return $value
}
function Get-LocalElapsed($Clock){if($Case -eq 'late_validation'){return $script:now};return $Clock.Elapsed.TotalMilliseconds}
function Read-LocalProgress {return $script:state}
function Start-ContractProcess($Job,$Executable,$Arguments,$Stdout,$Stderr,$Key) {
    $script:starts++;Require ($script:starts -eq 1 -and $Executable.EndsWith('llama-server.exe')) 'Extra/incorrect model startup'
    Require ($Arguments.Contains('"--predict" "3072"') -and $Arguments.Contains('"--host" "127.0.0.1"')) 'Actual launch settings changed'
    Require (-not $Arguments.Contains($Key)) 'Authentication leaked into argv'
    [IO.File]::WriteAllText($Stderr,'explicit synthetic settings log')
    return (Owner 101)
}
function Start-OwnedPython($Job,$Arguments,$Root) {
    $script:workers++
    Require ($Job -eq 'explicit-synthetic-job') 'Capture not in owned job'
    Require ($Arguments.Contains('"-I" "-X" "utf8" "-B"') -and $Arguments.Contains('"--supervised-capture"') -and $Arguments.Contains('"--approval" "explicit-synthetic-approval.json"')) 'Wrong launcher-to-capture argv'
    Require ($Arguments.Contains($(if($Corrected){'uc001_contract_local_v1_4_0'}else{'uc001_contract_local_v1_3_0'}))) 'Old capture module used'
    $worker=Owner 200
    $worker|Add-Member NoteProperty RedirectorIdentity ([pscustomobject]@{pid=200;created=2000})
    $worker|Add-Member NoteProperty Interpreter (Owner 300)
    $worker|Add-Member NoteProperty InterpreterIdentity ([pscustomobject]@{pid=300;created=3000})
    $worker|Add-Member NoteProperty ConsoleHelpers @([pscustomobject]@{identity=[pscustomobject]@{pid=400;created=2500};process=(Owner 400)})
    $worker|Add-Member NoteProperty LastJobMembers @(101,200,300,400)
    if($Corrected) {
        $worker.RedirectorIdentity=[pscustomobject]@{pid=200;created=$worker.StartTime.ToFileTimeUtc();parent_pid=$PID;image='C:\ResolenaExperiments\uc001-validator-env\Scripts\python.exe'}
        $worker.InterpreterIdentity=[pscustomobject]@{pid=300;created=$worker.RedirectorIdentity.created+20;parent_pid=200;image='C:\ResolenaExperiments\tools\python-3.12.10\python.exe'}
        $worker|Add-Member NoteProperty ServerIdentity $script:fullServer
        $worker.ConsoleHelpers=@(
            [pscustomobject]@{identity=[pscustomobject]@{pid=400;created=$worker.RedirectorIdentity.created+10;parent_pid=200;image='C:\Windows\System32\conhost.exe'};process=(Owner 400)},
            [pscustomobject]@{identity=[pscustomobject]@{pid=500;created=$script:fullServer.created+10;parent_pid=101;image='C:\Windows\System32\conhost.exe'};process=(Owner 500)})
        $worker.LastJobMembers=@(101,200,300,400,500)
        $worker|Add-Member NoteProperty ObservedMembers @()
        $worker|Add-Member ScriptMethod Bind {param($Job,$SupervisorId,$Server,$Expected,$Path)
            $script:proofs++
            Require ($Server.Id -eq 101 -and $Expected.created -eq $script:fullServer.created -and $Path -ceq $script:fullServer.image -and $Expected.parent_pid -eq $PID) 'Full server identity/trusted executable not wired through actual PS bridge'
            if($Case -eq 'binding_partial'){throw 'ownership/unexpected_owned_process'}
            return [pscustomobject]@{supervisor=[pscustomobject]@{pid=$PID;created=$script:fullServer.created-100;parent_pid=99;image='C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'};server=$Expected;server_pid=101
                redirector=$this.RedirectorIdentity;interpreter=$this.InterpreterIdentity;console_helpers=@($this.ConsoleHelpers|ForEach-Object {$_.identity})
                job_verified_pids=$this.LastJobMembers;job_membership_verified=$true}
        }
        if($Case -eq 'binding_partial') {
            $physical=$worker.Interpreter;$identity=$worker.InterpreterIdentity
            $worker.Interpreter=$null;$worker.InterpreterIdentity=$null
            $worker.ObservedMembers=@([pscustomobject]@{pid=300;identity=$identity;process=$physical;handle_held=$true;identity_verified=$true;job_verified=$true},
                [pscustomobject]@{pid=600;identity=[pscustomobject]@{pid=600;created=$identity.created+10};process=(Owner 600);handle_held=$true;identity_verified=$true;job_verified=$true})
            $worker.LastJobMembers+=600
        }
    }
    if($Case -eq 'settings_worker_stop'){[IO.File]::WriteAllText((Join-Path $Root 'capture-stopped.json'),'{"stage":"settings","reason":"sampling_mismatch"}')}
    $script:worker=$worker;return $worker
}
if(-not $Corrected){
function Get-OwnedPythonProof($Launch,$Job,$SupervisorId,$ServerId) {
    $script:proofs++;Require ($ServerId -eq 101 -and $SupervisorId -eq $PID) 'Native binding got wrong server/supervisor'
    return [pscustomobject]@{redirector=$Launch.RedirectorIdentity;interpreter=$Launch.InterpreterIdentity;console_helpers=@($Launch.ConsoleHelpers[0].identity)}
}
}
if($Corrected) {
    function Read-LocalServerIdentity($Server,$Job) {
        $script:fullServer=[pscustomobject]@{pid=$Server.Id;created=$Server.StartTime.ToFileTimeUtc();parent_pid=$PID;image=$runtimeExecutable}
        return $script:fullServer
    }
}
function New-ContractHttpClient {$value=[pscustomobject]@{};$value|Add-Member ScriptMethod Dispose {};return $value}
$propsJson='{"total_slots":1,"build_info":"explicit-synthetic","model_path":"explicit-synthetic","default_generation_settings":{"n_ctx":8192,"params":{"n_predict":-1}}}'
function Get-Http($Path,$Token) {
    $content=[pscustomobject]@{};$content|Add-Member ScriptMethod ReadAsStringAsync {
        $task=[pscustomobject]@{};$task|Add-Member ScriptMethod GetAwaiter {
            $awaiter=[pscustomobject]@{};$awaiter|Add-Member ScriptMethod GetResult {return $propsJson};return $awaiter
        };return $task
    }
    $value=[pscustomobject]@{StatusCode=$(if($Path -eq '/props' -or $Token.Length -ge 32){200}else{401});Content=$content}
    $value|Add-Member ScriptMethod Dispose {};return $value
}
try {
    $freeze=[IO.File]::ReadAllText((Join-Path $source 'freeze.json'))|ConvertFrom-Json
    $original=Join-Path $temp ('uc001-contract-runs/'+$freeze.original_attempt_identity)
    $null=New-Item -ItemType Directory -Path $original
    [IO.File]::WriteAllText((Join-Path $original 'preserved.txt'),'explicit synthetic historical marker')
    if($Corrected) {
        $previous=Join-Path $temp ('uc001-contract-runs/'+$freeze.previous_attempt_identity)
        $null=New-Item -ItemType Directory -Path $previous
        [IO.File]::WriteAllText((Join-Path $previous 'preserved.txt'),'explicit synthetic historical second attempt')
    }
    $run=Join-Path $temp ('uc001-contract-runs/'+$freeze.attempt_identity)
    if($Case -eq 'existing_attempt'){$null=New-Item -ItemType Directory -Path $run}
    $failed=$false
    try {Invoke-LocalExecution 'explicit-synthetic-review.json' 'explicit-synthetic-approval.json'} catch {$failed=$true}
    Require ([IO.File]::ReadAllText((Join-Path $original 'preserved.txt')) -eq 'explicit synthetic historical marker') 'Original attempt changed'
    if($Case -in @('approval_pending','existing_attempt')) {
        Require ($failed -and $script:starts -eq 0 -and $script:workers -eq 0) 'Unapproved/reserved attempt started'
        if($Case -eq 'approval_pending'){Require ($script:assets -eq 0) 'Pending approval reached asset checks'}
    } else {
        Require ($script:starts -eq 1 -and $script:closed -eq 1) 'Startup/cleanup dispatch mismatch'
        if($Corrected){Require ((Read-ContractJson (Join-Path $run 'reservation.json')).previous_attempt_identity -eq $freeze.previous_attempt_identity) 'Previous attempt link omitted'}
        $launch=Read-ContractJson (Join-Path $run 'startup-attempt.json')
        Require ($launch.original_attempt_identity -eq $freeze.original_attempt_identity -and $launch.startup_attempt -eq 1 -and $launch.launch_args -contains '--predict') 'Prospective argv/link missing'
        Require (-not (Test-Path -LiteralPath (Join-Path $original 'attempts.jsonl'))) 'Historical zero ledger invented'
        $result=Read-ContractJson (Join-Path $run 'export/execution-result.json')
        if($Case -eq 'success') {
            Require (-not $failed -and $result.completed) 'Actual proposed launcher failed with explicit substitutes'
            Require ($script:guard.Arms -eq 14 -and $script:guard.Disarms -eq 14 -and $script:proofs -gt 1) 'Ownership or per-request deadline checks bypassed'
            foreach($id in 1..14){Require (Test-Path (Join-Path $run ('export/accepted-{0:00}.json' -f $id))) 'Missing validation acknowledgment'}
            Require ((Read-ContractJson (Join-Path $run 'cleanup.json')).owned_exits.Count -eq $(if($Corrected){5}else{4})) 'Owned helper omitted from actual cleanup'
        } else {
            Require ($failed -and -not $result.completed) 'Failure accepted as success'
            if($Corrected -and $Case -eq 'binding_partial') {
                Require ($result.primary_failure.reason -eq 'unexpected_owned_process' -and -not $result.cleanup_confirmed) 'Partial binding failure lost'
                $cleanup=Read-ContractJson (Join-Path $run 'cleanup.json')
                $observed=@($cleanup.owned_exits|Where-Object {$_.PSObject.Properties['role_approved']})
                Require ($observed.Count -eq 2 -and @($observed|Where-Object {$_.role_approved -or -not $_.exit_confirmed}).Count -eq 0) 'Partial binding lost unapproved held exits'
            }
            if($Case -eq 'cleanup_failure'){Require ($result.cleanup_failures.Count -eq 1) 'Cleanup failure lost'}
            if($Case -eq 'settings_worker_stop'){Require ($script:guard.Arms -eq 0 -and $result.primary_failure.reason -eq 'check_failed') 'Worker validation failure did not stop before generation'}
        }
    }
    if($Corrected) {
        Require ([IO.File]::ReadAllText((Join-Path $previous 'preserved.txt')) -eq 'explicit synthetic historical second attempt') 'Second consumed attempt changed'
        Require (-not (Test-Path -LiteralPath (Join-Path $previous 'attempts.jsonl'))) 'Second historical zero ledger invented'
    }
    'PASS '+$Case
} finally {if(Test-Path -LiteralPath $temp){Remove-Item -LiteralPath $temp -Recurse -Force}}
