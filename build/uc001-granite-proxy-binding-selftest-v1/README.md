# Windows proxy binding self-test preparation — 2026-10-27

**OFFLINE PREPARATION ONLY. Future Windows execution: NOT AUTHORIZED / NOT EXECUTED.**
The owner accepts the [final prior-accounting receipt](../uc001-granite-prior-accounting-final-v1/prior-budget.json),
closing that preparation gate for the frozen Granite allowance. Its zero charge
rests on the explicit complete owner statement, not independently measured history.
The accepted receipt, proxy and all previous receipts/packages remain unchanged.
The successful harmless ownership/helper self-test remains CLOSED and was not rerun.

## Exact invariant and execution boundary

This separate diagnostic must establish, within **20 seconds including cleanup**:

1. The controller stays outside a fresh private Job. The owned worker is created
   suspended with atomic Job List association, checked before resume, with no
   breakaway and kill-on-close. Worker launcher/interpreter identities are distinct
   when the Windows venv redirector splits them; native parent, PID, creation
   FILETIME, stable retained handles and exact Job membership must agree.
2. That verified worker launches the exact accepted proxy behind the separate
   no-network guard. The actual corrected `NativeRunner.bind_proxy` and
   `PhaseMonitor` bind proxy launcher and interpreter independently, including
   the exact launcher parent. Only verified binding permits `PROXY_BOUND\n` over
   the owned worker's private pipe. Missing ACK remains failure.
3. Each applicable split launcher may have zero or one accepted system console
   helper, using the unchanged validator: exact GetSystemDirectoryW-derived
   conhost path, parent, stable PID/birth, expected membership and no query errors.
   It is an interpreter sibling under its launcher. Same-process paths require
   the same retained native identity and reject extra children conservatively.
4. The complete private-Job PID/birth set and lifetime count must equal the known
   worker/proxy identities plus accepted helpers. Extra processes, replacements,
   wrong paths/parents/membership and unqueryable identities remain failure.
5. Readiness and the listening ledger must name the verified proxy interpreter.
   The guard permits exactly one IPv4 loopback ephemeral listener, installs before
   executing the hash-verified proxy buffer, and blocks DNS, outbound connect/send,
   process launch and native-symbol access before those operations. No CONNECT
   client is created. Any forbidden attempt or guard-ledger failure fails.
6. Both worker and controller reject any CONNECT, tunnel, debit, outbound or unknown
   meter event, including zero-byte events. Only start/acquisition_clock/listening/
   end records are allowed; every counter stays at the accepted prior charge 0,
   with no tunnel identity/destination and the exact accepted prior SHA at start.
7. After verified ACK/listening, the worker records planned close and sends CLOSE.
   Both proxy roles require native zero exits, and worker query/Popen/log handles
   require explicit closure proof. Durable close events are consumed before judging
   a rapidly observed exit; unplanned exits and invalid branch evidence still fail.
8. Both worker base identities must exit zero. Verified helpers may finish during
   bounded Job cleanup; final active count must be zero with matching identity-bound
   exits for every expected process. Owned helpers require private-Job wait/exit
   proof and matching query readback. Every query and private-Job handle must close.
   Helpers/unclassified children are never directly terminated; failure/deadline
   stops only the owned Job and preserves evidence, without retry.

The 24-GiB Job committed-memory cap remains **25,769,803,776 bytes, not RSS**.
No frozen resource ceiling, build flag, backend or model/runtime pin changes.
The diagnostic's reused acquisition event names and UTC clock are diagnostic
observations only; they do not start, reset, renew or certify a real acquisition
allowance. The real acquisition start/approval gates remain separate.

## Changes and offline evidence

Only existing implementation file changed:
[worker.py](../../scripts/uc001_granite_controller/worker.py), adding an explicit
proxy-binding-selftest entry/CLI phase, worker identity observation and self-test
handle-closure proof. Existing acquisition/build functions and existing NativeRunner
methods remain AST-identical. New
[proxy_binding_selftest.py](../../scripts/uc001_granite_controller/proxy_binding_selftest.py)
orchestrates the unchanged controller/backend/helper logic;
[proxy_no_network.py](../../scripts/uc001_granite_controller/proxy_no_network.py)
guards execution of the exact accepted proxy bytes. Normal app.main is untouched.

RED receipts include the absent guard/controller entry, 20 missing worker-entry
failures and four missing-package failures. Additional RED checks caught uncertain
close retry, planned-close event timing, deadline coverage during cleanup, worker
parent binding, strict handle-proof values, structured entry-failure evidence and
helper exit lag. Intermediate fixture/import/clock wiring failures and their later
GREEN results remain in the raw logs; no overwritten evidence is reconstructed.
The original 44-pass controller log and subsequent 45-pass log are both retained,
despite reuse of a temporary filename. New bridge tests passed first time and make
no separate RED claim.

Final command ([raw result](green-final-focused.log), [exact invocation](green-final-command.json)):

```bash
.venv/bin/python -m pytest -q tests/unit/test_granite_proxy_no_network.py tests/unit/test_granite_proxy_binding_worker.py tests/unit/test_granite_proxy_binding_selftest.py tests/unit/test_granite_proxy_binding_flow.py tests/unit/test_granite_proxy_binding_package.py tests/unit/test_granite_controller_worker.py
```

**157 passed in 2.37s**, exit 0: 22 guard, 27 new worker, 49 controller,
8 worker-produced-event/real-monitor flow, 4 package and 47 existing worker checks.
All process/native/socket operations in these journeys are injected; no live proxy,
loopback listener or ownership test ran. The flow tests use the actual new worker,
NativeRunner binding, controller ACK/monitor and helper validator. Focused failures
cover the required identity/helper/ACK/premature-exit/cleanup and zero-event guards.
The closed ownership/backend suites, application/model tests and broad matrices
were excluded.

[Isolated flat-package imports/config/hash checks](codespace-package-structural.json)
passed with native/network/process operations blocked. Linux PowerShell parser
accepted the wrapper without invoking it ([syntax receipt](powershell-syntax.log)).
These are preparation checks, not Windows-native success or runtime suitability.

## Package identities

[uc001-granite-proxy-binding-selftest-v1.zip](uc001-granite-proxy-binding-selftest-v1.zip)
contains 14 flat files and is **59,475 bytes**.

| Item | SHA-256 |
|---|---|
| ZIP | `cd901381d3570224b954cab750a38326747947e718b57679e4e8632eec2aa666` |
| Manifest | `7acfe1635098f627ad29e9fa0156e2299e3cee63dcac6c5579de213b3b80d89e` |
| Self-test config | `0bfbcda1255808b1fc46a25006962b4d19a795d4744355bd1ca3ba97f2f47825` |
| Accepted proxy, unchanged | `a7c62f83356636bea839633382bb62a3e53bcce466caea7b32226cece1e7bb1d` |
| Accepted prior receipt, unchanged | `56a85b9ded9d6c4bf504462e11d551b59e016fcd1c77d8c5102b93ff7df7475a` |

[All helper hashes](package-result.json) and [exact manifest](package/manifest.json)
bind current source bytes. The accepted accounting receipt retains its original
historical preparation/helper hashes; it is not refrozen to include these new
self-test helpers. The new package manifest independently binds the updated worker.
The package config permits only this self-test, has no real native root or execution
authorization field, and all seven Python helper hashes must match.

## Future Windows command — NOT AUTHORIZED / NOT EXECUTED

After separate owner authorization, save the exact ZIP to Downloads and run this
single block once in Windows PowerShell. Existing destinations/results mean stop;
never overwrite an earlier attempt. The wrapper separately requires authorization,
the external manifest SHA, exact entries/hashes and approved isolated Python.

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $GraniteArchive = 'C:\Users\AndiWand\Downloads\uc001-granite-proxy-binding-selftest-v1.zip'
    $GraniteDestination = 'C:\Users\AndiWand\Downloads\granite-proxy-binding-selftest-v1'
    if ((Get-Item -LiteralPath $GraniteArchive).Length -ne 59475 -or
        (Get-FileHash -LiteralPath $GraniteArchive -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'cd901381d3570224b954cab750a38326747947e718b57679e4e8632eec2aa666') {
        throw 'Proxy binding archive integrity differs: stop.'
    }
    if (Test-Path -LiteralPath $GraniteDestination) {
        throw 'Proxy binding destination exists: preserve it and stop.'
    }
    Expand-Archive -LiteralPath $GraniteArchive -DestinationPath $GraniteDestination -ErrorAction Stop
    & powershell.exe -NoLogo -NoProfile -NonInteractive -File (Join-Path $GraniteDestination 'Run-ProxyBindingCheck.ps1') -ExpectedManifestSha256 '7acfe1635098f627ad29e9fa0156e2299e3cee63dcac6c5579de213b3b80d89e' -OwnerAuthorized
    if ($LASTEXITCODE -ne 0) {
        throw 'Proxy binding self-test failed: preserve complete output and stop without fixes/retry.'
    }
}
```

The result is a fresh sibling **proxy-binding-result-GUID** directory containing
result.json, durable controller/worker journals, stdout/stderr, generated self-test
config, proxy meter and no-network guard ledgers. Preserve the entire directory and
console output on failure. No source/build root, toolchain, Git, compiler, glslc,
GPU, model/server or inference is used. The guard is a restriction on this exact
trusted Python proxy path, not a machine-wide egress sandbox against other actors.

Readiness: **offline-prepared for owner review only**. Windows-native proxy binding,
audit behavior and cleanup in this exact package remain unverified. Resource fit
and model/runtime/semantic suitability remain unverified. No further native attempt
or real acquisition/build is authorized. Priority 5 acceptance, closed Qwen result,
reference permissions, inactive real drafts and unconfigured app.main are preserved.
Priorities 3/4 partial; Priority 6/Phase 4 pending. PHASE: 3 / STATUS: in-progress.
