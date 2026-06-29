$ErrorActionPreference = "Stop"

Write-Host "[FULL REGRESSION] Esto corre capture_v8 --all --clean. No usar para microfix."
Write-Host "[FULL REGRESSION] Reservado para regresion final o cambio transversal grande."

# Anti-fraud gate: runtime/product must not read/render/overlay canonical or
# reference artifacts. If this fails, the resulting report is NOT valid closure
# evidence even if the comparator reports PASS.
& .\.venv\Scripts\python.exe qa\anti_fraud_scan.py
if ($LASTEXITCODE -ne 0) {
  Write-Error "ANTI-FRAUD SCAN FAILED. Report is NOT valid closure evidence. Fix runtime/product references to canonical/reference artifacts before validating."
  exit 1
}

& .\.venv\Scripts\python.exe qa\capture_v8.py `
  --all `
  --clean `
  --out-dir qa\_captures_v8

& .\.venv\Scripts\python.exe qa\layered_visual_compare.py `
  --canonical qa\_mockup_canonical `
  --actual qa\_captures_v8 `
  --out-dir reports\qa\layered_visual_compare_fresh
