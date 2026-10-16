param([string]$SessionDirectory)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Dev-Common.ps1')
$controlRoot = Join-Path $script:CodeRiskWorkspace '.tmp/coderisk-dev'
$file = if ($SessionDirectory) { Join-Path ([IO.Path]::GetFullPath($SessionDirectory)) 'session.json' } else { Join-Path $controlRoot 'current.json' }
if (-not (Test-Path -LiteralPath $file)) { Write-Output 'No managed dev session. Nothing was stopped.'; return }
$session = Get-Content -LiteralPath $file -Raw | ConvertFrom-Json
$resolved = [IO.Path]::GetFullPath($session.sessionDirectory)
$allowed = [IO.Path]::GetFullPath((Join-Path $controlRoot 'sessions')) + [IO.Path]::DirectorySeparatorChar
if ($session.schemaVersion -ne 1 -or $session.coderiskRoot -ne $script:CodeRiskRoot -or -not $resolved.StartsWith($allowed, [StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid managed session path or metadata. No process was stopped.' }
for ($i=$session.processes.Count-1; $i -ge 0; $i--) { Stop-DevProcess $session.processes[$i] }
$session.status = 'STOPPED'
$session | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $resolved 'session.json') -Encoding UTF8
if (-not $SessionDirectory) { $session | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $file -Encoding UTF8 }
Write-Output 'Managed dev processes stopped. Data and logs were preserved. Unrelated processes were not stopped.'
