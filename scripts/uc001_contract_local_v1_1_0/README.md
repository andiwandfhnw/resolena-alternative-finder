# Windows-local technical feasibility — v1.1.0

Owner decision permits the existing bounded technical run while outstanding linguistic
approvals remain pending. Qualified expectations and model-output review are still
required before interpreter suitability or multilingual acceptance. Priority 3 partial;
Phase 3 DEVELOP in-progress. No execution occurred during this preparation.

`technical-decision.json` records that decision. `partial-expectations-review.json`
and `previous-freeze.json` are exact copies: the original review stays bound to
`4a38c66c09c4611530f3290f3d3f3de16fbd7ab2b403b764435d0a598c150079`.
The gate checks the unchanged parent freeze and prompt/schema/cases/config hashes.
DE/EN cases 2/5/10/11/13/14 and Swiss German case 12 retain their confirmations;
1/3/4/6/7/8/9 remain unapproved. `expected_meanings_approved` stays false.
The historical receipt's `startup_authorized:false` is preserved; this separate
owner decision supplies permission for the technical check only.

Launcher preflight, capture and owner-capture replay all enforce this decision and
the unchanged partial review. Shared adapter/domain validation and `check_case_state`
still stop on failure before another generation; unreviewed expectations are
provisional. Outputs separate technical validation, provisional case/policy checks
and pending semantic review. No technical pass can establish interpreter acceptance.

The original attempt identity/directory, create-once ledger, one startup/14 generations
in the same order, 90-second absolute per-request deadline (including prompt-fit and
validation), time/resource/artifact caps, authentication, native ownership and cleanup
are unchanged. No retry, repair, tuning, fallback or allowance reset. v1.3.0 helpers,
application source, model/runtime pins, prompt/schema/cases and dependencies are unchanged.
The original package, freeze and owner receipts remain preserved separately.

## One owner-operated Windows handoff

Download [windows-local-technical-source.zip](../../build/uc001-contract-local-v1_1_0/windows-local-technical-source.zip)
and [SHA256SUMS.txt](../../build/uc001-contract-local-v1_1_0/SHA256SUMS.txt) into
`C:\ResolenaExperiments\uc001-contract-local-v1_1_0-handoff`.
Charge actual transfers against the existing allowance (last owner setup receipt:
46,845,816 bytes remaining; earlier source transfers must also be accounted for).
Reuse the installed verified venv; no dependencies or model/runtime assets are downloaded.
In **64-bit Windows PowerShell 5.1**, paste once:

```powershell
$ErrorActionPreference = 'Stop'
if (-not [Environment]::Is64BitProcess -or $PSVersionTable.PSVersion.Major -ne 5 -or $PSVersionTable.PSVersion.Minor -ne 1) { throw 'Use 64-bit Windows PowerShell 5.1' }
$Incoming = 'C:\ResolenaExperiments\uc001-contract-local-v1_1_0-handoff'
$Archive = Join-Path $Incoming 'windows-local-technical-source.zip'
$Rows = @(Get-Content -LiteralPath (Join-Path $Incoming 'SHA256SUMS.txt') | Where-Object { $_ -match '^[0-9a-f]{64}  build/uc001-contract-local-v1_1_0/windows-local-technical-source\.zip$' })
if ($Rows.Count -ne 1 -or (Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Rows[0].Substring(0,64)) { throw 'Package hash mismatch; stop' }
$Root = 'C:\ResolenaExperiments\uc001-contract-local-v1_1_0'
if (Test-Path -LiteralPath $Root) { throw 'Extraction destination exists; preserve it and stop' }
Expand-Archive -LiteralPath $Archive -DestinationPath $Root
$Local = Join-Path $Root 'scripts\uc001_contract_local_v1_1_0'
& 'C:\ResolenaExperiments\uc001-validator-env\Scripts\python.exe' -I -X utf8 -B (Join-Path $Local 'capture.py') --preflight --review (Join-Path $Local 'partial-expectations-review.json')
if ($LASTEXITCODE -ne 0) { throw 'Revised preparation/decision gate failed; stop without repair or retry' }
& "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy RemoteSigned -File (Join-Path $Local 'Run-Windows.ps1') -Execute -Review (Join-Path $Local 'partial-expectations-review.json')
if ($LASTEXITCODE -ne 0) { throw 'Technical run stopped; preserve its private evidence and do not retry' }
```

The launcher repeats current source/dependency/schema/decision checks, freshly hashes
the retained runtime ZIP/model/52 runtime files, establishes complete native CIM/PCI/
DXGI/LUID/exact-WDDM identity and DXGI capacity, checks port 49187 and existing model
processes, and requires a new original attempt directory. It requires at least 20 GiB
free RAM, 14 GiB free GPU and 6 GiB disk before startup; the earlier 13,099,008-byte GPU
margin is historical. Do not substitute that snapshot. After its single startup,
protected authentication, owned loopback listener, positive measured owned-GPU
allocation, effective full offload/context/settings and readiness must pass before
generation. All existing runtime thresholds/deadlines and one-second monitoring remain.
Any failure stops; preserve the attempt directory and never delete/reset the ledger.

Native effects: unchanged Add-Type C# compilation may create temporary compiler files;
DXGI/WDDM/CIM/registry reads, Win32 process/job calls, restrictive directory ACLs,
one owned server and one owned Python worker. Confirmed cleanup of those processes
is required. The Codespace tests use synthetic measurements/processes; they do not
verify this Windows path, owned-GPU counters, allocation or model readiness.

## Codespace replay after confirmed Windows cleanup

Transfer **export only**, never private captures/logs/stdin/environment secrets.
Incomplete, secret-bearing and uninspectable captures stay private. Raw bounded
requests/responses precede parsing; the existing explicit authenticated logical-port
mapping and privacy scans remain unchanged. Replay has no network fallback.

```bash
PYTHONPATH=src:. .venv/bin/python -m scripts.uc001_contract_local_v1_1_0.replay \
  --export build/test-only/windows-local-technical-export \
  --output build/test-only/windows-local-technical-replay
```

Replay requires complete ordered captures/ledger and confirmed supervision/cleanup.
It reports technical results, provisional policy results and pending semantic review
separately. Every application/API replay uses labelled substitutes; live API/real-adapter
checks **1, 5, 10 remain deferred**. English-only rendering is separate from input
support. Structural checks cannot detect every semantic omission or prove DE/FR/IT/EN
understanding. No interpreter-suitability, multilingual or increment-completion claim.
