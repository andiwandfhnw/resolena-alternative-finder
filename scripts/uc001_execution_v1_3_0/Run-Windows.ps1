[CmdletBinding()]
param([switch]$Execute, [Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9-]+$')][string]$Codespace)

function Quoted([string]$Value) {
    if ($Value.Contains('"') -or $Value.Contains("`n") -or $Value.Contains("`r")) { throw 'Unsafe process argument.' }
    return '"' + $Value + '"'
}
function Get-Http([string]$Path, [string]$Token) {
    $request = New-Object Net.Http.HttpRequestMessage ([Net.Http.HttpMethod]::Get), ('http://127.0.0.1:49187' + $Path)
    if ($Token) { $request.Headers.Authorization = New-Object Net.Http.Headers.AuthenticationHeaderValue 'Bearer',$Token }
    try { return $client.SendAsync($request).GetAwaiter().GetResult() } finally { $request.Dispose() }
}
function Check-Running {
    $sample = Get-ContractResources $adapter $runRoot $server
    Assert-ContractResources $sample $config.limits
    if (([DateTime]::UtcNow - $modelStart).TotalSeconds -ge 1500 -or ([DateTime]::UtcNow - $totalStart).TotalSeconds -ge 2400) { throw 'Fixed model/total deadline expired.' }
    ($sample | ConvertTo-Json -Compress) | Add-Content -LiteralPath (Join-Path $runRoot 'resources.jsonl')
}
function Invoke-ContractExecution([string]$Codespace) {
    Assert-ContractWindows
    Assert-ContractBundle
    $totalStart = [DateTime]::UtcNow
    $config = Read-ContractJson (Join-Path $PSScriptRoot 'config.json')
    Get-ContractAssets $config
    $adapter = Get-ContractAdapter
    $tools = Get-ContractTools
    if (-not $tools.gh_pin_available -or $null -eq $tools.ssh) { throw 'Pinned gh 2.81.0 and existing Windows OpenSSH client required; no install/fallback.' }
    if (@(Get-CimInstance Win32_Process -Filter "Name='llama-server.exe'").Count -gt 0) { throw 'Existing server present; do not duplicate or stop it.' }
    if (@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -in @(49187,49189) }).Count -gt 0) { throw 'Owned ports are occupied.' }
    $runId = [guid]::NewGuid().ToString()
    $freezeHash = Get-ContractHash (Join-Path $PSScriptRoot 'freeze.json')
    $attemptIdentity = (Read-ContractJson (Join-Path $PSScriptRoot 'freeze.json')).attempt_identity
    if ($attemptIdentity -ne 'bda2015c0ffbe89ab1a612fb4003b2b12f254871cf32f2e47dbbbe9d45cf0f52') { throw 'Original attempt identity must be preserved; no reset.' }
    $runRoot = Join-Path (Split-Path $config.reuse_root -Parent) ('uc001-contract-runs\' + $attemptIdentity)
    if (Test-Path -LiteralPath $runRoot) { throw 'This frozen bundle has already started/attempted. Preserve it; no restart or deadline reset.' }
    $sample = Get-ContractResources $adapter $runRoot
    Assert-ContractResources $sample $config.limits $true
    if (([DateTime]::UtcNow - $totalStart).TotalSeconds -ge 2400) { throw 'Total preparation/execution budget expired.' }
    $null = New-Item -ItemType Directory -Path $runRoot
    $job = $null; $client = $null; $server = $null; $tunnel = $null; $key = $null
    try {
        Initialize-ContractProcessSupport
        $job = New-ContractJob
        $random = New-Object byte[] 32
        $rng = [Security.Cryptography.RandomNumberGenerator]::Create(); $rng.GetBytes($random); $rng.Dispose()
        $key = [Convert]::ToBase64String($random)
        $argsList = @('--model',(Join-Path $config.reuse_root 'Qwen3-8B-Q8_0.gguf'),'--alias','uc001-qwen3-8b',
            '--host','127.0.0.1','--port','49187','--offline','--no-webui','--no-warmup','--fit','off',
            '--device','Vulkan0','--n-gpu-layers','37','--threads','2','--threads-batch','2','--parallel','1',
            '--ctx-size','8192','--predict','3072','--batch-size','64','--ubatch-size','64',
            '--cache-type-k','f16','--cache-type-v','f16','--cache-ram','0','--temp','0.7','--top-p','0.8','--top-k','20','--min-p','0','--seed','42',
            '--jinja','--chat-template-kwargs','{"enable_thinking":false}','--log-verbosity','4')
        # StartProcess receives a Windows command line; escape the one JSON flag explicitly.
        $arguments = ($argsList | ForEach-Object { if ($_ -eq '{"enable_thinking":false}') { '"{\"enable_thinking\":false}"' } else { Quoted $_ } }) -join ' '
        $modelStart = [DateTime]::UtcNow
        $server = Start-ContractProcess $job (Join-Path $config.reuse_root 'runtime\llama-server.exe') $arguments (Join-Path $runRoot 'server.stdout.log') (Join-Path $runRoot 'server.stderr.log') $key
        $server.StandardInput.Close()
        $client = New-ContractHttpClient
        $props = $null
        while ($null -eq $props) {
            Check-Running
            if (([DateTime]::UtcNow - $modelStart).TotalSeconds -ge 90) { throw 'Readiness deadline expired; no restart.' }
            try { $response = Get-Http '/props' $key } catch [Net.Http.HttpRequestException] { Start-Sleep -Milliseconds 500; continue }
            try {
                if ([int]$response.StatusCode -eq 200) { $props = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult() | ConvertFrom-Json }
                elseif ([int]$response.StatusCode -ne 503) { throw 'Readiness/authentication failed.' }
            } finally { $response.Dispose() }
            if ($null -eq $props) { Start-Sleep -Milliseconds 500 }
        }
        foreach ($token in @('', 'deliberately-invalid')) {
            $response = Get-Http '/v1/models' $token
            try { if ([int]$response.StatusCode -ne 401) { throw 'Protected endpoint accepted missing/wrong authentication.' } } finally { $response.Dispose() }
        }
        $response = Get-Http '/v1/models' $key
        try { if ([int]$response.StatusCode -ne 200) { throw 'Valid authentication rejected.' } } finally { $response.Dispose() }
        $listeners = @(Get-NetTCPConnection -State Listen | Where-Object { $_.OwningProcess -eq $server.Id })
        if ($listeners.Count -ne 1 -or $listeners[0].LocalAddress -ne '127.0.0.1' -or $listeners[0].LocalPort -ne 49187) { throw 'Owned model listener is not loopback-only.' }
        $sample = Get-ContractResources $adapter $runRoot $server
        if ($sample.owned_gpu -le 0) { throw 'Positive owned GPU allocation missing.' }
        $log = [IO.File]::ReadAllText((Join-Path $runRoot 'server.stderr.log'))
        $selectedLog = ($log -split "`n" | Where-Object { $_ -match 'build 11429|using device Vulkan0|offloaded \d+/\d+ layers|n_threads =|n_ctx_seq\s*=|n_batch\s*=|n_ubatch\s*=|K \(f16\):' }) -join "`n"
        $compactProps = @{ total_slots=$props.total_slots; build_info=$props.build_info; model_path=$props.model_path
            default_generation_settings=@{n_ctx=$props.default_generation_settings.n_ctx; params=$props.default_generation_settings.params} }
        $receipt = @{run_id=$runId; attempt_identity=$attemptIdentity; freeze_sha256=(Get-ContractHash (Join-Path $PSScriptRoot 'freeze.json'))
            started_utc=$modelStart.ToString('o'); total_started_utc=$totalStart.ToString('o'); receipt_epoch=([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())
            authentication_verified=$true; props=$compactProps; startup_log=$selectedLog; owned_pid=$server.Id; resource_sample=$sample}
        $receiptText = $receipt | ConvertTo-Json -Depth 30 -Compress
        [IO.File]::WriteAllText((Join-Path $runRoot 'windows-receipt.json'),$receiptText)
        $encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($receiptText))
        $remote = 'cd /workspaces/resolena-alternative-finder && PYTHONPATH=src:. .venv/bin/python -m scripts.uc001_execution_v1_3_0.run --execute --key-stdin --review build/test-only/contract-review.json --windows-receipt-base64 ' + $encoded
        $sshArgs = @('codespace','ssh','--codespace',$Codespace,'--server-port','49189','--','-T','-o','BatchMode=yes',
            '-o','ExitOnForwardFailure=yes','-o','ServerAliveInterval=5','-o','ServerAliveCountMax=2','-o','ConnectTimeout=15',
            '-R','127.0.0.1:49188:127.0.0.1:49187',$remote)
        $tunnel = Start-ContractProcess $job $tools.gh (($sshArgs | ForEach-Object { Quoted $_ }) -join ' ') (Join-Path $runRoot 'transport.stdout.log') (Join-Path $runRoot 'transport.stderr.log') $null
        $bridgeReady = $false
        while (-not $bridgeReady) {
            Check-Running
            $tunnel.Refresh()
            if ($tunnel.HasExited) { throw 'Transport exited before its loopback bridge was established.' }
            $bridge = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq 49189 })
            if ($bridge.Count -gt 0) {
                if (@($bridge | Where-Object { $_.LocalAddress -notin @('127.0.0.1','::1') -or $_.OwningProcess -ne $tunnel.Id }).Count -gt 0) { throw 'Transport bridge is not an owned loopback-only listener.' }
                $bridgeReady = $true
            } else { Start-Sleep -Milliseconds 250 }
        }
        # The remote runner cannot authenticate/generate until this loopback proof succeeds.
        $tunnel.StandardInput.WriteLine($key); $tunnel.StandardInput.Close()
        while (-not $tunnel.HasExited) { Check-Running; Start-Sleep -Seconds 1; $tunnel.Refresh() }
        if ($tunnel.ExitCode -ne 0) { throw ('Transport/application check stopped: exit ' + $tunnel.ExitCode) }
        'completed; semantic review pending' | Set-Content -LiteralPath (Join-Path $runRoot 'status.txt')
    } catch {
        $_.Exception.Message | Set-Content -LiteralPath (Join-Path $runRoot 'stopped.txt')
        throw
    } finally {
        try { Complete-ContractCleanup $client $job $server $tunnel $runRoot } finally { $key = $null }
    }
}

if ($MyInvocation.InvocationName -ne '.') {
    if (-not $Execute) { throw 'Preparation only. -Execute requires separate owner authorization for live execution and transport.' }
    . (Join-Path $PSScriptRoot 'Common.ps1')
    Invoke-ContractExecution $Codespace
}
