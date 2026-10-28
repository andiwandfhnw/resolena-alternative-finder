from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path('scripts/uc001_transport_preparation')
VARIANT = ROOT / 'Test-TransportLogging.ps1'


def test_logging_variant_reuses_original_and_defaults_to_no_execution():
    assert VARIANT.exists(), 'Separate logging-only variant absent (RED)'
    text = VARIANT.read_text()
    assert ". (Join-Path $PSScriptRoot 'Test-Transport.ps1')" in text
    assert 'function Invoke-TransportProbe' not in text
    assert 'ProxyCommand=none' not in text and 'ProxyJump=none' not in text
    assert "'-4'" not in text and 'GH_DEBUG=api' not in text
    result = subprocess.run(
        ['pwsh', '-NoProfile', '-NonInteractive', '-File', str(VARIANT)],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode != 0 and 'logging-only approval' in result.stderr
    assert not (ROOT / 'results').exists()


@pytest.mark.skipif(shutil.which('pwsh') is None, reason='PowerShell parser absent')
@pytest.mark.parametrize('case', [
    'success', 'remote_failed', 'bridge_wildcard', 'endpoint_foreign',
    'job_close_failed', 'exit_unconfirmed', 'privacy_failed', 'native_start_failed',
])
def test_logging_flow_arguments_privacy_environment_and_owned_cleanup(case):
    assert VARIANT.exists(), 'Separate logging-only variant absent (RED)'
    fixture = (ROOT / 'Test-Offline.ps1').read_text()
    fixture = fixture.replace(
        ". (Join-Path $PSScriptRoot 'Test-Transport.ps1')",
        ". (Join-Path $PSScriptRoot 'Test-TransportLogging.ps1')",
    ).replace('function Start-ContractProcess {', '''
function Set-TransportLogPrivacy($Root) {
    if($Case -eq 'privacy_failed'){throw 'Synthetic ACL failure'}
    Require ($script:started -eq 0) 'Privacy applied after startup'
    $script:privateRoot=$Root
}
function Start-TransportLoggingNativeProcess {
    param($Job,$Executable,$Arguments,$Stdout,$Stderr,$Key)
    Require ($script:privateRoot -eq (Split-Path $Stdout -Parent)) 'Raw log path not protected'
    Require ($null -eq $Key) 'Ephemeral key passed as process environment/argument'
    if($Executable.EndsWith('gh.exe')) {
        Require ($env:GH_DEBUG -eq '1') 'Nonverbose gh debug absent'
        $argv=@([regex]::Matches($Arguments,'"([^\"]*)"')|ForEach-Object {$_.Groups[1].Value})
        $expected=@('codespace','ssh','--codespace','offline','--server-port','49189','--','-vvv','-E',
            (Join-Path $script:privateRoot 'ssh-debug.log'),'-T','-o','BatchMode=yes','-o','ExitOnForwardFailure=yes',
            '-o','ServerAliveInterval=5','-o','ServerAliveCountMax=2','-o','ConnectTimeout=15',
            '-R','127.0.0.1:49188:127.0.0.1:49187',
            'cd /workspaces/resolena-alternative-finder && timeout --signal=TERM --kill-after=5s 35s env PYTHONPATH=src:. .venv/bin/python scripts/uc001_transport_preparation/probe_forward.py')
        Require (($argv|ConvertTo-Json -Compress) -eq ($expected|ConvertTo-Json -Compress)) 'Nonlogging arguments changed'
        if($Case -eq 'native_start_failed'){$script:started++;throw 'Synthetic owned startup failure'}
        $ssh="debug1: Connecting to localhost [::1] port 49189.`ndebug1: Connection established.`nbanner exchange: Connection to UNKNOWN port -1: Connection refused`n"
        [IO.File]::WriteAllText((Join-Path $script:privateRoot 'ssh-debug.log'),$ssh)
        [IO.File]::WriteAllText($Stderr,"tunnel closed: error connecting to forwarded port: synthetic`nhttps://broker.invalid/private?token=SYNTHETIC_SECRET`nAuthorization: Bearer SYNTHETIC_SECRET`n-----BEGIN OPENSSH PRIVATE KEY-----`nSYNTHETIC_SECRET")
    }
''')
    fixture = fixture.replace(
        "$result=Invoke-TransportProbe $bundle 'offline'",
        "$env:GH_DEBUG='api'; $result=Invoke-TransportLoggingProbe $bundle 'offline'; Require ($env:GH_DEBUG -eq 'api') 'Debug environment not restored'",
    ).replace(
        "$expected=$(if($Case -eq 'endpoint_foreign'){1}else{2})",
        "$expected=$(if($Case -eq 'privacy_failed'){0}elseif($Case -in @('endpoint_foreign','native_start_failed')){1}else{2})",
    )
    fixture = fixture.replace(
        "} finally {if(Test-Path -LiteralPath $temp)",
        '''
    $summaryText=[IO.File]::ReadAllText((Join-Path $result.result_directory 'sanitized-summary.json'))
    foreach($sensitive in @('SYNTHETIC_SECRET','broker.invalid','Authorization','PRIVATE KEY',$result.result_directory)) {
        Require (-not $summaryText.Contains($sensitive)) 'Sensitive raw content copied to shareable summary'
    }
    $summary=$summaryText|ConvertFrom-Json
    Require ($summary.root_cause -eq 'not_established') 'Log markers treated as root-cause proof'
    Require (-not $summary.model_readiness_verified) 'Model readiness invented'
    Require ($summary.overall_limit_ms -eq 60000) 'Overall limit changed'
    if($Case -notin @('endpoint_foreign','privacy_failed','native_start_failed')) {
        Require ($summary.logs.ssh.state -eq 'present') 'SSH log missing'
        Require $summary.ssh_connection_established_marker 'Connection marker lost'
        Require $summary.banner_refusal_marker 'Banner marker lost'
        Require $summary.forward_error_marker 'Forward error marker lost'
    } else {Require ($summary.logs.ssh.state -eq 'missing') 'Missing SSH evidence concealed'}
} finally {if(Test-Path -LiteralPath $temp)''',
    )
    # Reuse the unchanged original fixture; only these named dependency hooks differ.
    fixture = fixture.replace("$PSScriptRoot", "'" + str(ROOT.resolve()).replace("'", "''") + "'")
    command = "$Case='" + case + "'; & {\n" + fixture.replace(
        'param([Parameter(Mandatory=$true)][string]$Case)', '', 1,
    ) + '\n}'
    result = subprocess.run(
        ['pwsh', '-NoProfile', '-NonInteractive', '-Command', command],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert f'PASS {case}' in result.stdout


@pytest.mark.skipif(shutil.which('pwsh') is None, reason='PowerShell parser absent')
@pytest.mark.parametrize('prior', [None, '', 'api'])
def test_gh_debug_scope_restores_absent_empty_or_prior_value(prior):
    assert VARIANT.exists(), 'Separate logging-only variant absent (RED)'
    value = '$null' if prior is None else "'" + prior + "'"
    command = rf'''
    . '{VARIANT.resolve()}'
    function Set-TransportLogPrivacy {{}}
    function Start-TransportLoggingNativeProcess {{
        if($env:GH_DEBUG -ne '1'){{throw 'Wrong debug mode'}}
        throw 'Synthetic native failure'
    }}
    [Environment]::SetEnvironmentVariable('GH_DEBUG',{value},'Process')
    $before=[Environment]::GetEnvironmentVariable('GH_DEBUG','Process')
    $script:TransportLoggingRoot=$null
    try {{
        Start-ContractProcess ([IntPtr]42) 'C:\ResolenaExperiments\tools\gh-2.81.0\bin\gh.exe' '"--" "-T"' '/tmp/offline/transport.stdout.log' '/tmp/offline/transport.stderr.log' $null
        throw 'Failure concealed'
    }} catch {{if($_.Exception.Message -ne 'Synthetic native failure'){{throw}}}}
    $after=[Environment]::GetEnvironmentVariable('GH_DEBUG','Process')
    if($before -cne $after){{throw 'Process environment not restored'}}
    '''
    result = subprocess.run(['pwsh', '-NoProfile', '-NonInteractive', '-Command', command], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
