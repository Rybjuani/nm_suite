# Layered visual comparison report

Generated: 2026-06-28T13:09:44

Handoff policy:
- Authority: LAYERED_VISUAL_COMPARE
- Use qa/_mockup_canonical plus a fresh complete qa/_captures_v8 run for operational handoff decisions. Zip inputs are archive/forensics only and must not close VISUAL_REPAIR_HANDOFF.md items.
- Canonical source: `qa\_mockup_canonical`
- Actual source: `qa\_captures_tmp5`
- HANDOFF_CLOSURE_ALLOWED: NO

Thresholds:
- raw SSIM >= 0.92
- raw mean_abs_diff <= 0.035
- raw changed_pixel_ratio <= 0.08
- odiff diff_percentage <= 8
- content bbox shift <= 18px

Summary:
- Total: 86
- Pass: 0
- Real divergences/review items: 86
- QA missed raw/layout: 2
- State or recipe suspects: 2
- By repair bucket: {'PAIRING_FIX': 84, 'STATE_RECIPE_OR_PRODUCT_FIX': 2}

| Severity | Status | Bucket | Key | Findings | Raw changed | ODiff % | BBox delta | Panel |
|---|---|---|---|---|---:|---:|---:|---|
| high | MISSING_ACTUAL | PAIRING_FIX | hub:detalle-plan-activacion@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | hub:detalle-plan-activacion@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | hub:detalle-plan-rutina@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | hub:detalle-plan-rutina@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | hub:detalle-plan-timer@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | hub:detalle-plan-timer@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | hub:detalle-resumen-ia-0@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | hub:detalle-resumen-ia-0@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | hub:detalle@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | hub:detalle@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | hub:pacientes-empty@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | hub:pacientes-empty@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | hub:pacientes@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | hub:pacientes@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | hub:textos-globales@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | hub:textos-globales@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:actividades-empty@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:actividades-empty@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:actividades-filtered@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:actividades-filtered@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:actividades-marked-hice@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:actividades-marked-hice@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:actividades@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:actividades@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:animo@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:animo@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:avisos-empty@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:avisos-empty@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:avisos-filter-activos@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:avisos-filter-activos@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:avisos-search@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:avisos-search@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:avisos-today@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:avisos-today@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:avisos@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:avisos@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:dbt-library@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:dbt-library@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:dbt-now@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:dbt-now@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:home-no-score@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:home-no-score@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:home@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:home@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:onboarding-error@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:onboarding-error@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:onboarding@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:onboarding@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:recuperar-acceso@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:recuperar-acceso@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:registro-step1-emotion-otro@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:registro-step1-emotion-otro@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:registro-step1-emotion@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:registro-step1-emotion@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:registro-step2-distortions@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:registro-step2-distortions@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:registro-step3-filled@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:registro-step3-filled@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:registro-success@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:registro-success@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:registro@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:registro@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:respiracion-paused@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:respiracion-paused@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:respiracion-running@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:respiracion-running@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:respiracion@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:respiracion@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:rutina-add-task@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:rutina-add-task@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:rutina-all-completed@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:rutina-all-completed@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:rutina-empty@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:rutina-empty@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:rutina@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:rutina@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:timer-empty@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:timer-empty@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:timer-paused@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:timer-paused@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:timer-running@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:timer-running@light | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:timer@dark | missing_actual |  |  |  |  |
| high | MISSING_ACTUAL | PAIRING_FIX | suite:timer@light | missing_actual |  |  |  |  |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:dbt-practice-stop@light | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.17851 | 6.65 | 94 | reports\qa\tmp5_title\panels\suite_dbt-practice-stop_light.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:dbt-practice-stop@dark | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.17657 | 1.86 | 31 | reports\qa\tmp5_title\panels\suite_dbt-practice-stop_dark.png |
