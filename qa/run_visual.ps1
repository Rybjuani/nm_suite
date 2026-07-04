# run_visual.ps1 — ÚNICO runner oficial de validación visual pre-cierre.
#
# Modos (exactamente uno):
#   -Key "<app>:<view>@<theme>"   1 key
#   -PlanFile <csv>               N keys (filas app,view,theme,key de target_scope.py --plan)
#   -All                          regresión completa (capture_v8 --all --clean + compare full)
#
# Cada modo corre: anti-fraud (--mode all) → captura (con back-screen para
# modales) → VAS gate POR KEY → compare batcheado → modal audit por key modal.
# El cierre oficial sigue siendo qa/close_visual_key.py (worktree aislado);
# este runner es el ciclo de reparación/validación, no evidencia de cierre.

param(
  [string]$Key = "",
  [string]$PlanFile = "",
  [switch]$All,
  [string]$OutDir = "",
  [switch]$SkipCapture
)

$ErrorActionPreference = "Stop"
$Python = ".\.venv\Scripts\python.exe"

$modes = @()
if (-not [string]::IsNullOrWhiteSpace($Key)) { $modes += "Key" }
if (-not [string]::IsNullOrWhiteSpace($PlanFile)) { $modes += "PlanFile" }
if ($All) { $modes += "All" }
if ($modes.Count -ne 1) {
  throw "Usar exactamente uno de: -Key <key> | -PlanFile <csv> | -All (recibido: $($modes -join ', '))"
}

if ([string]::IsNullOrWhiteSpace($OutDir)) {
  $OutDir = if ($All) { "reports\qa\layered_visual_compare_fresh" } else { "reports\qa\run_visual" }
}

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

# Anti-fraud gate (runtime + qa-harness): si falla, NINGÚN reporte de esta
# corrida es evidencia válida aunque el comparador dé PASS.
& $Python qa\anti_fraud_scan.py --mode all
if ($LASTEXITCODE -ne 0) {
  Write-Error "ANTI-FRAUD SCAN FAILED. Report is NOT valid closure evidence. Fix canonical/reference artifact usage before validating."
  exit 1
}

# VAS: introspección obligatoria en toda captura de validación.
$env:NM_VAS_INTROSPECT = "1"

# VAS: sidecar fresco sólo si vamos a capturar. Con -SkipCapture NO se borra:
# no habría captura que lo regenere y el gate por key fallaría espurio.
if (-not $SkipCapture) {
  Remove-Item .\qa\_visual_auditor_spec\introspection.json -ErrorAction SilentlyContinue
}

New-Item -ItemType Directory -Force $OutDir | Out-Null

if ($All) {
  Write-Host "[FULL REGRESSION] capture_v8 --all --clean. Reservado para cambio transversal o regresión final."
  if (-not $SkipCapture) {
    & $Python qa\capture_v8.py --all --clean --out-dir qa\_captures_v8
    if ($LASTEXITCODE -ne 0) {
      Write-Error "CAPTURE FAILED (exit $LASTEXITCODE)."
      exit 1
    }
  }

  & $Python qa\layered_visual_compare.py `
    --canonical qa\_mockup_canonical `
    --actual qa\_captures_v8 `
    --out-dir $OutDir
  $compareExit = $LASTEXITCODE

  # El run --all escribe TODAS las keys en el sidecar en una sola invocación
  # padre; acá (y sólo acá) el gate VAS sin filtro cubre el set completo.
  & $Python qa\vas_gate.py
  if ($LASTEXITCODE -ne 0) {
    Write-Error "VAS GATE FAILED for the full capture set. QA NOT approved."
    exit 1
  }

  & $Python tools\qa\audit_modal_backdrop_blur.py --all --out-dir (Join-Path $OutDir "modal_backdrop_blur")
  if ($LASTEXITCODE -ne 0) {
    Write-Error "MODAL BACKDROP/BLUR AUDIT FAILED in full regression."
    exit 1
  }

  if ($compareExit -ne 0) {
    Write-Error "LAYERED VISUAL COMPARE reported divergences (exit $compareExit). Ver $OutDir."
    exit 1
  }
  exit 0
}

# ── Modo por keys (1 key o plan multi-key) ───────────────────────────────────

$rows = @()
if (-not [string]::IsNullOrWhiteSpace($Key)) {
  if ($Key -notmatch '^(suite|hub):(.+)@(light|dark)$') {
    throw "Key inválida: $Key (esperado <app>:<view>@<theme>)"
  }
  $rows += [PSCustomObject]@{
    App = $Matches[1]
    View = $Matches[2]
    Theme = $Matches[3]
    Key = $Key
  }
}
else {
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
}

# capture_v8 REESCRIBE el sidecar por invocación (una key por proceso): el gate
# VAS corre POR KEY inmediatamente después de su captura, y el sidecar/manifest
# de cada key se archiva en $OutDir para que §2.3 pueda auditarse por key.
$introspectionArchiveDir = Join-Path $OutDir "introspection"
New-Item -ItemType Directory -Force $introspectionArchiveDir | Out-Null
$manifestArchiveDir = Join-Path $OutDir "manifests"
New-Item -ItemType Directory -Force $manifestArchiveDir | Out-Null

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
        & $Python qa\capture_v8.py `
          --app $($backScreenTarget.App) `
          --view $($backScreenTarget.View) `
          --theme $($backScreenTarget.Theme) `
          --out-dir qa\_captures_v8 `
          --no-clean
        $capturedKeys[$backScreenTarget.Key] = $true
      }
    }

    & $Python qa\capture_v8.py `
      --app $($row.App) `
      --view $($row.View) `
      --theme $($row.Theme) `
      --out-dir qa\_captures_v8 `
      --no-clean
  }

  # VAS Gate por key: el sidecar recién escrito corresponde a ESTA key; un
  # gate único al final sólo validaría la última key del set.
  $safeRowKey = ([string]$row.Key) -replace '[:@\\\/]', '_'
  $archivedSidecar = Join-Path $introspectionArchiveDir "$safeRowKey.json"
  $archivedManifest = Join-Path $manifestArchiveDir "$safeRowKey.json"
  if (-not $SkipCapture) {
    & $Python qa\vas_gate.py --key $($row.Key)
    if ($LASTEXITCODE -ne 0) {
      Write-Error "VAS GATE FAILED for key '$($row.Key)'. QA NOT approved. Do not close this item."
      exit 1
    }
    Copy-Item .\qa\_visual_auditor_spec\introspection.json $archivedSidecar -Force
    Copy-Item .\qa\_captures_v8\CAPTURE_MANIFEST.json $archivedManifest -Force
  }
  else {
    # -SkipCapture: el gate corre contra el sidecar archivado de esa key (o el
    # vivo como último recurso). Sin evidencia propia, el gate falla.
    if (Test-Path -LiteralPath $archivedSidecar) {
      & $Python qa\vas_gate.py --sidecar $archivedSidecar --key $($row.Key)
    }
    else {
      & $Python qa\vas_gate.py --key $($row.Key)
    }
    if ($LASTEXITCODE -ne 0) {
      Write-Error "VAS GATE FAILED for key '$($row.Key)'. QA NOT approved. Do not close this item."
      exit 1
    }
  }
}

$keysFile = New-TemporaryFile
try {
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllLines(
    $keysFile,
    [string[]]($rows | ForEach-Object { $_.Key }),
    $utf8NoBom
  )

  & $Python qa\layered_visual_compare.py `
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
  $archivedManifest = Join-Path $manifestArchiveDir "$safeKey.json"
  $liveManifest = ".\qa\_captures_v8\CAPTURE_MANIFEST.json"
  $manifestBackup = $null
  if (Test-Path -LiteralPath $archivedManifest) {
    $manifestBackup = New-TemporaryFile
    Copy-Item $liveManifest $manifestBackup -Force
    Copy-Item $archivedManifest $liveManifest -Force
  }
  try {
    & $Python tools\qa\audit_modal_backdrop_blur.py --key $($modalRow.Key) --out-dir $modalAuditOut
    if ($LASTEXITCODE -ne 0) {
      Write-Error "MODAL BACKDROP/BLUR AUDIT FAILED for key '$($modalRow.Key)'. QA NOT approved. Do not close this modal from panel similarity alone."
      exit 1
    }
  }
  finally {
    if ($null -ne $manifestBackup) {
      Copy-Item $manifestBackup $liveManifest -Force
      Remove-Item -LiteralPath $manifestBackup -Force -ErrorAction SilentlyContinue
    }
  }
}
