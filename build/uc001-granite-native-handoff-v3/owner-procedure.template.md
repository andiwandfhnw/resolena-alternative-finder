## Ordered future owner procedure — NOT AUTHORIZED / NOT EXECUTED

The placeholder hashes/size in the archived README must be taken from the
separately approved v3 receipt. The companion outer README renders their exact
values after packaging. This avoids a circular archive self-hash. Every Windows
step below remains unexecuted and requires separate owner approval; preparation
does not renew the consumed v2 attempt.

### 1. Future integrity verification and fresh extraction only

Only after explicit v3 transfer/preflight approval, save the exact v3 ZIP to
Downloads and replace the approval placeholder. Never reuse the v2 destination.

~~~powershell
& {
    $ErrorActionPreference = 'Stop'
    $GranitePreflightApproval = '<REQUIRED_SEPARATE_OWNER_V3_PREFLIGHT_APPROVAL>'
    if ($GranitePreflightApproval.StartsWith('<') -or [string]::IsNullOrWhiteSpace($GranitePreflightApproval)) {
        throw 'V3 Windows transfer/preflight is NOT AUTHORIZED: stop.'
    }
    $GraniteArchive = 'C:\Users\AndiWand\Downloads\uc001-granite-native-handoff-v3.zip'
    $GraniteDestination = 'C:\Users\AndiWand\Downloads\granite-native-handoff-v3'
    $GraniteArchiveHash = '__ZIP_SHA256__'
    $GraniteManifestHash = '__MANIFEST_SHA256__'
    $GraniteExpectedSize = '__ZIP_BYTES__'
    if ($GraniteArchiveHash -notmatch '^[0-9a-f]{64}$' -or
        $GraniteManifestHash -notmatch '^[0-9a-f]{64}$' -or $GraniteExpectedSize -notmatch '^\d+$') {
        throw 'Exact externally approved v3 hashes/size are required: stop.'
    }
    if ((Get-Item -LiteralPath $GraniteArchive).Length -ne [Int64]$GraniteExpectedSize -or
        (Get-FileHash -LiteralPath $GraniteArchive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $GraniteArchiveHash) {
        throw 'V3 archive differs: preserve it and stop.'
    }
    if (Test-Path -LiteralPath $GraniteDestination) { throw 'V3 destination exists: preserve it and stop.' }
    Expand-Archive -LiteralPath $GraniteArchive -DestinationPath $GraniteDestination -ErrorAction Stop
    if ((Get-FileHash -LiteralPath (Join-Path $GraniteDestination 'manifest.json') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $GraniteManifestHash) {
        throw 'V3 manifest differs: preserve extraction and stop.'
    }
}
~~~

### 2. Future shell-local activation only

After the same explicit approval, in a fresh ordinary Windows Command Prompt,
reuse the existing approved toolchain activation. No installation, elevation,
permanent PATH/registry/policy change, compiler or shader invocation:

~~~bat
if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" (call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" amd64 10.0.22621.0 -vcvars_ver=14.43.34808 && powershell.exe -NoLogo -NoProfile) else (echo STOP: Existing Visual Studio activation file is missing.)
~~~

Continue only in the successfully activated child PowerShell. If activation or
required entry conditions fail, retain evidence and stop without fixes/retry.

### 3. Future v3 preflight and actual worker environment entry check only

Replace the approval placeholder only after separate approval. The new preflight
invokes verify_config.py --check-environment, which calls the actual hash-bound
corrected worker.validate_environment(os.environ). It must report that this check
was required and passed, using the exact packaged worker path. No native phase,
Job, proxy, acquisition T0 or source/build root is created. The report directory
alone is created; the distinct native-output path remains prospective.

~~~powershell
& {
    $ErrorActionPreference = 'Stop'
    $GranitePreflightApproval = '<REQUIRED_SEPARATE_OWNER_V3_PREFLIGHT_APPROVAL>'
    if ($GranitePreflightApproval.StartsWith('<') -or [string]::IsNullOrWhiteSpace($GranitePreflightApproval)) {
        throw 'V3 Windows preflight is NOT AUTHORIZED: stop.'
    }
    $GranitePackage = 'C:\Users\AndiWand\Downloads\granite-native-handoff-v3'
    $GraniteManifestHash = '__MANIFEST_SHA256__'
    if ($GraniteManifestHash -notmatch '^[0-9a-f]{64}$') { throw 'Externally approved v3 manifest hash required: stop.' }
    $GranitePreflight = Join-Path 'C:\Users\AndiWand\Downloads' ('granite-native-v3-preflight-' + [Guid]::NewGuid().ToString())
    $GraniteNativeOutput = Join-Path 'C:\Users\AndiWand\Downloads' ('granite-native-v3-run-' + [Guid]::NewGuid().ToString())
    & powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File (Join-Path $GranitePackage 'Preflight-GraniteNative.ps1') -ExpectedManifestSha256 $GraniteManifestHash -Output $GranitePreflight -NativeOutput $GraniteNativeOutput -OwnerPreflightAuthorized
    if ($LASTEXITCODE -ne 0) { throw 'V3 preflight failed: preserve all output and stop without fixes/retry.' }
    $GraniteProof = Get-Content -Raw -LiteralPath (Join-Path $GranitePreflight 'preflight-result.json') | ConvertFrom-Json
    if ($GraniteProof.preflight_passed -ne $true -or $GraniteProof.configuration_inactive -ne $true -or
        $GraniteProof.worker_environment_validation_required -ne $true -or
        $GraniteProof.worker_environment_validation_passed -ne $true -or
        $GraniteProof.worker_module_path -ne (Join-Path $GranitePackage 'worker.py') -or
        $GraniteProof.native_output -ne $GraniteNativeOutput -or $GraniteProof.execution_authorized -ne $false) {
        throw 'V3 worker-entry/preflight proof differs: preserve output and stop.'
    }
    Write-Output ('Retain complete preflight output: ' + $GranitePreflight)
    Write-Output ('Prospective native output only: ' + $GraniteNativeOutput)
}
~~~

**STOP for owner review of the actual v3 preflight result.** The child-process-only
ExecutionPolicy Bypass applies to this invocation only; no persistent policy
change or elevation. The old successful v2 preflight cannot replace this check.
Fresh native resource/supervision gates remain mandatory during any later attempt;
neither v2 nor v3 preflight readings establish workload resource fit.

### 4. Future pinned source acquisition and model-free compilation only

NOT AUTHORIZED / NOT EXECUTED. Only after separate explicit owner approval of the
exact v3 package and this scope, fill both placeholders with the approval reference
and the reviewed successful v3 preflight directory. Reuse that directory unchanged.
The packaged config stays inactive; approved config/record use new v3 filenames.

~~~powershell
& {
    $ErrorActionPreference = 'Stop'
    $GraniteOwnerApprovalReference = '<REQUIRED_SEPARATE_OWNER_V3_SOURCE_BUILD_APPROVAL>'
    $GranitePreflight = '<EXACT_REVIEWED_SUCCESSFUL_V3_PREFLIGHT_DIRECTORY>'
    if ($GraniteOwnerApprovalReference.StartsWith('<') -or [string]::IsNullOrWhiteSpace($GraniteOwnerApprovalReference) -or
        $GranitePreflight.StartsWith('<') -or [string]::IsNullOrWhiteSpace($GranitePreflight)) {
        throw 'Separate v3 source/build approval and accepted v3 preflight are required: stop.'
    }
    $GranitePackage = 'C:\Users\AndiWand\Downloads\granite-native-handoff-v3'
    $GranitePython = 'C:\Users\AndiWand\Downloads\granite-python-3.12.11-20250702\env\Scripts\python.exe'
    $GraniteManifestHash = '__MANIFEST_SHA256__'
    $GraniteConfigHash = '__CONFIG_SHA256__'
    if ($GraniteManifestHash -notmatch '^[0-9a-f]{64}$' -or $GraniteConfigHash -notmatch '^[0-9a-f]{64}$') {
        throw 'Externally approved v3 manifest/config hashes required: stop.'
    }
    $GraniteProof = Get-Content -Raw -LiteralPath (Join-Path $GranitePreflight 'preflight-result.json') | ConvertFrom-Json
    $GraniteNativeOutput = [string]$GraniteProof.native_output
    if ($GraniteProof.preflight_passed -ne $true -or $GraniteProof.configuration_inactive -ne $true -or
        $GraniteProof.worker_environment_validation_required -ne $true -or
        $GraniteProof.worker_environment_validation_passed -ne $true -or
        $GraniteProof.worker_module_path -ne (Join-Path $GranitePackage 'worker.py') -or
        $GraniteProof.expected_manifest_sha256 -ne $GraniteManifestHash -or
        $GraniteProof.package -ne $GranitePackage -or $GraniteProof.preflight_output -ne $GranitePreflight -or
        (Split-Path -Parent $GraniteNativeOutput) -ne 'C:\Users\AndiWand\Downloads' -or
        (Split-Path -Leaf $GraniteNativeOutput) -notmatch '^granite-native-v3-run-[0-9a-f-]{36}$') {
        throw 'Reviewed v3 preflight/destination proof differs: stop.'
    }
    $GraniteActiveConfig = $GraniteNativeOutput + '.approved.json'
    $GraniteApprovalRecord = $GraniteNativeOutput + '.approval.json'
    foreach ($GraniteFresh in @('C:\Resolena\gn1-20261025', $GraniteNativeOutput, $GraniteActiveConfig, $GraniteApprovalRecord)) {
        if (Test-Path -LiteralPath $GraniteFresh) { throw ('Fresh destination required; preserve it and stop: ' + $GraniteFresh) }
    }
    $GraniteManifestPath = Join-Path $GranitePackage 'manifest.json'
    if ((Get-FileHash -LiteralPath $GraniteManifestPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $GraniteManifestHash) {
        throw 'V3 manifest differs: stop.'
    }
    $GraniteManifest = Get-Content -Raw -LiteralPath $GraniteManifestPath | ConvertFrom-Json
    foreach ($GraniteEntry in $GraniteManifest.files.PSObject.Properties) {
        if ((Get-FileHash -LiteralPath (Join-Path $GranitePackage $GraniteEntry.Name) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $GraniteEntry.Value) {
            throw ('V3 package file differs: ' + $GraniteEntry.Name)
        }
    }
    $GraniteDraft = Join-Path $GranitePackage 'native-config.inactive.json'
    if ((Get-FileHash -LiteralPath $GraniteDraft -Algorithm SHA256).Hash.ToLowerInvariant() -ne $GraniteConfigHash) { throw 'V3 inactive config differs: stop.' }
    $GraniteApproved = Get-Content -Raw -LiteralPath $GraniteDraft | ConvertFrom-Json
    if ($GraniteApproved.execution_authorized -ne $false) { throw 'Expected inactive v3 configuration: stop.' }
    $GraniteApproved.execution_authorized = $true
    $GraniteApproved.owner = $GraniteOwnerApprovalReference
    function Write-GraniteApprovalFile([string]$Path, [string]$Text) {
        $GraniteBytes = [Text.UTF8Encoding]::new($false).GetBytes($Text)
        $GraniteStream = [IO.FileStream]::new($Path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
        try { $GraniteStream.Write($GraniteBytes, 0, $GraniteBytes.Length); $GraniteStream.Flush($true) }
        finally { $GraniteStream.Dispose() }
    }
    Write-GraniteApprovalFile $GraniteActiveConfig (($GraniteApproved | ConvertTo-Json -Depth 10) + [Environment]::NewLine)
    $GraniteApproval = [ordered]@{
        approval_reference = $GraniteOwnerApprovalReference; recorded_utc = [DateTimeOffset]::UtcNow.ToString('o')
        version = 'uc001-granite-native-handoff-v3'; archive_sha256 = '__ZIP_SHA256__'
        manifest_sha256 = $GraniteManifestHash; inactive_config_sha256 = $GraniteConfigHash
        active_config = $GraniteActiveConfig; active_config_sha256 = (Get-FileHash -LiteralPath $GraniteActiveConfig -Algorithm SHA256).Hash.ToLowerInvariant()
        preflight_output = $GranitePreflight; native_output = $GraniteNativeOutput
        scope = 'source_acquisition_and_model_free_native_build_only'
    }
    Write-GraniteApprovalFile $GraniteApprovalRecord (($GraniteApproval | ConvertTo-Json -Depth 5) + [Environment]::NewLine)
    & $GranitePython -I -B (Join-Path $GranitePackage 'controller.py') native --config $GraniteActiveConfig --output $GraniteNativeOutput
    if ($LASTEXITCODE -ne 0) { throw 'V3 native attempt failed: preserve all output and stop without fixes/retry.' }
    $GraniteResult = Get-Content -Raw -LiteralPath (Join-Path $GraniteNativeOutput 'result.json') | ConvertFrom-Json
    if ($GraniteResult.status -ne 'controlled_phases_passed' -or
        $GraniteResult.scope -ne 'source_acquisition_and_model_free_native_build_only') {
        throw 'V3 native terminal proof differs: preserve evidence and stop.'
    }
}
~~~

The unchanged controller revalidates the current actual worker environment and
starts fresh resource/supervision/identity checks before any owned phase launch.
No old resource readings are reused. It alone creates the fixed native root and
fresh evidence destination. If that root already exists, stop; do not delete or
relocate it. Preserve any partial result and stop without fixes/retry.

## Exact proposed future owner approval scope

First, separately authorize one v3 integrity/extraction, shell-local activation
and preflight-only attempt, including the actual worker environment entry check
and retained reports. Stop for owner review before source/build.

Only after reviewing those Windows results, a separate decision may authorize one
supervised existing-controller invocation for the pinned runtime-source acquisition,
required source/object/archive validation and model-free llama-server compilation,
including required compiler/glslc/host shader-generator work. Keep all frozen
identity protections, numeric limits, cumulative charge/time and failure stops.
No model weights, GPU/VRAM probe, server execution (including --version), inference,
converters, benchmarks, closed diagnostics, installation, persistent policy change
or Git delivery. This document grants none of that execution permission.

## Unchanged limits, shared accounting and retained outputs

| Limit | Exact value |
|---|---|
| Acquisition window | One continuous original 1800 seconds |
| Shared model/source ceiling | 10737418240 cumulative conservative bytes |
| Configure + build | 2700 seconds combined |
| Private-Job memory | 25769803776 aggregate committed bytes, **not RSS** |
| Generated build output | 12884901888 bytes |
| Initial disk | At least 51539607552 caller-available bytes |
| Disk floor | Stop below 8589934592 bytes |
| Host physical-memory floor | Stop below 4294967296 bytes |
| Outer parallelism | 2 |

The accepted prior receipt remains byte-identical, including historical preparation
bindings and the owner-attested prior charge. No current download balance or
measured zero is fabricated. According to exact issued native_run source ordering,
the failed v2 invocation did not reach run_session/T0; desktop artifact absence
was not inspected. No acquisition ledger or T0 is reconstructed or reset.
When a separately authorized real acquisition initializes the original window,
build/review keeps consuming elapsed time. A 45-minute build can exhaust the shared
30-minute window and prevent later model acquisition. Carry actual validated source
charges and original T0 forward; never subtract overhead, pause, reset or renew.
This package provides no later model-download route or allowance.

Retain the entire future preflight directory, including package-validation.json
and preflight-result.json, tool/version stdout/stderr and resource observations.
If later separately approved, retain the approved configuration/approval record,
entire native output (result.json, controller/phase journals/stdout/stderr and
worker configuration) and the complete native root: repository, source ZIP/tree,
identity/archive/accounting ledgers, tool/environment hashes, CMake cache/build
files, licences and build/bin artifacts/DLLs. No compiled artifact hash is known
before execution. Never run the built server to identify it. Preserve all v2 and
failed-attempt evidence. On any failure, stop without fixes/retry.
