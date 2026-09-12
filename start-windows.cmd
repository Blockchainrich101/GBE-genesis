@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Setup required. Follow README.md to create .venv and install dependencies.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m app
set "GBE_EXIT=%ERRORLEVEL%"
echo Server stopped. Exit code: %GBE_EXIT%
pause
exit /b %GBE_EXIT%
