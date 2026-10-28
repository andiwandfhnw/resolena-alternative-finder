[CmdletBinding()]
param([switch]$Execute, [string]$Review)

function Get-LocalElapsed($Clock) { return $Clock.Elapsed.TotalMilliseconds }
function Assert-LocalDeadline($Clock) {
    if ((Get-LocalElapsed $Clock) -ge 90000) { throw 'Absolute 90-second supervised request deadline expired.' }
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
        $state=Read-LocalProgress $RunRoot
        $Worker.Refresh()
        if ($Worker.HasExited -and $Phase -eq 'complete') {$state=Read-LocalProgress $RunRoot}
        if ($Worker.HasExited -and -not ($Phase -eq 'complete' -and $null -ne $state -and $state.phase -eq 'complete' -and $state.case -eq 14)) { throw 'Owned capture worker exited before acknowledgment.' }
        if (-not $Worker.HasExited) {
            $current=Get-ContractProcessIdentity $Worker
            if ($current.Id -ne $Identity.Id -or $current.Started.Ticks -ne $Identity.Started.Ticks) { throw 'Owned capture worker PID/creation time changed.' }
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
function Invoke-LocalPythonPreflight([string]$ReviewPath) {
    & 'C:\ResolenaExperiments\uc001-validator-env\Scripts\python.exe' -I -X utf8 -B (Join-Path $PSScriptRoot 'capture.py') --preflight --review $ReviewPath
    if ($LASTEXITCODE -ne 0) { throw 'Local freeze/environment/owner technical-decision gate failed before startup.' }
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
function Invoke-LocalExecution([string]$ReviewPath) {
    Assert-ContractWindows
    Assert-ContractBundle
    $totalStart=[DateTime]::UtcNow
    Invoke-LocalPythonPreflight $ReviewPath
    $parent=Join-Path (Split-Path $PSScriptRoot -Parent) 'uc001_execution_v1_3_0'
    $config=Read-ContractJson (Join-Path $parent 'config.json')
    Get-ContractAssets $config
    $adapter=Get-ContractAdapter
    if (@(Get-CimInstance Win32_Process -Filter "Name='llama-server.exe'").Count -gt 0) { throw 'Existing model server; do not duplicate or stop it.' }
    if (@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object {$_.LocalPort -eq 49187}).Count -gt 0) { throw 'Required local port occupied.' }
    $freeze=Read-ContractJson (Join-Path $PSScriptRoot 'freeze.json')
    $runRoot=Join-Path (Split-Path $config.reuse_root -Parent) ('uc001-contract-runs\'+$freeze.attempt_identity)
    if (Test-Path -LiteralPath $runRoot) { throw 'Original attempt already reserved; no startup or ledger reset.' }
    Assert-ContractResources (Get-ContractResources $adapter $runRoot) $config.limits $true
    if (([DateTime]::UtcNow-$totalStart).TotalSeconds -ge 2400) { throw 'Total budget expired before startup.' }
    $null=New-Item -ItemType Directory -Path $runRoot
    Set-LocalPrivateDirectory $runRoot
    $null=New-Item -ItemType Directory -Path (Join-Path $runRoot 'export')
    $job=$null; $client=$null; $server=$null; $worker=$null; $key=$null; $completed=$false; $deadlineGuard=$null
    try {
        Initialize-ContractProcessSupport
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
        $modelStart=[DateTime]::UtcNow
        $server=Start-ContractProcess $job (Join-Path $config.reuse_root 'runtime\llama-server.exe') $arguments (Join-Path $runRoot 'server.stdout.log') (Join-Path $runRoot 'server.stderr.log') $key
        $server.StandardInput.Close()
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
        $receipt=@{freeze_sha256=(Get-ContractHash (Join-Path $PSScriptRoot 'freeze.json'));attempt_identity=$freeze.attempt_identity
            started_utc=$modelStart.ToString('o');total_started_utc=$totalStart.ToString('o');receipt_epoch=([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())
            supervisor_pid=$PID;authentication_verified=$true;owned_pid=$server.Id;resource_sample=$sample;startup_log=$selectedLog
            props=@{total_slots=$props.total_slots;build_info=$props.build_info;model_path=$props.model_path;default_generation_settings=$props.default_generation_settings}}
        $receiptPath=Join-Path $runRoot 'windows-receipt.json'
        [IO.File]::WriteAllText($receiptPath,($receipt|ConvertTo-Json -Depth 30))
        $workerArgs=@('-I','-X','utf8','-B',(Join-Path $PSScriptRoot 'capture.py'),'--supervised-capture','--review',$ReviewPath,'--receipt',$receiptPath,'--run-root',$runRoot)
        $worker=Start-ContractProcess $job 'C:\ResolenaExperiments\uc001-validator-env\Scripts\python.exe' (($workerArgs|ForEach-Object {Quoted $_})-join ' ') (Join-Path $runRoot 'capture.stdout.log') (Join-Path $runRoot 'capture.stderr.log') $null
        $identity=Get-ContractProcessIdentity $worker
        $worker.StandardInput.WriteLine($key); $worker.StandardInput.Flush()
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
        $_.Exception.GetType().FullName|Set-Content -LiteralPath (Join-Path $runRoot 'stopped.txt')
        throw 'Local capture stopped; retain private evidence. No retry or fallback.'
    } finally {
        try {Complete-ContractCleanup $client $job $server $worker $runRoot}
        finally {
            $key=$null
            if (Test-Path -LiteralPath (Join-Path $runRoot 'cleanup.json')) {Copy-Item -LiteralPath (Join-Path $runRoot 'cleanup.json') -Destination (Join-Path $runRoot 'export\cleanup.json')}
            if (Test-Path -LiteralPath (Join-Path $runRoot 'attempts.jsonl')) {Copy-Item -LiteralPath (Join-Path $runRoot 'attempts.jsonl') -Destination (Join-Path $runRoot 'export\attempts.jsonl') -Force}
            Write-LocalSupervision $runRoot $completed
        }
    }
}

if ($MyInvocation.InvocationName -ne '.') {
    if (-not $Execute) {throw 'Preparation only; separate owner authorization is required for model startup/inference.'}
    $parent=Join-Path (Split-Path $PSScriptRoot -Parent) 'uc001_execution_v1_3_0'
    . (Join-Path $parent 'Common.ps1')
    . (Join-Path $parent 'Run-Windows.ps1') -Codespace local
    Invoke-LocalExecution $Review
}
