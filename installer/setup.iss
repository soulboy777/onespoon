; ============================================================
; Inno Setup — Agent 开发助手 安装脚本
; ============================================================

[Setup]
AppName=Agent开发助手
AppVersion=0.2.0
AppPublisher=soulboy777
AppPublisherURL=https://github.com/soulboy777/onespoon
AppSupportURL=https://github.com/soulboy777/onespoon/issues
AppUpdatesURL=https://github.com/soulboy777/onespoon/releases
DefaultDirName={autopf}\AgentDev
DefaultGroupName=Agent开发助手
OutputDir=.\dist
OutputBaseFilename=AgentDev-Setup-0.2.0
SetupIconFile=..\icon\agent-dev.ico
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\agent-dev.exe
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "chinese"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Files]
Source: "..\dist\agent-dev\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Agent开发助手"; Filename: "{app}\agent-dev.exe"
Name: "{group}\Agent开发助手 (桌面UI)"; Filename: "{app}\agent-dev.exe"; Parameters: "desktop"
Name: "{group}\卸载 Agent开发助手"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Agent开发助手"; Filename: "{app}\agent-dev.exe"; Parameters: "desktop"
Name: "{userstartup}\Agent开发助手"; Filename: "{app}\agent-dev.exe"; Parameters: "desktop"

[Registry]
; 开机启动
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
    ValueType: string; ValueName: "AgentDev"; ValueData: "{app}\agent-dev.exe desktop"; \
    Flags: uninsdeletevalue

[Run]
Filename: "{app}\agent-dev.exe"; Parameters: "desktop"; \
    Description: "启动桌面助手"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "taskkill"; Parameters: "/f /im agent-dev.exe"; Flags: runhidden

[Code]
function InitializeSetup: Boolean;
begin
  Result := True;
end;
