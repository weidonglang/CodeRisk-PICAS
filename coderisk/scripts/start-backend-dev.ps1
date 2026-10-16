param([ValidateRange(1,65535)][int]$Port = 8080, [ValidateSet('local','mysql')][string]$Profile,
      [string]$JavaHome, [string]$DataRoot, [switch]$CheckOnly)
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot 'Dev-Common.ps1')
if (-not $PSBoundParameters.ContainsKey('Port') -and $env:CODERISK_BACKEND_PORT) {
    $Port = [int]$env:CODERISK_BACKEND_PORT
    if ($Port -lt 1 -or $Port -gt 65535) { throw 'CODERISK_BACKEND_PORT must be between 1 and 65535.' }
}
$jdk = Set-DevJava $JavaHome
$maven = Get-DevTool 'mvn.cmd'
if ($CheckOnly) { Write-Output "Backend runtime ready: $jdk; $maven"; return }
if (-not (Test-DevPort $Port)) { throw "Backend port $Port is occupied; no process was stopped." }
Set-DevData $DataRoot
$env:CODERISK_BACKEND_PORT = "$Port"
if (-not $env:SERVER_ADDRESS) { $env:SERVER_ADDRESS = '127.0.0.1' }

$root = Split-Path -Parent $PSScriptRoot
if ($env:JAVA_HOME) {
    $env:Path = "$env:JAVA_HOME\bin;$env:Path"
}
if (-not $env:CODERISK_UPLOAD_DIR) { $env:CODERISK_UPLOAD_DIR = Join-Path $root 'data/uploads' }
if (-not $env:CODERISK_ARTIFACT_DIR) { $env:CODERISK_ARTIFACT_DIR = Join-Path $root 'data/artifacts' }
if (-not $env:CODERISK_ANALYSIS_BASE_URL) { $env:CODERISK_ANALYSIS_BASE_URL = "http://localhost:8001" }
$env:SPRING_PROFILES_ACTIVE = if ($Profile) { $Profile } elseif ($env:SPRING_PROFILES_ACTIVE) { $env:SPRING_PROFILES_ACTIVE } else { "local" }
Write-Output "Starting CodeRisk backend: profile=$env:SPRING_PROFILES_ACTIVE; port=$Port"
if ($env:SPRING_PROFILES_ACTIVE -eq 'local') { Write-Output 'Database: H2 local profile, not MySQL verification.' }

Push-Location (Join-Path $root 'backend-springboot')
try {
    & $maven spring-boot:run
    if ($LASTEXITCODE -ne 0) { throw 'Backend startup failed' }
} finally {
    Pop-Location
}
