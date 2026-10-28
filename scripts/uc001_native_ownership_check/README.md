# Model-free Windows ownership/cleanup check

Separate diagnostic for the unchanged v1.3.0 execution bundle. Priority 3 remains
partial; Phase 3 in-progress. Preparation/offline verification only: no Windows
native result has been collected here. Recorded SSH/gh/port checks are not repeated.

Download `build/uc001-native-ownership-check/windows-native-ownership-check.zip`
and extract its two files into a fresh
`C:\ResolenaExperiments\uc001-native-ownership-check` directory. Keep the complete
existing v1.3.0 extraction at `C:\ResolenaExperiments\uc001-execution-v1_3_0`.
Do not overlay either frozen bundle or place this diagnostic in its attempt directory.

From **64-bit Windows PowerShell 5.1**, run exactly:

```powershell
& "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -NonInteractive -ExecutionPolicy RemoteSigned -File 'C:\ResolenaExperiments\uc001-native-ownership-check\Check-NativeOwnership.ps1' -BundleDirectory 'C:\ResolenaExperiments\uc001-execution-v1_3_0'
```

RemoteSigned is process-only; managed policy/FullLanguage restrictions still stop.
The check pins the v1.3.0 freeze and hashes only its two small helper sources,
`Common.ps1` and `ProcessTools.cs`. It reads/hashes no model or runtime assets.

The supervisor launches one diagnostic PowerShell worker. That worker uses the
existing `Initialize-ContractProcessSupport`, `New-ContractJob` and
`Start-ContractProcess` to launch a harmless, hidden PowerShell child that sleeps
for ten seconds without spawning descendants. The real
`Get-ContractProcessIdentity` compares the retained child's PID/UTC creation time
with a fresh process lookup and a second read. Within two seconds of child launch,
it deliberately throws a diagnostic abort, then invokes the unchanged
`Complete-ContractCleanup`: close the owned job and confirm the child exit with
the original five-second wait. This tests the abort/finally path without invoking
launcher initialization, resource acceptance or a model attempt.

The overall budget is **60 seconds**: the supervisor stops waiting at 45 seconds
including preparation, reserving five seconds for owned worker exit, five for
owned child cleanup and five for records. Worker preparation has a 35-second guard.
On timeout/failure, only the retained worker handle may be terminated. Its exit
also closes its non-inheritable kill-on-close job. If child cleanup needs a further
attempt, a fresh PID/creation-time match is mandatory before terminating that
retained process handle. No matching by order/name or PID alone. A missing identity
after a startup attempt is **unconfirmed cleanup and failure**, including the
narrow native start/assignment failure window; no success is inferred from job
closure alone. Further cleanup never converts an earlier failure into a pass.

Expected success: exit code **0**, `outcome: native_ownership_cleanup_passed`,
`expected_abort_exercised: true`, job created/closed, exactly one matching child
exit confirmed, and supervisor exit confirmed. Any query, identity, compilation,
job, exit-confirmation or deadline failure returns exit **1** with failure evidence.
Preserved output lives under `results\<new GUID>\`: `result.json`, worker identity,
logs/`cleanup.json`/result, supervisor cleanup and any recovery record. Never reuse
or delete earlier result directories. No model-attempt ledger is read or written.

Native effects: `Add-Type` compiles/loads the existing `ProcessTools.cs` and loads
System.Net.Http; it makes no HTTP requests. Windows PowerShell 5.1 may create or
retain compiler/source/assembly files under `%TEMP%`. No compiler is installed.
Native calls are the existing kernel32 job create/configure/assign/close calls,
plus .NET Windows process creation, PID/creation-time/handle reads, waits and
termination of owned processes on failure. The frozen sources are loaded, not
modified. AdapterIdentity.cs, DXGI, CIM/WDDM and GPU workloads are not invoked.

This can establish native ownership/lifetime/job closure and exit confirmation
only. **Real owned-GPU counter availability, adapter attribution during allocation,
model allocation and authorized startup resource checks remain pending.** There
is no GPU measurement, fabricated zero, model/runtime execution or semantic evidence.

Offline checks (Codespaces Bash; substitute objects only):

```bash
.venv/bin/python -m pytest -q tests/unit/test_execution_monitor.py tests/unit/test_preflight_adapter_association.py tests/unit/test_contract_run_controls.py
```
