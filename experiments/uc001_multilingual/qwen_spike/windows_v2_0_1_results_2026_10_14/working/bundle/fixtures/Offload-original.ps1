param([string]$Text)
    $matches = [regex]::Matches($Text, 'offloaded (\d+)/(\d+) layers to GPU')
    if ($matches.Count -eq 0 -or $Text -notmatch 'Vulkan0.*RX\s*6800\s*XT' -or $Text -notmatch 'Vulkan0.*model buffer size') { return $false }
    $kv = [regex]::Match($Text, 'Vulkan0.*KV buffer size\s*=\s*([0-9.]+)\s*MiB')
    if (-not $kv.Success -or [double]::Parse($kv.Groups[1].Value, [Globalization.CultureInfo]::InvariantCulture) -le 0) { return $false }
    foreach ($match in $matches) {
        if ([int]$match.Groups[1].Value -le 0 -or [int]$match.Groups[1].Value -ne [int]$match.Groups[2].Value) { return $false }
    }
    return $true
