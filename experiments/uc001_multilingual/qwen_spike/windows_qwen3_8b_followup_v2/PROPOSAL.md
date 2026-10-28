# Windows Qwen3-8B follow-up v2 — proposed 2026-10-13

**For owner review only; not approved, frozen for execution or run.** Review
unsupported-language handling and, separately, DE/FR/IT canonical-label output.
Supported scope remains DE/FR/IT/EN. Spanish is an unsupported-language negative
control for limitation/rephrasing behaviour, not interpretation/translation support.
The [v1 closeout](../windows_results_2026_10_13/REVIEW.md), original results and
failed gate remain intact. UC-001 increment 1 remains Phase 2 DESIGN/in-progress.

## Existing evidence and bounded hypotheses

| Responsibility | Observed evidence | Hypothesis or remaining uncertainty |
|---|---|---|
| Normalization versus grounding | V1 explicitly requests canonical English subjects and original verbatim quotes. C3/C4/C5 instead return `Wasserkocher`/`bouilloire`/`bollitore` as values, with exact original quotes. Repair and the German no-replacement constraint are preserved; C1/C2 pass. The schema permits arbitrary subject strings; the alias map lacks those kettle forms. | The model may conflate normalized values with source text or fail to follow the value instruction. The outputs do not establish the cause or wrong underlying object. Clearer field roles may help; no aliases or kettle-specific fixes are proposed. |
| Unsupported-language handling | C6 expects `unsupported`, `language:null`, nonempty uncertainty. It returns `understood/fr`, empty uncertainty and `hervidor`. The schema permits null, but does not enforce status/language relationships or a nonempty uncertainty array. The explicit assessor checks do enforce the expectations. | Familiar-word recognition or an inclination to select an enum language may contribute. Neither is established by one output. JSON validity and grounded quotes cannot make the wrong classification pass. |
| Runtime evidence | Both server streams lack an offloaded-layer count; stdout is empty. CLI requests Vulkan0/99 layers, and 439 samples report positive owned GPU allocation. Startup logs explicitly record verbosity 3. | Full offload remains unconfirmed. The pinned source explains why loader INFO messages can be suppressed at 3; it does not establish actual Windows layer placement or acceleration. |

Evidence: [six recorded assessments](../windows_results_2026_10_13/review/evidence/assessment.json),
[raw responses](../windows_results_2026_10_13/review/evidence/responses/),
[sent requests](../windows_results_2026_10_13/review/evidence/requests/),
[schema/prompt/scoring](../windows_qwen3_8b_v1/contract.py) and
[explicit assessor](../windows_qwen3_8b_v1/assess.py). All six responses finish with
`stop`; logs record no truncation. This is no evidence of a context/output-limit
cause. No model was run or retrospectively rescored while preparing this proposal.

## One proposed prompt revision

[prompt-v2.txt](prompt-v2.txt) is the complete proposed system prompt;
[prompt-v2.diff](prompt-v2.diff) is its exact delta from the actual v1 request.
All original v1 prompt lines are retained. The only additions are:

1. Distinguish original input-language classification from the language of English
   normalized values. Null is permitted for unsupported or unresolved input language.
2. Spell out the existing unsupported/null/nonempty-uncertainty route, explaining
   the limitation and requesting supported-language rephrasing. Recognizing words
   is not permission to report understood support.
3. Keep genuinely uncertain language separate from uncertain meaning: a recognizable
   subject can be understood with language null; unresolved meaning needs clarification.
4. Allow null/empty-quote subject/action fields when meaning is unreliable, preserving
   safely established partial meaning rather than inventing required values.
5. Explicitly distinguish English normalized labels from verbatim evidence quotes;
   never translate/case-fold/correct quotes or rename protected values.

No model, sampling, schema, aliases, validation or scoring change is proposed.
These instructions clarify the current route; they are not a Spanish requirement
or a new production mechanism. Prompt wording cannot guarantee correct behaviour.
The larger prompt must pass the actual template/token-capacity check before every
request; do not shorten it, increase context/output limits or silently drop rules.

## Exact runtime evidence required in a future authorized run

The surviving source is pinned to `d81235049384534c167caea52b85a694f6103d14`, matching
the recorded Windows b11429 build. Offline source inspection found:

- [llama-model.cpp, lines 1921–1933](https://github.com/ggml-org/llama.cpp/blob/d81235049384534c167caea52b85a694f6103d14/src/llama-model.cpp#L1921): loader reports offloaded layers and model-buffer sizes through INFO logging.
- [log.cpp, lines 532–549](https://github.com/ggml-org/llama.cpp/blob/d81235049384534c167caea52b85a694f6103d14/common/log.cpp#L532): that callback maps library INFO to trace; [log.h](https://github.com/ggml-org/llama.cpp/blob/d81235049384534c167caea52b85a694f6103d14/common/log.h#L24) defines trace as 4.
- [common.cpp, line 397](https://github.com/ggml-org/llama.cpp/blob/d81235049384534c167caea52b85a694f6103d14/common/common.cpp#L397) installs the callback; [arg.cpp, lines 3948–3963](https://github.com/ggml-org/llama.cpp/blob/d81235049384534c167caea52b85a694f6103d14/common/arg.cpp#L3948) implements the numeric verbosity flag.

Apply the same operational-only logging change to both prompt arms, before the
single server start: append `--log-verbosity 4`. Keep incremental stdout/stderr
capture from process creation through confirmed exit, with final stream flushing;
do not switch log format or overwrite v1 logs. Record full argv, executable/model
hashes, Windows/driver/GPU identification, actual verbosity and timestamps.

Before generation, require a complete loader line `offloaded N/N layers to GPU`
with equal positive counts, backend/device identification as Vulkan0/RX 6800 XT,
model-buffer placement/sizes and available context/KV buffer records. Save the raw
lines with PID/start-time ownership and positive WDDM allocation samples. Record
any CPU host buffers without treating them alone as CPU-only inference. If layer
confirmation is absent or partial within the 90-second startup allowance, stop
before inference; do not restart at another verbosity or invent offload evidence.

Continue saving per-request raw JSON, usage/finish reasons, prompt/prediction
timings, cache counters, graph reuse and resource samples. Layer confirmation is
an operational prerequisite, separate from semantic/label/quote assessments; even
an N/N line and allocation do not establish every operation runs on GPU or a speedup
over CPU. Extra logging can affect latency and applies equally to both arms.

## One proposed small experiment

**18 generation requests maximum, one server start, 30 minutes total** from first
local execution, including preflight/hash checking, loading, inference, offline
assessment/transfer and owned shutdown. Readiness: 90 seconds; each generation:
45 seconds. No warmup/smoke requests outside the count, retries, tuning or restarts.
The 18 requests require at most 810 seconds of request allowances plus startup;
the remaining wall budget covers checks, manual transfer/assessment and closeout.

Reuse the installed Windows model/runtime in
`C:\ResolenaExperiments\qwen3-8b-v1`; verify their pinned hashes locally and check
that no continuation/server is active. Stop on a mismatch or occupied port rather
than launching duplicates or stopping unrelated processes. New logs/receipts go
under a separate `C:\ResolenaExperiments\qwen3-8b-followup-v2` folder; no copy of the
large model, downloads, installations, rebuilds, driver changes, external inference,
firewall opening, CPU fallback or paid infrastructure.

Unchanged settings: Qwen3-8B Q8_0 and llama.cpp b11429/Vulkan0, two inference/prompt
threads, temperature 0.7, top-p 0.8, top-k 20, min-p 0, seed 42, context 2,048,
output 384, batch/ubatch 64, F16 KV, one slot, hard non-thinking, cache disabled and
loopback `127.0.0.1:49187`. [draft-plan.json](draft-plan.json) records the exact
proposed cases/order, pins, prompt/schema/scorer hashes and unchanged guard values.
No live desktop resource or current artifact-availability claim is made here.

| Resource | Unchanged preflight / runtime guard |
|---|---|
| RAM / server RSS | Available RAM at least 20 GiB before loading; at least 4 GiB during execution; owned server RSS at most 16 GiB. |
| Dedicated GPU memory | At least 14 GiB headroom before loading; at least 2 GiB during execution; owned allocation at most 12 GiB. Same DXGI/WDDM measurement limitations. |
| Storage | At least 30 GiB target-drive space before execution and 5 GiB thereafter; cumulative scratch at most 25 GiB, counting reused artifact folder plus new run folder. |

Preserve original deadlines/markers and use new, separately recorded deadlines.
Keep the independent watchdog and incremental measured-value/threshold/time/exit
records. Preserve artifacts and all partial results through closeout. The Codespace
cannot run commands on the desktop; a future approved bundle must retain manual
small-file transfer and offline assessment without exposing the model server.

Sequence:

1. Requests 1–6: v2 prompt on the unchanged six exposed calibration cases and
   expectations. Compare with preserved v1 responses as historical evidence,
   not a simultaneous control or unseen evaluation. All six must pass the unchanged
   strict semantic/status/normalization/quote/schema gate before any fresh requests.
2. Requests 7–18: six newly drafted examples, each once under v1 and once under v2,
   with three v1-first and three v2-first pairs. Same server, frozen schema/settings,
   independent two-message requests and cache disabled. The v1 arm supplies fresh
   baseline observations; it does not reopen or erase the failed v1 gate.

The fresh examples below test different objects/actions/constraints and ambiguous
language beyond the exposed kettle cases. They are AI-assisted draft expectations,
not qualified linguistic gold or evidence of general reliability. They are not
inserted into either prompt. Neither v1's untouched 24 new fixtures nor the original
55 held-out cases are opened or used for this plan.

| ID | Fresh draft input | Exact proposed expected interpretation |
|---|---|---|
| F1-DE | `Bitte repariere meinen Drucker, ohne ihn zu ersetzen.` | understood/de; printer/repair; goals []; no_replacement="true". |
| F2-FR | `Répare mon ordinateur ; garde au moins 256 GB de stockage.` | understood/fr; computer/repair; goals []; storage_min="256 GB". |
| F3-IT | `Riutilizza il mio contenitore, senza comprarne uno nuovo.` | understood/it; container/reuse; goals []; no_new_purchase="true". |
| F4-EN | `Repair my vacuum cleaner; budget 85 CHF, excluding delivery.` | understood/en; vacuum/repair; goals []; budget="85 CHF", cost_exclusion="delivery". |
| F5-ES | `Repara mi impresora.` | Unsupported-language negative control: unsupported/null, nonempty unresolved; no goals/constraints. Only safely grounded partial subject null/printer and action null/repair are permitted, following the existing assessor's partial-field mechanism. |
| F6-AMB | `Taxi` | Recognizable shared subject: understood/null; taxi; action null; no goals/constraints or unresolved meaning. Do not guess a supported language from one shared word. |

All populated quotes must be exact original substrings; null subject/action use
empty quotes. No alias additions, field-specific quote repair or normalization of
raw output is permitted. The French `256 GB` and English `85 CHF` must be preserved.
Unexpected source-language labels remain strict failures and are reported separately
from underlying meaning; new labels outside the assessor's known equivalents need
adjudication rather than an automatic claim that the object differs.

Stop immediately for startup, transport, timeout, resource, ownership, provenance,
non-stop finish or missing runtime evidence. At the six-case v2 gate, any strict
failure stops before fresh cases. During fresh pairs, record v1 model-content
failures as baseline data and still assess the planned counterpart; any v2 strict
failure stops further requests. This is diagnostic permission sought for the v1
comparator, not a relaxed acceptance gate. Never retry failed requests.

Success requires 6/6 known v2 and 6/6 fresh v2 strict passes, correct status/uncertainty
and expected meaning/constraints, exact grounding and runtime guards/evidence.
Report paired fresh v1/v2 outcomes without presuming improvement. Keep label,
semantic, quote and runtime dispositions separate. Report latency by arm with
sample counts, prompt/output tokens, cache/graph reuse and first versus warm timing;
use the existing 10s median/20s p95/45s maximum targets as exploratory targets only.
Prompt length, warm caches, logging and ordering limit latency attribution.

Passing would establish only adherence on these small AI-assisted fixtures. It
would not establish reliable multilingual support, unseen-set performance,
qualified language review, faithful rendering of source evidence or production
suitability. Known-case gains may reflect prompt adaptation to calibration data.
The revision could also translate quotes accidentally, increase latency or cause
unnecessary abstention; the unchanged gate must catch those regressions.
Failure closes this comparison pending review; it authorizes no tuning cycle.

## Approval and preparation needed

Approve the exact v2 prompt, six fresh expectations/order and one 18-request/
30-minute Windows comparison with the logging change and unchanged guards before
execution. No paid reviewer or hardware budget is requested; local electricity is
unpriced. No reviewer or fresh desktop availability is assumed.

After approval, prepare and review a separate execution bundle: freeze both prompt
arms, cases/expectations, complete requests/order/config and hashes before loading.
Reuse the byte-identical v1 schema/validator/canonicalizer/scoring functions. Its
CLI binds requests to v1's freeze, so a new experimental dispatcher must bind new
requests to the new freeze; do not alter v1 or falsely label a v2 request as v1.
Operational logging/receipt/dispatch changes must be recorded separately. No such
harness implementation or freeze is authorized by this proposal request.
