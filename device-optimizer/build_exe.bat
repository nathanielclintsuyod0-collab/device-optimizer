@echo off
REM Builds device_optimizer.exe from device_optimizer.py
REM Put this file in the same folder as device_optimizer.py, then double-click it.

echo Installing build tools...
python -m pip install --upgrade pip
python -m pip install psutil pyinstaller
if errorlevel 1 goto :fail

echo Building executable...
python -m PyInstaller --onefile --name device_optimizer device_optimizer.py
if errorlevel 1 goto :fail

echo.
echo Done! Your program is at:  dist\device_optimizer.exe
echo Run it from Command Prompt, e.g.:  dist\device_optimizer.exe report
pause
exit /b 0

:fail
echo.
echo Build failed. Make sure Python is installed and on your PATH.
pause
exit /b 1
