$script:CodeRiskRoot = Split-Path -Parent $PSScriptRoot
$script:CodeRiskWorkspace = Split-Path -Parent $script:CodeRiskRoot

function Invoke-DevProbe {
    param([string]$Executable, [string]$Arguments, [int]$TimeoutSeconds = 15)
    $info = New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName = $Executable
    $info.Arguments = $Arguments
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $info
    try {
        [void]$process.Start()
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit($TimeoutSeconds * 1000)) { $process.Kill(); throw 'Runtime probe timed out' }
        return [PSCustomObject]@{ ExitCode = $process.ExitCode; Output = $stdout.Result + $stderr.Result }
    } finally { $process.Dispose() }
}

function Get-DevTool {
    param([string]$Name)
    $tool = Get-Command $Name -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $tool) { throw "Missing $Name. Install its runtime or add it to PATH before starting CodeRisk." }
    return $tool.Source
}

function Get-DevPython {
    param([string]$Python)
    $explicit = if ($Python) { $Python } else { $env:CODERISK_PYTHON }
    $candidates = if ($explicit) { @($explicit) } else {
        @((Join-Path $script:CodeRiskRoot 'analysis-service-python/.venv-coderisk/Scripts/python.exe'),
          (Join-Path $script:CodeRiskRoot 'analysis-service-python/.venv/Scripts/python.exe'),
          (Join-Path $script:CodeRiskWorkspace '.tmp/language-venv/Scripts/python.exe'), 'python.exe')
    }
    foreach ($candidate in $candidates) {
        try {
            $command = Get-Command $candidate -ErrorAction Stop | Select-Object -First 1
            $probe = Invoke-DevProbe $command.Source '-c "import sys, fastapi, uvicorn, tree_sitter; assert sys.version_info >= (3, 11); print(sys.executable)"'
            if ($probe.ExitCode -eq 0) { return $command.Source }
        } catch { }
    }
    throw 'No working Python 3.11+ with FastAPI, uvicorn and tree-sitter. Set CODERISK_PYTHON or use -Python. Install the analysis-service-python dev dependencies in that environment; nothing is installed automatically.'
}

function Set-DevJava {
    param([string]$JavaHome)
    $explicit = if ($JavaHome) { $JavaHome } else { $env:CODERISK_JAVA_HOME }
    $candidates = @()
    if ($explicit) {
        $candidates = @($explicit)
    } else {
        if ($env:JAVA_HOME) { $candidates += $env:JAVA_HOME }
        $javac = Get-Command 'javac.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($javac) { $candidates += (Split-Path -Parent (Split-Path -Parent $javac.Source)) }
        $roots = @()
        foreach ($candidate in @($candidates)) {
            $manager = Split-Path -Parent (Split-Path -Parent $candidate)
            if ($manager) { $roots += (Join-Path $manager 'envs/jdks') }
        }
        if ($env:ProgramFiles) { $roots += (Join-Path $env:ProgramFiles 'Eclipse Adoptium'); $roots += (Join-Path $env:ProgramFiles 'Java') }
        foreach ($folder in ($roots | Select-Object -Unique)) {
            if (Test-Path -LiteralPath $folder) {
                $candidates += @(Get-ChildItem -LiteralPath $folder -Directory -ErrorAction SilentlyContinue | Sort-Object Name | ForEach-Object { $_.FullName })
            }
        }
    }
    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        $compiler = Join-Path $candidate 'bin/javac.exe'
        if (-not (Test-Path -LiteralPath $compiler)) { continue }
        try {
            $probe = Invoke-DevProbe (Join-Path $candidate 'bin/java.exe') '--version'
            $version = [regex]::Match($probe.Output, '(?:openjdk|java)\s+(\d+)')
            if ($probe.ExitCode -eq 0 -and $version.Success -and [int]$version.Groups[1].Value -ge 21) {
                if (-not $explicit -and $env:JAVA_HOME -and $candidate -ne $env:JAVA_HOME) {
                    Write-Host "Project JDK selected: $candidate (inherited JAVA_HOME is not suitable; machine settings unchanged)."
                }
                $env:JAVA_HOME = [IO.Path]::GetFullPath($candidate)
                $env:Path = "$env:JAVA_HOME\bin;$env:Path"
                return $env:JAVA_HOME
            }
        } catch { }
    }
    throw 'No suitable JDK 21+. Use -JavaHome or CODERISK_JAVA_HOME; no machine environment was changed.'
}

function Set-DevData {
    param([string]$DataRoot)
    $data = if ($DataRoot) { [IO.Path]::GetFullPath($DataRoot) } else { Join-Path $script:CodeRiskRoot 'data' }
    if ($data.Contains(';')) { throw 'DataRoot cannot contain a semicolon because it is used in an H2 file URL.' }
    if ($DataRoot -or -not $env:CODERISK_UPLOAD_DIR) { $env:CODERISK_UPLOAD_DIR = Join-Path $data 'uploads' }
    if ($DataRoot -or -not $env:CODERISK_ARTIFACT_DIR) { $env:CODERISK_ARTIFACT_DIR = Join-Path $data 'artifacts' }
    foreach ($folder in @($env:CODERISK_UPLOAD_DIR, $env:CODERISK_ARTIFACT_DIR)) {
        [void](New-Item -ItemType Directory -Force -Path $folder)
    }
    if ($DataRoot) {
        [void](New-Item -ItemType Directory -Force -Path (Join-Path $data 'db'))
        $db = (Join-Path $data 'db/coderisk-local').Replace('\', '/')
        $env:CODERISK_LOCAL_DB_URL = "jdbc:h2:file:$db;MODE=MySQL;DATABASE_TO_LOWER=TRUE;CASE_INSENSITIVE_IDENTIFIERS=TRUE;AUTO_SERVER=TRUE"
    }
}

function Test-DevPort {
    param([int]$Port)
    $listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, $Port)
    try { $listener.Start(); return $true } catch { return $false } finally { $listener.Stop() }
}

function Find-DevPort {
    param([int]$Preferred, [int[]]$Exclude = @(), [switch]$Strict)
    $last = if ($Strict) { $Preferred } else { [Math]::Min(65535, $Preferred + 30) }
    for ($candidate = $Preferred; $candidate -le $last; $candidate++) {
        if ($candidate -notin $Exclude -and (Test-DevPort $candidate)) { return $candidate }
    }
    throw "Port $Preferred is occupied or unavailable. No existing process was stopped. Select another port."
}

function Get-DevCommandHash {
    param([string]$CommandLine)
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($CommandLine)))).Replace('-', '').ToLowerInvariant() } finally { $sha.Dispose() }
}

function Test-DevProcess {
    param($Record)
    $process = Get-Process -Id $Record.processId -ErrorAction SilentlyContinue
    if (-not $process) { return $false }
    try {
        $recordedTime = if ($Record.startedAtUtc -is [DateTime]) { $Record.startedAtUtc.ToUniversalTime() }
            elseif ($Record.startedAtUtc -is [DateTimeOffset]) { $Record.startedAtUtc.UtcDateTime }
            else { [DateTime]::Parse([string]$Record.startedAtUtc, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::RoundtripKind).ToUniversalTime() }
        if ($process.StartTime.ToUniversalTime().Ticks -ne $recordedTime.Ticks) { return $false }
    } catch { return $false }
    $native = Get-CimInstance Win32_Process -Filter "ProcessId = $($Record.processId)" -ErrorAction Stop
    return $native -and (Get-DevCommandHash $native.CommandLine) -eq $Record.commandLineSha256
}

function Stop-DevProcess {
    param($Record)
    if (Test-DevProcess $Record) {
        & taskkill.exe /PID $Record.processId /T /F | Out-Null
        if ($LASTEXITCODE -ne 0 -and (Test-DevProcess $Record)) { throw "Could not stop managed $($Record.role) process" }
    }
}

function Wait-DevService {
    param([string]$Url, [string]$Role, $Record, [int]$TimeoutSeconds = 180)
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        if (-not (Get-Process -Id $Record.processId -ErrorAction SilentlyContinue)) { throw "$Role exited before ready. See $($Record.stderr) and $($Record.stdout)" }
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2
            if ($Role -eq 'frontend') {
                if ($response.Content -match '<div id="app">') { return }
            } else {
                $body = $response.Content | ConvertFrom-Json
                $expected = if ($Role -eq 'analysis') { 'coderisk-analysis-service' } else { 'coderisk-backend' }
                $data = if ($Role -eq 'analysis') { $body.result } else { $body.data }
                if ($body.success -and $data.status -eq 'UP' -and $data.service -eq $expected) { return }
            }
        } catch { }
        Start-Sleep -Milliseconds 350
    }
    throw "$Role did not become ready at $Url. See $($Record.stderr) and $($Record.stdout)"
}
