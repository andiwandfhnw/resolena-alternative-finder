#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT' -or -not [Environment]::Is64BitProcess) { throw 'Use existing 64-bit Windows PowerShell; no discovery was performed.' }

$Findings = [Collections.Generic.List[object]]::new()
$Notes = [Collections.Generic.List[string]]::new()
$Locations = [Collections.Generic.List[string]]::new()
$Active = @{}

function In-Scope([string]$Path) {
    return $Path -and $Path -notmatch '(?i)(^|[\\/])(ResolenaExperiments|experiments|uc001-validator-env)([\\/]|$)'
}

function Has-File([string]$Path) {
    return (In-Scope $Path) -and (Test-Path -LiteralPath $Path -PathType Leaf)
}

function Read-ProductKey([Microsoft.Win32.RegistryHive]$Hive, [Microsoft.Win32.RegistryView]$View, [string]$Name, [string[]]$Values) {
    $Locations.Add("Registry $Hive/$View/$Name (named values only)")
    $BaseKey = $null; $ProductKey = $null
    try {
        $BaseKey = [Microsoft.Win32.RegistryKey]::OpenBaseKey($Hive, $View)
        $ProductKey = $BaseKey.OpenSubKey($Name, $false)
        if ($ProductKey) {
            $Data = @{}
            foreach ($Value in $Values) { $Data[$Value] = $ProductKey.GetValue($Value) }
            return [pscustomobject]$Data
        }
    } catch { $Notes.Add("Cannot read $Hive/$View/${Name}: $($_.Exception.Message)") }
    finally { if ($ProductKey) { $ProductKey.Dispose() }; if ($BaseKey) { $BaseKey.Dispose() } }
}

function Add-Tool([string]$Tool, [string]$Path, [string]$Source, [string]$ComponentVersion = '') {
    if (-not (Has-File $Path)) { return }
    $File = Get-Item -LiteralPath $Path
    $Existing = @($Findings | Where-Object { $_.tool -eq $Tool -and $_.path -eq $File.FullName })
    if ($Existing.Count) {
        if ($ComponentVersion) { $Existing[0].component_version = $ComponentVersion; $Existing[0].discovery = 'installed and identifiable' }
        if ($Existing[0].source -notlike "*$Source*") { $Existing[0].source += '; ' + $Source }
        return
    }
    $Version = $File.VersionInfo.ProductVersion
    if (-not $Version) { $Version = $File.VersionInfo.FileVersion }
    $ActiveHere = [bool]($Active[$Tool] -and $Active[$Tool] -eq $File.FullName)
    $Findings.Add([pscustomobject]@{ tool = $Tool; path = $File.FullName; source = $Source
        file_version = $Version; component_version = $ComponentVersion
        discovery = $(if ($Version -or $ComponentVersion) { 'installed and identifiable' } else { 'present; version unverified' })
        shell = $(if ($ActiveHere) { 'resolved in current shell' } else { 'installed but not active in current shell' })
        compatibility = 'unverified; no configure, compilation or execution of this tool' })
}

function Version-Directories([string]$Root) {
    $Locations.Add($Root + '\<direct version directory>')
    if ((In-Scope $Root) -and (Test-Path -LiteralPath $Root -PathType Container)) {
        @(Get-ChildItem -LiteralPath $Root -Directory -ErrorAction Stop | Where-Object { $_.Name -match '^\d+(\.\d+)*$' -and -not ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) })
    }
}

function Query-VS([string]$Utility, [string]$Requires = '') {
    $Info = [Diagnostics.ProcessStartInfo]::new()
    $Info.FileName = $Utility
    $Info.Arguments = '-all -prerelease -products * -format json -utf8'
    if ($Requires) { $Info.Arguments += ' -requires ' + $Requires }
    $Info.UseShellExecute = $false; $Info.CreateNoWindow = $true
    $Info.RedirectStandardOutput = $true; $Info.RedirectStandardError = $true
    $Info.StandardOutputEncoding = [Text.Encoding]::UTF8
    $Info.StandardErrorEncoding = [Text.Encoding]::UTF8
    $Process = [Diagnostics.Process]::new(); $Process.StartInfo = $Info
    try {
        $null = $Process.Start()
        $OutputTask = $Process.StandardOutput.ReadToEndAsync()
        $ErrorTask = $Process.StandardError.ReadToEndAsync()
        if (-not $Process.WaitForExit(10000)) { $Process.Kill(); throw 'Owned vswhere query timed out; no retry.' }
        $Text = $OutputTask.GetAwaiter().GetResult()
        $Diagnostic = $ErrorTask.GetAwaiter().GetResult()
        if ($Process.ExitCode -ne 0 -or $Diagnostic) { throw "vswhere exit $($Process.ExitCode): $Diagnostic" }
        @($Text | ConvertFrom-Json)
    } catch { $Notes.Add("vswhere query '$Requires' unavailable: $($_.Exception.Message)") }
    finally { $Process.Dispose() }
}

foreach ($Pair in @(@('Git', 'git.exe'), @('CMake', 'cmake.exe'), @('Ninja', 'ninja.exe'), @('MSVC x64', 'cl.exe'), @('Vulkan compiler', 'glslc.exe'))) {
    $Command = Get-Command $Pair[1] -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($Command -and (In-Scope $Command.Source)) {
        $Active[$Pair[0]] = $Command.Source
        if ($Pair[0] -ne 'MSVC x64' -or $Command.Source -match '\\bin\\Hostx64\\x64\\cl\.exe$') {
            Add-Tool $Pair[0] $Command.Source 'current shell command resolution'
        } else { $Notes.Add("Shell cl path found, but Hostx64/x64 target not established: $($Command.Source)") }
    }
}
$ProgramRoots = @([Environment]::GetEnvironmentVariable('ProgramFiles'), [Environment]::GetEnvironmentVariable('ProgramFiles(x86)')) | Where-Object { $_ } | Select-Object -Unique
foreach ($Root in $ProgramRoots) {
    $Locations.Add($Root + '\Git\cmd\git.exe'); Add-Tool 'Git' (Join-Path $Root 'Git\cmd\git.exe') 'standard installation'
    $Locations.Add($Root + '\CMake\bin\cmake.exe'); Add-Tool 'CMake' (Join-Path $Root 'CMake\bin\cmake.exe') 'standard installation'
}
foreach ($Hive in @([Microsoft.Win32.RegistryHive]::LocalMachine, [Microsoft.Win32.RegistryHive]::CurrentUser)) {
    foreach ($View in @([Microsoft.Win32.RegistryView]::Registry64, [Microsoft.Win32.RegistryView]::Registry32)) {
        $Git = Read-ProductKey $Hive $View 'SOFTWARE\GitForWindows' @('InstallPath', 'CurrentVersion')
        if ($Git -and (In-Scope $Git.InstallPath)) { Add-Tool 'Git' (Join-Path $Git.InstallPath 'cmd\git.exe') 'GitForWindows product metadata' $Git.CurrentVersion }
    }
}

$VsRoots = [Collections.Generic.List[string]]::new()
$VsInstances = @(); $VcInstances = @(); $CMakeInstances = @()
$VsWhere = Join-Path ([Environment]::GetEnvironmentVariable('ProgramFiles(x86)')) 'Microsoft Visual Studio\Installer\vswhere.exe'
$Locations.Add($VsWhere)
if (Has-File $VsWhere) {
    $VsInstances = @(Query-VS $VsWhere)
    $VcInstances = @(Query-VS $VsWhere 'Microsoft.VisualStudio.Component.VC.Tools.x86.x64')
    $CMakeInstances = @(Query-VS $VsWhere 'Microsoft.VisualStudio.Component.VC.CMake.Project')
    foreach ($Instance in $VsInstances) { if (In-Scope $Instance.installationPath) { $VsRoots.Add($Instance.installationPath) } }
} else { $Notes.Add('Existing vswhere not found at the documented installer path; none downloaded.') }
foreach ($Root in $ProgramRoots) {
    $Standard = Join-Path $Root 'Microsoft Visual Studio'
    foreach ($Version in @(Version-Directories $Standard)) {
        foreach ($Edition in @('Community', 'Professional', 'Enterprise', 'BuildTools')) {
            $Candidate = Join-Path $Version.FullName $Edition
            if (Test-Path -LiteralPath $Candidate -PathType Container) { $VsRoots.Add($Candidate) }
        }
    }
}
if (In-Scope $env:VSINSTALLDIR) { $VsRoots.Add($env:VSINSTALLDIR) }
foreach ($Root in @($VsRoots | Select-Object -Unique)) {
    Add-Tool 'CMake' (Join-Path $Root 'Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe') 'Visual Studio bundled CMake'
    Add-Tool 'Ninja' (Join-Path $Root 'Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe') 'Visual Studio bundled Ninja'
    $DefaultFile = Join-Path $Root 'VC\Auxiliary\Build\Microsoft.VCToolsVersion.default.txt'
    foreach ($Version in @(Version-Directories (Join-Path $Root 'VC\Tools\MSVC'))) {
        Add-Tool 'MSVC x64' (Join-Path $Version.FullName 'bin\Hostx64\x64\cl.exe') 'MSVC Hostx64/x64 payload' $Version.Name
    }
    if (Has-File $DefaultFile) { $Notes.Add("MSVC default toolset at ${Root}: $((Get-Content -LiteralPath $DefaultFile -Raw).Trim())") }
}

$SdkRoots = [Collections.Generic.List[string]]::new()
foreach ($View in @([Microsoft.Win32.RegistryView]::Registry64, [Microsoft.Win32.RegistryView]::Registry32)) {
    $Kits = Read-ProductKey LocalMachine $View 'SOFTWARE\Microsoft\Windows Kits\Installed Roots' @('KitsRoot10')
    if ($Kits -and (In-Scope $Kits.KitsRoot10)) { $SdkRoots.Add($Kits.KitsRoot10) }
}
if (In-Scope $env:WindowsSdkDir) { $SdkRoots.Add($env:WindowsSdkDir) }
foreach ($Root in $ProgramRoots) { $SdkRoots.Add((Join-Path $Root 'Windows Kits\10')) }
foreach ($Root in @($SdkRoots | Select-Object -Unique)) {
    foreach ($Version in @(Version-Directories (Join-Path $Root 'Include'))) {
        $Parts = [ordered]@{ windows_h = (Has-File (Join-Path $Version.FullName 'um\Windows.h'))
            ucrt_stdio_h = (Has-File (Join-Path $Version.FullName 'ucrt\stdio.h'))
            kernel32_x64 = (Has-File (Join-Path $Root "Lib\$($Version.Name)\um\x64\kernel32.lib"))
            ucrt_x64 = (Has-File (Join-Path $Root "Lib\$($Version.Name)\ucrt\x64\ucrt.lib"))
            rc_x64 = (Has-File (Join-Path $Root "bin\$($Version.Name)\x64\rc.exe")) }
        $Findings.Add([pscustomobject]@{ tool = 'Windows SDK'; path = $Root; component_version = $Version.Name
            version_basis = 'SDK directory, not independently verified servicing/QFE version'; components = $Parts
            discovery = $(if ($Parts.windows_h -or $Parts.ucrt_stdio_h) { 'installed SDK payload identifiable; component completeness reported separately' } else { 'location present; SDK installation/version unverified' })
            shell = $(if ($env:WindowsSdkDir -and $env:WindowsSdkDir.TrimEnd('\') -eq $Root.TrimEnd('\')) { 'SDK root set in current shell; build environment unverified' } else { 'installed but not active in current shell' })
            compatibility = 'unverified; no compilation' })
    }
}

$VulkanRoots = [Collections.Generic.List[string]]::new()
foreach ($Scope in @('Process', 'User', 'Machine')) {
    foreach ($Name in @('VULKAN_SDK', 'VK_SDK_PATH')) {
        $Value = [Environment]::GetEnvironmentVariable($Name, $Scope)
        if (In-Scope $Value) { $VulkanRoots.Add($Value) }
    }
}
$StandardVulkan = Join-Path ([IO.Path]::GetPathRoot($env:SystemRoot)) 'VulkanSDK'
foreach ($Version in @(Version-Directories $StandardVulkan)) { $VulkanRoots.Add($Version.FullName) }
foreach ($Root in @($VulkanRoots | Select-Object -Unique)) {
    if (-not (Test-Path -LiteralPath $Root -PathType Container)) { continue }
    $Parts = [ordered]@{ glslc = (Has-File (Join-Path $Root 'Bin\glslc.exe'))
        vulkan_h = (Has-File (Join-Path $Root 'Include\vulkan\vulkan.h'))
        vulkan_x64_lib = (Has-File (Join-Path $Root 'Lib\vulkan-1.lib'))
        spirv_hpp = (Has-File (Join-Path $Root 'Include\spirv\unified1\spirv.hpp'))
        spirv_headers_config_lib = (Has-File (Join-Path $Root 'Lib\cmake\SPIRV-Headers\SPIRV-HeadersConfig.cmake'))
        spirv_headers_config_share = (Has-File (Join-Path $Root 'share\cmake\SPIRV-Headers\SPIRV-HeadersConfig.cmake')) }
    $Findings.Add([pscustomobject]@{ tool = 'Vulkan SDK'; path = $Root; component_version = (Split-Path -Leaf $Root.TrimEnd('\'))
        version_basis = 'directory label only; actual compiler compatibility unverified'; components = $Parts
        discovery = $(if ($Parts.glslc -or $Parts.vulkan_h -or $Parts.vulkan_x64_lib) { 'installed SDK payload identifiable; component completeness reported separately' } else { 'location present; SDK installation/version unverified' })
        shell = $(if ($env:VULKAN_SDK -and $env:VULKAN_SDK.TrimEnd('\') -eq $Root.TrimEnd('\')) { 'VULKAN_SDK set in current shell' } else { 'installed but not active in current shell' })
        compatibility = 'unverified; no compiler or GPU invoked' })
    Add-Tool 'Vulkan compiler' (Join-Path $Root 'Bin\glslc.exe') 'Vulkan SDK compiler payload'
}

$Summary = foreach ($Tool in @('Git', 'CMake', 'Ninja', 'MSVC x64', 'Windows SDK', 'Vulkan SDK', 'Vulkan compiler')) {
    $Found = @($Findings | Where-Object { $_.tool -eq $Tool })
    [pscustomobject]@{ tool = $Tool; locations_found = $Found.Count
        status = $(if ($Found.Count) { 'present; see identification, shell and compatibility fields' } else { 'not found by these bounded checks; machine-wide absence not established' }) }
}
[pscustomobject]@{ version = 'uc001-granite-tool-discovery-v1'; observed_utc = [DateTime]::UtcNow.ToString('o')
    runtime_commit = '620d2225cc436ab0b001e3200e590e3b286ef9ab'; route = 'Windows x64/Vulkan source build; unchanged'
    summary = @($Summary); findings = @($Findings.ToArray()); bounded_locations = @($Locations.ToArray()); notes = @($Notes.ToArray())
    visual_studio = @($VsInstances | Select-Object installationPath, installationVersion, isComplete, isLaunchable)
    vc_component_instances = @($VcInstances | Select-Object installationPath, installationVersion)
    cmake_component_instances = @($CMakeInstances | Select-Object installationPath, installationVersion)
    shell_environment = @{ VSCMD_ARG_TGT_ARCH = $env:VSCMD_ARG_TGT_ARCH; VCToolsVersion = $env:VCToolsVersion
        WindowsSdkDir = $env:WindowsSdkDir; WindowsSDKVersion = $env:WindowsSDKVersion; VULKAN_SDK = $env:VULKAN_SDK }
    compatibility = 'unverified; presence/version metadata is not a successful configure/build'
    changes_made = @(); build_or_compiler_invoked = $false; gpu_probed = $false; model_started = $false
} | ConvertTo-Json -Depth 8
