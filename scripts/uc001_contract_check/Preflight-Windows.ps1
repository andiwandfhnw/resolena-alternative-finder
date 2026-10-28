[CmdletBinding()]
param()
. (Join-Path $PSScriptRoot 'Common.ps1')
Assert-ContractWindows
Assert-ContractBundle
$config = Read-ContractJson (Join-Path $PSScriptRoot 'config.json')
Get-ContractAssets $config
$adapter = Get-ReadOnlyContractAdapter
$sample = Get-ContractResources $adapter (Join-Path (Split-Path $config.reuse_root -Parent) 'uc001-contract-runs\preflight-no-artifacts')
Assert-ContractResources $sample $config.limits $true
$tools = Get-ContractTools
$ports = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -in @(49187,49189) })
$servers = @(Get-CimInstance Win32_Process -Filter "Name='llama-server.exe'")
[ordered]@{ kind = 'read-only Windows preflight; no model/runtime execution or network connection'
    retained_assets_match = $true; resources = $sample; tools = $tools
    occupied_ports = @($ports | Select-Object LocalAddress,LocalPort,OwningProcess)
    existing_server_count = $servers.Count
    ready_for_review = ($tools.gh_pin_available -and $null -ne $tools.ssh -and $ports.Count -eq 0 -and $servers.Count -eq 0)
    limits = 'Active-driver registry capacity minus WDDM usage requires a unique mapping; not a residency guarantee. Live DXGI/transport/settings/context fit and qualified review remain unverified.'
} | ConvertTo-Json -Depth 12
