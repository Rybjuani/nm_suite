$ErrorActionPreference = "Stop"

Write-Host "[FULL REGRESSION] Esto corre capture_v8 --all --clean. No usar para microfix."
Write-Host "[FULL REGRESSION] Reservado para regresion final o cambio transversal grande."

& .\.venv\Scripts\python.exe qa\capture_v8.py `
  --all `
  --clean `
  --out-dir qa\_captures_v8

& .\.venv\Scripts\python.exe qa\layered_visual_compare.py `
  --canonical qa\_mockup_canonical `
  --actual qa\_captures_v8 `
  --out-dir reports\qa\layered_visual_compare_fresh
