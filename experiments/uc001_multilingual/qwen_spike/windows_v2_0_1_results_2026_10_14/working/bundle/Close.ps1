param([Parameter(Mandatory=$true)][string]$Root)
. (Join-Path $PSScriptRoot 'Common.ps1')
Close-Run ([IO.Path]::GetFullPath($Root).TrimEnd('\'))
