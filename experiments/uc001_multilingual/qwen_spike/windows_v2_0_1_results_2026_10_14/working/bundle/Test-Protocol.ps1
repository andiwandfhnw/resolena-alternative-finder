param([Parameter(Mandatory=$true)][string]$Scratch)
$errorsFound = @()
foreach ($file in @(Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.ps1')) {
    $tokens = $null; $errors = $null
    $null = [Management.Automation.Language.Parser]::ParseFile($file.FullName, [ref]$tokens, [ref]$errors)
    if ($errors) { $errorsFound += $errors }
}
if ($errorsFound.Count -gt 0) { $errorsFound | Format-List; throw 'Parser failure; no model process started.' }
. (Join-Path $PSScriptRoot 'Common.ps1')
Assert-Bundle $PSScriptRoot
if (Test-Path -LiteralPath $Scratch) { throw 'Use a new dedicated scratch folder; preserve previous checks.' }
$null = New-Item -ItemType Directory -Path $Scratch
$fixtures = Read-Json (Join-Path $PSScriptRoot 'selftest-fixtures.json'); $passed = @()
foreach ($scenario in $fixtures.scenarios) {
    $folder = Join-Path $Scratch $scenario.name; $null = New-Item -ItemType Directory -Path $folder
    foreach ($property in $scenario.files.PSObject.Properties) {
        $destination = Join-Path $folder $property.Name; $parent = [IO.Path]::GetDirectoryName($destination)
        $null = New-Item -ItemType Directory -Path $parent -Force
        [IO.File]::WriteAllBytes($destination, [Convert]::FromBase64String($property.Value))
    }
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'order.json') -Destination $folder
    $run = Read-Json (Join-Path $folder 'run.json'); $run.started_utc = [DateTime]::UtcNow.ToString('o')
    $run.deadline_utc = [DateTime]::UtcNow.AddSeconds(1800).ToString('o')
    if ($scenario.name -ceq 'expired') { $run.started_utc = [DateTime]::UtcNow.AddSeconds(-1801).ToString('o'); $run.deadline_utc = [DateTime]::UtcNow.AddSeconds(-1).ToString('o') }
    Write-Json (Join-Path $folder 'run.json') $run
    $checkpoint = Read-Json (Join-Path $folder 'checkpoint.json'); $checkpoint.deadline_utc = $run.deadline_utc
    $cpFolder = Join-Path $folder ('checkpoints\' + $checkpoint.checkpoint_id); $null = New-Item -ItemType Directory -Path $cpFolder -Force
    Write-Json (Join-Path $cpFolder 'checkpoint.json') $checkpoint
    $inbox = Join-Path $folder ('inbox\' + $checkpoint.checkpoint_id); $null = New-Item -ItemType Directory -Path $inbox -Force
    $assessment = Read-Json (Join-Path $folder 'assessment.json')
    $assessment.checkpoint_sha256 = Get-Sha (Join-Path $cpFolder 'checkpoint.json')
    Write-Json (Join-Path $inbox 'assessment.json') $assessment
    $receipt = Read-Json (Join-Path $folder 'receipt.json'); $receipt.deadline_utc = $run.deadline_utc
    $receipt.checkpoint_sha256 = $assessment.checkpoint_sha256
    $receipt.assessment_sha256 = Get-Sha (Join-Path $inbox 'assessment.json')
    if ($scenario.name -ceq 'stale') { $receipt.nonce = 'wrong-stale-nonce' }
    Write-Json (Join-Path $inbox 'receipt.json') $receipt
    Initialize-Clock $folder ([Diagnostics.Stopwatch]::StartNew()) 1800000
    $accepted = $true
    try { Assert-Receipt $folder $checkpoint } catch { $accepted = $false }
    if ($accepted -ne $scenario.expected_allowed) { throw ('Offline protocol check failed: ' + $scenario.name) }
    $passed += $scenario.name
}
Add-Type -Path (Join-Path $PSScriptRoot 'HardDeadline.cs')
$timerFolder = Join-Path $Scratch 'timer'; $null = New-Item -ItemType Directory -Path $timerFolder
$hard = New-Object ResolenaDeadline -ArgumentList @($timerFolder, 0, 0L, '', 20, [DateTime]::UtcNow.AddMilliseconds(20))
Start-Sleep -Milliseconds 250; $hard.Cancel()
if (-not (Test-Path -LiteralPath (Join-Path $timerFolder 'hard_deadline.json'))) { throw 'Hard timer check failed.' }
$exportFolder = Join-Path $Scratch 'export'; $null = New-Item -ItemType Directory -Path $exportFolder
$original = [byte[]](239, 187, 191, 123, 125, 13, 10)
[IO.File]::WriteAllBytes((Join-Path $exportFolder 'synthetic.json'), $original)
[IO.File]::WriteAllBytes((Join-Path $exportFolder 'resources.jsonl'), [Text.Encoding]::UTF8.GetBytes("{}`npartial"))
Export-SmallResults $exportFolder 'synthetic-export'
$copied = Join-Path $exportFolder 'exports\synthetic-export\synthetic.json'
if ((Get-Sha $copied) -cne (Get-Sha (Join-Path $exportFolder 'synthetic.json'))) { throw 'Export changed original JSON bytes.' }
if ([IO.File]::ReadAllText((Join-Path $exportFolder 'exports\synthetic-export\resources.jsonl')) -cne "{}`n") { throw 'Partial JSONL snapshot guard failed.' }
@{ classification = 'Offline synthetic harness checks only; no model/process termination'; passed = $passed;
    hard_timer_without_owned_process = 'passed'; byte_preserving_export = 'passed'; scratch_preserved = $Scratch; DESIGN = 'pending'; linguistic_validation = 'pending' } | ConvertTo-Json -Depth 12
