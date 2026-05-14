@echo off
setlocal EnableDelayedExpansion
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo ============================================================
echo  NeuroMood - Compilar Instalador Suite
echo ============================================================
echo.

cd /d "%ROOT%"

set "DIST=%ROOT%\dist"
set "ASSETS=%ROOT%\assets"
set "BUILD=%ROOT%\build"

if not exist "%DIST%\NeuroMood Suite\NeuroMood Suite.exe" (
    echo  FALTA: dist\NeuroMood Suite\NeuroMood Suite.exe
    echo  Ejecuta BUILD_ALL.bat primero.
    pause
    exit /b 1
)

:: Clean
echo  Limpiando builds anteriores...
if exist "%DIST%\Desinstalador NeuroMood"       rmdir /s /q "%DIST%\Desinstalador NeuroMood"       2>nul
if exist "%DIST%\Instalador NeuroMood Suite"     rmdir /s /q "%DIST%\Instalador NeuroMood Suite"     2>nul
del "%ROOT%\Desinstalador NeuroMood.spec" 2>nul
del "%ROOT%\Instalador NeuroMood Suite.spec"    2>nul

set BASE=--noconfirm --onedir --windowed^
 --workpath "%BUILD%"^
 --paths "%ROOT%"^
 --hidden-import shared^
 --hidden-import PIL^
 --hidden-import win32com^
 --hidden-import win32com.client^
 --hidden-import pywintypes

echo  [1/2] Compilando desinstalador...
pyinstaller %BASE%^
 --add-data "%ASSETS%\no_symbol.ico;."^
 --add-data "%ASSETS%\LOGO.png;."^
 --icon "%ASSETS%\no_symbol.ico"^
 --name "Desinstalador NeuroMood"^
 --distpath "%DIST%"^
 "%ROOT%\installers\uninstaller.py"
if %ERRORLEVEL% NEQ 0 goto :error
echo  OK: dist\Desinstalador NeuroMood\
echo.

echo  [2/2] Compilando instalador...
pyinstaller %BASE%^
 --add-data "%ASSETS%\installer_icon.ico;."^
 --add-data "%ASSETS%\NM_icon.ico;."^
 --add-data "%ASSETS%\no_symbol.ico;."^
 --add-data "%ASSETS%\LOGO.png;."^
 --add-data "%ROOT%\.env;."^
 --add-data "%DIST%\NeuroMood Suite;NeuroMood Suite"^
 --add-data "%DIST%\Desinstalador NeuroMood;Desinstalador NeuroMood"^
 --icon "%ASSETS%\installer_icon.ico"^
 --name "Instalador NeuroMood Suite"^
 --distpath "%DIST%"^
 "%ROOT%\installers\installer.py"
if %ERRORLEVEL% NEQ 0 goto :error
echo  OK: dist\Instalador NeuroMood Suite\
echo.

echo ============================================================
echo  LISTO
echo  dist\Instalador NeuroMood Suite\Instalador NeuroMood Suite.exe
echo ============================================================
pause
goto :end

:error
echo ============================================================
echo  ERROR - La compilacion fallo.
echo ============================================================
pause

:end
