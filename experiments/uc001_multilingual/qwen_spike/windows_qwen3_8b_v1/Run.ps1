param([Parameter(Mandatory=$true)][string]$Root)
. (Join-Path $PSScriptRoot 'Common.ps1')
$Root = [IO.Path]::GetFullPath($Root).TrimEnd('\')
Assert-Bundle $Root
Assert-Deadline $Root 'evaluation'
Assert-NoDuplicate $Root
$state = Get-State $Root
if ($state.status -ne 'prepared' -or (Test-Path -LiteralPath (Join-Path $Root 'run_attempt.json'))) { throw 'Run already attempted or setup not complete; no retry.' }
$config = Read-Json (Join-Path $Root 'config.json')
$artifacts = Read-Json (Join-Path $Root 'artifacts.json')
Write-Json (Join-Path $Root 'run_attempt.json') @{ utc = [DateTime]::UtcNow.ToString('o'); automatic_retry = $false;
    note = 'Single authorized Run invocation. Hash verification may warm OS file cache; no CPU speedup baseline.' }
try {
$adapter = Get-Adapter
$preload = Get-ResourceSample $Root $adapter
Write-Json (Join-Path $Root 'preload_resources.json') $preload
Assert-Resources $preload $config $true
$runtime = Read-Json (Join-Path $Root 'runtime_verification.json')
if ((Get-Sha $runtime.executable) -ne $runtime.executable_sha256) { throw 'Verified runtime binary changed.' }
$modelPath = Join-Path $Root $artifacts.artifacts[1].file
if ((Get-Sha $modelPath) -ne $artifacts.artifacts[1].sha256) { throw 'Verified model changed.' }
$occupied = @(Get-NetTCPConnection -LocalPort $config.server_port -ErrorAction SilentlyContinue)
if ($occupied.Count -gt 0) { throw 'Planned loopback port is already used; do not stop its owner.' }
Assert-Deadline $Root 'evaluation'
} catch {
    Write-Json (Join-Path $Root 'preload_failure.json') @{ utc = [DateTime]::UtcNow.ToString('o'); thresholds = $config.limits; error = $_.Exception.Message }
    $state.status = 'preload_failed'; Write-Json (Join-Path $Root 'state.json') $state
    throw
}
$now = [DateTime]::UtcNow
$state | Add-Member -NotePropertyName evaluation_deadline_utc -NotePropertyValue ($now.AddSeconds($config.limits.evaluation_seconds).ToString('o'))
$state.status = 'starting_model'; Write-Json (Join-Path $Root 'state.json') $state
foreach ($name in @('responses', 'templates')) { $null = New-Item -ItemType Directory -Path (Join-Path $Root $name) }
$serverArgs = @('-m', $modelPath, '--host', '127.0.0.1', '--port', [string]$config.server_port,
    '--device', 'Vulkan0', '--n-gpu-layers', '99', '--fit', 'off', '--threads', '2', '--threads-batch', '2',
    '--ctx-size', '2048', '--parallel', '1', '--batch-size', '64', '--ubatch-size', '64',
    '--cache-type-k', 'f16', '--cache-type-v', 'f16', '--n-predict', '384', '--jinja',
    '--offline', '--no-warmup', '--no-context-shift', '--no-cache-prompt', '--cache-reuse', '0',
    '--no-agent', '--no-webui', '--no-webui-mcp-proxy')
$argumentString = (($serverArgs | ForEach-Object { Quote-Argument $_ }) -join ' ')
Write-Json (Join-Path $Root 'server_command.json') @{ executable = $runtime.executable; arguments = $serverArgs;
    environment_overrides_removed = @('LLAMA_*', 'HF_*', 'VK_*'); nonthinking = 'enable_thinking=false in every frozen request and template probe' }
$server = $null; $client = $null; $watch = $null; $exitStatus = 1
try {
    $server = [ResolenaProcess]::Start($runtime.executable, $argumentString, (Join-Path $Root 'server.stdout.log'), (Join-Path $Root 'server.stderr.log'))
    Write-Json (Join-Path $Root 'server_process.json') @{ process_id = $server.Id; start_ticks = $server.StartTime.ToUniversalTime().Ticks; executable = $runtime.executable }
    $watchArgs = '-NoProfile -ExecutionPolicy RemoteSigned -File ' + (Quote-Argument (Join-Path $Root 'Watchdog.ps1')) + ' -Root ' + (Quote-Argument $Root)
    $watch = Start-Process -FilePath (Join-Path $PSHOME 'powershell.exe') -ArgumentList $watchArgs -PassThru -WindowStyle Hidden
    Write-Json (Join-Path $Root 'watchdog_process.json') @{ process_id = $watch.Id; start_ticks = $watch.StartTime.ToUniversalTime().Ticks }
    $client = New-LocalClient
    $base = 'http://127.0.0.1:' + $config.server_port
    $ready = [Diagnostics.Stopwatch]::StartNew(); $healthy = $false
    while ($ready.Elapsed.TotalSeconds -lt $config.limits.readiness_seconds) {
        Assert-Deadline $Root 'evaluation'
        if ($server.HasExited -or $watch.HasExited -or (Test-Path -LiteralPath (Join-Path $Root 'guard_failure.json'))) { throw 'Server/watchdog stopped before readiness.' }
        $connection = @(Get-NetTCPConnection -LocalPort $config.server_port -State Listen -ErrorAction SilentlyContinue)
        if ($connection.Count -gt 0 -and ($connection.Count -ne 1 -or $connection[0].OwningProcess -ne $server.Id -or $connection[0].LocalAddress -ne '127.0.0.1')) { throw 'Readiness listener ownership/binding mismatch.' }
        $cts = New-Object Threading.CancellationTokenSource
        $cts.CancelAfter(1000)
        try {
            $response = $client.GetAsync(($base + '/health'), $cts.Token).GetAwaiter().GetResult()
            if ([int]$response.StatusCode -eq 200) { $healthy = $true; break }
        } catch { Start-Sleep -Milliseconds 250 } finally { $cts.Dispose() }
    }
    if (-not $healthy) { throw 'Readiness exceeded 90 seconds.' }
    Assert-Loopback $server.Id $true
    Write-Json (Join-Path $Root 'readiness.json') @{ utc = [DateTime]::UtcNow.ToString('o'); seconds = $ready.Elapsed.TotalSeconds; ready = $true }
    $propsResponse = $client.GetAsync($base + '/props').GetAwaiter().GetResult()
    $propsRaw = $propsResponse.Content.ReadAsStringAsync().GetAwaiter().GetResult()
    Write-Json (Join-Path $Root 'server_properties.json') @{ http_status = [int]$propsResponse.StatusCode; raw_body = $propsRaw }
    $props = $propsRaw | ConvertFrom-Json
    if ([int]$propsResponse.StatusCode -ne 200 -or $props.total_slots -ne 1 -or $props.default_generation_settings.n_ctx -ne 2048) { throw 'Actual slot/context does not match freeze.' }
    $plan = @(Read-Json (Join-Path $Root 'order.json'))
    $freezeSha = Get-Sha (Join-Path $Root 'freeze.json')
    $completed = @(); $gateChecked = $false
    foreach ($entry in $plan) {
        if ($entry.stage -ne 'known' -and -not $gateChecked) {
            $state = Get-State $Root; $state.status = 'awaiting_offline_known_gate'; Write-Json (Join-Path $Root 'state.json') $state
            Export-SmallResults $Root 'known-results'
            Write-Host 'PAUSED: no additional inference. Transfer ONLY known-results.zip for offline assessment.'
            Write-Host ('Return gate.json AND assessment.json to ' + $Root + '. Original deadlines remain active during the pause.')
            while (-not (Test-Path -LiteralPath (Join-Path $Root 'gate.json')) -or -not (Test-Path -LiteralPath (Join-Path $Root 'assessment.json'))) {
                Assert-Deadline $Root 'evaluation'
                if ($server.HasExited -or $watch.HasExited -or (Test-Path -LiteralPath (Join-Path $Root 'guard_failure.json'))) { throw 'Server/watchdog/guard stopped while awaiting assessment.' }
                Start-Sleep -Seconds 1
            }
            $gate = Read-Json (Join-Path $Root 'gate.json')
            if ($gate.allowed -isnot [bool] -or -not $gate.allowed -or $gate.bundle_freeze_sha256 -ne $freezeSha -or
                @($gate.known_receipt.PSObject.Properties).Count -ne 6 -or
                -not (Test-Path -LiteralPath (Join-Path $Root 'assessment.json')) -or
                (Get-Sha (Join-Path $Root 'assessment.json')) -ne $gate.assessment_sha256) { throw 'Known-case strict gate failed or assessment provenance incomplete. STOP before new cases.' }
            foreach ($known in @($plan | Where-Object { $_.stage -eq 'known' })) {
                $receipt = $gate.known_receipt.PSObject.Properties[$known.id].Value
                if ($receipt.request_sha256 -ne (Get-Sha (Join-Path $Root $known.request)) -or $receipt.response_sha256 -ne (Get-Sha (Join-Path $Root ('responses/' + $known.id + '.json')))) { throw 'Known gate receipt mismatch.' }
            }
            Assert-Deadline $Root 'evaluation'
            if ($server.HasExited -or $watch.HasExited -or (Test-Path -LiteralPath (Join-Path $Root 'guard_failure.json'))) { throw 'Guard/server no longer active; no restart.' }
            $gateChecked = $true
        }
        Assert-Deadline $Root 'evaluation'
        if ($server.HasExited -or $watch.HasExited -or (Test-Path -LiteralPath (Join-Path $Root 'guard_failure.json'))) { throw 'Operational guard failed.' }
        $state = Get-State $Root; $state.status = 'request_' + $entry.id; Write-Json (Join-Path $Root 'state.json') $state
        $requestPath = Join-Path $Root $entry.request
        $body = [IO.File]::ReadAllText($requestPath, [Text.Encoding]::UTF8)
        $request = $body | ConvertFrom-Json
        $templateBody = @{ messages = $request.messages; chat_template_kwargs = @{ enable_thinking = $false }; add_generation_prompt = $true } | ConvertTo-Json -Depth 30
        $template = Invoke-LocalJson $client ($base + '/apply-template') $templateBody
        Write-Json (Join-Path $Root ('templates/' + $entry.id + '.json')) $template
        if ($template.http_status -ne 200) { throw 'Template inspection failed.' }
        $formatted = ($template.raw_body | ConvertFrom-Json).prompt
        if ($formatted -notmatch '(?s)<\|im_start\|>assistant\s*<think>\s*</think>\s*$') { throw 'Actual hard non-thinking prefix differs from the pinned Qwen3 contract.' }
        $tokenBody = @{ content = $formatted; add_special = $true; parse_special = $true } | ConvertTo-Json -Depth 5
        $tokens = Invoke-LocalJson $client ($base + '/tokenize') $tokenBody
        Write-Json (Join-Path $Root ('templates/' + $entry.id + '.tokens.json')) $tokens
        if ($tokens.http_status -ne 200) { throw 'Token-capacity inspection failed.' }
        $tokenCount = @(($tokens.raw_body | ConvertFrom-Json).tokens).Count
        if ($tokenCount + 384 -gt 2048) { throw 'Frozen prompt plus output exceeds context; no truncation/retuning.' }
        $result = Invoke-LocalJson $client ($base + '/v1/chat/completions') $body
        $result['bundle_freeze_sha256'] = $freezeSha; $result['request_sha256'] = Get-Sha $requestPath
        $result['started_case'] = $entry.id; $result['utc'] = [DateTime]::UtcNow.ToString('o')
        Write-Json (Join-Path $Root ('responses/' + $entry.id + '.json')) $result
        if ($result.http_status -ne 200) { throw 'Inference returned non-200; stop without retry.' }
        $raw = $result.raw_body | ConvertFrom-Json
        if ($raw.choices[0].finish_reason -ne 'stop') { throw 'Non-stop/truncated output; stop without retry.' }
        $completed += $entry.id
        Write-Json (Join-Path $Root 'progress.json') @{ utc = [DateTime]::UtcNow.ToString('o'); completed = $completed;
            phase = $entry.stage; heldout_model_exposure = 0; linguistic_validation = 'pending'; DESIGN = 'pending' }
        Write-Host ('Saved ' + $entry.id + ': ' + [Math]::Round($result.wall_seconds, 3) + ' seconds')
    }
    $exitStatus = 0
    $state = Get-State $Root; $state.status = 'planned_requests_completed_pending_assessment'; Write-Json (Join-Path $Root 'state.json') $state
} catch {
    Write-Json (Join-Path $Root 'run_failure.json') @{ utc = [DateTime]::UtcNow.ToString('o'); error = $_.Exception.Message; orchestration_exit = 1 }
    $state = Get-State $Root; $state.status = 'stopped_pending_review'; Write-Json (Join-Path $Root 'state.json') $state
    Write-Host ('STOP: ' + $_.Exception.Message)
} finally {
    if ($null -ne $client) { $client.Dispose() }
    $wasRunning = $null -ne $server -and -not $server.HasExited
    Stop-Owned $Root
    if ($null -ne $server) {
        $server.WaitForExit(10000) | Out-Null
        if ($server.HasExited) { $server.WaitForExit(); Write-Json (Join-Path $Root 'server_exit.json') @{ exit_code = $server.ExitCode; planned_owned_shutdown = $wasRunning; utc = [DateTime]::UtcNow.ToString('o') } }
    }
    Write-Json (Join-Path $Root 'driver_exit.json') @{ exit_code = $exitStatus; utc = [DateTime]::UtcNow.ToString('o'); model_correctness = 'separate offline assessment' }
    if (Test-Path -LiteralPath (Join-Path $Root 'responses')) { Export-SmallResults $Root 'final-results' }
}
exit $exitStatus
