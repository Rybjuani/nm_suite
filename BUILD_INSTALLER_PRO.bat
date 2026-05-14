@echo off
setlocal EnableDelayedExpansion
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo ============================================================
echo  NeuroMood - Compilar Instalador Hub
echo ============================================================
echo.

cd /d "%ROOT%"

set "DIST=%ROOT%\dist"
set "ASSETS=%ROOT%\assets"
set "BUILD=%ROOT%\build"

if not exist "%DIST%\HubProfesional\HubProfesional.exe" (
    echo  FALTA: dist\HubProfesional\HubProfesional.exe
    echo  Ejecuta BUILD_ALL.bat primero.
    pause
    exit /b 1
)

:: Clean
echo  Limpiando builds anteriores...
if exist "%DIST%\Desinstalar NeuroMood Pro"                rmdir /s /q "%DIST%\Desinstalar NeuroMood Pro"                2>nul
if exist "%DIST%\Instalar NeuroMood Hub Profesional"       rmdir /s /q "%DIST%\Instalar NeuroMood Hub Profesional"       2>nul
del "%ROOT%\Desinstalar NeuroMood Pro.spec"             2>nul
del "%ROOT%\Instalar NeuroMood Hub Profesional.spec"    2>nul

set BASE=--noconfirm --onedir --windowed^
 --workpath "%BUILD%"^
 --paths "%ROOT%"^
 --hidden-import shared^
 --hidden-import PIL^
 --hidden-import win32com^
 --hidden-import win32com.client^
 --hidden-import pywintypes

echo  [1/2] Compilando desinstalador Hub...
pyinstaller %BASE%^
 --add-data "%ASSETS%\NM_icon.ico;."^
 --add-data "%ASSETS%\LOGO.png;."^
 --icon "%ASSETS%\NM_icon.ico"^
 --name "Desinstalar NeuroMood Pro"^
 --distpath "%DIST%"^
 "%ROOT%\installers\uninstaller_pro.py"
if %ERRORLEVEL% NEQ 0 goto :error
echo  OK: dist\Desinstalar NeuroMood Pro\
echo.

echo  [2/2] Compilando instalador Hub...
pyinstaller %BASE%^
 --add-data "%ASSETS%\installer_icon.ico;."^
 --add-data "%ASSETS%\NM_icon.ico;."^
 --add-data "%ASSETS%\no_symbol.ico;."^
 --add-data "%ASSETS%\LOGO.png;."^
 --add-data "%ROOT%\.env;."^
 --add-data "%DIST%\HubProfesional;HubProfesional"^
 --add-data "%DIST%\Desinstalar NeuroMood Pro;Desinstalar NeuroMood Pro"^
 --icon "%ASSETS%\installer_icon.ico"^
 --name "Instalar NeuroMood Hub Profesional"^
 --distpath "%DIST%"^
 "%ROOT%\installers\installer_pro.py"
if %ERRORLEVEL% NEQ 0 goto :error
echo  OK: dist\Instalar NeuroMood Hub Profesional\
echo.

echo ============================================================
echo  LISTO
echo  dist\Instalar NeuroMood Hub Profesional\Instalar NeuroMood Hub Profesional.exe
echo ============================================================
pause
goto :end

:error
echo ============================================================
echo  ERROR - La compilacion fallo.
echo ============================================================
pause

:end
