# Consolidated inactive Granite native handoff — 2026-10-27

**ALL FUTURE WINDOWS EXECUTION: NOT AUTHORIZED / NOT EXECUTED.**
The owner accepts controller
9c5f3bab58fd3f2d20d345f5093ca2ac80b1e9149da74c1555fcf9b450e92fc1
and closes the count/owned-row finding for its demonstrated injected default-path
schedules. Advisor reconstruction and targeted reproductions are distinct from
Codex's preserved 92-pass receipt; the advisor did not rerun the full suite.
The 79-pass receipt and both CLOSED Windows diagnostics remain unchanged.
Their Windows results do not verify the changed default loop.

No controller/worker/backend/proxy behavior, admission rule, pin, flag or numeric
limit changes here. This is a complete inactive proposal for owner review;
Windows entry conditions, resource fit and acquisition/build readiness remain
unestablished. No execution is authorized by this document.

## Exact transfer and inactive draft

[uc001-granite-native-handoff-v2.zip](uc001-granite-native-handoff-v2.zip):
**67,856 bytes / 15 flat files**, destination
**C:\Users\AndiWand\Downloads\granite-native-handoff-v2**.

| Item | SHA-256 |
|---|---|
| ZIP | 0396e052f7753578c9e4c94764bc08a21e6e4f2cd67ffdfba9e8f97d7bfcdfe3 |
| Manifest | a63238267cc8e881d0609c3cffcdcac303d399454cef64ca0874fcbafd577556 |
| Inactive config | 4ce5c85efcc43903282f530b815689022f085f0d498d86cad7bbad40ae3ac6ab |
| Detached complete inventory | b9de15f4ef3001176ad68315cb4facb0b9069d3344fb36d035d0b323f087396e |
| Accepted proxy | a7c62f83356636bea839633382bb62a3e53bcce466caea7b32226cece1e7bb1d |
| Frozen configuration | c4610156c24e95cdf1abab658cfde1c18be568940c7cb952c5a673833c620cf4 |
| Accepted prior receipt | 56a85b9ded9d6c4bf504462e11d551b59e016fcd1c77d8c5102b93ff7df7475a |

[Complete inventory](transfer-inventory.json) supplies literal size, SHA and
destination for every ZIP entry, including manifest.json. It is detached to avoid
a circular self-hash; [package-result.json](package-result.json) binds it to the ZIP.
Payload:

- Four native helpers only: controller.py, worker.py, windows_job.py, standins.py.
- Immutable inputs: proxy.py, frozen-config.json, prior-budget.json,
  prior-budget.json.sha256, owner-statement.txt.
- Preparation: native-config.inactive.json, verify_config.py,
  Preflight-GraniteNative.ps1, README.md, native-build-procedure.md, manifest.json.

[native-config.inactive.json](package/native-config.inactive.json) has
execution_authorized=false and the exact current four-helper map. No diagnostic
helper enters that contract. Current execution bindings are separate from the
unchanged prior receipt's historical preparation/helper hashes. The frozen file
is a byte-identical copy, not a refreeze. The fixed native root is
**C:\Resolena\gn1-20261025** and must remain absent until the controller creates it.
Previous worktree/archive, Python environments, packages and results stay intact.
The accepted prior charge is explicitly owner-attested **0 bytes**, accounting
complete, rather than independently measured history; initial byte capacity is
10,737,418,240 before the first real acquisition.

## Ordered future owner procedure

Every step below is **NOT AUTHORIZED / NOT EXECUTED**. Separate owner execution
approval is required. Preflight-only approval never authorizes acquisition/build.
Failure means preserve all output and stop without fixes, retries or deletion.

### 1. Integrity and fresh extraction only

Save the exact ZIP to Downloads, then use Windows PowerShell:

~~~powershell
& {
    $ErrorActionPreference = 'Stop'
    $GraniteArchive = 'C:\Users\AndiWand\Downloads\uc001-granite-native-handoff-v2.zip'
    $GraniteDestination = 'C:\Users\AndiWand\Downloads\granite-native-handoff-v2'
    if ((Get-Item -LiteralPath $GraniteArchive).Length -ne 67856 -or
        (Get-FileHash -LiteralPath $GraniteArchive -Algorithm SHA256).Hash.ToLowerInvariant() -ne '0396e052f7753578c9e4c94764bc08a21e6e4f2cd67ffdfba9e8f97d7bfcdfe3') {
        throw 'Native handoff archive differs: preserve it and stop.'
    }
    if (Test-Path -LiteralPath $GraniteDestination) { throw 'Destination exists: preserve it and stop.' }
    Expand-Archive -LiteralPath $GraniteArchive -DestinationPath $GraniteDestination -ErrorAction Stop
    if ((Get-FileHash -LiteralPath (Join-Path $GraniteDestination 'manifest.json') -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'a63238267cc8e881d0609c3cffcdcac303d399454cef64ca0874fcbafd577556') {
        throw 'Extracted manifest differs: preserve extraction and stop.'
    }
}
~~~

### 2. Existing shell-local activation only

In a fresh ordinary **Windows Command Prompt**, reuse the accepted activation:

~~~bat
if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" (call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" amd64 10.0.22621.0 -vcvars_ver=14.43.34808 && powershell.exe -NoLogo -NoProfile) else (echo STOP: Existing Visual Studio activation file is missing.)
~~~

Continue in the successfully activated **child PowerShell**. Closing these shells
discards activation; no permanent PATH, registry or execution-policy change.

### 3. Preflight only

Define these variables in that activated PowerShell; retain the session for step 4.
The preflight creates only its report directory. Neither source root nor future
native output directory is created.

~~~powershell
$ErrorActionPreference = 'Stop'
$GranitePackage = 'C:\Users\AndiWand\Downloads\granite-native-handoff-v2'
$GranitePython = 'C:\Users\AndiWand\Downloads\granite-python-3.12.11-20250702\env\Scripts\python.exe'
$GraniteManifestHash = 'a63238267cc8e881d0609c3cffcdcac303d399454cef64ca0874fcbafd577556'
$GranitePreflight = Join-Path 'C:\Users\AndiWand\Downloads' ('granite-native-preflight-' + [Guid]::NewGuid().ToString())
$GraniteNativeOutput = Join-Path 'C:\Users\AndiWand\Downloads' ('granite-native-run-' + [Guid]::NewGuid().ToString())
& powershell.exe -NoLogo -NoProfile -NonInteractive -File (Join-Path $GranitePackage 'Preflight-GraniteNative.ps1') -ExpectedManifestSha256 $GraniteManifestHash -Output $GranitePreflight -NativeOutput $GraniteNativeOutput -OwnerPreflightAuthorized
if ($LASTEXITCODE -ne 0) { throw 'Preflight failed: preserve output and stop without fixes/retry.' }
$GranitePreflightResult = Get-Content -Raw -LiteralPath (Join-Path $GranitePreflight 'preflight-result.json') | ConvertFrom-Json
if ($GranitePreflightResult.preflight_passed -ne $true -or
    $GranitePreflightResult.configuration_inactive -ne $true -or
    $GranitePreflightResult.native_output -ne $GraniteNativeOutput) { throw 'Preflight proof/destination differs: stop.' }
~~~

Fresh Windows observations required:

- Package/schema/hash proof and approved **Windows Python 3.12.11 x64**.
- Exact existing Git **2.53.0.windows.2**, VS-bundled CMake **3.30.5-msvc23**,
  absolute Ninja path and identifiable version. Record Ninja's version without
  inventing a new pin; the worker prepares its child PATH.
- MSVC **14.43.34808 Hostx64/x64**, Windows SDK **10.0.22621.0**, exact compiler
  path and no CC/CXX/CMAKE_TOOLCHAIN_FILE/CMAKE_PREFIX_PATH overrides.
- Vulkan SDK **C:\VulkanSDK\1.4.357.0**, matching VULKAN_SDK/VK_SDK_PATH/glslc
  path, headers/libs and direct SPIRV-Headers CONFIG target/include definition.
  A separate Targets.cmake is not required.
- Caller-available C: disk >=48 GiB and labelled local CIM available-physical-memory
  observation >=4 GiB; fixed native root and separate native output remain absent.

Only existing Git/CMake/Ninja --version queries run. No cl/glslc invocation, proxy,
Job, GPU probe, source acquisition or build. Reports include actual paths/versions/
hashes/environment/resources. Preflight is point-in-time evidence, not resource
fit. Actual controller private-Job readback, fresh native sampler/watchdog health,
resource gates and atomic suspended assignment remain mandatory before first
worker resume. Do not rerun either closed diagnostic.

### 4. Proposed pinned source acquisition and model-free compilation

Only after separate explicit owner approval of this exact scope/package and fresh
successful preflight in the activated session. Keep the packaged inactive draft
unchanged. A future approved active file is a separate retained copy:

~~~powershell
$GraniteOwnerApprovalReference = '<REQUIRED_SEPARATE_OWNER_SOURCE_BUILD_APPROVAL>'
if ([string]::IsNullOrWhiteSpace($GraniteOwnerApprovalReference) -or $GraniteOwnerApprovalReference.StartsWith('<')) {
    throw 'Explicit separate source/build approval is required: stop.'
}
if ((Test-Path -LiteralPath 'C:\Resolena\gn1-20261025') -or
    (Test-Path -LiteralPath $GraniteNativeOutput)) { throw 'Fresh native/evidence paths required: stop.' }
$GraniteDraft = Join-Path $GranitePackage 'native-config.inactive.json'
if ((Get-FileHash -LiteralPath $GraniteDraft -Algorithm SHA256).Hash.ToLowerInvariant() -ne '4ce5c85efcc43903282f530b815689022f085f0d498d86cad7bbad40ae3ac6ab') { throw 'Inactive draft differs: stop.' }
$GraniteApproved = Get-Content -Raw -LiteralPath $GraniteDraft | ConvertFrom-Json
if ($GraniteApproved.execution_authorized -ne $false) { throw 'Expected reviewed inactive draft: stop.' }
$GraniteApproved.execution_authorized = $true
$GraniteApproved.owner = $GraniteOwnerApprovalReference
$GraniteActiveConfig = $GraniteNativeOutput + '.approved.json'
function Write-GraniteApprovalFile([string]$Path, [string]$Text) {
    $GraniteBytes = [Text.UTF8Encoding]::new($false).GetBytes($Text)
    $GraniteStream = [IO.FileStream]::new($Path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
    try { $GraniteStream.Write($GraniteBytes, 0, $GraniteBytes.Length); $GraniteStream.Flush($true) }
    finally { $GraniteStream.Dispose() }
}
Write-GraniteApprovalFile $GraniteActiveConfig (($GraniteApproved | ConvertTo-Json -Depth 10) + [Environment]::NewLine)
$GraniteActiveHash = (Get-FileHash -LiteralPath $GraniteActiveConfig -Algorithm SHA256).Hash.ToLowerInvariant()
$GraniteApprovalEvidence = [ordered]@{
    approval_reference = $GraniteOwnerApprovalReference; recorded_utc = [DateTimeOffset]::UtcNow.ToString('o')
    manifest_sha256 = $GraniteManifestHash; inactive_config_sha256 = '4ce5c85efcc43903282f530b815689022f085f0d498d86cad7bbad40ae3ac6ab'
    active_config = $GraniteActiveConfig; active_config_sha256 = $GraniteActiveHash
    preflight_output = $GranitePreflight; native_output = $GraniteNativeOutput
    scope = 'source_acquisition_and_model_free_native_build_only'
}
Write-GraniteApprovalFile ($GraniteNativeOutput + '.approval.json') (($GraniteApprovalEvidence | ConvertTo-Json -Depth 5) + [Environment]::NewLine)
& $GranitePython -I -B (Join-Path $GranitePackage 'controller.py') native --config $GraniteActiveConfig --output $GraniteNativeOutput
$GraniteNativeExit = $LASTEXITCODE
if ($GraniteNativeExit -ne 0) { throw 'Native acquisition/build failed: preserve partial output and stop without fixes/retry.' }
$GraniteNativeResult = Get-Content -Raw -LiteralPath (Join-Path $GraniteNativeOutput 'result.json') | ConvertFrom-Json
if ($GraniteNativeResult.status -ne 'controlled_phases_passed' -or
    $GraniteNativeResult.scope -ne 'source_acquisition_and_model_free_native_build_only') { throw 'Native terminal proof differs: preserve evidence and stop.' }
~~~

The controller alone creates the native root and owns both phases. It fetches
https://github.com/ggml-org/llama.cpp.git at
**620d2225cc436ab0b001e3200e590e3b286ef9ab / v0.7.0** through the accepted isolated,
command-local metered proxy. Commit/object fsck, tree, archive/hash and safe
extraction remain required. Configure/build use all 17 frozen flags, outer
**--parallel 2** and target **llama-server only**.

Compiler tests, glslc shader-compilation probes and host vulkan-shaders-gen
build/run are part of the proposed compilation scope; no GPU/model evaluation.
Never execute the built server, even for --version, or run native converters/
inspectors, tests, benchmarks or installers.

**Do not also run native-build-procedure.md's old manual root-creation or
unmetered fetch/build blocks.** That byte-identical document is provenance.
Its activation/pins/flags are reused through this consolidated supervised route.
The diagnostic no-network bootstrap is not included or used for real acquisition.

## Unchanged bounds and shared timing/accounting

| Quantity | Exact bound |
|---|---|
| Acquisition | 1800 seconds from one real initialization start, through source acquisition/validation; no reset/retry |
| Model + source downloads | 10,737,418,240 cumulative bytes including prior; conservative upstream charges include overhead, never an estimated subtraction |
| Configure + build | 2700 seconds combined, no new budget per command |
| Job memory | 25,769,803,776 aggregate committed virtual-memory bytes, **not RSS** |
| Generated build output | 12,884,901,888 bytes |
| Disk | Initial caller-available >=51,539,607,552; stop below 8,589,934,592 bytes |
| Host memory | Stop below 4,294,967,296 OS available physical bytes |
| Outer parallelism | 2; not a two-total-process limit |

**Sequencing consequence before approval:** later model acquisition shares the
same continuous original UTC window. Build/review does not pause or renew it.
A build allowed up to 45 minutes can outlast the 30-minute acquisition window.
Source/build success therefore does not promise later model acquisition remains
possible. If T0+1800 seconds has passed, or remaining bytes are insufficient, later
model acquisition must stop. No pause/reset or sequencing amendment is inferred.
There is no conflict preventing this source-only/build proposal; a guaranteed
model-after-build sequence cannot be promised. A changed budget/sequence needs a
separate owner decision.

Preserve the accepted zero receipt unchanged. After real source acquisition,
derive any later cumulative prior charge from its **actual validated terminal
proxy ledger**, including all charged overhead and its prior-receipt hash. Bind
that evidence and the unchanged original T0 in a separately reviewed carry-forward
receipt. Never erase partial/failed charges or reuse historical zero as a retry
allowance. Remaining bytes are ceiling minus actual cumulative charges; remaining
time is at most 1800 minus current age of original T0. No real source ledger, T0 or
post-source remaining balance exists yet. Diagnostic zero ledgers/timestamps are not a real acquisition
start. This package provides no later model-download route or HF proxy extension.

## Stop conditions and retained evidence

Missing/wrong tools, SDK, environment, integrity/accounting, source/object identity,
supervision, native identity/event/cleanup proof, stale/unavailable resources,
limit breach, unexpected dependency/network request, configure/build failure or
missing artifact mean **stop without fixes/retry**. Preserve partial directories
and console output. No installation, policy change, cleanup/reset, flags/backend
substitution or allowance renewal is approved.

Retain the complete preflight directory (preflight-result.json,
package-validation.json and Git/CMake/Ninja version stdout/stderr), any later
approved config/approval record, and the entire native output directory:
result.json, controller.jsonl, worker-config.json, acquisition/build journals and
stdout/stderr. Retain the entire native root: source-repository, source ZIP, src,
evidence and build. Evidence includes tool hashes/versions/environment, exact fetch
specification, proxy logs/ledger, source commit/tree/archive identity and build
manifests/hashes. Keep CMakeCache.txt, build.ninja, licences/notices and the whole
build/bin directory including llama-server.exe and companion DLLs. No source ZIP
or compiled-binary hash is known before execution; record actual outputs.

## Exact proposed future approval scope

**Recommendation for review only; execution_authorized remains false.**
Separate explicit approval would cover one fresh ordered attempt:

1. Verify/extract this exact package, shell-local existing activation and the
   stated preflight-only observations/version queries, preserving output.
2. After successful fresh entry checks, create the separate approved config copy
   and invoke the controller once for pinned metered runtime-source acquisition,
   source validation/archive and model-free llama-server configure/compilation,
   including required host compiler/glslc/shader-generator work.
3. Permit only the owned Git/proxy source route and existing Job/resource/identity
   monitoring/cleanup under unchanged limits; stop on failure without fixes/retry.
4. Exclude model weights, GPU/VRAM probes, server execution/startup, inference,
   converters, closed diagnostics, installation, persistent policy changes and Git
   delivery. Acknowledge that build/review can exhaust the shared acquisition
   window; no later-model allowance is reserved or renewed.

This is not that approval. A successful future preflight is not workload resource
fit or acquisition/build/model acceptance. The changed default loop remains
Windows-unverified.

## Offline verification and stopping point

[Packaged config verification](offline-config-result.json) passed once in isolated
Codespace Python. It checks the exact inactive file/current four helpers. Actual
controller validation rejects inactive execution; a path-mapped synthetic-authorized
dictionary validates hashes/limits/prior in memory only. Stale controller hashes,
diagnostic helper additions and wrong prior SHA are rejected. Process/socket/DLL
operations are audit-blocked. No active configuration is persisted.

[Static checks](package-static-checks.json) confirm every ZIP/inventory byte/hash/
destination and all 17 frozen flags. Python and Linux PowerShell parser-only
checks execute no Windows body. No diagnostic, 79/92-test suite, application/model
test, NativeApi, network, acquisition/build or hardware probe runs. Test totals
are not accumulated.

Only TASKS and new handoff artifacts change. Source, frozen bytes, Python
environments, accepted prior, historical bindings and previous evidence remain
unchanged. Priority 5 acceptance, closed Qwen result, inactive real drafts,
unconfigured app.main and reference permissions remain. Priorities 3/4 partial;
Priority 6/Phase 4 pending. PHASE: 3 / STATUS: in-progress. Stop for owner review.
