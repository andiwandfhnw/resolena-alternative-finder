param([Parameter(Mandatory=$true)][string]$Root, [string]$ArtifactsRoot = 'C:\ResolenaExperiments\qwen3-8b-v1')
$enteredUtc = [DateTime]::UtcNow; $clock = [Diagnostics.Stopwatch]::StartNew()
. (Join-Path $PSScriptRoot 'Common.ps1')
$Root = [IO.Path]::GetFullPath($Root).TrimEnd('\'); $ArtifactsRoot = [IO.Path]::GetFullPath($ArtifactsRoot).TrimEnd('\')
Assert-Bundle $Root
$freezeSha = Get-Sha (Join-Path $Root 'freeze.json'); $config = Read-Json (Join-Path $Root 'config.json')
$approvalPath = Join-Path $Root 'execution-approval.json'
if (-not (Test-Path -LiteralPath $approvalPath)) { throw 'Preparation-only authorization. Separate owner execution approval required; no process started.' }
$approval = Read-Json $approvalPath
if ($approval.allowed -isnot [bool] -or -not $approval.allowed -or $approval.approved_freeze_sha256 -cne $freezeSha) { throw 'Execution not approved for this freeze.' }
if ((Test-Path -LiteralPath (Join-Path $Root 'run_attempt.json')) -or (Test-Path -LiteralPath (Join-Path $Root 'run.json'))) { throw 'Attempt already exists; do not restart or delete markers.' }
if ($Root.StartsWith('\\') -or $ArtifactsRoot.StartsWith('\\') -or $Root -ieq $ArtifactsRoot -or $Root.StartsWith($ArtifactsRoot + '\', [StringComparison]::OrdinalIgnoreCase) -or $ArtifactsRoot.StartsWith($Root + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Separate local folders required.' }
$run = @{ run_id = [Guid]::NewGuid().ToString(); started_utc = $enteredUtc.ToString('o');
    deadline_utc = $enteredUtc.AddSeconds(1800).ToString('o'); freeze_sha256 = $freezeSha; artifacts_root = $ArtifactsRoot }
Write-NewJson (Join-Path $Root 'run_attempt.json') @{ run_id = $run.run_id; started_utc = $run.started_utc; automatic_retry = $false }
Write-NewJson (Join-Path $Root 'run.json') $run
Write-NewJson (Join-Path $Root 'controller_process.json') @{ process_id = $PID; start_ticks = (Get-Process -Id $PID).StartTime.ToUniversalTime().Ticks }
Write-NewJson (Join-Path $Root 'state.json') @{ status = 'preflight'; run_id = $run.run_id; deadline_utc = $run.deadline_utc }
Initialize-Clock $Root $clock 1800000
$server = $null; $watch = $null; $client = $null; $exitStatus = 1; $completed = @()
try {
    Assert-NoDuplicate $Root; Assert-NoDuplicate $ArtifactsRoot; Assert-Deadline $Root
    if (@(Get-NetTCPConnection -LocalPort $config.server_port -ErrorAction SilentlyContinue).Count -gt 0) { throw 'Port occupied; do not stop its owner.' }
    $adapter = Get-Adapter; $sample = Get-ResourceSample $Root $adapter 0 $ArtifactsRoot
    Write-NewJson (Join-Path $Root 'preflight.json') @{ utc = [DateTime]::UtcNow.ToString('o'); measured = $sample; thresholds = $config.limits }
    Assert-Resources $sample $config $true
    $pins = Read-Json (Join-Path $Root 'artifacts.json'); $verification = @{}
    foreach ($pin in $pins.artifacts) {
        $path = Join-Path $ArtifactsRoot $pin.file
        if (-not (Test-Path -LiteralPath $path) -or (Get-Item -LiteralPath $path).Length -ne $pin.bytes -or (Get-Sha $path) -cne $pin.sha256) { throw 'Pinned artifact absent or changed; no download or rebuild.' }
        $verification[$pin.file] = @{ bytes = $pin.bytes; sha256 = $pin.sha256; path = $path }
        Assert-Deadline $Root
    }
    $runtimeFiles = Read-Json (Join-Path $Root 'runtime-files.json')
    foreach ($property in $runtimeFiles.PSObject.Properties) {
        if ((Get-Sha (Join-Path $ArtifactsRoot $property.Name)) -cne $property.Value.sha256) { throw 'Runtime dependency changed; no replacement.' }
        Assert-Deadline $Root
    }
    $executable = Join-Path $ArtifactsRoot 'runtime\llama-server.exe'
    if ((Get-Sha $executable) -cne $config.runtime_executable_sha256) { throw 'Pinned runtime executable changed.' }
    Write-NewJson (Join-Path $Root 'artifact_verification.json') @{ status = 'verified_reuse'; artifacts = $verification;
        executable_sha256 = Get-Sha $executable; no_copy_or_download = $true }
    foreach ($probe in @(@{ name = 'runtime_version'; argument = '--version' }, @{ name = 'runtime_devices'; argument = '--list-devices' })) {
        $process = [ResolenaProcess]::Start($executable, $probe.argument, (Join-Path $Root ($probe.name + '.stdout.log')), (Join-Path $Root ($probe.name + '.stderr.log')))
        if (-not $process.WaitForExit(10000)) { $process.Kill(); $process.WaitForExit(); throw 'Runtime compatibility probe timed out; no model load.' }
        $process.WaitForExit()
        Write-NewJson (Join-Path $Root ($probe.name + '.exit.json')) @{ exit_code = $process.ExitCode; confirmed_exited = $true }
        if ($process.ExitCode -ne 0) { throw 'Runtime compatibility probe failed; no retry.' }
        Assert-Deadline $Root
    }
    $versionText = (Read-LiveText (Join-Path $Root 'runtime_version.stdout.log')) + (Read-LiveText (Join-Path $Root 'runtime_version.stderr.log'))
    $devicesText = Read-LiveText (Join-Path $Root 'runtime_devices.stdout.log')
    if ($versionText -notmatch '11429' -or $versionText -notmatch 'd81235049' -or $devicesText -notmatch 'Vulkan0:.*RX\s*6800\s*XT') { throw 'Actual build/device mismatch.' }
    $sample = Get-ResourceSample $Root $adapter 0 $ArtifactsRoot
    Write-NewJson (Join-Path $Root 'preload_resources.json') $sample; Assert-Resources $sample $config $true
    Write-NewJson (Join-Path $Root 'hardware.json') @{ utc = [DateTime]::UtcNow.ToString('o'); gpu = $sample.gpu_name;
        processors = @(Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors);
        drivers = @(Get-CimInstance Win32_VideoController | Where-Object { $_.Name -match 'RX\s*6800\s*XT' } | Select-Object Name, DriverVersion, DriverDate);
        total_ram_bytes = $sample.total_ram_bytes; target_drive_free_bytes = $sample.disk_free_bytes }
    foreach ($name in @('responses', 'templates', 'checkpoints', 'inbox')) { $null = New-Item -ItemType Directory -Path (Join-Path $Root $name) }
    $model = Join-Path $ArtifactsRoot 'Qwen3-8B-Q8_0.gguf'
    $arguments = @('-m', $model, '--host', '127.0.0.1', '--port', '49187', '--device', 'Vulkan0', '--n-gpu-layers', '99',
        '--fit', 'off', '--threads', '2', '--threads-batch', '2', '--ctx-size', '2048', '--parallel', '1',
        '--batch-size', '64', '--ubatch-size', '64', '--cache-type-k', 'f16', '--cache-type-v', 'f16', '--n-predict', '384',
        '--jinja', '--offline', '--no-warmup', '--no-context-shift', '--no-cache-prompt', '--cache-reuse', '0',
        '--no-agent', '--no-webui', '--no-webui-mcp-proxy', '--log-verbosity', '4')
    Write-NewJson (Join-Path $Root 'server_command.json') @{ executable = $executable; arguments = $arguments;
        environment_overrides_removed = @('LLAMA_*', 'HF_*', 'VK_*'); model_reuse_only = $true }
    Assert-Deadline $Root
    $readyTimer = [Diagnostics.Stopwatch]::StartNew()
    $server = [ResolenaProcess]::Start($executable, (($arguments | ForEach-Object { Quote-Argument $_ }) -join ' '),
        (Join-Path $Root 'server.stdout.log'), (Join-Path $Root 'server.stderr.log'))
    Write-NewJson (Join-Path $Root 'server_process.json') @{ process_id = $server.Id; start_ticks = $server.StartTime.ToUniversalTime().Ticks; executable = $executable }
    $remainingMs = [int][Math]::Max(0, 1800000 - $clock.ElapsedMilliseconds)
    $watchArgs = '-NoProfile -ExecutionPolicy RemoteSigned -File ' + (Quote-Argument (Join-Path $Root 'Watchdog.ps1')) + ' -Root ' + (Quote-Argument $Root) + ' -RemainingMs ' + $remainingMs
    $watch = Start-Process -FilePath (Join-Path $PSHOME 'powershell.exe') -ArgumentList $watchArgs -PassThru -WindowStyle Hidden
    Write-NewJson (Join-Path $Root 'watchdog_process.json') @{ process_id = $watch.Id; start_ticks = $watch.StartTime.ToUniversalTime().Ticks;
        executable = Join-Path $PSHOME 'powershell.exe' }
    $client = New-LocalClient; $base = 'http://127.0.0.1:49187'; $ready = $false
    while ($readyTimer.Elapsed.TotalSeconds -lt 90) {
        Assert-RunAlive $Root $server $watch
        try { $health = Invoke-GetJson $client ($base + '/health') 1 } catch { Start-Sleep -Milliseconds 100; continue }
        $log = Read-LiveText (Join-Path $Root 'server.stderr.log')
        if ($health.http_status -eq 200 -and (Test-OffloadText $log)) {
            $sample = Get-ResourceSample $Root $adapter $server.Id
            Assert-Resources $sample $config
            if ($sample.owned_gpu_bytes -gt 0) { $ready = $true; break }
        }
        Start-Sleep -Milliseconds 100
    }
    if (-not $ready) { throw 'Readiness/offload evidence absent within 90 seconds; no generation or retry.' }
    Assert-Loopback $server.Id $true
    Write-NewJson (Join-Path $Root 'readiness.json') @{ ready = $true; seconds = $readyTimer.Elapsed.TotalSeconds; utc = [DateTime]::UtcNow.ToString('o') }
    Write-NewJson (Join-Path $Root 'offload_evidence.json') @{ full_reported_layers = $true;
        raw_lines = @($log.Split("`n") | Where-Object { $_ -match 'offloaded|model buffer size|KV.*buffer|compute buffer' });
        owned_allocation_sample = $sample; selected_device = 'Vulkan0'; speedup_established = $false }
    $propsResponse = Invoke-GetJson $client ($base + '/props') (Remaining-Seconds $Root 5)
    Write-NewJson (Join-Path $Root 'server_properties.json') $propsResponse
    $props = $propsResponse.raw_body | ConvertFrom-Json
    if ($propsResponse.http_status -ne 200 -or $props.total_slots -ne 1 -or $props.default_generation_settings.n_ctx -ne 2048 -or $props.model_ftype -cne 'Q8_0') { throw 'Actual slot/context/model type mismatch.' }
    $plan = @(Read-Json (Join-Path $Root 'order.json')); $capacity = @{ context = 2048; output_tokens = 384; requests = @{} }
    foreach ($entry in $plan) {
        Assert-RunAlive $Root $server $watch; Assert-Bundle $Root
        $body = [IO.File]::ReadAllText((Join-Path $Root $entry.request), [Text.Encoding]::UTF8); $request = $body | ConvertFrom-Json
        $templateBody = @{ messages = $request.messages; chat_template_kwargs = @{ enable_thinking = $false }; add_generation_prompt = $true } | ConvertTo-Json -Depth 40
        $template = Invoke-LocalJson $client ($base + '/apply-template') $templateBody (Remaining-Seconds $Root 5)
        Write-NewJson (Join-Path $Root ('templates\' + $entry.id + '.json')) $template
        if ($template.http_status -ne 200) { throw 'Actual template probe failed.' }
        $formatted = ($template.raw_body | ConvertFrom-Json).prompt
        if ($formatted -notmatch '(?s)<\|im_start\|>assistant\s*<think>\s*</think>\s*$') { throw 'Non-thinking template prefix mismatch.' }
        $tokenBody = @{ content = $formatted; add_special = $true; parse_special = $true } | ConvertTo-Json -Depth 8
        $tokens = Invoke-LocalJson $client ($base + '/tokenize') $tokenBody (Remaining-Seconds $Root 5)
        Write-NewJson (Join-Path $Root ('templates\' + $entry.id + '.tokens.json')) $tokens
        if ($tokens.http_status -ne 200) { throw 'Actual tokenizer probe failed.' }
        $count = @(($tokens.raw_body | ConvertFrom-Json).tokens).Count
        if ($count -lt 1 -or $count + 384 -gt 2048) { throw 'Actual prompt exceeds capacity; no shortening/retuning.' }
        $capacity.requests[$entry.id] = @{ tokens = $count; request_sha256 = Get-Sha (Join-Path $Root $entry.request); nonthinking = $true }
    }
    Write-NewJson (Join-Path $Root 'capacity.json') $capacity
    foreach ($entry in $plan) {
        Assert-RunAlive $Root $server $watch; Assert-Bundle $Root
        $state = Get-State $Root; $state.status = 'request_' + $entry.id; Write-Json (Join-Path $Root 'state.json') $state
        $body = [IO.File]::ReadAllText((Join-Path $Root $entry.request), [Text.Encoding]::UTF8)
        $result = Invoke-LocalJson $client ($base + '/v1/chat/completions') $body (Remaining-Seconds $Root 45)
        $result['run_id'] = $run.run_id; $result['bundle_freeze_sha256'] = $freezeSha; $result['request_id'] = $entry.id
        $result['arm'] = $entry.arm; $result['case'] = $entry.case; $result['request_sha256'] = Get-Sha (Join-Path $Root $entry.request)
        $result['utc'] = [DateTime]::UtcNow.ToString('o')
        Write-NewJson (Join-Path $Root ('responses\' + $entry.id + '.json')) $result
        Assert-WireResponse $result
        $completed += $entry.id
        Write-Json (Join-Path $Root 'progress.json') @{ completed = $completed; utc = [DateTime]::UtcNow.ToString('o'); heldout_model_exposure = 0; DESIGN = 'pending'; linguistic_validation = 'pending' }
        if ($entry.index -in $config.checkpoint_after_indices) { Await-Checkpoint $Root $entry.index $server $watch }
    }
    Assert-Deadline $Root; $exitStatus = 0
} catch {
    Write-NewJson (Join-Path $Root 'run_failure.json') @{ utc = [DateTime]::UtcNow.ToString('o'); error = $_.Exception.Message;
        measured_elapsed_seconds = $clock.Elapsed.TotalSeconds; thresholds = $config.limits; completed = $completed; no_retry = $true }
} finally {
    if ($null -ne $client) { $client.Dispose() }
    try {
        $wasRunning = $null -ne $server -and -not $server.HasExited
        Stop-Owned $Root
        if ($null -ne $server) {
            if (-not $server.WaitForExit(10000)) { throw 'Owned server exit unconfirmed.' }
            $server.WaitForExit()
            Write-NewJson (Join-Path $Root 'server_exit.json') @{ confirmed_exited = $true; exit_code = $server.ExitCode;
                planned_owned_shutdown = $wasRunning; utc = [DateTime]::UtcNow.ToString('o') }
        }
        if ($null -ne $watch) {
            if (-not $watch.WaitForExit(15000)) {
                $r = Read-Json (Join-Path $Root 'watchdog_process.json'); $ownedWatch = Get-Process -Id $r.process_id
                if ($ownedWatch.StartTime.ToUniversalTime().Ticks -ne [long]$r.start_ticks -or $ownedWatch.Path -ine $r.executable) { throw 'Watchdog ownership mismatch; no process stopped.' }
                $ownedWatch.Kill(); $ownedWatch.WaitForExit(); $exitStatus = 1
                Write-NewJson (Join-Path $Root 'watchdog_forced_exit.json') @{ confirmed_exited = $true; exit_code = $ownedWatch.ExitCode;
                    reason = 'Owned watchdog blocked after confirmed model shutdown; no restart.' }
            }
            Write-NewJson (Join-Path $Root 'watchdog_process_exit.json') @{ confirmed_exited = $true; exit_code = $watch.ExitCode; utc = [DateTime]::UtcNow.ToString('o') }
        }
        Write-NewJson (Join-Path $Root 'driver_exit.json') @{ exit_code = $exitStatus; completed_requests = $completed.Count;
            elapsed_seconds = $clock.Elapsed.TotalSeconds; original_deadline_utc = $run.deadline_utc; DESIGN = 'pending'; linguistic_validation = 'pending' }
        Close-Run $Root $true
    } catch {
        Write-NewJson (Join-Path $Root 'closeout_failure.json') @{ utc = [DateTime]::UtcNow.ToString('o'); error = $_.Exception.Message; partial_results_preserved = $true }
        $exitStatus = 1
    }
}
exit $exitStatus
