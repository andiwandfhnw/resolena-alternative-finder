Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Read-Json([string]$Path) {
    return ([IO.File]::ReadAllText($Path, [Text.Encoding]::UTF8) | ConvertFrom-Json)
}
function Write-Json([string]$Path, $Value) {
    $temporary = $Path + '.tmp'
    [IO.File]::WriteAllText($temporary, ($Value | ConvertTo-Json -Depth 40), (New-Object Text.UTF8Encoding($false)))
    Move-Item -LiteralPath $temporary -Destination $Path -Force
}
function Get-Sha([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Assert-Bundle([string]$Root) {
    if ($PSVersionTable.PSEdition -ne 'Desktop' -or $PSVersionTable.PSVersion -lt [version]'5.1' -or -not [Environment]::Is64BitProcess) {
        throw 'Use existing 64-bit Windows PowerShell 5.1. Stop if unavailable; do not install prerequisites.'
    }
    if ($ExecutionContext.SessionState.LanguageMode -ne 'FullLanguage') { throw 'FullLanguage is required. Do not bypass managed policy.' }
    $null = Get-Command Get-NetTCPConnection
    $null = Get-Command Get-NetUDPEndpoint
    $freeze = Read-Json (Join-Path $Root 'freeze.json')
    foreach ($property in $freeze.files.PSObject.Properties) {
        $file = Join-Path $Root $property.Name
        if (-not (Test-Path -LiteralPath $file -PathType Leaf) -or (Get-Sha $file) -ne $property.Value) { throw ('Frozen bundle mismatch: ' + $property.Name) }
    }
}
function Get-Adapter {
    if (-not ('ResolenaDxgi' -as [type])) { Add-Type -Path (Join-Path $PSScriptRoot 'Native.cs') }
    $adapters = @([ResolenaDxgi]::ReadAdapters() | Where-Object { $_.Name -match 'RX\s*6800\s*XT' -and $_.Vendor -eq 4098 })
    if ($adapters.Count -ne 1) { throw 'Exactly one RX 6800 XT must be identified through DXGI.' }
    return $adapters[0]
}
function Get-ResourceSample([string]$Root, $Adapter, [int]$OwnedId = 0) {
    $os = Get-CimInstance -ClassName Win32_OperatingSystem
    $drive = New-Object IO.DriveInfo ([IO.Path]::GetPathRoot($Root))
    $global = @(Get-CimInstance -ClassName Win32_PerfRawData_GPUPerformanceCounters_GPUAdapterMemory | Where-Object { $_.Name -like ($Adapter.CounterKey + '*') })
    if ($global.Count -ne 1 -or $null -eq $global[0].DedicatedUsage) { throw 'Cannot uniquely measure this adapter dedicated usage. Stop; no measurement substitute or driver update.' }
    $counterClass = Get-CimClass -ClassName Win32_PerfRawData_GPUPerformanceCounters_GPUProcessMemory
    if ('DedicatedUsage' -notin $counterClass.CimClassProperties.Name) { throw 'Owned GPU-memory counter prerequisite is unavailable.' }
    $used = [long]$global[0].DedicatedUsage
    $ownedGpu = 0L
    $rss = 0L
    $private = 0L
    if ($OwnedId -gt 0) {
        $process = Get-Process -Id $OwnedId
        $rss = [long]$process.WorkingSet64
        $private = [long]$process.PrivateMemorySize64
        $local = @(Get-CimInstance -ClassName Win32_PerfRawData_GPUPerformanceCounters_GPUProcessMemory | Where-Object { $_.Name -like ('pid_' + $OwnedId + '_' + $Adapter.CounterKey + '*') })
        if ($local.Count -gt 1) { throw 'Ambiguous owned GPU process counters.' }
        if ($local.Count -eq 0 -and (Test-Path -LiteralPath (Join-Path $Root 'readiness.json'))) { throw 'Owned GPU usage cannot be measured after readiness.' }
        if ($local.Count -eq 1) { $ownedGpu = [long]$local[0].DedicatedUsage }
    }
    $scratch = 0L
    if (Test-Path -LiteralPath $Root) {
        $total = Get-ChildItem -LiteralPath $Root -File -Recurse | Measure-Object -Property Length -Sum
        if ($null -ne $total.Sum) { $scratch = [long]$total.Sum }
    }
    return [ordered]@{
        utc = [DateTime]::UtcNow.ToString('o'); available_ram_bytes = [long]$os.FreePhysicalMemory * 1024
        total_ram_bytes = [long]$os.TotalVisibleMemorySize * 1024
        disk_free_bytes = [long]$drive.AvailableFreeSpace; scratch_bytes = $scratch
        gpu_name = $Adapter.Name; dedicated_total_bytes = [long]$Adapter.DedicatedBytes
        adapter_dedicated_used_bytes = $used; adapter_free_bytes = [long]$Adapter.DedicatedBytes - $used
        owned_gpu_bytes = $ownedGpu; owned_rss_bytes = $rss; owned_private_bytes = $private
        gpu_measurement = 'DXGI capacity minus WDDM dedicated-usage gauge; not DXGI per-process dynamic residency budget'
    }
}
function Assert-Resources($Sample, $Config, [bool]$Preflight = $false) {
    $limits = $Config.limits
    if ($Preflight) {
        if ($Sample.available_ram_bytes -lt $limits.ram_preflight_bytes) { throw 'Available RAM below 20 GiB preflight minimum.' }
        if ($Sample.disk_free_bytes -lt $limits.disk_preflight_free_bytes) { throw 'Selected drive has less than 30 GiB free.' }
        if ($Sample.adapter_free_bytes -lt $limits.gpu_preflight_free_bytes) { throw 'Dedicated VRAM headroom below 14 GiB.' }
    }
    if ($Sample.available_ram_bytes -lt $limits.ram_floor_bytes -or $Sample.disk_free_bytes -lt $limits.disk_floor_bytes -or
        $Sample.adapter_free_bytes -lt $limits.gpu_floor_bytes -or $Sample.scratch_bytes -gt $limits.scratch_bytes -or
        $Sample.owned_rss_bytes -gt $limits.rss_bytes -or $Sample.owned_gpu_bytes -gt $limits.gpu_owned_bytes) { throw 'Runtime resource guard failed.' }
}
function Assert-NoDuplicate([string]$Root) {
    $owned = @(Get-CimInstance -ClassName Win32_Process -Filter "Name='llama-server.exe'" | Where-Object {
        $_.ExecutablePath -and $_.ExecutablePath.StartsWith($Root + '\', [StringComparison]::OrdinalIgnoreCase) })
    if ($owned.Count -gt 0) { throw 'An experiment-owned server is already present; do not duplicate or stop it.' }
}
function Quote-Argument([string]$Value) {
    if ($Value.Contains('"') -or $Value.Contains("`n")) { throw 'Unsupported quote/newline in argument.' }
    return '"' + $Value + '"'
}
function Get-State([string]$Root) { return Read-Json (Join-Path $Root 'state.json') }
function Assert-Deadline([string]$Root, [string]$Stage) {
    $state = Get-State $Root
    $now = [DateTime]::UtcNow
    if ($now -ge [DateTime]::Parse($state.total_deadline_utc).ToUniversalTime()) { throw 'Original total deadline expired; no reset/retry.' }
    if ($Stage -eq 'setup' -and $now -ge [DateTime]::Parse($state.setup_deadline_utc).ToUniversalTime()) { throw 'Original setup deadline expired.' }
    if ($state.PSObject.Properties.Name -contains 'evaluation_deadline_utc' -and $now -ge [DateTime]::Parse($state.evaluation_deadline_utc).ToUniversalTime()) { throw 'Original evaluation deadline expired.' }
}
function New-LocalClient {
    Add-Type -AssemblyName System.Net.Http
    $handler = New-Object Net.Http.HttpClientHandler
    $handler.UseProxy = $false
    $client = New-Object -TypeName Net.Http.HttpClient -ArgumentList $handler
    $client.Timeout = [TimeSpan]::FromSeconds(45)
    return $client
}
function Invoke-LocalJson($Client, [string]$Url, [string]$Body, [int]$Timeout = 45) {
    $cts = New-Object Threading.CancellationTokenSource
    $cts.CancelAfter($Timeout * 1000)
    $content = New-Object -TypeName Net.Http.StringContent -ArgumentList @($Body, [Text.Encoding]::UTF8, 'application/json')
    $timer = [Diagnostics.Stopwatch]::StartNew()
    try {
        $task = $Client.PostAsync($Url, $content, $cts.Token)
        $response = $task.GetAwaiter().GetResult()
        $raw = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
        return [ordered]@{ http_status = [int]$response.StatusCode; raw_body = $raw; wall_seconds = $timer.Elapsed.TotalSeconds }
    } catch {
        return [ordered]@{ http_status = 0; raw_body = $null; wall_seconds = $timer.Elapsed.TotalSeconds; transport_error = $_.Exception.Message }
    } finally { $content.Dispose(); $cts.Dispose() }
}
function Stop-Owned([string]$Root) {
    $receiptPath = Join-Path $Root 'server_process.json'
    if (-not (Test-Path -LiteralPath $receiptPath)) { return }
    $receipt = Read-Json $receiptPath
    $process = Get-Process -Id $receipt.process_id -ErrorAction SilentlyContinue
    if ($null -eq $process) { return }
    if ($process.StartTime.ToUniversalTime().Ticks -ne [long]$receipt.start_ticks -or $process.Path -ne $receipt.executable) {
        throw 'PID ownership mismatch; no process stopped.'
    }
    Stop-Process -Id $receipt.process_id
}
function Assert-Loopback([int]$OwnedId, [bool]$RequireListener = $false) {
    $tcp = @(Get-NetTCPConnection -OwningProcess $OwnedId -ErrorAction SilentlyContinue)
    if ($RequireListener -and @($tcp | Where-Object { $_.State -eq 'Listen' }).Count -ne 1) { throw 'Owned loopback listener cannot be verified.' }
    foreach ($connection in $tcp) {
        if ($connection.LocalAddress -notin @('127.0.0.1', '::1') -or $connection.RemoteAddress -notin @('127.0.0.1', '::1', '0.0.0.0', '::')) { throw 'Owned TCP endpoint is not loopback-only.' }
    }
    $udp = @(Get-NetUDPEndpoint -OwningProcess $OwnedId -ErrorAction SilentlyContinue)
    if ($udp.Count -gt 0) { throw 'Unexpected owned UDP endpoint.' }
}
function Export-SmallResults([string]$Root, [string]$Name) {
    $archive = Join-Path $Root ($Name + '.zip')
    if (Test-Path -LiteralPath $archive) { throw 'Existing result archive is preserved; do not overwrite.' }
    $snapshot = Join-Path $Root ('exports\' + $Name)
    if (Test-Path -LiteralPath $snapshot) { throw 'Existing export snapshot is preserved.' }
    $null = New-Item -ItemType Directory -Path $snapshot
    $files = @(Get-ChildItem -LiteralPath $Root -File | Where-Object { $_.Extension -in @('.json', '.jsonl', '.log') })
    foreach ($file in $files) {
        $stream = [IO.File]::Open($file.FullName, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
        try {
            $reader = New-Object IO.StreamReader($stream, [Text.Encoding]::UTF8)
            $text = $reader.ReadToEnd()
            if ($file.Extension -eq '.jsonl' -and -not $text.EndsWith("`n")) {
                $last = $text.LastIndexOf("`n")
                $text = $(if ($last -lt 0) { '' } else { $text.Substring(0, $last + 1) })
            }
            [IO.File]::WriteAllText((Join-Path $snapshot $file.Name), $text, (New-Object Text.UTF8Encoding($false)))
        } finally { $stream.Dispose() }
    }
    foreach ($folder in @('requests', 'responses', 'templates')) {
        $source = Join-Path $Root $folder
        if (Test-Path -LiteralPath $source) { Copy-Item -LiteralPath $source -Destination $snapshot -Recurse }
    }
    Compress-Archive -Path (Join-Path $snapshot '*') -DestinationPath $archive
    Write-Host ('Saved small results: ' + $archive)
    Write-Host ('SHA-256: ' + (Get-Sha $archive))
}
