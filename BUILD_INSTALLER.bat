@echo off
setlocal EnableDelayedExpansion
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo ============================================================
echo  NeuroMood Suite - Compilar Instalador Paciente
echo  neuromood.com.ar
echo ============================================================
echo.

cd /d "%ROOT%"

:: Verificar que las 6 apps paciente existen en dist\
set APPS_OK=1
for %%A in (
    "TermometroEmocional.exe"
    "RecordatoriosBienestar.exe"
    "TemporizadorActividades.exe"
    "RegistroPensamientos.exe"
    "GuiaRespiracion.exe"
    "ChecklistRutina.exe"
) do (
    if not exist "%ROOT%\dist\%%~A" (
        echo  FALTA: dist\%%~A
        set APPS_OK=0
    )
)

if "%APPS_OK%"=="0" (
    echo.
    echo  Ejecuta BUILD_ALL.bat primero para compilar todas las apps.
    pause
    exit /b 1
)

echo  [1/3] Compilando desinstalador paciente...
pyinstaller --noconfirm "%ROOT%\uninstaller.spec" --distpath "%ROOT%\dist" --workpath "%ROOT%\build"
if %ERRORLEVEL% NEQ 0 goto :error

echo.
echo  Desinstalador listo: dist\Desinstalar NeuroMood.exe

echo.
echo  [2/3] Compilando instalador paciente (incluye las 6 apps)...
pyinstaller --noconfirm "%ROOT%\installer.spec" --distpath "%ROOT%\dist" --workpath "%ROOT%\build"
if %ERRORLEVEL% NEQ 0 goto :error

echo.
echo  [3/3] Limpiando archivos temporales...
if exist "%ROOT%\build\Desinstalar NeuroMood" rmdir /s /q "%ROOT%\build\Desinstalar NeuroMood"
if exist "%ROOT%\build\Instalar NeuroMood Suite" rmdir /s /q "%ROOT%\build\Instalar NeuroMood Suite"
del /q "%ROOT%\*.spec.bak" 2>nul

echo.
echo ============================================================
echo  LISTO
echo.
echo  Instalador:    dist\Instalar NeuroMood Suite.exe
echo  Desinstalador: dist\Desinstalar NeuroMood.exe
echo.
echo  Distribuye solo: dist\Instalar NeuroMood Suite.exe
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
