# Ejecuta dbt con las credenciales de .env cargadas solo en este proceso (sin mostrarlas).
# Uso: .\scripts\dbt.ps1 build      ·      .\scripts\dbt.ps1 docs generate
param([Parameter(ValueFromRemainingArguments = $true)] [string[]] $Argumentos)

$proyecto = Split-Path $PSScriptRoot -Parent
foreach ($linea in Get-Content (Join-Path $proyecto '.env')) {
    if ($linea -match '^\s*([A-Z_]+)\s*=\s*(.*?)\s*$' -and $linea -notmatch '^\s*#') {
        Set-Item -Path "env:$($Matches[1])" -Value $Matches[2]
    }
}
$env:DBT_TARGET = 'prod'
Push-Location (Join-Path $proyecto 'dbt')
try {
    & (Join-Path $proyecto '.venv\Scripts\dbt.exe') @Argumentos --profiles-dir .
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
