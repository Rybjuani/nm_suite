$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Python = Join-Path $Root ".venv\Scripts\python.exe"

Push-Location $Root
try {
    & $Python -m pytest tests\e2e\smoke -q
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
