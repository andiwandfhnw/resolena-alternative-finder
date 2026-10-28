# v1.2.2 — model-free console-helper ownership correction

Separate correction of the owner-reported v1.2.1 `ownership/unexpected_owned_process`
at `candidate_constraints`. The candidate was `C:\Windows\System32\conhost.exe`,
parented to redirector 29444, not an identified interpreter. [Reported facts](../../build/uc001-contract-local-v1_2_2/owner-reported-v1_2_1-failure.json)
are owner-pasted evidence, not reconstructed raw files. Prior packages/receipts remain
unchanged. No surviving interpreter or zero-generation ledger is inferred.

## Binding and cleanup

Native enumeration accounts for every observed member as the existing redirector,
optional existing server, exactly one pinned Python interpreter, or at most one console
helper. Python remains the exact pinned base executable, a direct child of the verified
venv redirector, with matching creation time, fresh identity and membership in this job.
The helper must have the exact system-directory `conhost.exe` path obtained from the
native system directory, a verified redirector/interpreter parent, creation no earlier
than that parent, stable held-handle identity and membership in this exact job. A basename,
PID, enumeration order, arbitrary ancestor or image label alone never establishes trust.
Unknown members, duplicate helpers/interpreters and changed identities fail.

A helper before Python is retained for cleanup but returns `interpreter_pending`; the
existing 20 ms polling, 45-second ownership/job deadline and 60-second overall bound
remain unchanged. Success still requires one fully verified interpreter and Python-side
fresh validation of all role identities and the complete exact member set. Native binding
and Python validation both use these roles, with no fixed total-process count.

Verified helper handles/identities survive incomplete binding. Job closure is followed by
held-handle exit checks for redirector, interpreter and every verified helper, retaining the
existing 5-second waits. An unidentified interpreter remains `not_identified/unavailable`;
an identified process with unconfirmed exit remains `identified/unconfirmed`. Unaccounted
observed job PIDs, missing identities or unconfirmed exits fail cleanup. No cleanup by name
or reopened guessed PID. Primary, cleanup and deadline failures remain independent.
Raw exception details, observed paths and process logs remain in the private subtree.

## One owner-operated model-free Windows handoff

Download [model-free-console-helper-correction.zip](../../build/uc001-contract-local-v1_2_2/model-free-console-helper-correction.zip)
and [SHA256SUMS.txt](../../build/uc001-contract-local-v1_2_2/SHA256SUMS.txt) into
`C:\ResolenaExperiments\uc001-contract-local-v1_2_2-handoff`. Charge actual transfers
to the existing cumulative download allowance; no reset or additional dependencies.
Open **64-bit Windows PowerShell 5.1**, verify the archive and fully extract into a new
directory (do not overlay an earlier package):

```powershell
$ErrorActionPreference = 'Stop'
$Incoming = 'C:\ResolenaExperiments\uc001-contract-local-v1_2_2-handoff'
$Archive = Join-Path $Incoming 'model-free-console-helper-correction.zip'
$Rows = @(Get-Content -LiteralPath (Join-Path $Incoming 'SHA256SUMS.txt') | Where-Object { $_ -match '^[0-9a-f]{64}  build/uc001-contract-local-v1_2_2/model-free-console-helper-correction\.zip$' })
if ($Rows.Count -ne 1 -or (Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Rows[0].Substring(0,64)) { throw 'Package hash mismatch; stop' }
$Root = 'C:\ResolenaExperiments\uc001-contract-local-v1_2_2'
if (Test-Path -LiteralPath $Root) { throw 'Destination exists; preserve it and stop' }
Expand-Archive -LiteralPath $Archive -DestinationPath $Root
```

Then execute **once**, without a model or capture:

```powershell
& "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy RemoteSigned -File 'C:\ResolenaExperiments\uc001-contract-local-v1_2_2\scripts\uc001_contract_local_v1_2_2\Check-Windows.ps1' -SavedReceipt 'C:\ResolenaExperiments\uc001-contract-runs\bda2015c0ffbe89ab1a612fb4003b2b12f254871cf32f2e47dbbbe9d45cf0f52\windows-receipt.json'
```

Uses the existing `C:\ResolenaExperiments\uc001-validator-env\Scripts\python.exe`,
unchanged saved-receipt checks and a harmless owned Python redirector/worker pair;
Windows may create the validated console helper. Results go into a new GUID directory
under this revision's `results/`, outside the original model attempt and ledger.
On success expect `model_free_harness_checks_passed`, a complete ownership proof with
`console_helpers` (empty if none), worker checks, job closure and all owned exits confirmed.
A helper alone must expire without proof; missing identity, unknown members or unconfirmed
cleanup remain nonzero failures. Stop after any result; no automatic retry.

Return only `result.json`, `cleanup.json`, and `worker-result.json` if present. Keep
`private/` local: bounded raw exceptions, full observed paths and process stdout/stderr.
No inference, HTTP, GPU workload, SSH, installation, credential access or model-attempt
write occurs. Native effects: Add-Type compilation (possible temporary compiler files),
existing Win32 process/pipe/job/handle calls, NtQueryInformationProcess, native system-path
lookup and restrictive result ACLs. Cleanup is limited to this check's owned job/handles.

## Evidence and limits

[Offline verification](../../build/uc001-contract-local-v1_2_2/verification.json) covers the
actual role policy with explicit synthetic identities, Python ownership checks, supervised
failure/deadline/cleanup substitutes and compilation/layout. This is **not Windows native
verification**. The next owner-operated check must establish actual console/interpreter
binding and exit behavior. No model/GPU readiness or semantic acceptance is established.
All model/runtime pins, prompts, schema, 14 inputs, review bindings and resource/time limits
remain unchanged. The original startup allowance is consumed; model/capture entry points
remain blocked. Qualified semantic review remains pending/false. Priority 3 partial;
Phase 3 DEVELOP in-progress.
