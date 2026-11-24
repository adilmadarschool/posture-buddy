@echo off
REM Builds PostureBuddy.exe, PostureBuddyTest.exe (5-second version) and,
REM if Inno Setup 6 is installed, the installers. Everything lands in dist\
python -m pip install -r requirements.txt pyinstaller || goto :err
python -m PyInstaller --noconfirm --onefile --noconsole --name PostureBuddy --hidden-import pystray._win32 posture_buddy.py || goto :err
python -m PyInstaller --noconfirm --onefile --noconsole --name PostureBuddyTest --hidden-import pystray._win32 posture_buddy_test.py || goto :err

set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist %ISCC% (
  %ISCC% installer.iss || goto :err
  %ISCC% /DTEST installer.iss || goto :err
  echo.
  echo Installers: dist\PostureBuddy-Setup.exe and dist\PostureBuddy-Test-Setup.exe
) else (
  echo.
  echo Inno Setup 6 not found - skipped the installers. Get it free from https://jrsoftware.org/isdl.php
  echo Standalone apps: dist\PostureBuddy.exe and dist\PostureBuddyTest.exe
)
pause
exit /b 0
:err
echo BUILD FAILED
pause
exit /b 1
