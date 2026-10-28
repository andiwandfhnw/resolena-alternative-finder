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
    if (-not $OwnerAuthorized) { throw 'Separate owner authorization is required; readiness check not executed.' }
    $GraniteManifestPath = Join-Path $PSScriptRoot 'manifest.json'
    if ((Get-FileHash -LiteralPath $GraniteManifestPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedManifestSha256) { throw 'Readiness manifest hash differs.' }
    $GraniteManifest = Get-Content -Raw -LiteralPath $GraniteManifestPath | ConvertFrom-Json
    if ($GraniteManifest.version -ne 'uc001-granite-proxy-identities-v1' -or $GraniteManifest.execution_authorized -ne $false -or $GraniteManifest.readiness_scope -ne 'structural_only' -or $GraniteManifest.purpose -ne 'offline-prepared-proxy-identity-binding') { throw 'Unexpected readiness package scope.' }
    $GraniteExpected = @('controller.py','windows_job.py','worker.py','standins.py','proxy.py','check.py','controller-config.template.json','Run-ReadinessCheck.ps1','README.md')
    $GraniteListed = @($GraniteManifest.files.PSObject.Properties.Name)
    if ($GraniteListed.Count -ne $GraniteExpected.Count -or @(Compare-Object $GraniteExpected $GraniteListed).Count) { throw 'Incomplete readiness package.' }
    $GraniteActual = @(Get-ChildItem -LiteralPath $PSScriptRoot -Force | ForEach-Object { $_.Name })
    if (@(Compare-Object @($GraniteExpected + 'manifest.json') $GraniteActual).Count) { throw 'Unexpected or missing package entry.' }
    foreach ($GraniteName in $GraniteExpected) {
        $GranitePath = Join-Path $PSScriptRoot $GraniteName
        if (-not (Test-Path -LiteralPath $GranitePath -PathType Leaf)) { throw ('Missing package file: ' + $GraniteName) }
        if ((Get-FileHash -LiteralPath $GranitePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $GraniteManifest.files.$GraniteName) { throw ('Package hash differs: ' + $GraniteName) }
    }
    if ($GraniteManifest.files.'proxy.py' -ne 'a7c62f83356636bea839633382bb62a3e53bcce466caea7b32226cece1e7bb1d') { throw 'Accepted proxy bytes differ.' }
    $GraniteTemplate = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'controller-config.template.json') | ConvertFrom-Json
    if ($GraniteTemplate.execution_authorized -ne $false) { throw 'Native acquisition/build must remain disabled.' }
    $GranitePython = 'C:\Users\AndiWand\Downloads\granite-python-3.12.11-20250702\env\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $GranitePython -PathType Leaf)) { throw 'Approved Granite Python is absent.' }
    $GraniteOutput = Join-Path (Split-Path -Parent $PSScriptRoot) ('readiness-proxy-identities-' + [Guid]::NewGuid().ToString())
    Write-Output ('Structural readiness output directory: ' + $GraniteOutput)
    & $GranitePython -I -B (Join-Path $PSScriptRoot 'check.py') --expected-manifest-sha256 $ExpectedManifestSha256 --output $GraniteOutput
    if ($LASTEXITCODE -ne 0) { throw 'Structural readiness failed: preserve output and stop without fixes/retry.' }
    Write-Output ('Structural readiness output retained: ' + $GraniteOutput)
} catch {
    Write-Error -Message $_ -ErrorAction Continue
    exit 1
}
exit 0
