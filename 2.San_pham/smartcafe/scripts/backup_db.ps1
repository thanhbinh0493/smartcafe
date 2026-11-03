# SmartCafe - backup the PostgreSQL database before each demo (NFR-R5).
# Usage (from 2.San_pham/smartcafe):  powershell -ExecutionPolicy Bypass -File scripts\backup_db.ps1
# Output: backups\smartcafe_YYYYMMDD_HHMMSS.dump (pg_dump custom format, restore with scripts\restore_db.ps1)
param(
    [string]$OutDir = (Join-Path $PSScriptRoot "..\backups"),
    [string]$DbUser = "smartcafe",
    [string]$DbName = "smartcafe"
)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
New-Item -ItemType Directory -Force $OutDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$file = Join-Path (Resolve-Path $OutDir) "smartcafe_$stamp.dump"

# Dump inside the container then copy out (PowerShell redirection would corrupt binary output)
docker compose exec -T db pg_dump -U $DbUser -d $DbName -Fc -f /tmp/backup.dump
if ($LASTEXITCODE -ne 0) { throw "pg_dump failed" }
docker compose cp db:/tmp/backup.dump $file
if ($LASTEXITCODE -ne 0) { throw "docker compose cp failed" }
docker compose exec -T db rm -f /tmp/backup.dump | Out-Null

$size = (Get-Item $file).Length
Write-Output "BACKUP_OK $file $size"
