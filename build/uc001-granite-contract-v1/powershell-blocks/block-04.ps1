$GranitePackage = Join-Path $GraniteWorktree 'scripts\uc001_granite_contract_v1'
$GraniteInspectBuild = Join-Path $GraniteRoot 'native-schema-inspection-build'
$GraniteInspection = Join-Path $GraniteRoot 'native-schema-inspection-output'
if ((Test-Path $GraniteInspectBuild) -or (Test-Path $GraniteInspection)) { throw 'Fresh native-inspection paths required.' }
cmake -S (Join-Path $GranitePackage 'native-inspection') -B $GraniteInspectBuild -G Ninja -DCMAKE_BUILD_TYPE=Release "-DLLAMA_SOURCE_DIR=$GraniteSource"
if ($LASTEXITCODE -ne 0) { throw 'Native inspection configure failed; no automatic dependency acquisition.' }
cmake --build $GraniteInspectBuild --config Release --target granite-inspect-schema --parallel 2
if ($LASTEXITCODE -ne 0) { throw 'Native inspection build failed.' }
$GraniteInspector = Join-Path $GraniteInspectBuild 'bin\granite-inspect-schema.exe'
Get-FileHash -LiteralPath $GraniteInspector -Algorithm SHA256
New-Item -ItemType Directory -Path $GraniteInspection -ErrorAction Stop | Out-Null
$GraniteGrammar = Join-Path $GraniteInspection 'schema.gbnf'
$GraniteConversionErrors = Join-Path $GraniteInspection 'schema-conversion.stderr.txt'
& $GraniteInspector (Join-Path $GranitePackage 'schema.json') $GraniteGrammar 2> $GraniteConversionErrors
if ($LASTEXITCODE -ne 0) { throw 'Native schema conversion failed.' }
if (-not (Test-Path $GraniteGrammar) -or (Get-Item -LiteralPath $GraniteGrammar).Length -eq 0) { throw 'Native converter produced no grammar.' }
if (-not (Test-Path $GraniteConversionErrors) -or (Get-Item -LiteralPath $GraniteConversionErrors).Length -ne 0) { throw 'Native conversion warnings/errors are not accepted.' }
Get-FileHash -LiteralPath $GraniteGrammar -Algorithm SHA256
