<#
.SYNOPSIS
  Backup Chroma named Docker volume to a gzipped tar file in the project backups folder.

USAGE
  .\backup_chroma.ps1

Notes:
 - Default volume name: acebuddy_chroma_data (change below if you used a different name)
 - This script runs an ephemeral Alpine container to tar the volume contents.
#>
param(
  [string]$VolumeName = 'chroma_data',
  [string]$OutDir = "$PSScriptRoot\..\backups"
)

if (-not (Test-Path -Path $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir | Out-Null
}

$timestamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
$backupFile = Join-Path $OutDir "chroma_backup_$timestamp.tar.gz"

Write-Host "Creating backup of volume '$VolumeName' to '$backupFile'..."

$pwdWin = (Get-Location).Path

docker run --rm -v ${VolumeName}:/data -v ${pwdWin}:/backup alpine sh -c "tar czf /backup/" + [System.IO.Path]::GetFileName($backupFile) + " -C /data ." | Out-Null

if (Test-Path $backupFile) {
    Write-Host "Backup saved to: $backupFile"
} else {
    Write-Error "Backup failed - file not found: $backupFile"
}

Write-Host "Optional: copy backup to external storage (S3, Azure blob) for long-term retention."
