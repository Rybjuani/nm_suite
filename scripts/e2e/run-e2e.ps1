param(
    [switch]$Suite,
    [switch]$Hub,
    [switch]$Smoke,
    [switch]$Report
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Python = Join-Path $Root ".venv\Scripts\python.exe"

$Targets = @("tests\e2e")
if ($Suite) { $Targets = @("tests\e2e\suite") }
if ($Hub) { $Targets = @("tests\e2e\hub") }
if ($Smoke) { $Targets = @("tests\e2e\smoke") }

$Args = @("-m", "pytest") + $Targets + @("-q")
if ($Report) {
    New-Item -ItemType Directory -Force -Path (Join-Path $Root "reports\e2e") | Out-Null
    $Args += @("--junitxml", "reports\e2e\pytest-e2e.xml")
}

Push-Location $Root
try {
    & $Python @Args
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
