# Granite build supervision — bounded blocker, 2026-10-25

The owner accepts the [native build procedure](../uc001-granite-native-build-preparation/README.md)
as a **preparation artifact only**. Acquisition/configure/build remain unauthorized
and unexecuted by this session. That accepted procedure is unchanged.

## Result

**STOP: no complete executable supervisor is delivered.** The specific unresolved
requirement is trustworthy cumulative **downloaded-byte accounting** for the
unchanged Git-fetch acquisition route. The frozen ceiling is 10 GiB total downloaded,
shared across source/model acquisition, within 30 minutes; no model acquisition is
authorized here. Neither a missing measurement nor a source ZIP's size can establish
compliance. The [frozen requirements](../../scripts/uc001_granite_contract_v1/README.md#proposed-operational-limits-not-measurements)
explicitly require stopping on unsupported/ambiguous measurements.

This is a bounded capability finding, not proof that Windows cannot support a
complete supervisor or that third-party installation is necessary. The owner
authorized a minimal helper; the documented counters examined below do not supply
the required meter. A trustworthy custom network-accounting component is unresolved,
not assumed impossible or silently replaced with a different metric.

## What the built-in mechanism can provide

A private Windows Job Object is the appropriate ownership mechanism: create a
phase worker suspended, assign it before resuming, prohibit breakaway, retain a
non-inherited job handle and enable kill-on-last-handle-close. Ordinary descendants
then remain associated, including nested CMake/Ninja/compiler/shader-generator
processes. Job termination acts on that job and its nested jobs, without process-name
matching. Assignment/containment failure must stop before resuming a worker.
This follows [Microsoft's job ownership documentation](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects),
[assignment API](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject)
and [termination API](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-terminatejobobject).
It has not been implemented or exercised here; broker-created processes cannot be
assumed contained merely from ancestry.

Job-wide committed-memory limits are available, but that accounting must be
labelled accurately rather than silently described as RSS. A complete helper would
also need aggregate phase clocks, directory-output/headroom observations and
verified cleanup. Feasible ownership alone does not establish all-limit readiness.
[Microsoft memory-limit semantics](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information)
distinguish the job's committed-memory limit.

## Why the acquisition meter is a blocker

- [Job I/O accounting](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-io_counters)
  reports read/write/other totals, not a dedicated download counter. The documented
  [process counters](https://learn.microsoft.com/en-us/previous-versions/aa394323(v=vs.85))
  combine file, network and device I/O. Local fsck/archive/pipe traffic cannot be
  silently debited as downloaded bytes, and ZIP/source sizes omit acquisition traffic.
- [Job network rate control](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_net_rate_control_information)
  governs outgoing bandwidth, not cumulative incoming downloaded bytes. A machine-wide
  adapter counter also cannot attribute the total to this owned acquisition tree.
- Diagnostic CURL tracing in the discovered Git version is not an enforcement gate:
  its [trace-write implementation](https://raw.githubusercontent.com/git-for-windows/git/v2.53.0.windows.2/trace.c)
  warns and disables tracing after write failure without terminating acquisition.
  A diagnostic log cannot be assumed complete and treated as a fail-closed byte ledger.
- Built-in ETW is a possible implementation substrate, not a ready meter. Its
  [TCP event size is a packet measurement](https://learn.microsoft.com/en-us/windows/win32/etw/tcpip-typegroup1),
  and [events/buffers can be lost](https://learn.microsoft.com/en-us/windows/win32/etw/about-event-tracing).
  A custom consumer would need justified byte semantics, complete owned-process
  attribution across short-lived helpers, loss/staleness detection and a stop path
  on unknown accounting. This bounded review does not establish that component as
  trustworthy. Ordinary post-breach monitoring latency alone is **not** the blocker;
  no new zero-latency requirement is imposed.

No threshold, route or approval is amended to work around the missing meter. All
frozen limits remain: acquisition 30 minutes/10 GiB total; configure plus build
45 minutes combined; tree memory 24 GiB; build output 12 GiB; initial free disk
48 GiB; stop below 8 GiB free disk or 4 GiB OS free memory; outer parallelism 2.
The pinned commit, flags, paths, toolchain and Vulkan backend remain unchanged.

## Execution, evidence and stopping point

There is **no owner-run supervision invocation** to approve as complete. Do not run
the earlier acquisition/configure/build blocks under a timeout-only, process-name
or mixed-I/O substitute. No worker was launched, so ownership/PIDs, resource samples,
termination reason from a run and cleanup success are **not observed**, not zero or
passed. A future complete artifact must retain those records and logs/partial
artifacts; stop on unknown measurements or any breach; terminate only its owned
job; confirm no owned processes remain; report cleanup failure without retry.

Only relevant local requirements and primary-source documentation/source text were
reviewed. No application tests, Windows activation, resource/GPU probe, tracing
session, acquisition, configure, compiler, build, model work or installation occurred.
No third-party supervisor is selected or proposed for installation. Stop with this
specific unresolved metering requirement for owner review; no new implementation
or investigation is started automatically.

Documentation/local-link/anchor/fence and new-whitespace checks passed. All 832
previously protected files outside TASKS and all 79 existing Granite files retain
their fingerprints (overlapping counts are not added). Historical task entries and
the Priority 5 suffix, Git HEAD/branch/index and existing status entries are unchanged.
`git diff --check` exits 2 only for the preserved historical TASKS trailing space,
now line 2577. Only TASKS and this new receipt were written. No executable helper
was produced, so no script syntax/compilation or Windows execution check is claimed.
PHASE: 3 / STATUS: in-progress. Priorities 3/4 remain partial; Priority 6/Phase 4
remain pending. Priority 5 acceptance and the closed Qwen result are unchanged.
