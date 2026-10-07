$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Push-Location (Join-Path $root 'frontend-vue')
try {
    npm run dev -- --host 127.0.0.1 --port 5173
    if ($LASTEXITCODE -ne 0) { throw 'Frontend startup failed' }
} finally {
    Pop-Location
}
