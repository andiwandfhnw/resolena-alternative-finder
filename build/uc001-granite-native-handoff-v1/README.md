# Final native handoff review — stopped on lifecycle conflict, 2026-10-27

**Execution remains unauthorized. No final execution-configuration draft,
transfer package or acquisition/build command is issued.** The requested stop
condition applies: the default acquisition controller retains a lifecycle gap
that the separate successful diagnostic handles. No implementation is changed.

## Accepted owner-executed diagnostic

The [supplied owner report](owner-proxy-binding-result.txt) is owner-executed,
advisor-reviewed console evidence. The one authorized attempt is **consumed and
successful** in scope `harmless_network_free_proxy_binding_only`: native binding,
suspended assignment, zero acquisition events, network guard and both identity
cleanups verify; private Job lifetime/active counts 5/0, all five matching zero
exits and required handle closures, failure reason null, prior/cumulative bytes
0/0. Resource fit remains false. Execution timestamps and owner-retained desktop
directory are preserved exactly. Codex neither executed Windows nor inspected
desktop files; individual PID/birth records absent from this report are not invented.

The native proxy-binding blocker is **CLOSED for that demonstrated diagnostic**.
The earlier harmless ownership/helper model remains CLOSED. Neither is rerun or
reopened by the separate default-controller issue below. No acquisition/build,
GPU/model/inference or ownership-self-test rerun occurred in the supplied report.

Supplement, 2026-10-27: the owner subsequently supplied the
[complete console text](owner-proxy-binding-console.txt), now preserved separately
from the earlier summary. Its internally consistent chain is controller 51008 →
worker launcher 56344 → worker interpreter 56388 → proxy launcher 56428 → proxy
interpreter 56444. Worker helper 56352 is marked accepted, exit-zero, query-closed
and never directly terminated; its birth matches the expected/exited identity.
This result does not supply that helper's parent/image path or the ledger/guard
contents, so none is inferred or claimed inspected. Proxy helper list is empty.
All five PID/birth pairs match the expected set and zero-exit list. Reported
pending verified helpers are zero. The supplied elapsed value and UTC timestamps
are preserved independently. This strengthens the recorded diagnostic evidence
without exercising the separate native acquisition loop or changing its gap.

## Exact conflict and smallest required correction

The real `native_run` calls the existing two-phase `run_session`, rather than the
diagnostic's `run_binding_session`:

- [controller.py](../../scripts/uc001_granite_controller/controller.py), lines
  682–686: accept one journal batch, poll proxy exits, then drain the terminal tail.
  A worker can durably record valid planned close and finish between the first
  read and the exit query. The monitor then sees an exit before consuming its
  existing close evidence and can reject it as premature.
- Lines 689–690 require **zero active descendants immediately** after the phase
  worker launcher exits. A previously verified console helper finishing during
  bounded cleanup is rejected before that cleanup can establish its exit proof.
- The accepted diagnostic's separate
  [proxy_binding_selftest.py](../../scripts/uc001_granite_controller/proxy_binding_selftest.py)
  drains durable events when exits are observed and permits only verified helpers
  to finish during bounded cleanup, retaining exact final exits/zero active count.
  Its preserved [fast-close RED](../uc001-granite-proxy-binding-selftest-v1/controller-fast-close-red.log)
  and [helper-lag RED](../uc001-granite-proxy-binding-selftest-v1/controller-helper-lag-red.log)
  demonstrate these failure classes offline. They were not rerun or represented
  as fresh Windows failures of the real acquisition path.

This is a source-confirmed default-controller composition gap and possible false
failure, not a Job Object/binding failure or a request to relax identity rules.
The diagnostic pass does not transfer its separate orchestration into `run_session`.

**Smallest required change, requiring separate authorization:** a bounded offline
correction of that existing native loop, reusing the diagnostic's durable-tail
ordering and bounded already-verified-helper exit handling. Keep genuine premature
exits, unknown processes, missing cleanup and changed identity evidence fatal;
retain all final exit/handle proofs, deadlines and limits. Use focused injected
tests for this composition only. No new framework, helper role, native diagnostic
rerun or real execution is proposed. No correction is implemented here.

## Accounting and unchanged entry requirements

The accepted prior receipt remains SHA-256
`56a85b9ded9d6c4bf504462e11d551b59e016fcd1c77d8c5102b93ff7df7475a`,
including its historical preparation bindings. Current execution helper hashes
must be bound separately; the current worker hash is recorded with the other
reviewed inputs in verification.json. No stale template is activated.

Source bytes would be charged cumulatively by the accepted proxy. A later reviewed
carry-forward receipt must derive its prior total from the actual validated source
ledger and its original prior-receipt hash, preserving the accepted zero receipt.
No source ledger exists yet; no later charge is calculated or receipt fabricated.
The original real acquisition UTC start must carry forward unchanged. The
[proxy CLI](../../scripts/uc001_granite_acquisition_proxy/proxy.py) rejects age
1800 seconds or greater; elapsed build/review time does not pause or renew that
continuous window. Later model acquisition is permitted only within remaining
time and bytes; exhaustion means stop. The diagnostic timestamps/ledger are not
a real acquisition start. This conditional exhaustion is not a new blocker or
an authorization to amend the frozen 1800-second/10-GiB allowance.

No tool/path/flag mismatch was found in the narrow review. Remaining Windows-only
entry observations, after correction and separate execution approval, remain:

- Successful existing shell-local VS2022 activation for x64, MSVC 14.43.34808 and
  Windows SDK 10.0.22621.0; exact Git/CMake/Ninja/compiler paths/versions and no
  unreviewed toolchain overrides, using the
  [accepted native procedure](../uc001-granite-native-build-preparation/README.md).
- Pinned Vulkan SDK 1.4.357.0 environment, compiler path, headers/library and
  SPIRV-Headers CONFIG/direct target presence; no GPU or glslc probe.
- Fresh fixed native root and separate fresh evidence destination; initial disk
  >=48 GiB, stop below 8 GiB disk/4 GiB OS available memory, healthy independent
  supervision and exact frozen caps. Resource fit is not passed by old observations.

The controller must own root creation and metered phases; the old procedure's
manual root-creation/unmetered fetch blocks must not also be executed. Existing
activation is reusable. The diagnostic no-network bootstrap is not the real Git
acquisition route. A future separately approved execution scope would remain only
pinned runtime-source acquisition and model-free llama-server compilation,
including the accepted configure/compiler/glslc/shader-generator build work;
no model weights, GPU probe, server startup or inference. An executable approval
handoff is withheld until the lifecycle gap is corrected and reviewed.

## Checks and stopping point

Only relevant source/accepted receipts, read-only hashes, documentation links and
Git preservation were checked. Existing diagnostic evidence was reused. No tests,
Windows execution, live proxy/network, source acquisition, configure/build,
compiler/glslc, GPU/model/inference, installation or persistent policy change.
No application, proxy, identity policy, frozen pin/limit or historical receipt is
changed. Verification records the unchanged input hashes and preservation results.
Priority 5 acceptance, closed Qwen result, reference permissions, unconfigured
app.main and inactive real drafts remain. Priorities 3/4 partial; Priority 6 and
Phase 4 pending. PHASE: 3 / STATUS: in-progress. Stop for owner review.
