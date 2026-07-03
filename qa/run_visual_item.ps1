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

function Get-CanonicalCaptureForKey {
  param([Parameter(Mandatory=$true)][string]$VisualKey)

  $manifestPath = "qa\_mockup_canonical\MANIFEST.json"
  if (-not (Test-Path -LiteralPath $manifestPath)) {
    return $null
  }
  $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
  foreach ($capture in $manifest.captures) {
    $file = [string]$capture.file
    if ($file -match '^(suite|hub)-(.+)-(light|dark)-\d+x\d+(?:-scale\d+)?\.png$') {
      $key = "$($Matches[1]):$($Matches[2])@$($Matches[3])"
      if ($key -eq $VisualKey) {
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
  $surface = [string]$Capture.surface
  return @("modal", "window_modal") -contains $surface
}

function Get-BackScreenTarget {
  param($Capture)
  if ($null -eq $Capture) {
    return $null
  }
  $backKey = [string]$Capture.back_screen_key
  if ([string]::IsNullOrWhiteSpace($backKey)) {
    return $null
  }
  if ($backKey -notmatch '^(suite|hub):(.+)@(light|dark)$') {
    return $null
  }
  return [PSCustomObject]@{
    App = $Matches[1]
    View = $Matches[2]
    Theme = $Matches[3]
    Key = $backKey
  }
}

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

$canonicalCapture = Get-CanonicalCaptureForKey -VisualKey $Key
$isModalKey = Test-ModalVisualKey -Capture $canonicalCapture
$backScreenTarget = Get-BackScreenTarget -Capture $canonicalCapture

# VAS: force introspection mode for every closure capture.
$env:NM_VAS_INTROSPECT = "1"

# VAS: remove stale sidecar before capturing so evidence is from THIS run only.
# Con -SkipCapture NO se borra: no habría captura que lo regenere y el gate
# `vas_gate.py --key` del final quedaría sin sidecar (fallo espurio).
if (-not $SkipCapture) {
  Remove-Item .\qa\_visual_auditor_spec\introspection.json -ErrorAction SilentlyContinue
}

if (-not $SkipCapture) {
  if ($isModalKey -and $null -ne $backScreenTarget) {
    & .\.venv\Scripts\python.exe qa\capture_v8.py `
      --app $($backScreenTarget.App) `
      --view $($backScreenTarget.View) `
      --theme $($backScreenTarget.Theme) `
      --out-dir qa\_captures_v8 `
      --no-clean
  }

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
if ($LASTEXITCODE -ne 0) {
  Write-Error "LAYERED VISUAL COMPARE FAILED (exit $LASTEXITCODE). Check report for divergences."
  exit 1
}

if ($isModalKey) {
  $modalAuditOut = Join-Path $OutDir "modal_backdrop_blur"
  & .\.venv\Scripts\python.exe tools\qa\audit_modal_backdrop_blur.py --key $Key --out-dir $modalAuditOut
  if ($LASTEXITCODE -ne 0) {
    Write-Error "MODAL BACKDROP/BLUR AUDIT FAILED for key '$Key'. QA NOT approved. Do not close this modal from panel similarity alone."
    exit 1
  }
}

# VAS Gate: validate the sidecar for this exact key. Non-zero exit = QA not approved.
& .\.venv\Scripts\python.exe qa\vas_gate.py --key $Key
if ($LASTEXITCODE -ne 0) {
  Write-Error "VAS GATE FAILED for key '$Key'. QA NOT approved. Do not close this item."
  exit 1
}

if ($RuntimeProbe) {
  & .\.venv\Scripts\python.exe qa\runtime_live_probe.py `
    --app $App `
    --view $View `
    --theme $Theme `
    --mode offscreen
}
