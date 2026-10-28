# Granite owner handoff and prerequisite receipt — 2026-10-25

The owner accepted only the demonstrated candidate-specific adapter, mocked
checks and frozen assessment preparation: **43 final focused passes and seven
existing regressions**, without accumulating reruns. Granite remains provisional;
suitability is unverified. The overwritten intermediate test-clock log limitation
in the [original receipt](../uc001-granite-contract-v1/verification.json) remains;
no log was reconstructed. The advisor reviewed the supplied artifacts, case bytes
and pinned native fields, without live runtime, full-archive audit, Windows
execution or independent pytest execution.

This session executes in the Codespace, not the Windows desktop. No desktop
command below has been executed. The authorized stopping point is owner-mediated
handoff instructions, pending the owner's actual prerequisite output.

## Existing archive verified in the Codespace

Download only [desktop-transfer.zip](../uc001-granite-contract-v1/desktop-transfer.zip)
using the Codespaces/VS Code Explorer **Download** action. Exact remote location:
`/workspaces/resolena-alternative-finder/build/uc001-granite-contract-v1/desktop-transfer.zip`.

- Actual size: **229509 bytes**.
- Actual SHA-256: `10df90cc82de5ba92891993f3bd372978561c19c9e4f36e8277a635c5df91abd`.
- Frozen bundle: `9a4acb903c834737809b2648c358da9f2d91b116471966fb7b691847a069f4b4`.
- All **39 frozen files plus freeze.json** verified; every frozen entry's size/hash
  and current-worktree bytes match. No duplicate/case-colliding, symlink or unsafe
  entries. Frozen source payload: 2525031 bytes. No archive regeneration/re-freeze.

The exact allowlist carries required uncommitted application/composition files,
package and approved references. It excludes credentials, private databases,
caches, held-out material and old experiment directories. Do not copy the whole
repository or substitute HEAD. All original package/receipt bytes remain protected.

## Windows PowerShell — owner desktop only

Use an ordinary existing local Downloads directory without reparse links. Change
only the two local paths if necessary; the destination must not exist. Run this
block once in an existing PowerShell window. Compare the hash with the reviewed
value above before reading/executing archive content. This uses installed .NET
ZIP APIs, not compilation, model tooling or code from the archive.

```powershell
$ErrorActionPreference = 'Stop'
$GraniteArchive = Join-Path $env:USERPROFILE 'Downloads\desktop-transfer.zip'
$GraniteDestination = Join-Path $env:USERPROFILE 'Downloads\granite-handoff-2026-10-25'
if ((Get-Item -LiteralPath $GraniteArchive).Length -ne 229509 -or
    (Get-FileHash -LiteralPath $GraniteArchive -Algorithm SHA256).Hash.ToLowerInvariant() -ne '10df90cc82de5ba92891993f3bd372978561c19c9e4f36e8277a635c5df91abd') { throw 'Archive differs: stop; do not regenerate or extract.' }
if (Test-Path -LiteralPath $GraniteDestination) { throw 'Destination already exists: preserve it and stop.' }
for ($GraniteParent = Get-Item -LiteralPath (Split-Path -Parent $GraniteDestination); $null -ne $GraniteParent; $GraniteParent = $GraniteParent.Parent) {
    if ($GraniteParent.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Choose an ordinary local directory without reparse ancestors.' }
}
Add-Type -AssemblyName System.IO.Compression.FileSystem
$GraniteZip = [IO.Compression.ZipFile]::OpenRead($GraniteArchive)
try {
    $GraniteManifestName = 'scripts/uc001_granite_contract_v1/freeze.json'
    $GraniteReader = [IO.StreamReader]::new($GraniteZip.GetEntry($GraniteManifestName).Open())
    try { $GraniteFreeze = $GraniteReader.ReadToEnd() | ConvertFrom-Json } finally { $GraniteReader.Dispose() }
    if ($GraniteFreeze.bundle_id -cne '9a4acb903c834737809b2648c358da9f2d91b116471966fb7b691847a069f4b4') { throw 'Wrong frozen bundle.' }
    $GraniteAllowed = @($GraniteFreeze.files.PSObject.Properties.Name) + $GraniteManifestName
    $GraniteEntries = @($GraniteZip.Entries)
    if ($GraniteAllowed.Count -ne 40 -or $GraniteEntries.Count -ne 40 -or
        @($GraniteEntries.FullName | Sort-Object -Unique).Count -ne 40 -or
        ($GraniteEntries | Measure-Object -Property Length -Sum).Sum -gt 33554432) { throw 'Unexpected archive inventory.' }
    foreach ($GraniteEntry in $GraniteEntries) {
        $GraniteName = $GraniteEntry.FullName
        if ($GraniteName -cnotin $GraniteAllowed -or $GraniteName -match '(^/|\\|:|(^|/)\.\.?(/|$)|[. ](/|$)|(^|/)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|/|$))' -or
            (($GraniteEntry.ExternalAttributes -shr 16) -band 61440) -eq 40960) { throw 'Unexpected or unsafe entry.' }
        if ($GraniteName -ceq $GraniteManifestName) { continue }
        $GraniteExpected = $GraniteFreeze.files.PSObject.Properties[$GraniteName].Value
        $GraniteStream = $GraniteEntry.Open()
        $GraniteHasher = [Security.Cryptography.SHA256]::Create()
        try { $GraniteDigest = [BitConverter]::ToString($GraniteHasher.ComputeHash($GraniteStream)).Replace('-', '').ToLowerInvariant() }
        finally { $GraniteHasher.Dispose(); $GraniteStream.Dispose() }
        if ($GraniteEntry.Length -ne $GraniteExpected.bytes -or $GraniteDigest -cne $GraniteExpected.sha256) { throw 'Frozen entry differs.' }
    }
    $GraniteEntries | Select-Object FullName, Length | Format-Table -AutoSize
} finally { $GraniteZip.Dispose() }
if (Test-Path -LiteralPath $GraniteDestination) { throw 'Destination appeared during verification: preserve it and stop.' }
[IO.Compression.ZipFile]::ExtractToDirectory($GraniteArchive, $GraniteDestination)
Write-Output "Verified archive extracted into new destination: $GraniteDestination"
```

The reviewed whole-archive hash pins the manifest before it is read. Each allowed
file is then checked before extraction. Extraction does not overwrite existing
files. On any failure preserve partial output and stop; do not rerun into it.

In the **same desktop PowerShell window**, perform one read-only prerequisite
pass. If the existing approved Python environment uses another executable,
substitute its known path; do not search/install/upgrade. A WindowsApps alias is
not an established Python environment. The Python snippet reads distribution
metadata only; it imports no application, model, detector or test modules.

```powershell
[DateTime]::UtcNow.ToString('o')
foreach ($GraniteTool in @('python', 'git', 'cmake', 'ninja', 'cl', 'glslc')) {
    $GraniteCommand = Get-Command $GraniteTool -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    [pscustomobject]@{ Tool = $GraniteTool; Available = [bool]$GraniteCommand; Path = $GraniteCommand.Source; Version = $(if ($GraniteCommand) { (Get-Item -LiteralPath $GraniteCommand.Source).VersionInfo.ProductVersion }) }
}
[pscustomobject]@{ MsvcTarget = $env:VSCMD_ARG_TGT_ARCH; MsvcVersion = $env:VSCMD_VER; WindowsSdk = $env:WindowsSdkDir; VulkanSdk = $env:VULKAN_SDK }
if ($env:VULKAN_SDK) { Test-Path -LiteralPath (Join-Path $env:VULKAN_SDK 'Bin\glslc.exe') }
$GraniteVolume = [IO.Path]::GetPathRoot($GraniteDestination).TrimEnd('\')
Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='$GraniteVolume'" | Select-Object DeviceID, FreeSpace, Size
Get-CimInstance Win32_OperatingSystem | Select-Object FreePhysicalMemory, TotalVisibleMemorySize
$GranitePython = (Get-Command python -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1).Source
if (-not $GranitePython -or $GranitePython -match '\\WindowsApps\\') { throw 'Existing approved Python path missing/unverified: report and stop; no installation.' }
$GraniteMetadata = @'
import importlib.metadata as m, json, sys
expected = json.load(open(sys.argv[1], encoding="utf-8"))
observed = {}
for name in expected["packages"]:
    try: observed[name] = m.version(name)
    except m.PackageNotFoundError: observed[name] = None
print(json.dumps({"python": sys.version.split()[0], "expected": expected, "installed": observed}, indent=2))
'@
& $GranitePython -I -B -c $GraniteMetadata (Join-Path $GraniteDestination 'scripts\uc001_granite_contract_v1\validation-dependencies.json')
if ($LASTEXITCODE -ne 0) { throw 'Python metadata check failed: preserve output and stop.' }
& $GranitePython -I -B (Join-Path $GraniteDestination 'scripts\uc001_granite_contract_v1\package.py') verify
if ($LASTEXITCODE -ne 0) { throw 'Extracted frozen files differ: stop.' }
& $GranitePython -I -B (Join-Path $GraniteDestination 'scripts\uc001_granite_contract_v1\package.py') verify-archive --archive $GraniteArchive
if ($LASTEXITCODE -ne 0) { throw 'Transferred archive verification failed: stop.' }
```

`FreeSpace`/`Size` are bytes; OS physical-memory fields are KiB. Tool paths and
environment fields show availability, not successful compilation or compatibility.
The frozen Python version is 3.12.11; required distributions are FastAPI 0.142.2,
Pydantic 2.13.5, HTTPX 0.28.1, SQLAlchemy 2.1.3, Starlette 1.7.0 and pytest 9.1.1.
Report absent/different versions; do not change the freeze or dependencies.

Return this output and identify any **already approved** GPU attribution/resource/
process/deadline/cleanup mechanism with its actual evidence. The old Qwen stand-in
ownership evidence covers its tested ownership/exits only; it is not a verified
Granite supervisor, current available VRAM or a reusable startup allowance. No GPU
probe/allocation, model run or supervisor implementation is requested. Reviewer
availability requires an actual owner/reviewer confirmation and competence basis.

## Factual readiness at handoff

| Prerequisite | Observed evidence | Ready / missing / unverified |
|---|---|---|
| Frozen handoff source | Actual reviewed archive hash/size, bundle and 39 files match in Codespace | ready for owner copy |
| Desktop copy/new destination | No desktop output received | unverified |
| Python and installed distributions | Exact expected versions frozen; desktop not checked | unverified |
| Git, CMake, Ninja | No desktop observations | unverified |
| x64 MSVC environment; Vulkan SDK/compiler | No desktop observations | unverified |
| Destination disk and free host memory | No current desktop measurements | unverified |
| Intended-GPU attribution and available VRAM | No current approved measurement supplied; nominal 16 GB is insufficient | unverified |
| Appropriate approved supervisor/evidence | Package supplies none; no existing appropriate mechanism confirmed | missing confirmation; launch blocked |
| Competent review availability | No actual owner/reviewer confirmation | unverified |

Later acquisition/build needs the verified desktop handoff, existing tools/x64
environment, suitable disk/host capacity, approved acquisition/build supervision
and separate owner authorization. Before launch, actual artifact/header/template/
runtime/native-converter checks, useful Vulkan offload, fresh supported resource
measurements, trustworthy process/deadline/cleanup supervision and competent review
remain additional gates. Neither stage is declared ready from Linux observations.

Numerical bounds remain unchanged proposals: initial disk 48 GiB, prestart disk
24 GiB, prestart host free 24 GiB, prestart GPU free 12 GiB, together with all
limits in frozen config.json. This check neither approves nor loosens them.

Smallest next remedy: owner runs the pass above and returns actual output, naming
any existing approved supervision mechanism/evidence and confirmed reviewer.
If none exists, report that prerequisite as missing and obtain separate bounded
authorization before any installation or supervisor work. No new infrastructure
selection, acquisition, build or launch follows automatically.

## Documentation and preservation checks

Local Markdown links and new whitespace checks passed. Read-only `git rev-parse
HEAD`, `git branch --show-current`, `git ls-files --stage` and `git status --short
--branch` confirm unchanged HEAD, branch, index and existing status entries.
`git diff --check` exits **2** only for the preserved historical TASKS trailing
space at line **2440**; it was not cleaned up.

All **832 previously protected files** outside the authorized TASKS edit match
their existing fingerprints. All **70 original Granite package/receipt/test
files** also match their handoff-entry fingerprints (overlapping counts are not
added). Their sorted path/hash-map SHA-256 is
`05cc2f75c7b3b4f7a3e8c1fa9bb83ba6092cd313d1dde6e1c26afe835b17d985`.
Priority 5 status and all following TASKS history remain byte-identical. Only TASKS
and this new handoff receipt were written. No offline tests, Windows commands,
services, acquisition, compilation, inference or Git mutations were executed.

PHASE: 3 / STATUS: in-progress; Priorities 3/4 partial, Priority 6 and Phase 4 pending.
Priority 5 acceptance/ADR-007, closed Qwen/experiments, unconfigured app.main,
inactive real drafts and development-only reference permissions remain unchanged.
