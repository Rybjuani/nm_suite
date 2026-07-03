#!/usr/bin/env bash
# Genera capturas V8 baseline de superficies clave en subdirs individuales
set -e
cd "$(dirname "$0")/../.."
ROOT=qa/_captures_v8/iter_loop_2026_06_24_baseline
mkdir -p "$ROOT"

declare -a CAPS=(
  "suite home light"
  "suite home dark"
  "suite home-no-score light"
  "suite animo light"
  "suite animo dark"
  "suite registro-step1-emotion light"
  "suite registro-step1-emotion-otro light"
  "suite registro-step2-distortions light"
  "suite registro-step3-filled light"
  "suite respiracion light"
  "suite rutina light"
  "suite rutina-empty light"
  "suite rutina-all-completed light"
  "suite rutina-add-task light"
  "suite avisos light"
  "suite avisos-empty light"
  "suite timer light"
  "suite timer-empty light"
  "suite timer-running light"
  "suite timer-paused light"
  "suite dbt-now light"
  "suite dbt-library light"
  "suite dbt-practice-stop light"
  "suite actividades light"
  "suite actividades-empty light"
  "suite actividades-filtered light"
  "suite onboarding light"
  "suite onboarding-error light"
  "suite recuperar-acceso light"
  "suite registro-success light"
  "suite registro light"
  "hub pacientes light"
  "hub pacientes-empty light"
  "hub detalle light"
  "hub detalle-plan-activacion light"
  "hub detalle-plan-rutina light"
  "hub detalle-plan-timer light"
  "hub detalle-resumen-ia light"
  "hub textos-globales light"
)

for spec in "${CAPS[@]}"; do
  read -r app view theme <<< "$spec"
  out="$ROOT/${app}-${view}-${theme}"
  mkdir -p "$out"
  echo "→ $app/$view/$theme"
  .venv/Scripts/python.exe qa/capture_v8.py --app "$app" --view "$view" --theme "$theme" --out "$out" >/dev/null 2>&1 || echo "  FAIL: $app/$view/$theme"
done

echo "DONE. Total dirs: $(ls -d $ROOT/*/ 2>/dev/null | wc -l)"
