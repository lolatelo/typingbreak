@echo off
REM Builds a standalone TypingBreakReminder.exe into the dist\ folder.
REM Run this from the typing-break-reminder folder on your Windows laptop.

py -m pip install --upgrade pip
py -m pip install -r requirements.txt pyinstaller
py -m PyInstaller --noconsole --onefile --name TypingBreakReminder TypingBreakReminder.py

echo.
echo Done! Your app is at dist\TypingBreakReminder.exe
pause
