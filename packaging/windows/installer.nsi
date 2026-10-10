; Script NSIS Modern UI pour Échecs P2P Pro v2.1.0
!include "MUI2.nsh"
!include "FileFunc.nsh"

Name "Échecs P2P Pro"
OutFile "..\..\distribution\Setup-EchecsP2P-v2.exe"
InstallDir "$PROGRAMFILES64\EchecsP2P"
InstallDirRegKey HKLM "Software\EchecsP2P" "Install_Dir"
RequestExecutionLevel admin

!define MUI_ICON "..\..\assets\icon.ico"
!define MUI_UNICON "..\..\assets\icon.ico"
!define MUI_ABORTWARNING

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "French"

Section "EchecsP2P (obligatoire)" SecCore
    SetOutPath "$INSTDIR"
    File /r "..\..\dist\EchecsP2P\*.*"
    File "..\..\assets\icon.ico"
    File "..\..\assets\logo.png"

    WriteRegStr HKLM "Software\EchecsP2P" "Install_Dir" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EchecsP2P" "DisplayName" "Échecs P2P Pro"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EchecsP2P" "UninstallString" '"$INSTDIR\uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EchecsP2P" "DisplayIcon" '"$INSTDIR\icon.ico"'
    WriteUninstaller "$INSTDIR\uninstall.exe"

    CreateDirectory "$SMPROGRAMS\Échecs P2P Pro"
    CreateShortcut "$SMPROGRAMS\Échecs P2P Pro\Échecs P2P Pro.lnk" "$INSTDIR\EchecsP2P.exe" "" "$INSTDIR\icon.ico" 0
    CreateShortcut "$SMPROGRAMS\Échecs P2P Pro\Désinstaller.lnk" "$INSTDIR\uninstall.exe"
    CreateShortcut "$DESKTOP\Échecs P2P Pro.lnk" "$INSTDIR\EchecsP2P.exe" "" "$INSTDIR\icon.ico" 0
SectionEnd

Section "Uninstall"
    RMDir /r "$INSTDIR"
    Delete "$SMPROGRAMS\Échecs P2P Pro\*.*"
    RMDir "$SMPROGRAMS\Échecs P2P Pro"
    Delete "$DESKTOP\Échecs P2P Pro.lnk"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EchecsP2P"
    DeleteRegKey HKLM "Software\EchecsP2P"
SectionEnd
