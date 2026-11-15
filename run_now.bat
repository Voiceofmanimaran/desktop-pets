@echo off
setlocal

rem Run the app from this folder without opening a console window.
set "PROJECT_DIR=%~dp0"
set "PET_SCRIPT=%PROJECT_DIR%desktop_pets.py"
set "PYTHONW="

rem First look for pythonw.exe on PATH.
for /f "delims=" %%P in ('where pythonw.exe 2^>nul') do if not defined PYTHONW set "PYTHONW=%%P"

rem If needed, ask the Python launcher for its Python 3 windowed executable.
if not defined PYTHONW (
    for /f "delims=" %%P in ('py -3 -c "import os,sys; print(os.path.join(os.path.dirname(sys.executable), 'pythonw.exe'))" 2^>nul') do if not defined PYTHONW set "PYTHONW=%%P"
)

rem Check the usual per-user Python installation folder as a final fallback.
if not defined PYTHONW (
    for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python*") do if not defined PYTHONW if exist "%%~fD\pythonw.exe" set "PYTHONW=%%~fD\pythonw.exe"
)

if not defined PYTHONW (
    echo ERROR: Python was not found. Install Python 3, then run this file again.
    pause
    exit /b 1
)
if not exist "%PYTHONW%" (
    echo ERROR: pythonw.exe was not found: "%PYTHONW%"
    pause
    exit /b 1
)
if not exist "%PET_SCRIPT%" (
    echo ERROR: desktop_pets.py was not found in "%PROJECT_DIR%"
    pause
    exit /b 1
)

echo Starting desktop pets with "%PYTHONW%"
start "" /D "%PROJECT_DIR%" "%PYTHONW%" "%PET_SCRIPT%"
echo Desktop pets launched without a console window.
exit /b 0
