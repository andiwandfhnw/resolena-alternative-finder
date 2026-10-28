[CmdletBinding()]
param()

function Invoke-AdapterPreflight {
    $report = [ordered]@{version='uc001-preflight-capacity-v1.2.0';outcome='association_failed';association='unverified'
        adapter=$null;resources=$null;limits=$null;error=$null;verification_scope='identity and one resource snapshot only; no model/runtime or transport verification'}
    try {
        Assert-ContractWindows
        Assert-ContractBundle
        $config = Read-ContractJson (Join-Path $PSScriptRoot 'config.json')
        $report.limits = $config.limits
        $adapter = Get-ReadOnlyContractAdapter
        $report.adapter = $adapter
        $report.association = 'verified'
        $report.outcome = 'measurement_failed'
        $runRoot = Join-Path (Split-Path $config.reuse_root -Parent) 'uc001-contract-runs\preflight-no-artifacts'
        $report.resources = Get-ContractResources $adapter $runRoot
        $report.outcome = 'resource_guard_failed'
        Assert-ContractResources $report.resources $config.limits $true
        $report.outcome = 'preflight_passed'
    } catch { $report.error = $_.Exception.Message }
    return [pscustomobject]$report
}

if ($MyInvocation.InvocationName -ne '.') {
    . (Join-Path $PSScriptRoot 'Common.ps1')
    $result = Invoke-AdapterPreflight
    $result | ConvertTo-Json -Depth 12
    if ($result.outcome -ne 'preflight_passed') { exit 1 }
}
