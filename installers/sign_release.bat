@echo off
REM sign_release.bat — Firma Authenticode los 4 artefactos de release
REM
REM Prerequisitos:
REM   1. Windows SDK instalado (incluye signtool.exe):
REM      https://developer.microsoft.com/windows/downloads/windows-sdk/
REM      Durante la instalacion, seleccionar solo "Windows SDK Signing Tools for Desktop Apps"
REM
REM   2. Certificado EV Code Signing instalado en el almacen de certificados del usuario:
REM      Proveedores recomendados: DigiCert, Sectigo, GlobalSign
REM      El certificado EV elimina el aviso SmartScreen de forma inmediata.
REM      Un certificado OV puede requerir meses de reputacion para suprimir SmartScreen.
REM
REM   3. Variables de entorno configuradas (o editar las rutas abajo):
REM      NM_SIGNTOOL  — ruta completa a signtool.exe
REM      NM_CERT_SHA1 — SHA1 thumbprint del certificado (sin espacios)
REM      NM_TSA_URL   — URL del servidor de timestamp
REM
REM Uso:
REM   sign_release.bat
REM
REM Los 4 binarios firmados quedan en sus ubicaciones originales.

setlocal enabledelayedexpansion

REM --- Configuracion ---
if "%NM_SIGNTOOL%"=="" (
    set "SIGNTOOL=C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe"
) else (
    set "SIGNTOOL=%NM_SIGNTOOL%"
)

if "%NM_CERT_SHA1%"=="" (
    echo ERROR: Variable NM_CERT_SHA1 no definida.
    echo        Ejemplo: set NM_CERT_SHA1=AABBCCDDEEFF00112233445566778899AABBCCDD
    exit /b 1
)

if "%NM_TSA_URL%"=="" (
    REM DigiCert timestamp server
    set "TSA_URL=http://timestamp.digicert.com"
) else (
    set "TSA_URL=%NM_TSA_URL%"
)

set "ROOT=%~dp0.."
set "SUITE_EXE=%ROOT%\dist\NeuroMood Suite\NeuroMood Suite.exe"
set "HUB_EXE=%ROOT%\dist\NeuroMood Hub\NeuroMood Hub.exe"
set "SUITE_SETUP=%ROOT%\installers\nsis\Output\NM_Suite_Setup.exe"
set "HUB_SETUP=%ROOT%\installers\nsis\Output\NM_Hub_Setup.exe"

REM --- Verificaciones previas ---
if not exist "%SIGNTOOL%" (
    echo ERROR: signtool.exe no encontrado en: %SIGNTOOL%
    echo        Instala Windows SDK desde:
    echo        https://developer.microsoft.com/windows/downloads/windows-sdk/
    exit /b 1
)

for %%F in ("%SUITE_EXE%" "%HUB_EXE%" "%SUITE_SETUP%" "%HUB_SETUP%") do (
    if not exist %%F (
        echo ERROR: Artefacto no encontrado: %%F
        echo        Ejecuta BUILD_NEUROMOOD.bat primero.
        exit /b 1
    )
)

REM --- Firma ---
echo ==========================================
echo  NeuroMood V3 - Code Signing
echo ==========================================
echo Certificado SHA1: %NM_CERT_SHA1%
echo Timestamp server: %TSA_URL%
echo.

set SIGN_ARGS=/sha1 "%NM_CERT_SHA1%" /fd sha256 /td sha256 /tr "%TSA_URL%" /v

echo [1/4] Firmando NeuroMood Suite.exe...
"%SIGNTOOL%" sign %SIGN_ARGS% "%SUITE_EXE%"
if errorlevel 1 ( echo ERROR en Suite.exe && exit /b 1 )

echo [2/4] Firmando NeuroMood Hub.exe...
"%SIGNTOOL%" sign %SIGN_ARGS% "%HUB_EXE%"
if errorlevel 1 ( echo ERROR en Hub.exe && exit /b 1 )

echo [3/4] Firmando NM_Suite_Setup.exe...
"%SIGNTOOL%" sign %SIGN_ARGS% "%SUITE_SETUP%"
if errorlevel 1 ( echo ERROR en NM_Suite_Setup.exe && exit /b 1 )

echo [4/4] Firmando NM_Hub_Setup.exe...
"%SIGNTOOL%" sign %SIGN_ARGS% "%HUB_SETUP%"
if errorlevel 1 ( echo ERROR en NM_Hub_Setup.exe && exit /b 1 )

REM --- Verificacion post-firma ---
echo.
echo Verificando firmas...
for %%F in ("%SUITE_EXE%" "%HUB_EXE%" "%SUITE_SETUP%" "%HUB_SETUP%") do (
    "%SIGNTOOL%" verify /pa /v %%F 2>nul
    if errorlevel 1 ( echo ADVERTENCIA: verificacion fallo para %%F )
)

echo.
echo ==========================================
echo  FIRMA COMPLETADA
echo ==========================================
endlocal
