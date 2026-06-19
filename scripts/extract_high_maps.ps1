param(
    [int]$From = 41,
    [int]$To = 50
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
node (Join-Path $Root "scripts\extract_high_maps_cdp.js") $From $To
