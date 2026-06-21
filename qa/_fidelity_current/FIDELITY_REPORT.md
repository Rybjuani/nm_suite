# Fidelity diff report

Generated: 2026-06-20T22:03:14

Acceptance gate:
- SSIM >= 0.92
- mean_abs_diff <= 0.035
- changed_pixel_ratio <= 0.08
- capture manifest evidence, when present, must be technically valid and state-valid

| Status | App | View | Theme | Res | SSIM | MAD | Changed | Diff |
|---|---|---|---|---|---:|---:|---:|---|
| FAIL | hub | detalle | dark | 960x600 | 0.70255 | 0.06859 | 0.21119 |  |
| FAIL | hub | detalle | light | 960x600 | 0.72468 | 0.09648 | 0.64293 |  |
| FAIL | hub | detalle-plan-activacion | dark | 960x600 | 0.67489 | 0.06786 | 0.21368 |  |
| FAIL | hub | detalle-plan-activacion | light | 960x600 | 0.69242 | 0.09206 | 0.58064 |  |
| FAIL | hub | detalle-plan-rutina | dark | 960x600 | 0.71401 | 0.06589 | 0.19135 |  |
| FAIL | hub | detalle-plan-rutina | light | 960x600 | 0.73259 | 0.09463 | 0.62939 |  |
| FAIL | hub | detalle-plan-timer | dark | 960x600 | 0.69154 | 0.06812 | 0.2072 |  |
| FAIL | hub | detalle-plan-timer | light | 960x600 | 0.71107 | 0.09581 | 0.62369 |  |
| FAIL | hub | detalle-resumen-ia-0 | dark | 480x325 | 0.73257 | 0.05488 | 0.15155 |  |
| FAIL | hub | detalle-resumen-ia-0 | light | 480x325 | 0.73669 | 0.06433 | 0.14451 |  |
| FAIL | hub | pacientes | dark | 960x600 | 0.72162 | 0.05319 | 0.15681 |  |
| FAIL | hub | pacientes | light | 960x600 | 0.73361 | 0.06882 | 0.53472 |  |
| FAIL | hub | pacientes-empty | dark | 960x600 | 0.87649 | 0.0245 | 0.10045 |  |
| FAIL | hub | pacientes-empty | light | 960x600 | 0.88316 | 0.0298 | 0.19497 |  |
| FAIL | hub | textos-globales | dark | 960x600 | 0.59464 | 0.05352 | 0.24355 |  |
| FAIL | hub | textos-globales | light | 960x600 | 0.5927 | 0.06143 | 0.66329 |  |
| FAIL | suite | actividades | dark | 960x600 | 0.67488 | 0.04988 | 0.20324 |  |
| FAIL | suite | actividades | light | 960x600 | 0.68278 | 0.05767 | 0.37799 |  |
| FAIL | suite | actividades-empty | dark | 960x600 | 0.90278 | 0.03957 | 0.09331 |  |
| FAIL | suite | actividades-empty | light | 960x600 | 0.93639 | 0.08137 | 0.92001 |  |
| FAIL | suite | actividades-filtered | dark | 960x600 | 0.7993 | 0.04427 | 0.11328 |  |
| FAIL | suite | actividades-filtered | light | 960x600 | 0.82213 | 0.07782 | 0.73046 |  |
| FAIL | suite | actividades-marked-hice | dark | 960x600 | 0.67926 | 0.04954 | 0.20469 |  |
| FAIL | suite | actividades-marked-hice | light | 960x600 | 0.68727 | 0.05745 | 0.37916 |  |
| FAIL | suite | animo | dark | 960x600 | 0.76154 | 0.04456 | 0.209 |  |
| FAIL | suite | animo | light | 960x600 | 0.77772 | 0.05648 | 0.34505 |  |
| FAIL | suite | avisos | dark | 960x600 | 0.73365 | 0.03934 | 0.15169 |  |
| FAIL | suite | avisos | light | 960x600 | 0.71802 | 0.05279 | 0.37944 |  |
| FAIL | suite | avisos-completed | dark | 960x600 | 0.73601 | 0.03897 | 0.15287 |  |
| FAIL | suite | avisos-completed | light | 960x600 | 0.71968 | 0.05267 | 0.38025 |  |
| FAIL | suite | avisos-empty | dark | 960x600 | 0.87611 | 0.04471 | 0.0911 |  |
| FAIL | suite | avisos-empty | light | 960x600 | 0.91196 | 0.08706 | 0.87882 |  |
| FAIL | suite | avisos-filter-activos | dark | 960x600 | 0.78771 | 0.03779 | 0.12279 |  |
| FAIL | suite | avisos-filter-activos | light | 960x600 | 0.78231 | 0.05977 | 0.48612 |  |
| FAIL | suite | avisos-search | dark | 960x600 | 0.87137 | 0.03946 | 0.08153 |  |
| FAIL | suite | avisos-search | light | 960x600 | 0.89414 | 0.07995 | 0.7883 |  |
| FAIL | suite | dbt-library | dark | 960x600 | 0.62401 | 0.06603 | 0.25545 |  |
| FAIL | suite | dbt-library | light | 960x600 | 0.64745 | 0.08002 | 0.52927 |  |
| FAIL | suite | dbt-now | dark | 960x600 | 0.7444 | 0.05302 | 0.23246 |  |
| FAIL | suite | dbt-now | light | 960x600 | 0.77727 | 0.06841 | 0.54066 |  |
| FAIL | suite | dbt-practice-closure | dark | 960x600 | 0.76843 | 0.05749 | 0.24517 |  |
| FAIL | suite | dbt-practice-closure | light | 960x600 | 0.73889 | 0.22602 | 0.88065 |  |
| FAIL | suite | dbt-practice-stop | dark | 960x600 | 0.77799 | 0.05245 | 0.24946 |  |
| FAIL | suite | dbt-practice-stop | light | 960x600 | 0.74822 | 0.21922 | 0.83302 |  |
| FAIL | suite | home | dark | 960x600 | 0.63795 | 0.06016 | 0.27564 |  |
| FAIL | suite | home | light | 960x600 | 0.63826 | 0.06759 | 0.39959 |  |
| FAIL | suite | home-no-score | dark | 960x600 | 0.64888 | 0.05568 | 0.25237 |  |
| FAIL | suite | home-no-score | light | 960x600 | 0.65592 | 0.06103 | 0.37468 |  |
| FAIL | suite | onboarding | dark | 520x600 | 0.49774 | 0.07261 | 0.2622 |  |
| FAIL | suite | onboarding | light | 520x600 | 0.51055 | 0.07126 | 0.40384 |  |
| FAIL | suite | onboarding-error | dark | 520x600 | 0.48568 | 0.07505 | 0.27158 |  |
| FAIL | suite | onboarding-error | light | 520x600 | 0.49946 | 0.07344 | 0.41584 |  |
| FAIL | suite | recuperar-acceso | dark | 520x600 | 0.48018 | 0.0748 | 0.27592 |  |
| FAIL | suite | recuperar-acceso | light | 520x600 | 0.48811 | 0.07302 | 0.40062 |  |
| FAIL | suite | registro | dark | 960x600 | 0.81631 | 0.03662 | 0.1789 |  |
| FAIL | suite | registro | light | 960x600 | 0.83088 | 0.05654 | 0.58537 |  |
| FAIL | suite | registro-step1-emotion | dark | 960x600 | 0.75327 | 0.05579 | 0.24765 |  |
| FAIL | suite | registro-step1-emotion | light | 960x600 | 0.77616 | 0.07553 | 0.44142 |  |
| FAIL | suite | registro-step1-emotion-otro | dark | 960x600 | 0.74341 | 0.05612 | 0.24357 |  |
| FAIL | suite | registro-step1-emotion-otro | light | 960x600 | 0.76588 | 0.075 | 0.49196 |  |
| FAIL | suite | registro-step2-distortions | dark | 960x600 | 0.73751 | 0.05851 | 0.32625 |  |
| FAIL | suite | registro-step2-distortions | light | 960x600 | 0.76211 | 0.07138 | 0.58501 |  |
| FAIL | suite | registro-step3-filled | dark | 960x600 | 0.77382 | 0.05117 | 0.19342 |  |
| FAIL | suite | registro-step3-filled | light | 960x600 | 0.78709 | 0.07382 | 0.63998 |  |
| FAIL | suite | registro-success | dark | 960x600 | 0.81012 | 0.04995 | 0.18889 |  |
| FAIL | suite | registro-success | light | 960x600 | 0.8296 | 0.06694 | 0.65457 |  |
| FAIL | suite | respiracion | dark | 960x600 | 0.84363 | 0.03039 | 0.13856 |  |
| FAIL | suite | respiracion | light | 960x600 | 0.85483 | 0.03441 | 0.20243 |  |
| FAIL | suite | respiracion-paused | dark | 960x600 | 0.8414 | 0.03081 | 0.14234 |  |
| FAIL | suite | respiracion-paused | light | 960x600 | 0.85284 | 0.03464 | 0.20026 |  |
| FAIL | suite | respiracion-preset-10min | dark | 960x600 | 0.84362 | 0.03047 | 0.13864 |  |
| FAIL | suite | respiracion-preset-10min | light | 960x600 | 0.85485 | 0.03453 | 0.20233 |  |
| FAIL | suite | respiracion-preset-3min | dark | 960x600 | 0.84378 | 0.03034 | 0.13854 |  |
| FAIL | suite | respiracion-preset-3min | light | 960x600 | 0.85495 | 0.03435 | 0.20241 |  |
| FAIL | suite | respiracion-running | dark | 960x600 | 0.84374 | 0.02966 | 0.12993 |  |
| FAIL | suite | respiracion-running | light | 960x600 | 0.85311 | 0.03449 | 0.19033 |  |
| FAIL | suite | rutina | dark | 960x600 | 0.76476 | 0.04459 | 0.12797 |  |
| FAIL | suite | rutina | light | 960x600 | 0.78344 | 0.07242 | 0.60183 |  |
| FAIL | suite | rutina-add-task | dark | 960x600 | 0.7482 | 0.04852 | 0.16137 |  |
| FAIL | suite | rutina-add-task | light | 960x600 | 0.76875 | 0.07592 | 0.61969 |  |
| FAIL | suite | rutina-all-completed | dark | 960x600 | 0.75339 | 0.04797 | 0.13519 |  |
| FAIL | suite | rutina-all-completed | light | 960x600 | 0.77034 | 0.07812 | 0.60829 |  |
| FAIL | suite | rutina-empty | dark | 960x600 | 0.90083 | 0.03997 | 0.09375 |  |
| FAIL | suite | rutina-empty | light | 960x600 | 0.93416 | 0.08175 | 0.91915 |  |
| FAIL | suite | timer | dark | 960x600 | 0.86435 | 0.02975 | 0.10288 |  |
| FAIL | suite | timer | light | 960x600 | 0.86464 | 0.03406 | 0.16834 |  |
| FAIL | suite | timer-empty | dark | 960x600 | 0.90475 | 0.02053 | 0.07689 |  |
| FAIL | suite | timer-empty | light | 960x600 | 0.91078 | 0.02188 | 0.12978 |  |
| FAIL | suite | timer-paused | dark | 960x600 | 0.86952 | 0.02838 | 0.09737 |  |
| FAIL | suite | timer-paused | light | 960x600 | 0.87026 | 0.03258 | 0.16287 |  |
| FAIL | suite | timer-preset-45min | dark | 960x600 | 0.86139 | 0.03451 | 0.11376 |  |
| FAIL | suite | timer-preset-45min | light | 960x600 | 0.86183 | 0.04156 | 0.17444 |  |
| FAIL | suite | timer-preset-5min | dark | 960x600 | 0.86207 | 0.03372 | 0.11161 |  |
| FAIL | suite | timer-preset-5min | light | 960x600 | 0.86249 | 0.04008 | 0.1734 |  |
| FAIL | suite | timer-running | dark | 960x600 | 0.86524 | 0.02943 | 0.10128 |  |
| FAIL | suite | timer-running | light | 960x600 | 0.86569 | 0.03371 | 0.16689 |  |
