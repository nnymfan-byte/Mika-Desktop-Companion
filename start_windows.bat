@echo off
cd /d "%~dp0"
if exist "Mika.exe" (
  start "" "Mika.exe"
  exit /b 0
)
where python >nul 2>nul
if %errorlevel%==0 (
  python companion.py
) else (
  echo Mika.exe n'est pas present.
  echo Lance le workflow GitHub "Build Mika for Windows".
  pause
)
