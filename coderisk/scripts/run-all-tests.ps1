$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot

Push-Location $root
try {
    $venvPython = Join-Path $root 'analysis-service-python/.venv/Scripts/python.exe'
    $recoveryPython = Join-Path $root 'analysis-service-python/.venv-coderisk/Scripts/python.exe'
    $pythonExe = if ($env:CODERISK_PYTHON) { $env:CODERISK_PYTHON } elseif (Test-Path -LiteralPath $recoveryPython) { $recoveryPython } elseif (Test-Path -LiteralPath $venvPython) { $venvPython } else { 'python' }
    & $pythonExe -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw 'Python tests failed' }

    if ($env:JAVA_HOME) {
        $env:Path = "$env:JAVA_HOME\bin;$env:Path"
    }
    Push-Location "$root\backend-springboot"
    try {
        mvn test
        if ($LASTEXITCODE -ne 0) { throw 'Backend tests failed' }
    } finally {
        Pop-Location
    }

    Push-Location "$root\frontend-vue"
    try {
        npm run build
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed' }
    } finally {
        Pop-Location
    }
} finally {
    Pop-Location
}
