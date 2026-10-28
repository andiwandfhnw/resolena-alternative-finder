[CmdletBinding()]
param([switch]$ExecuteTransportCheck,
    [ValidatePattern('^[a-zA-Z0-9-]+$')][string]$Codespace='special-disco-vprpp7qrv9xrcwq6p',
    [string]$BundleDirectory='C:\ResolenaExperiments\uc001-execution-v1_3_0')

Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
function Get-ProbeResultsBase {return (Join-Path $PSScriptRoot 'results')}
function Quote-ProbeArgument([string]$Value) {
    if ($Value.Contains('"') -or $Value.Contains("`r") -or $Value.Contains("`n")) {throw 'Unsafe test argument.'}
    return '"'+$Value+'"'
}
function Invoke-TransportProbe([string]$BundleDirectory, [string]$Codespace) {
$clock=[Diagnostics.Stopwatch]::StartNew()
function Assert-ProbeTime {
    if ($clock.ElapsedMilliseconds -ge 45000) {throw 'Fixed model-free transport deadline expired; no retry.'}
}
Assert-ContractWindows
if ((Get-ContractHash (Join-Path $BundleDirectory 'freeze.json')) -ne 'b7ed2e54c507c434ec157d0b3daed3440136bde70fd0c76ab79df6707301e615') {throw 'Expected unchanged v1.3.0 bundle.'}
Assert-ContractBundle
if (@(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object {$_.LocalPort -in @(49187,49189)}).Count) {throw 'Test ports occupied; do not stop their owners.'}
$base=Get-ProbeResultsBase
if (-not (Test-Path -LiteralPath $base)) {$null=New-Item -ItemType Directory -Path $base}
$root=Join-Path $base ([guid]::NewGuid().ToString())
$null=New-Item -ItemType Directory -Path $root
$job=$null;$endpoint=$null;$tunnel=$null;$key=$null;$errors=@();$remote=$null
try {
    Initialize-ContractProcessSupport
    Assert-ProbeTime
    $job=New-ContractJob
    $random=New-Object byte[] 32
    $rng=[Security.Cryptography.RandomNumberGenerator]::Create()
    try {$rng.GetBytes($random)} finally {$rng.Dispose()}
    $key=[Convert]::ToBase64String($random)
    $source=[IO.File]::ReadAllText((Join-Path $PSScriptRoot 'Probe-Endpoint.ps1'))
    $encoded=[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($source))
    $endpoint=Start-ContractProcess $job (Join-Path $PSHOME 'powershell.exe') ('-NoLogo -NoProfile -NonInteractive -EncodedCommand '+$encoded) (Join-Path $root 'endpoint.stdout.log') (Join-Path $root 'endpoint.stderr.log') $null
    $endpoint.StandardInput.WriteLine($key);$endpoint.StandardInput.Close()
    $owner=Get-ContractProcessIdentity $endpoint
    do {
        Assert-ProbeTime
        $fresh=Get-ContractProcessIdentity $endpoint
        if ($fresh.Id -ne $owner.Id -or $fresh.Started.Ticks -ne $owner.Started.Ticks) {throw 'Owned endpoint lifetime changed.'}
        $listeners=@(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object {$_.LocalPort -eq 49187})
        if (-not $listeners.Count) {Start-Sleep -Milliseconds 50}
    } while (-not $listeners.Count)
    if ($listeners.Count -ne 1 -or $listeners[0].LocalAddress -ne '127.0.0.1' -or $listeners[0].OwningProcess -ne $owner.Id) {throw 'Test endpoint is not exclusively owned IPv4 loopback.'}
    $command='cd /workspaces/resolena-alternative-finder && timeout --signal=TERM --kill-after=5s 35s env PYTHONPATH=src:. .venv/bin/python scripts/uc001_transport_preparation/probe_forward.py'
    $arguments=@('codespace','ssh','--codespace',$Codespace,'--server-port','49189','--','-T',
        '-o','BatchMode=yes','-o','ExitOnForwardFailure=yes','-o','ServerAliveInterval=5','-o','ServerAliveCountMax=2','-o','ConnectTimeout=15',
        '-R','127.0.0.1:49188:127.0.0.1:49187',$command)
    $tunnel=Start-ContractProcess $job 'C:\ResolenaExperiments\tools\gh-2.81.0\bin\gh.exe' (($arguments|ForEach-Object {Quote-ProbeArgument $_}) -join ' ') (Join-Path $root 'transport.stdout.log') (Join-Path $root 'transport.stderr.log') $null
    $bridgeOwner=Get-ContractProcessIdentity $tunnel
    do {
        Assert-ProbeTime
        $fresh=Get-ContractProcessIdentity $tunnel
        if ($fresh.Id -ne $bridgeOwner.Id -or $fresh.Started.Ticks -ne $bridgeOwner.Started.Ticks) {throw 'Owned transport lifetime changed.'}
        $bridge=@(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object {$_.LocalPort -eq 49189})
        if (-not $bridge.Count) {Start-Sleep -Milliseconds 50}
    } while (-not $bridge.Count)
    if (@($bridge|Where-Object {$_.LocalAddress -notin @('127.0.0.1','::1') -or $_.OwningProcess -ne $bridgeOwner.Id}).Count) {throw 'Transport bridge is not owned loopback.'}
    $tunnel.StandardInput.WriteLine($key);$tunnel.StandardInput.Close()
    while (-not $tunnel.HasExited) {Assert-ProbeTime;Start-Sleep -Milliseconds 50;$tunnel.Refresh()}
    if ($tunnel.ExitCode -ne 0) {throw 'Model-free remote probe failed; inspect preserved logs.'}
    $remote=Read-ContractJson (Join-Path $root 'transport.stdout.log')
    if ($remote.outcome -ne 'model_free_forwarding_passed') {throw 'Forwarding proof absent.'}
} catch {$errors+=$_.Exception.Message}
finally {
    try {Complete-ContractCleanup $null $job $endpoint $tunnel $root} catch {$errors+=$_.Exception.Message}
    $key=$null
}
try {
    if (@(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object {$_.LocalPort -in @(49187,49189)}).Count) {throw 'Test listener cleanup not confirmed; terminate no other owner.'}
} catch {$errors+=$_.Exception.Message}
if ($clock.ElapsedMilliseconds -ge 60000) {$errors+='Overall model-free 60-second limit exceeded.'}
$result=@{outcome=$(if($null -ne $remote -and -not $errors.Count){'model_free_forwarding_and_windows_cleanup_passed'}else{'failed'})
    errors=$errors;elapsed_ms=$clock.ElapsedMilliseconds;codespace_forward_cleanup='pending separate read-only check'
    model_readiness_verified=$false;owned_gpu_counter_verified=$false;model_attempt_ledger_touched=$false;result_directory=$root}
[IO.File]::WriteAllText((Join-Path $root 'result.json'),($result|ConvertTo-Json -Depth 8))
return $result
}

if ($MyInvocation.InvocationName -ne '.') {
    if (-not $ExecuteTransportCheck) {throw 'Preparation only; separate transport-only approval is required. No model startup.'}
    . (Join-Path $BundleDirectory 'Common.ps1')
    $result=Invoke-TransportProbe $BundleDirectory $Codespace
    $result|ConvertTo-Json -Depth 8
    if($result.outcome -eq 'failed'){exit 1}
}
