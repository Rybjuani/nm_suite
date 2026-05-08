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
echo   7. Visualizador de Evolucion
echo   8. Asistente de Activacion
echo   9. Todas (una por una)
echo   0. Salir
echo.
set /p APP=Opcion:

if "%APP%"=="1" (python "%ROOT%\apps\termometro\main.py" & goto :test)
if "%APP%"=="2" (python "%ROOT%\apps\recordatorios\main.py" & goto :test)
if "%APP%"=="3" (python "%ROOT%\apps\temporizador\main.py" & goto :test)
if "%APP%"=="4" (python "%ROOT%\apps\pensamientos\main.py" & goto :test)
if "%APP%"=="5" (python "%ROOT%\apps\respiracion\main.py" & goto :test)
if "%APP%"=="6" (python "%ROOT%\apps\checklist\main.py" & goto :test)
if "%APP%"=="7" (python "%ROOT%\apps\visualizador\main.py" & goto :test)
if "%APP%"=="8" (python "%ROOT%\apps\activacion\main.py" & goto :test)
if "%APP%"=="9" goto :testall
if "%APP%"=="0" goto :end
echo Opcion invalida.
goto :test

:testall
echo.
echo Ejecutando todas las apps en secuencia...
echo (Cerra cada ventana para pasar a la siguiente)
echo.
echo [1/8] Termometro Emocional
python "%ROOT%\apps\termometro\main.py"
echo [2/8] Recordatorios de Bienestar
python "%ROOT%\apps\recordatorios\main.py"
echo [3/8] Temporizador de Actividades
python "%ROOT%\apps\temporizador\main.py"
echo [4/8] Registro de Pensamientos
python "%ROOT%\apps\pensamientos\main.py"
echo [5/8] Guia de Respiracion
python "%ROOT%\apps\respiracion\main.py"
echo [6/8] Checklist de Rutina
python "%ROOT%\apps\checklist\main.py"
echo [7/8] Visualizador de Evolucion
python "%ROOT%\apps\visualizador\main.py"
echo [8/8] Asistente de Activacion
python "%ROOT%\apps\activacion\main.py"
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
echo  NeuroMood Suite - Compilacion de las 8 aplicaciones
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
set "ICON=%ROOT%\NM_icon.ico"
set "LOGO=%ROOT%\LOGO.png"
set "SHARED=%ROOT%\shared"

if not exist "%DIST%" mkdir "%DIST%"
if not exist "%BUILD%" mkdir "%BUILD%"

set COMMON=--noconfirm --onefile --windowed --icon "%ICON%" --add-data "%LOGO%;." --add-data "%ICON%;." --add-data "%SHARED%;shared" --distpath "%DIST%" --workpath "%BUILD%" --paths "%ROOT%" --hidden-import shared --hidden-import shared.theme --hidden-import shared.db --hidden-import shared.components --hidden-import shared.utils --hidden-import PIL --hidden-import PIL._tkinter_finder --hidden-import sqlite3 --hidden-import _sqlite3

echo [1/8] Compilando TermometroEmocional.exe...
pyinstaller %COMMON% --name "TermometroEmocional" "%ROOT%\apps\termometro\main.py"
if %ERRORLEVEL% NEQ 0 goto :error

echo [2/8] Compilando RecordatoriosBienestar.exe...
pyinstaller %COMMON% --hidden-import pystray --hidden-import pygame --hidden-import numpy --name "RecordatoriosBienestar" "%ROOT%\apps\recordatorios\main.py"
if %ERRORLEVEL% NEQ 0 goto :error

echo [3/8] Compilando TemporizadorActividades.exe...
pyinstaller %COMMON% --hidden-import pygame --hidden-import numpy --name "TemporizadorActividades" "%ROOT%\apps\temporizador\main.py"
if %ERRORLEVEL% NEQ 0 goto :error

echo [4/8] Compilando RegistroPensamientos.exe...
pyinstaller %COMMON% --name "RegistroPensamientos" "%ROOT%\apps\pensamientos\main.py"
if %ERRORLEVEL% NEQ 0 goto :error

echo [5/8] Compilando GuiaRespiracion.exe...
pyinstaller %COMMON% --name "GuiaRespiracion" "%ROOT%\apps\respiracion\main.py"
if %ERRORLEVEL% NEQ 0 goto :error

echo [6/8] Compilando ChecklistRutina.exe...
pyinstaller %COMMON% --hidden-import pygame --hidden-import numpy --name "ChecklistRutina" "%ROOT%\apps\checklist\main.py"
if %ERRORLEVEL% NEQ 0 goto :error

echo [7/8] Compilando VisualizadorEvolucion.exe...
pyinstaller %COMMON% --hidden-import matplotlib --hidden-import matplotlib.backends.backend_tkagg --hidden-import matplotlib.backends.backend_agg --hidden-import reportlab --hidden-import reportlab.lib --hidden-import reportlab.platypus --name "VisualizadorEvolucion" "%ROOT%\apps\visualizador\main.py"
if %ERRORLEVEL% NEQ 0 goto :error

echo [8/8] Compilando AsistenteActivacion.exe...
pyinstaller %COMMON% --hidden-import pygame --hidden-import numpy --name "AsistenteActivacion" "%ROOT%\apps\activacion\main.py"
if %ERRORLEVEL% NEQ 0 goto :error

del "%ROOT%\TermometroEmocional.spec" 2>nul
del "%ROOT%\RecordatoriosBienestar.spec" 2>nul
del "%ROOT%\TemporizadorActividades.spec" 2>nul
del "%ROOT%\RegistroPensamientos.spec" 2>nul
del "%ROOT%\GuiaRespiracion.spec" 2>nul
del "%ROOT%\ChecklistRutina.spec" 2>nul
del "%ROOT%\VisualizadorEvolucion.spec" 2>nul
del "%ROOT%\AsistenteActivacion.spec" 2>nul

echo.
echo ============================================================
echo  COMPILACION EXITOSA - Los .exe estan en: %DIST%
echo ============================================================
echo.
dir "%DIST%\*.exe"
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
