@echo off
setlocal

rem Remove the Startup shortcut for the current Windows user.
set "STARTUP_LINK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\DesktopPets.lnk"
if exist "%STARTUP_LINK%" del "%STARTUP_LINK%"

rem Remove the per-user registry backup entry if it exists.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$key = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'; if (Test-Path $key) { Remove-ItemProperty -Path $key -Name 'DesktopPets' -ErrorAction SilentlyContinue }; Get-CimInstance -ClassName Win32_Process | Where-Object { $_.Name -eq 'pythonw.exe' -and $_.CommandLine -like '*desktop_pets.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"

echo Desktop pets autostart has been removed and any running pet app was stopped.
exit /b 0
