@echo off
setlocal EnableDelayedExpansion
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo ============================================================
echo  NeuroMood - Compilar Instalador Hub Pro
echo ============================================================
echo.

cd /d "%ROOT%"

set "DIST=%ROOT%\dist"
set "ASSETS=%ROOT%\assets"
set "BUILD=%ROOT%\build"

if not exist "%DIST%\NeuroMood Hub Pro\NeuroMood Hub Pro.exe" (
    echo  FALTA: dist\NeuroMood Hub Pro\NeuroMood Hub Pro.exe
    echo  Ejecuta BUILD_ALL.bat primero.
    pause
    exit /b 1
)

:: Clean ALL old + current builds
echo  Limpiando builds anteriores...
for %%F in (
    "Instalar NeuroMood Hub Profesional" "Instalador NeuroMood Hub Pro"
    "Desinstalar NeuroMood Pro" "Desinstalador NeuroMood Hub Pro"
) do (
    if exist "%DIST%\%%~F"     rmdir /s /q "%DIST%\%%~F"     2>nul
    if exist "%BUILD%\%%~F"    rmdir /s /q "%BUILD%\%%~F"    2>nul
    del "%ROOT%\%%~F.spec"     2>nul
)

set BASE=--noconfirm --onedir --windowed --clean^
 --workpath "%BUILD%"^
 --paths "%ROOT%"^
 --log-level WARN^
 --hidden-import win32com^
 --hidden-import win32com.client^
 --hidden-import pywintypes^
 --hidden-import PIL

echo  [1/2] Compilando desinstalador Hub Pro...
pyinstaller %BASE%^
 --add-data "%ASSETS%\NM_icon.ico;."^
 --add-data "%ASSETS%\LOGO.png;."^
 --icon "%ASSETS%\NM_icon.ico"^
 --name "Desinstalador NeuroMood Hub Pro"^
 --distpath "%DIST%"^
 "%ROOT%\installers\uninstaller_pro.py"
if %ERRORLEVEL% NEQ 0 goto :error
echo  OK: dist\Desinstalador NeuroMood Hub Pro\
echo.

echo  [2/2] Compilando instalador Hub Pro...
pyinstaller %BASE%^
 --add-data "%ASSETS%\installer_icon.ico;."^
 --add-data "%ASSETS%\NM_icon.ico;."^
 --add-data "%ASSETS%\no_symbol.ico;."^
 --add-data "%ASSETS%\LOGO.png;."^
 --add-data "%ROOT%\.env;."^
 --add-data "%DIST%\NeuroMood Hub Pro;NeuroMood Hub Pro"^
 --add-data "%DIST%\Desinstalador NeuroMood Hub Pro;Desinstalador NeuroMood Hub Pro"^
 --icon "%ASSETS%\installer_icon.ico"^
 --name "Instalador NeuroMood Hub Pro"^
 --distpath "%DIST%"^
 "%ROOT%\installers\installer_pro.py"
if %ERRORLEVEL% NEQ 0 goto :error
echo  OK: dist\Instalador NeuroMood Hub Pro\
echo.

:: Clean .spec files
del "%ROOT%\Desinstalador NeuroMood Hub Pro.spec"    2>nul
del "%ROOT%\Instalador NeuroMood Hub Pro.spec"       2>nul

echo ============================================================
echo  LISTO
echo  dist\Instalador NeuroMood Hub Pro\Instalador NeuroMood Hub Pro.exe
echo ============================================================
pause
goto :end

:error
echo ============================================================
echo  ERROR - La compilacion fallo.
echo ============================================================
pause

:end
