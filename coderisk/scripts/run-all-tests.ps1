param([string]$Python, [string]$JavaHome)
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot 'Dev-Common.ps1')

$root = Split-Path -Parent $PSScriptRoot

Push-Location $root
try {
    & (Join-Path $PSScriptRoot 'test-dev-scripts.ps1')
    $pythonExe = Get-DevPython $Python
    & $pythonExe -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw 'Python tests failed' }

    [void](Set-DevJava $JavaHome)
    Push-Location "$root\backend-springboot"
    try {
        mvn test
        if ($LASTEXITCODE -ne 0) { throw 'Backend tests failed' }
    } finally {
        Pop-Location
    }

    Push-Location "$root\frontend-vue"
    try {
        npm test
        if ($LASTEXITCODE -ne 0) { throw 'Frontend tests failed' }
        npm run build
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed' }
    } finally {
        Pop-Location
    }
} finally {
    Pop-Location
}
