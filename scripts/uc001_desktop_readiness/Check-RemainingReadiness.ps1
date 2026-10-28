[CmdletBinding()]
param([string]$BundlePath='C:\ResolenaExperiments\uc001-preflight-capacity-v1_2_0')

function Read-LocalToolVersion([string]$Path, [string]$Argument) {
    $process=New-Object Diagnostics.Process
    try {
        $process.StartInfo=New-Object Diagnostics.ProcessStartInfo
        $process.StartInfo.FileName=$Path; $process.StartInfo.Arguments=$Argument
        $process.StartInfo.UseShellExecute=$false; $process.StartInfo.CreateNoWindow=$true
        $process.StartInfo.RedirectStandardOutput=$true; $process.StartInfo.RedirectStandardError=$true
        if(-not $process.Start()){throw 'Version process did not start.'}
        $stdout=$process.StandardOutput.ReadToEndAsync(); $stderr=$process.StandardError.ReadToEndAsync()
        if(-not $process.WaitForExit(5000)) {
            $process.Kill(); $null=$process.WaitForExit(1000)
            throw 'Owned version query exceeded five seconds; stopped without retry.'
        }
        $output=($stdout.GetAwaiter().GetResult()+"`n"+$stderr.GetAwaiter().GetResult()).Trim()
        return [pscustomobject]@{State=$(if($process.ExitCode -eq 0){'ok'}else{'query_failed'});Output=$output;ExitCode=$process.ExitCode;Error=$null}
    } catch { return [pscustomobject]@{State='query_failed';Output=$null;ExitCode=$null;Error=$_.Exception.Message} }
    finally {$process.Dispose()}
}

function Get-RemainingDesktopReadiness([string]$Bundle) {
    $report=[ordered]@{Outcome='blocked';Integrity=$null;Ssh=@{State='not_queried'};Gh=@{State='not_queried'}
        Ports=@{State='not_queried'};CodespacePort=@{Port=49188;State='not_checked';Reason='Separate Codespace localhost'}
        FullPreflightVerified=$false;StartupAuthorized=$false;Error=$null
        ExecutionBlocker='Original launcher identity and monitor usage rules require alignment with v1.2.0 before execution.'}
    try {
        Assert-ContractWindows
        if((Get-ContractHash (Join-Path $Bundle 'freeze.json')) -ne 'b083c3821590e85c56729d8238e18f0ed500dfcce36fcf175054c3367601217e') {throw 'Use the complete unchanged v1.2.0 bundle.'}
        Assert-ContractBundle
        $config=Read-ContractJson (Join-Path $Bundle 'config.json')
        $runtime=Read-ContractJson (Join-Path $Bundle 'runtime-files.json')
        $report.Integrity=[ordered]@{State='historical_completion_inferred';HistoricalEntryCount=(@($config.assets).Count+@($runtime.PSObject.Properties).Count)
            FreshlyHashed=$false;CurrentIntegrityVerified=$false;RemainingFromReportedAttempt=@()
            Basis='Original reported adapter stop follows successful Get-ContractAssets: runtime ZIP, model and all 52 extracted runtime files. Conditional on unchanged original script/inputs; not a fresh hash receipt.'
            BeforeStartup='Fresh integrity validation is still required in any future authorized launcher; never use this report as current asset proof.'}
    } catch {$report.Error=$_.Exception.Message;return [pscustomobject]$report}
    try {
        $native=[IO.Path]::GetFullPath((Join-Path $env:WINDIR 'System32/OpenSSH/ssh.exe'))
        if(-not (Test-Path -LiteralPath $native -PathType Leaf)) {$report.Ssh=@{State='missing';NativePath=$native}}
        else {
            $pathSsh=Get-Command ssh.exe -CommandType Application -ErrorAction Stop
            $version=Read-LocalToolVersion $native '-V'
            $state=$version.State
            if($state -eq 'ok' -and $version.Output -notmatch '^OpenSSH_for_Windows_') {$state='unexpected_version_banner'}
            if(-not [string]::Equals([IO.Path]::GetFullPath($pathSsh.Source),$native,[StringComparison]::OrdinalIgnoreCase)) {$state='path_mismatch'}
            $report.Ssh=@{State=$state;NativePath=$native;PathResolved=$pathSsh.Source;Version=$version}
        }
    } catch {$report.Ssh=@{State=$(if($_.CategoryInfo.Category -eq 'ObjectNotFound'){'missing'}else{'query_failed'});Error=$_.Exception.Message}}
    try {
        $gh=Get-Command gh.exe -CommandType Application -ErrorAction Stop
        $version=Read-LocalToolVersion $gh.Source '--version'
        $state=$version.State
        if($state -eq 'ok' -and $version.Output -notmatch '^gh version 2\.81\.0(?:\s|$)') {$state='wrong_version'}
        $report.Gh=@{State=$state;Path=$gh.Source;RequiredVersion='2.81.0';Version=$version}
    } catch {$report.Gh=@{State=$(if($_.CategoryInfo.Category -eq 'ObjectNotFound'){'missing'}else{'query_failed'});Error=$_.Exception.Message}}
    try {
        $ports=@([int]$config.windows_port,[int]$config.ssh_bridge_port)
        $occupied=@(Get-NetTCPConnection -ErrorAction Stop | Where-Object {$_.LocalPort -in $ports} | Select-Object LocalAddress,LocalPort,State,OwningProcess)
        $report.Ports=@{State=$(if($occupied.Count){'occupied'}else{'no_observed_occupants'});Required=$ports;Occupants=$occupied
            Scope='Observed TCP allocations only; no bind/connect test or proof of future loopback binding.'}
    } catch {$report.Ports=@{State='query_failed';Error=$_.Exception.Message}}
    if($report.Ssh.State -eq 'ok' -and $report.Gh.State -eq 'ok' -and $report.Ports.State -eq 'no_observed_occupants') {$report.Outcome='remaining_desktop_checks_passed'}
    return [pscustomobject]$report
}

if($MyInvocation.InvocationName -ne '.') {
    Set-StrictMode -Version Latest
    $ErrorActionPreference='Stop'
    . (Join-Path $BundlePath 'Common.ps1')
    $result=Get-RemainingDesktopReadiness $BundlePath
    $result | ConvertTo-Json -Depth 12
    if($result.Outcome -ne 'remaining_desktop_checks_passed'){exit 1}
}
