@echo off
setlocal EnableDelayedExpansion
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo ============================================================
echo  NeuroMood - Compilar Instalador Paciente
echo  neuromood.com.ar
echo ============================================================
echo.

cd /d "%ROOT%"

:: Verificar que NeuroMood.exe existe en dist\
if not exist "%ROOT%\dist\NeuroMood.exe" (
    echo  FALTA: dist\NeuroMood.exe
    echo  Ejecuta BUILD_ALL.bat primero para compilar la app.
    pause
    exit /b 1
)

echo  [1/3] Compilando desinstalador paciente...
pyinstaller --noconfirm "%ROOT%\uninstaller.spec" --distpath "%ROOT%\dist" --workpath "%ROOT%\build"
if %ERRORLEVEL% NEQ 0 goto :error
echo  Desinstalador listo: dist\Desinstalar NeuroMood.exe
echo.

echo  [2/3] Compilando instalador paciente...
pyinstaller --noconfirm "%ROOT%\installer.spec" --distpath "%ROOT%\dist" --workpath "%ROOT%\build"
if %ERRORLEVEL% NEQ 0 goto :error
echo  Instalador listo.
echo.

echo  [3/3] Limpiando temporales...
if exist "%ROOT%\build\Desinstalar NeuroMood" rmdir /s /q "%ROOT%\build\Desinstalar NeuroMood"
if exist "%ROOT%\build\Instalar NeuroMood"     rmdir /s /q "%ROOT%\build\Instalar NeuroMood"
del /q "%ROOT%\*.spec.bak" 2>nul

echo.
echo ============================================================
echo  LISTO
echo.
echo  Instalador:    dist\Instalar NeuroMood.exe
echo  Desinstalador: dist\Desinstalar NeuroMood.exe
echo.
echo  Distribuye solo: dist\Instalar NeuroMood.exe
echo  (el desinstalador va incluido dentro del instalador)
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
