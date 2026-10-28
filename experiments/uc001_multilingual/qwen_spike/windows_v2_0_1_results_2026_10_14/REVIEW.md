# Windows Qwen3-8B v2.0.1 — reviewed closeout, 2026-10-14

**Strict gate failed; this configuration is not accepted for production.** Five
of six exposed calibration cases pass unchanged scoring. The Spanish unsupported-
language negative control fails status/language/uncertainty. Twelve further planned
generation requests did not run. General multilingual capability, faithful source-
evidence rendering and qualified linguistic validation remain unverified.
DE/FR/IT/EN requirements, direction A, privacy and DESIGN/in-progress are unchanged.

Run `b8591094-a685-48f4-88ef-3420d8b68d90`; harness freeze
`8ff486a621d90a3dfecff2b05287df25026a10cae8739e0b91530cce77f7088d`.
The archived approval, attempt markers and original 20:06:19.1580353–20:36:19.1580353
UTC window are preserved. Driver exited 1 at 508.023 seconds after the denied
cp06 receipt; no continuation or new receipt was created during this review.

## Verified model results

| Case / exact synthetic input | Status/language and meaning | Constraints | Exact quotes | Strict result |
|---|---|---|---|---|
| C1: `Repair my kettle.` | understood/en; kettle/repair, expected meaning | None invented | 2/2 | Pass |
| C2: `repair my kettle.` | understood/en; kettle/repair, expected meaning | None invented | 2/2 | Pass |
| C3: `Repariere meinen Wasserkocher, ohne ihn zu ersetzen.` | understood/de; normalized kettle/repair | no_replacement="true", grounded in `ohne ihn zu ersetzen` | 3/3 | Pass |
| C4: `Répare ma bouilloire.` | understood/fr; normalized kettle/repair | None invented | 2/2 | Pass |
| C5: `Ripara il mio bollitore.` | understood/it; normalized kettle/repair | None invented | 2/2 | Pass |
| C6: `Repara mi hervidor.` | **Unsupported-language negative control:** actual understood/en, unresolved=[]; expected unsupported/null with limitation/rephrasing uncertainty | None invented; grounded partial kettle/repair alone cannot make classification correct | 2/2 | Fail: status, language, missing_uncertainty |

All 13 populated quotes ground exactly; no canonical-label mismatch, quote error
or schema/validator failure occurs in this run. These are distinct from C6's
semantic classification failures. Compared with the earlier v1 outputs, DE/FR/IT
labels match the normalization contract on these known cases; exposed-case gains
do not establish generalization or a causal effect of prompt wording.

The unchanged [scorer](working/bundle/assess.py), [contract](working/bundle/contract.py)
and [dispatcher](working/bundle/dispatch.py) were copied separately and hash-verified.
[Offline reassessment](reassessment.json) matches every recorded evaluation. All
six request/response hashes, correct arm/order/freeze, cp06 checkpoint bytes and
the [denied receipt](evidence/inbox/cp06/receipt.json) bind correctly. Its assessment
hash matches the [recorded assessment](evidence/inbox/cp06/assessment.json), uploaded
assessment and return ZIP; creation precedes the unchanged deadline. No consumed
continuation marker exists. The review generates no receipt.

## Runtime and recorded shutdown

Readiness passed in 5.118 seconds. Actual template/tokenizer probes verified all
18 frozen request payloads before generation, with closed empty thinking prefixes.
Prompt lengths are 327–675 tokens: maximum 675 + output allowance 384 = 1,059,
within context 2,048. Six generated responses finish `stop`, use 78–118 output
tokens and report zero prompt-cache counters; no truncation explanation is supported.
The remaining twelve requests had metadata probes, not generation/evaluation.

The **current run's** [startup/inference log](evidence/server.stderr.log) reports
37/37 layers offloaded, Vulkan0/RX 6800 XT, 7,669.77 MiB model and 288 MiB KV buffers.
CPU-mapped/host buffers also appear. Positive WDDM allocation and 357 resource samples
meet unchanged guards: sampled peaks are 8,421,654,528 bytes owned GPU allocation,
8,191,111,168 bytes RSS and 8,841,275,804 bytes cumulative scratch. No recorded
resource/ownership guard failure or forced-watchdog exit occurs. These sampled
allocation figures are not residency guarantees or proof that every operation runs
on GPU. No CPU comparison measured acceleration.

Six request wall times total 15.672 seconds; median 2.449, nearest-rank p95/maximum
3.200 seconds. They meet exploratory targets on this small known-case sample, not
accepted product latency guarantees. No paired fresh v1 arm ran; graph reuse,
warmth, prompt length and manual transfer pauses limit performance attribution.
Time spent in transfer/assessment was not separately measured.

Windows records show planned [server exit](evidence/server_exit.json), confirmed
exit -1, and [watchdog exit](evidence/watchdog_exit.json) `server_ended`/0 with an
ended ownership observation. [Watchdog process exit](evidence/watchdog_process_exit.json)
is confirmed/0; [cleanup](evidence/cleanup_manifest.json) preserves reusable artifacts.
Pinned model/runtime/executable hashes match their recorded verification. These
are recorded Windows findings; this Codespace cannot inspect live desktop processes
or independently rehash its large artifacts.

## Original export versus supplemented copy

| Archive | SHA-256 | Verification |
|---|---|---|
| [Original upload](../../../../build/windows-v2-0-1-transfers/attempt-20261014-2207~/final-results.zip), also [preserved copy](uploaded/final-results-original.zip), 209,601 bytes | `189b7b7cb38a52f7ae8bddb6f1ec58b98887644303e79e5a67e08ef8c53f4a5f` | CRC/safe archive checks pass; 103 present manifest hashes match. One listed fixture is absent. Unchanged closeout verifier exits 1. |
| [Separately labelled supplemented archive](final-results-supplemented.zip), 213,588 bytes | `2fd071288861838d2e5962720a74ebd792f31b459db426073647414cf0685ce4` | All 107 original file entries/names/bytes and manifest preserved, plus exactly one verified fixture. CRC and unchanged closeout verifier pass, exit 0. **Model gate remains failed.** |

The sole missing member is `fixtures/startup-v2-20261014.log`: 14,212 bytes, SHA-256
`bd8b0840ff79f74c4da2f2ef0559ab76c7019eb3bcf929d55c4b01a23d08deaf`.
It matches the frozen 2.0.1 source file, downloadable frozen ZIP, freeze hash entry,
cleanup manifest and earlier failed v2 startup log exactly. It is a **historical
offline-regression fixture**, not substitute current-run offload evidence.
Supplementation recompresses unchanged original members into a new archive and
adds that fixture; it changes neither the original ZIP nor its manifest.

Cause: frozen [Common.ps1](working/bundle/Common.ps1) lines 191/201 export top-level
JSON/JSONL/log files and only requests/responses/templates/checkpoints/inbox folders.
Lines 246–249 build the manifest recursively, including nested `.log` files.
Thus the manifest includes the fixture while the exporter omits its folder.
The frozen harness is unchanged; no replacement bundle or run was prepared.

Prior CLI stderr was not uploaded. The original export's unchanged verifier failure
is reproduced and preserved in [original stderr](checks/original.stderr.log), separate
from the [supplemented verification](checks/supplemented-closeout-output/closeout-verification.json).
[Supplementation provenance](supplementation.json), [structured review](review.json)
and [review procedure](verify_review.py) retain hashes and exact commands. All
uploaded checkpoint/assessment/receipt files remain intact.

## Smallest proposed next investigation

Review the preserved C6 rendered request and output against the input-language,
status/null and limitation/uncertainty contract before deciding whether another
bounded comparison is justified. English normalized values may be conflated with
input-language classification; that is a hypothesis, not an established cause.
Keep this semantic routing question separate from the export selection defect
and from the now-matching DE/FR/IT labels on exposed examples. Proposal only:
no prompt/validator change, continuation, inference or automatic tuning is authorized.
All 55 held-out cases remain untouched; linguistic and final DESIGN acceptance
remain pending. No downloads, installation, production changes or Git delivery.

## Input-language separation — DESIGN proposal, 2026-10-15

**Proposal only; no execution or production component selected.** Retain direction
A, DE/FR/IT/EN, approved privacy and unchanged scoring. The closed run and failed
gate above remain intact. This develops the proposed offline routing review.

### Evidence and limits

The actual [C6 rendered template](evidence/templates/06-C6-v2.json) contains the
complete [request system text](evidence/requests/06-C6-v2.json) verbatim, including
the explicit Spanish unsupported instruction, independent input-language selection,
and `unsupported`/`language=null`/nonempty limitation and supported-language
rephrasing instruction. The [request schema](evidence/schema.json), identical to
the request's response format, permits that status, null language, nullable
subject/action with empty quotes, and a nonempty string array in `unresolved`.
It does not enforce those semantic relationships through conditional rules or
require a nonempty array; both the correct route and the observed wrong route
fit its structural constraints. A schema conflict did not require this failure.

The [response](evidence/responses/06-C6-v2.json) instead gives `understood/en`,
English `kettle`/`repair`, exact Spanish quotes and empty `unresolved`. Recorded
finish is `stop`: 662 input/80 output tokens, below the 384-output/2048-context
limits. No missing instruction or demonstrated truncation explains the error.
Conflating normalized English with input language remains a hypothesis; correlated
classification/instruction-following errors are also possible. These records
cannot distinguish the model's internal cause. Grounded quotes do not establish
correct status, supported-language interpretation or faithful evidence rendering.

### Proposed responsibilities and unchanged contract

A local recognition adapter would report hypotheses from **original input only**
at the existing interpretation boundary. Keep internal language identity/candidates
(including `es`, other unsupported languages, mixed or unknown), supported-scope
policy, meaning interpretation, English normalized values and explanation-language
choice distinct. Identifying Spanish internally adds no Spanish interpretation
or translation requirement. English category/action labels never establish that
the original input was English; quotations remain verbatim original spans.
Interpretation must still establish every meaning-bearing constraint independently.

| Evidence/outcome | Existing external handling to preserve |
|---|---|
| Reliably identified supported input | Supported language label and explanations in that language despite a different browser preference; `understood` only if meaning is established. No routine selector; recognition alone cannot approve interpretation. |
| Clearly unsupported language/capability | Map internal identity to `unsupported`, `language=null`, nonempty limitation and invitation to rephrase in DE/FR/IT/EN; preserve input/fields and only safely established partial meaning. No external `es` field or forced English label. |
| Understandable short/shared subject, uncertain language | Permit retrieval and `understood` with null language; existing supported explanation choice precedes supported browser preference, with easy correction. Neither is a claim of detection. If neither exists, offer the approved one-time choice. |
| Understood supported-language mixture | Retain every clause/constraint; external `mixed`, clear primary explanation language or the same preference path. A whole-text majority label must not discard a minority-language constraint. |
| Genuine meaning uncertainty or unavailable capability | Targeted `clarification` with uncertainty, or capability limitation/rephrasing as appropriate; never guess an amount, negation or unsupported clause. Unknown language alone is not proof of unsupported input. |

Names/places/shared words alone are not language evidence. Dialectal negation must
not be certified as standard German from a detector's `de` guess. A technical
recognizer fault remains a processing error with explicit retry, not a capability
or knowledge-coverage outcome. Search country stays independently entered/defaulted;
do not supply the country field as a language prior or strip places from original
text. Preferences affect explanation choice only under
the approved ambiguity path, not recognition or numeric interpretation. Preserve
originals and minimal justified provenance locally, without a new language profile,
telemetry, external fallback or broader retention. Faithful rendering of reviewed
source evidence remains a separate validation responsibility.

### Alternatives

| Consideration | A — separate classification call to retained Qwen3-8B | B — independent local detector |
|---|---|---|
| Suitability | Can be asked for broad language candidates/unknown and mixed clauses, without English subject labels; the same model may repeat correlated mistakes. A focused prompt is untested. | Independent signal suited to screening language identity, not meaning, constraints or translation. Short/shared, dialect and mixed input remain risks. |
| Privacy | Local, loopback only; no external inference. | Local CPU processing; no request text sent to a provider. |
| Dependencies/setup | Reuses pinned runtime/model; needs a newly approved classifier prompt and comparison, not a replay of the closed run. | Adds an experimental native library/wheel; isolated environment, version/hash and license review needed before acquisition. No application dependency change. |
| Resources/availability | Requires a newly verified suitable owner-controlled host and existing GPU/model safeguards. Neither this Codespace nor the ASUS client is assumed suitable. | CPU-only screen proposed in the Codespace, conditional on fresh headroom/package preflight; no desktop/GPU dependency. |
| Added latency | Adds a serial generation request, plus loading if not resident. Previous 2.39–3.20s complete interpretation times do not measure a focused classifier. | Measure cold initialization and warm CPU calls separately; no measured local latency yet. |

**Recommend B for one screening investigation**, not production selection.
[Lingua 2.2.0 documentation](https://github.com/pemistahl/lingua-py/blob/v2.2.0/README.md)
describes offline operation, Rust-backed Python bindings, 75 languages including
DE/FR/IT/EN and Spanish, ranked language scores and optional abstention. Its
mixed-language detection is explicitly experimental and weakens on short phrases;
scores/relative-distance settings are not a calibrated product confidence policy.
Use its full language inventory in the proposed screen, not just the four accepted
languages. Other languages can still be outside the detector's inventory.
[Publisher package metadata](https://pypi.org/project/lingua-language-detector/2.2.0/#files)
lists Python >=3.12 and CPython 3.12 Linux x86-64 and Windows x86-64 wheels of about
170 MB. Platform installation and local suitability are unverified. Do not
substitute a source build or low-accuracy mode if prerequisites fail.

### Bounded investigation requiring separate approval

Prepare/freeze **24 new synthetic controls** and expected language candidates,
allowed ambiguity, capability/clarification route and preference/country invariants
before any detector use. Add C6 only as an exposed diagnostic anchor: **25 inputs**.
Do not consult the 55 held-out cases or tailor vocabulary to kettles. Use several
product/service/habit contexts with negation, names, amounts and constraints.

| New controls | Coverage |
|---|---|
| 8 | Two clear requests per DE/FR/IT/EN; ordinary phrasing and meaningful constraints. |
| 4 | Clear unsupported Spanish, Portuguese, Dutch and Polish; capability/rephrasing controls, not added language support. |
| 4 | Short/shared words and names/place-only fragments; preserve ambiguity, distinguishing a recognisable subject from genuinely unclear meaning. |
| 4 | Clear-primary and balanced supported mixtures, an unresolved foreign constraint, and unvalidated Swiss-German negation. Never discard the difficult clause. |
| 4 | Preference/browser/country counterfactuals and numeric meaning uncertainty; include unsupported/missing preference and preserve country independently. |

Propose one fixed-order pass followed by one identical warm pass: **50 records**,
each with full-text ranked scores and experimental mixed-language spans (**100
library calls**, zero LLM calls). Keep original, hypotheses, initialization/call
timings, cache/loading state and peak RSS; distinguish raw detector output from
an offline review of the intended contract mapping. Do not overwrite C6's response
or run the old scorer on an invented repaired response. This cannot establish
actual interpretation, quote preservation or evidence rendering end to end.

Proposed limits: **30 minutes including acquisition/setup/loading**, at most two
CPU threads, **1 GiB owned RSS**, **1 GiB additional scratch**, **200 MB total
acquisition**, no paid infrastructure or reviewer expense. Verify exact wheel and
dependency sizes/hashes and live RAM/disk before acquisition; existing workspace
safeguards remain. No Qwen loading, GPU use, source builds, retries or threshold
sweeps. If no compatible wheel, sufficient headroom or approved acquisition is
available, stop. Time/resource/package/runtime failure stops and preserves partial
records; classification failures remain recorded through the fixed sample, without
tuning or another run.

Screening criteria: correct raw top-ranked language for all 12 clear new controls
and C6 in both passes; any error rejects this screen. Review all ambiguous/mixed/
preference controls against their frozen allowed routes: no forced detection from
names/preferences, no unsupported-to-supported promotion, lost constraint or
country change. Failure remains failure; do not hide it behind abstention or
post-hoc mapping. A misleading confident label on shared/dialect input is a
documented safety limitation, not evidence of understood meaning. No confidence
threshold is introduced; whether a usable abstention policy can be justified is
an open design question. Proposed feasibility targets: cold initialization plus
first classification <=5s, warm per-record p95 <=100ms (nearest-rank, 25 samples),
with ranking/segmentation measured separately. These are investigation targets,
not accepted product latency requirements or predictions.

AI-assisted expectations/results remain exploratory; qualified DE/FR/IT/EN review
is unstaffed and pending. Even a successful screen warrants only an owner review
of the next design step, not production selection or a combined interpreter run.
Approval needed before isolated acquisition/installation and this bounded CPU
screen; no execution bundle is prepared here. Requirements, frozen artifacts,
scoring and failed gates remain unchanged; DESIGN stays in-progress.
