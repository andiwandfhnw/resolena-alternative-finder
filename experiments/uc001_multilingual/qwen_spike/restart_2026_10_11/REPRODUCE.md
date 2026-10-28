# Multilingual restart — 2026-10-11

Owner-authorized new run linked to [the interrupted renewed attempt](../renewed_2026_10_11/REPRODUCE.md).
Earlier records, markers and deadlines remain immutable. Execute `restart.py` once
with the existing `.venv/bin/python -B`; it refuses an existing execution record,
locks the shared artifact tree and checks for active experiment processes.

Reuse the surviving verified acquisition/configured tree through a short,
Git-ignored workspace alias (`build/qwen-restart-20261011`). The alias fixes the
150-byte Unix socket path; it does not move or reacquire source. `run.py`,
`operations.py` and their existing checks are copied unchanged from the renewed
attempt. Parent prompt/schema/scorer/cases remain frozen and unchanged.

Operational additions only: artifact reuse, exclusive lock/process check,
fresh two-hour deadline from execution start, durable command PID/exit/resource
records, one-shot incremental model-download accounting, periodic inference
resource snapshots, and preservation of artifacts at closeout. Changes are
recorded separately in operational_changes.json; no prompt/model/scorer tuning.

At most 60 minutes including loading/inference and 30 minutes per build; 45 seconds
per request. Preserve 6 GiB scratch, 3.25 GiB owned RSS, available/preflight RAM
guards and cumulative 2.2 GB downloads across renewed attempt and restart.
The prior verified downloads total 185,797,378 bytes. Permit one download of
the pinned 1,834,426,016-byte model only if absent; retain any partial artifact
and its bytes on failure. No acquisition/build/startup retry cycle.

execution.json, progress.json, events.jsonl, resource_samples.jsonl, preparation.json,
download.json and closeout.json record actual execution. results.json saves each
model result immediately using the unchanged evaluator. Full build/inference logs
remain in the shared workspace tree. Model capability is separate from harness
checks. All examples/oracles are synthetic and AI-authored; final DESIGN/ADR-003
acceptance and independent linguistic/evidence-translation validation remain pending.

## Actual closeout

Executed 2026-10-11, 14:12:31–14:34:32 Europe/Berlin. Deadline remains 16:12:31;
unused time does not authorize another attempt after the failed smoke gate.
Build succeeded in 891.75s (exit 0), using existing source/configuration. An event
argument collision then stopped bookkeeping before download/startup. The original
driver and records are preserved in bookkeeping_failure_1; the separately recorded
continue_after_bookkeeping.py corrected that collision, reused the successful
binary and retained exactly the same start/deadline. Its synthetic event regression
check passed. No second build or execution-window renewal occurred.

One model download completed and matched pinned size/SHA-256. Readiness passed
in 14.85s. The separate “Repair my kettle.” smoke request returned well-formed JSON
with status unsupported and two `repair my kettle` quotes that do not occur verbatim
in the input. The unchanged validator classified it as invalid_output after 44.70s;
it was neither truncated (finish_reason stop) nor timed out. Prompt processing
took 21.16s and generation 23.51s under strace. No calibration, 55 frozen evaluation
cases or 16 repeats ran; per-language correctness remains unmeasured.

The runtime printed `0.6.0-dev (build 4, commit a6b2479)`: generated build metadata
picked up the enclosing application repository HEAD. Source acquisition remains
pinned to d81235049384534c167caea52b85a694f6103d14 by the recorded archive checksum;
the displayed commit string is not proof of that source pin. Binary/model hashes
and preservation checks are recorded in verification.json.

Orchestration exit 1; owned model process exit 0; no owned processes remain.
Cumulative downloads 2,020,223,394 bytes; peak owned RSS about 2.08 GiB, scratch
about 2.11 GiB. No AF_INET/AF_INET6 appeared in the owned strace only; this is not
a general telemetry claim. Source, build, binary, model, logs, socket and caches
remain retained. The unchanged evaluator's progress record contains an old cleanup
template; closeout.json and this explicit retention policy supersede that text.
No automatic restart, tuning, production changes or final DESIGN acceptance.

## Smoke diagnosis — read-only, 2026-10-11

Input: `Repair my kettle.` Expected: understood, language en, subject kettle,
action repair, no goals/constraints. Preserved raw message content:

```json
{"status": "unsupported", "language": "en", "subject": {"value": "kettle", "quote": "repair my kettle"}, "action": {"value": "repair", "quote": "repair my kettle"}, "goals": [], "constraints": [],"unresolved": []}
```

Both quotes select the entire clause, lowercase the input's initial `R` and omit
its final period. Omitting the period is permitted substring selection; lowercase
`r` is absent at that position, so neither quote occurs verbatim. The expected
record specifies no gold quotes; `kettle` and `Repair` are valid minimal examples,
not mandatory span boundaries. The model generated unsupported status while
recognizing en. The scorer's unsupported branch returns an empty differences map;
that is a category, not evidence of correct interpretation. Empty unresolved also
does not follow the prompt's uncertainty instruction. The overall invalid_output
comes from two unchanged grounding errors. Internal cause is unobserved: sampling
variation, instruction load or overgeneralized canonicalization are hypotheses.
No instruction asks for unsupported English or normalized quotes; canonical values
and verbatim quotes are separate requirements, not a demonstrated contradiction.

GGUF metadata identifies qwen3/Qwen3 1.7B Instruct and its embedded Qwen3 Jinja
template. Runtime arguments specify --jinja without a template override; pinned
common/chat.cpp:757–785 selects model metadata. The frozen client supplies boolean
chat_template_kwargs.enable_thinking=false, recognized by server-common.cpp:1397–1408.
The template's false branch adds `<think>\n\n</think>\n\n` after the assistant header.
This establishes the configured path; the exact rendered prompt/token IDs, runtime
/props and any reasoning_content were not saved. No reasoning appears in preserved
content. The tokenizer warning about control-looking `</s>` is observed but not
linked causally to this response; EOS metadata is 151645.

response_format=json_object includes the full schema, which the pinned server
accepts. It constrains keys/types/enums, not source-substring fidelity or the
status/language relationship: unsupported+en is structurally allowed. System text
is 1,566 characters/192 whitespace words; actual templated prompt was 329 tokens,
zero cached. Runtime context was 2,048 (GGUF native capacity 40,960); even maximum
329+384 output fits. Actual output was 63 tokens, finish_reason stop; log truncated=0.
No caller stop string was supplied. The runtime maps EOS or stop-word termination
to stop; exact terminal token/stop word and applied grammar were not captured.
There is no evidence of context/output truncation or a configuration correction.

Recorded timings: prompt 21.156797s (329 tokens, 15.55/s), generation 23.511868s
(63 tokens, 2.64/s), total 44.668665s; client wall 44.700436s. The 31.771ms residual
is timer/accounting overhead, not a measured breakdown into transport/queue/parsing.
Readiness 14.85s is separate. TTFT, streaming/token latencies, exact stop token,
logprobs, CPU scheduling cost and uninstrumented latency/strace overhead are absent.

Recommendation B, proposal only: paired calibration changing only request temperature
from .7 to 0, with the original .7 arm as control, seed 42 and all other settings,
prompt/schema/validator/scorer unchanged. Six cases per arm, 12 requests total:

| Synthetic calibration case | Expected meaning |
|---|---|
| `Repair my kettle.` | en, understood, kettle/repair, no goals/constraints; observed calibration reuse |
| `repair my kettle.` | Same; lowercase control |
| `Repariere meinen Wasserkocher, ohne ihn zu ersetzen.` | de, understood, kettle/repair, no_replacement=true |
| `Répare ma bouilloire.` | fr, understood, kettle/repair, no goals/constraints |
| `Ripara il mio bollitore.` | it, understood, kettle/repair, no goals/constraints |
| `Repara mi hervidor.` | unsupported, language null, explicit unresolved limitation |

Require separate authorization; reuse binary/model, no download/build. Budget:
15 minutes including one load (readiness at most 90s), 45s/request, unchanged
6 GiB/3.25 GiB RAM/disk guards. Stop immediately on startup, transport, timeout or
resource failure. Save semantic/grounding failures and complete only the fixed
calibration matrix; no tuning/retries/holdout execution. Success requires all six
temperature-0 cases to satisfy unchanged structural checks and their expected
language/meaning, including negation and unsupported handling; otherwise stop this
configuration pending review. Compare the two arms without claiming causality from
one sample or unseen validation. Capture full request/response, rendered template,
applied settings and stop metadata if available in that authorized experiment.

No inference, downloads or rebuilds occurred in diagnosis. Only smoke content and
planned IDs were inspected; the 55 frozen case texts/expectations were not opened
or sent to a model. Hash verification read frozen files as opaque bytes. All frozen
hashes matched; previous results/artifacts and validator remain intact. Check exact
calibration/holdout non-overlap before any future execution, without model exposure.
DESIGN remains pending; the proposal authorizes no experiment or phase transition.
