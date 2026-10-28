# Lingua B — stopped before detector execution, 2026-10-15

**Operational harness failure, not a language-classification result.** The single
approved attempt is closed without retry. No installation, detector import,
LLM/GPU call or application behaviour occurred. All 50 planned records remain
unexecuted; no category has a correctness, repeat-consistency or cold/warm result.

The frozen acquisition verifier assumed a wheel member ending `/LICENSE.txt`.
The publisher wheel instead declares `License-File: LICENSE` and contains
`lingua_language_detector-2.2.0.dist-info/licenses/LICENSE`. Its 11,357 bytes
match the pinned publisher Apache 2.0 license exactly. The filename assumption
in this experiment's harness caused `StopIteration`; this does not establish a
package/license defect or a detector capability failure. The frozen harness,
failure and original deadline are preserved unchanged.

| Check/measurement | Actual evidence |
|---|---|
| Python/platform | Existing CPython 3.12.11, Linux x86-64, glibc 2.36; publisher wheel tags compatible. Native loading is untested. |
| Dependency/license | No active Python package dependencies; optional pytest test extra excluded. Apache 2.0 bytes verified offline after stop; bundled native dependencies are bound by the wheel/SBOM hashes. |
| Acquisition | One wheel download, 170,332,900 bytes. Metadata/license/wheel total **170,430,323 bytes**, below 200,000,000. These are received body bytes, excluding transport overhead. |
| Wheel SHA-256 | `63d99c7570ba09525f1702e4e4b2362f8f1f7e0a0fba93a3a53d3f322e00659d` |
| Preparation headroom | Initial available RAM 4,980,621,312 bytes; disk free 23,649,120,256 bytes. A second pre-acquisition check passed. Visible cgroup has no finite memory maximum. |
| Supervised memory | Peak aggregate owned RSS/HWM sum **48,013,312 bytes (45.79 MiB)** during acquisition, sampled every 50ms. Preparation was not continuously monitored; this is not a measured detector footprint. |
| Scratch at execution exit | 170,662,143 logical / 170,754,048 allocated bytes; later evidence-copy/documentation usage is recorded separately in verification.json. Preserved wheel is included. |
| Time/exit | 16:56:34.342–17:05:21.769 UTC, **8m47.428s** including metadata/preparation; supervised acquisition/checks 5.245s. Acquire and supervisor exit 1. Original deadline 17:26:34.342 UTC was not reset. |
| Process state | Supervisor/acquisition recorded PIDs absent on subsequent live Codespace inspection. No retry, remaining experiment process or isolated venv. |

| Frozen control category | Controls | Planned records | Executed/correctness |
|---|---:|---:|---|
| Clear supported DE/FR/IT/EN | 8 | 16 | 0 / unmeasured |
| Clear unsupported language controls | 4 | 8 | 0 / unmeasured |
| Short/shared/name/place controls | 4 | 8 | 0 / unmeasured |
| Mixed/dialect controls | 4 | 8 | 0 / unmeasured |
| Preference/country/meaning uncertainty | 4 | 8 | 0 / unmeasured |
| Exposed Spanish C6 anchor | 1 | 2 | 0 / unmeasured |

There are 25 fixture contexts, 24 distinct text strings and two planned fixed
passes; the matched country pair intentionally repeats text. They would not be
50 independent examples. Frozen AI-assisted contract references are not observed
detector decisions, reviewed production routing or verified meaning/constraints.
No semantic, normalization, quote-grounding, translation or end-to-end pass follows.

Evidence: [results](results.json), [freeze](freeze.json), [controls](cases.json),
[order](order.json), [procedure](PROCEDURE.md), [package pin](artifact-pin.json),
[original failure](evidence/acquire.stderr.log), [original closeout](evidence/closeout.json),
[read-only license diagnosis](post-stop-wheel-inspection.json) and
[preservation verification](verification.json). Large reusable wheel and original
operational records remain under `build/lingua-b-20261015/`; nothing was deleted.
Four new synthetic guard checks passed before freezing; they do not validate
package acquisition, native loading or detector behaviour. An earlier preparation
assertion was corrected to exclude the inactive test extra, reusing metadata without
a network retry; that note is preserved in the pin and pre-execution checks.

Smallest proposed next step: prepare and review a separately versioned acquisition
verifier using the declared license filename, with an offline regression against
the retained wheel. This is a proposal only: no frozen-harness repair, new attempt,
continuation or installation is authorized by this closeout. Any future approved
execution should reuse the verified wheel without another download.

Previous results, application dependencies and all 55 unopened held-out cases
remain unchanged. No production component is selected; direction A and approved
DE/FR/IT/EN/privacy requirements remain. UC-001 increment 1 / Phase 2 DESIGN /
in-progress, final acceptance and qualified linguistic validation pending.
