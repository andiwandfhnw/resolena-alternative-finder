param([Parameter(Mandatory=$true)][string]$Case)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$path=Join-Path (Get-Location) 'scripts/uc001_desktop_readiness/Check-RemainingReadiness.ps1'
if(-not (Test-Path -LiteralPath $path)){throw 'Remaining-readiness check absent (RED).'}
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($path,[ref]$tokens,[ref]$errors)
if($errors.Count){throw $errors[0]}
foreach($definition in $ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst]},$true)) {Invoke-Expression $definition.Extent.Text}
$versionReader=(Get-Item Function:\Read-LocalToolVersion).ScriptBlock
if($Case -eq 'version_io') {
    $exe=(Get-Process -Id $PID).Path
    $good=& $versionReader $exe '-NoProfile -NonInteractive -Command "[Console]::Error.WriteLine(''synthetic version'')"'
    if($good.State -ne 'ok' -or $good.Output -ne 'synthetic version'){throw 'Successful stderr version output was treated as a failure'}
    $bad=& $versionReader $exe '-NoProfile -NonInteractive -Command "exit 7"'
    if($bad.State -ne 'query_failed' -or $bad.ExitCode -ne 7){throw 'Version exit failure was hidden'}
    Write-Output 'PASS version_io'; return
}
function Assert-ContractWindows {}
function Assert-ContractBundle {}
function Get-ContractHash($Path) {return 'b083c3821590e85c56729d8238e18f0ed500dfcce36fcf175054c3367601217e'}
function Read-ContractJson($Path) {return ([IO.File]::ReadAllText($Path) | ConvertFrom-Json)}
function Get-ContractAssets {throw 'Must reuse historical completed integrity checks, never rehash assets here'}
function Get-ReadOnlyContractAdapter {throw 'Remaining-only check must not query GPU again'}
function Get-ContractResources {throw 'Remaining-only check must not sample resources'}
function Get-Command($Name) {
    if($Case -eq 'missing_gh' -and $Name -eq 'gh.exe'){throw 'Synthetic tool missing'}
    $source=Join-Path $env:WINDIR 'System32/OpenSSH/ssh.exe'
    if($Name -eq 'gh.exe'){$source='synthetic-gh.exe'}
    if($Case -eq 'other_ssh' -and $Name -eq 'ssh.exe'){$source='synthetic-msys-ssh.exe'}
    return [pscustomobject]@{Source=$source}
}
function Test-Path($LiteralPath) {return ($Case -ne 'missing_ssh')}
function Read-LocalToolVersion($Path,$Argument) {
    if($Argument -notin @('-V','--version')){throw 'Unexpected/non-version invocation'}
    $text='OpenSSH_for_Windows_9.5p1, LibreSSL 3.8.2'
    if($Argument -eq '--version'){$text='gh version 2.81.0 (synthetic)'}
    if($Case -eq 'wrong_gh' -and $Argument -eq '--version'){$text='gh version 2.82.0 (synthetic)'}
    if($Case -eq 'version_failure'){return [pscustomobject]@{State='query_failed';Output=$null;Error='synthetic';ExitCode=$null}}
    return [pscustomobject]@{State='ok';Output=$text;Error=$null;ExitCode=0}
}
function Get-NetTCPConnection {
    if($Case -eq 'ports_failed'){throw 'Synthetic TCP query failure'}
    if($Case -eq 'port_busy'){return [pscustomobject]@{LocalPort=49189;LocalAddress='127.0.0.1';State='Listen';OwningProcess=123}}
    return [pscustomobject]@{LocalPort=12345;LocalAddress='127.0.0.1';State='Listen';OwningProcess=123}
}
$savedWindowsDir=$env:WINDIR
try {
    if([string]::IsNullOrWhiteSpace($env:WINDIR)){$env:WINDIR='/synthetic-windows'}
    $bundle=Join-Path (Get-Location) 'scripts/uc001_preflight_capacity_v1_2_0'
    $report=Get-RemainingDesktopReadiness $bundle
    if($report.Integrity.HistoricalEntryCount -ne 54 -or $report.Integrity.FreshlyHashed -or $report.Integrity.RemainingFromReportedAttempt.Count -ne 0){throw 'Historical integrity evidence misrepresented'}
    if($report.FullPreflightVerified -or $report.StartupAuthorized -or $report.CodespacePort.State -ne 'not_checked'){throw 'Readiness scope overstated'}
    if($Case -eq 'ok') {
        if($report.Outcome -ne 'remaining_desktop_checks_passed' -or $report.Ports.State -ne 'no_observed_occupants'){throw 'Successful remaining check rejected'}
    } else {
        if($report.Outcome -ne 'blocked'){throw ('Did not block: '+$Case)}
        switch($Case) {
            'port_busy' {if($report.Ports.State -ne 'occupied'){throw 'Busy port state lost'}}
            'ports_failed' {if($report.Ports.State -ne 'query_failed'){throw 'Failed port query reported free'}}
            'other_ssh' {if($report.Ssh.State -ne 'path_mismatch'){throw 'Non-native PATH ssh silently selected'}}
        }
    }
} finally {$env:WINDIR=$savedWindowsDir}
Write-Output ('PASS '+$Case)
