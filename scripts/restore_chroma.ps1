<#
.SYNOPSIS
  Restore a Chroma backup tar.gz into a named Docker volume.

USAGE
  .\restore_chroma.ps1 -BackupFile .\backups\chroma_backup_20251111_120000.tar.gz

Notes:
 - The script creates the target volume if it doesn't exist.
#>
param(
    [Parameter(Mandatory=$true)]
    [string]$BackupFile,
  [string]$TargetVolume = 'chroma_data'
)

if (-not (Test-Path $BackupFile)) {
    Write-Error "Backup file not found: $BackupFile"
    exit 1
}

Write-Host "Restoring $BackupFile into Docker volume '$TargetVolume'..."

# Create volume if missing
docker volume inspect $TargetVolume 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating volume: $TargetVolume"
    docker volume create $TargetVolume | Out-Null
}

$pwdWin = (Get-Location).Path

docker run --rm -v ${TargetVolume}:/data -v ${pwdWin}:/backup alpine sh -c "tar xzf /backup/$(Split-Path -Leaf $BackupFile) -C /data"

Write-Host "Restore complete. Restart Chroma container to use restored data."
