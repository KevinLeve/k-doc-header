; Inno Setup script for K-Doc Header.
;
; Build the app first:
;   pyinstaller --noconfirm --clean packaging\kdoc_header.spec --distpath dist-final --workpath build-final
; Then compile this script (adjust the ISCC path if Inno Setup is installed elsewhere):
;   & "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" packaging\kdoc_header.iss

#define MyAppName "K-Doc Header"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "Kevin Bastin"
#define MyAppExeName "K-Doc Header.exe"
#define SourceDir "..\dist-final"
#define MyAppIcon "..\assets\kdoc_header.ico"

[Setup]
AppId={{A1F3C9E2-7B4D-4E6A-9C2F-3D8E5B6A1C4F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist-installer
OutputBaseFilename=KDocHeader-Setup-{#MyAppVersion}
SetupIconFile={#MyAppIcon}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoProductName={#MyAppName}
VersionInfoDescription={#MyAppName} {#MyAppVersion} Setup
VersionInfoCopyright={#MyAppPublisher}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "{#SourceDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
