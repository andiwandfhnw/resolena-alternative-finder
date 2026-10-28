. (Join-Path $PSScriptRoot 'Base.ps1')
Set-Item -Path Function:Get-BaseResourceSample -Value (Get-Item Function:Get-ResourceSample).ScriptBlock
$script:OwnershipObservation = $null

function Write-NewJson([string]$Path, $Value) {
    if (Test-Path -LiteralPath $Path) { throw ('Existing record preserved: ' + $Path) }
    Write-Json $Path $Value
}
function Read-LiveText([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return '' }
    $stream = [IO.File]::Open($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
    try { $reader = New-Object IO.StreamReader($stream, [Text.Encoding]::UTF8); return $reader.ReadToEnd() }
    finally { $stream.Dispose() }
}
function Read-LiveBytes([string]$Path) {
    $stream = [IO.File]::Open($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
    $memory = New-Object IO.MemoryStream
    try { $stream.CopyTo($memory); return ,$memory.ToArray() }
    finally { $stream.Dispose(); $memory.Dispose() }
}
function Get-ResourceSample([string]$Root, $Adapter, [int]$OwnedId = 0, [string]$ArtifactsRoot = '') {
    $sample = Get-BaseResourceSample $Root $Adapter $OwnedId
    if (-not $ArtifactsRoot) { $ArtifactsRoot = (Read-Json (Join-Path $Root 'config.json')).reuse_root }
    if ((Test-Path -LiteralPath $ArtifactsRoot) -and $ArtifactsRoot -cne $Root) {
        $sum = Get-ChildItem -LiteralPath $ArtifactsRoot -File -Recurse | Measure-Object -Property Length -Sum
        if ($null -ne $sum.Sum) { $sample.scratch_bytes += [long]$sum.Sum }
    }
    return $sample
}
function Initialize-Clock([string]$Root, $Clock, [long]$BudgetMs) {
    $script:RunClock = $Clock; $script:BudgetMs = $BudgetMs
    $script:RunFileSha = Get-Sha (Join-Path $Root 'run.json')
}
function Assert-Deadline([string]$Root, [string]$Stage = '') {
    if ((Get-Sha (Join-Path $Root 'run.json')) -cne $script:RunFileSha) { throw 'Run identity/deadline changed; no continuation.' }
    $run = Read-Json (Join-Path $Root 'run.json')
    if ((Get-Sha (Join-Path $Root 'freeze.json')) -cne $run.freeze_sha256) { throw 'Freeze changed during execution.' }
    if ([DateTime]::UtcNow -ge [DateTime]::Parse($run.deadline_utc).ToUniversalTime() -or $script:RunClock.ElapsedMilliseconds -ge $script:BudgetMs) {
        throw 'Thirty-minute deadline expired; close and preserve partial results. No extension.'
    }
    if (Test-Path -LiteralPath (Join-Path $Root 'hard_deadline.json')) { throw 'Independent hard deadline fired.' }
}
function Assert-RunAlive([string]$Root, $Server, $Watch) {
    Assert-Deadline $Root
    if ($Server.HasExited -or $Watch.HasExited -or (Test-Path -LiteralPath (Join-Path $Root 'guard_failure.json'))) { throw 'Server/watchdog/guard stopped; no restart.' }
}
function Remaining-Seconds([string]$Root, [int]$Maximum) {
    Assert-Deadline $Root
    $run = Read-Json (Join-Path $Root 'run.json')
    $utc = ([DateTime]::Parse($run.deadline_utc).ToUniversalTime() - [DateTime]::UtcNow).TotalSeconds
    $mono = ($script:BudgetMs - $script:RunClock.ElapsedMilliseconds) / 1000.0
    return [Math]::Max(1, [Math]::Floor([Math]::Min($Maximum, [Math]::Min($utc, $mono))))
}
function Invoke-GetJson($Client, [string]$Url, [int]$Timeout) {
    $cts = New-Object Threading.CancellationTokenSource
    $cts.CancelAfter($Timeout * 1000)
    try {
        $response = $Client.GetAsync($Url, $cts.Token).GetAwaiter().GetResult()
        return @{ http_status = [int]$response.StatusCode; raw_body = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult() }
    } finally { $cts.Dispose() }
}
function Assert-WireResponse($Result) {
    if ($Result.http_status -ne 200 -or ($Result.Contains('transport_error'))) { throw 'Operational HTTP/transport failure.' }
    if ($Result.wall_seconds -gt 45) { throw 'Request timeout.' }
    $raw = $Result.raw_body | ConvertFrom-Json
    if ($raw.choices[0].finish_reason -cne 'stop') { throw 'Non-stop finish; do not retry.' }
    $message = $raw.choices[0].message
    if (($message.PSObject.Properties.Name -contains 'reasoning_content') -and $message.reasoning_content) { throw 'Thinking output violates fixed configuration.' }
    if ($raw.timings.cache_n -ne 0 -or $raw.usage.prompt_tokens_details.cached_tokens -ne 0) { throw 'Cache counters not zero.' }
    $null = $raw.usage.prompt_tokens; $null = $raw.usage.completion_tokens
    $null = $raw.timings.prompt_ms; $null = $raw.timings.predicted_ms
}
function Test-OffloadText([string]$Text) {
    $layerMatches = [regex]::Matches($Text, 'offloaded (\d+)/(\d+) layers to GPU')
    if ($layerMatches.Count -eq 0 -or $Text -notmatch 'Vulkan0.*RX\s*6800\s*XT' -or $Text -notmatch 'Vulkan0.*model buffer size') { return $false }
    $kv = [regex]::Match($Text, 'Vulkan0.*KV buffer size\s*=\s*([0-9.]+)\s*MiB')
    if (-not $kv.Success -or [double]::Parse($kv.Groups[1].Value, [Globalization.CultureInfo]::InvariantCulture) -le 0) { return $false }
    foreach ($match in $layerMatches) {
        if ([int]$match.Groups[1].Value -le 0 -or [int]$match.Groups[1].Value -ne [int]$match.Groups[2].Value) { return $false }
    }
    return $true
}
function Get-OwnedLiveProcess($Receipt, [scriptblock]$Lookup = { param([int]$OwnedId) Get-Process -Id $OwnedId -ErrorAction SilentlyContinue }) {
    $script:OwnershipObservation = @{ utc = [DateTime]::UtcNow.ToString('o'); expected_pid = [int]$Receipt.process_id;
        expected_start_ticks = [long]$Receipt.start_ticks; expected_executable = [string]$Receipt.executable;
        observed_pid = $null; observed_start_ticks = $null; observed_executable = $null; state = 'checking'; error = $null }
    $process = & $Lookup ([int]$Receipt.process_id)
    if ($null -eq $process) { $script:OwnershipObservation.state = 'absent'; return $null }
    try {
        $script:OwnershipObservation.observed_pid = $process.Id
        if ($process.Id -ne [int]$Receipt.process_id) { throw 'Ownership PID changed; no unrelated process stopped.' }
        if ($process.HasExited) { $script:OwnershipObservation.state = 'ended'; return $null }
        $script:OwnershipObservation.observed_start_ticks = $process.StartTime.ToUniversalTime().Ticks
        $script:OwnershipObservation.observed_executable = $process.Path
        if ($script:OwnershipObservation.observed_start_ticks -ne [long]$Receipt.start_ticks -or
            -not $script:OwnershipObservation.observed_executable -or $script:OwnershipObservation.observed_executable -ine $Receipt.executable) {
            throw 'Ownership changed or live identity unavailable; no unrelated process stopped.'
        }
        if ($process.HasExited) { $script:OwnershipObservation.state = 'ended'; return $null }
        $script:OwnershipObservation.state = 'live_identity_verified'
        return $process
    } catch {
        $identityError = $_.Exception.Message; $script:OwnershipObservation.error = $identityError
        try {
            if ($process.HasExited) { $script:OwnershipObservation.state = 'ended_during_identity_read'; return $null }
        } catch { }
        $rechecked = & $Lookup ([int]$Receipt.process_id)
        if ($null -eq $rechecked -or $rechecked.HasExited) { $script:OwnershipObservation.state = 'ended_on_recheck'; return $null }
        $script:OwnershipObservation.state = 'live_identity_rejected'
        throw $identityError
    }
}
function New-Checkpoint([string]$Root, [int]$Count) {
    $run = Read-Json (Join-Path $Root 'run.json'); $plan = @(Read-Json (Join-Path $Root 'order.json'))
    $config = Read-Json (Join-Path $Root 'config.json')
    if ($Count -notin $config.checkpoint_after_indices) { throw 'Unexpected pause index.' }
    $id = 'cp' + $Count.ToString('00'); $folder = Join-Path $Root ('checkpoints\' + $id)
    $null = New-Item -ItemType Directory -Path $folder
    $receipts = @(); $completed = @()
    for ($i = 0; $i -lt $Count; $i++) {
        $entry = $plan[$i]; $completed += $entry.id
        $receipts += @{ id = $entry.id; arm = $entry.arm; case = $entry.case;
            request_sha256 = Get-Sha (Join-Path $Root $entry.request)
            response_sha256 = Get-Sha (Join-Path $Root ('responses\' + $entry.id + '.json')) }
    }
    $checkpoint = @{ checkpoint_id = $id; nonce = [Guid]::NewGuid().ToString(); run_id = $run.run_id;
        freeze_sha256 = $run.freeze_sha256; deadline_utc = $run.deadline_utc; completed_ids = $completed; receipts = $receipts }
    Write-NewJson (Join-Path $folder 'checkpoint.json') $checkpoint
    Copy-Item -LiteralPath (Join-Path $folder 'checkpoint.json') -Destination (Join-Path $Root 'checkpoint.json') -Force
    $inbox = Join-Path $Root ('inbox\' + $id); $null = New-Item -ItemType Directory -Path $inbox
    $state = Get-State $Root; $state.status = 'awaiting_' + $id; Write-Json (Join-Path $Root 'state.json') $state
    Export-SmallResults $Root $id
    return $checkpoint
}
function Assert-Receipt([string]$Root, $Checkpoint) {
    Assert-Deadline $Root
    $id = $Checkpoint.checkpoint_id; $folder = Join-Path $Root ('inbox\' + $id)
    $receiptPath = Join-Path $folder 'receipt.json'; $assessmentPath = Join-Path $folder 'assessment.json'
    if (-not (Test-Path -LiteralPath $assessmentPath)) { throw 'Receipt arrived without complete assessment.' }
    $receipt = Read-Json $receiptPath; $assessment = Read-Json $assessmentPath
    $run = Read-Json (Join-Path $Root 'run.json'); $plan = @(Read-Json (Join-Path $Root 'order.json'))
    $count = @($Checkpoint.completed_ids).Count
    $cpHash = Get-Sha (Join-Path $Root ('checkpoints\' + $id + '\checkpoint.json'))
    if ($receipt.version -cne '2.0.0' -or $receipt.allowed -isnot [bool] -or
        $receipt.run_id -cne $run.run_id -or $receipt.freeze_sha256 -cne $run.freeze_sha256 -or
        $receipt.checkpoint_id -cne $id -or $receipt.checkpoint_sha256 -cne $cpHash -or
        $receipt.nonce -cne $Checkpoint.nonce -or $receipt.deadline_utc -cne $run.deadline_utc -or
        $receipt.next_index -ne ($count + 1) -or $receipt.assessment_sha256 -cne (Get-Sha $assessmentPath) -or
        @($receipt.receipts).Count -ne $count -or @($assessment.evaluations).Count -ne $count -or
        $assessment.run_id -cne $run.run_id -or $assessment.freeze_sha256 -cne $run.freeze_sha256 -or
        $assessment.checkpoint_id -cne $id -or $assessment.checkpoint_sha256 -cne $cpHash) { throw 'Stale or mismatched arm/request/freeze receipt.' }
    $derived = @($assessment.operational_errors).Count -eq 0
    for ($i = 0; $i -lt $count; $i++) {
        $entry = $plan[$i]; $r = $receipt.receipts[$i]; $e = $assessment.evaluations[$i]
        if ($r.id -cne $entry.id -or $r.case -cne $entry.case -or $r.arm -cne $entry.arm -or
            $r.request_sha256 -cne (Get-Sha (Join-Path $Root $entry.request)) -or
            $r.response_sha256 -cne (Get-Sha (Join-Path $Root ('responses\' + $entry.id + '.json'))) -or
            $e.id -cne $entry.id -or $e.case -cne $entry.case -or $e.arm -cne $entry.arm -or $e.strict_pass -isnot [bool]) {
            throw 'Receipt response/case/arm checksum mismatch.'
        }
        if (@($e.operational_errors).Count -gt 0 -or ($e.arm -ceq 'v2' -and -not $e.strict_pass)) { $derived = $false }
    }
    if (-not $receipt.allowed -or -not $derived -or $assessment.allowed -isnot [bool] -or -not $assessment.allowed) { throw 'STOP: v2 strict or either-arm operational gate failed.' }
    Write-NewJson (Join-Path $Root ('checkpoints\' + $id + '\consumed.json')) @{ utc = [DateTime]::UtcNow.ToString('o');
        run_id = $run.run_id; nonce = $Checkpoint.nonce; receipt_sha256 = Get-Sha $receiptPath; assessment_sha256 = Get-Sha $assessmentPath }
}
function Await-Checkpoint([string]$Root, [int]$Count, $Server, $Watch) {
    Assert-RunAlive $Root $Server $Watch
    $checkpoint = New-Checkpoint $Root $Count
    $folder = Join-Path $Root ('inbox\' + $checkpoint.checkpoint_id)
    Write-Host ('PAUSED ' + $checkpoint.checkpoint_id + ': transfer ' + (Join-Path $Root ($checkpoint.checkpoint_id + '.zip')))
    Write-Host ('Return assessment.json first, then atomically rename receipt.pending.json to receipt.json in ' + $folder)
    Write-Host 'The running controller resumes only after validation. The original 30-minute deadline remains active.'
    while (-not (Test-Path -LiteralPath (Join-Path $folder 'receipt.json'))) {
        Assert-RunAlive $Root $Server $Watch; Start-Sleep -Milliseconds 250
    }
    Assert-RunAlive $Root $Server $Watch; Assert-Bundle $Root
    Assert-Receipt $Root $checkpoint
    Assert-RunAlive $Root $Server $Watch
}
function Confirm-OwnedEnded($Receipt) {
    $process = Get-Process -Id $Receipt.process_id -ErrorAction SilentlyContinue
    if ($null -eq $process) { return $true }
    if ($process.StartTime.ToUniversalTime().Ticks -ne [long]$Receipt.start_ticks) { return $true }
    return $false
}
function Export-SmallResults([string]$Root, [string]$Name) {
    $archive = Join-Path $Root ($Name + '.zip'); $snapshot = Join-Path $Root ('exports\' + $Name)
    if ((Test-Path -LiteralPath $archive) -or (Test-Path -LiteralPath $snapshot)) { throw 'Existing export preserved; no overwrite.' }
    $null = New-Item -ItemType Directory -Path $snapshot
    foreach ($file in @(Get-ChildItem -LiteralPath $Root -File | Where-Object { $_.Extension -in @('.json', '.jsonl', '.log') })) {
        [byte[]]$bytes = Read-LiveBytes $file.FullName
        if ($file.Extension -eq '.jsonl' -and $bytes.Length -gt 0 -and $bytes[$bytes.Length - 1] -ne 10) {
            $last = [Array]::LastIndexOf($bytes, [byte]10)
            $trimmed = New-Object byte[] ($last + 1)
            if ($last -ge 0) { [Array]::Copy($bytes, $trimmed, $last + 1) }
            $bytes = $trimmed
        }
        [IO.File]::WriteAllBytes((Join-Path $snapshot $file.Name), $bytes)
    }
    foreach ($name in @('requests', 'responses', 'templates', 'checkpoints', 'inbox')) {
        $source = Join-Path $Root $name
        if (Test-Path -LiteralPath $source) { Copy-Item -LiteralPath $source -Destination $snapshot -Recurse }
    }
    Compress-Archive -Path (Join-Path $snapshot '*') -DestinationPath $archive
    Write-Host ('Saved ' + $archive + ' SHA-256 ' + (Get-Sha $archive))
}
function Close-Run([string]$Root, [bool]$FromController = $false) {
    Assert-Bundle $Root
    if (Test-Path -LiteralPath (Join-Path $Root 'final-results.zip')) {
        Write-Host ('Preserved final export SHA-256: ' + (Get-Sha (Join-Path $Root 'final-results.zip'))); return
    }
    $run = Read-Json (Join-Path $Root 'run.json')
    if (-not $FromController -and (Test-Path -LiteralPath (Join-Path $Root 'controller_process.json'))) {
        if (-not (Confirm-OwnedEnded (Read-Json (Join-Path $Root 'controller_process.json')))) { throw 'Controller still active; close its own window first. No duplicate closeout.' }
    }
    Stop-Owned $Root
    foreach ($item in @(@{ receipt = 'server_process.json'; exit = 'server_exit.json' }, @{ receipt = 'watchdog_process.json'; exit = 'watchdog_process_exit.json' })) {
        $rp = Join-Path $Root $item.receipt
        if (Test-Path -LiteralPath $rp) {
            $r = Read-Json $rp; $wait = [Diagnostics.Stopwatch]::StartNew()
            while (-not (Confirm-OwnedEnded $r) -and $wait.Elapsed.TotalSeconds -lt 15) { Start-Sleep -Milliseconds 100 }
            if (-not (Confirm-OwnedEnded $r)) {
                if ($item.receipt -cne 'watchdog_process.json') { throw 'Owned server exit unconfirmed; final export withheld.' }
                $ownedWatch = Get-Process -Id $r.process_id
                if ($ownedWatch.StartTime.ToUniversalTime().Ticks -ne [long]$r.start_ticks -or $ownedWatch.Path -ine $r.executable) { throw 'Watchdog ownership mismatch; no process stopped.' }
                $ownedWatch.Kill(); $ownedWatch.WaitForExit()
                Write-NewJson (Join-Path $Root 'watchdog_forced_exit.json') @{ confirmed_exited = $true; exit_code = $ownedWatch.ExitCode;
                    reason = 'Owned watchdog failed to end after confirmed server shutdown; no restart.' }
            }
            if (-not (Test-Path -LiteralPath (Join-Path $Root $item.exit))) {
                Write-NewJson (Join-Path $Root $item.exit) @{ utc = [DateTime]::UtcNow.ToString('o'); confirmed_exited = $true;
                    exit_code = $null; confirmation = 'Original PID/start-time no longer active; exact exit code unavailable after interruption.' }
            }
        } elseif (-not (Test-Path -LiteralPath (Join-Path $Root $item.exit))) {
            Write-NewJson (Join-Path $Root $item.exit) @{ confirmed_exited = $true; exit_code = $null; confirmation = 'Process was not started.' }
        }
    }
    if (-not (Test-Path -LiteralPath (Join-Path $Root 'watchdog_exit.json'))) {
        Write-NewJson (Join-Path $Root 'watchdog_exit.json') @{ status = 'not_started_or_exit_record_missing'; utc = [DateTime]::UtcNow.ToString('o'); exit_code = $null }
    }
    $state = Get-State $Root; $state.status = 'closed_artifacts_preserved'; Write-Json (Join-Path $Root 'state.json') $state
    Write-Json (Join-Path $Root 'closeout.json') @{ run_id = $run.run_id; utc = [DateTime]::UtcNow.ToString('o');
        original_deadline_utc = $run.deadline_utc; artifacts_root = $run.artifacts_root; no_deletion = $true; DESIGN = 'pending'; linguistic_validation = 'pending' }
    $files = @{}
    foreach ($file in @(Get-ChildItem -LiteralPath $Root -File -Recurse)) {
        $relative = $file.FullName.Substring($Root.Length + 1).Replace('\', '/')
        if ($relative -like 'exports/*' -or $relative -like 'checkpoints/*' -or $relative -like 'inbox/*' -or $file.Extension -eq '.zip' -or $file.Name -eq 'cleanup_manifest.json') { continue }
        if ($file.Extension -in @('.json', '.jsonl', '.log') -or $relative -like 'requests/*' -or $relative -like 'templates/*' -or $relative -like 'responses/*') {
            $files[$relative] = @{ bytes = $file.Length; sha256 = Get-Sha $file.FullName }
        }
    }
    $artifactVerification = @{ status = 'verification_not_completed'; no_artifact_mutation = $true }
    if (Test-Path -LiteralPath (Join-Path $Root 'artifact_verification.json')) { $artifactVerification = Read-Json (Join-Path $Root 'artifact_verification.json') }
    Write-Json (Join-Path $Root 'cleanup_manifest.json') @{ utc = [DateTime]::UtcNow.ToString('o'); run_id = $run.run_id;
        artifacts_preserved = $true; effect = 'Only matching owned server stopped. No artifacts, logs, markers or receipts deleted.';
        artifact_verification = $artifactVerification; files = $files }
    Export-SmallResults $Root 'final-results'
}
