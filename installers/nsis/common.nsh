; common.nsh — Constantes compartidas para los instaladores NSIS de NeuroMood
; USO: !include "common.nsh" al inicio de cada script .nsi.

!define NM_PUBLISHER         "NeuroMood"
!define NM_URL_PRODUCT       "https://neuromood.com.ar"
!define NM_URL_SUPPORT       "https://neuromood.com.ar"

; =============================================================================
; NeuroMood Suite — app paciente
; =============================================================================
!define NM_SUITE_NAME          "NeuroMood Suite"
; Versión oficial del producto — mantener en sync con shared/version.py
!define NM_SUITE_VERSION       "1.0.0"
!define NM_SUITE_EXE           "NeuroMood Suite.exe"
!define NM_SUITE_REG_KEY       "NeuroMoodSuite"
!define NM_SUITE_APPDATA_DIR   "NeuroMood"
!define NM_SUITE_DEFAULT_DIR   "$PROFILE\NeuroMood"
!define NM_SUITE_DIST_DIR      "..\..\dist\NeuroMood Suite"

; =============================================================================
; NeuroMood Hub — app profesional
; =============================================================================
!define NM_HUB_NAME            "NeuroMood Hub"
; Versión oficial del producto — mantener en sync con shared/version.py
!define NM_HUB_VERSION         "1.0.0"
!define NM_HUB_EXE             "NeuroMood Hub.exe"
!define NM_HUB_REG_KEY         "NeuroMoodHub"
!define NM_HUB_APPDATA_DIR     "NeuroMoodHub"
!define NM_HUB_DEFAULT_DIR     "$PROFILE\NeuroMood Hub"
!define NM_HUB_DIST_DIR        "..\..\dist\NeuroMood Hub"

; =============================================================================
; Assets compartidos (rutas relativas a la carpeta del script .nsi)
; =============================================================================
!define NM_ICON_APP            "..\..\assets\NM_icon.ico"
!define NM_ICON_INSTALLER      "..\..\assets\installer_icon.ico"
!define NM_ICON_UNINSTALL      "..\..\assets\no_symbol.ico"
!define NM_LOGO                "..\..\assets\LOGO.png"

; =============================================================================
; Assets MUI2 — sidebar (164x314) y header (150x57)
; =============================================================================
!define NM_SUITE_BMP_WELCOME   "assets\suite_welcome.bmp"
!define NM_SUITE_BMP_HEADER    "assets\suite_header.bmp"
!define NM_HUB_BMP_WELCOME     "assets\hub_welcome.bmp"
!define NM_HUB_BMP_HEADER      "assets\hub_header.bmp"
