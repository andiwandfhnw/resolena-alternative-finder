# Admitted-helper snapshot exit reconciliation — 2026-10-27

**Narrow offline follow-up only; execution remains unauthorized.** Owner/advisor
review supports the previous schedules but leaves final handoff-readiness
acceptance pending this count/owned-row finding. The advisor confirmed the previous
controller/diff and preserved definitions without rerunning its entire suite.
The [79-pass receipt](../uc001-granite-default-lifecycle-v1/verification.json),
its controller SHA 790836e62a9489f9ee1ff83591aa72acc1dc185287d5027167b81279fabe7179,
and all historical diagnostic packages/results remain unchanged.

## Direct RED and minimal change

WindowsJob.snapshot reads job state/count before its later owned-handle exit
queries. The new actual-run_session fixture preserves that order: count 1 is
observed, the admitted helper exits, then the owned rows all report zero exits.

Before changing implementation:

```bash
.venv/bin/python -m pytest -q tests/unit/test_granite_controller_run.py::test_default_session_reconciles_admitted_helper_exit_between_snapshot_count_and_owned_rows
```

**1 failed in 0.25s, exit 1**, against the previous controller hash: failure
`active_descendants_after_worker_exit`, one worker launched. This is injected
default-path evidence, not a Windows failure. [Raw RED](snapshot-order-red.log),
[exact command/hash](snapshot-order-red-command.json),
[failure schedule](snapshot-order-red-schedule.json).

Only [controller.py](../../scripts/uc001_granite_controller/controller.py) and the
[existing default-path tests](../../tests/unit/test_granite_controller_run.py)
change, plus docs/TASKS.md and this new receipt. [Source diff](controller.py.diff)
and [test diff](test_granite_controller_run.py.diff) are retained.

The default monitor records when an already admitted helper was observed active
through its retained native process handle. Helper admission itself is unchanged.
Before a count discrepancy can be reconciled, all retained PID/birth, owned-handle
exit, query-handle exit and owned-row evidence must agree. A higher earlier count
is explainable only when its deficit exactly matches newly confirmed exits of
previously observed-active admitted helpers. Each transition is usable once.

The contradictory snapshot always returns **pending**, never permission to build.
The existing supervised loop must obtain a fresh consistent zero-active snapshot
and valid helper exit proofs before advancing. A repeated stale count without new
proof, reversed exit observation, unknown active identity, replaced identity,
missing proof or unexplained discrepancy remains failure. The native count is
never overwritten with the row count. No general mismatch exception or count/name
admission is introduced.

No backend contract change is needed. Existing helper waiting, resource checks,
watchdog, phase clock and final cleanup remain active and unchanged. No grace
allowance, deadline reset, direct helper termination or whole-Job teardown between
phases is added. The backend remains non-atomic; bounded exit reconciliation plus
the later consistent snapshot establishes the phase boundary.

## Focused GREEN and schedules

```bash
.venv/bin/python -m pytest -q tests/unit/test_granite_controller_run.py tests/unit/test_granite_controller_cli.py
```

**92 passed in 2.07s, exit 0** ([raw GREEN](green-final-focused.log),
[exact command](green-final-command.json)): 87 actual-default-file cases, including
the 13 new cases below, plus five existing config/preflight cases. The former 79
passes remain historical; rerun counts are not accumulated. The existing helper-
query-race and unknown-descendant test bodies remain unchanged.

| New default-loop case/group | Required result |
|---|---|
| Helper exits between count and owned rows | Confirm known exit, require a second consistent zero snapshot, then launch build; no direct termination/Job teardown. |
| Unexplained count, active unknown, changed birth | Fail without build; count/name alone supplies no role proof. |
| Missing owned row, unavailable native exit or query proof | Fail without substituting zero or assuming exit. |
| Repeated stale count, unavailable fresh snapshot, exit-state reversal | Fail; do not reuse an exit transition or advance without fresh consistent zero. |
| No prior retained active observation | Reject the proposed exit explanation despite matching count arithmetic. |
| Deadline or disk floor after the contradictory observation | Abort under the original applicable budget, before build. |

The 85-pass intermediate default-file result is separately preserved in
snapshot-green-first.log. The new tests reuse the original lifecycle fixture and
call actual run_session/PhaseMonitor; all native/process/resource/clock boundaries
are injected. No parallel diagnostic or Windows runner is added.

## Hashes, preservation and remaining limits

Current controller SHA-256:
`9c5f3bab58fd3f2d20d345f5093ca2ac80b1e9149da74c1555fcf9b450e92fc1`.
[Current helper/input hashes](helper-hashes.json) are recorded separately from all
historical bindings. Worker, backend, accepted helper-admission code, proxy/prior,
frozen configuration, pins/flags and numerical ceilings remain unchanged.

Both accepted Windows diagnostics remain CLOSED and were not rerun; their passes
do not verify this changed loop. No Windows, live proxy/network, source/model
acquisition, configure/build/compiler/glslc, GPU/server/inference, installation or
Git delivery occurred. No execution draft is activated and no desktop instruction
or handoff package is produced. Resource fit and native behavior remain unverified.
This follow-up is complete for owner review; final handoff-readiness acceptance
remains pending. Priority 5 acceptance, closed Qwen result, inactive real drafts,
unconfigured app.main and reference permissions remain unchanged. Priorities 3/4
partial; Priority 6/Phase 4 pending. PHASE: 3 / STATUS: in-progress. Stop here.
