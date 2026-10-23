; Inno Setup Script for Semantic Language Toolchain & Native Launcher
; Produces Semantic-Setup-x64.exe

#define MyAppName "Semantic"
#define MyAppVersion "1.3.0-beta.1"
#define MyAppPublisher "skulmakov-oss"
#define MyAppURL "https://github.com/skulmakov-oss/Semantic"
#define MyAppExeName "sm-launch.exe"

[Setup]
AppId={{C6D6831A-AB8F-49CC-B5E0-70B34B3014D8}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\..\LICENSE
OutputDir=dist
OutputBaseFilename=Semantic-Setup-x64
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ChangesAssociations=yes
ChangesEnvironment=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "envPath"; Description: "Add Semantic bin directory to User PATH environment variable"; Flags: unchecked
Name: "assocSm"; Description: "Associate .sm files with Semantic Program Launcher"; Flags: checkedonce

[Files]
; Binaries
Source: "..\..\dist-staging\bin\smc.exe"; DestDir: "{app}\bin"; Flags: ignoreversion
Source: "..\..\dist-staging\bin\svm.exe"; DestDir: "{app}\bin"; Flags: ignoreversion
Source: "..\..\dist-staging\bin\sm-launch.exe"; DestDir: "{app}\bin"; Flags: ignoreversion
; Documentation & Licenses
Source: "..\..\README.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\..\LICENSE"; DestDir: "{app}\docs"; Flags: ignoreversion

[Registry]
; PATH environment variable update (User PATH)
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{code:GetNewPath}"; Tasks: envPath; Check: NeedsAddPath(ExpandConstant('{app}\bin'))
; Record whether installer actually added PATH so uninstaller only removes if added by setup
; AddedUserPath tracked via CurStepChanged

; File association for .sm
Root: HKCU; Subkey: "Software\Classes\.sm"; ValueType: string; ValueName: ""; ValueData: "Semantic.SourceFile.1"; Flags: uninsdeletevalue; Tasks: assocSm
Root: HKCU; Subkey: "Software\Classes\.sm\OpenWithProgids"; ValueType: string; ValueName: "Semantic.SourceFile.1"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assocSm

Root: HKCU; Subkey: "Software\Classes\Semantic.SourceFile.1"; ValueType: string; ValueName: ""; ValueData: "Semantic Source File"; Flags: uninsdeletekey; Tasks: assocSm
Root: HKCU; Subkey: "Software\Classes\Semantic.SourceFile.1\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\bin\sm-launch.exe,0"; Tasks: assocSm
Root: HKCU; Subkey: "Software\Classes\Semantic.SourceFile.1\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\bin\sm-launch.exe"" ""%1"""; Tasks: assocSm

[Code]
// Helper function to check if bin directory is already in user PATH
function NeedsAddPath(Param: string): boolean;
var
  OrigPath, TargetPart: string;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OrigPath) then
  begin
    Result := True;
    exit;
  end;
  TargetPart := ';' + UpperCase(Trim(Param)) + ';';
  Result := Pos(TargetPart, ';' + UpperCase(OrigPath) + ';') = 0;
end;

// Helper to calculate new PATH without introducing duplicate semicolons
function GetNewPath(Param: string): string;
var
  OrigPath, BinDir: string;
begin
  BinDir := ExpandConstant('{app}\bin');
  if RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OrigPath) then
  begin
    OrigPath := Trim(OrigPath);
    if OrigPath = '' then
      Result := BinDir
    else if (OrigPath[Length(OrigPath)] = ';') then
      Result := OrigPath + BinDir
    else
      Result := OrigPath + ';' + BinDir;
  end
  else
    Result := BinDir;
end;

procedure RemovePath(BinDir: string);
var
  OrigPath, NormPath, CleanedPath: string;
  SemiPos: Integer;
  Segment: string;
  First: Boolean;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OrigPath) then
    exit;

  NormPath := Trim(OrigPath);
  if NormPath = '' then
    exit;

  CleanedPath := '';
  First := True;

  while Length(NormPath) > 0 do
  begin
    SemiPos := Pos(';', NormPath);
    if SemiPos > 0 then
    begin
      Segment := Trim(Copy(NormPath, 1, SemiPos - 1));
      Delete(NormPath, 1, SemiPos);
    end
    else
    begin
      Segment := Trim(NormPath);
      NormPath := '';
    end;

    if (Segment <> '') and (CompareText(Segment, BinDir) <> 0) then
    begin
      if First then
      begin
        CleanedPath := Segment;
        First := False;
      end
      else
        CleanedPath := CleanedPath + ';' + Segment;
    end;
  end;

  RegWriteStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', CleanedPath);
end;


var
  ShouldAddUserPath: Boolean;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
  begin
    ShouldAddUserPath := WizardIsTaskSelected('envPath') and NeedsAddPath(ExpandConstant('{app}\bin'));
  end;
  if CurStep = ssPostInstall then
  begin
    if ShouldAddUserPath then
    begin
      RegWriteDWordValue(HKEY_CURRENT_USER, 'Software\Semantic', 'AddedUserPath', 1);
    end;
  end;
end;
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  AddedPathVal: Cardinal;
begin
  if CurUninstallStep = usUninstall then
  begin
    // Only remove PATH if this installation recorded that it modified user PATH
    if RegQueryDWordValue(HKEY_CURRENT_USER, 'Software\Semantic', 'AddedUserPath', AddedPathVal) and (AddedPathVal = 1) then
    begin
      RemovePath(ExpandConstant('{app}\bin'));
      RegDeleteValue(HKEY_CURRENT_USER, 'Software\Semantic', 'AddedUserPath');
      RegDeleteKeyIfEmpty(HKEY_CURRENT_USER, 'Software\Semantic');
    end;
  end;
end;
