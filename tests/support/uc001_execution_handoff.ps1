param([string]$Case)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
function Require($Value,$Reason){if(-not $Value){throw $Reason}}
$readme=Get-Content -LiteralPath (Join-Path $PSScriptRoot '../../scripts/uc001_contract_local_v1_4_0/README.md') -Raw
$block=[regex]::Match($readme,'(?s)```powershell\s*(.*?)```').Groups[1].Value
$tokens=$null;$errors=$null;$ast=[Management.Automation.Language.Parser]::ParseInput($block,[ref]$tokens,[ref]$errors)
Require ($errors.Count -eq 0) 'Handoff does not parse'
foreach($name in @('Assert-MatchingExecutionExtraction','Get-ExecutionApprovalPath')) {
    $node=$ast.Find({param($Node)$Node -is [Management.Automation.Language.FunctionDefinitionAst] -and $Node.Name -eq $name},$true)
    Require ($null -ne $node) ('Missing actual handoff function '+$name)
    . ([scriptblock]::Create($node.Extent.Text))
}
$temp=Join-Path ([IO.Path]::GetTempPath()) ('uc001-handoff-synthetic-'+[guid]::NewGuid());$null=New-Item -ItemType Directory -Path $temp
try {
    $source=Join-Path $temp 'source';$null=New-Item -ItemType Directory -Path $source
    [IO.File]::WriteAllText((Join-Path $source 'module.py'),'explicit synthetic source')
    $archive=Join-Path $temp 'fixture.zip'
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Compression.ZipFile]::CreateFromDirectory($source,$archive)
    $target=Join-Path $temp 'extracted';Expand-Archive -LiteralPath $archive -DestinationPath $target
    if($Case -in @('matching','mismatched','extra_file')) {
        if($Case -eq 'mismatched'){[IO.File]::WriteAllText((Join-Path $target 'module.py'),'changed synthetic source')}
        if($Case -eq 'extra_file'){[IO.File]::WriteAllText((Join-Path $target 'unexpected.py'),'extra synthetic source')}
        $failed=$false;try {Assert-MatchingExecutionExtraction $archive $target} catch {$failed=$true}
        Require ($failed -eq ($Case -ne 'matching')) 'Mismatched extraction accepted or matching extraction rejected'
    } else {
        $pending=@{approved=$false;attempt_identity='synthetic-never-a-real-attempt';freeze_sha256=$null;approval_reference=$null}
        [IO.File]::WriteAllText((Join-Path $source 'approval.pending.json'),($pending|ConvertTo-Json))
        [IO.File]::WriteAllText((Join-Path $source 'freeze.json'),'explicit synthetic freeze')
        $approvals=Join-Path $temp 'approvals';$null=New-Item -ItemType Directory -Path $approvals
        $path=Join-Path $approvals ($pending.attempt_identity+'.json')
        if($Case -eq 'reuse_approval') {
            $bytes=[Text.Encoding]::UTF8.GetBytes('{"approved":true,"evidence":"explicit synthetic existing approval; shared Python gate validates real records"}')
            [IO.File]::WriteAllBytes($path,$bytes)
            $returned=Get-ExecutionApprovalPath $source $approvals ''
            Require ($returned -eq $path -and [Convert]::ToBase64String([IO.File]::ReadAllBytes($path)) -eq [Convert]::ToBase64String($bytes)) 'Existing approval was overwritten or not reused'
        } else {
            $failed=$false;try {$null=Get-ExecutionApprovalPath $source $approvals ''} catch {$failed=$true}
            Require ($failed -and -not (Test-Path -LiteralPath $path)) 'Blank approval created permission'
        }
    }
    'PASS '+$Case
} finally {Remove-Item -LiteralPath $temp -Recurse -Force}
