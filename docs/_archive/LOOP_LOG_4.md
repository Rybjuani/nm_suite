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
| 1 | `1d7a8bc` | `0aec2c8` | Suite · Checklist de rutina · empty state | El empty state estaba centrado verticalmente en toda la pantalla; el mockup (l.909) lo posiciona cerca del top del screen con padding 24+50. | `app/modules/rutina_qt.py` | ruff pass; `tests/test_rutina_visual_contract.py` 2/2 pass; captura V8 regenerada; diff PASS (SSIM≥0.92, MAD≤0.035, changed≤0.08) |
| 2 | `0aec2c8` | `2301c96` | Suite · Temporizador · empty state | El empty state estaba centrado verticalmente dentro del timer_card; el mockup (l.856-858) lo posiciona cerca del top del screen. | `app/modules/timer_qt.py`, `qa/capture_v8.py` | ruff pass; `tests/test_timer_visual_contract.py` + `tests/test_capture_v8_evidence.py` 11/11 pass; captura V8 regenerada; diff PASS |
| 3 | `2301c96` | `8ffda51` | Suite · Recordatorios · búsqueda con resultados | La receta V8 buscaba `"medic"` mientras el mockup target muestra `"respir"` (resultado: "Respiración 5 min"); además el campo de búsqueda se estiraba hasta 480 px, desparramándose respecto al mockup. | `qa/capture_v8.py`, `app/modules/avisos_qt.py` | ruff pass; `tests/test_avisos_visual_contract.py` + `tests/test_capture_v8_evidence.py` 10/10 pass; captura V8 regenerada; diff mejora (dark SSIM 0.91545 / light SSIM 0.90482) pero aún no alcanza PASS por diferencias globales de chrome/estilo de fila |

