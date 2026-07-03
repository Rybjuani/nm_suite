# Mockup HTML parity baseline audit

- Generated: 2026-06-30T21:20:26
- Original HTML: `C:\Users\nosom\Desktop\nm_suite\reports\qa\mockup_parity_baseline\20260630_211522\sources\original_HEAD.html`
- Modified HTML: `C:\Users\nosom\Desktop\nm_suite\qa\pack canonico\neuromood-mockup_reparado.html`
- Original source: `git:HEAD`
- Formula: `mod_mean <= max(baseline_mean * 1.5 + 1.0, 5.0)`
- Formula: `mod_max <= max(baseline_max * 1.5 + 10, 50)`
- Scope: full canonical recipe from `qa/pack canonico/generate_captures.js`
- Safety: comparator thresholds, canonical PNGs, and VAS are not modified.

## Text delta

- Raw changed: YES
- EOL-only delta: NO
- Normalized textual delta: YES
- Normalized diff lines: 113
- Normalized diff: `C:\Users\nosom\Desktop\nm_suite\reports\qa\mockup_parity_baseline\20260630_211522\TEXT_DIFF_NORMALIZED.patch`
- EOL report: `C:\Users\nosom\Desktop\nm_suite\reports\qa\mockup_parity_baseline\20260630_211522\EOL_DELTA.txt`

## Summary

- Total captures: 86 / expected 86
- PASS: 86
- FAIL: 0
- EXPECTED_DELTA: 2
- EXPECTED_DELTA allowlist: `{'hub:detalle-resumen-ia-0@light': {'old_resolution': '560x220', 'new_resolution': '720x462', 'reason': 'canonical AI summary modal redesign'}, 'hub:detalle-resumen-ia-0@dark': {'old_resolution': '560x220', 'new_resolution': '720x462', 'reason': 'canonical AI summary modal redesign'}}`
- EOL-only delta: NO
- Statistical escalations: 0
- Modal/actioned captures: 4
- Surfaces: `{'window': 76, 'narrow': 6, 'modal': 2, 'window_modal': 2}`

## Results

| Status | Delta | Key | Base mean | Mod mean | Mean limit | Base max | Mod max | Max limit | Mode |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| PASS | EXPECTED_DELTA | `hub:detalle-resumen-ia-0@dark` |  |  |  |  |  |  | single_1x1 |
| PASS | EXPECTED_DELTA | `hub:detalle-resumen-ia-0@light` |  |  |  |  |  |  | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-activacion@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-activacion@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-rutina@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-rutina@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-timer@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-timer@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:pacientes-empty@dark` | 2e-05 | 0.001764 | 5.0 | 2.0 | 40.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:pacientes-empty@light` | 0.002543 | 1e-05 | 5.0 | 47.0 | 2.0 | 80.5 | single_1x1 |
| PASS | NO_DELTA | `hub:pacientes@dark` | 0.002226 | 0.002701 | 5.0 | 65.0 | 65.0 | 107.5 | single_1x1 |
| PASS | NO_DELTA | `hub:pacientes@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:textos-globales@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:textos-globales@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-empty@dark` | 0.00052 | 0.000657 | 5.0 | 39.0 | 41.0 | 68.5 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-empty@light` | 1.7e-05 | 0.000755 | 5.0 | 4.0 | 44.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-filtered@dark` | 0.000174 | 0.000161 | 5.0 | 44.0 | 44.0 | 76.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-filtered@light` | 1.6e-05 | 0.000131 | 5.0 | 4.0 | 33.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-marked-hice@dark` | 0.000192 | 2.8e-05 | 5.0 | 41.0 | 4.0 | 71.5 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-marked-hice@light` | 0.000134 | 2.4e-05 | 5.0 | 30.0 | 4.0 | 55.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades@dark` | 0.000163 | 3.6e-05 | 5.0 | 41.0 | 10.0 | 71.5 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades@light` | 0.0 | 0.000126 | 5.0 | 0.0 | 30.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:animo@dark` | 0.000181 | 0.0 | 5.0 | 1.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:animo@light` | 1.3e-05 | 0.000246 | 5.0 | 3.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-empty@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-empty@light` | 0.003802 | 1e-05 | 5.0 | 46.0 | 3.0 | 79.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-filter-activos@dark` | 5.5e-05 | 2.8e-05 | 5.0 | 3.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-filter-activos@light` | 1e-06 | 2.5e-05 | 5.0 | 1.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-search@dark` | 0.0 | 0.000824 | 5.0 | 0.0 | 19.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-search@light` | 7.3e-05 | 2.5e-05 | 5.0 | 17.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-today@dark` | 2.6e-05 | 2.9e-05 | 5.0 | 2.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-today@light` | 0.0 | 2.5e-05 | 5.0 | 0.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos@dark` | 0.000459 | 0.000499 | 5.0 | 50.0 | 50.0 | 85.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos@light` | 0.000508 | 0.000468 | 5.0 | 39.0 | 39.0 | 68.5 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-library@dark` | 0.002278 | 0.001524 | 5.0 | 50.0 | 50.0 | 85.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-library@light` | 0.003589 | 0.002958 | 5.0 | 55.0 | 55.0 | 92.5 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-now@dark` | 1.4e-05 | 1.4e-05 | 5.0 | 4.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-now@light` | 1e-06 | 3.6e-05 | 5.0 | 1.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-stop@dark` | 0.172009 | 0.171995 | 5.0 | 23.0 | 23.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-stop@light` | 2.566355 | 2.54916 | 5.0 | 204.0 | 204.0 | 316.0 | single_1x1 |
| PASS | NO_DELTA | `suite:home-no-score@dark` | 0.000171 | 6.4e-05 | 5.0 | 17.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:home-no-score@light` | 2.2e-05 | 0.000201 | 5.0 | 3.0 | 19.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:home@dark` | 0.003216 | 0.000198 | 5.0 | 17.0 | 5.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:home@light` | 0.000211 | 0.0002 | 5.0 | 19.0 | 19.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:onboarding-error@dark` | 1.8e-05 | 0.0 | 5.0 | 4.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:onboarding-error@light` | 1.9e-05 | 1.9e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:onboarding@dark` | 5.6e-05 | 3.7e-05 | 5.0 | 4.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:onboarding@light` | 1.5e-05 | 1.5e-05 | 5.0 | 1.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:recuperar-acceso@dark` | 1.8e-05 | 5.4e-05 | 5.0 | 4.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:recuperar-acceso@light` | 1.8e-05 | 1.8e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step1-emotion-otro@dark` | 0.0 | 9.3e-05 | 5.0 | 0.0 | 18.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step1-emotion-otro@light` | 8.9e-05 | 8.9e-05 | 5.0 | 14.0 | 14.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step1-emotion@dark` | 9.7e-05 | 9.7e-05 | 5.0 | 18.0 | 18.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step1-emotion@light` | 1e-06 | 0.0 | 5.0 | 1.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step2-distortions@dark` | 0.000108 | 0.000104 | 5.0 | 18.0 | 18.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step2-distortions@light` | 8.9e-05 | 8.6e-05 | 5.0 | 15.0 | 14.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step3-filled@dark` | 9e-06 | 9.7e-05 | 5.0 | 1.0 | 18.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step3-filled@light` | 0.0 | 3e-06 | 5.0 | 0.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-success@dark` | 2e-06 | 1.8e-05 | 5.0 | 1.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-success@light` | 0.0 | 8.4e-05 | 5.0 | 0.0 | 14.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro@dark` | 0.0001 | 1.2e-05 | 5.0 | 18.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro@light` | 8.1e-05 | 0.0 | 5.0 | 14.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-paused@dark` | 9.4e-05 | 1e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-paused@light` | 2.4e-05 | 3.8e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-running@dark` | 4.3e-05 | 0.000104 | 5.0 | 3.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-running@light` | 1e-06 | 7.2e-05 | 5.0 | 1.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion@dark` | 0.000105 | 1.4e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion@light` | 6.2e-05 | 1.7e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-add-task@dark` | 9e-05 | 0.000181 | 5.0 | 5.0 | 19.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-add-task@light` | 9.1e-05 | 0.001071 | 5.0 | 5.0 | 26.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-all-completed@dark` | 0.00084 | 0.00112 | 5.0 | 39.0 | 39.0 | 68.5 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-all-completed@light` | 0.000633 | 0.000657 | 5.0 | 21.0 | 18.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-empty@dark` | 0.003214 | 7.8e-05 | 5.0 | 40.0 | 4.0 | 70.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-empty@light` | 0.004719 | 0.0 | 5.0 | 44.0 | 0.0 | 76.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina@dark` | 7.3e-05 | 7.8e-05 | 5.0 | 5.0 | 6.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina@light` | 0.000552 | 0.000538 | 5.0 | 25.0 | 25.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-empty@dark` | 6.5e-05 | 8.2e-05 | 5.0 | 4.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-empty@light` | 0.003278 | 0.003242 | 5.0 | 46.0 | 45.0 | 79.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-paused@dark` | 2.5e-05 | 0.0 | 5.0 | 4.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-paused@light` | 0.0 | 2.8e-05 | 5.0 | 0.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-running@dark` | 2e-06 | 2e-06 | 5.0 | 1.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-running@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer@dark` | 0.0 | 8e-06 | 5.0 | 0.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer@light` | 2.8e-05 | 2.8e-05 | 5.0 | 3.0 | 3.0 | 50.0 | single_1x1 |
