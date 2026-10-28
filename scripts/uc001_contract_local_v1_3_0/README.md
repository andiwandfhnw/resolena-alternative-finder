# Proposed additional technical-feasibility attempt — v1.3.0

**Execution is blocked pending explicit owner approval of this additional allowance.**
The bundled `approval.pending.json` is false. Preparing this handoff does not approve
startup. Do not repeat the passed v1.2.2 model-free check.

[Owner-pasted v1.2.2 receipts and closure](../../build/uc001-contract-local-v1_2_2/owner-results/results_2026_10_18/verification.json)
verify the tested native redirector/interpreter/system-console-helper binding, Python
ownership validation, job closure and all three owned exits in 1667 ms. Harness debugging
is closed. This does not establish model/GPU readiness or semantic correctness. Historical
missing CLI evidence stays unavailable; it is not investigated again.

## Exact proposal

- Original consumed identity: `bda2015c0ffbe89ab1a612fb4003b2b12f254871cf32f2e47dbbbe9d45cf0f52`.
- Proposed additional identity: `3efca8db7f356fe00672ecf2a0607c2b57c017fafedca61e85778611abd1afe8`.
- One additional startup, at most 14 generations in unchanged case order; no retry,
  tuning, replacement model, asset/dependency downloads, SSH or held-out access.
- Same Qwen3-8B Q8_0 / llama.cpp b11429 pins, prompt/schema/14 exposed inputs and sampling;
  context 8192, full 37-layer offload, request/CLI cap 3072. Reported task default -1
  remains distinct from those enforced limits.
- Same 2400-second total, 1500-second model, 90-second readiness and absolute supervised
  90-second per-response deadline including prompt-fit/shared validation/case checks.
  Independent owned-job timer, 1-second resource sampling, 20 ms phase polls and original
  owned-process cleanup/exit waits remain.
- Fresh start headroom: RAM 20 GiB, GPU 14 GiB, disk 6 GiB. Runtime floors RAM 4 GiB,
  GPU 2 GiB, disk 5 GiB; owned GPU cap 12 GiB, server RSS cap 16 GiB. Existing 1 GiB
  artifact budget split Windows/Codespace 512 MiB each; bounded bodies 262144 bytes.

The new directory links to the original without reading, resetting or reconstructing its
ledger. An existing additional-attempt directory stops execution. Reservation and
`startup-attempt.json` record provenance and exact executable/argv/command line **before**
startup; `startup-started.json` records returned process identity. A startup failure retains
its attempted-start record. The existing RunBudget records actual prospective generation
attempts before dispatch, without retries. No historical zero-generation receipt is created.

The verified v1.2.2 `PythonOwnership.cs`, `Python-Ownership.ps1`, `harness_checks.py` and
native deadline helper are copied unchanged. Launcher and capture both enforce the separately
bound approval record. Capture uses the unchanged shared adapter/domain/check_case_state and
corrected effective-settings validator, with validation before each next generation. Exact
requests/responses retain the existing explicit 49188-to-49187 transport injection, secret
scan and incomplete-private-capture policy. The server remains authenticated localhost only.
The new replay accounts for all helper exits and has no network fallback.

Technical and provisional policy results remain separate from qualified semantics. The
original partial DE/EN/dialect confirmations and all unapproved records retain their original
hash binding; review stays pending and `expected_meanings_approved:false`. DE/FR/IT/EN product
requirements remain unchanged. Replay uses labelled substitutes and receives no live
API/real-adapter credit for cases 1/5/10. No suitability or multilingual acceptance follows
from a technical pass. Priority 3 partial; Phase 3 DEVELOP in-progress. SSH/Support paused.

## One Windows sequence for review — do not execute before approval

Download [proposed-execution.zip](../../build/uc001-contract-local-v1_3_0/proposed-execution.zip)
and [SHA256SUMS.txt](../../build/uc001-contract-local-v1_3_0/SHA256SUMS.txt) to
`C:\ResolenaExperiments\uc001-contract-local-v1_3_0-handoff`. Source handoff transfers count
against the existing cumulative allowance; no balance reset or dependency acquisition.

The following is the complete **future owner-operated** sequence in 64-bit Windows
PowerShell 5.1. It intentionally stops with the blank approval reference. Only after explicit
approval of this exact additional allowance, replace that blank with its actual chat/date
reference. This creates a separate owner approval record outside the frozen bundle; it does
not rewrite the pending template or the earlier review. No approved receipt is supplied here.

```powershell
$ErrorActionPreference = 'Stop'
$OwnerApprovalReference = '' # Remains blank until explicit approval of this proposed allowance.
if ([string]::IsNullOrWhiteSpace($OwnerApprovalReference)) { throw 'Additional execution approval pending; stop' }
$Incoming = 'C:\ResolenaExperiments\uc001-contract-local-v1_3_0-handoff'
$Archive = Join-Path $Incoming 'proposed-execution.zip'
$Rows = @(Get-Content -LiteralPath (Join-Path $Incoming 'SHA256SUMS.txt') | Where-Object { $_ -match '^[0-9a-f]{64}  build/uc001-contract-local-v1_3_0/proposed-execution\.zip$' })
if ($Rows.Count -ne 1 -or (Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Rows[0].Substring(0,64)) { throw 'Package hash mismatch; stop' }
$Root = 'C:\ResolenaExperiments\uc001-contract-local-v1_3_0'
if (Test-Path -LiteralPath $Root) { throw 'Extraction destination exists; preserve it and stop' }
Expand-Archive -LiteralPath $Archive -DestinationPath $Root
$Scripts = Join-Path $Root 'scripts\uc001_contract_local_v1_3_0'
$Approval = Get-Content -LiteralPath (Join-Path $Scripts 'approval.pending.json') -Raw | ConvertFrom-Json
$Approval.approved = $true
$Approval.approval_reference = $OwnerApprovalReference
$Approval.freeze_sha256 = (Get-FileHash -LiteralPath (Join-Path $Scripts 'freeze.json') -Algorithm SHA256).Hash.ToLowerInvariant()
$ApprovalDirectory = 'C:\ResolenaExperiments\uc001-contract-approvals'
if (-not (Test-Path -LiteralPath $ApprovalDirectory)) { $null = New-Item -ItemType Directory -Path $ApprovalDirectory }
$ApprovalPath = Join-Path $ApprovalDirectory ($Approval.attempt_identity + '.json')
if (Test-Path -LiteralPath $ApprovalPath) { throw 'Approval record already exists; preserve it and stop' }
[IO.File]::WriteAllText($ApprovalPath, ($Approval | ConvertTo-Json -Depth 8))
& "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy RemoteSigned -File (Join-Path $Scripts 'Run-Windows.ps1') -Execute -Review (Join-Path $Scripts 'partial-expectations-review.json') -Approval $ApprovalPath
if ($LASTEXITCODE -ne 0) { throw 'Attempt stopped; preserve all results, no retry' }
```

Uses only the verified `C:\ResolenaExperiments\uc001-validator-env\Scripts\python.exe`
and existing dependencies. Inside the launcher, approval/source/environment checks precede
fresh retained ZIP/model/52-runtime-file integrity checks, verified v1.2.0-policy DXGI/CIM/PCI/
LUID capacity/measurement/headroom checks and port 49187 availability. Startup then requires
protected-endpoint authentication, exact owned loopback listener, positive real owned-GPU
allocation, monitoring and current effective settings. Missing/invalid data still stops.
The passed model-free check is not repeated and does not replace these fresh live checks.

All results reside at
`C:\ResolenaExperiments\uc001-contract-runs\3efca8db7f356fe00672ecf2a0607c2b57c017fafedca61e85778611abd1afe8`.
After any stop, preserve the whole private Windows attempt and stop without retry. Share
only the scanned `export/` directory; retain API keys, raw process logs, incomplete bodies
and private exceptions locally. Launcher cleanup verifies every retained helper alongside
server/redirector/interpreter; a cleanup failure prevents completion and stays independent
from the primary stop/deadline. Add-Type may create temporary compiler files; Win32/Nt native
process/job/DXGI/resource calls are unchanged and cleanup touches only owned processes.

For a complete export, copy only `export/` into Codespace (manual file transfer; no SSH),
within the unchanged Codespace artifact sub-budget, then run the matching replay:
`.venv/bin/python -m scripts.uc001_contract_local_v1_3_0.replay --export <copied-export> --output build/test-only/<new-replay-directory>`.
A stopped/incomplete capture cannot become a successful replay. This is a replay substitute,
not completion of deferred live integration or semantic validation.

[Offline verification and changed files](../../build/uc001-contract-local-v1_3_0/verification.json).
No model, inference, transport, installation or Git delivery occurred during preparation.
