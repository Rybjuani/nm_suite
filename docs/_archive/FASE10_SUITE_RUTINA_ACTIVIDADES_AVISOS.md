# Fase 10 — Suite Rutina, Actividades y Avisos

## Objetivo (PLAN FASEADO §Fase 10)
- Rutina: menos columnas comprimidas, checkboxes y acciones legibles, empty state coherente.
- Actividades: cards menos apretadas, `No pude` y `Hice` con jerarquía equivalente, filtros y empty state deterministas.
- Avisos: eliminar duplicación visual `Completado`/`Hecho`, filtros/badges/acciones claros, listas cortas sin vacío absurdo.

## Cambios Aplicados

### Actividades — `No pude` y `Hice` con jerarquía equivalente (`app/modules/actividades_qt.py`)
- **Problema:** `_btn_yes` ("Hice") era `variant="primary"` (gradient dominante) frente a `_btn_no` ("No pude") `variant="secondary"` (outline). La asimetría **empujaba al usuario hacia el "éxito"**; en activación conductual ambas respuestas son válidas y honestas, ninguna debe privilegiarse.
- **Fix:** `_btn_yes` pasa a `variant="secondary"`. Ahora **ambos botones tienen el mismo peso visual** (outline, mismo tamaño/ancho) y se distinguen solo por la etiqueta. El estado completado sigue mostrando "No pude"/"Hecho" en gris deshabilitado.

### Avisos — eliminar duplicación `Completado`/`Hecho` (`app/modules/avisos_qt.py`)
- **Problema:** una fila completada mostraba **dos indicadores del mismo estado**: el badge "Completado" (columna de estado) **y** el botón deshabilitado "Hecho" (columna de acción).
- **Fix:** en filas completadas se **oculta el botón "Hecho"** (no hay acción posible sobre un aviso completado); el estado lo comunica únicamente el badge "Completado". Para no romper la alineación con las filas pendientes (badge + "Completar"), el botón usa `setRetainSizeWhenHidden(True)` → la columna de badges queda alineada en todas las filas.

### Rutina — verificado, ya correcto (`app/modules/rutina_qt.py`, sin cambios)
- **Columnas sin comprimir:** Mañana/Tarde/Noche entran en 3 columnas a 960×600 sin apelmazarse.
- **Checkboxes y acciones legibles:** checkboxes con tilde clara, tareas completadas con strikethrough, "+ Agregar tarea" en `secondary` (botón real), ring de progreso por sección y del día.
- **Empty state coherente:** `NMEmptyState` "Sin rutina asignada" (icono + título serif + subtítulo) + Nota del día disponible.
- Estados verificados: default (60%), all-completed (100%), add-task (alta inline), empty.

## Restricciones respetadas
- Cambios acotados a `actividades_qt.py` y `avisos_qt.py` (Suite-only) → Hub intacto. Rutina sin tocar.
- Sin tocar tokens ni componentes compartidos (`test_token_parity`, `test_components_public_api` OK).
- `NMButton variant="secondary"` y `setRetainSizeWhenHidden` no introducen componentes nuevos.

## Gates
- `py_compile` OK (rutina + actividades + avisos)
- `ruff check` OK (All checks passed)
- `pytest tests/` → **85 passed**
- Sin duplicados de hash: 26/26 capturas con MD5 distinto.

## Capturas evidencia (inspeccionadas 2026-06-14, light + dark)
| Vista | Resultado |
|---|---|
| `suite-rutina-{dark,light}` | revisado — 3 columnas sin comprimir, checkboxes/strikethrough legibles |
| `suite-rutina-add-task-{dark,light}` | revisado — alta inline "Nueva tarea…" |
| `suite-rutina-all-completed-{dark,light}` | revisado — 100% (10/10) |
| `suite-rutina-empty-{dark,light}` | revisado — NMEmptyState "Sin rutina asignada" |
| `suite-actividades-{dark,light}` | revisado — "No pude"/"Hice" jerarquía equivalente |
| `suite-actividades-empty-{dark,light}` | revisado — NMEmptyState "Sin sugerencias" (determinista) |
| `suite-actividades-filtered-{dark,light}` | revisado — filtro por familia con resultados |
| `suite-actividades-marked-hice-{dark,light}` | revisado — marcadas vs activas, botones equivalentes |
| `suite-avisos-{dark,light}` | revisado — sin duplicación Completado/Hecho |
| `suite-avisos-filter-activos-{dark,light}` | revisado — filtro Activos, badges/acciones claros |
| `suite-avisos-search-{dark,light}` | revisado — búsqueda con resultados |
| `suite-avisos-empty-{dark,light}` | revisado — NMEmptyState "Sin recordatorios asignados" |

> **Nota (2026-06-22):** `avisos-completed` (microestado de marcar un aviso) retirado del set canónico; candidato a `extended_runtime_qa`. Se incorpora `avisos-today` (filtro Hoy) que sí tiene pantalla canónica en el mockup. Conteo canónico total: `canonical_mockup_parity=86` (43 vistas × 2 temas).

## Deuda pendiente exacta
- Ninguna en el alcance de Fase 10. Las 12 vistas canónicas (24 capturas) quedan `revisado`; `avisos-today` pendiente de primera inspección.
- Fuera de alcance (no son deuda de Fase 10): quedan `pendiente`/`parcial` en la matriz `animo-note-filled`, `evolucion-monthly`, `pacientes-filter-sin-registros`, `pacientes-filter-sin-sync` (estados sueltos/data-dependent), más los `parcial` data-dependent ya documentados (empties/filtros/standalone). Se resuelven en la Fase 11 (regresión final) o quedan documentados como dependientes de datos reales.

## Estado
- **CERRADA** — implementación + capturas inspeccionadas + matriz actualizada + doc.
- Próxima: Fase 11 (Regresión final y cierre).
