[Setup]
AppId={{D7A8C0E6-19C4-4F26-B0D4-2A1D11A7A0F3}
AppName=GovPress_PDF_MD
AppVersion=1.0.0
AppPublisher=wavelen-jw
AppPublisherURL=https://github.com/wavelen-jw/GovPress_PDF_MD
AppSupportURL=https://github.com/wavelen-jw/GovPress_PDF_MD
AppUpdatesURL=https://github.com/wavelen-jw/GovPress_PDF_MD
VersionInfoCompany=wavelen-jw
VersionInfoDescription=Government press-release PDF to Markdown converter and editor.
VersionInfoProductName=GovPress_PDF_MD
VersionInfoProductVersion=1.0.0
VersionInfoCopyright=Copyright (c) 2026 wavelen-jw
DefaultDirName={autopf}\GovPress_PDF_MD
DefaultGroupName=GovPress_PDF_MD
DisableProgramGroupPage=yes
OutputDir=dist_installer
OutputBaseFilename=GovPress_PDF_MD_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

[Tasks]
Name: "desktopicon"; Description: "바탕 화면 바로 가기 생성"; GroupDescription: "추가 작업:"

[Files]
Source: "dist\GovPress_PDF_MD\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\GovPress_PDF_MD"; Filename: "{app}\GovPress_PDF_MD.exe"
Name: "{autodesktop}\GovPress_PDF_MD"; Filename: "{app}\GovPress_PDF_MD.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\GovPress_PDF_MD.exe"; Description: "GovPress_PDF_MD 실행"; Flags: nowait postinstall skipifsilent
