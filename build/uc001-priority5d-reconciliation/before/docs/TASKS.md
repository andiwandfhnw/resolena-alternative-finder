PHASE: 3
STATUS: in-progress

(0=Bootstrap | 1=Specify | 2=Design | 3=Develop | 4=Validate | 5=Deploy)

## Current Use Case

UC-001 — Find and compare alternatives. Sole active use case.

Specification: `docs/specs/UC-001-FIND-AND-SELECT-ALTERNATIVE.md`.
The full specification remains incomplete. Original Intent, Actors and Preconditions
were approved by the owner on 2026-10-07. Original Flow was approved by the owner
on 2026-10-07, including persistence before selection. Decomposition approved on
2026-10-09 assigns original steps 1–7 to UC-001 and 8–9 to UC-003; this does not
approve the complete specifications. UC-001 increment-1 acceptance and planned
tests were subsequently accepted on 2026-10-10 as recorded in the UC and architecture;
full mandatory research and UC-003 remain pending. Earlier scoped approval history
is preserved below.

The owner selected SPECIFY on 2026-10-07, then DESIGN for UC-001 increment 1
on 2026-10-10. On 2026-10-15 the owner accepted the increment-1 integration
design as the implementation baseline and authorized DEVELOP, starting with priority 1.
The approved UC, ADR-003 and reviewed architecture were checked together: atomic
request/options/evidence persistence, saved identities, immutable snapshots and
ownership/payload-bound recovery agree; no material conflict was found. ADR-003's
pending-review wording was routine status alignment, not a changed contract.

DEVELOP remains in progress: the priority-1 saved-comparison slice and authorized
priority-2 qualification/coverage are implemented and verified with test substitutes. Interpreter
selection, production hosting, reviewed knowledge and qualified linguistic validation
remain open delivery dependencies. This does not complete increment 1 or the journey.
The bounded priority-3 contract/policy step below is implemented; priority 3 remains partial.
The subsequent offline candidate preparation is recorded next; live execution is not authorized.

Current bounded-run status: the owner reports the original single model startup
occurred and its allowance is consumed. No replacement attempt or restart is authorized.
The reported generation ledger is absent; no zero-valued ledger is reconstructed.
The tested v1.2.2 Python-branch native path remains owner-reported verified. The owner
subsequently reports the additional v1.3.0 model startup occurred and failed at
`ownership/console_helper_ambiguous`; that allowance is also consumed. No further model
startup or inference is authorized. Owner-provided corrected combined Windows receipts now
verify native/Python ownership, fresh revalidation and all five exits in 1180 ms for the
tested stand-in setup; that ownership issue is closed. Earlier cleanup failures remain
unchanged. The owner subsequently supplied the v1.4.0 export: one startup and one case-1
generation are recorded; no cases were accepted, all five exits confirmed. That allowance
is consumed. Offline exact-byte replay reproduces a domain-contract rejection; cases 2–14
were not attempted. No further startup/retry is authorized; Priority 3 remains partial.

Current authorization, 2026-10-19: Priority 5D only — actual commit with lost
persistence confirmation and failed immediate readback, then explicit same-submission
recovery. Accepted 503/persistence_error/unknown and checked acknowledgement contract
confirmed. A test-only DBAPI seam can withhold commit confirmation while a separate
observer verifies SQLite without supplying facts to application logic. Current
commit-error handling lacks the required guarded readback; only a minimal test-first
fix is authorized. No full fault matrix, browser feature, real activation, experiments
or Git delivery. Phase 3 stays in-progress; stop for human review.

Previous authorization, extended 2026-10-19: bounded Priority 4 source-bound
DE/FR/IT/EN rendering for the accepted bicycle-repair / Switzerland packet only.
The [draft packet](knowledge/UC-001-BICYCLE-REPAIR-CH-DRAFT.md)
has owner-approved factual extraction dated 2026-10-18 for the repair service,
published CHF 120.00 hourly rate and listed Oberried location, with conditions and
unknowns preserved. Applicability, candidate qualification and DE/FR/IT/EN review
remain pending, with runtime use disabled. The new
[four draft renderings](knowledge/UC-001-BICYCLE-REPAIR-CH-RENDERINGS.json) are also
inactive/pending qualified review. No knowledge release or interpreter work was authorized by that slice.

## Priority 3 — offline candidate preparation, authorized 2026-10-16

Owner authorized offline preparation only of the retained Qwen3-8B Q8_0 /
llama.cpp b11429 application-contract feasibility check: HTTP adapter, offline TDD,
explicit development composition and separate Windows/Codespace run/preflight
artifacts. Candidate only; normal `app.main` stays unconfigured. No live model or
detector, transport installation/connection, assets acquisition, held-out access,
Priority 4, requirement changes or Git delivery/branch change.

Implemented preparation: strict wire decoding and quotation-occurrence mapping;
trusted originals/versions; no recognizer, country or preference in model requests;
distinct input/meaning/capability/rendering/technical routes; frozen 14 exposed
cases/settings; qualified-review gate; authenticated loopback/proxy-bypass checks;
bounded attempt/time/resource controls and owned-process cleanup. `Velo` now expects
meaning clarification (bicycle/veil), not an unsupported forced bicycle meaning.
Mixed and numeric uncertainty follow accepted L-02/03; no requirement conflict found.
All expectations remain AI-generated, without qualified linguistic approval.

Prepared scripts have offline evidence only, not verified Windows/runtime/transport
compatibility. [Plan, exact preflight and limits](../scripts/uc001_contract_check/README.md);
[tests and unresolved prerequisites](PROJECT.md#priority-3-offline-candidate-preparation--2026-10-16).
Priority 3 remains partial; Phase 3 in-progress. Stop after this preparation.

Windows preflight follow-up, owner-reported 2026-10-16: process-only RemoteSigned
allowed execution, then `Common.ps1:38` stopped with “Read-only active-adapter/WDDM
association is ambiguous; stop without a measurement substitute.” Actual Windows
adapter/counter data is pending. Authorized diagnosis only: print exact CIM/registry/
WDDM inputs without rerunning model hashes or other checks. No matching/guard change,
native probe, installation, tunnel or inference. Frozen bundle/ZIP remain unchanged;
the reported failure is appended to `build/uc001-contract-preparation/verification.json`.

Owner-supplied follow-up confirms one CIM RX 6800 XT, present Int64 registry
capacity and two WDDM `phys_0` counters with different LUIDs. Multiple-counter
failure is established; association remains unproven. Authorized preparation only
of a separate DXGI identity/LUID diagnostic, with native compilation/call disclosure
and exact fresh-counter matching. [Diagnostic and command](../build/uc001-contract-preparation/adapter-identity/README.md).
Offline syntax/layout/compilation and synthetic states passed; actual Windows
DXGI output is pending. No guard, threshold, frozen-bundle or ZIP changes; no
asset rehash, native execution here, installation, transport, inference or held-out
access. Priority 3 remains partial; Phase 3 stays in-progress.

### Adapter-association correction v1.1.0 — 2026-10-16

Owner reports the separate Windows DXGI diagnostic identifies the RX 6800 XT
hardware and Microsoft Basic Render Driver independently, each with one matching
WDDM counter. This establishes the global-single-counter defect; raw new DXGI
output is not imported here. Authorized correction only, packaged separately:
[instructions](../scripts/uc001_preflight_association_v1_1_0/README.md) and
[ZIP](../build/uc001-preflight-association-v1_1_0/windows-preflight-association-v1_1_0.zip).
Selection requires matching hardware descriptor/all PCI identifiers, CIM/registry
device and measured capacity, a fresh unique DXGI LUID and exactly one associated
counter. Missing/duplicate/inconsistent/failed data stops; measured zero is valid.
No launcher initialization or usage/order-based selection.

TDD RED reproduced the original global-counter rejection; further RED checks
exposed invalid flags and multiple physical counters for one LUID. GREEN: **56
focused association/existing control tests passed**, using synthetic Windows data
and offline compilation/layout checks, without native enumeration. All 30 protected
original source/evidence hashes match; pins, prompt/schema/cases, budgets and resource
thresholds remain unchanged. The reported **13.651 GiB available is below 14 GiB**:
a separate resource failure, not fixed or waived by association. Windows Add-Type
compilation/native DXGI calls and possible temporary compiler files are disclosed.
Actual corrected Windows verification remains pending. New version, hashes and
evidence: `build/uc001-preflight-association-v1_1_0/verification.json`.
No asset rehash, installation, transport, inference, held-out access or Git delivery.
Priority 3 remains partial; Phase 3 stays in-progress. Stop after this correction.

Capacity follow-up, owner-reported 2026-10-16: v1.1.0 stops at
“DXGI capacity and active-device registry capacity disagree.” This is a separate
attempt from the earlier incomplete-extraction failure referenced by the owner;
neither raw transcript nor fresh capacity values were supplied here. No success
or resource acceptance is inferred. Diagnosis only: native field/layout/unsigned
conversion checks found no offline defect; exact DXGI/`qwMemorySize` byte equality
is a harness assumption without justification in the primary documentation checked.
[Separate pasteable diagnostic](../build/uc001-preflight-association-v1_1_0/capacity-disagreement/Diagnose-Capacity.ps1)
reports same-device identities, both raw types/values and an exact signed difference;
it invokes no equality/resource guard or launcher. Twenty synthetic cases and x64
layout/unsigned-conversion checks passed without native enumeration. The stopped
attempt, sources and preservation checks are recorded separately in
`build/uc001-preflight-association-v1_1_0/capacity-disagreement/verification.json`.
Original and v1.1.0 source/ZIP/guards/evidence remain unchanged; no new package,
tolerance, selected capacity source, resource waiver or Windows execution here.
Priority 3 remains partial; Phase 3 stays in-progress. Stop after diagnosis.

### Capacity-source correction v1.2.0 — 2026-10-16

Owner authorized DXGI dedicated-video bytes as the sole capacity source, removing
the unsupported registry exact-equality assumption. Supplied diagnostic excerpt
is preserved verbatim in `build/uc001-preflight-capacity-v1_2_0/owner-supplied-diagnostic.txt`:
DXGI 17130819584, registry 17163091968, signed difference -32272384 bytes;
matching CIM/PCI/DXGI identity is owner-reported, cause unknown. No complete new
diagnostic JSON or fresh resource snapshot was supplied.

Separate [v1.2.0 package/instructions](../scripts/uc001_preflight_capacity_v1_2_0/README.md)
retain registry path, raw value/type, availability/error and exact signed difference
as diagnostics only. Missing registry data supplies no fallback. Invalid/missing
DXGI capacity, identity/counter ambiguity, invalid usage and insufficient resources
still stop. Native reader, pins/configuration, prompt/schema/cases, all thresholds
and earlier bundles/evidence remain unchanged. Full fresh extraction of all nine
files is documented; no overlay of an earlier or incomplete extraction.

TDD RED reproduced rejection of both unequal-reading directions and missing registry
data; focused GREEN verifies the DXGI source, diagnostics, invalid capacity and
byte-exact resource boundaries. Final offline checks: **114 passed** (58 new,
44 earlier association/package and 12 existing run-control tests). All 46 protected
small source/evidence hashes match. Results and preservation evidence:
`build/uc001-preflight-capacity-v1_2_0/verification.json`. Actual Windows execution
remains pending; no application change, asset hashing, installation, transport,
inference, held-out access or Git delivery. Priority 3 remains partial; Phase 3
stays in-progress. Stop after offline verification of this correction.

### Remaining desktop readiness — 2026-10-16

Owner supplied the raw v1.2.0 Windows JSON, preserved separately at
`build/uc001-desktop-readiness/windows-v1_2_0-result.raw.json`. Record only a
**successful adapter-identity/resource snapshot**: DXGI capacity 17130819584,
GPU free 15045484544 and unchanged start threshold 15032385536 bytes leave
**13099008 bytes**. Fresh v1.2.0-policy checking is required before any future
authorized startup. Full preflight, interpreter suitability and Priority 3 are
not complete; historical pending/failure records remain unchanged.

Integrity audit: the original reported adapter failure follows successful
`Get-ContractAssets`, which covers the runtime ZIP, model and all 52 extracted
runtime files. Historical completion of those 54 checks follows from frozen code
order plus the reported unchanged original command, not a new hash receipt or
current-content proof. No original checks remain uncompleted on that evidence;
fresh integrity validation still belongs before future authorized execution.

[Remaining read-only checker and exact Windows instruction](../scripts/uc001_desktop_readiness/README.md)
query existing native OpenSSH/gh versions and desktop ports 49187/49189 only;
Codespace 49188, transport setup/authenticated binding and qualified semantic review
remain pending. It sources v1.2.0, never the original failing preflight. A concrete
execution blocker is preserved: the original launcher matches only AMD vendor/name,
and its monitor uses loose counter-prefix/unchecked usage rules rather than v1.2.0
identity/capacity/usage enforcement. DXGI capacity itself is already used by the
original launcher. No launcher/monitor correction is authorized or implemented here.
Offline checks: **124 passed** (10 new, 114 retained); all 60 prior small
source/bundle/evidence hashes match. Evidence: `build/uc001-desktop-readiness/verification.json`.
No installation, auth/credential inspection, connection, runtime/model startup,
inference, held-out access or Git delivery. Priority 3 partial; Phase 3 in-progress.

### Launcher/monitor correction v1.3.0 — 2026-10-17

Owner authorized only the confirmed launcher/monitor incompatibility correction,
offline implementation and a separate execution bundle. Originals and historical
evidence remain unchanged. [New bundle documentation](../scripts/uc001_execution_v1_3_0/README.md).
Startup and runtime samples invoke v1.2.0 complete hardware/CIM/PCI/LUID identity,
DXGI capacity and exact adapter-counter policy; every sample revalidates the
selected identity/capacity rather than remapping. Owned measurements require the
exact PID/selected-LUID/phys_0 row and stable alive process identity before/after
sampling. Missing/invalid measurements stop; measured zero and no-owned-process
`not_applicable` states are distinct. Strict RSS/RAM/disk/artifact bounds preserve
all original thresholds. Cleanup failure cannot skip owned job/process cleanup.

The new receipt/review uses its new freeze, while the original attempt-directory
key remains unchanged across versions: no restart or budget reset. Config/pins,
prompt/schema/exposed cases, native ownership helper, semantic-review gates,
deadlines, sampling intervals and 1-startup/14-generation limits are preserved.
The copied runner changes only versioned module bindings; application code is unchanged.

TDD first rejected the missing runtime identity revalidation and exposed missing/
foreign owned counters being accepted as zero. Synthetic launcher tests exercise
actual startup/monitor/abort/cleanup dispatch with fake native/process/HTTP actions;
they are not Windows runtime verification. **174 offline tests passed** (50 new,
124 retained); all 76 prior small artifact/application-pin hashes match. Changed files, package
hashes and preservation evidence: `build/uc001-execution-v1_3_0/verification.json`.
Actual Windows owned-counter/lifetime/cleanup behaviour, desktop tools/ports,
transport prerequisites and qualified review of the exact new freeze remain pending.
No live execution, model/asset hashing, installation, credentials, transport,
held-out access or Git delivery. Priority 3 partial; Phase 3 stays in-progress.

### Supplied remaining-desktop result — 2026-10-17

Raw owner output preserved at
`build/uc001-desktop-readiness/results_2026_10_17/remaining-desktop-result.raw.json`.
The remaining desktop check passed: native/PATH OpenSSH **9.5p2 / LibreSSL 3.8.2**,
portable gh **2.81.0**, and no observed TCP allocations at **49187/49189** during
the check. No execution timestamp was supplied; record the reporting date only.
Integrity remains historical inference for 54 checks, not a fresh hash receipt.
Codespace 49188, actual binding/forwarding, fresh startup integrity/resources,
Windows owned-process monitoring/cleanup and qualified semantic review remain pending.

The raw checker's static `ExecutionBlocker` refers to the preserved original
launcher. Its separate v1.3.0 correction is implemented/offline-verified above;
this result neither reverses that work nor verifies Windows runtime execution.
Full preflight and startup authorization remain false. All raw fields and earlier
bundles/failures are preserved; only documentation/evidence recording changed.
Checks/interpretation: `build/uc001-desktop-readiness/results_2026_10_17/verification.json`.
Priority 3 remains partial; Phase 3 remains in-progress. No further execution authorized.

### Model-free native ownership diagnostic preparation — 2026-10-17

Owner authorized a separate Windows native ownership/cleanup diagnostic, not model
startup. [Diagnostic, effects and exact command](../scripts/uc001_native_ownership_check/README.md)
reuse unchanged v1.3.0 process/job, PID/creation-time and abort/cleanup functions
with a sleeping owned child, a 60-second supervisor budget and failed/unconfirmed
cleanup rejection. No GPU measurement is requested or substituted. Windows results
remain pending, as do real owned-GPU counters/allocation and authorized startup.
Earlier bundles, attempt ledgers, thresholds and evidence remain unchanged.
Offline TDD/results: `build/uc001-native-ownership-check/verification.json`.
Priority 3 remains partial; Phase 3 remains in-progress. Stop after preparation.

### Supplied native result and transport preparation — 2026-10-17

Raw Windows result: `build/uc001-native-ownership-check/results_2026_10_17/windows-native-result.raw.json`.
The tested PID/creation-time, deliberate abort, native owned-job close and child
exit-confirmation path passed: 919 ms overall, 256 ms worker, no reported errors.
This verifies only that tested native path; GPU counters/allocation, complete
failure matrices, model readiness and semantic suitability remain pending.

Owner authorized transport preparation and remaining Codespace read-only checks
only. Port 49188 has no observed allocations; sshd is absent. All eight cached
package/version/size/SHA-256 records and the solver match the v1.3.0 plan. Reuse
recorded Windows OpenSSH/gh observations; portable gh acquisition is complete.
After its 18317085 bytes and planned Debian 7508700 bytes, 79031815 bytes remain
under the original 100 MiB cap, before any additional preparation-file transfer.
[Exact proposed setup/authentication/connection and bounded model-free cleanup check](../scripts/uc001_transport_preparation/README.md).
Actual provider-managed sshd configuration/loopback compatibility is a connection
gate, not an assumption. No setup, credentials, connection or model execution here;
all frozen bundles, thresholds and model-attempt ledgers remain unchanged.
Evidence/offline checks: `build/uc001-transport-preparation/verification.json`.
Priority 3 partial; Phase 3 in-progress. Stop after preparation for owner review.

### Approved Codespace transport setup — 2026-10-17

Owner approved reviewed transport-only install/configuration, needed owner-operated
Windows authentication/key authorization and one bounded model-free connection test;
no repeated approval is needed for those matching actions. Codespace setup passed:
exact simulation/pins and existing exit-101 policy rechecked; eight archives
(7508700 bytes) acquired once, size/SHA-256 verified and installed once; package
audit clean. Planned drop-in created without overwrite, `sshd -t` and effective
loopback/authentication/remote-forward settings passed. No sshd, connection, restart
or index refresh was initiated; service policy, frozen work and model ledgers remain.
[Receipt and exact owner-operated Windows handoff](../build/uc001-transport-setup/README.md).
Actual gh-managed listener compatibility and both Windows test / separate Codespace
49188 cleanup receipts remain pending. GPU/model readiness is unverified. Priority 3
partial; Phase 3 in-progress. No model, held-out, later-priority or Git delivery work.

### Failed model-free transport attempt — read-only diagnosis, 2026-10-17

Owner reports the approved single attempt failed after 7791 ms during banner
exchange (`Connection refused`, exit 255); separate Codespace 49188 cleanup passed
at 15:58:42.517847 UTC. Supplied excerpts/authentication metadata are preserved
[separately with the diagnosis](../build/uc001-transport-diagnosis/failed_attempt_2026_10_17/README.md).
Surviving sshd PID 61844 owns 127.0.0.1:22; drop-in/default settings remain intact.
Available broker log snapshots predate the attempt; the refusing hop and original
broker target remain unproven. No server change is justified yet. A targeted
Windows `ssh -G` inspection is provided; no connection or service/configuration
action was taken, no new harness or broad tests run. The one approved attempt
failed; no retry was performed. Frozen bundles and prior evidence are unchanged.
Priority 3 remains partial; Phase 3 remains in-progress.

### Logging-only transport preparation — 2026-10-17

Owner-supplied Windows `ssh -G` summary confirms localhost/vscode/49189,
addressfamily any and no emitted proxycommand/proxyjump; preserved separately.
No proxy/IPv4 override applied. [Separate logging variant and review command](../build/uc001-transport-logging/README.md)
reuse the unchanged transport flow, ownership/authentication/loopback/deadline and
cleanup controls, adding private local GH_DEBUG=1 / OpenSSH -vvv/-E logging and a
fixed-field shareable summary. Pinned gh debug-file flags are unused and its
tunnel logger discards output; broker-target visibility cannot be promised.
Offline RED: 12 absent-variant failures; GREEN: 26 focused new/retained checks.
First-attempt Windows `cleanup.json` is still needed; separate Codespace cleanup
already passed. No connection, endpoint or native startup, config/service action,
new model attempt or retry. Original scripts/evidence preserved. Windows ACL and
actual logging/transport remain unverified. Priority 3 partial; Phase 3 in-progress.

### Logging wrapper parser correction v2 — 2026-10-17

Second Codespace cleanup receipt preserved byte-for-byte: passed at
16:52:10.674073 UTC. The supplied sanitized Windows summary is preserved separately:
failed after 4062 ms, limit not exceeded, owned cleanup confirmed, gh log present,
separate SSH log missing and all reported stage/error markers false. Its pending
Codespace-cleanup field is retained verbatim and linked to the later receipt;
missing markers do not establish the root cause or connection progress.
The earlier gh `-E` support claim was wrong: its pinned option-value list omits E,
so the log path/remaining controls become command tokens. The old wrapper and both
attempts' evidence remain historical and unchanged. [Separate v2 correction](../build/uc001-transport-logging-v2/README.md)
removes only -E/path, keeps -vvv and reads the combined private transport stderr
with honest source metadata. Source-derived parser replay verifies complete
controls/destination/remote command; Go binary execution was unavailable.
RED 9 failures/2 passes; GREEN 37 focused new/retained checks. Original privacy,
ownership/authentication/loopback/deadline/cleanup paths are retained. A targeted
Windows metadata-only check is provided for a possible gh-bin `-p` file; existence
and privacy are unverified. No connection/native startup, service/config change,
tool acquisition or retry; first refusal remains unresolved. Priority 3 partial;
Phase 3 in-progress.

### Third model-free transport attempt — evidence-only diagnosis, 2026-10-17

[Separate attempt record](../build/uc001-transport-diagnosis/attempt_3_2026_10_17/README.md)
preserves owner-pasted v2 Windows JSON, not an original-file byte receipt: failed
after 6771 ms, localhost bridge connected, banner refusal, Windows owned cleanup
confirmed. Existing Codespace cleanup pass at 18:08:04.291430 UTC is linked
unchanged; the pasted pending field is retained. Fresh SSH observation binds
127.0.0.1:22, but identified broker log snapshots lack attempt-time entries and
the startup artifact is unchanged. Actual broker destination/error and any
destination/listener mismatch remain unproven. Stop diagnosis; the one proposed
next action is an operator-provided sanitized existing host-broker trace for this
attempt, without another connection. Earlier attempts/bundles remain intact;
no new wrapper, regression rerun, service/config action or model work. Priority 3
partial; Phase 3 in-progress.

### Fourth model-free transport attempt — evidence recording, 2026-10-17

[Separate attempt record and unsent Support draft](../build/uc001-transport-diagnosis/attempt_4_2026_10_17/README.md)
preserve owner-pasted v2 JSON: failed after 5819 ms, bridge connected then banner
refusal, Windows owned cleanup confirmed. The unchanged Codespace cleanup
receipt passed at 18:30:57.818745 UTC; the pasted pending field is retained.
Markers match attempt 3. Owner reports VPN enabled for attempt 3 and desktop/browser
NordVPN connections disconnected for attempt 4: disconnecting them did not resolve
the observed failure. Other NordVPN filtering components are unverified; root
cause remains unknown. Existing diagnosis reused; no new log/process searches.
Support draft requests existing host-broker destination/port/network context,
associated errors and reachability to the historically observed 127.0.0.1:22
listener. Cleanup timestamps are not known attempt-start times; trace availability
is unknown. Draft not sent; no new attempt, wrapper, regression or system action.
Prior evidence preserved. Priority 3 partial; Phase 3 in-progress.

### Windows shared-validator setup preparation

SSH diagnosis/retries and Support preparation are paused by the owner. Authorized
environment-only preparation extends the existing cumulative 100 MiB allowance:
per-user Python 3.12.10 x64 at the requested tools path, dedicated validator venv,
unchanged shared validation and pinned binary wheels. Python 3.12.10 is the last
official 3.12 Windows installer, not the latest security-patched 3.12 release.
[Owner-operated setup/offline check](../scripts/uc001_validator_setup/README.md)
and [receipt](../build/uc001-validator-setup/verification.json) record official
provenance, conditional cumulative accounting and a small unchanged-source transfer.
Seven existing offline tests, shared schema/decoder/case probes and command syntax
checks pass in Codespace; Windows acquisition/installation/native wheel imports
remain pending. No second validator, capture/replay orchestration, model/transport
execution or ledger reset. Qualified linguistic review and three live API/real-adapter
checks remain open. Frozen sources/bundles/history preserved; Priority 3 partial,
Phase 3 DEVELOP in-progress. Stop at executable environment handoff.

### Windows-local contract capture / Codespace replay — offline implementation

Owner-pasted [setup and compatibility receipts](../build/uc001-contract-local/owner-results/)
establish Python 3.12.10 x64, exact dependencies and frozen-schema compatibility,
not model/GPU readiness or semantic correctness. All three supplied setup hashes
match preserved preparation artifacts. Reported cumulative allowance remaining:
46,845,816 bytes; no reset or dependency acquisition.

Authorized separate [local orchestration](../scripts/uc001_contract_local/README.md)
replaces the planned feasibility execution, retaining the original attempt identity,
create-once RunBudget, frozen inputs/pins and all limits. The unchanged adapter/domain/
case checks run on Windows before advancement. An owned worker handshake and independent
managed timer enforce 90 seconds, including validation; timer/cleanup coordinate the
existing native job close. Exact bounded bodies precede parsing; incomplete/secret-bearing
bodies stay private. Codespace replay uses labelled substitutes with no network fallback;
cases 1/5/10 remain live API/real-adapter gaps. No application or original bundle changes.

TDD: missing-module, independent-timer, dependency-drift, raw-completeness/privacy and
combined-artifact-budget and progress/exit-race RED checks, then GREEN. **202 focused
and relevant existing checks passed** (one existing Starlette/httpx deprecation warning).
[Verification and source handoff](../build/uc001-contract-local/verification.json) distinguish
synthetic/managed Codespace evidence from pending Windows execution. Qualified DE/FR/IT/EN
expectations approval is still required before inference; native GPU/allocation, new
Windows timing/cleanup and actual semantic suitability remain pending. Current handoff
is model-free `--verify-only`; no model/transport, held-out, installation or Git action.
SSH/Support remains paused. Priority 3 partial; Phase 3 DEVELOP in-progress.

Owner-confirmed follow-up, 2026-10-18 (Europe/Berlin): the separate
[Windows preparation receipt](../build/uc001-contract-local/owner-results/review_2026_10_18/windows-preparation.owner-pasted.json)
reports `local_preparation_verified`, bound to local freeze `4a38c66c…c150079`.
[Partial expectations review](../build/uc001-contract-local/owner-results/review_2026_10_18/partial-expectations-review.json):
owner `andiwandfhnw`, self-reported DE/EN competence, confirmed cases 2/5/10/11/13/14
and the Swiss German expectation for case 12; no corrections supplied.
Cases 1/3/4/6/7/8/9 remain unapproved. Overall review remains pending and
`expected_meanings_approved: false`; no model-output validation or startup authorization.
Evidence is outside the frozen bundle; no tests, rebuilds or frozen-file changes.
Priority 3 remains partial; Phase 3 DEVELOP remains in-progress.

Owner decision: defer outstanding linguistic approvals for the existing bounded
technical feasibility run only. They remain required before interpreter suitability
or multilingual acceptance. Separate [v1.1.0 handoff](../scripts/uc001_contract_local_v1_1_0/README.md)
and [recorded decision](../scripts/uc001_contract_local_v1_1_0/technical-decision.json)
replace the local execution gate; original package/receipts are unchanged. The original
partial review/hash and all case confirmations/unapproved records remain intact;
unchanged parent/input hashes establish applicability. Launcher, capture and replay
keep review pending and `expected_meanings_approved: false`, with provisional expectations
and separate technical/policy results. Original attempt/ledger/one-startup/14-generation
limits and all validation/resource/deadline/authentication/cleanup stops remain binding.
Focused TDD: original qualified-review gate rejected technical permission (RED), then
**48 checks passed** (GREEN), including affected synthetic replay/capture, actual launcher
with substitutes and existing budget/case-state checks; one existing deprecation warning.
[Verification/package](../build/uc001-contract-local-v1_1_0/verification.json).
No model/inference or connection executed. Fresh Windows readiness/native execution and
semantic validation remain pending; live API/real-adapter cases 1/5/10 retain no replay
credit. Priority 3 partial; Phase 3 DEVELOP in-progress; SSH/Support remains paused.

### Consumed startup — ownership/output-verifier correction

[Owner-reported facts](../build/uc001-contract-local-v1_2_0/owner-reported-failure.json):
one startup; confirmed exits for 30488/56840 without cleanup errors; no accepted cases
or listed case bodies; ValueError with progress/ledger absent. Unchanged collector
flow indicates failure before the first frozen generation; original ancestry and the
exact failing check remain unknown. The separate model-free probe reproduced the
direct-parent assumption problem. These are reported facts, not raw files or a new ledger.

Separate [v1.2.0 correction/model-free handoff](../scripts/uc001_contract_local_v1_2_0/README.md)
binds the venv redirector and actual interpreter by live PID/creation/path/direct-chain
and exact native job membership, assigning the job before resuming the redirector.
Both identities/exits are required at cleanup. Pinned llama.cpp source distinguishes
reported task `n_predict:-1`, CLI fallback and request `max_tokens:3072`; full verification
requires separate CLI/request evidence. Missing historical CLI evidence stays unverified.
Fixed stage/reason codes avoid secret/raw exception disclosure. Model/capture entry
points are hard-blocked by the consumed allowance; the handoff launches harmless Python only.
Focused RED/GREEN and relevant regressions: **118 passed**, one existing deprecation
warning; [verification](../build/uc001-contract-local-v1_2_0/verification.json).
Windows native verification is pending. Original packages, receipt/review bindings,
attempt directory, frozen inputs/pins and all model limits are preserved. Semantic
review remains pending/false; live API cases 1/5/10 remain gaps. Priority 3 partial;
Phase 3 DEVELOP in-progress; no model/transport, held-out or Git action.

### v1.2.0 model-free failure — reporting/binding investigation

[Owner-reported result](../build/uc001-contract-local-v1_2_1/owner-reported-v1_2_0-failure.json):
ownership/worker null, 680 ms, job closure and redirector 48020 exit confirmed; interpreter
identity/exit unconfirmed. No surviving process or zero-generation ledger is inferred.
Separate [v1.2.1 correction](../scripts/uc001_contract_local_v1_2_1/README.md) preserves
primary, cleanup and deadline failures independently, with fixed safe codes and private
raw detail. Code inspection also found cleanup's dependence on `LastProof`: a retained
interpreter could be ignored after late binding failure. Its separately verified identity
now survives that failure, while full ownership checks remain binding. Never identified,
identified/unconfirmed and confirmed exits are distinct and missing proof still fails.
The initiating Windows failure remains unknown: the first exception/native status and
binding step are missing from the supplied overwritten result. One prepared 60-second
model-free check captures these plus sanitized binding observations and cleanup.
Focused RED/GREEN and ownership/cleanup regressions: **35 passed**;
[verification](../build/uc001-contract-local-v1_2_1/verification.json). No Windows/native
execution or automatic rerun. Prior packages/receipts and the original model attempt are
preserved; startup allowance remains consumed. Priority 3 partial; Phase 3 in-progress.

### v1.2.1 console-helper binding failure — bounded correction

[Owner-reported facts](../build/uc001-contract-local-v1_2_2/owner-reported-v1_2_1-failure.json)
establish `ownership/unexpected_owned_process` at `candidate_constraints`: job members
29444 and 53380, the latter a system-path console host parented to the redirector.
No interpreter proof/worker result was completed; job closure and redirector exit passed,
while interpreter identity/exit remained unavailable. No surviving process or count is inferred.

Separate [v1.2.2 model-free handoff](../scripts/uc001_contract_local_v1_2_2/README.md)
accounts for every member by role rather than a fixed total. Exactly one pinned interpreter
is still required. At most one helper needs its native system path, verified owned parent,
creation time, stable held handle and exact-job membership. Helper-only binding waits within
the unchanged deadline; unknown/ambiguous identities stop. Python revalidates every role and
the exact member set. Retained helpers receive confirmed-exit cleanup even after partial
binding; missing interpreter identity and unknown members still fail. Primary/cleanup/deadline
failures remain independent, with raw details private.

Focused RED/GREEN and ownership/cleanup regressions: **77 passed**;
[verification](../build/uc001-contract-local-v1_2_2/verification.json). Native Windows
verification remains pending; the one model-free owner command is prepared, not run.
All prior bundles/receipts, pins, limits and review bindings remain intact. The original
model startup allowance remains consumed; no capture, SSH, dependencies or automatic retry.
Priority 3 partial; Phase 3 DEVELOP in-progress.

### Tested native path verified; additional attempt proposed — 2026-10-18

[Three owner-pasted v1.2.2 Windows receipts and scoped closure](../build/uc001-contract-local-v1_2_2/owner-results/results_2026_10_18/verification.json)
confirm binding of redirector 46024, interpreter 53216 and system console helper 50576,
exact reported job membership, Python worker checks, job closure and all three exits in
1667 ms, with no reported failure channels. Mark only the tested native ownership/binding/
cleanup path verified; **harness debugging closed**. The pasted JSON is not authenticated
as byte-identical Windows files. No model/GPU readiness, generation count or semantics is
inferred. Missing historical CLI evidence remains unavailable and is not reinvestigated.

The owner requested preparation, not execution, of [one additional technical attempt](../scripts/uc001_contract_local_v1_3_0/README.md):
new identity `3efca8db7f356fe00672ecf2a0607c2b57c017fafedca61e85778611abd1afe8`
links to original consumed `bda2015c0ffbe89ab1a612fb4003b2b12f254871cf32f2e47dbbbe9d45cf0f52`.
Proposed allowance: one additional model startup and at most 14 unchanged ordered cases,
all existing pins/resource/time/stop limits; no retry/tuning/replacement/downloads.
**Execution remains blocked pending explicit additional-allowance approval.** The packaged
approval template is false, and both launcher and capture require a separate owner record
bound to proposal/freeze/identities. No allowance or historical ledger is reset.

The separate handoff reuses verified v1.2.2 native/ownership/cleanup and settings code
unchanged. Focused offline tests exercise the actual launcher/capture dispatch, prospective
startup argv and generation records, per-response validation/deadlines, abort/cleanup and
helper-aware replay. [Verification](../build/uc001-contract-local-v1_3_0/verification.json)
records results and preservation. This is offline wiring evidence, not new Windows/model
execution. Qualified semantics remain pending/false; existing partial confirmations and
live API gaps 1/5/10 remain. SSH/Support paused; held-out unopened; Priority 3 partial,
Phase 3 DEVELOP in-progress. Stop after the reviewable handoff; no startup or Git delivery.

### v1.3.0 combined-job ownership failure — 2026-10-18

[Owner-reported facts](../build/uc001-combined-ownership/owner-reported-v1_3_0-failure.json)
confirm another consumed startup and `ownership/console_helper_ambiguous`. Raw failed-run
helper identities/ancestry and generation receipts were not supplied; none are reconstructed.
Both consumed attempts, prior packages/receipts and model settings/limits remain unchanged. Owner also
[pasted a current snapshot](../build/uc001-combined-ownership/current-process-snapshot.owner-pasted.json)
with no process rows at 2026-10-18T17:16:30.0029545Z. Its supplied scope explicitly
excludes termination and historical exit proof; it provides no helper ancestry.

Inspection confirms the native global-one-helper cap/Python-only parent policy, the matching
Python-validator restriction and a separate defect: classification failure disposed observed
handles before cleanup. A [separate model-free correction/handoff](../scripts/uc001_combined_ownership/README.md)
retains observed handles independently, validates their exact native job/lifetime identity
before exit confirmation, and keeps unknown roles unapproved. Missing identity/handle/job
verification or unconfirmed exit still fails; primary/cleanup/deadline failures stay separate.

**Helper-role acceptance is unchanged pending actual combined Windows evidence.** This Linux
Codespace cannot establish native Windows ancestry. The single prepared check uses production
server and Python launch primitives with harmless stand-ins in one job, snapshots identities/
parentage before classification and after rejection, then confirms retained exits. It does
not infer that the failed model run's helpers were legitimate. The necessary remaining data
is that check's `result.json`, `observation.json` and `cleanup.json`; no further model run is
proposed or authorized. [Focused offline evidence](../build/uc001-combined-ownership/verification.json)
covers both branch rejections, partial binding, unknown members, missing identity and
independent failures. Native reproduction is pending, not simulated as Windows success.
SSH/Support and language work stay paused; held-out unopened; Priority 3 partial,
Phase 3 DEVELOP in-progress. Stop after this bounded handoff.

### Combined branch correction — 2026-10-18

[Owner-pasted transcript](../build/uc001-combined-ownership-v1_1_0/owner-evidence/provenance.json)
confirms a verified system conhost under each stand-in branch and the base interpreter
under the redirector. All five observed identities exited. Historical `cleanup_confirmed`
remains false, with the missing approved interpreter role and cleanup error intact.
This resolves the earlier reproduction prerequisite; it does not authenticate model-run helpers.

[Separate correction and one model-free Windows handoff](../scripts/uc001_combined_ownership_v1_1_0/README.md)
validate one exact system helper per verified branch and the server's full held identity,
path, lifetime, ancestry and fresh job membership. Native proof, Python validator and
cleanup consumers agree; unknown/ambiguous members still fail, retained observations stay
independent of role approval. The check requires actual Python validation of the combined
proof and a final native rebind, then confirmed exits. [Focused offline verification](../build/uc001-combined-ownership-v1_1_0/verification.json)
is separate from pending Windows verification. No model-attempt package or allowance reset;
both startups consumed. Previous bundles/receipts/settings/cases untouched; semantic review
pending/false, SSH/Support paused, held-out unopened. Priority 3 partial; Phase 3 in-progress.

### Verified combined ownership and corrected execution proposal — 2026-10-18

[Owner-provided attachment and receipts](../build/uc001-combined-ownership-v1_1_0/owner-results/results_2026_10_18/verification.json)
confirm the combined check passed in 1180 ms: native binding, actual Python validator,
fresh native revalidation, job closure and five identity-bound exits. Attachment bytes
are preserved; the tested ownership issue is closed. Earlier failed receipts stay unchanged.
No standalone Windows check is repeated and no model/GPU readiness is claimed.

[Separate corrected v1.4.0 handoff](../scripts/uc001_contract_local_v1_4_0/README.md) reuses the
four Windows-verified helpers unchanged. Launcher/capture/replay bind the full server
identity and trusted pinned runtime path, both helper branches and cleanup; replay's
recorded readers are explicitly substitutes. Proposed identity
`d586feb0be95c5d955be7b6a60381ab41594a0136d8c45917f81460829675078` links the two consumed
identities. **One further startup / at most 14 unchanged ordered generations requires
explicit owner approval; execution remains blocked.** Matching extraction and existing
valid approval can be reused; an already reserved attempt cannot. No historical ledger
reset/count reconstruction. Pins/inputs/limits/deadlines/review bindings unchanged.
[Focused offline verification/package/hashes](../build/uc001-contract-local-v1_4_0/verification.json)
are distinct from future Windows model integration. Technical-only, semantic approval
false/pending, live API cases 1/5/10 deferred; Priority 3 partial, Phase 3 in-progress.

### v1.4.0 owner-export closure — 2026-10-18

[Original ZIP and offline closure](../build/uc001-contract-local-v1_4_0/closure_daa09499fcd8486f91cc6696279e2633/README.md)
are preserved separately from the frozen handoff. Approval/freeze/lineage and recorded
settings/full-server ownership/cleanup checks pass. The export records one startup, one
case-1 generation, zero accepted cases and all five confirmed exits. The v1.4.0 allowance
is consumed; earlier attempts/ledgers remain unchanged and no new startup is authorized.

Full replay correctly rejects incomplete supervision. Separate unchanged exact-byte case
replay reproduces `Meaning items must each belong to one original clause`: the subject
item is unreferenced. Additional packet defects are quantity objects on action/subject
items and Spanish unsupported input declared supported English/understood, contrary to
frozen case 1/LAC-10. Windows records only `worker/check_failed`; private detailed stop
is not exported. No packet repair, source change, model/regression rerun or extra generation.
Cases 2–14 untested; no four-language/suitability/semantic acceptance or live API 1/5/10
credit. Qualified review pending/false; Priority 3 partial, Phase 3 DEVELOP in-progress.

### Priority 4 — one draft evidence packet, authorized 2026-10-18

Prepared [bicycle repair / Switzerland](knowledge/UC-001-BICYCLE-REPAIR-CH-DRAFT.md)
from traceable provider sources, with scoped claims, exact source-currency hourly
cost, separate observation/review metadata, acceptance mapping and explicit unknowns.
Factual admission, current freshness, usability conditions and qualified multilingual
rendering/review remain pending. No qualifying comparison or release is claimed;
normal runtime and synthetic fixtures are unchanged. Documentation/content checks
passed: exact-cost JSON, three distinct UUIDs, four local links and phase/status markers.
No regression/model/experiment rerun. Historical evidence and consumed startup
allowances remain unchanged. Priority 4 preparation and Priority 3 are partial;
Phase 3 DEVELOP stays in-progress. Stop after this packet; no later work or delivery.

Owner review recorded 2026-10-18: approved only the provider-stated factual
extractions (repair service, published hourly rate and Oberried location), bound
to the original packet hash. No unrestricted applicability, qualification,
multilingual rendering or runtime approval. Review date has day precision;
freshness/expiry remain unresolved. Tariff/applicability unknowns and all prior
evidence remain intact. Documentation content/link checks only; no research or
experiment authorized or performed.

### Priority 4 — bounded source-bound rendering, 2026-10-19

Implemented `SourceBoundRenderer` through the existing renderer port and retained
application language/version, qualification and atomic save-before-presentation
checks. Source/target review records bind exact source/typed meaning, wording,
language and version; synthetic reviews require explicit test-only opt-in. Missing
review/rendering returns `rendering_unavailable`; changed bindings are processing
failures, both before saving. Structural checks do not prove linguistic fidelity.

[Four versioned drafts](knowledge/UC-001-BICYCLE-REPAIR-CH-RENDERINGS.json) preserve
provider attribution, exact hourly cost, location, citations, conditions and unknowns.
They bind the unchanged packet hash; actual qualified-material binding/reviews
remain absent and runtime use is false. The frontend displays admitted paraphrases
and localized unknowns with original citations/excerpts. Successful paths use only
isolated synthetic providers/review substitutes; normal `app.main` stays unconfigured.

TDD RED: five unchecked-review/content/version/binding/condition rejection cases
failed; browser RED demonstrated missing translated cost text. GREEN: **150 focused
backend/regression checks, 13 browser checks**, frontend lint/build passed. Includes
held-response commit-before-display, unsaved review limitation, rollback and immutable
saved content. [Commands, changed files and limits](../build/uc001-priority4-rendering/verification.json).
No research, interpreter/model/harness/SSH work, experiment or held-out access.
Source freshness/applicability, real qualification and qualified DE/FR/IT/EN review
remain acceptance gaps; TL-03 is not complete. Stop after this slice. Priorities 3/4
remain partial; Phase 3 DEVELOP in-progress; no release activation or Git delivery.

### Priority 5A — committed save / lost response recovery, 2026-10-19

Owner accepted only this reported bounded scope on 2026-10-19: successful atomic
save, lost response and explicit acknowledgement-only same-submission recovery.
This is not complete retry/security coverage, Priority 5/increment-1 acceptance or
DEVELOP completion. The original verification receipt and its limits remain unchanged.

Owner authorized only successful atomic persistence followed by lost HTTP delivery
and explicit same-submission recovery. Prerequisites confirmed against O-2,
ADR-003 and existing code; no accepted-contract conflict. React now retains the
serialized payload with key/proof, states delivery is unknown, and displays the
original outcome/assessment time in acknowledgement-only recovery. The backend
contract, storage and normal composition are unchanged.

TDD RED exposed the delivery-status wording and absent acknowledgement metadata.
GREEN: **5 focused backend checks; 1 new browser journey plus 3 directly affected
browser regressions; frontend lint/build passed**. The new browser journey was
rerun alone to persist its exact evidence. Real API/SQLite commit precedes the
test-only delivery abort; explicit recovery sends identical bytes/key/proof,
returns 200 / `submission_recovered`, and leaves one request, two saved options
and two evidence links unchanged. No claims replayed; no automatic request during
the bounded idle observations. Backend checks preserve uniform 403 denial and
409 changed-payload rejection. [Commands, identities, results and limits](../build/uc001-priority5a-recovery/verification.json).

Priority 5 remains partial: concurrency, ambiguous-commit/full persistence faults,
complete unauthorized-disclosure checks, locality/reference integration and complete
fresh-search reassessment remain pending. Priorities 3/4 remain partial; real drafts
inactive, interpreter experiments closed. Phase 3 DEVELOP in-progress. No activation,
research, model/held-out work, phase advance or Git delivery. Stop for human review.

### Priority 5B — explicit fresh search after recovery, 2026-10-19

Owner accepted only the reported bounded verification on 2026-10-19: fresh
submission after recovered acknowledgement with new key/proof/current fields,
current synthetic reassessment and preserved original record. This verifies
existing application behavior with test-support improvements, not a new production
feature. Original verification limits remain intact; no Priority 5/increment-1 or
DEVELOP completion is accepted.

Verified only the authorized recovered-acknowledgement → explicit fresh-search
slice. The accepted O-2 contract and production submission/recovery code already
implement the distinction; no production code, schema or runtime configuration
change was needed. Synthetic support now accepts a controlled UTC clock, with a
test-only clock JSON beneath `build/test-only/`. The default browser command gets
a unique initialized clock file. Tracing is disabled and proof comparisons use
digests in memory; verification artifacts contain no raw originating proofs.

RED: missing clock injection; browser returned a fixed-time comparison instead of
expired-evidence coverage; review exposed the absent default clock-file setup.
GREEN: **1 new backend integration check plus 8 directly affected regressions;
1 new browser journey plus the 5A regression; frontend lint/build passed**.
Repeated targeted runs verify fixes to the same scenarios, not additional coverage.
The fresh action alone sends nothing. Explicit fresh submission uses a new key/proof
and edited current `Velo`/CH/en fields, after recovery reused its captured body.
Controlled assessment advances from 2026-10-15 to 2027-10-16; expired required
evidence produces a newly saved `insufficient_coverage` with a new request ID/time.
Three browser requests are observed; original request/options/associations/evidence
and timestamp remain unchanged. New coverage is displayed only after atomic commit.
[Exact commands, identities/counts, RED/GREEN and preservation](../build/uc001-priority5b-fresh-search/verification.json).

Priority 5 remains partial: concurrency, ambiguous-commit/full persistence and
disclosure matrices, real locality/reference and remaining recovery/fresh-search
error/loading cases are unimplemented or unverified. Priorities 3/4 remain partial;
real drafts inactive, experiments closed. Phase 3 DEVELOP in-progress; no increment
acceptance, activation, research, model/held-out work or Git delivery. Stop for review.

### Priority 5C — one controlled same-submission collision, 2026-10-19

Owner accepted only this demonstrated interleaving on 2026-10-19 as verification
of existing production behavior. No RED failure or production fix occurred;
controlled-interleaving, application-facing call-counter and concurrency limits
in the original receipt remain unchanged.

Prerequisites confirmed against O-2/ADR-003 and the current adapter; no contract,
schema, architecture or dependency conflict. One new regression verifies existing
behavior; it passed first against unchanged production code. No RED failure or
production fix is claimed. **1 new integration scenario + 4 directly affected
transaction/recovery/proof/payload/immutable-projection regressions passed**.

Two overlapping API executions use separate real SQLite engines/connections and
the same key/proof/payload. Both real initial lookups miss and both prepare distinct
request/option IDs before the winner commits. Bounded test-only barriers/events
operate outside write transactions. The loser then attempts a genuine duplicate
insert: `SQLITE_CONSTRAINT_UNIQUE` on the submission-key digest → rollback →
`DuplicateSubmission` → winner lookup → ownership/payload checks → acknowledgement.
Winner returns 201/comparison; loser returns 200/`submission_recovered` with only
winner identity, original outcome/time. Exactly one request/two options/two links
remain; no loser IDs or unsaved projection persist or return. Evidence is unchanged.
[Exact interleaving, responses/IDs, commands, checks and limits](../build/uc001-priority5c-concurrency/verification.json).

This verifies only the controlled post-winner-commit unique-collision branch, not
SQLite lock timings, other process configurations or the full concurrency matrix.
Ambiguous-commit/full persistence/disclosure matrices, real locality/reference and
remaining browser/error paths stay pending. Priorities 3/4/5 remain partial;
Phase 3 DEVELOP in-progress. No browser expansion, real activation, experiments,
held-out/semantic work or Git delivery. Stop for human review.
Session model metadata (owner-reported): **GPT-6.1 Sol Ultra**; no historical run
or runtime-interpreter label is changed.

### Priority 5D — uncertain persistence then explicit recovery, 2026-10-19

One test-only DBAPI seam commits real SQLite, then withholds confirmation; a
separate observer sees committed rows without supplying them to application logic.
RED: the existing 503/unknown response passed, but the required readback never ran.
The minimal adapter fix now attempts one guarded read after commit-error cleanup;
the injected read failure preserves 503/`persistence_error`/unknown. Explicit same-
key/proof/payload recovery returns 200/`submission_recovered`, original ID/outcome/time
only. One save, unchanged snapshots/evidence, rows 0/0/0 → 1/2/2 → 1/2/2.
GREEN: **1 new integration scenario + 5 affected regressions, including 5C, passed**.
[Exact faults, application/observer knowledge, commands and evidence](../build/uc001-priority5d-uncertain-persistence/verification.json).
Browser presentation, successful/absent reconciliation variants, physical-crash
durability and full commit/fault/disclosure/concurrency matrices remain unverified;
other Priority 5 gaps stay pending. Priorities 3/4/5 partial; Phase 3 in-progress.
No browser/frontend feature, real activation, experiments or delivery. Stop for review.

## Priority 3 — bounded contracts/policy, authorized 2026-10-16

Implemented bounded step: application language policy and interpreter/optional recognizer
contracts using explicit synthetic adapters only. Preserve priorities 1/2 and
existing work. First clarify the priority-2 locality/persistence evidence below;
no unfinished qualification requirement or material requirement conflict was found
in that mapping. Use TDD for contract enforcement/routing; no stub/label establishes
semantic understanding. No real adapter selection/download/execution, experiments,
held-out access, knowledge release or priority-4 rendering. Stop after this bounded
step; priority 3 remains partial, Phase 3 in-progress. No Git delivery/branch change.

TDD: missing contracts first failed collection, then seven of eight initial API
tests failed on missing policy routing. New browser assertions failed before controls
were added. Focused RED/GREEN checks also cover essential action projection,
meaning/basis clarification before language choice, unavailable-rendering correction
and old correction becoming a preference after editing. Final results/limits:
[PROJECT.md](PROJECT.md#priority-3-partial-verification--2026-10-16).
No real interpreter/recognizer, model, held-out cases, reviewed knowledge release or
four-language renderer was selected, acquired or run. Stop at this bounded step.

## Priority 2 — authorized development, 2026-10-15

Owner authorized Qualification & Coverage only: accepted candidate/claim, freshness,
location, exact-cost and display rules plus saved insufficient outcomes. TDD and
relevant regressions required. Preserve priority 1 and existing work; stop after
verification. Desktop client; execution stays in the existing Codespace. Phase 3
remains in-progress. No later priorities, interpreter/model execution, held-out
inspection, requirement changes, staging, commits, push or deployment authorized.

Priority 2 implemented and verified; stopped on 2026-10-15. TDD RED recorded
missing qualification module, coverage/expiry API failures and missing coverage UI;
focused boundary regressions preceded fixes. Final checks: **57 backend tests,
4 real Chromium/API/SQLite tests passed; frontend lint/build passed**. Qualification
precedes deterministic ordering/three-result limit. Saved coverage has no comparison
or option rows; processing/input/capability/clarification/save failures remain distinct.
Atomic save, immutable evidence and saved snapshots/identities pass regressions,
including reopening and explicit retry after expiry. New synthetic evidence versions
preserve earlier versions. [Scope and limitations](PROJECT.md#priority-2-verification--2026-10-15).
Priorities 3–6 and full increment/phase acceptance remain pending; no further action
authorized. The existing historical backlog whitespace warning is preserved.

### Locality/persistence scope clarification — 2026-10-16

Mapping uses existing code/test evidence and the recorded 57/4 results; no checks
were rerun solely for this clarification. The geographic qualification rule is
implemented; reference truth and input interpretation are separate dependencies.

| Accepted criteria/tests | Existing evidence and remaining boundary | Planned work |
|---|---|---|
| AC-03/04/12/16; T-03/07/13 | `qualify` and `test_country_and_intended_locality_require_independent_coverage` / `test_narrow_locality_requires_identity_and_retains_geographic_limits` enforce country/named-locality scope, required evidence, unambiguous identity and narrower conditions. Confirmation cannot create applicability. Tests use prepared synthetic scope; no real reference verification claimed. | Priority-2 qualification implemented; real reviewed data and priority-6 journeys pending. |
| AC-01/02/13/16; T-01/02/10/11/13 | API checks blank text/country shape and supports location-choice fields; exact-match synthetic interpreter is not a locality resolver. Real country membership, malformed/mismatched/ambiguous/unverifiable locality, explicit confirmation/country-only handling and justified retention need input/reference/UI integration. An independent locality constraint in text must survive country-only choice. | Priority 3 covers meaning/contracts; priority 5 covers location/error API/browser handling with the separately reviewed local-reference dependency; priority 6 verifies real journeys. No reference preparation authorized here. |
| AC-07/08/10/11; T-08/09/11 | `test_saved_comparison.py` covers committed snapshots/identities, zero-option coverage, real partial-write rollback, coverage-save failure, immutable evidence, reopening and explicit retry after expiry. Browser tests cover success/rollback/coverage/save failure. | Implemented scoped priority-1/2 evidence; not the entire persistence fault matrix. |
| AC-10/11/14/17; T-09/12/13 | Basic same-key/proof/payload guards and acknowledgement-only recovery pass. Lost post-commit response, ambiguous commit, same-key races, full unauthorized-disclosure checks, all write/read/commit faults, delayed-save loading and recovery/fresh-search browser cases are not comprehensively verified. | Priority 5, then priority 6. |
| AC-10/13/15; TL-01/02/04 | Original input/interpretation are saved; language and span contracts were only the exact English fixture. | This bounded priority-3 step adds policy/contract tests; real semantics remain later priority 3/6, faithful rendering priority 4/6. |

The earlier broad “input/reference/recovery incomplete” note does not defer an
implemented qualification rule or claim the remaining matrices have passed.
Priority 3 now also projects represented actions and textual locality requirements
into essential qualification; this supplies previously absent input meaning rather
than deferring or weakening the geographic qualification rule.

## Priority 1 — authorized development, 2026-10-15

Scope: React submission → FastAPI/application/domain → real isolated SQLite →
display the committed comparison. Test-only interpreter/synthetic evidence must be
explicitly injected from test support, unavailable to normal runtime configuration.
TDD checks cover persistence, preparation before one atomic commit, saved identities/
order, a real partial-write rollback and a browser journey through the actual API/DB.
Preserve all approved language/privacy/evidence/recovery contracts; later tasks stay
pending. Stop after this slice is implemented and verified. No language experiments,
held-out inspection, model downloads, production deployment or Git delivery.

Priority 1 implemented and verified on 2026-10-15; stopped at this slice. TDD:
backend tests first failed on missing modules, then 8 passed; after resolving native
Chromium prerequisites, the two browser assertions failed against the starter,
then both passed through the real API/file-backed SQLite. The success response and
displayed order/IDs match committed rows; a trigger rejects the second required
evidence link and all request/option/link writes roll back, with no successful UI.
Normal API composition has no test adapters or fixture database. Basic same-key/
proof/payload guards prevent duplicate replay, without claiming complete T-13 coverage.
Frontend lint and TypeScript/Vite build passed. [Commands/demo](PROJECT.md#test-only-local-demonstration--codespaces-bash)
and [verification scope](PROJECT.md#priority-1-verification--2026-10-15) are recorded.
Phase 3 remains in-progress; priorities 2–6, increment-1 completion and qualified
linguistic validation are pending. No automatic move to priority 2 or VALIDATE.

## Increment-1 integration — accepted 2026-10-15

Owner direction: stop standalone detector experiments and exact unsupported-language
identification tuning. Preserve DE/FR/IT/EN free text, short/shared/preference and
mixed-input handling, country independence and Resolena-controlled processing.
Spanish versus Portuguese is not a product acceptance distinction when both receive
the appropriate unsupported-language limitation/rephrasing response. The frozen
[Lingua result](../experiments/uc001_multilingual/lingua_B_runner_v1_0_2/RESULTS.md)
remains failed and unchanged; no application route was tested. Lingua is an advisory
candidate, never independent proof of understanding or a trusted capability gate.
See [ADR-004](adr/ADR-004-multilingual-interpretation-scope.md#product-integration-refocus--owner-direction-2026-10-15).

The [integration design](ARCHITECTURE.md#multilingual-interpretation-and-explanation--provisional-mechanism)
separates original-input hypotheses, complete interpretation/English normalization,
application outcomes and faithful source-bound rendering. It preserves all clauses,
negation, values and exact original spans; genuine meaning uncertainty clarifies.
Clear supported input needs no routine language selector. The integration baseline
was accepted on 2026-10-15; real language behaviour remains unimplemented/unverified.
Priority 1 above records the authorized synthetic application slice.

Accepted DEVELOP task order; priorities 1 and 2 were separately authorized and
verified on 2026-10-15. On 2026-10-16 only the bounded priority-3 contracts/policy
step was authorized; priority 3 remains partial and priorities 4–6 pending.
Use TDD and keep synthetic substitutes explicit:

| Priority | Review-ready task / evidence required |
|---|---|
| 1 | Build one React → FastAPI → application/domain → SQLite → saved-comparison journey with a test-only interpreter and synthetic evidence fixture. Prepare/render before one atomic commit, then present stable IDs/order. This proves wiring only, not multilingual capability (AC-01/08/10/14). |
| 2 | Complete qualification and valid insufficient-coverage outcomes: independent support/freshness/constraint checks, country/locality applicability, source-currency amounts and deterministic up-to-three order. Preserve unknowns and distinguish input, knowledge and processing failures (AC-01–09/12/16; T-01–07). |
| 3 | Implement application language policy and interpreter/recognizer contracts; connect a separately selected suitable local interpreter. Verify complete DE/FR/IT/EN meaning, mixed clauses, amounts/negation, unsupported limitation, short/shared/preference/correction and independent country. Detector hints cannot replace these checks (AC-15; TL-01/02/04). Contract tests can precede adapter selection. |
| 4 | Prepare a minimal real reviewed knowledge release and faithful four-language claim/template/narrative renderings; validate source support and target meaning separately. Retrieve across source languages, retain conditions/citations/review dates and block unfaithful successful presentation (AC-03–06/09/10/15; TL-03). Review/data preparation can run alongside the earlier tasks. |
| 5 | Complete API/browser errors, loading/field preservation, originating-client proof/payload/concurrency checks and explicit recovery versus fresh reassessment. Test save/transport faults without false success, stale replay, automatic retry or disclosure (AC-10–14/17; T-08–13). |
| 6 | Verify real end-to-end comparison, insufficient coverage, clarification and limitation journeys plus privacy/recovery faults. Obtain qualified semantic/source-target review; synthetic substitutes and detector labels cannot count as verified language support. Acceptance remains against the unchanged UC, LAC and TL criteria. |

[Concrete dependencies](ARCHITECTURE.md#owner-decisions-and-material-trade-offs):
owner phase acceptance is recorded above; interpreter suitability gates the real
language adapter; reviewed knowledge gates a usable evidence-backed comparison;
qualified review gates linguistic acceptance. The latter dependencies do not block
all application implementation. No production hosting commitment or further detector
experiment is required to begin the first task after authorization.

The 55 held-out cases remain unopened. No inference, detector run, tuning, installation,
production change or Git delivery occurred in the preceding design task. Its pending
DESIGN status is superseded by explicit acceptance above; qualified linguistic
validation remains pending. Dated experiment entries below retain
history and earlier approvals; they are not authorization for another run.

## Multilingual experiment restart — authorized 2026-10-11

The owner authorized a new run linked to the interrupted renewed attempt:
[restart record](../experiments/uc001_multilingual/qwen_spike/restart_2026_10_11/REPRODUCE.md).
Reuse surviving source/configured build and valid artifacts; one pinned-model
download if absent. Two hours from execution start, at most 60 minutes including
loading/inference, unchanged pins/settings/cases/prompts/scoring, 6 GiB scratch,
3.25 GiB owned RSS and cumulative 2.2 GB downloads across renewed attempt/restart.
Stop on build/startup failure; no automatic restart. Preserve reusable workspace
artifacts and all earlier records/deadlines. Save progress/resources/exit status
incrementally; report model results separately from operational harness checks.

Read-only recovery found TASKS.md inconsistent with the supported UC/architecture/
workflow and different from its preflight hash. The discrepancy's cause is unknown.
The owner explicitly authorized this reconciliation to UC-001 / increment 1 /
Phase 2 DESIGN / in-progress. Earlier Phase 1 entries below are historical.
No production implementation, dependency changes, Git delivery or deployment is
authorized. Execution stopped at the separate smoke gate; final DESIGN acceptance
stays pending. Build succeeded (14m52s, exit 0), the pinned model checksum matched,
and HTTP readiness passed in 14.85s. The smoke response took 44.70s, incorrectly
reported supported English as unsupported and supplied two non-verbatim quotes;
the unchanged scorer rejected it as invalid output. No calibration, frozen
evaluation or repeat ran. Seven operational checks passed separately from model
results; a post-build event-name collision was corrected after preserving its
failure records, without rebuilding or changing the new run's deadline.
The run exited 1; the owned model process exited 0 and no experiment process
remains. Cumulative downloads: 2,020,223,394 bytes; artifacts/logs are retained
in Git-ignored workspace storage. See [actual results](../experiments/uc001_multilingual/qwen_spike/restart_2026_10_11/results.json)
and [closeout](../experiments/uc001_multilingual/qwen_spike/restart_2026_10_11/closeout.json).
No retry/tuning or further execution is authorized after this failed smoke gate.
Closeout verification: all frozen inputs and interrupted-attempt record hashes
match; the retained model matches its pin, no owned process remains, and new local
links/artifact whitespace checks pass. Branch/HEAD and empty index are preserved.
The pre-existing historical backlog whitespace warning is retained. Detailed
[verification](../experiments/uc001_multilingual/qwen_spike/restart_2026_10_11/verification.json)
records full-run resources, binary/model hashes and the runtime metadata caveat.
Read-only smoke diagnosis completed on 2026-10-11 in the existing restart record:
no demonstrated configuration correction; a bounded paired calibration is proposed
but unapproved. No execution, validator change or frozen-case exposure occurred.
Phase 2 DESIGN/in-progress and final acceptance pending remain unchanged.

## Calibration B — authorized 2026-10-11

The owner approved the six proposed synthetic calibration cases at temperatures
.7 and 0, seed 42, unchanged remaining settings/prompt/schema/validation.
[Plan and run records](../experiments/uc001_multilingual/qwen_spike/calibration_B_2026_10_11/REPRODUCE.md)
freeze expectations and twelve paired requests before loading; first temperature
alternates by case. Fifteen minutes including loading, 90s readiness, 45s/request,
existing memory/storage guards. Reuse retained artifacts; no download/build/retry.
Stop on startup/transport/timeout/resource failure; semantic failures are saved
and remaining planned cases continue within budget. Explicit status/language/
meaning/constraint/quote reporting supplements the unchanged scorer. All six
temperature-zero cases must pass for calibration success, which authorizes no
heldout evaluation or reliable multilingual claim. Original smoke remains intact.
Five synthetic reporting checks passed; exact holdout overlap is absent. The runner
exited 1 at the preflight RAM/disk guard before loading; no request or timed window
started. Subsequent inspection observed 3,933,028,352 bytes available RAM below the
4,026,531,840-byte preflight minimum, with sufficient disk. Exact values at the
failing guard were not captured. All twelve case/temperature outcomes are recorded
as unexecuted, not semantic failures. No retry, download, rebuild or model exposure
occurred; original smoke, frozen inputs and reusable artifacts remain intact.
Calibration did not establish success; this configuration is stopped pending review.
DESIGN remains in-progress with final acceptance pending; no tuning or Git delivery.
Subsequent read-only memory diagnosis: the guard reads host/VM MemAvailable rather
than cgroup headroom; visible cgroup has no finite max/high and no OOM events.
The 3.75 GiB threshold numerically equals cap+reserve; its original derivation is
not explicit. Orphaned test collectors are too small to reliably close the gap.
A larger-memory environment is recommended, not authorized or upgraded. A separate
future logging entry point records the exact sample/threshold/time without changing
limits or original frozen files; four synthetic checks passed. See the calibration
record and memory_diagnosis.json. No process termination or inference occurred.
Owner requested a concrete machine-change proposal only on 2026-10-11. The
calibration record now proposes the smallest offered >=16 GiB option (documented
4-core target, $0.36/active hour), preservation/verification, one unchanged
12-request calibration and return to the original machine. Actual account
availability/machine IDs remain unverified; no credentials/allowances were read.
Inventory includes uncommitted work and ignored persistent artifacts; no machine
change, restart, termination, inference or Git delivery occurred. The complete
sequence awaits owner approval; DESIGN remains in-progress/final acceptance pending.

Owner approved that sequence on 2026-10-11, conditional on the offered 4-core/
16 GiB machine, for one unchanged calibration only. Large reusable model/build
artifacts stay under /workspaces with hashes and are excluded from the downloaded
checkpoint, superseding the proposal's archive scope. Save editor buffers, refresh
inventory/hashes, checkpoint changed/untracked project work and diagnostic logs,
and confirm the independent download before any machine change. Current/target
machine type/storage require manual selector confirmation. After reconnect, stop
on file/Git/resource/CPU-compatibility mismatch without rebuilding; keep two
threads, frozen inputs, guards and the 15-minute/90s/45s limits. No further
downloads, retries, tuning or heldout evaluation. Preserve results and verify the
return to the recorded original machine; report promptly if blocked and aim for
less than one larger-machine active hour. The owner confirmed all editor buffers
saved and both checkpoint files downloaded locally. The selector confirms original
2 cores/8 GB RAM/32 GB storage and offered target 4 cores/16 GB RAM/32 GB storage.
At 16:44 Europe/Berlin the owner reported applying the approved change. Actual
application/restart/reconnection remain unverified; no calibration has started. See
[handoff](../experiments/uc001_multilingual/qwen_spike/calibration_B_2026_10_11/machine_change_handoff.json).
DESIGN remains pending; no production changes or Git delivery.

After owner-confirmed reconnection, the upgraded host exposes four CPUs, AMD EPYC
7763, 16,770,494,464 bytes usable RAM and 13,875,003,392 bytes available; workspace
capacity is unchanged. All 129 checkpoint project/diagnostic files (including the
three recorded handoff updates) and 12,665 reusable artifact files match. Branch,
HEAD, index and worktree inventory are preserved. CPU compatibility fails: the
original Intel Xeon native build uses -march=native, while the new AMD host lacks
the original AVX-512 flags. Stop before binary/model execution; no rebuild, loading,
calibration request or retry occurred. All twelve requests remain unexecuted.
Return to the recorded 2-core/8 GB/32 GB option now requires manual selection,
restart and verification; actual return remains pending. See the calibration
record and [verification](../build/checkpoints/uc001-machine-change-20261011-1427/reconnect_verification.json).
This is a compatibility stop, not an observed model/startup failure; DESIGN remains
in-progress with acceptance pending.

Owner amended the sequence on 2026-10-11: remain temporarily on the current
4-core/16 GB/32 GB machine for one experimental portable rebuild and one unchanged
calibration. [Extension record](../experiments/uc001_multilingual/qwen_spike/portable_2026_10_11/REPRODUCE.md).
Reuse the pinned source/model/toolchain without downloads or version changes;
separate Git-ignored /workspaces build and preserved original binary/logs.
GGML_NATIVE=OFF, fixed supported SSE4.2/AVX/AVX2/FMA/F16C/BMI2, AVX-VNNI/AVX-512/AMX
off; inspect effective flags and compatibility before loading. Fresh maximum
45 minutes from extension execution start: build at most 30 minutes, calibration
at most 15 minutes, two inference threads and existing safeguards. Cases/prompt/
schema/validator/seed/.7-vs-0/order are unchanged. Build/startup failure stops;
no retry cycle, tuning or heldout evaluation. Preserve results, then manually return
to 2 cores/8 GB/32 GB and verify actual return. Three synthetic flag-guard checks
passed; execution has not started at this authorization entry. DESIGN stays pending;
no production integration or Git delivery.

Portable extension actual closeout: 17:29:19–17:47:17 Europe/Berlin, 17m58.64s total.
Build passed in 13m05.29s (exit 0), with all 223 effective compile commands free of
native/unsupported switches and source hashes unchanged. New binary --version
passed; original binary/logs are separately preserved. Readiness 1.46s; twelve
requests completed in the unchanged plan, all HTTP 200/finish stop/cache_n=0.
Actual model calibration failed: 0/12 passes, including required 0/6 at temperature
zero. Incorrect supported-language classification, invented constraints, subject/
action label mismatches and ungrounded quotes are recorded separately per case.
No operational failure, acquisition, retry, tuning or heldout exposure occurred.
Calibration 4m28.90s; peak inference RSS 2.08 GiB, scratch 2.21 GiB, guards unchanged.
Owned model exited 0; driver exited 1 for failed calibration. Twelve synthetic
checks passed separately and establish no model success. Original results/markers/
deadlines remain intact. Configuration is stopped pending review; return to original
2-core/8 GB/32 GB requires manual selection/restart/reconnection and is not complete.
See [case report](../experiments/uc001_multilingual/qwen_spike/portable_2026_10_11/CASE_REPORT.md).
DESIGN remains Phase 2/in-progress, acceptance pending; no production or Git delivery.

Experiment closed after owner-confirmed return and read-only verification on
2026-10-11. Actual return resources: two CPUs, 8,327,036,928 bytes usable RAM,
5,502,414,848 bytes available and unchanged 33,636,024,320-byte workspace capacity;
physical CPU is now Xeon Platinum 8573C rather than the original 8370C. Resource
shape matches the original 2-core/8 GB/32 GB machine. All 206 saved project/record/
diagnostic files and 13,629 native/portable artifact files match; frozen inputs,
both archives, branch/HEAD/index and pre-existing work are preserved. No experiment
process remains. [Return verification](../build/checkpoints/uc001-machine-change-20261011-1427/return_verification.json).
The tested pinned Qwen3-1.7B Q8_0 configuration failed calibration and is not
accepted for production. Keep semantic classification/constraint/language errors,
quote-grounding failures and normalized-label mismatches distinct; label mismatch
alone does not establish a different underlying object/action. This conclusion
does not generalize to all local models or other configurations. Concise
[findings](../experiments/uc001_multilingual/qwen_spike/portable_2026_10_11/REPRODUCE.md#experiment-closed--verified-return)
link detailed evidence. Approved multilingual requirements and validators remain
unchanged; DESIGN remains Phase 2/in-progress with acceptance pending. No inference,
new experiment, download, rebuild, staging or commit occurred during closure.

Owner requested a concise A/B design decision on 2026-10-11, with no new experiment.
[ADR-004](adr/ADR-004-multilingual-interpretation-scope.md) is proposed: recommend A,
retaining approved multilingual free text with a demonstrably capable interpreter
on suitable Resolena-controlled infrastructure. The closed Codespace experiment's
limits are not production requirements. B explicitly replaces request interpretation
with structured fields and defers named free-text obligations; it retains reviewed
cross-language evidence, faithful explanations and all privacy/evidence/persistence
safeguards. Owner decisions: scope, resources/control or bounded form coverage, and
competent review/acceptance conditions. Model/host examples use current primary
sources and are unselected/unverified; no external inference is introduced.
Detailed architecture experiment history is preserved in the existing experiment
record; architecture now links concise findings and this proposed decision.
UC requirements/results remain unchanged; Phase 2/in-progress and DESIGN acceptance
pending. No download, installation, inference, production code or Git delivery.
Documentation verification: 99 preserved requirement/frozen-input/result/log hashes,
71 relative links and 24 anchors match; archived historical prose is preserved
after link rebasing. Branch/HEAD and empty index remain unchanged. Only the
pre-existing historical backlog whitespace warning remains.

Owner retained A on 2026-10-11: approved multilingual free text and privacy boundary
remain unchanged; B's amendments are not adopted. ADR-004 records this accepted
product direction only; interpreter/hosting and final DESIGN acceptance stay pending.
The [next-candidate proposal](../experiments/uc001_multilingual/qwen_spike/REPRODUCE.md#next-candidate-proposal--2026-10-11)
recommends Qwen3-8B Q8_0, based on publisher instruction-following/multilingual
benchmarks rather than size alone. Owner confirms a Windows 11 Pro/Ryzen 5950X/
64 GB/RX 6800 XT desktop available for up to two hours, with DxDiag driver/VRAM
details recorded; target-drive space, available RAM/VRAM and inference compatibility
are unverified. Proposed pinned Windows Vulkan runtime; CPU is a preselected
alternative, not an automatic retry. Connected two-CPU/7.76 GiB Codespace has no
exposed GPU and is unsuitable for this Q8 test. No desktop access is assumed.
Proposed 34 synthetic requests and frozen correctness/clarification/latency gates,
two-hour desktop window and new explicit resource/download caps need execution
approval. Paid infrastructure cap: $0 for recommended desktop; rental comparison
has a proposed $10 ceiling subject to quote/account/region approval, not authorized.
Electricity and qualified review effort/cost are separate and unpriced. No reviewers
are assumed; AI checks are exploratory. The 55 held-out inputs remain untouched.
No provisioning, download, installation, model run, production change or Git delivery.
Direction/proposal checks: 99 preserved hashes, 87 local links and 30 anchors pass;
archived history matches after link rebasing. Branch/HEAD and empty index preserved;
only the pre-existing backlog whitespace warning remains.

## Windows Qwen3-8B exploratory experiment — reviewed closeout 2026-10-13

The owner approved one Qwen3-8B Q8_0 experiment on the personal Windows desktop,
pinned llama.cpp Vulkan only, with local resource preflight and the proposed two-hour
window/caps. No paid infrastructure/reviewers, external inference, remote access,
firewall opening, driver update, additional prerequisite installation or CPU fallback.
AI-assisted expectations are explicitly exploratory, not independently validated.
The six known cases run first: any substantive semantic failure stops before the
24 new cases; quote/schema/normalized-label failures also block the unchanged strict
gate, with label mismatches reported separately. No tuning/retry. Candidate latency
targets do not amend product requirements. The 55 held-out cases remain untouched.

On 2026-10-13 the [version 1.0.0 bundle](../experiments/uc001_multilingual/qwen_spike/windows_qwen3_8b_v1/README.md)
was prepared with frozen cases/order/requests, verbatim pure prompt/schema/validator,
PowerShell preflight/setup/run/watchdog/cleanup and offline assessment. Publisher API
metadata confirms model 8,709,518,112 + runtime 33,337,769 = 8,742,855,881 bytes;
including the reserved 1 MiB bundle/metadata allowance fits the decimal 10 GB cap.
No model/runtime payload was downloaded in the Codespace. At bundle preparation,
Setup was to reverify exact metadata before acquisition. Ten offline harness checks passed; Windows parsing,
resource probes, runtime compatibility and GPU inference remain unexecuted.
The runner pauses for manual transfer/offline assessment after six cases while the
independent owned-process watchdog keeps original deadlines/resource guards active.
Artifacts/results/partial downloads and recovery markers are preserved through
cleanup. The preparation handoff proposed independent bundle download/hash checking,
then read-only Windows preflight; no Windows window had started at that record. UC-001 increment
1 / Phase 2 DESIGN / in-progress; interpreter/hosting/final DESIGN and qualified
linguistic validation pending. No production code/dependency changes or Git delivery.
Bundle handoff: [ZIP](../build/checkpoints/windows-qwen3-8b-v1.zip), 83,797 bytes,
SHA-256 `348d527dbd1ae4355e9bd2c23993ff20cf32af5a02a31569e3f36315858c72fc`;
[handoff record](../build/checkpoints/windows-qwen3-8b-v1-handoff.json).
All 49 payload hashes and ZIP entries match the freeze; positive/negative offline
known-gate integration passed with explicitly synthetic responses. Original frozen
inputs/prompt/validator/smoke/spec hashes match; no held-out contents were parsed.
These are harness/preservation checks, not model results or Windows test evidence.

Completed Windows evidence was reviewed on 2026-10-13:
[closeout and per-case findings](../experiments/uc001_multilingual/qwen_spike/windows_results_2026_10_13/REVIEW.md),
[verification](../experiments/uc001_multilingual/qwen_spike/windows_results_2026_10_13/review.json).
The uploaded ZIP matches the supplied SHA-256; all frozen payload/provenance hashes
and six gate receipts match. Unchanged offline reassessment on a separate copy
reproduces 2/6 strict passes, both English. DE/FR/IT fail canonical subject labels
without establishing wrong underlying meaning; the Spanish unsupported-language
negative control incorrectly reports understood/French with no uncertainty.
Exact quote grounding passes all six.
The strict gate stopped execution before the additional 24 cases/four repetitions.
All 55 held-out cases remain untouched and model-unexposed. Sampled resources and
latency meet experiment limits/targets; full GPU offload and acceleration remain
unestablished. Windows records consistently show planned owned-server shutdown,
watchdog completion and artifact-preserving cleanup; live Windows state is unverifiable
from this Codespace. This tested configuration is not accepted for production.
Proposed follow-up: review unsupported-language handling offline; review DE/FR/IT
canonical-label mismatches separately. Owner clarification on 2026-10-13 retains
EN/DE/FR/IT only: Spanish is a negative control for limitation/rephrasing behaviour,
not interpretation or translation support. No language requirement or inference/
experiment authorization is added; frozen tests, results and failed gate remain
intact. Direction A and requirements remain unchanged; interpreter,
hosting, final DESIGN acceptance and qualified linguistic validation remain pending.
PHASE 2 / STATUS in-progress retained; no production change or Git delivery.

On 2026-10-13 a [separate v2 follow-up proposal](../experiments/uc001_multilingual/qwen_spike/windows_qwen3_8b_followup_v2/PROPOSAL.md)
was prepared using existing evidence: clarify normalized English values versus
verbatim quotes and unsupported/null/uncertainty handling; no kettle-specific patch.
Proposed maximum 18 requests/30 minutes: six exposed cases with v2, then six fresh
examples paired across v1/v2 only after the unchanged strict gate passes. Model,
sampling, schema, scoring and resource guards stay unchanged. Verbosity 4 is a
separate logging proposal for both arms, supported by inspection of the pinned
source; actual full offload remains unconfirmed. Owner approval and a separate
execution-bundle freeze are required. No execution/harness implementation occurred;
v1 results/gate and all 55 held-out cases remain intact. DESIGN remains in progress.

On 2026-10-14 the owner authorized separate v2 execution-bundle preparation and
offline checks only. [Frozen bundle/handoff](../experiments/uc001_multilingual/qwen_spike/windows_qwen3_8b_followup_v2/BUNDLE.md)
records both prompts, 12 expectations and 18 exact requests/order/configuration.
Eight hash-bound manual assessment pauses enforce the six-known-v2 gate and each
fresh-v2 gate; v1 content failures may continue, either-arm operational failures
stop. All pauses count against the immutable 30-minute deadline. Fourteen synthetic
checks passed, including stale receipts, expiry, arm/request binding and final-export
integrity; these establish harness behaviour only. Windows parser/receipt/timer/export
checks and actual prompt capacity/offload/resource verification remain local
prerequisites. Reuse pinned artifacts without download/copy/rebuild; export records
confirmed owned exits and artifact-preserving cleanup. The bundle denies inference
without separate owner approval. V1's failed gate/uploads, approved requirements
and 55 held-out cases remain unchanged/unexposed. Phase 2 DESIGN/in-progress and
qualified linguistic validation remain pending; no production changes or Git delivery.

The uploaded [2026-10-14 v2 attempt](../experiments/uc001_multilingual/qwen_spike/windows_v2_results_2026_10_14/REVIEW.md)
matches its expected archive SHA-256 and closed as an operational failure with
zero evaluation requests, not semantic failures. Startup logged 37/37 GPU layers;
acceleration, prompt capacity and language capability were unmeasured. The offload
parser reused PowerShell's automatic Matches variable; a later ownership error
followed confirmed shutdown and is consistent with a race, without conclusive
identity evidence. Original approval/freeze/markers/deadline/results are preserved.
Owner authorized [separate harness 2.0.1 repair/offline checks](../experiments/uc001_multilingual/qwen_spike/windows_qwen3_8b_followup_v2_0_1/BUNDLE.md)
only: distinct regex collection, exit-aware identity checks with live mismatch
protection and added regressions. Nineteen Linux-available checks pass; Windows
PowerShell 5.1 parser/real-log/mocked-race/protocol checks remain pending. All
evaluation payloads/settings/scoring/guards remain unchanged. No inference,
downloads, marker reset, production work or Git delivery; DESIGN stays in-progress.

Owner authorized Yarn APT signing-key repair and Microsoft Debian-repository
PowerShell 7 installation on 2026-10-14, then isolated offline checks. Backups are
retained; Yarn remains enabled with repository-specific signed-by and signature
verification. PowerShell 7.6.7 Core/version check passes, with no existing-package
upgrade/removal or application dependency change. [Nineteen isolated PowerShell 7
regressions passed](../experiments/uc001_multilingual/qwen_spike/windows_qwen3_8b_followup_v2_0_1/offline_pwsh7_20261014/README.md):
original Groups reproduction, real-log/negative evidence and mocked ownership/exit
cases, plus nine parsed scripts. Frozen bundles/results/markers remain intact.
Windows PowerShell 5.1 and native Windows verification remain pending; no inference,
experiment restart, new deadline, Git delivery or DESIGN advancement is authorized.

The [completed Windows v2.0.1 closeout](../experiments/uc001_multilingual/qwen_spike/windows_v2_0_1_results_2026_10_14/REVIEW.md)
verifies 5/6 strict known-case passes (EN×2/DE/FR/IT), German no-replacement and
13/13 exact quotes. Spanish remains an unsupported-language negative control;
understood/en with empty uncertainty fails the unchanged gate. Twelve generation
requests did not run; production acceptance/general multilingual support remain
unverified. Recorded 37/37 GPU layers/resources/exits pass operational checks,
without live Windows inspection or measured acceleration. The original export
fails closeout for one omitted historical fixture; a labelled supplemented copy
adds only its freeze/manifest-matching bytes and passes the unchanged verifier.
Original archives, failures, markers and scoring remain intact. Proposal: review
unsupported-language routing offline. Direction A, requirements/privacy and the
55 untouched held-out cases remain unchanged; DESIGN/in-progress and linguistic
validation stay pending. No continuation receipt, new run or Git delivery.

On 2026-10-15 an [input-language separation DESIGN proposal](../experiments/uc001_multilingual/qwen_spike/windows_v2_0_1_results_2026_10_14/REVIEW.md#input-language-separation--design-proposal-2026-10-15)
confirms C6's actual template contained unsupported/null/limitation instructions
and its schema allowed the required response; root cause remains unproven.
Compare a focused call to the retained model with an independent local detector;
recommend one proposed CPU-only screen, 24 new controls plus exposed C6, 30 minutes,
pending separate acquisition/setup/execution approval. No production selection,
requirement/scoring change, held-out access or run occurs. Closed results and
approvals are preserved; Phase 2 DESIGN/in-progress and linguistic review pending.

The owner then approved one bounded Lingua 2.2.0 investigation under those limits.
Its [closeout](../experiments/uc001_multilingual/lingua_B_2026_10_15/README.md)
records a pre-installation harness failure: the verified wheel names its matching
Apache license `LICENSE`, while the frozen verifier assumed `LICENSE.txt`.
One acquisition totalled 170,430,323 bytes; zero detector calls/records ran.
No installation, retry, threshold change or application integration occurred;
the wheel, freeze, failure and deadline are retained. Capability/timing remains
unmeasured. A separately versioned offline verifier repair is proposed only.
Previous evidence/requirements and held-out cases are preserved; DESIGN and
qualified linguistic validation remain pending.

Owner-authorized offline [verifier 1.0.1 repair](../experiments/uc001_multilingual/lingua_B_verifier_v1_0_1/README.md)
now resolves declared license paths and preserves exact content/hash checks.
Four focused regressions pass: retained wheel, missing, altered and mislocated
license content. No downloads, installation, Lingua import or detector execution.
The frozen failed attempt/deadline remain unchanged. A future separately authorized
run still needs a versioned runner bound to new run storage/deadline and this
retained-wheel verifier; no new timed attempt or production selection is made.
Controls/scoring/limits and DESIGN/in-progress/linguistic-review status are unchanged.

The owner approved [runner 1.0.2 integration and one bounded attempt](../experiments/uc001_multilingual/lingua_B_runner_v1_0_2/RESULTS.md).
Seven offline integration checks passed; verifier 1.0.1, retained-wheel offline
installation and all 50 records/100 calls completed under one new deadline.
Raw-label screen failed: 12/13 required identities match per pass; exposed Spanish
C6 ranks Portuguese. Both are unsupported product languages, but that does not
pass the frozen identity check or establish actual limitation handling. Mixed/
shared/dialect risks remain; interpretation/contract routing was not executed.
Latency/resource targets pass, owned exits/cleanup are confirmed, zero new downloads
or retries occurred and original evidence/controls/limits/held-out cases are preserved.
No production selection; DESIGN and qualified linguistic validation remain pending.

## UC-001 increment 1 — input policy approved 2026-10-09

Owner approved decision 1: recognisable subject plus valid country permits
search; goal, budget, current price and locality are optional and remain
unspecified when absent. Infer neither cheapest nor lowest environmental impact;
preserve stated constraints. Unclear subject needs correction; recognisable
subject without knowledge is insufficient coverage, not invalid input.
Ambiguous locality needs clarification or explicit country-only choice; never
silently remove it or restore a cleared country to Switzerland.

Acceptance examples: “Repair my bicycle”/Switzerland without optional fields
passes input validation; whitespace or “something better” requires correction;
a recognisable subject without knowledge is valid input with insufficient coverage.
Constraint preservation, ambiguous locality, explicit country-only continuation
and cleared-country examples are recorded in
[UC-001 Acceptance](specs/UC-001-FIND-AND-SELECT-ALTERNATIVE.md#acceptance).

This approval covers only the input policy and its examples. Complete Errors, Acceptance
and Tests remain pending. Decision 2 was pending at this input-policy review;
its subsequent scoped approval is recorded below. Freshness thresholds and
remaining policies require owner approval. UC-003
selection policies remain separate. UC-001 stays the sole active UC, Phase 1 /
in-progress; journey increment 1 is planning focus and full scope is incomplete.
Verification: focused edits reviewed; 87 integrated local links/anchors, whitespace
and template checks passed. Existing work and phase/status are preserved;
no implementation, staging, commit or phase advance.

## UC-001 increment 1 — evidence distinction approved 2026-10-09

Owner approved decision 2 and its examples: evidence is essential for subject
relevance or explicit goals/constraints, including necessary geographic
applicability. “Cheaper” needs a supported cost comparison even without a budget.
Every displayed factual claim needs evidence, including optional information.
Optional information may be omitted/unknown without implying financial or
environmental advantage. Missing evidence means unverified; contradicting
evidence fails the relevant requirement. One unsupported candidate does not
disqualify others; passing this check does not establish overall sufficiency.

Approved examples cover unknown price with/without budget or cheaper goal,
missing current-price baseline, unverified town coverage, unknown versus
confirmed non-delivery, unsupported optional claims and independent candidates.
Detailed examples: [UC-001 Acceptance](specs/UC-001-FIND-AND-SELECT-ALTERNATIVE.md#acceptance).

At this evidence-distinction approval, source quality was pending; its subsequent
scoped approval is recorded below. Freshness, overall sufficiency, minimum comparison
content, currency/fallback policies and UC-003 selection eligibility remain pending.
This approval does not approve the full specification or complete Errors,
Acceptance or Tests sections. Phase 1/in-progress and full scope incomplete
remain unchanged. The source-quality review followed this decision.
Verification: scoped edits/examples reviewed; 88 integrated local links/anchors,
whitespace and template checks passed. Existing work, approval history and phase
state are preserved; no implementation, staging, commit or phase advance.

## UC-001 increment 1 — source quality approved 2026-10-09

Owner approved the claim-specific source-quality policy and examples: traceable
publisher/reference/support; competence and scope appropriate to the claim;
substantiated comparison inputs/basis (environmental method/scope); unresolved
same-scope conflicts cannot produce verified claims. No scores, weights or
mandatory citation counts. Assess stored reviewed evidence in increment 1.

Provider/retailer sources support their own scoped statements, labelled as such;
acceptance is not independent verification or guaranteed price/stock/availability.
Compare variant, geography, conditions and applicable dates before declaring
conflict. Traceable inputs plus documented calculation, baseline and assumptions
can support a result not stated verbatim in a source.

Approved examples: scoped provider coverage, retailer listing, unsupported
environmental slogan, documented environmental comparison, differing scopes,
same-scope disagreement and calculated comparison. Details:
[UC-001 Acceptance](specs/UC-001-FIND-AND-SELECT-ALTERNATIVE.md#acceptance).

Quality remains separate from freshness, applicability and overall sufficiency.
Freshness periods/date handling, overall sufficiency, minimum comparison content,
currency/fallback and UC-003 selection eligibility remain pending. This approval
does not approve the complete specification or Errors/Acceptance/Tests sections.
Phase 1/in-progress and full scope incomplete remain unchanged. Freshness policy
is next for owner review; no automatic refresh or research capability is authorized.
Documentation checks pending; no implementation, staging, commit or phase advance.

## Decomposition and journey increments — 2026-10-09

Owner-approved decomposition: UC-001 finds/compares; UC-003 selects a displayed
alternative. Provenance and mapping: [ADR-002](adr/ADR-002-use-case-decomposition.md).
[UC-003](specs/UC-003-SELECT-DISPLAYED-ALTERNATIVE.md) is a draft dependency,
not another active use case. Errors, Acceptance and Tests remain pending review
in both specs; no implementation is authorized.

Journey planning focus: increment 1. This is separate from PHASE: 1 / SPECIFY
and does not mark delivery started. Full mandatory scope: **incomplete**.

| Journey increment / delivery order | UC-001 contribution/status | UC-003 contribution/status | Journey validation |
|---|---|---|---|
| 1 — Sufficient existing knowledge | Location-aware retrieval, assessment and persisted comparison; specification draft | Explicit selection and evidence integrity; specification draft | Pending: comparison/selection end-to-end |
| 2 — Insufficient/empty knowledge | Approved conditional research and the same comparison guarantees; specification draft | Same selection guarantees; verification on researched results planned; specification draft | Pending: research journey end-to-end |

Track phase outputs/evidence for the sole active UC separately from this matrix.
Completing its selected phase or increment 1 does not establish completion of both
UCs or the full mandatory journey. UC-002 stays optional and deferred until UC-001 + UC-003,
including research, are validated. No permission-based location detection is authorized.
Verification: original steps 1–7 (including location additions) remain unchanged
in UC-001; steps 8–9 are transferred unchanged to UC-003. Location privacy,
policy drafts and all eight location scenario rows are preserved. Full changed/new
documents and tracked diffs reviewed; 86 local links/anchors, template structure,
tracked and new-document whitespace checks passed. ADR-001, router/skills,
branch/HEAD and index are unchanged. No application checks or implementation;
nothing staged/committed/pushed. Decomposition edits and both specs' pending
sections await owner review; unresolved policies remain unapproved.

## UC-001 search-location amendment — 2026-10-09

Owner-approved requirement amendment during SPECIFY: editable Switzerland
default (not detection), optional town/postcode, location-aware comparisons and
minimal location retention within existing privacy boundaries. Detailed approved
behaviour and draft errors/criteria/scenarios:
[UC-001](specs/UC-001-FIND-AND-SELECT-ALTERNATIVE.md).

- October 7 approvals and the nine-step flow are preserved. Errors, Acceptance
  and Tests remain draft/pending owner review; Phase 1 stays in-progress.
- Validation, fallback, currency, ranking and research-minimization policy options
  require owner resolution before implementation; no code/tests are authorized.
- Permission-based “Use my location” is deferred, not implemented or authorized.
- At this amendment's review, UC-001/UC-003 decomposition was unapproved.
  The later owner-approved decomposition is recorded above; UC-002 remains
  reserved for optional image input with the full-journey dependency.
- Verification: changed documents/diffs and 64 local links/anchors reviewed;
  links and whitespace passed. Original approved flow text and order are preserved;
  phase/status, branch/HEAD and index are unchanged. No application checks run,
  staging, commit, push or phase advance. Amendment edits and draft criteria
  await owner review; requirement approval does not approve these drafts.

## Documentation migration — 2026-10-09

Separate owner-authorized maintenance; UC-001 remains PHASE: 1 / STATUS:
in-progress. This task does not complete SPECIFY or authorize UC-001 code/tests.

- Decision approved: Codex in VS Code in Codespaces is primary; repository
  Markdown is maintained as the source of truth. See [ADR-001](adr/ADR-001-codex-repository-workflow.md).
- Scope: create canonical architecture/workflow documentation and the ADR;
  reconcile PROJECT.md, AGENTS.md and README.md while preserving previous work.
- Acceptance: preserve product/privacy decisions, bootstrap acceptance and
  October 7 UC approvals; distinguish historical evidence and follow-up proposals.
- Checks: review full documents/diffs, relative links, stale active guidance,
  tracked whitespace, new documents and unchanged UC-001 content.
- Documentation implemented on 2026-10-09. Full changed/new Markdown and tracked
  diffs reviewed; stale-role search found only optional or historical references.
  All 48 relative links/anchors across 17 maintained Markdown documents passed.
  Tracked `git diff --check` and separate new-document whitespace checks passed.
  UC-001 SHA-256 matches the pre-task fingerprint; phase/status and approvals
  are preserved. Branch/HEAD are unchanged and nothing is staged.
- Inspected unchanged: UC-001, UC-TEMPLATE.md, frontend/README.md,
  .github/copilot-instructions.md and all six canonical phase skills. The
  templates/pointer and linked phase procedures require no workflow rewrite.
- Verification is assistant self-review, not independent validation. No
  application, CI, MCP, Docker or deployment checks were run; documentation-only
  scope requires content/link checks rather than code tests. No credentials read.
- Migration review: initially pending; accepted by the owner on 2026-10-09,
  including AGENTS.md routing, the repository architecture/workflow documents,
  ADR-001 and the DESIGN skill correction. The correction routes architecture
  to ARCHITECTURE.md and shortens duplicated PROJECT.md scope without changing
  constraints; affected links, whitespace and preservation checks passed.
- Owner authorized a documentation checkpoint on the current branch, including
  UC-001 as an explicitly incomplete draft. This acceptance does not complete
  Phase 1, approve unresolved UC-001 behaviour or authorize CI/CD/MCP proposals.

## Proposed course follow-up work

These proposals authorize no installation, configuration or implementation.
Details and phase placement: [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md#proposed-follow-up-work).

- Application CI: frontend lint/build and meaningful automated tests.
- Reviewed PRs and verification of bootstrap integration into main; merge
  status has not been established.
- One useful development MCP pilot, initially Context7, with permissions and
  a synthetic comparison with/without the tool.
- Reproducible Docker release and human-authorized deployment.
- Hosting, persistent storage and recovery decisions during DESIGN.

## Bootstrap progress

- [x] Create the repository and bootstrap branch.
- [x] Configure Codespaces with Python 3.12 and Node.js 24.
- [x] Record the accepted scope, architecture and privacy boundaries.
- [x] Create the initial backend and test directories.
- [x] Initialize the React/TypeScript frontend with Vite and ESLint.
- [x] Verify frontend build, lint and browser startup.
- [x] Install backend dependencies, including SQLAlchemy.
- [x] Pin direct backend dependency versions and check compatibility.
- [x] Document setup commands and verification evidence.
- [x] Commit and push the initial bootstrap checkpoint.
- [x] Complete the final bootstrap review and resolve any findings.
- [x] Record owner acceptance and close BOOTSTRAP.

## Backlog

- UC-001: specify text/location input, knowledge reuse, research when needed,
  evidence-backed comparisons and persistence. 
- UC-003: specify explicit selection from UC-001, saving confirmation and evidence integrity.
- UC-001 + UC-003 pending SPECIFY clarification, proposed on 2026-10-09: comparison
  estimates and explicit selection must not be presented as proof of realized
  savings, completed behaviour or achieved environmental impact. Resolve with
  the owner before changing approved behaviour/acceptance; no Saver entities,
  logging features or integration contracts are authorized. Context:
  [PRODUCT_CONTEXT.md](PRODUCT_CONTEXT.md#pending-specify-clarification).
- UC-002: optional image-assisted input only after the full mandatory UC-001 +
  UC-003 journey, including research, is validated.

## Product-context documentation — 2026-10-09

Owner-authorized documentation only: add concise product context and discovery
links; preserve approved scope/privacy, UC-001, phase/status and existing work.
Acceptance/checks: 400–600 words, correct glossary/provenance, working local
links, consistent boundaries, tracked/new-document whitespace and unchanged UC.
Review: initially pending; accepted by the owner on 2026-10-09, including
PRODUCT_CONTEXT.md and the concise AGENTS.md routing addition.
The selection/realized-savings proposal remains pending SPECIFY, not approved
feature behaviour. Verification: product context is 561 whitespace-delimited
words; all 58 local links/anchors across eight integrated documents passed.
Content, terminology and tracked diffs reviewed; no scope/privacy conflicts
found. Tracked and new-document whitespace checks passed. UC-001, architecture,
workflow and ADR fingerprints, phase/status, approval history and branch/HEAD
are unchanged. No application checks run; nothing staged or committed.

## Working agreement

- Keep one active use case small enough to deliver vertically.
- Update this file when the lifecycle phase or active use case changes.
- Link decisions and validation evidence from the relevant project artifact.
- Follow the baseline in [PROJECT.md](PROJECT.md), the scope/privacy boundaries
  in [ARCHITECTURE.md](ARCHITECTURE.md) and [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md).
- Keep detailed acceptance criteria and design decisions in SPECIFY/DESIGN.
- Guide the project owner one step at a time; obtain required confirmation
  for unresolved decisions and phase transitions. Continue already-authorized
  work within its scope.

## Evidence

- Baseline, versions and historical setup checks: [PROJECT.md](PROJECT.md).
- Canonical scope and architecture: [ARCHITECTURE.md](ARCHITECTURE.md).
- Bootstrap work branch: setup/phase-0-bootstrap.
- Initial bootstrap checkpoint committed and pushed on 2026-10-04.
- Final bootstrap review completed on 2026-10-05.
- Project owner explicitly accepted BOOTSTRAP as complete on 2026-10-05.
- Acceptance covers project initialization and the documented baseline.
- Project owner selected SPECIFY for UC-001 on 2026-10-07.
- UC-001/UC-003 functionality, database connectivity, automated application
  tests and deployment remain pending.
