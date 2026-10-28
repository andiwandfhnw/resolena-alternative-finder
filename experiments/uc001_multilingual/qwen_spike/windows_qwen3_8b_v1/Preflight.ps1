param([Parameter(Mandatory=$true)][string]$Root)
$parseErrors = @()
foreach ($script in @(Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.ps1')) {
    $tokens = $null; $errors = $null
    $null = [Management.Automation.Language.Parser]::ParseFile($script.FullName, [ref]$tokens, [ref]$errors)
    if ($errors) { $parseErrors += $errors }
}
if ($parseErrors.Count -gt 0) { $parseErrors | Format-List; throw 'PowerShell parser errors; stop before setup.' }
. (Join-Path $PSScriptRoot 'Common.ps1')
Assert-Bundle $PSScriptRoot
$Root = [IO.Path]::GetFullPath($Root).TrimEnd('\')
if ($Root.StartsWith('\\')) { throw 'A dedicated local drive folder is required; no network share.' }
Assert-NoDuplicate $Root
$config = Read-Json (Join-Path $PSScriptRoot 'config.json')
$adapter = Get-Adapter
$sample = Get-ResourceSample $Root $adapter
try { Assert-Resources $sample $config $true } catch {
    [ordered]@{ status = 'preflight_failed'; measured = $sample; thresholds = $config.limits; error = $_.Exception.Message } | ConvertTo-Json -Depth 8
    throw
}
$drivers = @(Get-CimInstance -ClassName Win32_VideoController | Where-Object { $_.Name -match 'RX\s*6800\s*XT' } | Select-Object Name, DriverVersion, DriverDate)
$processors = @(Get-CimInstance -ClassName Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors)
[ordered]@{ status = 'preflight_pass'; target_folder = $Root; resources = $sample; drivers = $drivers;
    processors = $processors; powershell = $PSVersionTable.PSVersion.ToString();
    bundle_version = '1.0.0'; freeze_sha256 = Get-Sha (Join-Path $PSScriptRoot 'freeze.json');
    inference_compatibility = 'untested'; effect = 'read-only; no download/model/process or timed run start' } | ConvertTo-Json -Depth 8
