param([Parameter(Mandatory=$true)][string]$Case)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$selectedCase=$Case
$parent=Join-Path (Split-Path $PSScriptRoot -Parent) 'uc001_execution_v1_3_0'
. (Join-Path $parent 'Common.ps1')
. (Join-Path $parent 'Run-Windows.ps1') -Codespace synthetic
. (Join-Path $PSScriptRoot 'Run-Windows.ps1')
$productionProgressReader=(Get-Command Read-LocalProgress).ScriptBlock
$Case=$selectedCase
$script:starts=0; $script:closed=0; $script:now=0
$script:progressReads=0
$script:state=[pscustomobject]@{case=1;phase='running'}
$temp=Join-Path ([IO.Path]::GetTempPath()) ('uc001-local-offline-'+[guid]::NewGuid())
function Require($Value,$Message) {if(-not $Value){throw $Message}}
function Owner([int]$Number) {
    $value=[pscustomobject]@{Id=$Number;StartTime=[DateTime]::UtcNow;HasExited=$false;ExitCode=0}
    $value|Add-Member ScriptMethod Refresh {}
    $value|Add-Member ScriptMethod WaitForExit {param($Milliseconds) return ($Case -ne 'cleanup_failure')}
    $value|Add-Member ScriptMethod Dispose {}
    $inputStream=[pscustomobject]@{}
    $inputStream|Add-Member ScriptMethod Close {}
    $inputStream|Add-Member ScriptMethod Flush {}
    $inputStream|Add-Member ScriptMethod WriteLine {
        param($Text)
        if($Text -match '^begin (\d+)$') {$script:state=[pscustomobject]@{case=[int]$Matches[1];phase='validated'}}
        elseif($Text -match '^advance (\d+)$') {
            $number=[int]$Matches[1]
            $script:state=[pscustomobject]@{case=$(if($number -eq 14){14}else{$number+1});phase=$(if($number -eq 14){'complete'}else{'ready'})}
            if($number -eq 14){$script:worker.HasExited=$true}
        } else {$script:state=[pscustomobject]@{case=1;phase='ready'}}
    }
    $value|Add-Member NoteProperty StandardInput $inputStream
    return $value
}
function Read-LocalProgress {
    if($Case -eq 'complete_race') {
        $script:progressReads++
        return [pscustomobject]@{case=14;phase=$(if($script:progressReads -eq 1){'validated'}else{'complete'})}
    }
    if($Case -eq 'late_validation') {$script:now=90001;return [pscustomobject]@{case=1;phase='validated'}}
    if($Case -eq 'wrong_case') {return [pscustomobject]@{case=2;phase='validated'}}
    return $script:state
}
function Get-LocalElapsed($Clock) {
    if($Case -eq 'hang') {$script:now+=45000}
    if($Case -eq 'deadline') {return 90000}
    if($Case -in @('hang','late_validation')) {return $script:now}
    return $Clock.Elapsed.TotalMilliseconds
}
try {
    if($Case -eq 'progress_atomic') {
        Require ($productionProgressReader.ToString().Contains('[IO.FileShare]::Delete')) 'Windows progress reader must permit the producer atomic replacement while open'
        $null=New-Item -ItemType Directory -Path $temp
        [IO.File]::WriteAllText((Join-Path $temp 'progress.json'),'{"case":9,"phase":"ready"}')
        $state=& $productionProgressReader $temp
        Require ($state.case -eq 9 -and $state.phase -eq 'ready') 'Actual bounded progress reader failed'
        [IO.File]::WriteAllText((Join-Path $temp 'progress.json'),('x'*4097))
        $failed=$false;try {$null=& $productionProgressReader $temp} catch {$failed=$true}
        Require $failed 'Unbounded progress record accepted'
        'PASS '+$Case
        return
    }
    if($Case.StartsWith('timer_')) {
        Add-Type -Path (Join-Path $PSScriptRoot 'DeadlineGuard.cs')
        Add-Type -TypeDefinition @'
using System;
using System.Threading;
public static class SyntheticJobClose {
    public static int Calls;
    public static bool Result = true;
    public static ManualResetEvent Done = new ManualResetEvent(false);
    public static bool Close(IntPtr job) { Interlocked.Increment(ref Calls); Done.Set(); return Result; }
}
'@
        $guard=[Uc001Local.DeadlineGuard]::new([IntPtr]123,[SyntheticJobClose].GetMethod('Close'))
        if($Case -eq 'timer_limit') {
            foreach($value in @(0,90001)) {
                $failed=$false;try {$guard.Arm($value)} catch {$failed=$true}
                Require $failed 'Absolute timer could exceed the 90-second maximum'
            }
        } elseif($Case -eq 'timer_disarm') {
            $guard.Arm(90000);$guard.Disarm()
            Require (-not [SyntheticJobClose]::Done.WaitOne(30)) 'Disarmed timer closed the owned job'
        } else {
            if($Case -eq 'timer_close_failure'){[SyntheticJobClose]::Result=$false}
            $guard.Arm(20)
            Require ([SyntheticJobClose]::Done.WaitOne(5000)) 'Independent timer did not run while PowerShell was blocked'
            Require $guard.Expired 'Timer expiration was hidden'
            $failed=$false;try {$guard.Disarm()} catch {$failed=$true}
            Require $failed 'Late disarm was accepted'
        }
        $closed=$guard.Close();$null=$guard.Close()
        Require ($closed -eq ($Case -ne 'timer_close_failure')) 'Native close failure was not preserved'
        Require ([SyntheticJobClose]::Calls -eq 1) 'Owned native job handle was closed more than once'
        'PASS '+$Case
        return
    }
    $script:worker=Owner 102
    $identity=Get-ContractProcessIdentity $script:worker
    if($Case -eq 'complete_race') {
        function Update-LocalResources {}
        $script:worker.HasExited=$true
        $null=Wait-LocalPhase $script:worker $identity $temp 14 'complete' ([Diagnostics.Stopwatch]::StartNew())
        Require ($script:progressReads -ge 2) 'Completion was not reread after observing worker exit'
        'PASS '+$Case
        return
    }
    if($Case -in @('deadline','late_validation','hang','wrong_case')) {
        function Update-LocalResources {}
        $failed=$false
        try {$null=Wait-LocalPhase $script:worker $identity $temp 1 'validated' ([Diagnostics.Stopwatch]::StartNew())} catch {$failed=$true}
        Require $failed 'Deadline/invalid-phase guard missed a failed request'
        Require ($script:starts -eq 0) 'Native process unexpectedly started'
    } else {
        function Assert-ContractWindows {}
        function Assert-ContractBundle {}
        function Invoke-LocalPythonPreflight {if($Case -eq 'review_missing'){throw 'Synthetic pending qualified review'}}
        function Set-LocalPrivateDirectory {}
        function Get-ContractAssets {}
        function Get-ContractAdapter {return [pscustomobject]@{Name='synthetic-only'}}
        function Get-CimInstance {return}
        function Get-NetTCPConnection {
            if($script:starts -gt 0){return [pscustomobject]@{LocalAddress='127.0.0.1';LocalPort=49187;OwningProcess=101}}
        }
        function Read-ContractJson($Path) {
            $data=([IO.File]::ReadAllText($Path)|ConvertFrom-Json)
            if($Path.EndsWith('config.json')) {$data.reuse_root=Join-Path $temp 'assets'}
            return $data
        }
        function Get-ContractResources {
            $free=15GB
            if($Case -eq 'resource_failure' -and $script:starts -gt 0) {$free=0}
            return [ordered]@{ram_free=24GB;gpu_free=$free;disk_free=10GB;owned_gpu=1GB;owned_rss=1GB;artifact_bytes=0}
        }
        function Initialize-ContractProcessSupport {}
        function New-ContractJob {return 'synthetic-only-job'}
        function Close-ContractJob {$script:closed++;return $true}
        function New-LocalDeadline($Job) {
            $guard=[pscustomobject]@{Job=$Job;Arms=0;Disarms=0}
            $guard|Add-Member ScriptMethod Arm {param($Milliseconds) Require ($Milliseconds -eq 90000) 'Request deadline changed';$this.Arms++}
            $guard|Add-Member ScriptMethod Disarm {$this.Disarms++}
            $guard|Add-Member ScriptMethod Close {$script:closed++;return ($Case -ne 'job_close_failure')}
            $script:deadlineFixture=$guard
            return $guard
        }
        function Start-ContractProcess {
            param($Job,$Executable,$Arguments,$Stdout,$Stderr,$Key)
            $script:starts++
            Require ($script:starts -le 2) 'Extra startup/transport process'
            if($script:starts -eq 1) {
                Require ($Executable.EndsWith('llama-server.exe')) 'Unexpected server executable'
                [IO.File]::WriteAllText($Stderr,'synthetic startup log')
                return (Owner 101)
            }
            Require ($Executable -eq 'C:\ResolenaExperiments\uc001-validator-env\Scripts\python.exe') 'Wrong Python executable'
            Require ($Arguments.Contains('"-I" "-X" "utf8" "-B"')) 'Python isolation/encoding changed'
            Require ($null -eq $Key) 'Capture key must use stdin, not the environment/command'
            return $script:worker
        }
        function New-ContractHttpClient {
            $value=[pscustomobject]@{}; $value|Add-Member ScriptMethod Dispose {};return $value
        }
        $propsJson='{"total_slots":1,"build_info":"synthetic","model_path":"synthetic","default_generation_settings":{"n_ctx":8192,"params":{}}}'
        function Get-Http($Path,$Token) {
            $content=[pscustomobject]@{}
            $content|Add-Member ScriptMethod ReadAsStringAsync {
                $task=[pscustomobject]@{}
                $task|Add-Member ScriptMethod GetAwaiter {
                    $awaiter=[pscustomobject]@{}; $awaiter|Add-Member ScriptMethod GetResult {return $propsJson};return $awaiter
                };return $task
            }
            $value=[pscustomobject]@{StatusCode=$(if($Path -eq '/props' -or $Token.Length -ge 32){200}else{401});Content=$content}
            $value|Add-Member ScriptMethod Dispose {};return $value
        }
        $attempt='bda2015c0ffbe89ab1a612fb4003b2b12f254871cf32f2e47dbbbe9d45cf0f52'
        $run=Join-Path $temp ('uc001-contract-runs/'+$attempt)
        if($Case -eq 'existing_attempt') {$null=New-Item -ItemType Directory -Path $run}
        $failed=$false
        try {Invoke-LocalExecution 'synthetic-review-only.json'} catch {$failed=$true}
        if($Case -eq 'success') {
            Require (-not $failed) 'Synthetic launcher failed'
            Require ($script:starts -eq 2 -and $script:closed -eq 1) 'Ownership/cleanup path bypassed'
            Require ($script:deadlineFixture.Arms -eq 14 -and $script:deadlineFixture.Disarms -eq 14) 'Actual launcher bypassed a per-request native deadline'
            foreach($id in 1..14){Require (Test-Path (Join-Path $run ('export/accepted-{0:00}.json' -f $id))) 'Missing validation acknowledgment'}
        } elseif($Case -in @('existing_attempt','review_missing')) {
            Require ($failed -and $script:starts -eq 0) 'Existing model attempt was reused/reset'
        } else {
            Require $failed 'Abort/cleanup failure was accepted'
            Require ($script:closed -eq 1) 'Owned job cleanup not invoked on failure'
            $cleanup=Read-ContractJson (Join-Path $run 'cleanup.json')
            Require ($cleanup.owned_job_closed -eq ($Case -ne 'job_close_failure')) 'Owned job close result was changed'
            if($Case -eq 'cleanup_failure'){Require (@($cleanup.owned_exits|Where-Object {-not $_.exit_confirmed}).Count -gt 0) 'Unconfirmed cleanup was hidden'}
        }
    }
    'PASS '+$Case
} finally {if(Test-Path -LiteralPath $temp){Remove-Item -LiteralPath $temp -Recurse -Force}}
