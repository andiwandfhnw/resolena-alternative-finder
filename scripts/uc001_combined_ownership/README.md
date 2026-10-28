# Combined server/Python ownership reproduction — model-free

The owner reports that the additional v1.3.0 startup occurred and stopped at
`ownership/console_helper_ambiguous`. Both original and additional model allowances are
consumed. No new startup/inference is authorized, and no model-attempt ledger is read,
created or reset here. [Reported facts](../../build/uc001-combined-ownership/owner-reported-v1_3_0-failure.json)
are not reconstructed raw receipts; failed-run helper identities/ancestry were not supplied.
The successful v1.2.2 native check covered the Python branch, not this combined job.

## Supported correction and remaining evidence

The copied native binder previously disposed temporary observed handles on classification
failure. This separate correction retains each opened observation before identity/job reads
and role classification. Verified exact-job identities remain available for held-handle
exit confirmation even if classification fails. Missing handle/identity/job verification
and unconfirmed exits still fail; no process is killed by name or guessed PID. Cleanup
labels unclassified observations `role_approved:false`. It cannot approve unknown roles or
turn a missing approved interpreter identity into successful ownership/cleanup. Known
interpreter/helper handles are waited on only once when also present in observations.

**The console-helper role policy is unchanged pending actual Windows reproduction.**
Native AccountMembers still rejects two helpers globally and helpers parented only to the
server; the copied Python validator also remains closed. Offline synthetic tests reproduce
both limitations. They do not establish that the failed run's helpers were legitimate.
No new helper count or server-ancestry trust is introduced without the required Windows
observations. The Codespace is Linux, so native Windows ancestry has not been reproduced
here. This handoff is the evidence-producing step before that policy correction.

## One owner-operated Windows check

Download [combined-ownership-reproduction.zip](../../build/uc001-combined-ownership/combined-ownership-reproduction.zip)
and [SHA256SUMS.txt](../../build/uc001-combined-ownership/SHA256SUMS.txt) into
`C:\ResolenaExperiments\uc001-combined-ownership-handoff`. Source transfers count against
the existing cumulative allowance; no reset, dependency or model/runtime downloads.
In **64-bit Windows PowerShell 5.1**, verify, fully extract into a new directory and run once:

```powershell
$ErrorActionPreference = 'Stop'
$Incoming = 'C:\ResolenaExperiments\uc001-combined-ownership-handoff'
$Archive = Join-Path $Incoming 'combined-ownership-reproduction.zip'
$Rows = @(Get-Content -LiteralPath (Join-Path $Incoming 'SHA256SUMS.txt') | Where-Object { $_ -match '^[0-9a-f]{64}  build/uc001-combined-ownership/combined-ownership-reproduction\.zip$' })
if ($Rows.Count -ne 1 -or (Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Rows[0].Substring(0,64)) { throw 'Package hash mismatch; stop' }
$Root = 'C:\ResolenaExperiments\uc001-combined-ownership'
if (Test-Path -LiteralPath $Root) { throw 'Destination exists; preserve it and stop' }
Expand-Archive -LiteralPath $Archive -DestinationPath $Root
& "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -NonInteractive -ExecutionPolicy RemoteSigned -File (Join-Path $Root 'scripts\uc001_combined_ownership\Check-CombinedOwnership.ps1')
```

This creates a single owned kill-on-close job in the same PowerShell supervisor as the
production launcher. It uses unchanged `ContractProcesses.Start` / `Start-ContractProcess`
to launch native system PowerShell sleeping harmlessly as the server stand-in, then the
production `ContractPython.Start` / `Start-OwnedPython` path to launch the installed venv
redirector and actual Python interpreter running only `idle.py`. Same launching flags,
redirected streams and job-assignment paths; different harmless server executable, no
model binary. This tests combined launch mechanics, not the failed model's unseen helpers.

After the Python readiness hint and a bounded 200 ms stable-member wait, native fresh
identity/job reads record all observed members and ancestry, then the actual unchanged
role classifier is invoked once. Observation snapshots are updated after a rejection,
before cleanup. Unknown image paths/raw exceptions/logs stay private. Parent observations
are evidence labels, not approval of a server or helper role. Idle Python uses standard
library readiness only; this does not rerun application, semantic or saved-CLI checks.

Budget: setup checked at 10 seconds; an independent native timer closes the owned job by
30 seconds from check entry. Observation polling is 20 ms. Existing base server/redirector
exit waits remain at most 5 seconds each; retained-observation waits are capped at 5 seconds
and the remaining 45-second check budget. Exceeding that budget fails, with separate primary,
cleanup and deadline records. Owned process lifetime is guarded independently of PowerShell;
setup/compilation/native-query wall time is checked after calls, not claimed cancellable.
There are no retries, added workloads, sockets, HTTP, GPU probes or model budgets.

Results are preserved under `scripts\uc001_combined_ownership\results\<new GUID>`.
Return **result.json, observation.json and cleanup.json**; keep `private/` local. Expect a
nonzero exit if the global helper cap/server-parent restriction is reproduced. The result
records `reported_ambiguity_reproduced` and all retained exit observations. Even if every
observed native identity exits, the missing approved interpreter role remains a cleanup
failure under the unchanged policy. A binding pass means only this observed harmless setup
passed the current native policy; it does not establish failed-run helper legitimacy,
Python/application-contract integration, model/GPU readiness or semantic suitability.
Missing snapshots/identities or unconfirmed cleanup remain explicit failures. Stop after
this one result; do not rerun or propose another model attempt from it automatically.

Native effects: Windows Add-Type compiles the copied native sources and may create compiler
files under `%TEMP%`; existing kernel32 process/pipe/job/handle/creation/image calls and
NtQueryInformationProcess execute. The native system path is used. Restrictive result ACLs
and cleanup are confined to owned handles/job; no installations, asset hashing, settings/
driver changes, SSH/Support, inference or held-out access. Earlier source/packages/receipts,
model settings/frozen cases/resource/time limits and application contracts remain unchanged.
Priority 3 partial; Phase 3 DEVELOP in-progress. [Offline verification](../../build/uc001-combined-ownership/verification.json).
