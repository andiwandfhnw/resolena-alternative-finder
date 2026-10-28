Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$listener=$null;$key=$null
try {
    $key=[Console]::ReadLine()
    if ($null -eq $key -or $key.Length -lt 32) {throw 'Ephemeral test key absent.'}
    $clock=[Diagnostics.Stopwatch]::StartNew()
    $listener=[Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,49187)
    $listener.Start(1)
    for ($requestIndex=0;$requestIndex -lt 3;$requestIndex++) {
        while (-not $listener.Pending()) {
            if ($clock.ElapsedMilliseconds -ge 45000) {throw 'Model-free endpoint deadline expired.'}
            Start-Sleep -Milliseconds 50
        }
        $connection=$listener.AcceptTcpClient()
        $reader=$null;$writer=$null
        try {
            $stream=$connection.GetStream();$stream.ReadTimeout=2000;$stream.WriteTimeout=2000
            $reader=[IO.StreamReader]::new($stream,[Text.Encoding]::ASCII,$false,1024,$true)
            $writer=[IO.StreamWriter]::new($stream,[Text.Encoding]::ASCII,1024,$true)
            if ($reader.ReadLine() -ne 'GET /probe HTTP/1.1') {throw 'Unexpected test request.'}
            $authorization=$null;$complete=$false
            for ($lineIndex=0;$lineIndex -lt 64;$lineIndex++) {
                $line=$reader.ReadLine()
                if ($null -eq $line) {throw 'Incomplete test request.'}
                if ($line.Length -eq 0) {$complete=$true;break}
                if ($line.StartsWith('Authorization:',[StringComparison]::OrdinalIgnoreCase)) {
                    if ($null -ne $authorization) {throw 'Duplicate test authorization.'}
                    $authorization=$line.Substring(14).Trim()
                }
            }
            if (-not $complete) {throw 'Oversized test headers.'}
            $right=[string]::Equals($authorization,('Bearer '+$key),[StringComparison]::Ordinal)
            $status=$(if($right){'200 OK'}else{'401 Unauthorized'})
            $body=$(if($right){"uc001-model-free-transport`n"}else{"unauthorized`n"})
            $writer.Write("HTTP/1.1 $status`r`nConnection: close`r`nContent-Length: $([Text.Encoding]::ASCII.GetByteCount($body))`r`n`r`n$body")
            $writer.Flush()
        } finally {
            if ($null -ne $writer) {$writer.Dispose()}
            if ($null -ne $reader) {$reader.Dispose()}
            $connection.Dispose()
        }
    }
} finally {if ($null -ne $listener) {$listener.Stop()};$key=$null}
