<#
collect_docker_diagnostics.ps1
Collects WSL, Docker and Docker Desktop diagnostics into a timestamped folder and zips it.
Run as Administrator from project root:
    powershell -ExecutionPolicy Bypass -File .\collect_docker_diagnostics.ps1
#>

function Ensure-Admin {
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
    if (-not $isAdmin) {
        Write-Error "This script must be run as Administrator. Right-click PowerShell and choose 'Run as Administrator'."
        exit 1
    }
}

Ensure-Admin

$timestamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
$outDir = Join-Path -Path $PSScriptRoot -ChildPath "diagnostics_$timestamp"
New-Item -Path $outDir -ItemType Directory -Force | Out-Null

# Helper to run and save outputs
function Save-Output {
    param($FileName, $ScriptBlock)
    $outFile = Join-Path $outDir $FileName
    try {
        & $ScriptBlock *>&1 | Out-File -FilePath $outFile -Encoding UTF8 -Width 4096
    } catch {
        "Error running $($ScriptBlock) : $_" | Out-File -FilePath $outFile -Encoding UTF8
    }
}

Write-Host "Collecting WSL status..."
Save-Output -FileName "wsl_status.txt" -ScriptBlock { wsl --status }
Save-Output -FileName "wsl_list_verbose.txt" -ScriptBlock { wsl --list --verbose }

Write-Host "Collecting Windows services related to Docker..."
Save-Output -FileName "services_docker.txt" -ScriptBlock { Get-Service *docker* | Format-List * }

Write-Host "Collecting Docker Desktop processes..."
Save-Output -FileName "processes_docker.txt" -ScriptBlock { Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'Docker|com.docker' } | Format-List * }

Write-Host "Attempting docker CLI queries (may fail if engine not reachable)..."
Save-Output -FileName "docker_version.txt" -ScriptBlock { docker version --format '{{json .}}' }
Save-Output -FileName "docker_info.txt" -ScriptBlock { docker info --format '{{json .}}' }

Write-Host "Collecting Docker Desktop logs (if present)..."
$localLog = Join-Path $env:LOCALAPPDATA 'Docker\log.txt'
$appLog = Join-Path $env:APPDATA 'Docker\log.txt'
if (Test-Path $localLog) { Copy-Item -Path $localLog -Destination (Join-Path $outDir 'Docker_local_log.txt') -Force }
if (Test-Path $appLog) { Copy-Item -Path $appLog -Destination (Join-Path $outDir 'Docker_app_log.txt') -Force }

# Also collect Docker Desktop service logs folder
$ddPath = Join-Path $env:LOCALAPPDATA 'Docker\wsl\docker-desktop-data\logs'
if (Test-Path $ddPath) {
    Copy-Item -Path $ddPath -Destination (Join-Path $outDir 'docker_desktop_data_logs') -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "Collecting Event Log entries for Docker Desktop (last 200)"
try {
    $events = Get-WinEvent -FilterHashtable @{LogName='Application'; ProviderName='Docker Desktop'} -MaxEvents 200 -ErrorAction SilentlyContinue
    if ($events) { $events | Out-File -FilePath (Join-Path $outDir 'docker_app_events.txt') -Encoding UTF8 }
} catch { }

Write-Host "Zipping diagnostics..."
$zipPath = Join-Path $PSScriptRoot "diagnostics_$timestamp.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path (Join-Path $outDir '*') -DestinationPath $zipPath -Force

Write-Host "Diagnostics saved to: $outDir"
Write-Host "Diagnostics ZIP: $zipPath"
Write-Host "Please attach or paste the ZIP file contents (or upload it) so I can analyze further."
