# Calibration B — approved 2026-10-11

Owner-approved follow-up to the [preserved failed smoke and diagnosis](../restart_2026_10_11/REPRODUCE.md).
cases.json freezes six expectations and twelve paired requests at temperatures .7
and 0, seed 42; first temperature alternates by case. Original system prompt,
schema, model/runtime pins, all other sampling/context settings and validator/scorer
stay unchanged. The report supplements the unchanged scorer with explicit expected
status/language/meaning/constraint checks so unsupported cannot hide classification
errors. C1 is observed calibration reuse; none of these results is unseen validation.

Before loading, acquire the shared artifact lock, check for active owned processes,
verify retained binary/model and all frozen inputs, and recheck RAM/disk. Reuse
workspace artifacts; new Git-ignored workspace storage holds this run's socket,
trace and full log. Never download, rebuild, retry, tune or run heldout evaluation.
Freeze all inputs/order before execution. Exact-string calibration/holdout overlap
is checked locally without displaying holdout text or sending it to a model.

Fifteen minutes from execution start including loading, readiness at most 90s,
45s/request, existing 6 GiB scratch/3.25 GiB owned RSS and available/preflight RAM
guards. Stop immediately on startup, transport, timeout or resource failure;
save semantic failures and continue only the fixed remaining plan within budget.
Capture each complete request body, HTTP status/headers/raw response, parsed result,
finish reason, usage/cache and server timing fields, plus available runtime
properties/template diagnostics. Write started/completed status and resources
incrementally. Preserve all previous results and reusable artifacts through closeout.

Success requires all six temperature-zero results to satisfy unchanged validation
and explicit frozen expectations. Failure stops this configuration pending review.
Success grants no reliable multilingual-support claim or automatic evaluation.
DESIGN remains Phase 2/in-progress with final acceptance pending. No production,
dependency, staging, commit, push or deployment work is authorized.

## Actual closeout

Inputs/order were frozen; the five synthetic reporting checks passed, and local
hash comparison found no exact overlap with the 55 heldout case texts. Binary/model
hash verification and the owned-process check passed. The runner exited 1 at the
preflight RAM/disk guard before loading, creating no server/socket workspace and
starting no timed window. No request was sent at either temperature.

Read-only inspection at 15:36:20 Europe/Berlin observed 3,933,028,352 bytes (3.66 GiB)
available RAM against the unchanged 4,026,531,840-byte (3.75 GiB) preflight minimum;
disk had 24,158,359,552 bytes free against the 6 GiB reserve. These are subsequent
observations, not exact values captured at the guard. The observed RAM shortfall
was 93,503,488 bytes. No unrelated process was stopped and no guard was relaxed.

[results.json](results.json) lists every case/temperature as not_run: status,
meaning, constraints, quotes, finish reason, cache, token counts and timings are
unmeasured. This is a resource stop, not model semantic failure or evidence about
temperature. [execution.json](execution.json) closes this one-shot attempt and
prevents accidental repetition; [closeout.json](closeout.json) preserves the stop.
No download/build/retry occurred. All frozen hashes and the original failed smoke
match, and reusable artifacts remain intact. No heldout data reached a model.
Calibration success is not established; stop this configuration pending review.
DESIGN remains pending and no evaluation, tuning or Git delivery follows.

## Memory preflight diagnosis — 2026-10-11

[Read-only measurements](memory_diagnosis.json) at 15:50:49 Europe/Berlin show
7.76 GiB host/VM RAM, 3.65 GiB MemAvailable and no swap. The visible cgroup reports
2.76 GiB current/4.58 GiB historical peak usage, memory.max/high=max and zero
max/oom/oom_kill events. Current pressure averages are negligible; historical
reclaim/stall counters exist but do not establish OOM or explain the calibration
failure. The namespace hides host ancestors, so an effective parent limit cannot
be ruled out. MemAvailable is a host/VM estimate including reclaimable cache,
not cgroup-specific headroom ([kernel documentation](https://www.kernel.org/doc/html/latest/filesystems/proc.html),
[cgroup accounting](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html)).

The hard-coded preflight threshold exactly equals 3.25 GiB owned-RSS cap plus
0.5 GiB reserve. This is an inferred conservative full-cap fit rationale; no
explicit original derivation was recorded. One 2.08 GiB smoke peak is not a proven
upper bound for calibration/context workloads. These accounting measures differ;
neither the cap nor preflight is reserved RAM. The later 3.66 GiB observation
remains distinct from the unknown exact failure-time sample.

Largest visible consumers belong to vscode: extension host PID 5427 ~725 MiB RSS,
Pylance 6183 ~460 MiB, Codex server 5614 ~183 MiB, VS Code server 257 ~166 MiB.
No experiment process remains. Orphaned collect-only pytest PIDs 3372/3383 have
PPID 1, no children, unchanged CPU counters and wait_for_partner; they appear to
be stalled VS Code discovery, not running model evaluation. They are candidates
for owner-confirmed cleanup, with only ~60 MiB private memory to reclaim—less than
the current ~104 MiB shortfall. Active IDE services are not confirmed unneeded.
Recommendation: a larger-memory environment for a future separately authorized
calibration; keep the guard unchanged. No process was stopped or resource upgraded.

Operational improvement: memory_preflight.py records UTC, the exact compared
MemAvailable sample, disk value, both thresholds, individual failed guards and
visible cgroup context. Four synthetic boundary/failure checks passed.
calibrate_with_recorded_preflight.py substitutes only that guard block when
loading the original frozen runner; a load-only check passed without calling main.
The old source/freeze/results remain intact. This is a future entry point, not a
rerun authorization; the existing execution marker still refuses another attempt.
Record/freeze these operational additions in any separately authorized new run.
No threshold, validator, prompt, case, inference or production change occurred.

## Existing Codespace machine change — proposal, 2026-10-11

Target the smallest offered machine with memory_in_bytes >= 17,179,869,184,
preferably 4 cores/16 GiB. GitHub's [calculator](https://github.com/pricing/calculator)
documents 4 cores/16 GB at $0.36/hour; its [machine API example](https://docs.github.com/en/rest/codespaces/machines)
confirms 16 GiB in bytes. The example's machine name/storage are not account
availability. Current local observations are two CPUs, 7.76 GiB usable host RAM,
~32 GiB workspace volume, Xeon Platinum 8370C; control-plane machine ID is unverified.
Codespace: special-disco-vprpp7qrv9xrcwq6p. `gh` is absent and no Codespaces metadata
connector is available; credentials/allowances/billing account were not inspected.
Confirm the actual offered 4-core/16 GiB option, storage and original machine name
in GitHub/VS Code's machine selector before applying anything. If unavailable,
stop and revise this proposal rather than automatically choose a pricier machine.

[Inventory](machine_change_inventory.json) records the six modified documents,
110 pre-existing untracked files, ignored logs/artifacts, hashes and hardware.
All relevant data is on the mounted persistent /workspaces volume: experiment
records (~3.53 MB), source/configured/compiled tree plus model (~2.11 GiB), the
workspace alias, .venv and frontend/node_modules. The server/model hashes match
verification.json. .agents/skills resolves within the repository. .venv/bin/python
resolves outside it to /usr/local/bin/python3.12; verify it after reconnect.
The prior /tmp experiment trees are already absent and no current experiment
files were found in /tmp. No essential surviving model/build data depends on /tmp.

GitHub documents [workspace persistence](https://docs.github.com/en/codespaces/about-codespaces/deep-dive)
across stop/start and rebuild, including added files; Git-ignore does not affect it.
Home/container changes survive ordinary stop/start but are lost on rebuild;
[/tmp is cleared on stop](https://docs.github.com/en/codespaces/developing-in-a-codespace/persisting-environment-variables-and-temporary-files).
Processes and visible terminal output do not survive stop, and unsaved editor
buffers must be saved. This proposal changes the existing machine; no container
rebuild, replacement Codespace or deletion is proposed.

After approval, preserve in this order:

1. Save all editor buffers; refresh disk inventory/Git diff/status/HEAD and hashes.
   Save a binary Git patch and a non-secret archive of changed/untracked documents
   plus all experiments, including ignored logs and the actual artifact tree.
   Include the workspace alias as a symlink without duplicating its target.
   Exclude .aws/.codex, .env files, credentials and home/authentication stores.
   Keep the checkpoint under /workspaces; download a copy to the owner's local
   machine for an independent backup before restart. No commit/staging is required.
2. Record the original machine selector name/RAM/storage and offered target. Use
   Codespaces: Change Machine Type (or github.com/codespaces → … → Change machine
   type) for this same Codespace. A [storage-capacity change](https://docs.github.com/en/codespaces/customizing-your-codespace/changing-the-machine-type-for-your-codespace)
   automatically stops an active Codespace; equal capacity applies on its next
   restart. Expect disconnection/restart in either case, with no promised duration.
3. Reconnect and verify branch/HEAD/index, inventory hashes, model/server, Python
   symlink and RAM/cgroup headroom. Keep model/prompt/cases/order/validator and all
   guard thresholds unchanged. GGML_NATIVE=ON means the saved binary uses native
   CPU instructions: verify required ISA compatibility on the new host; if it
   cannot be established, stop before loading, with no rebuild or replacement.
4. Record actual old/new machine IDs, RAM, CPU model/flags/affinity, cgroup limits,
   binary/model hashes, startup timestamps and cache/timing instrumentation in a
   new calibration run linked to the preflight stop. Freeze the logging wrapper
   and unchanged six cases/twelve requests. Keep two inference/prompt threads,
   seed 42, .7/0 sampling arms, context/output limits and strict checks unchanged.
   Use the exact-sample logging guard. Run once: 15 minutes including loading,
   90s readiness, 45s/request, 6 GiB scratch, 3.25 GiB owned RSS, 3.75 GiB preflight
   and 0.5 GiB runtime available-memory minima. No downloads/builds/retries or
   heldout evaluation. Stop on operational failure; retain semantic failures and
   continue only the fixed plan within budget. Success still requires 6/6 at zero.
   Treat measurements as a new hardware environment; do not attribute differences
   from the old smoke to temperature or RAM alone, even with two threads unchanged.
5. Preserve results/artifacts, then select the recorded original machine through
   the same selector and apply/restart as required. Check storage fits before any
   downgrade to a smaller volume; local workspace currently uses ~7.75 GB, but
   account/control-plane storage figures still require confirmation. Verify hashes
   again. If the original option is unavailable, stop and report rather than delete
   files or pick another option automatically.

One active hour costs $0.36 compute if billable (four weighted included compute
hours), versus $0.18 for a two-core hour. Fifteen minutes is $0.09 compute at that
rate. [Storage billing](https://docs.github.com/en/billing/concepts/product-billing/github-codespaces)
continues at $0.07/GB-month based on actual billed storage, including while stopped;
allocated disk size alone is not billed usage. Actual total/remaining allowances
are unknown, so $0.36 is the compute estimate plus existing storage accrual, not a
promise of the final invoice. Aim to finish verification/calibration within one
upgraded active hour; stop/report if extra time or a different paid tier is needed.

Approval requested for this bounded preservation → machine change/restart → one
calibration → return-to-original sequence, conditional on the target's availability.
Nothing is upgraded/restarted/stopped/executed now. Prior results, markers/deadlines,
application code and Git state are preserved; final DESIGN acceptance is pending.

## Machine-change sequence accepted — 2026-10-11

The owner approved the preceding sequence conditional on the offered 4-core/
16 GiB option, for one calibration only. The downloaded checkpoint must exclude
the large reproducible source/build/model tree; retain that tree under /workspaces
and record its hashes instead. This supersedes step 1's proposed inclusion of
the artifact tree. Include changed/untracked project files, experiment records
and ignored diagnostic logs, plus a binary Git patch; exclude credential stores,
secret files and caches. Preserve the preceding inventory and all older records.

[machine_change_handoff.json](machine_change_handoff.json) records manual gates
and observed original hardware/storage. No connected editor tool is available:
the owner must use VS Code File → Save All and confirm before the final preservation
snapshot. Independently download the checkpoint and confirm that it is on the
local machine before selecting/applying the target. Do not infer completion from
elapsed time, a link being provided, or a locally created archive.

Record the current machine label/cores/RAM/storage and target availability through
github.com/codespaces → this Codespace's ⋯ → Change machine type, without applying
anything until the preservation gates are complete. Stop if 4-core/16 GiB is not
offered. After applying/restarting and reconnecting, verify preserved file/artifact
hashes, Git branch/HEAD/index, resources, interpreter and native CPU compatibility.
Stop on mismatch, without rebuilding. A new linked run must retain the old
preflight-stop execution marker/results and freeze the unchanged twelve-request
plan plus separately recorded operational logging changes before loading.

Only one calibration is authorized: two threads, original model/runtime/prompt/
schema/cases/validator, seed 42, temperatures .7 and 0, 15 minutes including load,
90s readiness, 45s/request, unchanged storage/RSS/available-memory safeguards.
No downloads, rebuilding, automatic retries, tuning or heldout evaluation. Preserve
each response/timing/cache/result immediately; semantic failures continue only the
remaining frozen plan, operational failures stop. Record hardware differences.
Preserve closeout/results and return through the selector to the recorded original
machine/storage, restarting if required and verifying actual return. Aim for less
than one larger-machine active hour; report a block promptly. No machine change,
restart, inference or downgrade is recorded as completed yet. DESIGN stays pending.

Manual preservation/availability gates confirmed by the owner at 16:44 Europe/
Berlin on 2026-10-11: checkpoint.tar.gz and checkpoint.sha256 downloaded locally;
selector original 2 cores/8 GB RAM/32 GB storage, offered target 4 cores/16 GB RAM/
32 GB storage. The owner reports applying the approved change now; actual machine
application, restart and reconnection are not yet verified. Equal storage capacity
means a restart is needed to apply the selection. After reconnect, verify the
checkpoint plus the separately hashed changes to these handoff records, retained
artifacts, Git state, resources and CPU compatibility before any loading. No
calibration or return-to-original has occurred. The downloaded checkpoint remains
unchanged; this manual-gate update is a separate preservation delta.

## Post-change verification stop — 2026-10-11

Owner confirmed reconnection. [Verification](../../../../build/checkpoints/uc001-machine-change-20261011-1427/reconnect_verification.json)
matches 129 project/diagnostic files using the separately recorded handoff delta,
all 12,665 retained artifact files, branch/HEAD/index and worktree inventory.
The new host has four CPUs, AMD EPYC 7763, 16,770,494,464 bytes usable RAM,
13,875,003,392 bytes MemAvailable, unchanged 33,636,024,320-byte workspace capacity,
and 24,136,617,984 bytes free. Visible cgroup max/high remain unlimited, with zero
OOM events. The interpreter matches its preserved hash. Resource headroom passes.
The report's UTC is verification start; the exact later resource-sample timestamp
was not separately captured. No billing/machine API ID was inferred.

Native compatibility does not pass: original CPU was Intel Xeon Platinum 8370C
with AVX-512; the AMD host lacks those exposed flags. Actual retained CPU-backend
flags.make has -march=native for C/C++, and CMakeCache has GGML_NATIVE=ON. Separate
AVX512 switches being OFF in that cache do not establish a portable native build.
No binary --version/startup probe or inference was attempted after this mismatch;
this is a pre-execution compatibility stop, not an observed illegal-instruction
or model startup failure. No rebuild, acquisition, retry, tuning or heldout exposure.
All twelve planned calibration requests remain not_run; no timed window started.
A preparation helper was drafted in ignored checkpoint storage but never executed,
and no new linked calibration directory was created. Original results/markers and
downloaded checkpoint remain intact.

Return promptly through github.com/codespaces → this Codespace's ⋯ → Change machine
type → 2 cores/8 GB RAM/32 GB storage → Update codespace, then Stop codespace and
reopen the same Codespace because storage capacity is unchanged. Manual return
and post-return preservation/resource verification remain pending; do not claim
return complete. DESIGN remains Phase 2/in-progress, final acceptance pending.
