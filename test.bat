@echo off
cd /d "C:\Program Files\SpotSeek"

REM ------------------------------------------------------------------
REM Load credentials from credentials.env
REM ------------------------------------------------------------------
if not exist "credentials.env" (
    echo ERROR: credentials.env not found in C:\Program Files\SpotSeek
    pause
    exit /b 1
)

for /f "usebackq tokens=1,* delims==" %%A in ("credentials.env") do (
    set "%%A=%%B"
)

REM ------------------------------------------------------------------
REM Defaults for Essentia test
REM ------------------------------------------------------------------
if "%SPOTSEEK_PENDING_DIR%"=="" set "SPOTSEEK_PENDING_DIR=C:\Program Files\SpotSeek\pending"
if "%SPOTSEEK_LIBRARY_DIR%"=="" set "SPOTSEEK_LIBRARY_DIR=E:\Music"
if "%SPOTSEEK_PIPELINE_THREADS%"=="" set "SPOTSEEK_PIPELINE_THREADS=1"
if "%ESSENTIA_SSH_PORT%"=="" set "ESSENTIA_SSH_PORT=22"
if "%ESSENTIA_SSH_REMOTE_TEMP_DIR%"=="" set "ESSENTIA_SSH_REMOTE_TEMP_DIR=/tmp/spotseek"
if "%ESSENTIA_SSH_REMOTE_EXTRACTOR%"=="" set "ESSENTIA_SSH_REMOTE_EXTRACTOR=/home/carlos/essentia/build/src/examples/essentia_streaming_extractor_music_svm"
if "%ESSENTIA_SSH_REMOTE_SVM_MODELS_DIR%"=="" set "ESSENTIA_SSH_REMOTE_SVM_MODELS_DIR=/home/carlos/.local/share/essentia-extractor-svm_models"

if "%ESSENTIA_SSH_HOST%"=="" (
    echo ERROR: ESSENTIA_SSH_HOST is not set in credentials.env
    pause
    exit /b 1
)

if "%ESSENTIA_SSH_USER%"=="" (
    echo ERROR: ESSENTIA_SSH_USER is not set in credentials.env
    pause
    exit /b 1
)

where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON_CMD=py -3"
) else (
    set "PYTHON_CMD=python"
)

echo Starting Essentia analysis pipeline...
%PYTHON_CMD% "C:\Program Files\SpotSeek\tools\essentia_pipeline.py" ^
    --input-dir "%SPOTSEEK_PENDING_DIR%" ^
    --output-dir "%SPOTSEEK_LIBRARY_DIR%" ^
    --threads %SPOTSEEK_PIPELINE_THREADS% ^
    --ssh-host "%ESSENTIA_SSH_HOST%" ^
    --ssh-user "%ESSENTIA_SSH_USER%" ^
    --ssh-port %ESSENTIA_SSH_PORT% ^
    --ssh-remote-temp-dir "%ESSENTIA_SSH_REMOTE_TEMP_DIR%" ^
    --ssh-remote-extractor-path "%ESSENTIA_SSH_REMOTE_EXTRACTOR%" ^
    --ssh-remote-svm-models-dir "%ESSENTIA_SSH_REMOTE_SVM_MODELS_DIR%"

if errorlevel 1 (
    echo ERROR: Essentia pipeline failed.
    pause
    exit /b 1
)

echo Process completed.
pause
exit /b 0
