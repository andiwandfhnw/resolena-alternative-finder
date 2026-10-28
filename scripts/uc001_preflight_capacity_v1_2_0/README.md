# DXGI capacity-source correction v1.2.0

Separate adapter/resource preflight only. Priority 3 remains partial; Phase 3
in-progress. Actual Windows verification is pending. No transport/model execution
is authorized. Original and v1.1.0 source, ZIPs and evidence remain unchanged.

## Capacity and diagnostics

`DedicatedBytes` comes solely from the uniquely identified hardware adapter's
`DXGI_ADAPTER_DESC1.DedicatedVideoMemory` (`UIntPtr.ToUInt64()`). The unsupported
exact-equality requirement with registry `HardwareInformation.qwMemorySize` is
removed. No tolerance, rounding, min/max selection, nominal capacity or fallback.
DXGI capacity must be a positive integral value within the existing signed-64-bit
resource arithmetic range; missing/invalid capacity still stops.

`CapacitySource` names the DXGI field. `RegistryCapacity` retains the same CIM-PNP
device/driver path, availability/error state, raw value/type, decoded decimal bytes
and exact signed `DifferenceBytes` (DXGI minus registry, BigInteger decimal string).
Missing/unreadable/invalid registry data remains visible without replacing DXGI
or preventing an otherwise valid DXGI association. Identity still requires the
unique hardware descriptor, all PCI identifiers, fresh unique LUID and exactly
one corresponding WDDM `phys_0` counter. Measured zero usage is valid; missing,
invalid, duplicate or inconsistent identity/usage stops.

Owner-supplied diagnostic excerpt, preserved separately under
`build/uc001-preflight-capacity-v1_2_0/owner-supplied-diagnostic.txt`:
DXGI **17130819584**, registry **17163091968**, difference **-32272384 bytes**.
Matching CIM/PCI/DXGI identity is owner-reported; a complete diagnostic JSON was
not supplied in this turn. The cause of the difference remains unknown.

All thresholds and inference budgets are unchanged. Start requires 14 GiB free
GPU, 20 GiB free RAM and 6 GiB free disk. Runtime floors remain GPU2/RAM4/disk5
GiB; owned GPU12/RSS16 GiB and original artifact caps remain. `config.json`,
`runtime-files.json`, native reader and resource-guard function are unchanged from
v1.1.0. Prompt/schema/cases remain in the preserved original bundle.

## Windows: download and full extraction

Download `build/uc001-preflight-capacity-v1_2_0/windows-preflight-capacity-v1_2_0.zip`
from the Codespace to your Windows Downloads folder. Extract the **whole ZIP** to
a fresh directory, keeping all nine files together. Do not copy only the entry
script or overlay an earlier/partial extraction. From 64-bit Windows PowerShell 5.1:

```powershell
$capacityZip = Join-Path $env:USERPROFILE 'Downloads\windows-preflight-capacity-v1_2_0.zip'
$capacityDir = 'C:\ResolenaExperiments\uc001-preflight-capacity-v1_2_0'
if (-not (Test-Path -LiteralPath $capacityZip -PathType Leaf)) { throw 'Download the full v1.2.0 ZIP first.' }
if (Test-Path -LiteralPath $capacityDir) { throw 'Destination exists; preserve it and use a fresh extraction directory.' }
Expand-Archive -LiteralPath $capacityZip -DestinationPath $capacityDir -ErrorAction Stop
$capacityFiles = @('AdapterIdentity.cs','Common.ps1','Preflight-Adapter.ps1','README.md','Test-Offline.ps1','VERSION.json','config.json','runtime-files.json','freeze.json')
foreach ($capacityFile in $capacityFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $capacityDir $capacityFile) -PathType Leaf)) { throw ('Incomplete extraction: '+$capacityFile) }
}
& "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -File (Join-Path $capacityDir 'Preflight-Adapter.ps1')
```

If downloaded elsewhere, change only `$capacityZip`. This block writes only the
new extraction; it deletes nothing. Existing process policy applies; no policy
change or bypass is included. The entry verifies all small frozen package-file
hashes, then checks identity and one fresh resource snapshot. It never hashes
model/runtime assets, probes tools/ports or initializes a launcher/monitor.

`preflight_passed` means only this identity/resource snapshot passed. Association,
measurement or resource failure exits 1 and retains the guard error in JSON.
Insufficient headroom still yields `resource_guard_failed` with a verified
association; no fresh headroom is assumed from earlier snapshots.

## Native effects and offline checks

`Add-Type` compiles/loads the unchanged `AdapterIdentity.cs` if needed; Windows
PowerShell 5.1 may create source/assembly/compiler files under `%TEMP%`. Desktop
temporary-file cleanup remains unverified. System.Numerics is loaded for exact
diagnostic arithmetic. Native calls remain `CreateDXGIFactory1` (`dxgi.dll`),
`EnumAdapters1`, `GetDesc1` and COM release. No Direct3D device/model is created;
no compiler/tool is installed automatically. This is not CIM/registry-only.

Codespaces Bash, using existing PowerShell if available:

```bash
.venv/bin/python -m pytest -q tests/unit/test_preflight_adapter_association.py tests/unit/test_contract_run_controls.py
```

Tests use synthetic CIM/registry/DXGI/WDDM data and compile/layout checks without
native enumeration. They cover unequal readings in both directions, registry
availability, invalid DXGI capacity, unchanged identity/counter failures, zero
usage, byte-exact thresholds and earlier association/run-control regressions.
Absent PowerShell means explicit skips/unverified, without installation.
Version/change provenance is in `VERSION.json`; hashes are in `freeze.json` and
the separate artifact `SHA256SUMS.txt`. Windows execution/compatibility is pending.
