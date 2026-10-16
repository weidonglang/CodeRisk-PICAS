$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Dev-Common.ps1')
$count = 0
function Assert-DevTest {
    param([bool]$Condition, [string]$Name)
    if (-not $Condition) { throw "FAIL: $Name" }
    $script:count++
    Write-Output "PASS: $Name"
}
foreach ($file in Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.ps1') {
    $tokens = $null; $errors = $null
    [void][Management.Automation.Language.Parser]::ParseFile($file.FullName, [ref]$tokens, [ref]$errors)
    Assert-DevTest ($errors.Count -eq 0) "PowerShell syntax: $($file.Name)"
}
$failed = $false
try { [void](Get-DevPython '__CODERISK_MISSING_PYTHON__.exe') } catch { $failed = $true }
Assert-DevTest $failed 'Explicit invalid Python does not silently select another runtime'
$failed = $false
try { [void](Get-DevTool '__CODERISK_MISSING_TOOL__.exe') } catch { $failed = $true }
Assert-DevTest $failed 'Missing tool fails before service startup'
$failed = $false
try { [void](Set-DevJava (Join-Path $PSScriptRoot '__MISSING_JDK__')) } catch { $failed = $true }
Assert-DevTest $failed 'Explicit invalid JDK does not silently select another version'
$listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, 0)
$listener.Start()
try {
    $port = $listener.LocalEndpoint.Port
    Assert-DevTest (-not (Test-DevPort $port)) 'Occupied port remains occupied'
    $failed = $false
    try { [void](Find-DevPort $port -Strict) } catch { $failed = $true }
    Assert-DevTest $failed 'Strict port refuses collisions without stopping an owner'
    if ($port -lt 65535) {
        Assert-DevTest ((Find-DevPort $port) -ne $port) 'Automatic port selection uses a different free port'
    } else {
        $failed = $false
        try { [void](Find-DevPort $port) } catch { $failed = $true }
        Assert-DevTest $failed 'Port selection refuses an occupied upper boundary'
    }
    Assert-DevTest (-not (Test-DevPort $port)) 'Original listener is still alive after port checks'
} finally { $listener.Stop() }
Assert-DevTest (-not (Test-DevProcess ([PSCustomObject]@{processId=$PID;startedAtUtc='1900-01-01';commandLineSha256='invalid'}))) 'Process identity mismatch is never treated as owned'
Assert-DevTest ((Get-DevCommandHash 'a') -ne (Get-DevCommandHash 'b')) 'Ownership command fingerprint differs'
$own = Get-Process -Id $PID
$native = Get-CimInstance Win32_Process -Filter "ProcessId = $PID" -ErrorAction Stop
$record = [PSCustomObject]@{processId=$PID;startedAtUtc=$own.StartTime.ToUniversalTime().ToString('o');commandLineSha256=(Get-DevCommandHash $native.CommandLine)}
Assert-DevTest (Test-DevProcess $record) 'Matching process identity accepts an ISO string timestamp'
$roundTrip = $record | ConvertTo-Json | ConvertFrom-Json
Assert-DevTest (Test-DevProcess $roundTrip) 'Ownership survives PowerShell JSON date conversion'
$roundTrip.commandLineSha256 = 'invalid'
Assert-DevTest (-not (Test-DevProcess $roundTrip)) 'Matching PID and date with wrong command is not owned'
$saved = @{}
foreach ($name in @('CODERISK_UPLOAD_DIR','CODERISK_ARTIFACT_DIR','CODERISK_LOCAL_DB_URL')) { $saved[$name] = [Environment]::GetEnvironmentVariable($name, 'Process') }
try {
    $dataRoot = Join-Path $script:CodeRiskWorkspace ('.tmp/dev-script-tests/' + [Guid]::NewGuid().ToString('N') + '/space root')
    $env:CODERISK_UPLOAD_DIR = 'OLD_PATH'
    Set-DevData $dataRoot
    Assert-DevTest ($env:CODERISK_UPLOAD_DIR -eq (Join-Path $dataRoot 'uploads')) 'Explicit data root overrides inherited upload location'
    Assert-DevTest ($env:CODERISK_ARTIFACT_DIR -eq (Join-Path $dataRoot 'artifacts')) 'Backend and analysis share explicit artifact root'
    Assert-DevTest ($env:CODERISK_LOCAL_DB_URL.Contains('space root/db/coderisk-local;')) 'H2 path preserves spaces'
    $failed = $false
    try { Set-DevData (Join-Path $dataRoot 'invalid;path') } catch { $failed = $true }
    Assert-DevTest $failed 'Ambiguous H2 path is rejected before file creation'
} finally { foreach ($name in $saved.Keys) { [Environment]::SetEnvironmentVariable($name, $saved[$name], 'Process') } }
$probe = Invoke-DevProbe (Get-DevTool 'powershell.exe') '-NoProfile -NonInteractive -Command "exit 7"'
Assert-DevTest ($probe.ExitCode -eq 7) 'Runtime probe preserves failure exit status'
Write-Output "$count dev-script checks passed"
