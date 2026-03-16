@echo off
setlocal enabledelayedexpansion

:: Check if environment needs setup (either missing .env or missing local Python)
if not exist "python_env" (
    echo [INFO] First run detected. Running setup...
    call setup.bat
    if errorlevel 1 (
        echo [ERROR] Setup failed. Exiting...
        pause
        exit /b 1
    )
)

if not exist ".env" (
    echo [INFO] .env missing. Running setup to restore...
    call setup.bat
)

echo.
echo ==============================================
echo          Starting AWB Batch Processor
echo ==============================================
echo.

"python_env\python.exe" src\main.py --consolidate
echo.
echo [INFO] Pipeline finished.
pause
