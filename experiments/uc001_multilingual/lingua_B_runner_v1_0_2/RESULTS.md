# Lingua B runner 1.0.2 — completed screen, 2026-10-15

**Operationally complete; the predeclared raw-language screen failed.** All 50
records/100 classification calls completed without retries or resource failures.
The 12 clear new controls matched their expected language in both passes; exposed
C6 ranked Portuguese instead of Spanish, giving **12/13 required raw-label matches
per pass**. No gate was relaxed and no further execution or tuning followed.

C6 is an unsupported-language negative control, not a Spanish interpretation or
translation requirement. Portuguese and Spanish are both outside DE/FR/IT/EN;
either identity could lead to an unsupported/null/limitation policy outcome.
That does not make the frozen internal-label check pass. **No external routing,
limitation response, request interpretation or evidence rendering was executed.**

## Findings by control category

| Category | Contexts / records | Observed detector result and boundary |
|---|---:|---|
| Clear DE/FR/IT/EN | 8 / 16 | 8/8 correct raw top labels per pass, two contexts per supported language. This does not establish preserved request meaning or constraints. |
| Clear unsupported ES/PT/NL/PL | 4 / 8 | 4/4 correct raw identities per pass. Limitation/rephrasing behaviour was not generated or tested. |
| Short/shared/name/place | 4 / 8 | `Port`→it, `Taxi`→ts, `Acme X-2`→so, `Genève`→fr. No unique request-language gold label is assumed. Even Genève's approximately .957 score cannot establish request language from a place name. |
| Mixed/dialect | 4 / 8 | EN/FR spans found for the clear-primary mixture. Balanced DE/EN/FR was all FR; EN/ES was all PT. Only 1/3 expected mixture-component sets appeared. Swiss-German text ranked de, which cannot certify standard-German capability or preserved negation. |
| Preference/country/uncertain amount | 4 / 8 | Both same-text `Velo` contexts ranked ts with identical rank order/spans; `Radio` ranked pl. These guesses cannot override the approved preference/choice path. The amount case ranked en but its numeric ambiguity was not interpreted. Context/country fields were deliberately not detector inputs; no application behaviour was checked. |
| Exposed C6 | 1 / 2 | Both passes ranked pt (.320807), then es (.231687): failed frozen raw-language identity check, distinct from an unexecuted external capability route. |

These are **25 fixture contexts, 24 distinct texts**, with one deliberate same-text
country pair. Two passes do not provide 50 independent examples. Expectations and
[contract review](contract-review.json) are AI-assisted, not qualified linguistic
validation. The review records required routes separately from raw hypotheses;
it does not manufacture repaired application responses or semantic/quote passes.

## Repeat consistency and latency

Top labels, complete rank order and spans match across passes for 25/25 contexts.
Only 2/25 full raw outputs are bit-exact: the maximum absolute score difference is
8.881784197001252e-16. No cause or calibrated confidence interpretation is assigned;
no tolerance was introduced into the unchanged label gate.

| Measurement | Actual |
|---|---:|
| Import / builder | 2.369 / .180 ms |
| Process initialization + first record | 32.959 ms; proposed <=5s target met |
| Pass 1 record median / nearest-rank p95 | 11.450 / 18.856 ms |
| Pass 2 record median / nearest-rank p95 | 11.910 / 15.978 ms; proposed <=100ms target met |
| Pass 2 ranking median / p95 | 2.581 / 3.763 ms |
| Pass 2 segmentation median / p95 | 4.219 / 5.357 ms |

Record times include incremental-save overhead. The same detector instance and
default lazy models were reused. Cache occupancy/misses were not exposed/measured;
no cache eviction occurred, and offline installation may warm filesystem cache.
“Cold” means process initialization/first record, not a cold machine. These are
candidate-screen targets and short synthetic inputs, not product latency acceptance
or evidence of statistically established warm-up benefit.

## Operation, resources and cleanup

The fresh window was **19:41:37.511–20:11:37.511 CEST**. Measurement finished at
**19:47:39.331 CEST**, 6m01.820s after preparation began, including the seven offline
integration checks, verification, setup and loading. Verify/venv/install/detector
and supervisor exited 0. All four workers recorded the identical context hash,
deadline, resource limits and two-CPU affinity.

Runtime: existing Codespace, CPython 3.12.11, Intel Xeon Platinum 8370C; Lingua 2.2.0,
all 75 languages, default high accuracy and unchanged relative-distance setting.
Live preflight passed with 5,386,235,904 bytes available RAM and 23,572,283,392 bytes
disk free; visible cgroup had no finite maximum or OOM events.

- Peak sampled aggregate owned RSS: **226,160,640 bytes / 215.68 MiB**;
  conservative summed HWM: 226,746,368 bytes / 216.24 MiB. Worker HWM: 198.85 MiB.
- Scratch at execution exit: **477,884,416 allocated bytes / 455.75 MiB**
  (477,520,528 logical), including retained wheel/earlier Lingua artifacts, new
  environment and records. Final evidence-copy usage is in verification.json.
- Zero new downloads: the original hash-verified wheel was reused without copying.
  Earlier acquisition remains 170,430,323 bytes; no LLM/GPU use or paid provisioning.
- RSS sampled every 50ms, scratch every 250ms; observed processes had one OS thread
  in samples, with two-CPU affinity and thread limits of two. Transient peaks can
  be missed; preparation was not continuously sampled.

Owned processes exited; subsequent live PID/start-time inspection confirms cleanup
in [verification](verification.json). Reusable wheel, isolated environment and all
results are retained. Original closed attempt/markers/deadline, verifier 1.0.1,
application dependencies and prior evidence are unchanged; all 55 held-out cases
remain unopened.

Detailed evidence: [analysis](analysis.json), [all raw records](evidence/records.jsonl),
[API call journal](evidence/calls.jsonl), [resource samples](evidence/resources.jsonl),
[closeout/exits](evidence/closeout.json), [wheel verification](evidence/wheel-verification.json),
[runner freeze](freeze.json), [shared context](evidence/context.json) and
[offline integration checks](integration-checks.json).

This configuration has not established a safe automatic language/capability gate
and is not selected for production. A proposed next step is an offline DESIGN
review of advisory hypotheses, genuine ambiguity and mixed/dialect boundaries;
no threshold sweep or another experiment is authorized. Direction A, approved
DE/FR/IT/EN/privacy requirements, Phase 2 DESIGN/in-progress and qualified linguistic
validation pending remain unchanged. No Git delivery or phase advancement.
