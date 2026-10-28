[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-f]{64}$')]
    [string]$ExpectedManifestSha256,
    [switch]$OwnerAuthorized
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
try {
    if (-not $OwnerAuthorized) { throw 'Separate owner authorization is required; diagnostic not executed.' }
    $GraniteManifestPath = Join-Path $PSScriptRoot 'manifest.json'
    if ((Get-FileHash -LiteralPath $GraniteManifestPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedManifestSha256) { throw 'Diagnostic manifest hash differs.' }
    $GraniteManifest = Get-Content -Raw -LiteralPath $GraniteManifestPath | ConvertFrom-Json
    if ($GraniteManifest.version -ne 'uc001-granite-controller-identity-diagnostic-v1' -or $GraniteManifest.execution_authorized -ne $false -or $GraniteManifest.purpose -ne 'offline-prepared-scoped-unknown-identity-diagnostic') { throw 'Unexpected diagnostic manifest scope.' }
    $GraniteExpected = @('controller.py', 'windows_job.py', 'worker.py', 'standins.py', 'controller-config.template.json', 'Run-IdentityDiagnostic.ps1', 'README.md')
    $GraniteListed = @($GraniteManifest.files.PSObject.Properties.Name)
    if ($GraniteListed.Count -ne $GraniteExpected.Count -or @(Compare-Object $GraniteExpected $GraniteListed).Count) { throw 'Incomplete diagnostic package.' }
    $GraniteActual = @(Get-ChildItem -LiteralPath $PSScriptRoot -Force | ForEach-Object { $_.Name })
    if (@(Compare-Object @($GraniteExpected + 'manifest.json') $GraniteActual).Count) { throw 'Unexpected or missing package entry.' }
    foreach ($GraniteName in $GraniteExpected) {
        $GranitePath = Join-Path $PSScriptRoot $GraniteName
        if (-not (Test-Path -LiteralPath $GranitePath -PathType Leaf)) { throw ('Missing package file: ' + $GraniteName) }
        if ((Get-FileHash -LiteralPath $GranitePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $GraniteManifest.files.$GraniteName) { throw ('Package hash differs: ' + $GraniteName) }
    }
    $GraniteTemplate = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'controller-config.template.json') | ConvertFrom-Json
    if ($GraniteTemplate.execution_authorized -ne $false) { throw 'Native acquisition/build must remain disabled.' }
    $GraniteHelperNames = @('controller.py', 'windows_job.py', 'worker.py', 'standins.py')
    if (@(Compare-Object $GraniteHelperNames @($GraniteTemplate.helper_hashes.PSObject.Properties.Name)).Count) { throw 'Helper hash list differs.' }
    foreach ($GraniteName in $GraniteHelperNames) {
        if ($GraniteTemplate.helper_hashes.$GraniteName -ne $GraniteManifest.files.$GraniteName) { throw 'Template helper hash differs.' }
    }
    $GranitePython = 'C:\Users\AndiWand\Downloads\granite-python-3.12.11-20250702\env\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $GranitePython -PathType Leaf)) { throw 'Approved Granite Python is absent.' }
    $GraniteOutput = Join-Path (Split-Path -Parent $PSScriptRoot) ('ownership-identity-diagnostic-' + [Guid]::NewGuid().ToString())
    Write-Output ('Diagnostic output directory: ' + $GraniteOutput)
    & $GranitePython -I -B (Join-Path $PSScriptRoot 'controller.py') ownership-self-test --output $GraniteOutput
    if ($LASTEXITCODE -ne 0) { throw 'Ownership diagnostic failed: preserve output and stop without fixes/retry.' }
    Write-Output ('Ownership diagnostic output retained: ' + $GraniteOutput)
} catch {
    Write-Error -Message $_ -ErrorAction Continue
    exit 1
}
exit 0
