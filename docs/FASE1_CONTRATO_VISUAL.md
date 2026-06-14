# Fase 1 - Contrato Visual Y Densidades

## Baseline De Comparacion
- Baseline Fase 0: `qa/_baseline_f0_phase01` (132 PNGs — directorio canónico, gitignored).
- Manifest baseline: no generado en `_baseline_f0_phase01/`; el manifest disponible es `qa/_captures_v8/CAPTURE_MANIFEST.json` (124 capturas, generado antes de añadir las 4 recetas nuevas — pendiente re-run `--all` para sincronizar a 132).
- Matriz versionable: `docs/QA_V8_BASELINE_MATRIX.md`.
- Capturas baseline: 132/132 en `_baseline_f0_phase01/`, 0 fallas tecnicas.
- Evidencia tecnica valida antes de inspeccion manual: 102.
- Estado global visual: parcial — 6 filas pre-inspeccionadas por flags; 126 requieren revision visual PNG.
- Comparacion post-Fase-1: pendiente — ejecutar `python qa/capture_v8.py --all --out-dir qa/_captures_f1_post` y comparar contra baseline.

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
