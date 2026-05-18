@echo off
echo installing PROATI Monitor Agent...
copy "%~dp0agent.exe" "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\agent.exe"
copy "%~dp0config.ini" "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\config.ini"
echo done! Agent will start automatically with Windows.