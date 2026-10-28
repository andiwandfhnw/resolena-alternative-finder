#Requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedManifestSha256,
    [Parameter(Mandatory = $true)][string]$Output,
    [Parameter(Mandatory = $true)][string]$NativeOutput,
    [switch]$OwnerPreflightAuthorized
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$GraniteReport = $null
$GraniteReportDirectory = $null

function Write-GraniteFile([string]$Path, [string]$Text) {
    $GraniteBytes = [Text.UTF8Encoding]::new($false).GetBytes($Text)
    $GraniteStream = [IO.FileStream]::new($Path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
    try { $GraniteStream.Write($GraniteBytes, 0, $GraniteBytes.Length); $GraniteStream.Flush($true) }
    finally { $GraniteStream.Dispose() }
}

function Read-GraniteVersion([string]$Path, [string]$Label) {
    $GraniteStdout = Join-Path $GraniteReportDirectory ($Label + '.version.stdout.log')
    $GraniteStderr = Join-Path $GraniteReportDirectory ($Label + '.version.stderr.log')
    $GraniteProcess = Start-Process -FilePath $Path -ArgumentList @('--version') -NoNewWindow -Wait -PassThru -RedirectStandardOutput $GraniteStdout -RedirectStandardError $GraniteStderr
    try {
        $GraniteExit = $GraniteProcess.ExitCode
        $GraniteText = [string](Get-Content -Raw -LiteralPath $GraniteStdout)
        $GraniteErrorText = [string](Get-Content -Raw -LiteralPath $GraniteStderr)
        if ($null -eq $GraniteExit -or $GraniteExit -ne 0 -or -not $GraniteText.Trim()) { throw ('Version query failed: ' + $Label) }
        return [pscustomobject]@{ path = $Path; arguments = @('--version'); exit_code = $GraniteExit; output = $GraniteText; stderr = $GraniteErrorText
            sha256 = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
    } finally { $GraniteProcess.Dispose() }
}

try {
    if (-not $OwnerPreflightAuthorized) { throw 'Separate owner authorization for Windows preflight is required; not executed.' }
    if ($env:OS -ne 'Windows_NT' -or -not [Environment]::Is64BitProcess) { throw 'Existing Windows x64 PowerShell is required.' }
    $GranitePackage = 'C:\Users\AndiWand\Downloads\granite-native-handoff-v3'
    $GraniteNativeRoot = 'C:\Resolena\gn1-20261025'
    $GraniteDownloads = 'C:\Users\AndiWand\Downloads'
    if ([IO.Path]::GetFullPath($PSScriptRoot).TrimEnd('\') -ne $GranitePackage) { throw 'Exact fresh package destination is required.' }
    $GraniteReportDirectory = [IO.Path]::GetFullPath($Output).TrimEnd('\')
    $GraniteNativeOutput = [IO.Path]::GetFullPath($NativeOutput).TrimEnd('\')
    if ((Split-Path -Parent $GraniteReportDirectory) -ne $GraniteDownloads -or
        (Split-Path -Leaf $GraniteReportDirectory) -notmatch '^granite-native-v3-preflight-[0-9a-f-]{36}$' -or
        (Split-Path -Parent $GraniteNativeOutput) -ne $GraniteDownloads -or
        (Split-Path -Leaf $GraniteNativeOutput) -notmatch '^granite-native-v3-run-[0-9a-f-]{36}$' -or
        $GraniteReportDirectory -eq $GraniteNativeOutput) { throw 'Separate fresh preflight/native evidence destinations are required.' }
    foreach ($GraniteFresh in @($GraniteReportDirectory, $GraniteNativeOutput, $GraniteNativeRoot)) {
        if (Test-Path -LiteralPath $GraniteFresh) { throw ('Destination already exists; preserve it and stop: ' + $GraniteFresh) }
    }
    $null = New-Item -ItemType Directory -Path $GraniteReportDirectory -ErrorAction Stop
    $GraniteReport = [ordered]@{
        version = 'uc001-granite-native-handoff-v3'; scope = 'preflight_only'
        started_utc = [DateTimeOffset]::UtcNow.ToString('o'); ended_utc = $null; preflight_passed = $false
        windows_execution = $true; execution_authorized = $false; configuration_inactive = $false
        resource_fit_established = $false; native_api_invoked = $false; acquisition_or_build = $false
        gpu_model_inference = $false; ownership_or_binding_diagnostic_rerun = $false
        package = $GranitePackage; expected_manifest_sha256 = $ExpectedManifestSha256
        native_root = $GraniteNativeRoot; native_output = $GraniteNativeOutput; preflight_output = $GraniteReportDirectory
        python = $null; package_validation = $null; tools = @(); activation = $null; sdk_files = @(); resources = $null
        worker_environment_validation_required = $true; worker_environment_validation_passed = $false; worker_module_path = $null
        supervision_entry = 'Pending actual controller private-Job/readback/sampler/watchdog checks before first resume; no diagnostic rerun.'
        failure_reason = $null
    }
    $GraniteManifestPath = Join-Path $GranitePackage 'manifest.json'
    if ((Get-FileHash -LiteralPath $GraniteManifestPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedManifestSha256) { throw 'External manifest SHA-256 differs.' }
    $GraniteManifest = Get-Content -Raw -LiteralPath $GraniteManifestPath | ConvertFrom-Json
    if ($GraniteManifest.version -ne 'uc001-granite-native-handoff-v3' -or
        $GraniteManifest.execution_authorized -ne $false -or
        $GraniteManifest.scope -ne 'pinned_runtime_source_and_model_free_build_only') { throw 'Inactive native handoff scope differs.' }
    $GraniteNames = @($GraniteManifest.files.PSObject.Properties.Name)
    if (-not $GraniteNames.Count -or @($GraniteNames | Where-Object { $_ -notmatch '^[A-Za-z0-9][A-Za-z0-9_.-]*$' }).Count) { throw 'Unsafe or empty package inventory.' }
    $GraniteActual = @(Get-ChildItem -LiteralPath $GranitePackage -Force | ForEach-Object { $_.Name })
    if (@(Compare-Object @($GraniteNames + 'manifest.json') $GraniteActual).Count) { throw 'Missing or unexpected package entry.' }
    foreach ($GraniteName in $GraniteNames) {
        $GranitePath = Join-Path $GranitePackage $GraniteName
        if (-not (Test-Path -LiteralPath $GranitePath -PathType Leaf) -or
            (Get-FileHash -LiteralPath $GranitePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $GraniteManifest.files.$GraniteName) { throw ('Package file differs: ' + $GraniteName) }
    }
    $GraniteConfig = Get-Content -Raw -LiteralPath (Join-Path $GranitePackage 'native-config.inactive.json') | ConvertFrom-Json
    if ($GraniteConfig.execution_authorized -ne $false) { throw 'Execution configuration must remain inactive.' }
    $GraniteReport.configuration_inactive = $true
    $GranitePython = 'C:\Users\AndiWand\Downloads\granite-python-3.12.11-20250702\env\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $GranitePython -PathType Leaf)) { throw 'Approved separate Granite Python is absent.' }
    $GraniteValidationText = & $GranitePython -I -B (Join-Path $GranitePackage 'verify_config.py') --package-root $GranitePackage --expected-manifest-sha256 $ExpectedManifestSha256 --check-environment
    $GraniteValidationExit = $LASTEXITCODE
    Write-GraniteFile (Join-Path $GraniteReportDirectory 'package-validation.json') (($GraniteValidationText -join [Environment]::NewLine) + [Environment]::NewLine)
    if ($GraniteValidationExit -ne 0) { throw 'Packaged configuration/worker environment verification failed; preserve package-validation.json and stop.' }
    $GraniteValidation = ($GraniteValidationText -join [Environment]::NewLine) | ConvertFrom-Json
    $GranitePythonInfo = $GraniteValidation.runtime
    if ($GranitePythonInfo.python_version -ne '3.12.11' -or $GranitePythonInfo.pointer_bits -ne 64 -or
        $GranitePythonInfo.platform -ne 'win32' -or $GranitePythonInfo.executable -ne $GranitePython) { throw 'Exact approved Windows Python 3.12.11 x64 environment is required.' }
    $GraniteReport.python = $GranitePythonInfo
    if ($GraniteValidation.configuration_inactive -ne $true -or $GraniteValidation.bound_prior_bytes -ne 0 -or
        $GraniteValidation.worker_environment_validation_required -ne $true -or
        $GraniteValidation.worker_environment_validation_passed -ne $true -or
        $GraniteValidation.worker_module_path -ne (Join-Path $GranitePackage 'worker.py') -or
        $GraniteValidation.native_api_invoked -ne $false -or $GraniteValidation.resource_fit_established -ne $false -or
        @($GraniteValidation.forbidden_attempts).Count) { throw 'Configuration/worker environment verification scope/result differs.' }
    $GraniteReport.package_validation = $GraniteValidation
    $GraniteReport.worker_environment_validation_passed = $true
    $GraniteReport.worker_module_path = $GraniteValidation.worker_module_path

    $GraniteVs = 'C:\Program Files\Microsoft Visual Studio\2022\Community'
    $GraniteGit = 'C:\Program Files\Git\cmd\git.exe'
    $GraniteCmake = Join-Path $GraniteVs 'Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
    $GraniteNinja = Join-Path $GraniteVs 'Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe'
    $GraniteCl = Join-Path $GraniteVs 'VC\Tools\MSVC\14.43.34808\bin\Hostx64\x64\cl.exe'
    $GraniteSdk = 'C:\VulkanSDK\1.4.357.0'
    foreach ($GraniteTool in @($GraniteGit, $GraniteCmake, $GraniteNinja, $GraniteCl, (Join-Path $GraniteVs 'VC\Auxiliary\Build\vcvarsall.bat'))) {
        if (-not (Test-Path -LiteralPath $GraniteTool -PathType Leaf)) { throw ('Existing pinned tool/activation path is absent: ' + $GraniteTool) }
    }
    if (([string]$env:VCToolsVersion).TrimEnd('\') -ne '14.43.34808' -or
        ([string]$env:WindowsSDKVersion).TrimEnd('\') -ne '10.0.22621.0' -or
        $env:VSCMD_ARG_HOST_ARCH -notin @('x64', 'amd64') -or $env:VSCMD_ARG_TGT_ARCH -notin @('x64', 'amd64') -or
        (Get-Command cl.exe -CommandType Application | Select-Object -First 1).Source -ne $GraniteCl) { throw 'Exact x64 MSVC/Windows SDK shell activation is not established.' }
    if (([string]$env:VULKAN_SDK).TrimEnd('\') -ne $GraniteSdk -or
        ([string]$env:VK_SDK_PATH).TrimEnd('\') -ne $GraniteSdk -or
        (Get-Command glslc.exe -CommandType Application | Select-Object -First 1).Source -ne (Join-Path $GraniteSdk 'Bin\glslc.exe')) { throw 'Pinned Vulkan SDK environment/path differs.' }
    foreach ($GraniteOverride in @('CC','CXX','CMAKE_TOOLCHAIN_FILE','CMAKE_PREFIX_PATH')) {
        if ([Environment]::GetEnvironmentVariable($GraniteOverride)) { throw ('Unreviewed toolchain override; stop without clearing: ' + $GraniteOverride) }
    }
    $GraniteReport.activation = [pscustomobject]@{
        VCToolsVersion = $env:VCToolsVersion; WindowsSDKVersion = $env:WindowsSDKVersion
        VSCMD_ARG_HOST_ARCH = $env:VSCMD_ARG_HOST_ARCH; VSCMD_ARG_TGT_ARCH = $env:VSCMD_ARG_TGT_ARCH
        VULKAN_SDK = $env:VULKAN_SDK; VK_SDK_PATH = $env:VK_SDK_PATH; compiler_path = $GraniteCl
        compiler_sha256 = (Get-FileHash -LiteralPath $GraniteCl -Algorithm SHA256).Hash.ToLowerInvariant()
        compiler_file_version = (Get-Item -LiteralPath $GraniteCl).VersionInfo.FileVersion
        ninja_path_policy = 'Absolute pinned executable; worker prepends its directory in the child environment. Parent-shell Ninja resolution is not required.'
    }
    $GraniteSdkFiles = @(
        (Join-Path $GraniteSdk 'Bin\glslc.exe'), (Join-Path $GraniteSdk 'Include\vulkan\vulkan.h'),
        (Join-Path $GraniteSdk 'Lib\vulkan-1.lib'), (Join-Path $GraniteSdk 'Include\spirv\unified1\spirv.hpp'),
        (Join-Path $GraniteSdk 'Lib\cmake\SPIRV-Headers\SPIRV-HeadersConfig.cmake'),
        (Join-Path $GraniteSdk 'Lib\cmake\SPIRV-Headers\SPIRV-HeadersConfigVersion.cmake')
    )
    $GraniteWinSdkRoot = Join-Path ([Environment]::GetEnvironmentVariable('ProgramFiles(x86)')) 'Windows Kits\10'
    $GraniteSdkFiles += @(
        (Join-Path $GraniteWinSdkRoot 'Include\10.0.22621.0\um\windows.h'), (Join-Path $GraniteWinSdkRoot 'Include\10.0.22621.0\ucrt\stdlib.h'),
        (Join-Path $GraniteWinSdkRoot 'Lib\10.0.22621.0\um\x64\kernel32.lib'), (Join-Path $GraniteWinSdkRoot 'Lib\10.0.22621.0\ucrt\x64\ucrt.lib'),
        (Join-Path $GraniteWinSdkRoot 'bin\10.0.22621.0\x64\rc.exe')
    )
    $GraniteReport.sdk_files = @(
        foreach ($GraniteFile in $GraniteSdkFiles) {
            if (-not (Test-Path -LiteralPath $GraniteFile -PathType Leaf)) { throw ('Required SDK component is absent: ' + $GraniteFile) }
            [pscustomobject]@{ path = $GraniteFile; sha256 = (Get-FileHash -LiteralPath $GraniteFile -Algorithm SHA256).Hash.ToLowerInvariant() }
        }
    )
    $GraniteSpirvConfig = Get-Content -Raw -LiteralPath (Join-Path $GraniteSdk 'Lib\cmake\SPIRV-Headers\SPIRV-HeadersConfig.cmake')
    if ($GraniteSpirvConfig -notmatch 'add_library\(\s*SPIRV-Headers::SPIRV-Headers\s+INTERFACE\s+IMPORTED\s*\)' -or
        $GraniteSpirvConfig -notmatch 'INTERFACE_INCLUDE_DIRECTORIES' -or
        $GraniteSpirvConfig -notmatch '\$\{_IMPORT_PREFIX\}/include') { throw 'Accepted direct SPIRV-Headers imported target/include definition is unavailable.' }
    $GraniteGitVersion = Read-GraniteVersion $GraniteGit 'git'
    $GraniteCmakeVersion = Read-GraniteVersion $GraniteCmake 'cmake'
    $GraniteNinjaVersion = Read-GraniteVersion $GraniteNinja 'ninja'
    $GraniteReport.tools = @($GraniteGitVersion, $GraniteCmakeVersion, $GraniteNinjaVersion)
    if (($GraniteGitVersion.output -split '\r?\n')[0].Trim() -ne 'git version 2.53.0.windows.2' -or
        ($GraniteCmakeVersion.output -split '\r?\n')[0].Trim() -ne 'cmake version 3.30.5-msvc23') { throw 'Existing pinned Git/CMake version differs.' }
    if (($GraniteNinjaVersion.output -split '\r?\n')[0].Trim() -notmatch '^\d+(\.\d+)+([-.][A-Za-z0-9.]+)?$') { throw 'Existing Ninja version is not identifiable; stop without inventing a pin.' }

    $GraniteDrive = [IO.DriveInfo]::new('C:\')
    if (-not $GraniteDrive.IsReady) { throw 'Native-root volume is unavailable.' }
    $GraniteAvailableDisk = [UInt64]$GraniteDrive.AvailableFreeSpace
    $GraniteOs = Get-CimInstance -ClassName Win32_OperatingSystem -Property FreePhysicalMemory
    if ($null -eq $GraniteOs.FreePhysicalMemory) { throw 'Available host physical memory is unknown.' }
    $GraniteHostFree = [UInt64]$GraniteOs.FreePhysicalMemory * [UInt64]1024
    $GraniteReport.resources = [pscustomobject]@{
        observed_utc = [DateTimeOffset]::UtcNow.ToString('o'); drive = 'C:\'
        caller_available_disk_bytes = $GraniteAvailableDisk; volume_free_disk_bytes = [UInt64]$GraniteDrive.TotalFreeSpace
        os_available_physical_memory_bytes = $GraniteHostFree; initial_disk_required_bytes = [UInt64]51539607552
        host_memory_observation_source = 'Local CIM Win32_OperatingSystem.FreePhysicalMemory (KiB converted to bytes); actual controller obtains its own fresh native observation.'
        stop_disk_below_bytes = [UInt64]8589934592; stop_host_below_bytes = [UInt64]4294967296
        resource_fit_established = $false
        authority = 'Point-in-time preflight only; actual controller must obtain fresh native observations and enforce ongoing limits.'
    }
    if ($GraniteAvailableDisk -lt [UInt64]51539607552 -or $GraniteHostFree -lt [UInt64]4294967296) { throw 'Fresh build-entry disk/host-memory requirement failed.' }
    if ((Test-Path -LiteralPath $GraniteNativeRoot) -or (Test-Path -LiteralPath $GraniteNativeOutput)) { throw 'Native source/output destination became occupied; stop without cleanup.' }
    $GraniteReport.preflight_passed = $true
} catch {
    if ($null -eq $GraniteReport) { Write-Error -Message $_ -ErrorAction Continue; exit 1 }
    $GraniteReport.failure_reason = $_.ToString()
} finally {
    if ($null -ne $GraniteReport) {
        $GraniteReport.ended_utc = [DateTimeOffset]::UtcNow.ToString('o')
        $GraniteReportText = $GraniteReport | ConvertTo-Json -Depth 12
        Write-GraniteFile (Join-Path $GraniteReportDirectory 'preflight-result.json') ($GraniteReportText + [Environment]::NewLine)
        Write-Output $GraniteReportText
    }
}
if (-not $GraniteReport.preflight_passed) { exit 1 }
exit 0
