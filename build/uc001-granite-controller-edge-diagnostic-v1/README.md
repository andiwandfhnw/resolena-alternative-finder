# Scoped child-edge diagnostic preparation — 2026-10-26

**NOT AUTHORIZED / NOT EXECUTED on Windows.** The one corrected native attempt
is consumed. This package is ready for offline owner review only; another native
execution needs separate explicit authorization. PHASE: 3 / STATUS: in-progress.

## Consumed owner attempt

[Owner-confirmed fields](owner-confirmed-corrected-attempt.json) record controller
60812 → launcher 61512 → interpreter 28420. Both unrelated identities were verified
outside the private Job and later have identity-verified exits, code 57345. The
failure remains `StandinFailure: unknown additional unrelated process`, before any
owned worker. Assignment/resume is false, owned identities/exits are empty and
private Job cleanup is verified with active/total 0/0. Both original unrelated
survival/cleanup flags remain false. This demonstrates the unrelated identity-pair
correction, not an owned tree or a Job Object failure. The extra edge was not
recorded; no process identity/name is inferred. These are owner-supplied results,
not a Codex Windows run or reconstructed desktop files. Earlier attempts, packages,
receipts and their limitations remain unchanged.

## Exact check and minimal change

`outside_shape()` queries `children_of({launcher.pid, interpreter.pid})`: for this
attempt, exactly **{61512, 28420}**. Native Toolhelp retains only `(child_pid,
parent_pid)` pairs with one of those parents. Its existing 1-second maximum and
65,536-entry cap remain unchanged. The expected set is exactly **{(28420, 61512)}**.
The same comparison runs before `job.launch()` and at later rechecks, including
after private-Job termination. No names or unrelated process inventory are returned.

Only `standins.py` changes among the four helpers. `_observe_scoped_edges()` writes
a durable `scoped_child_edges` journal record immediately before the unchanged exact
comparison. Each edge carries parent PID, child PID, verified parent kind, snapshot
observation UTC and monotonic time. The event also records the query start/end
interval. These are snapshot observation times, not per-child creation times.
An existing verified child's creation FILETIME is copied from its retained verified
identity and labelled `previously_verified_retained_identity`; it is not a fresh
query. Unknown children have null creation time and `no_retained_verified_handle`.
No unknown process is opened, terminated or given a helper role by this diagnostic.

Malformed/out-of-scope results are recorded as `malformed` with null edges, without
raw data; API errors record `failed`, error type and null edges before propagation.
Null means unavailable, never an empty successful observation. Journal failure
also stops execution. Unexpected valid edges still raise exactly
`StandinFailure: unknown additional unrelated process`. No allowance, name whitelist,
cleanup rule, resource limit, proxy, native build procedure or frozen setting changes.

## Offline verification

Commands ran in Linux Codespace only, using injected process/API stand-ins:

```bash
.venv/bin/python -m pytest -q tests/unit/test_granite_controller_standins.py -k edge_diagnostic
.venv/bin/python -m pytest -q tests/unit/test_granite_controller_standins.py tests/unit/test_granite_controller_cli.py tests/unit/test_granite_controller_edge_package.py
.venv/bin/python -m pytest -q tests/unit/test_granite_windows_job.py -k 'child_snapshot or scoped_snapshot'
```

Diagnostic RED: **13 failed**, pytest exit 1; GREEN: **13 passed**, exit 0.
Final directly affected self-test/CLI/package checks: **52 passed**, exit 0.
Scoped Toolhelp regressions: **5 passed**, exit 0. Cases include expected singleton,
an extra under each parent, multiple extras, malformed/failed observation, durable
record ordering before termination, failed journal writes and bounded evidence.
Unknown child handles are never opened. Package TDD separately began with five
failures; an intermediate PowerShell parser-test harness defect was corrected;
all logs are retained. Counts above are final scoped results, not accumulated reruns.
Package tests parse PowerShell and exercise only the denied authorization gate;
they do not run ownership code. No real Windows API/process test, acquisition,
configure/build, glslc, GPU, model or inference occurred.

Raw command outputs are retained here as `red-scoped-edges.log`,
`green-scoped-edges.log`, `green-final-focused.log`, `green-toolhelp-regression.log`
and `package-{red,green-first,green-final}.log`. The existing source/test snapshots
are under `before/`; preservation checks and identities are in
[verification.json](verification.json). No broader application matrix was rerun.

## Separate review package

[uc001-granite-controller-edge-diagnostic-v1.zip](uc001-granite-controller-edge-diagnostic-v1.zip)
contains all four explicit helpers, a new inactive template, one runner, README and
manifest. Original packages/templates are untouched. The exact build command was:

```python
result = module.build_package(root, receipt/'package',
    receipt/'Run-OwnershipDiagnostic.ps1', receipt/'package-readme.md')
```

| Item | Identity |
|---|---|
| ZIP size | 32,303 bytes |
| ZIP SHA-256 | `f944a4c051147abe28db40cfe173c2284f24b7a5ac9fc8058ac6e78b62032e72` |
| Manifest SHA-256 | `17fc800cffafa91a3fac3f826db7542d911a693a06cd04f5b509b1dd550a852a` |
| New inactive template SHA-256 | `6e3fd2efaa86c333ddd822c9a22fafb4e84795739a28ea8067ee10a192951692` |

## Future owner command — NOT AUTHORIZED / NOT EXECUTED

This is the exact future Windows PowerShell block, **only after separate explicit
owner authorization**, with the ZIP saved at the path shown. `-OwnerAuthorized`
records that later approval; its presence here does not grant approval. The runner
rejects omission of the switch before reading the package or invoking Python.
No command below was executed. Fresh destination only; no retry or fixes on failure.

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $GraniteArchive = 'C:\Users\AndiWand\Downloads\uc001-granite-controller-edge-diagnostic-v1.zip'
    $GraniteDestination = 'C:\Users\AndiWand\Downloads\granite-controller-edge-diagnostic-v1'
    if ((Get-Item -LiteralPath $GraniteArchive).Length -ne 32303 -or
        (Get-FileHash -LiteralPath $GraniteArchive -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'f944a4c051147abe28db40cfe173c2284f24b7a5ac9fc8058ac6e78b62032e72') {
        throw 'Diagnostic archive integrity differs: stop.'
    }
    if (Test-Path -LiteralPath $GraniteDestination) {
        throw 'Diagnostic destination exists: preserve it and stop.'
    }
    Expand-Archive -LiteralPath $GraniteArchive -DestinationPath $GraniteDestination -ErrorAction Stop
    & powershell.exe -NoLogo -NoProfile -NonInteractive -File (Join-Path $GraniteDestination 'Run-OwnershipDiagnostic.ps1') -ExpectedManifestSha256 '17fc800cffafa91a3fac3f826db7542d911a693a06cd04f5b509b1dd550a852a' -OwnerAuthorized
    if ($LASTEXITCODE -ne 0) {
        throw 'Diagnostic failed: preserve complete output and stop without fixes/retry.'
    }
}
```

The runner uses only the approved isolated Python 3.12.11 executable and writes a
fresh sibling `ownership-edge-diagnostic-<GUID>` result/log directory. Native
ownership remains unverified. No new attempt, acquisition/build, resource-fit,
model suitability or later gate is approved by this preparation. Priority 5 owner
acceptance and the closed Qwen result remain; Priorities 3/4 are partial, Priority 6
and Phase 4 pending. Stop for owner review.
