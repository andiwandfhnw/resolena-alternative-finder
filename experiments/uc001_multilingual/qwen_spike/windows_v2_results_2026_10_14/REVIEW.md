# Windows v2 attempt — operational closeout 2026-10-14

The original [uploaded archive](../../../../build/windows-v2-results-20261014/final-results.zip)
matches SHA-256 `404b1620056c8cdc023d36d3d164ffcbc9bf5b3caf9d2ddecf2de9335b805d2c`.
Its [preserved copy](original-final-results.zip) is identical. Safe inspection found
57 unique normalized members, a passing CRC check and 56 matching cleanup hashes.
The archived freeze/approval bind to the unchanged harness-2.0.0 freeze
`00fc5dd00449456bfe5d054110b463f642815f092cfc4cea8a3c1e05d24bbceb`.
Approval and attempt records are retained as recorded Windows provenance.

**Operational failure; zero evaluation requests.** Run
`727afaa2-2b48-48e8-b8b5-d01754405e50` began at 18:39:27.9483386 UTC with its
original 19:09:27.9483386 deadline. The primary [failure](evidence/run_failure.json)
occurred at 18.5647622 seconds; [driver exit](evidence/driver_exit.json) was 1 after
20.0707831 seconds. All 18 requests are unexecuted, not semantic failures: no response
files, generation-task launches, capacity proofs or assessment checkpoints exist.
The server did load/listen; the harness readiness gate did not complete.

The [startup log](evidence/server.stderr.log) records **37/37 layers offloaded to
GPU**, Vulkan0/RX 6800 XT, 7,669.77 MiB model and 288 MiB KV buffers, and context 2,048.
CPU-mapped/host buffers also exist. Three WDDM samples show positive owned allocation
(sampled maximum 8,075,534,336 bytes); sampled server RSS maximum is 7,804,915,712
bytes. These are startup observations, not measured acceleration, inference latency,
effective per-request thinking/cache behaviour or multilingual capability.

The frozen [offload function](../windows_qwen3_8b_followup_v2/execution/Common.ps1)
assigns `$matches`, then uses `-notmatch`. PowerShell variable names are case-insensitive;
matching regex checks update automatic `$Matches`, replacing that collection with
a hashtable. The later `.Groups` access explains the recorded error. The separate
Windows regression reproduces the original function on this log, then tests the
corrected function and missing/partial evidence. It has not run in this Codespace.

The subsequent [ownership error](evidence/guard_failure.json) was recorded
0.652097 seconds after [confirmed server exit](evidence/server_exit.json).
This supports a race between lookup and metadata access during shutdown. The old
guard did not capture the failing identity/HasExited values; genuine mismatch cannot
be ruled out from those records alone. The repair accepts proven absence/exit,
rechecks metadata-read races and still rejects live PID/start-time/executable or
uninspectable-identity mismatches. Future watchdog records include those observations.
Resource thresholds and matching-process stop protection remain unchanged.

Windows records confirm planned owned server shutdown (exit -1), watchdog/process
exit 1 and artifact-preserving cleanup. This Codespace cannot verify live Windows
processes. [Structured review](review.json) and [original evidence](evidence/) retain
the failures, approval, markers, deadlines, configuration and exit records unchanged.

Only [separate harness 2.0.1 preparation](../windows_qwen3_8b_followup_v2_0_1/BUNDLE.md)
and offline checks are authorized. Prompts, cases, expectations, scoring, settings
and limits remain unchanged; no automatic retry or inference is authorized.
V1's failed semantic gate remains intact; the 55 held-out cases were not read.
DESIGN/in-progress and qualified linguistic validation remain pending.
