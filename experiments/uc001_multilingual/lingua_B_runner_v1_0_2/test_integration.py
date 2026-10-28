import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from common import LIMITS, OLD_RUN, validate_context, check_limits, write, load_context
from runner import phase_commands, monitor, stop_owned


class Integration(unittest.TestCase):
    def test_wiring_uses_new_paths_and_one_context(self):
        root = Path(__file__).resolve().parents[3] / 'build/lingua-b-v1-0-2-20261015'
        commands = phase_commands(root / 'context.json')
        self.assertEqual([n for n, _ in commands], ['verify', 'venv', 'install', 'detector'])
        for _, command in commands:
            self.assertEqual(command[-1], str(root / 'context.json'))
            self.assertNotIn('acquire.py', ' '.join(command))

    def test_context_propagates_limits_and_rejects_old_outputs(self):
        root = Path(__file__).resolve().parents[3] / 'build/lingua-b-v1-0-2-20261015'
        c = {'run_dir': str(root), 'deadline_monotonic': time.monotonic()+60,
             'deadline_wall_unix': time.time()+60, 'limits': LIMITS}
        self.assertEqual(validate_context(c, root / 'context.json')['limits'], LIMITS)
        c['run_dir'] = str(OLD_RUN)
        with self.assertRaisesRegex(RuntimeError, 'output'):
            validate_context(c, root / 'context.json')

    def test_deadline_and_resource_failure_are_enforced(self):
        with self.assertRaisesRegex(RuntimeError, 'deadline'):
            check_limits(2, 2, 0, 0)
        for rss, scratch in [(2**30+1, 0), (0, 2**30+1)]:
            with self.assertRaises(RuntimeError):
                check_limits(1, 2, rss, scratch)

    def test_actual_child_context_receives_exact_deadline_and_limits(self):
        root = Path(__file__).resolve().parents[3] / 'build/lingua-b-v1-0-2-20261015'
        with tempfile.TemporaryDirectory(prefix='offline-check-', dir=root) as directory:
            path=Path(directory)/'context.json'
            c={'run_dir':directory,'deadline_monotonic':time.monotonic()+10,'deadline_wall_unix':time.time()+10,
               'deadline_utc':'synthetic-only','limits':LIMITS,'freeze_sha256':'synthetic-only',
               'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
            write(path,c)
            env=dict(os.environ, LINGUA_CONTEXT_SHA256=hashlib.sha256(path.read_bytes()).hexdigest(),
                     LINGUA_DEADLINE_MONOTONIC=str(c['deadline_monotonic']),LINGUA_LIMITS_JSON=json.dumps(LIMITS))
            code='import sys,json;sys.path.insert(0,'+repr(str(Path(__file__).parent))+');from common import load_context,worker_start;c=load_context();worker_start(c,"synthetic-context");print(json.dumps(c))'
            child=subprocess.run([sys.executable,'-B','-c',code,'--context',str(path)],env=env,capture_output=True,text=True,check=True)
            self.assertEqual(json.loads(child.stdout),c)
            self.assertTrue((path.parent/'synthetic-context.started.json').exists())
            with patch.dict(os.environ,dict(env,LINGUA_DEADLINE_MONOTONIC='0')),patch.object(sys,'argv',['check','--context',str(path)]):
                with self.assertRaisesRegex(RuntimeError,'deadline propagation'):
                    load_context()

    def test_expiry_stops_only_owned_synthetic_process(self):
        root = Path(__file__).resolve().parents[3] / 'build/lingua-b-v1-0-2-20261015'
        with tempfile.TemporaryDirectory(prefix='offline-check-', dir=root) as directory:
            context = {'deadline_monotonic': time.monotonic()+.2, 'deadline_wall_unix': time.time()+.2,
                       'run_dir': directory, 'limits': LIMITS}
            child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(20)'], start_new_session=True)
            try:
                with self.assertRaisesRegex(RuntimeError, 'deadline'):
                    monitor(child, context, 'synthetic-expiry', lambda: {'logical_bytes': 0, 'allocated_bytes': 0})
                self.assertIsNotNone(child.poll())
            finally:
                if child.poll() is None:
                    child.terminate()
                    child.wait()

    def test_operational_failure_preserves_exit_and_returns_failure(self):
        root = Path(__file__).resolve().parents[3] / 'build/lingua-b-v1-0-2-20261015'
        with tempfile.TemporaryDirectory(prefix='offline-check-', dir=root) as directory:
            context = {'deadline_monotonic': time.monotonic()+10, 'deadline_wall_unix': time.time()+10,
                       'run_dir': directory, 'limits': LIMITS}
            child = subprocess.Popen([sys.executable, '-c', 'raise SystemExit(7)'], start_new_session=True)
            with self.assertRaisesRegex(RuntimeError, 'exit 7'):
                monitor(child, context, 'synthetic-failure', lambda: {'logical_bytes': 0, 'allocated_bytes': 0})
            status=json.loads((Path(directory)/'synthetic-failure.exit.json').read_text())
            self.assertEqual(status['exit_code'],7)

    def test_live_ownership_mismatch_cannot_signal(self):
        child = type('Child', (), {'pid': 999999})()
        with patch('runner.process', return_value={'pid': 999999, 'start_ticks': 2, 'pgrp': 999999}), patch('runner.os.killpg') as kill:
            with self.assertRaisesRegex(RuntimeError, 'ownership'):
                stop_owned(child, 1)
            kill.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
