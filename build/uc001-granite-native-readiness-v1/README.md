# Native ownership result and acquisition/build readiness — 2026-10-26

The owner reports the authorized console-helper Windows attempt **consumed and
successful**. The corrected ownership/helper blocker is **CLOSED for this harmless
self-test model**. [Supplied result fields](owner-success.json) preserve the six
base identities, four helpers, exact nine owned exits, unrelated survival/cleanup,
verified helper exits/handle closure, no failures and approximately 0.688 seconds.
Resource fit remains false. This is owner-executed evidence, not a Codex Windows
run; no missing birth records, exit codes or desktop files are reconstructed.

## Gates satisfied at their accepted scope

| Gate | Evidence reused and limit |
|---|---|
| Harmless Windows ownership/helper model | Owner-accepted pass: suspended association/resume, root/child/grandchild ownership, nine owned exits, outside pair/helper cleanup and handle closure. No rerun. |
| Conservative acquisition meter | [Accepted proxy preparation](../uc001-granite-acquisition-proxy/README.md): cumulative upstream debit before forwarding, no bypass/reset/guessed zero. Offline preparation, not a Windows fetch result. |
| Native source/build route | [Accepted procedure](../uc001-granite-native-build-preparation/README.md): Windows x64/MSVC/Vulkan; llama.cpp commit 620d2225cc436ab0b001e3200e590e3b286ef9ab, frozen flags and model-free target. No source/build execution. |
| Build memory definition | Preserved owner decision: 25,769,803,776 bytes aggregate Job committed virtual memory, **not RSS**; host available-memory floor is separate. |
| Python/application dependency path | [Owner-reported Windows compatibility](../uc001-granite-tool-discovery-v1/README.md): isolated Python 3.12.11 and one synthetic API/SQLite save path. No model/native-build suitability follows. |
| Installed Vulkan SDK | [Owner installation result](../uc001-granite-native-build-preparation/README.md): 1.4.357.0, headers/libs/glslc and direct SPIRV-Headers CONFIG target verified. Earlier verifier false negative is preserved. |
| Frozen settings/ceilings | Existing pins, flags, outer parallelism and limits remain unchanged. No new allowance or measured workload fit is inferred. |

## Concrete remaining gates

**Real acquisition/configure/build execution should not yet be proposed.** One
source-confirmed composition defect remains outside the closed harmless test:

- [worker.py](../../scripts/uc001_granite_controller/worker.py), `child_identity`
  / `NativeRunner.start` (lines 104–149), records `Popen.pid` and its retained
  launcher creation identity.
- The acquisition path (lines 288–296) launches the proxy through `sys.executable`
  and requires its readiness PID to equal that launcher PID.
- The unchanged [accepted proxy](../../scripts/uc001_granite_acquisition_proxy/proxy.py)
  emits its executing interpreter's `os.getpid()` in readiness (line 482) and the
  listening ledger (line 128).
- [controller.py](../../scripts/uc001_granite_controller/controller.py),
  `PhaseMonitor` (lines 369–406), carries the launch identity into proxy lifecycle
  and ledger-PID validation.

For the demonstrated Windows venv launcher → interpreter split, those identities
are distinct. The current source would reject `proxy_readiness_identity_differs`
before fetch; merely relaxing that comparison would leave the controller's ledger
binding wrong. This is read-only source analysis, **not an executed failure**.
The ownership/helper self-test is not reopened; its successful result remains closed.

Independent execution inputs also remain mandatory:

1. A complete owner-reviewed prior-download receipt, tied to the frozen bundle and
   its exact SHA-256, with explicit integer prior charge. No such reviewed receipt
   is established by supplied evidence. The [template](../uc001-granite-acquisition-proxy/prior-budget.template.json)
   is still incomplete; absence of acquisition in harmless tests does not imply
   prior zero or a renewed 10-GiB allowance. `proxy.load_prior` (lines 412–422)
   enforces this gate.
2. Separate explicit execution approval and a fresh approved configuration binding
   current corrected helper hashes, accepted proxy hash, frozen config and reviewed
   prior SHA. `controller.validate_native_config` (lines 548–570) enforces these.
   Existing templates remain inactive and historical; none is activated here.
3. At future authorized entry: exact shell-local pinned MSVC/Windows/Vulkan SDK
   activation, tool selection/version checks, fresh fixed native root and separate
   fresh evidence directory, current disk/host-memory floors and healthy ongoing
   supervision. These are fail-closed run-entry checks, not established by the
   harmless pass or stale desktop observations. No fresh investigation was repeated.

All ceilings remain: acquisition **1800 s / cumulative 10 GiB**, configure/build
**2700 s combined**, Job commit **24 GiB**, generated output **12 GiB**, initial
disk **48 GiB**, stop below **8 GiB disk / 4 GiB host available memory**, outer
parallelism **2**. Committed Job memory remains distinct from RSS. GPU/VRAM,
server/client RSS, model startup and semantic review are later gates; they are not
new prerequisites for a model-free build and are not reopened here.

## Exactly one smallest blocking preparation

**Recommendation only — NOT AUTHORIZED / NOT EXECUTED:** one bounded **offline
worker ↔ proxy ↔ controller identity-binding correction preparation**.

Use the already accepted launcher/interpreter ownership model to distinguish the
proxy's retained launch identity from its executing/listening interpreter identity.
Bind both through strict PID/creation/native-parent/private-Job evidence; carry the
actual interpreter identity through readiness, listening-ledger validation and exit
evidence while retaining launcher cleanup proof. Keep the accepted proxy bytes,
native procedure, all pins/limits and closed harmless self-test unchanged.

The proposed owner scope is focused injected TDD for split and unchanged identities,
wrong/reused PID or birth, parent/member mismatch, wrong readiness/ledger PID and
missing identity-bound exits; then the smallest worker/controller correction and
a separate inactive hash-bound review artifact. Stop for owner review. No Windows
execution, live proxy/service/network, source acquisition, compiler/glslc/configure/
build, model work or ownership-test rerun is part of that proposed preparation.
It is not implemented or authorized by this readiness review.

## Checks and stopping point

Only relevant current source/accepted receipts were read. No tests, ownership
reruns, native calls, services, downloads, source fetch, configure/build, compiler,
glslc, GPU/model actions or inference occurred. Prior evidence and application code
remain unchanged. Documentation/link checks, evidence preservation and read-only
Git checks are recorded in [verification.json](verification.json).

PHASE: 3 / STATUS: in-progress. Priority 5 acceptance and closed Qwen result remain;
Priorities 3/4 partial; Priority 6/Phase 4 pending. Stop after this readiness review.
