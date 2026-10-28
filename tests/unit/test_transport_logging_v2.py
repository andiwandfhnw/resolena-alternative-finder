from hashlib import sha256
from pathlib import Path
import json
import re
import shutil
import subprocess

import pytest


ROOT = Path('scripts/uc001_transport_preparation')
OLD = ROOT / 'Test-TransportLogging.ps1'
CORRECTED = ROOT / 'Test-TransportLoggingV2.ps1'
REFERENCE = Path('build/uc001-transport-logging-v2/reference/gh-v2.81.0-ssh.go.txt')


def gh_parse_ssh_args(args):
    """Source-derived transcription of ParseSSHArgs/parseArgs, not gh execution."""
    source = REFERENCE.read_text()
    unary = re.search(r'return parseArgs\(args, "([^"]+)"\)', source).group(1)
    flags, command, i = [], [], 0
    while i < len(args):
        arg = args[i]
        if not arg.startswith('-'):
            command = args[i:]
            break
        flags.append(arg)
        if len(arg) == 2 and arg[1:2] in unary:
            i += 1
            if i == len(args):
                raise ValueError(f'flag: {arg} requires an argument')
            flags.append(args[i])
        i += 1
    return flags, command


def gh_shell_argv(flags, command):
    """newSSHCommand's argument construction; creates no executable/process."""
    return [*flags, '-p', '49189', '-o', 'NoHostAuthenticationForLocalhost=yes',
            '-o', 'PasswordAuthentication=no', '-C', 'vscode@localhost', *command]


def flow(variant, case):
    fixture = (ROOT / 'Test-Offline.ps1').read_text().replace(
        ". (Join-Path $PSScriptRoot 'Test-Transport.ps1')",
        f". (Join-Path $PSScriptRoot '{variant.name}')",
    ).replace('function Start-ContractProcess {', r'''
function Set-TransportLogPrivacy($Root) {
    if($Case -eq 'privacy_failed'){throw 'Synthetic ACL failure'}
    Require ($script:started -eq 0) 'Private directory applied after startup'
    $script:privateRoot=$Root
}
$script:capturedArguments=@()
function Start-TransportLoggingNativeProcess {
    param($Job,$Executable,$Arguments,$Stdout,$Stderr,$Key)
    Require ($script:privateRoot -eq (Split-Path $Stdout -Parent)) 'Unprotected log path'
    Require ($null -eq $Key) 'Probe secret put in environment instead of stdin'
    if($Executable.EndsWith('gh.exe')) {
        Require ($env:GH_DEBUG -eq '1') 'Wrong debug setting'
        $script:capturedArguments=@([regex]::Matches($Arguments,'"([^"]*)"')|ForEach-Object {$_.Groups[1].Value})
        if($Case -eq 'native_start_failed'){$script:started++;throw 'Synthetic startup failure'}
        $ssh="debug1: Connecting to localhost [::1] port 49189.`ndebug1: Connection established.`nbanner exchange: Connection to UNKNOWN port -1: Connection refused`n"
        [IO.File]::WriteAllText($Stderr,($ssh+"tunnel closed: error connecting to forwarded port: synthetic`nhttps://broker.invalid/private?token=SYNTHETIC_SECRET`nAuthorization: Bearer SYNTHETIC_SECRET`n-----BEGIN OPENSSH PRIVATE KEY-----`nSYNTHETIC_SECRET"))
    }
''').replace(
        "$result=Invoke-TransportProbe $bundle 'offline'",
        "$env:GH_DEBUG='api'; $result=Invoke-TransportLoggingProbe $bundle 'offline'; Require ($env:GH_DEBUG -eq 'api') 'Parent debug value not restored'",
    ).replace(
        "$expected=$(if($Case -eq 'endpoint_foreign'){1}else{2})",
        "$expected=$(if($Case -eq 'privacy_failed'){0}elseif($Case -in @('endpoint_foreign','native_start_failed')){1}else{2})",
    ).replace(
        "} finally {if(Test-Path -LiteralPath $temp)",
        '''
    $summary=[IO.File]::ReadAllText((Join-Path $result.result_directory 'sanitized-summary.json'))
    foreach($secret in @('SYNTHETIC_SECRET','broker.invalid','Authorization','PRIVATE KEY',$result.result_directory)) {
        Require (-not $summary.Contains($secret)) 'Unsafe summary copied raw log content'
    }
    $capture=@{argv=$script:capturedArguments;summary=($summary|ConvertFrom-Json)}
    Write-Output ('CAPTURE:'+($capture|ConvertTo-Json -Depth 8 -Compress))
} finally {if(Test-Path -LiteralPath $temp)''',
    ).replace('$PSScriptRoot', "'" + str(ROOT.resolve()).replace("'", "''") + "'")
    command = "$Case='" + case + "'; & {\n" + fixture.replace(
        'param([Parameter(Mandatory=$true)][string]$Case)', '', 1,
    ) + '\n}'
    result = subprocess.run(['pwsh', '-NoProfile', '-NonInteractive', '-Command', command], capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f'PASS {case}' in result.stdout
    return json.loads(next(line.removeprefix('CAPTURE:') for line in result.stdout.splitlines() if line.startswith('CAPTURE:')))


def test_source_pin_and_parser_boundaries():
    assert sha256(REFERENCE.read_bytes()).hexdigest() == 'eeb8cfee913b497a7e37aa186657eb837f27a08c44c74fe7ccaf632d081ec8a8'
    assert gh_parse_ssh_args(['-o', 'BatchMode=yes', 'remote'])[0] == ['-o', 'BatchMode=yes']
    assert gh_parse_ssh_args(['-E', 'logfile', '-T', 'remote']) == (['-E'], ['logfile', '-T', 'remote'])
    with pytest.raises(ValueError, match='requires an argument'):
        gh_parse_ssh_args(['-R'])
    source = REFERENCE.read_text()
    for construction in ['"-p", strconv.Itoa(port)', 'append(cmdArgs, connArgs...)', 'append(cmdArgs, "-C")', 'append(cmdArgs, dst)', 'append(cmdArgs, command...)']:
        assert construction in source


@pytest.mark.skipif(shutil.which('pwsh') is None, reason='PowerShell fixture absent')
def test_preserved_wrapper_reproduces_parser_defect_and_stray_log_operand():
    capture = flow(OLD, 'success')
    argv = capture['argv']
    flags, command = gh_parse_ssh_args(argv[argv.index('--') + 1:])
    assert flags == ['-vvv', '-E']
    assert command[0].endswith('ssh-debug.log') and command[1] == '-T'
    malformed = gh_shell_argv(flags, command)
    assert malformed[:5] == ['-vvv', '-E', '-p', '49189', '-o']
    assert malformed[malformed.index('-E') + 1] == '-p'
    assert malformed.index('vscode@localhost') < malformed.index('-T')


@pytest.mark.skipif(shutil.which('pwsh') is None, reason='PowerShell fixture absent')
@pytest.mark.parametrize('case', ['success', 'remote_failed', 'bridge_wildcard', 'endpoint_foreign',
    'job_close_failed', 'exit_unconfirmed', 'privacy_failed', 'native_start_failed'])
def test_corrected_parser_and_combined_log_keep_original_controls_and_cleanup(case):
    # Before implementation this runs the old candidate, exposing the real split (RED).
    capture = flow(CORRECTED if CORRECTED.exists() else OLD, case)
    argv, summary = capture['argv'], capture['summary']
    if argv:
        flags, command = gh_parse_ssh_args(argv[argv.index('--') + 1:])
        assert flags == ['-vvv', '-T', '-o', 'BatchMode=yes', '-o', 'ExitOnForwardFailure=yes',
            '-o', 'ServerAliveInterval=5', '-o', 'ServerAliveCountMax=2', '-o', 'ConnectTimeout=15',
            '-R', '127.0.0.1:49188:127.0.0.1:49187']
        assert command == ['cd /workspaces/resolena-alternative-finder && timeout --signal=TERM --kill-after=5s 35s env PYTHONPATH=src:. .venv/bin/python scripts/uc001_transport_preparation/probe_forward.py']
        shell = gh_shell_argv(flags, command)
        assert shell[-1] == command[0] and shell[-2] == 'vscode@localhost'
        assert shell[shell.index('-p') + 1] == '49189'
        assert shell[-7:] == ['-o', 'NoHostAuthenticationForLocalhost=yes', '-o',
            'PasswordAuthentication=no', '-C', 'vscode@localhost', command[0]]
        assert '-E' not in shell and not any('ssh-debug.log' in token for token in shell)
        identity = ['-i', r'C:\synthetic\codespaces.auto']
        with_identity, identity_command = gh_parse_ssh_args(identity + argv[argv.index('--') + 1:])
        assert with_identity == identity + flags and identity_command == command
        assert gh_shell_argv(with_identity, identity_command)[-2:] == ['vscode@localhost', command[0]]
    assert summary['version'] == 'uc001-transport-logging-2'
    assert summary['overall_limit_ms'] == 60000 and not summary['model_attempt_ledger_touched']
    assert summary['logs']['combined']['source'] == 'transport.stderr.log'
    assert summary['logs']['combined']['producers'] == ['gh', 'OpenSSH']
    if case not in {'endpoint_foreign', 'privacy_failed', 'native_start_failed'}:
        assert summary['ssh_connection_established_marker'] and summary['banner_refusal_marker'] and summary['forward_error_marker']
    else:
        assert summary['logs']['combined']['state'] == 'missing'
    assert summary['root_cause'] == 'not_established'


@pytest.mark.skipif(shutil.which('pwsh') is None, reason='PowerShell fixture absent')
def test_corrected_entry_is_guarded_and_control_delta_is_minimal():
    assert CORRECTED.exists(), 'Corrected separate wrapper is missing (RED)'
    old = OLD.read_text()
    expected = old.replace("$logging='\"--\" \"-vvv\" \"-E\" '+(Quote-ProbeArgument (Join-Path $root 'ssh-debug.log'))+' \"-T\"'", "$logging='\"--\" \"-vvv\" \"-T\"'")
    expected = expected.replace("$ssh=Get-TransportDiagnosticLog (Join-Path $result.result_directory 'ssh-debug.log')\n    $gh=Get-TransportDiagnosticLog (Join-Path $result.result_directory 'transport.stderr.log')", "$combined=Get-TransportDiagnosticLog (Join-Path $result.result_directory 'transport.stderr.log')")
    expected = expected.replace("version='uc001-transport-logging-1'", "version='uc001-transport-logging-2'")
    expected = expected.replace("logs=@{ssh=@{state=$ssh.state};gh=@{state=$gh.state}}", "logs=@{combined=@{state=$combined.state;source='transport.stderr.log';producers=@('gh','OpenSSH')}}")
    expected = expected.replace('($ssh.text+"`n"+$gh.text)', '$combined.text').replace('$ssh.text', '$combined.text').replace('$gh.text', '$combined.text')
    assert CORRECTED.read_text() == expected
    result = subprocess.run(['pwsh', '-NoProfile', '-NonInteractive', '-File', str(CORRECTED)], capture_output=True, text=True, timeout=10)
    assert result.returncode != 0 and 'logging-only approval' in result.stderr
    assert not (ROOT / 'results').exists()
