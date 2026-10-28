# Granite Windows compatibility-check preparation — 2026-10-25

## Owner-supplied setup result

Observed by the owner at **2026-10-25T16:49:01.935641+00:00**, not executed by Codex:

- Approved CPython archive SHA-256 verified:
  `195033883da90a35a57aecce522eb068b9b0a36908e6e07b91929f0acf646c8f`.
- Python **3.12.11, Windows x64**. New executable:
  `C:\Users\AndiWand\Downloads\granite-python-3.12.11-20250702\env\Scripts\python.exe`.
- All **22 approved pins** and all **six frozen requirements** match.
  `pip check`: **No broken requirements found.** `metadata_check_passed: true`.
- `application_tests_run: false`; `model_started: false`.
- Owner retains `setup-result.json` and `install-report.json` beneath
  `C:\Users\AndiWand\Downloads\granite-python-3.12.11-20250702`.
  These desktop files were **not read remotely**. Setup did not target the original
  validator environment or the frozen handoff.

Installation/metadata success is owner-reported verified. Windows application
compatibility remains pending; Granite/model/runtime suitability remains unverified.
The [historical proposal](../uc001-granite-python-resolution/README.md) is unchanged.

## Executable check and boundary

[check.py](check.py) is the complete standalone artifact, outside the frozen package.
SHA-256: **`8a3bf0f118bb467d7e77c0108af1d7635c7210147de47e59e90ba81180777f7f`**.
Size: **12311 bytes**.

It imports the frozen Granite adapter and assessment module without constructing
Granite transport or invoking assessment. Explicit interpreter/worktree gates,
`-I -B` and module-origin checks bind project imports to the transferred files.
The existing `create_development_app` and `tests.support.synthetic` are already
included in that transfer; no additional test support or suite copy is required.

One prepared interpretation of existing `EXAMPLE` supplies **one in-process POST**
through FastAPI/Pydantic/Starlette/HTTPX/application/SQLAlchemy/SQLite. Required
success expectations reuse `test_returns_only_the_committed_projection_with_saved_ids_and_evidence`:
HTTP 201, `comparison`, persistence `saved`, matching request UUID/timestamp,
Alpha/Zeta synthetic options in positions 1/2, complete saved projection and option
snapshots, direct option-to-request binding, evidence links and fixture snapshots.
Required before/after request/option/link counts are **0/0/0 → 1/2/2**; seeded
alternatives/evidence stay **2/2**. These are pending assertions, not observed results.

The check blocks network-backed HTTPX transports and Granite construction. It uses
Starlette's in-process transport, starts no HTTP server, closes TestClient and all
SQLite read connections, and disposes tracked database engines even on failure.
It never invokes live assessment, changes approval gates, activates app.main,
loads a model, accesses a GPU or downloads/installs/builds anything.

Each invocation reserves a new UUID directory beneath the transferred worktree's
`build/test-only/`, containing `compatibility.sqlite3` and `result.json`.
Existing files are never overwritten. Result JSON/stdout records stage, concrete
failure, imports, HTTP response, saved identities/counts and cleanup observations.
This is a prepared **synthetic Windows dependency check**, not Granite generation,
semantic acceptance, captured-model replay or another Priority 5 scenario.

## Windows PowerShell — owner desktop only

Download **only check.py** through the Codespaces Explorer, saving it outside the
freeze as `C:\Users\AndiWand\Downloads\granite-windows-compat-v1.py`.
The session cannot execute on the desktop. Run this once using the already verified
worktree and new environment; no activation, installation or handoff recheck:

```powershell
$ErrorActionPreference = 'Stop'
$GraniteCheck = 'C:\Users\AndiWand\Downloads\granite-windows-compat-v1.py'
if ((Get-FileHash -LiteralPath $GraniteCheck -Algorithm SHA256).Hash.ToLowerInvariant() -ne '8a3bf0f118bb467d7e77c0108af1d7635c7210147de47e59e90ba81180777f7f') { throw 'Check file hash differs: stop.' }
& 'C:\Users\AndiWand\Downloads\granite-python-3.12.11-20250702\env\Scripts\python.exe' -I -B $GraniteCheck --worktree 'C:\Users\AndiWand\Downloads\granite-handoff-2026-10-25'
if ($LASTEXITCODE -ne 0) { throw 'Compatibility check failed: preserve output/result/database and stop; no fix or retry.' }
```

Return the printed output and retained result for review. Do not rerun on failure,
add packages, change the application/freeze or proceed to runtime/model work.
No further approval is inferred from a pass. Resource supervision, hardware
readiness and competent linguistic review remain outside this task and unverified.

## Preparation evidence

Codespace command: `python3` with standard-library `ast.parse` over check.py bytes,
and `hashlib.sha256`; final syntax passed and the hash above was recorded.
This **does not import or execute the check or application**, establish Windows
DLL compatibility, or count as a passing application test. Static source review
checked the transferred helper closure, positive-path assertions and cleanup.
No broad offline suite or desktop invocation ran. Documentation links, new
whitespace, recorded hash and Python syntax checks passed; static AST contains one
POST call site. All 832 previously protected files outside TASKS and all 72
original Granite preparation/handoff/proposal files retain their fingerprints
(overlapping counts are not added). Prior TASKS history and Priority 5 acceptance
are preserved. Read-only Git checks confirm unchanged HEAD, branch, index and
existing file-status entries. `git diff --check` exits 2 only for the preserved
historical TASKS trailing space at line 2481. Only TASKS and this new check/receipt
were written; original v1 bytes and receipts remain unchanged.

PHASE: 3 / STATUS: in-progress. Priorities 3/4 remain partial; Priority 6/Phase 4
remain pending. Priority 5 acceptance/ADR-007 and closed Qwen/experiments remain
unchanged; app.main unconfigured, real drafts inactive, reference permissions unchanged.
