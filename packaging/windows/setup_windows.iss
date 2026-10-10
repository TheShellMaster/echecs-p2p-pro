; Script Inno Setup 6 pour Échecs P2P Pro v2.1.0
; Génère un véritable installeur Setup Windows guidé

#define MyAppName "Échecs P2P Pro"
#define MyAppVersion "2.1.0"
#define MyAppPublisher "Échecs P2P Studio"
#define MyAppURL "https://github.com/echecs-p2p"
#define MyAppExeName "EchecsP2P.exe"

[Setup]
AppId={{8B1A2C3D-4E5F-6A7B-8C9D-0E1F2A3B4C5D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=LISEZMOI_COMPATIBILITE.md
OutputDir=..\..\distribution
OutputBaseFilename=Setup-EchecsP2P-v2.1.0
SetupIconFile=..\..\assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardSmallImageFile=..\..\assets\icon.png
DisableWelcomePage=no

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\dist\EchecsP2P\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\assets\icon.ico"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "..\..\assets\logo.png"; DestDir: "{app}\assets"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
