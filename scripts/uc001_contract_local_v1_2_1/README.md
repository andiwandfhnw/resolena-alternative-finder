# v1.2.1 — model-free failure reporting and binding observation

Preserves the failed v1.2.0 source/ZIP/evidence. The owner reports ownership/worker null,
680 ms, job closure and redirector 48020 exit confirmed, but no interpreter identity
or confirmed interpreter exit. [Reported facts](../../build/uc001-contract-local-v1_2_1/owner-reported-v1_2_0-failure.json)
are not reconstructed raw files. Neither a surviving interpreter nor zero generations
is inferred. The original model startup allowance remains consumed; every model/capture
entry remains blocked. Priority 3 partial; Phase 3 DEVELOP in-progress.

## Correction and evidence limit

`primary_failure`, `cleanup_failures` and `deadline_failures` are independent. The
compatibility `stop` field prefers the primary failure and cannot overwrite it with
cleanup or the overall deadline. Unknown exceptions yield fixed safe codes; recognized
native failures can include numeric Win32/NT status. Raw exception text is bounded to
4096 characters per private record. Process logs and full observed executable paths
are also private. Share only the sanitized result/worker/cleanup JSON, never `private/`.

Code inspection found a distinct binding/cleanup defect: a verified interpreter handle
could be retained before `LastProof` was assigned, but cleanup used only `LastProof`
to obtain its identity. The corrected binder retains a unique verified child's identity
independently before the remaining supervisor/proof checks. Cleanup waits on that held
handle even if full binding fails. Full ownership still requires every original check.
Unknown/ambiguous candidates never become accepted interpreters.

Cleanup distinguishes `identity_state:not_identified` / `exit_confirmation:unavailable`
from `identity_state:identified` / `exit_confirmation:unconfirmed`, and confirmed exits.
Missing identity is still a failure. No process is opened or terminated by name, guessed
PID, enumeration order or usage. Suspended start/job assignment, handle inheritance,
all identity/uniqueness checks, 45-second job timer, 60-second overall bound and 5-second
exit waits remain unchanged. No dependencies or model/runtime assets are acquired.

The initiating v1.2.0 Windows failure cannot be recovered from the supplied summary:
its first exception code/native status and failing binding step were overwritten.
This correction does not claim that the separate identity-retention defect caused it.
One prepared check captures those observations plus job member PIDs, candidate identity/
image classification, independent cleanup and bounded private diagnostic detail.

## Smallest next Windows action — one prepared model-free check

Download [model-free-reporting-correction.zip](../../build/uc001-contract-local-v1_2_1/model-free-reporting-correction.zip)
and [SHA256SUMS.txt](../../build/uc001-contract-local-v1_2_1/SHA256SUMS.txt) into
`C:\ResolenaExperiments\uc001-contract-local-v1_2_1-handoff`.
Charge actual transfers to the existing cumulative allowance; no reset or installation.
In 64-bit Windows PowerShell 5.1, verify and fully extract into a new directory:

```powershell
$ErrorActionPreference = 'Stop'
$Incoming = 'C:\ResolenaExperiments\uc001-contract-local-v1_2_1-handoff'
$Archive = Join-Path $Incoming 'model-free-reporting-correction.zip'
$Rows = @(Get-Content -LiteralPath (Join-Path $Incoming 'SHA256SUMS.txt') | Where-Object { $_ -match '^[0-9a-f]{64}  build/uc001-contract-local-v1_2_1/model-free-reporting-correction\.zip$' })
if ($Rows.Count -ne 1 -or (Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Rows[0].Substring(0,64)) { throw 'Package hash mismatch; stop' }
$Root = 'C:\ResolenaExperiments\uc001-contract-local-v1_2_1'
if (Test-Path -LiteralPath $Root) { throw 'Destination exists; preserve it and stop' }
Expand-Archive -LiteralPath $Archive -DestinationPath $Root
```

Then the one model-free command, prepared for owner operation only:

```powershell
& "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy RemoteSigned -File 'C:\ResolenaExperiments\uc001-contract-local-v1_2_1\scripts\uc001_contract_local_v1_2_1\Check-Windows.ps1' -SavedReceipt 'C:\ResolenaExperiments\uc001-contract-runs\bda2015c0ffbe89ab1a612fb4003b2b12f254871cf32f2e47dbbbe9d45cf0f52\windows-receipt.json'
```

It reuses the installed venv and unchanged saved-receipt checks. It starts only a harmless
owned Python redirector/worker pair and exercises job-close cleanup, without HTTP/model/
GPU/transport work or model-attempt writes. It creates a fresh GUID result directory
under this revision's `results/`. Return `result.json`, `cleanup.json`, and
`worker-result.json` only if present. If failed, stop without retry. Missing interpreter
identity or unconfirmed cleanup remains nonzero failure. Missing historical CLI evidence
still stays unverified. No semantic/interpreter acceptance follows from a technical pass.

Native effects remain Add-Type compilation (possible temporary compiler files), Win32
process/pipe/job/handle calls and NtQueryInformationProcess, with restrictive result ACLs
and cleanup confined to this check's owned job/handles. No Windows execution occurred
during preparation; offline tests use explicit substitutes and C# compilation/layout only.
All frozen model/runtime/prompt/schema/cases/review bindings, resource limits and consumed
allowance remain unchanged. Qualified semantic review is pending/false; live cases 1/5/10
retain no replay credit. [Offline verification](../../build/uc001-contract-local-v1_2_1/verification.json).
