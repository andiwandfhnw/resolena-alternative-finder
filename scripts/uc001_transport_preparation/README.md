# Transport preparation — review only, 2026-10-17

No installation, authentication or connection below has been executed. Priority 3
remains partial; Phase 3 in-progress. Frozen v1.3.0 and all model-attempt budgets
are unchanged. The separate supplied Windows native check passed its tested
identity/abort/job-close/exit path in 919 ms; this proves neither GPU monitoring
nor model readiness.

Read-only Codespace inspection: Debian 12 amd64, current name
`special-disco-vprpp7qrv9xrcwq6p`; no observed TCP allocations at 49188; existing
OpenSSH client `1:9.2p1-2+deb12u6`, but `/usr/sbin/sshd` and server configuration
are absent. `ss`, `timeout`, Python/httpx are available. Windows native OpenSSH
9.5p2/LibreSSL 3.8.2, portable gh 2.81.0 and the earlier port observations are
reused, not investigated again. Fresh bind guards still run during a future test.

The cached solver and SHA-256/size/version metadata match the unchanged
`../uc001_execution_v1_3_0/transport-plan.json`: four new packages, four updates,
no removals, about 2,222 kB additional installed space. Cached metadata is not proof
that mirrors will still serve these archives. A missing/changed pin stops; no
index refresh, substitute version, extra package or automatic retry is approved.

| Package | Exact version | Download bytes |
|---|---|---:|
| openssh-server | 1:9.2p1-2+deb12u10 | 456,584 |
| openssh-client | 1:9.2p1-2+deb12u10 | 993,532 |
| openssh-sftp-server | 1:9.2p1-2+deb12u10 | 65,928 |
| libssl3 | 3.0.22-1~deb12u1 | 2,039,240 |
| libssl-dev | 3.0.22-1~deb12u1 | 2,449,908 |
| openssl | 3.0.22-1~deb12u1 | 1,442,052 |
| libwrap0 | 7.6.q-32 | 54,936 |
| runit-helper | 2.15.2 | 6,520 |
| **Remaining Debian acquisition** | | **7,508,700** |

The original **100 MiB = 104,857,600 bytes** cap includes the completed portable
gh archive acquisition, **18,317,085 bytes**. Remaining before Debian acquisition:
**86,540,515 bytes**; after the eight pinned archives: **79,031,815 bytes**.
Charge any additional transport transfers against that remainder. The two prepared
Windows scripts total **8,546 bytes**; one copy leaves **79,023,269 bytes** after
the planned archives. These figures account for the stated acquisitions, not an
assumption that unreported downloads were free. No gh
reinstallation, Linux gh, SSH feature download, model/runtime download or rebuild
is proposed. Existing OpenSSL consumers may need a separately agreed restart;
do not restart the editor/application, current work or workstation automatically.

**Codespaces Bash — only after setup approval.** Keep this shell open through
verification/install; do not rerun downloads or remove earlier staging directories.
The existing root-owned executable `/usr/sbin/policy-rc.d` already returns 101 and
must remain unchanged. Stop if its fingerprint/state differs. This prevents Debian
service autostart; provider-managed SSH startup is a separate connection effect.

```bash
set -euo pipefail
cd /workspaces/resolena-alternative-finder
test -x /usr/sbin/policy-rc.d
test "$(stat -c %u /usr/sbin/policy-rc.d)" = 0
printf '%s  %s\n' 21a8dca0d6a52cbac52cb7a86178d973616ffb42ea08747e6ff311659ab095e1 /usr/sbin/policy-rc.d | sha256sum --check --status
specs=(openssh-server=1:9.2p1-2+deb12u10 openssh-client=1:9.2p1-2+deb12u10
  openssh-sftp-server=1:9.2p1-2+deb12u10 libssl3=3.0.22-1~deb12u1
  libssl-dev=3.0.22-1~deb12u1 openssl=3.0.22-1~deb12u1
  libwrap0=7.6.q-32 runit-helper=2.15.2)
apt-get --simulate --no-install-recommends install "${specs[@]}"
apt-get --print-uris --yes --download-only --no-install-recommends install "${specs[@]}"
# STOP for any difference from the eight versions/archives/sizes above and frozen hashes.
# After that review, and only with download/installation approval:
package_dir=$(mktemp -d /tmp/uc001-transport-debs.XXXXXX)
chmod 755 "$package_dir"
sudo apt-get --yes --download-only --no-install-recommends \
  -o Acquire::Retries=0 -o Acquire::http::Timeout=15 \
  -o Dir::Cache::archives="$package_dir/" install "${specs[@]}"
.venv/bin/python - "$package_dir" <<'PY'
from pathlib import Path
from hashlib import sha256
import json, subprocess, sys
plan=json.loads(Path('scripts/uc001_execution_v1_3_0/transport-plan.json').read_text())
expected={p['Package']:p for p in plan['codespace_packages']}; seen=set()
files=list(Path(sys.argv[1]).glob('*.deb'))
assert len(files)==len(expected)==8, 'Unexpected archive count; do not install'
for path in files:
    package=subprocess.check_output(['dpkg-deb','-f',str(path),'Package'],text=True).strip()
    version=subprocess.check_output(['dpkg-deb','-f',str(path),'Version'],text=True).strip()
    assert package in expected and package not in seen, 'Unknown/duplicate package'
    p=expected[package]
    assert version==p['Version'] and path.stat().st_size==p['Size']
    assert sha256(path.read_bytes()).hexdigest()==p['SHA256'], 'Archive hash mismatch'
    seen.add(package)
assert seen==set(expected)
assert sum(p.stat().st_size for p in files)==7508700
print('Eight pinned transport archives verified; no installation performed by this check')
PY
sudo env DEBIAN_FRONTEND=noninteractive dpkg -i "$package_dir"/*.deb
# Keep the staging directory and receipts; no service start/rebuild/reboot command.
```

Package configuration creates normal OpenSSH host keys; do not inspect/print them.
Prepare the already planned restrictive drop-in; never overwrite an existing one:

```bash
sudo test ! -e /etc/ssh/sshd_config.d/00-uc001-contract.conf
sudo install -d -m 755 /etc/ssh/sshd_config.d /run/sshd
sudo tee /etc/ssh/sshd_config.d/00-uc001-contract.conf >/dev/null <<'EOF'
ListenAddress 127.0.0.1
GatewayPorts no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
AllowTcpForwarding remote
PermitListen 127.0.0.1:49188
EOF
sudo /usr/sbin/sshd -t
sudo /usr/sbin/sshd -T -C user=vscode,addr=127.0.0.1,host=localhost |
  awk '$1 ~ /^(listenaddress|gatewayports|passwordauthentication|kbdinteractiveauthentication|pubkeyauthentication|allowtcpforwarding|permitlisten)$/ {print}'
```

Require only loopback ListenAddress, GatewayPorts=no, password/interactive=no,
public key=yes, forwarding=remote and PermitListen=127.0.0.1:49188. This checks
default configuration only. gh requests server startup through the Codespaces RPC;
that implementation/configuration is not verified here. The connection test must
inspect the actual SSH port from SSH_CONNECTION and its live listeners, plus the
reverse listener. If the provider ignores/overrides these settings or binds a
wildcard, stop and preserve evidence. No wrapper, configuration replacement,
shared-daemon termination or guard relaxation is authorized as a workaround.

**Windows PowerShell 5.1 — authentication proposal, not executed.** Reuse existing
approved portable gh and native OpenSSH; use the owner's existing account if it
already has Codespaces access. If browser login/additional scope is necessary,
the proposed owner-operated command is:

```powershell
& 'C:\ResolenaExperiments\tools\gh-2.81.0\bin\gh.exe' auth login --hostname github.com --web --git-protocol https --scopes codespace --skip-ssh-key
```

For an already authenticated account needing only scope, use `auth refresh
--hostname github.com --scopes codespace` instead, after review. No tokens are
requested, read or printed here. Login uses the OS credential store; gh documents
a plaintext fallback if secure storage fails, which the owner must not accept
without a separate decision. Codespace SSH may select/create `~/.ssh/codespaces.auto`
and its public key and authorize that public key remotely. These persistent
authentication effects require approval; do not display/delete private keys or
rewrite global SSH configuration. gh's localhost SSH host-check behavior relies
on its authenticated GitHub broker; this is not independently pinned SSH host-key
verification. No authentication status/token inspection has been run.

**Bounded model-free connection validation — only after transport approval.**
Copy `Test-Transport.ps1` and `Probe-Endpoint.ps1` into a fresh Windows directory
`C:\ResolenaExperiments\uc001-transport-check`. Keep `probe_forward.py` at its
current Codespace path; do not run either frozen model launcher/runner. First set
this test shell's native SSH path so gh uses the recorded Windows client:

```powershell
$env:PATH = "$env:WINDIR\System32\OpenSSH;" + $env:PATH
& "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -NonInteractive -ExecutionPolicy RemoteSigned -File 'C:\ResolenaExperiments\uc001-transport-check\Test-Transport.ps1' -ExecuteTransportCheck -Codespace 'special-disco-vprpp7qrv9xrcwq6p' -BundleDirectory 'C:\ResolenaExperiments\uc001-execution-v1_3_0'
```

The wrapper owns the test endpoint and this exact connection (shown for review;
stdin/key delivery and cleanup belong to the wrapper):

```powershell
& 'C:\ResolenaExperiments\tools\gh-2.81.0\bin\gh.exe' codespace ssh --codespace 'special-disco-vprpp7qrv9xrcwq6p' --server-port 49189 -- -T -o BatchMode=yes -o ExitOnForwardFailure=yes -o ServerAliveInterval=5 -o ServerAliveCountMax=2 -o ConnectTimeout=15 -R '127.0.0.1:49188:127.0.0.1:49187' 'cd /workspaces/resolena-alternative-finder && timeout --signal=TERM --kill-after=5s 35s env PYTHONPATH=src:. .venv/bin/python scripts/uc001_transport_preparation/probe_forward.py'
```

49189 is the **desktop gh bridge**, not the remote sshd port. Windows and Codespace
localhost are separate. The fixed test endpoint is exclusively desktop
127.0.0.1:49187; the reverse listener must be exactly Codespace 127.0.0.1:49188.
The existing v1.3.0 listener validator also requires the actual session sshd
listener to be loopback. Windows checks endpoint/bridge PID and creation time.
The ephemeral test secret travels only through owned stdin; the test HTTP client
disables proxies/redirects. Missing/wrong authentication must return 401 and the
right key must return 200 with the exact probe body. No public health response is
authentication evidence. This synthetic endpoint proves transport only.

One connection; no repair/retry/fallback. The Windows 45-second work deadline plus
the unchanged two five-second owned-exit waits leaves five seconds within a
60-second overall test budget. Remote Python has a 30-second alarm, wrapped in
35-second timeout with five-second forced termination. Closing only the owned
kill-on-close job terminates its endpoint/gh/SSH subtree and verifies owned exits;
failed closure, unconfirmed exits or remaining Windows test listeners fail.
The existing C# process helper is compiled via Add-Type (possible TEMP compiler
files); test endpoint sockets/native job/process calls occur only after approval.
Results/logs/cleanup remain under a fresh Windows `results/<GUID>` directory.
No model ledger, generation, resource acceptance or GPU measurement is involved.

After Windows reports success, require this separate **Codespaces Bash** cleanup
check from the existing IDE terminal; no second SSH connection:

```bash
python3 - <<'PY'
import subprocess, time
deadline=time.monotonic()+5
while True:
    rows=subprocess.run(['ss','-H','-lntp','sport = :49188'],capture_output=True,text=True,check=True,timeout=1).stdout.strip()
    if not rows:
        print('{"outcome":"codespace_forward_cleanup_passed","port":49188}')
        break
    if time.monotonic()>=deadline:
        raise SystemExit('49188 listener remains; preserve evidence, stop without killing its owner')
    time.sleep(.1)
PY
```

Both results are needed. Provider-managed sshd may persist independently; never
kill a daemon by name, delete shared keys/configuration, or stop the Codespace.
Real listener/configuration/lifecycle compatibility remains a connection gate;
no successful connection, full preflight, GPU allocation or semantic suitability
is claimed. Qualified review and fresh startup integrity/resources still remain.

Primary references: [pinned gh SSH startup/bridge](https://github.com/cli/cli/blob/v2.81.0/pkg/cmd/codespace/ssh.go),
[pinned SSH client behavior](https://github.com/cli/cli/blob/v2.81.0/internal/codespaces/ssh.go),
[authentication effects](https://cli.github.com/manual/gh_auth_login),
[forwarding controls](https://man.openbsd.org/sshd_config).
