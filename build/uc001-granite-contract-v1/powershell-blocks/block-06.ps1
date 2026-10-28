$GraniteApproval = 'C:\Resolena\private\granite-v1-owner-approval.json'
$GraniteOutput = 'build/test-only/granite-v1-REPLACE-WITH-NEW-ID'
$env:PYTHONPATH = "$(Join-Path $GraniteWorktree 'src');$GraniteWorktree"
$env:RESOLENA_GRANITE_API_KEY = (Get-Content -LiteralPath $GraniteKeyFile -Raw).Trim()
python -m scripts.uc001_granite_contract_v1.assess --approval $GraniteApproval --output $GraniteOutput
$GraniteClientExit = $LASTEXITCODE
Remove-Item Env:RESOLENA_GRANITE_API_KEY -ErrorAction SilentlyContinue
if ($GraniteClientExit -ne 0) { throw 'Assessment stopped; preserve captures and stop the owned server.' }
