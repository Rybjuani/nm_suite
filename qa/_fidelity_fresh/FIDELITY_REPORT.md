# Fidelity diff report

Generated: 2026-06-21T02:36:22

Acceptance gate:
- SSIM >= 0.92
- mean_abs_diff <= 0.035
- changed_pixel_ratio <= 0.08
- capture manifest evidence, when present, must be technically valid and state-valid

| Status | App | View | Theme | Res | SSIM | MAD | Changed | Diff |
|---|---|---|---|---|---:|---:|---:|---|
| FAIL | hub | detalle | dark | 960x600 | 0.71164 | 0.06454 | 0.161 | qa/_fidelity_fresh/hub-detalle-dark-960x600-diff.png |
| FAIL | hub | detalle | light | 960x600 | 0.73315 | 0.09295 | 0.60119 | qa/_fidelity_fresh/hub-detalle-light-960x600-diff.png |
| FAIL | hub | detalle-plan-activacion | dark | 960x600 | 0.68001 | 0.06625 | 0.16723 | qa/_fidelity_fresh/hub-detalle-plan-activacion-dark-960x600-diff.png |
| FAIL | hub | detalle-plan-activacion | light | 960x600 | 0.69341 | 0.09195 | 0.54052 | qa/_fidelity_fresh/hub-detalle-plan-activacion-light-960x600-diff.png |
| FAIL | hub | detalle-plan-rutina | dark | 960x600 | 0.72356 | 0.06047 | 0.1447 | qa/_fidelity_fresh/hub-detalle-plan-rutina-dark-960x600-diff.png |
| FAIL | hub | detalle-plan-rutina | light | 960x600 | 0.74223 | 0.09013 | 0.58482 | qa/_fidelity_fresh/hub-detalle-plan-rutina-light-960x600-diff.png |
| FAIL | hub | detalle-plan-timer | dark | 960x600 | 0.69798 | 0.06363 | 0.15567 | qa/_fidelity_fresh/hub-detalle-plan-timer-dark-960x600-diff.png |
| FAIL | hub | detalle-plan-timer | light | 960x600 | 0.7153 | 0.09123 | 0.58647 | qa/_fidelity_fresh/hub-detalle-plan-timer-light-960x600-diff.png |
| FAIL | hub | detalle-resumen-ia-0 | dark | 480x325 | 0.73064 | 0.05338 | 0.14515 | qa/_fidelity_fresh/hub-detalle-resumen-ia-0-dark-480x325-diff.png |
| FAIL | hub | detalle-resumen-ia-0 | light | 480x325 | 0.73404 | 0.06449 | 0.14129 | qa/_fidelity_fresh/hub-detalle-resumen-ia-0-light-480x325-diff.png |
| FAIL | hub | pacientes | dark | 960x600 | 0.73022 | 0.05113 | 0.11928 | qa/_fidelity_fresh/hub-pacientes-dark-960x600-diff.png |
| FAIL | hub | pacientes | light | 960x600 | 0.74498 | 0.06726 | 0.50372 | qa/_fidelity_fresh/hub-pacientes-light-960x600-diff.png |
| FAIL | hub | pacientes-empty | dark | 960x600 | 0.89723 | 0.02022 | 0.05773 | qa/_fidelity_fresh/hub-pacientes-empty-dark-960x600-diff.png |
| FAIL | hub | pacientes-empty | light | 960x600 | 0.90569 | 0.0241 | 0.15637 | qa/_fidelity_fresh/hub-pacientes-empty-light-960x600-diff.png |
| FAIL | hub | textos-globales | dark | 960x600 | 0.62336 | 0.04821 | 0.22795 | qa/_fidelity_fresh/hub-textos-globales-dark-960x600-diff.png |
| FAIL | hub | textos-globales | light | 960x600 | 0.63576 | 0.05746 | 0.65213 | qa/_fidelity_fresh/hub-textos-globales-light-960x600-diff.png |
| FAIL | suite | actividades | dark | 960x600 | 0.68537 | 0.04879 | 0.19294 | qa/_fidelity_fresh/suite-actividades-dark-960x600-diff.png |
| FAIL | suite | actividades | light | 960x600 | 0.69808 | 0.05631 | 0.36436 | qa/_fidelity_fresh/suite-actividades-light-960x600-diff.png |
| FAIL | suite | actividades-empty | dark | 960x600 | 0.91032 | 0.03737 | 0.08325 | qa/_fidelity_fresh/suite-actividades-empty-dark-960x600-diff.png |
| FAIL | suite | actividades-empty | light | 960x600 | 0.94545 | 0.08031 | 0.91737 | qa/_fidelity_fresh/suite-actividades-empty-light-960x600-diff.png |
| FAIL | suite | actividades-filtered | dark | 960x600 | 0.81581 | 0.04146 | 0.09361 | qa/_fidelity_fresh/suite-actividades-filtered-dark-960x600-diff.png |
| FAIL | suite | actividades-filtered | light | 960x600 | 0.8386 | 0.0746 | 0.71662 | qa/_fidelity_fresh/suite-actividades-filtered-light-960x600-diff.png |
| FAIL | suite | actividades-marked-hice | dark | 960x600 | 0.68933 | 0.04842 | 0.18899 | qa/_fidelity_fresh/suite-actividades-marked-hice-dark-960x600-diff.png |
| FAIL | suite | actividades-marked-hice | light | 960x600 | 0.70244 | 0.05569 | 0.36179 | qa/_fidelity_fresh/suite-actividades-marked-hice-light-960x600-diff.png |
| FAIL | suite | animo | dark | 960x600 | 0.77107 | 0.04177 | 0.20197 | qa/_fidelity_fresh/suite-animo-dark-960x600-diff.png |
| FAIL | suite | animo | light | 960x600 | 0.78917 | 0.05455 | 0.33637 | qa/_fidelity_fresh/suite-animo-light-960x600-diff.png |
| FAIL | suite | avisos | dark | 960x600 | 0.74053 | 0.03498 | 0.14007 | qa/_fidelity_fresh/suite-avisos-dark-960x600-diff.png |
| FAIL | suite | avisos | light | 960x600 | 0.72839 | 0.04899 | 0.3532 | qa/_fidelity_fresh/suite-avisos-light-960x600-diff.png |
| FAIL | suite | avisos-completed | dark | 960x600 | 0.74367 | 0.03464 | 0.14104 | qa/_fidelity_fresh/suite-avisos-completed-dark-960x600-diff.png |
| FAIL | suite | avisos-completed | light | 960x600 | 0.73073 | 0.04884 | 0.35374 | qa/_fidelity_fresh/suite-avisos-completed-light-960x600-diff.png |
| FAIL | suite | avisos-empty | dark | 960x600 | 0.88359 | 0.04197 | 0.07576 | qa/_fidelity_fresh/suite-avisos-empty-dark-960x600-diff.png |
| FAIL | suite | avisos-empty | light | 960x600 | 0.91934 | 0.0854 | 0.865 | qa/_fidelity_fresh/suite-avisos-empty-light-960x600-diff.png |
| FAIL | suite | avisos-filter-activos | dark | 960x600 | 0.79473 | 0.03443 | 0.11182 | qa/_fidelity_fresh/suite-avisos-filter-activos-dark-960x600-diff.png |
| FAIL | suite | avisos-filter-activos | light | 960x600 | 0.79115 | 0.05719 | 0.46401 | qa/_fidelity_fresh/suite-avisos-filter-activos-light-960x600-diff.png |
| FAIL | suite | avisos-search | dark | 960x600 | 0.88155 | 0.0357 | 0.0713 | qa/_fidelity_fresh/suite-avisos-search-dark-960x600-diff.png |
| FAIL | suite | avisos-search | light | 960x600 | 0.90417 | 0.07663 | 0.7711 | qa/_fidelity_fresh/suite-avisos-search-light-960x600-diff.png |
| FAIL | suite | dbt-library | dark | 960x600 | 0.65584 | 0.05522 | 0.2184 | qa/_fidelity_fresh/suite-dbt-library-dark-960x600-diff.png |
| FAIL | suite | dbt-library | light | 960x600 | 0.67703 | 0.06918 | 0.48434 | qa/_fidelity_fresh/suite-dbt-library-light-960x600-diff.png |
| FAIL | suite | dbt-now | dark | 960x600 | 0.76599 | 0.04572 | 0.20612 | qa/_fidelity_fresh/suite-dbt-now-dark-960x600-diff.png |
| FAIL | suite | dbt-now | light | 960x600 | 0.79122 | 0.06095 | 0.52511 | qa/_fidelity_fresh/suite-dbt-now-light-960x600-diff.png |
| FAIL | suite | dbt-practice-closure | dark | 960x600 | 0.78079 | 0.05505 | 0.24188 | qa/_fidelity_fresh/suite-dbt-practice-closure-dark-960x600-diff.png |
| FAIL | suite | dbt-practice-closure | light | 960x600 | 0.7492 | 0.22572 | 0.87832 | qa/_fidelity_fresh/suite-dbt-practice-closure-light-960x600-diff.png |
| FAIL | suite | dbt-practice-stop | dark | 960x600 | 0.7886 | 0.04915 | 0.23822 | qa/_fidelity_fresh/suite-dbt-practice-stop-dark-960x600-diff.png |
| FAIL | suite | dbt-practice-stop | light | 960x600 | 0.75719 | 0.21719 | 0.8144 | qa/_fidelity_fresh/suite-dbt-practice-stop-light-960x600-diff.png |
| FAIL | suite | home | dark | 960x600 | 0.68307 | 0.05878 | 0.30182 | qa/_fidelity_fresh/suite-home-dark-960x600-diff.png |
| FAIL | suite | home | light | 960x600 | 0.67784 | 0.06498 | 0.38945 | qa/_fidelity_fresh/suite-home-light-960x600-diff.png |
| FAIL | suite | home-no-score | dark | 960x600 | 0.69323 | 0.05403 | 0.26153 | qa/_fidelity_fresh/suite-home-no-score-dark-960x600-diff.png |
| FAIL | suite | home-no-score | light | 960x600 | 0.69336 | 0.06336 | 0.37496 | qa/_fidelity_fresh/suite-home-no-score-light-960x600-diff.png |
| FAIL | suite | onboarding | dark | 520x600 | 0.65284 | 0.04473 | 0.14145 | qa/_fidelity_fresh/suite-onboarding-dark-520x600-diff.png |
| FAIL | suite | onboarding | light | 520x600 | 0.65935 | 0.0494 | 0.30213 | qa/_fidelity_fresh/suite-onboarding-light-520x600-diff.png |
| FAIL | suite | onboarding-error | dark | 520x600 | 0.615 | 0.05626 | 0.16296 | qa/_fidelity_fresh/suite-onboarding-error-dark-520x600-diff.png |
| FAIL | suite | onboarding-error | light | 520x600 | 0.62322 | 0.06321 | 0.31971 | qa/_fidelity_fresh/suite-onboarding-error-light-520x600-diff.png |
| FAIL | suite | recuperar-acceso | dark | 520x600 | 0.63126 | 0.04707 | 0.15849 | qa/_fidelity_fresh/suite-recuperar-acceso-dark-520x600-diff.png |
| FAIL | suite | recuperar-acceso | light | 520x600 | 0.6336 | 0.05208 | 0.30975 | qa/_fidelity_fresh/suite-recuperar-acceso-light-520x600-diff.png |
| FAIL | suite | registro | dark | 960x600 | 0.82771 | 0.03342 | 0.14028 | qa/_fidelity_fresh/suite-registro-dark-960x600-diff.png |
| FAIL | suite | registro | light | 960x600 | 0.84223 | 0.05492 | 0.59349 | qa/_fidelity_fresh/suite-registro-light-960x600-diff.png |
| FAIL | suite | registro-step1-emotion | dark | 960x600 | 0.76971 | 0.05162 | 0.20398 | qa/_fidelity_fresh/suite-registro-step1-emotion-dark-960x600-diff.png |
| FAIL | suite | registro-step1-emotion | light | 960x600 | 0.78878 | 0.07283 | 0.43329 | qa/_fidelity_fresh/suite-registro-step1-emotion-light-960x600-diff.png |
| FAIL | suite | registro-step1-emotion-otro | dark | 960x600 | 0.75494 | 0.05233 | 0.19906 | qa/_fidelity_fresh/suite-registro-step1-emotion-otro-dark-960x600-diff.png |
| FAIL | suite | registro-step1-emotion-otro | light | 960x600 | 0.77535 | 0.07329 | 0.4967 | qa/_fidelity_fresh/suite-registro-step1-emotion-otro-light-960x600-diff.png |
| FAIL | suite | registro-step2-distortions | dark | 960x600 | 0.73809 | 0.05666 | 0.29762 | qa/_fidelity_fresh/suite-registro-step2-distortions-dark-960x600-diff.png |
| FAIL | suite | registro-step2-distortions | light | 960x600 | 0.76346 | 0.07162 | 0.58804 | qa/_fidelity_fresh/suite-registro-step2-distortions-light-960x600-diff.png |
| FAIL | suite | registro-step3-filled | dark | 960x600 | 0.78784 | 0.04714 | 0.154 | qa/_fidelity_fresh/suite-registro-step3-filled-dark-960x600-diff.png |
| FAIL | suite | registro-step3-filled | light | 960x600 | 0.801 | 0.07195 | 0.64688 | qa/_fidelity_fresh/suite-registro-step3-filled-light-960x600-diff.png |
| FAIL | suite | registro-success | dark | 960x600 | 0.82459 | 0.04644 | 0.15556 | qa/_fidelity_fresh/suite-registro-success-dark-960x600-diff.png |
| FAIL | suite | registro-success | light | 960x600 | 0.84483 | 0.06457 | 0.6508 | qa/_fidelity_fresh/suite-registro-success-light-960x600-diff.png |
| FAIL | suite | respiracion | dark | 960x600 | 0.8528 | 0.02848 | 0.11557 | qa/_fidelity_fresh/suite-respiracion-dark-960x600-diff.png |
| FAIL | suite | respiracion | light | 960x600 | 0.86717 | 0.03309 | 0.19801 | qa/_fidelity_fresh/suite-respiracion-light-960x600-diff.png |
| FAIL | suite | respiracion-paused | dark | 960x600 | 0.85211 | 0.02843 | 0.11823 | qa/_fidelity_fresh/suite-respiracion-paused-dark-960x600-diff.png |
| FAIL | suite | respiracion-paused | light | 960x600 | 0.86626 | 0.03288 | 0.19594 | qa/_fidelity_fresh/suite-respiracion-paused-light-960x600-diff.png |
| FAIL | suite | respiracion-preset-10min | dark | 960x600 | 0.85276 | 0.02857 | 0.1157 | qa/_fidelity_fresh/suite-respiracion-preset-10min-dark-960x600-diff.png |
| FAIL | suite | respiracion-preset-10min | light | 960x600 | 0.86717 | 0.03324 | 0.19792 | qa/_fidelity_fresh/suite-respiracion-preset-10min-light-960x600-diff.png |
| FAIL | suite | respiracion-preset-3min | dark | 960x600 | 0.85287 | 0.02847 | 0.11566 | qa/_fidelity_fresh/suite-respiracion-preset-3min-dark-960x600-diff.png |
| FAIL | suite | respiracion-preset-3min | light | 960x600 | 0.86723 | 0.03309 | 0.19801 | qa/_fidelity_fresh/suite-respiracion-preset-3min-light-960x600-diff.png |
| FAIL | suite | respiracion-running | dark | 960x600 | 0.85355 | 0.02737 | 0.10685 | qa/_fidelity_fresh/suite-respiracion-running-dark-960x600-diff.png |
| FAIL | suite | respiracion-running | light | 960x600 | 0.86615 | 0.03276 | 0.18625 | qa/_fidelity_fresh/suite-respiracion-running-light-960x600-diff.png |
| FAIL | suite | rutina | dark | 960x600 | 0.77947 | 0.04092 | 0.09528 | qa/_fidelity_fresh/suite-rutina-dark-960x600-diff.png |
| FAIL | suite | rutina | light | 960x600 | 0.80037 | 0.06888 | 0.58394 | qa/_fidelity_fresh/suite-rutina-light-960x600-diff.png |
| FAIL | suite | rutina-add-task | dark | 960x600 | 0.76524 | 0.04386 | 0.11791 | qa/_fidelity_fresh/suite-rutina-add-task-dark-960x600-diff.png |
| FAIL | suite | rutina-add-task | light | 960x600 | 0.78697 | 0.0712 | 0.60296 | qa/_fidelity_fresh/suite-rutina-add-task-light-960x600-diff.png |
| FAIL | suite | rutina-all-completed | dark | 960x600 | 0.76736 | 0.04465 | 0.10267 | qa/_fidelity_fresh/suite-rutina-all-completed-dark-960x600-diff.png |
| FAIL | suite | rutina-all-completed | light | 960x600 | 0.78704 | 0.07448 | 0.58946 | qa/_fidelity_fresh/suite-rutina-all-completed-light-960x600-diff.png |
| FAIL | suite | rutina-empty | dark | 960x600 | 0.90822 | 0.03782 | 0.08408 | qa/_fidelity_fresh/suite-rutina-empty-dark-960x600-diff.png |
| FAIL | suite | rutina-empty | light | 960x600 | 0.94318 | 0.08072 | 0.91675 | qa/_fidelity_fresh/suite-rutina-empty-light-960x600-diff.png |
| FAIL | suite | timer | dark | 960x600 | 0.87927 | 0.02614 | 0.07212 | qa/_fidelity_fresh/suite-timer-dark-960x600-diff.png |
| FAIL | suite | timer | light | 960x600 | 0.8829 | 0.03045 | 0.1599 | qa/_fidelity_fresh/suite-timer-light-960x600-diff.png |
| FAIL | suite | timer-empty | dark | 960x600 | 0.91492 | 0.01778 | 0.04929 | qa/_fidelity_fresh/suite-timer-empty-dark-960x600-diff.png |
| FAIL | suite | timer-empty | light | 960x600 | 0.923 | 0.01973 | 0.12656 | qa/_fidelity_fresh/suite-timer-empty-light-960x600-diff.png |
| FAIL | suite | timer-paused | dark | 960x600 | 0.88384 | 0.02505 | 0.06768 | qa/_fidelity_fresh/suite-timer-paused-dark-960x600-diff.png |
| FAIL | suite | timer-paused | light | 960x600 | 0.88788 | 0.0292 | 0.15546 | qa/_fidelity_fresh/suite-timer-paused-light-960x600-diff.png |
| FAIL | suite | timer-preset-45min | dark | 960x600 | 0.87517 | 0.03063 | 0.08277 | qa/_fidelity_fresh/suite-timer-preset-45min-dark-960x600-diff.png |
| FAIL | suite | timer-preset-45min | light | 960x600 | 0.87872 | 0.03753 | 0.16564 | qa/_fidelity_fresh/suite-timer-preset-45min-light-960x600-diff.png |
| FAIL | suite | timer-preset-5min | dark | 960x600 | 0.87565 | 0.02992 | 0.08081 | qa/_fidelity_fresh/suite-timer-preset-5min-dark-960x600-diff.png |
| FAIL | suite | timer-preset-5min | light | 960x600 | 0.87923 | 0.03623 | 0.16478 | qa/_fidelity_fresh/suite-timer-preset-5min-light-960x600-diff.png |
| FAIL | suite | timer-running | dark | 960x600 | 0.88034 | 0.02584 | 0.07082 | qa/_fidelity_fresh/suite-timer-running-dark-960x600-diff.png |
| FAIL | suite | timer-running | light | 960x600 | 0.88412 | 0.03011 | 0.15872 | qa/_fidelity_fresh/suite-timer-running-light-960x600-diff.png |
