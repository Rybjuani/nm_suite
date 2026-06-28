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
- [x] 02. `suite:onboarding-error@light` - Parcial `5f0add1`. Checkbox ahora desmarcado (canónico); borde rose en campo Nombre. Divergencia restante: texto legal más extenso (decisión de producto).
- [x] 03. `suite:recuperar-acceso@light` - STALE: fidelity PASS al recapturar.
- [x] 04. `suite:onboarding@light` - Parcial `023b9680`. Checkbox movido fuera de consent_card (estructura canonica); divergencia restante: texto legal más extenso que mockup.
- [x] 05. `suite:registro-step2-distortions@light` - STALE: fidelity PASS al recapturar.
- [x] 06. `suite:registro-step3-filled@light` - STALE: fidelity PASS al recapturar.
- [x] 07. `suite:registro@light` - STALE: fidelity PASS al recapturar.
- [x] 08. `suite:registro-step2-distortions@dark` - STALE: fidelity PASS al recapturar.
- [x] 09. `suite:dbt-practice-stop@dark` - Corregido en f2b896f. Misma corrección de scrim que item 01; mismo codigo.
- [x] 10. `suite:timer-running@light` - Corregido en `023b9680`. Helper _timer_snap_to_initial resetea display a 25:00; estado=Sesión en curso + pausa icon.
- [x] 11. `suite:timer-paused@light` - Corregido en `023b9680`. Helper _timer_set_paused_display fija remaining_sec=912 (15:12); estado=En pausa + play icon.
- [x] 12. `suite:registro-step1-emotion-otro@light` - STALE: fidelity PASS al recapturar.
- [x] 13. `suite:onboarding-error@dark` - Cubierto por `5f0add1`. Misma corrección que item 02; dark theme usa el mismo recipe.
- [x] 14. `suite:recuperar-acceso@dark` - STALE: fidelity PASS al recapturar.
- [x] 15. `suite:actividades-marked-hice@light` - STALE: fidelity PASS al recapturar.
- [x] 16. `suite:respiracion-paused@light` - Corregido en `023b9680`. Helper _respiracion_set_paused_display → CRONO 01:32, CICLOS 4 (coincide canonico).
- [x] 17. `suite:avisos-filter-activos@light` - STALE: fidelity PASS al recapturar.
- [x] 18. `suite:onboarding@dark` - STALE: fidelity PASS al recapturar.
- [x] 19. `suite:respiracion-running@light` - Corregido en `3f48360`. Eliminado NMCard wrapper de la práctica; contenido flota sobre fondo beige como en el canónico.
- [x] 20. `suite:avisos-today@light` - STALE: fidelity PASS al recapturar.
- [x] 21. `suite:actividades-filtered@light` - Corregido en `023b9680`. Cambia categoria a Fisica, corrige canonicalizacion de label; muestra Caminata 20 min.
- [x] 22. `suite:avisos-filter-activos@dark` - STALE: fidelity PASS al recapturar.
- [x] 23. `suite:registro-step1-emotion-otro@dark` - STALE: fidelity PASS al recapturar.
- [x] 24. `suite:actividades-marked-hice@dark` - STALE: fidelity PASS al recapturar.
- [x] 25. `suite:registro-step1-emotion@dark` - STALE: fidelity PASS al recapturar.
- [x] 26. `suite:registro-step1-emotion@light` - STALE: fidelity PASS al recapturar.
- [x] 27. `suite:avisos-today@dark` - STALE: fidelity PASS al recapturar.
- [x] 28. `suite:respiracion-paused@dark` - Cubierto por `023b9680`. Mismo helper _respiracion_set_paused_display que item 16; dark theme usa el mismo código.
- [x] 29. `suite:registro-step3-filled@dark` - STALE: fidelity PASS al recapturar.
- [x] 30. `suite:respiracion-running@dark` - Cubierto por `3f48360`. Misma corrección que item 19; dark theme usa el mismo código.
- [x] 31. `suite:registro@dark` - STALE: fidelity PASS al recapturar.
- [x] 32. `suite:registro-success@dark` - STALE: fidelity PASS al recapturar.
- [x] 33. `suite:avisos-search@light` - STALE: fidelity PASS al recapturar.
- [x] 34. `suite:actividades-filtered@dark` - Cubierto por `023b9680`. Misma receta y canonicalización de categoría que item 21; dark theme usa el mismo código.
- [x] 35. `suite:avisos-search@dark` - STALE: fidelity PASS al recapturar.
- [x] 36. `suite:timer-running@dark` - Cubierto por `023b9680`. Misma receta y helpers que item 10; dark theme usa el mismo código.
- [x] 37. `suite:timer-paused@dark` - Cubierto por `023b9680`. Misma receta y helpers que item 11; dark theme usa el mismo código.
- [x] 38. `suite:registro-success@light` - STALE: fidelity PASS al recapturar.

### 2. Layout Estructural

- [x] 39. `hub:textos-globales@light` - STALE: fidelity PASS al recapturar (divergencia en datos, no en código).
- [x] 40. `hub:detalle-plan-timer@dark` - STALE: fidelity PASS al recapturar.
- [x] 41. `hub:detalle-plan-rutina@dark` - STALE: fidelity PASS al recapturar.
- [x] 42. `hub:detalle-plan-timer@light` - STALE: fidelity PASS al recapturar.
- [x] 43. `hub:detalle-plan-rutina@light` - STALE: fidelity PASS al recapturar.
- [x] 44. `hub:detalle@dark` - STALE: fidelity PASS al recapturar.
- [x] 45. `suite:home@light` - Corregido en `a8c4fd6`. Hero compactado (maxH 178→138, margins 18→10, gap 18→12, top 24→16).
- [x] 46. `hub:detalle@light` - STALE: fidelity PASS al recapturar.
- [x] 47. `suite:home-no-score@light` - Cubierto por `a8c4fd6`. Misma corrección que item 45.
- [x] 48. `hub:detalle-plan-activacion@dark` - STALE: fidelity PASS al recapturar.
- [x] 49. `hub:detalle-plan-activacion@light` - STALE: fidelity PASS al recapturar.
- [x] 50. `hub:pacientes@light` - STALE: fidelity PASS al recapturar.
- [x] 51. `hub:textos-globales@dark` - STALE: fidelity PASS al recapturar.
- [x] 52. `suite:home@dark` - Cubierto por `a8c4fd6`. Misma corrección que item 45.
- [x] 53. `suite:home-no-score@dark` - Cubierto por `a8c4fd6`. Misma corrección que item 45.
- [x] 54. `hub:pacientes@dark` - STALE: fidelity PASS al recapturar.
- [x] 55. `hub:pacientes-empty@light` - STALE: fidelity PASS al recapturar.
- [x] 56. `suite:timer@light` - STALE: fidelity PASS al recapturar.
- [x] 57. `suite:avisos@light` - STALE: fidelity PASS al recapturar.
- [x] 58. `suite:respiracion@light` - Corregido en `3f48360`. Eliminado NMCard wrapper; layout ahora flat sobre fondo.
- [x] 59. `suite:avisos@dark` - STALE: fidelity PASS al recapturar.
- [x] 60. `suite:animo@dark` - STALE: fidelity PASS al recapturar.
- [x] 61. `suite:dbt-library@dark` - STALE: fidelity PASS al recapturar.
- [x] 62. `suite:actividades@dark` - STALE: fidelity PASS al recapturar.
- [x] 63. `hub:pacientes-empty@dark` - STALE: fidelity PASS al recapturar.
- [x] 64. `suite:dbt-now@dark` - STALE: fidelity PASS al recapturar.
- [x] 65. `suite:respiracion@dark` - Cubierto por `3f48360`. Misma corrección que item 58; dark theme usa el mismo código.
- [x] 66. `suite:rutina-add-task@dark` - STALE: fidelity PASS al recapturar.
- [x] 67. `suite:rutina-all-completed@dark` - STALE: fidelity PASS al recapturar.
- [x] 68. `suite:rutina@dark` - STALE: fidelity PASS al recapturar.
- [x] 69. `suite:timer@dark` - STALE: fidelity PASS al recapturar.
- [x] 70. `suite:timer-empty@light` - STALE: fidelity PASS al recapturar.
- [x] 71. `suite:rutina-empty@light` - STALE: fidelity PASS al recapturar.
- [x] 72. `suite:actividades-empty@light` - STALE: fidelity PASS al recapturar.
- [x] 73. `suite:avisos-empty@light` - STALE: fidelity PASS al recapturar.
- [x] 74. `suite:timer-empty@dark` - STALE: fidelity PASS al recapturar.
- [x] 75. `suite:actividades-empty@dark` - STALE: fidelity PASS al recapturar.
- [x] 76. `suite:rutina-empty@dark` - STALE: fidelity PASS al recapturar.
- [x] 77. `suite:avisos-empty@dark` - STALE: fidelity PASS al recapturar.

### 3. Pairing / Captura / Tamano

- [ ] 78. `hub:detalle-resumen-ia-0@light` - `PAIRING_FIX`, high. Raw changed `0.20232`, canonico `560x220`, V8 `480x325`. Findings: `size_mismatch`, `raw_pixel_delta`, `state_or_recipe_suspect`. Actualizar runtime/captura de Resumen IA a tamano canonico.
- [ ] 79. `hub:detalle-resumen-ia-0@dark` - `PAIRING_FIX`, high. Raw changed `0.1967`, canonico `560x220`, V8 `480x325`. Findings: `size_mismatch`, `raw_pixel_delta`, `state_or_recipe_suspect`. Actualizar runtime/captura de Resumen IA a tamano canonico.

### 4. Estilo Visual Localizado

- [x] 80. `suite:animo@light` - STALE: fidelity PASS al recapturar.
- [x] 81. `suite:actividades@light` - STALE: fidelity PASS al recapturar.
- [x] 82. `suite:rutina-add-task@light` - STALE: fidelity PASS al recapturar.
- [x] 83. `suite:rutina-all-completed@light` - STALE: fidelity PASS al recapturar.
- [x] 84. `suite:rutina@light` - STALE: fidelity PASS al recapturar.
- [x] 85. `suite:dbt-library@light` - STALE: fidelity PASS al recapturar.
- [x] 86. `suite:dbt-now@light` - STALE: fidelity PASS al recapturar.

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
