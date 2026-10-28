# Isolated PowerShell 7 checks — 2026-10-14

Owner authorized the Codespace Yarn APT repair and Microsoft-repository PowerShell
installation, followed by isolated offline harness checks. No model execution,
restart, application dependency changes or DESIGN acceptance.

Yarn's existing source already had `signed-by`, but the old keyring lacked the
2026 signing subkey `62D54FD4003F6525`. The official HTTPS key contains fingerprint
`FF7CB5667B542092084BBDC562D54FD4003F6525` under primary
`4EF8150F4F2D7DE44F1DFF0BB42879CC6B38E118`; `gpgv` verifies the fetched InRelease.
The repaired source uses `/etc/apt/keyrings/yarn-archive-keyring.gpg`, mode 0644.
The original `/usr/share/keyrings` key remains unchanged. Both signed APT updates
passed; signature verification was never bypassed and Yarn remains enabled.
Configuration backups, before-state metadata, keys and installation logs remain in
[operation records](../../../../../build/operations/yarn-powershell-20261014/).

PowerShell **7.6.7 Core** was installed from Microsoft's Debian 12 package repository
using its official configuration package and repository-specific signed key.
PowerShell installation upgraded/removed no existing packages. The required
`pwsh -NoLogo -NoProfile -Command '$PSVersionTable'` check passed. This is an
environment tool, not a new application/runtime dependency or Windows installation.
Official instructions: [Yarn](https://classic.yarnpkg.com/lang/en/docs/install/),
[Microsoft](https://learn.microsoft.com/en-us/powershell/scripting/install/install-debian?view=powershell-7.5).

[Test-Isolated.ps1](Test-Isolated.ps1) verifies all frozen payload hashes, parses
nine scripts under PowerShell 7, then loads only `Test-OffloadText` and
`Get-OwnedLiveProcess` from their unchanged frozen AST definitions. It reuses the
frozen Windows regression body with test-only fixture-path adaptation; process
lookup is mocked throughout. Windows startup, guards, sampling, model loading,
cleanup/termination and inference are neither loaded nor invoked.

[Results](results.json): **19/19 passed**. The original Groups error was reproduced;
the corrected function accepts the preserved 37/37 log and rejects missing/partial/
zero evidence. Mocked tests accept matching live or demonstrably ended processes
and reject live PID/start-time/executable or uninspectable identity. Nine scripts
parse under this Core version. These are actual offline PowerShell 7 checks, not
model outcomes or proof of Windows PowerShell 5.1 compatibility.

Still pending: Windows 5.1 parser/runtime, DXGI/WDDM measurements, native Windows
process/exit races, timer/export/protocol execution on Windows, inference and
linguistic validation. The cause of the original watchdog event remains a qualified
shutdown-race explanation; mocked checks cannot recover missing original metadata.
The original ZIPs, freezes, approval/attempt markers and results remain unchanged.
No new inference approval or deadline is created. DESIGN remains in-progress.

Reproduction in the Codespace only, with a new output path:

```bash
pwsh -NoLogo -NoProfile -File experiments/uc001_multilingual/qwen_spike/windows_qwen3_8b_followup_v2_0_1/offline_pwsh7_20261014/Test-Isolated.ps1 -BundleRoot experiments/uc001_multilingual/qwen_spike/windows_qwen3_8b_followup_v2_0_1/execution -Output build/isolated-pwsh7-recheck.json
```

Do not substitute this for the separately packaged Windows offline checks.
