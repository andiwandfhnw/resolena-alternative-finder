# Static schema and native-interface audit

Inspected 2026-10-25 against llama.cpp v0.7.0 commit
`620d2225cc436ab0b001e3200e590e3b286ef9ab`. This records static source inspection.
Offline schema-shape checks are reported separately in the preparation receipt;
they do not execute the native converter, selected GGUF, template engine or
model. The candidate remains provisional.

## Schema boundary

The existing `WireResult` is finite and nonrecursive. Its validation keywords
are `type`, `properties`, `required`, `additionalProperties`, `items`, `enum`,
`anyOf`, `minLength` and integer `minimum`; `$defs`/`$ref` express reusable local
definitions. `title` is a non-validating annotation. Removing an annotation does
not remove a constraint. The transport schema must retain every validation
constraint and reject unknown/unaccounted validation keywords.

Inline local references without inventing defaults, coercing types or losing
sibling constraints. Preserve closed objects, every required nullable field,
string minima and positive integer quotation occurrences. Never substitute `{}`
or unconstrained JSON. Clause coverage, unique item membership, exact original
spans, literal names/places and numeric meaning remain enforced by the unchanged
strict decoder/domain validation; grammar cannot establish semantic correctness.

The pinned [grammar guide](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/grammars/README.md#json-schemas--gbnf)
warns that some features are unsupported and nested references have limitations.
However, the current [converter](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/common/json-schema-to-grammar.cpp#L993)
and its [tests](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/tests/test-json-schema-to-grammar.cpp#L1550)
include recursive-reference support. Inlining this finite schema is a conservative
compatibility measure, not evidence that this revision's reference handling failed.
String length and integer bounds have explicit converter branches. Native conversion
and inspection of the resulting grammar remain pending.

Only `json_schema` is sent to native completion; do not also send `grammar`.
The pinned [request parser](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/tools/server/server-schema.cpp#L251)
can select the grammar branch when both keys exist. Build with LLGuidance disabled
to keep the selected native GBNF route explicit. The prompt must explain the
contract because the schema is not automatically inserted into model instructions.

## Native observations requiring later confirmation

- `/apply-template` uses the actual chat parser and accepts template kwargs.
  Explicit system-first instructions, `thinking:false`, `enable_thinking:false`
  and reasoning format `none` are proposed. Equality with an expected mock string
  proves no actual GGUF/template rendering. Later verify the artifact/header,
  published template expectation, server-reported template and actual rendering.
- `/tokenize` with `add_special:false`, `parse_special:true`, `with_pieces:false`
  returns integer IDs. Passing those IDs to native completion avoids implicit
  BOS insertion; no original input may be truncated to fit.
- Native final `content` is decoded exactly. Require complete EOS termination,
  no truncation, effective settings and complete prompt/output accounting.
  Reject wrappers, fences, malformed JSON and invalid meaning packets without repair.
- Native `tokens_evaluated` is the full submitted prompt count. `tokens_cached`
  is assigned the final slot cache length, despite older documentation wording;
  it is not proof of previous-prompt reuse and need not be zero. The echoed
  `prompt` is a detokenized string, even for token-array input.
- `generation_settings` does not echo `cache_prompt`, `id_slot`, `n_cmpl` or
  context size. `/props` exposes `default_generation_settings.n_ctx`, `total_slots`,
  `model_alias`, `chat_template`, `bos_token`, `eos_token`, `build_info` and
  modalities. Server identity/header/build checks remain execution prerequisites.
- An empty requested stop list falls back to CLI defaults. Check the effective
  stop list as well. No warm-up, speculative generation or hidden application
  inference is permitted by the proposed eleven-generation budget.
- Greedy selection requires both temperature and dynamic temperature range zero
  in the pinned [sampler construction](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/common/sampling.cpp#L403).
  Request and check `dynatemp_range:0.0`; a positive range can enable distribution
  sampling even with base temperature zero. Its exponent is immaterial at zero range.

Sources: [native API](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/tools/server/README.md#post-completion-given-a-prompt-it-returns-the-predicted-completion),
[template/token handlers and accounting](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/tools/server/server-context.cpp#L2252),
[effective-setting serializer](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/tools/server/server-task.cpp#L30).

## Frozen model-free inspector source

`native-inspection/inspect-schema.cpp` calls only the pinned native JSON/schema
conversion API; it has no model loading, context creation, tokenization or
generation calls. Its CMake project links the actual `llama-common` target in
the separately acquired, integrity-checked pinned source. GPU backends are off
for this inspector only; this is not permission for CPU model fallback.

No build or execution of that helper occurred here. After separate authorization,
use a fresh build directory and verified source revision, capture stderr, and
require successful exit, a new nonempty GBNF output and an empty stderr file.
The converter can print incomplete-conversion warnings without throwing; the
helper does not turn a zero exit alone into a warning-free conversion claim.
Review the grammar and its retained constraints before future inference.

Old guide references to a Python converter and `llama-gbnf-validator` do not
correspond to tools present at this pin. Do not use nonexistent commands or
`llama-cli -n 0`: evaluating a prompt is still inference. Model-free structural
conversion is separate from grammar sampling correctness and qualified meaning
review, all of which retain their stated pending status.
