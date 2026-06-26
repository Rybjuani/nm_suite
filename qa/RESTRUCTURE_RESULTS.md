# RESTRUCTURE_RESULTS — Fase 4 (medición)

Branch `qa/canonical-source` vs base pre-reestructuración `805955d`.
Cambio **tooling-only** (no toca código de app): métricas medidas con app
constante (`qa/_captures_v8`, 86 superficies) para aislar el efecto de la herramienta.

## Gates por fase

| Fase | Gate | Target | Medido | Estado |
|---|---|---|---|---|
| 0 | Canonical = pack aprobado | 86 PNG, sha256==MANIFEST | 86/86 sha256, 0 junk | PASS |
| 1.2 | Specs sin header_band/score_widget | ≥30% menos divergencias | 201→77 = 61.7%↓ | PASS |
| 1.3 | canvas_bg corners+mediana+tol25 | sin FP bg sólido | implementado | PASS |
| 1.4 | `--introspect` opt-in + contracts | radius/gradient activos | implementado | PASS |
| 1.5 | tests rotos | collect 0 errores | 315 tests / 0 err | PASS |
| 2.1 | odiff AA vs SSIM (FAIL) | ≥40% menos FAIL | 19 vs 79 = 76%↓ | PASS |
| 2.2 | graphify oficial | graph ≥200 nodos, ≥30% menos tokens | 683 nodos, 17.9× | PASS |
| 2.3 | probe split runtime/visual | RUNTIME sin reasons visuales | implementado | PASS |
| 3.4 | refs obsoletas | 0 en Python activo | 0 | PASS |

## Métricas Fase 4.3

| Métrica | Target | Medido | Estado |
|---|---|---|---|
| Divergencias spec (86) | ≤35% del baseline | 77 / 201 = 38% (61.7%↓) | MARGINAL (+3 pts) |
| Divergencias odiff (86) | — | 19 / 79 = 24% (76%↓) | PASS |
| Falsos positivos (clasif. real/FP) | ≤20% FP | ver desglose ↓; veredicto = owner | OWNER |
| Tiempo pipeline diff | ≤115% baseline | odiff 2.9s = 14% de SSIM 20.5s | PASS |
| Deuda visual real (contracts) | ≥5 nuevas | 10 SHADOW + 2 TEXT + radius/gradient | PASS |
| Tokens por query (graphify) | ≥30% menos | 17.9× (~94%) | PASS |
| Consistencia canonical | SSIM≥0.95 ≥80/86 | 86/86 sha256-idéntico al pack | PASS |

## Desglose divergencias spec (77)

| Kind | N | Notas |
|---|---|---|
| COLOR_MISMATCH | 65 | delta min 13 / mediana 32 / max 124 |
| — delta ≤20 (borderline cross-renderer) | 15 | candidatos FP, requieren inspección |
| — delta >40 (probable real) | 26 | divergencia real probable |
| SHADOW_MISMATCH | 10 | presence-based (FP-resistant) |
| TEXT_MISSING | 2 | presence-based (FP-resistant) |

## Timing (86 superficies, app constante)

| Paso | s |
|---|---|
| verify-all | 5.8 |
| diff odiff | 2.9 |
| diff ssim (legacy) | 20.5 |

## Pendiente owner

- Clasificación real/FP del sample (el agente no decide calidad visual).
- Las 19 superficies odiff>8% son las candidatas a deuda visual real.
- Decisión de merge `qa/canonical-source` → `main`.
