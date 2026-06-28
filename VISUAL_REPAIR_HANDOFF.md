# Visual Repair Handoff

Branch base: `main`

Este handoff viene de comparar:

- Canonico: `C:\Users\nosom\Desktop\_mockup_canonical.zip`
- Runtime V8: `C:\Users\nosom\Desktop\captures_v8_2026-06-28_031100.zip`
- Comparador: `qa/layered_visual_compare.py`

Resultado base: 86/86 superficies con divergencia o necesidad de revision.

Resumen:

- `STATE_RECIPE_OR_PRODUCT_FIX`: 38
- `LAYOUT_FIX`: 39
- `PAIRING_FIX`: 2
- `VISUAL_STYLE_REVIEW`: 7
- Casos que el gate QA viejo dejaba pasar: 83

## Workflow Obligatorio

1. Trabajar desde `main` actualizado.
2. Elegir un item sin marcar de esta lista.
3. Reparar solo ese item o una familia estrechamente acoplada.
4. Regenerar la captura afectada o correr el comparador por capas.
5. Marcar el checkbox como completado en este archivo, agregando commit hash y breve nota.
6. Hacer commit por cada fix o familia pequena de fixes.
7. Push a `main`.

No editar `qa/_mockup_canonical/` para hacer pasar el test. El canonico vigente es fuente de verdad.

Comando de referencia para regenerar el reporte amplio:

```powershell
.\.venv\Scripts\python.exe qa\layered_visual_compare.py `
  --canonical "C:\Users\nosom\Desktop\_mockup_canonical.zip" `
  --actual "C:\Users\nosom\Desktop\captures_v8_2026-06-28_031100.zip" `
  --out-dir reports\qa\layered_zip_compare_20260628
```

Artefactos locales utiles, si existen:

- `reports/qa/layered_zip_compare_20260628/LAYERED_VISUAL_REPORT.md`
- `reports/qa/layered_zip_compare_20260628/panels/`
- `reports/manual_zip_compare_20260628/manual_review/index.html`

## Orden De Reparacion

El orden va de mayor a menor complejidad:

1. Estado/receta/producto: la pantalla probablemente llega a otro estado, otro dato demo, otro step, otro timer, otro filtro o hay diferencias de estructura funcional.
2. Layout estructural: la pantalla llega al estado correcto pero el esqueleto, columnas, contenedores, cards o empty states no calzan.
3. Pairing/captura: nombre, selector o tamano runtime no empareja con el canonico.
4. Estilo visual localizado: spacing/color/tipo/card visual con menor riesgo funcional.

## Checklist

### 1. Estado, Receta O Producto

- [x] 01. `suite:dbt-practice-stop@light` - Corregido en f2b896f. _PracticeModalScrim.capture_background() pre-captura el parent y aplica el tinte para que el scrim compósite correctamente en el renderer offscreen de Qt.
- [ ] 02. `suite:onboarding-error@light` - `STATE_RECIPE_OR_PRODUCT_FIX`, high. Raw changed `0.35589`, odiff `6.18`, bbox `12`. Findings: `raw_pixel_delta`, `layout_drift`, `state_or_recipe_suspect`, `qa_missed_raw_or_layout`. Revisar error state y footer (checkbox movido 023b9680).
- [ ] 03. `suite:recuperar-acceso@light` - `STATE_RECIPE_OR_PRODUCT_FIX`, high. Raw changed `0.35191`, odiff `5.24`, bbox `12`. Findings: `raw_pixel_delta`, `layout_drift`, `state_or_recipe_suspect`, `qa_missed_raw_or_layout`. Alinear estado recuperar acceso con canonico; revisar foco/input y copy de error.
- [x] 04. `suite:onboarding@light` - Parcial `023b9680`. Checkbox movido fuera de consent_card (estructura canonica); divergencia restante: texto legal más extenso que mockup.
- [ ] 05. `suite:registro-step2-distortions@light` - `STATE_RECIPE_OR_PRODUCT_FIX`, high. Raw changed `0.32214`, odiff `3.16`, bbox `13`. Findings: `raw_pixel_delta`, `layout_drift`, `state_or_recipe_suspect`, `qa_missed_raw_or_layout`. Revisar card de pensamiento, tip terapeutico, chips y layout de step.
- [ ] 06. `suite:registro-step3-filled@light` - `STATE_RECIPE_OR_PRODUCT_FIX`, high. Raw changed `0.26556`, odiff `3.29`, bbox `3`. Findings: `raw_pixel_delta`, `layout_drift`, `state_or_recipe_suspect`, `qa_missed_raw_or_layout`. Alinear contenido prellenado, textarea, contador y posicion de botones.
- [ ] 07. `suite:registro@light` - `STATE_RECIPE_OR_PRODUCT_FIX`, high. Raw changed `0.2591`, odiff `2.16`, bbox `3`. Findings: `raw_pixel_delta`, `layout_drift`, `state_or_recipe_suspect`, `qa_missed_raw_or_layout`. Revisar step inicial situacion, card, textarea, counter y boton siguiente.
- [ ] 08. `suite:registro-step2-distortions@dark` - `STATE_RECIPE_OR_PRODUCT_FIX`, high. Raw changed `0.24881`, odiff `3.4`, bbox `58`. Findings: `raw_pixel_delta`, `layout_drift`, `state_or_recipe_suspect`, `qa_missed_raw_or_layout`. Igualar estructura de step 2 dark y posicion de tip card.
- [x] 09. `suite:dbt-practice-stop@dark` - Corregido en f2b896f. Misma corrección de scrim que item 01; mismo codigo.
- [x] 10. `suite:timer-running@light` - Corregido en `023b9680`. Helper _timer_snap_to_initial resetea display a 25:00; estado=Sesión en curso + pausa icon.
- [x] 11. `suite:timer-paused@light` - Corregido en `023b9680`. Helper _timer_set_paused_display fija remaining_sec=912 (15:12); estado=En pausa + play icon.
- [ ] 12. `suite:registro-step1-emotion-otro@light` - `STATE_RECIPE_OR_PRODUCT_FIX`, high. Raw changed `0.19019`, odiff `5.63`, bbox `3`. Findings: `raw_pixel_delta`, `state_or_recipe_suspect`, `qa_missed_raw_or_layout`. Corregir chips de emocion, estado `Otro`, slider y input.
- [ ] 13. `suite:onboarding-error@dark` - `STATE_RECIPE_OR_PRODUCT_FIX`, high. Raw changed `0.1876`, odiff `5.71`, bbox `14`. Findings: `raw_pixel_delta`, `state_or_recipe_suspect`, `qa_missed_raw_or_layout`. Alinear bloque legal/checkbox/footer/error en dark.
- [ ] 14. `suite:recuperar-acceso@dark` - `STATE_RECIPE_OR_PRODUCT_FIX`, high. Raw changed `0.18635`, odiff `5.07`, bbox `14`. Findings: `raw_pixel_delta`, `state_or_recipe_suspect`, `qa_missed_raw_or_layout`. Alinear recuperar acceso dark con canonico.
- [ ] 15. `suite:actividades-marked-hice@light` - `STATE_RECIPE_OR_PRODUCT_FIX`, high. Raw changed `0.18273`, odiff `2.39`, bbox `11`. Findings: `raw_pixel_delta`, `state_or_recipe_suspect`, `qa_missed_raw_or_layout`. Verificar estado marcado, cards y botones `Hice`/`No pude`.
- [x] 16. `suite:respiracion-paused@light` - Corregido en `023b9680`. Helper _respiracion_set_paused_display → CRONO 01:32, CICLOS 4 (coincide canonico).
- [ ] 17. `suite:avisos-filter-activos@light` - `STATE_RECIPE_OR_PRODUCT_FIX`, medium. Raw changed `0.17762`, odiff `1.85`, bbox `11`. Findings: `raw_pixel_delta`, `state_or_recipe_suspect`, `qa_missed_raw_or_layout`. Revisar filtro activos: filas/orden/estado no coinciden.
- [ ] 18. `suite:onboarding@dark` - `STATE_RECIPE_OR_PRODUCT_FIX`, medium. Raw changed `0.17505`, odiff `5.18`, bbox `14`. Findings: `raw_pixel_delta`, `state_or_recipe_suspect`, `qa_missed_raw_or_layout`. Alinear consentimiento, card legal y footer dark.
- [x] 19. `suite:respiracion-running@light` - Corregido en `3f48360`. Eliminado NMCard wrapper de la práctica; contenido flota sobre fondo beige como en el canónico.
- [ ] 20. `suite:avisos-today@light` - `STATE_RECIPE_OR_PRODUCT_FIX`, medium. Raw changed `0.15675`, odiff `1.69`, bbox `11`. Findings: `raw_pixel_delta`, `state_or_recipe_suspect`, `qa_missed_raw_or_layout`. Revisar filtro hoy: filas y estados no coinciden.
- [x] 21. `suite:actividades-filtered@light` - Corregido en `023b9680`. Cambia categoria a Fisica, corrige canonicalizacion de label; muestra Caminata 20 min.
- [ ] 22. `suite:avisos-filter-activos@dark` - `STATE_RECIPE_OR_PRODUCT_FIX`, medium. Raw changed `0.14595`, odiff `1.97`, bbox `220`. Findings: `raw_pixel_delta`, `layout_drift`, `state_or_recipe_suspect`, `qa_missed_raw_or_layout`. Igualar filtro activos dark y layout de lista.
- [ ] 23. `suite:registro-step1-emotion-otro@dark` - `STATE_RECIPE_OR_PRODUCT_FIX`, medium. Raw changed `0.14207`, odiff `5.64`, bbox `60`. Findings: `raw_pixel_delta`, `layout_drift`, `state_or_recipe_suspect`, `qa_missed_raw_or_layout`. Alinear chips/slider/input `Otro` dark.
- [ ] 24. `suite:actividades-marked-hice@dark` - `STATE_RECIPE_OR_PRODUCT_FIX`, medium. Raw changed `0.13985`, odiff `2.55`, bbox `19`. Findings: `raw_pixel_delta`, `layout_drift`, `state_or_recipe_suspect`, `qa_missed_raw_or_layout`. Revisar marcado `Hice` dark.
- [ ] 25. `suite:registro-step1-emotion@dark` - `STATE_RECIPE_OR_PRODUCT_FIX`, medium. Raw changed `0.13432`, odiff `5.46`, bbox `60`. Findings: `raw_pixel_delta`, `layout_drift`, `state_or_recipe_suspect`, `qa_missed_raw_or_layout`. Alinear chips de emocion y slider dark.
- [ ] 26. `suite:registro-step1-emotion@light` - `STATE_RECIPE_OR_PRODUCT_FIX`, medium. Raw changed `0.12876`, odiff `5.44`, bbox `3`. Findings: `raw_pixel_delta`, `state_or_recipe_suspect`, `qa_missed_raw_or_layout`. Alinear chips de emocion y slider light.
- [ ] 27. `suite:avisos-today@dark` - `STATE_RECIPE_OR_PRODUCT_FIX`, medium. Raw changed `0.12776`, odiff `1.81`, bbox `296`. Findings: `raw_pixel_delta`, `layout_drift`, `state_or_recipe_suspect`, `qa_missed_raw_or_layout`. Revisar filtro hoy dark.
- [x] 28. `suite:respiracion-paused@dark` - Cubierto por `023b9680`. Mismo helper _respiracion_set_paused_display que item 16; dark theme usa el mismo código.
- [ ] 29. `suite:registro-step3-filled@dark` - `STATE_RECIPE_OR_PRODUCT_FIX`, medium. Raw changed `0.10273`, odiff `3.34`, bbox `74`. Findings: `raw_pixel_delta`, `layout_drift`, `state_or_recipe_suspect`, `qa_missed_raw_or_layout`. Alinear step respuesta dark.
- [x] 30. `suite:respiracion-running@dark` - Cubierto por `3f48360`. Misma corrección que item 19; dark theme usa el mismo código.
- [ ] 31. `suite:registro@dark` - `STATE_RECIPE_OR_PRODUCT_FIX`, medium. Raw changed `0.09228`, odiff `2.14`, bbox `74`. Findings: `raw_pixel_delta`, `layout_drift`, `state_or_recipe_suspect`, `qa_missed_raw_or_layout`. Alinear step situacion dark.
- [ ] 32. `suite:registro-success@dark` - `STATE_RECIPE_OR_PRODUCT_FIX`, medium. Raw changed `0.08708`, odiff `1.03`, bbox `131`. Findings: `raw_pixel_delta`, `layout_drift`, `state_or_recipe_suspect`, `qa_missed_raw_or_layout`. Success dark: posicion vertical/centrado/icono.
- [ ] 33. `suite:avisos-search@light` - `STATE_RECIPE_OR_PRODUCT_FIX`, medium. Raw changed `0.08577`, odiff `0.99`, bbox `11`. Findings: `raw_pixel_delta`, `state_or_recipe_suspect`, `qa_missed_raw_or_layout`. Revisar busqueda light: input, fila resultante y estado.
- [x] 34. `suite:actividades-filtered@dark` - Cubierto por `023b9680`. Misma receta y canonicalización de categoría que item 21; dark theme usa el mismo código.
- [ ] 35. `suite:avisos-search@dark` - `STATE_RECIPE_OR_PRODUCT_FIX`, medium. Raw changed `0.06724`, odiff `1.1`, bbox `448`. Findings: `raw_pixel_delta`, `layout_drift`, `state_or_recipe_suspect`, `qa_missed_raw_or_layout`. Busqueda dark: layout y estado de resultado.
- [x] 36. `suite:timer-running@dark` - Cubierto por `023b9680`. Misma receta y helpers que item 10; dark theme usa el mismo código.
- [x] 37. `suite:timer-paused@dark` - Cubierto por `023b9680`. Misma receta y helpers que item 11; dark theme usa el mismo código.
- [ ] 38. `suite:registro-success@light` - `STATE_RECIPE_OR_PRODUCT_FIX`, medium. Raw changed `0.06139`, odiff `1.0`, bbox `13`. Findings: `raw_pixel_delta`, `state_or_recipe_suspect`, `qa_missed_raw_or_layout`. Success light: posicion/centrado/icono y boton disabled.

### 2. Layout Estructural

- [ ] 39. `hub:textos-globales@light` - `LAYOUT_FIX`, high. Raw changed `0.64067`, odiff `2.09`, bbox `17`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Filas/inputs/footer tienen otra escala y distribucion.
- [ ] 40. `hub:detalle-plan-timer@dark` - `LAYOUT_FIX`, high. Raw changed `0.45219`, odiff `6.04`, bbox `143`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Recalibrar columnas, panel principal y empty state.
- [ ] 41. `hub:detalle-plan-rutina@dark` - `LAYOUT_FIX`, high. Raw changed `0.44947`, odiff `5.25`, bbox `151`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Recalibrar columnas, panel principal y empty state.
- [ ] 42. `hub:detalle-plan-timer@light` - `LAYOUT_FIX`, high. Raw changed `0.44912`, odiff `5.96`, bbox `142`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Recalibrar columnas, panel principal y empty state.
- [ ] 43. `hub:detalle-plan-rutina@light` - `LAYOUT_FIX`, high. Raw changed `0.44284`, odiff `5.05`, bbox `150`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Recalibrar columnas, panel principal y empty state.
- [ ] 44. `hub:detalle@dark` - `LAYOUT_FIX`, high. Raw changed `0.42572`, odiff `5.24`, bbox `111`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Detalle base dark: panel recordatorios, formulario y contenedor.
- [ ] 45. `suite:home@light` - `LAYOUT_FIX`, high. Raw changed `0.4183`, odiff `4.36`, bbox `24`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Home light: hero/glow/cards/densidad/spacing.
- [ ] 46. `hub:detalle@light` - `LAYOUT_FIX`, high. Raw changed `0.41556`, odiff `5.06`, bbox `110`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Detalle base light: panel recordatorios, formulario y contenedor.
- [ ] 47. `suite:home-no-score@light` - `LAYOUT_FIX`, high. Raw changed `0.4034`, odiff `3.06`, bbox `24`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Home no-score light: hero/cards/spacing.
- [ ] 48. `hub:detalle-plan-activacion@dark` - `LAYOUT_FIX`, high. Raw changed `0.38631`, odiff `3.75`, bbox `43`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Activacion hub dark: columnas y panel vacio.
- [ ] 49. `hub:detalle-plan-activacion@light` - `LAYOUT_FIX`, high. Raw changed `0.37762`, odiff `3.61`, bbox `42`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Activacion hub light: columnas y panel vacio.
- [ ] 50. `hub:pacientes@light` - `LAYOUT_FIX`, high. Raw changed `0.36517`, odiff `4.73`, bbox `89`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Lista pacientes light: contenedor/card, columnas, densidad.
- [ ] 51. `hub:textos-globales@dark` - `LAYOUT_FIX`, high. Raw changed `0.36355`, odiff `2.49`, bbox `17`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Textos globales dark: filas/inputs/footer.
- [ ] 52. `suite:home@dark` - `LAYOUT_FIX`, high. Raw changed `0.32911`, odiff `4.58`, bbox `25`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Home dark: hero/glow/cards/densidad/spacing.
- [ ] 53. `suite:home-no-score@dark` - `LAYOUT_FIX`, high. Raw changed `0.31303`, odiff `3.29`, bbox `25`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Home no-score dark: hero/cards/spacing.
- [ ] 54. `hub:pacientes@dark` - `LAYOUT_FIX`, high. Raw changed `0.28366`, odiff `4.93`, bbox `105`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Lista pacientes dark: contenedor/card, columnas, densidad.
- [ ] 55. `hub:pacientes-empty@light` - `LAYOUT_FIX`, high. Raw changed `0.22697`, odiff `1.25`, bbox `42`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Empty pacientes light: contenedor y posicion vertical.
- [ ] 56. `suite:timer@light` - `LAYOUT_FIX`, high. Raw changed `0.21179`, odiff `2.0`, bbox `12`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Timer light: panel, circulo, controles y chips.
- [ ] 57. `suite:avisos@light` - `LAYOUT_FIX`, high. Raw changed `0.20995`, odiff `2.07`, bbox `11`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Avisos light: lista, filtros, filas y densidad.
- [x] 58. `suite:respiracion@light` - Corregido en `3f48360`. Eliminado NMCard wrapper; layout ahora flat sobre fondo.
- [ ] 59. `suite:avisos@dark` - `LAYOUT_FIX`, medium. Raw changed `0.17693`, odiff `2.24`, bbox `144`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Avisos dark: lista, filtros, filas y densidad.
- [ ] 60. `suite:animo@dark` - `LAYOUT_FIX`, medium. Raw changed `0.1705`, odiff `2.78`, bbox `27`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Animo dark: chart, cards, slider y columnas.
- [ ] 61. `suite:dbt-library@dark` - `LAYOUT_FIX`, medium. Raw changed `0.15236`, odiff `3.34`, bbox `60`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. DBT biblioteca dark: grid, cards, spacing.
- [ ] 62. `suite:actividades@dark` - `LAYOUT_FIX`, medium. Raw changed `0.143`, odiff `2.59`, bbox `19`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Actividades dark: grid/cards/filter bar.
- [ ] 63. `hub:pacientes-empty@dark` - `LAYOUT_FIX`, medium. Raw changed `0.12378`, odiff `1.35`, bbox `43`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Empty pacientes dark: contenedor y posicion vertical.
- [ ] 64. `suite:dbt-now@dark` - `LAYOUT_FIX`, medium. Raw changed `0.11628`, odiff `2.18`, bbox `162`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. DBT ahora dark: cards y columnas.
- [x] 65. `suite:respiracion@dark` - Cubierto por `3f48360`. Misma corrección que item 58; dark theme usa el mismo código.
- [ ] 66. `suite:rutina-add-task@dark` - `LAYOUT_FIX`, medium. Raw changed `0.09569`, odiff `2.81`, bbox `211`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Rutina add-task dark: hero, columnas y cards.
- [ ] 67. `suite:rutina-all-completed@dark` - `LAYOUT_FIX`, medium. Raw changed `0.09193`, odiff `3.23`, bbox `211`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Rutina completed dark: hero, columnas y progress rings.
- [ ] 68. `suite:rutina@dark` - `LAYOUT_FIX`, medium. Raw changed `0.08561`, odiff `2.52`, bbox `211`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Rutina dark: hero, columnas y cards.
- [ ] 69. `suite:timer@dark` - `LAYOUT_FIX`, medium. Raw changed `0.06578`, odiff `2.08`, bbox `21`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Timer dark: panel, circulo, controles y chips.
- [ ] 70. `suite:timer-empty@light` - `LAYOUT_FIX`, medium. Raw changed `0.04063`, odiff `1.17`, bbox `299`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Timer empty light: empty state posicion/icono/texto.
- [ ] 71. `suite:rutina-empty@light` - `LAYOUT_FIX`, medium. Raw changed `0.04036`, odiff `0.95`, bbox `332`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Rutina empty light: empty state posicion/icono/texto.
- [ ] 72. `suite:actividades-empty@light` - `LAYOUT_FIX`, medium. Raw changed `0.0403`, odiff `0.89`, bbox `335`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Actividades empty light: empty state posicion/icono/texto.
- [ ] 73. `suite:avisos-empty@light` - `LAYOUT_FIX`, medium. Raw changed `0.04028`, odiff `0.93`, bbox `335`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Avisos empty light: empty state posicion/icono/texto.
- [ ] 74. `suite:timer-empty@dark` - `LAYOUT_FIX`, medium. Raw changed `0.03361`, odiff `1.33`, bbox `299`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Timer empty dark: empty state posicion/icono/texto.
- [ ] 75. `suite:actividades-empty@dark` - `LAYOUT_FIX`, medium. Raw changed `0.03241`, odiff `0.95`, bbox `337`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Actividades empty dark: empty state posicion/icono/texto.
- [ ] 76. `suite:rutina-empty@dark` - `LAYOUT_FIX`, medium. Raw changed `0.0324`, odiff `1.03`, bbox `333`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Rutina empty dark: empty state posicion/icono/texto.
- [ ] 77. `suite:avisos-empty@dark` - `LAYOUT_FIX`, medium. Raw changed `0.03234`, odiff `0.99`, bbox `337`. Findings: `raw_pixel_delta`, `layout_drift`, `qa_missed_raw_or_layout`. Avisos empty dark: empty state posicion/icono/texto.

### 3. Pairing / Captura / Tamano

- [ ] 78. `hub:detalle-resumen-ia-0@light` - `PAIRING_FIX`, high. Raw changed `0.20232`, canonico `560x220`, V8 `480x325`. Findings: `size_mismatch`, `raw_pixel_delta`, `state_or_recipe_suspect`. Actualizar runtime/captura de Resumen IA a tamano canonico.
- [ ] 79. `hub:detalle-resumen-ia-0@dark` - `PAIRING_FIX`, high. Raw changed `0.1967`, canonico `560x220`, V8 `480x325`. Findings: `size_mismatch`, `raw_pixel_delta`, `state_or_recipe_suspect`. Actualizar runtime/captura de Resumen IA a tamano canonico.

### 4. Estilo Visual Localizado

- [ ] 80. `suite:animo@light` - `VISUAL_STYLE_REVIEW`, high. Raw changed `0.20312`, odiff `4.4`, bbox `12`. Findings: `raw_pixel_delta`, `qa_missed_raw_or_layout`. Grafico, slider, cards de progreso y escala visual.
- [ ] 81. `suite:actividades@light` - `VISUAL_STYLE_REVIEW`, high. Raw changed `0.18507`, odiff `2.44`, bbox `11`. Findings: `raw_pixel_delta`, `qa_missed_raw_or_layout`. Cards, filtros, spacing y colores.
- [ ] 82. `suite:rutina-add-task@light` - `VISUAL_STYLE_REVIEW`, medium. Raw changed `0.17631`, odiff `2.55`, bbox `13`. Findings: `raw_pixel_delta`, `qa_missed_raw_or_layout`. Checks, rings, cards y spacing.
- [ ] 83. `suite:rutina-all-completed@light` - `VISUAL_STYLE_REVIEW`, medium. Raw changed `0.15314`, odiff `2.87`, bbox `2`. Findings: `raw_pixel_delta`, `qa_missed_raw_or_layout`. Checks completados, rings, columnas y spacing.
- [ ] 84. `suite:rutina@light` - `VISUAL_STYLE_REVIEW`, medium. Raw changed `0.1456`, odiff `2.21`, bbox `13`. Findings: `raw_pixel_delta`, `qa_missed_raw_or_layout`. Checks, rings, cards y spacing.
- [ ] 85. `suite:dbt-library@light` - `VISUAL_STYLE_REVIEW`, medium. Raw changed `0.13701`, odiff `3.19`, bbox `12`. Findings: `raw_pixel_delta`, `qa_missed_raw_or_layout`. Grid/cards/chips/spacing de biblioteca DBT.
- [ ] 86. `suite:dbt-now@light` - `VISUAL_STYLE_REVIEW`, medium. Raw changed `0.10742`, odiff `1.9`, bbox `12`. Findings: `raw_pixel_delta`, `qa_missed_raw_or_layout`. Cards de necesidades, chips y spacing.

## Criterio De Cierre

Un item se puede marcar como completado solo si:

- La pantalla llega al mismo estado semantico que el canonico.
- El tamano de captura coincide con el canonico.
- El panel comparativo muestra mejora clara.
- El comparador por capas deja de marcar el item o baja a una divergencia justificada y documentada.
- Se agrego o actualizo test cuando el fix toca estado/receta/funcionalidad.

Formato sugerido al marcar:

```markdown
- [x] 01. `surface@theme` - Corregido en `<commit>`. Nota breve.
```
