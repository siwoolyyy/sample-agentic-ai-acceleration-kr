[Setup]
AppId={{D244F39D-2828-4504-8291-38511F96D581}
AppName=AWSome Gateway
AppVersion=0.1.0
DefaultDirName={autopf}\AWSomeGateway
DefaultGroupName=AWSome Gateway
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#Out}
OutputBaseFilename=AWSomeGatewaySetup-Windows-x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
InfoBeforeFile=before-install.txt
UninstallDisplayIcon={app}\login\GatewayLogin.exe

[Languages]
#if FileExists(AddBackslash(CompilerPath) + "Languages\Korean.isl")
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"
#endif
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: desktop; Description: "Configure Claude Desktop for the company Gateway (all users of this PC)"; Flags: checkedonce

[Files]
Source: "{#Stage}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\AWSome Gateway Login"; Filename: "{app}\login\GatewayLogin.exe"

[Run]
Filename: "{app}\login\GatewayLogin.exe"; Description: "Open company account login"; Flags: postinstall nowait skipifsilent runasoriginaluser

[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var Names: TArrayOfString;
begin
  Result := '';
  if WizardIsTaskSelected('desktop') and not FileExists(ExpandConstant('{app}\desktop-policy-state.json')) then begin
    if RegGetValueNames(HKLM64, 'SOFTWARE\Policies\Claude', Names) then
      if GetArrayLength(Names) > 0 then
        Result := 'Existing Claude policy detected. Contact IT; it will not be overwritten.';
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var Code: Integer;
begin
  if (CurStep = ssPostInstall) and WizardIsTaskSelected('desktop') then begin
    if not Exec(ExpandConstant('{app}\helper\api-key-helper.exe'), '--install-desktop', '', SW_HIDE, ewWaitUntilTerminated, Code) then
      RaiseException('Claude Desktop setup could not start. Contact IT.');
    if Code <> 0 then RaiseException('Claude Desktop policy was not applied. Existing policy was preserved. Contact IT.');
  end;
end;

function InitializeUninstall(): Boolean;
var Code: Integer;
begin
  Result := Exec(ExpandConstant('{app}\helper\api-key-helper.exe'), '--remove-desktop', '', SW_HIDE, ewWaitUntilTerminated, Code);
  if Result then Result := Code = 0;
  if not Result then MsgBox('Policy restore failed. Uninstall was stopped; contact IT.', mbError, MB_OK);
end;
