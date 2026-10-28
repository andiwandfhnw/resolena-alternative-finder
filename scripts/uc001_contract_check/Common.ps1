Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Read-ContractJson([string]$Path) { return ([IO.File]::ReadAllText($Path) | ConvertFrom-Json) }
function Get-ContractHash([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Assert-ContractBundle {
    $freeze = Read-ContractJson (Join-Path $PSScriptRoot 'freeze.json')
    foreach ($item in $freeze.files.PSObject.Properties) {
        if ((Get-ContractHash (Join-Path $PSScriptRoot $item.Name)) -ne $item.Value) { throw ('Frozen bundle mismatch: ' + $item.Name) }
    }
}
function Assert-ContractWindows {
    if ($PSVersionTable.PSEdition -ne 'Desktop' -or $PSVersionTable.PSVersion -lt [version]'5.1' -or -not [Environment]::Is64BitProcess) {
        throw 'Use existing 64-bit Windows PowerShell 5.1; no automatic installation.'
    }
    if ($ExecutionContext.SessionState.LanguageMode -ne 'FullLanguage') { throw 'FullLanguage required; do not bypass managed policy.' }
}
function Get-ContractAdapter {
    if (-not ('ContractDxgi' -as [type])) { Add-Type -Path (Join-Path $PSScriptRoot 'Dxgi.cs') }
    $adapters = @([ContractDxgi]::ReadAdapters() | Where-Object { $_.Vendor -eq 4098 -and $_.Name -match 'RX\s*6800\s*XT' })
    if ($adapters.Count -ne 1) { throw 'Exactly one retained RX 6800 XT must be measurable.' }
    return $adapters[0]
}
function Get-ReadOnlyContractAdapter {
    $controllers = @(Get-CimInstance Win32_VideoController)
    if ($controllers.Count -ne 1 -or $controllers[0].Name -notmatch 'RX\s*6800\s*XT') { throw 'Read-only preflight requires one unambiguously mapped active RX 6800 XT.' }
    $device = Get-ItemProperty -LiteralPath ('HKLM:\SYSTEM\CurrentControlSet\Enum\' + $controllers[0].PNPDeviceID)
    $driver = Get-ItemProperty -LiteralPath ('HKLM:\SYSTEM\CurrentControlSet\Control\Class\' + $device.Driver)
    $property = $driver.PSObject.Properties['HardwareInformation.qwMemorySize']
    if ($null -eq $property) { throw 'Active driver has no 64-bit dedicated-memory capacity; do not use truncated AdapterRAM or guess.' }
    $bytes = $property.Value
    if ($bytes -is [byte[]]) {
        if ($bytes.Length -ne 8) { throw 'GPU capacity is not a 64-bit value.' }
        $bytes = [BitConverter]::ToUInt64($bytes,0)
    }
    if ([long]$bytes -le 0) { throw 'GPU capacity is unavailable.' }
    $gauges = @(Get-CimInstance Win32_PerfRawData_GPUPerformanceCounters_GPUAdapterMemory)
    if ($gauges.Count -ne 1 -or $gauges[0].Name -notmatch '^luid_0x[0-9a-fA-F]{8}_0x[0-9a-fA-F]{8}_phys_0$') { throw 'Read-only active-adapter/WDDM association is ambiguous; stop without a measurement substitute.' }
    return [pscustomobject]@{Name=$controllers[0].Name; CounterKey=($gauges[0].Name -replace '_phys_0$',''); DedicatedBytes=[long]$bytes}
}
function Get-ContractResources($Adapter, [string]$RunRoot, $OwnedProcess = $null) {
    $os = Get-CimInstance Win32_OperatingSystem
    $drive = New-Object IO.DriveInfo ([IO.Path]::GetPathRoot($RunRoot))
    $gauge = @(Get-CimInstance Win32_PerfRawData_GPUPerformanceCounters_GPUAdapterMemory | Where-Object { $_.Name -like ($Adapter.CounterKey + '*') })
    if ($gauge.Count -ne 1 -or $null -eq $gauge[0].DedicatedUsage) { throw 'Unique adapter WDDM usage unavailable; no substitute.' }
    $counterClass = Get-CimClass Win32_PerfRawData_GPUPerformanceCounters_GPUProcessMemory
    if ('DedicatedUsage' -notin $counterClass.CimClassProperties.Name) { throw 'Owned GPU counter unavailable.' }
    $rss = 0L; $gpu = 0L
    if ($null -ne $OwnedProcess) {
        $OwnedProcess.Refresh()
        if ($OwnedProcess.HasExited) { throw 'Owned server exited.' }
        $rss = [long]$OwnedProcess.WorkingSet64
        $owned = @(Get-CimInstance Win32_PerfRawData_GPUPerformanceCounters_GPUProcessMemory | Where-Object { $_.Name -like ('pid_' + $OwnedProcess.Id + '_' + $Adapter.CounterKey + '*') })
        if ($owned.Count -gt 1) { throw 'Ambiguous owned GPU counters.' }
        if ($owned.Count -eq 1) { $gpu = [long]$owned[0].DedicatedUsage }
    }
    $bytes = 0L
    if (Test-Path -LiteralPath $RunRoot) {
        $size = Get-ChildItem -LiteralPath $RunRoot -Recurse -File | Measure-Object Length -Sum
        if ($null -ne $size.Sum) { $bytes = [long]$size.Sum }
    }
    return [ordered]@{ utc = [DateTime]::UtcNow.ToString('o'); ram_free = [long]$os.FreePhysicalMemory * 1024
        ram_total = [long]$os.TotalVisibleMemorySize * 1024; disk_free = [long]$drive.AvailableFreeSpace
        gpu_free = [long]$Adapter.DedicatedBytes - [long]$gauge[0].DedicatedUsage
        gpu_total = [long]$Adapter.DedicatedBytes; owned_gpu = $gpu; owned_rss = $rss; artifact_bytes = $bytes }
}
function Assert-ContractResources($Sample, $Limits, [bool]$Preflight = $false) {
    if ($Preflight -and ($Sample.ram_free -lt $Limits.ram_preflight_bytes -or $Sample.gpu_free -lt $Limits.gpu_preflight_free_bytes -or $Sample.disk_free -lt $Limits.disk_preflight_free_bytes)) {
        throw 'Preflight headroom failed: RAM 20 GiB, free VRAM 14 GiB, free disk 6 GiB required.'
    }
    if ($Sample.ram_free -lt $Limits.ram_floor_bytes -or $Sample.gpu_free -lt $Limits.gpu_floor_bytes -or $Sample.disk_free -lt $Limits.disk_floor_bytes -or
        $Sample.owned_gpu -gt $Limits.gpu_owned_bytes -or $Sample.owned_rss -gt $Limits.rss_bytes -or $Sample.artifact_bytes -gt $Limits.windows_artifact_bytes) {
        throw 'Runtime resource floor/cap failed.'
    }
}
function Get-ContractAssets($Config) {
    $root = $Config.reuse_root
    foreach ($asset in $Config.assets) {
        $path = Join-Path $root $asset.file
        if ((Get-Item -LiteralPath $path).Length -ne $asset.bytes -or (Get-ContractHash $path) -ne $asset.sha256) { throw ('Retained asset mismatch: ' + $asset.file) }
    }
    $runtime = Read-ContractJson (Join-Path $PSScriptRoot 'runtime-files.json')
    foreach ($file in $runtime.PSObject.Properties) {
        $path = Join-Path $root $file.Name
        if ((Get-Item -LiteralPath $path).Length -ne $file.Value.bytes -or (Get-ContractHash $path) -ne $file.Value.sha256) { throw ('Retained runtime mismatch: ' + $file.Name) }
    }
}
function Get-ContractTools {
    $ssh = Get-Command ssh.exe -ErrorAction SilentlyContinue
    $gh = Get-Command gh.exe -ErrorAction SilentlyContinue
    $sshVersion = $null; $ghVersion = $null
    if ($null -ne $ssh) { $sshVersion = [Diagnostics.FileVersionInfo]::GetVersionInfo($ssh.Source).ProductVersion }
    if ($null -ne $gh) { $ghVersion = (& $gh.Source --version | Select-Object -First 1) }
    return [ordered]@{ ssh = $(if ($ssh) { $ssh.Source } else { $null }); ssh_version = $sshVersion
        gh = $(if ($gh) { $gh.Source } else { $null }); gh_version = $ghVersion
        gh_pin_available = ($null -ne $ghVersion -and $ghVersion -match '^gh version 2\.81\.0\b') }
}
