param(
  [Parameter(Mandatory=$true)] [string]$PlanFile,
  [string]$OutDir = "reports\qa\layered_visual_compare_family",
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

# VAS: force introspection mode for every closure capture.
$env:NM_VAS_INTROSPECT = "1"

# VAS: remove stale sidecar before capturing so evidence is from THIS run only.
# Con -SkipCapture NO se borra: no habría captura que lo regenere y el gate
# por key de abajo debe correr contra el sidecar existente.
if (-not $SkipCapture) {
  Remove-Item .\qa\_visual_auditor_spec\introspection.json -ErrorAction SilentlyContinue
}

# capture_v8 REESCRIBE el sidecar en cada invocación (una key por proceso),
# así que el gate VAS corre por key inmediatamente después de su captura y el
# sidecar se archiva por key en $OutDir\introspection\ — el introspection.json
# vivo sólo retiene la última key del set.
$introspectionArchiveDir = Join-Path $OutDir "introspection"
New-Item -ItemType Directory -Force $introspectionArchiveDir | Out-Null

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

$modalRows = @()
$capturedKeys = @{}
foreach ($row in $rows) {
  $canonicalCapture = Get-CanonicalCaptureForKey -VisualKey $row.Key
  $isModalKey = Test-ModalVisualKey -Capture $canonicalCapture
  if ($isModalKey) {
    $modalRows += [PSCustomObject]@{
      Key = $row.Key
      Capture = $canonicalCapture
    }
  }

  if (-not $SkipCapture) {
    if ($isModalKey) {
      $backScreenTarget = Get-BackScreenTarget -Capture $canonicalCapture
      if ($null -ne $backScreenTarget -and -not $capturedKeys.ContainsKey($backScreenTarget.Key)) {
        & .\.venv\Scripts\python.exe qa\capture_v8.py `
          --app $($backScreenTarget.App) `
          --view $($backScreenTarget.View) `
          --theme $($backScreenTarget.Theme) `
          --out-dir qa\_captures_v8 `
          --no-clean
        $capturedKeys[$backScreenTarget.Key] = $true
      }
    }

    & .\.venv\Scripts\python.exe qa\capture_v8.py `
      --app $($row.App) `
      --view $($row.View) `
      --theme $($row.Theme) `
      --out-dir qa\_captures_v8 `
      --no-clean
  }

  # VAS Gate por key: el sidecar recién escrito corresponde a ESTA key; si se
  # gateara una sola vez al final, sólo la última key del set quedaría
  # validada (bug observado 2026-07-03 con un set de 2 keys: "all 1 entries").
  $safeRowKey = ([string]$row.Key) -replace '[:@\\\/]', '_'
  $archivedSidecar = Join-Path $introspectionArchiveDir "$safeRowKey.json"
  if (-not $SkipCapture) {
    & .\.venv\Scripts\python.exe qa\vas_gate.py --key $($row.Key)
    if ($LASTEXITCODE -ne 0) {
      Write-Error "VAS GATE FAILED for key '$($row.Key)'. QA NOT approved. Do not close this item."
      exit 1
    }
    Copy-Item .\qa\_visual_auditor_spec\introspection.json $archivedSidecar -Force
  }
  else {
    # -SkipCapture: sin captura fresca, el gate corre contra el sidecar
    # archivado de esa key (o el vivo como último recurso). Si ninguno cubre
    # la key, el gate falla — no hay aprobación VAS sin evidencia propia.
    if (Test-Path -LiteralPath $archivedSidecar) {
      & .\.venv\Scripts\python.exe qa\vas_gate.py --sidecar $archivedSidecar --key $($row.Key)
    }
    else {
      & .\.venv\Scripts\python.exe qa\vas_gate.py --key $($row.Key)
    }
    if ($LASTEXITCODE -ne 0) {
      Write-Error "VAS GATE FAILED for key '$($row.Key)'. QA NOT approved. Do not close this item."
      exit 1
    }
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
  if ($LASTEXITCODE -ne 0) {
    Write-Error "LAYERED VISUAL COMPARE FAILED (exit $LASTEXITCODE). Check report for divergences."
    exit 1
  }
}
finally {
  Remove-Item -LiteralPath $keysFile -Force -ErrorAction SilentlyContinue
}

foreach ($modalRow in $modalRows) {
  $safeKey = ([string]$modalRow.Key) -replace '[:@\\\/]', '_'
  $modalAuditOut = Join-Path (Join-Path $OutDir "modal_backdrop_blur") $safeKey
  & .\.venv\Scripts\python.exe tools\qa\audit_modal_backdrop_blur.py --key $($modalRow.Key) --out-dir $modalAuditOut
  if ($LASTEXITCODE -ne 0) {
    Write-Error "MODAL BACKDROP/BLUR AUDIT FAILED for key '$($modalRow.Key)'. QA NOT approved. Do not close this modal from panel similarity alone."
    exit 1
  }
}

# VAS Gate: ya corrió POR KEY dentro del loop de capturas (el sidecar vivo se
# reescribe por invocación de capture_v8; un gate único al final sólo cubría
# la última key del set). Los sidecars por key quedan archivados en
# $OutDir\introspection\<key_safe>.json.
