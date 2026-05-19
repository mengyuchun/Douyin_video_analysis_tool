@echo off
chcp 65001 >nul 2>&1
title Douyin Video Analysis Tool

echo ========================================
echo    Douyin Video Analysis Tool
echo ========================================
echo.

REM Activate conda environment
call conda activate data_env
if %errorlevel% neq 0 (
    echo [ERROR] Cannot activate conda environment data_env
    echo Please run: conda init cmd.exe
    pause
    exit /b 1
)

REM Check dependencies
python -c "import httpx, rich, browser_cookie3" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing dependencies...
    pip install -r "%~dp0requirements.txt"
)

REM Run main program
cd /d "%~dp0"
python main.py

pause
