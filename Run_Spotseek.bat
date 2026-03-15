@echo off
cd /d "C:\Program Files\SpotSeek"

REM ------------------------------------------------------------------
REM Load credentials from credentials.env
REM ------------------------------------------------------------------
if not exist "credentials.env" (
    echo ERROR: credentials.env not found in C:\Program Files\SpotSeek
    echo Aborting Run_Spotseek.bat
    exit /b 1
)

for /f "usebackq tokens=1,2 delims==" %%A in ("credentials.env") do (
    set %%A=%%B
)

REM ------------------------------------------------------------------
REM Validate required variables
REM ------------------------------------------------------------------
if "%SOULSEEK_USER%"=="" (
    echo ERROR: SOULSEEK_USER is not set in credentials.env
    exit /b 1
)

if "%SOULSEEK_PASS%"=="" (
    echo ERROR: SOULSEEK_PASS is not set in credentials.env
    exit /b 1
)

REM ------------------------------------------------------------------
REM Execute Soulseek download
REM ------------------------------------------------------------------
echo Starting download via Soulseek...
"C:\Program Files\SpotSeek\soulseek\sldl.exe" "C:\Program Files\SpotSeek\export\pending.csv" ^
    --path "C:\Program Files\SpotSeek" ^
    --user %SOULSEEK_USER% ^
    --pass %SOULSEEK_PASS% ^
    --format flac,aac,m4a,mp3 ^
    --pref-format flac,aac,m4a,mp3 ^
    --min-bitrate 320 ^
	--concurrent-downloads 6 ^
	--skip-not-found 

if errorlevel 1 (
    echo ERROR: Soulseek download failed.
    exit /b 1
)

REM ------------------------------------------------------------------
REM Execute Essentia analysis pipeline
REM ------------------------------------------------------------------
if "%SPOTSEEK_PENDING_DIR%"=="" set "SPOTSEEK_PENDING_DIR=C:\Program Files\SpotSeek\pending"
if "%SPOTSEEK_LIBRARY_DIR%"=="" set "SPOTSEEK_LIBRARY_DIR=E:\Music"
if "%SPOTSEEK_PIPELINE_THREADS%"=="" set "SPOTSEEK_PIPELINE_THREADS=1"

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
    --threads %SPOTSEEK_PIPELINE_THREADS%

if errorlevel 1 (
    echo ERROR: Essentia pipeline failed.
    exit /b 1
)

echo Process completed.
exit /b 0
