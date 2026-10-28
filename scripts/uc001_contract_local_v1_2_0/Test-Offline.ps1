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
    $value|Add-Member ScriptMethod WaitForExit {param($Milliseconds) return ($this.Id -ne 300 -or $Case -ne 'cleanup_failure')}
    $value|Add-Member ScriptMethod Dispose {}
    return $value
}
function Assert-HarnessDeadline($Clock,$Limit,$Reason) {if($Case -eq 'deadline' -and $Limit -eq 45000){throw 'deadline/ownership_expired'}}
function Start-OwnedPython($Job,$Arguments,$Root) {
    $script:starts++
    Require ($Arguments.Contains('"-I" "-X" "utf8" "-B"')) 'Wrong isolated interpreter arguments'
    $rootProcess=Owner 200;$child=Owner 300
    $rootProcess|Add-Member NoteProperty Interpreter $child
    $rootProcess|Add-Member NoteProperty RedirectorIdentity ([pscustomobject]@{pid=200;created=2000})
    $rootProcess|Add-Member NoteProperty LastProof ([pscustomobject]@{interpreter=@{pid=300;created=3000}})
    $stdin=[pscustomobject]@{};$stdin|Add-Member ScriptMethod WriteLine {param($Text)};$stdin|Add-Member ScriptMethod Flush {}
    $rootProcess|Add-Member NoteProperty StandardInput $stdin
    [IO.File]::WriteAllText((Join-Path $Root 'worker-result.json'),(@{outcome=$(if($Case -eq 'worker_failure'){'failed'}else{'model_free_worker_checks_passed'});cli_execution_verified=$false}|ConvertTo-Json))
    return $rootProcess
}
function Get-OwnedPythonProof {
    $script:reads++
    if($Case -eq 'membership_failure'){throw 'ownership/job_membership_failed'}
    return [pscustomobject]@{interpreter=@{pid=$(if($Case -eq 'wrong_identity' -and $script:reads -gt 1){301}else{300});created=3000}}
}
$temp=Join-Path ([IO.Path]::GetTempPath()) ('uc001-harness-synthetic-'+[guid]::NewGuid())
$null=New-Item -ItemType Directory -Path $temp
try {
    $result=Invoke-ModelFreeHarnessCheck 'synthetic-unused.json' $temp
    Require ($script:starts -eq 1 -and $script:closed -eq 1) ('Owned launch/close path bypassed; starts='+$script:starts+' closed='+$script:closed+' stop='+($result.stop|ConvertTo-Json -Compress))
    Require (-not $result.startup_authorized -and -not $result.model_attempt_ledger_touched) 'Model allowance changed'
    $cleanup=Read-ContractJson (Join-Path $temp 'cleanup.json')
    Require ($cleanup.owned_exits.Count -eq 2) 'Actual interpreter was omitted from cleanup'
    Require ($cleanup.owned_exits[0].created -eq 2000 -and $cleanup.owned_exits[1].created -eq 3000) 'Creation-time cleanup evidence omitted'
    if($Case -eq 'success'){Require ($result.outcome -eq 'model_free_harness_checks_passed') 'Synthetic model-free path failed'}
    else {Require ($result.outcome -eq 'failed') 'Synthetic failure was accepted'}
    if($Case -eq 'cleanup_failure'){Require (-not $cleanup.owned_exits[1].exit_confirmed) 'Unconfirmed interpreter cleanup hidden'}
    if($Case -eq 'job_close_failure'){Require (-not $cleanup.owned_job_closed) 'Failed job closure hidden'}
    'PASS '+$Case
} finally {Remove-Item -LiteralPath $temp -Recurse -Force}
