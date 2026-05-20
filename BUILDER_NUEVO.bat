@echo off
setlocal
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

cd /d "%ROOT%"

echo ============================================================
echo  AVISO: BUILDER_NUEVO.bat esta DEPRECADO
echo ============================================================
echo Este script de build ha sido deprecado en favor de:
echo BUILD_NEUROMOOD.bat
echo.
echo Redireccionando en 3 segundos...
echo.
timeout /t 3 >nul 2>nul

if exist "%ROOT%\BUILD_NEUROMOOD.bat" (
    call "%ROOT%\BUILD_NEUROMOOD.bat" %*
) else (
    echo [ERROR] No se encontro BUILD_NEUROMOOD.bat en: %ROOT%
    pause
    exit /b 1
)