# Granite Vulkan SDK resolution — 2026-10-25

## Owner-executed discovery result

Owner reports **2026-10-25T18:10:46.8540278Z**; not a Codex desktop run:

| Present, inactive in ordinary PowerShell | Owner-reported version/path |
|---|---|
| Git | 2.53.0.windows.2; `C:\Program Files\Git\cmd\git.exe` |
| CMake | 3.30.5-msvc23; `C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe` |
| Ninja | Version unverified; `C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe` |
| MSVC x64 | Toolset 14.43.34808; `C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.43.34808\bin\Hostx64\x64\cl.exe` |
| Windows SDK | 10.0.22621.0; windows.h/UCRT/kernel32 x64/UCRT x64/rc x64 present |

Vulkan SDK and glslc were **not found by the bounded checks**, not proved absent
machine-wide. No VSCMD/Vulkan SDK variables in that shell; no compiler/build, GPU
probe or model startup. Earlier discovery files/results remain unchanged.

## One proposed SDK pin

**LunarG Vulkan SDK 1.4.357.0, Windows x64**, publisher **LunarG, Inc.**, released
2026-07-29. Exact installer: `vulkansdk-windows-X64-1.4.357.0.exe`.
[Official fixed download](https://sdk.lunarg.com/sdk/download/1.4.357.0/windows/vulkansdk-windows-X64-1.4.357.0.exe).
[Current official hash metadata](https://vulkan.lunarg.com/sdk/sha/1.4.357.0/windows/vulkan_sdk.exe.json):
**`81f474711e9042f4cd22b31b2f7a8870db2e428b21586fb43dd80150be97310d`**.
HTTP HEAD returned 200 / **287971024 bytes**; no installer body was read.

This pin follows the selected runtime's own [Windows Vulkan recipe](https://raw.githubusercontent.com/ggml-org/llama.cpp/620d2225cc436ab0b001e3200e590e3b286ef9ab/.github/workflows/build-vulkan.yml#L178),
which installs this official x64 SDK and enables GGML_VULKAN. The required
[Vulkan/glslc and SPIRV-Headers CONFIG lookups](https://raw.githubusercontent.com/ggml-org/llama.cpp/620d2225cc436ab0b001e3200e590e3b286ef9ab/ggml/src/ggml-vulkan/CMakeLists.txt#L8)
have no supplemental package override there. This is **upstream recipe evidence**,
not an observed CI pass. That recipe uses LLVM; the frozen Resolena route remains
**MSVC Windows x64/Vulkan**. Its actual build compatibility remains unverified.

The [exact SDK component metadata](https://vulkan.lunarg.com/sdk/config/1.4.357.0/windows/config.json)
includes Vulkan-Headers/Loader/SPIRV-Headers at tag `vulkan-sdk-1.4.357.0`, and
shaderc at `ef2c68b4871a3c399a0808321b51379847a54673` (glslc). Headers/libs/glslc
are the SDK development payload. **SPIRV-Headers CONFIG inclusion is inferred from
the pinned upstream recipe's unchanged required lookup**, not verified from an
inspected installer file list. Require the actual config and target files below
after installation; missing/unexpected layout means stop, without a build or fix.
The general [LunarG CMake packaging issue](https://vulkan.lunarg.com/issue/view/6598781b5df1125b58afbb3c)
does not establish absence of this specific package and is not treated as proof.

Licence basis: the [versioned SDK licence page](https://vulkan.lunarg.com/doc/view/1.4.357.0/windows/licenses.html)
retains individual component open-source licences, mostly MIT/Apache-2.0; there is
no umbrella SDK relicense. Preserve component notices and review terms before
acceptance. No published signer thumbprint is asserted and no Authenticode
signature has been verified here; the proposed owner command checks it locally.

## Proposed installation — owner approval required first

Use the [documented core-only installation](https://vulkan.lunarg.com/doc/view/1.4.357.0/windows/getting_started.html#user-content-unattended-installation).
Approval must cover the exact download, component licences, elevated core install,
SDK registry/layer registration and system SDK/PATH updates. No optional packages,
driver update, Python change, developer-shell activation or build is proposed.
The SDK does not install GPU drivers. Existing installations/files are preserved.

**Windows PowerShell — owner desktop, elevated, only after approval and licence review:**

```powershell
$ErrorActionPreference = 'Stop'
$GraniteSdkInstaller = 'C:\Users\AndiWand\Downloads\vulkansdk-windows-X64-1.4.357.0.exe'
$GraniteSdkRoot = 'C:\VulkanSDK\1.4.357.0'
if ((Test-Path -LiteralPath $GraniteSdkInstaller) -or (Test-Path -LiteralPath $GraniteSdkRoot)) { throw 'Preserve existing files/installation and stop.' }
Invoke-WebRequest -UseBasicParsing -Uri 'https://sdk.lunarg.com/sdk/download/1.4.357.0/windows/vulkansdk-windows-X64-1.4.357.0.exe' -OutFile $GraniteSdkInstaller -TimeoutSec 600
if ((Get-Item -LiteralPath $GraniteSdkInstaller).Length -ne 287971024 -or
    (Get-FileHash -LiteralPath $GraniteSdkInstaller -Algorithm SHA256).Hash.ToLowerInvariant() -ne '81f474711e9042f4cd22b31b2f7a8870db2e428b21586fb43dd80150be97310d') { throw 'Installer size/hash differs: stop.' }
$GraniteSdkSignature = Get-AuthenticodeSignature -LiteralPath $GraniteSdkInstaller
$GraniteSdkSignature | Select-Object Status, @{Name='Signer';Expression={$_.SignerCertificate.Subject}}, @{Name='Thumbprint';Expression={$_.SignerCertificate.Thumbprint}}
if ($GraniteSdkSignature.Status -ne 'Valid' -or $GraniteSdkSignature.SignerCertificate.Subject -notmatch 'LunarG') { throw 'Publisher signature not established: stop and report.' }
$GraniteSdkInstall = Start-Process -FilePath $GraniteSdkInstaller -ArgumentList @('--root', $GraniteSdkRoot, '--accept-licenses', '--default-answer', '--confirm-command', 'install') -Wait -PassThru
if ($GraniteSdkInstall.ExitCode -ne 0) { throw 'Installation failed or needs attention: preserve output and stop; no retry.' }
```

Default path is **C:\VulkanSDK\1.4.357.0**. Normal installation sets system
**VULKAN_SDK** and **VK_SDK_PATH** to it and prepends its **Bin** directory to PATH.
Reopen existing shells/IDE hosts to inherit those values; no reboot is prescribed
by this proposal. If the installer requests one, stop/report before proceeding.
MSVC activation and Ninja's version remain separate pending matters.

## Read-only post-install verification — owner desktop

In a fresh ordinary PowerShell, after a separately approved installation only:

```powershell
$GraniteSdkRoot = 'C:\VulkanSDK\1.4.357.0'
$GraniteSdkFiles = @('Bin\glslc.exe', 'Include\vulkan\vulkan.h', 'Lib\vulkan-1.lib', 'Include\spirv\unified1\spirv.hpp')
$GraniteSdkPresence = @($GraniteSdkFiles | ForEach-Object { [pscustomobject]@{ Path = (Join-Path $GraniteSdkRoot $_); Present = (Test-Path -LiteralPath (Join-Path $GraniteSdkRoot $_) -PathType Leaf) } })
$GraniteSdkConfigs = @(@('Lib\cmake\SPIRV-Headers\SPIRV-HeadersConfig.cmake', 'share\cmake\SPIRV-Headers\SPIRV-HeadersConfig.cmake') | ForEach-Object { Join-Path $GraniteSdkRoot $_ } | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf })
$GraniteSdkTargets = @($GraniteSdkConfigs | ForEach-Object { [pscustomobject]@{ Config = $_; TargetsPresent = (Test-Path -LiteralPath (Join-Path (Split-Path -Parent $_) 'SPIRV-HeadersTargets.cmake') -PathType Leaf) } })
$GraniteSdkPresence | Format-Table -AutoSize
$GraniteSdkTargets | Format-Table -AutoSize
$GraniteSdkEnvironment = [pscustomobject]@{ VULKAN_SDK = $env:VULKAN_SDK; VK_SDK_PATH = $env:VK_SDK_PATH; BinOnPath = @($env:PATH -split ';' | Where-Object { $_.TrimEnd('\') -eq (Join-Path $GraniteSdkRoot 'Bin') }).Count -gt 0 }
$GraniteSdkEnvironment
if (@($GraniteSdkPresence | Where-Object { -not $_.Present }).Count -or $GraniteSdkConfigs.Count -eq 0 -or @($GraniteSdkTargets | Where-Object { -not $_.TargetsPresent }).Count) { throw 'Required SDK payload/config not established in the checked layout: stop and report; no workaround.' }
if (([string]$env:VULKAN_SDK).TrimEnd('\') -ne $GraniteSdkRoot -or ([string]$env:VK_SDK_PATH).TrimEnd('\') -ne $GraniteSdkRoot -or -not $GraniteSdkEnvironment.BinOnPath) { throw 'Fresh-shell environment does not identify the pinned SDK: stop and report; no automatic environment edits.' }
```

This reads files/environment only: no glslc invocation, CMake configure, SDK demos,
vulkaninfo/vkcube, GPU probe or model. A pass establishes checked payload presence,
not successful CMake resolution, compilation, driver fit or Granite suitability.
Do not copy configs, add a replacement dependency, set SPIRV-Headers_DIR or alter
the frozen build to obtain a pass. Stop after returning installation/verification
output for review. No installation is currently authorized by this proposal.

## Preparation and preservation

Only documentation/official metadata reads and installer HEAD occurred here;
no binary, runtime source tree or model was acquired. API-host HTTP 403 was
resolved by reading the same official hash metadata on vulkan.lunarg.com.
The route is proposed, not installed or build-qualified. Both proposed PowerShell
blocks passed syntax-only parsing after correcting the parser wrapper's quoting;
neither block executed. Documentation links, pin consistency, fences and new
whitespace checks passed. All 832 previously protected files outside TASKS and
all 77 original Granite preparation/evidence files retain their fingerprints
(overlapping counts are not added). Prior task history and Priority 5 acceptance
are preserved; read-only Git checks confirm unchanged HEAD, branch, index and
existing file-status entries. `git diff --check` exits 2 only for the preserved
historical TASKS trailing space at line 2522. Only TASKS and this new readiness
receipt were written. Original pins, Python environments, freeze/archive,
receipts, uncommitted work and closed Qwen result are preserved.
PHASE: 3 / STATUS: in-progress. Priorities 3/4 partial; Priority 6/Phase 4 pending.
