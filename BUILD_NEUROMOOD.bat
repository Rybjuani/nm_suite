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

where py >nul 2>nul
if errorlevel 1 (
    python "%BUILD_SCRIPT%" --clean-all --clean %*
) else (
    py -3 "%BUILD_SCRIPT%" --clean-all --clean %*
)
if errorlevel 1 (
    echo.
    echo Build fallido. Revisa build.log.
    exit /b 1
)

echo.
echo Build finalizado correctamente.
echo Ejecutables nuevos en: %ROOT%\dist
exit /b 0
