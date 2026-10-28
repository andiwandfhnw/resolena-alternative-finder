# Windows Qwen3-8B v2 execution bundle — harness 2.0.1

Prepared under the owner's **2026-10-14 bundle-preparation/offline-check authorization
only**. Windows inference is not authorized. DESIGN and qualified linguistic
validation remain pending. No Python, download, installation or remote access is
required on Windows. Reuse verified artifacts from the completed v1 experiment;
do not edit v1 or delete its markers/results. Supported scope is DE/FR/IT/EN only;
Spanish cases are unsupported-language negative controls for limitation/rephrasing.

Harness 2.0.1 repairs the closed 2.0.0 attempt’s offload `$Matches` collision and
shutdown-race handling. The evaluation/configuration/receipt protocol remains 2.0.0,
with byte-identical prompts, cases, requests, schema, scoring, settings and limits.
The original attempt/freeze/approval/markers are preserved. Use this new folder;
do not copy an old approval or reset markers. Local offline checks include the
preserved startup log, the original Groups reproduction, negative evidence tests
and mocked ownership/exit races. These tests do not start or stop a real process.

This bundle links to the preserved v1 ZIP/freeze in [provenance.json](provenance.json).
Both [v1 prompt](prompts/v1.txt) and [v2 prompt](prompts/v2.txt), [cases/expectations](cases.json),
[configuration](config.json), [schema](schema.json), [order](order.json), all 18
[requests](requests/) and code are bound by [freeze.json](freeze.json). The repository's
handoff record gives the ZIP size/SHA-256 and displays each payload hash. Model/
runtime pins are in [artifacts.json](artifacts.json); URLs are provenance, not
instructions to download. [runtime-files.json](runtime-files.json) binds reused DLLs
and binaries to their original Windows hashes. Missing/mismatched artifacts stop.

## Frozen order and gates

| # | Request ID | Arm | Pause after saving |
|---:|---|---|---|
| 1 | 01-C1-v2 | v2 | — |
| 2 | 02-C2-v2 | v2 | — |
| 3 | 03-C3-v2 | v2 | — |
| 4 | 04-C4-v2 | v2 | — |
| 5 | 05-C5-v2 | v2 | — |
| 6 | 06-C6-v2 | v2 | cp06: all six known assessments |
| 7 | 07-F1-DE-v1 | v1 | — |
| 8 | 08-F1-DE-v2 | v2 | cp08 |
| 9 | 09-F2-FR-v2 | v2 | cp09 |
| 10 | 10-F2-FR-v1 | v1 | — |
| 11 | 11-F3-IT-v1 | v1 | — |
| 12 | 12-F3-IT-v2 | v2 | cp12 |
| 13 | 13-F4-EN-v2 | v2 | cp13 |
| 14 | 14-F4-EN-v1 | v1 | — |
| 15 | 15-F5-ES-v1 | v1 | — |
| 16 | 16-F5-ES-v2 | v2 | cp16 |
| 17 | 17-F6-AMB-v2 | v2 | cp17 |
| 18 | 18-F6-AMB-v1 | v1 | cp18: final comparator assessment |

All six known v2 responses are assessed together before request 7. Every fresh v2
response is assessed before **any** subsequent generation, including a v1 counterpart.
Each checkpoint reassesses the entire completed prefix: prior v1 content failures
remain comparison data, but any v2 strict failure or either-arm operational failure
denies continuation. The final pause covers the last v1 response. Eight manual
transfer cycles can consume the budget; the clock never pauses for them.

| Fresh case / original text | Frozen expected interpretation |
|---|---|
| F1-DE: `Bitte repariere meinen Drucker, ohne ihn zu ersetzen.` | understood/de; printer/repair; no_replacement="true"; goals []. |
| F2-FR: `Répare mon ordinateur ; garde au moins 256 GB de stockage.` | understood/fr; computer/repair; storage_min="256 GB"; goals []. |
| F3-IT: `Riutilizza il mio contenitore, senza comprarne uno nuovo.` | understood/it; container/reuse; no_new_purchase="true"; goals []. |
| F4-EN: `Repair my vacuum cleaner; budget 85 CHF, excluding delivery.` | understood/en; vacuum/repair; budget="85 CHF", cost_exclusion="delivery"; goals []. |
| F5-ES: `Repara mi impresora.` | Unsupported negative control: unsupported/null, nonempty unresolved, goals/constraints empty; grounded partial subject null/printer and action null/repair only. |
| F6-AMB: `Taxi` | understood/null; taxi; action null; no goals/constraints/unresolved meaning. Do not force a supported language. |

Expectations are AI-assisted, not independently qualified linguistic gold. The 55
held-out cases and v1's 24 unrun new cases are excluded. No aliases, canonicalizer,
schema, validator or scoring function changed: [contract.py](contract.py) and
[assess.py](assess.py) are byte-identical v1 copies. Only [dispatch.py](dispatch.py)
is the v2 assessment entry point; do not use the v1 CLI/freeze for new requests.

## Limits and runtime checks

One server start, at most 18 generation requests, **1,800 seconds total from Run
entry**, including preflight/hash checks, loading, metadata probes, generation and
all transfers/assessments. Readiness/offload confirmation within 90 seconds; each
generation at most 45 seconds. No warmup/smoke generation outside the count, restart,
retry, automatic CPU fallback, retuning or deadline extension. Expiry stops the
owned model and preserves partial data. Protective exit/export work may finish
after expiry; this permits no additional inference or renewed budget.

Unchanged: Qwen3-8B Q8_0, b11429/Vulkan0, two inference/prompt threads, temperature
0.7, top-p 0.8, top-k 20, min-p 0, seed 42, context 2,048, output 384, batch/ubatch
64, F16 KV, one slot, hard non-thinking, cache disabled, loopback 127.0.0.1:49187.
The logging-only change is `--log-verbosity 4` for both arms. Pinned source verification
is recorded separately; loader INFO is mapped to trace 4, whereas v1 captured 3.

Require positive equal N/N offload counts, Vulkan0/RX 6800 XT identification,
model-buffer placement and a positive Vulkan0 KV-buffer size in
the actual startup stderr, matching device enumeration and positive WDDM owned
allocation. Missing/partial evidence stops before generation. N/N does not prove
every operation runs on GPU or measured speedup. Keep all raw streams/timings/cache
counters and graph reuse separate from semantic scoring.

All 18 actual rendered prompts are sent to `/apply-template` and `/tokenize` after
a separately authorized load, **before first generation**. Require the empty closed
thinking prefix and `actual_prompt_tokens + 384 <= 2048` for every request. Save
raw probes and counts in `templates/` and `capacity.json`; stop on any mismatch.
V2's actual token counts are not measured in this Codespace: no 8B artifact or
desktop access is present. Synthetic boundary tests establish guard behaviour only.

Unchanged guards: available RAM >=20 GiB before loading and >=4 GiB thereafter;
owned server RSS <=16 GiB. Dedicated headroom >=14 GiB before loading and >=2 GiB
thereafter; owned GPU allocation <=12 GiB. Target drive >=30 GiB free initially and
>=5 GiB thereafter; scratch <=25 GiB, counting v1 artifact folder plus v2 run folder.
Keep DXGI/WDDM measurement limitations and sampled-peak limitations explicit.

## Windows preparation only — no inference

1. Download the supplied small ZIP to the desktop and use **Windows PowerShell**:

   ```powershell
   $bundleZip = Join-Path $env:USERPROFILE 'Downloads\windows-qwen3-8b-v2-0-1.zip'
   (Get-FileHash -LiteralPath $bundleZip -Algorithm SHA256).Hash.ToLowerInvariant()
   ```

   Compare with the repository handoff/chat SHA-256. Stop on mismatch. Nothing has
   run yet; independent download is not assumed completed.
2. Only after a match, unblock this verified ZIP if needed and extract to a new,
   dedicated local sibling of v1, `C:\ResolenaExperiments\qwen3-8b-followup-v2-0-1`.
   Do not overwrite an existing attempt or extract into v1. Use existing 64-bit
   Windows PowerShell 5.1; do not change machine policy or install prerequisites.
3. Run the parser/offload/ownership/receipt/hard-timer checks **on Windows, offline**:

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File C:\ResolenaExperiments\qwen3-8b-followup-v2-0-1\Test-Harness.ps1 -Scratch C:\ResolenaExperiments\qwen3-8b-v2-0-1-offline-checks
   ```

   Scratch must not exist. These tests check receipt decisions, exact export bytes
   and the hard timer, using synthetic files and an owned-process
   ID of zero for the timer; no model or other process is started/stopped. Preserve
   their output/scratch. Stop on parser, receipt or compiler failure; do not install
   a prerequisite or modify the freeze. No Python is needed on Windows.
4. Run read-only local resource preparation, still **no inference**:

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File C:\ResolenaExperiments\qwen3-8b-followup-v2-0-1\Preflight.ps1 -Root C:\ResolenaExperiments\qwen3-8b-followup-v2-0-1 -ArtifactsRoot C:\ResolenaExperiments\qwen3-8b-v1
   ```

   The Codespace cannot execute these steps or verify live Windows state. Its
   offline Python checks do not establish PowerShell parsing/runtime compatibility.

## Future execution — separate owner authorization required

Stop after preparation under the current authorization. `Run.ps1` refuses to start
without a separate, unfrozen `execution-approval.json` with `allowed:true` and
`approved_freeze_sha256` matching this bundle. The example deliberately denies
execution. Do not create an approval receipt until the owner authorizes inference.

After that separate approval and successful Windows checks, execute `Run.ps1` once
in a dedicated Windows PowerShell window using `-Root` and `-ArtifactsRoot` above.
The future Windows command is:

```powershell
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File C:\ResolenaExperiments\qwen3-8b-followup-v2-0-1\Run.ps1 -Root C:\ResolenaExperiments\qwen3-8b-followup-v2-0-1 -ArtifactsRoot C:\ResolenaExperiments\qwen3-8b-v1
```

It verifies the existing model/runtime ZIP/binary/DLL hashes and actual compatibility
without copies/downloads, creates a GUID and immutable deadline, then loads once.
Never invoke Run again to resume a pause or recover an interruption.

At each of cp06/cp08/cp09/cp12/cp13/cp16/cp17/cp18:

1. Windows prints the paused checkpoint ZIP and SHA-256. Transfer only that ZIP to
   the Codespace's Git-ignored `build/windows-v2-0-1-transfers/<run-id>/cpNN.zip`.
   Keep the original Windows controller open. Never forward the model port.
2. **Codespace only**, compare the transferred ZIP's SHA-256 with Windows, then:

   ```bash
   python3 -B experiments/uc001_multilingual/qwen_spike/windows_qwen3_8b_followup_v2_0_1/execution/dispatch.py assess build/windows-v2-0-1-transfers/<run-id>/cpNN.zip --output build/windows-v2-0-1-transfers/<run-id>/cpNN-assessed
   ```

   Substitute the actual run ID/checkpoint. Output folders must be new. Exit 0
   permits the exact next step; exit 1 includes a denied receipt. Inspect status,
   meaning, constraints and grounding per case; v1 failures do not become passes.
3. Download `return-cpNN.zip` from that output folder to Windows and extract into
   **that checkpoint's** `inbox\cpNN` folder. It contains `assessment.json` and
   `receipt.pending.json`. Preserve their bytes; do not edit or reformat JSON.
   Compare the pending receipt's SHA-256 with the dispatcher output. Complete the
   assessment copy first, then, **Windows only**, publish the receipt last:

   ```powershell
   Rename-Item -LiteralPath C:\ResolenaExperiments\qwen3-8b-followup-v2-0-1\inbox\cpNN\receipt.pending.json -NewName receipt.json
   ```

4. The existing running controller validates run GUID, freeze, active nonce,
   checkpoint-byte hash, prefix/order/case/arm, every request/response hash and the
   assessment hash. It derives continuation from v2 strict results and either-arm
   operational status, writes a consumed marker, then resumes without resetting
   time. A stale/wrong receipt stops. A denied receipt stops and closes. If the
   offline assessor errors without producing a receipt, press Ctrl+C in the owned
   Windows controller and preserve records; do not wait for or start a new attempt.

Every receipt is bound to the original 30-minute deadline. If time expires during
transfer, the watchdog/hard timer closes the model; no late receipt can resume it.
Both supported-language label errors and unsupported-language handling remain
strict failures for v2. Operational HTTP, timeout, finish, provenance, cache, thinking,
resource or ownership failure stops either arm immediately.

## Exit, export and recovery

Normal or failed closeout stops only the PID/start-time/executable-matched server,
confirms server exit, waits for watchdog exit and records both actual exit codes
when handles survive. A blocked owned watchdog may be stopped only after confirmed
model exit; this is recorded as an operational failure, not a normal watchdog exit.
Cleanup preserves model/runtime, originals, deadlines, markers and all partial data.
Final export is created only after exit and cleanup records, includes all checkpoints,
consumed/incoming receipts and raw results, and never includes the large artifacts.

After an interrupted controller, wait until it has ended; do not duplicate Run.
`Close.ps1 -Root <v2-folder>` may close the matching owned server and finish export.
It refuses while the original controller remains active. Recovered exit confirmation
can establish the old process is absent while its exact exit code remains unknown;
those records say so. Missing confirmation withholds the final archive and retains
partial data for review. A prior final archive is preserved, not overwritten.

Transfer `final-results.zip` plus its printed SHA-256 to the Codespace, and run the
same dispatcher with `closeout` and a new output directory to verify recorded exits,
cleanup and manifest hashes. This is Windows evidence, not live process verification.
Do not delete reusable artifacts or any recovery marker. No new run is authorized
by cleanup, transfer, receipt acceptance or passing this exploratory comparison.
