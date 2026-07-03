# Mockup HTML parity baseline audit

- Generated: 2026-06-30T21:14:17
- Original HTML: `C:\Users\nosom\Desktop\nm_suite\reports\qa\mockup_parity_baseline\20260630_210914\sources\original_HEAD.html`
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
- Normalized diff: `C:\Users\nosom\Desktop\nm_suite\reports\qa\mockup_parity_baseline\20260630_210914\TEXT_DIFF_NORMALIZED.patch`
- EOL report: `C:\Users\nosom\Desktop\nm_suite\reports\qa\mockup_parity_baseline\20260630_210914\EOL_DELTA.txt`

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
| PASS | NO_DELTA | `hub:pacientes-empty@dark` | 0.001723 | 6.1e-05 | 5.0 | 40.0 | 4.0 | 70.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `hub:pacientes-empty@light` | 7.9e-05 | 0.000156 | 5.0 | 13.0 | 13.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:pacientes@dark` | 0.000516 | 0.00027 | 5.0 | 28.0 | 28.0 | 52.0 | single_1x1 |
| PASS | NO_DELTA | `hub:pacientes@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:textos-globales@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:textos-globales@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:actividades-empty@dark` | 0.000157 | 0.000509 | 5.0 | 41.0 | 39.0 | 71.5 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:actividades-empty@light` | 0.000126 | 0.000131 | 5.0 | 30.0 | 33.0 | 55.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-filtered@dark` | 2e-06 | 2e-06 | 5.0 | 1.0 | 1.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:actividades-filtered@light` | 2.4e-05 | 0.000139 | 5.0 | 4.0 | 33.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:actividades-marked-hice@dark` | 3.1e-05 | 0.000192 | 5.0 | 5.0 | 41.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-marked-hice@light` | 0.000139 | 2e-05 | 5.0 | 33.0 | 3.0 | 59.5 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:actividades@dark` | 2.5e-05 | 3e-05 | 5.0 | 5.0 | 5.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades@light` | 1.7e-05 | 1.6e-05 | 5.0 | 4.0 | 4.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:animo@dark` | 4e-06 | 9e-06 | 5.0 | 1.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:animo@light` | 0.00024 | 0.00024 | 5.0 | 1.0 | 1.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:avisos-empty@dark` | 0.0 | 7.2e-05 | 5.0 | 0.0 | 5.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-empty@light` | 0.003781 | 0.00378 | 5.0 | 46.0 | 46.0 | 79.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-filter-activos@dark` | 2.7e-05 | 0.0 | 5.0 | 3.0 | 0.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:avisos-filter-activos@light` | 0.0 | 3.6e-05 | 5.0 | 0.0 | 2.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:avisos-search@dark` | 6.8e-05 | 0.000861 | 5.0 | 17.0 | 19.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-search@light` | 0.000943 | 6.1e-05 | 5.0 | 22.0 | 17.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-today@dark` | 5.5e-05 | 0.0 | 5.0 | 3.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-today@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos@dark` | 0.000532 | 7.5e-05 | 5.0 | 50.0 | 4.0 | 85.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:avisos@light` | 5.4e-05 | 0.000541 | 5.0 | 3.0 | 39.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:dbt-library@dark` | 0.001461 | 0.001468 | 5.0 | 50.0 | 50.0 | 85.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-library@light` | 0.000622 | 0.000514 | 5.0 | 55.0 | 55.0 | 92.5 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:dbt-now@dark` | 3.4e-05 | 3.7e-05 | 5.0 | 4.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-now@light` | 3.6e-05 | 3.5e-05 | 5.0 | 3.0 | 3.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:dbt-practice-stop@dark` | 0.164021 | 0.171699 | 5.0 | 23.0 | 23.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:dbt-practice-stop@light` | 0.15094 | 0.167155 | 5.0 | 22.0 | 22.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:home-no-score@dark` | 6.5e-05 | 0.000172 | 5.0 | 3.0 | 17.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:home-no-score@light` | 9e-05 | 0.00019 | 5.0 | 4.0 | 19.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:home@dark` | 0.00056 | 0.00314 | 5.0 | 41.0 | 17.0 | 71.5 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:home@light` | 0.000117 | 0.003425 | 5.0 | 3.0 | 19.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:onboarding-error@dark` | 0.000175 | 0.0 | 5.0 | 18.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:onboarding-error@light` | 1.8e-05 | 1.8e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:onboarding@dark` | 0.0 | 1.4e-05 | 5.0 | 0.0 | 4.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:onboarding@light` | 0.0 | 0.000136 | 5.0 | 0.0 | 13.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:recuperar-acceso@dark` | 0.0 | 3.7e-05 | 5.0 | 0.0 | 2.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:recuperar-acceso@light` | 1.6e-05 | 1.8e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:registro-step1-emotion-otro@dark` | 9e-06 | 9.3e-05 | 5.0 | 1.0 | 18.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step1-emotion-otro@light` | 8.3e-05 | 8.1e-05 | 5.0 | 15.0 | 14.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:registro-step1-emotion@dark` | 1.1e-05 | 9.7e-05 | 5.0 | 1.0 | 18.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step1-emotion@light` | 1e-06 | 1e-06 | 5.0 | 1.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step2-distortions@dark` | 0.00011 | 9.7e-05 | 5.0 | 18.0 | 18.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:registro-step2-distortions@light` | 9e-06 | 9.8e-05 | 5.0 | 3.0 | 14.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:registro-step3-filled@dark` | 0.0 | 9.7e-05 | 5.0 | 0.0 | 18.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:registro-step3-filled@light` | 0.0 | 8.3e-05 | 5.0 | 0.0 | 14.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-success@dark` | 0.000102 | 1e-05 | 5.0 | 18.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-success@light` | 7.8e-05 | 7e-06 | 5.0 | 14.0 | 3.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:registro@dark` | 2e-06 | 9e-06 | 5.0 | 1.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro@light` | 8.9e-05 | 1.6e-05 | 5.0 | 14.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-paused@dark` | 3.5e-05 | 3.3e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-paused@light` | 1e-06 | 0.0 | 5.0 | 1.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-running@dark` | 0.000104 | 1.7e-05 | 5.0 | 3.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-running@light` | 7.2e-05 | 3.4e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:respiracion@dark` | 9.6e-05 | 0.000101 | 5.0 | 3.0 | 2.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:respiracion@light` | 1e-06 | 1.9e-05 | 5.0 | 1.0 | 2.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:rutina-add-task@dark` | 5e-05 | 9e-05 | 5.0 | 6.0 | 6.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-add-task@light` | 0.000281 | 0.00027 | 5.0 | 18.0 | 18.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-all-completed@dark` | 0.000887 | 0.000833 | 5.0 | 39.0 | 39.0 | 68.5 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:rutina-all-completed@light` | 0.00122 | 0.00127 | 5.0 | 44.0 | 44.0 | 76.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-empty@dark` | 0.003178 | 7.3e-05 | 5.0 | 40.0 | 4.0 | 70.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:rutina-empty@light` | 1.4e-05 | 0.004728 | 5.0 | 2.0 | 44.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:rutina@dark` | 0.000774 | 0.000816 | 5.0 | 24.0 | 24.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:rutina@light` | 6.9e-05 | 0.000307 | 5.0 | 6.0 | 18.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-empty@dark` | 0.002214 | 0.002185 | 5.0 | 41.0 | 41.0 | 71.5 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:timer-empty@light` | 0.003242 | 0.003296 | 5.0 | 46.0 | 46.0 | 79.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:timer-paused@dark` | 1e-05 | 2.5e-05 | 5.0 | 4.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-paused@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-running@dark` | 2.7e-05 | 0.0 | 5.0 | 4.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-running@light` | 9e-06 | 9e-06 | 5.0 | 3.0 | 3.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:timer@dark` | 0.0 | 1e-05 | 5.0 | 0.0 | 4.0 | 50.0 | single_1x1 |
| PASS | UNEXPECTED_DELTA | `suite:timer@light` | 1.9e-05 | 2.8e-05 | 5.0 | 2.0 | 3.0 | 50.0 | single_1x1 |
