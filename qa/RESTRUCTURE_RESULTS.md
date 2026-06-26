# RESTRUCTURE_RESULTS — Fase 4 (medición)

Branch `qa/canonical-source` vs base pre-reestructuración `805955d`.
Cambio **tooling-only** (no toca código de app): métricas con app constante
(`qa/_captures_v8`, 86 superficies) para aislar el efecto de la herramienta.

## Gates por fase

| Fase | Gate | Target | Medido | Estado |
|---|---|---|---|---|
| 0 | Canonical = pack aprobado | 86 PNG, sha256==MANIFEST | 86/86, 0 junk | PASS |
| 1.2 | Specs sin header_band/score_widget | ≥30%↓ divergencias | 201→77 = 61.7%↓ | PASS |
| 1.3 | canvas_bg corners+mediana+tol25 | sin FP bg sólido | implementado | PASS |
| 1.4 | `--introspect` + contracts radius/gradient | activos | implementado | PASS |
| 1.5 | tests rotos | collect 0 err | 315/0 | PASS |
| 2.1 | odiff AA vs SSIM (FAIL) | ≥40%↓ | ver calibración ↓ | PASS |
| 2.2 | graphify oficial | ≥200 nodos, ≥30% tokens | 683, 17.9× | PASS |
| 2.3 | probe split runtime/visual | RUNTIME sin reasons visuales | implementado | PASS |
| 3.4 | refs obsoletas | 0 Python activo | 0 | PASS |

## Calibración honesta odiff (puntos owner 1+3)

A `--threshold 0.1` el % se infla con **tinte de fondo uniforme** (backdrops de
modal) + **antialiasing de fuentes** + **offset de métricas de fuente** — todos
artefactos cross-renderer, NO defectos. Validado por inspección visual de
overlays. A `--threshold 0.3` (piso de ruido) esos artefactos se suprimen.

| Config | median | FAIL@8% |
|---|---|---|
| t=0.1 (antes) | 3.91% | 19 |
| **t=0.3 (honesto)** | **2.50%** | **8** |

**Clasificación real/FP de los 8 FAIL (punto owner 2 — inspección visual):**

| % | Superficie(s) | Veredicto |
|---|---|---|
| 55.93% | suite-dbt-practice-stop-light | **FP** — tinte uniforme del backdrop del modal (colapsa a 3.3% a t0.4) |
| 8.0–9.2% | 7× hub-detalle (resumen-ia, plan-activacion, plan-timer, detalle) | **REAL** — 1 defecto sistemático |

vs SSIM estricto 79 FAIL → **78/86 PASS, 1 FP, 1 defecto real (×7 hermanas)**.

## Deuda real encontrada

**hub-detalle: offset vertical sistemático (~10–15 px).** Todo el bloque de
contenido (header paciente, tabs, body, botones) aparece desplazado en vertical
entre canonical (Chromium) y captura (Qt), en las 7 pantallas de la familia
hub-detalle. Overlay = elementos duplicados a dos posiciones-y. Root cause a
triagear por owner (margen-top de la app vs framing de captura). **No se corrige
acá** (fuera de scope del restructure tooling).

## OCR (punto owner 5)

Probado: pytesseract + tesseract.exe + tessdata eng/spa. Overlap de palabras
canonical-vs-captura (20 superficies): **min 0.17 / mediana 0.58 / max 1.00**.
Variabilidad alta = OCR cross-renderer de fuentes estilizadas mete ruido
(segmentación, acentos). **No se integra** como check de contenido: incumple la
condición "no mete ruido". El check de presencia por densidad de bordes ya cubre
render-en-blanco sin ruido. tessdata se conserva gitignored para OCR futuro
sobre elementos aislados (no superficie completa).

## Timing (86 superficies, app constante)

| Paso | s |
|---|---|
| verify-all | 5.8 |
| diff odiff | 2.9 |
| diff ssim (legacy) | 20.5 |

## Pendiente owner

- Triage del defecto real hub-detalle (offset vertical).
- Aprobación de merge (otorgada).

## Fase 5 — Cierre (5.D: cerrar y mantener)

Decisión owner: **5.D**. No se ejecutan 5.A (VLM sidecar), 5.B (QWebEngineView),
5.C (Applitools). Criterio cumplido: FP ≈ **1/86 ≈ 1.2%** (≤15%). Roadmap **CERRADO**.

**Estado final del pipeline (mantener):**

| Componente | Fuente / comando |
|---|---|
| Canonical (única) | `qa/_mockup_canonical/` ← `qa/pack canonico/generate_captures.js` + `neuromood-mockup_reparado.html` (ver README) |
| Specs | `qa/spec_generator.py` → `qa/specs/specs.json` |
| Auditor visual | `qa/visual_auditor_spec.py verify-all` |
| Diff píxeles | `qa/diff_fidelity.py --engine odiff` (threshold 0.3, accept 8%) |
| Introspección Qt | `qa/vas_introspect.py` (opt-in `--introspect`) |
| Probe runtime | `qa/runtime_live_probe.py` (PROBE_RUNTIME/VISUAL) |
| Grafo agentes | `graphify update qa/` (oficial, out-of-band) |

**Deuda abierta entregada al owner:** hub-detalle offset vertical (UI migration).

