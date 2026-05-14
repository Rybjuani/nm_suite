@echo off
setlocal EnableDelayedExpansion
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo ============================================================
echo  Compilar Instalador NeuroMood Suite
echo ============================================================

cd /d "%ROOT%"

if not exist "%ROOT%\dist\NeuroMood Suite\NeuroMood Suite.exe" (
    echo  FALTA: dist\NeuroMood Suite\NeuroMood Suite.exe
    echo  Ejecuta BUILD_ALL.bat primero.
    exit /b 1
)

:: Clean
rd /s /q "%ROOT%\dist\Instalador NeuroMood Suite"         2>nul
rd /s /q "%ROOT%\dist\Desinstalador NeuroMood"            2>nul
rd /s /q "%ROOT%\dist\Instalar NeuroMood"                 2>nul
rd /s /q "%ROOT%\dist\Desinstalar NeuroMood"              2>nul
rd /s /q "%ROOT%\build\Instalador NeuroMood Suite"         2>nul
rd /s /q "%ROOT%\build\Desinstalador NeuroMood"           2>nul
del "%ROOT%\Instalador NeuroMood Suite.spec"              2>nul
del "%ROOT%\Desinstalador NeuroMood.spec"                 2>nul

:: [1/2] Desinstalador
echo  [1/2] Desinstalador...
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
 --add-data "%ROOT%\assets\no_symbol.ico;."^
 --add-data "%ROOT%\assets\LOGO.png;."^
 --icon "%ROOT%\assets\no_symbol.ico"^
 --name "Desinstalador NeuroMood"^
 --distpath "%ROOT%\dist"^
 "%ROOT%\installers\uninstaller.py" >nul 2>&1
if %ERRORLEVEL% NEQ 0 goto :error
echo     OK

:: [2/2] Instalador
echo  [2/2] Instalador...
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
 --add-data "%ROOT%\dist\NeuroMood Suite;NeuroMood Suite"^
 --add-data "%ROOT%\dist\Desinstalador NeuroMood;Desinstalador NeuroMood"^
 --icon "%ROOT%\assets\installer_icon.ico"^
 --name "Instalador NeuroMood Suite"^
 --distpath "%ROOT%\dist"^
 "%ROOT%\installers\installer.py" >nul 2>&1
if %ERRORLEVEL% NEQ 0 goto :error
echo     OK

echo ============================================================
echo  LISTO
echo  dist\Instalador NeuroMood Suite\Instalador NeuroMood Suite.exe
echo ============================================================
exit /b 0

:error
echo ============================================================
echo  ERROR - La compilacion fallo.
echo ============================================================
exit /b 1
