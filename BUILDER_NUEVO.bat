@echo off
setlocal
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

cd /d "%ROOT%"
echo ============================================================
echo [AVISO] BUILDER_NUEVO.bat esta DEPRECADO
echo ============================================================
echo Este script ha sido reemplazado por la build tool canonical:
echo BUILD_NEUROMOOD.bat
echo.
echo Redirigiendo la ejecucion...
echo ============================================================
echo.

if exist "%ROOT%\BUILD_NEUROMOOD.bat" (
    call "%ROOT%\BUILD_NEUROMOOD.bat" %*
) else (
    echo [ERROR] No se encontro BUILD_NEUROMOOD.bat
    pause
    exit /b 1
)