; Inno Setup script -> builds PostureBuddy-Setup.exe
; Normal build:  iscc installer.iss
; Test build:    iscc /DTEST installer.iss   (installs the 5-second test version)
#ifdef TEST
  #define AutoRunName "PostureBuddyTest"
  #define AppName "Posture Buddy (Test)"
  #define ExeName "PostureBuddyTest.exe"
  #define OutName "PostureBuddy-Test-Setup"
  #define AppId "{{6B0D2F1C-3A54-4E1B-9D55-7C1B0F7A2E11}"
#else
  #define AutoRunName "PostureBuddy"
  #define AppName "Posture Buddy"
  #define ExeName "PostureBuddy.exe"
  #define OutName "PostureBuddy-Setup"
  #define AppId "{{A3F7C2D9-5E18-4B6A-8C42-1D9E0B7F5A60}"
#endif

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion=1.0
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=dist
OutputBaseFilename={#OutName}
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\{#ExeName}
DisableProgramGroupPage=yes
WizardStyle=modern

[Tasks]
Name: "startup"; Description: "Start {#AppName} when I sign in to Windows"; Flags: checkedonce
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Files]
Source: "dist\{#ExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#ExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#ExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; \
  ValueName: "{#AutoRunName}"; ValueData: """{app}\{#ExeName}"" --quiet"; \
  Tasks: startup; Flags: uninsdeletevalue

[Run]
Filename: "{app}\{#ExeName}"; Description: "Launch {#AppName} now"; Flags: nowait postinstall skipifsilent
