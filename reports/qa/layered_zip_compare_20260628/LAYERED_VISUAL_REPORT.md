# Layered visual comparison report

Generated: 2026-06-28T09:39:00

Thresholds:
- raw SSIM >= 0.92
- raw mean_abs_diff <= 0.035
- raw changed_pixel_ratio <= 0.08
- odiff diff_percentage <= 8
- content bbox shift <= 18px

Summary:
- Total: 86
- Pass: 0
- Real divergences/review items: 86
- QA missed raw/layout: 83
- State or recipe suspects: 40
- By repair bucket: {'LAYOUT_FIX': 39, 'PAIRING_FIX': 2, 'STATE_RECIPE_OR_PRODUCT_FIX': 38, 'VISUAL_STYLE_REVIEW': 7}

| Severity | Status | Bucket | Key | Findings | Raw changed | ODiff % | BBox delta | Panel |
|---|---|---|---|---|---:|---:|---:|---|
| high | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:dbt-practice-stop@light | raw_pixel_delta,layout_drift,state_or_recipe_suspect,odiff_delta | 0.70341 | 8.94 | 17 | reports\qa\layered_zip_compare_20260628\panels\suite_dbt-practice-stop_light.png |
| high | FAIL | LAYOUT_FIX | hub:textos-globales@light | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.64067 | 2.09 | 17 | reports\qa\layered_zip_compare_20260628\panels\hub_textos-globales_light.png |
| high | FAIL | LAYOUT_FIX | hub:detalle-plan-timer@dark | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.45219 | 6.04 | 143 | reports\qa\layered_zip_compare_20260628\panels\hub_detalle-plan-timer_dark.png |
| high | FAIL | LAYOUT_FIX | hub:detalle-plan-rutina@dark | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.44947 | 5.25 | 151 | reports\qa\layered_zip_compare_20260628\panels\hub_detalle-plan-rutina_dark.png |
| high | FAIL | LAYOUT_FIX | hub:detalle-plan-timer@light | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.44912 | 5.96 | 142 | reports\qa\layered_zip_compare_20260628\panels\hub_detalle-plan-timer_light.png |
| high | FAIL | LAYOUT_FIX | hub:detalle-plan-rutina@light | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.44284 | 5.05 | 150 | reports\qa\layered_zip_compare_20260628\panels\hub_detalle-plan-rutina_light.png |
| high | FAIL | LAYOUT_FIX | hub:detalle@dark | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.42572 | 5.24 | 111 | reports\qa\layered_zip_compare_20260628\panels\hub_detalle_dark.png |
| high | FAIL | LAYOUT_FIX | suite:home@light | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.4183 | 4.36 | 24 | reports\qa\layered_zip_compare_20260628\panels\suite_home_light.png |
| high | FAIL | LAYOUT_FIX | hub:detalle@light | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.41556 | 5.06 | 110 | reports\qa\layered_zip_compare_20260628\panels\hub_detalle_light.png |
| high | FAIL | LAYOUT_FIX | suite:home-no-score@light | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.4034 | 3.06 | 24 | reports\qa\layered_zip_compare_20260628\panels\suite_home-no-score_light.png |
| high | FAIL | LAYOUT_FIX | hub:detalle-plan-activacion@dark | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.38631 | 3.75 | 43 | reports\qa\layered_zip_compare_20260628\panels\hub_detalle-plan-activacion_dark.png |
| high | FAIL | LAYOUT_FIX | hub:detalle-plan-activacion@light | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.37762 | 3.61 | 42 | reports\qa\layered_zip_compare_20260628\panels\hub_detalle-plan-activacion_light.png |
| high | FAIL | LAYOUT_FIX | hub:pacientes@light | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.36517 | 4.73 | 89 | reports\qa\layered_zip_compare_20260628\panels\hub_pacientes_light.png |
| high | FAIL | LAYOUT_FIX | hub:textos-globales@dark | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.36355 | 2.49 | 17 | reports\qa\layered_zip_compare_20260628\panels\hub_textos-globales_dark.png |
| high | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:onboarding-error@light | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.35589 | 6.18 | 12 | reports\qa\layered_zip_compare_20260628\panels\suite_onboarding-error_light.png |
| high | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:recuperar-acceso@light | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.35191 | 5.24 | 12 | reports\qa\layered_zip_compare_20260628\panels\suite_recuperar-acceso_light.png |
| high | FAIL | LAYOUT_FIX | suite:home@dark | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.32911 | 4.58 | 25 | reports\qa\layered_zip_compare_20260628\panels\suite_home_dark.png |
| high | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:onboarding@light | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.32642 | 5.42 | 3 | reports\qa\layered_zip_compare_20260628\panels\suite_onboarding_light.png |
| high | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:registro-step2-distortions@light | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.32214 | 3.16 | 13 | reports\qa\layered_zip_compare_20260628\panels\suite_registro-step2-distortions_light.png |
| high | FAIL | LAYOUT_FIX | suite:home-no-score@dark | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.31303 | 3.29 | 25 | reports\qa\layered_zip_compare_20260628\panels\suite_home-no-score_dark.png |
| high | FAIL | LAYOUT_FIX | hub:pacientes@dark | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.28366 | 4.93 | 105 | reports\qa\layered_zip_compare_20260628\panels\hub_pacientes_dark.png |
| high | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:registro-step3-filled@light | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.26556 | 3.29 | 3 | reports\qa\layered_zip_compare_20260628\panels\suite_registro-step3-filled_light.png |
| high | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:registro@light | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.2591 | 2.16 | 3 | reports\qa\layered_zip_compare_20260628\panels\suite_registro_light.png |
| high | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:registro-step2-distortions@dark | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.24881 | 3.4 | 58 | reports\qa\layered_zip_compare_20260628\panels\suite_registro-step2-distortions_dark.png |
| high | FAIL | LAYOUT_FIX | hub:pacientes-empty@light | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.22697 | 1.25 | 42 | reports\qa\layered_zip_compare_20260628\panels\hub_pacientes-empty_light.png |
| high | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:dbt-practice-stop@dark | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.21457 | 2.84 | 64 | reports\qa\layered_zip_compare_20260628\panels\suite_dbt-practice-stop_dark.png |
| high | FAIL | LAYOUT_FIX | suite:timer@light | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.21179 | 2.0 | 12 | reports\qa\layered_zip_compare_20260628\panels\suite_timer_light.png |
| high | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:timer-running@light | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.21096 | 2.03 | 12 | reports\qa\layered_zip_compare_20260628\panels\suite_timer-running_light.png |
| high | FAIL | LAYOUT_FIX | suite:avisos@light | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.20995 | 2.07 | 11 | reports\qa\layered_zip_compare_20260628\panels\suite_avisos_light.png |
| high | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:timer-paused@light | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.20778 | 2.03 | 12 | reports\qa\layered_zip_compare_20260628\panels\suite_timer-paused_light.png |
| high | FAIL | VISUAL_STYLE_REVIEW | suite:animo@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.20312 | 4.4 | 12 | reports\qa\layered_zip_compare_20260628\panels\suite_animo_light.png |
| high | SIZE_MISMATCH | PAIRING_FIX | hub:detalle-resumen-ia-0@light | size_mismatch,raw_pixel_delta,state_or_recipe_suspect | 0.20232 |  | 0 | reports\qa\layered_zip_compare_20260628\panels\hub_detalle-resumen-ia-0_light.png |
| high | SIZE_MISMATCH | PAIRING_FIX | hub:detalle-resumen-ia-0@dark | size_mismatch,raw_pixel_delta,state_or_recipe_suspect | 0.1967 |  | 0 | reports\qa\layered_zip_compare_20260628\panels\hub_detalle-resumen-ia-0_dark.png |
| high | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:registro-step1-emotion-otro@light | raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.19019 | 5.63 | 3 | reports\qa\layered_zip_compare_20260628\panels\suite_registro-step1-emotion-otro_light.png |
| high | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:onboarding-error@dark | raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.1876 | 5.71 | 14 | reports\qa\layered_zip_compare_20260628\panels\suite_onboarding-error_dark.png |
| high | FAIL | LAYOUT_FIX | suite:respiracion@light | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.18659 | 1.6 | 12 | reports\qa\layered_zip_compare_20260628\panels\suite_respiracion_light.png |
| high | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:recuperar-acceso@dark | raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.18635 | 5.07 | 14 | reports\qa\layered_zip_compare_20260628\panels\suite_recuperar-acceso_dark.png |
| high | FAIL | VISUAL_STYLE_REVIEW | suite:actividades@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.18507 | 2.44 | 11 | reports\qa\layered_zip_compare_20260628\panels\suite_actividades_light.png |
| high | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:actividades-marked-hice@light | raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.18273 | 2.39 | 11 | reports\qa\layered_zip_compare_20260628\panels\suite_actividades-marked-hice_light.png |
| high | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:respiracion-paused@light | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.1823 | 1.58 | 12 | reports\qa\layered_zip_compare_20260628\panels\suite_respiracion-paused_light.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:avisos-filter-activos@light | raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.17762 | 1.85 | 11 | reports\qa\layered_zip_compare_20260628\panels\suite_avisos-filter-activos_light.png |
| medium | FAIL | LAYOUT_FIX | suite:avisos@dark | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.17693 | 2.24 | 144 | reports\qa\layered_zip_compare_20260628\panels\suite_avisos_dark.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:rutina-add-task@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.17631 | 2.55 | 13 | reports\qa\layered_zip_compare_20260628\panels\suite_rutina-add-task_light.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:onboarding@dark | raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.17505 | 5.18 | 14 | reports\qa\layered_zip_compare_20260628\panels\suite_onboarding_dark.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:respiracion-running@light | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.17315 | 1.61 | 12 | reports\qa\layered_zip_compare_20260628\panels\suite_respiracion-running_light.png |
| medium | FAIL | LAYOUT_FIX | suite:animo@dark | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.1705 | 2.78 | 27 | reports\qa\layered_zip_compare_20260628\panels\suite_animo_dark.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:avisos-today@light | raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.15675 | 1.69 | 11 | reports\qa\layered_zip_compare_20260628\panels\suite_avisos-today_light.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:rutina-all-completed@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.15314 | 2.87 | 2 | reports\qa\layered_zip_compare_20260628\panels\suite_rutina-all-completed_light.png |
| medium | FAIL | LAYOUT_FIX | suite:dbt-library@dark | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.15236 | 3.34 | 60 | reports\qa\layered_zip_compare_20260628\panels\suite_dbt-library_dark.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:actividades-filtered@light | raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.15222 | 1.81 | 11 | reports\qa\layered_zip_compare_20260628\panels\suite_actividades-filtered_light.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:avisos-filter-activos@dark | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.14595 | 1.97 | 220 | reports\qa\layered_zip_compare_20260628\panels\suite_avisos-filter-activos_dark.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:rutina@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.1456 | 2.21 | 13 | reports\qa\layered_zip_compare_20260628\panels\suite_rutina_light.png |
| medium | FAIL | LAYOUT_FIX | suite:actividades@dark | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.143 | 2.59 | 19 | reports\qa\layered_zip_compare_20260628\panels\suite_actividades_dark.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:registro-step1-emotion-otro@dark | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.14207 | 5.64 | 60 | reports\qa\layered_zip_compare_20260628\panels\suite_registro-step1-emotion-otro_dark.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:actividades-marked-hice@dark | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.13985 | 2.55 | 19 | reports\qa\layered_zip_compare_20260628\panels\suite_actividades-marked-hice_dark.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-library@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.13701 | 3.19 | 12 | reports\qa\layered_zip_compare_20260628\panels\suite_dbt-library_light.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:registro-step1-emotion@dark | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.13432 | 5.46 | 60 | reports\qa\layered_zip_compare_20260628\panels\suite_registro-step1-emotion_dark.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:registro-step1-emotion@light | raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.12876 | 5.44 | 3 | reports\qa\layered_zip_compare_20260628\panels\suite_registro-step1-emotion_light.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:avisos-today@dark | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.12776 | 1.81 | 296 | reports\qa\layered_zip_compare_20260628\panels\suite_avisos-today_dark.png |
| medium | FAIL | LAYOUT_FIX | hub:pacientes-empty@dark | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.12378 | 1.35 | 43 | reports\qa\layered_zip_compare_20260628\panels\hub_pacientes-empty_dark.png |
| medium | FAIL | LAYOUT_FIX | suite:dbt-now@dark | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.11628 | 2.18 | 162 | reports\qa\layered_zip_compare_20260628\panels\suite_dbt-now_dark.png |
| medium | FAIL | LAYOUT_FIX | suite:respiracion@dark | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.10942 | 1.68 | 23 | reports\qa\layered_zip_compare_20260628\panels\suite_respiracion_dark.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:respiracion-paused@dark | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.10814 | 1.65 | 23 | reports\qa\layered_zip_compare_20260628\panels\suite_respiracion-paused_dark.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-now@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.10742 | 1.9 | 12 | reports\qa\layered_zip_compare_20260628\panels\suite_dbt-now_light.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:registro-step3-filled@dark | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.10273 | 3.34 | 74 | reports\qa\layered_zip_compare_20260628\panels\suite_registro-step3-filled_dark.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:respiracion-running@dark | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.09707 | 1.69 | 23 | reports\qa\layered_zip_compare_20260628\panels\suite_respiracion-running_dark.png |
| medium | FAIL | LAYOUT_FIX | suite:rutina-add-task@dark | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.09569 | 2.81 | 211 | reports\qa\layered_zip_compare_20260628\panels\suite_rutina-add-task_dark.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:registro@dark | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.09228 | 2.14 | 74 | reports\qa\layered_zip_compare_20260628\panels\suite_registro_dark.png |
| medium | FAIL | LAYOUT_FIX | suite:rutina-all-completed@dark | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.09193 | 3.23 | 211 | reports\qa\layered_zip_compare_20260628\panels\suite_rutina-all-completed_dark.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:registro-success@dark | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.08708 | 1.03 | 131 | reports\qa\layered_zip_compare_20260628\panels\suite_registro-success_dark.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:avisos-search@light | raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.08577 | 0.99 | 11 | reports\qa\layered_zip_compare_20260628\panels\suite_avisos-search_light.png |
| medium | FAIL | LAYOUT_FIX | suite:rutina@dark | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.08561 | 2.52 | 211 | reports\qa\layered_zip_compare_20260628\panels\suite_rutina_dark.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:actividades-filtered@dark | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.08111 | 1.89 | 19 | reports\qa\layered_zip_compare_20260628\panels\suite_actividades-filtered_dark.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:avisos-search@dark | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.06724 | 1.1 | 448 | reports\qa\layered_zip_compare_20260628\panels\suite_avisos-search_dark.png |
| medium | FAIL | LAYOUT_FIX | suite:timer@dark | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.06578 | 2.08 | 21 | reports\qa\layered_zip_compare_20260628\panels\suite_timer_dark.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:timer-running@dark | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.06493 | 2.11 | 21 | reports\qa\layered_zip_compare_20260628\panels\suite_timer-running_dark.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:timer-paused@dark | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.06179 | 2.1 | 21 | reports\qa\layered_zip_compare_20260628\panels\suite_timer-paused_dark.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:registro-success@light | raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.06139 | 1.0 | 13 | reports\qa\layered_zip_compare_20260628\panels\suite_registro-success_light.png |
| medium | FAIL | LAYOUT_FIX | suite:timer-empty@light | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.04063 | 1.17 | 299 | reports\qa\layered_zip_compare_20260628\panels\suite_timer-empty_light.png |
| medium | FAIL | LAYOUT_FIX | suite:rutina-empty@light | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.04036 | 0.95 | 332 | reports\qa\layered_zip_compare_20260628\panels\suite_rutina-empty_light.png |
| medium | FAIL | LAYOUT_FIX | suite:actividades-empty@light | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.0403 | 0.89 | 335 | reports\qa\layered_zip_compare_20260628\panels\suite_actividades-empty_light.png |
| medium | FAIL | LAYOUT_FIX | suite:avisos-empty@light | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.04028 | 0.93 | 335 | reports\qa\layered_zip_compare_20260628\panels\suite_avisos-empty_light.png |
| medium | FAIL | LAYOUT_FIX | suite:timer-empty@dark | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.03361 | 1.33 | 299 | reports\qa\layered_zip_compare_20260628\panels\suite_timer-empty_dark.png |
| medium | FAIL | LAYOUT_FIX | suite:actividades-empty@dark | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.03241 | 0.95 | 337 | reports\qa\layered_zip_compare_20260628\panels\suite_actividades-empty_dark.png |
| medium | FAIL | LAYOUT_FIX | suite:rutina-empty@dark | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.0324 | 1.03 | 333 | reports\qa\layered_zip_compare_20260628\panels\suite_rutina-empty_dark.png |
| medium | FAIL | LAYOUT_FIX | suite:avisos-empty@dark | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.03234 | 0.99 | 337 | reports\qa\layered_zip_compare_20260628\panels\suite_avisos-empty_dark.png |
