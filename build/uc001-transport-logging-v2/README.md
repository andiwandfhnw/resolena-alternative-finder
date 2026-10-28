# Logging wrapper correction v2 — prepared only

Priority 3 partial; Phase 3 in-progress. No connection, endpoint or native job was
started. Original transport scripts, defective logging v1, both attempts' existing
evidence and model budgets remain unchanged. Use this separate correction for
review; earlier v1 instructions are historical.

## Confirmed correction and evidence boundary

gh 2.81.0's [actual parser](https://github.com/cli/cli/blob/v2.81.0/internal/codespaces/ssh.go)
uses `bcDeFIiLlmOopRSWw` as its value-taking option list; uppercase `E` is absent.
The previous claim in `source-review.json` that this parser accepts `-E <path>`
was incorrect. Its argument-string tests missed the subsequent parse. That
artifact and the defective wrapper are preserved rather than rewritten.

The [new wrapper](../../scripts/uc001_transport_preparation/Test-TransportLoggingV2.ps1)
removes only `-E` and its path from the argument injection, retaining `-vvv` and
GH_DEBUG=1. SSH inherits gh's redirected stderr, so both producers use the existing
private `transport.stderr.log`. The v2 summary reads it once and names its source
and possible producers explicitly; it makes no separate-file or source-attribution
claim. All original controls, stdin secret, private DACL, deadlines, owned-job
cleanup, exact ports, remote command and separate Codespace cleanup requirement
remain unchanged. No retries, fallback or extra probes were added.

[Parser replay](parser-reproduction.json) demonstrates that v1's flags become
`-vvv -E`; its intended log path and all following tokens become the command.
gh then inserts `-p 49189 ...` immediately after `-E`. V2 retains every original
SSH control as options and the entire remote command after `vscode@localhost`.
Tests also cover a synthetic automatically prepended `-i` identity.

The pinned 5392-byte source is [retained unchanged with its license](reference/source-record.json).
No Go compiler was available. Offline tests use an explicit Python transcription
of the pinned `ParseSSHArgs`/`parseArgs` control flow and `newSSHCommand` argument
construction, with the option list read from the hashed source. This is source
logic verification, not execution of the gh binary or native Windows verification.
PowerShell substitutes capture arguments from the actual original transport flow;
the corrected parsing is checked beyond an expected argument string.

The [second Codespace cleanup receipt](attempt_2_2026_10_17/codespace-cleanup.raw.json)
is copied byte-for-byte: passed at **2026-10-17T16:52:10.674073+00:00**. Windows
cleanup is confirmed by the [supplied sanitized Windows summary](attempt_2_2026_10_17/windows-sanitized-summary.raw.json):
failed after **4062 ms**, overall limit not exceeded, gh log present and separate
SSH log missing; all reported stage/error markers are false. The summary's pending
Codespace-cleanup field is preserved as emitted; the separate receipt above closes
that cleanup observation. Missing markers do not establish unobserved stages or
resolve the root cause. The [owner report](attempt_2_2026_10_17/owner-report.json)
links both records; a raw Windows cleanup receipt is still unsupplied. First-attempt evidence
remains [separate](../uc001-transport-diagnosis/failed_attempt_2026_10_17/README.md).
This second-wrapper defect cannot explain the first attempt, which had no `-E`.

## Possible stray `-p` log — read-only Windows check

In the malformed argv, OpenSSH can consume `-p` as the filename for `-E`.
[OpenSSH 9.5](https://github.com/openssh/openssh-portable/blob/V_9_5_P1/ssh.c)
redirects the log during initialization, and its
[log reader/writer](https://github.com/openssh/openssh-portable/blob/V_9_5_P1/log.c)
opens that filename with create/append semantics. It could create or append a
file outside the private result directory if that initialization was reached.

The frozen native helper starts gh with its executable directory as working
directory. gh's child SSH command leaves its working directory unset, inheriting
that directory. The expected candidate is therefore
`C:\ResolenaExperiments\tools\gh-2.81.0\bin\-p`. Actual Windows creation, timing,
ACLs and any Windows-specific directory behavior remain unverified. A present
file alone would not prove which attempt created it.

Paste this **metadata-only** command into Windows PowerShell 5.1 if collecting
that evidence. It reads no contents or credentials, starts no connection/process,
and does not delete, move, hash or change the file:

```powershell
$path = 'C:\ResolenaExperiments\tools\gh-2.81.0\bin\-p'
$report = try {
    $item = Get-Item -LiteralPath $path -Force -ErrorAction Stop
    [ordered]@{
        state = $(if ($item.PSIsContainer) { 'directory_not_file' } elseif ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { 'reparse_point_metadata_only' } else { 'file_present' })
        path = $path
        bytes = $(if ($item.PSIsContainer) { $null } else { $item.Length })
        created_utc = $item.CreationTimeUtc.ToString('o')
        modified_utc = $item.LastWriteTimeUtc.ToString('o')
        attributes = [string]$item.Attributes
    }
} catch [System.Management.Automation.ItemNotFoundException] {
    [ordered]@{ state = 'missing'; path = $path }
} catch {
    [ordered]@{ state = 'query_failed'; path = $path; error_type = $_.Exception.GetType().FullName }
}
$report | ConvertTo-Json
```

Leave any discovered file unchanged and do not paste its raw contents. Existing
v1 privacy claims do not establish that this possible stray log was private.

## Proposed execution command — not authorized or executed here

Place only the new wrapper next to the unchanged original test and endpoint in
`C:\ResolenaExperiments\uc001-transport-check`. The extracted v1.3.0 bundle remains
required. From a 64-bit Windows PowerShell 5.1 console, the future review command is:

```powershell
& "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -NonInteractive -ExecutionPolicy RemoteSigned -File 'C:\ResolenaExperiments\uc001-transport-check\Test-TransportLoggingV2.ps1' -ExecuteTransportLoggingCheck -BundleDirectory 'C:\ResolenaExperiments\uc001-execution-v1_3_0' -Codespace 'special-disco-vprpp7qrv9xrcwq6p'
```

Preparation grants no additional attempt. No-switch execution stops. A future
authorized run retains 45-second work, two five-second owned-exit waits and the
60-second overall failure guard. Frozen ProcessTools.cs native compilation/calls
and possible Windows temporary compiler files are unchanged; private-directory
ACLs apply before child/log creation. Only sanitized-summary.json may be shared;
combined raw stderr stays local and may contain sensitive URLs or key metadata.
Broker target/internal errors can still be unavailable with pinned gh logging.

[Verification and changed files](verification.json), [hashes](SHA256SUMS.txt).
Offline RED: 9 failures/2 passes, including the actual bad parser split; GREEN:
37 focused new/retained checks. Windows behavior, the original banner refusal,
possible stray file, complete first-attempt cleanup receipt and GPU/model/semantic
readiness remain unresolved. No tools were installed/downloaded or services changed.
