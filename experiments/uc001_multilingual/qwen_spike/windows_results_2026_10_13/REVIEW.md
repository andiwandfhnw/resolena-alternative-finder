# Windows Qwen3-8B experiment closeout — 2026-10-13

The tested Qwen3-8B Q8_0 / llama.cpp b11429 Vulkan configuration failed the
unchanged six-case gate: **2/6 strict passes**, both English. The additional
24 new cases and four repetitions did not run. This configuration is not accepted
for production; the finding does not reject every Qwen3 configuration or local
model. Direction A, approved multilingual requirements and privacy remain intact.
UC-001 increment 1 remains **Phase 2 DESIGN / in-progress**; interpreter/hosting,
final DESIGN acceptance and qualified linguistic validation remain pending.

Owner clarification, 2026-10-13: supported-language scope remains English, German,
French and Italian only. C6 is a **Spanish unsupported-language negative control**:
it checks appropriate limitation/rephrasing behaviour, not Spanish interpretation
or translation support. This clarification adds no language requirement and
authorizes no new inference or experiment; the frozen test/results/gate are intact.

## Integrity and provenance

The three uploaded originals are unchanged. Their SHA-256 values are:

| File | Bytes | SHA-256 |
|---|---:|---|
| [final-results.zip](final-results.zip) | 101,614 | `7580e171fc9dde4a9b086f76fea2eae5fc182fea66b20606f1601f734723e2cf` |
| [watchdog_exit.json](watchdog_exit.json) | 80 | `0546c197f19a279c3e136fc4d6d73cee1bca99a753e9e3b06799013376a67353` |
| [cleanup_manifest.json](cleanup_manifest.json) | 112,003 | `b6ed39c76990f3ed342c4c94df6a496f858e053f99b5f347c57e16523314b7cd` |

The ZIP matches the owner-supplied hash, passes CRC checks and contains 86 unique
files totalling 467,635 expanded bytes. Windows separators were normalized only
when creating the new [evidence copy](review/evidence/); absolute/traversal paths,
symlinks, encrypted entries and normalized-name collisions were rejected.

The archived freeze matches repository bundle 1.0.0, SHA-256
`fc9eb769afba2cac79bb69ff1f3ed8cc02c955b2c8293fe7a2d09245ca49a5ce`.
All 39 archived frozen payload files match; the Windows cleanup manifest records
matching hashes for all 49 bundle payload files, including assessor and contract.
The recorded assessment hash and all six request/response gate receipts match.
All 86 archived files match the manifest's `exports\final-results\` entries.
Its experiment-root entries match 85/86: the remaining `state.json` hash is exactly
reproduced by changing only `stopped_pending_review` to
`closed_artifacts_preserved`, as the frozen cleanup script specifies.

Model and runtime ZIP hashes/sizes in the Windows manifest match the approved
pins; binary hash and runtime build information agree with the recorded runtime
verification. These are owner-supplied Windows records, not signed provenance or
an independent rehash of artifacts on the desktop. See [machine-readable review](review.json).

The inspected, unchanged [assessor](../windows_qwen3_8b_v1/assess.py) was run offline
on a separate working copy. Exit 1 is the expected failed gate, not an inference or
assessor crash. [Reassessment](review/reassessment.json) reproduces every per-case
assessment, failures and latency; [reassessed gate](review/reassessed_gate.json)
remains blocked with identical request/response receipts. Only the positive GPU
sample count changes, from 14 to 439: the earlier 7,165-byte resource snapshot is
an exact hash-matching prefix of the final log. Assessment/gate hashes consequently
differ; the [recorded assessment](review/evidence/assessment.json) and
[recorded gate](review/evidence/gate.json) remain unchanged.

## Actual model results

Expectations are frozen, AI-assisted synthetic calibration, without independent
linguistic validation. Exact quote grounding passed for all 13 populated fields
across six responses; it does not establish correct meaning or faithful rendering
of external evidence.

| Case / synthetic input | Strict outcome and meaning assessment | Constraints and grounding |
|---|---|---|
| C1: `Repair my kettle.` | Pass: `understood/en`, `kettle/repair`; expected meaning. [Raw response](review/evidence/responses/01-C1-known.json). | No invented goals/constraints; quotes `kettle`, `Repair` exact. |
| C2: `repair my kettle.` | Pass: `understood/en`, `kettle/repair`; expected meaning. [Raw response](review/evidence/responses/02-C2-known.json). | No invented goals/constraints; quotes `kettle`, `repair` exact. |
| C3: `Repariere meinen Wasserkocher, ohne ihn zu ersetzen.` | Fail: subject `Wasserkocher` canonicalizes to `wasserkocher`, expected `kettle`. Correct `understood/de` and `repair`; plausible equivalent subject, meaning not independently validated. [Raw response](review/evidence/responses/03-C3-known.json). | `no_replacement=true` preserved; exact quotes `Wasserkocher`, `Repariere`, `ohne ihn zu ersetzen`. |
| C4: `Répare ma bouilloire.` | Fail: subject `bouilloire`, expected `kettle`. Correct `understood/fr` and `repair`; plausible equivalent subject. [Raw response](review/evidence/responses/04-C4-known.json). | No invented goals/constraints; quotes `bouilloire`, `Répare` exact. |
| C5: `Ripara il mio bollitore.` | Fail: subject `bollitore`, expected `kettle`. Correct `understood/it` and `repair`; plausible equivalent subject. [Raw response](review/evidence/responses/05-C5-known.json). | No invented goals/constraints; quotes `bollitore`, `Ripara` exact. |
| C6, Spanish unsupported-language negative control: `Repara mi hervidor.` | Fail: expected `unsupported`, language `null`, nonempty uncertainty; actual `understood/fr`, empty uncertainty, subject `hervidor`, action `repair`. [Raw response](review/evidence/responses/06-C6-known.json). | No invented goals/constraints; quotes `hervidor`, `Repara` exact. Unsupported-language handling fails despite valid JSON and grounding; Spanish support is not being evaluated. |

DE/FR/IT failures concern the canonical-English subject contract, explicitly
required by the prompt. The unchanged alias map lacks those kettle variants.
Neither its scorer's `incorrect` category nor those label mismatches alone proves
an incorrect underlying object. They remain strict failures; no alias, validator
or expectation was changed. C6 additionally receives the assessor's `subject`
flag because `hervidor` is outside its permitted partial labels. That flag does not
independently establish a different object; the wrong supported-language/status
classification and absent uncertainty establish failure regardless.

The six response files, six inference task launches and
[progress record](review/evidence/progress.json) agree. The remaining 28 request
fixtures exist as frozen inputs, with no response/template execution records.
They are unrun, not failed evaluations. The original 55 held-out cases are excluded
from the bundle; no contents were opened in this review, and recorded model
exposure is zero. These six known cases remain calibration data.

## Runtime, timing and closeout

Windows records identify the RX 6800 XT and Vulkan0, pinned Q8_0 model/runtime,
two inference/prompt threads, context 2,048, output limit 384, temperature 0.7,
seed 42 and the frozen JSON schema. All six rendered template probes end in an
empty closed thinking block; no reasoning output was returned. Prompt counts
329–341 plus the output allowance fit context; completions are 78–121 tokens.
Every response is HTTP 200 with `finish_reason=stop`; server logs record
`truncated=0`. There is no evidence of truncation explaining these failures.
Requests override server sampling defaults; responses do not independently report
all effective sampler values. See [command](review/evidence/server_command.json),
[properties](review/evidence/server_properties.json), and [server log](review/evidence/server.stderr.log).

Readiness took 6.571 s. Request wall times were 2.498, 2.042, 2.859, 2.136, 2.096
and 2.087 s. Warm median 2.096 s and nearest-rank p95 2.859 s meet experimental
targets for five warm samples only. Cache-token counters are zero in all responses;
server logs record graph reuse and hash verification may have warmed OS file cache.
This is neither a CPU speedup comparison nor evidence of general latency reliability.

The final 439 resource samples all report positive owned GPU allocation, peaking
at 7.843 GiB; sampled owned RSS peaks at 7.639 GiB and scratch at 8.232 GiB.
Minimum sampled available RAM is 30.762 GiB, GPU headroom 5.620 GiB and target-drive
space 532.657 GiB. All recorded samples stay within unchanged caps/floors; no guard
failure is present. Sampling can miss short peaks, and the GPU gauge is WDDM usage
against DXGI capacity, not a per-process dynamic residency budget. Neither log
contains an offloaded-layer count, so the assessor's `full_offload=false` represents
missing confirmation, not confirmed CPU-only execution or a measured partial count.
Requested `--n-gpu-layers 99` and measured allocation do not prove full offload or
acceleration. This also blocks the runtime-evidence gate.

Setup started 19:08:07 UTC; evaluation window started 19:18:56 UTC. Shutdown at
19:29:12 was 21m05.63s after setup and 10m15.79s into evaluation, within the original
deadlines. Approximately 9m54s elapsed between the sixth completion and the recorded
gate rejection; the logs do not separately time transfer versus owner assessment.
The download ledger records verified model/runtime acquisition plus its reserved
allowance: 8,743,904,457 bytes, below 10 GB.

[Run failure](review/evidence/run_failure.json) records the rejected known gate.
[Driver exit](review/evidence/driver_exit.json) is 1;
[server exit](review/evidence/server_exit.json) is -1 with planned owned shutdown,
consistent with the runner's explicit owned-process stop rather than a natural
success exit. [Watchdog exit](watchdog_exit.json) records `server_ended` at
19:29:12.781 UTC; it is a completion record, not a captured watchdog process exit
code. Cleanup at 19:34:28 UTC records preservation of model, runtime, results,
logs, markers and deadlines without deletion. No ownership-stop failure is recorded.
The Codespace cannot establish current Windows process state or current artifact
existence; shutdown/cleanup findings are limited to the consistent uploaded evidence.

## Proposed follow-up — review unsupported-language handling

Review limitation/rephrasing behaviour offline using C6's preserved
request/template/response and its unchanged unsupported-language expectation.
The Spanish negative control tests respect for the EN/DE/FR/IT support boundary,
not Spanish interpretation or translation. Do not claim a root cause from one output.

Review DE/FR/IT canonical-English subject-label mismatches separately as a
normalization-contract issue, not relaxed validation or proof of wrong meaning.
Full-offload log capture remains a separate operational evidence gap, not an
explanation for the unsupported-language failure. These reviews remain proposals;
any later change or experiment requires its own approval/freeze. No new inference
or experiment is authorized by this clarification.

The [separate v2 proposal](../windows_qwen3_8b_followup_v2/PROPOSAL.md) supplies the
exact draft prompt changes, six fresh expectations and an 18-request/30-minute
comparison for owner review. It also records pinned-source evidence for the
logging threshold. This does not change the original v1 results or failed gate.

Request interpretation and faithful source-evidence rendering remain separate
validation responsibilities; this run tested only the former and input quote
grounding. Qualified DE/FR/IT/EN review remains pending; reviewers are not assumed
available and these AI-assisted judgments do not replace them. No production or
phase acceptance follows.
