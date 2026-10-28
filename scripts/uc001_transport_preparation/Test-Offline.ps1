param([Parameter(Mandatory=$true)][string]$Case)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$bundle=Join-Path (Split-Path $PSScriptRoot -Parent) 'uc001_execution_v1_3_0'
. (Join-Path $bundle 'Common.ps1')
$tokens=$null;$parseErrors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'Test-Transport.ps1'),[ref]$tokens,[ref]$parseErrors)
if(-not $ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Invoke-TransportProbe'},$true)){throw 'Testable transport control flow is absent (RED).'}
. (Join-Path $PSScriptRoot 'Test-Transport.ps1')
$script:started=0;$script:closed=0;$script:disposed=0
function Require($Condition,$Message){if(-not $Condition){throw $Message}}
function FakeOwner([int]$OwnerId) {
    $value=[pscustomobject]@{Id=$OwnerId;StartTime=[DateTime]'2026-10-17T00:00:00Z';HasExited=$false;ExitCode=0}
    $value|Add-Member ScriptMethod Refresh {}
    $value|Add-Member ScriptMethod WaitForExit {param($ms) return ($Case -ne 'exit_unconfirmed')}
    $value|Add-Member ScriptMethod Dispose {$script:disposed++}
    $stream=[pscustomobject]@{}
    $stream|Add-Member ScriptMethod WriteLine {param($line)}
    $stream|Add-Member ScriptMethod Close {if($script:started -eq 2){$script:fakeTunnel.HasExited=$true}}
    $value|Add-Member NoteProperty StandardInput $stream
    return $value
}
$script:fakeEndpoint=FakeOwner 123;$script:fakeTunnel=FakeOwner 456
if($Case -eq 'remote_failed'){$script:fakeTunnel.ExitCode=1}
$temp=Join-Path ([IO.Path]::GetTempPath()) ('uc001-transport-offline-'+[guid]::NewGuid())
function Get-ProbeResultsBase {return $temp}
function Assert-ContractWindows {}
function Initialize-ContractProcessSupport {}
function New-ContractJob {return [IntPtr]42}
function Close-ContractJob {$script:closed++;return ($Case -ne 'job_close_failed')}
function Start-ContractProcess {
    $script:started++
    if($script:started -eq 1){return $script:fakeEndpoint}
    if($script:started -eq 2){return $script:fakeTunnel}
    throw 'Unexpected extra startup'
}
function Get-NetTCPConnection {
    if($script:closed -gt 0){return}
    if($script:started -ge 1){[pscustomobject]@{LocalPort=49187;LocalAddress='127.0.0.1';OwningProcess=$(if($Case -eq 'endpoint_foreign'){789}else{123})}}
    if($script:started -ge 2){[pscustomobject]@{LocalPort=49189;LocalAddress=$(if($Case -eq 'bridge_wildcard'){'0.0.0.0'}else{'127.0.0.1'});OwningProcess=456}}
}
function Read-ContractJson($Path) {
    if($Path.EndsWith('transport.stdout.log')){return [pscustomobject]@{outcome='model_free_forwarding_passed'}}
    return ([IO.File]::ReadAllText($Path)|ConvertFrom-Json)
}
try {
    $result=Invoke-TransportProbe $bundle 'offline'
    if($Case -eq 'success') {Require ($result.outcome -eq 'model_free_forwarding_and_windows_cleanup_passed') ('Valid fake flow failed: '+($result.errors -join ','))}
    else {Require ($result.outcome -eq 'failed') 'Failure concealed'}
    $expected=$(if($Case -eq 'endpoint_foreign'){1}else{2})
    Require ($script:closed -eq 1 -and $script:disposed -eq $expected) 'Abort skipped owned cleanup or started another process'
    $cleanup=Read-ContractJson (Join-Path $result.result_directory 'cleanup.json')
    Require ($cleanup.owned_exits.Count -eq $expected) 'Owned exit confirmations omitted'
    Require (-not $result.model_readiness_verified -and -not $result.owned_gpu_counter_verified -and -not $result.model_attempt_ledger_touched) 'Model/GPU evidence invented'
} finally {if(Test-Path -LiteralPath $temp){Remove-Item -LiteralPath $temp -Recurse -Force}}
Write-Output ('PASS '+$Case)
