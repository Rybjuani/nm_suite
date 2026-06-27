# Visual Auditor V2

## Purpose

Convert mockup↔capture comparisons into structured, navigable, prioritized visual
evidence. Reuses existing stack (`capture_v8.py`, `diff_fidelity.py`,
`_mockup_canonical/MANIFEST.json`). Replaces heuristic classification with
VLM-driven analysis.

## Architecture

```
qa/_mockup_canonical/MANIFEST.json ← canónico vigente, no se toca
     ↓
qa/capture_v8.py --all ← existe, no se toca
     ↓
qa/_captures_v8/CAPTURE_MANIFEST.json
     ↓
qa/diff_fidelity.py ← existe, no se toca
     ↓
qa/_fidelity_current/FIDELITY_REPORT.json
     ↓
qa/visual_auditor_v2.py analyze --all ← NUEVO
```

### Pipeline steps

1. **Pairing** — reads `manifest.json` and matches each item to a capture file
   via `(app, screen_id, state_id, theme)` → filename convention.
2. **Diff + BBoxes** — `scipy.ndimage.label` extracts connected diff regions,
   produces `diff.png` (side-by-side) and `overlay.png` (bboxes drawn).
3. **Crops** — per-bbox crops of mockup, real, and diff for close inspection.
4. **Classification** — VLM (GLM-4V or configurable backend) receives the bundle
   (mockup + real + diff + overlay + metrics context) and returns structured JSON.
5. **Cache** — per `(mockup_sha256, capture_sha256)` to avoid reclassifying
   unchanged images.
6. **Outputs** — `index.html`, `report.json`, `queue.md`, per-surface
   `metrics.json` + `classification.json` + `agent_package.json`.

## Quickstart for agents

```powershell
# 1. Validate que todo está en orden
.\.venv\Scripts\python.exe qa\visual_auditor_v2.py doctor

# 2. Generar capturas frescas (si hiciste cambios de UI)
.\.venv\Scripts\python.exe qa\capture_v8.py --all --theme both

# 3. Correr el auditor (offline si no tenés VLM configurado)
.\.venv\Scripts\python.exe qa\visual_auditor_v2.py analyze --all --no-vlm

# 4. Ver el reporte HTML
start qa\_visual_auditor_v2\latest\index.html

# 5. Ver la cola priorizada
Get-Content qa\_visual_auditor_v2\latest\queue.md
```

## Workflow paso a paso para agentes

### Paso 0: Pre-requisitos
- `qa/_captures_v8/CAPTURE_MANIFEST.json` debe existir (generado por `capture_v8.py`).
- `qa/_mockup_canonical/MANIFEST.json` debe existir (canónico, versionado).
- Si querés VLM real: exportar `NM_VLM_BACKEND` y tener `z-ai-web-dev-sdk` instalado.

### Paso 1: Correr `doctor`
Si falla algo, arreglarlo antes de continuar. Los issues comunes:
- `MISSING: qa/_fidelity_current/FIDELITY_REPORT.json` → correr `diff_fidelity.py` con `--target-dir qa/_mockup_targets`.
- `MISSING DEP` → `pip install scipy imagehash scikit-image`.
- `NM_VLM_BACKEND not set` → normal si no tenés VLM; el sistema degrada a `NEEDS_HUMAN_REVIEW`.

### Paso 2: Analizar
```powershell
# Modo offline (sin VLM) — todo es NEEDS_HUMAN_REVIEW
.\.venv\Scripts\python.exe qa\visual_auditor_v2.py analyze --all --no-vlm

# Modo con VLM (si NM_VLM_BACKEND está seteado)
.\.venv\Scripts\python.exe qa\visual_auditor_v2.py analyze --all
```

### Paso 3: Leer los outputs

#### `report.json`
Array de 86 objetos (una por superficie). Cada objeto tiene:
- `pairing` — cómo se emparejó mockup↔captura.
- `metrics` — SSIM, MAD, changed_pixel_ratio, bbox_count, phash_distance.
- `classification` — labels, severity, explanation, recommendation, suspected_module, confidence.
- `agent_package` — resumen accionable para agentes sin visión.

#### `queue.md`
Lista priorizada. Orden: severity → confidence → recommendation → cross_theme → cross_state.

#### `index.html`
Tabla navegable con filtros (app, theme, severity, recommendation, search).

#### Per-surface (`surfaces/<surface_key>/`)
- `mockup.png` — referencia canónica.
- `real.png` — captura real.
- `diff.png` — mockup | real | abs diff ×4.
- `overlay.png` — captura real con bboxes de regiones divergentes.
- `metrics.json` — métricas heredadas de diff_fidelity + bbox info nueva.
- `classification.json` — resultado del VLM (o NEEDS_HUMAN_REVIEW si offline).
- `agent_package.json` — paquete para agente sin visión.
- `crops/bbox_N/` — recortes ampliables de cada región.

### Paso 4: Decidir el próximo fix

Leer `agent_package.json` de la superficie top de `queue.md`.

```json
{
  "surface_key": "suite:rutina-empty:default@light",
  "decision": "FIX_PRODUCT",
  "suspected_module": "shared/components/empty_states.py",
  "evidence_summary": "Empty state en light renderiza sobre bg (#E9E3D6) en vez de surface card (#FBF8F1). Cambió 92% de pixeles.",
  "confidence": "high",
  "what_to_check_first": "Buscar dónde se construye el empty state de rutina...",
  "do_not_touch_if": "confidence == 'low' o si el diff parece RENDER_NOISE"
}
```

**Regla de oro:** Si `confidence == 'low'`, `decision` siempre es `NEEDS_HUMAN_REVIEW`. No tocar código.

### Paso 5: Iterar
Después de hacer un fix, regenerar capturas (`capture_v8.py --all --theme both`) y re-correr `analyze --all`. El cache evita reclasificar lo que no cambió.

## Commands

```powershell
# Analyze all surfaces
.\.venv\Scripts\python.exe qa\visual_auditor_v2.py analyze --all

# Analyze one surface
.\.venv\Scripts\python.exe qa\visual_auditor_v2.py analyze --surface suite:rutina-empty:default@light

# Offline mode (no VLM, everything NEEDS_HUMAN_REVIEW)
.\.venv\Scripts\python.exe qa\visual_auditor_v2.py analyze --all --no-vlm

# Export prioritized queue
.\.venv\Scripts\python.exe qa\visual_auditor_v2.py queue

# Clear classification cache
.\.venv\Scripts\python.exe qa\visual_auditor_v2.py clear-cache

# Validate environment
.\.venv\Scripts\python.exe qa\visual_auditor_v2.py doctor
```

## Environment

- `NM_VLM_BACKEND` — if set, enables VLM calls. If unset, classification
  degrades gracefully to `NEEDS_HUMAN_REVIEW`.
- The VLM client attempts to import `z_ai_web_dev_sdk` (GLM-4V). Other backends
  can be wired in by patching `_call_vlm`.

## Output structure

```
qa/_visual_auditor_v2/latest/
  index.html
  report.json
  queue.md
  surfaces/
    <surface_key>/
      mockup.png
      real.png
      diff.png
      overlay.png
      metrics.json
      classification.json
      agent_package.json
      crops/
        bbox_0/
          mockup.png
          real.png
          diff.png
        bbox_1/ ...
```

## Taxonomy

### Labels (closed set)

- `LAYOUT_SHIFT`
- `SIZE_MISMATCH`
- `SPACING_MISMATCH`
- `COLOR_MISMATCH`
- `TEXT_MISMATCH`
- `MISSING_COMPONENT`
- `EXTRA_COMPONENT`
- `CHROME_MISMATCH`
- `RENDER_NOISE`
- `PAIRING_OR_CAPTURE_MISMATCH`
- `NEEDS_HUMAN_REVIEW`

### Recommendations (closed set)

- `PRODUCT_FIX_CANDIDATE`
- `FIXTURE_FIX_CANDIDATE`
- `PAIRING_OR_CAPTURE_FIX_CANDIDATE`
- `LIKELY_RENDER_NOISE`
- `NEEDS_HUMAN_REVIEW`

## Agent package (`agent_package.json`)

Designed for agents without vision. Contains:

- `decision` — `FIX_PRODUCT`, `FIX_FIXTURE`, `FIX_PAIRING`, `SKIP_RENDER_NOISE`, `NEEDS_HUMAN_REVIEW`
- `suspected_module` — file path guess from VLM
- `evidence_summary` — textual description of what changed
- `confidence` — `high`, `medium`, `low`
- `what_to_check_first` — next step suggestion
- `do_not_touch_if` — guardrail rule

## Decision tree para agentes

```
┌─────────────────────────────────────┐
│  Leer agent_package.json            │
│  de la superficie top en queue.md   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  confidence == 'low'?               │
└──────────────┬──────────────────────┘
               │
      ┌────────┴────────┐
      │                 │
     YES               NO
      │                 │
      ▼                 ▼
┌─────────────┐   ┌─────────────────────────┐
│ NEEDS_HUMAN │   │ decision == FIX_PRODUCT?│
│ _REVIEW     │   └────────────┬────────────┘
│ No tocar.   │                │
└─────────────┘       ┌────────┴────────┐
                      │                 │
                     YES               NO
                      │                 │
                      ▼                 ▼
            ┌──────────────┐    ┌──────────────┐
            │ Revisar      │    │ decision ==  │
            │ suspected_   │    │ FIX_FIXTURE? │
            │ module y     │    └──────┬───────┘
            │ aplicar fix│           │
            └──────────────┘    ┌────┴────┐
                                │         │
                               YES       NO
                                │         │
                                ▼         ▼
                        ┌──────────┐ ┌──────────┐
                        │ Revisar  │ │ decision │
                        │ fixtures │ │ == FIX_  │
                        │ /estado  │ │ PAIRING? │
                        └──────────┘ └────┬─────┘
                                           │
                                    ┌──────┴──────┐
                                    │             │
                                   YES           NO
                                    │             │
                                    ▼             ▼
                            ┌──────────┐   ┌──────────┐
                            │ Revisar  │   │ SKIP o   │
                            │ pairing  │   │ NEEDS_   │
                            │ /capture │   │ HUMAN_   │
                            └──────────┘   │ REVIEW   │
                                           └──────────┘
```

## Guardrails

- If `confidence == 'low'`, `decision` is forced to `NEEDS_HUMAN_REVIEW`.
- pHash distance is reported as auxiliary metric but **never** used as sole
  severity criterion.
- No heuristic numpy classification (no edge density, text density, color delta).
- `--no-vlm` produces `NEEDS_HUMAN_REVIEW` for all surfaces; no invented labels.

## Limitations

- VLM accuracy is not perfect. Some classifications will be wrong. Confidence is
  reported explicitly and the low-confidence rule is enforced.
- VLM cannot validate states that require real persisted data or network
  interaction. Those still need manual validation.
- Cache can theoretically go stale if images change but SHA-256 collisions occur
  (extremely rare). `clear-cache` resolves this.

## Troubleshooting

| Síntoma | Causa probable | Fix |
|---------|---------------|-----|
| `0 surfaces analyzed` | `manifest.json` vacío o mal parseado | Verificar `qa/_mockup_canonical/MANIFEST.json` |
| `all unpaired` | Capturas faltantes o nombres de archivo no coinciden | Correr `capture_v8.py --all --theme both` |
| `TypeError: np.int64 not JSON serializable` | Bug de sanitización | Reportar; workaround: usar `--no-vlm` |
| `VLM call failed` | `NM_VLM_BACKEND` mal configurado o SDK no instalado | Verificar env var e instalar `z-ai-web-dev-sdk` |
| `Cache stale` | Imágenes cambiaron pero SHA-256 coincide (raro) | `clear-cache` y re-correr |
| `doctor` reporta `MISSING DEP` | Dependencia no instalada | `pip install scipy imagehash scikit-image` |

## Git hygiene

`qa/_visual_auditor_v2/` is in `.gitignore`. Do not commit generated outputs.
Commit only `qa/visual_auditor_v2.py`, `tests/test_visual_auditor_v2.py`, and
`docs/VISUAL_AUDITOR_V2.md`.

## What V2 does NOT do (lessons from Sentinel)

- No hardcoded semantic regions (header/sidebar/content/cards/modal/CTA/bottom/right/form).
- No heuristics of "text density delta" / "edge density delta" / "color delta global".
- No 7-dimension heuristic scoring queue.
- No crawler (reuses `capture_v8.py`).
- No global diff (reuses `diff_fidelity.py`).
- No manifest reconstruction (reads canonical `manifest.json`).
- No auto-approval. If VLM is unavailable, everything is `NEEDS_HUMAN_REVIEW`.
- No blind microfixes. Low confidence means no fix recommendation.
