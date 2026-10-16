param([ValidateRange(1,65535)][int]$Port = 5173, [string]$ApiBaseUrl, [switch]$CheckOnly)
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot 'Dev-Common.ps1')
$npm = Get-DevTool 'npm.cmd'
$node = Get-DevTool 'node.exe'
if (-not (Test-Path -LiteralPath (Join-Path $script:CodeRiskRoot 'frontend-vue/node_modules/vite/bin/vite.js'))) { throw 'Frontend dependencies missing. Run npm --prefix coderisk/frontend-vue ci first.' }
if ($CheckOnly) { Write-Output "Frontend runtime ready: $node; $npm"; return }
if (-not (Test-DevPort $Port)) { throw "Frontend port $Port is occupied; no process was stopped." }
if ($ApiBaseUrl) { $env:VITE_API_BASE_URL = $ApiBaseUrl }

$root = Split-Path -Parent $PSScriptRoot
Push-Location (Join-Path $root 'frontend-vue')
try {
    & $npm run dev -- --host 127.0.0.1 --port $Port --strictPort
    if ($LASTEXITCODE -ne 0) { throw 'Frontend startup failed' }
} finally {
    Pop-Location
}
