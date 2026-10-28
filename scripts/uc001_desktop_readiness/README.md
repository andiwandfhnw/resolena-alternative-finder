# Remaining desktop readiness only — 2026-10-16

Priority 3 remains partial; Phase 3 in-progress. The supplied v1.2.0 Windows JSON
is preserved separately as `build/uc001-desktop-readiness/windows-v1_2_0-result.raw.json`.
It verifies adapter identity and one resource snapshot only: GPU free 15045484544
minus the unchanged 15032385536-byte start threshold leaves **13099008 bytes**.
Every threshold stays unchanged. A fresh v1.2.0-policy check is required immediately
before any separately authorized startup; this snapshot is not a future reservation.

## Integrity evidence and remaining check

The reported original `Common.ps1:38` adapter failure occurs after
`Get-ContractAssets` returns in frozen `Preflight-Windows.ps1`. That function checks
the runtime ZIP, model and all **52 extracted runtime files**, stopping on any
missing/size/hash failure. Thus those **54 checks completed historically by
code-order inference**, conditional on the reported unchanged original command/
inputs. No per-file Windows hash receipt was supplied. The closed experiment review
also retains earlier recorded model/runtime/executable verification; it is historical.

No original hash checks remain uncompleted on that evidence. Do not rehash the
8.71 GB model solely to finish the tools/ports check. Neither the v1.2.0 resource
result nor this remaining check proves unchanged present-day asset contents.
Fresh integrity verification remains a prerequisite in a future authorized launcher.
No asset file is opened or hashed by this checker; only the small v1.2.0 preparation
files/manifests are validated against their unchanged freeze.

The single checker uses the complete existing v1.2.0 directory. It reports:

- Existing native `%WINDIR%\System32\OpenSSH\ssh.exe`, its local `-V` output and
  whether PATH resolves that same client. A different PATH client blocks review.
- Existing PATH `gh.exe --version`, requiring the existing **2.81.0** pin.
- Fresh TCP allocations at desktop **49187** (future model listener) and **49189**
  (future gh SSH bridge), with occupied/query-failed states. No bind/connect test;
  no claim about future binds, excluded ports or firewall behaviour.
- Codespace **49188** explicitly not checked: remote localhost is separate.

Only version commands execute, with a five-second limit and cleanup of their own
process on timeout. Both stdout and stderr are captured, including OpenSSH's normal
stderr version banner. No auth/status/token command, credential inspection, network
connection, model/runtime process or resource monitor starts. No installation or
settings change. The remaining check does not repeat GPU queries or native calls.

## Exact Windows instruction

Copy the prepared `scripts/uc001_desktop_readiness/Check-RemainingReadiness.ps1` to
`C:\ResolenaExperiments\diagnostics\Check-RemainingReadiness.ps1`. Preserve the
complete extracted v1.2.0 bundle at the path below. From 64-bit Windows PowerShell
5.1 using the existing process policy:

```powershell
& "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -File C:\ResolenaExperiments\diagnostics\Check-RemainingReadiness.ps1 -BundlePath C:\ResolenaExperiments\uc001-preflight-capacity-v1_2_0
```

`remaining_desktop_checks_passed` covers only the tools/observed ports above.
Failures exit 1. It never means full preflight or interpreter suitability passed.
Retain the printed JSON as a separate readiness result. Use no original preflight
command. No launcher command is provided while the following blocker remains.

## Concrete execution blocker and remaining dependencies

Original `Run-Windows.ps1` still imports its frozen original `Common.ps1`:

- Its `Get-ContractAdapter` checks AMD vendor/name only, without v1.2.0's CIM/all
  PCI/hardware-flag/complete-enumeration/unique-LUID validation. The old native
  reader silently caps enumeration at 32. It does use DXGI dedicated-video bytes;
  it does **not** use the registry equality requirement for launcher capacity.
- Its `Get-ContractResources` uses a loose LUID prefix and casts usage to Int64,
  without v1.2.0's exact corresponding `phys_0`, strict integral/range and
  usage-within-capacity checks. Runtime `Check-Running` calls this older function.

Before execution, a separately reviewed launcher/monitor correction must reuse
the v1.2.0 identity/capacity/usage policy and retain every threshold, fresh startup
check, budgets, receipts and owned-process cleanup. No correction is implemented
or live-execution bundle produced in this task; all frozen versions are preserved.

Also pending: the new Windows tool/port results; Codespace 49188 availability;
approved pinned transport installation/configuration, existing gh authorization
(not inspected here), effective authenticated loopback binding/forwarding and proxy
bypass; actual runtime settings/offload/context/schema/prompt fit; qualified
DE/FR/IT/EN expectation approval before inference and later output semantic review.
The retained candidate's known Spanish route failure is unresolved. An English-only
test renderer does not establish or refute input-language understanding. No
Priority-4 rendering/knowledge work or verified four-language capability is claimed.

Offline checks use existing Codespace PowerShell, mocked Windows queries/tools and
local PowerShell subprocesses to test stderr/exit handling. No actual Windows
tool/port/resource queries, large asset reads, transport or inference occur.
