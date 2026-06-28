# Cross-Gate Matrix: odiff vs VAS

**Total surfaces:** 86

## Summary

| Category | Count | Description |
|----------|-------|-------------|
| A | 74 | odiff PASS + VAS PASS |
| B | 9 | odiff PASS + VAS FAIL ← CRITICAL |
| C | 3 | odiff FAIL + VAS PASS |
| D | 0 | odiff FAIL + VAS FAIL |
| E | 0 | missing / skipped |

## Full Matrix

| Surface | Cat | odiff | diff% | VAS pass | VAS fail | Classification |
|---------|-----|-------|-------|----------|----------|----------------|
| hub:detalle-plan-activacion@dark | **A** | PASS | 5.97 | 3 | 0 | — |
| hub:detalle-plan-activacion@light | **A** | PASS | 5.97 | 1 | 0 | — |
| hub:detalle-plan-rutina@dark | **A** | PASS | 5.08 | 3 | 0 | — |
| hub:detalle-plan-rutina@light | **A** | PASS | 4.89 | 1 | 0 | — |
| hub:detalle-plan-timer@dark | **A** | PASS | 5.86 | 3 | 0 | — |
| hub:detalle-plan-timer@light | **A** | PASS | 5.78 | 1 | 0 | — |
| hub:detalle-resumen-ia-0@dark | **C** | FAIL | 9.18 | 1 | 0 | — |
| hub:detalle-resumen-ia-0@light | **C** | FAIL | 8.55 | 1 | 0 | — |
| hub:detalle@dark | **A** | PASS | 5.97 | 3 | 0 | — |
| hub:detalle@light | **A** | PASS | 5.87 | 1 | 0 | — |
| hub:pacientes-empty@dark | **A** | PASS | 1.16 | 1 | 0 | — |
| hub:pacientes-empty@light | **A** | PASS | 1.07 | 3 | 0 | — |
| hub:pacientes@dark | **B** | PASS | 4.87 | 5 | 1 | requiere_inspeccion_visual |
| hub:pacientes@light | **A** | PASS | 4.64 | 1 | 0 | — |
| hub:textos-globales@dark | **A** | PASS | 2.37 | 3 | 0 | — |
| hub:textos-globales@light | **A** | PASS | 1.95 | 3 | 0 | — |
| suite:actividades-empty@dark | **A** | PASS | 0.88 | 3 | 0 | — |
| suite:actividades-empty@light | **A** | PASS | 0.82 | 3 | 0 | — |
| suite:actividades-filtered@dark | **A** | PASS | 1.67 | 6 | 0 | — |
| suite:actividades-filtered@light | **A** | PASS | 1.59 | 4 | 0 | — |
| suite:actividades-marked-hice@dark | **A** | PASS | 2.69 | 6 | 0 | — |
| suite:actividades-marked-hice@light | **A** | PASS | 2.45 | 4 | 0 | — |
| suite:actividades@dark | **A** | PASS | 2.68 | 6 | 0 | — |
| suite:actividades@light | **A** | PASS | 2.47 | 4 | 0 | — |
| suite:animo@dark | **A** | PASS | 2.77 | 6 | 0 | — |
| suite:animo@light | **A** | PASS | 4.39 | 4 | 0 | — |
| suite:avisos-empty@dark | **A** | PASS | 0.91 | 3 | 0 | — |
| suite:avisos-empty@light | **A** | PASS | 0.83 | 3 | 0 | — |
| suite:avisos-filter-activos@dark | **A** | PASS | 1.94 | 6 | 0 | — |
| suite:avisos-filter-activos@light | **A** | PASS | 1.82 | 4 | 0 | — |
| suite:avisos-search@dark | **B** | PASS | 1.08 | 3 | 2 | color/shadow theme |
| suite:avisos-search@light | **B** | PASS | 0.96 | 1 | 2 | color/shadow theme |
| suite:avisos-today@dark | **A** | PASS | 1.77 | 6 | 0 | — |
| suite:avisos-today@light | **A** | PASS | 1.67 | 4 | 0 | — |
| suite:avisos@dark | **A** | PASS | 2.20 | 6 | 0 | — |
| suite:avisos@light | **A** | PASS | 2.05 | 4 | 0 | — |
| suite:dbt-library@dark | **A** | PASS | 3.33 | 3 | 0 | — |
| suite:dbt-library@light | **A** | PASS | 3.19 | 1 | 0 | — |
| suite:dbt-now@dark | **A** | PASS | 2.15 | 6 | 0 | — |
| suite:dbt-now@light | **A** | PASS | 1.88 | 4 | 0 | — |
| suite:dbt-practice-stop@dark | **A** | PASS | 3.27 | 3 | 0 | — |
| suite:dbt-practice-stop@light | **C** | FAIL | 55.93 | 1 | 0 | — |
| suite:home-no-score@dark | **A** | PASS | 3.84 | 6 | 0 | — |
| suite:home-no-score@light | **A** | PASS | 3.59 | 4 | 0 | — |
| suite:home@dark | **A** | PASS | 4.79 | 6 | 0 | — |
| suite:home@light | **A** | PASS | 4.54 | 4 | 0 | — |
| suite:onboarding-error@dark | **A** | PASS | 5.89 | 1 | 0 | — |
| suite:onboarding-error@light | **A** | PASS | 6.39 | 1 | 0 | — |
| suite:onboarding@dark | **A** | PASS | 5.41 | 1 | 0 | — |
| suite:onboarding@light | **A** | PASS | 5.61 | 1 | 0 | — |
| suite:recuperar-acceso@dark | **A** | PASS | 5.57 | 1 | 0 | — |
| suite:recuperar-acceso@light | **A** | PASS | 5.92 | 1 | 0 | — |
| suite:registro-step1-emotion-otro@dark | **A** | PASS | 5.47 | 3 | 0 | — |
| suite:registro-step1-emotion-otro@light | **A** | PASS | 5.45 | 3 | 0 | — |
| suite:registro-step1-emotion@dark | **B** | PASS | 5.40 | 5 | 1 | estructural_confirmada |
| suite:registro-step1-emotion@light | **B** | PASS | 5.38 | 2 | 1 | estructural_confirmada |
| suite:registro-step2-distortions@dark | **A** | PASS | 3.38 | 3 | 0 | — |
| suite:registro-step2-distortions@light | **A** | PASS | 3.13 | 3 | 0 | — |
| suite:registro-step3-filled@dark | **A** | PASS | 3.32 | 3 | 0 | — |
| suite:registro-step3-filled@light | **A** | PASS | 3.27 | 3 | 0 | — |
| suite:registro-success@dark | **B** | PASS | 0.98 | 4 | 1 | color/shadow theme |
| suite:registro-success@light | **B** | PASS | 1.81 | 1 | 2 | color/shadow theme |
| suite:registro@dark | **A** | PASS | 2.14 | 3 | 0 | — |
| suite:registro@light | **A** | PASS | 2.15 | 3 | 0 | — |
| suite:respiracion-paused@dark | **A** | PASS | 1.55 | 3 | 0 | — |
| suite:respiracion-paused@light | **A** | PASS | 1.46 | 3 | 0 | — |
| suite:respiracion-running@dark | **A** | PASS | 1.56 | 3 | 0 | — |
| suite:respiracion-running@light | **A** | PASS | 1.46 | 3 | 0 | — |
| suite:respiracion@dark | **A** | PASS | 1.56 | 3 | 0 | — |
| suite:respiracion@light | **A** | PASS | 1.47 | 3 | 0 | — |
| suite:rutina-add-task@dark | **A** | PASS | 2.80 | 6 | 0 | — |
| suite:rutina-add-task@light | **B** | PASS | 2.53 | 1 | 1 | color/shadow theme |
| suite:rutina-all-completed@dark | **A** | PASS | 3.21 | 5 | 0 | — |
| suite:rutina-all-completed@light | **B** | PASS | 2.85 | 3 | 1 | detector_noise_probable |
| suite:rutina-empty@dark | **A** | PASS | 0.96 | 3 | 0 | — |
| suite:rutina-empty@light | **A** | PASS | 0.86 | 3 | 0 | — |
| suite:rutina@dark | **A** | PASS | 2.51 | 6 | 0 | — |
| suite:rutina@light | **A** | PASS | 2.19 | 1 | 0 | — |
| suite:timer-empty@dark | **A** | PASS | 1.27 | 3 | 0 | — |
| suite:timer-empty@light | **A** | PASS | 1.05 | 3 | 0 | — |
| suite:timer-paused@dark | **A** | PASS | 2.10 | 3 | 0 | — |
| suite:timer-paused@light | **A** | PASS | 2.03 | 3 | 0 | — |
| suite:timer-running@dark | **A** | PASS | 2.11 | 3 | 0 | — |
| suite:timer-running@light | **A** | PASS | 2.01 | 3 | 0 | — |
| suite:timer@dark | **A** | PASS | 2.08 | 3 | 0 | — |
| suite:timer@light | **A** | PASS | 2.00 | 3 | 0 | — |

## Category B — odiff PASS + VAS FAIL (critical zone)

Total: **9** surfaces

| # | Surface | diff% | VAS fail | Classification | Divergences |
|---|---------|-------|----------|----------------|-------------|
| 1 | suite:avisos-search@light | 0.96 | 2 | color/shadow theme | COLOR_MISMATCH(card_group,Δ=13.6); COLOR_MISMATCH(icons,Δ=43.3) |
| 2 | suite:avisos-search@dark | 1.08 | 2 | color/shadow theme | COLOR_MISMATCH(card_group,Δ=21.8); COLOR_MISMATCH(icons,Δ=51.0) |
| 3 | suite:registro-success@light | 1.81 | 2 | color/shadow theme | COLOR_MISMATCH(card_group,Δ=20.0); COLOR_MISMATCH(icons,Δ=57.3) |
| 4 | suite:registro-success@dark | 0.98 | 1 | color/shadow theme | COLOR_MISMATCH(icons,Δ=29.4) |
| 5 | suite:rutina-add-task@light | 2.53 | 1 | color/shadow theme | COLOR_MISMATCH(card_group,Δ=59.1) |
| 6 | suite:rutina-all-completed@light | 2.85 | 1 | detector_noise_probable | SHADOW_MISMATCH(effects,Δ=?) |
| 7 | hub:pacientes@dark | 4.87 | 1 | requiere_inspeccion_visual | COLOR_MISMATCH(icons,Δ=18.0) |
| 8 | suite:registro-step1-emotion@light | 5.38 | 1 | estructural_confirmada | COLOR_MISMATCH(card_group,Δ=15.9) |
| 9 | suite:registro-step1-emotion@dark | 5.40 | 1 | estructural_confirmada | COLOR_MISMATCH(icons,Δ=13.3) |

## Top 10 Critical Surfaces

Criteria: category B, sorted by VAS fail count desc, then diff% asc

| # | Surface | diff% | VAS fail | Classification |
|---|---------|-------|----------|----------------|
| 1 | suite:avisos-search@light | 0.96 | 2 | color/shadow theme |
| 2 | suite:avisos-search@dark | 1.08 | 2 | color/shadow theme |
| 3 | suite:registro-success@light | 1.81 | 2 | color/shadow theme |
| 4 | suite:registro-success@dark | 0.98 | 1 | color/shadow theme |
| 5 | suite:rutina-add-task@light | 2.53 | 1 | color/shadow theme |
| 6 | suite:rutina-all-completed@light | 2.85 | 1 | detector_noise_probable |
| 7 | hub:pacientes@dark | 4.87 | 1 | requiere_inspeccion_visual |
| 8 | suite:registro-step1-emotion@light | 5.38 | 1 | estructural_confirmada |
| 9 | suite:registro-step1-emotion@dark | 5.40 | 1 | estructural_confirmada |

