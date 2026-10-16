param([ValidateRange(1,65535)][int]$Port = 8001, [string]$Python, [string]$DataRoot, [switch]$CheckOnly)
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot 'Dev-Common.ps1')
$pythonExe = Get-DevPython $Python
if ($CheckOnly) { Write-Output "Analysis runtime ready: $pythonExe"; return }
if (-not (Test-DevPort $Port)) { throw "Analysis port $Port is occupied; no process was stopped." }
Set-DevData $DataRoot
$env:PYTHONUTF8 = '1'

$root = Split-Path -Parent $PSScriptRoot
if (-not $env:CODERISK_UPLOAD_DIR) { $env:CODERISK_UPLOAD_DIR = Join-Path $root 'data/uploads' }
if (-not $env:CODERISK_ARTIFACT_DIR) { $env:CODERISK_ARTIFACT_DIR = Join-Path $root 'data/artifacts' }

Push-Location (Join-Path $root 'analysis-service-python')
try {
    & $pythonExe -m uvicorn app.main:app --host 127.0.0.1 --port $Port
    if ($LASTEXITCODE -ne 0) { throw 'Analysis service startup failed' }
} finally {
    Pop-Location
}
