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
    if (-not $OwnerAuthorized) { throw 'Separate owner authorization is required; proxy binding self-test not executed.' }
    $GraniteManifestPath = Join-Path $PSScriptRoot 'manifest.json'
    if ((Get-FileHash -LiteralPath $GraniteManifestPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedManifestSha256) { throw 'Proxy binding manifest hash differs.' }
    $GraniteManifest = Get-Content -Raw -LiteralPath $GraniteManifestPath | ConvertFrom-Json
    if ($GraniteManifest.version -ne 'uc001-granite-proxy-binding-selftest-v1' -or $GraniteManifest.execution_authorized -ne $false -or $GraniteManifest.scope -ne 'network-free-proxy-native-binding-selftest') { throw 'Unexpected proxy binding package scope.' }
    $GraniteExpected = @('controller.py','windows_job.py','worker.py','standins.py','proxy.py','proxy_no_network.py','proxy_binding_selftest.py','prior-budget.json','prior-budget.json.sha256','owner-statement.txt','selftest-config.json','Run-ProxyBindingCheck.ps1','README.md')
    $GraniteListed = @($GraniteManifest.files.PSObject.Properties.Name)
    if ($GraniteListed.Count -ne $GraniteExpected.Count -or @(Compare-Object $GraniteExpected $GraniteListed).Count) { throw 'Incomplete proxy binding package.' }
    $GraniteActual = @(Get-ChildItem -LiteralPath $PSScriptRoot -Force | ForEach-Object { $_.Name })
    if (@(Compare-Object @($GraniteExpected + 'manifest.json') $GraniteActual).Count) { throw 'Unexpected or missing package entry.' }
    foreach ($GraniteName in $GraniteExpected) {
        $GranitePath = Join-Path $PSScriptRoot $GraniteName
        if (-not (Test-Path -LiteralPath $GranitePath -PathType Leaf)) { throw ('Missing package file: ' + $GraniteName) }
        if ((Get-FileHash -LiteralPath $GranitePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $GraniteManifest.files.$GraniteName) { throw ('Package hash differs: ' + $GraniteName) }
    }
    if ($GraniteManifest.files.'proxy.py' -ne 'a7c62f83356636bea839633382bb62a3e53bcce466caea7b32226cece1e7bb1d') { throw 'Accepted proxy bytes differ.' }
    if ($GraniteManifest.files.'prior-budget.json' -ne '56a85b9ded9d6c4bf504462e11d551b59e016fcd1c77d8c5102b93ff7df7475a') { throw 'Accepted prior receipt differs.' }
    $GraniteConfig = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'selftest-config.json') | ConvertFrom-Json
    if ($GraniteConfig.selftest_only -ne $true) { throw 'Diagnostic-only configuration required.' }
    $GranitePython = 'C:\Users\AndiWand\Downloads\granite-python-3.12.11-20250702\env\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $GranitePython -PathType Leaf)) { throw 'Approved Granite Python is absent.' }
    $GraniteOutput = Join-Path (Split-Path -Parent $PSScriptRoot) ('proxy-binding-result-' + [Guid]::NewGuid().ToString())
    Write-Output ('Proxy binding self-test result directory: ' + $GraniteOutput)
    & $GranitePython -I -B (Join-Path $PSScriptRoot 'proxy_binding_selftest.py') --config (Join-Path $PSScriptRoot 'selftest-config.json') --output $GraniteOutput --owner-authorized
    if ($LASTEXITCODE -ne 0) { throw 'Proxy binding self-test failed: preserve complete output and stop without fixes/retry.' }
    Write-Output ('Proxy binding self-test result retained: ' + $GraniteOutput)
} catch {
    Write-Error -Message $_ -ErrorAction Continue
    exit 1
}
exit 0
