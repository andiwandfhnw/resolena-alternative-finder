# Actual paired calibration results — portable build

All twelve requests completed; 0/12 passed and the required temperature-zero score is 0/6. Stop this configuration pending review. No retries, tuning or heldout evaluation.

Build: 785.29s, exit 0. Readiness: 1.459s. Calibration including loading: 268.90s. Total extension: 1078.64s. Model exit 0; driver exit 1 for failed calibration.

These are actual model results. Separately, 12 synthetic harness checks passed (3 flags, 5 reporting, 4 preflight logging). No validator/prompt/schema/case/alias changes.

All HTTP statuses are 200, all finish reasons are stop, and all cache_n/cached prompt tokens are 0. Complete request and raw wire response records are linked for each arm. Output-token limit 384; context 2048; seed 42; two threads; non-thinking. No response reached the output limit.

Subject/action columns refer to the unchanged normalized-label check; status, language, goals/constraints and quote fidelity remain separate required dimensions. The water_kettle/bouilloire/répare labels miss the frozen normalization contract; they are not by themselves evidence of a different physical object. For unsupported C6 the unchanged helper does not score subject/constraints; describe any emitted unsupported interpretation rather than treating the branch as a pass.

The original Intel/native smoke and this AMD/fixed-feature build differ in hardware/build. Hashing may warm OS cache; exact model-page residency was not measured. Do not attribute elapsed differences to temperature alone; emitted token counts differ.

## C1

Synthetic input: `Repair my kettle.`.

Frozen expectation: `{"status": "understood", "language": "en", "subject": "kettle", "action": "repair", "goals": [], "constraints": {}}`.

| Temp | Actual status/language | Status correct | Language correct | Subject/action match | Goals/constraints preserved | Exact quote grounding | Required uncertainty | Pass |
|---|---|---|---|---|---|---|---|---|
| 0.7 | understood/en | yes | yes | yes | yes | no | yes | no |
| 0 | unsupported/en | no | yes | yes | no | no | yes | no |

Temperature 0.7: [complete request](requests/01-C1-t0.7.json), [raw HTTP response](responses/01-C1-t0.7.json).

Actual model content:

```json
{"status": "understood", "language": "en", "subject": {"value": "kettle", "quote": "kettle"}, "action": {"value": "repair", "quote": "repair my kettle"}, "goals": [], "constraints": [],"unresolved": []}
```

Structural errors: `["ungrounded_quote"]`. Frozen category: `correct`.

Exact grounding by field: `[{"field": "subject", "quote": "kettle", "exact_substring": true, "absent_value": false}, {"field": "action", "quote": "repair my kettle", "exact_substring": false, "absent_value": false}]`.

Temperature 0: [complete request](requests/02-C1-t0.json), [raw HTTP response](responses/02-C1-t0.json).

Actual model content:

```json
{
  "status": "unsupported",
  "language": "en",
  "subject": {"value": "kettle", "quote": "repair my kettle"},
  "action": {"value": "repair", "quote": "repair my kettle"},
  "goals": [],
  "constraints": [
    {"kind": "no_repair", "value": "true", "quote": "repair my kettle"},
    {"kind": "no_new_purchase", "value": "true", "quote": "repair my kettle"}
  ],
  "unresolved": []
}
```

Structural errors: `["ungrounded_quote", "ungrounded_quote", "ungrounded_quote", "ungrounded_quote"]`. Frozen category: `unsupported`.

Exact grounding by field: `[{"field": "subject", "quote": "repair my kettle", "exact_substring": false, "absent_value": false}, {"field": "action", "quote": "repair my kettle", "exact_substring": false, "absent_value": false}, {"field": "constraints[0]", "quote": "repair my kettle", "exact_substring": false, "absent_value": false}, {"field": "constraints[1]", "quote": "repair my kettle", "exact_substring": false, "absent_value": false}]`.

## C2

Synthetic input: `repair my kettle.`.

Frozen expectation: `{"status": "understood", "language": "en", "subject": "kettle", "action": "repair", "goals": [], "constraints": {}}`.

| Temp | Actual status/language | Status correct | Language correct | Subject/action match | Goals/constraints preserved | Exact quote grounding | Required uncertainty | Pass |
|---|---|---|---|---|---|---|---|---|
| 0 | unsupported/en | no | yes | yes | no | yes | yes | no |
| 0.7 | unsupported/en | no | yes | yes | yes | yes | yes | no |

Temperature 0: [complete request](requests/03-C2-t0.json), [raw HTTP response](responses/03-C2-t0.json).

Actual model content:

```json
{
  "status": "unsupported",
  "language": "en",
  "subject": {"value": "kettle", "quote": "repair my kettle"},
  "action": {"value": "repair", "quote": "repair my kettle"},
  "goals": [],
  "constraints": [
    {"kind": "no_repair", "value": "true", "quote": "repair my kettle"},
    {"kind": "no_new_purchase", "value": "true", "quote": "repair my kettle"}
  ],
  "unresolved": []
}
```

Structural errors: `[]`. Frozen category: `unsupported`.

Exact grounding by field: `[{"field": "subject", "quote": "repair my kettle", "exact_substring": true, "absent_value": false}, {"field": "action", "quote": "repair my kettle", "exact_substring": true, "absent_value": false}, {"field": "constraints[0]", "quote": "repair my kettle", "exact_substring": true, "absent_value": false}, {"field": "constraints[1]", "quote": "repair my kettle", "exact_substring": true, "absent_value": false}]`.

Temperature 0.7: [complete request](requests/04-C2-t0.7.json), [raw HTTP response](responses/04-C2-t0.7.json).

Actual model content:

```json
{"status": "unsupported", "language": "en", "subject": {"value": "kettle", "quote": "repair my kettle"}, "action": {"value": "repair", "quote": "repair my kettle"}, "goals": [], "constraints": [],"unresolved": []}
```

Structural errors: `[]`. Frozen category: `unsupported`.

Exact grounding by field: `[{"field": "subject", "quote": "repair my kettle", "exact_substring": true, "absent_value": false}, {"field": "action", "quote": "repair my kettle", "exact_substring": true, "absent_value": false}]`.

## C3

Synthetic input: `Repariere meinen Wasserkocher, ohne ihn zu ersetzen.`.

Frozen expectation: `{"status": "understood", "language": "de", "subject": "kettle", "action": "repair", "goals": [], "constraints": {"no_replacement": "true"}}`.

| Temp | Actual status/language | Status correct | Language correct | Subject/action match | Goals/constraints preserved | Exact quote grounding | Required uncertainty | Pass |
|---|---|---|---|---|---|---|---|---|
| 0.7 | understood/de | yes | yes | no | no | no | yes | no |
| 0 | understood/de | yes | yes | no | no | no | yes | no |

Temperature 0.7: [complete request](requests/05-C3-t0.7.json), [raw HTTP response](responses/05-C3-t0.7.json).

Actual model content:

```json
{
  "status": "understood",
  "language": "de",
  "subject": {"value": "water_kettle", "quote": "Wasserkocher"},
  "action": {"value": "repair", "quote": "Repariere"},
  "goals": [],
  "constraints": [
    {"kind": "no_replacement", "value": "true", "quote": "ohne ihn zu ersetzen"},
    {"kind": "no_repair", "value": "false", "quote": ""},
    {"kind": "preserve_quality", "value": "true", "quote": ""},
    {"kind": "no_new_purchase", "value": "true", "quote": ""},
    {"kind": "budget", "value": "", "quote": ""},
    {"kind": "storage_min", "value": "", "quote": ""},
    {"kind": "cost_exclusion", "value": "", "quote": ""},
    {"kind": "locality", "value": "", "quote": ""},
    {"kind": "identifier", "value": "", "quote": ""}
  ],
  "unresolved": []
}
```

Structural errors: `["ungrounded_quote", "ungrounded_quote", "ungrounded_quote", "ungrounded_quote", "ungrounded_quote", "ungrounded_quote", "ungrounded_quote", "ungrounded_quote"]`. Frozen category: `incorrect`.

Exact grounding by field: `[{"field": "subject", "quote": "Wasserkocher", "exact_substring": true, "absent_value": false}, {"field": "action", "quote": "Repariere", "exact_substring": true, "absent_value": false}, {"field": "constraints[0]", "quote": "ohne ihn zu ersetzen", "exact_substring": true, "absent_value": false}, {"field": "constraints[1]", "quote": "", "exact_substring": false, "absent_value": false}, {"field": "constraints[2]", "quote": "", "exact_substring": false, "absent_value": false}, {"field": "constraints[3]", "quote": "", "exact_substring": false, "absent_value": false}, {"field": "constraints[4]", "quote": "", "exact_substring": false, "absent_value": false}, {"field": "constraints[5]", "quote": "", "exact_substring": false, "absent_value": false}, {"field": "constraints[6]", "quote": "", "exact_substring": false, "absent_value": false}, {"field": "constraints[7]", "quote": "", "exact_substring": false, "absent_value": false}, {"field": "constraints[8]", "quote": "", "exact_substring": false, "absent_value": false}]`.

Temperature 0: [complete request](requests/06-C3-t0.json), [raw HTTP response](responses/06-C3-t0.json).

Actual model content:

```json
{
  "status": "understood",
  "language": "de",
  "subject": {"value": "water_kettle", "quote": "Wasserkocher"},
  "action": {"value": "repair", "quote": "Repariere"},
  "goals": [],
  "constraints": [
    {"kind": "no_replacement", "value": "true", "quote": "ohne ihn zu ersetzen"},
    {"kind": "no_repair", "value": "false", "quote": ""},
    {"kind": "preserve_quality", "value": "true", "quote": ""},
    {"kind": "no_new_purchase", "value": "true", "quote": ""},
    {"kind": "budget", "value": "null", "quote": ""},
    {"kind": "storage_min", "value": "null", "quote": ""},
    {"kind": "cost_exclusion", "value": "null", "quote": ""},
    {"kind": "locality", "value": "null", "quote": ""},
    {"kind": "identifier", "value": "null", "quote": ""}
  ],
  "unresolved": []
}
```

Structural errors: `["ungrounded_quote", "ungrounded_quote", "ungrounded_quote", "ungrounded_quote", "ungrounded_quote", "ungrounded_quote", "ungrounded_quote", "ungrounded_quote"]`. Frozen category: `incorrect`.

Exact grounding by field: `[{"field": "subject", "quote": "Wasserkocher", "exact_substring": true, "absent_value": false}, {"field": "action", "quote": "Repariere", "exact_substring": true, "absent_value": false}, {"field": "constraints[0]", "quote": "ohne ihn zu ersetzen", "exact_substring": true, "absent_value": false}, {"field": "constraints[1]", "quote": "", "exact_substring": false, "absent_value": false}, {"field": "constraints[2]", "quote": "", "exact_substring": false, "absent_value": false}, {"field": "constraints[3]", "quote": "", "exact_substring": false, "absent_value": false}, {"field": "constraints[4]", "quote": "", "exact_substring": false, "absent_value": false}, {"field": "constraints[5]", "quote": "", "exact_substring": false, "absent_value": false}, {"field": "constraints[6]", "quote": "", "exact_substring": false, "absent_value": false}, {"field": "constraints[7]", "quote": "", "exact_substring": false, "absent_value": false}, {"field": "constraints[8]", "quote": "", "exact_substring": false, "absent_value": false}]`.

## C4

Synthetic input: `Répare ma bouilloire.`.

Frozen expectation: `{"status": "understood", "language": "fr", "subject": "kettle", "action": "repair", "goals": [], "constraints": {}}`.

| Temp | Actual status/language | Status correct | Language correct | Subject/action match | Goals/constraints preserved | Exact quote grounding | Required uncertainty | Pass |
|---|---|---|---|---|---|---|---|---|
| 0 | understood/fr | yes | yes | no | yes | no | yes | no |
| 0.7 | understood/fr | yes | yes | no | no | no | yes | no |

Temperature 0: [complete request](requests/07-C4-t0.json), [raw HTTP response](responses/07-C4-t0.json).

Actual model content:

```json
{"status": "understood", "language": "fr", "subject": {"value": "bouilloire", "quote": "répare ma bouilloire"}, "action": {"value": "repair", "quote": "répare ma bouilloire"}, "goals": [], "constraints": [],"unresolved": []}
```

Structural errors: `["ungrounded_quote", "ungrounded_quote"]`. Frozen category: `incorrect`.

Exact grounding by field: `[{"field": "subject", "quote": "répare ma bouilloire", "exact_substring": false, "absent_value": false}, {"field": "action", "quote": "répare ma bouilloire", "exact_substring": false, "absent_value": false}]`.

Temperature 0.7: [complete request](requests/08-C4-t0.7.json), [raw HTTP response](responses/08-C4-t0.7.json).

Actual model content:

```json
{
  "status": "understood",
  "language": "fr",
  "subject": {"value": "bouilloire", "quote": "bouilloire"},
  "action": {"value": "répare", "quote": "répare ma bouilloire"},
  "goals": [],
  "constraints": [
    {"kind": "no_repair", "value": "true", "quote": "répare ma bouilloire"},
    {"kind": "no_new_purchase", "value": "true", "quote": "répare ma bouilloire"}
  ],
  "unresolved": []
}
```

Structural errors: `["ungrounded_quote", "ungrounded_quote", "ungrounded_quote"]`. Frozen category: `incorrect`.

Exact grounding by field: `[{"field": "subject", "quote": "bouilloire", "exact_substring": true, "absent_value": false}, {"field": "action", "quote": "répare ma bouilloire", "exact_substring": false, "absent_value": false}, {"field": "constraints[0]", "quote": "répare ma bouilloire", "exact_substring": false, "absent_value": false}, {"field": "constraints[1]", "quote": "répare ma bouilloire", "exact_substring": false, "absent_value": false}]`.

## C5

Synthetic input: `Ripara il mio bollitore.`.

Frozen expectation: `{"status": "understood", "language": "it", "subject": "kettle", "action": "repair", "goals": [], "constraints": {}}`.

| Temp | Actual status/language | Status correct | Language correct | Subject/action match | Goals/constraints preserved | Exact quote grounding | Required uncertainty | Pass |
|---|---|---|---|---|---|---|---|---|
| 0.7 | unsupported/it | no | yes | yes | yes | yes | yes | no |
| 0 | unsupported/it | no | yes | yes | yes | yes | yes | no |

Temperature 0.7: [complete request](requests/09-C5-t0.7.json), [raw HTTP response](responses/09-C5-t0.7.json).

Actual model content:

```json
{"status": "unsupported", "language": "it", "subject": {"value": "kettle", "quote": "bollitore"}, "action": {"value": "repair", "quote": "Ripara il mio bollitore"}, "goals": [], "constraints": [],"unresolved": []}
```

Structural errors: `[]`. Frozen category: `unsupported`.

Exact grounding by field: `[{"field": "subject", "quote": "bollitore", "exact_substring": true, "absent_value": false}, {"field": "action", "quote": "Ripara il mio bollitore", "exact_substring": true, "absent_value": false}]`.

Temperature 0: [complete request](requests/10-C5-t0.json), [raw HTTP response](responses/10-C5-t0.json).

Actual model content:

```json
{"status": "unsupported", "language": "it", "subject": {"value": "kettle", "quote": "bollitore"}, "action": {"value": "repair", "quote": "Ripara il mio bollitore"}, "goals": [], "constraints": [],"unresolved": []}
```

Structural errors: `[]`. Frozen category: `unsupported`.

Exact grounding by field: `[{"field": "subject", "quote": "bollitore", "exact_substring": true, "absent_value": false}, {"field": "action", "quote": "Ripara il mio bollitore", "exact_substring": true, "absent_value": false}]`.

## C6

Synthetic input: `Repara mi hervidor.`.

Frozen expectation: `{"status": "unsupported", "language": null, "unresolved_nonempty": true}`.

| Temp | Actual status/language | Status correct | Language correct | Subject/action match | Goals/constraints preserved | Exact quote grounding | Required uncertainty | Pass |
|---|---|---|---|---|---|---|---|---|
| 0 | unsupported/en | yes | no | not scored | not scored | yes | no | no |
| 0.7 | unsupported/en | yes | no | not scored | not scored | yes | no | no |

Temperature 0: [complete request](requests/11-C6-t0.json), [raw HTTP response](responses/11-C6-t0.json).

Actual model content:

```json
{"status": "unsupported", "language": "en", "subject": {"value": "kettle", "quote": "hervidor"}, "action": {"value": "repair", "quote": "Repara mi hervidor"}, "goals": [], "constraints": [],"unresolved": []}
```

Structural errors: `[]`. Frozen category: `unsupported`.

Exact grounding by field: `[{"field": "subject", "quote": "hervidor", "exact_substring": true, "absent_value": false}, {"field": "action", "quote": "Repara mi hervidor", "exact_substring": true, "absent_value": false}]`.

Unsupported status is expected, but language should be null and unresolved nonempty; actual en/empty unresolved fails. Emitted subject/action and any constraints do not establish supported interpretation. At .7 the no_repair/preserve_quality/no_new_purchase assertions are unsupported by the input; this is descriptive diagnosis, with no scoring change.

Temperature 0.7: [complete request](requests/12-C6-t0.7.json), [raw HTTP response](responses/12-C6-t0.7.json).

Actual model content:

```json
{
  "status": "unsupported",
  "language": "en",
  "subject": {"value": "kettle", "quote": "hervidor"},
  "action": {"value": "repair", "quote": "Repara mi hervidor"},
  "goals": [],
  "constraints": [
    {"kind": "no_repair", "value": "true", "quote": "Repara mi hervidor"},
    {"kind": "preserve_quality", "value": "true", "quote": "Repara mi hervidor"},
    {"kind": "no_new_purchase", "value": "true", "quote": "Repara mi hervidor"}
  ],
  "unresolved": []
}
```

Structural errors: `[]`. Frozen category: `unsupported`.

Exact grounding by field: `[{"field": "subject", "quote": "hervidor", "exact_substring": true, "absent_value": false}, {"field": "action", "quote": "Repara mi hervidor", "exact_substring": true, "absent_value": false}, {"field": "constraints[0]", "quote": "Repara mi hervidor", "exact_substring": true, "absent_value": false}, {"field": "constraints[1]", "quote": "Repara mi hervidor", "exact_substring": true, "absent_value": false}, {"field": "constraints[2]", "quote": "Repara mi hervidor", "exact_substring": true, "absent_value": false}]`.

Unsupported status is expected, but language should be null and unresolved nonempty; actual en/empty unresolved fails. Emitted subject/action and any constraints do not establish supported interpretation. At .7 the no_repair/preserve_quality/no_new_purchase assertions are unsupported by the input; this is descriptive diagnosis, with no scoring change.

## Captured timings

| Order | Case | Temp | Wall s | Prompt s | Generation s | Prompt/output tokens | Prompt cache | Finish |
|---|---|---|---|---|---|---|---|---|
| 1 | C1 | 0.7 | 15.524 | 7.877 | 7.633 | 329/64 | 0 | stop |
| 2 | C1 | 0 | 22.135 | 7.809 | 14.312 | 329/120 | 0 | stop |
| 3 | C2 | 0 | 22.386 | 7.800 | 14.574 | 329/120 | 0 | stop |
| 4 | C2 | 0.7 | 15.248 | 7.798 | 7.438 | 329/63 | 0 | stop |
| 5 | C3 | 0.7 | 38.146 | 8.159 | 29.974 | 341/247 | 0 | stop |
| 6 | C3 | 0 | 39.074 | 7.961 | 31.102 | 341/256 | 0 | stop |
| 7 | C4 | 0 | 16.768 | 8.057 | 8.699 | 332/72 | 0 | stop |
| 8 | C4 | 0.7 | 23.761 | 7.704 | 16.045 | 332/133 | 0 | stop |
| 9 | C5 | 0.7 | 15.807 | 7.790 | 8.005 | 334/68 | 0 | stop |
| 10 | C5 | 0 | 15.999 | 7.819 | 8.165 | 334/68 | 0 | stop |
| 11 | C6 | 0 | 15.702 | 7.807 | 7.884 | 332/66 | 0 | stop |
| 12 | C6 | 0.7 | 25.972 | 7.854 | 18.106 | 332/154 | 0 | stop |

Full server properties and applied templates are retained. No additional smoke or frozen evaluation ran; all 55 heldout cases remain preserved and unexposed to this model. Calibration is observed data.

Artifacts/results remain under /workspaces. Return to original 2-core/8 GB/32 GB requires manual selection, stop/start and verification; it is not yet complete. DESIGN stays Phase 2/in-progress with final acceptance pending.
