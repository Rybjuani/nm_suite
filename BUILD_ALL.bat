@echo off
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

if "%1"=="test" goto :test
if "%1"=="release" goto :release
goto :build

:: ============================================================
::  MODO TEST
:: ============================================================
:test
echo ============================================================
echo  NeuroMood V3 - Modo Testing
echo ============================================================
echo.
for /d /r "%ROOT%" %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
echo  1. NeuroMood Suite        (app\main_qt.py)
echo  2. NeuroMood Hub Pro      (hub\main_qt.py)
echo  0. Salir
set /p APP="> "
if "%APP%"=="1" (python "%ROOT%\app\main_qt.py" & goto :test)
if "%APP%"=="2" (python "%ROOT%\hub\main_qt.py"   & goto :test)
if "%APP%"=="0" goto :end
goto :test

:: ============================================================
::  BUILD (default) - onedir, arranque <1s
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
echo ============================================================
echo.

cd /d "%ROOT%"

:: Kill any running instances that would lock dist/ folder
taskkill /f /im "NeuroMood Suite.exe"      2>nul
taskkill /f /im "NeuroMood Hub Pro.exe"    2>nul
timeout /t 1 /nobreak >nul

set "DIST=%ROOT%\dist"
set "BUILD=%ROOT%\build"
set "ASSETS=%ROOT%\assets"

:: Clean
echo  Limpiando builds anteriores...
rd /s /q "%DIST%\NeuroMood Suite"             2>nul
rd /s /q "%DIST%\NeuroMood Hub Pro"           2>nul
rd /s /q "%DIST%\NeuroMood"                   2>nul
rd /s /q "%DIST%\HubProfesional"              2>nul
rd /s /q "%BUILD%\NeuroMood Suite"            2>nul
rd /s /q "%BUILD%\NeuroMood Hub Pro"          2>nul
del "%ROOT%\NeuroMood Suite.spec"             2>nul
del "%ROOT%\NeuroMood Hub Pro.spec"           2>nul
del "%ROOT%\NeuroMood.spec"                   2>nul
del "%ROOT%\HubProfesional.spec"              2>nul
if not exist "%DIST%"  mkdir "%DIST%"
if not exist "%BUILD%" mkdir "%BUILD%"

:: ============================================================
::  [1/2] NeuroMood Suite
:: ============================================================
echo  [1/2] Compilando NeuroMood Suite...
pyinstaller --noconfirm %MODE% --windowed --clean^
 --icon "%ASSETS%\NM_icon.ico"^
 --add-data "%ASSETS%\LOGO.png;."^
 --add-data "%ASSETS%\NM_icon.ico;."^
 --add-data "%ROOT%\shared;shared"^
 --add-data "%ROOT%\app;app"^
 --distpath "%DIST%"^
 --workpath "%BUILD%"^
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
echo     OK: dist\NeuroMood Suite\
echo.

:: ============================================================
::  [2/2] NeuroMood Hub Pro
:: ============================================================
echo  [2/2] Compilando NeuroMood Hub Pro...
pyinstaller --noconfirm %MODE% --windowed --clean^
 --icon "%ASSETS%\NM_icon.ico"^
 --add-data "%ASSETS%\LOGO.png;."^
 --add-data "%ASSETS%\NM_icon.ico;."^
 --add-data "%ROOT%\shared;shared"^
 --add-data "%ROOT%\hub;hub"^
 --distpath "%DIST%"^
 --workpath "%BUILD%"^
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
echo     OK: dist\NeuroMood Hub Pro\
echo.

echo ============================================================
echo  BUILD EXITOSO [%LABEL%]
echo  dist\NeuroMood Suite\NeuroMood Suite.exe
echo  dist\NeuroMood Hub Pro\NeuroMood Hub Pro.exe
echo ============================================================
pause
goto :end

:error
echo ============================================================
echo  ERROR - La compilacion fallo.
echo ============================================================
pause

:end
