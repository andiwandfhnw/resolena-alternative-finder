# Console-helper correction preparation — 2026-10-26

**NOT AUTHORIZED / NOT EXECUTED on Windows.** All previous native attempts,
including the identity diagnostic, are consumed. This bounded correction is ready
for offline owner review only. PHASE: 3 / STATUS: in-progress.

## Accepted observation and preserved history

[Owner-confirmed fields](owner-confirmed-identity-attempt.json) record controller
55232 → launcher 54420 (creation FILETIME 134375187725802401), with interpreter
52808 (134375187725983520) and system console host 50704
(134375187725860683) as launcher children. The helper's retained native identity,
parent 54420 and image `C:\Windows\System32\conhost.exe` revalidated without query
errors, outside the private Job. The extra edge appeared twice. Raw exit 259 stayed
ambiguous; `role_accepted` was false and the query handle later closed without a
termination request. Snapshot-to-handle identity remained unestablished.

The owner accepts this evidence as a system console-host association for the
tested launcher pattern. This is owner-supplied evidence, not Codex desktop
execution. Previous receipts/false flags are unchanged; no image identity is
reconstructed for earlier PID 38564 and no owned-tree success/resource fit follows.

The historical [helper checks](../../scripts/uc001_combined_ownership_v1_1_0/PythonOwnership.cs)
and [individual exit handling](../../scripts/uc001_combined_ownership_v1_1_0/Python-Ownership.ps1)
are reused as a narrow pattern: exact system image, retained identity, parent
lifetime, branch membership and explicit helper exits. Their older
interpreter-parent allowance is excluded: this correction permits **launcher
parent only**. Historical failures and later evidence remain separate and unchanged.

## Exact helper invariant

Every applicable verified launcher has its one verified interpreter and **zero or
one** console-helper sibling. The unrelated branch remains outside the private Job;
owned root/child/grandchild branches remain inside it. A helper is admitted only if:

1. All required launcher/interpreter edges are present. It is the sole extra
   direct child of that launcher, with no extra child under an interpreter.
2. A retained query-only handle binds the observed PID, valid integer creation
   FILETIME and exact native launcher parent. Helper birth is no earlier than
   retained launcher birth, and PID/birth remain stable after collection.
3. Full image path equals `GetSystemDirectoryW() + '\conhost.exe'` under Windows
   case-insensitive full-path comparison. No environment/hardcoded Windows path,
   basename-only check, arbitrary system executable or alias resolution is used.
4. Membership is explicitly the expected branch boolean; no PID/identity/parent/
   membership/path/exit query error or missing evidence occurs.
5. The same helper PID/birth remains bound for that launcher on later checks.
   Missing or replacement helpers fail; a second helper is never admitted.

All candidates and cardinalities validate before any new role is promoted.
Unclassified children remain query-only and are never directly terminated. A system
path alone grants no role. All required negative cases remain fail-closed.

The owned base graph retains its nested interpreter → next-launcher edges:

```text
controller → Lroot → Iroot → Lchild → Ichild → Lgrand → Igrand
             └ Hroot?        └ Hchild?        └ Hgrand?
```

Helpers are children of the corresponding launcher, not of its interpreter.
Final live identities, observed identity union, active count and lifetime total
must equal the six base identities plus only the admitted owned helpers. The early
nine-process ceiling is a structural rejection bound, never an unknown-process
allowance. Cleanup uses the exact accepted count; short-lived owned extras still fail.

## Source and cleanup changes

`standins.py` now separates raw identity collection from helper admission, keeps
one retained helper per launcher, checks both unrelated and owned branch graphs,
registers owned helpers with existing Job identity tracking, and requires all helper
exits and query-handle closure. Raw `unknown_child_identity` rows still grant no
role (`role_accepted=false`); separate `console_helper_accepted` and
`console_helper_revalidated` events record promotion/revalidation. Raw rows also
identify previously admitted helpers to keep the timeline explicit.

`windows_job.py` adds only bounded, pointer-safe `GetSystemDirectoryW` discovery,
one 32,768-WCHAR buffer and UTF-16 length/full-directory validation. Existing native
methods, atomic suspended Job association, no breakaway, kill-on-close and memory
metric remain unchanged. [Microsoft documentation](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-getsystemdirectoryw)
supports its interface and length checks. No native code was executed.

Accepted helpers are fully revalidated before cleanup. No helper query handle has
termination rights. Existing private-Job termination and verified unrelated
launcher/interpreter termination are unchanged:

- Outside helper: after launcher/interpreter cleanup, poll the same query handle
  within the existing 20-second bound. Stable PID/birth plus a successful non-259
  raw exit code proves exit. Code 259 remains unresolved and fails at the deadline.
- Owned helper: existing Job cleanup must retain its exact identity, confirm its
  exit by wait, and report the same exit code as the stable query handle. A 259
  code is acceptable only with this separate Job wait proof.
- Every helper appears in `console_helper_exits`, with identity verification,
  exit proof, direct-termination flag false and query-handle closure. Job cleanup
  scope is labelled as scope, not claimed termination success. Missing exits,
  changed identities, failed revalidation or failed handle closure prevent success.

The initial cleanup event records exit-stage observations; the final
`console_helper_cleanup_complete` event and result include handle closure. Unknown
or unclassified children never receive direct termination authority. Existing Job
cleanup still applies to processes already in that private Job. On any failure,
preserve evidence and stop without fixes/retry.

## Offline RED → GREEN

Commands executed in Linux Codespace, with injected Windows APIs/processes only:

```bash
.venv/bin/python -m pytest -q tests/unit/test_granite_controller_standins.py -k console_role
.venv/bin/python -m pytest -q tests/unit/test_granite_windows_job.py -k console_system
.venv/bin/python -m pytest -q tests/unit/test_granite_controller_console_package.py
.venv/bin/python -m pytest -q tests/unit/test_granite_controller_standins.py -k 'console_role_owned_helpers or console_role_handle_close_failure'
.venv/bin/python -m pytest -q tests/unit/test_granite_controller_standins.py tests/unit/test_granite_windows_job.py tests/unit/test_granite_controller_cli.py tests/unit/test_granite_controller_console_package.py
```

Main role RED: **28 failed** → GREEN: **28 passed**. Native system-directory RED:
**12 failed** → GREEN: **12 passed**. Package RED: **five failed** → GREEN: **five
passed**. Review added two RED cases for cleanup-scope receipt precision and failed
helper-handle closure. Final focused result: **190 passed**, pytest exit 0.
This is one final result, not accumulated reruns: 90 stand-in, 91 native-binding,
four CLI and five package checks. No application/model tests or broad matrices ran.

Cases cover absent/present helpers, all owned launchers, exact nested base edges,
zero/multiple interpreters, multiple helpers, interpreter-parent helpers, fake
paths/other system executables, changed PID/birth, native-parent mismatch,
membership mismatch/unknown, unavailable/path/query failures, unknown third
children, pre-launcher birth, replacement/disappearance, exact lifetime accounting,
missing/stuck helper exits, failed revalidation and failed handle closure. A spy
outside implementation exception handling forbids accidental helper/unknown direct
termination. Full-path case semantics and non-default native system directories
are covered.

All raw logs are retained, including the earlier bounded-scope test failure and
package-description assertion failures. The old scope expectation was extended
from two unrelated identities to also permit exactly the six verified owned
identities; it still checks the exact known edges and excludes unrelated inventory.
`green-final.log` is the reviewed final result. Earlier logs, the first superseded
offline ZIP and its original metadata remain under this directory and
`intermediate-package/`; no evidence was overwritten or reconstructed.
Snapshots are in `before/`; [verification.json](verification.json) records commands,
hashes and preservation checks.

## Separate final package

[uc001-granite-controller-console-helper-v1.zip](uc001-granite-controller-console-helper-v1.zip)
contains the four helpers, one new inactive template, runner, README and manifest.
Original archives, configurations and frozen assessment files are unchanged.
The final standard-library packager call was:

```python
result = module.build_package(root, receipt/'package',
    receipt/'Run-ConsoleHelperCheck.ps1', receipt/'package-readme.md')
```

| Item | Identity |
|---|---|
| Final ZIP size | 36,126 bytes |
| Final ZIP SHA-256 | `70f048452a65f619e60c350334fa658280ec8bbfd63b18c1fe9001e3513989e5` |
| Manifest SHA-256 | `c9e011f8a483153c25c7ce01be91f1a67f4b505c7280f6a328905e44b7990880` |
| New inactive template SHA-256 | `269adcff1eec7e77566915a9d266ac8428efab6257fa19cd0f9eb8cad50b98cf` |

## Future owner command — NOT AUTHORIZED / NOT EXECUTED

Only after separate explicit owner authorization, save the **final** ZIP at the
path below and run the complete block once in Windows PowerShell. The switch
records that later authorization; its presence here grants none. Fresh destination
only. Preserve the complete printed result/log directory; stop on failure without
fixes/retry.

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $GraniteArchive = 'C:\Users\AndiWand\Downloads\uc001-granite-controller-console-helper-v1.zip'
    $GraniteDestination = 'C:\Users\AndiWand\Downloads\granite-controller-console-helper-v1'
    if ((Get-Item -LiteralPath $GraniteArchive).Length -ne 36126 -or
        (Get-FileHash -LiteralPath $GraniteArchive -Algorithm SHA256).Hash.ToLowerInvariant() -ne '70f048452a65f619e60c350334fa658280ec8bbfd63b18c1fe9001e3513989e5') {
        throw 'Console-helper archive integrity differs: stop.'
    }
    if (Test-Path -LiteralPath $GraniteDestination) {
        throw 'Console-helper destination exists: preserve it and stop.'
    }
    Expand-Archive -LiteralPath $GraniteArchive -DestinationPath $GraniteDestination -ErrorAction Stop
    & powershell.exe -NoLogo -NoProfile -NonInteractive -File (Join-Path $GraniteDestination 'Run-ConsoleHelperCheck.ps1') -ExpectedManifestSha256 'c9e011f8a483153c25c7ce01be91f1a67f4b505c7280f6a328905e44b7990880' -OwnerAuthorized
    if ($LASTEXITCODE -ne 0) {
        throw 'Console-helper self-test failed: preserve complete output and stop without fixes/retry.'
    }
}
```

The pinned separate Python 3.12.11 environment is reused. The runner prints a
fresh sibling `ownership-console-helper-<GUID>` result path before its one harmless
self-test. It does not acquire source/model artifacts or run configure/build.

## Evidence limits and stopping point

Windows role admission, owned branch membership and helper cleanup remain
unverified for this correction. Owned helper behavior is covered by injected tests,
not by the observed unrelated native branch. Outside Toolhelp snapshots cannot
exclude every unobserved transient process, and snapshot-to-open PID reuse remains
a limit; retained identity/native-parent/lifetime checks do not invent snapshot
birth evidence. A system path is not a signature or file-content verification.
Open error 87 and outside exit 259 retain their explicit limits.

This changes only the harmless self-test model. Actual acquisition/build worker
composition, accepted proxy/native procedure, resource bounds, frozen Granite
assessment, model/runtime settings and Python environments remain unchanged.
No native execution, acquisition/configure/build/glslc/GPU/model/inference or Git
delivery occurred. Normal app.main remains unconfigured and real drafts inactive.
Priority 5 acceptance and closed Qwen result remain; Priorities 3/4 partial;
Priority 6/Phase 4 pending. Stop after offline preparation for owner review.
