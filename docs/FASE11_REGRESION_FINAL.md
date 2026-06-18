# Fase 11 — Regresión Final y Cierre

## Objetivo (PLAN FASEADO §Fase 11)
- Ejecutar `compileall`, `ruff`, `pytest`, smoke runtime Suite, smoke runtime Hub, `build_neuromood.py --dry-run`.
- Ejecutar V8 completo y revisar la matriz completa.
- Declarar el estado global con honestidad (`terminada` sólo si TODO está cerrado).

## 1. Manifest V8 completo regenerado (el stale era real)
- La matriz declaraba "Manifest regenerado: 2026-06-14T18:57" — **antes** de Fases 8–10. Las capturas parciales no probaban que las 132 vistas siguieran sanas.
- `python qa/capture_v8.py --all --theme both` → **132 capturadas, 0 fallos, 0 duplicados** (MD5 distinto en las 132). Manifest fresco: `2026-06-15T00:01:07`, git `3b66ce0`.

## 2. Las 8 vistas `pendiente` resueltas + inspección-pendiente a 0
- `animo-note-filled` ×2 → **revisado** (nota escrita, header "Sin registro / —/10" sin falso 0, Guardar deshabilitado hasta puntaje).
- `evolucion-monthly` ×2 → **revisado** (vista Mensual 30 días, chart + métricas coherentes).
- `pacientes-filter-sin-registros` ×2 → **parcial** (REQUIRES_DATA_STATE): el empty-state "Sin resultados" se inspeccionó OK, pero el set filtrado depende de la distribución real de datos, igual que `pacientes-filter-activos`.
- `pacientes-filter-sin-sync` ×2 → **parcial** (REQUIRES_DATA_STATE): lista de 5 pacientes escaneable; el set depende de la sync real.
- Además se inspeccionaron las filas `parcial` que aún tenían `inspeccion=pendiente` (dashboard-empty, pacientes-empty, pacientes-filter-activos, pacientes-search, animo-stats-empty y variantes runtime legacy): todas renderizan coherentes → `inspeccion=revisado_f11`. **Inspección-pendiente queda en 0: las 132 vistas fueron inspeccionadas.**

## 3. Guardado REAL del TCC probado (lo que QA salta deliberadamente)
- El modo QA visual salta el INSERT (sólo muestra la página de éxito), así que el guardado real quedaba sin cubrir. Se extrajo el seam `_persistir_pensamiento(d, intensidad)` que `_guardar` invoca cuando QA está OFF.
- `tests/test_tcc_persistencia.py` (**6 tests**): con `APPDATA` redirigido a `tmp_path` (SQLite temporal) y QA desactivado (el conftest limpia `NM_VISUAL_QA`):
  - `test_qa_desactivado_en_tests` — el camino real es el activo.
  - `test_persistencia_real` — inserta y commitea una fila legible en `pensamientos`.
  - `test_intensidad_default_5_persiste` — el default 5 satisface el CHECK(0..10).
  - `test_intensidad_constraint_rollback` — intensidad 99 viola el CHECK → `IntegrityError` y **rollback** (0 filas): el manejo de errores que `_guardar` traduce en toast.
  - `test_error_db_propaga` — un fallo de conexión se propaga (no se traga en silencio).
  - `test_nm_data_db_no_tocado` — la escritura ocurre SÓLO en la SQLite temporal bajo `tmp_path`; **`nm_data.db` real intacto**.

## 4. Tests específicos para los cambios F8–F10 (antes inexistentes)
- `tests/test_fase9_10_regressions.py` (**4 tests**, guards de fuente estables): F9 sin BPM biométrico simulado (Ciclos reales); F10 "Hice"/"No pude" jerarquía equivalente; F10 Avisos sin duplicación Completado/Hecho; F8 "Anterior" secondary + seam de guardado real.

## 5. Regresión completa (resultados locales — no hay CI asociada)
| Gate | Resultado |
|---|---|
| `python -m compileall app shared hub qa build_neuromood.py` | OK (exit 0) |
| `ruff check .` | All checks passed |
| `pytest tests/` | **95 passed** (85 previos + 10 nuevos) |
| smoke runtime Suite + Hub (`qa/runtime_live_probe.py --all --theme both`) | **OK=30, DEFECTS=0, FAILED=0** |
| `python build_neuromood.py --dry-run` | OK (Suite+Hub EXE + 2 NSIS, exit 0) |
| V8 completo (`qa/capture_v8.py --all --theme both`) | **132 capturas, 0 fallos, 0 duplicados** |

> **Aviso explícito:** los 95 tests y el smoke son resultados **locales**. El repo no tiene CI configurada, por lo que el commit final no lleva checks de CI asociados. Recomendación de seguimiento: agregar un workflow (GitHub Actions) que corra `ruff` + `pytest` + `compileall` en cada push.

## 6. Estado global del plan — honesto
- **PARCIAL.** Por la regla del propio plan (`terminada` sólo si TODAS las filas están cerradas) no puede declararse terminado mientras existan filas `parcial`/`bloqueado`.
- Matriz final: **pendiente=0** (resultado e inspección), `revisado=102`, `parcial=28`, `bloqueado=2`.
- El residual **NO es deuda de diseño** — todo el trabajo visual de Fases 1–10 está cerrado e inspeccionado. Es límite del harness de captura estática:
  - **28 `parcial`**: `REQUIRES_DATA_STATE` (el estado de datos real no se prueba con mock QA: empties/filtros/búsqueda/dashboard-pacientes) y `REQUIRES_RUNTIME` (capturas standalone no prueban el chrome/lifecycle lanzado: pin-setup, privacy-lock×2 y variantes legacy).
  - **2 `bloqueado`**: `home-settings-open` (overlay transitorio; la captura estática de la ventana principal puede no contenerlo).
- Cerrar estos a `revisado` requeriría evidencia de runtime real con datos reales (fuera del alcance de coherencia visual), no más cambios de diseño.

## Estado
- **CERRADA** la Fase 11 (regresión ejecutada, matriz completa revisada, guardado real probado, estado global declarado con honestidad).
- **Plan global: PARCIAL** con residual documentado (límite de evidencia, no diseño).
