# ============================================================
#  AI Java Interview Assistant — Package Builder
#  Creates a self-contained distributable ZIP package
# ============================================================

param(
    [string]$Version = "1.2.0",
    [string]$OutputDir = "$PSScriptRoot\dist"
)

$AppName    = "AIJavaInterview"
$PackageDir = "$OutputDir\$AppName-$Version"
$ZipPath    = "$OutputDir\$AppName-$Version-Setup.zip"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  AI Java Interview Assistant - Package Builder v$Version" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Create output folders ──────────────────────────
Write-Host "[1/6] Creating package folder..." -ForegroundColor Yellow
if (Test-Path $PackageDir) { Remove-Item $PackageDir -Recurse -Force }
New-Item -ItemType Directory -Path $PackageDir | Out-Null
New-Item -ItemType Directory -Path "$OutputDir" -Force | Out-Null
Write-Host "      OK: $PackageDir" -ForegroundColor Green

# ── Step 2: Copy app files ──────────────────────────────────
Write-Host "[2/6] Copying application files..." -ForegroundColor Yellow

$filesToCopy = @(
    "ai_assistant.py",
    "question_bank.json",
    "requirements.txt",
    "install.bat",
    "logo.ps1",
    "generate_icon.py",
    "README.txt",
    "build_package.bat",
    "build_package.ps1",
    "run_app.bat"
)

foreach ($file in $filesToCopy) {
    $src = "$PSScriptRoot\$file"
    if (Test-Path $src) {
        Copy-Item $src -Destination "$PackageDir\$file"
        Write-Host "      Copied: $file" -ForegroundColor Green
    } else {
        Write-Host "      MISSING: $file (skipped)" -ForegroundColor DarkYellow
    }
}

# Copy icon if exists
if (Test-Path "$PSScriptRoot\app_icon.ico") {
    Copy-Item "$PSScriptRoot\app_icon.ico" -Destination "$PackageDir\app_icon.ico"
    Write-Host "      Copied: app_icon.ico" -ForegroundColor Green
}

# ── Step 3: Write version file ──────────────────────────────
Write-Host "[3/6] Writing version info..." -ForegroundColor Yellow
@"
AI Java Interview Assistant
Version: $Version
Build Date: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Platform: Windows
Python: 3.9+
URL: http://localhost:8501/JavaAIMockInterview/

CHANGELOG v1.2.0
----------------
+ Admin system: amara.goodwill@gmail.com auto-promoted to Admin
+ Admin Dashboard: User management, plan control, stats, plan distribution chart
+ Admin can change any user's plan from the dashboard
+ SyntaxError fix: _all_topics list closure bug resolved
+ Plan enforcement: topics/questions/source restricted per plan
+ Subscription bar: shows plan badge + days left on top bar
+ run_app.bat: improved with server background start + auto browser open
+ Base URL: /JavaAIMockInterview/ across all launchers

CHANGELOG v1.1.0
----------------
+ Microservices topic (45 questions: Junior/Mid/Senior)
+ System Design topic (45 questions: Junior/Mid/Senior)
+ DSA Problems topic (45 questions: Junior/Mid/Senior)
+ Smart timer: System Design and DSA auto-set to 30-50 min per question
+ Topic-aware timer colour thresholds
+ Mixed mode: combine Question Bank + AI Generated questions
+ Login / Sign Up / Forgot Password (3-step reset flow)
+ Custom red mug icon (app_icon.ico)
+ Every session generates different questions
+ Voice input improvements

PLANS
-----
Free Trial    : 3 days   | 5Q  | Core Java only | AI only
Basic         : 99/month | 10Q | 5 topics       | AI + Bank
Premium       : 299/month| 15Q | All 13 topics  | All modes
Professional  : 499/month| 15Q | All 13 topics  | All + Priority AI
Admin         : Unlimited| All | All features   | No restrictions
"@ | Out-File "$PackageDir\VERSION.txt" -Encoding UTF8
Write-Host "      OK: VERSION.txt" -ForegroundColor Green

# ── Step 4: Create the smart SETUP.bat ──────────────────────
Write-Host "[4/6] Creating SETUP.bat launcher..." -ForegroundColor Yellow

$setupContent = @'
@echo off
setlocal EnableDelayedExpansion
title AI Java Interview - Setup
color 0B

:: ── Display logo ──
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0logo.ps1" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  ============================================
    echo   AI Java Interview Assistant - Setup
    echo  ============================================
    echo.
)

echo  Version: APP_VERSION
echo  Build:   APP_DATE
echo.

:: ── Check if already installed (run_app.bat exists) ──
if exist "%~dp0run_app.bat" (
    echo  [INFO] Already installed. Launching app...
    start "" "%~dp0run_app.bat"
    timeout /t 8 /nobreak >nul
    start "" "http://localhost:8501/JavaAIMockInterview/"
    exit /b 0
)

:: ── Run full install ──
echo  [INFO] First time setup - running installer...
call "%~dp0install.bat"
'@

$setupContent = $setupContent `
    -replace "APP_VERSION", $Version `
    -replace "APP_DATE", (Get-Date -Format "yyyy-MM-dd")

$setupContent | Out-File "$PackageDir\SETUP.bat" -Encoding ASCII
Write-Host "      OK: SETUP.bat" -ForegroundColor Green

# ── Step 5: Create ZIP package ──────────────────────────────
Write-Host "[5/6] Creating ZIP package..." -ForegroundColor Yellow
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($PackageDir, $ZipPath)

$sizeMB = [math]::Round((Get-Item $ZipPath).Length / 1MB, 2)
Write-Host "      OK: $ZipPath ($sizeMB MB)" -ForegroundColor Green

# ── Step 6: Create installation guide ──────────────────────
Write-Host "[6/6] Creating HOW_TO_INSTALL.txt..." -ForegroundColor Yellow
@"
===========================================================
  AI Java Interview Assistant v$Version
  HOW TO INSTALL & RUN
===========================================================

REQUIREMENTS
------------
  - Windows 10 or 11
  - Python 3.9+ (https://www.python.org/downloads/)
    * During install: CHECK "Add Python to PATH"
  - Internet connection (for Groq AI + Speech Recognition)
  - Microphone (optional, for voice answers)

INSTALLATION STEPS
------------------
  1. Extract this ZIP to any folder
     (e.g. C:\AIJavaInterview\)

  2. Double-click  SETUP.bat
     - First run: installs all Python packages automatically
     - Creates Desktop shortcut "AI Java Interview"
     - Creates Start Menu entry

  3. Your browser opens at:
     http://localhost:8501/JavaAIMockInterview/

  NEXT TIME: Just double-click the Desktop shortcut!

  NOTE: If browser does not open automatically, go to:
  http://localhost:8501/JavaAIMockInterview/

FEATURES
--------
  ☕ Java Mock Interview
     - 10 Java topic areas
     - 3 difficulty levels (Junior / Mid / Senior)
     - 200+ pre-loaded questions in Question Bank
     - AI-generated fresh questions every session
     - Mixed mode: combine Bank + AI questions
     - Voice input (speak your answer)
     - AI scores 0-10 with detailed feedback
     - 4-5 minute countdown timer per question
     - Final report with AI analysis

  🌍 Multilingual Assistant
     - English, Hindi, Spanish translation
     - Log file analysis
     - Groq API support assistant

  🔐 Login System
     - Register / Login / Forgot Password
     - Guest mode available

TROUBLESHOOTING
---------------
  Error: "python not found"
  -> Install Python from https://www.python.org/downloads/
  -> Check "Add Python to PATH" during setup

  Error: "module not found"
  -> Re-run SETUP.bat to reinstall packages

  App doesn't open in browser
  -> Manually go to: http://localhost:8501

  Voice not working
  -> Check Windows Settings > Sound > Input device

SUPPORT
-------
  App folder: Contains all source files
  Question Bank: question_bank.json (add your own questions!)
  Users: users.json (auto-created on first registration)

===========================================================
"@ | Out-File "$PackageDir\HOW_TO_INSTALL.txt" -Encoding UTF8
Copy-Item "$PackageDir\HOW_TO_INSTALL.txt" -Destination "$OutputDir\HOW_TO_INSTALL.txt"
Write-Host "      OK: HOW_TO_INSTALL.txt" -ForegroundColor Green

# ── Done ────────────────────────────────────────────────────
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  PACKAGE BUILT SUCCESSFULLY!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Package : $ZipPath" -ForegroundColor White
Write-Host "  Size    : $sizeMB MB" -ForegroundColor White
Write-Host "  Version : $Version" -ForegroundColor White
Write-Host ""
Write-Host "  TO DISTRIBUTE:" -ForegroundColor Yellow
Write-Host "  1. Send the ZIP file to anyone" -ForegroundColor White
Write-Host "  2. They extract it and double-click SETUP.bat" -ForegroundColor White
Write-Host "  3. App installs and opens automatically!" -ForegroundColor White
Write-Host ""

# Open dist folder
Start-Process explorer $OutputDir

