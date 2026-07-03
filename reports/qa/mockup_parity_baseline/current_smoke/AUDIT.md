# Mockup HTML parity baseline audit

- Generated: 2026-06-30T16:44:10
- Original HTML: `C:\Users\nosom\Desktop\nm_suite\reports\qa\mockup_parity_baseline\current_smoke\sources\original_HEAD.html`
- Modified HTML: `C:\Users\nosom\Desktop\nm_suite\qa\pack canonico\neuromood-mockup_reparado.html`
- Original source: `git:HEAD`
- Formula: `mod_mean <= max(baseline_mean * 1.5 + 1.0, 5.0)`
- Formula: `mod_max <= max(baseline_max * 1.5 + 10, 50)`
- Scope: full canonical recipe from `qa/pack canonico/generate_captures.js`
- Safety: comparator thresholds, canonical PNGs, and VAS are not modified.

## Text delta

- Raw changed: YES
- EOL-only delta: YES
- Normalized textual delta: NO
- Normalized diff lines: 0
- Normalized diff: `C:\Users\nosom\Desktop\nm_suite\reports\qa\mockup_parity_baseline\current_smoke\TEXT_DIFF_NORMALIZED.patch`
- EOL report: `C:\Users\nosom\Desktop\nm_suite\reports\qa\mockup_parity_baseline\current_smoke\EOL_DELTA.txt`

## Summary

- Total captures: 86 / expected 86
- PASS: 84
- FAIL: 2
- EXPECTED_DELTA: 0
- EOL-only delta rows: 86
- Statistical escalations: 0
- Modal/actioned captures: 4
- Surfaces: `{'window': 76, 'narrow': 6, 'modal': 2, 'window_modal': 2}`

## Results

| Status | Delta | Key | Base mean | Mod mean | Mean limit | Base max | Mod max | Max limit | Mode |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| FAIL | EOL_ONLY_DELTA | `hub:detalle-resumen-ia-0@light` | 0.0 | 1.80734 | 5.0 | 0.0 | 154.0 | 50.0 | single_1x1 |
| FAIL | EOL_ONLY_DELTA | `suite:dbt-practice-stop@light` | 0.168282 | 2.71205 | 5.0 | 22.0 | 204.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `hub:detalle-plan-activacion@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `hub:detalle-plan-activacion@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `hub:detalle-plan-rutina@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `hub:detalle-plan-rutina@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `hub:detalle-plan-timer@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `hub:detalle-plan-timer@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `hub:detalle-resumen-ia-0@dark` | 1.750319 | 1.76099 | 5.0 | 147.0 | 147.0 | 230.5 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `hub:detalle@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `hub:detalle@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `hub:pacientes-empty@dark` | 7.5e-05 | 0.001726 | 5.0 | 3.0 | 40.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `hub:pacientes-empty@light` | 0.002594 | 8e-05 | 5.0 | 47.0 | 4.0 | 80.5 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `hub:pacientes@dark` | 0.000489 | 0.002273 | 5.0 | 37.0 | 65.0 | 65.5 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `hub:pacientes@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `hub:textos-globales@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `hub:textos-globales@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:actividades-empty@dark` | 0.0 | 0.000161 | 5.0 | 0.0 | 44.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:actividades-empty@light` | 0.000927 | 0.000123 | 5.0 | 45.0 | 30.0 | 77.5 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:actividades-filtered@dark` | 0.000203 | 0.000175 | 5.0 | 44.0 | 44.0 | 76.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:actividades-filtered@light` | 0.0 | 0.000126 | 5.0 | 0.0 | 30.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:actividades-marked-hice@dark` | 3.5e-05 | 2.8e-05 | 5.0 | 10.0 | 10.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:actividades-marked-hice@light` | 0.000158 | 0.000168 | 5.0 | 30.0 | 33.0 | 55.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:actividades@dark` | 0.000185 | 0.0 | 5.0 | 41.0 | 0.0 | 71.5 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:actividades@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:animo@dark` | 1.2e-05 | 9e-06 | 5.0 | 4.0 | 1.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:animo@light` | 0.000246 | 0.000242 | 5.0 | 1.0 | 1.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:avisos-empty@dark` | 2e-06 | 0.002594 | 5.0 | 1.0 | 40.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:avisos-empty@light` | 9.3e-05 | 2.5e-05 | 5.0 | 5.0 | 2.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:avisos-filter-activos@dark` | 2.6e-05 | 2.6e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:avisos-filter-activos@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:avisos-search@dark` | 0.000783 | 0.000852 | 5.0 | 19.0 | 19.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:avisos-search@light` | 0.000927 | 0.000927 | 5.0 | 22.0 | 22.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:avisos-today@dark` | 2.8e-05 | 2.8e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:avisos-today@light` | 2.5e-05 | 3.7e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:avisos@dark` | 0.000459 | 0.000488 | 5.0 | 50.0 | 50.0 | 85.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:avisos@light` | 6.1e-05 | 3.6e-05 | 5.0 | 17.0 | 17.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:dbt-library@dark` | 0.000906 | 0.001468 | 5.0 | 50.0 | 50.0 | 85.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:dbt-library@light` | 0.001361 | 0.003049 | 5.0 | 55.0 | 55.0 | 92.5 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:dbt-now@dark` | 3.2e-05 | 3.4e-05 | 5.0 | 4.0 | 4.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:dbt-now@light` | 3.1e-05 | 9e-06 | 5.0 | 3.0 | 2.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:dbt-practice-stop@dark` | 0.171339 | 0.00704 | 5.0 | 23.0 | 9.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:home-no-score@dark` | 0.000157 | 0.000201 | 5.0 | 17.0 | 17.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:home-no-score@light` | 6.3e-05 | 0.000163 | 5.0 | 3.0 | 19.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:home@dark` | 0.000501 | 0.000395 | 5.0 | 41.0 | 42.0 | 71.5 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:home@light` | 0.003302 | 0.000204 | 5.0 | 8.0 | 35.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:onboarding-error@dark` | 3.7e-05 | 5.6e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:onboarding-error@light` | 5e-06 | 5e-06 | 5.0 | 1.0 | 1.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:onboarding@dark` | 1.7e-05 | 3.8e-05 | 5.0 | 4.0 | 2.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:onboarding@light` | 0.000146 | 0.000146 | 5.0 | 13.0 | 13.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:recuperar-acceso@dark` | 3.8e-05 | 1.8e-05 | 5.0 | 2.0 | 4.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:recuperar-acceso@light` | 1.8e-05 | 0.0 | 5.0 | 2.0 | 0.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:registro-step1-emotion-otro@dark` | 9.7e-05 | 0.0 | 5.0 | 18.0 | 0.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:registro-step1-emotion-otro@light` | 1.2e-05 | 0.0 | 5.0 | 3.0 | 0.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:registro-step1-emotion@dark` | 9.5e-05 | 1.1e-05 | 5.0 | 18.0 | 1.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:registro-step1-emotion@light` | 4e-06 | 7.9e-05 | 5.0 | 2.0 | 15.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:registro-step2-distortions@dark` | 0.000117 | 0.000104 | 5.0 | 18.0 | 18.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:registro-step2-distortions@light` | 8.9e-05 | 0.0 | 5.0 | 14.0 | 0.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:registro-step3-filled@dark` | 0.0 | 9e-06 | 5.0 | 0.0 | 1.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:registro-step3-filled@light` | 8.3e-05 | 8.9e-05 | 5.0 | 15.0 | 14.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:registro-success@dark` | 0.0 | 0.000104 | 5.0 | 0.0 | 18.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:registro-success@light` | 8.1e-05 | 7e-06 | 5.0 | 14.0 | 3.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:registro@dark` | 0.0 | 0.000104 | 5.0 | 0.0 | 18.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:registro@light` | 0.0 | 1e-06 | 5.0 | 0.0 | 1.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:respiracion-paused@dark` | 8.9e-05 | 8e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:respiracion-paused@light` | 3.8e-05 | 2.7e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:respiracion-running@dark` | 4.1e-05 | 5.2e-05 | 5.0 | 3.0 | 3.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:respiracion-running@light` | 1.8e-05 | 8.3e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:respiracion@dark` | 4.3e-05 | 3.5e-05 | 5.0 | 3.0 | 2.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:respiracion@light` | 0.000175 | 0.000125 | 5.0 | 3.0 | 3.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:rutina-add-task@dark` | 0.000723 | 0.000155 | 5.0 | 23.0 | 19.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:rutina-add-task@light` | 0.00011 | 4.9e-05 | 5.0 | 5.0 | 4.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:rutina-all-completed@dark` | 0.00168 | 0.000947 | 5.0 | 40.0 | 39.0 | 70.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:rutina-all-completed@light` | 0.001251 | 0.000812 | 5.0 | 44.0 | 44.0 | 76.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:rutina-empty@dark` | 0.003214 | 0.003214 | 5.0 | 40.0 | 40.0 | 70.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:rutina-empty@light` | 0.0 | 1e-06 | 5.0 | 0.0 | 1.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:rutina@dark` | 5e-05 | 0.000122 | 5.0 | 3.0 | 5.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:rutina@light` | 0.000782 | 0.000453 | 5.0 | 26.0 | 18.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:timer-empty@dark` | 0.002214 | 0.002214 | 5.0 | 41.0 | 41.0 | 71.5 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:timer-empty@light` | 0.003278 | 0.003233 | 5.0 | 46.0 | 45.0 | 79.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:timer-paused@dark` | 1.9e-05 | 0.0 | 5.0 | 3.0 | 0.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:timer-paused@light` | 1e-06 | 1e-06 | 5.0 | 1.0 | 1.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:timer-running@dark` | 0.0 | 8e-06 | 5.0 | 0.0 | 4.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:timer-running@light` | 1.9e-05 | 1.9e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:timer@dark` | 1.9e-05 | 0.0 | 5.0 | 3.0 | 0.0 | 50.0 | single_1x1 |
| PASS | EOL_ONLY_DELTA | `suite:timer@light` | 0.0 | 1e-06 | 5.0 | 0.0 | 1.0 | 50.0 | single_1x1 |

## FAIL Details

- `hub:detalle-resumen-ia-0@light`: dynamic_baseline_exceeded (mode `single_1x1`)
- `suite:dbt-practice-stop@light`: dynamic_baseline_exceeded (mode `single_1x1`)
