# Mockup HTML parity baseline audit

- Generated: 2026-07-01T21:09:58
- Original HTML: `C:\Users\nosom\Desktop\nm_suite\reports\qa\mockup_parity_baseline\20260701_204457\sources\original_HEAD.html`
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
- Normalized diff lines: 344
- Normalized diff: `C:\Users\nosom\Desktop\nm_suite\reports\qa\mockup_parity_baseline\20260701_204457\TEXT_DIFF_NORMALIZED.patch`
- EOL report: `C:\Users\nosom\Desktop\nm_suite\reports\qa\mockup_parity_baseline\20260701_204457\EOL_DELTA.txt`

## Summary

- Total captures: 86 / expected 86
- PASS: 83
- FAIL: 3
- EXPECTED_DELTA: 1
- EXPECTED_DELTA allowlist: `{'hub:detalle-resumen-ia-0@light': {'old_resolution': '720x462', 'new_resolution': '960x600', 'reason': 'canonical AI summary modal window_overlay redesign'}, 'hub:detalle-resumen-ia-0@dark': {'old_resolution': '720x462', 'new_resolution': '960x600', 'reason': 'canonical AI summary modal window_overlay redesign'}}`
- EOL-only delta: NO
- Statistical escalations: 4
- Modal/actioned captures: 4
- Surfaces: `{'window': 76, 'narrow': 6, 'modal': 0, 'window_modal': 4}`

## Results

| Status | Delta | Key | Base mean | Mod mean | Mean limit | Base max | Mod max | Max limit | Mode |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| FAIL | UNEXPECTED_DELTA | `suite:dbt-library@dark` | 0.002299 | 11.098301 | 5.0 | 50.0 | 230.0 | 85.0 | statistical_5x5_p95 |
| FAIL | UNEXPECTED_DELTA | `suite:dbt-library@light` | 0.003264 | 10.139645 | 5.0 | 55.0 | 205.0 | 92.5 | statistical_5x5_p95 |
| FAIL | UNEXPECTED_DELTA | `suite:dbt-practice-stop@dark` | 0.171524 | 2.157456 | 5.0 | 23.0 | 207.0 | 50.0 | statistical_5x5_p95 |
| PASS | EXPECTED_DELTA | `hub:detalle-resumen-ia-0@dark` | 0.89862 | 4.635031 | 5.0 | 150.0 | 205.0 | 235.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-activacion@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-activacion@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-rutina@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-rutina@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-timer@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-timer@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-resumen-ia-0@light` | 0.91539 | 0.91539 | 5.0 | 166.0 | 166.0 | 259.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:pacientes-empty@dark` | 0.001764 | 0.001879 | 5.0 | 40.0 | 40.0 | 70.0 | single_1x1 |
| PASS | NO_DELTA | `hub:pacientes-empty@light` | 0.002558 | 0.002525 | 5.0 | 47.0 | 47.0 | 80.5 | single_1x1 |
| PASS | NO_DELTA | `hub:pacientes@dark` | 0.00342 | 0.000653 | 5.0 | 63.0 | 34.0 | 104.5 | single_1x1 |
| PASS | NO_DELTA | `hub:pacientes@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:textos-globales@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:textos-globales@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-empty@dark` | 0.000534 | 0.000157 | 5.0 | 39.0 | 41.0 | 68.5 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-empty@light` | 0.000803 | 0.0 | 5.0 | 45.0 | 0.0 | 77.5 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-filtered@dark` | 1.3e-05 | 0.000201 | 5.0 | 2.0 | 44.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-filtered@light` | 8e-06 | 0.0 | 5.0 | 2.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-marked-hice@dark` | 5.8e-05 | 0.000192 | 5.0 | 10.0 | 41.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-marked-hice@light` | 0.000134 | 0.000159 | 5.0 | 30.0 | 30.0 | 55.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades@dark` | 0.000185 | 3.5e-05 | 5.0 | 41.0 | 10.0 | 71.5 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades@light` | 1.9e-05 | 3.3e-05 | 5.0 | 3.0 | 8.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:animo@dark` | 9e-06 | 7e-06 | 5.0 | 1.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:animo@light` | 1.8e-05 | 2e-06 | 5.0 | 3.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-empty@dark` | 0.002562 | 0.000101 | 5.0 | 39.0 | 5.0 | 68.5 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-empty@light` | 0.003802 | 0.003802 | 5.0 | 46.0 | 46.0 | 79.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-filter-activos@dark` | 2.6e-05 | 2.6e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-filter-activos@light` | 0.0 | 2.5e-05 | 5.0 | 0.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-search@dark` | 0.000809 | 0.0 | 5.0 | 19.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-search@light` | 6.3e-05 | 0.0 | 5.0 | 3.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-today@dark` | 5.3e-05 | 2.7e-05 | 5.0 | 3.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-today@light` | 3.6e-05 | 0.0 | 5.0 | 2.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos@dark` | 0.000486 | 0.000104 | 5.0 | 50.0 | 17.0 | 85.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos@light` | 5.3e-05 | 0.00043 | 5.0 | 3.0 | 39.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-now@dark` | 1.4e-05 | 3.5e-05 | 5.0 | 4.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-now@light` | 2.7e-05 | 8e-06 | 5.0 | 3.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-stop@light` | 2.695207 | 1.99742 | 5.04281 | 204.0 | 203.0 | 316.0 | statistical_5x5_p95 |
| PASS | NO_DELTA | `suite:home-no-score@dark` | 5e-05 | 3.5e-05 | 5.0 | 3.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:home-no-score@light` | 1e-05 | 2.7e-05 | 5.0 | 3.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:home@dark` | 5.5e-05 | 0.003212 | 5.0 | 3.0 | 41.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:home@light` | 0.003436 | 0.000321 | 5.0 | 34.0 | 35.0 | 61.0 | single_1x1 |
| PASS | NO_DELTA | `suite:onboarding-error@dark` | 5.6e-05 | 5.6e-05 | 5.0 | 4.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:onboarding-error@light` | 1.8e-05 | 0.0 | 5.0 | 2.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:onboarding@dark` | 1.8e-05 | 5.6e-05 | 5.0 | 4.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:onboarding@light` | 0.000144 | 0.000144 | 5.0 | 13.0 | 13.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:recuperar-acceso@dark` | 3.7e-05 | 1.7e-05 | 5.0 | 2.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:recuperar-acceso@light` | 1.8e-05 | 1e-06 | 5.0 | 2.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step1-emotion-otro@dark` | 9.7e-05 | 1.3e-05 | 5.0 | 18.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step1-emotion-otro@light` | 4e-06 | 8.2e-05 | 5.0 | 2.0 | 14.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step1-emotion@dark` | 9.7e-05 | 0.0 | 5.0 | 18.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step1-emotion@light` | 1.2e-05 | 3e-06 | 5.0 | 3.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step2-distortions@dark` | 0.0 | 0.000109 | 5.0 | 0.0 | 18.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step2-distortions@light` | 9e-06 | 8.2e-05 | 5.0 | 3.0 | 14.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step3-filled@dark` | 1.6e-05 | 9.3e-05 | 5.0 | 4.0 | 18.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step3-filled@light` | 7.8e-05 | 9e-06 | 5.0 | 14.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-success@dark` | 0.000104 | 9.7e-05 | 5.0 | 18.0 | 18.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-success@light` | 8.8e-05 | 9.5e-05 | 5.0 | 14.0 | 14.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro@dark` | 0.000104 | 0.0 | 5.0 | 18.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro@light` | 4e-06 | 8.1e-05 | 5.0 | 2.0 | 14.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-paused@dark` | 6e-06 | 2e-06 | 5.0 | 1.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-paused@light` | 7.2e-05 | 7.2e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-running@dark` | 4.5e-05 | 7e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-running@light` | 0.0001 | 0.000107 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion@dark` | 0.000124 | 1.8e-05 | 5.0 | 3.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion@light` | 0.000137 | 6.4e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-add-task@dark` | 0.000786 | 0.000593 | 5.0 | 23.0 | 24.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-add-task@light` | 0.000155 | 0.000226 | 5.0 | 13.0 | 6.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-all-completed@dark` | 0.000593 | 0.000539 | 5.0 | 40.0 | 40.0 | 70.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-all-completed@light` | 0.000912 | 0.00215 | 5.0 | 21.0 | 37.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-empty@dark` | 1.3e-05 | 0.003227 | 5.0 | 2.0 | 40.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-empty@light` | 0.000125 | 0.004644 | 5.0 | 3.0 | 44.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina@dark` | 0.000656 | 0.000144 | 5.0 | 23.0 | 11.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina@light` | 0.000623 | 0.000927 | 5.0 | 26.0 | 23.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-empty@dark` | 0.002193 | 0.002211 | 5.0 | 41.0 | 41.0 | 71.5 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-empty@light` | 1.9e-05 | 0.0 | 5.0 | 2.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-paused@dark` | 1.7e-05 | 0.0 | 5.0 | 3.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-paused@light` | 1.9e-05 | 9e-06 | 5.0 | 2.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-running@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-running@light` | 1.9e-05 | 0.0 | 5.0 | 2.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer@dark` | 2.5e-05 | 2e-06 | 5.0 | 4.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer@light` | 1e-06 | 1e-05 | 5.0 | 1.0 | 3.0 | 50.0 | single_1x1 |

## FAIL Details

- `suite:dbt-library@light`: dynamic_baseline_exceeded_after_statistical_escalation (mode `statistical_5x5_p95`)
- `suite:dbt-library@dark`: dynamic_baseline_exceeded_after_statistical_escalation (mode `statistical_5x5_p95`)
- `suite:dbt-practice-stop@dark`: dynamic_baseline_exceeded_after_statistical_escalation (mode `statistical_5x5_p95`)
