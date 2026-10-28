# Final Granite prior-accounting receipt — 2026-10-27

The project owner's [explicit complete accounting statement](owner-statement.txt)
supports **previously_charged_bytes = 0** and **accounting_complete = true**.
This is owner-attested history, not a Codex network measurement or an inference
from isolated preparation runs. It resolves the evidence gap in the preserved
[earlier blocked preparation](../uc001-granite-prior-accounting-v1/README.md);
that record and the original incomplete template remain unchanged.

The final [prior-budget.json](prior-budget.json) is **2,793 bytes**, UTF-8 without
BOM, with LF newlines. Its exact SHA-256 is:

```text
56a85b9ded9d6c4bf504462e11d551b59e016fcd1c77d8c5102b93ff7df7475a
```

The [detached hash file](prior-budget.json.sha256) avoids a circular self-hash.
Any byte change requires a new reviewed receipt/hash. The original cumulative
model/source ceiling remains **10,737,418,240 bytes** without reset or renewal.
The owner explicitly includes partial, failed and interrupted transfers in the
zero-charge statement, and excludes prerequisite downloads and closed Qwen runs.
No missing traffic history is reconstructed or measured independently here.

## Exact versioned format and bindings

Receipt schema: **uc001-granite-prior-accounting**, integer version **1**.
The JSON file is the exact issued instance. Its fields are:

| Fields | Meaning/type |
|---|---|
| `receipt_schema`, `receipt_schema_version` | Format identifier string and integer 1 |
| `recorded_on`, `owner` | Recording date and explicit project-owner attribution |
| `bundle_id` | Unchanged frozen bundle identity |
| `accounting_complete`, `previously_charged_bytes` | Boolean true and strict integer 0; loader result becomes controller `prior_bytes` |
| `acquisition_ceiling_bytes`, `allowance_scope`, `allowance_reset_or_renewed` | Integer 10737418240, combined model/source scope, boolean false |
| `accepted_proxy_sha256`, `frozen_config_sha256`, `runtime_revision` | Exact accepted proxy/configuration hashes and unchanged runtime commit |
| `preparation_bindings`, `helper_hashes` | Path-to-SHA maps for frozen config, native procedure, accepted proxy, correction ZIP/manifest and all four controller helpers |
| `evidence` | Owner-attestation provenance, statement filename/SHA, recording date, complete coverage/exclusions and no independent Codex measurement |
| `execution_authorized` | Boolean false; receipt preparation grants no execution |

Accepted proxy SHA remains
`a7c62f83356636bea839633382bb62a3e53bcce466caea7b32226cece1e7bb1d`.
Frozen bundle/configuration and current native preparation identities are bound
inside the receipt; none is amended. The statement SHA is
`3fd9e56c68a9dba8fefc198eec6d5599af05c24fed7ddacf376dcc9db152b38c`.

The unchanged proxy `load_prior` enforces the external receipt SHA, bundle,
owner, completeness and strict integer range. Additional version/provenance/
preparation metadata is covered by the receipt hash and this offline verification;
the loader does not independently enforce those extra fields. Controller preflight
separately enforces helper/proxy/frozen identities and its execution gate. Receipt
`execution_authorized: false` is descriptive and does not replace that gate.

## Executed verification and stopping point

**Codespace offline verification only:**

```bash
.venv/bin/python -I -B build/uc001-granite-prior-accounting-final-v1/verify.py
```

**Eight focused checks passed, exit 0:** metadata/evidence/preparation hashes;
actual proxy acceptance of integer zero; actual controller preflight acceptance
of the same receipt; both validators rejecting a wrong external hash, changed
receipt bytes, and incomplete accounting even with a matching hash; separate
execution-gate rejection; no process/network/native-symbol attempts.
The [result](verification.json) retains the exact receipt hash and scope flags.

Controller-positive validation used an isolated in-memory synthetic authorization
input solely to call `validate_native_config`; no execution configuration was
written, activated or passed to `native_run`. No NativeApi, Windows execution,
proxy startup, source/network acquisition, configure/build/compiler/glslc, GPU,
model or inference occurred. Native binding and resource fit remain false.

The receipt is prepared for owner review. It does not establish acquisition/build
readiness or model/runtime suitability, authorize execution or reopen the closed
harmless ownership/helper result. Prior receipts, frozen packages, accepted proxy,
limits, Python environments, Priority 5 acceptance and closed Qwen result remain
unchanged. Normal app.main and real drafts remain inactive. Priorities 3/4 remain
partial; Priority 6/Phase 4 pending. PHASE: 3 / STATUS: in-progress. Stop here.
