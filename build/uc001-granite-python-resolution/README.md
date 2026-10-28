# Granite Python environment resolution proposal — 2026-10-25

Documentation only. Owner observations below were not executed by Codex.
No handoff recheck, application import/test, installation, binary download or
Windows command occurred. Primary-source pages/metadata and one HTTP HEAD request
were read; HEAD returned 200/21177389 bytes without reading the binary body.

## Owner-supplied desktop observations

- Destination: `C:\Users\AndiWand\Downloads\granite-handoff-2026-10-25`.
- Both `package.py verify` and `verify-archive` succeeded: 39 files, inference
  false, bundle `9a4acb903c834737809b2648c358da9f2d91b116471966fb7b691847a069f4b4`.
  This establishes owner-reported handoff integrity, not application compatibility.
- Existing interpreter: `C:\ResolenaExperiments\uc001-validator-env\Scripts\python.exe`,
  Python **3.12.10**. Pydantic 2.13.5, HTTPX 0.28.1 and pytest 9.1.1 match.
  FastAPI, SQLAlchemy and Starlette are absent from that environment. Preserve it.
- Earlier disk free: **589066960896 bytes**; host free: **35577820 KiB**.
  These are dated owner observations, not fresh measurements or approval of limits.
- Git/CMake/Ninja/cl/glslc were not found in the ordinary PowerShell session;
  machine-wide absence is not established. MSVC/Windows SDK/Vulkan SDK environment
  fields were empty. GPU availability, supervision and competent review remain
  unverified; this task does not reopen those checks.

## One recommended isolated route

Use **Astral python-build-standalone CPython 3.12.11, build 20250702, Windows
x86_64 MSVC, install_only_stripped**, extracted into a new private Granite directory,
then create a separate venv. No uv installation, PATH/registry change, machine-wide
upgrade or mutation of the old validator environment is proposed.

The [PSF release page](https://www.python.org/downloads/release/python-31211/)
confirms 3.12.11 has no binary installers. Astral provides a separate distribution;
it is not a PSF Windows installer. Its [pinned distributor catalogue](https://raw.githubusercontent.com/astral-sh/uv/0.7.19/crates/uv-python/download-metadata.json)
lists the exact Windows x64 asset and expected SHA-256 below. The asset is available
by HTTP HEAD; no acquired artifact hash is claimed. The [archive specification](https://docs.astral.sh/python-build-standalone/distributions/#install-only-archive)
documents install-only layout under `python/` and stripped archives.

`assess.py:check_dependencies` checks Windows and exact `platform.python_version()`
against **3.12.11**, plus all six distribution versions. This proposal preserves
that requirement and leaves the gate and v1 freeze unchanged. It does not silently
accept 3.12.10. No version amendment is needed for this route. A different Python
version would instead require owner-approved separate versioned package/manifest
amendment, new freeze/handoff and focused offline gate/adapter/API/SQLite compatibility
verification; changing or bypassing the v1 check in place is not authorized.

## Primary package metadata: compatible declarations, not runtime proof

All six versions exist, are not yanked, and admit Python 3.12. The links are exact
PyPI release metadata. No pip resolver or installation was executed.

| Exact release | Requires-Python | Relevant declared constraint / Windows distribution |
|---|---|---|
| [FastAPI 0.142.2](https://pypi.org/pypi/fastapi/0.142.2/json) | >=3.10 | Starlette>=0.46.0, Pydantic>=2.9.0; universal wheel |
| [Pydantic 2.13.5](https://pypi.org/pypi/pydantic/2.13.5/json) | >=3.9 | pydantic-core==2.46.5; universal wheel |
| [HTTPX 0.28.1](https://pypi.org/pypi/httpx/0.28.1/json) | >=3.8 | AnyIO, httpcore==1.*; universal wheel |
| [SQLAlchemy 2.1.3](https://pypi.org/pypi/sqlalchemy/2.1.3/json) | >=3.11 | cp312 Windows x64 wheel |
| [Starlette 1.7.0](https://pypi.org/pypi/starlette/1.7.0/json) | >=3.10 | AnyIO>=4,<5; universal wheel |
| [pytest 9.1.1](https://pypi.org/pypi/pytest/9.1.1/json) | >=3.10 | Includes Windows Colorama dependency; universal wheel |

[pydantic-core 2.46.5](https://pypi.org/pypi/pydantic-core/2.46.5/json) publishes
`pydantic_core-2.46.5-cp312-cp312-win_amd64.whl`. Applicable optional-free transitive
metadata also admits 3.12 and Windows wheels, using the exact pins below. Their
exact metadata endpoints are `https://pypi.org/pypi/<name>/<version>/json`.
Do not install `standard`/`full` extras or the broader server requirements.
Declared compatibility and wheel availability do not prove actual Windows imports,
native DLL loading or the Starlette/legacy-HTTPX TestClient path. Those remain later
focused offline compatibility observations, separately authorized; integrity checks
and a future successful pip check cannot establish them or interpreter suitability.

## Required approval and prerequisites

Owner approval is required **before** the commands below: acquire this exact
third-party CPython build, verify its published hash, extract it into the new
Granite-only directory, create its venv and install only the pinned wheel set,
then run pip/standard-library metadata checks. This is proposed setup, not current
permission, package amendment, application-test permission or model authorization.

Prerequisites: Windows x64 with existing runtime/DLL support; existing PowerShell
with HTTPS access to GitHub/PyPI and an already available `tar.exe`; an unused,
writable ordinary local destination. Missing tools/DLLs or resolution failures
mean stop and report, without source builds, installation of system components,
dependency substitution or changes to the old environment. No compiler/SDK is
needed for this wheel-only Python route; model-runtime build prerequisites remain
separate and unverified.

## Proposed commands — Windows PowerShell, owner desktop, after approval only

Execute none under the current documentation authorization. Use explicit paths;
do not activate or upgrade the old environment. Preserve partial artifacts on any
failure; no automatic retry or alternative version follows.

```powershell
$ErrorActionPreference = 'Stop'
$GraniteSetup = Join-Path $env:USERPROFILE 'Downloads\granite-python-3.12.11-20250702'
if (Test-Path -LiteralPath $GraniteSetup) { throw 'Use a new destination; preserve prior work.' }
$GraniteTar = (Get-Command tar.exe -CommandType Application -ErrorAction Stop).Source
$null = New-Item -ItemType Directory -Path $GraniteSetup -ErrorAction Stop
$GranitePythonArchive = Join-Path $GraniteSetup 'cpython-3.12.11-20250702-windows-x64.tar.gz'
$GranitePythonUrl = 'https://github.com/astral-sh/python-build-standalone/releases/download/20250702/cpython-3.12.11%2B20250702-x86_64-pc-windows-msvc-install_only_stripped.tar.gz'
Invoke-WebRequest -UseBasicParsing -Uri $GranitePythonUrl -OutFile $GranitePythonArchive -TimeoutSec 120
if ((Get-Item -LiteralPath $GranitePythonArchive).Length -ne 21177389 -or
    (Get-FileHash -LiteralPath $GranitePythonArchive -Algorithm SHA256).Hash.ToLowerInvariant() -ne '195033883da90a35a57aecce522eb068b9b0a36908e6e07b91929f0acf646c8f') { throw 'CPython archive size/hash differs: stop.' }
& $GraniteTar -xzf $GranitePythonArchive -C $GraniteSetup
if ($LASTEXITCODE -ne 0) { throw 'Extraction failed: stop.' }
$GraniteBasePython = Join-Path $GraniteSetup 'python\python.exe'
@'
import sys, struct
assert sys.platform == "win32" and sys.version_info[:3] == (3, 12, 11) and struct.calcsize("P") == 8
print(sys.version)
'@ | & $GraniteBasePython -I -B -
if ($LASTEXITCODE -ne 0) { throw 'Required CPython version/architecture not established: stop.' }
$GraniteVenv = Join-Path $GraniteSetup 'env'
& $GraniteBasePython -I -B -m venv $GraniteVenv
if ($LASTEXITCODE -ne 0) { throw 'New Granite environment creation failed: stop.' }
$GranitePython = Join-Path $GraniteVenv 'Scripts\python.exe'
$GranitePins = @(
    'fastapi==0.142.2', 'pydantic==2.13.5', 'httpx==0.28.1',
    'sqlalchemy==2.1.3', 'starlette==1.7.0', 'pytest==9.1.1',
    'pydantic-core==2.46.5', 'annotated-types==0.8.0',
    'typing-extensions==4.16.0', 'typing-inspection==0.4.4',
    'annotated-doc==0.0.5', 'opentelemetry-api==1.45.1',
    'anyio==4.15.1', 'certifi==2026.10.23', 'httpcore==1.0.9',
    'h11==0.16.0', 'idna==3.20', 'colorama==0.4.6',
    'iniconfig==2.3.1', 'packaging==26.3', 'pluggy==1.7.0', 'pygments==2.21.0'
)
& $GranitePython -I -B -m pip --isolated --disable-pip-version-check --no-cache-dir install --index-url https://pypi.org/simple --only-binary=:all: --retries 0 --timeout 30 --report (Join-Path $GraniteSetup 'install-report.json') @GranitePins
if ($LASTEXITCODE -ne 0) { throw 'Pinned wheel resolution/installation failed: stop without changes or retries.' }
& $GranitePython -I -B -m pip --isolated --disable-pip-version-check check
if ($LASTEXITCODE -ne 0) { throw 'Installed dependency constraints failed: stop.' }
$GraniteMetadata = @'
import importlib.metadata as m, json, sys
from pathlib import Path
expected = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
observed = {name: m.version(name) for name in expected["packages"]}
assert sys.platform == "win32" and sys.version.split()[0] == expected["python"]
assert observed == expected["packages"]
print(json.dumps({"python": sys.version, "executable": sys.executable, "installed": observed}, indent=2))
'@
$GraniteMetadata | & $GranitePython -I -B - 'C:\Users\AndiWand\Downloads\granite-handoff-2026-10-25\scripts\uc001_granite_contract_v1\validation-dependencies.json'
if ($LASTEXITCODE -ne 0) { throw 'Frozen Python/distribution metadata differs: stop.' }
```

Stop after setup and metadata output for owner review. Preserve the install report
and original v1 package/archive/receipts. Do not run the assessment, application
imports/tests, services, GPU probes, runtime acquisition/build or inference from
this procedure. Further focused compatibility verification needs separate scope.

Only this readiness receipt and TASKS were written. Original handoff rows/receipts
remain historical, with these owner observations appended as a separate record.
Documentation links, Markdown fences and new whitespace checks passed. Read-only
Git checks confirm unchanged HEAD `a6b2479c3d82ff5d9987a73d310a3a4eff064455`,
branch `specify/phase-1-uc-001`, index and existing file-status entries. All 832
previously protected files outside TASKS and all 71 original Granite preparation/
handoff files retain their fingerprints (overlapping counts are not added).
`git diff --check` exits 2 only for the preserved historical TASKS trailing space,
now at line 2460. No handoff commands, setup, imports or tests were executed.
PHASE: 3 / STATUS: in-progress; Priorities 3/4 partial; Priority 6/Phase 4 pending.
Priority 5 acceptance/ADR-007 and the closed Qwen result remain unchanged.
