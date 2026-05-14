@echo off
setlocal EnableDelayedExpansion
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo ============================================================
echo  NeuroMood - Compilar Instalador Paciente
echo ============================================================
echo.

cd /d "%ROOT%"

if not exist "%ROOT%\dist\NeuroMood\NeuroMood.exe" (
    echo  FALTA: dist\NeuroMood\NeuroMood.exe
    echo  Ejecuta BUILD_ALL.bat primero para compilar la app.
    pause
    exit /b 1
)

set "ASSETS=%ROOT%\assets"
set "INSTALLERS=%ROOT%\installers"
set "DIST=%ROOT%\dist"
set "BUILD=%ROOT%\build"

:: Clean previous
if exist "%DIST%\Instalar NeuroMood"          rmdir /s /q "%DIST%\Instalar NeuroMood"          2>nul
if exist "%DIST%\Desinstalar NeuroMood"       rmdir /s /q "%DIST%\Desinstalar NeuroMood"       2>nul
del "%ROOT%\Desinstalar NeuroMood.spec" 2>nul
del "%ROOT%\Instalar NeuroMood.spec"    2>nul

set BASE_FLAGS=--noconfirm --onedir --windowed^
 --workpath "%BUILD%"^
 --paths "%ROOT%"^
 --collect-all shared^
 --hidden-import PIL^
 --hidden-import win32com^
 --hidden-import win32com.client^
 --hidden-import pywintypes

echo  [1/2] Compilando desinstalador...
pyinstaller %BASE_FLAGS%^
 --add-data "%ASSETS%\no_symbol.ico;."^
 --add-data "%ASSETS%\LOGO.png;."^
 --icon "%ASSETS%\no_symbol.ico"^
 --name "Desinstalar NeuroMood"^
 --distpath "%DIST%"^
 "%INSTALLERS%\uninstaller.py"
if %ERRORLEVEL% NEQ 0 goto :error
echo  OK: dist\Desinstalar NeuroMood\
echo.

echo  [2/2] Compilando instalador...
pyinstaller %BASE_FLAGS%^
 --add-data "%ASSETS%\installer_icon.ico;."^
 --add-data "%ASSETS%\NM_icon.ico;."^
 --add-data "%ASSETS%\no_symbol.ico;."^
 --add-data "%ASSETS%\LOGO.png;."^
 --add-data "%ROOT%\.env;."^
 --add-data "%DIST%\NeuroMood;NeuroMood"^
 --add-data "%DIST%\Desinstalar NeuroMood;Desinstalar NeuroMood"^
 --icon "%ASSETS%\installer_icon.ico"^
 --name "Instalar NeuroMood"^
 --distpath "%DIST%"^
 "%INSTALLERS%\installer.py"
if %ERRORLEVEL% NEQ 0 goto :error
echo  OK: dist\Instalar NeuroMood\
echo.

echo ============================================================
echo  LISTO - Arranque instantaneo
echo.
echo  Instalador:    dist\Instalar NeuroMood\Instalar NeuroMood.exe
echo.
echo  Para distribuir: comprime la carpeta dist\Instalar NeuroMood\
echo  en un .zip y compartilo. El usuario extrae y ejecuta el .exe.
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
