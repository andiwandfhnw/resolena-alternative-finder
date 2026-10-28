# Execution preparation v1.3.0 — 2026-10-17

Offline implementation only; this package authorizes no model, transport or
dependency execution. Priority 3 remains partial; Phase 3 in-progress. All earlier
bundles, failures and the supplied Windows resource snapshot remain unchanged.

## Correction

Startup and every resource sample use the established v1.2.0 complete native
enumeration, unique intended hardware/CIM/all-PCI/LUID association, DXGI
`DedicatedVideoMemory` capacity and exact corresponding WDDM `phys_0` measurement.
The native reader is byte-identical to v1.2.0. Samples re-read identity and abort
if the selected device/LUID/capacity changes; no remapping or capacity fallback.
Registry data/differences remain diagnostics only.

For an owned server, counter identity must be exactly
`pid_<owned PID>_<selected adapter LUID>_phys_0`. Missing/duplicate/other-physical
instances stop; unrelated PID/adapter rows never supply a measurement. The retained
owned process object's PID, creation time and alive state are checked before and
after sampling. RSS/usage must be nonnegative integers within measured capacities;
null, strings, fractions, negative or excessive values stop. RAM/disk/artifact
measurements also receive strict range/overflow checks.

A measured owned zero is explicitly `measured`, while pre-startup fields with no
owned process are `not_applicable`. Missing owned measurements throw and cannot
become zero. The existing later requirement for positive owned GPU allocation
before the receipt remains. Startup counter availability/instance naming and actual
Windows process-lifetime behaviour remain unverified; absent data aborts immediately,
without grace, retry or fallback.

The native owned-job/process helper is unchanged. Cleanup still closes only the
owned kill-on-close job and confirms owned exits, preserving logs/attempts/assets.
Cleanup errors now cannot skip job closure or later process cleanup; failed closure,
client disposal or exit confirmation is recorded and reported as failure.

## Frozen limits, identity and packaging

Model/runtime pins, config, prompt, schema, 14 exposed cases, synthetic application
composition, controls and semantic-review gate are unchanged. One startup,
14 ordered generations, total/model deadlines 2400/1500 seconds, readiness/request
90 seconds and all original sampling intervals/resource thresholds remain.
The last snapshot's 13099008-byte start margin is not a reservation: fresh asset
integrity, identity and resource validation remain before any authorized startup.

The package has a new freeze SHA for receipts and qualified review. Its
`attempt_identity` retains the original logical key
`bda2015c0ffbe89ab1a612fb4003b2b12f254871cf32f2e47dbbbe9d45cf0f52`.
Windows continues using the original `uc001-contract-runs/<key>` directory: an
existing attempt blocks all versions. Never delete/rename it or reset the budget.
Codespace attempt recording/fsync/order/count enforcement is unchanged. Only
copied Python module references bind the runner to this new frozen directory.
Qualified review must reference this exact new freeze; no approval is fabricated
or transferred from earlier artifacts.

Use the separate `windows-execution-v1_3_0.zip`; extract its entire flat contents
into a fresh directory such as `C:\ResolenaExperiments\uc001-execution-v1_3_0`.
Do not overlay an older/partial extraction. Source lives in the matching Codespace
directory `scripts/uc001_execution_v1_3_0`. `freeze.json` lists file hashes and
unchanged application pins; `VERSION.json` records provenance. Package/hash files
and the full verification record are under `build/uc001-execution-v1_3_0/`.
No live execution command is provided or authorized in this step. The Windows
entry requires explicit `-Execute`; the copied Python runner also requires its
explicit execution flags and qualified review before inference.

## Offline evidence and remaining prerequisites

```bash
.venv/bin/python -m pytest -q tests/unit/test_execution_monitor.py tests/unit/test_preflight_adapter_association.py tests/unit/test_contract_run_controls.py
```

Synthetic checks invoke the actual launcher startup/monitor/abort paths with fake
native reads, job/process operations and HTTP calls. They test missing/invalid
samples, measured zero, foreign/duplicate identities, process exit/change,
runtime resource aborts, preserved attempts and failed cleanup. They start no
model, tunnel or native Windows process. These are not Windows runtime verification.

Still required: actual Windows owned-counter/PID/lifetime/cleanup verification;
desktop OpenSSH/gh/port results; Codespace transport prerequisites and authenticated
loopback forwarding; effective runtime settings/schema/context/prompt fit; qualified
DE/FR/IT/EN review for the exact freeze and later semantic output review. Existing
candidate limitations and English-only synthetic rendering remain unchanged.

On a future authorized Windows run, Add-Type compiles/loads `AdapterIdentity.cs`
and `ProcessTools.cs`; Windows PowerShell 5.1 may leave temporary source/assembly/
compiler files under `%TEMP%`. Native calls include DXGI factory/enumeration/descriptor/
COM release and the unchanged kernel32 job creation/configuration/assignment/close
operations. No compiler is installed automatically. Actual desktop compilation,
native cleanup and resource behaviour are pending, including the strict first
owned-counter sample. No held-out access or real semantic capability is claimed.
