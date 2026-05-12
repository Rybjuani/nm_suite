@echo off
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

if "%1"=="test" goto :test
if "%1"=="icon" goto :icon
goto :build

:: ============================================================
::  MODO TEST - Ejecutar sin compilar
:: ============================================================
:test
echo ============================================================
echo  NeuroMood V3 - Modo Testing
echo  neuromood.com.ar
echo ============================================================
echo.
echo  Selecciona:
echo   1. App Paciente  (app\main.py)
echo   2. Hub Profesional  (hub\main.py)
echo   0. Salir
echo.
set /p APP=Opcion:
if "%APP%"=="1" (python "%ROOT%\app\main.py" & goto :test)
if "%APP%"=="2" (python "%ROOT%\hub\main.py" & goto :test)
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
::  MODO BUILD - 2 EXEs
:: ============================================================
:build
echo ============================================================
echo  NeuroMood V3 - Compilacion
echo  [1/2] NeuroMood.exe  +  [2/2] HubProfesional.exe
echo  neuromood.com.ar
echo ============================================================
echo.

cd /d "%ROOT%"

set "DIST=%ROOT%\dist"
set "BUILD=%ROOT%\build"
set "DIST_PRO=%ROOT%\dist\pro"
set "ICON=%ROOT%\NM_icon.ico"
set "LOGO=%ROOT%\LOGO.png"
set "SHARED=%ROOT%\shared"
set "APP_DIR=%ROOT%\app"
set "HUB_DIR=%ROOT%\hub"

if not exist "%DIST%"     mkdir "%DIST%"
if not exist "%BUILD%"    mkdir "%BUILD%"
if not exist "%DIST_PRO%" mkdir "%DIST_PRO%"

set COMMON=--noconfirm --onefile --windowed --icon "%ICON%"^
 --add-data "%LOGO%;."^
 --add-data "%ICON%;."^
 --add-data "%SHARED%;shared"^
 --add-data "%APP_DIR%;app"^
 --distpath "%DIST%"^
 --workpath "%BUILD%"^
 --paths "%ROOT%"^
 --hidden-import shared^
 --hidden-import shared.theme^
 --hidden-import shared.db^
 --hidden-import shared.components^
 --hidden-import shared.utils^
 --hidden-import shared.sync^
 --hidden-import shared.identidad^
 --hidden-import shared.config^
 --hidden-import shared.base_module^
 --hidden-import app.home^
 --hidden-import app.modules.animo^
 --hidden-import app.modules.respiracion^
 --hidden-import app.modules.registro_tcc^
 --hidden-import app.modules.rutina^
 --hidden-import app.modules.actividades^
 --hidden-import app.modules.timer^
 --hidden-import app.modules.avisos^
 --hidden-import app.motor_activacion^
 --hidden-import app.avisos_daemon^
 --hidden-import pystray^
 --hidden-import pystray._win32^
 --hidden-import winotify^
 --hidden-import PIL^
 --hidden-import PIL._tkinter_finder^
 --hidden-import sqlite3^
 --hidden-import _sqlite3^
 --hidden-import supabase^
 --hidden-import supabase._sync^
 --hidden-import supabase._async^
 --hidden-import postgrest^
 --hidden-import storage3^
 --hidden-import realtime

:: ── [1/2] App Paciente ──────────────────────────────────────
echo [1/2] Compilando NeuroMood.exe...
pyinstaller %COMMON% --name "NeuroMood" "%ROOT%\app\main.py"
if %ERRORLEVEL% NEQ 0 goto :error
echo     OK: dist\NeuroMood.exe
echo.

:: ── [2/2] Hub Profesional ───────────────────────────────────
echo [2/2] Compilando HubProfesional.exe...
pyinstaller --noconfirm --onefile --windowed --icon "%ICON%"^
 --add-data "%LOGO%;."^
 --add-data "%ICON%;."^
 --add-data "%SHARED%;shared"^
 --add-data "%HUB_DIR%;hub"^
 --distpath "%DIST_PRO%"^
 --workpath "%BUILD%"^
 --paths "%ROOT%"^
 --hidden-import shared^
 --hidden-import shared.theme^
 --hidden-import shared.db^
 --hidden-import shared.components^
 --hidden-import shared.utils^
 --hidden-import shared.config^
 --hidden-import hub.main^
 --hidden-import hub.pacientes^
 --hidden-import hub.visualizacion^
 --hidden-import hub.ia_asistente^
 --hidden-import hub.exportar^
 --hidden-import groq^
 --hidden-import matplotlib^
 --hidden-import matplotlib.backends.backend_tkagg^
 --hidden-import reportlab^
 --hidden-import reportlab.lib^
 --hidden-import reportlab.lib.pagesizes^
 --hidden-import reportlab.lib.styles^
 --hidden-import reportlab.lib.units^
 --hidden-import reportlab.platypus^
 --hidden-import PIL^
 --hidden-import PIL._tkinter_finder^
 --hidden-import sqlite3^
 --hidden-import _sqlite3^
 --hidden-import supabase^
 --hidden-import supabase._sync^
 --hidden-import supabase._async^
 --hidden-import postgrest^
 --hidden-import numpy^
 --name "HubProfesional" "%ROOT%\hub\main.py"
if %ERRORLEVEL% NEQ 0 goto :error
echo     OK: dist\pro\HubProfesional.exe
echo.

:: ── Limpiar .spec generados ─────────────────────────────────
del "%ROOT%\NeuroMood.spec"       2>nul
del "%ROOT%\HubProfesional.spec"  2>nul

echo ============================================================
echo  COMPILACION EXITOSA
echo.
echo  App paciente:      dist\NeuroMood.exe
echo  Hub Profesional:   dist\pro\HubProfesional.exe
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
