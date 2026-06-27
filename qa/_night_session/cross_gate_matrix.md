# Cross-Gate Matrix: odiff vs VAS

**Total surfaces:** 86

## Summary

| Category | Count | Description |
|----------|-------|-------------|
| A | 43 | odiff PASS + VAS PASS |
| B | 40 | odiff PASS + VAS FAIL ← CRITICAL |
| C | 1 | odiff FAIL + VAS PASS |
| D | 2 | odiff FAIL + VAS FAIL |
| E | 0 | missing / skipped |

## Full Matrix

| Surface | Cat | odiff | diff% | VAS pass | VAS fail | Classification |
|---------|-----|-------|-------|----------|----------|----------------|
| hub:detalle-plan-activacion@dark | **A** | PASS | 5.97 | 4 | 0 | — |
| hub:detalle-plan-activacion@light | **A** | PASS | 5.97 | 4 | 0 | — |
| hub:detalle-plan-rutina@dark | **A** | PASS | 5.08 | 4 | 0 | — |
| hub:detalle-plan-rutina@light | **A** | PASS | 4.89 | 4 | 0 | — |
| hub:detalle-plan-timer@dark | **A** | PASS | 5.86 | 4 | 0 | — |
| hub:detalle-plan-timer@light | **A** | PASS | 5.78 | 4 | 0 | — |
| hub:detalle-resumen-ia-0@dark | **C** | FAIL | 9.18 | 4 | 0 | — |
| hub:detalle-resumen-ia-0@light | **D** | FAIL | 8.55 | 3 | 1 | — |
| hub:detalle@dark | **A** | PASS | 5.97 | 4 | 0 | — |
| hub:detalle@light | **A** | PASS | 5.87 | 4 | 0 | — |
| hub:pacientes-empty@dark | **A** | PASS | 1.17 | 4 | 0 | — |
| hub:pacientes-empty@light | **B** | PASS | 1.07 | 5 | 1 | color/shadow theme |
| hub:pacientes@dark | **B** | PASS | 4.72 | 5 | 2 | color/shadow theme |
| hub:pacientes@light | **A** | PASS | 4.50 | 4 | 0 | — |
| hub:textos-globales@dark | **B** | PASS | 2.37 | 3 | 1 | detector_noise_probable |
| hub:textos-globales@light | **A** | PASS | 1.95 | 4 | 0 | — |
| suite:actividades-empty@dark | **A** | PASS | 0.88 | 3 | 0 | — |
| suite:actividades-empty@light | **B** | PASS | 0.82 | 5 | 1 | color/shadow theme |
| suite:actividades-filtered@dark | **B** | PASS | 1.68 | 5 | 2 | color/shadow theme |
| suite:actividades-filtered@light | **B** | PASS | 1.58 | 5 | 2 | color/shadow theme |
| suite:actividades-marked-hice@dark | **B** | PASS | 2.67 | 4 | 3 | color/shadow theme |
| suite:actividades-marked-hice@light | **B** | PASS | 2.47 | 5 | 2 | color/shadow theme |
| suite:actividades@dark | **B** | PASS | 2.70 | 4 | 3 | color/shadow theme |
| suite:actividades@light | **B** | PASS | 2.47 | 5 | 2 | color/shadow theme |
| suite:animo@dark | **B** | PASS | 3.01 | 5 | 1 | color/shadow theme |
| suite:animo@light | **B** | PASS | 4.63 | 6 | 1 | color/shadow theme |
| suite:avisos-empty@dark | **A** | PASS | 0.94 | 3 | 0 | — |
| suite:avisos-empty@light | **B** | PASS | 0.83 | 4 | 2 | color/shadow theme |
| suite:avisos-filter-activos@dark | **B** | PASS | 1.94 | 5 | 3 | color/shadow theme |
| suite:avisos-filter-activos@light | **B** | PASS | 1.82 | 5 | 2 | color/shadow theme |
| suite:avisos-search@dark | **B** | PASS | 1.08 | 4 | 2 | color/shadow theme |
| suite:avisos-search@light | **B** | PASS | 0.96 | 4 | 2 | color/shadow theme |
| suite:avisos-today@dark | **B** | PASS | 1.99 | 5 | 3 | color/shadow theme |
| suite:avisos-today@light | **B** | PASS | 1.88 | 5 | 2 | color/shadow theme |
| suite:avisos@dark | **B** | PASS | 2.20 | 5 | 3 | color/shadow theme |
| suite:avisos@light | **B** | PASS | 2.05 | 5 | 2 | color/shadow theme |
| suite:dbt-library@dark | **A** | PASS | 3.33 | 4 | 0 | — |
| suite:dbt-library@light | **A** | PASS | 3.19 | 4 | 0 | — |
| suite:dbt-now@dark | **B** | PASS | 2.15 | 5 | 3 | color/shadow theme |
| suite:dbt-now@light | **B** | PASS | 1.88 | 5 | 2 | color/shadow theme |
| suite:dbt-practice-stop@dark | **B** | PASS | 3.27 | 3 | 1 | detector_noise_probable |
| suite:dbt-practice-stop@light | **D** | FAIL | 55.93 | 3 | 1 | — |
| suite:home-no-score@dark | **B** | PASS | 3.84 | 5 | 3 | color/shadow theme |
| suite:home-no-score@light | **B** | PASS | 3.59 | 5 | 2 | color/shadow theme |
| suite:home@dark | **B** | PASS | 4.79 | 5 | 3 | color/shadow theme |
| suite:home@light | **B** | PASS | 4.54 | 5 | 2 | color/shadow theme |
| suite:onboarding-error@dark | **A** | PASS | 5.89 | 4 | 0 | — |
| suite:onboarding-error@light | **A** | PASS | 6.39 | 4 | 0 | — |
| suite:onboarding@dark | **A** | PASS | 5.41 | 4 | 0 | — |
| suite:onboarding@light | **A** | PASS | 5.61 | 4 | 0 | — |
| suite:recuperar-acceso@dark | **A** | PASS | 5.57 | 4 | 0 | — |
| suite:recuperar-acceso@light | **A** | PASS | 5.92 | 4 | 0 | — |
| suite:registro-step1-emotion-otro@dark | **A** | PASS | 3.99 | 4 | 0 | — |
| suite:registro-step1-emotion-otro@light | **A** | PASS | 3.95 | 4 | 0 | — |
| suite:registro-step1-emotion@dark | **B** | PASS | 4.20 | 6 | 1 | estructural_confirmada |
| suite:registro-step1-emotion@light | **B** | PASS | 4.15 | 5 | 2 | estructural_confirmada |
| suite:registro-step2-distortions@dark | **A** | PASS | 3.38 | 4 | 0 | — |
| suite:registro-step2-distortions@light | **A** | PASS | 3.13 | 4 | 0 | — |
| suite:registro-step3-filled@dark | **A** | PASS | 3.32 | 4 | 0 | — |
| suite:registro-step3-filled@light | **A** | PASS | 3.27 | 4 | 0 | — |
| suite:registro-success@dark | **B** | PASS | 2.16 | 5 | 1 | color/shadow theme |
| suite:registro-success@light | **B** | PASS | 2.48 | 4 | 2 | color/shadow theme |
| suite:registro@dark | **A** | PASS | 2.14 | 4 | 0 | — |
| suite:registro@light | **A** | PASS | 2.15 | 4 | 0 | — |
| suite:respiracion-paused@dark | **A** | PASS | 1.55 | 4 | 0 | — |
| suite:respiracion-paused@light | **A** | PASS | 1.46 | 4 | 0 | — |
| suite:respiracion-running@dark | **A** | PASS | 1.56 | 4 | 0 | — |
| suite:respiracion-running@light | **A** | PASS | 1.46 | 4 | 0 | — |
| suite:respiracion@dark | **A** | PASS | 1.56 | 4 | 0 | — |
| suite:respiracion@light | **A** | PASS | 1.47 | 4 | 0 | — |
| suite:rutina-add-task@dark | **B** | PASS | 2.80 | 5 | 2 | color/shadow theme |
| suite:rutina-add-task@light | **B** | PASS | 2.73 | 4 | 1 | color/shadow theme |
| suite:rutina-all-completed@dark | **B** | PASS | 3.21 | 5 | 1 | color/shadow theme |
| suite:rutina-all-completed@light | **B** | PASS | 3.24 | 5 | 2 | color/shadow theme |
| suite:rutina-empty@dark | **A** | PASS | 0.96 | 4 | 0 | — |
| suite:rutina-empty@light | **B** | PASS | 0.86 | 5 | 1 | color/shadow theme |
| suite:rutina@dark | **B** | PASS | 2.51 | 5 | 2 | color/shadow theme |
| suite:rutina@light | **B** | PASS | 2.45 | 4 | 1 | color/shadow theme |
| suite:timer-empty@dark | **A** | PASS | 1.28 | 3 | 0 | — |
| suite:timer-empty@light | **B** | PASS | 1.06 | 5 | 1 | color/shadow theme |
| suite:timer-paused@dark | **A** | PASS | 2.10 | 3 | 0 | — |
| suite:timer-paused@light | **A** | PASS | 2.03 | 4 | 0 | — |
| suite:timer-running@dark | **A** | PASS | 2.11 | 3 | 0 | — |
| suite:timer-running@light | **A** | PASS | 2.01 | 4 | 0 | — |
| suite:timer@dark | **A** | PASS | 2.08 | 3 | 0 | — |
| suite:timer@light | **A** | PASS | 2.00 | 4 | 0 | — |

## Category B — odiff PASS + VAS FAIL (critical zone)

Total: **40** surfaces

| # | Surface | diff% | VAS fail | Classification | Divergences |
|---|---------|-------|----------|----------------|-------------|
| 1 | suite:avisos-filter-activos@dark | 1.94 | 3 | color/shadow theme | SHADOW_MISMATCH(effects,Δ=?); COLOR_MISMATCH(card_group,Δ=21.1); COLOR_MISMATCH(icons,Δ=45.4) |
| 2 | suite:avisos-today@dark | 1.99 | 3 | color/shadow theme | SHADOW_MISMATCH(effects,Δ=?); COLOR_MISMATCH(card_group,Δ=21.1); COLOR_MISMATCH(icons,Δ=45.4) |
| 3 | suite:dbt-now@dark | 2.15 | 3 | color/shadow theme | SHADOW_MISMATCH(effects,Δ=?); COLOR_MISMATCH(card_group,Δ=21.5); COLOR_MISMATCH(icons,Δ=49.7) |
| 4 | suite:avisos@dark | 2.20 | 3 | color/shadow theme | SHADOW_MISMATCH(effects,Δ=?); COLOR_MISMATCH(card_group,Δ=21.6); COLOR_MISMATCH(icons,Δ=45.9) |
| 5 | suite:actividades-marked-hice@dark | 2.67 | 3 | color/shadow theme | SHADOW_MISMATCH(effects,Δ=?); COLOR_MISMATCH(card_group,Δ=13.3); COLOR_MISMATCH(icons,Δ=64.0) |
| 6 | suite:actividades@dark | 2.70 | 3 | color/shadow theme | SHADOW_MISMATCH(effects,Δ=?); COLOR_MISMATCH(card_group,Δ=13.1); COLOR_MISMATCH(icons,Δ=63.9) |
| 7 | suite:home-no-score@dark | 3.84 | 3 | color/shadow theme | SHADOW_MISMATCH(effects,Δ=?); COLOR_MISMATCH(card_group,Δ=18.0); COLOR_MISMATCH(icons,Δ=39.9) |
| 8 | suite:home@dark | 4.79 | 3 | color/shadow theme | SHADOW_MISMATCH(effects,Δ=?); COLOR_MISMATCH(card_group,Δ=18.0); COLOR_MISMATCH(icons,Δ=40.1) |
| 9 | suite:avisos-empty@light | 0.83 | 2 | color/shadow theme | COLOR_MISMATCH(card_group,Δ=32.3); COLOR_MISMATCH(icons,Δ=16.0) |
| 10 | suite:avisos-search@light | 0.96 | 2 | color/shadow theme | COLOR_MISMATCH(card_group,Δ=17.6); COLOR_MISMATCH(icons,Δ=44.9) |
| 11 | suite:avisos-search@dark | 1.08 | 2 | color/shadow theme | COLOR_MISMATCH(card_group,Δ=25.8); COLOR_MISMATCH(icons,Δ=52.6) |
| 12 | suite:actividades-filtered@light | 1.58 | 2 | color/shadow theme | COLOR_MISMATCH(card_group,Δ=15.1); COLOR_MISMATCH(icons,Δ=62.6) |
| 13 | suite:actividades-filtered@dark | 1.68 | 2 | color/shadow theme | SHADOW_MISMATCH(effects,Δ=?); COLOR_MISMATCH(icons,Δ=48.0) |
| 14 | suite:avisos-filter-activos@light | 1.82 | 2 | color/shadow theme | COLOR_MISMATCH(card_group,Δ=21.2); COLOR_MISMATCH(icons,Δ=53.9) |
| 15 | suite:avisos-today@light | 1.88 | 2 | color/shadow theme | COLOR_MISMATCH(card_group,Δ=21.2); COLOR_MISMATCH(icons,Δ=53.9) |
| 16 | suite:dbt-now@light | 1.88 | 2 | color/shadow theme | COLOR_MISMATCH(card_group,Δ=26.1); COLOR_MISMATCH(icons,Δ=56.5) |
| 17 | suite:avisos@light | 2.05 | 2 | color/shadow theme | COLOR_MISMATCH(card_group,Δ=22.0); COLOR_MISMATCH(icons,Δ=54.7) |
| 18 | suite:actividades-marked-hice@light | 2.47 | 2 | color/shadow theme | COLOR_MISMATCH(card_group,Δ=17.8); COLOR_MISMATCH(icons,Δ=90.3) |
| 19 | suite:actividades@light | 2.47 | 2 | color/shadow theme | COLOR_MISMATCH(card_group,Δ=17.6); COLOR_MISMATCH(icons,Δ=90.2) |
| 20 | suite:registro-success@light | 2.48 | 2 | color/shadow theme | COLOR_MISMATCH(card_group,Δ=24.3); COLOR_MISMATCH(icons,Δ=57.2) |
| 21 | suite:rutina@dark | 2.51 | 2 | color/shadow theme | COLOR_MISMATCH(card_group,Δ=17.0); COLOR_MISMATCH(icons,Δ=35.7) |
| 22 | suite:rutina-add-task@dark | 2.80 | 2 | color/shadow theme | COLOR_MISMATCH(card_group,Δ=16.9); COLOR_MISMATCH(icons,Δ=35.6) |
| 23 | suite:rutina-all-completed@light | 3.24 | 2 | color/shadow theme | SHADOW_MISMATCH(effects,Δ=?); COLOR_MISMATCH(card_group,Δ=37.4) |
| 24 | suite:home-no-score@light | 3.59 | 2 | color/shadow theme | COLOR_MISMATCH(card_group,Δ=20.2); COLOR_MISMATCH(icons,Δ=53.3) |
| 25 | suite:registro-step1-emotion@light | 4.15 | 2 | estructural_confirmada | COLOR_MISMATCH(card_group,Δ=18.2); COLOR_MISMATCH(icons,Δ=43.1) |
| 26 | suite:home@light | 4.54 | 2 | color/shadow theme | COLOR_MISMATCH(card_group,Δ=20.3); COLOR_MISMATCH(icons,Δ=53.1) |
| 27 | hub:pacientes@dark | 4.72 | 2 | color/shadow theme | COLOR_MISMATCH(card_group,Δ=20.4); COLOR_MISMATCH(icons,Δ=56.3) |
| 28 | suite:actividades-empty@light | 0.82 | 1 | color/shadow theme | COLOR_MISMATCH(card_group,Δ=13.7) |
| 29 | suite:rutina-empty@light | 0.86 | 1 | color/shadow theme | COLOR_MISMATCH(card_group,Δ=13.8) |
| 30 | suite:timer-empty@light | 1.06 | 1 | color/shadow theme | COLOR_MISMATCH(icons,Δ=12.7) |
| 31 | hub:pacientes-empty@light | 1.07 | 1 | color/shadow theme | COLOR_MISMATCH(canvas,Δ=35.2) |
| 32 | suite:registro-success@dark | 2.16 | 1 | color/shadow theme | COLOR_MISMATCH(icons,Δ=23.7) |
| 33 | hub:textos-globales@dark | 2.37 | 1 | detector_noise_probable | TEXT_MISSING(header_text,Δ=?) |
| 34 | suite:rutina@light | 2.45 | 1 | color/shadow theme | COLOR_MISMATCH(card_group,Δ=43.1) |
| 35 | suite:rutina-add-task@light | 2.73 | 1 | color/shadow theme | COLOR_MISMATCH(card_group,Δ=43.1) |
| 36 | suite:animo@dark | 3.01 | 1 | color/shadow theme | COLOR_MISMATCH(icons,Δ=21.4) |
| 37 | suite:rutina-all-completed@dark | 3.21 | 1 | color/shadow theme | COLOR_MISMATCH(card_group,Δ=21.8) |
| 38 | suite:dbt-practice-stop@dark | 3.27 | 1 | detector_noise_probable | TEXT_MISSING(header_text,Δ=?) |
| 39 | suite:registro-step1-emotion@dark | 4.20 | 1 | estructural_confirmada | COLOR_MISMATCH(icons,Δ=31.9) |
| 40 | suite:animo@light | 4.63 | 1 | color/shadow theme | COLOR_MISMATCH(icons,Δ=32.7) |

## Top 10 Critical Surfaces

Criteria: category B, sorted by VAS fail count desc, then diff% asc

| # | Surface | diff% | VAS fail | Classification |
|---|---------|-------|----------|----------------|
| 1 | suite:avisos-filter-activos@dark | 1.94 | 3 | color/shadow theme |
| 2 | suite:avisos-today@dark | 1.99 | 3 | color/shadow theme |
| 3 | suite:dbt-now@dark | 2.15 | 3 | color/shadow theme |
| 4 | suite:avisos@dark | 2.20 | 3 | color/shadow theme |
| 5 | suite:actividades-marked-hice@dark | 2.67 | 3 | color/shadow theme |
| 6 | suite:actividades@dark | 2.70 | 3 | color/shadow theme |
| 7 | suite:home-no-score@dark | 3.84 | 3 | color/shadow theme |
| 8 | suite:home@dark | 4.79 | 3 | color/shadow theme |
| 9 | suite:avisos-empty@light | 0.83 | 2 | color/shadow theme |
| 10 | suite:avisos-search@light | 0.96 | 2 | color/shadow theme |

