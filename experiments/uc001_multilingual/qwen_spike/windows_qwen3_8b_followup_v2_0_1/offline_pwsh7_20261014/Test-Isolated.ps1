param([Parameter(Mandatory=$true)][string]$BundleRoot, [Parameter(Mandatory=$true)][string]$Output)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSEdition -cne 'Core' -or $PSVersionTable.PSVersion.Major -ne 7) { throw 'This is an isolated PowerShell 7 check, not the Windows runner.' }
if (Test-Path -LiteralPath $Output) { throw 'Existing regression results preserved; use a new output path.' }
$BundleRoot = [IO.Path]::GetFullPath($BundleRoot)
$freezePath = Join-Path $BundleRoot 'freeze.json'
$freeze = [IO.File]::ReadAllText($freezePath) | ConvertFrom-Json
foreach ($property in $freeze.files.PSObject.Properties) {
    $hash = (Get-FileHash -LiteralPath (Join-Path $BundleRoot $property.Name) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -cne $property.Value) { throw ('Frozen payload mismatch: ' + $property.Name) }
}
$parsed = @()
foreach ($file in @(Get-ChildItem -LiteralPath $BundleRoot -Filter '*.ps1' -Recurse)) {
    $tokens = $null; $errors = $null
    $null = [Management.Automation.Language.Parser]::ParseFile($file.FullName, [ref]$tokens, [ref]$errors)
    if ($errors) { $errors | Format-List; throw ('PowerShell 7 parser failure: ' + $file.Name) }
    $parsed += $file.FullName.Substring($BundleRoot.Length + 1)
}
$tokens = $null; $errors = $null
$commonAst = [Management.Automation.Language.Parser]::ParseFile((Join-Path $BundleRoot 'Common.ps1'), [ref]$tokens, [ref]$errors)
$script:OwnershipObservation = $null
foreach ($name in @('Test-OffloadText', 'Get-OwnedLiveProcess')) {
    $definition = $commonAst.FindAll({ param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] }, $true) | Where-Object { $_.Name -ceq $name }
    if (@($definition).Count -ne 1) { throw 'Expected exactly one isolated function definition.' }
    . ([scriptblock]::Create($definition.Extent.Text))
}
$windowsAst = [Management.Automation.Language.Parser]::ParseFile((Join-Path $BundleRoot 'Test-Harness.ps1'), [ref]$tokens, [ref]$errors)
$statements = @($windowsAst.EndBlock.Statements)
$begin = -1; $end = -1
for ($i = 0; $i -lt $statements.Count; $i++) {
    if ($statements[$i] -is [Management.Automation.Language.AssignmentStatementAst]) {
        if ($statements[$i].Left.Extent.Text -ceq '$log') { $begin = $i }
        if ($statements[$i].Left.Extent.Text -ceq '$report') { $end = $i; break }
    }
}
if ($begin -lt 0 -or $end -le $begin) { throw 'Frozen regression boundaries changed.' }
$body = ($statements[$begin..($end - 1)] | ForEach-Object { $_.Extent.Text }) -join "`n"
$body = $body.Replace('$PSScriptRoot', '$BundleRoot').Replace("'fixtures\", "'fixtures/")
. ([scriptblock]::Create($body))
if ($passed.Count -ne 19) { throw 'Expected 19 original-log, evidence and mocked ownership checks.' }
$report = [ordered]@{
    classification = 'Isolated offline PowerShell 7 regressions; no inference; no real process lookup/start/stop'
    utc = [DateTime]::UtcNow.ToString('o'); version = $PSVersionTable.PSVersion.ToString(); edition = $PSVersionTable.PSEdition
    platform = [string]$PSVersionTable.Platform; os = $PSVersionTable.OS
    freeze_sha256 = (Get-FileHash -LiteralPath $freezePath -Algorithm SHA256).Hash.ToLowerInvariant()
    functions_loaded_from_frozen_AST = @('Test-OffloadText', 'Get-OwnedLiveProcess')
    frozen_Windows_regression_body_reused = $true; parsed_scripts = $parsed; passed = $passed
    original_Groups_error_reproduced = $groupsReproduced
    Windows_guards_modified_or_called = $false; Windows_5_1_compatibility_verified = $false
    Windows_specific_verification = 'pending'; inference_requests = 0; DESIGN = 'pending'; linguistic_validation = 'pending'
}
$parent = [IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($Output))
$null = [IO.Directory]::CreateDirectory($parent)
[IO.File]::WriteAllText($Output, ($report | ConvertTo-Json -Depth 12), (New-Object Text.UTF8Encoding($false)))
$report | ConvertTo-Json -Depth 12
