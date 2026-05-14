@echo off
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

if "%1"=="test" goto :test
if "%1"=="icon" goto :icon
if "%1"=="dev" goto :dev
goto :build

:: ============================================================
::  MODO TEST - Ejecutar sin compilar (PyQt6)
:: ============================================================
:test
echo ============================================================
echo  NeuroMood V3 - Modo Testing (PyQt6)
echo  neuromood.com.ar
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
::  MODO ICON
:: ============================================================
:icon
echo Regenerando icono...
python "%ROOT%\generar_icono.py"
pause
goto :end

:: ============================================================
::  MODO DEV - Compilar con --onedir (arranque instantaneo)
::  Para desarrollo y testing: la ventana abre en <1s.
::  NO usar para distribucion final.
::  BUILD_ALL.bat dev
:: ============================================================
:dev
echo ============================================================
echo  NeuroMood V3 - Modo DEV (onedir, arranque rapido)
echo  Para distribucion final usa BUILD_ALL.bat sin argumentos
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

set BASE_DEV=--noconfirm --onedir --windowed^
 --icon "%ICON%"^
 --add-data "%LOGO%;."^
 --add-data "%ICON%;."^
 --add-data "%SHARED%;shared"^
 --workpath "%BUILD%"^
 --paths "%ROOT%"

set SHARED_HI=^
 --collect-all shared^
 --hidden-import supabase^
 --hidden-import supabase._sync^
 --hidden-import supabase._async^
 --hidden-import postgrest^
 --hidden-import storage3^
 --hidden-import realtime^
 --hidden-import sqlite3^
 --hidden-import PIL^
 --hidden-import pystray^
 --hidden-import pystray._win32^
 --hidden-import winotify

echo [1/2] Compilando NeuroMood.exe (onedir)...
pyinstaller %BASE_DEV%^
 --add-data "%APP_DIR%;app"^
 --distpath "%DIST%"^
 --collect-all PyQt6^
 %SHARED_HI%^
 --collect-submodules app^
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

echo [2/2] Compilando HubProfesional.exe (onedir)...
pyinstaller %BASE_DEV%^
 --add-data "%HUB_DIR%;hub"^
 --distpath "%DIST_PRO%"^
 --collect-all PyQt6^
 --hidden-import pyqtgraph^
 %SHARED_HI%^
 --collect-submodules hub^
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

del "%ROOT%\NeuroMood.spec"       2>nul
del "%ROOT%\HubProfesional.spec"  2>nul

echo ============================================================
echo  COMPILACION DEV EXITOSA (onedir, arranque <1s)
echo  App paciente:      dist\NeuroMood\NeuroMood.exe
echo  Hub Profesional:   dist\pro\HubProfesional\HubProfesional.exe
echo ============================================================
pause
goto :end

:: ============================================================
::  MODO BUILD - 2 EXEs (PyQt6)
:: Salida:
::   dist\NeuroMood.exe            <- app paciente
::   dist\pro\HubProfesional.exe   <- hub profesional
::
:: Flujo de distribucion:
::   1. BUILD_ALL.bat              -> genera los 2 EXEs
::   2. BUILD_INSTALLER.bat        -> empaqueta instalador paciente
::   3. BUILD_INSTALLER_PRO.bat    -> empaqueta instalador Hub
:: ============================================================
:build
echo ============================================================
echo  NeuroMood V3 - Compilacion (PyQt6)
echo  [1/2] NeuroMood.exe  +  [2/2] HubProfesional.exe
echo  neuromood.com.ar
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

:: ── Flags comunes (sin --collect-all aun; se agregan por EXE) ────────────────
set BASE=--noconfirm --onefile --windowed^
 --icon "%ICON%"^
 --add-data "%LOGO%;."^
 --add-data "%ICON%;."^
 --add-data "%SHARED%;shared"^
 --workpath "%BUILD%"^
 --paths "%ROOT%"

:: ── Hidden imports compartidos (shared/ + infra) ─────────────────────────────
set SHARED_HI=^
 --collect-all shared^
 --hidden-import supabase^
 --hidden-import supabase._sync^
 --hidden-import supabase._async^
 --hidden-import postgrest^
 --hidden-import storage3^
 --hidden-import realtime^
 --hidden-import sqlite3^
 --hidden-import _sqlite3^
 --hidden-import PIL^
 --hidden-import pystray^
 --hidden-import pystray._win32^
 --hidden-import winotify

:: ============================================================
::  [1/2] App Paciente — NeuroMood.exe
::  Entry point: app\main_qt.py
:: ============================================================
echo [1/2] Compilando NeuroMood.exe...

pyinstaller %BASE%^
 --add-data "%APP_DIR%;app"^
 --distpath "%DIST%"^
 --collect-all PyQt6^
 %SHARED_HI%^
 --collect-submodules app^
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
echo     OK: dist\NeuroMood.exe
echo.

:: ============================================================
::  [2/2] Hub Profesional — HubProfesional.exe
::  Entry point: hub\main_qt.py
:: ============================================================
echo [2/2] Compilando HubProfesional.exe...

pyinstaller %BASE%^
 --add-data "%HUB_DIR%;hub"^
 --distpath "%DIST_PRO%"^
  --collect-all PyQt6^
  --hidden-import pyqtgraph^
  %SHARED_HI%^
  --collect-submodules hub^
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
echo     OK: dist\pro\HubProfesional.exe
echo.

:: ── Limpiar .spec generados por pyinstaller ───────────────────────────────────
del "%ROOT%\NeuroMood.spec"       2>nul
del "%ROOT%\HubProfesional.spec"  2>nul

echo ============================================================
echo  COMPILACION EXITOSA
echo.
echo  App paciente:      dist\NeuroMood.exe
echo  Hub Profesional:   dist\pro\HubProfesional.exe
echo.
echo  Siguiente paso:
echo    BUILD_INSTALLER.bat      -> genera Instalar NeuroMood.exe
echo    BUILD_INSTALLER_PRO.bat  -> genera Instalar Hub Profesional.exe
echo ============================================================
echo.
pause
goto :end

:error
echo.
echo ============================================================
echo  ERROR - La compilacion fallo. Revisa el mensaje arriba.
echo ============================================================
echo.
pause

:end
