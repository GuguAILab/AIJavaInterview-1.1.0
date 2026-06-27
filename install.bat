@echo off
setlocal EnableDelayedExpansion
title AI Java Interview - Installer
color 0B

:: ── Display logo from logo.ps1 ──
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0logo.ps1"



:: ── Set install directory to script location ──
set "INSTALL_DIR=%~dp0"
cd /d "%INSTALL_DIR%"

:: ─────────────────────────────────────────────
:: STEP 1 - Find Python
:: ─────────────────────────────────────────────
echo  [1/5] Checking Python installation...

set "PYTHON="

where python >nul 2>&1
if %ERRORLEVEL%==0 (
    for /f "tokens=*" %%P in ('where python') do (
        set "PYTHON=%%P"
        goto :python_found
    )
)

for %%V in (313 312 311 310 39 38) do (
    if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python%%V\python.exe" (
        set "PYTHON=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python%%V\python.exe"
        goto :python_found
    )
    if exist "C:\Python%%V\python.exe" (
        set "PYTHON=C:\Python%%V\python.exe"
        goto :python_found
    )
)

where py >nul 2>&1
if %ERRORLEVEL%==0 (
    set "PYTHON=py"
    goto :python_found
)

echo.
echo  [ERROR] Python not found!
echo  Please install Python 3.9+ from https://www.python.org/downloads/
echo  Make sure to check "Add Python to PATH" during install.
echo.
pause
exit /b 1

:python_found
echo  [OK] Found Python: %PYTHON%

:: ─────────────────────────────────────────────
:: STEP 2 - Verify Python version
:: ─────────────────────────────────────────────
echo.
echo  [2/5] Verifying Python version...
"%PYTHON%" --version
if %ERRORLEVEL% NEQ 0 (
    echo  [ERROR] Could not run Python. Exiting.
    pause
    exit /b 1
)
echo  [OK] Python is working.

:: ─────────────────────────────────────────────
:: STEP 3 - Upgrade pip and install dependencies
:: ─────────────────────────────────────────────
echo.
echo  [3/5] Installing required packages...
echo  This may take a few minutes on first run...
echo.

"%PYTHON%" -m pip install --upgrade pip --quiet
echo  [pip] Upgraded pip.

if exist "%INSTALL_DIR%requirements.txt" (
    "%PYTHON%" -m pip install -r "%INSTALL_DIR%requirements.txt" --quiet
    if !ERRORLEVEL! NEQ 0 (
        echo  [WARN] pyaudio failed ^(common on Windows^). Retrying without it...
        "%PYTHON%" -m pip install streamlit groq pyttsx3 SpeechRecognition --quiet
    )
) else (
    "%PYTHON%" -m pip install streamlit groq pyttsx3 SpeechRecognition --quiet
)

echo  [OK] All packages installed.

:: ─────────────────────────────────────────────
:: STEP 4 - Create launcher script
:: ─────────────────────────────────────────────
echo.
echo  [4/5] Creating launcher...

:: Write run_app.bat with correct python path
(
echo @echo off
echo title AI Java Mock Interview - Running
echo cd /d "%INSTALL_DIR%"
echo echo.
echo echo  Starting AI Mock Interview Assistant...
echo echo  URL: http://localhost:8501/JavaAIMockInterview/
echo echo.
echo start "" "%PYTHON%" -m streamlit run ai_assistant.py --server.port 8501 --server.baseUrlPath "/JavaAIMockInterview" --browser.gatherUsageStats false
echo timeout /t 6 /nobreak ^>nul
echo start "" "http://localhost:8501/JavaAIMockInterview/"
echo pause
) > "%INSTALL_DIR%run_app.bat"

echo  [OK] Launcher created: run_app.bat

:: ─────────────────────────────────────────────
:: STEP 4b - Generate app icon
:: ─────────────────────────────────────────────
echo.
echo  [4b] Generating application icon...
if exist "%INSTALL_DIR%generate_icon.py" (
    "%PYTHON%" "%INSTALL_DIR%generate_icon.py" >nul 2>&1
    if exist "%INSTALL_DIR%app_icon.ico" (
        echo  [OK] Icon generated: app_icon.ico
    ) else (
        echo  [WARN] Icon generation failed. Shortcuts will use default icon.
    )
) else (
    echo  [WARN] generate_icon.py not found. Skipping icon.
)
set "ICON_PATH=%INSTALL_DIR%app_icon.ico"

:: ─────────────────────────────────────────────
:: STEP 5 - Create Desktop Shortcut (via PowerShell)
:: ─────────────────────────────────────────────
echo.
echo  [5/5] Creating Desktop shortcut...

set "SHORTCUT_NAME=AI Java Interview"

:: Resolve actual Desktop path (handles OneDrive redirect, custom paths, etc.)
for /f "usebackq delims=" %%D in (`powershell -NoProfile -Command "[Environment]::GetFolderPath('Desktop')"`) do set "DESKTOP=%%D"

echo  [INFO] Desktop path resolved: %DESKTOP%

powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$desktop = [Environment]::GetFolderPath('Desktop'); " ^
  "$s = $ws.CreateShortcut($desktop + '\AI Java Interview.lnk'); " ^
  "$s.TargetPath = '%INSTALL_DIR%run_app.bat'; " ^
  "$s.WorkingDirectory = '%INSTALL_DIR%'; " ^
  "$s.Description = 'AI Java Interview - Smart Multilingual AI Assistant'; " ^
  "$s.IconLocation = '%ICON_PATH%,0'; " ^
  "$s.WindowStyle = 1; " ^
  "$s.Save(); Write-Host 'Shortcut saved to ' $desktop"

if exist "%DESKTOP%\AI Java Interview.lnk" (
    echo  [OK] Desktop shortcut created at: %DESKTOP%\AI Java Interview.lnk
) else (
    echo  [WARN] Desktop shortcut failed. Creating on Public Desktop instead...
    powershell -NoProfile -Command ^
      "$ws = New-Object -ComObject WScript.Shell; " ^
      "$s = $ws.CreateShortcut('C:\Users\Public\Desktop\AI Java Interview.lnk'); " ^
      "$s.TargetPath = '%INSTALL_DIR%run_app.bat'; " ^
      "$s.WorkingDirectory = '%INSTALL_DIR%'; " ^
      "$s.Description = 'AI Java Interview - Smart Multilingual AI Assistant'; " ^
      "$s.IconLocation = '%ICON_PATH%,0'; " ^
      "$s.WindowStyle = 1; " ^
      "$s.Save()"
    if exist "C:\Users\Public\Desktop\AI Java Interview.lnk" (
        echo  [OK] Shortcut created on Public Desktop.
    ) else (
        echo  [INFO] Shortcut skipped. Use run_app.bat to launch.
    )
)

:: ─────────────────────────────────────────────
:: Create Start Menu shortcut
:: ─────────────────────────────────────────────
set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$s = $ws.CreateShortcut('%START_MENU%\AI Java Interview.lnk'); " ^
  "$s.TargetPath = '%INSTALL_DIR%run_app.bat'; " ^
  "$s.WorkingDirectory = '%INSTALL_DIR%'; " ^
  "$s.Description = 'AI Java Interview - Smart Multilingual AI Assistant'; " ^
  "$s.IconLocation = '%ICON_PATH%,0'; " ^
  "$s.WindowStyle = 1; " ^
  "$s.Save()"

echo  [OK] Start Menu shortcut created with custom icon.

:: ─────────────────────────────────────────────
:: Done
:: ─────────────────────────────────────────────
echo.
echo  ============================================================
echo    INSTALLATION COMPLETE!
echo  ============================================================
echo.
echo   To run the app:
echo   1. Double-click "AI Java Interview" on your Desktop
echo   OR
echo   2. Double-click run_app.bat in this folder
echo   OR
echo   3. Open Start Menu and search "AI Java Interview"
echo.
echo   The app will open at: http://localhost:8501/JavaAIMockInterview/
echo.

set /p LAUNCH="  Launch the app now? (Y/N): "
if /i "%LAUNCH%"=="Y" (
    echo  Launching...
    start "" "%INSTALL_DIR%run_app.bat"
    timeout /t 8 /nobreak >nul
    start "" "http://localhost:8501/JavaAIMockInterview/"
)

echo.
echo  Installation finished. Press any key to exit.
pause >nul
endlocal
