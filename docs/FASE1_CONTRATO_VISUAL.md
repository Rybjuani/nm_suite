# Fase 1 - Contrato Visual Y Densidades

## Baseline De Comparacion
- Baseline Fase 0: `qa/_baseline_f0_phase01` (132 PNGs — directorio canónico, gitignored).
- Manifest activo: `qa/_captures_v8/CAPTURE_MANIFEST.json` — generado 2026-06-14T19:23:30, 132 capturas, 0 fallos, 0 duplicados, unique_hash_count=132.
- Regenerar con: `python qa/capture_v8.py --all --no-clean`
- Matriz versionable: `docs/QA_V8_BASELINE_MATRIX.md`.
- Capturas post-Fase-2: 132/132, 0 fallos, state_valid=106, REQUIRES_DATA_STATE=16, REQUIRES_RUNTIME=8, WRONG_VIEW=2.
- Estado global visual: parcial — 14 filas inspeccionadas; 118 pendientes de revision visual PNG.

## Comparacion F0 Baseline vs F1+F2

Hash diff (MD5) entre `qa/_baseline_f0_phase01/` (132 PNGs) y `qa/_captures_v8/`
(132 PNGs, run 2026-06-14T19:23:30, Suite=38px, Hub=32px):

- **57/132 cambiados** — capturas Hub afectadas por densidad compacta (Fase 1) y
  chrome 32px + sidebar compacta (Fase 2).
- **75/132 sin cambio** — capturas Suite (densidad `suite_comfortable` codifica
  valores ya presentes en el stylesheet base; headless no detecta diferencia visual)
  + archivos REQUIRES_RUNTIME/WRONG_VIEW que producen output identico en ambas runs.

Capturas Hub vs Suite: Hub tiene ~55 capturas efectivas; todos los Hub excepto
`hub-editor-text-overrides` (REQUIRES_RUNTIME) aparecen en el grupo cambiado.
Suite tiene ~77 capturas; ninguna registra cambio visible en headless post-Fase-1.

Nota: un run previo con Suite regresada a 32px (bug chrome global) habia mostrado
125 cambiados. Ese dato era invalido; 57 es el valor correcto post-fix.

Comandos para reproducir:
```
python qa/capture_v8.py --all --no-clean
# Luego comparar con _baseline_f0_phase01/ via hash MD5
```

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
- 118 filas con `inspeccion_manual=pendiente` requieren revisión visual PNG (post-Fase-2).
- 16 filas `REQUIRES_DATA_STATE` solo verificables con Supabase real (dashboard, pacientes y variantes).
- 8 filas `REQUIRES_RUNTIME` no capturables en headless (privacy-lock, pin-setup, settings-overlay, editor-text-overrides).
- 2 filas `bloqueado` en `home-settings-open`: overlay transitorio no capturado desde la main-window estática.
