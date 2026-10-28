param([Parameter(Mandatory=$true)][string]$Scratch)
$parseErrors = @()
foreach ($file in @(Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.ps1' -Recurse)) {
    $tokens = $null; $errors = $null
    $null = [Management.Automation.Language.Parser]::ParseFile($file.FullName, [ref]$tokens, [ref]$errors)
    if ($errors) { $parseErrors += $errors }
}
if ($parseErrors.Count -gt 0) { $parseErrors | Format-List; throw 'Offline parser failure.' }
. (Join-Path $PSScriptRoot 'Common.ps1')
Assert-Bundle $PSScriptRoot
if (Test-Path -LiteralPath $Scratch) { throw 'Use a new scratch folder; preserve prior checks and attempt markers.' }
$null = New-Item -ItemType Directory -Path $Scratch
$log = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'fixtures\startup-v2-20261014.log'), [Text.Encoding]::UTF8)
$groupsReproduced = $false
try { $null = & (Join-Path $PSScriptRoot 'fixtures\Offload-original.ps1') -Text $log }
catch { $groupsReproduced = $_.Exception.Message -like '*Groups*' }
if (-not $groupsReproduced) { throw 'Original Groups regression was not reproduced; stop and review.' }
$passed = @('original-Groups-regression')
$variants = @(
    @{ name = 'recorded-37-of-37'; text = $log; expected = $true },
    @{ name = 'missing-layers'; text = [regex]::Replace($log, '(?m)^.*offloaded \d+/\d+ layers to GPU[^\r\n]*\r?\n?', ''); expected = $false },
    @{ name = 'incomplete-layers'; text = $log.Replace('offloaded 37/37 layers', 'offloaded 36/37 layers'); expected = $false },
    @{ name = 'zero-layers'; text = $log.Replace('offloaded 37/37 layers', 'offloaded 0/0 layers'); expected = $false },
    @{ name = 'missing-device'; text = [regex]::Replace($log, '(?m)^.*Vulkan0.*RX\s*6800\s*XT[^\r\n]*\r?\n?', ''); expected = $false },
    @{ name = 'missing-model-buffer'; text = [regex]::Replace($log, '(?m)^.*Vulkan0.*model buffer size[^\r\n]*\r?\n?', ''); expected = $false },
    @{ name = 'missing-KV-buffer'; text = [regex]::Replace($log, '(?m)^.*Vulkan0.*KV buffer size[^\r\n]*\r?\n?', ''); expected = $false },
    @{ name = 'zero-KV-buffer'; text = [regex]::Replace($log, '(Vulkan0.*KV buffer size\s*=\s*)[0-9.]+', '${1}0.00'); expected = $false }
)
foreach ($variant in $variants) {
    if ((Test-OffloadText $variant.text) -ne $variant.expected) { throw ('Offload check failed: ' + $variant.name) }
    $passed += $variant.name
}
$start = [DateTime]::SpecifyKind([DateTime]'2026-10-14T18:39:41.7398037', [DateTimeKind]::Utc)
$receipt = @{ process_id = 50988; start_ticks = $start.Ticks; executable = 'C:\ResolenaExperiments\qwen3-8b-v1\runtime\llama-server.exe' }
foreach ($name in @('live-match', 'absent', 'already-exited', 'exit-during-path', 'exit-during-starttime', 'wrong-PID', 'reused-PID', 'wrong-executable', 'uninspectable-live', 'missing-live-path')) {
    $script:FakeProcess = [pscustomobject]@{ Id = 50988; StartTime = $start; Path = $receipt.executable; HasExited = $false }
    $expected = 'rejected'
    switch ($name) {
        'live-match' { $expected = 'live' }
        'absent' { $script:FakeProcess = $null; $expected = 'ended' }
        'already-exited' { $script:FakeProcess.HasExited = $true; $expected = 'ended' }
        'exit-during-path' {
            $script:FakeProcess | Add-Member -MemberType ScriptProperty -Name Path -Value { $this.HasExited = $true; return $null } -Force
            $expected = 'ended'
        }
        'exit-during-starttime' {
            $script:FakeProcess | Add-Member -MemberType ScriptProperty -Name StartTime -Value { $this.HasExited = $true; throw 'Synthetic metadata access during exit.' } -Force
            $expected = 'ended'
        }
        'wrong-PID' { $script:FakeProcess.Id = 12345 }
        'reused-PID' { $script:FakeProcess.StartTime = $start.AddSeconds(1) }
        'wrong-executable' { $script:FakeProcess.Path = 'C:\Unrelated\application.exe' }
        'uninspectable-live' { $script:FakeProcess | Add-Member -MemberType ScriptProperty -Name Path -Value { throw 'Synthetic live metadata access denied.' } -Force }
        'missing-live-path' { $script:FakeProcess.Path = $null }
    }
    $actual = 'rejected'
    try {
        $owned = Get-OwnedLiveProcess $receipt { param([int]$OwnedId) return $script:FakeProcess }
        $actual = $(if ($null -eq $owned) { 'ended' } else { 'live' })
    } catch { $actual = 'rejected' }
    if ($actual -cne $expected) { throw ('Ownership check failed: ' + $name + ', got ' + $actual) }
    $passed += $name
}
$report = @{ classification = 'Offline Windows harness regressions only; mocked process lookup; no inference or real process termination';
    utc = [DateTime]::UtcNow.ToString('o'); PowerShell = $PSVersionTable.PSVersion.ToString();
    freeze_sha256 = Get-Sha (Join-Path $PSScriptRoot 'freeze.json'); passed = $passed;
    DESIGN = 'pending'; linguistic_validation = 'pending' }
Write-NewJson (Join-Path $Scratch 'harness-regression.json') $report
$protocolScratch = Join-Path $Scratch 'protocol'
& (Join-Path $PSScriptRoot 'Test-Protocol.ps1') -Scratch $protocolScratch | Tee-Object -FilePath (Join-Path $Scratch 'protocol-output.txt')
$report | ConvertTo-Json -Depth 12
