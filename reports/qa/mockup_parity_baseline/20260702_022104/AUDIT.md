# Mockup HTML parity baseline audit

- Generated: 2026-07-02T02:35:52
- Original HTML: `C:\Users\nosom\Desktop\nm_suite\reports\qa\mockup_parity_baseline\20260702_022104\sources\original_HEAD.html`
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
- Normalized diff: `C:\Users\nosom\Desktop\nm_suite\reports\qa\mockup_parity_baseline\20260702_022104\TEXT_DIFF_NORMALIZED.patch`
- EOL report: `C:\Users\nosom\Desktop\nm_suite\reports\qa\mockup_parity_baseline\20260702_022104\EOL_DELTA.txt`

## Summary

- Total captures: 116 / expected 116
- PASS: 112
- FAIL: 4
- EXPECTED_DELTA: 0
- EXPECTED_DELTA allowlist: `{'hub:detalle-resumen-ia-0@light': {'old_resolution': '720x462', 'new_resolution': '960x600', 'reason': 'canonical AI summary modal window_overlay redesign'}, 'hub:detalle-resumen-ia-0@dark': {'old_resolution': '720x462', 'new_resolution': '960x600', 'reason': 'canonical AI summary modal window_overlay redesign'}}`
- EOL-only delta: YES
- Statistical escalations: 5
- Modal/actioned captures: 34
- Surfaces: `{'window': 76, 'narrow': 6, 'modal': 0, 'window_modal': 34}`

## Results

| Status | Delta | Key | Base mean | Mod mean | Mean limit | Base max | Mod max | Max limit | Mode |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| FAIL | UNEXPECTED_DELTA | `suite:dbt-practice-give@light` | 0.134674 | 1.173115 | 5.0 | 22.0 | 113.0 | 50.0 | statistical_2x2_p95 |
| FAIL | UNEXPECTED_DELTA | `suite:dbt-practice-opposite-action@dark` | 0.1647 | 0.995484 | 5.0 | 22.0 | 114.5 | 50.0 | statistical_2x2_p95 |
| FAIL | UNEXPECTED_DELTA | `suite:dbt-practice-participate@dark` | 0.15534 | 0.853432 | 5.0 | 22.0 | 114.5 | 50.0 | statistical_2x2_p95 |
| FAIL | UNEXPECTED_DELTA | `suite:dbt-practice-radical-acceptance@light` | 0.15908 | 2.35644 | 5.0 | 22.0 | 204.0 | 50.0 | statistical_2x2_p95 |
| PASS | NO_DELTA | `hub:detalle-plan-activacion@dark` | 21.336755 | 21.336755 | 33.005132 | 241.0 | 241.0 | 371.5 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-activacion@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-rutina@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-rutina@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-timer@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-plan-timer@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-resumen-ia-0@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-resumen-ia-0@light` | 5.831051 | 2.963464 | 9.746576 | 219.0 | 119.5 | 338.5 | statistical_2x2_p95 |
| PASS | NO_DELTA | `hub:detalle@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:pacientes-empty@dark` | 0.00177 | 0.00173 | 5.0 | 40.0 | 40.0 | 70.0 | single_1x1 |
| PASS | NO_DELTA | `hub:pacientes-empty@light` | 9.5e-05 | 0.000174 | 5.0 | 5.0 | 12.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:pacientes@dark` | 0.000266 | 0.002969 | 5.0 | 37.0 | 65.0 | 65.5 | single_1x1 |
| PASS | NO_DELTA | `hub:pacientes@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:textos-globales@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:textos-globales@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-empty@dark` | 0.000668 | 0.00015 | 5.0 | 41.0 | 41.0 | 71.5 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-empty@light` | 0.0 | 0.00075 | 5.0 | 0.0 | 44.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-filtered@dark` | 2.5e-05 | 0.0 | 5.0 | 5.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-filtered@light` | 0.000131 | 1.6e-05 | 5.0 | 30.0 | 4.0 | 55.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-marked-hice@dark` | 8e-06 | 3.1e-05 | 5.0 | 1.0 | 5.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-marked-hice@light` | 0.00016 | 1.6e-05 | 5.0 | 30.0 | 4.0 | 55.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades@dark` | 3.5e-05 | 6e-06 | 5.0 | 10.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades@light` | 8e-06 | 7e-06 | 5.0 | 1.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:animo@dark` | 0.00109 | 0.000914 | 5.0 | 49.0 | 49.0 | 83.5 | single_1x1 |
| PASS | NO_DELTA | `suite:animo@light` | 0.0 | 0.00024 | 5.0 | 0.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-empty@dark` | 0.002557 | 0.002534 | 5.0 | 42.0 | 40.0 | 73.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-empty@light` | 9.3e-05 | 0.003797 | 5.0 | 5.0 | 46.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-filter-activos@dark` | 2.9e-05 | 0.0 | 5.0 | 3.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-filter-activos@light` | 2.5e-05 | 0.0 | 5.0 | 2.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-search@dark` | 7.6e-05 | 3.8e-05 | 5.0 | 17.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-search@light` | 0.000922 | 0.0 | 5.0 | 22.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-today@dark` | 5.5e-05 | 2.9e-05 | 5.0 | 3.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-today@light` | 1e-06 | 0.0 | 5.0 | 1.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos@dark` | 0.000486 | 2.6e-05 | 5.0 | 50.0 | 2.0 | 85.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos@light` | 0.000115 | 8.2e-05 | 5.0 | 17.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-library@dark` | 0.001342 | 0.001351 | 5.0 | 34.0 | 34.0 | 61.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-library@light` | 0.001785 | 0.002781 | 5.0 | 37.0 | 38.0 | 65.5 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-now@dark` | 2.1e-05 | 1.4e-05 | 5.0 | 2.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-now@light` | 2.8e-05 | 3e-05 | 5.0 | 3.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-check-facts@dark` | 1.714899 | 0.008334 | 5.0 | 207.0 | 9.0 | 320.5 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-check-facts@light` | 0.158522 | 0.15851 | 5.0 | 22.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-dear-man@dark` | 1.876565 | 1.735923 | 5.0 | 211.0 | 207.0 | 326.5 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-dear-man@light` | 6.8e-05 | 3.5e-05 | 5.0 | 1.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-fast@dark` | 1.547938 | 1.54791 | 5.0 | 207.0 | 207.0 | 320.5 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-fast@light` | 2.294879 | 2.294893 | 5.0 | 204.0 | 204.0 | 316.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-give@dark` | 0.000403 | 0.006904 | 5.0 | 6.0 | 9.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-non-judgmental@dark` | 0.000102 | 0.14628 | 5.0 | 1.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-non-judgmental@light` | 0.147333 | 0.147626 | 5.0 | 22.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-observe-describe@dark` | 0.157994 | 0.157681 | 5.0 | 20.0 | 20.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-observe-describe@light` | 0.01713 | 0.001212 | 5.0 | 10.0 | 9.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-opposite-action@light` | 0.003234 | 0.150406 | 5.0 | 10.0 | 21.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-participate@light` | 0.000108 | 0.134556 | 5.0 | 1.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-please@dark` | 0.164127 | 0.000359 | 5.0 | 20.0 | 9.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-please@light` | 0.14891 | 0.000216 | 5.0 | 22.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-problem-solving@dark` | 1.749016 | 1.748512 | 5.0 | 207.0 | 207.0 | 320.5 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-problem-solving@light` | 0.00086 | 0.143153 | 5.0 | 10.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-radical-acceptance@dark` | 3.3e-05 | 8.4e-05 | 5.0 | 1.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-self-soothe@dark` | 0.155737 | 0.005407 | 5.0 | 20.0 | 9.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-self-soothe@light` | 2.329729 | 0.153086 | 5.0 | 204.0 | 21.0 | 316.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-stop@dark` | 0.148805 | 0.149578 | 5.0 | 22.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-stop@light` | 0.151585 | 0.151512 | 5.0 | 21.0 | 21.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-tipp@dark` | 0.152796 | 0.15276 | 5.0 | 22.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-tipp@light` | 0.137547 | 0.021488 | 5.0 | 21.0 | 10.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-validation-limits@dark` | 1.782405 | 0.171721 | 5.0 | 206.0 | 20.0 | 319.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-validation-limits@light` | 2.53111 | 0.00017 | 5.0 | 204.0 | 1.0 | 316.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-wise-mind@dark` | 0.161943 | 0.1564 | 5.0 | 20.0 | 20.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-wise-mind@light` | 0.000189 | 0.000194 | 5.0 | 1.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:home-no-score@dark` | 0.000139 | 0.000169 | 5.0 | 17.0 | 17.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:home-no-score@light` | 8.2e-05 | 0.000162 | 5.0 | 4.0 | 19.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:home@dark` | 8.9e-05 | 0.003264 | 5.0 | 9.0 | 41.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:home@light` | 0.000339 | 0.003597 | 5.0 | 35.0 | 35.0 | 62.5 | single_1x1 |
| PASS | NO_DELTA | `suite:onboarding-error@dark` | 0.000165 | 1.3e-05 | 5.0 | 18.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:onboarding-error@light` | 0.0 | 1.8e-05 | 5.0 | 0.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:onboarding@dark` | 0.000175 | 0.0 | 5.0 | 18.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:onboarding@light` | 0.000142 | 0.000136 | 5.0 | 12.0 | 13.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:recuperar-acceso@dark` | 5.6e-05 | 5.4e-05 | 5.0 | 4.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:recuperar-acceso@light` | 1.8e-05 | 1.8e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step1-emotion-otro@dark` | 9.3e-05 | 0.0 | 5.0 | 18.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step1-emotion-otro@light` | 3e-06 | 3e-06 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step1-emotion@dark` | 0.000104 | 1.6e-05 | 5.0 | 18.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step1-emotion@light` | 8.1e-05 | 8.2e-05 | 5.0 | 14.0 | 14.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step2-distortions@dark` | 9.3e-05 | 9.9e-05 | 5.0 | 18.0 | 18.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step2-distortions@light` | 8.2e-05 | 8.2e-05 | 5.0 | 14.0 | 14.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step3-filled@dark` | 0.000101 | 1.2e-05 | 5.0 | 18.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step3-filled@light` | 0.0 | 3e-06 | 5.0 | 0.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-success@dark` | 9.7e-05 | 9.7e-05 | 5.0 | 18.0 | 18.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-success@light` | 8.4e-05 | 0.0 | 5.0 | 14.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro@dark` | 9.7e-05 | 0.0 | 5.0 | 18.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro@light` | 8.2e-05 | 8.2e-05 | 5.0 | 14.0 | 14.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-paused@dark` | 4.5e-05 | 0.000134 | 5.0 | 3.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-paused@light` | 0.000108 | 0.000148 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-running@dark` | 3e-05 | 9.3e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-running@light` | 3.1e-05 | 1.4e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion@dark` | 6.2e-05 | 9.6e-05 | 5.0 | 3.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion@light` | 7.1e-05 | 3.4e-05 | 5.0 | 2.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-add-task@dark` | 9.5e-05 | 8.4e-05 | 5.0 | 5.0 | 5.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-add-task@light` | 0.000564 | 0.000417 | 5.0 | 26.0 | 26.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-all-completed@dark` | 0.000424 | 0.000527 | 5.0 | 38.0 | 19.0 | 67.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-all-completed@light` | 0.002679 | 0.002333 | 5.0 | 44.0 | 28.0 | 76.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-empty@dark` | 0.000847 | 0.003161 | 5.0 | 40.0 | 40.0 | 70.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-empty@light` | 0.0 | 0.004728 | 5.0 | 0.0 | 44.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina@dark` | 0.000202 | 0.000206 | 5.0 | 19.0 | 19.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina@light` | 8e-05 | 0.000291 | 5.0 | 13.0 | 25.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-empty@dark` | 0.00223 | 0.0 | 5.0 | 41.0 | 0.0 | 71.5 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-empty@light` | 8e-05 | 0.003242 | 5.0 | 3.0 | 46.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-paused@dark` | 2e-06 | 8e-06 | 5.0 | 1.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-paused@light` | 0.0 | 9e-06 | 5.0 | 0.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-running@dark` | 8e-06 | 1.9e-05 | 5.0 | 4.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-running@light` | 2.8e-05 | 1.9e-05 | 5.0 | 3.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer@dark` | 0.0 | 8e-06 | 5.0 | 0.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer@light` | 1.9e-05 | 2.8e-05 | 5.0 | 2.0 | 3.0 | 50.0 | single_1x1 |

## FAIL Details

- `suite:dbt-practice-participate@dark`: dynamic_baseline_exceeded_after_statistical_escalation (mode `statistical_2x2_p95`)
- `suite:dbt-practice-radical-acceptance@light`: dynamic_baseline_exceeded_after_statistical_escalation (mode `statistical_2x2_p95`)
- `suite:dbt-practice-opposite-action@dark`: dynamic_baseline_exceeded_after_statistical_escalation (mode `statistical_2x2_p95`)
- `suite:dbt-practice-give@light`: dynamic_baseline_exceeded_after_statistical_escalation (mode `statistical_2x2_p95`)
