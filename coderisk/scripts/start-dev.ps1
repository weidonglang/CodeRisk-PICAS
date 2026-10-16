param([ValidateRange(1,65535)][int]$FrontendPort = 5173, [ValidateRange(1,65535)][int]$BackendPort = 8080,
      [ValidateRange(1,65535)][int]$AnalysisPort = 8001, [ValidateSet('local','mysql')][string]$Profile = 'local',
      [string]$Python, [string]$JavaHome, [string]$DataRoot, [switch]$CheckOnly, [switch]$StrictPorts,
      [ValidateRange(5,600)][int]$StartupTimeoutSeconds = 180)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Dev-Common.ps1')

$pythonExe = Get-DevPython $Python
$jdk = Set-DevJava $JavaHome
[void](Get-DevTool 'mvn.cmd')
[void](Get-DevTool 'npm.cmd')
[void](Get-DevTool 'node.exe')
if (-not (Test-Path -LiteralPath (Join-Path $script:CodeRiskRoot 'frontend-vue/node_modules/vite/bin/vite.js'))) { throw 'Run npm --prefix coderisk/frontend-vue ci before starting.' }
$controlRoot = Join-Path $script:CodeRiskWorkspace '.tmp/coderisk-dev'
$currentFile = Join-Path $controlRoot 'current.json'
if (-not $CheckOnly -and (Test-Path -LiteralPath $currentFile)) {
    $previous = Get-Content -LiteralPath $currentFile -Raw | ConvertFrom-Json
    if ($previous.schemaVersion -ne 1 -or $previous.coderiskRoot -ne $script:CodeRiskRoot) { throw 'Unrecognized dev session metadata; no process was modified.' }
    $alive = @($previous.processes | Where-Object { Test-DevProcess $_ })
    if ($alive.Count) {
        if ($alive.Count -eq 3) {
            if ($previous.profile -ne $Profile) { throw 'An existing managed session uses another database profile. Stop it before changing profile; no service was changed.' }
            Write-Output "Already running: $($previous.frontendUrl)`nProfile: $($previous.profile) (existing settings retained; stop before changing configuration)`nSession: $($previous.sessionDirectory)"
            return
        }
        throw 'A partial managed session is still running. Run stop-dev.ps1 first; no existing process was stopped.'
    }
}
$analysis = Find-DevPort $AnalysisPort -Strict:$StrictPorts
$backend = Find-DevPort $BackendPort -Exclude @($analysis) -Strict:$StrictPorts
$frontend = Find-DevPort $FrontendPort -Exclude @($analysis, $backend) -Strict:$StrictPorts
if ($CheckOnly) {
    [PSCustomObject]@{ Python=$pythonExe; JavaHome=$jdk; Profile=$Profile; AnalysisPort=$analysis; BackendPort=$backend; FrontendPort=$frontend; StartsServices=$false }
    return
}
[void](Get-CimInstance Win32_Process -Filter "ProcessId = $PID" -ErrorAction Stop)
$sessionId = [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,8)
$sessionDirectory = Join-Path $controlRoot "sessions/$sessionId"
[void](New-Item -ItemType Directory -Path $sessionDirectory -Force)
$session = [PSCustomObject]@{ schemaVersion=1; coderiskRoot=$script:CodeRiskRoot; sessionDirectory=$sessionDirectory;
    frontendUrl="http://127.0.0.1:$frontend"; backendUrl="http://127.0.0.1:$backend"; analysisUrl="http://127.0.0.1:$analysis";
    profile=$Profile; status='STARTING'; processes=@() }
function Save-Session {
    $session | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $sessionDirectory 'session.json') -Encoding UTF8
    $session | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $currentFile -Encoding UTF8
}
function Start-Component {
    param([string]$Role, [string]$ScriptName, [hashtable]$Arguments)
    $command = "# CODERISK_MANAGED:$sessionId`n& '" + (Join-Path $PSScriptRoot $ScriptName).Replace("'", "''") + "'"
    foreach ($key in $Arguments.Keys) { $command += " -$key '" + ([string]$Arguments[$key]).Replace("'", "''") + "'" }
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($command))
    $out = Join-Path $sessionDirectory "$Role.out.log"
    $err = Join-Path $sessionDirectory "$Role.err.log"
    $process = Start-Process -FilePath (Get-DevTool 'powershell.exe') -ArgumentList @('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-EncodedCommand',$encoded) -WorkingDirectory $script:CodeRiskWorkspace -WindowStyle Hidden -RedirectStandardOutput $out -RedirectStandardError $err -PassThru
    $native = Get-CimInstance Win32_Process -Filter "ProcessId = $($process.Id)" -ErrorAction Stop
    if (-not $native) { throw "$Role exited immediately. See $err" }
    $record = [PSCustomObject]@{ role=$Role; processId=$process.Id; startedAtUtc=$process.StartTime.ToUniversalTime().ToString('o'); commandLineSha256=(Get-DevCommandHash $native.CommandLine); stdout=$out; stderr=$err }
    $session.processes += $record
    Save-Session
    return $record
}
Save-Session
try {
    Write-Output '1/3 Starting analysis service...'
    $record = Start-Component 'analysis' 'start-analysis-dev.ps1' @{Port=$analysis; Python=$pythonExe; DataRoot=$DataRoot}
    Wait-DevService "$($session.analysisUrl)/internal/health" 'analysis' $record $StartupTimeoutSeconds
    $env:CODERISK_ANALYSIS_BASE_URL = $session.analysisUrl
    Write-Output '2/3 Starting backend and existing database migrations...'
    $record = Start-Component 'backend' 'start-backend-dev.ps1' @{Port=$backend; Profile=$Profile; JavaHome=$jdk; DataRoot=$DataRoot}
    Wait-DevService "$($session.backendUrl)/api/system/health" 'backend' $record $StartupTimeoutSeconds
    Write-Output '3/3 Starting frontend...'
    $record = Start-Component 'frontend' 'start-frontend-dev.ps1' @{Port=$frontend; ApiBaseUrl=$session.backendUrl}
    Wait-DevService $session.frontendUrl 'frontend' $record $StartupTimeoutSeconds
    $session.status = 'READY'
    Save-Session
    Write-Output "CodeRisk ready: $($session.frontendUrl)`nBackend: $($session.backendUrl)`nAnalysis: $($session.analysisUrl)`nDatabase profile: $Profile`nLogs: $sessionDirectory`nStop: .\coderisk\scripts\stop-dev.ps1"
} catch {
    $session.status = 'FAILED'
    Save-Session
    for ($i=$session.processes.Count-1; $i -ge 0; $i--) {
        try { Stop-DevProcess $session.processes[$i] } catch { Write-Warning "Managed cleanup failed; see $sessionDirectory" }
    }
    throw
}
