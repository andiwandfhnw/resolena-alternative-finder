"""Harmless owned Python readiness signal; no HTTP, model, receipt or ledger access."""

import json
from pathlib import Path
import os
import sys


target = Path(sys.argv[1])
temporary = target.with_suffix('.tmp')
temporary.write_text(json.dumps({'pid': os.getpid(), 'parent_pid': os.getppid()}), encoding='utf-8')
os.replace(temporary, target)
sys.stdin.readline()
