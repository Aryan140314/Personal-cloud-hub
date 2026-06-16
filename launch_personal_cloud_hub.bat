@echo off
setlocal

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 goto error
)

if not exist "venv\.personal_cloud_hub_ready" (
    echo Installing required packages...
    "venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto error
    echo ready> "venv\.personal_cloud_hub_ready"
)

echo Starting Personal Cloud Hub...
"venv\Scripts\python.exe" app.py
if errorlevel 1 goto error

exit /b 0

:error
echo.
echo Personal Cloud Hub could not start. Check the error above.
pause
exit /b 1
