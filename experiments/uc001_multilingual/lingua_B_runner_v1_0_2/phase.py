import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

from common import HERE, ORIGINAL, VERIFIER, OLD_RUN, load_context, deadline, worker_start, write

c = load_context()
phase = sys.argv[sys.argv.index('--phase')+1]
worker_start(c, phase)
root = Path(c['run_dir'])
if phase == 'verify':
    spec = importlib.util.spec_from_file_location('offline_verifier_1_0_1', VERIFIER / 'verify_retained.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    write(root / 'wheel-verification.json', module.verify_retained())
elif phase in ['venv', 'install']:
    if phase == 'venv':
        command = [sys.executable, '-B', '-m', 'venv', '--without-pip', '--symlinks', str(root/'venv')]
    else:
        command = [sys.executable, '-B', '-m', 'pip', '--isolated', '--python', str(root/'venv'),
                   'install', '--no-index', '--find-links', str(OLD_RUN), '--no-deps',
                   '--no-cache-dir', '--no-compile', '--require-hashes', '-r', str(ORIGINAL/'requirements.lock')]
    deadline(c)
    write(root/(phase+'.command.json'), {'command': command, 'deadline_monotonic': c['deadline_monotonic'],
          'limits': c['limits'], 'context': str(root/'context.json'), 'network_sources': []})
    result = subprocess.run(command, timeout=max(.01, c['deadline_monotonic']-time.monotonic()))
    if result.returncode: raise RuntimeError(phase+' failed: '+str(result.returncode))
else:
    raise RuntimeError('Unknown phase')
deadline(c)
