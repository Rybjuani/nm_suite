# Fase 1 - Contrato Visual Y Densidades

## Baseline De Comparacion
- Manifest activo: `qa/_captures_v8_fresh/CAPTURE_MANIFEST.json` — generado 2026-06-21T02:34:12 contra HEAD 51f4448.
- Regenerar con: `python qa/capture_v8.py --all --clean --out-dir qa/_captures_v8_fresh`
- Targets canónicos del mockup: `qa/_mockup_targets/` (96 PNGs, regenerados con Playwright contra HEAD 51f4448).
- Diff de fidelidad fresco: `qa/_fidelity_fresh/FIDELITY_REPORT.md` (gate: SSIM>=0.92, MAD<=0.035, changed<=0.08).
- Resumen versionable: `docs/CAPTURE_MANIFEST_SUMMARY.md`.
- Capturas frescas: 98/98, 0 fallos tecnicos, 92 state-valid, 6 `REQUIRES_DATA_STATE`.
- Estado global visual: 0/96 PASS en el gate endurecido. Ver `docs/VISUAL_QA_AUDIT.md` para deuda por pantalla.

Nota: los artifacts `qa/_baseline_f0_phase01/`, `qa/_captures_v8/` (default dir),
`qa/_mockup_verify/`, `qa/_mockup_verify2/`, `qa/_fidelity_current/`,
`qa/_fidelity_selfcheck/` y `qa/nm_capturas_actualizadas/` fueron purgados el
2026-06-21 por ser stale o autocomparacion trivial. No volver a referenciarlos.

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
