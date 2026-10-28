# Adapter-association correction v1.1.0

UC-001 Priority 3 remains partial; Phase 3 in-progress. Owner authorized this
bounded preflight correction only. Actual corrected Windows verification is pending.
No model, transport or later-priority work is authorized.

The original `scripts/uc001_contract_check/`, original Windows ZIP and earlier
failure/diagnostic evidence remain unchanged. Extract this separate preflight-only
package into `C:\ResolenaExperiments\uc001-preflight-association-v1_1_0`.
It is not a replacement live-execution bundle; it contains no launcher/runner.

From **64-bit Windows PowerShell 5.1**, run:

```powershell
& "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -File C:\ResolenaExperiments\uc001-preflight-association-v1_1_0\Preflight-Adapter.ps1
```

This checks the small preparation-file hashes, adapter identity and one fresh
resource snapshot. It does **not** call asset hashing, inspect model/runtime asset
files, probe client tools/ports, initialize a launcher or start monitoring. No
installation, policy/driver/settings change, transport or inference is performed.
Use the existing process policy; do not bypass a denial.

## Correction and preserved stops

The old guard required one WDDM adapter-memory instance globally. The supplied
Windows diagnostic identifies the RX 6800 XT and Microsoft Basic Render Driver
separately, with one corresponding counter each. Two global instances do not
establish ambiguous identity for the intended hardware.

The corrected path retains the one-CIM-RX-6800-XT prerequisite and follows its
PNP device to the active registry driver/capacity. It reads DXGI descriptors and
LUIDs afresh, requiring one hardware descriptor with the same full description and
all PCI vendor/device/subsystem/revision identifiers. Software adapters cannot
satisfy that hardware match. It requires a unique LUID across descriptors and
exact agreement between measured DXGI and 64-bit registry capacity.

It then requires exactly one counter belonging to that LUID, with the expected
full `_phys_0` name. Duplicate counters or other physical counters for that LUID
stop. Hex letter case alone is ignored; no observed LUID, enumeration position,
zero/nonzero usage, largest usage, prefix lookalike or guessed capacity selects
an adapter. Resource sampling repeats the exact association against fresh counters.

Missing/invalid/failed/partial CIM, registry, DXGI or WDDM data stops. Numeric
strings/nulls/negative values do not become zero. A measured integer zero remains
valid. Usage above checked capacity, changed PCI identity, descriptor/capacity
disagreement and duplicate identities stop rather than falling back.

`config.json` and `runtime-files.json` are byte-identical copies of the original.
Model/runtime pins, all resource thresholds and inference budgets are unchanged;
original prompt/schema/cases remain untouched and are not duplicated in this ZIP.
In particular: start needs **14 GiB free GPU**, 20 GiB free RAM and 6 GiB free disk;
runtime floors remain GPU2/RAM4/disk5 GiB, owned GPU12/RSS16 GiB caps and the
original artifact limits. This correction does not authorize a run.

The owner-reported sample estimates **13.651 GiB available**, below 14 GiB.
This is a separate resource precondition failure, not the association defect.
That estimate is recorded as reported, not recalculated from an earlier counter
snapshot or claimed current. If fresh data remains below the limit, this command
must return `resource_guard_failed`, with `association=verified`, and exit 1.
Missing association/measurement data also exits 1. `preflight_passed` applies only
to this identity/resource snapshot, not full runtime suitability or language support.

## Native effects and offline evidence

This is **not CIM/registry-only or zero-file-write preparation** on Windows.
`Add-Type` compiles `AdapterIdentity.cs` and loads the assembly into this process.
Windows PowerShell 5.1's compiler may create temporary source/assembly/compiler
files under `%TEMP%`; their actual desktop cleanup is unverified. There is no
explicit output DLL. No compiler/tool is installed automatically.

The minimal reader reuses the separate diagnostic's DXGI 1.1 layout, vtable/delegate
access, unsigned high/low LUID formatting and COM reference release. Native calls
are `CreateDXGIFactory1` (`dxgi.dll`), `EnumAdapters1`, `GetDesc1` and COM release.
No Direct3D device or model is created. The selected capacity is measured, never
assumed to be 16 GiB. The assembly unloads at process exit.

Focused tests use synthetic adapters/CIM/registry/WDDM data and compile C# without
calling its native reader. They cover software/hardware coexistence, order and
usage independence, fresh LUIDs, missing/duplicate/inconsistent/failed data,
zero usage, below/exact headroom and unchanged runtime resource limits. The CLI
test distinguishes valid association from insufficient resources and forbids
asset hashing. Windows PowerShell 5.1 and actual desktop checks remain pending.

Run the offline tests in Codespaces:

```bash
.venv/bin/python -m pytest -q tests/unit/test_preflight_adapter_association.py tests/unit/test_contract_run_controls.py
```

Existing `pwsh` is used if available; absence reports checks as skipped/unverified,
without installing it. Version/change provenance is in `VERSION.json`; the new
`freeze.json` lists this package's hashes. Parent frozen records are preserved.
