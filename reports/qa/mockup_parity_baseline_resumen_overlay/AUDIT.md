# Mockup HTML parity baseline audit

- Generated: 2026-06-30T23:53:50
- Original HTML: `C:\Users\nosom\Desktop\nm_suite\reports\qa\mockup_parity_baseline_resumen_overlay\sources\original_HEAD.html`
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
- Normalized diff: `C:\Users\nosom\Desktop\nm_suite\reports\qa\mockup_parity_baseline_resumen_overlay\TEXT_DIFF_NORMALIZED.patch`
- EOL report: `C:\Users\nosom\Desktop\nm_suite\reports\qa\mockup_parity_baseline_resumen_overlay\EOL_DELTA.txt`

## Summary

- Total captures: 86 / expected 86
- PASS: 86
- FAIL: 0
- EXPECTED_DELTA: 2
- EXPECTED_DELTA allowlist: `{'hub:detalle-resumen-ia-0@light': {'old_resolution': '720x462', 'new_resolution': '960x600', 'reason': 'canonical AI summary modal window_overlay redesign'}, 'hub:detalle-resumen-ia-0@dark': {'old_resolution': '720x462', 'new_resolution': '960x600', 'reason': 'canonical AI summary modal window_overlay redesign'}}`
- EOL-only delta: YES
- Statistical escalations: 0
- Modal/actioned captures: 4
- Surfaces: `{'window': 76, 'narrow': 6, 'modal': 2, 'window_modal': 2}`

## Results

| Status | Delta | Key | Base mean | Mod mean | Mean limit | Base max | Mod max | Max limit | Mode |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| PASS | EXPECTED_DELTA | `hub:detalle-resumen-ia-0@dark` |  |  |  |  |  |  | single_1x1 |
| PASS | EXPECTED_DELTA | `hub:detalle-resumen-ia-0@light` |  |  |  |  |  |  | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-activacion@dark` | 21.336755 | 21.336755 | 33.005132 | 241.0 | 241.0 | 371.5 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-activacion@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-rutina@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-rutina@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-timer@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-timer@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:pacientes-empty@dark` | 8e-06 | 0.001771 | 5.0 | 4.0 | 40.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:pacientes-empty@light` | 0.002662 | 0.002543 | 5.0 | 47.0 | 47.0 | 80.5 | single_1x1 |
| PASS | NO_DELTA | `hub:pacientes@dark` | 0.00327 | 0.002617 | 5.0 | 63.0 | 65.0 | 104.5 | single_1x1 |
| PASS | NO_DELTA | `hub:pacientes@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:textos-globales@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:textos-globales@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-empty@dark` | 0.000509 | 6.3e-05 | 5.0 | 39.0 | 5.0 | 68.5 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-empty@light` | 0.00013 | 0.0002 | 5.0 | 33.0 | 33.0 | 59.5 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-filtered@dark` | 0.000164 | 0.0 | 5.0 | 42.0 | 0.0 | 73.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-filtered@light` | 0.000174 | 2.3e-05 | 5.0 | 33.0 | 4.0 | 59.5 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-marked-hice@dark` | 5.3e-05 | 0.000188 | 5.0 | 10.0 | 44.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-marked-hice@light` | 0.00013 | 0.000129 | 5.0 | 30.0 | 30.0 | 55.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades@dark` | 5.5e-05 | 0.000171 | 5.0 | 10.0 | 42.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades@light` | 0.0 | 0.000129 | 5.0 | 0.0 | 30.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:animo@dark` | 6.1e-05 | 6.1e-05 | 5.0 | 1.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:animo@light` | 0.00024 | 2e-06 | 5.0 | 1.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-empty@dark` | 0.002566 | 0.002535 | 5.0 | 40.0 | 39.0 | 70.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-empty@light` | 1.6e-05 | 0.003821 | 5.0 | 4.0 | 46.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-filter-activos@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-filter-activos@light` | 6.2e-05 | 6.2e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-search@dark` | 9.4e-05 | 0.000803 | 5.0 | 17.0 | 19.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-search@light` | 3.6e-05 | 0.000922 | 5.0 | 17.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-today@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-today@light` | 1e-06 | 0.0 | 5.0 | 1.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos@dark` | 0.0 | 3.1e-05 | 5.0 | 0.0 | 17.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos@light` | 0.000542 | 5.6e-05 | 5.0 | 39.0 | 3.0 | 68.5 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-library@dark` | 0.001429 | 0.002306 | 5.0 | 50.0 | 50.0 | 85.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-library@light` | 0.001649 | 0.001431 | 5.0 | 55.0 | 55.0 | 92.5 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-now@dark` | 3.5e-05 | 0.0 | 5.0 | 4.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-now@light` | 2.7e-05 | 3.5e-05 | 5.0 | 3.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-stop@dark` | 0.172251 | 0.172247 | 5.0 | 23.0 | 23.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-stop@light` | 2.655328 | 9e-05 | 5.0 | 204.0 | 1.0 | 316.0 | single_1x1 |
| PASS | NO_DELTA | `suite:home-no-score@dark` | 0.000133 | 0.000148 | 5.0 | 17.0 | 17.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:home-no-score@light` | 0.000154 | 0.000165 | 5.0 | 19.0 | 19.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:home@dark` | 0.002955 | 0.000113 | 5.0 | 12.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:home@light` | 9.1e-05 | 0.000386 | 5.0 | 7.0 | 35.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:onboarding-error@dark` | 3.7e-05 | 0.0 | 5.0 | 2.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:onboarding-error@light` | 1.8e-05 | 0.0 | 5.0 | 2.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:onboarding@dark` | 1.3e-05 | 1.8e-05 | 5.0 | 4.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:onboarding@light` | 0.0 | 2e-06 | 5.0 | 0.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:recuperar-acceso@dark` | 3.7e-05 | 3.7e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:recuperar-acceso@light` | 0.0 | 0.000144 | 5.0 | 0.0 | 13.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step1-emotion-otro@dark` | 9.7e-05 | 9.7e-05 | 5.0 | 18.0 | 18.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step1-emotion-otro@light` | 8.3e-05 | 7.9e-05 | 5.0 | 15.0 | 15.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step1-emotion@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step1-emotion@light` | 0.0 | 7.9e-05 | 5.0 | 0.0 | 15.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step2-distortions@dark` | 9.7e-05 | 1.3e-05 | 5.0 | 18.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step2-distortions@light` | 1.2e-05 | 1.3e-05 | 5.0 | 2.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step3-filled@dark` | 9e-06 | 9e-06 | 5.0 | 1.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step3-filled@light` | 7.8e-05 | 8.1e-05 | 5.0 | 14.0 | 14.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-success@dark` | 9.7e-05 | 1e-05 | 5.0 | 18.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-success@light` | 8.9e-05 | 1e-06 | 5.0 | 14.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro@dark` | 0.0 | 9e-06 | 5.0 | 0.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro@light` | 1.3e-05 | 8.2e-05 | 5.0 | 2.0 | 14.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-paused@dark` | 8.9e-05 | 8.9e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-paused@light` | 0.000126 | 0.0 | 5.0 | 3.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-running@dark` | 7.3e-05 | 6e-05 | 5.0 | 3.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-running@light` | 7.8e-05 | 9.7e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion@dark` | 8.6e-05 | 9e-05 | 5.0 | 3.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion@light` | 6e-05 | 5.5e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-add-task@dark` | 0.000156 | 0.000241 | 5.0 | 11.0 | 11.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-add-task@light` | 0.000785 | 0.000805 | 5.0 | 26.0 | 26.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-all-completed@dark` | 0.000714 | 0.000422 | 5.0 | 22.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-all-completed@light` | 0.001366 | 0.000477 | 5.0 | 44.0 | 21.0 | 76.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-empty@dark` | 0.003214 | 0.003216 | 5.0 | 40.0 | 40.0 | 70.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-empty@light` | 0.004742 | 0.000139 | 5.0 | 44.0 | 3.0 | 76.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina@dark` | 1.5e-05 | 1e-06 | 5.0 | 2.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina@light` | 2.8e-05 | 8.6e-05 | 5.0 | 4.0 | 13.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-empty@dark` | 0.000215 | 0.002224 | 5.0 | 25.0 | 41.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-empty@light` | 9.8e-05 | 0.003243 | 5.0 | 3.0 | 46.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-paused@dark` | 0.0 | 8e-06 | 5.0 | 0.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-paused@light` | 1e-05 | 2.8e-05 | 5.0 | 3.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-running@dark` | 2.5e-05 | 1.7e-05 | 5.0 | 4.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-running@light` | 1.9e-05 | 2.8e-05 | 5.0 | 2.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer@dark` | 1e-05 | 1.7e-05 | 5.0 | 4.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer@light` | 0.0 | 1e-05 | 5.0 | 0.0 | 3.0 | 50.0 | single_1x1 |
