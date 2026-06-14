# Fase 1 - Contrato Visual Y Densidades

## Baseline De Comparacion
- Baseline Fase 0: `qa/_baseline_f0_phase01` (132 PNGs — directorio canónico, gitignored).
- Manifest activo: `qa/_captures_v8/CAPTURE_MANIFEST.json` — generado 2026-06-14T18:57:00, 132 capturas, 0 fallos, 0 duplicados, unique_hash_count=132.
- Regenerar con: `python qa/capture_v8.py --all --no-clean`
- Matriz versionable: `docs/QA_V8_BASELINE_MATRIX.md`.
- Capturas post-Fase-2: 132/132, 0 fallos, state_valid=106, REQUIRES_DATA_STATE=16, REQUIRES_RUNTIME=8, WRONG_VIEW=2.
- Estado global visual: parcial — 14 filas inspeccionadas; 118 pendientes de revision visual PNG.

## Densidades
- Suite: `suite_comfortable`.
- Hub: `hub_professional_compact`.
- Fuente runtime: `shared.theme.VISUAL_DENSITIES`.
- Bridge compatibility: `shared.design_tokens.VISUAL_DENSITIES`.
- Aplicacion Qt: `shared.theme_qt.product_density_tokens()` y `hub_density_qss()`.

## Regla De Separacion
- La Suite conserva escala comfortable: botones 36 px, inputs 36 px, tabs 32 px y scrollbar 8 px.
- El Hub aplica compactacion scoped a `#HubMain`: botones 32 px, inputs 32 px, tabs/subtabs/filtros 28 px y scrollbar 6 px.
- Ninguna regla de densidad Hub se aplica a `QApplication`; `apply_hub_density()` solo concatena QSS sobre el `QMainWindow` del Hub.
- Los tests verifican que los roles compactos del Hub no superen la escala de Suite.

## Roles Cubiertos
- Tabs y subtabs.
- Filtros.
- Badges y chips.
- Botones.
- Inputs, textareas y comboboxes.
- Scrollbars.
- Estados disabled y focus.

## Deuda Pendiente
- La matriz baseline mantiene `inspeccion_manual=pendiente` para todas las filas.
- Hay filas `parcial` por estados que requieren datos reales o runtime vivo.
- Hay filas `bloqueado` en `home-settings-open` porque el overlay transitorio no queda probado por captura main-window estatica.
