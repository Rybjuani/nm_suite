@echo off
setlocal EnableDelayedExpansion
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo ============================================================
echo  NeuroMood - Compilar Instalador Hub Pro
echo ============================================================
echo.

cd /d "%ROOT%"

:: Kill any running instances that would lock dist/ folder
taskkill /f /im "NeuroMood Hub Pro.exe"                2>nul
taskkill /f /im "Desinstalador NeuroMood Hub Pro.exe"   2>nul
timeout /t 1 /nobreak >nul

set "DIST=%ROOT%\dist"
set "ASSETS=%ROOT%\assets"
set "BUILD=%ROOT%\build"

if not exist "%DIST%\NeuroMood Hub Pro\NeuroMood Hub Pro.exe" (
    echo  FALTA: dist\NeuroMood Hub Pro\NeuroMood Hub Pro.exe
    echo  Ejecuta BUILD_ALL.bat primero.
    pause
    exit /b 1
)

:: Clean
rd /s /q "%DIST%\Instalador NeuroMood Hub Pro"          2>nul
rd /s /q "%DIST%\Instalar NeuroMood Hub Profesional"     2>nul
rd /s /q "%DIST%\Desinstalador NeuroMood Hub Pro"        2>nul
rd /s /q "%DIST%\Desinstalar NeuroMood Pro"              2>nul
rd /s /q "%BUILD%\Instalador NeuroMood Hub Pro"          2>nul
rd /s /q "%BUILD%\Desinstalador NeuroMood Hub Pro"       2>nul
del "%ROOT%\Instalador NeuroMood Hub Pro.spec"          2>nul
del "%ROOT%\Desinstalador NeuroMood Hub Pro.spec"       2>nul

echo  [1/2] Compilando desinstalador Hub Pro...
pyinstaller --noconfirm --onedir --windowed --clean^
 --workpath "%BUILD%"^
 --paths "%ROOT%"^
 --log-level WARN^
 --hidden-import win32com^
 --hidden-import win32com.client^
 --hidden-import pywintypes^
 --hidden-import PIL^
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
pyinstaller --noconfirm --onedir --windowed --clean^
 --workpath "%BUILD%"^
 --paths "%ROOT%"^
 --log-level WARN^
 --hidden-import win32com^
 --hidden-import win32com.client^
 --hidden-import pywintypes^
 --hidden-import PIL^
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
