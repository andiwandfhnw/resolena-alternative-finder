# UC-001 Priority 3: offline preparation

Preparation authorized 2026-10-16. **No live execution or transport installation
is authorized.** Priority 3 is partial; Phase 3 stays in-progress. Normal
`app.main` stays unconfigured. Do not run the historical experiment harness.

The retained Qwen3-8B Q8_0 / llama.cpp b11429 Vulkan configuration is a test
candidate only. Closed v2.0.1 achieved 5/6 strict exposed cases; the Spanish
negative control was wrongly understood as English. Exact quotes and prior
calibration success do not establish complete understanding. The richer contract,
8192-token context, 3072-token output, runtime schema compatibility, transport and
live resource fit remain unverified. No detector is configured or proposed.

`config.json`, `prompt.txt`, generated `schema.json`, `cases.json`, runtime pins and
scripts are frozen in `freeze.json`; application source and synthetic fixture
hashes are also checked in the Codespace. Historical results remain untouched.
The Windows ZIP contains this directory only, without models, keys or held-out cases.

## Expected meanings and review

The fixed 14 cases are exposed synthetic development inputs, one generation each
in manifest order. Expectations are **AI-generated, qualified review pending**.
`review-template.json` is an unapproved template, not a review. Before inference,
competent DE/FR/IT/EN reviewers must approve exact expectations and permissible
normalizations against the frozen bundle, with names/roles, demonstrated language
competence, date, artifact hash and corrections. Save the separately approved
receipt as `build/test-only/contract-review.json`. A new requirement conflict stops
preparation for owner resolution; do not amend accepted requirements.

- Case 9 `Velo` is meaning-ambiguous: bicycle in Swiss German / veil in Italian.
  L-02/03 require targeted meaning clarification. Country or an explanation
  preference cannot choose the object. The architecture's bicycle example is
  explicitly conditional on understanding that meaning; no requirement conflict.
  Existing synthetic `Velo` tests stipulate bicycle meaning to test a conditional
  policy; they do not establish understanding of this real ambiguous input.
- Cases 7/8 may proceed only with complete mixed meaning. L-03 also permits honest
  targeted clarification or a capability limitation for unresolved meaning.
  Those safe outcomes record a suitability gap, not a successful interpretation.
  A clear supported primary selects the explanation language; otherwise an
  understood mixture uses preference/browser/one-time choice. Language uncertainty
  alone must not be reported as meaning uncertainty or unsupported input.
- Case 10 has clear English but an unresolved `1,200` magnitude. L-02 forbids a
  guess. Either `needs_clarification`, or a packet retaining `amount=null`, must
  route to targeted clarification before any language choice or saving.
- Dialect support is not promised. Case 12 may limit/clarify; a claim of complete
  understanding needs competent dialect review, including negation. A `de` label
  does not establish it. No dialect acceptance requirement was added.

Structural checks enforce schema, exact quotations/occurrences, source coverage,
references and typed quantities. They cannot detect every semantic omission,
incorrect normalization, polarity, numeric convention or language hypothesis.
Qualified review must compare every original clause/action/constraint/scope with
the decoded packet, separately from routing. Do not use detector agreement,
machine labels, English normalization or schema success as linguistic approval.

## Adapter and application boundary

The HTTP adapter sends only the original text, frozen instructions/schema and
settings. It uses the retained server's schema-constrained `json_object` envelope
with the full frozen schema. Trusted original text and adapter/prompt versions are supplied locally;
the model cannot set them. Exact quote plus 1-based occurrence maps to Python
Unicode code-point offsets, counting overlapping matches, without fuzzy repair.
All fields are decoded strictly; malformed JSON, duplicate keys, coercions,
truncation, changed currency/precision and detectable missing spans/items stop.
No retry, repair, fallback, language keyword gate or fabricated missing meaning.

Only `run.py` composes the candidate with isolated **synthetic** evidence and the
existing **English-only test renderer**. Recognizer is disabled. Country and
preferences stay outside interpreter requests. Cases 1/5/10 traverse the actual
FastAPI/application/SQLite composition in-process, without a browser or separate
API listener. Other cases assess the adapter and application language policy.
Captured packets are replayed through preference/browser/correction paths without
new model calls. Existing offline tests cover the conditional understood/shared
path; the ambiguous `Velo` case cannot demonstrate that path in a real interpreter.

Understandable DE/FR/IT packets select their own supported language. Unavailable
English-test-renderer targets are `rendering_unavailable`, never evidence of
unsupported input. Interpretation is assessed before renderer availability;
faithful four-language rendering remains Priority 4. Saving still requires full
preparation, atomic commit and immutable snapshots before presentation. No real
knowledge, location-reference preparation or real-world coverage is introduced.

## Transport installation plan — proposed only

Desktop Windows and remote Codespace have separate hardware/filesystems/localhost.
The model would run on the owner desktop; Codespace inference is not planned.
Authenticated SSH reverse forwarding would connect Windows `127.0.0.1:49187` to
Codespace `127.0.0.1:49188`. The pinned GitHub CLI uses local SSH bridge 49189
(`--server-port` is the **local bridge**, not a remote sshd port). Actual remote
SSH listener identity/binding must be inspected after connection; a wildcard bind
stops before generation. No public model endpoint or Codespaces public port is used.

The exact cached Debian 12 amd64 solver plan is `transport-plan.json` (versions,
archive byte sizes and SHA-256). No package has been fetched or installed:

| Packages | Version | Archive bytes |
|---|---|---:|
| openssh-server | 1:9.2p1-2+deb12u10 | 456,584 |
| openssh-client | 1:9.2p1-2+deb12u10 | 993,532 |
| openssh-sftp-server | 1:9.2p1-2+deb12u10 | 65,928 |
| libssl3 | 3.0.22-1~deb12u1 | 2,039,240 |
| libssl-dev | 3.0.22-1~deb12u1 | 2,449,908 |
| openssl | 3.0.22-1~deb12u1 | 1,442,052 |
| libwrap0 | 7.6.q-32 | 54,936 |
| runit-helper | 2.15.2 | 6,520 |

Total **7,508,700 bytes**, four new packages/four updates, approximately 2,222 kB
additional installed space. OpenSSL development/CLI updates result from the solver
and existing installed packages, not a general system upgrade. Stop if the solver,
signed-index availability or required package hashes differ; no unpinned substitution.

Windows needs existing native OpenSSH and GitHub CLI **2.81.0**. If gh is absent or
different, the proposed portable `gh_2.81.0_windows_amd64.zip` is **18,317,085 bytes**,
SHA-256 `8f5a19ee2271d20477c5c8d8204b65cd0ff6d73279417f5cdab49135516ca1b5`.
Extract to a separate directory and use that directory on this shell's PATH only;
no MSI/global replacement. Maximum planned transport acquisition is **25,825,785
bytes**, below the proposed 100 MiB cap; zero model/runtime downloads.
Native Windows OpenSSH version/availability remains a desktop preflight dependency.
If absent, stop: no OS-dependent capability download size or installation is invented.
GitHub CLI account authorization is a separate prerequisite; no token inspection.

After separate installation approval, prevent default sshd service autostart using
a temporary root-owned `policy-rc.d` returning 101 (preserve/restore any existing
policy; do not replace an existing restrictive policy). Install only the eight
exact specs above using `apt-get --no-install-recommends`, after matching the
simulated/printed-URI plan to the frozen manifest. Configure an sshd drop-in:
`ListenAddress 127.0.0.1`, `GatewayPorts no`, `PasswordAuthentication no`,
`KbdInteractiveAuthentication no`, `PubkeyAuthentication yes`,
`AllowTcpForwarding remote`, `PermitListen 127.0.0.1:49188`.
Validate `sshd -t`/effective configuration before allowing the CLI to start SSH.
The gh-managed startup may use its own configuration: actual binding/forwarding
must pass the runner's inspection; compatibility is pending, never assumed.
Preserve the existing Codespace/devcontainer; no image rebuild or workstation
restart is planned. Processes using replaced OpenSSL may need a separately agreed
restart. Do not restart the current application/editor or delete existing work.

Publisher references: [pinned server interface](https://github.com/ggml-org/llama.cpp/blob/d81235049384534c167caea52b85a694f6103d14/tools/server/README.md),
[pinned CLI SSH implementation](https://github.com/cli/cli/blob/v2.81.0/pkg/cmd/codespace/ssh.go),
[CLI release](https://github.com/cli/cli/releases/tag/v2.81.0),
[reverse forwarding](https://man.openbsd.org/ssh#R).

## Commands by execution location

**Windows PowerShell 5.1 — next read-only preflight only.** Privately copy/extract
the prepared `build/uc001-contract-preparation/windows-preparation.zip` to
`C:\ResolenaExperiments\uc001-contract-v1` first; no model transfer. Then:

```powershell
powershell.exe -NoProfile -File C:\ResolenaExperiments\uc001-contract-v1\Preflight-Windows.ps1
```

This rehashes retained model/runtime/ZIP/DLL assets, reads active-device 64-bit
registry capacity, WDDM usage, RAM/disk/ports
and client versions, and prints JSON. It creates no files, installs nothing,
starts no model/runtime or tunnel, changes no execution policy and inspects no
credentials. Allow the 8.71 GB model hash read to finish. There is no native
compilation or asset-binary execution in preflight. Missing capacity or an
ambiguous active-device/WDDM association stops; never use truncated 32-bit
`AdapterRAM` or assume 16 GiB. The future live launcher independently uses DXGI.

**Codespaces Bash — read-only preparation preflight:**

```bash
bash scripts/uc001_contract_check/Preflight-Codespace.sh
```

The simulated package plan is not an install command. No `sudo`, network query,
package-index update, rebuild or tunnel is performed by that script.

**Windows PowerShell — future live command, NOT AUTHORIZED NOW:**

```powershell
powershell.exe -NoProfile -File C:\ResolenaExperiments\uc001-contract-v1\Run-Windows.ps1 -Execute -Codespace ACTUAL_CODESPACE_NAME
```

The launcher sends an ephemeral model key through SSH stdin and the server's
process environment, not command arguments or saved artifacts. Both HTTP clients
bypass proxies and redirects. Protected `/v1/models` must reject missing/wrong keys
and accept the correct key at desktop and forwarded endpoints. **Public `/health`
is never authentication evidence.** Forwarding uses `ExitOnForwardFailure=yes`,
keepalives and connection timeout; runner checks actual listeners before generation.
The remote command runs `run.py`; do not launch an unrelated API/browser/model test.

## Frozen limits and stop conditions

| Guard | Enforcement |
|---|---|
| One startup; at most 14 generations, fixed order | A preserved Windows directory keyed by freeze hash blocks reuse. Codespace attempt ledger is created exclusively and fsynced before each HTTP generation. No resume/reset or replacement candidate. |
| 40 min total; 25 min model activity including load/transport; 90 s readiness; 90 s per request | Windows supervisor and owned process job; independent Codespace wall-clock deadline and per-case alarm. Readiness may poll metadata until deadline; it never restarts or retries generation. |
| RSS <=16 GiB, owned GPU <=12 GiB | Windows WDDM/process samples approximately every second. Full 37/37 Vulkan offload and positive owned allocation required; CPU host buffers may exist. No CPU fallback. |
| Free RAM >=4 GiB, free GPU >=2 GiB, free disk >=5 GiB | Windows sampling. Start requires RAM20/GPU14/disk6 GiB. Capacity-minus-WDDM usage measures sampled allocation, not guaranteed residency. |
| New artifacts <=1 GiB combined | 512 MiB sub-cap on each machine; retained assets excluded. Sampling is not a hard OS memory/quota guarantee. |
| Actual settings and context | Current owned startup log plus authenticated props must establish build/model, slots/context8192, threads2, batch/ubatch64, KVf16, sampling/output3072 and 37/37 Vulkan offload. `--fit off`, no warmup generation, no prompt caching. Missing proof stops. |
| Prompt-token fit | For every request, use the same non-thinking chat template and actual tokenizer before generation; full prompt +3072 <=8192. Require non-thinking template marker and matching reported prompt usage. No truncation or allowance reduction. |

Machine-detectable failures (pins, auth, forwarding, limits, configuration proof,
token fit, JSON/schema/grounding, incomplete finish, declared-state/API-route mismatch,
known unsupported-control failure) stop immediately and preserve partial results.
Windows closes an owned kill-on-close job containing only its new server/transport
subtrees; no process-name killing or retained-asset deletion. SSH/session teardown
ends its remote runner; provider-managed sshd lifecycle is separate, and must be
documented after transport validation rather than killing an unrelated daemon.
An API mismatch may expose a synthetic normalization/qualification mapping gap;
that is not automatically a model semantic error. Preserve both forms for diagnosis.

Semantic errors not detectable from declarations are reviewed **after** the fixed
pass. Any omission, wrong scope/polarity/amount/language or unsafe outcome rejects
suitability to proceed; no automatic tuning or rerun. Honest unresolved mixed
meaning remains a coverage gap. Real suitability requires qualified semantic
review, correct independent application routing and operational evidence. Even a
successful bounded check does not establish general DE/FR/IT/EN support, faithful
rendering, held-out performance or increment completion. Paid infrastructure and
external LLM processing are excluded; existing Codespace use/desktop electricity
and GitHub-controlled SSH access remain operational costs/data-boundary dependencies.

## Offline verification

Run project pytest regressions and frontend lint/build in Codespaces. Adapter tests
use `httpx.MockTransport`; PowerShell tests parse scripts and exercise pure guards
with synthetic samples, never invoke Windows preflight/launcher. No browser behavior
changes, so existing browser journeys are the regression check. No model binary,
network inference, detector, download, install or held-out access is needed.
