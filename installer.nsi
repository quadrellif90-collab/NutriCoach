; NutriCoach — installer Windows (NSIS)
; Installazione in Program Files; i dati utente restano in %USERPROFILE%\.nutricoach\
; e NON vengono toccati da installazione/aggiornamento (così i clienti e le misure
; sopravvivono senza migrazione).

!define APPNAME "NutriCoach"
!define APPNAMEFULL "NutriCoach - Gestione Nutrizione"
!define PUBLISHER "NutriCoach"
; VERSION passata dal CI come /DVERSION=X.Y.Z (makensis installer.nsi /DVERSION=1.0.0).
!ifndef VERSION
  !define VERSION "1.0.0"
!endif
!define INSTDIR "$PROGRAMFILES64\NutriCoach"

Name "NutriCoach - Gestione Nutrizione"
OutFile "NutriCoach-Setup-${VERSION}.exe"
InstallDir "${INSTDIR}"
RequestExecutionLevel admin
Icon "assets\icon.ico"
UninstallIcon "assets\icon.ico"

; I dati utente vivono fuori da INSTDIR -> non li includiamo e non li cancelliamo.
InstallDirRegKey HKLM "Software\NutriCoach" "InstallDir"

Section "Install"
  SetOutPath "$INSTDIR"
  ; File dell'app (EXE bundle da PyInstaller one-file) + icona.
  File "dist\NutriCoach.exe"
  File "assets\icon.ico"

  ; Scorciatoia nel menu Start e sul desktop
  CreateDirectory "$SMPROGRAMS\${APPNAME}"
  CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAMEFULL}.lnk" "$INSTDIR\NutriCoach.exe" "" "$INSTDIR\icon.ico" 0
  CreateShortCut "$DESKTOP\${APPNAMEFULL}.lnk" "$INSTDIR\NutriCoach.exe" "" "$INSTDIR\icon.ico" 0

  ; Disinstallatore
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\NutriCoach" "DisplayName" "${APPNAMEFULL}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\NutriCoach" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\NutriCoach" "DisplayVersion" "${VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\NutriCoach" "Publisher" "${PUBLISHER}"
  WriteRegStr HKLM "Software\NutriCoach" "InstallDir" "$INSTDIR"
SectionEnd

Section "Uninstall"
  ; NOTA: NON cancelliamo %USERPROFILE%\.nutricoach\ (dati/clienti utente).
  Delete "$SMPROGRAMS\${APPNAME}\${APPNAMEFULL}.lnk"
  Delete "$DESKTOP\${APPNAMEFULL}.lnk"
  RMDir "$SMPROGRAMS\${APPNAME}"
  Delete "$INSTDIR\NutriCoach.exe"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\NutriCoach"
  DeleteRegKey HKLM "Software\NutriCoach"
SectionEnd
