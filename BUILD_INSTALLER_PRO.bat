@echo off
setlocal EnableDelayedExpansion
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo ============================================================
echo  NeuroMood Suite - Compilar Instalador Hub Profesional
echo  neuromood.com.ar
echo ============================================================
echo.

cd /d "%ROOT%"

:: Verificar que el Hub existe en dist\pro\
if not exist "%ROOT%\dist\pro\HubProfesional.exe" (
    echo  FALTA: dist\pro\HubProfesional.exe
    echo.
    echo  Ejecuta BUILD_ALL.bat primero para compilar el Hub.
    pause
    exit /b 1
)

echo  [1/3] Compilando desinstalador del Hub Profesional...
pyinstaller --noconfirm "%ROOT%\uninstaller_pro.spec" --distpath "%ROOT%\dist\pro" --workpath "%ROOT%\build"
if %ERRORLEVEL% NEQ 0 goto :error

echo.
echo  Desinstalador listo: dist\pro\Desinstalar NeuroMood Pro.exe

echo.
echo  [2/3] Compilando instalador del Hub Profesional...
pyinstaller --noconfirm "%ROOT%\installer_pro.spec" --distpath "%ROOT%\dist" --workpath "%ROOT%\build"
if %ERRORLEVEL% NEQ 0 goto :error

echo.
echo  [3/3] Limpiando archivos temporales...
if exist "%ROOT%\build\Desinstalar NeuroMood Pro" rmdir /s /q "%ROOT%\build\Desinstalar NeuroMood Pro"
if exist "%ROOT%\build\Instalar NeuroMood Hub Profesional" rmdir /s /q "%ROOT%\build\Instalar NeuroMood Hub Profesional"
del /q "%ROOT%\*.spec.bak" 2>nul

echo.
echo ============================================================
echo  LISTO
echo.
echo  Instalador Pro: dist\Instalar NeuroMood Hub Profesional.exe
echo.
echo  Distribuye solo ese archivo al profesional.
echo  Incluye internamente:
echo    - HubProfesional.exe
echo    - Desinstalar NeuroMood Pro.exe
echo ============================================================
echo.
pause
goto :end

:error
echo.
echo ============================================================
echo  ERROR - La compilacion fallo.
echo ============================================================
echo.
pause

:end
