# Posture Buddy

A goofy character slides in from the right edge of your screen every 30-60 minutes
(random) and says "Hi, mind your posture!" or another phrase. Click it to send it away.
Five characters: Spud the potato, Prickles the cactus, Dr. Boo the ghost,
Pidge the pigeon, Sir Curve the banana.

## Run it
    pip install -r requirements.txt
    python posture_buddy.py --fast      # test mode: appears every 10-20 seconds

## Build the .exe and installers
Double-click `build.bat` on Windows (needs Python 3.9+; Inno Setup 6 is optional, for the installers).
Output in `dist\`:
- `PostureBuddy-Setup.exe` - installer (Start menu entry, optional start-with-Windows, uninstaller)
- `PostureBuddy-Test-Setup.exe` - installer for the TEST version (character every 5 seconds)
- `PostureBuddy.exe` / `PostureBuddyTest.exe` - the standalone apps

No Windows machine handy? Push this folder to a GitHub repo and run the "Build Windows installers"
workflow (Actions tab); download the .exe files from the run's artifacts.

The test version runs side by side with the normal one (separate name and autostart entry).

## Tray icon (potato face)
Say hi now / Pause / Start with Windows / Quit

## Notes
- Skips its visit (retries in 5 min) when a fullscreen app is in front.
- Only one copy can run at a time.
- Tweak the interval, phrases and hold time at the top of `posture_buddy.py`.
- Unsigned .exe files can trigger a SmartScreen warning: More info > Run anyway.
