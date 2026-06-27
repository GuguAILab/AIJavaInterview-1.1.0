@echo off
title AI Java Interview - Build Package v1.2.0
color 0A
echo.
echo  Building distributable package v1.2.0...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_package.ps1" -Version "1.2.0"
echo.
pause
