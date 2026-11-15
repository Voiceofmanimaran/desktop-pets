@echo off
setlocal

rem Resolve the app location from this batch file.
set "PROJECT_DIR=%~dp0"
set "PET_SCRIPT=%PROJECT_DIR%desktop_pets.py"
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "STARTUP_LINK=%STARTUP_DIR%\DesktopPets.lnk"
set "PYTHONW="

rem Try PATH first, then the Python launcher.
for /f "delims=" %%P in ('where pythonw.exe 2^>nul') do if not defined PYTHONW set "PYTHONW=%%P"
if not defined PYTHONW (
    for /f "delims=" %%P in ('py -3 -c "import os,sys; print(os.path.join(os.path.dirname(sys.executable), 'pythonw.exe'))" 2^>nul') do if not defined PYTHONW set "PYTHONW=%%P"
)

rem Also check the standard per-user install location when PATH and py are unavailable.
if not defined PYTHONW (
    for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python*") do if not defined PYTHONW if exist "%%~fD\pythonw.exe" set "PYTHONW=%%~fD\pythonw.exe"
)

if not defined PYTHONW (
    echo ERROR: Python was not found. Install Python 3 and try again.
    goto :failed
)
if not exist "%PYTHONW%" (
    echo ERROR: pythonw.exe was not found at "%PYTHONW%".
    goto :failed
)
echo Python windowed executable: "%PYTHONW%"

set "PYTHON=%PYTHONW:pythonw.exe=python.exe%"
if not exist "%PYTHON%" (
    echo ERROR: Matching python.exe was not found at "%PYTHON%".
    goto :failed
)

if not exist "%PET_SCRIPT%" (
    echo ERROR: desktop_pets.py was not found in "%PROJECT_DIR%".
    goto :failed
)

rem Pillow must already be installed; this installer does not access the internet.
"%PYTHON%" -c "import PIL" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Pillow is not installed for this Python. Install it once with internet, then retry.
    goto :failed
)

if not exist "%STARTUP_DIR%" mkdir "%STARTUP_DIR%"
if not exist "%STARTUP_DIR%" (
    echo ERROR: Could not access or create the Startup folder "%STARTUP_DIR%".
    goto :registry_fallback
)

rem Create the Startup shortcut and explicitly verify that it was written.
set "PET_PYTHONW=%PYTHONW%"
set "PET_LINK=%STARTUP_LINK%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; try { $shell = New-Object -ComObject WScript.Shell; $s = $shell.CreateShortcut($env:PET_LINK); $s.TargetPath = $env:PET_PYTHONW; $s.Arguments = [char]34 + $env:PET_SCRIPT + [char]34; $s.WorkingDirectory = $env:PROJECT_DIR; $s.WindowStyle = 7; $s.Save(); if (-not (Test-Path -LiteralPath $env:PET_LINK)) { throw 'Shortcut file was not created.' }; Write-Output ('Shortcut created: ' + $env:PET_LINK) } catch { Write-Error ('Shortcut creation failed: ' + $_.Exception.Message); exit 1 }"
if errorlevel 1 goto :registry_fallback
if not exist "%STARTUP_LINK%" goto :registry_fallback

rem Start now as well as automatically at sign-in.
start "" /D "%PROJECT_DIR%" "%PYTHONW%" "%PET_SCRIPT%"
echo Done! Desktop pets will start automatically when Windows starts.
goto :finished

:registry_fallback
echo Shortcut creation failed. Trying the current-user Run registry key...
set "PET_PYTHONW=%PYTHONW%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; try { $key = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'; $value = [char]34 + $env:PET_PYTHONW + [char]34 + ' ' + [char]34 + $env:PET_SCRIPT + [char]34; New-Item -Path $key -Force | Out-Null; Set-ItemProperty -Path $key -Name 'DesktopPets' -Value $value; $saved = (Get-ItemProperty -Path $key -Name 'DesktopPets').DesktopPets; if ($saved -ne $value) { throw 'Registry value verification failed.' }; Write-Output 'Registry autostart created: DesktopPets' } catch { Write-Error ('Registry fallback failed: ' + $_.Exception.Message); exit 1 }"
if errorlevel 1 (
    echo ERROR: Could not create the shortcut or registry autostart entry.
    goto :failed
)
start "" /D "%PROJECT_DIR%" "%PYTHONW%" "%PET_SCRIPT%"
echo Done! Desktop pets will start automatically when Windows starts (registry backup).
goto :finished

:failed
echo Installation did not complete.

:finished
echo.
pause
exit /b
