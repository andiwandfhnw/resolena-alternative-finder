[CmdletBinding()]
param([switch]$ExecuteTransportLoggingCheck,
    [ValidatePattern('^[a-zA-Z0-9-]+$')][string]$Codespace='special-disco-vprpp7qrv9xrcwq6p',
    [string]$BundleDirectory='C:\ResolenaExperiments\uc001-execution-v1_3_0')

Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if ($MyInvocation.InvocationName -ne '.') {
    if (-not $ExecuteTransportLoggingCheck) {throw 'Preparation only; separate logging-only approval is required. No connection started.'}
    . (Join-Path $BundleDirectory 'Common.ps1')
}
. (Join-Path $PSScriptRoot 'Test-Transport.ps1')
$script:TransportLoggingRoot=$null

function Set-TransportLogPrivacy([string]$Root) {
    $sid=[Security.Principal.WindowsIdentity]::GetCurrent().User
    $acl=New-Object Security.AccessControl.DirectorySecurity
    $acl.SetOwner($sid)
    $acl.SetAccessRuleProtection($true,$false)
    $rule=New-Object Security.AccessControl.FileSystemAccessRule($sid,'FullControl','ContainerInherit,ObjectInherit','None','Allow')
    $acl.AddAccessRule($rule)
    Set-Acl -LiteralPath $Root -AclObject $acl
    $actual=Get-Acl -LiteralPath $Root
    $rules=@($actual.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier]))
    if (-not $actual.AreAccessRulesProtected -or $rules.Count -ne 1 -or
        $rules[0].IdentityReference.Value -ne $sid.Value -or $rules[0].IsInherited -or
        $rules[0].AccessControlType -ne 'Allow' -or $rules[0].FileSystemRights -ne 'FullControl' -or
        $rules[0].InheritanceFlags -ne 'ContainerInherit,ObjectInherit' -or $rules[0].PropagationFlags -ne 'None') {
        throw 'Private result-directory ACL not confirmed; stop before child startup.'
    }
}

function Start-TransportLoggingNativeProcess($Job,$Executable,$Arguments,$Stdout,$Stderr,$Key) {
    return [ContractProcesses]::Start($Job,$Executable,$Arguments,$Stdout,$Stderr,$Key)
}

function Start-ContractProcess($Job,$Executable,$Arguments,$Stdout,$Stderr,$Key) {
    $root=Split-Path $Stdout -Parent
    if ($null -eq $script:TransportLoggingRoot) {
        Set-TransportLogPrivacy $root
        $script:TransportLoggingRoot=$root
    }
    if ($root -ne $script:TransportLoggingRoot -or (Split-Path $Stderr -Parent) -ne $root) {throw 'Unexpected log directory.'}
    if ($Executable -ne 'C:\ResolenaExperiments\tools\gh-2.81.0\bin\gh.exe') {
        return Start-TransportLoggingNativeProcess $Job $Executable $Arguments $Stdout $Stderr $Key
    }
    $needle='"--" "-T"'
    if ([regex]::Matches($Arguments,[regex]::Escape($needle)).Count -ne 1) {throw 'Expected original SSH argument boundary absent.'}
    $logging='"--" "-vvv" "-T"'
    $Arguments=$Arguments.Replace($needle,$logging)
    $previous=[Environment]::GetEnvironmentVariable('GH_DEBUG','Process')
    try {
        [Environment]::SetEnvironmentVariable('GH_DEBUG','1','Process')
        return Start-TransportLoggingNativeProcess $Job $Executable $Arguments $Stdout $Stderr $Key
    } finally {[Environment]::SetEnvironmentVariable('GH_DEBUG',$previous,'Process')}
}

function Get-TransportDiagnosticLog([string]$Path) {
    try {
        if (-not [IO.File]::Exists($Path)) {return @{state='missing';text=''}}
        if ((Get-Item -LiteralPath $Path).Length -gt 1048576) {return @{state='not_read_over_1_mib';text=''}}
        return @{state='present';text=[IO.File]::ReadAllText($Path)}
    } catch {return @{state='read_failed';text=''}}
}

function Invoke-TransportLoggingProbe([string]$BundleDirectory,[string]$Codespace) {
    $clock=[Diagnostics.Stopwatch]::StartNew()
    $script:TransportLoggingRoot=$null
    if ((Get-ContractHash (Join-Path $PSScriptRoot 'Test-Transport.ps1')) -ne 'c0a3538a7e5fbea8df00b7396c186d87a5487844f503c4cbedc38a1a8ee9e67d' -or
        (Get-ContractHash (Join-Path $PSScriptRoot 'Probe-Endpoint.ps1')) -ne 'd5755775915c366a4b569817a354a634a98114e665e4e81b68a686cd864c8a8c') {
        throw 'Unchanged original model-free test and endpoint are required.'
    }
    $result=Invoke-TransportProbe $BundleDirectory $Codespace
    $combined=Get-TransportDiagnosticLog (Join-Path $result.result_directory 'transport.stderr.log')
    $cleanupConfirmed=$false
    try {
        $cleanup=Read-ContractJson (Join-Path $result.result_directory 'cleanup.json')
        $cleanupConfirmed=($cleanup.owned_job_closed -eq $true -and @($cleanup.owned_exits|Where-Object {-not $_.exit_confirmed}).Count -eq 0 -and $cleanup.errors.Count -eq 0)
    } catch {}
    $overallExpired=($clock.ElapsedMilliseconds -ge 60000)
    $summary=[ordered]@{
        version='uc001-transport-logging-2';outcome=$(if($overallExpired){'failed'}else{$result.outcome})
        elapsed_ms=$clock.ElapsedMilliseconds;overall_limit_ms=60000;overall_limit_exceeded=$overallExpired
        logs=@{combined=@{state=$combined.state;source='transport.stderr.log';producers=@('gh','OpenSSH')}}
        ssh_loopback_connect_marker=[bool]($combined.text -match '(?m)^debug1: Connecting to localhost \[(127\.0\.0\.1|::1)\] port 49189\.')
        ssh_connection_established_marker=[bool]($combined.text -match '(?m)^debug1: Connection established\.')
        ssh_local_refusal_marker=[bool]($combined.text -match '(?m)(connect to address (127\.0\.0\.1|::1) port 49189: Connection refused|connect to host localhost port 49189: Connection refused)')
        ssh_remote_protocol_marker=[bool]($combined.text -match '(?m)^debug1: Remote protocol version ')
        banner_refusal_marker=[bool]($combined.text -match 'banner exchange:[^\r\n]*Connection refused')
        forward_error_marker=[bool]($combined.text -match '(tunnel closed:|error connecting to forwarded port:|failed to open port forward channel:)')
        ssh_details_error_marker=[bool]($combined.text -match 'error getting ssh server details:')
        windows_owned_cleanup_confirmed=$cleanupConfirmed
        codespace_forward_cleanup='pending separate read-only receipt'
        root_cause='not_established';broker_target_visibility='not_guaranteed_by_pinned_logging'
        model_readiness_verified=$false;owned_gpu_counter_verified=$false;model_attempt_ledger_touched=$false
    }
    [IO.File]::WriteAllText((Join-Path $result.result_directory 'sanitized-summary.json'),($summary|ConvertTo-Json -Depth 6))
    if ($overallExpired) {$result.outcome='failed'}
    return $result
}

if ($MyInvocation.InvocationName -ne '.') {
    $result=Invoke-TransportLoggingProbe $BundleDirectory $Codespace
    [IO.File]::ReadAllText((Join-Path $result.result_directory 'sanitized-summary.json'))
    if ($result.outcome -eq 'failed') {exit 1}
}
