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
