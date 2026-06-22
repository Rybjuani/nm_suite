@echo off
chcp 65001 >nul

cd /d "%~dp0"

set "PYTHON_CMD="

rem 1) Preferir el venv del proyecto (.venv\Scripts\python.exe).
rem    Es el interprete canonico del repo: tiene PyInstaller y el resto de
rem    dependencias pinneadas. Si existe, se usa SIEMPRE antes que cualquier
rem    Python global del sistema.
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_CMD=.\.venv\Scripts\python.exe"
    goto :check_pyinstaller
)

rem 2) Python Launcher (py -3)
py -3 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
    goto :check_pyinstaller
)

rem 3) python en el PATH
python --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    goto :check_pyinstaller
)

rem 4) Fallback: buscar python.exe en ubicaciones de instalacion conocidas.
rem    Necesario para que el doble-click desde el Explorador funcione aunque
rem    Python no este en el PATH que Windows le pasa al .bat. Se prueban las
rem    rutas tipicas del instalador per-usuario y per-maquina (3.13 -> 3.10).
for %%V in (313 312 311 310) do (
    if not defined PYTHON_CMD if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" set "PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe""
    if not defined PYTHON_CMD if exist "%PROGRAMFILES%\Python%%V\python.exe" set "PYTHON_CMD="%PROGRAMFILES%\Python%%V\python.exe""
)
if defined PYTHON_CMD goto :check_pyinstaller

rem 5) Ultimo recurso: py sin version
py --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py"
    goto :check_pyinstaller
)

echo [ERROR] No se encontro un interprete de Python valido ('py' o 'python'),
echo         ni en el PATH ni en las rutas de instalacion conocidas.
echo         Se recomienda crear el venv del proyecto:
echo           py -3 -m venv .venv
echo           .\.venv\Scripts\python.exe -m pip install -r requirements.txt
echo         o instala Python 3 desde https://www.python.org/ y reintenta.
pause
exit /b 1

:check_pyinstaller
rem El build requiere PyInstaller en el interprete seleccionado. Si falta,
rem fallar aqui con un mensaje claro en vez de dejar que PyInstaller emita
rem un error "No module named PyInstaller" mas criptico mas adelante.
%PYTHON_CMD% -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller no esta instalado en el interprete seleccionado:
    echo           %PYTHON_CMD%
    echo         El build requiere PyInstaller. Instalalo en ese interprete:
    echo           %PYTHON_CMD% -m pip install pyinstaller
    echo         Recomendado: usar el venv del proyecto .venv con todas las
    echo         dependencias pinneadas, ver requirements.txt.
    pause
    exit /b 1
)

:run_build
%PYTHON_CMD% build_neuromood.py %*
set "EXIT_CODE=%errorlevel%"

if %EXIT_CODE% neq 0 (
    echo.
    echo [ERROR] El proceso de build fallo con codigo de salida %EXIT_CODE%
    pause
)

exit /b %EXIT_CODE%
