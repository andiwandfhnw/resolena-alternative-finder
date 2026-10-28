#!/usr/bin/env bash
set -euo pipefail
cd /workspaces/resolena-alternative-finder
PYTHONPATH=src:. .venv/bin/python - <<'PY'
import json, os, shutil
from pathlib import Path
from scripts.uc001_contract_check.controls import load_bundle
bundle = load_bundle()
print(json.dumps({
    'kind': 'read-only Codespace preflight; no connection, installation or inference',
    'freeze_sha256': bundle['freeze_sha256'], 'logical_cpus': os.cpu_count(),
    'memory': [v for v in Path('/proc/meminfo').read_text().splitlines() if v.startswith(('MemTotal:', 'MemAvailable:'))],
    'disk_free_bytes': shutil.disk_usage('.').free,
    'sshd_present': Path('/usr/sbin/sshd').is_file(), 'ssh_client': shutil.which('ssh'),
    'ss': shutil.which('ss'), 'qualified_review': bundle['cases']['qualified_review']['status'],
    'execution_authorized': False,
}, indent=2))
PY
dpkg-query -W -f='${binary:Package} ${Version}\n' openssh-client openssh-server openssh-sftp-server libssl3 libssl-dev openssl libwrap0 runit-helper 2>/dev/null || true
apt-get --simulate --no-install-recommends install \
    openssh-server=1:9.2p1-2+deb12u10 openssh-client=1:9.2p1-2+deb12u10 openssh-sftp-server=1:9.2p1-2+deb12u10 \
    libssl3=3.0.22-1~deb12u1 libssl-dev=3.0.22-1~deb12u1 openssl=3.0.22-1~deb12u1 \
    libwrap0=7.6.q-32 runit-helper=2.15.2
