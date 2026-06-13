@echo off
chcp 65001 >nul

cd /d "%~dp0"

set "PYTHON_CMD="

rem 1) Python Launcher (py -3)
py -3 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
    goto :run_build
)

rem 2) python en el PATH
python --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    goto :run_build
)

rem 3) Fallback: buscar python.exe en ubicaciones de instalacion conocidas.
rem    Necesario para que el doble-click desde el Explorador funcione aunque
rem    Python no este en el PATH que Windows le pasa al .bat. Se prueban las
rem    rutas tipicas del instalador per-usuario y per-maquina (3.13 -> 3.10).
for %%V in (313 312 311 310) do (
    if not defined PYTHON_CMD if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" set "PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe""
    if not defined PYTHON_CMD if exist "%PROGRAMFILES%\Python%%V\python.exe" set "PYTHON_CMD="%PROGRAMFILES%\Python%%V\python.exe""
)
if defined PYTHON_CMD goto :run_build

rem 4) Ultimo recurso: py sin version
py --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py"
    goto :run_build
)

echo [ERROR] No se encontro un interprete de Python valido ('py' o 'python'),
echo         ni en el PATH ni en las rutas de instalacion conocidas.
echo         Instala Python 3 desde https://www.python.org/ y reintenta.
pause
exit /b 1

:run_build
%PYTHON_CMD% build_neuromood.py %*
set "EXIT_CODE=%errorlevel%"

if %EXIT_CODE% neq 0 (
    echo.
    echo [ERROR] El proceso de build fallo con codigo de salida %EXIT_CODE%
    pause
)

exit /b %EXIT_CODE%
