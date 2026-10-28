# Scoped unknown-child identity diagnostic — 2026-10-26

**Offline preparation only. NOT AUTHORIZED / NOT EXECUTED on Windows.** The
scoped-edge diagnostic attempt is consumed. This separate package is ready for
owner review; another native execution requires separate explicit authorization.
PHASE: 3 / STATUS: in-progress.

## Owner-supplied consumed attempt

[Recorded fields](owner-confirmed-scoped-attempt.json) preserve the supplied chain
14444 → launcher 17520 (creation FILETIME 134375170217369722) → interpreter 28924
(134375170217547838). At approximately 19:37:01.871 UTC and again at 19:37:01.888
UTC after private-Job termination, scoped Toolhelp edges were 17520 → 28924 and
17520 → 38564. The unexpected PID is 38564, beneath the verified launcher; its
creation identity and image path remain unknown. No observation date was supplied.
No owned worker was created and no Job Object failure is established. Persistence
across both snapshots does not demonstrate a snapshot race. No console-helper
identity is inferred from older project evidence. These are owner-supplied results,
not Codex Windows checks or reconstructed desktop raw files. All prior attempts,
packages and receipts remain unchanged.

## Minimal additions and unchanged rejection

`outside_shape()` still queries exactly the verified launcher/interpreter parents
and accepts only `{(interpreter_pid, launcher_pid)}` in child/parent tuple order.
The durable scoped-edge record remains first. For each unexpected scoped child,
the new diagnostic checks the retained parent's PID/creation identity and opens
only that child PID. No broad process inventory is added. Three native methods
are added; existing ownership/open/termination methods remain unchanged:

| Method | Bounded native operation |
|---|---|
| `open_query_process(pid)` | `OpenProcess(0x1000, FALSE, pid)`: query-limited only; no terminate, synchronization, VM-read or inheritance rights |
| `image_path(handle)` | Pointer-safe `QueryFullProcessImageNameW`, flags 0, one 32,768-WCHAR buffer; full Win32 path and UTF-16-unit length checks; no resizing/retry |
| `query_exit_code(handle)` | Raw `GetExitCodeProcess`; no wait or synchronization right |

The existing handle-bound PID, integer creation FILETIME, native parent and private
Job-membership queries are reused. Microsoft documents the
[limited query rights](https://learn.microsoft.com/en-us/windows/win32/procthread/process-security-and-access-rights),
[image-path interface](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-queryfullprocessimagenamew),
[open behavior](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-openprocess)
and [raw exit-code semantics](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getexitcodeprocess).
Only documentation was consulted; no native code or binary was acquired/executed.

`unknown_child_identity` journal rows include the observed child/parent, verified
parent kind, native PID/birth/parent, private-Job membership, full image path/path
status, raw exit code, query errors and UTC/monotonic journal timestamps. Separate
statuses distinguish observed/unbound, identity-bound-but-unknown, open failure,
changed identity, parent mismatch, membership mismatch/unknown and path failure.
The handle is stored immediately after open in a separate diagnostic collection,
checked again after metadata and before existing cleanup, then closed. A failed
open is not retried during later observations; an opened handle is reused rather
than reopening its PID. Unknown handles never enter `outside`, `owned`,
`kill_allowed` or direct termination calls. Deadline checks remain between queries.
Diagnostic/journal failure cannot lead to an accepted edge or an owned launch.

The exact comparison and `StandinFailure: unknown additional unrelated process`
remain unchanged. A system path, including a literal system `conhost.exe` path,
is only an image-path observation; it approves no executable, signature or helper
role. Every extra edge still fails. The diagnostic adds no termination authority;
existing private-Job cleanup remains unchanged for processes already in that Job.

## Evidence limits

- Toolhelp has no child creation identity. Successful handle binding identifies
  the process held after open, and cannot rule out PID reuse between snapshot and
  open. Rows explicitly retain `snapshot_to_handle_identity: not_established`.
- Native open error 87 is recorded as `not_found_or_invalid_pid_before_binding`:
  a disappeared process is possible, not proven. Access denial/other failures
  remain unbound UNKNOWN. No replacement PID or helper is guessed.
- Raw exit code 259 remains `active_or_exit_code_259`, since query-only rights
  provide no wait-based disambiguation. Other successful raw codes record exit.
- Identity/path/parent/membership gaps remain UNKNOWN/failure. An identity-bound
  unknown child is still untrusted and never a legitimate-helper classification.
- Linux injected tests do not establish Windows query behavior, process ownership,
  resource fit, executable identity for PID 38564 or model/runtime suitability.
  The existing 20-second self-test bound, all resource limits, runtime/model pins,
  accepted proxy/native build procedure and frozen assessment remain unchanged.

## Offline RED → GREEN evidence

Executed focused test commands in Linux Codespace:

```bash
.venv/bin/python -m pytest -q tests/unit/test_granite_controller_standins.py -k identity_diagnostic
.venv/bin/python -m pytest -q tests/unit/test_granite_windows_job.py -k identity_query
.venv/bin/python -m pytest -q tests/unit/test_granite_windows_job.py -k identity_query_image_utf16
.venv/bin/python -m pytest -q tests/unit/test_granite_controller_identity_package.py
.venv/bin/python -m pytest -q tests/unit/test_granite_controller_standins.py tests/unit/test_granite_windows_job.py tests/unit/test_granite_controller_cli.py tests/unit/test_granite_controller_identity_package.py
```

Stand-in RED: 13 failed/1 passed; GREEN: 14 passed. One intermediate failure was an
injected PID-change fixture lookup defect, corrected without changing expectations;
its log is preserved. Native-query RED: 23 failed; GREEN: 23 passed. The separate
UTF-16 case failed before the WCHAR-unit correction. Package RED: five failed;
GREEN: five passed. Final focused result: **146 passed**, pytest exit 0, without
accumulating reruns. This includes the added interpreter-parent case and UTF-16
case. All native APIs were injected. Package tests use temporary files, PowerShell
syntax parsing and the denied authorization gate; no ownership execution occurred.

Coverage includes the expected edge only, unexpected children beneath either
verified parent, system/non-system image paths, unavailable/disappeared process,
changed PID/creation identity, parent mismatch, Job mismatch/unknown, image failure,
evidence before rejection, retained-handle revalidation and forbidden unknown-child
termination. A spy outside the implementation's exception handling verifies that
no unknown termination was attempted. Open/access/path/status failures are never
treated as successful observations.

All raw logs are retained as `standins-{red,green-first,green}.log`,
`native-{red,green}.log`, `native-utf16-red.log`, `package-{red,green}.log` and
`green-final-focused.log`. Source/test snapshots are in `before/`; the final
[verification receipt](verification.json) records hashes, checks and limitations.
Earlier overwritten-log limitations remain unchanged; no evidence was reconstructed.
No application tests or unrelated matrices were run.

## Separate diagnostic package

[uc001-granite-controller-identity-diagnostic-v1.zip](uc001-granite-controller-identity-diagnostic-v1.zip)
contains all four helpers, one new inactive template, runner, README and manifest.
Only standins/native query helpers differ from the previous prepared helper bytes;
previous archives/templates are not regenerated. Exact package-builder call:

```python
result = module.build_package(root, receipt/'package',
    receipt/'Run-IdentityDiagnostic.ps1', receipt/'package-readme.md')
```

| Item | Identity |
|---|---|
| ZIP size | 34,111 bytes |
| ZIP SHA-256 | `1150dfa3860f1eaf7dbd241e00134060d4ebb734d39c4972c2690c42d117a629` |
| Manifest SHA-256 | `643247f8d2ded7c4fa66d3f9d4e77bf850c901254609545a8aa0f8e80ddf1d48` |
| New inactive template SHA-256 | `cd952dd74eeb65dcb534a9ac08500fbe4aa689b2d54fbbe6bde3c6f37b4f7115` |

## Future owner command — NOT AUTHORIZED / NOT EXECUTED

Only after separate explicit owner authorization, save the ZIP at the exact path
below and run the complete block once in Windows PowerShell. The
`-OwnerAuthorized` switch records later authorization; its appearance here grants
none. Fresh destination only. Stop on any error without fixes/retry. Do not
interpret process names during execution. Preserve the complete result/log directory.

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $GraniteArchive = 'C:\Users\AndiWand\Downloads\uc001-granite-controller-identity-diagnostic-v1.zip'
    $GraniteDestination = 'C:\Users\AndiWand\Downloads\granite-controller-identity-diagnostic-v1'
    if ((Get-Item -LiteralPath $GraniteArchive).Length -ne 34111 -or
        (Get-FileHash -LiteralPath $GraniteArchive -Algorithm SHA256).Hash.ToLowerInvariant() -ne '1150dfa3860f1eaf7dbd241e00134060d4ebb734d39c4972c2690c42d117a629') {
        throw 'Identity diagnostic archive integrity differs: stop.'
    }
    if (Test-Path -LiteralPath $GraniteDestination) {
        throw 'Identity diagnostic destination exists: preserve it and stop.'
    }
    Expand-Archive -LiteralPath $GraniteArchive -DestinationPath $GraniteDestination -ErrorAction Stop
    & powershell.exe -NoLogo -NoProfile -NonInteractive -File (Join-Path $GraniteDestination 'Run-IdentityDiagnostic.ps1') -ExpectedManifestSha256 '643247f8d2ded7c4fa66d3f9d4e77bf850c901254609545a8aa0f8e80ddf1d48' -OwnerAuthorized
    if ($LASTEXITCODE -ne 0) {
        throw 'Identity diagnostic failed: preserve complete output and stop without fixes/retry.'
    }
}
```

The runner uses only the approved separate Python 3.12.11 environment and prints
the fresh sibling `ownership-identity-diagnostic-<GUID>` output path before its one
harmless self-test invocation. No native execution is authorized by this receipt.
No acquisition/configure/build/glslc/GPU/model/inference, reference activation or
Git delivery occurred. Priority 5 acceptance, closed Qwen result and inactive
normal runtime/knowledge remain unchanged. Priorities 3/4 partial; Priority 6 and
Phase 4 pending. Stop after offline preparation for owner review.
