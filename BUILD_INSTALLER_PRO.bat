@echo off
setlocal EnableDelayedExpansion
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo ============================================================
echo  NeuroMood Suite - Compilar Instalador Hub Profesional
echo  neuromood.com.ar
echo ============================================================
echo.

cd /d "%ROOT%"

if not exist "%ROOT%\dist\pro\HubProfesional.exe" (
    echo  FALTA: dist\pro\HubProfesional.exe
    echo  Ejecuta BUILD_ALL.bat primero para compilar el Hub.
    pause
    exit /b 1
)

set "ASSETS=%ROOT%\assets"
set "INSTALLERS=%ROOT%\installers"
set "DIST=%ROOT%\dist"
set "DIST_PRO=%ROOT%\dist\pro"
set "BUILD=%ROOT%\build"

set BASE_FLAGS=--noconfirm --onefile --windowed^
 --workpath "%BUILD%"^
 --paths "%ROOT%"^
 --collect-all shared^
 --hidden-import PIL^
 --hidden-import PIL._tkinter_finder^
 --hidden-import win32com^
 --hidden-import win32com.client^
 --hidden-import win32com.shell^
 --hidden-import pywintypes

echo  [1/3] Compilando desinstalador del Hub Profesional...
pyinstaller %BASE_FLAGS%^
 --add-data "%ASSETS%\NM_icon.ico;."^
 --add-data "%ASSETS%\LOGO.png;."^
 --icon "%ASSETS%\NM_icon.ico"^
 --name "Desinstalar NeuroMood Pro"^
 --distpath "%DIST_PRO%"^
 "%INSTALLERS%\uninstaller_pro.py"
if %ERRORLEVEL% NEQ 0 goto :error
echo  Desinstalador listo: dist\pro\Desinstalar NeuroMood Pro.exe
echo.

echo  [2/3] Compilando instalador del Hub Profesional...
pyinstaller %BASE_FLAGS%^
 --add-data "%ASSETS%\installer_icon.ico;."^
 --add-data "%ASSETS%\NM_icon.ico;."^
 --add-data "%ASSETS%\no_symbol.ico;."^
 --add-data "%ASSETS%\LOGO.png;."^
 --add-data "%ROOT%\.env;."^
 --add-data "%DIST_PRO%\HubProfesional.exe;pro"^
 --add-data "%DIST_PRO%\Desinstalar NeuroMood Pro.exe;pro"^
 --icon "%ASSETS%\installer_icon.ico"^
 --name "Instalar NeuroMood Hub Profesional"^
 --distpath "%DIST%"^
 "%INSTALLERS%\installer_pro.py"
if %ERRORLEVEL% NEQ 0 goto :error
echo  Instalador listo.
echo.

echo  [3/3] Limpiando archivos temporales...
if exist "%BUILD%\Desinstalar NeuroMood Pro"              rmdir /s /q "%BUILD%\Desinstalar NeuroMood Pro"
if exist "%BUILD%\Instalar NeuroMood Hub Profesional"     rmdir /s /q "%BUILD%\Instalar NeuroMood Hub Profesional"
del /q "%ROOT%\Desinstalar NeuroMood Pro.spec"            2>nul
del /q "%ROOT%\Instalar NeuroMood Hub Profesional.spec"   2>nul

echo.
echo ============================================================
echo  LISTO
echo.
echo  Instalador Pro: dist\Instalar NeuroMood Hub Profesional.exe
echo.
echo  Distribuye solo ese archivo al profesional.
echo  Incluye internamente:
echo    - HubProfesional.exe
echo    - Desinstalar NeuroMood Pro.exe
echo ============================================================
echo.
pause
goto :end

:error
echo.
echo ============================================================
echo  ERROR - La compilacion fallo.
echo ============================================================
echo.
pause

:end
