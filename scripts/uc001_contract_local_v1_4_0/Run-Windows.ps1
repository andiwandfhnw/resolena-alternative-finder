[CmdletBinding()]
param([switch]$Execute, [string]$Review, [string]$Approval)

function Read-LocalServerIdentity($Server,$Job){return [ContractPython]::ReadInJob($Server,$Job)}
function Get-LocalElapsed($Clock) { return $Clock.Elapsed.TotalMilliseconds }
function Assert-LocalDeadline($Clock) {
    if ((Get-LocalElapsed $Clock) -ge 90000) { throw 'deadline/request_expired' }
}
function Read-LocalProgress([string]$RunRoot) {
    $path=Join-Path $RunRoot 'progress.json'
    if (-not (Test-Path -LiteralPath $path)) { return $null }
    $stream=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
    try {
        if ($stream.Length -gt 4096) {throw 'Invalid supervisor progress record.'}
        $reader=New-Object IO.StreamReader $stream,([Text.Encoding]::UTF8)
        try {return ($reader.ReadToEnd()|ConvertFrom-Json)} finally {$reader.Dispose()}
    } finally {$stream.Dispose()}
}
function Update-LocalResources {
    if ($monitor.clock.Elapsed.TotalSeconds -ge $monitor.next) {
        Check-Running
        $monitor.next=$monitor.clock.Elapsed.TotalSeconds+$config.limits.sample_seconds
    }
}
function Wait-LocalPhase($Worker, $Identity, [string]$RunRoot, [int]$CaseId, [string]$Phase, $Clock) {
    while ($true) {
        Assert-LocalDeadline $Clock
        Update-LocalResources
        Assert-LocalDeadline $Clock
        if(Test-Path -LiteralPath (Join-Path $RunRoot 'capture-stopped.json')){throw 'worker/check_failed'}
        $state=Read-LocalProgress $RunRoot
        $Worker.Refresh()
        if ($Worker.HasExited -and $Phase -eq 'complete') {$state=Read-LocalProgress $RunRoot}
        if ($Worker.HasExited -and -not ($Phase -eq 'complete' -and $null -ne $state -and $state.phase -eq 'complete' -and $state.case -eq 14)) { throw 'Owned capture worker exited before acknowledgment.' }
        if (-not $Worker.HasExited) {
            $current=Get-ContractProcessIdentity $Worker
            if ($current.Id -ne $Identity.Id -or $current.Started.Ticks -ne $Identity.Started.Ticks) { throw 'Owned capture worker PID/creation time changed.' }
            $proof=Get-OwnedPythonProof $Worker $job $PID $server $serverNativeIdentity $runtimeExecutable
            if($null -eq $proof){throw 'ownership/interpreter_unavailable'}
        }
        if ($null -ne $state) {
            $number=Get-AssociationInteger $state.case 'Progress case'
            $expected=($number -eq $CaseId -and $state.phase -eq $Phase)
            $waiting=($Phase -eq 'ready' -and $number -eq ($CaseId-1) -and $state.phase -eq 'validated') -or
                ($Phase -eq 'validated' -and $number -eq $CaseId -and $state.phase -in @('ready','running')) -or
                ($Phase -eq 'complete' -and $number -eq 14 -and $state.phase -eq 'validated')
            if (-not $expected -and -not $waiting) { throw 'Unexpected request/phase; no generation acknowledgment.' }
            if ($expected) { Assert-LocalDeadline $Clock; return (Get-LocalElapsed $Clock) }
        }
        Assert-LocalDeadline $Clock
        Start-Sleep -Milliseconds 20
    }
}
function Set-LocalPrivateDirectory([string]$Path) {
    $acl=New-Object Security.AccessControl.DirectorySecurity
    $acl.SetAccessRuleProtection($true,$false)
    foreach ($sid in @([Security.Principal.WindowsIdentity]::GetCurrent().User, (New-Object Security.Principal.SecurityIdentifier 'S-1-5-18'))) {
        $rule=New-Object Security.AccessControl.FileSystemAccessRule $sid,'FullControl','ContainerInherit,ObjectInherit','None','Allow'
        $acl.AddAccessRule($rule)
    }
    [IO.Directory]::SetAccessControl($Path,$acl)
}
function Invoke-LocalPythonPreflight([string]$ReviewPath,[string]$ApprovalPath) {
    & 'C:\ResolenaExperiments\uc001-validator-env\Scripts\python.exe' -I -X utf8 -B (Join-Path $PSScriptRoot 'capture.py') --preflight --review $ReviewPath --approval $ApprovalPath
    if ($LASTEXITCODE -ne 0) { throw 'startup/approval_or_preflight_failed' }
}
function New-LocalDeadline($Job) {
    Add-Type -Path (Join-Path $PSScriptRoot 'DeadlineGuard.cs')
    return [Uc001Local.DeadlineGuard]::new($Job, [ContractProcesses].GetMethod('CloseHandle'))
}
function Write-LocalSupervision([string]$RunRoot, [bool]$Completed) {
    $records=@()
    foreach ($id in 1..14) {
        $directory=Join-Path $RunRoot ('private\cases\{0:00}' -f $id)
        $bodies=@()
        if (Test-Path -LiteralPath $directory) {
            foreach ($file in @(Get-ChildItem -LiteralPath $directory -Filter '*.bin' -Recurse -File)) {
                $bodies+=@{exchange=$file.Directory.Name;kind=$file.Name;private_bytes=$file.Length}
            }
        }
        $records+=@{case=$id;accepted_before_deadline=(Test-Path -LiteralPath (Join-Path $RunRoot ('export\accepted-{0:00}.json' -f $id)));private_bodies=$bodies}
    }
    $status=@{completed=$Completed;cases=$records;live_api_real_adapter_verified=$false;deferred_live_cases=@(1,5,10)
        execution_purpose='technical_feasibility_only';semantic_review='pending';expected_meanings_approved=$false
        interpreter_suitability_verified=$false;multilingual_acceptance_verified=$false
        incomplete='Unfinished raw bodies remain private; do not manually copy private files or logs to Codespace.'}
    [IO.File]::WriteAllText((Join-Path $RunRoot 'export\supervision.json'),($status|ConvertTo-Json -Depth 8))
}
function Get-HarnessFailure($ErrorRecord,[string]$Stage) {
    $failure=@{stage=$Stage;reason='unexpected_failure'}
    $known=@(
        'bundle/source_mismatch','worker/exited_without_result','worker/check_failed',
        'startup/approval_or_preflight_failed','deadline/request_expired',
        'deadline/setup_expired','deadline/ownership_expired','deadline/worker_expired','deadline/overall_expired',
        'cleanup/unowned_job','cleanup/exit_unconfirmed',
        'ownership/process_exited','ownership/process_times_query_failed','ownership/process_creation_invalid',
        'ownership/process_basic_query_failed','ownership/process_image_query_failed','ownership/process_pid_mismatch',
        'ownership/job_query_failed','ownership/job_members_ambiguous','ownership/job_pid_invalid',
        'ownership/job_membership_query_failed','ownership/job_membership_failed','ownership/redirector_identity_changed',
        'ownership/unexpected_owned_process','ownership/interpreter_ambiguous','ownership/interpreter_identity_changed',
        'ownership/candidate_identity_changed','ownership/console_helper_ambiguous',
        'ownership/console_helper_constraints','ownership/console_helper_identity_changed',
        'ownership/supervisor_identity_mismatch','ownership/redirector_path_mismatch','ownership/stdin_pipe_failed',
        'ownership/stdio_handles_failed','ownership/handle_list_failed','ownership/create_suspended_failed',
        'ownership/job_assignment_failed','ownership/resume_failed','ownership/suspended_cleanup_unconfirmed',
        'ownership/identity_changed','ownership/interpreter_unavailable','ownership/server_identity_mismatch','ownership/server_receipt_mismatch')
    $cause=$ErrorRecord.Exception
    while($null -ne $cause) {
        if($failure.reason -eq 'unexpected_failure' -and $cause.Message -cin $known){$parts=$cause.Message.Split('/');$failure.stage=$parts[0];$failure.reason=$parts[1]}
        if(-not $failure.ContainsKey('native_status')) {
            if($cause -is [ComponentModel.Win32Exception]){$failure.native_status=@{domain='win32';code=$cause.NativeErrorCode}}
            elseif($cause.Data.Contains('ntstatus') -and $cause.Data['ntstatus'] -is [int]){$failure.native_status=@{domain='ntstatus';code=$cause.Data['ntstatus']}}
        }
        $cause=$cause.InnerException
    }
    return $failure
}
function Write-HarnessPrivateFailure([string]$Root,[string]$Phase,$ErrorRecord) {
    try {
        $private=Join-Path $Root 'private'
        if(-not (Test-Path -LiteralPath $private)){$null=New-Item -ItemType Directory -Path $private}
        $text=$ErrorRecord.Exception.ToString()+[Environment]::NewLine+$ErrorRecord.ScriptStackTrace
        if($text.Length -gt 4096){$text=$text.Substring(0,4096)}
        [IO.File]::WriteAllText((Join-Path $private ($Phase+'-error.txt')),$text)
        return $true
    } catch {return $false}
}
function Invoke-LocalExecution([string]$ReviewPath,[string]$ApprovalPath) {
    Assert-ContractWindows
    Assert-ContractBundle
    $totalStart=[DateTime]::UtcNow
    Invoke-LocalPythonPreflight $ReviewPath $ApprovalPath
    $parent=Join-Path (Split-Path $PSScriptRoot -Parent) 'uc001_execution_v1_3_0'
    $config=Read-ContractJson (Join-Path $parent 'config.json')
    $runtimeExecutable=Join-Path $config.reuse_root 'runtime\llama-server.exe'
    Get-ContractAssets $config
    $adapter=Get-ContractAdapter
    if (@(Get-CimInstance Win32_Process -Filter "Name='llama-server.exe'").Count -gt 0) { throw 'Existing model server; do not duplicate or stop it.' }
    if (@(Get-NetTCPConnection -State Listen | Where-Object {$_.LocalPort -eq 49187}).Count -gt 0) { throw 'Required local port occupied.' }
    $freeze=Read-ContractJson (Join-Path $PSScriptRoot 'freeze.json')
    $runRoot=Join-Path (Split-Path $config.reuse_root -Parent) ('uc001-contract-runs\'+$freeze.attempt_identity)
    if (Test-Path -LiteralPath $runRoot) { throw 'Additional attempt already reserved; no retry or ledger reset.' }
    Assert-ContractResources (Get-ContractResources $adapter $runRoot) $config.limits $true
    if (([DateTime]::UtcNow-$totalStart).TotalSeconds -ge 2400) { throw 'Total budget expired before startup.' }
    $null=New-Item -ItemType Directory -Path $runRoot
    Set-LocalPrivateDirectory $runRoot
    $null=New-Item -ItemType Directory -Path (Join-Path $runRoot 'export')
    $job=$null; $client=$null; $server=$null; $serverNativeIdentity=$null; $worker=$null; $key=$null; $completed=$false; $deadlineGuard=$null; $primary=$null; $cleanupFailures=@(); $deadlineFailures=@(); $stage='native_setup'; $cleanupPassed=$false
    [IO.File]::WriteAllText((Join-Path $runRoot 'reservation.json'),(@{attempt_identity=$freeze.attempt_identity;original_attempt_identity=$freeze.original_attempt_identity;previous_attempt_identity=$freeze.previous_attempt_identity;reserved_utc=[DateTime]::UtcNow.ToString('o');purpose='technical_feasibility_only';allowance_reset=$false}|ConvertTo-Json))
    try {
        Initialize-PythonOwnership
        $job=New-ContractJob
        $deadlineGuard=New-LocalDeadline $job
        function Close-ContractJob($Job) {
            if ($null -eq $deadlineGuard) {return [ContractProcesses]::CloseHandle($Job)}
            if ($Job -ne $deadlineGuard.Job) {throw 'Refusing to close an unowned job'}
            return $deadlineGuard.Close()
        }
        $random=New-Object byte[] 32
        $rng=[Security.Cryptography.RandomNumberGenerator]::Create(); $rng.GetBytes($random); $rng.Dispose()
        $key=[Convert]::ToBase64String($random)
        $argsList = @('--model',(Join-Path $config.reuse_root 'Qwen3-8B-Q8_0.gguf'),'--alias','uc001-qwen3-8b',
            '--host','127.0.0.1','--port','49187','--offline','--no-webui','--no-warmup','--fit','off',
            '--device','Vulkan0','--n-gpu-layers','37','--threads','2','--threads-batch','2','--parallel','1',
            '--ctx-size','8192','--predict','3072','--batch-size','64','--ubatch-size','64',
            '--cache-type-k','f16','--cache-type-v','f16','--cache-ram','0','--temp','0.7','--top-p','0.8','--top-k','20','--min-p','0','--seed','42',
            '--jinja','--chat-template-kwargs','{"enable_thinking":false}','--log-verbosity','4')
        $arguments=($argsList|ForEach-Object {if($_ -eq '{"enable_thinking":false}'){'"{\"enable_thinking\":false}"'}else{Quoted $_}})-join ' '
        $stage='startup';$modelStart=[DateTime]::UtcNow
        $launchRecord=@{attempt_identity=$freeze.attempt_identity;original_attempt_identity=$freeze.original_attempt_identity;previous_attempt_identity=$freeze.previous_attempt_identity;startup_attempt=1;utc=$modelStart.ToString('o');executable=$runtimeExecutable;launch_args=$argsList;command_line=$arguments}
        $launchPath=Join-Path $runRoot 'startup-attempt.json'
        if(Test-Path -LiteralPath $launchPath){throw 'startup/already_attempted'}
        [IO.File]::WriteAllText($launchPath,($launchRecord|ConvertTo-Json -Depth 8))
        $server=Start-ContractProcess $job $runtimeExecutable $arguments (Join-Path $runRoot 'server.stdout.log') (Join-Path $runRoot 'server.stderr.log') $key
        $server.StandardInput.Close()
        $serverIdentity=Get-ContractProcessIdentity $server
        $serverNativeIdentity=Read-LocalServerIdentity $server $job
        if($serverNativeIdentity.pid -ne $server.Id -or $serverNativeIdentity.parent_pid -ne $PID -or
            -not [string]::Equals($serverNativeIdentity.image,$runtimeExecutable,[StringComparison]::OrdinalIgnoreCase)){throw 'ownership/server_identity_mismatch'}
        [IO.File]::WriteAllText((Join-Path $runRoot 'startup-started.json'),(@{attempt_identity=$freeze.attempt_identity;pid=$serverIdentity.Id;started_utc=$serverIdentity.Started.ToString('o');native_identity=$serverNativeIdentity}|ConvertTo-Json))
        $stage='readiness'
        $monitor=@{clock=[Diagnostics.Stopwatch]::StartNew();next=0}
        $client=New-ContractHttpClient
        $props=$null
        while ($null -eq $props) {
            Check-Running
            if (([DateTime]::UtcNow-$modelStart).TotalSeconds -ge 90) { throw 'Readiness deadline expired; no restart.' }
            try {$response=Get-Http '/props' $key} catch [Net.Http.HttpRequestException] {Start-Sleep -Milliseconds 500;continue}
            try {
                if ([int]$response.StatusCode -eq 200) {$props=$response.Content.ReadAsStringAsync().GetAwaiter().GetResult()|ConvertFrom-Json}
                elseif ([int]$response.StatusCode -ne 503) {throw 'Readiness/authentication failed.'}
            } finally {$response.Dispose()}
            if ($null -eq $props) {Start-Sleep -Milliseconds 500}
        }
        foreach ($token in @('','deliberately-invalid',$key)) {
            $response=Get-Http '/v1/models' $token
            try {if ([int]$response.StatusCode -ne $(if($token -eq $key){200}else{401})) {throw 'Protected authentication check failed.'}} finally {$response.Dispose()}
        }
        $listeners=@(Get-NetTCPConnection -State Listen|Where-Object {$_.OwningProcess -eq $server.Id})
        if ($listeners.Count -ne 1 -or $listeners[0].LocalAddress -ne '127.0.0.1' -or $listeners[0].LocalPort -ne 49187) {throw 'Owned model listener must be loopback-only.'}
        $sample=Get-ContractResources $adapter $runRoot $server
        if ($sample.owned_gpu -le 0) {throw 'Positive measured owned GPU allocation is missing.'}
        $log=[IO.File]::ReadAllText((Join-Path $runRoot 'server.stderr.log'))
        $selectedLog=($log -split "`n"|Where-Object {$_ -match 'build 11429|using device Vulkan0|offloaded \d+/\d+ layers|n_threads =|n_ctx_seq\s*=|n_batch\s*=|n_ubatch\s*=|K \(f16\):'})-join "`n"
        $receipt=@{freeze_sha256=(Get-ContractHash (Join-Path $PSScriptRoot 'freeze.json'));attempt_identity=$freeze.attempt_identity;original_attempt_identity=$freeze.original_attempt_identity;previous_attempt_identity=$freeze.previous_attempt_identity
            started_utc=$modelStart.ToString('o');total_started_utc=$totalStart.ToString('o');receipt_epoch=([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())
            supervisor_pid=$PID;authentication_verified=$true;owned_pid=$server.Id;owned_created=$serverNativeIdentity.created;resource_sample=$sample;startup_log=$selectedLog;launch_args=$argsList
            props=@{total_slots=$props.total_slots;build_info=$props.build_info;model_path=$props.model_path;default_generation_settings=$props.default_generation_settings}}
        $receiptPath=Join-Path $runRoot 'windows-receipt.json'
        [IO.File]::WriteAllText($receiptPath,($receipt|ConvertTo-Json -Depth 30))
        $workerArgs=@('-I','-X','utf8','-B',(Join-Path $PSScriptRoot 'capture.py'),'--supervised-capture','--review',$ReviewPath,'--receipt',$receiptPath,'--run-root',$runRoot,'--approval',$ApprovalPath)
        $stage='ownership'
        $worker=Start-OwnedPython $job (($workerArgs|ForEach-Object {Quoted $_})-join ' ') $runRoot
        $ownershipClock=[Diagnostics.Stopwatch]::StartNew();$proof=$null
        while($null -eq $proof) {
            Assert-LocalDeadline $ownershipClock;Check-Running
            $proof=Get-OwnedPythonProof $worker $job $PID $server $serverNativeIdentity $runtimeExecutable
            if($null -eq $proof){Start-Sleep -Milliseconds 20}
        }
        $receipt.python_ownership=$proof
        [IO.File]::WriteAllText($receiptPath,($receipt|ConvertTo-Json -Depth 30))
        $identity=Get-ContractProcessIdentity $worker
        $worker.StandardInput.WriteLine($key); $worker.StandardInput.Flush()
        $stage='capture'
        foreach ($id in 1..14) {
            $null=Wait-LocalPhase $worker $identity $runRoot $id 'ready' ([Diagnostics.Stopwatch]::StartNew())
            $clock=[Diagnostics.Stopwatch]::StartNew()
            $deadlineGuard.Arm(90000)
            $worker.StandardInput.WriteLine(('begin '+$id)); $worker.StandardInput.Flush()
            $elapsed=Wait-LocalPhase $worker $identity $runRoot $id 'validated' $clock
            Assert-LocalDeadline $clock
            $deadlineGuard.Disarm()
            $accepted=@{case=$id;elapsed_ms=$elapsed;owned_pid=$identity.Id;owned_started_utc=$identity.Started.ToString('o')}
            [IO.File]::WriteAllText((Join-Path $runRoot ('export\accepted-{0:00}.json' -f $id)),($accepted|ConvertTo-Json))
            Assert-LocalDeadline $clock
            $worker.StandardInput.WriteLine(('advance '+$id)); $worker.StandardInput.Flush()
        }
        $null=Wait-LocalPhase $worker $identity $runRoot 14 'complete' ([Diagnostics.Stopwatch]::StartNew())
        $worker.StandardInput.Close()
        $finishClock=[Diagnostics.Stopwatch]::StartNew()
        while (-not $worker.HasExited) {Assert-LocalDeadline $finishClock;Update-LocalResources;Start-Sleep -Milliseconds 20;$worker.Refresh()}
        if ($worker.ExitCode -ne 0) {throw 'Capture worker failed; no retry.'}
        $completed=$true
    } catch {
        $primary=Get-HarnessFailure $_ $stage
        if($primary.stage -eq 'deadline'){$deadlineFailures+=@($primary)}
        $null=Write-HarnessPrivateFailure $runRoot 'primary' $_
    } finally {
        try {Complete-OwnedPythonCleanup $client $job $server $worker $runRoot $serverNativeIdentity;$cleanupPassed=$true}
        catch {$cleanupFailures+=@(Get-HarnessFailure $_ 'cleanup');$null=Write-HarnessPrivateFailure $runRoot 'cleanup' $_}
        finally {
            $key=$null
            foreach($name in @('cleanup.json','attempts.jsonl','startup-attempt.json','startup-started.json','reservation.json')) {
                $path=Join-Path $runRoot $name
                if(Test-Path -LiteralPath $path){Copy-Item -LiteralPath $path -Destination (Join-Path $runRoot ('export\'+$name))}
            }
            Write-LocalSupervision $runRoot $completed
            $result=@{attempt_identity=$freeze.attempt_identity;original_attempt_identity=$freeze.original_attempt_identity;previous_attempt_identity=$freeze.previous_attempt_identity
                completed=($completed -and $cleanupPassed -and $null -eq $primary);primary_failure=$primary;cleanup_failures=$cleanupFailures;deadline_failures=$deadlineFailures
                cleanup_confirmed=$cleanupPassed;execution_purpose='technical_feasibility_only';expected_meanings_approved=$false;semantic_review='pending'
                live_api_real_adapter_verified=$false;deferred_live_cases=@(1,5,10)}
            [IO.File]::WriteAllText((Join-Path $runRoot 'export\execution-result.json'),($result|ConvertTo-Json -Depth 10))
        }
    }
    if(-not $result.completed){throw 'execution/stopped'}
}

if ($MyInvocation.InvocationName -ne '.') {
    $ErrorActionPreference='Stop';Set-StrictMode -Version Latest
    if (-not $Execute) {throw 'Prepared proposal only; explicit approval of the additional allowance is required.'}
    $parent=Join-Path (Split-Path $PSScriptRoot -Parent) 'uc001_execution_v1_3_0'
    . (Join-Path $parent 'Common.ps1')
    . (Join-Path $parent 'Run-Windows.ps1') -Codespace local
    . (Join-Path $PSScriptRoot 'Python-Ownership.ps1')
    Invoke-LocalExecution $Review $Approval
}
