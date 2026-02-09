; AI Input Method Tool - Windows Installer Script
; NSIS (Nullsoft Scriptable Install System) configuration
; Creates professional Windows installer with proper uninstallation support

!define APP_NAME "AI Input Method Tool"
; Version will be set dynamically by build script
!ifndef APP_VERSION
    !define APP_VERSION "0.02"
!endif
!define APP_PUBLISHER "AI Input Method Team"
!define APP_URL "https://github.com/ai-input-method/ai-input-method"
!define APP_EXECUTABLE "reInput.exe"
!define APP_REGISTRY_KEY "Software\${APP_PUBLISHER}\${APP_NAME}"
!define UNINSTALL_REGISTRY_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"

; Include modern UI
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"
!include "WinVer.nsh"

; Installer properties
Name "${APP_NAME}"
OutFile "..\dist\ai-input-method-installer-${APP_VERSION}.exe"
InstallDir "$PROGRAMFILES64\${APP_NAME}"
InstallDirRegKey HKLM "${APP_REGISTRY_KEY}" ""
RequestExecutionLevel admin
ShowInstDetails show
ShowUnInstDetails show

; Version information
VIProductVersion "0.1.0.0"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "ProductVersion" "${APP_VERSION}"
VIAddVersionKey "CompanyName" "${APP_PUBLISHER}"
VIAddVersionKey "FileDescription" "AI-powered input method tool for Windows"
VIAddVersionKey "FileVersion" "${APP_VERSION}"
VIAddVersionKey "LegalCopyright" "© 2025 ${APP_PUBLISHER}"

; Modern UI Configuration
!define MUI_ABORTWARNING
; Icon configuration disabled due to invalid icon file
; !define MUI_ICON "..\..\app.ico"
; !define MUI_UNICON "..\..\app.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Header\nsis3-metro.bmp"
!define MUI_WELCOMEFINISHPAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Wizard\nsis3-metro.bmp"

; Installer pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXECUTABLE}"
!define MUI_FINISHPAGE_RUN_TEXT "Launch ${APP_NAME}"
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Languages
!insertmacro MUI_LANGUAGE "English"

; Installation sections
Section "Core Application" SecCore
    SectionIn RO  ; Required section
    
    DetailPrint "Installing ${APP_NAME} core application..."
    
    ; Set output path
    SetOutPath "$INSTDIR"
    
    ; Install main application files
    File "..\dist\reInput.exe"
    File "..\app.ico"
    File "..\LICENSE"
    
    ; Install configuration files
    File "..\dist\settings.toml"
    File "..\dist\settings.toml.example"
    
    ; Create application data directory
    CreateDirectory "$APPDATA\${APP_NAME}"
    
    ; Write registry keys
    WriteRegStr HKLM "${APP_REGISTRY_KEY}" "" $INSTDIR
    WriteRegStr HKLM "${APP_REGISTRY_KEY}" "Version" "${APP_VERSION}"
    WriteRegStr HKLM "${APP_REGISTRY_KEY}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "${APP_REGISTRY_KEY}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "${APP_REGISTRY_KEY}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "${APP_REGISTRY_KEY}" "DisplayVersion" "${APP_VERSION}"
    
    ; Uninstaller registry information
    WriteRegStr HKLM "${UNINSTALL_REGISTRY_KEY}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "${UNINSTALL_REGISTRY_KEY}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKLM "${UNINSTALL_REGISTRY_KEY}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "${UNINSTALL_REGISTRY_KEY}" "URLInfoAbout" "${APP_URL}"
    WriteRegStr HKLM "${UNINSTALL_REGISTRY_KEY}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "${UNINSTALL_REGISTRY_KEY}" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "${UNINSTALL_REGISTRY_KEY}" "QuietUninstallString" "$INSTDIR\uninstall.exe /S"
    WriteRegDWORD HKLM "${UNINSTALL_REGISTRY_KEY}" "NoModify" 1
    WriteRegDWORD HKLM "${UNINSTALL_REGISTRY_KEY}" "NoRepair" 1
    
    ; Calculate and write installation size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "${UNINSTALL_REGISTRY_KEY}" "EstimatedSize" "$0"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
    
SectionEnd

Section "Desktop Shortcut" SecDesktop
    DetailPrint "Creating desktop shortcut..."
    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXECUTABLE}" \
        "" "$INSTDIR\${APP_EXECUTABLE}" 0 SW_SHOWNORMAL \
        "" "AI-powered input method tool"
SectionEnd

Section "Start Menu Shortcuts" SecStartMenu
    DetailPrint "Creating start menu shortcuts..."
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXECUTABLE}" \
        "" "$INSTDIR\${APP_EXECUTABLE}" 0 SW_SHOWNORMAL \
        "" "AI-powered input method tool"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe" \
        "" "$INSTDIR\uninstall.exe" 0 SW_SHOWNORMAL \
        "" "Uninstall ${APP_NAME}"
SectionEnd

Section "Auto-start with Windows" SecAutoStart
    DetailPrint "Setting up auto-start..."
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "${APP_NAME}" "$INSTDIR\${APP_EXECUTABLE}"
SectionEnd

; Section descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecCore} "Core application files (required)"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} "Create desktop shortcut"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} "Create start menu shortcuts"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecAutoStart} "Start automatically with Windows"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; Installer functions
Function .onInit
    ; Check Windows version
    ${IfNot} ${AtLeastWin10}
        MessageBox MB_OK|MB_ICONSTOP "This application requires Windows 10 or later."
        Abort
    ${EndIf}
    
    ; Check if already installed
    ReadRegStr $R0 HKLM "${APP_REGISTRY_KEY}" ""
    ${If} $R0 != ""
        MessageBox MB_YESNO|MB_ICONQUESTION \
            "${APP_NAME} is already installed in $R0.$\n$\nDo you want to uninstall the previous version?" \
            IDYES uninst IDNO done
        
        uninst:
            ; Run uninstaller
            ExecWait '$R0\uninstall.exe /S _?=$R0'
            ; Wait for uninstaller to finish
            Sleep 2000
            
        done:
    ${EndIf}
    
    ; Check for running instances
    FindWindow $R0 "Qt5QWindowIcon" "${APP_NAME}"
    ${If} $R0 != 0
        MessageBox MB_YESNO|MB_ICONEXCLAMATION \
            "${APP_NAME} is currently running. Please close it before installing.$\n$\nDo you want to continue anyway?" \
            IDYES continue IDNO abort
        
        abort:
            Abort
        continue:
    ${EndIf}
FunctionEnd

Function .onInstSuccess
    ; Show completion message
    DetailPrint "Installation completed successfully!"
    
    ; Optional: Check for required runtimes
    DetailPrint "Checking for Microsoft Visual C++ Redistributable..."
    ; Add runtime checks here if needed
FunctionEnd

; Uninstaller section
Section "Uninstall"
    DetailPrint "Removing ${APP_NAME}..."
    
    ; Stop any running instances
    FindWindow $R0 "Qt5QWindowIcon" "${APP_NAME}"
    ${If} $R0 != 0
        DetailPrint "Closing running application..."
        SendMessage $R0 ${WM_CLOSE} 0 0
        Sleep 2000
    ${EndIf}
    
    ; Remove application files
    Delete "$INSTDIR\reInput.exe"
    Delete "$INSTDIR\app.ico"
    Delete "$INSTDIR\LICENSE"
    Delete "$INSTDIR\settings.toml"
    Delete "$INSTDIR\settings.toml.example"
    Delete "$INSTDIR\uninstall.exe"
    
    ; Remove installation directory if empty
    RMDir "$INSTDIR"
    
    ; Remove shortcuts
    Delete "$DESKTOP\${APP_NAME}.lnk"
    RMDir /r "$SMPROGRAMS\${APP_NAME}"
    
    ; Remove auto-start entry
    DeleteRegValue HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "${APP_NAME}"
    
    ; Remove registry keys
    DeleteRegKey HKLM "${UNINSTALL_REGISTRY_KEY}"
    DeleteRegKey HKLM "${APP_REGISTRY_KEY}"
    
    ; Remove application data (ask user)
    MessageBox MB_YESNO|MB_ICONQUESTION \
        "Do you want to remove application settings and data?$\n$\nSelect No if you plan to reinstall later." \
        IDNO skip_appdata
        
    RMDir /r "$APPDATA\${APP_NAME}"
    
    skip_appdata:
    
    DetailPrint "Uninstallation completed!"
SectionEnd

; Uninstaller functions
Function un.onInit
    MessageBox MB_YESNO|MB_ICONQUESTION \
        "Are you sure you want to uninstall ${APP_NAME}?" \
        IDYES continue IDNO abort
    abort:
        Abort
    continue:
FunctionEnd

Function un.onUninstSuccess
    MessageBox MB_OK|MB_ICONINFORMATION \
        "${APP_NAME} has been successfully removed from your computer."
FunctionEnd