@echo off
setlocal enabledelayedexpansion

echo ==============================================
echo   AWB Batch Processor Setup Initialization
echo ==============================================
echo.

set "PY_DIR=python_env"
set "PYTHON_URL=https://www.python.org/ftp/python/3.10.11/python-3.10.11-embed-amd64.zip"
set "PIP_URL=https://bootstrap.pypa.io/get-pip.py"

:: 1. Setup Local Python Environment
if not exist "%PY_DIR%" (
    echo [INFO] Local Python environment not found.
    echo [INFO] Downloading Python 3.10 Embeddable package...
    powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile 'python_embed.zip'"
    
    if not exist "python_embed.zip" (
        echo [ERROR] Failed to download Python.
        pause
        exit /b 1
    )
    
    echo [INFO] Extracting Python...
    powershell -Command "Expand-Archive -Path 'python_embed.zip' -DestinationPath '%PY_DIR%' -Force"
    del python_embed.zip
    
    :: Modify python310._pth to enable site packages (required for pip)
    echo [INFO] Configuring Python environment for PIP...
    powershell -Command "(Get-Content '%PY_DIR%\python310._pth') -replace '#import site', 'import site' | Set-Content '%PY_DIR%\python310._pth'"
    
    :: Install PIP locally
    echo [INFO] Downloading PIP installer...
    powershell -Command "Invoke-WebRequest -Uri '%PIP_URL%' -OutFile 'get-pip.py'"
    echo [INFO] Installing PIP...
    "%PY_DIR%\python.exe" get-pip.py
    del get-pip.py
)

:: 2. Install Project Requirements using LOCAL Python
echo [INFO] Ensuring required Python packages are installed locally...
"%PY_DIR%\python.exe" -m pip install -q --upgrade pip
"%PY_DIR%\python.exe" -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install requirements. Please check your internet connection.
    pause
    exit /b 1
)

:: 3. Setup Project Configuration
if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] Creating default .env configuration...
        copy .env.example .env >nul
    ) else (
        echo [WARNING] .env.example not found. Creating a minimal .env file...
        echo INPUT_LIST_PATH=./batch_input.txt ^> .env
        echo OUTPUT_DIR=./output ^>^> .env
        echo LOG_DIR=./logs ^>^> .env
    )
)

:: 4. Create necessary directories
if not exist "data\output" mkdir "data\output"
if not exist "logs" mkdir "logs"

echo.
echo [SUCCESS] Setup completed successfully!
echo You can configure your input/output paths in the newly created .env file.
echo.
pause
