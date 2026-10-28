param([Parameter(Mandatory=$true)][string]$Root, [string]$ArtifactsRoot = 'C:\ResolenaExperiments\qwen3-8b-v1')
$parseErrors = @()
foreach ($file in @(Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.ps1')) {
    $tokens = $null; $errors = $null
    $null = [Management.Automation.Language.Parser]::ParseFile($file.FullName, [ref]$tokens, [ref]$errors)
    if ($errors) { $parseErrors += $errors }
}
if ($parseErrors.Count -gt 0) { $parseErrors | Format-List; throw 'Parser failure: stop before any model process.' }
. (Join-Path $PSScriptRoot 'Common.ps1')
Assert-Bundle $PSScriptRoot
$Root = [IO.Path]::GetFullPath($Root).TrimEnd('\'); $ArtifactsRoot = [IO.Path]::GetFullPath($ArtifactsRoot).TrimEnd('\')
if ($Root.StartsWith('\\') -or $ArtifactsRoot.StartsWith('\\') -or $Root -ieq $ArtifactsRoot -or $Root.StartsWith($ArtifactsRoot + '\', [StringComparison]::OrdinalIgnoreCase) -or $ArtifactsRoot.StartsWith($Root + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Use separate local folders; do not modify v1 or overlap artifacts.' }
Assert-NoDuplicate $Root; Assert-NoDuplicate $ArtifactsRoot
$config = Read-Json (Join-Path $PSScriptRoot 'config.json')
if (@(Get-NetTCPConnection -LocalPort $config.server_port -ErrorAction SilentlyContinue).Count -gt 0) { throw 'Loopback port already occupied; stop, do not terminate its owner.' }
$adapter = Get-Adapter; $sample = Get-ResourceSample $Root $adapter 0 $ArtifactsRoot
try { Assert-Resources $sample $config $true } catch {
    @{ status = 'preflight_failed'; utc = [DateTime]::UtcNow.ToString('o'); measured = $sample; thresholds = $config.limits; error = $_.Exception.Message } | ConvertTo-Json -Depth 12
    throw
}
@{ status = 'preflight_pass'; freeze_sha256 = Get-Sha (Join-Path $PSScriptRoot 'freeze.json'); target_folder = $Root;
    artifacts_root = $ArtifactsRoot; resources = $sample; effect = 'Read-only preflight; no timed attempt or model process started.';
    capacity = 'Actual v2 token capacity unmeasured until a separately authorized model load; all requests checked before generation.' } | ConvertTo-Json -Depth 12
