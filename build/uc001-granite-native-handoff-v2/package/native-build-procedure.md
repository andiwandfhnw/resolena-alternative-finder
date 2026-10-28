# Granite native build preparation — 2026-10-25

## Owner SDK result and verifier correction

Owner reports LunarG Windows x64 SDK **1.4.357.0 installed and post-install
verification passed**, with glslc.exe, Vulkan header/x64 library, SPIR-V header,
SPIRV-HeadersConfig.cmake and ConfigVersion file present beneath
`C:\VulkanSDK\1.4.357.0`. Fresh-shell VULKAN_SDK/VK_SDK_PATH identify that root and
its Bin is on PATH. Codex did not execute those desktop checks or inspect the files.

The owner's read-only inspection found the expected imported target
`SPIRV-Headers::SPIRV-Headers` declared directly by
`add_library(SPIRV-Headers::SPIRV-Headers INTERFACE IMPORTED)`, with
INTERFACE_INCLUDE_DIRECTORIES referencing `${_IMPORT_PREFIX}/include`.
The earlier verifier's demand for a separate SPIRV-HeadersTargets.cmake was too
strict for this package: its failure was a verifier false negative, not an SDK
installation failure. Preserve that historical verifier/receipt unchanged; this
record appends the correction. No configure, compiler/glslc execution, GPU probe,
llama.cpp build, model download/startup or inference occurred in that owner report.

## Scope and prerequisites

**Preparation only; owner review and explicit execution authorization are still
required.** These commands acquire only the pinned runtime source and compile
llama-server without a model. They never execute the resulting server, even for
`--version`. No model URL, SDK installation, dependency installation or Python
environment change is included. Frozen model/runtime pins and all CMake flags stay
unchanged; native build records are separate from the frozen handoff.

Configure runs host compiler tests and **glslc shader-compilation probes**; build
compiles/runs host `vulkan-shaders-gen` and invokes glslc for offline shaders.
These are compilation operations, without GPU/model evaluation, as shown in the
[pinned Vulkan CMake source](https://raw.githubusercontent.com/ggml-org/llama.cpp/620d2225cc436ab0b001e3200e590e3b286ef9ab/ggml/src/ggml-vulkan/CMakeLists.txt).
This is a Windows MSVC/Vulkan procedure, not an LLVM or alternative-backend route.

The existing frozen requirement for approved acquisition/build time, process-tree
memory/output and cleanup supervision still applies. This procedure does not
implement or verify such a supervisor. If the owner cannot observe/enforce the
bounds below and stop the owned build tree, do not start acquisition/configure/build.
No ownership investigation or new supervisor is authorized by this preparation.

## 1. Windows Command Prompt — owner desktop, fresh ordinary cmd.exe

Exact activation target in the discovered VS2022 Community installation:
`C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat`.
The first command checks its presence; no desktop existence check occurred here.
[Microsoft documents](https://learn.microsoft.com/en-us/cpp/build/building-on-the-command-line?view=msvc-170)
the architecture, Windows SDK and full toolset-version arguments.

```bat
if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" (call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" amd64 10.0.22621.0 -vcvars_ver=14.43.34808 && powershell.exe -NoLogo -NoProfile) else (echo STOP: Existing Visual Studio activation file is missing.)
```

Continue only in the **child PowerShell opened by successful activation**. A batch
file called from an ordinary PowerShell cannot update that parent environment.
This route changes only the new cmd/child PowerShell environment; closing both
discards activation. No permanent PATH, registry or execution-policy change.

## 2. Activated Windows PowerShell — bind tools and reserve fresh directories

Run all remaining blocks in that same child shell, only after approval and resource
supervision are established. The short root below must not exist; it is outside
both the transferred Resolena worktree and old experiment/Python directories.

```powershell
$ErrorActionPreference = 'Stop'
$GraniteVs = 'C:\Program Files\Microsoft Visual Studio\2022\Community'
$GraniteGit = 'C:\Program Files\Git\cmd\git.exe'
$GraniteCmake = Join-Path $GraniteVs 'Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
$GraniteNinja = Join-Path $GraniteVs 'Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe'
$GraniteCl = Join-Path $GraniteVs 'VC\Tools\MSVC\14.43.34808\bin\Hostx64\x64\cl.exe'
$GraniteSdk = 'C:\VulkanSDK\1.4.357.0'
$GraniteRoot = 'C:\Resolena\gn1-20261025'
$GraniteRuntimeCommit = '620d2225cc436ab0b001e3200e590e3b286ef9ab'
foreach ($GraniteTool in @($GraniteGit, $GraniteCmake, $GraniteNinja, $GraniteCl)) {
    if (-not (Test-Path -LiteralPath $GraniteTool -PathType Leaf)) { throw "Required existing tool missing: $GraniteTool" }
}
if (([string]$env:VCToolsVersion).TrimEnd('\') -ne '14.43.34808' -or
    ([string]$env:WindowsSDKVersion).TrimEnd('\') -ne '10.0.22621.0' -or
    $env:VSCMD_ARG_HOST_ARCH -notin @('x64', 'amd64') -or $env:VSCMD_ARG_TGT_ARCH -notin @('x64', 'amd64') -or
    (Get-Command cl.exe -CommandType Application).Source -ne $GraniteCl) { throw 'Exact x64 MSVC/Windows SDK activation not established: stop.' }
if (([string]$env:VULKAN_SDK).TrimEnd('\') -ne $GraniteSdk -or
    ([string]$env:VK_SDK_PATH).TrimEnd('\') -ne $GraniteSdk -or
    (Get-Command glslc.exe -CommandType Application).Source -ne (Join-Path $GraniteSdk 'Bin\glslc.exe')) { throw 'Pinned Vulkan SDK environment differs: stop.' }
if (-not (Test-Path -LiteralPath (Join-Path $GraniteSdk 'Lib\cmake\SPIRV-Headers\SPIRV-HeadersConfig.cmake') -PathType Leaf)) { throw 'Owner-verified SPIRV-Headers CONFIG missing: stop.' }
foreach ($GraniteOverride in @('CC', 'CXX', 'CMAKE_TOOLCHAIN_FILE', 'CMAKE_PREFIX_PATH')) {
    if ([Environment]::GetEnvironmentVariable($GraniteOverride)) { throw "Unreviewed compiler/package selection override: $GraniteOverride. Stop without clearing it." }
}
if (Test-Path -LiteralPath $GraniteRoot) { throw 'Fresh native root required; preserve existing work.' }
$GraniteRepo = Join-Path $GraniteRoot 'source-repository'
$GraniteSourceZip = Join-Path $GraniteRoot 'llama-620d2225-source.zip'
$GraniteSource = Join-Path $GraniteRoot 'src'
$GraniteBuild = Join-Path $GraniteRoot 'build'
$GraniteEvidence = Join-Path $GraniteRoot 'evidence'
$null = New-Item -ItemType Directory -Path $GraniteEvidence -ErrorAction Stop
# Existing Ninja only; this PATH change is local to the activated child shell.
$env:PATH = (Split-Path -Parent $GraniteNinja) + ';' + $env:PATH
$env:CMAKE_BUILD_PARALLEL_LEVEL = '2'
$env:GIT_LFS_SKIP_SMUDGE = '1'
if ((Get-Command ninja.exe -CommandType Application).Source -ne $GraniteNinja) { throw 'Unexpected Ninja selection: stop.' }

function Invoke-GraniteNative([string]$FilePath, [string[]]$Arguments, [string]$Label) {
    $Started = [DateTime]::UtcNow.ToString('o')
    $Process = Start-Process -FilePath $FilePath -ArgumentList $Arguments -NoNewWindow -Wait -PassThru -RedirectStandardOutput (Join-Path $GraniteEvidence ($Label + '.stdout.log')) -RedirectStandardError (Join-Path $GraniteEvidence ($Label + '.stderr.log'))
    [pscustomobject]@{ command = $FilePath; arguments = $Arguments; started_utc = $Started; ended_utc = [DateTime]::UtcNow.ToString('o'); exit_code = $Process.ExitCode } |
        ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $GraniteEvidence ($Label + '.command.json')) -Encoding UTF8
    if ($Process.ExitCode -ne 0) { Get-Content -LiteralPath (Join-Path $GraniteEvidence ($Label + '.stderr.log')); throw "Native phase failed: $Label. Preserve all outputs; no retry/fix." }
}
Invoke-GraniteNative -FilePath $GraniteGit -Arguments @('--version') -Label 'git-version'
Invoke-GraniteNative -FilePath $GraniteCmake -Arguments @('--version') -Label 'cmake-version'
Invoke-GraniteNative -FilePath $GraniteNinja -Arguments @('--version') -Label 'ninja-version'
Get-FileHash -LiteralPath @($GraniteGit, $GraniteCmake, $GraniteNinja, $GraniteCl, (Join-Path $GraniteSdk 'Bin\glslc.exe'), (Join-Path $GraniteSdk 'Lib\cmake\SPIRV-Headers\SPIRV-HeadersConfig.cmake')) -Algorithm SHA256 |
    Select-Object Path, Hash | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $GraniteEvidence 'tool-hashes.json') -Encoding UTF8
[pscustomobject]@{ VCToolsVersion = $env:VCToolsVersion; WindowsSDKVersion = $env:WindowsSDKVersion; VULKAN_SDK = $env:VULKAN_SDK; cl = $GraniteCl; ninja = $GraniteNinja } |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $GraniteEvidence 'build-environment.json') -Encoding UTF8
```

The wrapper records each permitted native command and its output; it is not a
timeout/memory/cleanup supervisor. Do not run these commands again into a consumed
root. Ninja's actual version is captured here; no version or compatibility is
invented from its prior file presence.

## 3. Activated Windows PowerShell — pinned source acquisition/integrity

Only this new auxiliary source repository is mutated. No checkout, submodule/LFS
fetch, model endpoint, Resolena Git operation or dependency installer is involved.

```powershell
Invoke-GraniteNative -FilePath $GraniteGit -Arguments @('init', $GraniteRepo) -Label 'source-init'
Invoke-GraniteNative -FilePath $GraniteGit -Arguments @('-C', $GraniteRepo, 'remote', 'add', 'origin', 'https://github.com/ggml-org/llama.cpp.git') -Label 'source-origin'
Invoke-GraniteNative -FilePath $GraniteGit -Arguments @('-C', $GraniteRepo, 'fetch', '--depth=1', '--no-tags', '--recurse-submodules=no', 'origin', $GraniteRuntimeCommit) -Label 'source-fetch'
$GraniteFetchedCommit = & $GraniteGit -C $GraniteRepo rev-parse --verify 'FETCH_HEAD^{commit}'
if ($LASTEXITCODE -ne 0 -or $GraniteFetchedCommit.Trim() -ne $GraniteRuntimeCommit) { throw 'Fetched commit identity differs: stop.' }
Invoke-GraniteNative -FilePath $GraniteGit -Arguments @('-C', $GraniteRepo, 'fsck', '--full', '--strict', $GraniteRuntimeCommit) -Label 'source-fsck'
Invoke-GraniteNative -FilePath $GraniteGit -Arguments @('-C', $GraniteRepo, 'archive', '--format=zip', ('--output=' + $GraniteSourceZip), $GraniteRuntimeCommit) -Label 'source-archive'
$GraniteTree = & $GraniteGit -C $GraniteRepo rev-parse ($GraniteRuntimeCommit + '^{tree}')
if ($LASTEXITCODE -ne 0) { throw 'Source tree identity unavailable: stop.' }
$GraniteArchiveHash = Get-FileHash -LiteralPath $GraniteSourceZip -Algorithm SHA256
[pscustomobject]@{ version = 'v0.7.0'; commit = $GraniteFetchedCommit.Trim(); tree = $GraniteTree.Trim(); archive = $GraniteSourceZip; bytes = (Get-Item -LiteralPath $GraniteSourceZip).Length; sha256 = $GraniteArchiveHash.Hash.ToLowerInvariant() } |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $GraniteEvidence 'source-identity.json') -Encoding UTF8
Expand-Archive -LiteralPath $GraniteSourceZip -DestinationPath $GraniteSource -ErrorAction Stop
```

Git object validation and exact commit binding establish source identity; record
the locally produced ZIP digest separately. It is not a prepublished archive hash
and is unknown until owner execution. ZIP size is not a network-byte measurement.

## 4. Activated Windows PowerShell — exact frozen configure/build flags

```powershell
$GraniteCmakeFlags = @(
    '-DCMAKE_BUILD_TYPE=Release', '-DFETCHCONTENT_FULLY_DISCONNECTED=ON',
    '-DGGML_VULKAN=ON', '-DLLAMA_BUILD_SERVER=ON', '-DLLAMA_BUILD_TOOLS=ON',
    '-DLLAMA_BUILD_COMMON=ON', '-DLLAMA_BUILD_IS_DEV=OFF',
    ('-DLLAMA_BUILD_COMMIT=' + $GraniteRuntimeCommit), '-DLLAMA_BUILD_NUMBER=0',
    '-DLLAMA_BUILD_TESTS=OFF', '-DLLAMA_BUILD_EXAMPLES=OFF', '-DLLAMA_BUILD_APP=OFF',
    '-DLLAMA_BUILD_UI=OFF', '-DLLAMA_USE_PREBUILT_UI=OFF', '-DLLAMA_OPENSSL=OFF',
    '-DLLAMA_SUBPROCESS=OFF', '-DLLAMA_LLGUIDANCE=OFF'
)
Invoke-GraniteNative -FilePath $GraniteCmake -Arguments (@('-S', $GraniteSource, '-B', $GraniteBuild, '-G', 'Ninja') + $GraniteCmakeFlags) -Label 'configure'
$GraniteCache = @{}
foreach ($GraniteLine in Get-Content -LiteralPath (Join-Path $GraniteBuild 'CMakeCache.txt')) {
    if ($GraniteLine -match '^([^#/:][^:]*):[^=]+=(.*)$') { $GraniteCache[$Matches[1]] = $Matches[2] }
}
$GraniteExpectedPaths = @{
    CMAKE_C_COMPILER = $GraniteCl; CMAKE_CXX_COMPILER = $GraniteCl; CMAKE_MAKE_PROGRAM = $GraniteNinja
    Vulkan_GLSLC_EXECUTABLE = (Join-Path $GraniteSdk 'Bin\glslc.exe')
    'SPIRV-Headers_DIR' = (Join-Path $GraniteSdk 'Lib\cmake\SPIRV-Headers')
}
foreach ($GraniteKey in $GraniteExpectedPaths.Keys) {
    if (-not $GraniteCache[$GraniteKey] -or [IO.Path]::GetFullPath($GraniteCache[$GraniteKey]).TrimEnd('\') -ne [IO.Path]::GetFullPath($GraniteExpectedPaths[$GraniteKey]).TrimEnd('\')) { throw "Configured tool/package differs: $GraniteKey. Stop before build; no workaround." }
}
Invoke-GraniteNative -FilePath $GraniteCmake -Arguments @('--build', $GraniteBuild, '--config', 'Release', '--target', 'llama-server', '--parallel', '2') -Label 'build'
$GraniteServer = Join-Path $GraniteBuild 'bin\llama-server.exe'
if (-not (Test-Path -LiteralPath $GraniteServer -PathType Leaf)) { throw 'Expected server artifact missing: stop.' }
Get-ChildItem -LiteralPath (Join-Path $GraniteBuild 'bin') -File | ForEach-Object {
    [pscustomobject]@{ path = $_.FullName; bytes = $_.Length; sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant(); product_version = $_.VersionInfo.ProductVersion }
} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $GraniteEvidence 'built-artifacts.json') -Encoding UTF8
Get-FileHash -LiteralPath (Join-Path $GraniteBuild 'CMakeCache.txt'), (Join-Path $GraniteBuild 'build.ninja') -Algorithm SHA256 |
    Select-Object Path, Hash | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $GraniteEvidence 'build-metadata-hashes.json') -Encoding UTF8
Get-Content -LiteralPath (Join-Path $GraniteEvidence 'source-identity.json')
Get-Content -LiteralPath (Join-Path $GraniteEvidence 'built-artifacts.json')
```

The flags match [frozen config.json](../../scripts/uc001_granite_contract_v1/config.json).
LLAMA_BUILD_COMMIT/NUMBER explicitly label the Git-archive build; they do not prove
compiled-source identity independently. Retain the source repository/ZIP/tree,
logs/command records, CMakeCache.txt/build.ninja, generated build information and
licences/notices. Expected output is `build\bin\llama-server.exe` plus accompanying
DLLs (Windows defaults to shared libraries); retain/hash the entire fresh bin
directory rather than copying the EXE alone. No binary hash is known in advance.
Do not run the server, native schema inspector, tests, benchmarks or installer.

## Frozen operational bounds and stopping point

| Scope | Unchanged frozen bound |
|---|---|
| Acquisition | 30 minutes / 10 GiB total; existing combined model+source ceiling, not a new allowance; no model acquisition here |
| Configure + build | 45 minutes combined, including nested shader generation; generated build output at most 12 GiB |
| Build memory | Process-tree memory at most 24 GiB |
| Parallelism | Frozen outer `--parallel 2`; nested CMake hint also 2; this does not prove an aggregate two-process ceiling |
| Disk | At least 48 GiB free initially; stop below 8 GiB free |
| Host headroom | Stop below 4 GiB OS free memory |

No measured resource fit or enforcement is established here. Nested builds can
overlap; approved supervision must account for their combined tree/time/output.
Configure/build receive no extra budget per command or retry. All unrelated
startup/VRAM/inference limits remain untouched and are not exercised here.

Stop on missing/incorrect activation, tool/SDK selection, source identity/object
failure, unavailable supervision, resource/deadline breach, configure/build error,
unexpected download/dependency request or missing artifact. Preserve partial
outputs; do not install, fix, change flags, switch backend or retry. Stop after
returning source/build logs and metadata/hashes for owner review. No model/server
startup, GPU probe, native-converter run or interpreter suitability acceptance.

## Preparation evidence

Only documentation/source-metadata review and syntax/static/preservation checks
are permitted in Codespace. No activation, source acquisition, configure or build
was executed here. Three PowerShell blocks passed syntax-only parsing; the Command
Prompt activation block received static review only. All 17 configure parameters
match the frozen manifest/Release setting. Local links, fences and new whitespace
checks passed. All 832 previously protected files outside TASKS and all 78 original
Granite preparation/evidence files retain their fingerprints (overlapping counts
are not added). Prior task/Priority 5 history and Git HEAD/branch/index/existing
status entries are preserved. `git diff --check` exits 2 only for the historical
TASKS trailing space at line 2560. Only TASKS and this new procedure were written.
Original SDK/proposal receipts, frozen package/archive, Python environments, application
code, evidence, Priority 5 acceptance and closed Qwen result remain unchanged.
PHASE: 3 / STATUS: in-progress; Priorities 3/4 partial; Priority 6/Phase 4 pending.
