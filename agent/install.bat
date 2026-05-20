@echo off
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Please right-click and select "Run as Administrator".
    pause
    exit /b
)

echo [+] Installing PROATI Monitor Agent...

if not exist "C:\Program Files\PROATI-Monitor" (
    mkdir "C:\Program Files\PROATI-Monitor"
)

copy /y "%~dp0WinNetMonitor.exe" "C:\Program Files\PROATI-Monitor\" >nul
copy /y "%~dp0config.ini" "C:\Program Files\PROATI-Monitor\" >nul

schtasks /create /tn "PROATI_Agent" /tr "'C:\Program Files\PROATI-Monitor\WinNetMonitor.exe'" /sc onstart /ru "SYSTEM" /f >nul

echo.
echo [OK] Agent installed successfully and configured in Task Scheduler!
timeout /t 3 >nul