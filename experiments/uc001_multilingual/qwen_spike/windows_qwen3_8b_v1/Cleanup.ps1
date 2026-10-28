param([Parameter(Mandatory=$true)][string]$Root)
. (Join-Path $PSScriptRoot 'Common.ps1')
$Root = [IO.Path]::GetFullPath($Root).TrimEnd('\')
Assert-Bundle $Root
Stop-Owned $Root
$state = Get-State $Root; $state.status = 'closed_artifacts_preserved'
Write-Json (Join-Path $Root 'state.json') $state
$manifest = @{}
foreach ($file in @(Get-ChildItem -LiteralPath $Root -File -Recurse)) {
    if ($file.Name -eq 'cleanup_manifest.json') { continue }
    $relative = $file.FullName.Substring($Root.Length + 1)
    $manifest[$relative] = @{ bytes = $file.Length; sha256 = Get-Sha $file.FullName }
}
Write-Json (Join-Path $Root 'cleanup_manifest.json') @{ utc = [DateTime]::UtcNow.ToString('o'); files = $manifest;
    effect = 'Only matching owned server stopped. Models/results/markers/logs remain; no deletion.' }
Write-Host 'Closed. Keep the dedicated folder and archives. No automatic retry or deletion.'
