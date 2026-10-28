& {
    function Count-State($n) {
        if ($n -eq 0) { 'none' } elseif ($n -eq 1) { 'single' } else { 'multiple' }
    }
    function Field($object, $name) {
        $p = $object.PSObject.Properties[$name]
        if ($null -eq $p) { return @{status='missing_property'; value=$null} }
        if ($null -eq $p.Value) { return @{status='null_value'; value=$null} }
        return @{status='present'; type=$p.Value.GetType().FullName; value=$p.Value}
    }
    $out = [ordered]@{}
    $adapters = @()
    try {
        $adapters = @(Get-CimInstance Win32_VideoController -ErrorAction Stop)
        $matching = @($adapters | Where-Object { $_.Name -match 'RX\s*6800\s*XT' })
        $out.adapters = @{query='ok'; total=$adapters.Count; total_state=(Count-State $adapters.Count)
            matching=$matching.Count; matching_state=(Count-State $matching.Count)
            instances=@($adapters | Select-Object Name,DeviceID,PNPDeviceID,DriverVersion)}
    } catch { $out.adapters = @{query='unavailable'; error=$_.Exception.Message; error_id=$_.FullyQualifiedErrorId} }
    $out.registry = @(foreach ($a in $adapters) {
        $row = [ordered]@{adapter=$a.Name; pnp_id=$a.PNPDeviceID}
        try {
            if ([string]::IsNullOrWhiteSpace($a.PNPDeviceID)) { throw 'PNPDeviceID missing; registry mapping unavailable.' }
            $row.enum_path = 'HKLM:\SYSTEM\CurrentControlSet\Enum\' + $a.PNPDeviceID
            $device = Get-ItemProperty -LiteralPath $row.enum_path -ErrorAction Stop
            $row.Driver = Field $device 'Driver'
            if ($row.Driver.status -ne 'present' -or $row.Driver.value -isnot [string] -or
                [string]::IsNullOrWhiteSpace($row.Driver.value)) { throw 'Driver mapping missing or unavailable.' }
            $row.driver_path = 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\' + $row.Driver.value
            $driver = Get-ItemProperty -LiteralPath $row.driver_path -ErrorAction Stop
            $row.capacity_raw = Field $driver 'HardwareInformation.qwMemorySize'
        } catch { $row.error = $_.Exception.Message; $row.error_id = $_.FullyQualifiedErrorId }
        [pscustomobject]$row
    })
    $pattern = '^luid_0x[0-9a-fA-F]{8}_0x[0-9a-fA-F]{8}_phys_0$'
    try {
        $gauges = @(Get-CimInstance Win32_PerfRawData_GPUPerformanceCounters_GPUAdapterMemory -ErrorAction Stop)
        $matching = @($gauges | Where-Object { $_.Name -match $pattern })
        $out.wddm = @{query='ok'; total=$gauges.Count; total_state=(Count-State $gauges.Count)
            expected_name_pattern=$pattern; matching=$matching.Count; matching_state=(Count-State $matching.Count)
            instances=@(foreach ($g in $gauges) {
                [pscustomobject]@{Name=(Field $g 'Name'); matches_pattern=($g.Name -match $pattern)
                    DedicatedUsage=(Field $g 'DedicatedUsage')}
            })}
    } catch { $out.wddm = @{query='unavailable'; error=$_.Exception.Message; error_id=$_.FullyQualifiedErrorId} }
    $out | ConvertTo-Json -Depth 10
}
