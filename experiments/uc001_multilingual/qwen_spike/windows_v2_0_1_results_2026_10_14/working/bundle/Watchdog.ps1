param([Parameter(Mandatory=$true)][string]$Root, [Parameter(Mandatory=$true)][int]$RemainingMs)
$clock = [Diagnostics.Stopwatch]::StartNew()
. (Join-Path $PSScriptRoot 'Common.ps1')
Assert-Bundle $Root
Initialize-Clock $Root $clock $RemainingMs
$config = Read-Json (Join-Path $Root 'config.json'); $run = Read-Json (Join-Path $Root 'run.json')
$receipt = Read-Json (Join-Path $Root 'server_process.json'); $sample = $null; $status = 'server_ended'; $exitStatus = 0
$hard = $null
try {
    Add-Type -Path (Join-Path $Root 'HardDeadline.cs')
    $remaining = [Math]::Max(0, $RemainingMs - $clock.ElapsedMilliseconds)
    $hard = New-Object ResolenaDeadline -ArgumentList @($Root, [int]$receipt.process_id, [long]$receipt.start_ticks,
        [string]$receipt.executable, [int]$remaining, [DateTime]::Parse($run.deadline_utc).ToUniversalTime())
    $adapter = Get-Adapter
    while ($true) {
        $process = Get-OwnedLiveProcess $receipt
        if ($null -eq $process) { break }
        Assert-Deadline $Root
        Assert-Loopback $receipt.process_id (Test-Path -LiteralPath (Join-Path $Root 'readiness.json'))
        try { $sample = Get-ResourceSample $Root $adapter $receipt.process_id }
        catch {
            if ($null -eq (Get-OwnedLiveProcess $receipt)) { break }
            throw
        }
        [IO.File]::AppendAllText((Join-Path $Root 'resources.jsonl'), (($sample | ConvertTo-Json -Compress -Depth 12) + "`n"), (New-Object Text.UTF8Encoding($false)))
        Assert-Resources $sample $config
        Start-Sleep -Milliseconds 1000
    }
} catch {
    $status = 'guard_stopped'; $exitStatus = 1
    Write-Json (Join-Path $Root 'guard_failure.json') @{ utc = [DateTime]::UtcNow.ToString('o'); measured = $sample;
        threshold = $config.limits; error = $_.Exception.Message; ownership_observation = $script:OwnershipObservation }
    try { Stop-Owned $Root } catch { Write-NewJson (Join-Path $Root 'ownership_stop_failure.json') @{ error = $_.Exception.Message } }
} finally {
    if ($null -ne $hard) { $hard.Cancel() }
    Write-NewJson (Join-Path $Root 'watchdog_exit.json') @{ utc = [DateTime]::UtcNow.ToString('o'); status = $status;
        exit_code = $exitStatus; original_deadline_utc = $run.deadline_utc; ownership_observation = $script:OwnershipObservation }
}
exit $exitStatus
