<#
.SYNOPSIS
    Runner PowerShell nativo para el validador Fase 0B de VisualParity V3.1.

.DESCRIPTION
    Localiza el repo root desde su propia ruta, busca Python en este orden:
      1. .\.venv\Scripts\python.exe
      2. python
      3. py -3
    Ejecuta tools\visualparity\phase0b\validate_phase0b.py y propaga el exit code.

    No invoca V1/V2. No invoca capture_v8.py. No toca archivos.
    No tiene runtime authority. No cierra keys.

.NOTES
    Fase 0C - Governance smoke only. No runtime authority. No visual closure.
    Compatible con Windows PowerShell nativo (no Git Bash, no WSL).
#>

# --- Locate repo root from this script's path ------------------------------
# This script lives at <repo-root>\tools\visualparity\phase0b\run_phase0b.ps1
$ScriptPath = $MyInvocation.MyCommand.Path
$ScriptDir = Split-Path -Parent $ScriptPath
# repo root = 3 levels up from phase0b/
$RepoRoot = (Get-Item $ScriptDir).Parent.Parent.Parent.FullName

Write-Host "=== Fase 0B Governance Runner (PowerShell) ===" -ForegroundColor Cyan
Write-Host "Repo root: $RepoRoot"
Write-Host ""

# --- Locate Python ----------------------------------------------------------
$PythonExe = $null
$PythonSource = $null

# 1. venv
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $PythonExe = $VenvPython
    $PythonSource = ".venv\Scripts\python.exe"
}

# 2. python on PATH
if (-not $PythonExe) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) {
        $PythonExe = "python"
        $PythonSource = "python (PATH)"
    }
}

# 3. py -3 launcher
if (-not $PythonExe) {
    $cmd = Get-Command py -ErrorAction SilentlyContinue
    if ($cmd) {
        $PythonExe = "py"
        $PythonArgs = @("-3")
        $PythonSource = "py -3 (launcher)"
    }
}

if (-not $PythonExe) {
    Write-Host "ERROR: Python not found." -ForegroundColor Red
    Write-Host "  Tried:" -ForegroundColor Red
    Write-Host "    1. $VenvPython" -ForegroundColor Red
    Write-Host "    2. python (on PATH)" -ForegroundColor Red
    Write-Host "    3. py -3 (launcher)" -ForegroundColor Red
    Write-Host "  Install Python 3.9+ or create a venv at .\.venv\" -ForegroundColor Red
    exit 2
}

Write-Host "Python: $PythonExe ($PythonSource)"

# Show Python version for traceability
if ($PythonArgs) {
    & $PythonExe @PythonArgs --version 2>&1 | ForEach-Object { Write-Host "Python version: $_" }
} else {
    & $PythonExe --version 2>&1 | ForEach-Object { Write-Host "Python version: $_" }
}
Write-Host ""

# --- Run validator ----------------------------------------------------------
$ValidatorPath = Join-Path $RepoRoot "tools\visualparity\phase0b\validate_phase0b.py"
if (-not (Test-Path $ValidatorPath)) {
    Write-Host "ERROR: validator not found: $ValidatorPath" -ForegroundColor Red
    exit 2
}

$CmdDisplay = if ($PythonArgs) {
    "$PythonExe $($PythonArgs -join ' ') `"$ValidatorPath`""
} else {
    "$PythonExe `"$ValidatorPath`""
}
Write-Host "Command: $CmdDisplay"
Write-Host ""

if ($PythonArgs) {
    & $PythonExe @PythonArgs $ValidatorPath
} else {
    & $PythonExe $ValidatorPath
}

$ExitCode = $LASTEXITCODE

Write-Host ""
Write-Host "=== Runner result ===" -ForegroundColor Cyan
Write-Host "Exit code: $ExitCode"
if ($ExitCode -eq 0) {
    Write-Host "Status: PASS (validator returned 0)" -ForegroundColor Green
} else {
    Write-Host "Status: FAIL (validator returned $ExitCode)" -ForegroundColor Red
}

exit $ExitCode
