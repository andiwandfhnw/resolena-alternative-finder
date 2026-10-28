# Corrected technical-feasibility proposal — v1.4.0

**Execution approval is pending.** This package does not grant another startup.
[Owner-provided Windows receipts](../../build/uc001-combined-ownership-v1_1_0/owner-results/results_2026_10_18/verification.json)
close the tested combined stand-in ownership issue: native binding, actual Python validator,
fresh native revalidation and all five exits passed in 1180 ms. Earlier failures remain
unchanged. Model/GPU readiness and the earlier model-run helpers' legitimacy are unproven.
Do not repeat the successful standalone diagnostic.

Proposed identity: `d586feb0be95c5d955be7b6a60381ab41594a0136d8c45917f81460829675078`.
It links both consumed identities: original `bda2015c0ffbe89ab1a612fb4003b2b12f254871cf32f2e47dbbbe9d45cf0f52`
and preceding `3efca8db7f356fe00672ecf2a0607c2b57c017fafedca61e85778611abd1afe8`.
The separate [proposal](execution-proposal.json) requests **one further startup and at most
14 unchanged ordered generations**, with no retry, tuning, replacement or downloads.
No historical counters/ledgers are reset or generation counts reconstructed. Reservation
of this identity is exclusive; an existing attempt directory always stops execution.
Actual argv/startup and generation attempts are recorded prospectively before dispatch.

The Windows-verified native binder, ownership bridge, Python validator and deadline helper
are reused byte-for-byte. Launcher/capture/replay now share full server identity, creation
and trusted frozen runtime path (`C:\ResolenaExperiments\qwen3-8b-v1\runtime\llama-server.exe`).
One exact system console helper per verified server/Python branch is permitted; all job
members are accounted for and unknown/ambiguous members stop. Retained handles remain
available independently of role approval; cleanup checks server, redirector, interpreter
and both helpers when present. Capture uses fresh native identities. Replay uses the same
policy with explicitly recorded identity readers and the tested machine's frozen system
path `C:\Windows\System32`; it makes no fresh native ownership claim or network fallback.

Pins, prompt, schema, cases and sampling stay unchanged: Qwen3-8B Q8_0 / llama.cpp b11429
commit d81235049384534c167caea52b85a694f6103d14; context 8192, full 37-layer offload,
CLI/request cap 3072 (reported task default -1 remains separate). Existing limits remain:
2400 seconds total, 1500 model, 90 readiness, absolute owned-job-supervised 90 seconds per
response including prompt-fit/shared validation/case checks, 1-second resource sampling.
Start headroom RAM/GPU/disk 20/14/6 GiB; runtime floors 4/2/5 GiB, owned GPU/RSS caps
12/16 GiB; artifacts 1 GiB split 512 MiB Windows/Codespace, bodies <=262144 bytes.
Validation and supervisor acknowledgment precede every next generation. Complete secret-
scanned bodies are exported; incomplete bodies/errors/process logs remain private.

## One future Windows sequence — review only until explicit approval

Download [proposed-execution.zip](../../build/uc001-contract-local-v1_4_0/proposed-execution.zip)
and [SHA256SUMS.txt](../../build/uc001-contract-local-v1_4_0/SHA256SUMS.txt) into
`C:\ResolenaExperiments\uc001-contract-local-v1_4_0-handoff`. Source transfers count against
the existing cumulative allowance; no reset or dependency/asset acquisition.

Run this sequence in **64-bit Windows PowerShell 5.1 only after explicit approval of this
exact allowance**. A matching extraction and valid existing approval may be reused unchanged.
If no approval exists, the blank reference intentionally stops; fill it only with the actual
owner approval reference after approval. Existing invalid approvals are preserved and rejected
by the shared Python approval gate before asset checks/startup. Approval lives outside the
frozen extraction. Reuse never bypasses the exclusive attempt reservation.

```powershell
$ErrorActionPreference = 'Stop'
function Assert-MatchingExecutionExtraction($Archive,$Root) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    if (-not (Test-Path -LiteralPath $Root -PathType Container)) { throw 'Extraction directory missing' }
    if ((Get-Item -LiteralPath $Root).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Extraction root is a link; stop' }
    $Items = @(Get-ChildItem -LiteralPath $Root -Recurse -Force)
    if (@($Items | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count) { throw 'Extraction contains a link; stop' }
    $Zip = [IO.Compression.ZipFile]::OpenRead($Archive)
    $Hasher = [Security.Cryptography.SHA256]::Create()
    try {
        $Entries = @($Zip.Entries | Where-Object { $_.Name })
        if (@($Items | Where-Object { -not $_.PSIsContainer }).Count -ne $Entries.Count) { throw 'Extraction file inventory differs; preserve and stop' }
        foreach ($Entry in $Entries) {
            if ([IO.Path]::IsPathRooted($Entry.FullName) -or (($Entry.FullName -split '[/\\]') -contains '..')) { throw 'Unexpected archive path' }
            $Stream = $Entry.Open()
            try { $Expected = ([BitConverter]::ToString($Hasher.ComputeHash($Stream))).Replace('-','').ToLowerInvariant() } finally { $Stream.Dispose() }
            $Path = Join-Path $Root $Entry.FullName
            if ((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Expected) { throw 'Extraction bytes differ; preserve and stop' }
        }
    } finally { $Hasher.Dispose(); $Zip.Dispose() }
}
function Get-ExecutionApprovalPath($Scripts,$Directory,$Reference) {
    $Record = Get-Content -LiteralPath (Join-Path $Scripts 'approval.pending.json') -Raw | ConvertFrom-Json
    $Path = Join-Path $Directory ($Record.attempt_identity + '.json')
    if (Test-Path -LiteralPath $Path) { return $Path }
    if ([string]::IsNullOrWhiteSpace($Reference)) { throw 'Further startup approval pending; stop' }
    $Record.approved = $true
    $Record.approval_reference = $Reference
    $Record.freeze_sha256 = (Get-FileHash -LiteralPath (Join-Path $Scripts 'freeze.json') -Algorithm SHA256).Hash.ToLowerInvariant()
    if (-not (Test-Path -LiteralPath $Directory)) { $null = New-Item -ItemType Directory -Path $Directory }
    $Bytes = ([Text.UTF8Encoding]::new($false)).GetBytes(($Record | ConvertTo-Json -Depth 8))
    $Stream = [IO.File]::Open($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try { $Stream.Write($Bytes,0,$Bytes.Length); $Stream.Flush() } finally { $Stream.Dispose() }
    return $Path
}
$OwnerApprovalReference = '' # Leave blank until explicit approval; valid existing records need no rewrite.
$Incoming = 'C:\ResolenaExperiments\uc001-contract-local-v1_4_0-handoff'
$Archive = Join-Path $Incoming 'proposed-execution.zip'
$Rows = @(Get-Content -LiteralPath (Join-Path $Incoming 'SHA256SUMS.txt') | Where-Object { $_ -match '^[0-9a-f]{64}  build/uc001-contract-local-v1_4_0/proposed-execution\.zip$' })
if ($Rows.Count -ne 1 -or (Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Rows[0].Substring(0,64)) { throw 'Package hash mismatch; stop' }
$Root = 'C:\ResolenaExperiments\uc001-contract-local-v1_4_0'
if (-not (Test-Path -LiteralPath $Root)) { Expand-Archive -LiteralPath $Archive -DestinationPath $Root }
Assert-MatchingExecutionExtraction $Archive $Root
$Scripts = Join-Path $Root 'scripts\uc001_contract_local_v1_4_0'
$ApprovalPath = Get-ExecutionApprovalPath $Scripts 'C:\ResolenaExperiments\uc001-contract-approvals' $OwnerApprovalReference
& "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy RemoteSigned -File (Join-Path $Scripts 'Run-Windows.ps1') -Execute -Review (Join-Path $Scripts 'partial-expectations-review.json') -Approval $ApprovalPath
if ($LASTEXITCODE -ne 0) { throw 'Attempt stopped; preserve results, no retry' }
```

The launcher reuses the installed `C:\ResolenaExperiments\uc001-validator-env\Scripts\python.exe`.
Its shared approval/source/schema/environment checks precede fresh model/ZIP/52-runtime-file
integrity validation, verified DXGI/CIM/PCI/LUID capacity/measurement/headroom checks and local
port 49187 availability. Startup additionally requires protected-endpoint authentication,
exact owned loopback listener, positive real owned-GPU allocation, resource monitoring and
effective runtime settings. Missing/invalid data stops; the stand-in pass replaces none of
these fresh checks. No SSH tunnel is used. Add-Type may create temporary compiler files;
Win32/Nt process/job/DXGI/resource calls and owned-handle/job cleanup retain existing behavior.

Results: `C:\ResolenaExperiments\uc001-contract-runs\d586feb0be95c5d955be7b6a60381ab41594a0136d8c45917f81460829675078`.
On any stop preserve the whole Windows directory; share only the scanned `export/` directory.
Copy only that export manually to Codespace, then use the matching labelled substitute replay:
`.venv/bin/python -m scripts.uc001_contract_local_v1_4_0.replay --export <copied-export> --output build/test-only/<new-directory>`.
Incomplete captures/unconfirmed cleanup cannot pass. Replay gets no live API/real-adapter
credit for cases 1/5/10. Technical/provisional policy results remain separate from pending
qualified semantics; partial DE/EN/dialect confirmations and original review hashes stay
unchanged, `expected_meanings_approved:false`. No interpreter suitability or multilingual
acceptance claim follows. Priority 3 partial; Phase 3 DEVELOP in-progress. SSH/Support paused,
held-out unopened. [Offline verification and changed files](../../build/uc001-contract-local-v1_4_0/verification.json).
