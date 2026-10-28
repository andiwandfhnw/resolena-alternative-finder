# Windows Qwen3-8B exploratory bundle 1.0.0

Prepared 2026-10-13 under the owner's approval for one Windows/Vulkan experiment.
No Windows execution, artifact acquisition or model inference has occurred here.
All expectations are AI-assisted synthetic calibration, not independently validated.
Product direction A, production integration, final DESIGN and linguistic validation
are separate: only A is accepted. No paid infrastructure/reviewers are authorized.

## Contents and immutable inputs

`cases.json` freezes six known cases and 24 new cases. `order.json` fixes six known
requests first, then 24 new requests and four explicit repeats. `requests/` contains
the complete UTF-8 HTTP bodies. `contract.py` copies the original prompt, schema,
aliases, validator and semantic scorer verbatim; `contract_provenance.json` identifies
the exact source block/hash. `assess.py` supplements the unchanged scorer with
status/language/constraint checks so unsupported output cannot hide semantic errors.
Plausible equivalent labels are reported separately and still fail the strict gate.
`freeze.json` hashes every payload file. Original 55 held-out cases are excluded:
they are never loaded into the new harness or sent to Windows/the model.

Operational changes only: Windows loopback HTTP instead of AF_UNIX, Windows resource
sampling/process ownership, pinned prebuilt Vulkan runtime, explicit no-auto-fit/
no-warmup switches and an offline known-case gate. No prompt, schema, alias or
validator relaxation. No extra smoke request; template/tokenization probes do not
generate model output. GPU computation changes the environment; no CPU speedup
comparison or acceleration claim follows merely from device detection.

## Artifact verification

`artifacts.json` records exact pinned URLs, versions and publisher metadata APIs.
Read-only publisher metadata confirms:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| Qwen3-8B Q8_0, revision `7c41481f57cb95916b40956ab2f0b139b296d974` | 8,709,518,112 | `408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6` |
| llama.cpp b11429 Windows x64 Vulkan ZIP, source `d81235049384534c167caea52b85a694f6103d14` | 33,337,769 | `1bfe78ad9168b79fa02bf67f6af9f5e17a966d824d77238517f7bef12ac73b36` |

Combined 8,742,855,881 bytes; 1 MiB reserved for this small bundle/metadata still
leaves the sum below the **10,000,000,000-byte** acquisition cap. No artifact bytes
were acquired in the Codespace. Setup rechecks exact publisher sizes/digests/URLs
before either artifact GET and counts downloaded body bytes incrementally; no
automatic retry/resume/redownload. HTTP/TLS overhead is not measured. The reserve
is conservative for the bundle and metadata; a partial download is preserved.

Runtime b11429 is an upstream pre-release matching the existing source commit.
Only its Vulkan ZIP is permitted. No CPU/CUDA/ROCm fallback, SDK/compiler/driver
installation or update. Missing DLLs or an incompatible runtime/device stop setup
after recording the failure; the model is acquired only after --version and
--list-devices succeed with the pin and Vulkan0 RX 6800 XT.

## Windows execution — follow one step at a time

All PowerShell commands below run **on your Windows desktop**, in existing
**64-bit Windows PowerShell 5.1**, not in VS Code's Codespace terminal. No administrator
elevation, remote access, port forwarding, external inference or firewall opening
is part of the bundle. Cancel any network-access permission prompt rather than
opening access. Reviewed/unblocked scripts use RemoteSigned for their process only,
without modifying a system/user policy; enforced managed policy takes precedence.
Stop if such a policy blocks execution; do not bypass it.

1. Download the small repository bundle ZIP independently using VS Code Explorer's
   Download action; verify its SHA-256 against the provided handoff. Do not assume
   download happened. After reviewing the scripts and matching the hash, unblock
   **that ZIP only**, then extract it into a new staging folder:

   ```powershell
   $bundleZip = Join-Path $env:USERPROFILE 'Downloads\windows-qwen3-8b-v1.zip'
   Get-FileHash -LiteralPath $bundleZip -Algorithm SHA256
   # Only after the expected handoff hash matches and scripts are reviewed:
   Unblock-File -LiteralPath $bundleZip
   Expand-Archive -LiteralPath $bundleZip -DestinationPath (Join-Path $env:USERPROFILE 'Downloads\windows-qwen3-8b-v1')
   ```

   Adjust only the downloaded-file path if your browser used another directory.
   Do not overwrite an existing staging folder.

2. Read-only local preflight; select a **new dedicated experiment folder** on a local
   drive. The sample below uses C:; choose a different drive explicitly if appropriate.
   This probe checks all PS syntax before executing helpers, frozen hashes, DXGI
   capacity/LUID and built-in WDDM counters, RAM, actual target-drive free space and
   absence of a matching owned server. It does not create the folder/start deadlines.

   ```powershell
   Set-Location (Join-Path $env:USERPROFILE 'Downloads\windows-qwen3-8b-v1')
   powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\Preflight.ps1 -Root 'C:\ResolenaExperiments\qwen3-8b-v1'
   ```

   Stop and return the preflight JSON or exact error. Do not run setup until reviewed.
   Missing counters/permissions/dependencies mean stop, not installing another tool.
   Dedicated headroom is DXGI physical capacity minus matched WDDM dedicated usage;
   a lower driver per-process residency budget is not independently captured. WDDM
   allocations/actual offload/startup outcomes remain essential subsequent evidence.

3. After preflight passes, execute setup on Windows:

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\Setup.ps1 -Root 'C:\ResolenaExperiments\qwen3-8b-v1'
   ```

   This creates a new owned folder and original `state.json`, starting the fixed
   **120-minute total / 60-minute setup** windows. It freezes the original deadlines,
   verifies metadata before artifact download, hashes each file, extracts the runtime
   and verifies version/device without loading a model. Stop and report setup status
   and deadlines before run. Metadata mismatch/failure means no artifact download.
   Existing folders/markers are preserved and cannot be used for an automatic retry.

4. After verified setup, start the single planned model process on Windows:

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File 'C:\ResolenaExperiments\qwen3-8b-v1\Run.ps1' -Root 'C:\ResolenaExperiments\qwen3-8b-v1'
   ```

   Loading plus requests/pause share **30 minutes**, also within the original total
   window. Readiness <=90s and requests <=45s. One slot, two inference/prompt threads,
   context 2,048, output 384, F16 KV, batch/ubatch 64, temperature .7/top-p .8/top-k 20/
   min-p 0/seed 42, hard non-thinking kwargs, no history/tools/cache/context shift.
   Runtime overrides in the child LLAMA/HF/VK environment are removed by name without
   reading/logging their values. Loopback listener ownership is verified.

   Each complete request/raw response/finish/token/timing record is saved before
   the next case. `resources.jsonl` samples owned working set/private bytes, owned
   dedicated GPU allocation, matched adapter headroom, RAM and disk with timestamps.
   Native server logs capture actual layer offload. Counter sampling is approximately
   once per second plus query time; sub-sample peaks are not captured. Absence of a
   detected non-loopback socket is a sampled check, not a comprehensive telemetry audit.

5. **Known gate:** the runner produces `known-results.zip` after C1–C6, then waits
   without sending the 24 new cases. Upload only that small synthetic-results archive
   to this conversation/workspace for offline assessment. Do not copy secrets,
   model weights, personal documents or expose the server. Keep the Windows console
   open; the independent watchdog remains active even if the console disappears.
   The pause consumes the existing 30/120-minute deadlines; they cannot be reset.

   **Codespace only**, after safely extracting the archive into a new ignored folder:

   ```bash
   python3 -B experiments/uc001_multilingual/qwen_spike/windows_qwen3_8b_v1/assess.py known /ABSOLUTE/PATH/TO/EXTRACTED/KNOWN/RESULTS
   ```

   This does no inference and reads no held-out inputs. It writes `assessment.json`
   and `gate.json`. Any substantive semantic error stops; quote/schema/label failures
   also block the unchanged strict gate. A label-only mismatch is reported separately
   and does not imply a different physical object, but cannot permit more cases.
   GPU full-offload and positive memory evidence, zero cache and complete timings are
   required; an upstream scorer's unsupported branch never supplies success by itself.

   Return the assessment and gate through independent file download. Copy
   `assessment.json` first, then `gate.json`, to the Windows experiment folder.
   A failed gate stops the existing server before new cases. A passing gate must match
   the frozen bundle and all six request/response hashes; only then can the waiting
   runner send the remaining fixed requests. An expired/stopped process cannot restart.

6. The runner stops only its owned server and exports `final-results.zip` on completion
   or failure. Transfer the small archive for offline `assess.py all` assessment if all
   34 requests completed. For a partial run, report the saved failure/unexecuted cases;
   do not force a complete assessment or count missing responses as semantic failures.
   Median <=10s / p95 <=20s are candidate targets, not product-spec amendments. The
   first request, sampling/cache/hardware differences and unavailable measurements
   remain separate. All results remain exploratory with linguistic validation pending.

## Cleanup and interruption recovery

On Windows, if the runner was interrupted, first inspect `state.json`,
`server_process.json`, `watchdog_exit.json`/`guard_failure.json`, `progress.json`
and the response folder. Do not rerun Setup/Run, delete markers, reacquire artifacts,
reset timestamps, kill unrelated processes or switch backend. The watchdog enforces
the old deadlines and stops only a PID whose start time/executable match the receipt.

For explicit closeout on Windows:

```powershell
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File 'C:\ResolenaExperiments\qwen3-8b-v1\Cleanup.ps1' -Root 'C:\ResolenaExperiments\qwen3-8b-v1'
```

Cleanup verifies the bundle and PID/start-time/path ownership, stops only the owned
server if still present, records hashes and keeps **all weights, runtime files,
results, partial downloads, recovery markers and original deadlines**. The watchdog
exits once the owned server ends; no unrelated process is stopped. Model process
exit status records the actual forced owned shutdown separately from semantic/model
assessment. Verify independent small-archive preservation before any later decision
about releasing storage; deletion is not included here. Keep the dedicated folder
through closeout and report actual shutdown/preservation, never assume it happened.

## Verification boundary

Offline tests exercise the actual saved 1.7B failures, classification hidden by
unsupported status, exact quote case, label-only mismatch and targeted uncertainty.
They validate harness checks, not model performance. Windows PS parsing, DXGI/WDDM
queries, native binary compatibility and GPU inference remain unexecuted until the
corresponding local step. Stop on an additional prerequisite; do not install it.
