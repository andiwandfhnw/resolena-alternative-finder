# Granite prior-accounting preparation — 2026-10-27

**Blocked by missing complete prior-accounting evidence. No final prior receipt
or integer charge is issued.** The unchanged cumulative ceiling is 10,737,418,240
bytes; no allowance is reset, renewed or treated as unspent.

The owner reports the one authorized Windows structural readiness attempt
**consumed and successful**. The [supplied result](owner-structural-result.json)
records Python 3.12.11, packaged controller/worker imports, schema 1 and integrity
success, without runtime injection or forbidden attempts. The owner accepts only
the Windows integrity/import/schema gate. Native binding and resource fit remain
false; no live proxy, ownership rerun, acquisition/build or GPU/model/inference
occurred. Codex did not execute Windows or read a desktop result directory. The
successful harmless ownership/helper model remains CLOSED and unchanged.

## Evidence basis and missing charge

| Category | Preserved evidence and accounting consequence |
|---|---|
| Directly measured Granite prior source/model bytes | No complete historical counter/ledger is supplied in the relevant preserved receipts. No measured integer can be credited. |
| Previously accepted Granite cumulative accounting | None established. The [existing template](../uc001-granite-acquisition-proxy/prior-budget.template.json) explicitly has `accounting_complete: false` and `previously_charged_bytes: null`. |
| Dated no-acquisition observations | The [original preparation receipt](../uc001-granite-contract-v1/verification.json) reports no weights/source/runtime acquisition during that preparation. The harmless/structural runs likewise performed none. These bounded observations do not certify the complete allowance history. |
| Other downloads | Python/package/SDK installation and handoff transfers are prerequisites outside the frozen combined model/source acquisition scope. Expected file sizes, HEAD metadata and local ZIP sizes do not measure cumulative source/model downloads. No such number is substituted or deducted. |
| Separate earlier accounting | TASKS preserves a 2,020,223,394-byte total for the closed Qwen run. It is not an accepted Granite prior charge; no experiment artifacts were reopened or total recalculated. |
| Unknown/unproven | Complete Granite model/source transfer history, including any partial/failed attempts and charges already accepted against this allowance. Unknown is not zero. |

The [frozen acquisition definition](../../scripts/uc001_granite_contract_v1/README.md)
states that model and runtime-source acquisition share one 30-minute/10-GiB
allowance. The [accepted readiness review](../uc001-granite-native-readiness-v1/README.md)
already identifies the missing complete owner-reviewed receipt; that finding is
reused, without reopening feasibility or experiment history.

**Smallest missing evidence:** one complete owner-supplied, allowance-specific
accounting statement covering all earlier Granite model/source acquisitions,
including partial/failed transfers, with preserved measured-byte or previously
accepted-charge evidence and its exact hashes. If none occurred, that requires
an explicit complete owner statement; it cannot be inferred from preparation
permissions or isolated no-acquisition observations. Missing history must not be
reconstructed from artifact sizes or guesses.

## Actual receipt and preflight contracts

The accepted [proxy `load_prior`](../../scripts/uc001_granite_acquisition_proxy/proxy.py)
checks the exact external receipt SHA-256, then these JSON fields:

| Field | Required value |
|---|---|
| `bundle_id` | `9a4acb903c834737809b2648c358da9f2d91b116471966fb7b691847a069f4b4` |
| `owner` | Explicit, nonempty owner attribution |
| `accounting_complete` | Exactly `true`, supported by complete evidence |
| `previously_charged_bytes` | Strict integer `0 <= value < 10737418240`; this becomes controller `prior_bytes` |

The [controller preflight](../../scripts/uc001_granite_controller/controller.py)
separately requires explicit execution authorization, the fixed native root,
four exact helper hashes, frozen configuration SHA/limits, the accepted proxy SHA
and the prior receipt SHA. No execution configuration is activated here.

The current loader's receipt contract is unnumbered: it does not itself enforce
additional schema/version, explicit ceiling or preparation-hash metadata. Any
eventual completed receipt must also identify its exact schema/version, unchanged
ceiling, accepted proxy SHA, applicable frozen/native preparation identities and
supporting evidence; its exact bytes must be SHA-bound for review and preflight.
No final receipt/schema instance or receipt SHA is emitted while the charge is
unknown. [Contract checks and evidence hashes](contract-checks.json) bind this
blocked preparation to the unchanged sources and accepted package instead.

## Focused offline verification and stopping point

Executed in Codespace only:

```bash
.venv/bin/python -m pytest -q tests/unit/test_granite_acquisition_proxy.py::test_prior_unknown_cannot_be_loaded_as_zero tests/unit/test_granite_controller_cli.py
```

**5 passed in 0.16s**, exit 0: exact hash/config gates and rejection of incomplete
accounting. The existing synthetic 7-byte fixture establishes contract behavior,
not a historical charge. A separate validation-only probe of the actual preserved
template produced `prior_accounting_unknown` from the proxy and
`native_preflight_failed:prior_accounting_unknown` from the controller. Its
isolated in-memory synthetic configuration was never passed to native execution.
Accepted proxy SHA remains
`a7c62f83356636bea839633382bb62a3e53bcce466caea7b32226cece1e7bb1d`;
frozen configuration SHA remains
`c4610156c24e95cdf1abab658cfde1c18be568940c7cb952c5a673833c620cf4`.

No native calls, network, live proxy, source acquisition, configure/build, compiler,
glslc, GPU/model/inference or ownership rerun occurred. No real execution command
is prepared or authorized. Source, limits, packages, earlier receipts and failed
attempts remain unchanged. Structural success does not establish acquisition/build
readiness, resource fit or model/runtime suitability. Preserve Priority 5 acceptance,
closed Qwen result, inactive real drafts and unconfigured app.main. Priorities 3/4
remain partial; Priority 6/Phase 4 pending. PHASE: 3 / STATUS: in-progress.
Stop for owner review of the missing accounting evidence.
