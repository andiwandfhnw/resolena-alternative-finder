# Granite acquisition proxy preparation — 2026-10-25

## Bounded outcome A

The owner accepts the [earlier supervision blocker](../uc001-granite-supervision-preparation/README.md)
and explicitly permits conservative accounting of every upstream-to-client tunnel
byte, including TLS overhead, without subtracting an estimated payload overhead.
The frozen **10 GiB cumulative ceiling remains unchanged**. The [native build
procedure](../uc001-granite-native-build-preparation/README.md) remains accepted as
preparation only and is **not amended** by this supplement.

The standalone [proxy.py](../../scripts/uc001_granite_acquisition_proxy/proxy.py)
uses Python 3.12 standard-library sockets/selectors/JSON/filesystem operations only.
It never executes Git, acquires a model, decrypts TLS or changes certificates.
Its `fetch-spec` mode prints a reviewed command/environment delta without executing
it. No package installation is required.

One selector thread owns the loopback listener and all tunnel sockets. Each raw
upstream `recv` is bounded by the current remaining allowance; the same thread
increments the integer counter and writes/fsyncs the ledger before queueing those
bytes toward Git. There is no upstream reader/transport with independent read-ahead.
Concurrent and sequential tunnels share that one counter. Thus:

`Git payload delivered <= upstream bytes durably charged + prior charge <= 10 GiB`.

Undelivered bytes already charged are never refunded. At the exact ceiling the
proxy immediately fails/closes all tunnels, without reading an extra sentinel byte
or forwarding the final charged chunk. This conservative resource stop is not a
successful acquisition. Bytes buffered outside the application's socket reads are
not represented as a whole-machine traffic measurement or Git payload estimate.

## Fail-closed behavior and evidence

- Listener is IPv4 **127.0.0.1 only**, allocated port; Windows exclusive-address use.
  Production CLI permits CONNECT only to **github.com:443**. No forwarding proxy,
  redirect target or alternate acquisition URL is accepted. Invalid requests fail
  all tunnels. Eight active tunnels, bounded headers/buffers and a CONNECT timeout
  are implementation safety stops, not additional acquisition allowances.
- Every upstream socket is owned/tracked before connecting; there is no automatic
  connection-address retry. Normal FIN ends one tunnel without resetting its charge.
  Socket error, unavailable upstream, unknown accounting or ledger failure closes
  all tunnels. Cleanup checks all tracked sockets, not just an empty tunnel map.
- A new ledger is opened exclusively; existing/partial evidence is never overwritten
  or resumed. Every JSONL record includes UTC/monotonic timestamps, tunnel ID,
  destination, per-tunnel bytes and cumulative bytes. Start/clock/listening records,
  debits, tunnel ends and terminal status are retained. On a failed write/fsync,
  newly read bytes are not forwarded; the result is unknown/failure, never zero/pass.
  Missing/malformed terminal evidence also means failure/unknown.
- A hash-bound owner-supplied prior accounting receipt is mandatory: explicit owner,
  bundle identity, `accounting_complete: true` and integer `previously_charged_bytes`.
  No default zero or fresh 10-GiB allowance is created. The [template](prior-budget.template.json)
  is deliberately unusable until completed/reviewed; it is not execution evidence.
  Prior unknown acquisition cannot be certified as zero or retried under a new ledger.
- The original acquisition start is supplied once and ledgered; proxy startup does
  not reset the 30-minute budget. The private stdin control channel accepts only
  `CLOSE` followed by newline. EOF/invalid control is failure. A clean close reports
  `meter_closed_unqualified`, not a successful fetch/build or interpreter acceptance.

## Explicit Git binding and bypass conditions

The source remains `https://github.com/ggml-org/llama.cpp.git`, fetched at commit
`620d2225cc436ab0b001e3200e590e3b286ef9ab`. Existing commit/tree verification,
`git fsck --full --strict`, `git archive` and ZIP/hash records remain required and
unchanged. No GitHub ZIP/API route replaces Git fetch.

`git_fetch_spec` validates the fresh auxiliary repository's minimal raw configuration,
exact origin URL/refspec and absence of unexpected sections/options/worktree config or common-directory/Git-directory redirects.
It removes inherited GIT variables, all case variants of proxy environment variables
(including NO_PROXY), SSH_ASKPASS and CURL_HOME from the child environment. Empty
private global/system config files and empty hooks isolate inherited configuration.
Both command-local `http.proxy` and `remote.origin.proxy` name the exact loopback
listener. Redirects are disabled, only HTTPS transport is permitted, credential
helpers are cleared and TLS verification stays enabled. No permanent Git/environment
configuration changes are made. A redirect, unexpected config/header/host or proxy
connection failure stops; do not fix it by bypassing the meter.

[Git's documented proxy/remote/URL settings](https://git-scm.com/docs/git-config/2.53.0),
[the discovered Windows Git's proxy code](https://raw.githubusercontent.com/git-for-windows/git/v2.53.0.windows.2/http.c)
and [libcurl NO_PROXY semantics](https://curl.se/libcurl/c/CURLOPT_NOPROXY.html)
confirm why that isolation is necessary. `NO_PROXY`, empty/per-remote/per-URL proxy
overrides, URL rewrites, inherited includes/custom helpers and modified executables
would invalidate binding if allowed. They are excluded/rejected by this prepared
route; this is not an OS egress sandbox against a malicious replacement Git/helper
or another actor modifying the fresh files between validation and execution.
Auxiliary OS certificate-validation/DNS traffic is not claimed as tunnel payload.

## Private Job Object integration — required before execution

The external controller retains its private, non-inherited job handle and creates
one owned phase worker **suspended**, assigns it successfully, prohibits breakaway,
sets kill-on-job-close, then resumes it. The proxy and Git launched by that worker
inherit membership; nested acquisition/configure/build descendants remain owned.
The controller stays outside its job and independently observes proxy/worker exits,
ledger health, resources and the global clocks. Any breach/error/unknown requires
terminating that job only, waiting for all owned exits/active-job count zero and
recording cleanup result. Never identify victims by process names.

The proxy's synchronous DNS and fsync can block its thread: its own timer is not a
replacement for the external controller. That controller must kill the owned job
if observations become stale, proxy startup/exit fails or cleanup is unverified.
Abrupt termination can leave a partial ledger; preserve it as unknown, without retry.
The controller sends CLOSE only after Git finishes, then requires proxy exit 0,
complete terminal ledger, verified socket/job cleanup, unchanged source identity and
all other checks before considering acquisition successful.

All other bounds stay exact: acquisition **1800 s / 10737418240 bytes cumulative**;
configure + build **2700 s** combined; process-tree memory **25769803776 bytes**;
build output **12884901888 bytes**; initial free disk **>=51539607552 bytes**;
stop below **8589934592 bytes** disk or **4294967296 bytes** OS free memory;
outer parallelism **2**. No phase/retry resets. The full controller is not supplied
or verified by this proxy task; acquisition/build readiness remains gated on it.

## Future Windows owner invocation — NOT EXECUTED / NOT AUTHORIZED TO RUN NOW

Copy only the reviewed helper outside the freeze to
`C:\Users\AndiWand\Downloads\granite-acquisition-proxy-v1\proxy.py`.
Use the existing separate Granite Python, existing Git and unchanged fresh native
root. No installer, archive regeneration or frozen-worktree edit is needed.
The following is the exact **future integration draft**, to be launched by the
approved controller inside its already assigned/resumed phase worker. It is not a
standalone replacement for that controller. Review/approval of this preparation
alone does not authorize the commands or any acquisition.

**Windows PowerShell — controller-owned activated worker, proxy startup.**
The prior receipt must already be completed/reviewed at the path shown. Set the
acquisition clock exactly once before the first acquisition operation; retain the
same value if any preceding initialization already started that clock. Do not reset
it after errors. All paths below are explicit; no persistent PATH/config changes.

```powershell
$ErrorActionPreference = 'Stop'
$GranitePython = 'C:\Users\AndiWand\Downloads\granite-python-3.12.11-20250702\env\Scripts\python.exe'
$GraniteProxyScript = 'C:\Users\AndiWand\Downloads\granite-acquisition-proxy-v1\proxy.py'
$GraniteGit = 'C:\Program Files\Git\cmd\git.exe'
$GraniteRoot = 'C:\Resolena\gn1-20261025'
$GraniteRepo = Join-Path $GraniteRoot 'source-repository'
$GraniteEvidence = Join-Path $GraniteRoot 'evidence'
$GranitePrior = 'C:\Users\AndiWand\Downloads\granite-acquisition-proxy-v1\prior-budget.json'
$GranitePriorHash = (Get-FileHash -LiteralPath $GranitePrior -Algorithm SHA256).Hash.ToLowerInvariant()
if ((Get-FileHash -LiteralPath $GraniteProxyScript -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'a7c62f83356636bea839633382bb62a3e53bcce466caea7b32226cece1e7bb1d') { throw 'Proxy helper hash differs: stop.' }
# The controller supplies its original start as an ISO8601 timezone-bearing string.
# Create it once with [DateTimeOffset]::UtcNow.ToString('o') at the original start.
if (-not $GraniteAcquisitionStartedUtc) { throw 'Original acquisition clock is required.' }
$GraniteMeterStart = New-Object System.Diagnostics.ProcessStartInfo
$GraniteMeterStart.FileName = $GranitePython
$GraniteMeterStart.Arguments = '-I "' + $GraniteProxyScript + '" --ledger "' + (Join-Path $GraniteEvidence 'acquisition-proxy.jsonl') + '" --prior-receipt "' + $GranitePrior + '" --prior-sha256 ' + $GranitePriorHash + ' --acquisition-started-utc ' + $GraniteAcquisitionStartedUtc
$GraniteMeterStart.UseShellExecute = $false
$GraniteMeterStart.RedirectStandardInput = $true
$GraniteMeterStart.RedirectStandardOutput = $true
$GraniteMeterStart.RedirectStandardError = $true
$GraniteMeter = New-Object System.Diagnostics.Process
$GraniteMeter.StartInfo = $GraniteMeterStart
if (-not $GraniteMeter.Start()) { throw 'Proxy failed to start.' }
$GraniteMeterErrFile = [IO.File]::Open((Join-Path $GraniteEvidence 'proxy.stderr.log'), [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
$GraniteMeterErrors = $GraniteMeter.StandardError.BaseStream.CopyToAsync($GraniteMeterErrFile)
$GraniteReadyLine = $GraniteMeter.StandardOutput.ReadLine()
$GraniteReadyLine | Set-Content -LiteralPath (Join-Path $GraniteEvidence 'proxy-ready.json') -Encoding UTF8
$GraniteReady = $GraniteReadyLine | ConvertFrom-Json
if ($GraniteReady.pid -ne $GraniteMeter.Id -or $GraniteReady.proxy_url -notmatch '^http://127\.0\.0\.1:[0-9]+$') { throw 'Proxy readiness/ownership differs.' }
$GraniteMeterOutput = $GraniteMeter.StandardOutput.ReadToEndAsync()
```

**Same owned Windows worker — print/validate the isolated fetch specification.**
The existing init/origin setup must have succeeded in the fresh native root under
this same controller. The empty paths below must not exist; no prior evidence is
replaced. The printed specification is metadata, not execution.

```powershell
$GraniteEmptyConfig = Join-Path $GraniteEvidence 'proxy-empty.config'
$GraniteEmptyHooks = Join-Path $GraniteEvidence 'proxy-empty-hooks'
if ((Test-Path -LiteralPath $GraniteEmptyConfig) -or (Test-Path -LiteralPath $GraniteEmptyHooks)) { throw 'Fresh private config/hooks required.' }
$null = New-Item -ItemType File -Path $GraniteEmptyConfig
$null = New-Item -ItemType Directory -Path $GraniteEmptyHooks
$GranitePort = ([Uri]$GraniteReady.proxy_url).Port
$GraniteSpecJson = & $GranitePython -I $GraniteProxyScript fetch-spec --git $GraniteGit --repo $GraniteRepo --proxy-port $GranitePort --empty-config $GraniteEmptyConfig --empty-hooks $GraniteEmptyHooks
if ($LASTEXITCODE -ne 0) { throw 'Unreviewed Git route/configuration: stop.' }
$GraniteSpecJson | Set-Content -LiteralPath (Join-Path $GraniteEvidence 'source-fetch.proxy-spec.json') -Encoding UTF8
$GraniteSpec = $GraniteSpecJson | ConvertFrom-Json
```

**Same owned worker — future fetch, then close the meter.**
This replaces only the acquisition invocation in a future approved integration;
**the accepted procedure is not edited now**. These fixed arguments contain no
embedded quotes/trailing backslashes; unexpected forms stop rather than guessing
Windows quoting. The external controller must independently monitor both children
and terminate its owned job if this worker throws or blocks.

```powershell
$GraniteFetchStart = New-Object System.Diagnostics.ProcessStartInfo
$GraniteFetchStart.FileName = $GraniteSpec.argv[0]
if ($GraniteFetchStart.FileName -ne $GraniteGit) { throw 'Git executable differs.' }
$GraniteFetchArguments = @($GraniteSpec.argv | Select-Object -Skip 1)
if (@($GraniteFetchArguments | Where-Object { $_.Contains('"') -or $_.EndsWith('\') }).Count) { throw 'Unreviewed argument quoting.' }
$GraniteFetchStart.Arguments = ($GraniteFetchArguments | ForEach-Object { '"' + $_ + '"' }) -join ' '
$GraniteFetchStart.UseShellExecute = $false
$GraniteFetchStart.RedirectStandardOutput = $true
$GraniteFetchStart.RedirectStandardError = $true
foreach ($GraniteKey in $GraniteSpec.environment_remove) { $GraniteFetchStart.EnvironmentVariables.Remove($GraniteKey) }
foreach ($GraniteProperty in $GraniteSpec.environment_set.PSObject.Properties) { $GraniteFetchStart.EnvironmentVariables[$GraniteProperty.Name] = $GraniteProperty.Value }
$GraniteFetch = New-Object System.Diagnostics.Process
$GraniteFetch.StartInfo = $GraniteFetchStart
if (-not $GraniteFetch.Start()) { throw 'Git fetch failed to start.' }
$GraniteFetchOutFile = [IO.File]::Open((Join-Path $GraniteEvidence 'source-fetch.stdout.log'), [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
$GraniteFetchErrFile = [IO.File]::Open((Join-Path $GraniteEvidence 'source-fetch.stderr.log'), [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
$GraniteFetchOutput = $GraniteFetch.StandardOutput.BaseStream.CopyToAsync($GraniteFetchOutFile)
$GraniteFetchErrors = $GraniteFetch.StandardError.BaseStream.CopyToAsync($GraniteFetchErrFile)
while (-not $GraniteFetch.WaitForExit(100)) { if ($GraniteMeter.HasExited) { throw 'Proxy exited during acquisition: terminate owned job.' } }
$GraniteFetchOutput.GetAwaiter().GetResult()
$GraniteFetchErrors.GetAwaiter().GetResult()
$GraniteFetchOutFile.Flush($true)
$GraniteFetchErrFile.Flush($true)
$GraniteFetchOutFile.Dispose()
$GraniteFetchErrFile.Dispose()
if ($GraniteFetch.ExitCode -ne 0 -or $GraniteMeter.HasExited) { throw 'Fetch/proxy failure: terminate owned job, preserve artifacts; no retry.' }
$GraniteMeter.StandardInput.WriteLine('CLOSE')
$GraniteMeter.StandardInput.Flush()
if (-not $GraniteMeter.WaitForExit(5000)) { throw 'Proxy cleanup unverified: terminate owned job.' }
$GraniteMeterOutput.Result | Set-Content -LiteralPath (Join-Path $GraniteEvidence 'proxy-close.json') -Encoding UTF8
$GraniteMeterErrors.GetAwaiter().GetResult()
$GraniteMeterErrFile.Flush($true)
$GraniteMeterErrFile.Dispose()
$GraniteClosed = $GraniteMeterOutput.Result | ConvertFrom-Json
if ($GraniteMeter.ExitCode -ne 0 -or $GraniteClosed.status -ne 'meter_closed_unqualified' -or $GraniteClosed.cleanup_verified -ne $true) { throw 'Meter failed or cleanup unknown.' }
```

Stop for review after returning the complete ledger, ready/close records, command
spec, source/build-controller ownership/exits, timestamps, stdout/stderr and source
identity/integrity/archive records. Do not automatically configure/build. PIDs,
job containment, source hashes and Windows success are unknown until actual owner
execution. On any failure retain partial artifacts/ledger and all available logs;
no retry, guessed zero, alternate host/route, install or silent configuration repair.

## Offline verification and evidence limits

[Focused tests](../../tests/unit/test_granite_acquisition_proxy.py): **36 passed**
on Codespace Python 3.12.11, using loopback/socketpair synthetic traffic only.
The two real Git probes use a temporary auxiliary repository and a synthetic
loopback HTTPS target, never GitHub. Linux Git was **2.50.1**; Windows owner Git
**2.53.0.windows.2** was source-reviewed, not executed. The unavailable-proxy case
asserted nonzero Git exit and no direct target connection despite inherited
NO_PROXY. The available-proxy case confirmed CONNECT and metered a synthetic TLS
alert; it did not transfer objects or establish Windows TLS/native compatibility.

Tests cover simultaneous/sequential aggregation; exact limit and prevented extra
byte; prior credit; chunks; binary transparency both ways; upstream/client EOF;
ledger write/fsync failure before forwarding; close-all on budget/error; active
cleanup; rejected destinations/config bypasses; original clock; controller EOF and
clean close; existing-ledger preservation; safe command emission and both Git probes.

RED: [missing helper](red-tests.log); [cleanup race/clock failure](red-additional.log);
[missing controller/spec CLI](red-control.log);
[common-directory/symlink redirect rejection](red-config-redirect.log). Intermediate GREEN logs are retained;
final [green-final-hardened.log](green-final-hardened.log) reports 36 passes. Exact command
for each focused run: `.venv/bin/python -m pytest -q tests/unit/test_granite_acquisition_proxy.py`,
with stdout/stderr redirected to its named new log. No unrelated test suite reran.
The receipt [verification.json](verification.json) records hashes/checks and limits.
No native procedure, frozen files, Python environments, SDK/tool pins, application
code, earlier receipts or historical evidence changed. No acquisition/configure/
build/GPU/model action, new dependency or Git delivery. PHASE: 3 / STATUS: in-progress.
Priority 5 acceptance/closed Qwen result unchanged; Priorities 3/4 partial,
Priority 6/Phase 4 pending. Stop for owner review.

Preparation checks: Python syntax, local links/anchors/fences and new whitespace
passed; all three PowerShell blocks passed syntax-only parsing, with no block run.
All 832 previously protected files outside TASKS and all 80 prior Granite files
retain their fingerprints (overlapping counts are not added). Earlier TASKS entries
and Priority 5 history, Git HEAD/branch/index and existing status entries remain.
Only the new helper/test/artifacts and current TASKS summary/appended entry changed.
`git diff --check` exits 2 only for the historical TASKS trailing space, now line 2598.
