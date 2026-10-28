# Renewed Qwen evaluation — 2026-10-11

One owner-authorized attempt; original parent artifacts remain immutable history.
Run from the repository root with the existing Python environment:

1. `.venv/bin/python -B -m unittest discover -s experiments/uc001_multilingual/qwen_spike/renewed_2026_10_11 -p test_operations.py -v`
2. `.venv/bin/python -B experiments/uc001_multilingual/qwen_spike/renewed_2026_10_11/run.py prepare`
3. `.venv/bin/python -B experiments/uc001_multilingual/qwen_spike/renewed_2026_10_11/run.py evaluate`

The attempt uses the parent pinned acquisition/scoring modules, unchanged prompt,
schema/sampling and frozen cases. New config changes only the authorized start
time. Operational checks are synthetic fake-server/process checks, not model
capability. Readiness is an HTTP health gate, followed by one distinct synthetic
smoke request; evaluation starts only after its response is accepted. No tuning.

Limits and full artifact pins are in config.json; preflight.json records resources,
publisher checksum/tag checks and fingerprints of existing work. A private new
scratch tree under /tmp holds the model, build, caches and Unix socket, with no
TCP listener or forwarding. preparation.json/progress.json record its exact path,
owned process IDs, intended cleanup and gate outcomes. Small JSON records use
atomic replacement; events.jsonl records each stage and started/completed case.

Stop at any startup/smoke failure; preserve diagnostics without another acquisition
cycle. Inference is capped at 60 minutes from load start, within the original
two-hour renewed deadline. Runtime memory/disk guards remain unchanged. Retain
results/configuration/logs before removing only this attempt's verified scratch
tree after owned processes stop. Do not silently renew expired limits.

All inputs and expectations are AI-authored synthetic exploration; no independent
linguistic validation. Request interpretation does not establish narrative-evidence
translation fidelity. DESIGN/ADR-003 acceptance remains pending.
