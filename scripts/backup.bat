@echo off
REM Backup script for AceBuddy RAG system (Windows batch version)
REM Backs up data, embeddings, and configuration for migration/recovery

setlocal enabledelayedexpansion

set BACKUP_DIR=backups
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
set TIMESTAMP=%mydate%_%mytime%
set BACKUP_NAME=acebuddy_backup_%TIMESTAMP%
set FULL_BACKUP_PATH=%BACKUP_DIR%\%BACKUP_NAME%

echo Starting AceBuddy RAG backup...
echo Backup destination: %FULL_BACKUP_PATH%

REM Create backup directory
if not exist "%FULL_BACKUP_PATH%" mkdir "%FULL_BACKUP_PATH%"

REM Backup data files
echo Backing up data files...
if exist "data\kb" xcopy "data\kb" "%FULL_BACKUP_PATH%\kb" /E /I /Y
if exist "data\chroma" xcopy "data\chroma" "%FULL_BACKUP_PATH%\chroma" /E /I /Y
if exist "data\processed_chunks.json" copy "data\processed_chunks.json" "%FULL_BACKUP_PATH%\"

REM Backup configuration
echo Backing up configuration...
if exist ".env" copy ".env" "%FULL_BACKUP_PATH%\.env.backup"
copy "requirements.txt" "%FULL_BACKUP_PATH%\"
copy "docker-compose.yml" "%FULL_BACKUP_PATH%\"
if exist "app\Dockerfile" copy "app\Dockerfile" "%FULL_BACKUP_PATH%\"

REM Backup app code
echo Backing up application code...
xcopy "app" "%FULL_BACKUP_PATH%\app" /E /I /Y
xcopy "scripts" "%FULL_BACKUP_PATH%\scripts" /E /I /Y

REM Create backup metadata
echo Creating backup metadata...
(
echo AceBuddy RAG System Backup
echo ==========================
echo Backup Date: %date% %time%
echo Timestamp: %TIMESTAMP%
echo.
echo Contents:
echo - kb/ : Knowledge base files
echo - chroma/ : Vector database index
echo - processed_chunks.json : Processed and embedded chunks
echo - app/ : FastAPI application code
echo - scripts/ : Utility scripts
echo - requirements.txt : Python dependencies
echo - docker-compose.yml : Docker orchestration config
echo - .env.backup : Environment configuration
echo.
echo To restore:
echo 1. Copy all contents to target system
echo 2. Update .env file with target server details
echo 3. Run: docker-compose up --build
) > "%FULL_BACKUP_PATH%\BACKUP_INFO.txt"

echo.
echo ✓ Backup completed successfully!
echo Backup location: %FULL_BACKUP_PATH%
echo.
echo To restore this backup:
echo 1. Copy entire directory to target system
echo 2. Update .env with new environment settings
echo 3. Run: docker-compose up --build -d
echo.
