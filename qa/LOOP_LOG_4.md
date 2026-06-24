# LOOP_LOG_4 — Reducción controlada de discrepancias visuales

## Meta

Reducir discrepancias visuales reales del producto contra `neuromood-mockup.html` y `qa/mockup_reference_static/`, en ciclos pequeños, reversibles y verificables.

## Convenciones

- Un ciclo = una discrepancia visible y accionable cubierta por V8.
- Si el fix no mejora visualmente o genera regresión, se revierte.
- Nunca se toca lógica clínica, DB, auth ni sync.
- Nunca se modifica `qa/mockup_reference_static/`.
- No se declara PASS visual global.

## Estado inicial

- SHA inicial: `1d7a8bc`
- Fecha inicio: 2026-06-24

## Ciclos

| # | SHA antes | SHA después | Superficie | Discrepancia | Archivos | Validación |
|---|---|---|---|---|---|---|
| 1 | `1d7a8bc` | `31ea9d7` | Suite · Checklist de rutina · empty state | El empty state estaba centrado verticalmente en toda la pantalla; el mockup (l.909) lo posiciona cerca del top del screen con padding 24+50. | `app/modules/rutina_qt.py` | ruff pass; `tests/test_rutina_visual_contract.py` 2/2 pass; captura V8 regenerada; diff PASS (SSIM≥0.92, MAD≤0.035, changed≤0.08) |

