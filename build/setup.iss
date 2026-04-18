; 德语学习助手 - Inno Setup安装脚本
; 用于创建Windows安装程序

#define MyAppName "德语学习助手"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Deutsch Lernen Team"
#define MyAppURL "https://github.com/deutsch-lernen"
#define MyAppExeName "DeutschLernenApp.exe"

[Setup]
; 应用ID
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; 安装目录
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; 输出设置
OutputDir=..\dist
OutputBaseFilename=DeutschLernenApp_Setup_{#MyAppVersion}
SetupIconFile=..\resources\icons\app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

; 压缩设置
Compression=lzma2/ultra64
SolidCompression=yes

; 权限
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; 外观
WizardStyle=modern
WizardSizePercent=120

; 语言
ShowLanguageDialog=auto

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; 主程序
Source: "..\dist\DeutschLernenApp\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\DeutschLernenApp\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; 配置文件
Source: "..\config.json"; DestDir: "{app}"; Flags: onlyifdoesntexist

; 资源文件
Source: "..\resources\*"; DestDir: "{app}\resources"; Flags: ignoreversion recursesubdirs createallsubdirs

; 文档
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion; Check: FileExists(ExpandConstant('..\LICENSE'))

[Dirs]
Name: "{app}\data"; Permissions: users-modify
Name: "{app}\logs"; Permissions: users-modify
Name: "{app}\exports"; Permissions: users-modify

[Icons]
; 开始菜单
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; 桌面快捷方式
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; 快速启动
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; 安装完成后运行
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\exports"
Type: files; Name: "{app}\config.json"

[Code]
// 检查Python是否安装
function IsPythonInstalled(): Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('python', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

// 检查FFmpeg是否安装
function IsFFmpegInstalled(): Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('ffmpeg', '-version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

// 安装前检查
function InitializeSetup(): Boolean;
begin
  Result := True;
  
  // 提示用户
  if not IsPythonInstalled() then
  begin
    if MsgBox('未检测到Python环境。' + #13#10 + 
              '本应用需要Python 3.8或更高版本。' + #13#10 + #13#10 +
              '是否继续安装？' + #13#10 +
              '(建议先安装Python: https://www.python.org/downloads/)',
              mbConfirmation, MB_YESNO) = IDNO then
      Result := False;
  end;
  
  if Result and not IsFFmpegInstalled() then
  begin
    if MsgBox('未检测到FFmpeg。' + #13#10 + 
              '音频处理功能需要FFmpeg。' + #13#10 + #13#10 +
              '是否继续安装？' + #13#10 +
              '(可从 https://ffmpeg.org/download.html 下载)',
              mbConfirmation, MB_YESNO) = IDNO then
      Result := False;
  end;
end;

// 安装后配置
procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigPath: String;
begin
  if CurStep = ssPostInstall then
  begin
    // 更新配置文件路径
    ConfigPath := ExpandConstant('{app}\config.json');
    if FileExists(ConfigPath) then
    begin
      // 可以在这里修改配置
    end;
  end;
end;