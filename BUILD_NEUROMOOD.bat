@echo off
setlocal enabledelayedexpansion

REM ============================================================================
REM BUILD_NEUROMOOD.bat — Launcher oficial del build NeuroMood V3
REM ============================================================================
REM Delega a build_neuromood.py (raiz del repo) pasando todos los flags.
REM
REM Flags principales soportados (vienen del .py):
REM   --dry-run             Validar rutas sin compilar
REM   --clean               Cache limpia de PyInstaller (--clean por target)
REM   --clean-all           Borrar dist/, build/ y specs antes de empezar
REM   --keep-build          Conservar build/ tras compilar (diagnostico)
REM   --only LABEL          Compilar solo el target indicado (repetible)
REM   --skip LABEL          Saltar un target (repetible)
REM   --installer-mode {nested,external}
REM                         Default: nested (bundle todo-en-uno)
REM
REM Ejemplos:
REM   BUILD_NEUROMOOD.bat --dry-run
REM   BUILD_NEUROMOOD.bat --clean
REM   BUILD_NEUROMOOD.bat --only "NeuroMood Hub"
REM   BUILD_NEUROMOOD.bat --installer-mode external
REM ============================================================================

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"

title NeuroMood V3 - Build

set "BUILD_SCRIPT=%ROOT%\build_neuromood.py"
if not exist "%BUILD_SCRIPT%" (
    echo [ERROR] No se encontro build_neuromood.py en la raiz: %ROOT%
    pause
    exit /b 1
)

REM ── Detectar Python: venv activo > .venv/venv local > py 3.12 > py 3 > system
set "PYTHON_EXE="

if defined VIRTUAL_ENV (
    if exist "%VIRTUAL_ENV%\Scripts\python.exe" (
        set PYTHON_EXE="%VIRTUAL_ENV%\Scripts\python.exe"
        echo [INFO] Python: entorno virtual activo !VIRTUAL_ENV!
    )
)

if not defined PYTHON_EXE (
    if exist "%ROOT%\.venv\Scripts\python.exe" (
        set PYTHON_EXE="%ROOT%\.venv\Scripts\python.exe"
        echo [INFO] Python: .venv local
    ) else if exist "%ROOT%\venv\Scripts\python.exe" (
        set PYTHON_EXE="%ROOT%\venv\Scripts\python.exe"
        echo [INFO] Python: venv local
    )
)

if not defined PYTHON_EXE (
    where py >nul 2>nul
    if !errorlevel! equ 0 (
        py -3.12 -c "import sys" >nul 2>nul
        if !errorlevel! equ 0 (
            set "PYTHON_EXE=py -3.12"
            echo [INFO] Python: py -3.12
        ) else (
            py -3 -c "import sys" >nul 2>nul
            if !errorlevel! equ 0 (
                set "PYTHON_EXE=py -3"
                echo [INFO] Python: py -3
            )
        )
    )
)

if not defined PYTHON_EXE (
    where python >nul 2>nul
    if !errorlevel! equ 0 (
        set "PYTHON_EXE=python"
        echo [INFO] Python: python (global)
    )
)

if not defined PYTHON_EXE (
    echo [ERROR] No se encontro una instalacion valida de Python.
    echo Instala Python 3.12+ o activa tu entorno virtual.
    pause
    exit /b 1
)

echo ==========================================
echo NeuroMood V3 - Build
echo ==========================================
echo Args: %*
echo.

%PYTHON_EXE% "%BUILD_SCRIPT%" %*
set "BUILD_RC=!errorlevel!"

echo.
if "!BUILD_RC!"=="0" (
    echo ==========================================
    echo BUILD OK
    echo ==========================================
) else (
    echo ==========================================
    echo BUILD FALLO  (exit code !BUILD_RC!)
    echo ==========================================
)

REM Pause solo si el .bat se ejecuto haciendo doble-click (no en CI).
if /I "%~1"=="" pause

exit /b !BUILD_RC!
