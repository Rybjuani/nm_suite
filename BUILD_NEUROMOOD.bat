@echo off
setlocal enabledelayedexpansion
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

cd /d "%ROOT%"
title NeuroMood V3 - Build oficial limpio

:: Buscar build_neuromood.py
set "BUILD_SCRIPT=%ROOT%\build_neuromood.py"
if not exist "%BUILD_SCRIPT%" (
    echo [ERROR] No se encontro build_neuromood.py en la raiz del repositorio: %ROOT%
    pause
    exit /b 1
)

set "LOG_FILE=%ROOT%\build.log"

echo ============================================================
echo  NeuroMood V3 - Constructor de Ejecutables
echo ============================================================
echo Proyecto: %ROOT%
echo Script:   build_neuromood.py
echo.

:: Detectar entorno de Python
set "PYTHON_EXE="

:: 1. Detectar si hay un entorno virtual activo en la sesion actual
if defined VIRTUAL_ENV (
    if exist "%VIRTUAL_ENV%\Scripts\python.exe" (
        set "PYTHON_EXE=%VIRTUAL_ENV%\Scripts\python.exe"
        echo [INFO] Usando entorno virtual activo: !VIRTUAL_ENV!
    )
)

:: 2. Buscar entornos virtuales locales tipicos (.venv o venv)
if not defined PYTHON_EXE (
    if exist "%ROOT%\.venv\Scripts\python.exe" (
        set "PYTHON_EXE=%ROOT%\.venv\Scripts\python.exe"
        echo [INFO] Usando entorno virtual local: .venv
    ) else if exist "%ROOT%\venv\Scripts\python.exe" (
        set "PYTHON_EXE=%ROOT%\venv\Scripts\python.exe"
        echo [INFO] Usando entorno virtual local: venv
    )
)

:: 3. Probar el launcher global de Windows (py) prefiriendo 3.12
if not defined PYTHON_EXE (
    where py >nul 2>nul
    if !errorlevel! equ 0 (
        py -3.12 -c "import sys" >nul 2>nul
        if !errorlevel! equ 0 (
            set "PYTHON_EXE=py -3.12"
            echo [INFO] Usando lanzador de Windows: py -3.12
        ) else (
            py -3 -c "import sys" >nul 2>nul
            if !errorlevel! equ 0 (
                set "PYTHON_EXE=py -3"
                echo [INFO] Usando lanzador de Windows: py -3
            )
        )
    )
)

:: 4. Fallback al comando python global del sistema
if not defined PYTHON_EXE (
    where python >nul 2>nul
    if !errorlevel! equ 0 (
        set "PYTHON_EXE=python"
        echo [INFO] Usando Python global del sistema
    )
)

:: 5. Si no se detecto nada, abortar
if not defined PYTHON_EXE (
    echo [ERROR] No se pudo encontrar una instalacion de Python valida.
    echo Asegurate de tener Python instalado o activar tu entorno virtual.
    echo.
    pause
    exit /b 1
)

echo.
echo Ejecutando compilacion...
echo %PYTHON_EXE% build_neuromood.py --clean-all --clean %*
echo.

%PYTHON_EXE% "%BUILD_SCRIPT%" --clean-all --clean %*

if errorlevel 1 (
    echo.
    echo ============================================================
    echo  BUILD FALLIDO (Codigo de salida: !errorlevel!)
    echo ============================================================
    echo Revisa el log completo en: %LOG_FILE%
    echo.
    if exist "%LOG_FILE%" (
        echo Ultimas lineas del log:
        echo ------------------------------------------------------------
        powershell -Command "Get-Content '%LOG_FILE%' -Tail 30" 2>nul
        echo ------------------------------------------------------------
    )
    echo.
    pause
    exit /b !errorlevel!
)

echo.
echo ============================================================
echo  Build finalizado correctamente
echo ============================================================
echo Ejecutables en: %ROOT%\dist
echo Log completo:   %LOG_FILE%
echo.
if exist "%ROOT%\dist" (
    dir "%ROOT%\dist" /b
)
exit /b 0
