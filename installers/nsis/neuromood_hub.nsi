; neuromood_hub.nsi - Instalador NSIS para NeuroMood Hub

Unicode true
RequestExecutionLevel user

!include "common.nsh"

; Nombre del instalador y archivo de salida
Name "${NM_HUB_NAME}"
OutFile "..\..\dist\NM_Hub_Setup.exe"

; Directorio de instalación predeterminado
InstallDir "${NM_HUB_DEFAULT_DIR}"

; Guardar la carpeta de instalación en el registro para actualizaciones/desinstalación
InstallDirRegKey HKCU "Software\${NM_HUB_REG_KEY}" "InstallDir"

; Modern UI 2
!include "MUI2.nsh"
!include "FileFunc.nsh"

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "${NM_ICON_INSTALLER}"
!define MUI_UNICON "${NM_ICON_UNINSTALL}"

; Brand assets (Hub azul profesional)
!define MUI_WELCOMEFINISHPAGE_BITMAP     "${NM_HUB_BMP_WELCOME}"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP           "${NM_HUB_BMP_HEADER}"
!define MUI_HEADERIMAGE_RIGHT
; El DESINSTALADOR usa la misma identidad: sin este define, MUI cae al
; arte default de NSIS (win.bmp) en las páginas un.Welcome/un.Finish
; (informe owner v1.0: "los uninstallers pierden su diseño al recompilar").
; OJO: el uninstall.exe ya instalado en una máquina NO se actualiza al
; recompilar este script — recién al reinstalar con el setup nuevo.
!define MUI_UNWELCOMEFINISHPAGE_BITMAP   "${NM_HUB_BMP_WELCOME}"
!define MUI_HEADERIMAGE_UNBITMAP         "${NM_HUB_BMP_HEADER}"

; Textos personalizados para el Wizard
!define MUI_WELCOMEPAGE_TITLE "Bienvenido al panel profesional de NeuroMood"
!define MUI_WELCOMEPAGE_TEXT "Este asistente preparará el entorno clínico local de NeuroMood Hub en tu equipo.$\r$\n$\r$\nToda la información de tus pacientes se gestionará bajo estrictos estándares de privacidad y seguridad. Tus credenciales clínicas y llaves de acceso a Supabase se configurarán de forma segura en el primer inicio dentro del Hub (el instalador no solicita ni almacena contraseñas)."

!define MUI_DIRECTORYPAGE_TEXT_DESTINATION "Entorno de trabajo clínico$\r$\nElegí dónde instalar NeuroMood Hub. La instalación es local para tu usuario clínico, manteniendo separados tus datos y los de la app de pacientes."

; Bienvenido
!insertmacro MUI_PAGE_WELCOME
; Carpeta de instalación
!insertmacro MUI_PAGE_DIRECTORY
; Accesos y tareas
!insertmacro MUI_PAGE_COMPONENTS
; Instalando
!insertmacro MUI_PAGE_INSTFILES

; Finalizar
!define MUI_FINISHPAGE_TITLE "Consultorio listo"
!define MUI_FINISHPAGE_TEXT "NeuroMood Hub se instaló correctamente.$\r$\n$\r$\nAl abrir el Hub por primera vez, se te guiará para configurar de forma segura la conexión Supabase y tus credenciales de terapeuta para comenzar a gestionar pacientes."
!define MUI_FINISHPAGE_RUN "$INSTDIR\${NM_HUB_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "Ejecutar NeuroMood Hub"
!insertmacro MUI_PAGE_FINISH

; Páginas del desinstalador (con identidad de marca).
; MUI2 NO tiene MUI_UNWELCOMEPAGE_*/MUI_UNFINISHPAGE_*: las páginas un.*
; leen MUI_WELCOMEPAGE_*/MUI_FINISHPAGE_* re-definidos ANTES de cada
; !insertmacro (MUI los des-define tras cada inserción). Los defines UN*
; anteriores no existían y el desinstalador mostraba los textos default.
!define MUI_WELCOMEPAGE_TITLE "Vas a desinstalar NeuroMood Hub"
!define MUI_WELCOMEPAGE_TEXT "Este asistente te guiará para quitar NeuroMood Hub de tu equipo.$\r$\n$\r$\nPodrás decidir si conservás o eliminás la carpeta de datos profesionales (configuración de conexión Supabase, claves de API y ajustes clínicos locales). Conservarlos te permite retomar tu trabajo sin reconfigurar el Hub."
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!define MUI_FINISHPAGE_TITLE "NeuroMood Hub se desinstaló"
!define MUI_FINISHPAGE_TEXT "El entorno clínico se quitó de este equipo. Tus datos en Supabase permanecen intactos en la nube."
!insertmacro MUI_UNPAGE_FINISH

; Idioma
!insertmacro MUI_LANGUAGE "Spanish"

; Variables
Var DeleteAppData

; =============================================================================
; Secciones del instalador
; =============================================================================

Section "NeuroMood Hub (Requerido)" SecApp
  SectionIn RO
  SetOutPath "$INSTDIR"

  ; Cerrar una instancia previa para que no bloquee el reemplazo de archivos
  ; al actualizar/reinstalar (paridad con el instalador del Suite).
  nsExec::Exec 'taskkill /F /IM "${NM_HUB_EXE}"'
  Sleep 800

  ; Limpieza mecánica de payloads anteriores
  RMDir /r "$INSTDIR\_internal"
  Delete "$INSTDIR\base_library.zip"
  Delete "$INSTDIR\install_path.txt"
  Delete "$INSTDIR\.neuromood_hub_install_manifest.json"
  
  ; Copiar archivos de payload principal
  File /r "${NM_HUB_DIST_DIR}\*"
  
  ; Copiar iconos para accesos directos
  File "${NM_ICON_APP}"
  File "${NM_ICON_UNINSTALL}"
  
  ; Copiar .env runtime a AppData (credenciales Supabase del Hub).
  ; Guard de TIEMPO DE COMPILACION (!if /FileExists): si el build generó
  ; build/runtime_env/hub/.env, se empaqueta y SIEMPRE se extrae en destino.
  ; Un IfFileExists de runtime sobre una ruta relativa al instalador nunca
  ; existe en la máquina del usuario y saltearía la extracción. NO revertir.
  !if /FileExists "..\..\build\runtime_env\hub\.env"
    CreateDirectory "$APPDATA\${NM_HUB_APPDATA_DIR}"
    File /oname=$APPDATA\${NM_HUB_APPDATA_DIR}\.env "..\..\build\runtime_env\hub\.env"
    SetFileAttributes "$APPDATA\${NM_HUB_APPDATA_DIR}\.env" HIDDEN
  !endif

  ; Escribir el desinstalador
  WriteUninstaller "$INSTDIR\uninstall.exe"
  
  ; Guardar directorio de instalación en registro
  WriteRegStr HKCU "Software\${NM_HUB_REG_KEY}" "InstallDir" "$INSTDIR"

  ; Registro de desinstalación en Apps & Features (HKCU)
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NM_HUB_REG_KEY}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NM_HUB_REG_KEY}" "DisplayName" "${NM_HUB_NAME}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NM_HUB_REG_KEY}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NM_HUB_REG_KEY}" "DisplayIcon" "$INSTDIR\no_symbol.ico"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NM_HUB_REG_KEY}" "DisplayVersion" "${NM_HUB_VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NM_HUB_REG_KEY}" "Publisher" "${NM_PUBLISHER}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NM_HUB_REG_KEY}" "URLInfoAbout" "${NM_URL_PRODUCT}"
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NM_HUB_REG_KEY}" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NM_HUB_REG_KEY}" "NoRepair" 1

  ; Acceso directo en el Menú Inicio (siempre creado)
  CreateDirectory "$SMPROGRAMS\NeuroMood"
  CreateShortcut "$SMPROGRAMS\NeuroMood\${NM_HUB_NAME}.lnk" "$INSTDIR\${NM_HUB_EXE}" "" "$INSTDIR\NM_icon.ico" 0
SectionEnd

Section "Crear acceso directo en el escritorio" SecDesktop
  CreateShortcut "$DESKTOP\${NM_HUB_NAME}.lnk" "$INSTDIR\${NM_HUB_EXE}" "" "$INSTDIR\NM_icon.ico" 0
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
    "Estás desinstalando NeuroMood Hub.$\r$\n¿Deseás eliminar también la carpeta de datos profesionales y configuraciones?$\r$\nUbicación: $APPDATA\${NM_HUB_APPDATA_DIR}$\r$\n$\r$\nImportante: Si elegís 'Sí', se borrarán de forma definitiva los registros de conexión Supabase, claves de API y configuraciones clínicas locales. Conservar estos datos (eligiendo 'No') te permitirá retomar tu trabajo sin reconfigurar el Hub en una futura reinstalación.$\r$\n$\r$\nNota: Los datos personales del paciente en NeuroMood Suite no se verán afectados." \
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

  ; Cerrar la app si sigue corriendo: sin esto el .exe y _internal quedan
  ; BLOQUEADOS, RMDir /r falla parcial y la carpeta sobrevive a la
  ; desinstalación (paridad con el desinstalador del Suite).
  nsExec::Exec 'taskkill /F /IM "${NM_HUB_EXE}"'
  Sleep 800

  ; Eliminar accesos directos
  Delete "$SMPROGRAMS\NeuroMood\${NM_HUB_NAME}.lnk"
  RMDir "$SMPROGRAMS\NeuroMood"
  Delete "$DESKTOP\${NM_HUB_NAME}.lnk"

  ; Eliminar archivos instalados
  RMDir /r "$INSTDIR\_internal"
  Delete "$INSTDIR\${NM_HUB_EXE}"
  Delete "$INSTDIR\uninstall.exe"
  Delete "$INSTDIR\NM_icon.ico"
  Delete "$INSTDIR\no_symbol.ico"
  Delete "$INSTDIR\base_library.zip"
  Delete "$INSTDIR\install_path.txt"
  Delete "$INSTDIR\.neuromood_hub_install_manifest.json"
  
  ; Eliminar el directorio completo (incluye restos: logs, .env de fallback,
  ; etc. — paridad con el desinstalador del Suite; las guardas de seguridad
  ; de arriba ya impiden borrar directorios del sistema).
  RMDir /r "$INSTDIR"

  ; Eliminar AppData si se solicitó
  StrCmp $DeleteAppData "1" 0 skip_appdata_delete
    RMDir /r "$APPDATA\${NM_HUB_APPDATA_DIR}"
  skip_appdata_delete:

  ; Eliminar registros
  DeleteRegKey HKCU "Software\${NM_HUB_REG_KEY}"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NM_HUB_REG_KEY}"

safe_done:
SectionEnd
