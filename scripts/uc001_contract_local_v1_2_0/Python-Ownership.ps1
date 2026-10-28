function Initialize-PythonOwnership {
    if(-not ('ContractProcesses' -as [type])){Initialize-ContractProcessSupport}
    if(-not ('ContractPython' -as [type])){Add-Type -Path (Join-Path $PSScriptRoot 'PythonOwnership.cs')}
}
function Start-OwnedPython($Job, [string]$Arguments, [string]$Root) {
    return [ContractPython]::Start($Job,'C:\ResolenaExperiments\uc001-validator-env\Scripts\python.exe',$Arguments,
        (Join-Path $Root 'python.stdout.log'),(Join-Path $Root 'python.stderr.log'))
}
function Get-OwnedPythonProof($Launch,$Job,[int]$SupervisorId,[int]$ServerId=0) {
    return $Launch.Bind($Job,$SupervisorId,$ServerId)
}
function Complete-OwnedPythonCleanup($Client,$Job,$Server,$Launch,[string]$Root) {
    $failed=$false
    $redirectorIdentity=$null
    if($null -ne $Launch){$redirectorIdentity=$Launch.RedirectorIdentity}
    try {Complete-ContractCleanup $Client $Job $Server $Launch $Root} catch {$failed=$true}
    $path=Join-Path $Root 'cleanup.json'
    if(Test-Path -LiteralPath $path) {$cleanup=Read-ContractJson $path}
    else {$cleanup=[pscustomobject]@{owned_job_closed=$false;owned_exits=@();errors=@('cleanup/receipt_unavailable')}}
    $errors=@();if($failed -or $cleanup.errors.Count){$errors+=@('cleanup/base_cleanup_failed')}
    if($null -ne $redirectorIdentity) {
        foreach($entry in $cleanup.owned_exits) {
            if($entry.pid -eq $redirectorIdentity.pid) {
                $entry|Add-Member NoteProperty role 'redirector'
                $entry|Add-Member NoteProperty created $redirectorIdentity.created
            }
        }
    }
    if($null -ne $Launch) {
        $ended=$false;$identity=$null
        if($null -ne $Launch.LastProof){$identity=$Launch.LastProof.interpreter}
        if($null -ne $Launch.Interpreter -and $null -ne $identity) {
            try {$ended=$Launch.Interpreter.WaitForExit(5000)} catch {$errors+=@('cleanup/interpreter_wait_failed')}
            finally {try {$Launch.Interpreter.Dispose()} catch {$errors+=@('cleanup/interpreter_dispose_failed')}}
        }
        $cleanup.owned_exits=@($cleanup.owned_exits)+@(@{role='interpreter';pid=$(if($null -ne $identity){$identity.pid}else{$null});created=$(if($null -ne $identity){$identity.created}else{$null});exit_confirmed=$ended})
        if(-not $ended){$errors+=@('cleanup/interpreter_exit_unconfirmed')}
    }
    $cleanup.errors=@($errors)
    [IO.File]::WriteAllText($path,($cleanup|ConvertTo-Json -Depth 8))
    if(-not $cleanup.owned_job_closed -or $cleanup.errors.Count -or @($cleanup.owned_exits|Where-Object {-not $_.exit_confirmed}).Count){throw 'cleanup/exit_unconfirmed'}
}
