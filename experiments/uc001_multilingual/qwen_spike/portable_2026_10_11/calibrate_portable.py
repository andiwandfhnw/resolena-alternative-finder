import hashlib
import json
from pathlib import Path
from memory_preflight import enforce_preflight

HERE = Path(__file__).resolve().parent


def load_runner():
    original = HERE/'calibrate.py'
    freeze = json.loads((HERE/'freeze.json').read_text())
    if hashlib.sha256(original.read_bytes()).hexdigest() != freeze['files']['calibrate.py']:
        raise RuntimeError('Original frozen runner changed')
    execution = json.loads((HERE/'extension_execution.json').read_text())
    source = original.read_text()
    substitutions = [
        ('        if owner.available() < config["preflight_memory_min_bytes"] or shutil.disk_usage(scratch).free < config["scratch_budget_bytes"]:\n            raise RuntimeError("Preflight RAM/disk guard")',
         '        enforce_preflight(owner.available, config, scratch, write)'),
        ('prep = json.loads((PRIOR / "preparation.json").read_text())',
         'prep = json.loads((HERE / "portable_preparation.json").read_text())'),
        ('verification = json.loads((PRIOR / "verification.json").read_text())',
         'verification = json.loads((HERE / "portable_verification.json").read_text())'),
        ('workspace = REPO / "build/qwen-calibration-B-20261011"',
         'workspace = Path(prep["portable_root"]) / "runtime"'),
        ('started = time.time(); deadline = started + 900',
         'started = time.time(); deadline = min(started + 900, extension_deadline)'),
        ('        runtime_args[runtime_args.index("-o") + 1] = str(workspace / "network.trace")',
         '        runtime_args[runtime_args.index(prep["original_server"])] = prep["server"]\n        runtime_args[runtime_args.index("-o") + 1] = str(workspace / "network.trace")'),
        ('for root in [scratch, workspace, HERE]',
         'for root in [scratch, Path(prep["portable_root"]), HERE]')]
    for before,after in substitutions:
        if source.count(before) != 1:
            raise RuntimeError('Expected operational substitution absent')
        source = source.replace(before,after)
    namespace = {'__file__':str(original), '__name__':'portable_calibration_runner',
                 'enforce_preflight':enforce_preflight, 'extension_deadline':execution['deadline_epoch']}
    exec(compile(source,str(original),'exec'),namespace)
    return namespace


if __name__ == '__main__':
    raise RuntimeError('Execute only through the one-shot extension driver')
