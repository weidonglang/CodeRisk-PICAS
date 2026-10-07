$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
if ($env:JAVA_HOME) {
    $env:Path = "$env:JAVA_HOME\bin;$env:Path"
}
if (-not $env:CODERISK_UPLOAD_DIR) { $env:CODERISK_UPLOAD_DIR = Join-Path $root 'data/uploads' }
if (-not $env:CODERISK_ARTIFACT_DIR) { $env:CODERISK_ARTIFACT_DIR = Join-Path $root 'data/artifacts' }
if (-not $env:CODERISK_ANALYSIS_BASE_URL) { $env:CODERISK_ANALYSIS_BASE_URL = "http://localhost:8001" }
$env:SPRING_PROFILES_ACTIVE = if ($env:SPRING_PROFILES_ACTIVE) { $env:SPRING_PROFILES_ACTIVE } else { "local" }

Push-Location (Join-Path $root 'backend-springboot')
try {
    mvn spring-boot:run
    if ($LASTEXITCODE -ne 0) { throw 'Backend startup failed' }
} finally {
    Pop-Location
}
