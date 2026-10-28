function Initialize-PythonOwnership {
    if(-not ('ContractProcesses' -as [type])){Initialize-ContractProcessSupport}
    if(-not ('ContractPython' -as [type])){Add-Type -Path (Join-Path $PSScriptRoot 'PythonOwnership.cs')}
}
function Start-OwnedPython($Job, [string]$Arguments, [string]$Root) {
    $private=Join-Path $Root 'private'
    if(-not (Test-Path -LiteralPath $private)){$null=New-Item -ItemType Directory -Path $private}
    return [ContractPython]::Start($Job,'C:\ResolenaExperiments\uc001-validator-env\Scripts\python.exe',$Arguments,
        (Join-Path $private 'python.stdout.log'),(Join-Path $private 'python.stderr.log'))
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
        $identity=$Launch.InterpreterIdentity
        if($null -ne $Launch.Interpreter -and $null -ne $identity) {
            try {$ended=$Launch.Interpreter.WaitForExit(5000)} catch {$errors+=@('cleanup/interpreter_wait_failed')}
            finally {try {$Launch.Interpreter.Dispose()} catch {$errors+=@('cleanup/interpreter_dispose_failed')}}
        }
        $identified=($null -ne $identity -and $null -ne $Launch.Interpreter)
        $cleanup.owned_exits=@($cleanup.owned_exits)+@(@{role='interpreter';pid=$(if($null -ne $identity){$identity.pid}else{$null});created=$(if($null -ne $identity){$identity.created}else{$null});exit_confirmed=$ended
            identity_state=$(if($identified){'identified'}else{'not_identified'});exit_confirmation=$(if($ended){'confirmed'}elseif($identified){'unconfirmed'}else{'unavailable'})})
        if(-not $identified){$errors+=@('cleanup/interpreter_not_identified')}
        elseif(-not $ended){$errors+=@('cleanup/interpreter_exit_unconfirmed')}
        foreach($helper in @($Launch.ConsoleHelpers)) {
            $identity=$helper.identity;$process=$helper.process;$ended=$false
            $identified=($null -ne $identity -and $null -ne $process)
            if($identified) {
                try {$ended=$process.WaitForExit(5000)} catch {$errors+=@('cleanup/console_helper_wait_failed')}
                finally {try {$process.Dispose()} catch {$errors+=@('cleanup/console_helper_dispose_failed')}}
            }
            $cleanup.owned_exits=@($cleanup.owned_exits)+@(@{role='console_helper';pid=$(if($null -ne $identity){$identity.pid}else{$null});created=$(if($null -ne $identity){$identity.created}else{$null});exit_confirmed=$ended
                identity_state=$(if($identified){'identified'}else{'not_identified'});exit_confirmation=$(if($ended){'confirmed'}elseif($identified){'unconfirmed'}else{'unavailable'})})
            if(-not $identified){$errors+=@('cleanup/console_helper_not_identified')}
            elseif(-not $ended){$errors+=@('cleanup/console_helper_exit_unconfirmed')}
        }
        $accounted=@($cleanup.owned_exits|Where-Object {$null -ne $_.pid}|ForEach-Object {$_.pid})
        $unknown=$null
        if($null -ne $Launch.LastJobMembers){$unknown=@($Launch.LastJobMembers|Where-Object {$_ -notin $accounted})}
        $cleanup|Add-Member NoteProperty unidentified_job_pids $unknown
        if($null -ne $unknown -and @($unknown).Count){$errors+=@('cleanup/member_identity_unavailable')}
    }
    $cleanup.errors=@($errors)
    [IO.File]::WriteAllText($path,($cleanup|ConvertTo-Json -Depth 8))
    if(-not $cleanup.owned_job_closed -or $cleanup.errors.Count -or @($cleanup.owned_exits|Where-Object {-not $_.exit_confirmed}).Count){throw 'cleanup/exit_unconfirmed'}
}
