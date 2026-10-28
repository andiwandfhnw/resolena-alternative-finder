# Granite application-contract preparation v1

This is an offline, provisional Priority 3 preparation package, not an accepted
suitable interpreter or live-run authorization. Model/runtime acquisition, build,
Windows changes, transfer, startup and inference remain unauthorized. Priority 5
acceptance under ADR-007 and the closed Qwen result remain unchanged. Normal
`app.main` is unconfigured; references remain development-only and real knowledge/
rendering drafts remain inactive.

## Frozen identity and scope

- Publisher: `ibm-granite/granite-3.3-8b-instruct-GGUF` at
  `e40e9dd739c7be00fa965c16ce167088190ce114`.
- Artifact: `granite-3.3-8b-instruct-Q8_0.gguf`; expected **8684264992 bytes**;
  expected SHA-256
  `8ced2b014c6b5d4b1be698fd2cb5b051b08ce0b439d2584eb358e0d3f0a00611`.
- Runtime: llama.cpp `v0.7.0`, source commit
  `620d2225cc436ab0b001e3200e590e3b286ef9ab`, proposed Windows x64/Vulkan source build.
  No release-matched Windows binary or verified binary hash is claimed.
- Use the selected GGUF's embedded tokenizer/template. Repository metadata reports
  template SHA-256
  `8a58e18acd9ca00a43a285fe6ba3760efbda06b5ab7fb57875bfacd72957ed5e`;
  actual artifact/header/template verification is pending. The exact upstream
  conversion revision is not established. Do not substitute another tokenizer or
  the later upstream template merely to match an expectation.
- Frozen request scope: one sequence, 8192 total context, at most 4096 generated
  tokens, FP16 K/V cache, intended all-layer Vulkan offload, greedy temperature 0,
  seed 42, non-streaming, no tools/documents, no automatic retry. Country and
  language preferences remain in application policy, outside the interpreter.

The weight repository declares Apache-2.0; the pinned runtime uses MIT. Preserve
licences/notices and modification markings. Actual source archive/build hashes,
build-toolchain/dependency notices, drivers, available memory and desktop Python
availability remain later checks; none is inferred from metadata or a mock.

`prompt.txt` contains generic contract instructions, not assessment answers.
`schema.json` is the frozen transport schema. Local references are inlined without
changing their meaning; non-validating annotations are distinguished from retained
constraints. Offline schema inspection is not execution of the native converter.
The pinned runtime's older grammar guide names tools absent from this source pin:
there is no assumed Python converter or `llama-gbnf-validator` command. Actual
native conversion/grammar inspection needs an approved non-inference method before
live generation. Neither `llama-cli -n 0` nor `/completion` with zero output is a
safe substitute: prompt evaluation is inference.

The future adapter uses `/apply-template`, `/tokenize` and native `/completion`.
Raw native content passes unchanged to existing strict decoding/domain validation;
no fences, reasoning wrappers, lost clauses or malformed packets are repaired.
Mocked envelopes establish only the tested client boundaries. Actual GGUF template,
rendering, tokenization, effective native settings, truncation/termination and
runtime compatibility remain unverified.

## Case order, review and generation accounting

`cases.json` contains the exact input text, UTF-8 base64, byte count and SHA-256,
source references, semantic obligations and acceptable outcomes. These obligations
are AI-assisted preparation, with competent review **pending**, not gold packets.

| Order | Case | Existing reference | Required observation |
|---|---|---|---|
| 1 | `g01-de` | LAC-01; AC-15; TL-01 | Complete standard-DE repair/no-replacement meaning. |
| 2 | `g02-fr` | LAC-02; AC-15; TL-01 | Complete FR meaning; no country inference. |
| 3 | `g03-it` | LAC-03; AC-15; TL-01 | Complete IT meaning; no invented market/currency. |
| 4 | `g04-en` | LAC-04; AC-15; TL-01/04 | Complete EN meaning; capture for the one API/SQLite replay. |
| 5 | `g05-shared` | LAC-05/13; AC-15; TL-02/04 | No forced language/subject; genuine meaning clarification or competently justified understood branch. |
| 6 | `g06-mixed-primary` | LAC-06; AC-15; TL-02 | Retain the French condition in the primarily English request. |
| 7 | `g07-mixed-balanced` | LAC-06/13; AC-15; TL-02/04 | Preserve all balanced mixed meaning; preference cannot resolve meaning. |
| 8 | `g08-protected-values` | LAC-07; AC-15; TL-01 | Literal names/place, exact amount/context and negation. |
| 9 | `g09-ambiguous-amount` | LAC-08; AC-15; TL-01/02/04 | Exact `1,200 CHF`; targeted clarification, no invented budget/subject. |
| 10 | `g10-out-of-scope` | LAC-10; AC-15; TL-02/04 | Honest application-scope limitation; no false claim that IBM cannot understand Spanish. |
| 11 | `g11-unvalidated-dialect` | LAC-10; AC-15; TL-02/04 | Retain `nöd neu`; rephrasing/targeted clarification, no dialect-support success. |

At most **one future model startup and eleven total generations**, in this order,
one per case. There is no allocated warm-up or hidden twelfth application call.
`--no-warmup` is mandatory. Metadata, template rendering and tokenization are not
permission to add a generation. No retries, retuning, prompt/case changes, candidate
switching or continuation after the stop condition.

The one API/SQLite observation **replays the captured `g04-en` result** through the
existing opt-in synthetic composition: zero new generations. Label it as replay,
not a second live-interpreter demonstration. Use a new isolated database beneath
`build/test-only/`; retain original text, interpretation version/provenance and the
actual honest saved/limitation outcome. Synthetic English-only evidence/rendering
cannot establish real providers or faithful DE/FR/IT renderings. Preference/browser/
correction replay of justified understood shared/balanced captures also adds no
inference and must not resolve uncertain meaning.

Record separately for each case:

1. Structural validity: native envelope, complete termination, no truncation,
   settings/accounting, strict JSON/schema and unchanged domain validation.
2. Semantic correctness: every clause, negation, protected value, requirement and
   genuine uncertainty against the exposed obligation. Valid JSON can be wrong.
3. Qualified review: named competent source-language/meaning reviewer, decision and
   rationale bound to the raw response/input hashes. Unavailable review remains
   unverified, never passed. No paid reviewer or dialect acceptance is assumed.
4. Application-policy/persistence observation, explicitly live versus replay.

Review the expectations before execution. After each response, complete the required
review within its bound before proceeding. An honest clarification/limitation is
acceptable only under that case's frozen conditions; it is not automatically proof
of complete interpreter suitability. Stop on integrity/control/resource failure,
transport/contract failure, confirmed semantic failure, review timeout or unavailable
competent review. Preserve the partial result and leave later cases unrun. No new
product pass percentage, confidence, latency or aggregate acceptance threshold is
introduced. Qualified linguistic/TL-03 and later Priority 6/Phase 4 gates remain.

## Proposed operational limits, not measurements

| Phase/resource | Proposed bound |
|---|---|
| Acquisition | 30 minutes total; at most 10 GiB total downloaded; no automatic retry. |
| Build | 45 minutes; at most 12 GiB build output; parallelism 2; process-tree memory at most 24 GiB. |
| Disk | At least 48 GiB free initially and 24 GiB immediately before startup; stop below 8 GiB. |
| Host memory | At least 24 GiB free before startup; server RSS at most 16 GiB, client RSS at most 2 GiB, combined at most 18 GiB; stop if OS free memory falls below 4 GiB. |
| GPU | At least 12 GiB free on the intended RX 6800 XT before startup; stop below 1 GiB free; prove actual intended GPU offload. |
| Startup | One model-server process/start only, at most 180 seconds. |
| Request | At most 120 seconds for the entire interpret operation, including template/tokenization/completion. |
| Assessment | At most 30 minutes total, including startup and review pauses; at most 120 seconds review per case. |

The total deadline wins: phase/request/review maxima do not guarantee all eleven
cases fit. Start the assessment clock at the reserved model launch; do not reset it
when the client starts, during review or after an error. A stopped/failed startup
consumes the new Granite allowance; it does not reset a Qwen allowance.

Resource estimates are not measurements: approximately 8.09 GiB weight bytes plus
1.25 GiB FP16 KV at 8192 context, before buffers, driver and host overhead. The known
desktop profile is Ryzen 9 5950X / RX 6800 XT 16 GB; host RAM, driver, SDK, available
VRAM, toolchain and current compatibility are unknown. The Codespace has no implied
access to the desktop GPU. No paid infrastructure or CPU fallback is authorized.

**Live execution is blocked until trustworthy Windows process ownership, measurement
and enforcement are approved.** This package's Python assessment client is not a
verified Windows resource/process supervisor. It does not establish a trustworthy
GPU adapter binding, measure/enforce GPU headroom or supervise Windows server RSS.
The owner must identify an approved process-tree supervisor covering the numerical
limits, global clock and cleanup. Unsupported, stale, ambiguous or unenforceable
measurements mean STOP; neither zero nor an old observation is a substitute.
Do not launch a new investigation or install tools under this preparation approval.

## Current-worktree handoff and prerequisites

No transfer is performed now. A checkout of HEAD is insufficient: required code and
approved reference files are still uncommitted. The prepared transfer archive uses
an explicit allowlist of the necessary **current worktree bytes**, hashes each entry,
and excludes credentials, private databases, caches and held-out material. It
contains the frozen new package, current app code, required synthetic composition
and approved country/locality reference dependencies. It is not a repository clone.

For later authorized handoff, the owner first checks the archive SHA-256 against the
reviewed receipt through a trusted channel, then unpacks into a new empty desktop
worktree. Never overwrite an old attempt. Verify archive entries/hashes and frozen
files before executing the new client; a self-reported archive checksum is not
independent approval. No credentials enter the archive.

The existing preparation commands are, from **Codespaces Bash — remote Linux**:

```bash
.venv/bin/python -m scripts.uc001_granite_contract_v1.package verify
.venv/bin/python -m scripts.uc001_granite_contract_v1.package transfer --output build/uc001-granite-contract-v1/desktop-transfer.zip
.venv/bin/python -m scripts.uc001_granite_contract_v1.package verify-archive --archive build/uc001-granite-contract-v1/desktop-transfer.zip
```

After a separately authorized transfer, **Windows PowerShell — desktop**, from the
new worktree with a pre-approved Python 3.12 environment:

```powershell
$GraniteWorktree = (Get-Location).Path
$env:PYTHONPATH = "$(Join-Path $GraniteWorktree 'src');$GraniteWorktree"
python -m scripts.uc001_granite_contract_v1.package verify
python -m scripts.uc001_granite_contract_v1.package verify-archive --archive 'C:\Resolena\granite-v1\desktop-transfer.zip'
```

Prerequisites remain explicit: the desktop worktree, Python/runtime dependencies,
Git, CMake, Ninja, an approved x64 MSVC developer environment and compatible Vulkan
SDK/compiler/driver must exist and be recorded. Missing tools mean STOP and separate
owner authorization; these instructions install none. Preserve applicable dependency
licences. Confirm the frozen archive/package, candidate hashes and approvals; a
successful offline preparation test grants no startup permission.

## Future acquisition/build commands — separate authorization required

The commands below are a proposed recipe, not an executable allowance. Run only
under the separately approved acquisition/build supervisor and its global limits.
Use fresh owner-approved directories outside the desktop worktree; never run source
Git commands in the Resolena repository. These phase commands perform no model run.

**Windows PowerShell — desktop**, after explicit acquisition approval:

```powershell
$GraniteRoot = 'C:\Resolena\granite-v1'
$GraniteAssets = Join-Path $GraniteRoot 'assets'
$GraniteSourceRepo = Join-Path $GraniteRoot 'runtime-source-repository'
$GraniteSourceZip = Join-Path $GraniteRoot 'llama-620d2225-source.zip'
$GraniteSource = Join-Path $GraniteRoot 'runtime-source'
$GraniteBuild = Join-Path $GraniteRoot 'runtime-build'
$GraniteRuntimeCommit = '620d2225cc436ab0b001e3200e590e3b286ef9ab'
$GraniteArtifact = 'granite-3.3-8b-instruct-Q8_0.gguf'
$GraniteExpectedHash = '8ced2b014c6b5d4b1be698fd2cb5b051b08ce0b439d2584eb358e0d3f0a00611'
$GraniteModel = Join-Path $GraniteAssets $GraniteArtifact
$GranitePartial = $GraniteModel + '.partial'
if ((Test-Path $GraniteSourceRepo) -or (Test-Path $GraniteSourceZip) -or (Test-Path $GraniteSource) -or (Test-Path $GraniteBuild) -or (Test-Path $GraniteModel) -or (Test-Path $GranitePartial)) { throw 'Fresh paths required; preserve earlier artifacts.' }
New-Item -ItemType Directory -Path $GraniteAssets -ErrorAction Stop | Out-Null
$GraniteModelUrl = 'https://huggingface.co/ibm-granite/granite-3.3-8b-instruct-GGUF/resolve/e40e9dd739c7be00fa965c16ce167088190ce114/granite-3.3-8b-instruct-Q8_0.gguf?download=true'
curl.exe --fail --location --proto '=https' --proto-redir '=https' --retry 0 --connect-timeout 30 --max-time 1800 --max-filesize 8684264992 --output $GranitePartial $GraniteModelUrl
if ($LASTEXITCODE -ne 0) { throw 'Model acquisition failed; do not retry automatically.' }
if ((Get-Item -LiteralPath $GranitePartial).Length -ne 8684264992) { throw 'Model byte count mismatch.' }
if ((Get-FileHash -LiteralPath $GranitePartial -Algorithm SHA256).Hash.ToLowerInvariant() -ne $GraniteExpectedHash) { throw 'Model SHA-256 mismatch.' }
Move-Item -LiteralPath $GranitePartial -Destination $GraniteModel -ErrorAction Stop

git init $GraniteSourceRepo
if ($LASTEXITCODE -ne 0) { throw 'Source repository initialization failed.' }
git -C $GraniteSourceRepo remote add origin https://github.com/ggml-org/llama.cpp.git
git -C $GraniteSourceRepo fetch --depth=1 --no-tags --recurse-submodules=no origin $GraniteRuntimeCommit
if ($LASTEXITCODE -ne 0) { throw 'Pinned source acquisition failed; do not retry automatically.' }
if ((git -C $GraniteSourceRepo rev-parse FETCH_HEAD).Trim() -ne $GraniteRuntimeCommit) { throw 'Runtime source revision mismatch.' }
git -C $GraniteSourceRepo archive --format=zip "--output=$GraniteSourceZip" FETCH_HEAD
if ($LASTEXITCODE -ne 0) { throw 'Source archive failed.' }
Get-FileHash -LiteralPath $GraniteSourceZip -Algorithm SHA256
Expand-Archive -LiteralPath $GraniteSourceZip -DestinationPath $GraniteSource -ErrorAction Stop
```

The 30-minute/10-GiB bound covers the combined model and source acquisition, not a
fresh allowance per command. The local archive hash is unknown until authorized
acquisition and must then be recorded; it is not replaced by the Git commit hash.
Verify selected GGUF header/tokenizer/template with an approved metadata-only
method before live use. No second model CLI is permitted as a header probe.

After separate build approval, within the approved x64 developer environment:

```powershell
cmake -S $GraniteSource -B $GraniteBuild -G Ninja -DCMAKE_BUILD_TYPE=Release -DFETCHCONTENT_FULLY_DISCONNECTED=ON -DGGML_VULKAN=ON -DLLAMA_BUILD_SERVER=ON -DLLAMA_BUILD_TOOLS=ON -DLLAMA_BUILD_COMMON=ON -DLLAMA_BUILD_IS_DEV=OFF "-DLLAMA_BUILD_COMMIT=$GraniteRuntimeCommit" -DLLAMA_BUILD_NUMBER=0 -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_APP=OFF -DLLAMA_BUILD_UI=OFF -DLLAMA_USE_PREBUILT_UI=OFF -DLLAMA_OPENSSL=OFF -DLLAMA_SUBPROCESS=OFF -DLLAMA_LLGUIDANCE=OFF
if ($LASTEXITCODE -ne 0) { throw 'Offline pinned configure failed; do not install/fetch missing dependencies automatically.' }
cmake --build $GraniteBuild --config Release --target llama-server --parallel 2
if ($LASTEXITCODE -ne 0) { throw 'Pinned source build failed.' }
$GraniteServer = Join-Path $GraniteBuild 'bin\llama-server.exe'
Get-FileHash -LiteralPath $GraniteServer -Algorithm SHA256
```

Record actual executable/DLL hashes, compiler/SDK versions, source archive hash and
licences for owner review. Build output/ownership and numerical limits must be
supervised. No Windows binary hash or compatibility is inferred from this recipe.

`LLAMA_BUILD_COMMIT` and `LLAMA_BUILD_NUMBER` explicitly label build metadata for
the archived source tree. Those supplied values are not proof of compiled-source
identity: the pinned Git revision, source archive digest, reviewed recipe and actual
executable/DLL hashes remain separate integrity evidence.

## Future model-free native schema inspection

`native-inspection/` supplies a small source-only helper using the selected
runtime's `json_schema_to_grammar` function. It reads the frozen schema and writes
a new GBNF file; its main program invokes no model, context, tokenizer or GPU API.
Its CPU-only build is inspection tooling, not a CPU inference fallback. The helper
has not been built or run here. Actual Windows compilation/linking and converter
behavior remain pending.

After separate source-acquisition/build approval, use the same verified runtime
source and approved toolchain. These builds share the **combined** 45-minute,
12-GiB-output, 24-GiB-memory and parallelism-2 build bounds; they do not create a
new allowance. CMake's existence check is not source identity verification.

**Windows PowerShell — desktop**, under the approved build supervisor:

```powershell
$GranitePackage = Join-Path $GraniteWorktree 'scripts\uc001_granite_contract_v1'
$GraniteInspectBuild = Join-Path $GraniteRoot 'native-schema-inspection-build'
$GraniteInspection = Join-Path $GraniteRoot 'native-schema-inspection-output'
if ((Test-Path $GraniteInspectBuild) -or (Test-Path $GraniteInspection)) { throw 'Fresh native-inspection paths required.' }
cmake -S (Join-Path $GranitePackage 'native-inspection') -B $GraniteInspectBuild -G Ninja -DCMAKE_BUILD_TYPE=Release "-DLLAMA_SOURCE_DIR=$GraniteSource"
if ($LASTEXITCODE -ne 0) { throw 'Native inspection configure failed; no automatic dependency acquisition.' }
cmake --build $GraniteInspectBuild --config Release --target granite-inspect-schema --parallel 2
if ($LASTEXITCODE -ne 0) { throw 'Native inspection build failed.' }
$GraniteInspector = Join-Path $GraniteInspectBuild 'bin\granite-inspect-schema.exe'
Get-FileHash -LiteralPath $GraniteInspector -Algorithm SHA256
New-Item -ItemType Directory -Path $GraniteInspection -ErrorAction Stop | Out-Null
$GraniteGrammar = Join-Path $GraniteInspection 'schema.gbnf'
$GraniteConversionErrors = Join-Path $GraniteInspection 'schema-conversion.stderr.txt'
& $GraniteInspector (Join-Path $GranitePackage 'schema.json') $GraniteGrammar 2> $GraniteConversionErrors
if ($LASTEXITCODE -ne 0) { throw 'Native schema conversion failed.' }
if (-not (Test-Path $GraniteGrammar) -or (Get-Item -LiteralPath $GraniteGrammar).Length -eq 0) { throw 'Native converter produced no grammar.' }
if (-not (Test-Path $GraniteConversionErrors) -or (Get-Item -LiteralPath $GraniteConversionErrors).Length -ne 0) { throw 'Native conversion warnings/errors are not accepted.' }
Get-FileHash -LiteralPath $GraniteGrammar -Algorithm SHA256
```

Preserve the helper/build/source/schema/grammar hashes and complete stderr result.
An exit code of zero alone is insufficient: unsupported constraints can produce
warnings or lose meaning. Before any model generation, a technical reviewer must
inspect the resulting grammar against `schema-audit.md` and the frozen schema,
checking retained constraints and rejecting any unexplained loss. Do not repair or
relax the schema/grammar to obtain apparent success. This model-free inspection
consumes no generation and establishes neither template behavior nor semantics.

## Future launch and assessment — separate owner approval required

Before launch, the owner must approve this exact frozen package, acquisition/build
artifacts, trustworthy supervisor, desktop readiness, numerical bounds and named
competent reviewers. Complete the external approval record using the package's
approval template; its initial false gates are not self-authorization. Keep the
approval and fresh API-key file outside the archive and frozen package. Never put a
key in a command argument, captured request, report, shell history or Git.

In the separately authorized approval record, set `assessment_start_utc` to the
actual timezone-qualified UTC instant immediately before the single server launch.
The client subtracts elapsed startup time from its thirty-minute budget and rejects
missing, future-dated or expired start times. This timestamp is an owner attestation,
not client verification of the server PID, hardware or supervisor.

Use an isolated clean child environment. If inherited `LLAMA_*` options are present,
stop rather than silently remove or accept them. Do not alter HOME or system paths.
All-layer GPU offload and actual runtime properties must be checked; the flag alone
is not evidence and can be ignored by a CPU-only build. No automatic CPU fallback,
port substitution, context fitting, source replacement or speculative draft model.

The following is the exact proposed **Windows PowerShell — desktop** server command,
executed once in the approved supervisor's model process, never here:

```powershell
$GraniteKeyFile = 'C:\Resolena\private\granite-v1-api-key.txt'
if (Get-ChildItem Env:LLAMA_* -ErrorAction SilentlyContinue) { throw 'Unreviewed LLAMA_* environment overrides; stop.' }
$GraniteServerArgs = @('--model', $GraniteModel, '--alias', 'uc001-granite-3.3-8b-v1', '--host', '127.0.0.1', '--port', '9931', '--api-key-file', $GraniteKeyFile, '--ctx-size', '8192', '--parallel', '1', '--gpu-layers', 'all', '--cache-type-k', 'f16', '--cache-type-v', 'f16', '--threads', '8', '--threads-batch', '8', '--batch-size', '256', '--ubatch-size', '128', '--flash-attn', 'off', '--no-context-shift', '--no-cont-batching', '--no-warmup', '--fit', 'off', '--offline', '--no-mmproj', '--no-webui', '--jinja', '--reasoning', 'off', '--reasoning-format', 'none', '--spec-type', 'none', '--n-predict', '4096', '--temp', '0', '--seed', '42', '--samplers', 'temperature')
& $GraniteServer @GraniteServerArgs
```

Request-level generation settings are frozen and sent/checked by the adapter; they
must not be silently changed to make a case fit or pass. Dynamic temperature range
is explicitly zero and its native echo is checked, preserving greedy selection.
Only known native echo
forms `none` / `none,none` are permitted for the explicitly disabled speculative
mode; neither permits a draft model. The actual model alias/properties, embedded
template/rendering, full prompt-plus-output token fit and native schema conversion
remain gates before any generation. A mock returning expected values passes none
of those real-runtime gates. There is no warm-up, dummy completion or automatic
health-check generation; health/props/template/tokenization remain non-generating.

In a second supervised **Windows PowerShell — desktop** process, from the verified
current-worktree transfer and approved Python environment:

```powershell
$GraniteWorktree = (Get-Location).Path
$GraniteKeyFile = 'C:\Resolena\private\granite-v1-api-key.txt'
$GraniteApproval = 'C:\Resolena\private\granite-v1-owner-approval.json'
$GraniteOutput = 'build/test-only/granite-v1-REPLACE-WITH-NEW-ID'
$env:PYTHONPATH = "$(Join-Path $GraniteWorktree 'src');$GraniteWorktree"
$env:RESOLENA_GRANITE_API_KEY = (Get-Content -LiteralPath $GraniteKeyFile -Raw).Trim()
python -m scripts.uc001_granite_contract_v1.assess --approval $GraniteApproval --output $GraniteOutput
$GraniteClientExit = $LASTEXITCODE
Remove-Item Env:RESOLENA_GRANITE_API_KEY -ErrorAction SilentlyContinue
if ($GraniteClientExit -ne 0) { throw 'Assessment stopped; preserve captures and stop the owned server.' }
```

For each printed `awaiting_review` event, the named competent reviewer must:

1. Open `cases.json` for that exact case, the unchanged
   `<output>/<case-id>/response.json` raw native envelope, and
   `<output>/<case-id>/structural-result.json`. Compare the original input and
   every frozen semantic obligation with the raw `content` and grounded
   interpretation. Structural `pass` is not a semantic or qualified-review pass.
   Do not edit the capture, reinterpret another case or ask the model for an
   explanation; that would be another inference.
2. Confirm that the printed `packet_sha256` identifies the UTF-8 raw `content`
   string, not the whole envelope or a reformatted JSON interpretation. Use that
   exact hash, current case ID and frozen bundle ID in the review receipt.
3. Copy `review-template.json` to a new staging file outside the frozen package,
   such as `<output>/reviews/<case-id>.pending`. Fill `reviewer`,
   `competence_basis` and `obligation_by_obligation_notes` from actual competent
   review. Set `semantic_status: "pass"` and `qualified_review_status: "confirmed"`
   only after the case's allowed outcome and all obligations are confirmed.
   Unsupported dialect success, changed quantities or lost meaning cannot become
   passing through a generic approval. Unavailable competence remains pending;
   a negative semantic decision remains failure.
4. Save complete UTF-8 JSON without a BOM, then atomically rename the staging file
   on the same volume to the printed path `<output>/reviews/<case-id>.json`.
   A same-volume `[System.IO.File]::Move(staging, final)` to a previously absent
   final path is suitable. Do not write incrementally to the polled `.json` file
   or overwrite an existing review. Only the final receipt is consumed.

The client proceeds only after its receipt checks pass. Missing/pending review,
failure or expiration of the 120-second review or global thirty-minute window
means STOP, preserve the raw/partial result and terminate the owned model server.
Do not extend the clock, preapprove future cases, relaunch or turn an unavailable
review into automatic acceptance.

The client must use the approved existing startup and never launch/relaunch a
server. Its thirty-minute timer cannot replace or extend the supervisor's clock
anchored at startup. Stop the owned server on failure/deadline/review stop or after
the final allowed case, confirm its exit, and preserve all partial artifacts. No
continuation, reset, second startup or other candidate follows without separate
owner authorization. Startup, completed generation, structural validity, semantics,
qualified review and application replay must remain separately recorded.

## Pinned primary-source basis

- [IBM immutable artifact metadata](https://huggingface.co/api/models/ibm-granite/granite-3.3-8b-instruct-GGUF/revision/e40e9dd739c7be00fa965c16ce167088190ce114?blobs=true).
- [Runtime build options](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/CMakeLists.txt).
- [Windows Vulkan build route](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/docs/build.md#vulkan).
- [Pinned runtime flags](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/common/arg.cpp).
- [Native server API](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/tools/server/README.md).
- [Grammar limitations](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/grammars/README.md).

These documentation/source findings are not native conversion, template, backend,
resource or semantic verification. No build, probe, transfer, startup or inference
was executed by preparation. Future authorization is separate from this package.
