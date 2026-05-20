@echo off
setlocal
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

cd /d "%ROOT%"
title NeuroMood V3 - Build Launcher

set "BUILD_SCRIPT=%ROOT%\build_neuromood.py"
if not exist "%BUILD_SCRIPT%" (
    echo [ERROR] No se encontro build_neuromood.py en la raiz del repositorio: %ROOT%
    pause
    exit /b 1
)

:: Detectar Python
set "PYTHON_EXE="

:: 1. Preferir el entorno virtual local (.venv) si existe
if exist "%ROOT%\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%ROOT%\.venv\Scripts\python.exe"
    echo [INFO] Usando entorno virtual del proyecto: .venv
    goto run
)

:: 2. Usar entorno virtual activo si existe la variable VIRTUAL_ENV
if not defined VIRTUAL_ENV goto try_py
if not exist "%VIRTUAL_ENV%\Scripts\python.exe" goto try_py
set "PYTHON_EXE=%VIRTUAL_ENV%\Scripts\python.exe"
echo [INFO] Usando entorno virtual activo: %VIRTUAL_ENV%
goto run

:try_py
:: 3. Intentar 'py -3.12' launcher
where py >nul 2>nul
if errorlevel 1 goto try_python
py -3.12 -c "import sys" >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_EXE=py -3.12"
    goto run
)
py -3 -c "import sys" >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_EXE=py -3"
    goto run
)

:try_python
:: 4. Intentar comando 'python'
where python >nul 2>nul
if errorlevel 1 goto no_python
set "PYTHON_EXE=python"
goto run

:no_python
echo [ERROR] No se encontro ninguna instalacion de Python en el sistema.
echo Por favor, instala Python 3.12 o posterior y agregalo al PATH.
pause
exit /b 1

:run
echo ============================================================
echo  NeuroMood V3 - Iniciando compilacion oficial
echo ============================================================
echo Script: %BUILD_SCRIPT%
echo.

:: Por defecto, si no se especifican argumentos, usamos --clean-all --clean
if "%~1"=="" (
    echo [INFO] No se especificaron argumentos. Ejecutando build completo con limpieza...
    %PYTHON_EXE% "%BUILD_SCRIPT%" --clean-all --clean
) else (
    echo [INFO] Ejecutando con argumentos: %*
    %PYTHON_EXE% "%BUILD_SCRIPT%" %*
)

set "EXIT_CODE=%errorlevel%"
if %EXIT_CODE% neq 0 (
    echo.
    echo ============================================================
    echo  ERROR: El build fallo con codigo %EXIT_CODE%
    echo ============================================================
    echo Revisa el log completo en build.log
    echo.
    pause
    exit /b %EXIT_CODE%
)

echo.
echo ============================================================
echo  COMPILACION COMPLETADA CON EXITO
echo ============================================================
echo Ejecutables e instaladores listos en la carpeta: dist/
echo.
exit /b 0
