# Windows-local capture / Codespace replay — preparation only

Replaces the planned transport-based feasibility execution; no additional startup
or generation allowance. Priority 3 partial; Phase 3 DEVELOP in-progress. No live
execution is authorized by this implementation. SSH/Support work remains paused.

Both supplied Windows receipts are [recorded separately](../../build/uc001-contract-local/owner-results/)
as owner-pasted JSON, not byte-identical original files. They establish Python
3.12.10 x64/shared-validator compatibility only. Reported allowance remaining:
**46,845,816 bytes**; no dependencies acquired here and no allowance reset.

## Reuse and controls

The v1.3.0 files and application code remain unchanged. `config.json` references
the retained configuration; the new freeze pins this orchestration and its exact
parent. Prompt/schema/14 exposed cases, model/runtime pins, thresholds and all
limits remain the same. No recognizer or country/preferences enter model requests.
The shared adapter sees port 49188; an explicit `BaseTransport` maps only approved
paths to authenticated Windows **127.0.0.1:49187**, with proxy/redirect/retry disabled.

`Run-Windows.ps1` reuses v1.3.0 Common/ProcessTools/identity/monitoring/cleanup and
startup arguments. Qualified expectations review bound to the **new freeze**
is checked before startup. Copy the retained review template outside the frozen
tree, obtain actual qualified DE/FR/IT/EN approval, and bind reviewer provenance
to the printed local freeze hash. No approval is supplied or manufactured here.

The original attempt directory/identity and create-once `RunBudget` remain binding.
One server and one Python worker share the native kill-on-close job. Python waits
for `begin N`; PowerShell arms its monotonic 90-second watchdog **before** sending
that command. Prompt-fit, HTTP, shared decoding/domain validation and case-state
validation all precede `validated N`. Late validation fails; only a live worker
with unchanged PID/creation time gets `advance N`. Failure closes the owned job
and confirms both owned exits. The watchdog polls independently of Python/HTTP;
resource sampling remains at the retained one-second interval. A small managed
`DeadlineGuard.cs` timer independently closes the same owned job through the
unchanged ProcessTools `CloseHandle` method if PowerShell blocks in an OS query.
Timed expiry and normal cleanup coordinate one close attempt; a failed close or
unconfirmed exit fails. Native Windows timing/measurement/termination behavior
still requires authorized execution; managed synthetic timer tests are not that evidence.
Progress reads permit atomic Windows replacement; final completion is reread after
observing worker exit, and still requires its successful exit code.

Each raw body is captured **before parsing**, capped at 262,144 bytes (including
partial bodies); the retained decoded-body cap also applies. There is no repair,
fallback, retry or automatic tuning. Incomplete, uninspectable encoded or
secret-bearing bodies remain in the private Windows attempt directory; only
complete scanned bodies and whitelisted headers go to `export`. The privacy scan
also checks decoded HTTP bodies and escaped JSON strings, without validating meaning.
Raw completeness stays separate from later decoding/contract failure. Never manually
copy `private`, server/worker logs, stdin or environment values to Codespace.
Only the `export` directory is transferable. It records the deferred live API
cases **1, 5 and 10**, supervisor acceptances, incomplete-body metadata and cleanup.
Artifact accounting includes private plus exported files under the original
512 MiB Windows cap. Imported captures and replay output together consume the
separate 512 MiB Codespace cap; the combined cap stays 1 GiB.

Native effects on future execution: v1.3.0 Add-Type C# compilation can create
temporary compiler files; DXGI/WDDM/CIM/registry reads, Win32 job/process calls,
owner/SYSTEM-only directory ACLs and two owned processes. No native calls, model
or network startup occur in offline synthetic tests. A zero GPU sample never
substitutes for a missing measurement; positive owned allocation is still required
at readiness. The earlier narrow GPU margin requires fresh checks before startup.

## Owner-operated handoff now: model-free verification only

Download [windows-local-source.zip](../../build/uc001-contract-local/windows-local-source.zip)
and [SHA256SUMS.txt](../../build/uc001-contract-local/SHA256SUMS.txt) to
`C:\ResolenaExperiments\uc001-contract-local-handoff`.
Charge the transferred bytes against the reported remaining allowance; do not
redownload dependencies or overwrite the previous setup/source directory.

In Windows PowerShell 5.1 x64, run only:

```powershell
$Incoming = 'C:\ResolenaExperiments\uc001-contract-local-handoff'
$Archive = Join-Path $Incoming 'windows-local-source.zip'
$Rows = @(Get-Content -LiteralPath (Join-Path $Incoming 'SHA256SUMS.txt') | Where-Object { $_ -match '^[0-9a-f]{64}  build/uc001-contract-local/windows-local-source\.zip$' })
if ($Rows.Count -ne 1 -or (Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Rows[0].Substring(0,64)) { throw 'Package hash mismatch; stop' }
if (Test-Path -LiteralPath 'C:\ResolenaExperiments\uc001-contract-local') { throw 'Extraction destination exists; preserve it and stop' }
Expand-Archive -LiteralPath $Archive -DestinationPath 'C:\ResolenaExperiments\uc001-contract-local'
& 'C:\ResolenaExperiments\uc001-validator-env\Scripts\python.exe' -I -X utf8 -B 'C:\ResolenaExperiments\uc001-contract-local\scripts\uc001_contract_local\capture.py' --verify-only
if ($LASTEXITCODE -ne 0) { throw 'Local preparation verification failed; stop without repair or retry' }
```

Expected: `local_preparation_verified`, local freeze SHA-256, review pending,
`startup_authorized:false`. No retained-asset hashes, port probe, model, generation,
native helper initialization or attempt-ledger creation. Stop and return that receipt.
Running `Run-Windows.ps1 -Execute -Review <qualified-review.json>` requires separate
live execution authorization; it is not the current handoff.

## Later Codespace replay

After a separately authorized capture and confirmed cleanup, copy **export only**
to a new directory under `build/test-only`. Use the existing Codespace environment:

```bash
PYTHONPATH=src:. .venv/bin/python -m scripts.uc001_contract_local.replay \
  --export build/test-only/windows-local-export \
  --output build/test-only/windows-local-replay
```

The replay transport requires exact captured requests and responses; no network
fallback exists. It reruns the unchanged adapter/domain/case validation, application
language policy and isolated synthetic-knowledge API/save routes. Every output
is labelled `replay_substitute`; cases 1/5/10 remain live API/real-adapter gaps.
The English-only renderer remains separate from input understanding. Structural
success cannot detect every semantic omission or establish real DE/FR/IT/EN support.
Qualified source-meaning/result review remains pending even after a structural pass.

A full replay requires the complete ordered ledger, all 14 validated captures and
confirmed supervision/cleanup. Stopped captures remain failure evidence; replay
cannot turn them into a complete feasibility pass.

Focused offline evidence and remaining gaps: [verification.json](../../build/uc001-contract-local/verification.json).
