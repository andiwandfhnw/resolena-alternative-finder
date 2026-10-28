# Granite Windows controller preparation — 2026-10-25

## Owner decision and bounded result

The [supplied owner review/authorization](owner-authorization.txt) accepts
[Outcome A](../uc001-granite-acquisition-proxy/README.md) as closing the
acquisition-byte-meter blocker **at the offline preparation level only**. The
10-GiB ceiling, mandatory prior accounting, conservative upstream charges,
durable debit before forwarding, failure at exact exhaustion and isolated
command-local Git binding remain unchanged. Neither acquisition nor build
execution is established by that acceptance.

The complete controller implementation is now prepared with **146 focused offline
tests passing**. The [verification receipt](verification.json) records source
hashes, RED/GREEN logs, coverage and preservation. Windows native behavior remains
unverified; no real acquisition, configure/build, GPU/model operation or dependency
installation occurred. This is ready for owner review, **not cleared for real
acquisition/build execution**. No complete historical PID trace or measured resource
fit is inferred from the offline tests.

New source, outside the freeze:

- [controller.py](../../scripts/uc001_granite_controller/controller.py): independent
  sampling/watchdog, frozen limits, strict proxy-terminal validation, phase clocks,
  identity/event monitoring, cleanup and guarded CLI.
- [windows_job.py](../../scripts/uc001_granite_controller/windows_job.py): Windows x64
  ctypes backend, native ownership, committed-memory enforcement and handle cleanup.
- [worker.py](../../scripts/uc001_granite_controller/worker.py): the prepared source/
  configure/build steps, unchanged pins/flags, accepted proxy and durable child logs.
- [standins.py](../../scripts/uc001_granite_controller/standins.py): future harmless
  native ownership check, with three nested owned processes and a separate synthetic
  process whose survival is checked before its own identity-bound cleanup.

The accepted proxy and native build procedure are unchanged. The worker executes
those prepared steps under the controller; do not also launch the manual blocks.
No application or frozen assessment file was edited.

## Ownership and independent enforcement

The controller stays outside an unnamed private Job Object and retains its
non-inherited handle. The job has kill-on-last-handle-close and no breakaway flags.
Worker creation uses `CREATE_SUSPENDED` plus `PROC_THREAD_ATTRIBUTE_JOB_LIST` to bind
the job atomically at creation, closing the crash window between creation and a
separate assignment. Membership and creation identity are verified before resume.
Unsupported atomic assignment fails without a non-atomic production fallback.
Only the worker's stdin/stdout/stderr handles are whitelisted for inheritance;
the job/completion-port handles remain private.

A permanent abort flag and a short resume/terminate lock prevent a worker from
resuming after watchdog termination. Cleanup/termination does not depend on the
resource-sampler lock. Each expected worker is retained by process handle and
PID/creation time. Ordinary descendants inherit job membership, including proxy,
Git, CMake, Ninja, compiler, glslc and shader generator children. There is no
process-name termination. Resource snapshots record observed descendant identities;
very short-lived children may conservatively cause an unavailable-identity stop.
Worker-held child handles also supply creation/exit evidence. Ordinary Job
notifications are not guaranteed to provide every historical descendant PID.

A separate sampler thread obtains job committed memory, OS available physical
memory, caller-available/free disk and logical file lengths beneath the fixed
`build` directory. Missing, invalid, failed, redirected or disappeared measurements
fail closed. A directory not created yet is explicitly distinguished from a lost
previously observed build directory. Symbolic links/reparse redirects are rejected.
The sampler timestamps the **beginning** of a complete observation. Maximum age is
one second; polling is 50 ms. These are monitoring controls, not extra time/resource
allowances or product acceptance thresholds.

The control loop independently monitors phase workers, proxy identity/exits and
worker events. A separate watchdog terminates the private job if the control loop
becomes stale or the phase deadline expires, including blocked worker/controller
I/O. Neither worker progress nor a fresh proxy clock grants more time. Logging or
measurement failure never substitutes zero. Normal monitoring/termination latency
is not represented as hard real-time execution or a filesystem write quota.

| Scope | Exact enforced limit / authority |
|---|---|
| Acquisition | 1800 s from one original initialization start through proxy/Git/object/archive steps; no retry/reset |
| Download | 10737418240 bytes cumulative, including explicit prior charge; accepted proxy is the conservative byte authority |
| Configure + build | 2700 s combined, anchored once before their phase worker launches |
| Job memory | 25769803776 bytes aggregate **committed virtual memory**, native hard cap plus sampled current/peak values |
| Build output | 12884901888 bytes, measured logical file lengths in the build tree; breach/unknown terminates the job |
| Initial free disk | At least 51539607552 bytes before launching work |
| Disk floor | Stop below 8589934592 bytes |
| Host memory floor | Stop below 4294967296 bytes OS available physical memory |
| Parallelism | Frozen outer `--parallel 2` and existing nested hint 2; not a claim of two total descendant processes |

Committed job memory is **not RSS**. The frozen build-memory bound is enforced as
Windows' aggregate job commit quantity, with its exact 24-GiB value; no RSS quantity
is silently relabelled. The separately frozen server/client RSS and GPU/startup
requirements are untouched and not exercised. Unsupported job-memory queries stop;
no guessed zero or RSS fallback is used. If owner review requires a different
meaning for build memory, execution remains blocked pending that explicit resolution.

On breach/error/interruption the controller permanently aborts, terminates that job
only, retains partial files/logs, and requires active-job count zero plus signalled,
identity-bound exits. Cleanup failure is reported as failure/unknown even if handle
close subsequently requests kernel cleanup. No retry or alternate root/backend is
selected. Kill-on-job-close also protects assigned descendants if the controller
process exits unexpectedly. Incomplete controller evidence cannot establish success.

## Proxy and native procedure integration

The same accepted hash-bound proxy is launched as a separate owned child with a
private stdin channel. Its PID/creation identity, ready record, original acquisition
start and mandatory prior accounting are bound to the worker events. Premature
proxy exit fails independently of Git's result. CLOSE is recorded before requesting
a normal proxy close. The controller independently parses the terminal ledger:
strict JSON/no duplicate keys, complete newline records, unchanged prior/ceiling,
integer monotone debit and tunnel totals, approved destination, expected listening
PID, closed tunnels, clean terminal and matching final hash. Exact exhaustion fails.
Partial/malformed/missing terminal evidence is never accepted.

The source remains `https://github.com/ggml-org/llama.cpp.git`, revision
`620d2225cc436ab0b001e3200e590e3b286ef9ab`. Object validation, tree/ZIP hashes,
archive extraction, exact 17 CMake parameters, tool/cache checks and model-free
`llama-server` target remain the prepared route. The full artifact manifest is
retained; phase completion references its path/hash/count, independently checked
by the controller. No server binary is executed, even for its version.

## Evidence and Windows limits

One final command exercised only these six new test files:

```text
.venv/bin/python -m pytest -q tests/unit/test_granite_controller.py tests/unit/test_granite_controller_run.py tests/unit/test_granite_controller_cli.py tests/unit/test_granite_windows_job.py tests/unit/test_granite_controller_worker.py tests/unit/test_granite_controller_standins.py
```

[green-combined-final.log](green-combined-final.log): **146 passed in 1.79s**.
Intermediate counts are not added. RED receipts retain missing modules/APIs,
resource/cleanup/clock defects, ambiguous evidence, launch-abort races and compact
terminal integration cases. The earlier `green-controller-cli-first.log` is an
intermediate failed assembly run (missing stand-in helper in the manifest), not a
GREEN claim; it remains unchanged. Some shell cells ended in cat/tail, so interim
pytest exit codes were not all separately captured; raw pytest summaries remain.

The suite covers all requested groups: suspended assignment/no resume on failure;
nested termination/unrelated survival; both deadline boundaries and no reset;
committed-memory/output boundaries; initial disk/floors/host-memory failure;
stale/failed observations and blocked monitoring; premature proxy/worker exit;
terminal-ledger failure; interruption; active/failed cleanup; no retry. Windows
ctypes/kernel calls and process trees are injected stand-ins here, not native runs.
No original application/model/knowledge matrices were rerun.

Native prerequisites still require owner observation: Windows x64/Python 3.12.11,
Windows 10+/Server 2016+ atomic Job List support, native job-memory query support,
actual handle/membership/cleanup behavior and activated pinned tools. The prepared
native check uses a 20-second watchdog, harmless children with 30-second safety
exits, fresh output and no network/build/GPU operations. It establishes ownership
only if it passes; it does not establish native tool/runtime/model suitability or
resource fit for the real build.

Primary implementation basis: [Microsoft Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects),
[atomic Job List attributes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute),
[committed-memory limits](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information),
[Microsoft's job memory query binding](https://github.com/microsoft/hcsshim/blob/main/internal/winapi/jobobject.go),
[OS memory observations](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-globalmemorystatusex)
and [CreateProcess environment semantics](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw).
Source review is not desktop execution.

## Future Windows owner commands — NOT AUTHORIZED / NOT EXECUTED

Copy the four new `.py` helpers together to
`C:\Users\AndiWand\Downloads\granite-controller-v1` and copy
[controller-config.template.json](controller-config.template.json) there. Preserve
the original template (`execution_authorized: false`). Its SHA-256 is
`5b6a5a099a058ab7911af0177942668ed457ec24b0b4beb3886fedb13a29b70e`.
The helper hashes are recorded in that file and verification.json. Use the existing
separate Granite Python; no installation, frozen archive regeneration or old-env
modification is involved.

**Future ownership check only — ordinary Windows PowerShell after owner review:**

```powershell
$ErrorActionPreference = 'Stop'
$GranitePython = 'C:\Users\AndiWand\Downloads\granite-python-3.12.11-20250702\env\Scripts\python.exe'
$GraniteControllerDir = 'C:\Users\AndiWand\Downloads\granite-controller-v1'
$GraniteTemplate = Join-Path $GraniteControllerDir 'controller-config.template.json'
if ((Get-FileHash -LiteralPath $GraniteTemplate -Algorithm SHA256).Hash.ToLowerInvariant() -ne '5b6a5a099a058ab7911af0177942668ed457ec24b0b4beb3886fedb13a29b70e') { throw 'Controller template hash differs.' }
$GraniteConfig = Get-Content -Raw -LiteralPath $GraniteTemplate | ConvertFrom-Json
foreach ($GraniteHelper in $GraniteConfig.helper_hashes.PSObject.Properties) {
    if ((Get-FileHash -LiteralPath (Join-Path $GraniteControllerDir $GraniteHelper.Name) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $GraniteHelper.Value) { throw 'Controller helper hash differs.' }
}
$GraniteOwnershipOutput = Join-Path $GraniteControllerDir ('ownership-' + [Guid]::NewGuid().ToString())
& $GranitePython -I (Join-Path $GraniteControllerDir 'controller.py') ownership-self-test --output $GraniteOwnershipOutput
if ($LASTEXITCODE -ne 0) { throw 'Ownership check failed: preserve output and stop without fixes/retry.' }
```

Return the complete output/result/log directory. The separate synthetic process is
created by the test itself, survives job termination, then is cleaned through its
own retained handle; no unrelated user process is selected or killed.

**Future native phases — separate concrete execution approval required.**
Only after review/verified native ownership and explicit acquisition/build approval,
create a separate `controller-config.approved.json` from the retained template,
record owner authorization, set its execution flag and bind the mandatory reviewed
prior receipt's SHA-256. The template does not establish prior zero. The accepted
proxy helper must be present at its recorded unchanged path/hash; the frozen config
is read from the transferred current-worktree files. Existing native root means
STOP, without deletion/path switching or renewed allowances.

Use the already prepared shell-local activation, unchanged:

```bat
if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" (call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" amd64 10.0.22621.0 -vcvars_ver=14.43.34808 && powershell.exe -NoLogo -NoProfile) else (echo STOP: Existing Visual Studio activation file is missing.)
```

Then, in that activated child PowerShell, after the separate approval above:

```powershell
$ErrorActionPreference = 'Stop'
$GranitePython = 'C:\Users\AndiWand\Downloads\granite-python-3.12.11-20250702\env\Scripts\python.exe'
$GraniteControllerDir = 'C:\Users\AndiWand\Downloads\granite-controller-v1'
$GraniteApprovedConfig = Join-Path $GraniteControllerDir 'controller-config.approved.json'
$GraniteNativeOutput = Join-Path $GraniteControllerDir ('native-' + [Guid]::NewGuid().ToString())
& $GranitePython -I (Join-Path $GraniteControllerDir 'controller.py') native --config $GraniteApprovedConfig --output $GraniteNativeOutput
if ($LASTEXITCODE -ne 0) { throw 'Controlled phases failed: preserve receipts/partial artifacts; no retry.' }
```

These commands remain unexecuted. No model acquisition/startup/inference follows
successful source/build phases. All output remains for review: controller/worker
JSONL, ownership identities, resource samples, stdout/stderr, proxy ledger/prior
binding, source identity/tree/archive hashes, CMake cache/build metadata, artifact
manifest, termination/cleanup result and final JSON. No saved application records
are changed.

PHASE: 3 / STATUS: in-progress. Priority 5 owner acceptance and the closed Qwen
result remain unchanged. Priorities 3/4 remain partial; Priority 6 integrated review
and Phase 4 VALIDATE remain pending. Stop for owner review.

Preparation checks passed: Python source/test syntax, local documentation links,
new whitespace, exact helper hashes and two PowerShell blocks parsed without
execution. The CMD activation is byte-for-byte the accepted command, statically
reviewed only. All 832 earlier protected files outside TASKS and all 95 accepted
Granite files retain their fingerprints (overlapping counts are not added).
Historical task entries/Priority 5, Git HEAD/branch/index and prior status entries
remain unchanged. The new controller directory is the only added top-level Git
status entry. `git diff --check` exits 2 only for the preserved historical TASKS
trailing space, now line 2622. No accepted or frozen artifact was modified.
