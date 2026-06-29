param(
  [Parameter(Mandatory=$true)] [string]$PlanFile,
  [string]$OutDir = "reports\qa\layered_visual_compare_family",
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

$rows = @()
foreach ($line in Get-Content -LiteralPath $PlanFile) {
  $trimmed = $line.Trim()
  if ([string]::IsNullOrWhiteSpace($trimmed) -or $trimmed.StartsWith("#")) {
    continue
  }
  $parts = $trimmed.Split(",")
  if ($parts.Count -lt 4) {
    continue
  }
  $rows += [PSCustomObject]@{
    App = $parts[0].Trim()
    View = $parts[1].Trim()
    Theme = $parts[2].Trim()
    Key = $parts[3].Trim()
  }
}

if ($rows.Count -eq 0) {
  throw "PlanFile has no valid rows: $PlanFile"
}

foreach ($row in $rows) {
  if (-not $SkipCapture) {
    & .\.venv\Scripts\python.exe qa\capture_v8.py `
      --app $($row.App) `
      --view $($row.View) `
      --theme $($row.Theme) `
      --out-dir qa\_captures_v8 `
      --no-clean
  }
}

$keysFile = New-TemporaryFile
try {
  $rows | ForEach-Object { $_.Key } | Set-Content -LiteralPath $keysFile -Encoding UTF8

  & .\.venv\Scripts\python.exe qa\layered_visual_compare.py `
    --canonical qa\_mockup_canonical `
    --actual qa\_captures_v8 `
    --out-dir $OutDir `
    --keys-file $keysFile
}
finally {
  Remove-Item -LiteralPath $keysFile -Force -ErrorAction SilentlyContinue
}
