# v1.2.0 — offline harness correction; model-free Windows check only

The original single model startup allowance is **consumed**. No restart, replacement
attempt or ledger reset is authorized. `Run-Windows.ps1 -Execute` and supervised
capture are hard-blocked with `startup/allowance_consumed`, including direct function
invocation. The existing Windows attempt directory is read only. No zero ledger is
created from the reported missing `attempts.jsonl`.

[Owner-reported evidence](../../build/uc001-contract-local-v1_2_0/owner-reported-failure.json)
is a record of supplied facts, not reconstructed raw Windows files. Two exits were
confirmed (30488/56840); no accepted cases or listed case bodies, ValueError, and no
progress/ledger. The unchanged flow puts this before the first frozen generation;
the precise original failing check and original ancestry remain unknown. The separate
probe reproduced a Python parent different from PowerShell.

## Corrections

`PythonOwnership.cs` starts the installed venv redirector suspended, assigns the
existing kill-on-close job **before its first instruction**, then resumes it. The
interpreter consequently inherits that job. Native enumeration requires exactly
the intended redirector and its direct child, with explicit venv/base executable
paths, PID/creation-time identities and membership in that exact job. A model server,
when present in retained orchestration, is the only additional allowed member.
Held process handles prevent PID reuse from redirecting exit confirmation.
Both Python processes are rechecked and cleaned up; missing identity or unconfirmed
exit fails. No arbitrary ancestor search or usage/order-based selection.

Python independently checks live process identities and the exact two-link ancestry
against the supervisor proof delivered through its owned stdin pipe. The supervisor
establishes exact job membership using native queries. No job handle is inherited or
duplicated into Python, so it cannot defeat kill-on-last-job-handle-close deadlines.
`Check-Windows.ps1` uses these same corrected paths with a harmless waiting Python
worker, deliberately closes the job, then confirms both exits. It does not run an
interpreter request, create a model attempt or send HTTP.

[Pinned source evidence](PINNED-SOURCE.md) distinguishes the -1 **reported task default**,
CLI fallback and the unchanged adapter's explicit 3072-token request. Full verification
requires separate CLI/request evidence; it never blindly accepts -1. The saved receipt
check reports missing historical CLI evidence honestly. All other runtime/offload/
sampling/context checks and every time/resource/output limit are preserved.
Fixed stage/reason codes identify ownership, settings, output-limit, worker, deadline
and cleanup failures without raw exception text, credentials or prompts.

## Owner-operated handoff

Download [model-free-harness-correction.zip](../../build/uc001-contract-local-v1_2_0/model-free-harness-correction.zip)
and [SHA256SUMS.txt](../../build/uc001-contract-local-v1_2_0/SHA256SUMS.txt) into
`C:\ResolenaExperiments\uc001-contract-local-v1_2_0-handoff`.
Charge actual transfers against the existing cumulative download allowance; no reset,
dependency acquisition or reinstallation. Preserve every earlier extraction and ZIP.
In 64-bit Windows PowerShell 5.1, verify and **fully extract** once:

```powershell
$ErrorActionPreference = 'Stop'
$Incoming = 'C:\ResolenaExperiments\uc001-contract-local-v1_2_0-handoff'
$Archive = Join-Path $Incoming 'model-free-harness-correction.zip'
$Rows = @(Get-Content -LiteralPath (Join-Path $Incoming 'SHA256SUMS.txt') | Where-Object { $_ -match '^[0-9a-f]{64}  build/uc001-contract-local-v1_2_0/model-free-harness-correction\.zip$' })
if ($Rows.Count -ne 1 -or (Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Rows[0].Substring(0,64)) { throw 'Package hash mismatch; stop' }
$Root = 'C:\ResolenaExperiments\uc001-contract-local-v1_2_0'
if (Test-Path -LiteralPath $Root) { throw 'Destination exists; preserve it and stop' }
Expand-Archive -LiteralPath $Archive -DestinationPath $Root
```

Then run this **one model-free verification command** (process-only execution policy):

```powershell
& "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy RemoteSigned -File 'C:\ResolenaExperiments\uc001-contract-local-v1_2_0\scripts\uc001_contract_local_v1_2_0\Check-Windows.ps1' -SavedReceipt 'C:\ResolenaExperiments\uc001-contract-runs\bda2015c0ffbe89ab1a612fb4003b2b12f254871cf32f2e47dbbbe9d45cf0f52\windows-receipt.json'
```

Expected: `model_free_harness_checks_passed`, verified identities for redirector and
actual Python, compatible saved settings, confirmed exits, `startup_authorized:false`
and `model_attempt_ledger_touched:false`. An old receipt without launch arguments
must report `cli_execution_verified:false`; success does not erase that gap. Failure
or unconfirmed cleanup exits nonzero. Return only `result.json`, `worker-result.json`
and `cleanup.json` from the fresh `scripts\uc001_contract_local_v1_2_0\results\<GUID>`
directory. Keep any logs local. Do not modify or rerun the original model attempt.

Bound: at most 60 seconds overall, a separate 45-second job-close timer and retained
5-second exit waits. Only the check's own redirector/interpreter are terminated.
Native effects: Add-Type compiles retained/new C# (possible temporary compiler files);
Win32 process/pipe/handle/job and NtQueryInformationProcess calls, process metadata
reads, restrictive result-directory ACLs, and two harmless owned Python processes.
No model, GPU workload/counter check, port probe, tunnel or network request.

Original model/runtime pins, prompt/schema/14 exposed inputs, all review bytes/hash
bindings and semantic deferral remain unchanged. Qualified review stays pending and
`expected_meanings_approved:false`. Replay has no live credit for cases 1/5/10.
Windows native execution of this correction is pending; Codespace synthetic tests
and C# layout/compilation cannot prove it. Priority 3 partial; Phase 3 in-progress.
