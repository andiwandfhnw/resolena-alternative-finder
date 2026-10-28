[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$BundleDirectory, [switch]$Worker, [string]$RunDirectory)

Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'

function Write-OwnershipJson([string]$Path, $Value) {
    [IO.File]::WriteAllText($Path, ($Value | ConvertTo-Json -Depth 12))
}
function Assert-OwnershipDeadline($Clock, [long]$Milliseconds) {
    if ($Clock.ElapsedMilliseconds -ge $Milliseconds) { throw 'Diagnostic deadline expired.' }
}
function Open-OwnershipProcess([int]$ProcessId) { return [Diagnostics.Process]::GetProcessById($ProcessId) }
function Start-OwnershipSupervisorProcess([string]$Script, [string]$Bundle, [string]$Root) {
    $command="`$null = & '"+$Script.Replace("'","''")+"' -Worker -BundleDirectory '"+$Bundle.Replace("'","''")+"' -RunDirectory '"+$Root.Replace("'","''")+"'"
    $info=New-Object Diagnostics.ProcessStartInfo
    $info.FileName=Join-Path $PSHOME 'powershell.exe'
    $info.Arguments='-NoLogo -NoProfile -NonInteractive -ExecutionPolicy RemoteSigned -EncodedCommand '+[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($command))
    $info.UseShellExecute=$false; $info.CreateNoWindow=$true
    return [Diagnostics.Process]::Start($info)
}
function Invoke-OwnershipWorker([string]$Root) {
    $clock=[Diagnostics.Stopwatch]::StartNew()
    $job=$null; $child=$null; $lookup=$null; $identity=$null; $expectedAbort=$false; $errors=@()
    try {
        Initialize-ContractProcessSupport
        Assert-OwnershipDeadline $clock 35000
        $job=New-ContractJob
        Write-OwnershipJson (Join-Path $Root 'child-start-attempt.json') @{attempted=$true}
        $childClock=[Diagnostics.Stopwatch]::StartNew()
        $idle=[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes('[System.Threading.Thread]::Sleep(10000)'))
        $child=Start-ContractProcess $job (Join-Path $PSHOME 'powershell.exe') ('-NoLogo -NoProfile -NonInteractive -EncodedCommand '+$idle) (Join-Path $Root 'child.stdout.log') (Join-Path $Root 'child.stderr.log') $null
        $child.StandardInput.Close()
        $identity=Get-ContractProcessIdentity $child
        Write-OwnershipJson (Join-Path $Root 'child-identity.json') @{pid=$identity.Id;started_utc=$identity.Started.ToString('o');started_ticks=$identity.Started.Ticks}
        $lookup=Open-OwnershipProcess $identity.Id
        $fresh=Get-ContractProcessIdentity $lookup
        $again=Get-ContractProcessIdentity $child
        if ($fresh.Id -ne $identity.Id -or $again.Id -ne $identity.Id -or $fresh.Started.Ticks -ne $identity.Started.Ticks -or $again.Started.Ticks -ne $identity.Started.Ticks) { throw 'Owned PID/creation-time mismatch.' }
        Assert-OwnershipDeadline $clock 35000
        Assert-OwnershipDeadline $childClock 2000
        throw 'Expected model-free diagnostic abort.'
    } catch {
        if ($_.Exception.Message -eq 'Expected model-free diagnostic abort.') { $expectedAbort=$true }
        else { $errors+=$_.Exception.Message }
    } finally {
        if ($null -ne $lookup) { try {$lookup.Dispose()} catch {$errors+=$_.Exception.Message} }
        try { Complete-ContractCleanup $null $job $child $null $Root } catch {$errors+=$_.Exception.Message}
    }
    $cleanup=$null
    try {
        $cleanup=Read-ContractJson (Join-Path $Root 'cleanup.json')
        if (-not $cleanup.owned_job_created -or -not $cleanup.owned_job_closed -or $cleanup.owned_exits.Count -ne 1 -or -not $cleanup.owned_exits[0].exit_confirmed -or $null -eq $identity -or $cleanup.owned_exits[0].pid -ne $identity.Id -or $cleanup.errors.Count) { throw 'Native owned job/exit confirmation is incomplete.' }
        Assert-OwnershipDeadline $clock 45000
    } catch {$errors+=$_.Exception.Message}
    $result=[ordered]@{outcome=$(if($expectedAbort -and -not $errors.Count){'native_ownership_cleanup_passed'}else{'failed'})
        expected_abort_exercised=$expectedAbort;identity=$identity;cleanup=$cleanup;errors=$errors
        elapsed_ms=$clock.ElapsedMilliseconds;owned_gpu_counter_verified=$false;model_allocation_verified=$false}
    Write-OwnershipJson (Join-Path $Root 'worker-result.json') $result
    return $result
}
function Complete-OwnershipChildCleanup([string]$Root) {
    $path=Join-Path $Root 'worker/child-identity.json'
    if (-not (Test-Path -LiteralPath $path)) {
        if (Test-Path -LiteralPath (Join-Path $Root 'worker/child-start-attempt.json')) { throw 'Child startup was attempted but its identity/exit is unconfirmed.' }
        return
    }
    $identity=Read-ContractJson $path
    $ownerId=Get-AssociationInteger $identity.pid 'Diagnostic child PID'
    $ticks=Get-AssociationInteger $identity.started_ticks 'Diagnostic child creation ticks'
    if ($ownerId -le 0 -or $ownerId -gt [int]::MaxValue -or $ticks -le 0 -or $ticks -gt [DateTime]::MaxValue.Ticks) { throw 'Recovery identity is invalid; no PID-only cleanup.' }
    $child=$null
    try {
        try {$child=Open-OwnershipProcess $ownerId} catch [ArgumentException] {
            Write-OwnershipJson (Join-Path $Root 'recovery.json') @{pid=$ownerId;state='no_current_process_at_owned_pid';kill_attempted=$false}
            return
        }
        $null=$child.Handle
        $fresh=Get-ContractProcessIdentity $child
        if ($fresh.Id -ne $ownerId -or $fresh.Started.Ticks -ne $ticks) { throw 'Recovery PID/creation time differs; do not terminate that process.' }
        $child.Kill()
        Complete-ContractCleanup $null $null $child $null (Join-Path $Root 'recovery')
    } finally {if ($null -ne $child) {$child.Dispose()}}
}
function Invoke-OwnershipSupervisor([string]$Script, [string]$Bundle, [string]$Root, $Clock) {
    $worker=$null; $identity=$null; $errors=@(); $result=$null
    try {
        Assert-OwnershipDeadline $Clock 40000
        $worker=Start-OwnershipSupervisorProcess $Script $Bundle (Join-Path $Root 'worker')
        $null=$worker.Handle
        $identity=Get-ContractProcessIdentity $worker
        $remaining=[int][Math]::Max(0,45000-$Clock.ElapsedMilliseconds)
        if (-not $worker.WaitForExit($remaining)) { throw 'Worker deadline expired; stop only the owned worker.' }
        if ($worker.ExitCode -ne 0) { throw 'Native worker failed; inspect preserved worker evidence.' }
        $result=Read-ContractJson (Join-Path $Root 'worker/worker-result.json')
        if ($result.outcome -ne 'native_ownership_cleanup_passed' -or -not $result.expected_abort_exercised -or -not $result.cleanup.owned_job_created -or -not $result.cleanup.owned_job_closed -or $result.cleanup.owned_exits.Count -ne 1 -or -not $result.cleanup.owned_exits[0].exit_confirmed -or $result.cleanup.owned_exits[0].pid -ne $result.identity.Id -or $result.errors.Count) { throw 'Worker success/cleanup receipt is missing or inconsistent.' }
    } catch {$errors+=$_.Exception.Message}
    finally {
        if ($null -ne $worker) {
            try {
                $worker.Refresh()
                if (-not $worker.HasExited) {
                    try {
                        $fresh=Get-ContractProcessIdentity $worker
                        if ($null -eq $identity -or $fresh.Id -ne $identity.Id -or $fresh.Started.Ticks -ne $identity.Started.Ticks) { throw 'Supervisor owned-worker identity changed.' }
                    } catch {$errors+=$_.Exception.Message}
                    # This is the retained process/handle returned by our own Start, never a PID lookup.
                    $worker.Kill()
                }
            } catch {$errors+=$_.Exception.Message}
            try {Complete-ContractCleanup $null $null $worker $null (Join-Path $Root 'supervisor')} catch {$errors+=$_.Exception.Message}
        }
        if ($errors.Count) {try {Complete-OwnershipChildCleanup $Root} catch {$errors+=$_.Exception.Message}}
    }
    if ($Clock.ElapsedMilliseconds -ge 60000) {$errors+='Overall 60-second diagnostic deadline exceeded.'}
    $report=[ordered]@{version='uc001-native-ownership-check-1';outcome=$(if($null -ne $result -and -not $errors.Count){'native_ownership_cleanup_passed'}else{'failed'})
        worker_identity=$identity;native_result=$result;errors=$errors;elapsed_ms=$Clock.ElapsedMilliseconds;deadline_ms=60000
        result_directory=$Root;owned_gpu_counter_verified=$false;model_allocation_verified=$false;model_attempt_ledger_touched=$false}
    Write-OwnershipJson (Join-Path $Root 'result.json') $report
    return $report
}

if ($MyInvocation.InvocationName -ne '.') {
    $clock=[Diagnostics.Stopwatch]::StartNew()
    try {
        $BundleDirectory=[IO.Path]::GetFullPath($BundleDirectory)
        $freeze=Join-Path $BundleDirectory 'freeze.json'
        if ((Get-FileHash -LiteralPath $freeze -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'b7ed2e54c507c434ec157d0b3daed3440136bde70fd0c76ab79df6707301e615') {throw 'Expected unchanged v1.3.0 freeze required.'}
        $pins=([IO.File]::ReadAllText($freeze)|ConvertFrom-Json).files
        foreach($name in @('Common.ps1','ProcessTools.cs')) {
            if ((Get-FileHash -LiteralPath (Join-Path $BundleDirectory $name) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pins.$name) {throw ('Frozen helper mismatch: '+$name)}
        }
        . (Join-Path $BundleDirectory 'Common.ps1')
        Assert-ContractWindows
        if ($Worker) {
            if (-not $RunDirectory -or -not (Test-Path -LiteralPath $RunDirectory -PathType Container)) {throw 'Supervisor-created worker directory required.'}
            $result=Invoke-OwnershipWorker $RunDirectory
        } else {
            if ($RunDirectory) {throw 'Result directory is generated exclusively; do not reuse evidence directories.'}
            $base=Join-Path $PSScriptRoot 'results'
            if (-not (Test-Path -LiteralPath $base)) {$null=New-Item -ItemType Directory -Path $base}
            $root=Join-Path $base ([guid]::NewGuid().ToString())
            $null=New-Item -ItemType Directory -Path $root
            foreach($name in @('worker','supervisor','recovery')) {$null=New-Item -ItemType Directory -Path (Join-Path $root $name)}
            $result=Invoke-OwnershipSupervisor $PSCommandPath $BundleDirectory $root $clock
        }
        $result | ConvertTo-Json -Depth 12
        if ($result.outcome -ne 'native_ownership_cleanup_passed') {exit 1}
    } catch {
        @{outcome='failed';error=$_.Exception.Message;owned_gpu_counter_verified=$false;model_allocation_verified=$false} | ConvertTo-Json
        exit 1
    }
}
