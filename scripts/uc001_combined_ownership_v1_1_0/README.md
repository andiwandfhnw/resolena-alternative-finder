# Combined ownership correction 1.1.0 — model-free only

The [owner-pasted Windows transcript](../../build/uc001-combined-ownership-v1_1_0/owner-evidence/provenance.json)
shows a system conhost child of the sleeping server stand-in, a system conhost child
of the venv redirector, and the base Python child of that redirector. All five observed
job members exited. The historical result remains failed/`cleanup_confirmed:false`:
interpreter role classification failed. Earlier model-run helper legitimacy remains unknown.
All previous packages/evidence stay unchanged. Both model-startup allowances remain consumed.

The native binder and actual Python ownership validator now allow at most one exact
system conhost per verified branch: server, and Python (redirector or interpreter).
Each requires its verified parent lifetime and exact job membership. The server has a
full identity in the proof, checked against the held process, launch identity, trusted
exact executable path and supervisor ancestry. A PID alone is insufficient. Unknown
members, duplicate branch helpers/interpreters, changed identities and incomplete proofs
still stop. Observed handles remain available for cleanup independently of approved roles.
The cleanup proof includes the server creation time as well as both helpers' lifetimes.

This separate check migrates its proof producer, PowerShell bridge, Python worker and
cleanup consumer together. Frozen model launch/capture/replay packages remain historical;
this archive contains no model launcher, capture or replay execution handoff.

## One Windows sequence

Download [combined-ownership-check.zip](../../build/uc001-combined-ownership-v1_1_0/combined-ownership-check.zip)
and [SHA256SUMS.txt](../../build/uc001-combined-ownership-v1_1_0/SHA256SUMS.txt) into
`C:\ResolenaExperiments\uc001-combined-ownership-v1_1_0-handoff`. Use the already verified
venv at `C:\ResolenaExperiments\uc001-validator-env`; no setup or dependencies are acquired.
In **64-bit Windows PowerShell 5.1**, verify the archive, fully extract into a fresh
location and run once:

```powershell
$ErrorActionPreference = 'Stop'
$Incoming = 'C:\ResolenaExperiments\uc001-combined-ownership-v1_1_0-handoff'
$Archive = Join-Path $Incoming 'combined-ownership-check.zip'
$Rows = @(Get-Content -LiteralPath (Join-Path $Incoming 'SHA256SUMS.txt') | Where-Object { $_ -match '^[0-9a-f]{64}  build/uc001-combined-ownership-v1_1_0/combined-ownership-check\.zip$' })
if ($Rows.Count -ne 1 -or (Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Rows[0].Substring(0,64)) { throw 'Package hash mismatch; stop' }
$Root = 'C:\ResolenaExperiments\uc001-combined-ownership-v1_1_0'
if (Test-Path -LiteralPath $Root) { throw 'Destination exists; preserve it and stop' }
Expand-Archive -LiteralPath $Archive -DestinationPath $Root
& "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -NonInteractive -ExecutionPolicy RemoteSigned -File (Join-Path $Root 'scripts\uc001_combined_ownership_v1_1_0\Check-CombinedOwnership.ps1')
```

The production `Start-ContractProcess` and `Start-OwnedPython` primitives launch a sleeping
native-system PowerShell server stand-in and the installed venv/base interpreter in one
owned kill-on-close job. Native binding requires both observed helper branches. Its proof
is sent over owned stdin to the actual `verify_python_ownership` function; its fresh Win32
identity queries include the server. The trusted server path comes from Windows, never
from the proof. The worker stays alive after writing its result. The supervisor requires
that result and rebinds native identity/membership before job closure and exit confirmation.
Native code establishes exact job membership; Python verifies those proof members and
fresh identities. Python does not independently query the supervisor's job handle.
The unchanged adapter/domain imports are included only because the shared harness module
imports them; no requests or application cases execute, and there is no substitute validator.

Expect `combined_native_python_and_cleanup_passed`, `python_validator.outcome` equal to
`python_combined_ownership_verified`, a full server identity, both helpers, no primary/
cleanup/deadline/observation failures and confirmed exits for all five identities. Native-only
success cannot pass. Missing Python results/identity/job evidence or unconfirmed exits fail.
Return **result.json, python-result.json, ownership.json, observation.json and cleanup.json**
from `scripts\uc001_combined_ownership_v1_1_0\results\<fresh GUID>`; keep `private/` local.
On any failure, preserve the directory and stop; no automatic retry.

Limits unchanged from the separate reproduction: 10-second setup check, independent native
job closure by 30 seconds from entry, 20 ms polling/200 ms initial member stability,
45-second acceptance deadline, <=5-second base exit waits and <=5-second/remaining-budget
retained exit waits. Compilation/native query time is checked after return, not claimed
cancellable. Results use owner/SYSTEM ACLs. Add-Type compiles C# and may leave compiler files
under `%TEMP%`; kernel32 process/job/pipe/image/time calls and NtQueryInformationProcess
execute, as do Python ctypes identity queries. Only owned job/held processes are cleaned up.
No sockets, GPU measurements, model/runtime/asset checks, ledger access or process-name kills.
Source transfer bytes count against the existing cumulative download allowance; no reset.

[Offline verification](../../build/uc001-combined-ownership-v1_1_0/verification.json) is distinct
from pending Windows native verification. This check establishes neither historical model
helper legitimacy nor model/GPU readiness, language understanding or semantic acceptance.
Qualified semantic review stays pending/false. Priority 3 partial; Phase 3 DEVELOP in-progress.
