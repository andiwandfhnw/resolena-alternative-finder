param([Parameter(Mandatory=$true)][string]$Root)
. (Join-Path $PSScriptRoot 'Common.ps1')
Assert-Bundle $PSScriptRoot
$Root = [IO.Path]::GetFullPath($Root).TrimEnd('\')
if ($Root.StartsWith('\\') -or $Root -eq $PSScriptRoot -or (Test-Path -LiteralPath $Root)) { throw 'Select a NEW dedicated local folder; preserve any existing folder.' }
$config = Read-Json (Join-Path $PSScriptRoot 'config.json')
$adapter = Get-Adapter
$preflight = Get-ResourceSample $Root $adapter
Assert-Resources $preflight $config $true
Assert-NoDuplicate $Root
$stagingMarker = Join-Path $PSScriptRoot 'setup_attempt.json'
if (Test-Path -LiteralPath $stagingMarker) { throw 'This bundle already started setup; preserve its marker and original deadlines. No new folder/retry.' }
$null = New-Item -ItemType Directory -Path $Root
$now = [DateTime]::UtcNow
Write-Json $stagingMarker @{ root = $Root; started_utc = $now.ToString('o'); single_authorized_attempt = $true }
Write-Json (Join-Path $Root 'state.json') @{ status = 'setup_running'; version = '1.0.0'; started_utc = $now.ToString('o');
    total_deadline_utc = $now.AddSeconds($config.limits.total_seconds).ToString('o'); setup_deadline_utc = $now.AddSeconds($config.limits.setup_seconds).ToString('o') }
try {
    $freeze = Read-Json (Join-Path $PSScriptRoot 'freeze.json')
    foreach ($property in $freeze.files.PSObject.Properties) {
        $destination = Join-Path $Root $property.Name
        $null = New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($destination)) -Force
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot $property.Name) -Destination $destination
    }
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'freeze.json') -Destination $Root
    Copy-Item -LiteralPath $stagingMarker -Destination $Root
    Assert-Bundle $Root
    Write-Json (Join-Path $Root 'preflight.json') $preflight
    $artifacts = Read-Json (Join-Path $Root 'artifacts.json')
    $expectedTotal = [long]($artifacts.artifacts | Measure-Object -Property bytes -Sum).Sum
    if ($expectedTotal + $artifacts.reserved_bundle_and_metadata_bytes -gt $artifacts.cap_bytes) { throw 'Artifact sizes exceed the acquisition cap.' }
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $headers = @{ 'User-Agent' = 'Resolena-read-only-artifact-metadata' }
    $runtime = $artifacts.artifacts[0]
    $model = $artifacts.artifacts[1]
    $runtimeMetadata = Invoke-WebRequest -UseBasicParsing -Uri $runtime.metadata_url -Headers $headers -TimeoutSec 30
    $runtimeJson = $runtimeMetadata.Content | ConvertFrom-Json
    $asset = @($runtimeJson.assets | Where-Object { $_.name -eq $runtime.file })
    $modelMetadata = Invoke-WebRequest -UseBasicParsing -Uri $model.metadata_url -Headers $headers -TimeoutSec 30
    $modelJson = $modelMetadata.Content | ConvertFrom-Json
    $weight = @($modelJson.siblings | Where-Object { $_.rfilename -eq $model.file })
    if ($asset.Count -ne 1 -or $weight.Count -ne 1 -or $modelJson.sha -ne $model.revision -or
        [long]$asset[0].size -ne [long]$runtime.bytes -or $asset[0].digest -ne ('sha256:' + $runtime.sha256) -or
        $asset[0].browser_download_url -ne $runtime.url -or [long]$weight[0].size -ne [long]$model.bytes -or
        $weight[0].lfs.sha256 -ne $model.sha256) { throw 'Publisher metadata differs from the frozen sizes/URLs/digests. STOP before artifact download.' }
    $metadataBytes = [Text.Encoding]::UTF8.GetByteCount($runtimeMetadata.Content) + [Text.Encoding]::UTF8.GetByteCount($modelMetadata.Content)
    if ($metadataBytes -gt 524288) { throw 'Metadata exceeds its reserved budget; STOP before artifact download.' }
    Write-Json (Join-Path $Root 'metadata_verification.json') @{ utc = [DateTime]::UtcNow.ToString('o');
        artifact_bytes = $expectedTotal; cap_bytes = $artifacts.cap_bytes; reserved_bundle_metadata_bytes = $artifacts.reserved_bundle_and_metadata_bytes;
        measured_metadata_body_bytes = $metadataBytes; status = 'exact_frozen_metadata_matched' }
    $ledger = @{ status = 'started'; bytes = [long]$artifacts.reserved_bundle_and_metadata_bytes; cap_bytes = [long]$artifacts.cap_bytes; completed = @() }
    Write-Json (Join-Path $Root 'download.json') $ledger
    foreach ($artifact in $artifacts.artifacts) {
        Assert-Deadline $Root 'setup'
        Assert-Resources (Get-ResourceSample $Root $adapter) $config
        $path = Join-Path $Root $artifact.file
        $request = [Net.HttpWebRequest]::Create($artifact.url)
        $request.UserAgent = 'Resolena-pinned-synthetic-experiment'; $request.Timeout = 30000; $request.ReadWriteTimeout = 15000
        $response = $request.GetResponse()
        if ($response.ContentLength -ge 0 -and $response.ContentLength -ne [long]$artifact.bytes) { $response.Close(); throw 'Download Content-Length mismatch; no body read.' }
        $inputStream = $response.GetResponseStream()
        $outputStream = [IO.File]::Open(($path + '.part'), [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
        $buffer = New-Object byte[] 1048576
        $received = 0L
        $lastSaved = 0L
        try {
            while (($count = $inputStream.Read($buffer, 0, $buffer.Length)) -gt 0) {
                Assert-Deadline $Root 'setup'
                $received += $count; $ledger.bytes += $count
                if ($received -gt [long]$artifact.bytes -or $ledger.bytes -gt [long]$ledger.cap_bytes) { throw 'Acquisition byte cap exceeded.' }
                $outputStream.Write($buffer, 0, $count)
                if ($received - $lastSaved -ge 16777216) {
                    $outputStream.Flush(); $lastSaved = $received
                    Write-Json (Join-Path $Root 'download.json') $ledger
                    Assert-Resources (Get-ResourceSample $Root $adapter) $config
                }
            }
        } finally { $outputStream.Dispose(); $inputStream.Dispose(); $response.Close(); Write-Json (Join-Path $Root 'download.json') $ledger }
        if ($received -ne [long]$artifact.bytes -or (Get-Sha ($path + '.part')) -ne $artifact.sha256) { throw 'Artifact size/SHA-256 verification failed; preserve partial file and stop.' }
        Move-Item -LiteralPath ($path + '.part') -Destination $path
        $ledger.completed += $artifact.id
        Write-Json (Join-Path $Root 'download.json') $ledger
        if ($artifact.id -eq 'runtime') {
            $runtimeFolder = Join-Path $Root 'runtime'
            Expand-Archive -LiteralPath $path -DestinationPath $runtimeFolder
            $servers = @(Get-ChildItem -LiteralPath $runtimeFolder -Filter 'llama-server.exe' -Recurse)
            if ($servers.Count -ne 1) { throw 'Runtime layout is unexpected; stop without prerequisite installation.' }
            $server = $servers[0].FullName
            $checks = @(@{ flag = '--version'; name = 'version' }, @{ flag = '--list-devices'; name = 'devices' })
            foreach ($check in $checks) {
                Assert-Deadline $Root 'setup'
                $prefix = Join-Path $Root ('runtime_' + $check.name)
                $process = [ResolenaProcess]::Start($server, $check.flag, ($prefix + '.stdout.log'), ($prefix + '.stderr.log'))
                if (-not $process.WaitForExit(30000)) { $process.Kill(); throw 'Runtime compatibility utility timed out; stop.' }
                $process.WaitForExit()
                Write-Json ($prefix + '.exit.json') @{ exit_code = $process.ExitCode; utc = [DateTime]::UtcNow.ToString('o') }
                if ($process.ExitCode -ne 0) { throw 'Runtime compatibility/device check failed. No model download or driver update.' }
            }
            $versionText = [IO.File]::ReadAllText((Join-Path $Root 'runtime_version.stdout.log')) + [IO.File]::ReadAllText((Join-Path $Root 'runtime_version.stderr.log'))
            $deviceText = [IO.File]::ReadAllText((Join-Path $Root 'runtime_devices.stdout.log')) + [IO.File]::ReadAllText((Join-Path $Root 'runtime_devices.stderr.log'))
            if ($versionText -notmatch 'd812350' -or $deviceText -notmatch 'Vulkan0:[^\r\n]*RX\s*6800\s*XT') { throw 'Pinned runtime/selected Vulkan0 RX 6800 XT not confirmed; STOP before model acquisition.' }
            Write-Json (Join-Path $Root 'runtime_verification.json') @{ executable = $server; executable_sha256 = Get-Sha $server;
                version_pin = 'd81235049384534c167caea52b85a694f6103d14'; device = 'Vulkan0'; model_loaded = $false }
        }
    }
    Assert-Deadline $Root 'setup'
    $ledger.status = 'verified_complete'; Write-Json (Join-Path $Root 'download.json') $ledger
    $state = Get-State $Root; $state.status = 'prepared'; Write-Json (Join-Path $Root 'state.json') $state
    Write-Host ('Prepared and verified, no model loaded. Original total deadline: ' + $state.total_deadline_utc)
    Write-Host 'Stop here and report setup status before the separate Run.ps1 step.'
} catch {
    Write-Json (Join-Path $Root 'setup_failure.json') @{ utc = [DateTime]::UtcNow.ToString('o'); error = $_.Exception.Message; exit_status = 1 }
    $state = Get-State $Root; $state.status = 'setup_failed'; Write-Json (Join-Path $Root 'state.json') $state
    throw
}
