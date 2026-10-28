# Logging-only transport variant — prepared, not executed

Priority 3 partial; Phase 3 in-progress. No second attempt is authorized or run by
this preparation. The original scripts, failed attempt, setup and frozen execution
bundle remain unchanged.

The [owner-supplied Windows ssh -G summary](ssh-g-owner-report_2026_10_17.json)
records `localhost`, `vscode`, port 49189, address family `any`, and no emitted
proxycommand/proxyjump. It is a supplied summary, not a raw command receipt. No
proxy, IPv4 or server override is justified or applied.

## What the pinned logging can expose

- In gh 2.81.0, [SSH debug/debug-file flags](https://github.com/cli/cli/blob/v2.81.0/pkg/cmd/codespace/ssh.go)
  bind fields that the SSH execution path never consumes; adding them would not
  provide the claimed file. This variant uses `GH_DEBUG=1` only for the owned gh
  child, then restores the parent value even on startup failure. The
  [HTTP client](https://github.com/cli/cli/blob/v2.81.0/api/http_client.go) enables
  nonverbose request metadata; `api` selects verbose HTTP and is deliberately not
  used. Raw URL metadata remains private.
- [OpenSSH 9.5](https://github.com/openssh/openssh-portable/blob/V_9_5_P1/ssh.1)
  supports `-vvv` and `-E <file>`. These expose selected local addresses, connect
  progress, banner/key-exchange/authentication progress and forwarding errors if
  reached. Debug output appends to `ssh-debug.log` in a fresh result directory.
- The [tunnel client receives a discard logger](https://github.com/cli/cli/blob/v2.81.0/internal/codespaces/connection/connection.go).
  The RPC-returned SSH port is passed internally without a target debug print.
  The SSH command returns whichever shell/tunnel completion wins; a shell error
  can obscure a concurrent tunnel error. Ordinary gh stderr may preserve an
  available forwarding error, but these settings **cannot guarantee the broker
  target, RPC response or internal forwarding error**. Do not infer a remote
  target from desktop port 49189. [Pinned source hashes/findings](source-review.json).

## Minimal variant and proposed Windows command

Download only [Test-TransportLogging.ps1](../../scripts/uc001_transport_preparation/Test-TransportLogging.ps1)
next to the already retained `Test-Transport.ps1` and `Probe-Endpoint.ps1` in
`C:\ResolenaExperiments\uc001-transport-check`. It checks both original script
hashes and sources the original flow. It needs the unchanged extracted v1.3.0
bundle. [Hashes](SHA256SUMS.txt) are repository-relative. The new script is 6616
bytes; charge any actual transfer to the existing transport allowance (one copy
would reduce the previously accounted 79023269 bytes to 79016653). No tool/runtime
acquisition is needed or performed here.

**For review only; do not execute in this preparation step.** From an existing
64-bit Windows PowerShell 5.1 console, the proposed command for a separately
authorized single logging-enabled attempt is:

```powershell
& "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -NonInteractive -ExecutionPolicy RemoteSigned -File 'C:\ResolenaExperiments\uc001-transport-check\Test-TransportLogging.ps1' -ExecuteTransportLoggingCheck -BundleDirectory 'C:\ResolenaExperiments\uc001-execution-v1_3_0' -Codespace 'special-disco-vprpp7qrv9xrcwq6p'
```

No-switch execution stops before loading native support. The variant retains
the original ports 49187/49189/49188, random stdin-only probe secret, owned PID and
creation-time checks, loopback/authentication proof, forwarding-failure options,
45-second work guard, two owned five-second exit waits, 60-second overall failure
guard and separate Codespace 49188 cleanup receipt. There is one gh invocation,
the same remote probe and three existing authentication assertions, no extra
probe connection, retry, fallback, model ledger or model budget change.

Future native effects are those of the existing test: compile/load the frozen
`ProcessTools.cs` helper (possible Windows temporary compiler files), create an
owned job, start the endpoint PowerShell and gh/SSH child tree, then close only
that job and require owned exits. This variant additionally sets/verifies an
owner-only inheritable DACL on its fresh GUID result directory before child/log
creation. ACL failure stops startup and retains the original cleanup path. No
launcher initialization, GPU workload, service or SSH configuration action is added.

## Evidence, sharing and the first attempt

Raw `ssh-debug.log`, `transport.stderr.log`, endpoint logs, `result.json` and
`cleanup.json` remain local under the private fresh `results\<GUID>` directory.
Do not share raw logs: URLs, account/key paths or fingerprints can be sensitive.
The probe secret remains on stdin; HTTP bodies are not enabled by GH_DEBUG=1.
No transcript, environment dump, credentials or key contents are collected.

Only `sanitized-summary.json` is printed for sharing. It contains fixed marker
booleans, known outcome, time and cleanup status; no raw lines, errors, URLs,
paths, keys or secrets. Missing/read-failed/over-1-MiB logs remain explicit;
summary reading is bounded and never replaces raw evidence. Markers describe log
observations, not proof of a cause. An absent marker is not proof a stage failed.
The summary always leaves root cause unestablished and remote cleanup pending.

To close the **first** attempt's Windows cleanup evidence, retrieve its already
existing receipt, without rerunning anything:

```text
C:\ResolenaExperiments\uc001-transport-check\results\8c6ce485-2b58-4244-94fb-de1e8d1bb830\cleanup.json
```

It must report owned-job closure, confirmed exits for every recorded owned child
and no errors. It is not yet supplied. The
[separate Codespace receipt](../uc001-transport-setup/setup_2026_10_17_u_qanf5t/forward-cleanup.json)
already passed; absence of port 49188 does not replace the Windows receipt.

[Offline verification](verification.json): meaningful RED/GREEN, exact argument
comparison, privacy/environment failure paths, sanitized synthetic secret/URL
handling and retained transport regressions. Native Windows ACLs, actual gh/SSH
log visibility and transport success remain unverified. GPU/model/semantic gates
remain pending. Stop on missing prerequisites; do not restart or tune anything.
