@echo off
setlocal EnableDelayedExpansion
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo ============================================================
echo  NeuroMood - Compilar Instalador Paciente
echo  neuromood.com.ar
echo ============================================================
echo.

cd /d "%ROOT%"

if not exist "%ROOT%\dist\NeuroMood.exe" (
    echo  FALTA: dist\NeuroMood.exe
    echo  Ejecuta BUILD_ALL.bat primero para compilar la app.
    pause
    exit /b 1
)

set "ASSETS=%ROOT%\assets"
set "INSTALLERS=%ROOT%\installers"
set "DIST=%ROOT%\dist"
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

echo  [1/3] Compilando desinstalador paciente...
pyinstaller %BASE_FLAGS%^
 --add-data "%ASSETS%\no_symbol.ico;."^
 --add-data "%ASSETS%\LOGO.png;."^
 --icon "%ASSETS%\no_symbol.ico"^
 --name "Desinstalar NeuroMood"^
 --distpath "%DIST%"^
 "%INSTALLERS%\uninstaller.py"
if %ERRORLEVEL% NEQ 0 goto :error
echo  Desinstalador listo: dist\Desinstalar NeuroMood.exe
echo.

echo  [2/3] Compilando instalador paciente...
pyinstaller %BASE_FLAGS%^
 --add-data "%ASSETS%\installer_icon.ico;."^
 --add-data "%ASSETS%\NM_icon.ico;."^
 --add-data "%ASSETS%\no_symbol.ico;."^
 --add-data "%ASSETS%\LOGO.png;."^
 --add-data "%ROOT%\.env;."^
 --add-data "%DIST%\NeuroMood.exe;."^
 --add-data "%DIST%\Desinstalar NeuroMood.exe;."^
 --icon "%ASSETS%\installer_icon.ico"^
 --name "Instalar NeuroMood"^
 --distpath "%DIST%"^
 "%INSTALLERS%\installer.py"
if %ERRORLEVEL% NEQ 0 goto :error
echo  Instalador listo.
echo.

echo  [3/3] Limpiando temporales...
if exist "%BUILD%\Desinstalar NeuroMood" rmdir /s /q "%BUILD%\Desinstalar NeuroMood"
if exist "%BUILD%\Instalar NeuroMood"    rmdir /s /q "%BUILD%\Instalar NeuroMood"
del /q "%ROOT%\Desinstalar NeuroMood.spec" 2>nul
del /q "%ROOT%\Instalar NeuroMood.spec"    2>nul

echo.
echo ============================================================
echo  LISTO
echo.
echo  Instalador:    dist\Instalar NeuroMood.exe
echo  Desinstalador: dist\Desinstalar NeuroMood.exe
echo.
echo  Distribuye solo: dist\Instalar NeuroMood.exe
echo  (el desinstalador va incluido dentro del instalador)
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
