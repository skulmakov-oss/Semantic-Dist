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
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}\bin"; Tasks: envPath; Check: NeedsAddPath(ExpandConstant('{app}\bin'))

; File association for .sm
Root: HKCU; Subkey: "Software\Classes\.sm"; ValueType: string; ValueName: ""; ValueData: "Semantic.SourceFile.1"; Flags: uninsdeletevalue; Tasks: assocSm
Root: HKCU; Subkey: "Software\Classes\.sm\OpenWithProgids"; ValueType: string; ValueName: "Semantic.SourceFile.1"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assocSm

Root: HKCU; Subkey: "Software\Classes\Semantic.SourceFile.1"; ValueType: string; ValueName: ""; ValueData: "Semantic Source File"; Flags: uninsdeletekey; Tasks: assocSm
Root: HKCU; Subkey: "Software\Classes\Semantic.SourceFile.1\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\bin\sm-launch.exe,0"; Tasks: assocSm
Root: HKCU; Subkey: "Software\Classes\Semantic.SourceFile.1\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\bin\sm-launch.exe"" ""%1"""; Tasks: assocSm

[Code]
// Helper function to prevent duplicate PATH entries
function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OrigPath) then
  begin
    Result := True;
    exit;
  end;
  // Look for the path with semicolons surrounding it
  Result := Pos(';' + UpperCase(Param) + ';', ';' + UpperCase(OrigPath) + ';') = 0;
end;

procedure RemovePath(Param: string);
var
  OrigPath, NewPath: string;
  P, L: Integer;
begin
  if RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OrigPath) then
  begin
    NewPath := OrigPath;
    Param := UpperCase(Param);
    P := Pos(';' + Param + ';', ';' + UpperCase(NewPath) + ';');
    if P > 0 then
    begin
      L := Length(Param);
      if (P = 1) then
        Delete(NewPath, 1, L + 1)
      else
        Delete(NewPath, P - 1, L + 1);
      RegWriteStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', NewPath);
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
  begin
    RemovePath(ExpandConstant('{app}\bin'));
  end;
end;
