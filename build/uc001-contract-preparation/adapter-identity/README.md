# Separate DXGI/WDDM identity diagnostic

Preparation only, 2026-10-16. Frozen preflight, launcher, bundle and original ZIP
are unchanged. Do not run the launcher or preflight for this diagnostic.

The owner-supplied CIM/registry diagnostic establishes one RX 6800 XT, present
64-bit registry capacity, and two WDDM `phys_0` instances with distinct LUIDs.
The guard's multiple-instance branch is confirmed. Counter-to-adapter identity,
software/hardware classification and current headroom are not established by that
snapshot; usage magnitude, including zero, cannot choose an identity.

Copy **only** `Diagnose-DxgiWddmIdentity.ps1` to
`C:\ResolenaExperiments\diagnostics\Diagnose-DxgiWddmIdentity.ps1`, outside the frozen
bundle. From the existing Windows PowerShell 5.1 session run:

```powershell
powershell.exe -NoProfile -File C:\ResolenaExperiments\diagnostics\Diagnose-DxgiWddmIdentity.ps1
```

Use existing 64-bit Windows PowerShell 5.1. No execution-policy change, elevation,
installation or downloaded dependency is requested. If existing policy denies
compilation/native calls, the diagnostic must report failure; do not bypass policy.

This **is a native diagnostic**. `Add-Type` compiles embedded C# and loads its
assembly into the diagnostic process. Windows PowerShell 5.1's compiler can create
temporary source/assembly/compiler files under `%TEMP%`; this is not a promise of
zero filesystem writes. There is no explicit output DLL, report file or cache
created by the script. Do not claim that compiler temporary-file cleanup was
verified on this desktop. The assembly unloads when the process exits.

It calls native `CreateDXGIFactory1` in `dxgi.dll`, then COM `EnumAdapters1` and
`GetDesc1`, and releases the adapter/factory references. It reads descriptions,
PCI/ACPI IDs, type flags and LUIDs. This reuses the launcher's descriptor layout,
delegate/vtable access, reference release and unsigned high/low LUID formatting;
DXGI 1.1 adds the required software flag. It does not source Common.ps1 or launch
any server, create a Direct3D device, run compute, start monitoring or access assets.

Each adapter reports description, vendor/device/subsystem/revision IDs, raw flags,
software/hardware classification and LUID. Enumeration index is informational and
never used to select an adapter. The freshly queried WDDM names are joined by
**exact full name**, ignoring only hex letter case, against each discovered LUID's
`_phys_0` name, matching the frozen guard's physical-index expectation.
Other physical indexes remain visible as unmatched, not silently accepted.
All counter names/usage remain visible, including unmatched rows; no hard-coded
desktop LUID or use of usage magnitude appears in the diagnostic.

`identity_state` preserves duplicate DXGI LUIDs; `counter_state` preserves missing,
single, ambiguous and failed-query states. Missing/null usage is separate from zero.
Native enumeration and per-adapter descriptor failures remain explicit, including
partial results; unmatched counters are unresolved, not declared stale or software.
The snapshots have UTC start times. A match provides identity evidence, not proof of
resource headroom, residency, model suitability or permission to change the guard.

Offline validation used existing Linux `pwsh`: PowerShell AST, C# compilation,
x64 structure size/offsets, unsigned LUID formatting and synthetic checks for exact
matches, lookalikes, hardware/software flags, zero/nonzero values, duplicate
identities/counters, unmatched physical index, missing/null usage and failed queries.
No native reader or real Windows query was invoked. Windows PowerShell 5.1 execution,
compiler behavior and actual identity associations await the returned output.
No unrelated regression checks, model hashes, downloads, installs, driver/settings
changes, transport, inference or held-out access occurred. Priority 3 is partial;
Phase 3 remains in-progress. Stop after preparing this diagnostic.

API/layout references: [adapter descriptor](https://learn.microsoft.com/en-us/windows/win32/api/dxgi/ns-dxgi-dxgi_adapter_desc1),
[software flag](https://learn.microsoft.com/en-us/windows/win32/api/dxgi/ne-dxgi-dxgi_adapter_flag),
[adapter enumeration](https://learn.microsoft.com/en-us/windows/win32/api/dxgi/nf-dxgi-idxgifactory1-enumadapters1),
[SDK interface declarations](https://github.com/microsoft/win32metadata/blob/main/generation/WinSDK/RecompiledIdlHeaders/shared/dxgi.h).
