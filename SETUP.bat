@echo off
setlocal EnableDelayedExpansion
title AI Java Interview - Setup
color 0B

:: ?????? Display logo ??????
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0logo.ps1" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  ============================================
    echo   AI Java Interview Assistant - Setup
    echo  ============================================
    echo.
)

echo  Version: 1.2.0
echo  Build:   2026-06-26
echo.

:: ?????? Check if already installed (run_app.bat exists) ??????
if exist "%~dp0run_app.bat" (
    echo  [INFO] Already installed. Launching app...
    start "" "%~dp0run_app.bat"
    timeout /t 8 /nobreak >nul
    start "" "http://localhost:8501/JavaAIMockInterview/"
    exit /b 0
)

:: ?????? Run full install ??????
echo  [INFO] First time setup - running installer...
call "%~dp0install.bat"
