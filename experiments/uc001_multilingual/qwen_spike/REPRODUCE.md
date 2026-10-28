# Qwen structured-interpretation spike

Owner-authorized 2026-10-10; isolated DESIGN experiment, no production integration.
All inputs/oracles are synthetic and AI-authored; no independent linguistic review.

## Recorded run

Reviewed on 2026-10-11: checksum-verified acquisition and the single-job CPU build
succeeded; model calibration/evaluation did not run. First startup failed because
the client did not wait for readiness; the second encountered its stale Unix
socket. `results.json` preserves the second failure, `startup_attempt_1.*` the first.
The harness now polls health and checks a stale owned socket before removing it;
the socket correction was never executed and differs from the executed harness
hash in `freeze.json`. `change_history.json` and `closeout.json` record that boundary.
`operational_socket_fix.patch` records the exact unexecuted change; removing its
added block reconstructs the executed harness hash from `freeze.json` (verified).
No prompt/model/scorer tuning; the 32 new cases remain model-unseen.

At resumption the recorded deadlines had expired and the exact scratch tree was
already absent; its removal cause/time are unknown. No owned model process remained,
and no further downloads/inference were performed. A continuation requires a new
explicit bounded authorization and resource check; do not run these commands with
expired timestamps or silently renew the budget. Retain the existing results before
any separately authorized rerun. Model correctness/latency/loaded-memory/translation
are unmeasured; six harness checks do not demonstrate model capability.

## Reproduction

From the repository root, use the existing Python environment:

1. Run `.venv/bin/python -B -m unittest discover -s experiments/uc001_multilingual/qwen_spike -p test_spike.py -v`.
2. Review `config.json`, resource guards and `upstream_verification.json`. Recheck
   current RAM/disk and publisher metadata/checksums. Set a new authorized start time
   for any rerun; the recorded two-hour deadline must not be silently renewed.
3. Freeze new cases/scoring/prompt before evaluation. `freeze.json` records this run's
   hashes. `heldout_v2.json` is separate from calibration and the older known sample.
   Reusing either evaluation file later is reuse, not unseen validation.
4. Run `.venv/bin/python -B experiments/uc001_multilingual/qwen_spike/prepare.py`.
   It downloads temporary CMake/source, builds `llama-server` with one compile job,
   then acquires the checksum-verified Q8 model. All artifacts live in its owned
   `/tmp/resolena-qwen-spike-*` tree; no pip/apt/global/application dependency changes.
5. Run `.venv/bin/python -B experiments/uc001_multilingual/qwen_spike/evaluate_model.py`.
   The harness uses a private Unix socket (no TCP listener/forwarded service), local
   model path and offline mode, disabled agent/Web UI, and traces owned network
   syscalls. No actual user requests or application data are used.
6. Preserve generated small results/log tails/configuration. Stop only owned process
   groups; verify ownership/path against `preparation.json`, then remove only its
   exact temporary tree. Preserve existing parser/data and this reproduction record.

Pinned source commits, artifact sizes/checksums, exact build flags, context/sampling,
time/memory/disk limits are in `config.json`. The source archive's actual checksum
and measured build resource peaks are in `preparation.json`. Build target dependencies
are bundled; any missing extra requirement stops the experiment before installation.

## Assessment boundaries

Quote spans are resolved against original Unicode text; matching spans/valid JSON
do not validate meaning. The scorer checks expected subject/action/goals/constraints,
including negation and exclusions, and reports structural failures separately from
semantic discrepancies. Partial/rejected values never drive qualification.
Old-case semantic expectations add explicit no-repair/replacement-required/name/location
checks; the prior frozen parser results remain untouched. Shared-field comparisons
and additional checks must remain distinguishable.

All network/latency measurements are instrumented with strace, not a general proof
of no telemetry or a production benchmark. Status/latency/peak RSS are reported
separately, per language and case. No model weight tuning; later prompt/scorer changes
must be recorded and evaluation reuse disclosed. Request interpretation says nothing
about evidence-translation fidelity, factual quality/freshness or persistence.

## Next-candidate proposal — 2026-10-11

**Proposal only; execution approval pending.** The owner retained free-text direction
A in [ADR-004](../../../docs/adr/ADR-004-multilingual-interpretation-scope.md).
The closed 1.7B experiment and all original deadlines/results remain intact.
Recommend one Qwen3-8B Q8_0 request-interpretation test on the owner's Windows
desktop. This temporary synthetic-data environment is not production hosting.

### Candidate and rationale

The publisher's [technical report, Tables 18/20](https://arxiv.org/html/2505.09388v1)
reports non-thinking IFEval strict-prompt accuracy of 83.0 versus 68.2 for 1.7B,
and multilingual Multi-IF scores of 69.2 versus 44.7. These instruction-following
results motivate testing supported-language classification and preservation of
explicit conditions without invented constraints. They are publisher benchmarks,
not evidence that Q8_0 meets Resolena's extraction/quote contract or four-language
requirements. Same-family chat-template/runtime compatibility permits a controlled
comparison. Size alone, general benchmarks and exact quotes cannot prove semantics;
literal quote fidelity and canonical-label adherence remain distinct test gates.

Candidate: [official Qwen3-8B-Q8_0.gguf](https://huggingface.co/Qwen/Qwen3-8B-GGUF/blob/7c41481f57cb95916b40956ab2f0b139b296d974/Qwen3-8B-Q8_0.gguf),
Apache-2.0, about 8.71 GB; revision
`7c41481f57cb95916b40956ab2f0b139b296d974`, publisher SHA-256
`408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6`.
No candidate artifact has been acquired or checked locally. This is not a production
model selection; failure would stop this configuration, not reject all local models.

### Environment comparison and Windows feasibility

| Route | Availability/evidence | Setup, resources and cost |
|---|---|---|
| Owner desktop — recommended | Owner confirms up to two hours: Windows 11 Pro, Ryzen 9 5950X/16 cores, 64 GB DDR4-3200, RX 6800 XT/16 GB; approximately 3.19 TB free in aggregate. DxDiag: display VRAM 16,337 MB, driver 32.0.21045.5002 dated 17 August 2026, WDDM 3.2. No direct access or independent local verification. | Estimate 30–60 minutes for checks, transfer/hash verification, portable runtime and transport preparation, depending on bandwidth and existing tools. No paid hardware/software expected. Electricity at the owner's tariff and review labour are unestimated; this is not a verified zero all-in cost. |
| Connected Codespace | Read-only current snapshot: two allowed CPUs, 8,327,041,024 bytes RAM, 5,569,531,904 available, no swap; 24,010,342,400 workspace bytes free, no NVIDIA/DRI devices; visible cgroup max/high unlimited and OOM counters zero. | Q8 weights alone exceed available/total RAM. Reject this test location; its limits do not constrain production. |
| Temporary self-managed rental — comparison only | [AWS g5.2xlarge](https://aws.amazon.com/ec2/instance-types/g5/) documents 8 vCPUs, 32 GiB RAM and 24 GB A10G VRAM. Account entitlement, regional GPU quota, actual capacity and price are unverified; [quotas](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-resource-limits.html) must be checked by the owner. | Estimate 45–90 minutes for approved regional host/image/driver setup and preserving outputs. Proposed two active hours, up to 80 GB durable disk for at most one day; $10 infrastructure ceiling including applicable taxes, not a quoted price. Require compute quote <=$2.50/hour and combined storage/network/address/tax allowance <=$5; no credits assumed. Separate approval required, no automatic rental fallback. |

Recommended runtime: official [b11429 Windows x64 Vulkan release](https://github.com/ggml-org/llama.cpp/releases/tag/b11429),
same source commit `d81235049384534c167caea52b85a694f6103d14` as the prior runtime;
GitHub marks b11429 pre-release. [Published asset digests](https://github.com/ggml-org/llama.cpp/releases/expanded_assets/b11429):

- `llama-b11429-bin-win-vulkan-x64.zip` (~31.8 MB), SHA-256
  `1bfe78ad9168b79fa02bf67f6af9f5e17a966d824d77238517f7bef12ac73b36`.
- CPU alternative `llama-b11429-bin-win-cpu-x64.zip` (~18.5 MB), SHA-256
  `1283323272b04cd07905816a597a0da810918102de958f4ff6f7bbaa70ed2efe`.

[AMD documents Windows 11, 16 GB memory and Vulkan API support for this card](https://www.amd.com/en/support/downloads/drivers.html/graphics/radeon-rx/radeon-rx-6000-series/amd-radeon-rx-6800-xt.html);
[pinned llama.cpp documentation](https://github.com/ggml-org/llama.cpp/blob/d81235049384534c167caea52b85a694f6103d14/docs/build.md)
documents a Windows Vulkan backend. DxDiag proves neither Vulkan compute features,
available device budget nor successful Q8 inference. No CUDA compatibility, ROCm
support or accelerated performance is assumed. Existing AMD driver is retained:
missing dependencies, unsupported instructions/device features or a required driver
update stop the proposal's run rather than trigger installation/build troubleshooting.
The original Linux binaries cannot execute natively on Windows.

Before any model acquisition/loading, locally verify target-drive free space,
available RAM and dedicated VRAM, installed x64 runtime dependencies and CPU
compatibility; after approved runtime acquisition verify hashes, --version and
device listing without a model. Vulkan must identify RX 6800 XT; subsequent loading
must show actual layer offload and monitored device allocation, not just detection.
Choose exactly one backend before freezing execution: Vulkan with two inference/
prompt threads, or CPU with eight threads and zero GPU layers. CPU memory fit is
plausible; latency is unknown and judged against the same criteria. No automatic
backend switch, rebuild or second inference attempt after a startup/run failure.

Planning estimates: GPU 9–12 GiB dedicated allocation, CPU 10–14 GiB host working
set at 2,048 context/one slot; not measurements. Proposed new-run guards (not changes
to closed-run limits): owned RSS/working set <=16 GiB, available host RAM >=20 GiB
before starting and >=4 GiB during execution; Vulkan free device budget >=14 GiB
before loading, owned dedicated allocation <=12 GiB and >=2 GiB device headroom.
Stop if device usage cannot be measured. Scratch <=25 GiB with >=30 GiB free on
the selected drive before setup and >=5 GiB free throughout. New acquisition cap
10 GB, one model file and the selected runtime only; no full-weight conversion,
SDK/driver/compiler installation or source rebuild. Existing OS PowerShell transports
requests; unchanged Python validation can run offline in the Codespace on saved
responses, avoiding a Python installation on the desktop.

### Frozen protocol, criteria and stop rules

Freeze the input bytes, reviewed expectations, case order and all configuration
hashes before the first model request. No held-out file is opened for diagnosis,
transferred to the desktop or run; preserve the 23+32 frozen cases (55) untouched.
Use separate new calibration files/results. Proposed total **34 requests**:

1. Six previously observed calibration cases once each, temperature .7/seed 42:
   reuse for regression diagnosis only, not unseen evaluation.
2. Twenty-four fresh synthetic cases: four per DE/FR/IT/EN (ordinary paraphrase,
   non-bicycle subject/optional omissions, negation/exclusion, protected name/amount),
   plus two mixed supported requests, two understandable short subjects with
   uncertain language, two genuinely ambiguous meanings/numbers, and two unsupported
   language/dialect controls. Expectations distinguish unknown language from uncertain
   meaning and unsupported capability; language never sets country. Explain-language
   preference/correction is an application responsibility, not invented by this schema.
3. Four preselected repeats, one clear case per language, unchanged seed/settings;
   deliberate variability probes are not failure retries.

Unchanged system/user prompt contract, schema, aliases, validator and semantic
scorer. Non-thinking hard template switch verified before requests; temperature
.7/top-p .8/top-k 20/min-p 0, seed 42, context 2,048, output maximum 384, F16 KV,
batch/ubatch 64, one slot, no tools/history/speculation/context shifting or prompt
cache. Only candidate, platform/backend and (CPU alternative) thread count change.
Windows loopback HTTP transport is an operational adaptation; freeze it separately,
verify UTF-8/Unicode preservation against saved requests, and check it offline with
the existing raw-response fixtures. No validator or quote/label relaxation.

All 30 unique cases and four repeats must pass strict validation plus independently
checked status/language/meaning/constraint expectations. Specifically: all 25 clear/
understandable unique requests must be understood (zero unnecessary clarification/
unsupported); both truly ambiguous cases must clarify the recorded uncertainty
without guessed values; all three unsupported cases must retain correct language/
uncertainty handling, without invented conditions hidden by the unsupported scorer.
Zero changed/ungrounded quotes, lost/reversed negation, changed protected values or
invented goals/constraints. Report normalized-label contract mismatches separately
from underlying meaning errors. Any semantic/grounding/label failure fails calibration;
save it and continue only the remaining preplanned cases within the same budget.

Proposed single-user latency gates: readiness <=90s; warm end-to-end request median
<=10s, nearest-rank p95 <=20s, every request <=45s. Time through receipt of complete
JSON; no caching. First request is reported separately from warm requests, with
prompt/generation timings, token counts, finish reasons and cache usage. Available
measurements and missing measurements are explicit; hardware/build/backend changes
prevent direct speed attribution to the candidate. These are proposed screening
targets, not existing requirements or a production SLO.

Total desktop window <=120 minutes from first approved setup execution: setup <=60,
loading/34 requests <=30, preservation/closeout <=30. Stop on setup/readiness,
transport, timeout, non-stop/truncated output or resource failure; no automatic retry,
tuning, driver update or rental fallback. Save each raw request/response and incremental
resource/deadline/exit records immediately; run unchanged validation/scoring offline
after transfer and save each assessment when computed. Requests complete only the
fixed plan; no success is claimed before assessment and human review. Use loopback only with
offline local model path, agent/Web UI/MCP disabled and scoped outbound prevention;
verify containment rather than assuming absence of telemetry. No remote-access setup
or personal/application data. Stop only the owned server; preserve artifacts and
copy small hashed results back to workspace storage. Confirm independent preservation.

Rental pricing must be quoted before approval: [EC2 bills applicable Linux use per
second, minimum 60s](https://aws.amazon.com/ec2/pricing/on-demand/), while [EBS storage
remains billed until released](https://aws.amazon.com/ebs/pricing/). The $10 envelope
requires scheduled stop, bounded storage retention and owned-resource closeout after
verified export; a billing alert alone is not a hard cap. This document authorizes
no deletion/provisioning. Local electricity, operator/reviewer labour and continued
retention beyond the proposed day are outside the infrastructure envelope and need
explicit owner treatment; no account allowances or actual costs are assumed.

### Review responsibilities and limits

Before freezing new expectations, seek one competent written-language reviewer per
DE/FR/IT/EN; one person may cover several languages only with demonstrated competence.
Plan roughly 1–2 hours per language across pre-run expectation review and post-run
output assessment (4–8 person-hours total), plus dispute adjudication. These are
effort estimates, not available reviewers or a paid-review quote. Reviewers first
agree gold meaning/status/constraints/protected values and ambiguous outcomes; after
execution independently judge raw outputs without model identity where practical.
Escalate disagreements to a second competent reviewer; unresolved meaning prevents
an acceptance claim. AI can draft cases, point out discrepancies and run deterministic
quote/schema checks, but is not independent qualified linguistic review. Without
reviewers, only exploratory technical calibration can be reported, even if automatic
checks pass. No reliable multilingual-support or population-accuracy claim follows.

This experiment evaluates request interpretation only. Faithful evidence rendering
needs separate TL-03 responsibility: qualified source-language review of original
conditions/exclusions and target-language review of derived explanations, numbers,
units, negation and provenance, including a non-template narrative. Arrange four-
language source/target coverage and independent adjudication; do not presume one
reviewer understands all source languages. No evidence translation inference is
included or authorized here. Existing evidence freshness/qualification and atomic
persistence still apply; interpretation success cannot accept rendering or DESIGN.

Owner decisions needed: desktop Vulkan or CPU route after local preflight; the
120-minute/new-resource/download budget and screening latency gates; reviewer
identity/time/funding and whether an AI-only exploratory run is acceptable if they
are unavailable. Recommended paid infrastructure spending cap $0 on the desktop;
rental would require a separate <=$10 quote/control/region approval. Production
interpreter/hosting and final DESIGN acceptance remain separate pending decisions.
No cases, runtime adapter or executable plan is created/run by this proposal.

## Windows candidate authorization and bundle — prepared 2026-10-13

The owner approved one exploratory Qwen3-8B Q8_0 Windows desktop experiment,
pinned Vulkan runtime only, conditional on local preflight and exact acquisition
sizes within 10 GB. No paid infrastructure/reviewers or additional prerequisite
installation, remote access, firewall opening, driver update or CPU fallback.
The [version 1.0.0 bundle](windows_qwen3_8b_v1/README.md) freezes 24 new AI-assisted
expectations before inference and copies the unchanged pure contract. Six known
cases run first; any semantic failure stops before new inputs. Quote/schema/label
failures also block the strict gate without treating label-only mismatch as proof
of different meaning. No tuning/retry. The paused server remains monitored within
its original deadlines during manual transfer/offline assessment. Explicit cleanup
preserves artifacts/results/partial downloads/markers; it stops only the owned PID.

Publisher metadata checked 2026-10-13: model 8,709,518,112 bytes and Vulkan runtime
33,337,769 bytes, combined 8,742,855,881. This plus reserved bundle/metadata fits
10,000,000,000 bytes; no model/runtime payload acquired in the Codespace. Ten offline
harness checks passed separately from Windows compatibility/model tests unexecuted
at bundle preparation.
All 55 held-out cases and earlier evidence remain intact. Budget starts at local
Setup execution, not repository bundle preparation or read-only preflight; no such
window/run had started at that preparation record. Original proposal remains historical; this authorization
supersedes its backend/review choices and adds the strict known-case stop gate.
No production integration, DESIGN acceptance or linguistic-validation claim follows.

### Windows execution closeout — reviewed 2026-10-13

[Detailed review](windows_results_2026_10_13/REVIEW.md) preserves the uploaded
originals and links raw responses, recorded/reassessed gates, resources and exits.
The unchanged assessor reproduces 2/6 strict passes (both English); DE/FR/IT
canonical subject-label mismatches are distinct from failure of the Spanish
unsupported-language negative control. It checks limitation/rephrasing behaviour,
not Spanish interpretation/translation; supported scope stays EN/DE/FR/IT only.
Exact quote grounding passes all six. The additional 28
requests did not run and the 55 held-out cases remain unexposed. Positive owned
GPU allocation was measured, but full offload/CPU speedup were not established.
The recorded shutdown, watchdog completion and cleanup are consistent and retain
artifacts; this Codespace cannot verify live Windows processes. The tested
configuration is not accepted for production. Proposed follow-up:
review unsupported-language handling; review DE/FR/IT canonical-label mismatches separately. The owner
clarification adds no language requirement or new inference/experiment authorization;
frozen inputs, original results and failed gate are intact. Direction A and pending
DESIGN/linguistic review remain unchanged.

A [separate v2 proposal](windows_qwen3_8b_followup_v2/PROPOSAL.md) now records the
exact draft prompt delta, fresh cases and maximum 18-request/30-minute comparison.
Pinned-source inspection explains the verbosity-3 gap for loader INFO; verbosity 4
is proposed for both arms, with actual offload confirmation still required. Nothing
has been executed or accepted; v1 remains closed and the 55 held-out cases untouched.

The owner authorized [v2 bundle preparation/offline checks](windows_qwen3_8b_followup_v2/BUNDLE.md)
on 2026-10-14. The separate frozen bundle implements the reviewed maximum 18-request/
30-minute order, manual assessment gates and logging prerequisites. Fourteen
synthetic checks pass; Windows checks, actual capacity/offload and execution approval
remain pending. No inference or acquisition occurred; v1 and held-out inputs are preserved.

[V2 original-attempt closeout](windows_v2_results_2026_10_14/REVIEW.md): checksum-
verified Windows evidence records a Groups parser failure and later possible
shutdown race, with zero evaluation requests. Logged 37/37 layer offload is separate
from unmeasured acceleration/language capability. [Harness 2.0.1](windows_qwen3_8b_followup_v2_0_1/BUNDLE.md)
is a separate offline-only repair with unchanged evaluation contract; old approvals,
markers, deadlines and results remain preserved. No further inference is authorized.

## Archived design experiment assessment — 2026-10-11

Relocated from `docs/ARCHITECTURE.md` without changing historical prose;
relative links are rebased. Dates, proposals, reproduction commands and
authorization statements below are historical, not permission to execute.
The configuration is closed; see [final findings](portable_2026_10_11/REPRODUCE.md#experiment-closed--verified-return).
Original section SHA-256: `f2af8b34c1f28a6b3633e8b41ed880459ba5465103bfce26305573b0d12c2363`.

### Multilingual feasibility experiment — 2026-10-10

Owner-authorized isolated DESIGN spike in
[experiments/uc001_multilingual](..), using existing
Python 3.12.11 stdlib only; no application imports/dependency changes/network/model.
Calibration tests were written first (initial missing-module failure), then six
groups passed. Parser frozen before held-out fixture creation, SHA-256
`1c905509724e9bcd09ba1574ce361582323bff3f65d7bac76de5a638b92eb04e`;
no tuning after evaluation. Same agent authored parser, examples and semantic
oracles: this is a development hold-out, not blind/independent linguistic validation.

| Executed check | Actual result / limit |
|---|---|
| 23 request cases (four each DE/FR/IT/EN, plus mixed/short/unsupported/novel/name cases) | 8 handled against the oracle; 13 requested clarification; 2 unsupported. Zero accepted incorrect interpretations in this sample; no population accuracy claim. |
| Ordinary variants | DE/FR each handled 1 of 4; IT/EN each 2 of 4. “Mein Velo braucht eine Reparatur …”, “remis en état”, “cycle fixed” and other valid paraphrases abstained. Names/place suffixes and a novel kettle also caused clarification: coverage gaps, not invalid submissions. |
| Negation/ambiguity | Ambiguous `1,200 CHF` correctly prompted clarification. DE-4's negated “without” and FR-3/IT-3/EN-3's negated repair had wrong partial hints despite abstention; never use these hints to qualify or render a result. |
| Mixed and short | MIX-1 parsed the French constraint in English context with browser preference; MIX-2 abstained. Short “Velo” used the explicit FR choice. Unsupported ES/dialect outcomes rely on configured lexical markers, not general detection. |
| Eight synthetic evidence statements | Four prepared labour-price/parts-exclusion patterns extracted new amounts/currencies and rendered into each target (16 actual render executions). Four narrative exclusions/non-electric applicability clauses were unsupported; no general translation demonstrated. |

Reproduce: `.venv/bin/python -B -m unittest discover -s experiments/uc001_multilingual -p test_calibration.py -v`,
then `.venv/bin/python -B experiments/uc001_multilingual/evaluate.py`.
[Machine results](../results.json) record inputs, actual
outputs, mismatches and hashes; [held-out fixture](../heldout.json)
supplies scoring oracles only. The parser/renderer never reads expected fields;
the harness compares actually executed outputs. Templates/oracles are AI-authored,
not reviewed translations. Outbound sockets were blocked during evaluation; zero
attempts observed. No runtime retrieval, actual evidence quality/freshness,
persistence/recovery/ownership, API/UI or production dataset was tested.

Recommendation: retain reviewed claim templates and deterministic protected-value
checks as components, **evaluate a local multilingual semantic interpreter** rather
than extend aliases as the sole mechanism. This conservative prototype cannot yet
satisfy ordinary-input/narrative coverage across the approved scope; abstention
prevents unsafe success but excessive clarification is not demonstrated adequacy.
No scope adjustment is approved or recommended as a shortcut.

No extra dependency was needed here. Checked installed modules: pytest available;
Lingua, fastText, Transformers, PyTorch, SentenceTransformers and spaCy absent.
One next local-evaluation route would require compatible `transformers`/`torch`
packages plus a licensed multilingual model artifact and local resource evaluation;
none is selected/downloaded/installed. Present exact package/model/resource requirements
for authorization before installation. Qualified source/target review capacity
also remains unconfirmed; AI-authored tests cannot establish linguistic support.

### Local multilingual interpreter assessment — proposed 2026-10-10

Initially read-only inspection/research; download/build/evaluation was subsequently
authorized on 2026-10-10 within the bounded experiment below. Existing requirements,
O-1/O-2 and final DESIGN/ADR status are unchanged. This is an experimental proposal,
not a production model decision; the interrupted run is recorded below.

Observed Codespace: Debian 12 x86-64, glibc 2.36; 2 logical Xeon Platinum 8370C
CPUs (AVX2/AVX-512 exposed), 7.76 GiB RAM total / 3.84 GiB available, no swap.
Affinity/cpuset allows two CPUs; visible cgroup limits are `max`, not additional
capacity. Free space: workspace 24.66 GiB; `/tmp` 40.05 GiB (not assumed additive).
No NVIDIA utility/devices or DRI access visible; GPU is unavailable to this assessment.
These are remote Linux resources, **not the owner's Windows host**, which was not
inspected. Availability is a snapshot, not reserved RAM. GCC/G++ 12.2, Make 4.3,
Python 3.12.11, tar/timeout/strace exist; CMake and llama binaries do not.

Two candidates, both using [llama.cpp v0.6.0](https://github.com/ggml-org/llama.cpp/releases/tag/v0.6.0)
(MIT, native CPU/GPU backends; neither Transformers nor PyTorch required):

| Model/artifact and provenance | Language/license evidence | Fit estimate, untested |
|---|---|---|
| [Official Qwen3-1.7B GGUF](https://huggingface.co/Qwen/Qwen3-1.7B-GGUF/tree/90862c4b9d2787eaed51d12237eafdfe7c5f6077), `Qwen3-1.7B-Q8_0.gguf` | Apache-2.0, ungated publisher repository. [Qwen's language list](https://qwenlm.github.io/blog/qwen3/) explicitly includes DE/FR/IT/EN. This documents intended multilingual capability, not accurate project interpretation. | 1,834,426,016 bytes (1.83 GB / 1.71 GiB); estimate 2.4–3.2 GiB process RAM at 2,048 context/one slot/small batch. Best initial fit; small-model semantic omissions remain a risk. |
| [Official Gemma 3 4B QAT GGUF](https://huggingface.co/google/gemma-3-4b-it-qat-q4_0-gguf), `gemma-3-4b-it-q4_0.gguf`, revision `15f73f5eee9c28f53afefef5723e29680c2fc78a` | [Google model card](https://ai.google.dev/gemma/docs/core/model_card_3) describes 140+ languages; target-language interpretation is an untested expectation, without four-language evidence here. [Gemma terms](https://ai.google.dev/gemma/terms), gated access/contact consent; no entitlement assumed. | 3,155,051,328 bytes (3.16 GB / 2.94 GiB), text weights only; omit the 851 MB image projector. Estimate 4–5 GiB process RAM with short context. Tight against current free RAM/no swap; not the first experiment. |

CPU inference is documented for both; GPU acceleration is optional and inaccessible
here. RAM estimates include weights, cache and buffers, not measured peaks. Qwen's
[configuration](https://huggingface.co/Qwen/Qwen3-1.7B/blob/main/config.json) implies
about 224 MiB F16 KV cache at 2,048 tokens (28 layers, 8 KV heads, head dimension 128);
remaining buffers depend on the build. No tokens/second or latency is established.

Bounded experiment proposed here, subsequently authorized on 2026-10-10:

1. Use Qwen revision above; verify model SHA-256
   `061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a`.
   Build only the CPU `llama-server` target from commit
   `d81235049384534c167caea52b85a694f6103d14` (v0.6.0), using existing GCC/Make.
   Obtain temporary [Kitware CMake 3.31.6](https://github.com/Kitware/CMake/releases/tag/v3.31.6),
   `cmake-3.31.6-linux-x86_64.tar.gz` (55,010,959 bytes), checksum
   `5a1133ff103c71eb5120e2cc3de922733e7d8a26a98ae716397e8676adb367bf`.
   [CPU build instructions](https://github.com/ggml-org/llama.cpp/blob/d81235049384534c167caea52b85a694f6103d14/docs/build.md)
   support CMake/Make; a current Ubuntu binary's glibc compatibility is unverified.
   Release/static CPU build, GPU/BLAS, OpenSSL, subprocess tools, LLGuidance,
   app/examples/tests, UI build and prebuilt UI fetch disabled; no Rust/Node/pip/
   system-package install. Verify temporary CMake/build compatibility before acquiring
   weights; stop and report any extra dependency.
2. Run one slot, two CPU threads, 2,048 context, F16 cache, batch/ubatch 64,
   384 output tokens, hard non-thinking chat-template switch, schema-constrained
   JSON. Use documented non-thinking sampling (temperature .7, top-p .8, top-k 20,
   min-p 0; fixed seed 42), no history/tools or automatic retry. These are proposed
   experiment settings, not permanent product policies.
3. Model output is limited to subject, intended action, explicit goals/constraints,
   language/uncertainty and supporting original Unicode text spans; unresolved
   meaning stays explicit. No search-country inference, defaults for omitted goals,
   qualification, evidence judgement, freshness, financial calculation or saving.
   Application-side schema/span/protected-literal checks reject malformed,
   truncated or ungrounded output; only complete accepted interpretations can
   proceed. Span validity alone cannot prove correct negation/scope. Partial/rejected
   fields never drive qualification, even if some fields appear plausible. Enforce
   the four-standard-language scope outside the model, even if it understands more.
4. Preserve the frozen parser/hash and 23-case evaluation. Before prompt/model
   tuning, freeze a separate 32-case hold-out: six per standard language covering
   ordinary paraphrases, non-bicycle subjects, negation/exclusions and budgets,
   plus eight mixed/short/ambiguous/unsupported/dialect controls. Supply gold
   meaning/spans separately from runtime input; no fixture-aware lookup.
   Run both mechanisms on the new cases; compare shared semantics on old cases,
   with new span checks scored separately where the parser lacks them.
5. Report each case and language: correct complete interpretation, clarification/
   abstention, unsupported, incorrect meaning, invalid output and timeout separately.
   Expose omitted/reversed negation, exclusions, amounts/units/names as individual
   errors, including wrong partial hints; never hide them in an aggregate score.
   Record cold-load, prompt/generation and warm wall latency separately (median,
   p95/max), peak RSS and available RAM. Repeat eight preselected cases twice to
   assess variability with fixed/reported seeds. AI-authored tests are exploratory;
   source/target review capacity is unconfirmed. No model fine-tuning in this pilot.
6. Use one private scratch tree under `/tmp` for tools/source/model/cache; no
   app configuration/dependency changes. Downloads contact publishers only for
   artifacts, without user/application text. Inference uses local model path,
   `--offline`, loopback only/no forwarding, Web UI/agent/MCP disabled and synthetic
   inputs only. [Server documentation](https://github.com/ggml-org/llama.cpp/blob/d81235049384534c167caea52b85a694f6103d14/tools/server/README.md)
   documents local/offline and constrained-output options; no required external
   inference/telemetry is documented, but absence of telemetry is not independently
   audited. Trace network syscalls with existing strace, reject non-loopback attempts;
   distinguish instrumented timings from uninstrumented timings. No cloud fallback.
7. Proposed budget: about 2 GB downloads; reserve 6 GiB scratch space. Recheck
   RAM before starting; abort above 3.25 GiB process RSS or below 0.5 GiB available.
   Bound build to 30 minutes, inference to 60 minutes, each request to 45 seconds;
   report aborted/unexecuted cases without silently expanding resources/context.
   Plan 1–2 active hours including acquisition/build. Published [Codespaces rates](https://docs.github.com/en/billing/concepts/product-billing/github-codespaces)
   imply USD 0.18–0.36 compute at two cores if billable; storage is USD 0.07/GB-month.
   No account quota/entitlement inspected. Stop owned processes and remove only the
   created scratch tree after retaining synthetic outputs, pins, measurements and
   limitations in the existing experiment area. Preserve all frozen earlier artifacts.

Narrative evidence remains a **separate capability**: source-language review,
typed claim extraction and reviewed claim-specific target-language paraphrases with
original conditions/exclusions/provenance. The four unprepared evidence cases stay
unsupported in the existing renderer. Request interpretation success authorizes
neither automatic evidence translation nor dropping essential conditions.
A later local narrative-translation experiment needs separate paired-source/target
fidelity evaluation and qualified review; unchanged source review dates and
application-controlled evidence checks still apply. This pilot makes no translation,
language-support or production-readiness claim.

### Local interpreter experiment — interrupted; reviewed 2026-10-11

Retained [pins, harness and reproduction instructions](REPRODUCE.md),
[preparation measurements](preparation.json)
and [actual startup results](results.json).
Publisher model/CMake checksums matched; the pinned CPU build succeeded with one
compile job. Downloads totalled 1.93 GB; build took 14.17 minutes, peaking at
646 MiB owned RSS with at least 3.23 GiB available RAM during sampled monitoring.

**No model calibration or evaluation case completed.** The first client called
before model readiness (HTTP 503); the next startup encountered the owned stale
Unix socket. Readiness polling and a stale-socket safeguard were added without
prompt/scorer tuning; the latter correction was not executed. At resumption the
recorded deadlines had expired, the exact temporary tree was absent and no owned
model process remained. Its removal time/cause and peak temporary disk usage are
unverified; no second download or deadline renewal was performed.

[Closeout](closeout.json) distinguishes
unexecuted per-language model measures from the frozen-parser baseline and six
passing harness checks. Semantic correctness, abstention, unsupported handling,
case timeouts, latency and loaded-model peak RAM remain **unmeasured**. Startup
traces show no Internet socket activity in those owned process trees only; they
establish neither offline behaviour during inference nor general telemetry absence.
The additional 32-case corpus remains model-unseen; its AI-authored expectations
are not independent linguistic validation. No model/prompt tuning occurred.

The unchanged parser was run on the 32 additional cases at closeout: one complete
match, 29 abstentions and two unsupported inputs; raw partial fields are retained
and never accepted. These are parser results, not model capability or an all-language
benchmark. The earlier 23-case parser evaluation remains unchanged.

Recommendation: retain this as acquisition/build evidence and seek a separately
bounded continuation to evaluate the same pinned interpreter before any design
choice. It provides no basis for adopting or rejecting Qwen's semantics, reducing
accepted multilingual scope, or claiming narrative-evidence translation fidelity.
DESIGN/ADR-003 acceptance remains pending; application behaviour/dependencies and
the mandatory research/UC-003 scope are unchanged.

The owner authorized a separate artifact-reusing restart on 2026-10-11 after
read-only recovery of the interrupted renewed attempt. Its [run record](restart_2026_10_11/REPRODUCE.md)
preserves the earlier deadlines/markers and uses a fresh two-hour execution window,
at most 60 minutes including loading/inference, unchanged pins/cases/prompts/scoring,
and the same resource guards. The cumulative 2.2 GB download cap spans the renewed
attempt and restart. Workspace artifacts are retained; a short Git-ignored alias
fixes the Unix socket path length. The [actual run](restart_2026_10_11/results.json)
stopped at its separate smoke gate: build/version verification and model checksum
passed; readiness took 14.85s. “Repair my kettle.” produced unsupported status
and two quotes with changed case, failing original-text grounding checks after
44.70s. No calibration, frozen evaluation or repeat ran; this single synthetic
response provides no four-language benchmark or narrative-translation evidence.
Owned inference ended normally; the orchestration exit was 1. Sampled/per-case
peak owned RSS was about 2.08 GiB and retained scratch about 2.11 GiB; cumulative
downloads were 2,020,223,394 bytes. A post-build bookkeeping collision was fixed
within the same restart deadline after preserving the failure records; no rebuild,
prompt/scorer change or automatic inference retry occurred. Seven operational
checks and a targeted bookkeeping regression check are separate from model results.
Final DESIGN/ADR-003 acceptance remains pending; further execution needs a new
explicit decision rather than using the unused time to retry this failed gate.

The subsequent [read-only smoke diagnosis](restart_2026_10_11/REPRODUCE.md#smoke-diagnosis--read-only-2026-10-11)
found case-normalized quotes and unsupported status for recognized English, with
no evidence of truncation or a template/non-thinking configuration error. Cause
remains uncertain; a separately authorized, 12-request temperature-only calibration
is proposed. No new model exposure occurred; frozen evaluation and strict checks
remain intact. This is a diagnostic proposal, not a DESIGN acceptance or model choice.

The owner subsequently approved [calibration B](calibration_B_2026_10_11/REPRODUCE.md)
on 2026-10-11. Its six expectations/twelve requests were frozen, but execution
stopped at the preflight resource guard before loading. Subsequent available RAM
was 3.66 GiB against the unchanged 3.75 GiB preflight minimum; exact guard-time
values were not captured. No case ran, so no temperature or semantic conclusion
is supported. The configuration is stopped pending review, with no retry/tuning;
artifacts and heldout evaluation are preserved. Final DESIGN acceptance is pending.
Subsequent operational memory diagnosis distinguishes host/VM MemAvailable from
visible cgroup accounting; no finite visible quota or OOM event was found, while
hidden ancestor limits remain unverified. Keep the conservative cap+reserve
preflight unchanged; one smoke peak is not a workload maximum. The calibration
record documents exact-sample logging for future authorized runs and recommends
more environmental headroom, without a resource upgrade or architecture decision.

Experiment closed on 2026-10-11 after the owner-authorized 4-core/16 GB portable
rebuild and unchanged paired calibration. Build/compatibility/readiness passed;
actual model results were **0/12 strict passes, including 0/6 at temperature zero**.
The tested pinned **Qwen3-1.7B Q8_0 configuration is not accepted for production**.
[Findings and closeout](portable_2026_10_11/REPRODUCE.md#experiment-closed--verified-return)
link the [paired evidence](portable_2026_10_11/CASE_REPORT.md)
and [raw results](portable_2026_10_11/results.json).

Keep the failure dimensions distinct: semantic errors include incorrect supported-
language classification, invented/contradictory constraints and wrong language/
missing uncertainty; quote-grounding failures include changed case and empty
supporting quotes; normalized-label mismatches include water_kettle/bouilloire/
répare against the frozen canonical labels. The latter alone do not establish a
different physical object/action. Categories overlap; not every failed strict
result proves incorrect underlying meaning. No validator, aliases, scoring or
approved multilingual requirement was relaxed. The six synthetic cases are
calibration data; the 55 frozen cases remain unexposed to the model. This finding
is scoped to the tested pins/build/prompt/schema/settings and does not reject all
local models or other Qwen configurations. Original resources were restored and
workspace hashes verified; artifacts/results remain preserved. DESIGN/ADR-003
acceptance stays pending; no production integration or further experiment follows.

