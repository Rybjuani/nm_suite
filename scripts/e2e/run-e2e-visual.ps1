$ErrorActionPreference = "Stop"

$Root = Resolve-Path "$PSScriptRoot\..\.."
Set-Location $Root

if (-not $env:QT_QPA_PLATFORM) {
    $env:QT_QPA_PLATFORM = "offscreen"
}
$env:NM_VISUAL_QA = "1"
$env:NM_TEST_FORCE_CLOSE = "1"

.\.venv\Scripts\python.exe -m pytest tests\e2e -m e2e_visual @args
