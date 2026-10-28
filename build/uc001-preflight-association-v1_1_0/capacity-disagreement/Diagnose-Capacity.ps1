& {
    Set-StrictMode -Version Latest
    $ErrorActionPreference = 'Stop'
    function Assert-CapacityEnvironment {
        if ($PSVersionTable.PSEdition -ne 'Desktop' -or $PSVersionTable.PSVersion -lt [version]'5.1' -or
            -not [Environment]::Is64BitProcess -or $ExecutionContext.SessionState.LanguageMode -ne 'FullLanguage') {
            throw 'Use existing 64-bit Windows PowerShell 5.1 FullLanguage; do not change policy.'
        }
        Add-Type -AssemblyName System.Numerics
    }
    function Read-CapacityDxgi([string]$Bundle) {
        if (-not ('Uc001PreflightAssociationV110.Reader' -as [type])) {
            Add-Type -Path (Join-Path $Bundle 'AdapterIdentity.cs') -ErrorAction Stop
        }
        return [Uc001PreflightAssociationV110.Reader]::Read()
    }
    function Format-CapacityValue($Value) {
        $result = [ordered]@{state='unavailable';raw_value=$Value;raw_type=$null;bytes_decimal=$null;decoded_type=$null}
        if ($null -eq $Value) { return $result }
        $result.raw_type = $Value.GetType().FullName
        if ($Value -is [byte[]]) {
            $result.raw_value = @($Value)
            if ($Value.Length -ne 8) { $result.state='invalid_length'; return $result }
            $number = [BitConverter]::ToUInt64($Value,0)
        } elseif ($Value -is [long] -or $Value -is [uint64]) {
            $number = $Value
        } else { $result.state='invalid_type'; return $result }
        if ($number -lt 0) { $result.state='invalid_value'; return $result }
        $result.state='ok'; $result.decoded_type=$number.GetType().FullName
        $result.bytes_decimal=$number.ToString([Globalization.CultureInfo]::InvariantCulture)
        return $result
    }
    function Get-CapacityDiagnostic([string]$Bundle) {
        $report = [ordered]@{status='incomplete';utc=[DateTime]::UtcNow.ToString('o');bundle=$Bundle
            cim=[ordered]@{state='not_queried';devices=@();error=$null}
            registry=[ordered]@{state='not_queried';field='HardwareInformation.qwMemorySize';enum_path=$null;driver_raw=$null;driver_type=$null;path=$null;capacity=@{state='not_queried'};error=$null}
            dxgi=[ordered]@{state='not_queried';field='DXGI_ADAPTER_DESC1.DedicatedVideoMemory (SIZE_T -> UIntPtr -> UInt64 DedicatedBytes)';scan_status=$null;adapters=@();identity=$null;capacity=@{state='not_queried'};error=$null}
            difference=[ordered]@{state='unavailable';direction='DXGI minus registry';bytes=$null;type='System.Numerics.BigInteger'}
            error=$null}
        try { Assert-CapacityEnvironment } catch { $report.error=$_.Exception.Message; return [pscustomobject]$report }
        try {
            $controllers = @(Get-CimInstance Win32_VideoController -ErrorAction Stop)
            $report.cim.devices = @($controllers | Select-Object Name,PNPDeviceID,DeviceID,DriverVersion)
            if ($controllers.Count -ne 1) {
                $report.cim.state=$(if($controllers.Count -eq 0){'missing'}else{'ambiguous'}); return [pscustomobject]$report
            }
            $c = $controllers[0]
            $pattern='^PCI\\VEN_([0-9A-F]{4})&DEV_([0-9A-F]{4})&SUBSYS_([0-9A-F]{8})&REV_([0-9A-F]{2})\\[^\\]+$'
            if ($c.Name -notmatch 'RX\s*6800\s*XT' -or $c.PNPDeviceID -notmatch $pattern) {
                $report.cim.state='invalid_identity'; return [pscustomobject]$report
            }
            $pci = @($Matches[1],$Matches[2],$Matches[3],$Matches[4] | ForEach-Object {[Convert]::ToUInt32($_,16)})
            if ($pci[0] -ne 0x1002) { $report.cim.state='invalid_identity'; return [pscustomobject]$report }
            $report.cim.state='ok'
        } catch { $report.cim.state='query_failed'; $report.cim.error=$_.Exception.Message; return [pscustomobject]$report }
        try {
            $report.registry.enum_path='HKLM:\SYSTEM\CurrentControlSet\Enum\'+$c.PNPDeviceID
            $device=Get-ItemProperty -LiteralPath $report.registry.enum_path -ErrorAction Stop
            $driver=$device.PSObject.Properties['Driver']
            if ($null -eq $driver) { $report.registry.state='missing_driver' }
            elseif ($driver.Value -isnot [string] -or [string]::IsNullOrWhiteSpace($driver.Value)) { $report.registry.state='unavailable_driver' }
            else {
                $report.registry.driver_raw=$driver.Value; $report.registry.driver_type=$driver.Value.GetType().FullName
                $report.registry.path='HKLM:\SYSTEM\CurrentControlSet\Control\Class\'+$driver.Value
                $key=Get-ItemProperty -LiteralPath $report.registry.path -ErrorAction Stop
                $value=$key.PSObject.Properties['HardwareInformation.qwMemorySize']
                $report.registry.state='ok'
                if ($null -eq $value) { $report.registry.capacity=@{state='missing'} }
                else { $report.registry.capacity=Format-CapacityValue $value.Value }
            }
        } catch {
            $report.registry.state=$(if($_.CategoryInfo.Category -eq 'ObjectNotFound'){'missing_key'}else{'query_failed'})
            $report.registry.error=$_.Exception.Message
        }
        try {
            $scan=Read-CapacityDxgi $Bundle
            if ($null -eq $scan) { throw 'Native reader returned no query result.' }
            $report.dxgi.scan_status=$scan.Status; $report.dxgi.adapters=@($scan.Adapters | ForEach-Object {$_})
            if ($scan.Status -ne 'ok') { throw ('Native enumeration failed/incomplete: '+$scan.Status+'; '+$scan.Error) }
            $all=$report.dxgi.adapters
            $matching=@($all | Where-Object {
                $_.Status -eq 'ok' -and ($_.Flags -band 2) -eq 0 -and
                [string]::Equals($_.Description.Trim(),$c.Name.Trim(),[StringComparison]::OrdinalIgnoreCase) -and
                $_.Vendor -eq $pci[0] -and $_.Device -eq $pci[1] -and $_.Subsystem -eq $pci[2] -and $_.Revision -eq $pci[3]
            })
            if ($matching.Count -ne 1) { $report.dxgi.state=$(if($matching.Count -eq 0){'missing'}else{'ambiguous'}) }
            else {
                $a=$matching[0]
                $sameLuid=@($all | Where-Object {[string]::Equals($_.CounterKey,$a.CounterKey,[StringComparison]::OrdinalIgnoreCase)})
                if ($sameLuid.Count -ne 1 -or $a.CounterKey -notmatch '^luid_0x[0-9A-F]{8}_0x[0-9A-F]{8}$') { $report.dxgi.state='ambiguous' }
                else {
                    $report.dxgi.state='ok'
                    $report.dxgi.identity=$a | Select-Object Description,Vendor,Device,Subsystem,Revision,Flags,CounterKey
                    $report.dxgi.capacity=Format-CapacityValue $a.DedicatedBytes
                }
            }
        } catch { $report.dxgi.state='query_failed'; $report.dxgi.error=$_.Exception.Message }
        if ($report.registry.capacity.state -eq 'ok' -and $report.dxgi.capacity.state -eq 'ok') {
            $culture=[Globalization.CultureInfo]::InvariantCulture
            $d=[Numerics.BigInteger]::Parse($report.dxgi.capacity.bytes_decimal,$culture)
            $r=[Numerics.BigInteger]::Parse($report.registry.capacity.bytes_decimal,$culture)
            $report.difference.bytes=[Numerics.BigInteger]::Subtract($d,$r).ToString($culture)
            $report.difference.state='ok'; $report.status='comparison_available'
        }
        return [pscustomobject]$report
    }
    Get-CapacityDiagnostic 'C:\ResolenaExperiments\uc001-preflight-association-v1_1_0' | ConvertTo-Json -Depth 12
}
