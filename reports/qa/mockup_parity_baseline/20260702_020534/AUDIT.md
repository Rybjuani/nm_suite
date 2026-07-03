# Mockup HTML parity baseline audit

- Generated: 2026-07-02T02:42:19
- Original HTML: `C:\Users\nosom\Desktop\nm_suite\reports\qa\mockup_parity_baseline\20260702_020534\sources\original_HEAD.html`
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
- Normalized diff: `C:\Users\nosom\Desktop\nm_suite\reports\qa\mockup_parity_baseline\20260702_020534\TEXT_DIFF_NORMALIZED.patch`
- EOL report: `C:\Users\nosom\Desktop\nm_suite\reports\qa\mockup_parity_baseline\20260702_020534\EOL_DELTA.txt`

## Summary

- Total captures: 116 / expected 116
- PASS: 116
- FAIL: 0
- EXPECTED_DELTA: 0
- EXPECTED_DELTA allowlist: `{'hub:detalle-resumen-ia-0@light': {'old_resolution': '720x462', 'new_resolution': '960x600', 'reason': 'canonical AI summary modal window_overlay redesign'}, 'hub:detalle-resumen-ia-0@dark': {'old_resolution': '720x462', 'new_resolution': '960x600', 'reason': 'canonical AI summary modal window_overlay redesign'}}`
- EOL-only delta: YES
- Statistical escalations: 2
- Modal/actioned captures: 34
- Surfaces: `{'window': 76, 'narrow': 6, 'modal': 0, 'window_modal': 34}`

## Results

| Status | Delta | Key | Base mean | Mod mean | Mean limit | Base max | Mod max | Max limit | Mode |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| PASS | NO_DELTA | `hub:detalle-plan-activacion@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-activacion@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-rutina@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-rutina@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-timer@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-timer@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-resumen-ia-0@dark` | 4.611617 | 0.001 | 7.917426 | 205.0 | 10.0 | 317.5 | statistical_5x5_p95 |
| PASS | NO_DELTA | `hub:detalle-resumen-ia-0@light` | 0.929775 | 0.0 | 5.0 | 166.0 | 0.0 | 259.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:pacientes-empty@dark` | 8.2e-05 | 0.001756 | 5.0 | 4.0 | 40.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:pacientes-empty@light` | 9e-06 | 0.002519 | 5.0 | 2.0 | 47.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:pacientes@dark` | 0.000832 | 0.0033 | 5.0 | 37.0 | 63.0 | 65.5 | single_1x1 |
| PASS | NO_DELTA | `hub:pacientes@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:textos-globales@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:textos-globales@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-empty@dark` | 0.000543 | 0.000193 | 5.0 | 39.0 | 41.0 | 68.5 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-empty@light` | 6.8e-05 | 0.000802 | 5.0 | 4.0 | 45.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-filtered@dark` | 0.00017 | 0.00017 | 5.0 | 41.0 | 41.0 | 71.5 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-filtered@light` | 9e-06 | 0.000135 | 5.0 | 2.0 | 30.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-marked-hice@dark` | 0.000192 | 3e-05 | 5.0 | 41.0 | 5.0 | 71.5 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-marked-hice@light` | 4.3e-05 | 3.6e-05 | 5.0 | 8.0 | 8.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades@dark` | 0.000165 | 3.5e-05 | 5.0 | 41.0 | 10.0 | 71.5 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades@light` | 0.000154 | 0.000151 | 5.0 | 30.0 | 30.0 | 55.0 | single_1x1 |
| PASS | NO_DELTA | `suite:animo@dark` | 1.2e-05 | 0.000321 | 5.0 | 1.0 | 49.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:animo@light` | 2e-06 | 1.3e-05 | 5.0 | 1.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-empty@dark` | 2.7e-05 | 0.0 | 5.0 | 3.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-empty@light` | 0.0 | 0.003797 | 5.0 | 0.0 | 46.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-filter-activos@dark` | 2.8e-05 | 5.3e-05 | 5.0 | 2.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-filter-activos@light` | 2.5e-05 | 1e-06 | 5.0 | 2.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-search@dark` | 4.7e-05 | 0.000847 | 5.0 | 3.0 | 19.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-search@light` | 1.7e-05 | 9.7e-05 | 5.0 | 1.0 | 17.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-today@dark` | 2.9e-05 | 0.0 | 5.0 | 3.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-today@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos@dark` | 5.8e-05 | 0.000104 | 5.0 | 17.0 | 17.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos@light` | 0.000545 | 8.2e-05 | 5.0 | 39.0 | 3.0 | 68.5 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-library@dark` | 0.002181 | 0.002646 | 5.0 | 34.0 | 34.0 | 61.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-library@light` | 0.00149 | 0.00149 | 5.0 | 38.0 | 37.0 | 67.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-now@dark` | 0.0 | 3.6e-05 | 5.0 | 0.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-now@light` | 3.6e-05 | 1e-06 | 5.0 | 3.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-check-facts@dark` | 0.163344 | 0.163307 | 5.0 | 20.0 | 20.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-check-facts@light` | 2.457135 | 2.335161 | 5.0 | 204.0 | 204.0 | 316.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-dear-man@dark` | 7.3e-05 | 0.165953 | 5.0 | 1.0 | 20.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-dear-man@light` | 0.144278 | 0.018775 | 5.0 | 21.0 | 10.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-fast@dark` | 1.538256 | 1.542348 | 5.0 | 207.0 | 207.0 | 320.5 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-fast@light` | 7.5e-05 | 0.148277 | 5.0 | 1.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-give@dark` | 0.156245 | 3.6e-05 | 5.0 | 20.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-give@light` | 0.150191 | 0.151138 | 5.0 | 22.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-non-judgmental@dark` | 0.000637 | 0.153707 | 5.0 | 9.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-non-judgmental@light` | 0.131157 | 0.001462 | 5.0 | 22.0 | 10.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-observe-describe@dark` | 0.006968 | 0.007176 | 5.0 | 9.0 | 9.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-observe-describe@light` | 0.135185 | 0.151902 | 5.0 | 22.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-opposite-action@dark` | 0.165276 | 0.16526 | 5.0 | 22.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-opposite-action@light` | 0.167197 | 0.163547 | 5.0 | 21.0 | 21.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-participate@dark` | 0.002132 | 0.006994 | 5.0 | 9.0 | 9.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-participate@light` | 0.134575 | 0.000727 | 5.0 | 22.0 | 8.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-please@dark` | 0.007866 | 0.000415 | 5.0 | 9.0 | 9.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-please@light` | 0.149554 | 0.149498 | 5.0 | 22.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-problem-solving@dark` | 0.158049 | 0.158118 | 5.0 | 22.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-problem-solving@light` | 0.143782 | 0.143806 | 5.0 | 22.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-radical-acceptance@dark` | 0.007509 | 0.00804 | 5.0 | 9.0 | 10.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-radical-acceptance@light` | 2.318858 | 2.31986 | 5.0 | 204.0 | 204.0 | 316.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-self-soothe@dark` | 8.3e-05 | 0.000137 | 5.0 | 1.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-self-soothe@light` | 0.018097 | 0.020521 | 5.0 | 10.0 | 10.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-stop@dark` | 0.007238 | 0.001023 | 5.0 | 9.0 | 9.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-stop@light` | 0.000136 | 0.000142 | 5.0 | 1.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-tipp@dark` | 1.700624 | 0.008671 | 5.0 | 207.0 | 9.0 | 320.5 | statistical_5x5_p95 |
| PASS | NO_DELTA | `suite:dbt-practice-tipp@light` | 0.15519 | 0.019711 | 5.0 | 21.0 | 10.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-validation-limits@dark` | 0.164347 | 0.00528 | 5.0 | 20.0 | 9.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-validation-limits@light` | 2e-06 | 0.148905 | 5.0 | 1.0 | 21.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-wise-mind@dark` | 0.0071 | 0.156878 | 5.0 | 9.0 | 20.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-wise-mind@light` | 0.142885 | 0.142818 | 5.0 | 21.0 | 21.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:home-no-score@dark` | 0.000197 | 0.00019 | 5.0 | 17.0 | 17.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:home-no-score@light` | 3e-06 | 0.000127 | 5.0 | 2.0 | 19.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:home@dark` | 0.000333 | 0.000168 | 5.0 | 17.0 | 17.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:home@light` | 0.003418 | 0.003573 | 5.0 | 19.0 | 35.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:onboarding-error@dark` | 5.6e-05 | 5.4e-05 | 5.0 | 4.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:onboarding-error@light` | 1.6e-05 | 1.8e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:onboarding@dark` | 3.8e-05 | 5.4e-05 | 5.0 | 2.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:onboarding@light` | 0.0 | 0.000151 | 5.0 | 0.0 | 12.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:recuperar-acceso@dark` | 3.7e-05 | 3.7e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:recuperar-acceso@light` | 0.0 | 2e-06 | 5.0 | 0.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step1-emotion-otro@dark` | 0.0 | 0.000104 | 5.0 | 0.0 | 18.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step1-emotion-otro@light` | 8.3e-05 | 7.6e-05 | 5.0 | 15.0 | 15.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step1-emotion@dark` | 1.1e-05 | 0.0001 | 5.0 | 1.0 | 18.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step1-emotion@light` | 7.9e-05 | 7.8e-05 | 5.0 | 15.0 | 14.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step2-distortions@dark` | 1e-05 | 2.1e-05 | 5.0 | 1.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step2-distortions@light` | 9e-05 | 2.2e-05 | 5.0 | 14.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step3-filled@dark` | 1.3e-05 | 9.4e-05 | 5.0 | 1.0 | 18.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step3-filled@light` | 1.6e-05 | 7.8e-05 | 5.0 | 3.0 | 14.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-success@dark` | 0.000102 | 1.1e-05 | 5.0 | 18.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-success@light` | 0.0 | 7.8e-05 | 5.0 | 0.0 | 14.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro@dark` | 9.3e-05 | 1e-06 | 5.0 | 18.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro@light` | 1.6e-05 | 7.8e-05 | 5.0 | 3.0 | 14.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-paused@dark` | 4.7e-05 | 9e-05 | 5.0 | 3.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-paused@light` | 0.000121 | 0.00011 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-running@dark` | 0.000102 | 0.0 | 5.0 | 3.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-running@light` | 5.2e-05 | 1.1e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion@dark` | 1.4e-05 | 8.2e-05 | 5.0 | 3.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion@light` | 6.4e-05 | 4.7e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-add-task@dark` | 0.000106 | 0.000218 | 5.0 | 11.0 | 19.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-add-task@light` | 0.000299 | 0.000329 | 5.0 | 25.0 | 25.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-all-completed@dark` | 0.000867 | 0.000968 | 5.0 | 39.0 | 39.0 | 68.5 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-all-completed@light` | 0.001311 | 0.001198 | 5.0 | 25.0 | 25.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-empty@dark` | 0.003214 | 0.0 | 5.0 | 40.0 | 0.0 | 70.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-empty@light` | 1.4e-05 | 0.000139 | 5.0 | 2.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina@dark` | 0.000201 | 0.000222 | 5.0 | 19.0 | 19.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina@light` | 0.00024 | 4e-05 | 5.0 | 18.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-empty@dark` | 0.002215 | 0.002205 | 5.0 | 41.0 | 41.0 | 71.5 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-empty@light` | 8e-05 | 8e-05 | 5.0 | 3.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-paused@dark` | 8e-06 | 8e-06 | 5.0 | 4.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-paused@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-running@dark` | 1.9e-05 | 0.0 | 5.0 | 3.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-running@light` | 1.9e-05 | 9e-06 | 5.0 | 2.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer@dark` | 8e-06 | 2.5e-05 | 5.0 | 4.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer@light` | 2.8e-05 | 0.0 | 5.0 | 3.0 | 0.0 | 50.0 | single_1x1 |
