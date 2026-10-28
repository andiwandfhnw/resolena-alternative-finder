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
    return Get-ReadOnlyContractAdapter
}
function Read-AssociationDxgi {
    if (-not ('Uc001PreflightAssociationV110.Reader' -as [type])) { Add-Type -Path (Join-Path $PSScriptRoot 'AdapterIdentity.cs') -ErrorAction Stop }
    return [Uc001PreflightAssociationV110.Reader]::Read()
}
function Get-AssociationInteger($Value, [string]$Label) {
    $integral = $Value -is [byte] -or $Value -is [sbyte] -or $Value -is [int16] -or $Value -is [uint16] -or
        $Value -is [int32] -or $Value -is [uint32] -or $Value -is [int64] -or $Value -is [uint64]
    if (-not $integral -or $Value -lt 0 -or $Value -gt [long]::MaxValue) { throw ($Label + ' is missing or not a usable nonnegative integer; no substitution.') }
    return [long]$Value
}
function Get-AssociatedUsage($Adapter, $Counters) {
    $name = $Adapter.CounterKey + '_phys_0'
    $matches = @($Counters | Where-Object {
        $identity = $_.PSObject.Properties['Name']
        if ($null -eq $identity -or $identity.Value -isnot [string] -or [string]::IsNullOrWhiteSpace($identity.Value)) { throw 'WDDM counter identity is missing or unavailable.' }
        [string]::Equals($identity.Value,$Adapter.CounterKey,[StringComparison]::OrdinalIgnoreCase) -or
            $identity.Value.StartsWith($Adapter.CounterKey+'_',[StringComparison]::OrdinalIgnoreCase)
    })
    if ($matches.Count -ne 1 -or -not [string]::Equals($matches[0].Name,$name,[StringComparison]::OrdinalIgnoreCase)) { throw 'Exactly one WDDM counter for the discovered hardware LUID, with expected phys_0 identity, is required.' }
    $property = $matches[0].PSObject.Properties['DedicatedUsage']
    if ($null -eq $property) { throw 'Matched WDDM counter has no dedicated-usage measurement.' }
    $usage = Get-AssociationInteger $property.Value 'Matched WDDM dedicated usage'
    if ($usage -gt $Adapter.DedicatedBytes) { throw 'WDDM usage exceeds independently checked adapter capacity.' }
    return $usage
}
function Get-RegistryCapacityDiagnostic([string]$PnpDeviceId, [long]$DxgiCapacity) {
    $result = [ordered]@{Status='not_queried';EnumPath=('HKLM:\SYSTEM\CurrentControlSet\Enum\'+$PnpDeviceId)
        DriverMapping=$null;DriverPath=$null;Field='HardwareInformation.qwMemorySize'
        RawValue=$null;RawType=$null;BytesDecimal=$null;DecodedType=$null
        DifferenceStatus='unavailable';DifferenceBytes=$null;DifferenceDirection='DXGI minus registry';DifferenceType='System.Numerics.BigInteger';Error=$null}
    $stage='query'
    try {
        $device=Get-ItemProperty -LiteralPath $result.EnumPath -ErrorAction Stop
        $mapping=$device.PSObject.Properties['Driver']
        if ($null -eq $mapping) { $result.Status='missing_driver'; return [pscustomobject]$result }
        $result.DriverMapping=$mapping.Value
        if ($mapping.Value -isnot [string] -or [string]::IsNullOrWhiteSpace($mapping.Value)) { $result.Status='unavailable_driver'; return [pscustomobject]$result }
        $result.DriverPath='HKLM:\SYSTEM\CurrentControlSet\Control\Class\'+$mapping.Value
        $driver=Get-ItemProperty -LiteralPath $result.DriverPath -ErrorAction Stop
        $property=$driver.PSObject.Properties['HardwareInformation.qwMemorySize']
        if ($null -eq $property) { $result.Status='missing'; return [pscustomobject]$result }
        $stage='decode'
        $value=$property.Value; $result.RawValue=$value
        if ($null -eq $value) { $result.Status='unavailable'; return [pscustomobject]$result }
        $result.RawType=$value.GetType().FullName
        if ($value -is [byte[]]) {
            $result.RawValue=@($value)
            if ($value.Length -ne 8) { $result.Status='invalid_length'; return [pscustomobject]$result }
            $number=[BitConverter]::ToUInt64($value,0)
        } elseif ($value -is [int64] -or $value -is [uint64]) { $number=$value }
        else { $result.Status='invalid_type'; return [pscustomobject]$result }
        if ($number -lt 0) { $result.Status='invalid_value'; return [pscustomobject]$result }
        $culture=[Globalization.CultureInfo]::InvariantCulture
        $result.Status='available'; $result.DecodedType=$number.GetType().FullName
        $result.BytesDecimal=$number.ToString($culture)
        $stage='difference'
        Add-Type -AssemblyName System.Numerics -ErrorAction Stop
        $d=[Numerics.BigInteger]::Parse($DxgiCapacity.ToString($culture),$culture)
        $r=[Numerics.BigInteger]::Parse($result.BytesDecimal,$culture)
        $result.DifferenceBytes=[Numerics.BigInteger]::Subtract($d,$r).ToString($culture)
        $result.DifferenceStatus='available'
    } catch {
        if ($stage -eq 'query') { $result.Status=$(if($_.CategoryInfo.Category -eq 'ObjectNotFound'){'missing_key'}else{'query_failed'}) }
        elseif ($stage -eq 'decode') { $result.Status='diagnostic_failed' }
        else { $result.DifferenceStatus='diagnostic_failed' }
        $result.Error=$_.Exception.Message
    }
    return [pscustomobject]$result
}
function Get-ReadOnlyContractAdapter {
    $controllers = @(Get-CimInstance Win32_VideoController -ErrorAction Stop)
    if ($controllers.Count -ne 1 -or $controllers[0].Name -notmatch 'RX\s*6800\s*XT') { throw 'Exactly one intended CIM RX 6800 XT device is required.' }
    $pattern = '^PCI\\VEN_([0-9A-F]{4})&DEV_([0-9A-F]{4})&SUBSYS_([0-9A-F]{8})&REV_([0-9A-F]{2})\\[^\\]+$'
    if ($controllers[0].PNPDeviceID -notmatch $pattern) { throw 'CIM PCI vendor/device/subsystem/revision identity is unavailable.' }
    $pci = @($Matches[1],$Matches[2],$Matches[3],$Matches[4] | ForEach-Object {[Convert]::ToUInt32($_,16)})
    if ($pci[0] -ne 0x1002) { throw 'Intended RX 6800 XT does not have the expected AMD vendor identity.' }
    $scan = Read-AssociationDxgi
    if ($null -eq $scan -or $scan.Status -ne 'ok') { throw 'DXGI enumeration failed or is incomplete; adapter uniqueness cannot be established.' }
    $all = @($scan.Adapters | ForEach-Object {$_})
    foreach ($item in $all) {
        if ($item.Status -ne 'ok' -or [string]::IsNullOrWhiteSpace($item.Description) -or
            $item.CounterKey -notmatch '^luid_0x[0-9A-F]{8}_0x[0-9A-F]{8}$') { throw 'DXGI descriptor/identity is missing or failed.' }
        foreach ($field in @('Vendor','Device','Subsystem','Revision','Flags')) {
            $number = Get-AssociationInteger $item.$field ('DXGI '+$field)
            if ($number -gt [uint32]::MaxValue) { throw ('DXGI '+$field+' is outside its native unsigned 32-bit range.') }
        }
    }
    $matching = @($all | Where-Object {
        ($_.Flags -band 2) -eq 0 -and [string]::Equals($_.Description.Trim(),$controllers[0].Name.Trim(),[StringComparison]::OrdinalIgnoreCase) -and
        $_.Vendor -eq $pci[0] -and $_.Device -eq $pci[1] -and $_.Subsystem -eq $pci[2] -and $_.Revision -eq $pci[3]
    })
    if ($matching.Count -ne 1) { throw 'Exactly one hardware DXGI descriptor matching CIM name and all PCI identifiers is required.' }
    $chosen = $matching[0]
    if (@($all | Where-Object {[string]::Equals($_.CounterKey,$chosen.CounterKey,[StringComparison]::OrdinalIgnoreCase)}).Count -ne 1) { throw 'The intended hardware LUID is duplicated across DXGI descriptors.' }
    $dxgiCapacity = Get-AssociationInteger $chosen.DedicatedBytes 'DXGI capacity'
    if ($dxgiCapacity -le 0) { throw 'DXGI dedicated-video capacity is unavailable; no fallback.' }
    $registry=Get-RegistryCapacityDiagnostic $controllers[0].PNPDeviceID $dxgiCapacity
    $adapter = [pscustomobject]@{Name=$chosen.Description;CounterKey=$chosen.CounterKey;DedicatedBytes=$dxgiCapacity
        CapacitySource='DXGI_ADAPTER_DESC1.DedicatedVideoMemory';RegistryCapacity=$registry
        Vendor=$chosen.Vendor;Device=$chosen.Device;Subsystem=$chosen.Subsystem;Revision=$chosen.Revision;Flags=$chosen.Flags
        PNPDeviceID=$controllers[0].PNPDeviceID;RegistryDriverPath=$registry.DriverPath;Association='CIM descriptor/PCI/DXGI LUID/exact WDDM phys_0'}
    $null = Get-AssociatedUsage $adapter @(Get-CimInstance Win32_PerfRawData_GPUPerformanceCounters_GPUAdapterMemory -ErrorAction Stop)
    return $adapter
}
function Get-ContractResources($Adapter, [string]$RunRoot, $OwnedProcess = $null) {
    $os = Get-CimInstance Win32_OperatingSystem
    $drive = New-Object IO.DriveInfo ([IO.Path]::GetPathRoot($RunRoot))
    $used = Get-AssociatedUsage $Adapter @(Get-CimInstance Win32_PerfRawData_GPUPerformanceCounters_GPUAdapterMemory -ErrorAction Stop)
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
        gpu_free = [long]$Adapter.DedicatedBytes - $used
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
