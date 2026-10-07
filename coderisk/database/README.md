# Database

The backend uses JDBC and Flyway. The production datasource is MySQL 8; the `local` profile uses an H2 file database in MySQL compatibility mode so local development remains runnable without database credentials.

Migrations:

```text
backend-springboot/src/main/resources/db/migration/V1__coderisk_core.sql
backend-springboot/src/main/resources/db/migration/V2__v4_ready_consistency.sql
```

Initialize a local MySQL development database with an administrative account:

```powershell
Get-Content database\init_mysql.sql -Raw | mysql -u root -p
```

Then run the backend with:

```powershell
$env:SPRING_PROFILES_ACTIVE = "mysql"
$env:CODERISK_DB_URL = "jdbc:mysql://127.0.0.1:3306/coderisk?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai&useSSL=false"
$env:CODERISK_DB_USERNAME = "coderisk"
$env:CODERISK_DB_PASSWORD = "coderisk"
.\scripts\start-backend-dev.ps1
```

Flyway creates and validates the tables automatically. Change the example password outside local development.

Verify connectivity and the migrated core tables without exposing the password on the command line:

```powershell
$env:CODERISK_DB_USERNAME = "coderisk"
$env:CODERISK_DB_PASSWORD = "<local password>"
.\scripts\verify-mysql.ps1 -RequireMigratedSchema
```

`init_mysql.sql` is for local development. It resets the example `coderisk` account password on rerun and grants only schema-level privileges needed by the application/Flyway; use a secret-managed password and narrower deployment process outside local development.

## Profile Switch

H2 fallback:

```powershell
$env:SPRING_PROFILES_ACTIVE = "local"
$env:CODERISK_LOCAL_DB_URL = "jdbc:h2:file:E:/ms/coderisk/data/db/coderisk-local;MODE=MySQL;DATABASE_TO_LOWER=TRUE;CASE_INSENSITIVE_IDENTIFIERS=TRUE;AUTO_SERVER=TRUE"
.\scripts\start-backend-dev.ps1
```

MySQL 8:

```powershell
$env:SPRING_PROFILES_ACTIVE = "mysql"
$env:CODERISK_DB_USERNAME = "coderisk"
$env:CODERISK_DB_PASSWORD = "<local password>"
.\scripts\start-backend-dev.ps1
```

## Connection Troubleshooting

- `Access denied`: verify the account host (`localhost` versus `%`), password, and grants with an administrative account.
- `Unknown database`: run `database/init_mysql.sql` with an administrative account.
- `Public Key Retrieval is not allowed`: retain `allowPublicKeyRetrieval=true` for local development or configure TLS for deployment.
- `Communications link failure`: check `Get-Service MySQL80`, port 3306, bind address, and firewall rules.
- Flyway checksum mismatch: never edit an already-applied migration; add a new numbered migration. Use `flyway_schema_history` to identify the applied version.
- H2 file lock: stop duplicate backend processes or use a different `CODERISK_LOCAL_DB_URL` for isolated tests.

Current verification on 2026-06-21: MySQL 8.0.42 service is running and reachable, but no credential is present in the environment; example `coderisk/coderisk` and passwordless `root` are rejected with error 1045. The verification script and deterministic initialization/permission instructions are complete. H2 MySQL-compatibility mode remains the verified fallback; MySQL live E2E is pending a valid administrative or application credential.
