param(
  [string]$PlanFile = "",
  [string[]]$Key = @(),
  [string[]]$BaselineDir = @(),
  [string[]]$ModifiedDir = @(),
  [string[]]$ExpectedDeltaKey = @(),
  [string]$CanonicalDir = "qa\_mockup_canonical",
  [string]$ActualDir = "qa\_captures_v8",
  [string]$OutDir = "reports\qa\visual_scope_regression",
  [switch]$SkipCapture,
  [switch]$DiagnosticNoise,
  [string]$DiffBase = "",
  [string[]]$AllowPath = @()
)

$ErrorActionPreference = "Stop"
$Python = ".\.venv\Scripts\python.exe"

function Invoke-Checked {
  param(
    [Parameter(Mandatory=$true)][scriptblock]$Command,
    [Parameter(Mandatory=$true)][string]$Label
  )
  & $Command
  if ($LASTEXITCODE -ne 0) {
    Write-Error "$Label failed with exit code $LASTEXITCODE. This wrapper is advisory/no-regression evidence only; do not use a partial run as closure."
    exit $LASTEXITCODE
  }
}

function Convert-KeyToRow {
  param([Parameter(Mandatory=$true)][string]$VisualKey)
  if ($VisualKey -notmatch '^(suite|hub):(.+)@(light|dark)$') {
    throw "Invalid key format: $VisualKey"
  }
  return [PSCustomObject]@{
    App = $Matches[1]
    View = $Matches[2]
    Theme = $Matches[3]
    Key = $VisualKey
  }
}

function Read-PlanRows {
  param([Parameter(Mandatory=$true)][string]$Path)
  $rows = @()
  foreach ($line in Get-Content -LiteralPath $Path) {
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
  return $rows
}

function Get-CanonicalCaptureForKey {
  param([Parameter(Mandatory=$true)][string]$VisualKey)
  $manifestPath = Join-Path $CanonicalDir "MANIFEST.json"
  if (-not (Test-Path -LiteralPath $manifestPath)) {
    return $null
  }
  $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
  foreach ($capture in $manifest.captures) {
    $file = [string]$capture.file
    if ($file -match '^(suite|hub)-(.+)-(light|dark)-\d+x\d+(?:-scale\d+)?\.png$') {
      $candidate = "$($Matches[1]):$($Matches[2])@$($Matches[3])"
      if ($candidate -eq $VisualKey) {
        return $capture
      }
    }
  }
  return $null
}

function Test-ModalVisualKey {
  param($Capture)
  if ($null -eq $Capture) {
    return $false
  }
  if ($Capture.PSObject.Properties.Name -contains "is_modal" -and [bool]$Capture.is_modal) {
    return $true
  }
  return @("modal", "window_modal") -contains [string]$Capture.surface
}

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$rows = @()
if (-not [string]::IsNullOrWhiteSpace($PlanFile)) {
  $rows += Read-PlanRows -Path $PlanFile
}
foreach ($visualKey in $Key) {
  $rows += Convert-KeyToRow -VisualKey $visualKey
}

Invoke-Checked -Label "anti_fraud_scan" -Command {
  & $Python qa\anti_fraud_scan.py
}

$env:NM_VAS_INTROSPECT = "1"
Remove-Item .\qa\_visual_auditor_spec\introspection.json -ErrorAction SilentlyContinue

if (-not $SkipCapture) {
  foreach ($row in $rows) {
    Invoke-Checked -Label "capture_v8 $($row.Key)" -Command {
      & $Python qa\capture_v8.py `
        --app $($row.App) `
        --view $($row.View) `
        --theme $($row.Theme) `
        --out-dir $ActualDir `
        --no-clean
    }
  }
}

if ($BaselineDir.Count -gt 0 -or $ModifiedDir.Count -gt 0) {
  if ($BaselineDir.Count -lt 2 -or $ModifiedDir.Count -lt 1) {
    throw "runtime_noise_envelope requires at least two -BaselineDir values and one -ModifiedDir value."
  }
  $noiseArgs = @(
    "qa\runtime_noise_envelope.py",
    "--out-dir", (Join-Path $OutDir "runtime_noise_envelope"),
    "--mode", ($(if ($DiagnosticNoise) { "diagnostic" } else { "strict" }))
  )
  foreach ($dir in $BaselineDir) {
    $noiseArgs += @("--baseline-dir", $dir)
  }
  foreach ($dir in $ModifiedDir) {
    $noiseArgs += @("--modified-dir", $dir)
  }
  foreach ($expected in $ExpectedDeltaKey) {
    $noiseArgs += @("--expected-delta-key", $expected)
  }
  Invoke-Checked -Label "runtime_noise_envelope" -Command {
    & $Python @noiseArgs
  }
}

if ($rows.Count -gt 0) {
  $keysFile = New-TemporaryFile
  try {
    $keys = [string[]]($rows | ForEach-Object { $_.Key })
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllLines($keysFile.FullName, $keys, $utf8NoBom)
    Invoke-Checked -Label "layered_visual_compare filtered" -Command {
      & $Python qa\layered_visual_compare.py `
        --canonical $CanonicalDir `
        --actual $ActualDir `
        --out-dir (Join-Path $OutDir "layered_visual_compare") `
        --keys-file $keysFile
    }
  }
  finally {
    Remove-Item -LiteralPath $keysFile -Force -ErrorAction SilentlyContinue
  }

  foreach ($row in $rows) {
    $capture = Get-CanonicalCaptureForKey -VisualKey $row.Key
    if (Test-ModalVisualKey -Capture $capture) {
      $safeKey = ([string]$row.Key) -replace '[:@\\\/]', '_'
      Invoke-Checked -Label "modal_backdrop_blur $($row.Key)" -Command {
        & $Python tools\qa\audit_modal_backdrop_blur.py `
          --key $($row.Key) `
          --canonical $CanonicalDir `
          --actual $ActualDir `
          --out-dir (Join-Path (Join-Path $OutDir "modal_backdrop_blur") $safeKey)
      }
    }
  }

  Invoke-Checked -Label "vas_gate" -Command {
    & $Python qa\vas_gate.py
  }
}

if (-not [string]::IsNullOrWhiteSpace($DiffBase)) {
  if ($AllowPath.Count -eq 0) {
    throw "Diff confinement requested with -DiffBase but no -AllowPath entries."
  }
  $diffArgs = @(
    "tools\qa\audit_diff_confinement.py",
    "--base", $DiffBase,
    "--out-dir", (Join-Path $OutDir "diff_confinement")
  )
  foreach ($path in $AllowPath) {
    $diffArgs += @("--allow-path", $path)
  }
  Invoke-Checked -Label "diff_confinement" -Command {
    & $Python @diffArgs
  }
}

Write-Host "VISUAL SCOPE REGRESSION advisory wrapper completed. This is no-regression evidence only; exact-key closure still requires the official layered comparator flow."
