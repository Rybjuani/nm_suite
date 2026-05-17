@echo off
setlocal
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

cd /d "%ROOT%"
title NeuroMood V3 - Build oficial

where py >nul 2>nul
if errorlevel 1 (
    python "%ROOT%\AI_SCRIPTS\build_neuromood.py" %*
) else (
    py -3 "%ROOT%\AI_SCRIPTS\build_neuromood.py" %*
)
if errorlevel 1 (
    echo.
    echo Build fallido. Revisa build.log.
    exit /b 1
)

echo.
echo Build finalizado correctamente.
exit /b 0
