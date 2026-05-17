@echo off
setlocal
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

cd /d "%ROOT%"
title NeuroMood V3 - Build oficial limpio

set "BUILD_SCRIPT=%ROOT%\AI_SCRIPTS\build_neuromood.py"
if not exist "%BUILD_SCRIPT%" (
    if exist "%ROOT%\build_neuromood.py" (
        set "BUILD_SCRIPT=%ROOT%\build_neuromood.py"
    ) else (
        echo No se encontro build_neuromood.py ni en AI_SCRIPTS ni en la raiz del repo.
        exit /b 1
    )
)

set "LOG_FILE=%ROOT%\build.log"

echo ============================================================
echo  NeuroMood V3 - Build
echo ============================================================
echo Build script: %BUILD_SCRIPT%
echo Log file:     %LOG_FILE%
echo.

where py >nul 2>nul
if errorlevel 1 (
    python "%BUILD_SCRIPT%" --clean-all --clean %*
) else (
    py -3 "%BUILD_SCRIPT%" --clean-all --clean %*
)

if errorlevel 1 (
    echo.
    echo ============================================================
    echo  BUILD FALLIDO
    echo ============================================================
    echo Revisa el log completo en: %LOG_FILE%
    echo.
    if exist "%LOG_FILE%" (
        echo Ultimas lineas del log:
        echo ------------------------------------------------------------
        powershell -Command "Get-Content '%LOG_FILE%' -Tail 30"
        echo ------------------------------------------------------------
    )
    exit /b 1
)

echo.
echo ============================================================
echo  Build finalizado correctamente
echo ============================================================
echo Ejecutables en: %ROOT%\dist
echo Log completo:   %LOG_FILE%
echo.
dir "%ROOT%\dist" /b
exit /b 0
