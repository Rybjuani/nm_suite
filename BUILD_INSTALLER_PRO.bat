@echo off
setlocal EnableDelayedExpansion
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo ============================================================
echo  Compilar Instalador NeuroMood Hub Pro
echo ============================================================

cd /d "%ROOT%"

if not exist "%ROOT%\dist\NeuroMood Hub Pro\NeuroMood Hub Pro.exe" (
    echo  FALTA: dist\NeuroMood Hub Pro\NeuroMood Hub Pro.exe
    echo  Ejecuta BUILD_ALL.bat primero.
    exit /b 1
)

:: Clean
rd /s /q "%ROOT%\dist\Instalador NeuroMood Hub Pro"              2>nul
rd /s /q "%ROOT%\dist\Desinstalador NeuroMood Hub Pro"           2>nul
rd /s /q "%ROOT%\dist\Instalar NeuroMood Hub Profesional"        2>nul
rd /s /q "%ROOT%\dist\Desinstalar NeuroMood Pro"                 2>nul
rd /s /q "%ROOT%\build\Instalador NeuroMood Hub Pro"             2>nul
rd /s /q "%ROOT%\build\Desinstalador NeuroMood Hub Pro"          2>nul
del "%ROOT%\Instalador NeuroMood Hub Pro.spec"                  2>nul
del "%ROOT%\Desinstalador NeuroMood Hub Pro.spec"               2>nul

:: [1/2] Desinstalador Hub
echo  [1/2] Desinstalador Hub...
pyinstaller --noconfirm --onedir --windowed --clean --optimize 2^
 --workpath "%ROOT%\build"^
 --paths "%ROOT%"^
 --log-level ERROR^
 --add-data "%ROOT%\shared;shared"^
 --hidden-import shared^
 --hidden-import win32com^
 --hidden-import win32com.client^
 --hidden-import pywintypes^
 --hidden-import PIL^
 --add-data "%ROOT%\assets\NM_icon.ico;."^
 --add-data "%ROOT%\assets\LOGO.png;."^
 --icon "%ROOT%\assets\NM_icon.ico"^
 --name "Desinstalador NeuroMood Hub Pro"^
 --distpath "%ROOT%\dist"^
 "%ROOT%\installers\uninstaller_pro.py"
if %ERRORLEVEL% NEQ 0 goto :error
echo     OK

:: [2/2] Instalador Hub
echo  [2/2] Instalador Hub...
pyinstaller --noconfirm --onedir --windowed --clean --optimize 2^
 --workpath "%ROOT%\build"^
 --paths "%ROOT%"^
 --log-level ERROR^
 --add-data "%ROOT%\shared;shared"^
 --hidden-import shared^
 --hidden-import win32com^
 --hidden-import win32com.client^
 --hidden-import pywintypes^
 --hidden-import PIL^
 --add-data "%ROOT%\assets\installer_icon.ico;."^
 --add-data "%ROOT%\assets\NM_icon.ico;."^
 --add-data "%ROOT%\assets\no_symbol.ico;."^
 --add-data "%ROOT%\assets\LOGO.png;."^
 --add-data "%ROOT%\.env;."^
 --add-data "%ROOT%\dist\NeuroMood Hub Pro;NeuroMood Hub Pro"^
 --add-data "%ROOT%\dist\Desinstalador NeuroMood Hub Pro;Desinstalador NeuroMood Hub Pro"^
 --icon "%ROOT%\assets\installer_icon.ico"^
 --name "Instalador NeuroMood Hub Pro"^
 --distpath "%ROOT%\dist"^
 "%ROOT%\installers\installer_pro.py"
if %ERRORLEVEL% NEQ 0 goto :error
echo     OK

echo ============================================================
echo  LISTO
echo  dist\Instalador NeuroMood Hub Pro\Instalador NeuroMood Hub Pro.exe
echo ============================================================
exit /b 0

:error
echo ============================================================
echo  ERROR - La compilacion fallo.
echo ============================================================
exit /b 1
