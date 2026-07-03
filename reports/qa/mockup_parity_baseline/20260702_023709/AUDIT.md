# Mockup HTML parity baseline audit

- Generated: 2026-07-02T02:44:37
- Original HTML: `C:\Users\nosom\Desktop\nm_suite\reports\qa\mockup_parity_baseline\20260702_023709\sources\original_HEAD.html`
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
- Normalized diff: `C:\Users\nosom\Desktop\nm_suite\reports\qa\mockup_parity_baseline\20260702_023709\TEXT_DIFF_NORMALIZED.patch`
- EOL report: `C:\Users\nosom\Desktop\nm_suite\reports\qa\mockup_parity_baseline\20260702_023709\EOL_DELTA.txt`

## Summary

- Total captures: 116 / expected 116
- PASS: 116
- FAIL: 0
- EXPECTED_DELTA: 0
- EXPECTED_DELTA allowlist: `{'hub:detalle-resumen-ia-0@light': {'old_resolution': '720x462', 'new_resolution': '960x600', 'reason': 'canonical AI summary modal window_overlay redesign'}, 'hub:detalle-resumen-ia-0@dark': {'old_resolution': '720x462', 'new_resolution': '960x600', 'reason': 'canonical AI summary modal window_overlay redesign'}}`
- EOL-only delta: YES
- EOL-only max outliers accepted: 0
- Statistical escalations: 0
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
| PASS | NO_DELTA | `hub:detalle-resumen-ia-0@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle-resumen-ia-0@light` | 0.929769 | 0.0 | 5.0 | 166.0 | 0.0 | 259.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:detalle@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:pacientes-empty@dark` | 0.001763 | 2e-05 | 5.0 | 40.0 | 2.0 | 70.0 | single_1x1 |
| PASS | NO_DELTA | `hub:pacientes-empty@light` | 0.002593 | 0.002593 | 5.0 | 47.0 | 47.0 | 80.5 | single_1x1 |
| PASS | NO_DELTA | `hub:pacientes@dark` | 0.005345 | 0.002185 | 5.0 | 65.0 | 65.0 | 107.5 | single_1x1 |
| PASS | NO_DELTA | `hub:pacientes@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:textos-globales@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `hub:textos-globales@light` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-empty@dark` | 0.000196 | 0.000196 | 5.0 | 41.0 | 41.0 | 71.5 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-empty@light` | 0.000194 | 0.000194 | 5.0 | 30.0 | 30.0 | 55.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-filtered@dark` | 5.5e-05 | 0.000201 | 5.0 | 22.0 | 44.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-filtered@light` | 2.4e-05 | 0.000131 | 5.0 | 4.0 | 33.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-marked-hice@dark` | 0.000189 | 5.8e-05 | 5.0 | 42.0 | 10.0 | 73.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades-marked-hice@light` | 5.6e-05 | 2.4e-05 | 5.0 | 8.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades@dark` | 0.000199 | 0.000163 | 5.0 | 42.0 | 42.0 | 73.0 | single_1x1 |
| PASS | NO_DELTA | `suite:actividades@light` | 0.0 | 0.00013 | 5.0 | 0.0 | 33.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:animo@dark` | 0.000186 | 2.3e-05 | 5.0 | 1.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:animo@light` | 6e-06 | 6e-06 | 5.0 | 1.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-empty@dark` | 8.2e-05 | 0.002557 | 5.0 | 5.0 | 42.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-empty@light` | 0.003796 | 0.003737 | 5.0 | 46.0 | 45.0 | 79.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-filter-activos@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-filter-activos@light` | 6.2e-05 | 2.5e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-search@dark` | 3.1e-05 | 4.7e-05 | 5.0 | 17.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-search@light` | 7.8e-05 | 0.00096 | 5.0 | 17.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-today@dark` | 2.6e-05 | 2.6e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos-today@light` | 6.1e-05 | 6.1e-05 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos@dark` | 7.3e-05 | 2.9e-05 | 5.0 | 4.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:avisos@light` | 2.8e-05 | 8.2e-05 | 5.0 | 2.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-library@dark` | 0.002493 | 0.001691 | 5.0 | 34.0 | 34.0 | 61.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-library@light` | 0.002693 | 0.002651 | 5.0 | 38.0 | 38.0 | 67.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-now@dark` | 1e-05 | 3e-06 | 5.0 | 4.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-now@light` | 3.5e-05 | 2e-06 | 5.0 | 3.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-check-facts@dark` | 8e-05 | 0.000104 | 5.0 | 1.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-check-facts@light` | 0.000762 | 0.141742 | 5.0 | 4.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-dear-man@dark` | 0.158763 | 8.9e-05 | 5.0 | 20.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-dear-man@light` | 0.160526 | 0.160556 | 5.0 | 21.0 | 21.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-fast@dark` | 0.001796 | 0.000393 | 5.0 | 9.0 | 9.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-fast@light` | 0.131914 | 0.002667 | 5.0 | 22.0 | 10.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-give@dark` | 0.156233 | 0.0076 | 5.0 | 20.0 | 9.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-give@light` | 2.310905 | 2.310926 | 5.0 | 204.0 | 204.0 | 316.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-non-judgmental@dark` | 0.002048 | 0.151173 | 5.0 | 9.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-non-judgmental@light` | 0.002299 | 0.018217 | 5.0 | 10.0 | 10.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-observe-describe@dark` | 0.157017 | 0.007178 | 5.0 | 20.0 | 9.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-observe-describe@light` | 0.135159 | 0.135865 | 5.0 | 22.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-opposite-action@dark` | 0.000205 | 0.172852 | 5.0 | 9.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-opposite-action@light` | 0.001129 | 0.017488 | 5.0 | 10.0 | 10.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-participate@dark` | 0.156229 | 0.008073 | 5.0 | 22.0 | 9.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-participate@light` | 0.000106 | 0.151283 | 5.0 | 1.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-please@dark` | 0.008068 | 0.172065 | 5.0 | 9.0 | 20.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-please@light` | 0.16591 | 0.165976 | 5.0 | 22.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-problem-solving@dark` | 8.3e-05 | 8.9e-05 | 5.0 | 1.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-problem-solving@light` | 0.143872 | 0.143841 | 5.0 | 22.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-radical-acceptance@dark` | 0.163821 | 3.3e-05 | 5.0 | 20.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-radical-acceptance@light` | 0.000209 | 0.158841 | 5.0 | 1.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-self-soothe@dark` | 0.158887 | 0.008329 | 5.0 | 20.0 | 10.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-self-soothe@light` | 0.153072 | 0.003958 | 5.0 | 21.0 | 10.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-stop@dark` | 0.001951 | 0.156655 | 5.0 | 4.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-stop@light` | 6.7e-05 | 0.000117 | 5.0 | 1.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-tipp@dark` | 0.002129 | 0.158264 | 5.0 | 9.0 | 22.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-tipp@light` | 0.000477 | 0.019549 | 5.0 | 8.0 | 10.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-validation-limits@dark` | 0.008302 | 0.000231 | 5.0 | 9.0 | 9.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-validation-limits@light` | 0.165501 | 0.000134 | 5.0 | 21.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-wise-mind@dark` | 0.004975 | 0.161947 | 5.0 | 9.0 | 20.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:dbt-practice-wise-mind@light` | 0.142019 | 0.000188 | 5.0 | 21.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:home-no-score@dark` | 1.4e-05 | 8.3e-05 | 5.0 | 3.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:home-no-score@light` | 0.000148 | 4.1e-05 | 5.0 | 19.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:home@dark` | 0.003198 | 0.000287 | 5.0 | 17.0 | 41.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:home@light` | 7.5e-05 | 0.000425 | 5.0 | 3.0 | 35.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:onboarding-error@dark` | 0.000174 | 0.000174 | 5.0 | 18.0 | 18.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:onboarding-error@light` | 1.6e-05 | 0.0 | 5.0 | 2.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:onboarding@dark` | 2.5e-05 | 0.0 | 5.0 | 4.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:onboarding@light` | 1.5e-05 | 0.000146 | 5.0 | 1.0 | 13.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:recuperar-acceso@dark` | 5.4e-05 | 1.7e-05 | 5.0 | 4.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:recuperar-acceso@light` | 0.0 | 1.8e-05 | 5.0 | 0.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step1-emotion-otro@dark` | 9.7e-05 | 0.0001 | 5.0 | 18.0 | 18.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step1-emotion-otro@light` | 8.2e-05 | 8.1e-05 | 5.0 | 14.0 | 14.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step1-emotion@dark` | 0.000101 | 9.9e-05 | 5.0 | 18.0 | 18.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step1-emotion@light` | 1.6e-05 | 7.9e-05 | 5.0 | 3.0 | 15.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step2-distortions@dark` | 0.00011 | 9.7e-05 | 5.0 | 18.0 | 18.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step2-distortions@light` | 1.8e-05 | 9.2e-05 | 5.0 | 3.0 | 15.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step3-filled@dark` | 0.0 | 9.7e-05 | 5.0 | 0.0 | 18.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-step3-filled@light` | 1.3e-05 | 3e-06 | 5.0 | 2.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-success@dark` | 2e-05 | 3e-06 | 5.0 | 4.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro-success@light` | 4e-06 | 9e-05 | 5.0 | 2.0 | 15.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro@dark` | 1.6e-05 | 3e-06 | 5.0 | 4.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:registro@light` | 8.2e-05 | 8.1e-05 | 5.0 | 14.0 | 14.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-paused@dark` | 7e-05 | 2.1e-05 | 5.0 | 2.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-paused@light` | 6e-06 | 6e-06 | 5.0 | 1.0 | 1.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-running@dark` | 4e-06 | 0.000102 | 5.0 | 1.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion-running@light` | 1.6e-05 | 0.0001 | 5.0 | 1.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion@dark` | 4.4e-05 | 3.4e-05 | 5.0 | 3.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:respiracion@light` | 1e-06 | 0.000114 | 5.0 | 1.0 | 2.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-add-task@dark` | 0.000247 | 8.2e-05 | 5.0 | 19.0 | 5.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-add-task@light` | 0.000943 | 0.000228 | 5.0 | 26.0 | 5.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-all-completed@dark` | 0.000317 | 0.000635 | 5.0 | 16.0 | 39.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-all-completed@light` | 0.00052 | 0.000441 | 5.0 | 18.0 | 18.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-empty@dark` | 0.003214 | 0.003214 | 5.0 | 40.0 | 40.0 | 70.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina-empty@light` | 0.004733 | 0.00463 | 5.0 | 44.0 | 44.0 | 76.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina@dark` | 0.000898 | 0.000688 | 5.0 | 24.0 | 24.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:rutina@light` | 2e-06 | 0.000303 | 5.0 | 1.0 | 18.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-empty@dark` | 7.5e-05 | 0.002176 | 5.0 | 3.0 | 41.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-empty@light` | 0.003284 | 1.9e-05 | 5.0 | 45.0 | 2.0 | 77.5 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-paused@dark` | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-paused@light` | 2.8e-05 | 9e-06 | 5.0 | 3.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-running@dark` | 0.0 | 8e-06 | 5.0 | 0.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer-running@light` | 1.9e-05 | 2.8e-05 | 5.0 | 2.0 | 3.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer@dark` | 1e-05 | 2.5e-05 | 5.0 | 4.0 | 4.0 | 50.0 | single_1x1 |
| PASS | NO_DELTA | `suite:timer@light` | 2.8e-05 | 1e-06 | 5.0 | 3.0 | 1.0 | 50.0 | single_1x1 |
