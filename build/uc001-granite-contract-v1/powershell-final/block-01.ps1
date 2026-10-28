$GraniteWorktree = (Get-Location).Path
$env:PYTHONPATH = "$(Join-Path $GraniteWorktree 'src');$GraniteWorktree"
python -m scripts.uc001_granite_contract_v1.package verify
python -m scripts.uc001_granite_contract_v1.package verify-archive --archive 'C:\Resolena\granite-v1\desktop-transfer.zip'
