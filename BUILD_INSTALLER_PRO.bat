@echo off
setlocal EnableDelayedExpansion
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo ============================================================
echo  NeuroMood Suite - Compilar Instalador Hub Profesional
echo ============================================================
echo.

cd /d "%ROOT%"

if not exist "%ROOT%\dist\pro\HubProfesional\HubProfesional.exe" (
    echo  FALTA: dist\pro\HubProfesional\HubProfesional.exe
    echo  Ejecuta BUILD_ALL.bat primero para compilar el Hub.
    pause
    exit /b 1
)

set "ASSETS=%ROOT%\assets"
set "INSTALLERS=%ROOT%\installers"
set "DIST=%ROOT%\dist"
set "DIST_PRO=%ROOT%\dist\pro"
set "BUILD=%ROOT%\build"

:: Clean previous
if exist "%DIST%\Instalar NeuroMood Hub Profesional"          rmdir /s /q "%DIST%\Instalar NeuroMood Hub Profesional"          2>nul
if exist "%DIST_PRO%\Desinstalar NeuroMood Pro"                rmdir /s /q "%DIST_PRO%\Desinstalar NeuroMood Pro"                2>nul
del "%ROOT%\Desinstalar NeuroMood Pro.spec"             2>nul
del "%ROOT%\Instalar NeuroMood Hub Profesional.spec"    2>nul

set BASE_FLAGS=--noconfirm --onedir --windowed^
 --workpath "%BUILD%"^
 --paths "%ROOT%"^
 --collect-all shared^
 --hidden-import PIL^
 --hidden-import win32com^
 --hidden-import win32com.client^
 --hidden-import pywintypes

echo  [1/2] Compilando desinstalador Hub...
pyinstaller %BASE_FLAGS%^
 --add-data "%ASSETS%\NM_icon.ico;."^
 --add-data "%ASSETS%\LOGO.png;."^
 --icon "%ASSETS%\NM_icon.ico"^
 --name "Desinstalar NeuroMood Pro"^
 --distpath "%DIST_PRO%"^
 "%INSTALLERS%\uninstaller_pro.py"
if %ERRORLEVEL% NEQ 0 goto :error
echo  OK: dist\pro\Desinstalar NeuroMood Pro\
echo.

echo  [2/2] Compilando instalador Hub...
pyinstaller %BASE_FLAGS%^
 --add-data "%ASSETS%\installer_icon.ico;."^
 --add-data "%ASSETS%\NM_icon.ico;."^
 --add-data "%ASSETS%\no_symbol.ico;."^
 --add-data "%ASSETS%\LOGO.png;."^
 --add-data "%ROOT%\.env;."^
 --add-data "%DIST_PRO%\HubProfesional;HubProfesional"^
 --add-data "%DIST_PRO%\Desinstalar NeuroMood Pro;Desinstalar NeuroMood Pro"^
 --icon "%ASSETS%\installer_icon.ico"^
 --name "Instalar NeuroMood Hub Profesional"^
 --distpath "%DIST%"^
 "%INSTALLERS%\installer_pro.py"
if %ERRORLEVEL% NEQ 0 goto :error
echo  OK: dist\Instalar NeuroMood Hub Profesional\
echo.

echo ============================================================
echo  LISTO - Arranque instantaneo
echo.
echo  Instalador Pro: dist\Instalar NeuroMood Hub Profesional\Instalar NeuroMood Hub Profesional.exe
echo.
echo  Para distribuir: comprime la carpeta en un .zip y compartilo.
echo ============================================================
pause
goto :end

:error
echo.
echo ============================================================
echo  ERROR - La compilacion fallo.
echo ============================================================
pause

:end
