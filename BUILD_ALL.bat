@echo off
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

if "%1"=="test" goto :test
if "%1"=="icon" goto :icon
if "%1"=="release" goto :release
goto :build

:: ============================================================
::  MODO TEST - Ejecutar sin compilar (desarrollo rapido)
:: ============================================================
:test
echo ============================================================
echo  NeuroMood V3 - Modo Testing (PyQt6)
echo ============================================================
echo.
echo  Limpiando __pycache__...
for /d /r "%ROOT%" %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
echo.
echo  Selecciona:
echo   1. App Paciente      (app\main_qt.py)
echo   2. Hub Profesional   (hub\main_qt.py)
echo   0. Salir
echo.
set /p APP=Opcion:
if "%APP%"=="1" (python "%ROOT%\app\main_qt.py" & goto :test)
if "%APP%"=="2" (python "%ROOT%\hub\main_qt.py" & goto :test)
if "%APP%"=="0" goto :end
echo Opcion invalida.
goto :test

:: ============================================================
::  MODO ICONO
:: ============================================================
:icon
echo Regenerando icono...
python "%ROOT%\generar_icono.py"
pause
goto :end

:: ============================================================
::  MODO BUILD (default) - onedir, arranque instantaneo
::  BUILD_ALL.bat           → compila para desarrollo (onedir, <1s arranque)
::  BUILD_ALL.bat release   → compila para distribucion (onefile, .exe unico)
::
::  Salida onedir:
::    dist\NeuroMood\NeuroMood.exe
::    dist\pro\HubProfesional\HubProfesional.exe
::
::  Para distribuir: comprime la carpeta dist\NeuroMood\ en un .zip
::  o usa BUILD_ALL.bat release para un solo .exe (mas lento al abrir).
:: ============================================================
:build
set "MODE=--onedir"
set "MODE_LABEL=onedir (arranque rapido)"
goto :compile

:: ============================================================
::  MODO RELEASE - onefile, .exe unico para distribucion
::  Mas lento al compilar (~3-5 min) y al abrir (~4-8s).
:: ============================================================
:release
set "MODE=--onefile"
set "MODE_LABEL=onefile (distribucion)"
goto :compile

:: ============================================================
::  COMPILACION
:: ============================================================
:compile
echo ============================================================
echo  NeuroMood V3 - Compilacion [%MODE_LABEL%]
echo  [1/2] NeuroMood  +  [2/2] HubProfesional
echo ============================================================
echo.

cd /d "%ROOT%"

set "DIST=%ROOT%\dist"
set "BUILD=%ROOT%\build"
set "DIST_PRO=%ROOT%\dist\pro"
set "ASSETS=%ROOT%\assets"
set "ICON=%ASSETS%\NM_icon.ico"
set "LOGO=%ASSETS%\LOGO.png"
set "SHARED=%ROOT%\shared"
set "APP_DIR=%ROOT%\app"
set "HUB_DIR=%ROOT%\hub"

if not exist "%DIST%"     mkdir "%DIST%"
if not exist "%BUILD%"    mkdir "%BUILD%"
if not exist "%DIST_PRO%" mkdir "%DIST_PRO%"

:: Clean previous build
if exist "%DIST%\NeuroMood"         rmdir /s /q "%DIST%\NeuroMood"         2>nul
if exist "%DIST_PRO%\HubProfesional" rmdir /s /q "%DIST_PRO%\HubProfesional" 2>nul

set BASE=--noconfirm %MODE% --windowed^
 --icon "%ICON%"^
 --add-data "%LOGO%;."^
 --add-data "%ICON%;."^
 --add-data "%SHARED%;shared"^
 --workpath "%BUILD%"^
 --paths "%ROOT%"

set SHARED_HI=^
 --collect-all shared^
 --hidden-import supabase^
 --hidden-import sqlite3^
 --hidden-import PIL^
 --hidden-import pystray^
 --hidden-import pystray._win32^
 --hidden-import winotify

:: ============================================================
::  [1/2] App Paciente
:: ============================================================
echo [1/2] Compilando NeuroMood...

pyinstaller %BASE%^
 --add-data "%APP_DIR%;app"^
 --distpath "%DIST%"^
 --collect-all PyQt6^
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
 --name "NeuroMood"^
 "%ROOT%\app\main_qt.py"

if %ERRORLEVEL% NEQ 0 goto :error
echo     OK: dist\NeuroMood\
echo.

:: ============================================================
::  [2/2] Hub Profesional
:: ============================================================
echo [2/2] Compilando HubProfesional...

pyinstaller %BASE%^
 --add-data "%HUB_DIR%;hub"^
 --distpath "%DIST_PRO%"^
 --collect-all PyQt6^
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
 --name "HubProfesional"^
 "%ROOT%\hub\main_qt.py"

if %ERRORLEVEL% NEQ 0 goto :error
echo     OK: dist\pro\HubProfesional\
echo.

:: Clean .spec files
del "%ROOT%\NeuroMood.spec"       2>nul
del "%ROOT%\HubProfesional.spec"  2>nul

echo ============================================================
echo  COMPILACION EXITOSA [%MODE_LABEL%]
echo.
if "%MODE%"=="--onedir" (
    echo  App paciente:      dist\NeuroMood\NeuroMood.exe
    echo  Hub Profesional:   dist\pro\HubProfesional\HubProfesional.exe
    echo.
    echo  Para distribuir: comprime dist\NeuroMood\ en un .zip
    echo  O usa: BUILD_ALL.bat release (onefile para distribucion)
) else (
    echo  App paciente:      dist\NeuroMood.exe
    echo  Hub Profesional:   dist\pro\HubProfesional.exe
)
echo.
echo  Siguiente paso:
echo    BUILD_INSTALLER.bat      -> empaqueta instalador suite
echo    BUILD_INSTALLER_PRO.bat  -> empaqueta instalador Hub
echo ============================================================
pause
goto :end

:error
echo.
echo ============================================================
echo  ERROR - La compilacion fallo. Revisa el mensaje arriba.
echo ============================================================
pause

:end
