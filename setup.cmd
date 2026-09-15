@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto install
if exist ".python\tools\python.exe" (
    ".python\tools\python.exe" -m venv .venv
) else (
    py -3.13 -m venv .venv
)
if errorlevel 1 goto failed
:install
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip check
if errorlevel 1 goto failed
if not exist ".env" copy /y ".env.example" ".env" >nul
echo Setup complete. Run start.cmd to start the backend.
pause
exit /b 0
:failed
echo Setup failed. See the error above. Python 3.13 is required for this setup.
pause
exit /b 1
