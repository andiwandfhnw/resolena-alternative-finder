# Default native-controller lifecycle correction — 2026-10-27

**Offline correction only; execution remains unauthorized.** The owner accepts
the source-grounded diagnosis and authorizes the bounded work in
[owner-authorization.txt](owner-authorization.txt). This receipt records new RED
and GREEN through the actual `controller.run_session`, independently of the
historical diagnostic reproductions and accepted Windows passes. Both successful
Windows diagnostics remain CLOSED; their packages/results are unchanged and
neither diagnostic nor its suite was rerun.

## Minimal changes

- [controller.py](../../scripts/uc001_granite_controller/controller.py): optional
  exit-observation reconciliation in the real monitor/loop; retention of the
  already admitted proxy helpers' owned process handles; strict phase-end helper
  waiting. [Exact source diff](controller.py.diff).
- [test_granite_controller_run.py](../../tests/unit/test_granite_controller_run.py):
  28 focused injected cases using the existing actual-default-path fixtures.
  All original test bodies, including unknown-descendant rejection, are preserved.
  [Exact test diff](test_granite_controller_run.py.diff).
- [test_granite_controller_cli.py](../../tests/unit/test_granite_controller_cli.py):
  correct the stale fixture's directory-wide Python glob to the existing canonical
  four-helper contract; verify that a diagnostic helper cannot expand that manifest.
  No production configuration rule changes.
- docs/TASKS.md records the bounded result. No worker, backend, stand-in/helper
  admission policy, accepted proxy/prior, frozen assessment, pin/flag or limit changes.

## Actual default-path RED → GREEN

Before changing controller.py, execute the following exact selector
([command/exit receipt](default-positive-red-command.json),
[raw RED](default-positive-red.log), [observed schedules](default-positive-red-schedules.json)):

```bash
.venv/bin/python -m pytest -q tests/unit/test_granite_controller_run.py -k 'default_session_reconciles_durable_close_after_read_before_observed_proxy_exit or default_session_waits_only_for_already_verified_helper_before_build'
```

**3 failed, 46 deselected, exit 1**: worker-alive and worker-exited schedules
both rejected `proxy_launcher_premature_exit`; admitted-helper lag rejected
`active_descendants_after_worker_exit`. No build worker was launched in those REDs.

Review then exposed a separate helper completing between the owned-handle exit
query and the query-handle readback. Its actual-default-path RED is retained:

```bash
.venv/bin/python -m pytest -q tests/unit/test_granite_controller_run.py::test_default_session_reconciles_verified_helper_exit_between_native_queries
```

**1 failed, exit 1** ([raw RED](default-helper-query-race-red.log)). The correction
makes one immediate retained-owned-handle recheck and requires exact matching exit
evidence; it never reopens a PID or waits for missing proof to become acceptable.

Final focused invocation:

```bash
.venv/bin/python -m pytest -q tests/unit/test_granite_controller_run.py tests/unit/test_granite_controller_cli.py
```

**79 passed in 1.22s, exit 0** ([raw GREEN](green-final-focused-corrected.log),
[exact command](green-final-command-corrected.json)): 46 original default-loop/
monitor cases, 28 new actual-loop cases and five config/preflight cases. A previous
combined attempt was **77 passed / 1 failed** because the stale config fixture
included later diagnostic files in its four-helper map; that failure remains in
green-final-focused.log. No manifest acceptance was relaxed to fix it.
The log named default-negative-baseline.log is explicitly classified in its JSON
receipt as **post-correction intermediate GREEN**, not pre-fix baseline evidence.
Historical run_binding_session REDs retain their original scope and are not counted
as this task's default-path reproductions. No aggregate total across reruns is claimed.

## Schedules covered by each new default-loop test

| Test suffix (all prefixed `test_default_session_`) | Cases and event/process schedule |
|---|---|
| `reconciles_durable_close_after_read_before_observed_proxy_exit` | 3: valid close becomes durable after initial read; worker remains alive, worker exits, or proxy exits after the initial native precheck. Correct ordered close/native role evidence is consumed before rejection; the build advances only after terminal validation. |
| `waits_only_for_already_verified_helper_before_build` | 1: both proxy roles and phase worker have completed; the monitor-admitted helper is still active, then exits during supervised phase waiting. Build starts after zero active; no Job cleanup/close occurs between phases and no direct process termination occurs. |
| `reconciles_verified_helper_exit_between_native_queries` | 1: retained owned query reports active, helper exits, query-only handle reports zero; one bounded native recheck establishes the same exit. |
| `durable_exit_reconciliation_never_accepts_invalid_lifecycle` | 7: absent/mismatched/malformed/out-of-order close; genuine premature launcher/interpreter exit; unsuccessful proxy exit. One close reconciliation read, failure and no build. |
| `wait_rejects_unknown_changed_or_unproven_helper` | 7: unknown remaining PID, helper birth change, wrong membership, timeout, inconsistent exit proof, wrong retained PID and failed image query. Count/name alone never admits a helper. |
| `final_cleanup_proof_remains_mandatory` | 2: missing helper identity-bound final exit or query-handle closure failure prevents success. |
| `deadlines_and_resources_remain_active_during_exit_handling` | 4: phase deadline or disk-floor breach during event reconciliation or helper waiting aborts the owned Job without build advancement. |
| `reconciled_exit_still_requires_original_accounting_and_interpreter_ledger` | 3: wrong prior charge, cumulative charge or listening PID cannot be accepted. The positive synthetic ledger uses actual BudgetLedger records, prior 7 + debit 2 = cumulative 9, bound to interpreter PID rather than launcher. |

## Phase-boundary and final-cleanup semantics

The real loop observes worker/proxy native exit before making **one immediate
ordered event reread per loop iteration**. Proxy polling checks again after
retained metadata queries to cover an exit between native observations. Resource/
deadline/watchdog checks bracket the reread. Missing or invalid close still fails
immediately: no arbitrary sleep, event grace period or exception suppression.
Worker-alive reconciliation does not require acquisition terminal records early;
the remaining source checks may finish under the unchanged phase budget.

After native zero worker exit, terminal/child/role/ledger evidence must validate
before helper waiting. The helper registry comes from the default PhaseMonitor's
existing accepted `_check_console_shape` path and retained owned/query handles,
not the diagnostic WorkerBranch registry. No new helper roles are admitted.
Unclassified worker-launcher helpers or other descendants remain failures.

Active snapshot PID/birth identities must be a subset of that registry, matching
the active count. Retained identity, native/query exit agreement and live parent/
private-Job/system-path checks remain mandatory. Even count zero cannot bypass a
registered helper's exit proof. Sampler/watchdog and the same applicable phase
clock remain active throughout; no time/resource allowance is added. Only after
zero active processes may the build worker launch. The private Job remains intact.

Final Job cleanup, exact role/helper exits and query-handle closure are still
required; failed final proof cannot report success even if build work finished.
Genuine failures use the existing abort/Job cleanup path. Helpers and unknown
children gain no direct termination authority. No changed event order, identity
rules, proxy algorithm, numeric ceilings or cumulative accounting is introduced.

## Current hashes, limits and stopping point

Current controller SHA-256:
`790836e62a9489f9ee1ff83591aa72acc1dc185287d5027167b81279fabe7179`.
[All current helper/input hashes](helper-hashes.json) separately bind the changed
source. Historical packages/prior preparation bindings remain untouched; existing
execution templates remain inactive and must not be treated as current-hash drafts.
No new package, Windows runner or desktop execution instruction is produced.

Evidence is injected offline behavior of the actual default loop. No Windows
verification of the changed source, native process/socket journey, proxy/network,
source/model acquisition, compiler/glslc/configure/build, GPU/server/inference,
installation or Git delivery occurred. Closed diagnostic/backend suites and
application/model/broad matrices were excluded. Resource fit stays unverified.

The two identified lifecycle cases now pass in the actual default path; the source
therefore permits completion of the previously authorized **inactive handoff
preparation after owner review**. This task stops without assembling that handoff,
activating a configuration or claiming acquisition/build/model readiness. Priority 5
acceptance, closed Qwen result, unconfigured app.main, inactive real drafts and
reference permissions remain. Priorities 3/4 partial; Priority 6/Phase 4 pending.
PHASE: 3 / STATUS: in-progress. Stop for owner review.
