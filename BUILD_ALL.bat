@echo off
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

if "%1"=="test" goto :test
if "%1"=="release" goto :release
goto :build

:: ============================================================
::  MODO TEST - Ejecutar sin compilar
:: ============================================================
:test
echo ============================================================
echo  NeuroMood V3 - Modo Testing
echo ============================================================
echo.
for /d /r "%ROOT%" %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
echo  1. App Paciente      (app\main_qt.py)
echo  2. NeuroMood Hub Pro (hub\main_qt.py)
echo  0. Salir
set /p APP="> "
if "%APP%"=="1" (python "%ROOT%\app\main_qt.py" & goto :test)
if "%APP%"=="2" (python "%ROOT%\hub\main_qt.py"   & goto :test)
if "%APP%"=="0" goto :end
goto :test

:: ============================================================
::  BUILD (default) - onedir, arranque <1s
::  BUILD_ALL.bat          -> desarrollo (onedir)
::  BUILD_ALL.bat release  -> distribucion (onefile)
::
::  Salida:
::    dist\NeuroMood Suite\NeuroMood Suite.exe
::    dist\NeuroMood Hub Pro\NeuroMood Hub Pro.exe
:: ============================================================
:build
set "MODE=--onedir"
set "LABEL=onedir (arranque rapido)"
goto :compile

:release
set "MODE=--onefile"
set "LABEL=onefile (distribucion)"
goto :compile

:compile
echo ============================================================
echo  NeuroMood V3 - Build [%LABEL%]
echo  [1/2] NeuroMood Suite  +  [2/2] NeuroMood Hub Pro
echo ============================================================
echo.

cd /d "%ROOT%"

set "DIST=%ROOT%\dist"
set "BUILD=%ROOT%\build"
set "ASSETS=%ROOT%\assets"
set "ICON=%ASSETS%\NM_icon.ico"
set "LOGO=%ASSETS%\LOGO.png"

:: Clean
echo  Limpiando builds anteriores...
if exist "%DIST%\NeuroMood Suite"      rmdir /s /q "%DIST%\NeuroMood Suite"      2>nul
if exist "%DIST%\NeuroMood Hub Pro"  rmdir /s /q "%DIST%\NeuroMood Hub Pro"  2>nul
if exist "%ROOT%\NeuroMood Suite.spec"       del /q "%ROOT%\NeuroMood Suite.spec"       2>nul
if exist "%ROOT%\NeuroMood Hub Pro.spec"  del /q "%ROOT%\NeuroMood Hub Pro.spec"  2>nul
if not exist "%DIST%"  mkdir "%DIST%"
if not exist "%BUILD%" mkdir "%BUILD%"

set BASE=--noconfirm %MODE% --windowed^
 --icon "%ICON%"^
 --add-data "%LOGO%;."^
 --add-data "%ICON%;."^
 --add-data "%ROOT%\shared;shared"^
 --workpath "%BUILD%"^
 --paths "%ROOT%"

set SHARED_HI=^
 --hidden-import shared^
 --hidden-import supabase^
 --hidden-import sqlite3^
 --hidden-import PIL^
 --hidden-import pystray^
 --hidden-import pystray._win32^
 --hidden-import winotify

:: ============================================================
::  [1/2] App Paciente
:: ============================================================
echo  [1/2] Compilando NeuroMood Suite...
pyinstaller %BASE%^
 --add-data "%ROOT%\app;app"^
 --distpath "%DIST%"^
 --hidden-import PyQt6^
 %SHARED_HI%^
 --hidden-import app.home_qt^
 --hidden-import app.modules.animo_qt^
 --hidden-import app.modules.respiracion_qt^
 --hidden-import app.modules.registro_tcc_qt^
 --hidden-import app.modules.rutina_qt^
 --hidden-import app.modules.actividades_qt^
 --hidden-import app.modules.timer_qt^
 --hidden-import app.modules.avisos_qt^
 --hidden-import app.motor_activacion^
 --hidden-import app.avisos_daemon^
 --name "NeuroMood Suite"^
 "%ROOT%\app\main_qt.py"
if %ERRORLEVEL% NEQ 0 goto :error
echo     OK: dist\NeuroMood Suite\
echo.

:: ============================================================
::  [2/2] NeuroMood Hub Pro
:: ============================================================
echo  [2/2] Compilando NeuroMood Hub Pro...
pyinstaller %BASE%^
 --add-data "%ROOT%\hub;hub"^
 --distpath "%DIST%"^
 --hidden-import PyQt6^
 --hidden-import pyqtgraph^
 %SHARED_HI%^
 --hidden-import groq^
 --hidden-import google.generativeai^
 --hidden-import openai^
 --hidden-import reportlab^
 --hidden-import reportlab.lib^
 --hidden-import reportlab.lib.pagesizes^
 --hidden-import reportlab.lib.styles^
 --hidden-import reportlab.lib.units^
 --hidden-import reportlab.platypus^
 --hidden-import numpy^
 --name "NeuroMood Hub Pro"^
 "%ROOT%\hub\main_qt.py"
if %ERRORLEVEL% NEQ 0 goto :error
echo     OK: dist\NeuroMood Hub Pro\
echo.

echo ============================================================
echo  BUILD EXITOSO [%LABEL%]
echo.
echo  dist\NeuroMood Suite\NeuroMood Suite.exe
echo  dist\NeuroMood Hub Pro\NeuroMood Hub Pro.exe
echo.
echo  Siguiente: BUILD_INSTALLER.bat / BUILD_INSTALLER_PRO.bat
echo ============================================================
pause
goto :end

:error
echo ============================================================
echo  ERROR - La compilacion fallo.
echo ============================================================
pause

:end
