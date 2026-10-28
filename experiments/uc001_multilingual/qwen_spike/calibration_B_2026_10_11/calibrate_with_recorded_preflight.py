"""Future authorized entry point; preserve the original frozen runner and records."""
import hashlib
import json
from pathlib import Path
from memory_preflight import enforce_preflight

HERE = Path(__file__).resolve().parent


def load_runner():
    original = HERE / "calibrate.py"
    expected = json.loads((HERE / "freeze.json").read_text())["files"]["calibrate.py"]
    if hashlib.sha256(original.read_bytes()).hexdigest() != expected:
        raise RuntimeError("Original frozen calibration runner changed")
    source = original.read_text()
    before = ('        if owner.available() < config["preflight_memory_min_bytes"] or '
              'shutil.disk_usage(scratch).free < config["scratch_budget_bytes"]:\n'
              '            raise RuntimeError("Preflight RAM/disk guard")')
    if source.count(before) != 1:
        raise RuntimeError("Expected preflight block absent; do not alter another path")
    source = source.replace(before, "        enforce_preflight(owner.available, config, scratch, write)")
    namespace = {"__file__": str(original), "__name__": "recorded_preflight_runner",
                 "enforce_preflight": enforce_preflight}
    exec(compile(source, str(original), "exec"), namespace)
    return namespace


if __name__ == "__main__":
    raise SystemExit(load_runner()["main"]())
