param(
    [string]$MysqlExe = "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe",
    [string]$DatabaseHost = "127.0.0.1",
    [int]$Port = 3306,
    [string]$Database = "coderisk",
    [string]$Username = $env:CODERISK_DB_USERNAME,
    [string]$Password = $env:CODERISK_DB_PASSWORD,
    [switch]$RequireMigratedSchema
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $MysqlExe -PathType Leaf)) {
    throw "mysql.exe not found: $MysqlExe"
}
if ([string]::IsNullOrWhiteSpace($Username) -or [string]::IsNullOrWhiteSpace($Password)) {
    throw "Set CODERISK_DB_USERNAME and CODERISK_DB_PASSWORD, or pass -Username and -Password. The password is not printed."
}
foreach ($value in @($Database, $Username)) {
    if ($value -notmatch "^[A-Za-z0-9_%-]+$") {
        throw "Database and username may contain only letters, digits, underscore, percent, and hyphen."
    }
}

$requiredTables = @(
    "question",
    "submission",
    "detection_task",
    "analysis_result",
    "similarity_metric",
    "evidence",
    "threshold_adjustment",
    "report_file",
    "flyway_schema_history"
)
$previousPassword = $env:MYSQL_PWD
try {
    $env:MYSQL_PWD = $Password
    $baseArguments = @(
        "--protocol=tcp",
        "--connect-timeout=5",
        "--host=$DatabaseHost",
        "--port=$Port",
        "--user=$Username",
        "--database=$Database",
        "--batch",
        "--skip-column-names"
    )
    $ErrorActionPreference = "Continue"
    $identity = & $MysqlExe @baseArguments --execute "SELECT VERSION(), DATABASE(), CURRENT_USER();" 2>&1
    $identityExitCode = $LASTEXITCODE
    $ErrorActionPreference = "Stop"
    if ($identityExitCode -ne 0) {
        throw "MySQL connection failed: $identity"
    }
    $ErrorActionPreference = "Continue"
    $tableRows = & $MysqlExe @baseArguments --execute "SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE();" 2>&1
    $tableExitCode = $LASTEXITCODE
    $ErrorActionPreference = "Stop"
    if ($tableExitCode -ne 0) {
        throw "MySQL schema inspection failed: $tableRows"
    }
    $tables = @($tableRows | ForEach-Object { $_.ToString().Trim() } | Where-Object { $_ })
    $missing = @($requiredTables | Where-Object { $_ -notin $tables })
    if ($RequireMigratedSchema -and $missing.Count -gt 0) {
        throw "MySQL is reachable but required migrated tables are missing: $($missing -join ', ')"
    }
    $parts = $identity.ToString().Split("`t")
    [PSCustomObject]@{
        status = "UP"
        serverVersion = $parts[0]
        database = $parts[1]
        currentUser = $parts[2]
        tableCount = $tables.Count
        missingRequiredTables = $missing
        migratedSchemaReady = $missing.Count -eq 0
    } | ConvertTo-Json -Depth 4
} finally {
    if ($null -eq $previousPassword) {
        Remove-Item Env:MYSQL_PWD -ErrorAction SilentlyContinue
    } else {
        $env:MYSQL_PWD = $previousPassword
    }
}
