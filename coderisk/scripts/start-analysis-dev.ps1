$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
if (-not $env:CODERISK_UPLOAD_DIR) { $env:CODERISK_UPLOAD_DIR = Join-Path $root 'data/uploads' }
if (-not $env:CODERISK_ARTIFACT_DIR) { $env:CODERISK_ARTIFACT_DIR = Join-Path $root 'data/artifacts' }
$venvPython = Join-Path $root 'analysis-service-python/.venv/Scripts/python.exe'
$pythonExe = if (Test-Path -LiteralPath $venvPython) { $venvPython } else { 'python' }

Push-Location (Join-Path $root 'analysis-service-python')
try {
    & $pythonExe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
    if ($LASTEXITCODE -ne 0) { throw 'Analysis service startup failed' }
} finally {
    Pop-Location
}
