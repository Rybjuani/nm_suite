param(
  [Parameter(Mandatory=$true)][ValidateSet("suite","hub")] [string]$App,
  [Parameter(Mandatory=$true)] [string]$View,
  [Parameter(Mandatory=$true)][ValidateSet("light","dark")] [string]$Theme,
  [string]$Key = "",
  [string]$OutDir = "reports\qa\layered_visual_compare_item",
  [switch]$RuntimeProbe,
  [switch]$SkipCapture
)

$ErrorActionPreference = "Stop"

# Anti-fraud gate: runtime/product must not read/render/overlay canonical or
# reference artifacts. If this fails, the resulting report is NOT valid closure
# evidence even if the comparator reports PASS.
& .\.venv\Scripts\python.exe qa\anti_fraud_scan.py
if ($LASTEXITCODE -ne 0) {
  Write-Error "ANTI-FRAUD SCAN FAILED. Report is NOT valid closure evidence. Fix runtime/product references to canonical/reference artifacts before validating."
  exit 1
}

if ([string]::IsNullOrWhiteSpace($Key)) {
  $Key = "${App}:${View}@${Theme}"
}

if (-not $SkipCapture) {
  & .\.venv\Scripts\python.exe qa\capture_v8.py `
    --app $App `
    --view $View `
    --theme $Theme `
    --out-dir qa\_captures_v8 `
    --no-clean
}

& .\.venv\Scripts\python.exe qa\layered_visual_compare.py `
  --canonical qa\_mockup_canonical `
  --actual qa\_captures_v8 `
  --out-dir $OutDir `
  --key $Key

if ($RuntimeProbe) {
  & .\.venv\Scripts\python.exe qa\runtime_live_probe.py `
    --app $App `
    --view $View `
    --theme $Theme `
    --mode offscreen
}
