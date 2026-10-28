# Lingua B acquisition verifier 1.0.1 — offline repair

Prepared and verified on 2026-10-15. This is a separately versioned verifier,
not another experiment attempt. The [original frozen harness and failed
closeout](../lingua_B_2026_10_15/README.md) remain unchanged. No enabled run
approval, new deadline, installation or detector execution is included.

## Focused changes

- Replace suffix guessing for `/LICENSE.txt` with the wheel METADATA's
  `License-File` declarations, resolved under that wheel's `.dist-info/licenses/`
  directory. For this wheel, `LICENSE` resolves to
  `lingua_language_detector-2.2.0.dist-info/licenses/LICENSE`.
- Keep **exact byte-for-byte comparison** with the hash-pinned publisher license;
  no newline normalization, basename fallback or acceptance of merely similar text.
  Missing and altered content produce explicit `VerificationError` diagnostics.
- Verify the existing wheel read-only, without the old download/mutation stage.
  Preserve wheel size/SHA-256, ZIP CRC/path/expansion, publisher metadata,
  dependency and compatible-tag checks. Explicit failures remain active under
  Python optimization. The old frozen acquire.py is not imported or changed.

The old failing selection was:

```python
license_name = next(n for n in z.namelist() if n.endswith('/LICENSE.txt'))
license_bytes = z.read(license_name)
assert license_bytes == expected_license
```

The repaired [verification call](verify_retained.py) delegates to
`verify_declared_licenses`, which checks every declared file against its pinned
content. Declaration/path ambiguity, missing references and duplicates fail closed.

## Focused offline evidence

[Four regressions passed](regressions.json), zero failures/errors:

| Regression | Evidence/result |
|---|---|
| Retained publisher wheel | Located declared `licenses/LICENSE`; all 11,357 bytes match SHA-256 `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4`. Full wheel SHA-256 remains `63d99c7570ba09525f1702e4e4b2362f8f1f7e0a0fba93a3a53d3f322e00659d`. |
| Missing content | In-memory ZIP without the declared member rejected with `Missing declared license content` and the exact archive path. |
| Altered content | Synthetic license bytes rejected with `License content mismatch`, including expected/actual hashes. |
| Mislocated matching decoy | Matching bytes at `.dist-info/LICENSE.txt` do not substitute for the declared member; rejected as missing. |

Tests preceded implementation (missing-module failure), then passed after repair.
Negative fixtures exist only in memory; the 170,332,900-byte wheel was not copied,
altered or reacquired. The test process blocks network, additional subprocesses
and Lingua imports through an audit hook. Tests do not install/import Lingua,
start/stop a synthetic child process, run a detector, or inspect held-out cases.
Negative fixtures exercise the same license-checking function; a changed complete
wheel would also fail the unchanged outer SHA-256 gate before content inspection.
These are artifact-verifier checks, not language or application evidence.
[Verification/provenance](verification.json) records preservation and repair hashes.

Optional read-only verification from the Codespace repository root:

```bash
python3 -B experiments/uc001_multilingual/lingua_B_verifier_v1_0_1/verify_retained.py
```

This command reads the original metadata and retained wheel and prints JSON;
it never acquires, installs or starts a timed attempt. It does not modify the
closed attempt or create a replacement wheel-verification marker there.

## Readiness and remaining setup

The retained artifact/license verification blocker is resolved offline. Controls,
expectations, order, scoring references, accuracy mode and all resource limits
remain bound to the [original freeze](../lingua_B_2026_10_15/freeze.json).

**The whole experiment is not yet launchable.** The original supervisor calls the
old acquire.py, binds `build/lingua-b-20261015` and refuses its existing execution
marker; the worker also uses that environment and the old monotonic deadline.
A separately authorized run needs a separately versioned runner wired to this
offline verifier and retained-wheel installation path, new run storage and its
own authorized deadline/freeze. Do not clear old markers or edit the old deadline.
That runner and new attempt are not prepared or started by this repair.

No additional artifact or license blocker was found. Isolated installation and
native loading remain **untested**, rather than known failures. Fresh memory/disk
preflight is still required before a future run. Reuse the verified wheel with
zero new acquisition; keep the two fixed passes, maximum 100 classification calls,
30 minutes including setup/loading, two CPU threads, 1 GiB owned RSS, 1 GiB additional
scratch and 200 MB acquisition cap. No tuning, source build, upgrade or fallback.

Production integration, final DESIGN acceptance and qualified linguistic validation
remain pending. The 55 held-out cases remain unopened; no Git delivery or phase change.
