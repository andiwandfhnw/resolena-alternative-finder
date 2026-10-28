param([Parameter(Mandatory=$true)][string]$Root)
. (Join-Path $PSScriptRoot 'Common.ps1')
$config = Read-Json (Join-Path $Root 'config.json')
$receipt = Read-Json (Join-Path $Root 'server_process.json')
$sample = $null
$monotonic = [Diagnostics.Stopwatch]::StartNew()
try {
    $adapter = Get-Adapter
    while ($true) {
        $process = Get-Process -Id $receipt.process_id -ErrorAction SilentlyContinue
        if ($null -eq $process) { break }
        if ($process.StartTime.ToUniversalTime().Ticks -ne [long]$receipt.start_ticks -or $process.Path -ne $receipt.executable) { throw 'Server ownership changed.' }
        Assert-Deadline $Root 'evaluation'
        if ($monotonic.Elapsed.TotalSeconds -ge $config.limits.evaluation_seconds) { throw 'Monotonic evaluation limit reached.' }
        Assert-Loopback $receipt.process_id (Test-Path -LiteralPath (Join-Path $Root 'readiness.json'))
        $sample = Get-ResourceSample $Root $adapter $receipt.process_id
        [IO.File]::AppendAllText((Join-Path $Root 'resources.jsonl'), (($sample | ConvertTo-Json -Compress -Depth 10) + "`n"), (New-Object Text.UTF8Encoding($false)))
        Assert-Resources $sample $config
        Start-Sleep -Seconds 1
    }
    Write-Json (Join-Path $Root 'watchdog_exit.json') @{ utc = [DateTime]::UtcNow.ToString('o'); status = 'server_ended' }
} catch {
    Write-Json (Join-Path $Root 'guard_failure.json') @{ utc = [DateTime]::UtcNow.ToString('o'); measured = $sample; threshold = $config.limits; error = $_.Exception.Message }
    try { Stop-Owned $Root } catch { Write-Json (Join-Path $Root 'ownership_stop_failure.json') @{ error = $_.Exception.Message } }
}
