@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo NeuroMood - Build rapido modo EXTERNAL
echo ==========================================
echo.

echo [1/5] Verificando sintaxis...
python -m compileall . || goto error

echo.
echo [2/5] Compilando Suite Paciente...
python build_neuromood.py --only "Suite Paciente" --installer-mode external || goto error

echo.
echo [3/5] Compilando NeuroMood Hub...
python build_neuromood.py --only "NeuroMood Hub" --installer-mode external || goto error

echo.
echo [4/5] Compilando desinstaladores...
python build_neuromood.py --only "Desinstalador Suite" --only "Desinstalador Hub" --installer-mode external || goto error

echo.
echo [5/5] Compilando instaladores external...
python build_neuromood.py --only "Instalador Suite" --only "Instalador Hub" --installer-mode external || goto error

echo.
echo Verificando payloads...
if not exist "dist\Instalador Suite\payload_suite.zip" goto error_payload_suite
if not exist "dist\Instalador Hub\payload_hub.zip" goto error_payload_hub

echo.
echo ==========================================
echo BUILD EXTERNAL COMPLETADO OK
echo ==========================================
echo.
echo Archivos importantes:
echo dist\Instalador Suite\Instalador Suite.exe
echo dist\Instalador Suite\payload_suite.zip
echo.
echo dist\Instalador Hub\Instalador Hub.exe
echo dist\Instalador Hub\payload_hub.zip
echo.
pause
exit /b 0

:error_payload_suite
echo.
echo ERROR: No se genero payload_suite.zip
pause
exit /b 1

:error_payload_hub
echo.
echo ERROR: No se genero payload_hub.zip
pause
exit /b 1

:error
echo.
echo ==========================================
echo ERROR EN BUILD
echo ==========================================
pause
exit /b 1