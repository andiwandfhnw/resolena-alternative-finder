# Proxy launcher/interpreter binding preparation — 2026-10-26

**Offline preparation only. Future Windows check NOT AUTHORIZED / NOT EXECUTED.**
The owner accepted the [readiness review](../uc001-granite-native-readiness-v1/README.md)
and authorized this bounded worker/proxy/controller correction. The successful
harmless ownership/helper result remains **CLOSED**; its source, tests and receipts
were not changed or rerun. Real acquisition/configure/build execution is not prepared.

## Identity and event contract

[event-schema.json](event-schema.json) is the explicit version-1 contract.
Every full identity contains positive integer `pid`, integer creation FILETIME,
native `parent_pid` and `in_any_job=true`. Worker any-Job observations are preliminary:
the controller independently proves membership in its **exact private Job** before
allowing fetch. Boolean/float aliases are rejected for schema versions and PID fields.

| Worker event | Meaning |
|---|---|
| `proxy_launcher_started` | Retained Popen launcher identity; no interpreter role implied |
| `proxy_binding_requested` | Both full identities, strict `same_process`, actual readiness PID |
| `proxy_listening` | Both identities plus listening PID equal to the verified interpreter |
| `proxy_closing` | Both identities after the worker verifies both still alive, before CLOSE |
| `proxy_interpreter_exit` | Interpreter's native identity-bound zero exit |
| `proxy_launcher_exit` | Launcher's independently verified zero exit |
| `acquisition_terminal` | Explicit `proxy_launcher_pid` / `proxy_interpreter_pid`, schema and unchanged ledger accounting |

Generic `child_started` / `child_exit` retain their non-proxy meaning. Old ambiguous
proxy events are rejected. Proxy events are valid only during acquisition.

For a split, readiness PID is distinct from launcher PID; the retained interpreter
handle must resolve exactly that PID, have valid birth no earlier than launcher,
native parent exactly launcher, stable PID/birth and matching private-Job membership.
For no-split, both roles must resolve to the **same actual retained launcher
handle/process**, with identical verified native facts. Equal fixture numbers do
not establish sameness. The two role exit records then describe one physical process.

The controller validates the pair and scoped branch, then writes exactly
`PROXY_BOUND\n` once to the acquisition worker's fresh private stdin pipe. The
worker cannot publish listening/start fetch before reading that ACK. This uses the
existing bounded pipe writer; it adds no new clock or budget. There is no ACK for
an unbound PID or unclassified branch.

Active split-branch checks reuse the **unchanged** accepted console-helper validator:
launcher → interpreter plus optional exactly-one fully verified system console
helper under launcher. Other children fail. No-split accepts no extra child.
Once closing begins, observed edges may disappear but no new edge/helper is admitted.
The controller checks launcher and interpreter lifecycles independently, including
launcher exit before interpreter binding. Ledger validation always uses interpreter
PID, never a launcher substitute; the accepted proxy still reports its own `os.getpid()`.

## Minimal source changes and cleanup

- [worker.py](../../scripts/uc001_granite_controller/worker.py): retained interpreter
  binding alongside Popen launcher, mandatory private ACK, explicit proxy events,
  both-role liveness/exit checks, interpreter-PID ledger validation and separate
  interpreter-handle closure in `finally`. Non-proxy commands/build flags remain.
- [controller.py](../../scripts/uc001_granite_controller/controller.py): exact native
  pair/branch proof, ACK only after verification, independent lifecycle tracking,
  strict interpreter-ledger identity, role-exit requirements and per-phase cleanup.

The worker retains the Popen launcher handle and opens a separate interpreter
handle with existing query/synchronization rights, **without terminate rights**.
No-split reuses the launcher handle. Both processes must remain alive until planned
close; both native exit proofs are required. Separately opened interpreter handles
close on success/failure; the Popen handle remains Popen-owned.

The controller retains independent Job handles for both roles and any admitted
helper. Normal completion requires both explicit role exits backed by native
retained-identity checks. Final cleanup reconciles role PID/birth keys with the
Job's confirmed exits after native handles close; it also verifies helper exits
and closes helper/unknown query handles. The receipt includes phase and
`binding_established`, so an empty build-phase cleanup is not a proxy-binding pass.
Abort cleanup can verify exits while the phase remains failed. Unknown children
gain no direct termination authority. Missing/changed/unverified evidence stays failure.

The accepted proxy bytes, `standins.py`, `windows_job.py`, successful native receipt,
acquisition proxy algorithm, native build procedure, all pins and frozen ceilings
are unchanged. Acquisition remains 1800 seconds / cumulative 10 GiB including
reviewed prior charges; build 2700 seconds combined; Job committed memory 24 GiB
(not RSS), output 12 GiB, initial disk 48 GiB, disk floor 8 GiB, host-memory floor
4 GiB, outer parallelism 2. Waiting for ACK counts within the original acquisition
deadline; no allowance resets or guessed prior zero were introduced.

## RED → GREEN evidence

Focused injected commands, all in Linux Codespace:

```bash
.venv/bin/python -m pytest -q tests/unit/test_granite_controller_worker.py -k proxy_identity
.venv/bin/python -m pytest -q tests/unit/test_granite_controller_run.py -k proxy_binding
.venv/bin/python -m pytest -q tests/unit/test_granite_proxy_identity_package.py
.venv/bin/python -m pytest -q tests/unit/test_granite_proxy_identity_flow.py
.venv/bin/python -m pytest -q tests/unit/test_granite_controller_worker.py tests/unit/test_granite_controller_run.py tests/unit/test_granite_controller.py tests/unit/test_granite_proxy_identity_flow.py tests/unit/test_granite_proxy_identity_package.py
```

Worker RED: **20 failed**; controller RED: **16 failed**; package RED: **nine failed**.
Review retained additional RED cases for premature-close publication, typed ledger
PIDs/schema, missing helper handles, explicit phase receipts and wrong-phase events.
Final focused result: **165 passed**, pytest exit 0 (47 worker, 46 controller,
53 unchanged safety-policy regressions, ten cross-component flow/identity cases,
nine package checks). Counts are not accumulated across reruns.

Coverage includes split/no-split native handle proofs, wrong readiness PID,
parent/member/birth changes, launcher-PID ledger rejection, independent premature
launcher/interpreter exits, missing role exits, retained cleanup for both roles,
unknown branch processes and optional helpers under the unchanged policy. The flow
test drives actual worker-produced events through the real PhaseMonitor, verifies
ACK before synthetic fetch and uses the accepted ledger implementation. Real
process/network calls are forbidden in that injected flow. Synthetic archive/tool
fixtures do not acquire or configure third-party source.

All raw logs remain here, including intermediate package failures; none was
overwritten. [verification.json](verification.json) records exact executed arguments,
results, source preservation and limits. No closed ownership/Windows-backend suite,
application/model tests or broad matrices ran.

## Separate inactive package and hashes

[uc001-granite-proxy-identities-v1.zip](uc001-granite-proxy-identities-v1.zip) contains
four helpers, the unchanged accepted proxy, structural `check.py`, inactive template,
one PowerShell runner, README and manifest. No real acquisition/build invocation
or approved execution configuration is supplied.

| Item | SHA-256 |
|---|---|
| ZIP — 49,081 bytes | `5e17772727fae81fb73f48f734e7301a148d56927841fe0c7f5ade0c70f18ade` |
| Manifest | `8b9a01de56eb28f1b4b0040d3626158c2b64010bf69e3df357ef19644bbb9f33` |
| Inactive template | `d778202f34ad163dd1a2cc89b3ec71f35ef623eaf8c1894935a4bde1139c8e9b` |
| controller.py | `5889ea53fe3a0ada4acaee072196b953a04b0b797fb77ea46df1154c0f78d787` |
| worker.py | `6c786d97f23a92b5ee6f6699d2b92a3de0bdb9913a332e3a8d046a67fe4aca85` |
| standins.py — unchanged | `eddac526505213644f553b0b8617396ff7898f53dd174ecd6dd030b21f69501f` |
| windows_job.py — unchanged | `792ee180000065fc39edcccbf2e7130ec68fff5358128b258f2a0e95952f0a22` |
| proxy.py — unchanged | `a7c62f83356636bea839633382bb62a3e53bcce466caea7b32226cece1e7bb1d` |

The standard-library builder call was `build_package(root, receipt/'package',
receipt/'Run-ReadinessCheck.ps1', receipt/'package-readme.md')`. Actual packaged
imports/hashes/syntax/schema passed in Codespace under an explicitly injected Linux
runtime gate, with forbidden attempts empty. [That result](codespace-structural.json)
reports `windows_execution=false`, `native_binding_verified=false` and
`runtime_check_injected=true`; it is not Windows success.

## Future Windows readiness command — NOT AUTHORIZED / NOT EXECUTED

**Structural integrity/import/schema check only.** This does not launch a proxy,
instantiate native APIs, rerun ownership, or perform acquisition/build. Its result
deliberately keeps native binding/resource fit false. Separate owner authorization
is required before running this future block; `-OwnerAuthorized` records that later
approval and grants none here. Save the ZIP at the exact path shown; fresh folder only.

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $GraniteArchive = 'C:\Users\AndiWand\Downloads\uc001-granite-proxy-identities-v1.zip'
    $GraniteDestination = 'C:\Users\AndiWand\Downloads\granite-proxy-identities-v1'
    if ((Get-Item -LiteralPath $GraniteArchive).Length -ne 49081 -or
        (Get-FileHash -LiteralPath $GraniteArchive -Algorithm SHA256).Hash.ToLowerInvariant() -ne '5e17772727fae81fb73f48f734e7301a148d56927841fe0c7f5ade0c70f18ade') {
        throw 'Proxy-identities archive integrity differs: stop.'
    }
    if (Test-Path -LiteralPath $GraniteDestination) {
        throw 'Proxy-identities destination exists: preserve it and stop.'
    }
    Expand-Archive -LiteralPath $GraniteArchive -DestinationPath $GraniteDestination -ErrorAction Stop
    & powershell.exe -NoLogo -NoProfile -NonInteractive -File (Join-Path $GraniteDestination 'Run-ReadinessCheck.ps1') -ExpectedManifestSha256 '8b9a01de56eb28f1b4b0040d3626158c2b64010bf69e3df357ef19644bbb9f33' -OwnerAuthorized
    if ($LASTEXITCODE -ne 0) {
        throw 'Structural readiness failed: preserve complete output and stop without fixes/retry.'
    }
}
```

The pinned separate Python 3.12.11 environment is reused. A fresh sibling
`readiness-proxy-identities-<GUID>` result directory is printed and retained.

## Limits and stopping point

This establishes offline contract fit only. Windows native worker/proxy/ACK-pipe
behavior remains unverified; the structural command cannot establish it. Scoped
snapshots cannot exclude every unobserved transient child; initial snapshot-to-open
PID reuse remains a limit. Binding/exits depend on retained native identity checks
and the controller's exact private-Job proof, not worker any-Job flags alone.
The no-split path conservatively rejects all extra children.

Real acquisition/build remains gated on separate review/approval, complete reviewed
SHA-bound prior accounting, current approved configuration and fresh tool/path/
resource entry checks. No source, configure/build/compiler/glslc/GPU/model/inference,
native ownership run or Git delivery occurred. Closed Qwen result, Priority 5
acceptance, normal app.main and inactive real drafts remain unchanged.
Priorities 3/4 partial; Priority 6/Phase 4 pending. PHASE: 3 / STATUS: in-progress.
Stop after offline preparation for owner review.
