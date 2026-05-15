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
echo  1. NeuroMood Suite        (app\main_qt.py)
echo  2. NeuroMood Hub Pro      (hub\main_qt.py)
echo  0. Salir
set /p APP="> "
if "%APP%"=="1" (python "%ROOT%\app\main_qt.py" & goto :test)
if "%APP%"=="2" (python "%ROOT%\hub\main_qt.py" & goto :test)
if "%APP%"=="0" goto :end
goto :test

:: ============================================================
::  BUILD (default) - onedir, arranque <1s
::  BUILD_ALL.bat          -> desarrollo (onedir)
::  BUILD_ALL.bat release  -> distribucion (onefile)
:: ============================================================
:build
set "MODE=--onedir"
set "LABEL=onedir (arranque <1s)"
goto :compile

:release
set "MODE=--onefile"
set "LABEL=onefile (distribucion)"
goto :compile

:compile
echo ============================================================
echo  NeuroMood V3 - Build [%LABEL%]
echo ============================================================

cd /d "%ROOT%"

:: Clean silently
rd /s /q "%ROOT%\dist\NeuroMood Suite"     2>nul
rd /s /q "%ROOT%\dist\NeuroMood Hub Pro"   2>nul
rd /s /q "%ROOT%\dist\NeuroMood"           2>nul
rd /s /q "%ROOT%\dist\HubProfesional"      2>nul
rd /s /q "%ROOT%\build\NeuroMood Suite"     2>nul
rd /s /q "%ROOT%\build\NeuroMood Hub Pro"   2>nul
del "%ROOT%\NeuroMood Suite.spec"          2>nul
del "%ROOT%\NeuroMood Hub Pro.spec"        2>nul
if not exist "%ROOT%\dist"  mkdir "%ROOT%\dist"
if not exist "%ROOT%\build" mkdir "%ROOT%\build"

:: [1/2] NeuroMood Suite
echo  [1/2] NeuroMood Suite...
pyinstaller --noconfirm %MODE% --windowed --clean --optimize 2^
 --icon "%ROOT%\assets\NM_icon.ico"^
 --add-data "%ROOT%\assets\LOGO.png;."^
 --add-data "%ROOT%\assets\NM_icon.ico;."^
 --add-data "%ROOT%\shared;shared"^
 --add-data "%ROOT%\app;app"^
 --distpath "%ROOT%\dist"^
 --workpath "%ROOT%\build"^
 --paths "%ROOT%"^
 --log-level ERROR^
 --hidden-import pystray^
 --hidden-import pystray._win32^
 --hidden-import winotify^
 --hidden-import PIL^
 --hidden-import sqlite3^
 --name "NeuroMood Suite"^
 "%ROOT%\app\main_qt.py"
if %ERRORLEVEL% NEQ 0 goto :error
echo     OK

:: [2/2] NeuroMood Hub Pro
echo  [2/2] NeuroMood Hub Pro...
pyinstaller --noconfirm %MODE% --windowed --clean --optimize 2^
 --icon "%ROOT%\assets\NM_icon.ico"^
 --add-data "%ROOT%\assets\LOGO.png;."^
 --add-data "%ROOT%\assets\NM_icon.ico;."^
 --add-data "%ROOT%\shared;shared"^
 --add-data "%ROOT%\hub;hub"^
 --distpath "%ROOT%\dist"^
 --workpath "%ROOT%\build"^
 --paths "%ROOT%"^
 --log-level ERROR^
 --hidden-import supabase^
 --hidden-import pystray^
 --hidden-import pystray._win32^
 --hidden-import winotify^
 --hidden-import PIL^
 --hidden-import sqlite3^
 --hidden-import groq^
 --hidden-import google.generativeai^
 --hidden-import openai^
 --hidden-import pyqtgraph^
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
echo     OK

echo ============================================================
echo  BUILD EXITOSO [%LABEL%]
echo  dist\NeuroMood Suite\NeuroMood Suite.exe
echo  dist\NeuroMood Hub Pro\NeuroMood Hub Pro.exe
echo ============================================================
exit /b 0

:error
echo ============================================================
echo  ERROR - La compilacion fallo.
echo ============================================================
exit /b 1

:end
