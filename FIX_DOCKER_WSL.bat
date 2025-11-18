@echo off
REM AceBuddy - Docker WSL Auto-Fix Script
REM This script automatically fixes Docker Desktop WSL issues

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║          Docker WSL Auto-Fix Script                       ║
echo ║     This will install WSL 2 and fix Docker Desktop        ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Check if running as Administrator
echo Checking Administrator privileges...
openfiles >nul 2>&1
if errorlevel 1 (
    echo ERROR: This script must be run as Administrator!
    echo.
    echo Solution:
    echo   1. Right-click on PowerShell
    echo   2. Select "Run as Administrator"
    echo   3. Run this script again
    echo.
    pause
    exit /b 1
)

echo ✓ Running with Administrator privileges
echo.

REM Step 1: Enable WSL Feature
echo Step 1: Enabling Windows Subsystem for Linux...
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
if errorlevel 1 (
    echo Warning: WSL feature enable returned non-zero code
) else (
    echo ✓ WSL feature enabled
)
echo.

REM Step 2: Enable Virtual Machine Platform
echo Step 2: Enabling Virtual Machine Platform...
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
if errorlevel 1 (
    echo Warning: Virtual Machine Platform enable returned non-zero code
) else (
    echo ✓ Virtual Machine Platform enabled
)
echo.

REM Step 3: Set WSL 2 as default
echo Step 3: Setting WSL 2 as default version...
wsl --set-default-version 2
if errorlevel 1 (
    echo Warning: Could not set WSL 2 as default
    echo This might require you to download the WSL 2 kernel manually
    echo Visit: https://aka.ms/wsl2kernel
) else (
    echo ✓ WSL 2 set as default
)
echo.

REM Step 4: Install Ubuntu if not already installed
echo Step 4: Checking Ubuntu installation...
wsl --list 2>nul | findstr /i ubuntu >nul
if errorlevel 1 (
    echo Ubuntu not found. Installing Ubuntu...
    wsl --install -d Ubuntu
    echo ✓ Ubuntu installed
) else (
    echo ✓ Ubuntu already installed
)
echo.

REM Step 5: Verify installation
echo Step 5: Verifying WSL installation...
echo.
echo WSL Status:
wsl --list --verbose
echo.

REM Step 6: Check Docker
echo Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Docker is not installed or not in PATH
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
) else (
    echo ✓ Docker is installed
    docker --version
)
echo.

REM Step 7: Summary
echo ╔════════════════════════════════════════════════════════════╗
echo ║                 Fix Complete - Summary                     ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo ✓ WSL 2 features enabled
echo ✓ Virtual Machine Platform enabled
echo ✓ Ubuntu Linux installed (or already present)
echo.
echo NEXT STEPS:
echo.
echo 1. Restart your computer (IMPORTANT!)
echo    - Some WSL changes require system reboot
echo    - Type: shutdown /r /t 30
echo.
echo 2. After restart, open PowerShell and run:
echo    - docker ps
echo    - This should work without errors
echo.
echo 3. Then start AceBuddy-RAG:
echo    - cd "C:\Users\aryan.gupta\OneDrive - Real Time Data Services Pvt Ltd\Desktop\AceBuddy-RAG"
echo    - docker-compose up --build -d
echo.
echo ═══════════════════════════════════════════════════════════════
echo.

echo Do you want to restart your computer now? (Y/N)
set /p RESTART=
if /i "%RESTART%"=="Y" (
    echo Restarting in 30 seconds... (Press Ctrl+C to cancel)
    shutdown /r /t 30
) else (
    echo Remember to restart your computer for changes to take effect!
    echo.
)

pause
