$GraniteRoot = 'C:\Resolena\granite-v1'
$GraniteAssets = Join-Path $GraniteRoot 'assets'
$GraniteSourceRepo = Join-Path $GraniteRoot 'runtime-source-repository'
$GraniteSourceZip = Join-Path $GraniteRoot 'llama-620d2225-source.zip'
$GraniteSource = Join-Path $GraniteRoot 'runtime-source'
$GraniteBuild = Join-Path $GraniteRoot 'runtime-build'
$GraniteRuntimeCommit = '620d2225cc436ab0b001e3200e590e3b286ef9ab'
$GraniteArtifact = 'granite-3.3-8b-instruct-Q8_0.gguf'
$GraniteExpectedHash = '8ced2b014c6b5d4b1be698fd2cb5b051b08ce0b439d2584eb358e0d3f0a00611'
$GraniteModel = Join-Path $GraniteAssets $GraniteArtifact
$GranitePartial = $GraniteModel + '.partial'
if ((Test-Path $GraniteSourceRepo) -or (Test-Path $GraniteSourceZip) -or (Test-Path $GraniteSource) -or (Test-Path $GraniteBuild) -or (Test-Path $GraniteModel) -or (Test-Path $GranitePartial)) { throw 'Fresh paths required; preserve earlier artifacts.' }
New-Item -ItemType Directory -Path $GraniteAssets -ErrorAction Stop | Out-Null
$GraniteModelUrl = 'https://huggingface.co/ibm-granite/granite-3.3-8b-instruct-GGUF/resolve/e40e9dd739c7be00fa965c16ce167088190ce114/granite-3.3-8b-instruct-Q8_0.gguf?download=true'
curl.exe --fail --location --proto '=https' --proto-redir '=https' --retry 0 --connect-timeout 30 --max-time 1800 --max-filesize 8684264992 --output $GranitePartial $GraniteModelUrl
if ($LASTEXITCODE -ne 0) { throw 'Model acquisition failed; do not retry automatically.' }
if ((Get-Item -LiteralPath $GranitePartial).Length -ne 8684264992) { throw 'Model byte count mismatch.' }
if ((Get-FileHash -LiteralPath $GranitePartial -Algorithm SHA256).Hash.ToLowerInvariant() -ne $GraniteExpectedHash) { throw 'Model SHA-256 mismatch.' }
Move-Item -LiteralPath $GranitePartial -Destination $GraniteModel -ErrorAction Stop

git init $GraniteSourceRepo
if ($LASTEXITCODE -ne 0) { throw 'Source repository initialization failed.' }
git -C $GraniteSourceRepo remote add origin https://github.com/ggml-org/llama.cpp.git
git -C $GraniteSourceRepo fetch --depth=1 --no-tags --recurse-submodules=no origin $GraniteRuntimeCommit
if ($LASTEXITCODE -ne 0) { throw 'Pinned source acquisition failed; do not retry automatically.' }
if ((git -C $GraniteSourceRepo rev-parse FETCH_HEAD).Trim() -ne $GraniteRuntimeCommit) { throw 'Runtime source revision mismatch.' }
git -C $GraniteSourceRepo archive --format=zip "--output=$GraniteSourceZip" FETCH_HEAD
if ($LASTEXITCODE -ne 0) { throw 'Source archive failed.' }
Get-FileHash -LiteralPath $GraniteSourceZip -Algorithm SHA256
Expand-Archive -LiteralPath $GraniteSourceZip -DestinationPath $GraniteSource -ErrorAction Stop
