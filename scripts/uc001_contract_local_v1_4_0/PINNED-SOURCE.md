# Output-limit evidence

Inspected retained source and the publisher's exact commit
`d81235049384534c167caea52b85a694f6103d14`; no runtime/model execution.

- [`get_res_props`](https://github.com/ggml-org/llama.cpp/blob/d81235049384534c167caea52b85a694f6103d14/tools/server/server-context.cpp)
  creates a fresh task parameter object and copies sampling settings, not the CLI
  output count. [`task_params`](https://github.com/ggml-org/llama.cpp/blob/d81235049384534c167caea52b85a694f6103d14/tools/server/server-task.h)
  initializes `n_predict` to -1; its serialized value is a reported task default.
  It is not evidence that the launched server's CLI fallback is unlimited.
- [`eval_llama_cmpl_schema` and `build_llama_cmpl_schema`](https://github.com/ggml-org/llama.cpp/blob/d81235049384534c167caea52b85a694f6103d14/tools/server/server-schema.cpp)
  initialize request defaults from server parameters and recognize `max_tokens`
  and `max_completion_tokens` as aliases for `n_predict`.
- The same pinned server-context implementation selects the request's count when
  specified, otherwise the CLI fallback, and checks the remaining output budget.
  CLI `--predict 3072` therefore is not a ceiling on an overriding request.

The corrected full verifier requires the pinned report behavior **plus** recorded
launch arguments `--predict 3072` and an exact integer request `max_tokens:3072`,
without alternative output-count fields. Capture checks the actual request body
before sending it; the shared adapter is unchanged. Existing prompt-fit, response
token-count and finish-reason checks remain. Sampling comparison tolerance is unchanged.

The old saved receipt did not record launch arguments. Its -1 and floating-point
sampling values can be checked model-free, together with the unchanged adapter's
request construction. This does not establish historical CLI execution, output
generation, GPU readiness or interpreter suitability. No values are substituted
into the saved receipt and no runtime settings are changed.
