# ADR-004 — Multilingual interpretation or a structured first increment

Date: 2026-10-11. Product direction A: owner-approved on this date.
Integration DESIGN/ADR-003 accepted on 2026-10-15; priority-1 DEVELOP authorized.
Interpreter selection, production hosting and qualified review remain pending.
Earlier pending DESIGN statements below retain their dated decision history.

## Context and recommendation

The approved [UC-001](../specs/UC-001-FIND-AND-SELECT-ALTERNATIVE.md#language-amendment--owner-approved-2026-10-10)
requires ordinary DE/FR/IT/EN free text, meaning/constraint preservation and faithful
cross-language explanations. The closed Qwen3-1.7B Q8_0 configuration failed its
six-case paired calibration; this rejects that configuration, not all local models.
Detailed history stays in [experiments](../../experiments/uc001_multilingual/qwen_spike/portable_2026_10_11/REPRODUCE.md#experiment-closed--verified-return).

**Decision: retain A and the approved multilingual free-text/privacy requirements.**
The owner explicitly declined B's scope changes on 2026-10-11. Resource constraints
of one development spike do not justify an implicit product-scope reduction.
The comparison and B amendment list below remain decision history, not accepted scope.
No production interpreter or host is selected. One [next-candidate proposal](../../experiments/uc001_multilingual/qwen_spike/REPRODUCE.md#next-candidate-proposal--2026-10-11)
recommends Qwen3-8B Q8_0 on the owner's available Windows/AMD desktop, subject to
local compatibility/resource checks and separate execution approval. A temporary
synthetic-data test creates no production hosting commitment.
The owner subsequently conditionally approved one exploratory Windows/Vulkan run,
without paid infrastructure/reviewers or CPU fallback. The [versioned bundle](../../experiments/uc001_multilingual/qwen_spike/windows_qwen3_8b_v1/README.md)
prepared on 2026-10-13 freezes the new cases and preserves the original contract;
six known cases must pass the strict gate before more requests. Preparation is not
local preflight or execution evidence, independent linguistic validation or acceptance
of a production interpreter/host. Latency targets are experimental only.
The [2026-10-13 closeout](../../experiments/uc001_multilingual/qwen_spike/windows_results_2026_10_13/REVIEW.md)
records that execution stopped after six known cases: 2/6 strict passes, DE/FR/IT
canonical subject-label failures and failure of the Spanish unsupported-language
negative control's status/language/uncertainty checks,
with exact input quotes grounded in all six. Full GPU offload is unconfirmed.
This tested configuration is not accepted for production; direction A and pending
qualified review/interpreter/hosting/DESIGN decisions remain unchanged.

The [2026-10-14 v2.0.1 closeout](../../experiments/uc001_multilingual/qwen_spike/windows_v2_0_1_results_2026_10_14/REVIEW.md)
verifies 5/6 strict known-case passes, exact quotes and reported 37/37 GPU offload;
the Spanish unsupported-language control still fails status/language/uncertainty.
Twelve planned requests did not run. A labelled supplement repairs archive
completeness only. This configuration remains unaccepted for production; direction
A, approved DE/FR/IT/EN/privacy requirements and pending review/selection/hosting/
DESIGN decisions are unchanged. Further execution is unapproved.

Owner clarification, 2026-10-13: supported languages remain English, German, French
and Italian only. The Spanish negative control verifies appropriate limitation/
rephrasing behaviour, not Spanish interpretation or translation support. Proposed
follow-up: review unsupported-language handling; review DE/FR/IT canonical-label
mismatches separately. No language requirement or new inference/experiment is
authorized; the frozen test, original results and failed gate remain unchanged.

## Product integration refocus — owner direction, 2026-10-15

Stop further standalone detector experiments and exact unsupported-language identity
tuning. DE/FR/IT/EN remain the supported languages; an appropriate limitation and
rephrasing response does not need the exact name of an unsupported language.
This clarifies product relevance without amending requirements or rescoring tests.

The [frozen Lingua screen](../../experiments/uc001_multilingual/lingua_B_runner_v1_0_2/RESULTS.md)
remains failed on its Spanish-versus-Portuguese diagnostic identity check. Both
are unsupported; no application limitation response was tested. The earlier Qwen
unsupported-as-understood result is a product-relevant routing failure for that
configuration. Neither detector identity nor exact quote grounding proves meaning.
Preserve all frozen inputs, failed gates, previous results and closed attempts.

Lingua remains an advisory candidate, not a selected production component or trusted
capability gate. Refocus on the [increment-1 integration proposal](../ARCHITECTURE.md#multilingual-interpretation-and-explanation--provisional-mechanism):
separate recognition hints, complete request interpretation/English normalization,
application policy and faithful evidence rendering. Preserve short/shared-word and
preference handling, all mixed clauses, genuine uncertainty, independent country and
local/Resolena-controlled processing. No scope B changes are adopted.

The [prioritized DEVELOP tasks](../TASKS.md#increment-1-integration--accepted-2026-10-15)
can start with an explicitly test-only vertical slice after phase authorization;
real interpreter suitability, reviewed knowledge and qualified linguistic review
remain scoped delivery/acceptance dependencies. The refocus itself did not accept DESIGN. The owner subsequently accepted the
integration baseline and ADR-003 on 2026-10-15 and authorized only priority-1
DEVELOP. No new experiment, held-out inspection or component/hosting selection
follows; real language capability remains unverified.

## Comparison

| Dimension | A — Approved multilingual free text | B — Explicitly reduced structured input |
|---|---|---|
| User experience | Describe ordinary requests naturally in DE/FR/IT/EN; preserve mixed-language conditions and protected values. Clarify genuine uncertainty; do not make routine form/language selection the substitute for understanding. | Declare a subject from prepared choices or an Other-subject label; optionally choose action/goals and enter typed constraints, amounts/currency/basis and baseline. Subject plus valid country remains sufficient; optional fields stay unspecified. A visible result-language choice uses supported preference/browser default with correction. More predictable but more form effort and less expressiveness. |
| Privacy | Run recognition/interpretation/rendering in Resolena-controlled processing. Preserve originals/provenance; private model access, controlled storage/logging and no external inference/translation fallback. A rented self-managed host still requires owner approval of infrastructure operator access, region and control. | Same privacy boundary and minimal justified location. Deterministic field mapping needs no inference service. Retain submitted fields and field-level provenance rather than invent an original prose request. An unsupported Other-condition must trigger a truthful limitation/clarification, never be ignored. |
| Development effort | Higher: interpreter adapter, deterministic protected-value/grounding/normalization checks, reviewed four-language semantics, uncertainty handling and model-service operation. Existing evidence qualification/persistence rules remain essential. | Lower interpretation/serving effort; additional form, bounded vocabulary, typed validation and submission/provenance work. Prepared labels need review; translating these new controls is additional explicit scope, not assumed full UI localization. Evidence curation, faithful multilingual explanations and application/persistence testing remain. |
| Hosting | Application/persistence plus an interpreter service, colocated or private on controlled infrastructure. Size for measured model/runtime memory, context, concurrency, latency, persistent artifacts and recovery; GPU is an option, not a universal requirement. | Ordinary application/database hosting and durable storage/backups; no model server or GPU required by this proposal. Exact capacity and operating cost remain unmeasured. |
| Unverified | No more capable candidate has passed project checks. Meaning/quotes/labels, ordinary and mixed input, faithful evidence rendering, review capacity, performance, privacy isolation, availability and cost still need evidence. | Vocabulary coverage, form usability/accessibility, four-language labels/renderings, unknown-condition handling and complete application behaviour remain unverified. Structured input does not establish general multilingual understanding. |

Both retain prepared cross-language evidence through reviewed mappings and faithful
DE/FR/IT/EN templates/claim-specific narrative paraphrases. Essential meaning that
cannot be rendered blocks successful presentation. Neither path makes a model an
evidence authority or silently limits evidence to the selected language.

## A: development constraints versus production requirements

[GitHub defines Codespaces as a development environment](https://docs.github.com/en/codespaces/about-codespaces/what-are-codespaces).
Its current 2-core/8 GB resources and the closed experiment's RSS/scratch/time caps
are development/authorization constraints, not production ceilings. Application
work can use isolated substitutes for the interpreter; any future real-model
assessment needs separate, bounded authorization on an approved processing host.

Illustrative capacity only: the publisher's [Qwen3-8B card](https://huggingface.co/Qwen/Qwen3-8B)
documents 8.2B parameters, BF16 tensors, Apache-2.0 and multilingual capability.
Calculated BF16 weights alone are about 16.4 GB (8.2B × 2 bytes), excluding runtime,
KV cache and workspaces. This is not a measured RAM requirement or proof of fitness.
Larger parameter count does not establish better project interpretation.
[AWS lists g5.2xlarge](https://aws.amazon.com/ec2/instance-types/g5/) with 8 vCPUs,
32 GiB host RAM and one A10G GPU with 24 GB GPU memory: a self-managed VM capacity
example, not a selected service, guaranteed model fit, price or account availability.
Production capacity must follow the chosen precision/context and agreed load/latency.

An own server or approved self-managed rented VM could supply the service; external
managed-model APIs are excluded. Keep artifacts/results on durable storage:
[EC2 instance-store data is lost on stop/start](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-lifecycle.html).
Region, quotas, cost, isolation, service operation and actual resource fit are not
verified. No current model/hosting example is a production recommendation.

## B: historical proposed changes — not adopted

This B reduces request interpretation only; broader free-text interpretation is
deferred to a later increment, not removed from the product without approval.

| Approved provision | Required amendment for B |
|---|---|
| Intent trigger; Flow 1–2; R-01/AC-01 | Replace submitting/interpreting prose with declared structured fields. Review the Other-subject path so missing catalogue knowledge remains insufficient coverage rather than invalid input; no new mandatory goal/action/budget/baseline/locality. |
| L-01; R-15/AC-15 | Defer automatic DE/FR/IT/EN request-language recognition and ordinary-paraphrase handling. Permit explicit result-language choice; do not claim input language was detected. |
| L-02 and input portions of L-03 | Defer extracting meaning/raw spans, negation and arbitrary constraints from ordinary/short/mixed prose. Preserve supplied names/values/constraints as fields with field provenance. Unsupported conditions must not be silently discarded. |
| L-05; persistence representation in L-06/Flow 7 and R-10/AC-10 | Explanation language derives from declared preference/browser/correction rather than clear prose detection; persist original structured submission, its mapped interpretation and actual language origin. Preserve faithful source/derived provenance and local processing. |
| Affected examples/tests | Amend LAC-01–07, request-rephrasing parts of LAC-10/11, and automatic-detection parts of LAC-12/13; split/defer their free-text portions in TL-01/02/04 and T-01/08/10–12. Numeric ambiguity in LAC-08, source/rendering safeguards in LAC-09/11/12 and TL-03 remain. No silently deleted test obligations. |

Country independence, optional omissions, evidence/constraint satisfaction, freshness,
currency, coverage outcomes, loading, atomic saving and O-1/O-2 recovery stay binding.
L-04 cross-language evidence and L-05 faithful rendering are retained, not deferred.
Adding reviewed form labels/choices and changing original-input/provenance contracts
requires explicit acceptance. B is not Fast Track; amend the UC and affected design/
acceptance/test records before implementation if chosen. This proposal changes none.

## Remaining owner decisions

1. Completed on 2026-10-15: owner accepted the integration design/ADR-003 and
   selected DEVELOP for priority 1 after the UC/ADR/architecture alignment check. Standalone detector work is stopped; no exact
   unsupported-language identity gate is required by the product. Closed Windows/
   Lingua results are preserved; no further run, CPU fallback or paid rental is
   authorized. Experimental latency targets do not amend product requirements.
2. Qualified DE/FR/IT/EN review remains a future decision; no paid reviewers are
   authorized. AI-assisted expectations/results remain exploratory without qualified
   human adjudication, including after passing automated checks.
3. Select a suitable local interpreter before delivering the real language adapter;
   separately decide production infrastructure control/operator/region, load/latency
   and operating budget when needed for deployment. These choices do not block
   implementing application ports/policy/storage with test substitutes. A detector
   screen settles none of them. No provisioning, download, installation or model run
   is authorized by the product-direction decision.

Current primary sources checked 2026-10-11; publisher/host specifications are not
project validation. The accepted baseline is now in Phase 3/in-progress, priority 1. Approved requirements,
closed experimental results and [ADR-003](ADR-003-persisted-comparison-boundary.md)
remain intact. Only the synthetic saved-comparison slice and necessary test tooling
are authorized; no further language experiment, production hosting or deployment.
