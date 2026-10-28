# Portable experimental extension — authorized 2026-10-11

Owner amended the previous native-CPU stop: remain on 4 cores/16 GB RAM/32 GB
storage for one compatible rebuild and the approved calibration. This is linked
to ../calibration_B_2026_10_11/ and the preserved failed smoke; their records,
deadlines, markers, source, model and native binary/logs remain intact.

Pinned llama.cpp d81235049384534c167caea52b85a694f6103d14 is reused, with the
same Qwen3-1.7B-Q8_0 model/checksum and retained CMake. Local pinned ggml/CMakeLists.txt
documents native and individual feature switches; ggml/src/ggml-cpu/CMakeLists.txt
defines the resulting non-native flags. Use GGML_NATIVE=OFF with supported fixed
SSE4.2/AVX/AVX2/FMA/F16C/BMI2. Disable AVX-VNNI, AVX-512 variants and AMX; keep
single static CPU backend. Generic x86-64/generic-tuning global C/C++ flags make
the compiler baseline explicit. This targets the fixed supported feature set,
not every x86 CPU. Disable ccache and disconnected fetch-content for this build.
All other previous CPU-only/privacy build settings are retained. No source/model
downloads, source edits, runtime/model pin changes or production integration.

Separate Git-ignored /workspaces/resolena-alternative-finder/build/qwen-portable-20261011/
holds compiled/ output, original_native/ binary/log copies, temporary build files
and runtime/ socket/trace/log. Model and verified source remain in the original
workspace tree. Count original tree plus this directory and records against the
same 6 GiB scratch limit. Owned RSS 3.25 GiB, preflight available 3.75 GiB, runtime
available 0.5 GiB; no safeguard is lowered. Acquire the shared owner lock and check
active experiment processes before building/loading. Only owned subprocess groups
are stopped at timeout/failure/closeout; unrelated processes are untouched.

Freeze operational files and byte-identical original cases/order/prompt/schema/
validator runner before execution. New operational substitutions redirect only
portable binary/preparation, isolated runtime directory, total-extension deadline,
scratch accounting and previously authorized exact-sample preflight logging.
No inference request/scoring change. Fresh window begins once extend.py executes:
2700s total, first 1800s maximum for configuration/build/checks, then at most 900s
including loading/calibration and within total deadline. Readiness 90s, requests
45s. Seed 42, temperatures .7/0, two inference/prompt threads, all remaining settings
unchanged. No additional smoke, retries, tuning or heldout evaluation.

Record incremental state, commands, hardware, resources, complete build logs,
effective compile flags and exit status. Reject native/unapproved/missing-host
instruction switches in all compile_commands entries before and after building.
Verify source unchanged, hash new binary, and run --version before loading; build
or compatibility/startup failure stops without retry. Semantic failures are saved
and only remaining fixed requests continue within budget. Capture each complete
request/raw response/finish/usage/cache/timing using the unchanged calibration.
Hash verification may warm OS file cache; no cache flush, and measurements must
not treat old/new hardware or builds as identical. All six temperature-zero cases
must pass strict validation and frozen meaning; success alone authorizes no support
claim or heldout evaluation. Three synthetic architecture-flag guard checks passed.

Preserve artifacts/results through closeout, then guide manual return to the
recorded 2-core/8 GB/32 GB type, restart/reconnect and verify files/Git/resources.
Actual return remains pending until verified. DESIGN stays Phase 2/in-progress
with final acceptance pending. No staging, commits, pushes or deployment.

## Actual closeout

Extension ran 17:29:19–17:47:17 Europe/Berlin, 17m58.64s total. Portable compilation
passed in 785.29s (13m05.29s), exit 0. All 223 effective compile commands passed
the fixed-feature guard; source hashes remained unchanged, the new binary hash
is recorded, and --version passed before loading. Original binary/full logs are
separately retained under build/qwen-portable-20261011/original_native/ and at
their original paths. No source/model acquisition, version/pin change or retry.

Model readiness passed in 1.46s. All twelve planned requests completed with HTTP
200 and finish_reason=stop; none passed unchanged strict checks, including 0/6
at temperature zero. Calibration took 268.90s (4m28.90s) including loading; owned
model process exited 0, driver/calibration exited 1 because of semantic/grounding
failures. No operational resource/transport/timeout failure occurred. Peak build
owned RSS 678,666,240 bytes; peak inference owned RSS 2,234,003,456 bytes; maximum
recorded scratch 2,371,961,845 bytes. Original limits remained unchanged.

All completed responses report cache_n=0 and cached prompt tokens=0. Requests used
cache_prompt=false. Prompt/generation timings and token counts are captured per
response. Verification hashes may warm OS file cache; exact model-page residency
was not measured. The AMD/fixed-feature environment differs from Intel/native;
do not attribute faster timings versus the smoke to temperature alone. Output
length also differs between sampling arms. Twelve synthetic harness checks passed
separately (3 new flag checks, 5 reporting checks, 4 preflight logging checks);
they are not actual model passes.

Full paired dimensions, frozen expectations, raw model content, exact quote
grounding, token/cache/timing fields and request/response links are preserved in
CASE_REPORT.md and results.json. Unsupported categories do not count as success
when expected classification/language or uncertainty is wrong. C6's unsupported
status matches, but its en language and empty unresolved list do not; added
constraints are described even though the unchanged unsupported scorer has no
meaning projection. No validator, alias, schema, case or prompt was relaxed.

Calibration failed; stop this configuration pending review. No extra experiment,
tuning, retry or heldout evaluation follows. The 55 frozen cases remain unchanged
and unexposed to this model; C1 remains observed calibration data. Original attempt
records/deadlines/markers/results match the pre-execution preservation hashes.
Return to 2 cores/8 GB/32 GB is manual and remains pending. Reconnect after selector
change and stop/start, then verify the new preservation manifest and actual return.
DESIGN stays pending; no production integration or Git delivery.

## Experiment closed — verified return

Owner confirmed selecting/reconnecting on the original type. Read-only
[return verification](../../../../build/checkpoints/uc001-machine-change-20261011-1427/return_verification.json)
finished at 18:18:42 Europe/Berlin on 2026-10-11: two CPUs, 8,327,036,928 bytes
usable RAM (7.76 GiB), 5,502,414,848 bytes available (5.12 GiB), unchanged
33,636,024,320-byte workspace capacity and 24,014,274,560 bytes free. The physical
host is now Xeon Platinum 8573C; original machine type/resource shape is restored,
not the identical physical CPU. Visible cgroup max/high are unlimited and OOM
events zero; hidden ancestors are not independently verified. All 206 project/
record/log files and 13,629 native/portable artifact files match saved hashes,
as do both checkpoint/result archives, model/interpreter and frozen inputs.
Branch/HEAD/index and existing uncommitted work are preserved; no experiment
process remains. No inference or runtime binary was executed for this verification.

The tested pinned **Qwen3-1.7B Q8_0 configuration failed calibration and is not
accepted for production**: 0/12 strict passes, required temperature-zero 0/6.
Build, native-flag removal, binary compatibility and readiness succeeded; twelve
synthetic harness checks passed separately. The operational successes do not
establish model correctness. [Paired case report](CASE_REPORT.md),
[raw responses and assessments](results.json), [frozen cases/order](cases.json),
[actual portable build options](build_configuration.json) and
[hardware](hardware.json) retain the detailed evidence. Earlier failed smoke,
resource preflight stop, recovery markers/deadlines and original binary/logs
remain preserved; this final closure does not overwrite their historical states.

Observed failures are distinct and can overlap:

- Semantic failures: supported English/Italian incorrectly marked unsupported,
  invented or contradictory constraints, and incorrect language/missing uncertainty
  for the Spanish unsupported case. Exact quotes in C2/C5/C6 do not cure these.
- Quote-grounding failures: changed initial case in English/French quotes and
  empty/non-verbatim support for extra German constraints.
- Normalized-label mismatches: water_kettle/bouilloire/répare do not match frozen
  canonical labels. These recognizable equivalents alone do not prove a different
  physical object/action; they still fail the unchanged output contract/scoring.

Do not describe all twelve strict failures as twelve wrong underlying meanings.
No aliases, quote fidelity, semantic checks, expected statuses/languages, prompts,
schema or cases were relaxed. This is a small synthetic calibration of the recorded
model/runtime pins, quantization, non-thinking prompt/template, context/output
limits, two-thread portable build, seed 42 and .7/0 comparison. The conclusion
does not generalize to all local models or other Qwen configurations. No reliable
multilingual-support claim follows; all 55 frozen cases remain unexposed to this
model, and the observed smoke remains calibration data.

The experiment is closed; return to the original type is verified complete.
Reusable artifacts/results stay in Git-ignored /workspaces storage, with preserved
manifests and archives. Approved multilingual requirements remain unchanged and
DESIGN/ADR-003 acceptance remains pending. No new experiment, download, rebuild,
inference, production change, staging, commit, push or deployment is authorized
or performed by this closure.
