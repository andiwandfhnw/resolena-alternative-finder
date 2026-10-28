# Ownership self-test launcher correction — 2026-10-25

## Confirmed failure and preserved evidence

The owner confirms the failed attempt's actual chain:

| Identity | PID | Creation FILETIME (100 ns) | Parent |
|---|---:|---:|---:|
| Controller | 60320 | Not supplied | Not supplied |
| Retained venv launcher | 61196 | 134374354509552652 | Controller |
| Actual interpreter | 61020 | 134374354509736275 | 61196 |

The original comparison incorrectly equated launcher and interpreter identities.
It failed **before owned worker creation**, so suspended assignment/resume remained
false and owned identities empty. This was a stand-in identity-model defect, not
an established Job Object failure. Credit remains limited to controller outside
the private Job, empty-Job cleanup, launcher survival and subsequent launcher
cleanup. Interpreter/nested ownership cleanup was not established by that attempt.

The owner retains the failed directory unchanged at
`C:\Users\AndiWand\Downloads\granite-controller-v1\ownership-ecc37015-dc69-4455-acdf-36bfdb4956d9`.
[owner-confirmed-observations.json](owner-confirmed-observations.json) transcribes
only supplied facts; it is not a reconstructed raw result or independent desktop
file audit. No commands modified or reran the failed attempt.

Separately, the owner reports that the previously absent original template is now
copied and hashes to
`5b6a5a099a058ab7911af0177942668ed457ec24b0b4beb3886fedb13a29b70e`;
the four desktop helpers also match the previous preparation receipt. This current
handoff observation does **not** retroactively validate the failed precheck.
The original template/receipt remain unchanged.

Original controller/helpers/tests were [snapshotted before editing](before/).
Their exact hashes are in [preservation-before.json](preservation-before.json).
The original [146-test receipt](../uc001-granite-controller/verification.json),
accepted proxy/native procedure and frozen assessment/archive remain historical,
unchanged evidence. The old stand-in bytes/hash are preserved in the snapshot.

## Bounded correction

Only stand-in ownership/cleanup and necessary native identity helpers changed:

- [standins.py](../../scripts/uc001_granite_controller/standins.py) distinguishes
  controller, launcher and interpreter. Every expected PID, FILETIME and native
  parent must match; a manifest alone cannot establish identity.
- [windows_job.py](../../scripts/uc001_granite_controller/windows_job.py) adds
  retained-handle PID/parent queries, optional termination rights for controlled
  outside processes, scoped child-edge observations and final lifetime Job count.
  Atomic Job assignment, no breakaway, kill-on-close and memory limits are unchanged.

For the unrelated pair, retained launcher and interpreter handles are both verified
outside the private Job. The interpreter must have the retained launcher as native
parent; launcher PID/birth remains stable across interpreter verification. Both
must survive private-Job termination, then both must have separately observed,
identity-bound exits. Launcher exit cannot substitute for interpreter exit.
Unverified manifest PIDs are not termination targets. Unknown/incomplete cleanup
remains failure, including missing interpreter evidence.

The owned chain is explicitly:

`controller → root launcher → root interpreter → child launcher → child interpreter → grandchild launcher → grandchild interpreter`.

All six identities must have native handle/creation/parent verification and private
Job membership. The live snapshot is refreshed after verification; exact observed
membership, active count **6** and lifetime process count **6** are required.
Final cleanup must retain lifetime count 6, active count zero and all six
identity-bound exits. An additional short-lived Job process therefore also fails.
Parent interpreters record their child launcher's retained identity separately.
There is no direct-process fallback that merges launcher/interpreter identities.

A bounded Toolhelp snapshot checks only child edges of the known unrelated
launcher/interpreter; only those edges are retained, with no executable-name or
unrelated software inventory export. Unknown active edges fail before and after
private-Job termination. This is not a complete historical trace of already-exited
outside processes. The reviewed unrelated stand-in code creates no further child.

The independent 20-second watchdog stops the private Job and both verified outside
handles without waiting for journal writes. Deadline/termination reason is explicit.
No new allowance, retry or process-name termination is introduced. Harmless role
safety exits remain unchanged. Unknown cleanup is reported rather than inferred.
`-B` prevents bytecode caches from modifying the extracted helper inventory.

The build-supervision limit remains **25,769,803,776 aggregate committed Job bytes**,
explicitly not RSS. No later server/client RSS, host physical-memory, GPU/VRAM or
startup/inference requirement changes. The accepted acquisition proxy and native
build procedure were not edited. General acquisition/build launcher integration is
not qualified by this bounded harmless-test correction; no real execution follows.

Native implementation basis: [Microsoft retained-handle parent query](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntqueryinformationprocess),
[Microsoft .NET's limited-query parent implementation](https://raw.githubusercontent.com/dotnet/runtime/main/src/libraries/System.Diagnostics.Process/src/System/Diagnostics/Process.Windows.cs),
[process snapshot API](https://learn.microsoft.com/en-us/windows/win32/api/tlhelp32/nf-tlhelp32-createtoolhelp32snapshot).
Unsupported/failed native observations stop; none was executed in this Codespace.

## Offline RED → GREEN evidence

The exact owner-supplied PID/FILETIME split first failed the old comparison:
[red-split.log](red-split.log), followed by [full split RED](red-split-all.log).
Negative cases cover wrong parent, changed launcher/interpreter birth, missing
interpreter, unknown inside/outside processes, one-sided cleanup, blocked monitoring,
post-stop process changes and late extra lifetime counts. The original test intents
remain, and before-edit test bytes are retained.

Native-helper RED receipts cover absent PID/parent/edge methods and missing final
lifetime accounting. Package RED reproduced absent package/gate artifacts. Final
focused verification, without adding intermediate pass counts:

```text
.venv/bin/python -m pytest -q tests/unit/test_granite_controller_standins.py tests/unit/test_granite_windows_job.py tests/unit/test_granite_controller_cli.py tests/unit/test_granite_controller_correction_package.py
```

[green-final-correction.log](green-final-correction.log): **94 passed in 4.74s**,
actual pytest exit **0**. No application/model/knowledge or unrelated matrix ran.
Windows calls/processes were injected. Linux PowerShell gate tests used synthetic
package copies and a harmless marker executable; no Windows ownership attempt ran.
They prove missing template/changed helper prevents invocation inside one script.

Evidence limit: the intermediate `green-poststop-watchdog.log` was overwritten by
a later 28-test run after an earlier 82-test run used the same filename. The earlier
summary exists in the tool transcript only; the missing raw log was not reconstructed.
The final 94-test log is separate. All earlier accepted receipts and the failed
Windows-attempt evidence were unaffected.

## New complete correction package

[uc001-granite-controller-launcher-fix-v1.zip](uc001-granite-controller-launcher-fix-v1.zip)
is a new eight-file review package, separate from all original archives/directories:

- Four controller helpers; controller.py and worker.py remain byte-identical.
- A new inactive controller-config.template.json matching the corrected helper hashes.
- Run-OwnershipCheck.ps1, README.md and manifest.json.

Archive: **31,769 bytes**; SHA-256:
`5efbb4a13d45cbc8e187dcdffe08614f01d8d8d045d0b14a4eec45aca8ac638a`.
Manifest SHA-256: `f072e378ce1da2827edb6aa8e754d66e641f5ce65c8d0cf2279962a4b5203f13`.
New template SHA-256: `c7833fe714979ceb31a1254426827ea7471f00cbe1581f099d87addc3a60c9fc`.
The original template hash 5b6a… is unchanged and is not reused for the new template.
All file identities are recorded in [verification.json](verification.json).

The single runner verifies the complete inventory, manifest, every file and template
helper hashes before invoking only the harmless self-test. A missing file terminates
that script; interactive entry cannot continue its internal steps after a failure.
No retry or native acquisition/build command exists in the runner. The template's
`execution_authorized` remains false. No dependency or environment installation.

## Exact future owner command — NOT AUTHORIZED / NOT EXECUTED

**Another native attempt requires separate owner authorization.** After such approval,
copy this ZIP to the exact Downloads path below. Keep the original controller folder
and failed output untouched. Paste the following as **one block** in ordinary Windows
PowerShell. It uses a fresh correction directory and a separate output directory;
there is no VS activation, configure/build, glslc, GPU or model step.

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $GraniteArchive = 'C:\Users\AndiWand\Downloads\uc001-granite-controller-launcher-fix-v1.zip'
    $GraniteDestination = 'C:\Users\AndiWand\Downloads\granite-controller-launcher-fix-v1'
    if ((Get-Item -LiteralPath $GraniteArchive).Length -ne 31769 -or (Get-FileHash -LiteralPath $GraniteArchive -Algorithm SHA256).Hash.ToLowerInvariant() -ne '5efbb4a13d45cbc8e187dcdffe08614f01d8d8d045d0b14a4eec45aca8ac638a') { throw 'Correction archive integrity differs: stop.' }
    if (Test-Path -LiteralPath $GraniteDestination) { throw 'Correction destination exists: preserve it and stop.' }
    Expand-Archive -LiteralPath $GraniteArchive -DestinationPath $GraniteDestination -ErrorAction Stop
    & powershell.exe -NoLogo -NoProfile -NonInteractive -File (Join-Path $GraniteDestination 'Run-OwnershipCheck.ps1') -ExpectedManifestSha256 'f072e378ce1da2827edb6aa8e754d66e641f5ce65c8d0cf2279962a4b5203f13'
    if ($LASTEXITCODE -ne 0) { throw 'Ownership check/precheck failed: retain output and stop without fixes/retry.' }
}
```

Current result: offline correction ready for owner review; corrected Windows
ownership and resource fit remain unverified. No new Windows test is authorized
or executed, and no acquisition/build/model readiness is inferred.
PHASE: 3 / STATUS: in-progress. Priority 5 acceptance and closed Qwen result remain;
Priorities 3/4 partial, Priority 6/Phase 4 pending. Stop for owner review.

Preparation checks passed: new source/test Python syntax, local links/fences/new
whitespace, package/manifest/helper hashes, runner and future command syntax.
All 832 older protected files and 148 accepted Granite artifacts outside the four
authorized source/test changes retain their fingerprints (counts overlap).
All seven before-edit snapshots match their originals. Historical task/Priority 5
entries, Git HEAD/branch/index/status and the original 5b6a… template are unchanged.
`git diff --check` exits 2 only for the preserved historical TASKS trailing space,
now line 2678. No staged/committed/delivered Git action occurred.
