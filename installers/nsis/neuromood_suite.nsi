; neuromood_suite.nsi - Instalador NSIS para NeuroMood Suite

Unicode true
RequestExecutionLevel user

!include "common.nsh"

; Nombre del instalador y archivo de salida
Name "${NM_SUITE_NAME}"
OutFile "..\..\dist\NM_Suite_Setup.exe"

; Directorio de instalación predeterminado
InstallDir "${NM_SUITE_DEFAULT_DIR}"

; Guardar la carpeta de instalación en el registro para actualizaciones/desinstalación
InstallDirRegKey HKCU "Software\${NM_SUITE_REG_KEY}" "InstallDir"

; Modern UI 2
!include "MUI2.nsh"
!include "FileFunc.nsh"

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "${NM_ICON_INSTALLER}"
!define MUI_UNICON "${NM_ICON_UNINSTALL}"

; Brand assets (Linen & Sage)
!define MUI_WELCOMEFINISHPAGE_BITMAP     "${NM_SUITE_BMP_WELCOME}"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP           "${NM_SUITE_BMP_HEADER}"
!define MUI_HEADERIMAGE_RIGHT
; El DESINSTALADOR usa la misma identidad: sin este define, MUI cae al
; arte default de NSIS (win.bmp) en las páginas un.Welcome/un.Finish
; (informe owner v1.0: "los uninstallers pierden su diseño al recompilar").
; OJO: el uninstall.exe ya instalado en una máquina NO se actualiza al
; recompilar este script — recién al reinstalar con el setup nuevo.
!define MUI_UNWELCOMEFINISHPAGE_BITMAP   "${NM_SUITE_BMP_WELCOME}"
!define MUI_HEADERIMAGE_UNBITMAP         "${NM_SUITE_BMP_HEADER}"

; Textos personalizados para el Wizard
!define MUI_WELCOMEPAGE_TITLE "Bienvenido a tu espacio de calma"
!define MUI_WELCOMEPAGE_TEXT "Este asistente preparará la instalación local de NeuroMood Suite en tu equipo.$\r$\n$\r$\nTus datos, registros de bienestar y privacidad se mantendrán seguros de forma local. Al finalizar, un asistente en la aplicación te guiará en el primer inicio de sesión y consentimiento clínico (no se realiza configuración de cuenta durante la instalación)."

!define MUI_DIRECTORYPAGE_TEXT_DESTINATION "Elegí la carpeta donde querés instalar NeuroMood Suite (instalación privada de usuario)."

; Bienvenido
!insertmacro MUI_PAGE_WELCOME
; Carpeta de instalación
!insertmacro MUI_PAGE_DIRECTORY
; Accesos y tareas
!insertmacro MUI_PAGE_COMPONENTS
; Instalando
!insertmacro MUI_PAGE_INSTFILES

; Finalizar
!define MUI_FINISHPAGE_TITLE "Todo listo para comenzar, respira."
!define MUI_FINISHPAGE_TEXT "NeuroMood Suite se instaló correctamente.$\r$\n$\r$\nAl iniciar la aplicación por primera vez, se te guiará a través del proceso de inicio de sesión y la firma de consentimiento legal para proteger tus datos de salud mental."
!define MUI_FINISHPAGE_RUN "$INSTDIR\${NM_SUITE_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "Ejecutar NeuroMood Suite"
!insertmacro MUI_PAGE_FINISH

; Páginas del desinstalador (con identidad de marca).
; MUI2 NO tiene MUI_UNWELCOMEPAGE_*/MUI_UNFINISHPAGE_*: las páginas un.*
; leen MUI_WELCOMEPAGE_*/MUI_FINISHPAGE_* re-definidos ANTES de cada
; !insertmacro (MUI los des-define tras cada inserción). Los defines UN*
; anteriores no existían y el desinstalador mostraba los textos default.
!define MUI_WELCOMEPAGE_TITLE "Vas a desinstalar NeuroMood Suite"
!define MUI_WELCOMEPAGE_TEXT "Este asistente te guiará para quitar NeuroMood Suite de tu equipo.$\r$\n$\r$\nPodrás decidir si conservás o eliminás tu carpeta de datos locales (historial de bienestar, base de datos y consentimientos firmados). Conservarlos te permite recuperar todo si reinstalás más adelante."
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!define MUI_FINISHPAGE_TITLE "NeuroMood Suite se desinstaló"
!define MUI_FINISHPAGE_TEXT "Gracias por confiar en NeuroMood. Cuidá tu bienestar; acá vas a estar siempre que lo necesites."
!insertmacro MUI_UNPAGE_FINISH

; Idioma
!insertmacro MUI_LANGUAGE "Spanish"

; Variables
Var DeleteAppData

; =============================================================================
; Secciones del instalador
; =============================================================================

Section "NeuroMood Suite (Requerido)" SecApp
  SectionIn RO
  SetOutPath "$INSTDIR"

  ; Cerrar una instancia previa (puede estar minimizada en bandeja) para que no
  ; bloquee el reemplazo de archivos al actualizar/reinstalar.
  nsExec::Exec 'taskkill /F /IM "${NM_SUITE_EXE}"'
  Sleep 800

  ; Limpieza mecánica de payloads anteriores
  RMDir /r "$INSTDIR\_internal"
  Delete "$INSTDIR\base_library.zip"
  Delete "$INSTDIR\install_path.txt"
  Delete "$INSTDIR\.neuromood_install_manifest.json"
  
  ; Copiar archivos de payload principal
  File /r "${NM_SUITE_DIST_DIR}\*"
  
  ; Copiar iconos para accesos directos
  File "${NM_ICON_APP}"
  File "${NM_ICON_UNINSTALL}"
  
  ; Copiar .env runtime a AppData (credenciales Supabase publicas).
  ; El guard es de TIEMPO DE COMPILACION (!if /FileExists): si el build generó
  ; build/runtime_env/suite/.env, se empaqueta y SIEMPRE se extrae en la máquina
  ; del usuario. Un guard de runtime (IfFileExists sobre una ruta relativa al
  ; instalador) jamás existe en destino y saltearía la extracción, dejando la
  ; Suite sin SUPABASE_URL/KEY. NO volver a un IfFileExists de runtime acá.
  !if /FileExists "..\..\build\runtime_env\suite\.env"
    CreateDirectory "$APPDATA\${NM_SUITE_APPDATA_DIR}"
    File /oname=$APPDATA\${NM_SUITE_APPDATA_DIR}\.env "..\..\build\runtime_env\suite\.env"
    SetFileAttributes "$APPDATA\${NM_SUITE_APPDATA_DIR}\.env" HIDDEN
  !endif

  ; Escribir el desinstalador
  WriteUninstaller "$INSTDIR\uninstall.exe"
  
  ; Guardar directorio de instalación en registro
  WriteRegStr HKCU "Software\${NM_SUITE_REG_KEY}" "InstallDir" "$INSTDIR"

  ; Registro de desinstalación en Apps & Features (HKCU)
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NM_SUITE_REG_KEY}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NM_SUITE_REG_KEY}" "DisplayName" "${NM_SUITE_NAME}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NM_SUITE_REG_KEY}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NM_SUITE_REG_KEY}" "DisplayIcon" "$INSTDIR\no_symbol.ico"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NM_SUITE_REG_KEY}" "DisplayVersion" "${NM_SUITE_VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NM_SUITE_REG_KEY}" "Publisher" "${NM_PUBLISHER}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NM_SUITE_REG_KEY}" "URLInfoAbout" "${NM_URL_PRODUCT}"
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NM_SUITE_REG_KEY}" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NM_SUITE_REG_KEY}" "NoRepair" 1

  ; Acceso directo en el Menú Inicio (siempre creado)
  CreateDirectory "$SMPROGRAMS\NeuroMood"
  CreateShortcut "$SMPROGRAMS\NeuroMood\${NM_SUITE_NAME}.lnk" "$INSTDIR\${NM_SUITE_EXE}" "" "$INSTDIR\NM_icon.ico" 0
SectionEnd

Section "Crear acceso directo en el escritorio" SecDesktop
  CreateShortcut "$DESKTOP\${NM_SUITE_NAME}.lnk" "$INSTDIR\${NM_SUITE_EXE}" "" "$INSTDIR\NM_icon.ico" 0
SectionEnd

; =============================================================================
; Lógica del desinstalador
; =============================================================================

Function un.onInit
  ${GetParameters} $R0
  ClearErrors
  ${GetOptions} $R0 "/DELETEAPPDATA" $R1
  IfErrors no_delete_switch
    StrCpy $DeleteAppData "1"
    Goto done_switch
  no_delete_switch:
    StrCpy $DeleteAppData "0"
  done_switch:
FunctionEnd

Section "Uninstall"
  ; Confirmación interactiva si no hay flag /DELETEAPPDATA y no es silencioso
  StrCmp $DeleteAppData "1" delete_appdata
  IfSilent skip_dialog
  
  MessageBox MB_YESNO|MB_DEFBUTTON2|MB_ICONQUESTION \
    "Estás desinstalando NeuroMood Suite.$\r$\n¿Deseás eliminar también tu carpeta de datos locales y configuraciones?$\r$\nUbicación: $APPDATA\${NM_SUITE_APPDATA_DIR}$\r$\n$\r$\nImportante: Si elegís 'Sí', se borrarán de forma definitiva tu historial de bienestar, la base de datos local y los consentimientos firmados. Conservar estos datos (eligiendo 'No') te permitirá recuperarlos si reinstalás la aplicación en el futuro.$\r$\n$\r$\nNota: Los datos profesionales de NeuroMood Hub no se verán afectados." \
    IDNO skip_dialog
    StrCpy $DeleteAppData "1"
  skip_dialog:
  
  delete_appdata:
  
  ; Guardas de seguridad para no borrar directorios del sistema
  StrCmp $INSTDIR "" safe_done
  StrCmp $INSTDIR "$PROFILE" safe_done
  StrCmp $INSTDIR "$APPDATA" safe_done
  StrCmp $INSTDIR "$PROGRAMFILES" safe_done
  StrCmp $INSTDIR "$WINDIR" safe_done

  ; Cerrar la app si sigue corriendo (minimizada en bandeja o proceso huérfano).
  ; Sin esto el .exe y _internal quedan BLOQUEADOS → la carpeta no se borra y los
  ; procesos quedan vivos tras desinstalar (a diferencia del Hub, que sí cierra).
  nsExec::Exec 'taskkill /F /IM "${NM_SUITE_EXE}"'
  Sleep 800

  ; Eliminar accesos directos
  Delete "$SMPROGRAMS\NeuroMood\${NM_SUITE_NAME}.lnk"
  RMDir "$SMPROGRAMS\NeuroMood"
  Delete "$DESKTOP\${NM_SUITE_NAME}.lnk"

  ; Eliminar archivos instalados
  RMDir /r "$INSTDIR\_internal"
  Delete "$INSTDIR\${NM_SUITE_EXE}"
  Delete "$INSTDIR\uninstall.exe"
  Delete "$INSTDIR\NM_icon.ico"
  Delete "$INSTDIR\no_symbol.ico"
  Delete "$INSTDIR\base_library.zip"
  Delete "$INSTDIR\install_path.txt"
  Delete "$INSTDIR\.neuromood_install_manifest.json"
  
  ; Eliminar el directorio completo (incluye restos: logs, .env de fallback, etc.)
  RMDir /r "$INSTDIR"

  ; Eliminar AppData si se solicitó
  StrCmp $DeleteAppData "1" 0 skip_appdata_delete
    RMDir /r "$APPDATA\${NM_SUITE_APPDATA_DIR}"
  skip_appdata_delete:

  ; Eliminar registros
  DeleteRegKey HKCU "Software\${NM_SUITE_REG_KEY}"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NM_SUITE_REG_KEY}"
  ; Quitar el arranque automático ("Iniciar con Windows") por si quedó activo —
  ; si no, Windows intentaría lanzar un .exe ya borrado en cada inicio de sesión.
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "NeuroMood"

safe_done:
SectionEnd
