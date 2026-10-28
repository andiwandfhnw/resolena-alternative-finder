# Offline Windows environment-key correction — 2026-10-28

**Step 4 is CONSUMED and FAILED at environment validation. No retry/native
execution is authorized.** This supersedes only the pending-execution status in
the earlier handoff/approval records; those records and the issued v2 package
remain unchanged. PHASE: 3 / STATUS: in-progress.

## Failure and evidence boundary

The [owner-supplied excerpt](owner-failure-excerpt.txt) reports
controller.native_run -> worker.validate_environment(os.environ), then
WorkerFailure: frozen_x64_environment_not_active. The full raw desktop traceback
and existing approved config/approval record were not supplied/read by Codex.
Preserve whatever the owner retained; no missing traceback or artifact is recreated.
The advisor inspected the package/Python documentation statically, without package
execution, tests or Windows work. Codex's tests below ran in Codespaces only.

Exact [issued native_run](../uc001-granite-native-handoff-v2/package/controller.py)
ordering: Python/config validation precedes environment validation at line 918;
native-output creation (925), journal (926), private Job (929), run_session (949)
and result writing (951) follow it. Therefore the reported failing call did not
reach those operations or any owned worker/proxy/acquisition/build. T0 is created
inside run_session (727 onward), which was not reached. WorkerFailure is not in
the CLI's caught exception types (980), consistent with an unhandled traceback.
These are source-derived conclusions; desktop files/absence were not inspected.
The owner wrapper's approved config/approval writes precede controller invocation;
their actual retained contents remain owner evidence, not reconstructed output.
No result file, meter ledger, measured zero charge or acquisition T0 is invented.
The original prior receipt and cumulative/continuous-window rules are not renewed.

## Minimal correction and verification

[worker.py](../../scripts/uc001_granite_controller/worker.py) copies keys to
uppercase, reads the exact MSVC/Windows SDK pins canonically, and keeps the original
build-environment.json labels while reading their values from the prepared
canonical environment. Only four source lines change. No valid version is supplied
as a default, and no architecture/path/SDK/override guard is bypassed. Child PATH,
parallelism/smudge settings and caller nonmutation are preserved. No further
refactor was needed.

The existing [worker tests](../../tests/unit/test_granite_controller_worker.py)
add Windows uppercase/mixed-case success cases and missing/wrong version,
architecture, SDK, existing-tool/active-path and case-variant override failures.
The version-evidence case reuses the injected runner and deliberately stops at
synthetic source-init failure before any proxy/fetch; it executes no native tool.

- [RED](red.log): exact uppercase-key test failed with the reported exception
  against the unchanged issued worker; [command and source hashes](red-command.json).
- [GREEN](green.log): **38 passed, 45 deselected**; environment guards and version
  evidence only; [command and source hashes](green-command.json).
- [Minimal source diff](worker.py.diff), [test additions](test_granite_controller_worker.py.diff)
  and [current helper hashes](helper-hashes.json) are separate from issued receipts.

Commands actually executed:

~~~bash
.venv/bin/python -m pytest -q tests/unit/test_granite_controller_worker.py::test_environment_guard_accepts_windows_uppercase_keys --tb=short
.venv/bin/python -m pytest -q tests/unit/test_granite_controller_worker.py -k environment_guard --tb=short
~~~

The Windows PowerShell preflight uses its environment provider rather than a
case-sensitive copied Python dict. Static comparison of its existing lines
107–115 with worker lines 82–104 confirms matching required values:

| Shared condition | Unchanged requirement |
|---|---|
| MSVC / Windows SDK | 14.43.34808 / 10.0.22621.0 |
| Host / target | x64 or amd64 |
| Active compiler / shader compiler | Exact existing cl.exe / glslc.exe paths |
| Vulkan variables | Pinned C:\VulkanSDK\1.4.357.0 |
| Overrides | Reject nonempty CC, CXX, CMAKE_TOOLCHAIN_FILE, CMAKE_PREFIX_PATH |

Preflight additionally checks package/other SDK/version/resource observations;
this comparison does not claim identical total coverage. No preflight or closed
diagnostic was rerun. No native ownership/resource/model suitability is established.

## Hash boundary and future handoff

| Worker bytes | SHA-256 |
|---|---|
| Issued v2, preserved | 4f0dc7571edeb097ad172f5e423659e94c8026e5f2dbcb6e0f4d0874e8a32028 |
| Corrected repository worker | 7e2660e10139862c7d5542e40c5e4ad0739eea917ee97de59be3671327b8daf5 |

Controller, backend, stand-ins, accepted proxy, frozen config, prior receipt and
issued ZIP/manifest are unchanged. A future **separately authorized** handoff must
bind the corrected worker in its four-helper map and update its versioned inactive
configuration, manifest, inventory, archive and derived hashes. Those new artifact
hashes are not invented here. Do not edit the issued v2 package, existing desktop
approved files or historical preparation bindings; no new config/package is
generated or activated, and no owner retry approval is inferred.

[Verification/preservation receipt](verification.json) records exact commands,
limits of evidence, diffs/hashes and read-only Git checks. The historical TASKS
whitespace warning is retained. No Windows, network, real source/model acquisition,
configure/build/compiler/glslc/GPU/server/inference, installation or Git delivery.
Priorities 3/4 remain partial; Priority 6/Phase 4 pending. Stop for review.
