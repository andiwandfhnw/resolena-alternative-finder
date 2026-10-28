cmake -S $GraniteSource -B $GraniteBuild -G Ninja -DCMAKE_BUILD_TYPE=Release -DFETCHCONTENT_FULLY_DISCONNECTED=ON -DGGML_VULKAN=ON -DLLAMA_BUILD_SERVER=ON -DLLAMA_BUILD_TOOLS=ON -DLLAMA_BUILD_COMMON=ON -DLLAMA_BUILD_IS_DEV=OFF "-DLLAMA_BUILD_COMMIT=$GraniteRuntimeCommit" -DLLAMA_BUILD_NUMBER=0 -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_APP=OFF -DLLAMA_BUILD_UI=OFF -DLLAMA_USE_PREBUILT_UI=OFF -DLLAMA_OPENSSL=OFF -DLLAMA_SUBPROCESS=OFF -DLLAMA_LLGUIDANCE=OFF
if ($LASTEXITCODE -ne 0) { throw 'Offline pinned configure failed; do not install/fetch missing dependencies automatically.' }
cmake --build $GraniteBuild --config Release --target llama-server --parallel 2
if ($LASTEXITCODE -ne 0) { throw 'Pinned source build failed.' }
$GraniteServer = Join-Path $GraniteBuild 'bin\llama-server.exe'
Get-FileHash -LiteralPath $GraniteServer -Algorithm SHA256
