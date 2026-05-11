@echo off
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

if "%1"=="test" goto :test
if "%1"=="icon" goto :icon
goto :build

:: ============================================================
::  MODO TEST - Ejecutar apps sin compilar
:: ============================================================
:test
echo ============================================================
echo  NeuroMood Suite - Modo Testing (sin compilar)
echo  neuromood.com.ar
echo ============================================================
echo.
echo  Selecciona la app a testear:
echo.
echo   1. Termometro Emocional
echo   2. Recordatorios de Bienestar
echo   3. Temporizador de Actividades
echo   4. Registro de Pensamientos
echo   5. Guia de Respiracion
echo   6. Checklist de Rutina
echo   7. Hub Profesional
echo   9. Apps paciente (1-6 en secuencia)
echo   0. Salir
echo.
set /p APP=Opcion:

if "%APP%"=="1" (python "%ROOT%\apps\termometro\main.py" & goto :test)
if "%APP%"=="2" (python "%ROOT%\apps\recordatorios\main.py" & goto :test)
if "%APP%"=="3" (python "%ROOT%\apps\temporizador\main.py" & goto :test)
if "%APP%"=="4" (python "%ROOT%\apps\pensamientos\main.py" & goto :test)
if "%APP%"=="5" (python "%ROOT%\apps\respiracion\main.py" & goto :test)
if "%APP%"=="6" (python "%ROOT%\apps\checklist\main.py" & goto :test)
if "%APP%"=="7" (python "%ROOT%\apps\hub_profesional\main.py" & goto :test)
if "%APP%"=="9" goto :testall
if "%APP%"=="0" goto :end
echo Opcion invalida.
goto :test

:testall
echo.
echo Ejecutando apps paciente en secuencia...
echo (Cerra cada ventana para pasar a la siguiente)
echo.
echo [1/6] Termometro Emocional
python "%ROOT%\apps\termometro\main.py"
echo [2/6] Recordatorios de Bienestar
python "%ROOT%\apps\recordatorios\main.py"
echo [3/6] Temporizador de Actividades
python "%ROOT%\apps\temporizador\main.py"
echo [4/6] Registro de Pensamientos
python "%ROOT%\apps\pensamientos\main.py"
echo [5/6] Guia de Respiracion
python "%ROOT%\apps\respiracion\main.py"
echo [6/6] Checklist de Rutina
python "%ROOT%\apps\checklist\main.py"
echo.
echo Testing completo.
pause
goto :end

:: ============================================================
::  MODO ICON - Regenerar icono
:: ============================================================
:icon
echo Regenerando icono...
python "%ROOT%\generar_icono.py"
pause
goto :end

:: ============================================================
::  MODO BUILD - Compilar .exe
:: ============================================================
:build
echo ============================================================
echo  NeuroMood Suite - Compilacion completa
echo  Apps paciente (dist\) + Hub Profesional (dist\pro\)
echo  neuromood.com.ar
echo ============================================================
echo.
echo  Uso: BUILD_ALL.bat [test^|icon^|build]
echo    test  - Ejecutar apps sin compilar (testing rapido)
echo    icon  - Regenerar NM_icon.ico
echo    build - Compilar .exe (por defecto)
echo.

cd /d "%ROOT%"

set "DIST=%ROOT%\dist"
set "BUILD=%ROOT%\build"
set "DIST_PRO=%ROOT%\dist\pro"
set "ICON=%ROOT%\NM_icon.ico"
set "LOGO=%ROOT%\LOGO.png"
set "SHARED=%ROOT%\shared"

if not exist "%DIST%" mkdir "%DIST%"
if not exist "%BUILD%" mkdir "%BUILD%"
if not exist "%DIST_PRO%" mkdir "%DIST_PRO%"

:: Hidden imports comunes a todas las apps paciente
set COMMON=--noconfirm --onefile --windowed --icon "%ICON%" --add-data "%LOGO%;." --add-data "%ICON%;." --add-data "%SHARED%;shared" --distpath "%DIST%" --workpath "%BUILD%" --paths "%ROOT%" --hidden-import shared --hidden-import shared.theme --hidden-import shared.db --hidden-import shared.components --hidden-import shared.utils --hidden-import shared.sync --hidden-import shared.identidad --hidden-import supabase --hidden-import supabase._sync --hidden-import supabase._async --hidden-import postgrest --hidden-import storage3 --hidden-import supabase_auth --hidden-import realtime --hidden-import PIL --hidden-import PIL._tkinter_finder --hidden-import sqlite3 --hidden-import _sqlite3

:: ── Apps paciente ──────────────────────────────────────────────────────────

echo [1/7] Compilando TermometroEmocional.exe...
pyinstaller %COMMON% --paths "%ROOT%\apps\activacion" --hidden-import motor --name "TermometroEmocional" "%ROOT%\apps\termometro\main.py"
if %ERRORLEVEL% NEQ 0 goto :error

echo [2/7] Compilando RecordatoriosBienestar.exe...
pyinstaller %COMMON% --hidden-import pystray --hidden-import pygame --hidden-import numpy --name "RecordatoriosBienestar" "%ROOT%\apps\recordatorios\main.py"
if %ERRORLEVEL% NEQ 0 goto :error

echo [3/7] Compilando TemporizadorActividades.exe...
pyinstaller %COMMON% --paths "%ROOT%\apps\temporizador" --hidden-import pygame --hidden-import numpy --hidden-import sonido --hidden-import presets --name "TemporizadorActividades" "%ROOT%\apps\temporizador\main.py"
if %ERRORLEVEL% NEQ 0 goto :error

echo [4/7] Compilando RegistroPensamientos.exe...
pyinstaller %COMMON% --name "RegistroPensamientos" "%ROOT%\apps\pensamientos\main.py"
if %ERRORLEVEL% NEQ 0 goto :error

echo [5/7] Compilando GuiaRespiracion.exe...
pyinstaller %COMMON% --name "GuiaRespiracion" "%ROOT%\apps\respiracion\main.py"
if %ERRORLEVEL% NEQ 0 goto :error

echo [6/7] Compilando ChecklistRutina.exe...
pyinstaller %COMMON% --paths "%ROOT%\apps\checklist" --hidden-import pygame --hidden-import numpy --hidden-import plantillas --hidden-import editor_checklist --name "ChecklistRutina" "%ROOT%\apps\checklist\main.py"
if %ERRORLEVEL% NEQ 0 goto :error

:: ── Hub Profesional ────────────────────────────────────────────────────────

echo [7/7] Compilando HubProfesional.exe...
pyinstaller --noconfirm --onefile --windowed --icon "%ICON%" --add-data "%LOGO%;." --add-data "%ICON%;." --add-data "%SHARED%;shared" --distpath "%DIST_PRO%" --workpath "%BUILD%" --paths "%ROOT%" --paths "%ROOT%\apps\activacion" --paths "%ROOT%\apps\checklist" --paths "%ROOT%\apps\temporizador" --hidden-import shared --hidden-import shared.theme --hidden-import shared.db --hidden-import shared.components --hidden-import shared.utils --hidden-import supabase --hidden-import reportlab --hidden-import reportlab.lib --hidden-import reportlab.lib.pagesizes --hidden-import reportlab.lib.styles --hidden-import reportlab.lib.units --hidden-import reportlab.platypus --hidden-import PIL --hidden-import PIL._tkinter_finder --hidden-import sqlite3 --hidden-import _sqlite3 --hidden-import terapeuta --hidden-import motor --hidden-import perfil --hidden-import analisis --hidden-import editor_checklist --hidden-import plantillas --hidden-import editor_presets --hidden-import presets --hidden-import sonido --name "HubProfesional" "%ROOT%\apps\hub_profesional\main.py"
if %ERRORLEVEL% NEQ 0 goto :error

:: ── Limpieza de .spec ─────────────────────────────────────────────────────

del "%ROOT%\TermometroEmocional.spec"    2>nul
del "%ROOT%\RecordatoriosBienestar.spec" 2>nul
del "%ROOT%\TemporizadorActividades.spec" 2>nul
del "%ROOT%\RegistroPensamientos.spec"   2>nul
del "%ROOT%\GuiaRespiracion.spec"        2>nul
del "%ROOT%\ChecklistRutina.spec"        2>nul
del "%ROOT%\HubProfesional.spec"         2>nul

echo.
echo ============================================================
echo  COMPILACION EXITOSA
echo.
echo  Apps paciente:    dist\
dir "%DIST%\*.exe" /b 2>nul
echo.
echo  Hub Profesional:  dist\pro\
dir "%DIST_PRO%\*.exe" /b 2>nul
echo ============================================================
echo.
pause
goto :end

:error
echo.
echo ============================================================
echo  ERROR - La compilacion fallo. Revisa el mensaje de arriba.
echo ============================================================
echo.
pause

:end
