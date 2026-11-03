# SmartCafe - restore a backup made by scripts\backup_db.ps1 (NFR-R5).
# WARNING: replaces all data of the target database.
# Usage:  powershell -ExecutionPolicy Bypass -File scripts\restore_db.ps1 -File backups\smartcafe_20261103_180000.dump
#         (add -DbName other_db to restore into another database, e.g. to check a backup)
param(
    [Parameter(Mandatory = $true)][string]$File,
    [string]$DbUser = "smartcafe",
    [string]$DbName = "smartcafe"
)
$ErrorActionPreference = "Stop"
$full = (Resolve-Path $File).Path
Set-Location (Join-Path $PSScriptRoot "..")

docker compose cp $full db:/tmp/restore.dump
if ($LASTEXITCODE -ne 0) { throw "docker compose cp failed" }
# create the target database if it does not exist yet (ignore "already exists")
docker compose exec -T db sh -c "createdb -U $DbUser $DbName 2>/dev/null || true"
docker compose exec -T db pg_restore -U $DbUser -d $DbName --clean --if-exists --no-owner /tmp/restore.dump
if ($LASTEXITCODE -ne 0) { throw "pg_restore failed" }
docker compose exec -T db rm -f /tmp/restore.dump | Out-Null
Write-Output "RESTORE_OK $DbName"
if ($DbName -eq "smartcafe") { Write-Output "Restart backend: docker compose restart backend" }
