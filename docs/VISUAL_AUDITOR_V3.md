# Visual Auditor V3

## Purpose

OCR-driven, 100% offline visual auditor. Replaces VLM classification with
Tesseract OCR + rapidfuzz string matching + pixel-level color diff.
Zero cost, zero network, runs on CPU. Reuses existing stack
(`capture_v8.py`, `diff_fidelity.py`, `mockup_reference_normalized/`).

V2 remains alive in Fase 2; V3 is an alternative pipeline for environments
without VLM access or where deterministic, reproducible text comparison is
preferred over neural classification.

## Surface key alias format

A surface is uniquely identified by a `surface_key` string. The canonical
internal format produced by `pair_surfaces()` is:

```
{app}:{view}@{theme}
```

- `app` — `suite` or `hub`
- `view` — view name from the normalized manifest (e.g. `home`, `rutina-empty`)
- `theme` — `light` or `dark`

Examples:
- `suite:home@light`
- `suite:avisos-search@light`
- `hub:pacientes@dark`

The CLI argument `--surface` **accepts both separators** (`@` and `:`) and
**normalizes internally** before matching against the canonical key:

| Input form                | Normalized to              | Notes                          |
|---------------------------|----------------------------|--------------------------------|
| `suite:home@light`        | `suite:home@light`         | Canonical form, no change      |
| `suite:home:light`        | `suite:home@light`         | `:` between view/theme → `@`   |
| `suite@home@light`        | `suite:home@light`         | `:` injected before view       |
| `suite-home-light`        | `suite:home@light`         | Hyphens normalized to `:` / `@`|

Normalization rules:
1. If the key contains `@`, the segment before `@` is split into `app:view`
   using the first `:`. Otherwise, split on `:` — first segment is `app`,
   last segment is `theme`, middle segments are joined as `view`.
2. Hyphens in the `view` segment are preserved (e.g. `home-no-score`).
3. Lookup against `pair_surfaces()` output uses the normalized canonical
   form, so any of the input aliases resolves to the same pairing.

This makes it ergonomic to copy/paste surface keys from CI logs, GitHub
issues, or older docs that used different separator conventions.

## Architecture

```
qa/mockup_reference_normalized/manifest.json ← canónico, output de Fase 1
     ↓
qa/capture_v8.py --all ← existe, no se toca
     ↓
qa/_captures_v8/CAPTURE_MANIFEST.json
     ↓
qa/diff_fidelity.py ← existe, no se toca
     ↓
qa/_fidelity_current/FIDELITY_REPORT.json
     ↓
qa/visual_auditor_v3.py analyze --all ← NUEVO
```

### Pipeline steps

1. **Pairing** — reads `manifest.json` and matches each item to a capture file
   via the canonical `surface_key` (`{app}:{view}@{theme}`) derived from
   `item["surface_key"]` in the manifest. Hub surfaces are paired the same
   way as Suite surfaces — the `app` prefix (`suite` or `hub`) is parsed
   from `surface_key`, **not** defaulted to `suite`. The capture filename
   convention is `{app}-{view}-{theme}-{WxH}.png`, indexed from
   `CAPTURE_MANIFEST.json`.
2. **Diff + BBoxes** — `scipy.ndimage.label` extracts connected diff regions,
   produces `diff.png` (side-by-side) and `overlay.png` (bboxes drawn).
3. **OCR** — Tesseract OCR on mockup and real crops. Extracts text per region.
4. **Text Diff** — `rapidfuzz` compares extracted strings; flags
   `TEXT_MISMATCH_PROBABLE` when similarity < threshold.
5. **Color Diff** — per-bbox mean RGB delta; flags `COLOR_MISMATCH` when
   ΔE > threshold.
6. **Cache** — per `(mockup_sha256, capture_sha256)` to avoid reprocessing
   unchanged images.
7. **Outputs** — `index.html`, `report.json`, `queue.md`, per-surface
   `metrics.json` + `classification.json` + `agent_package.json`.

## Quickstart for agents

```powershell
# 1. Validate que todo está en orden
.\.venv\Scripts\python.exe qa\visual_auditor_v3.py doctor

# 2. Generar capturas frescas (si hiciste cambios de UI)
.\.venv\Scripts\python.exe qa\capture_v8.py --all --theme both

# 3. Correr el auditor V3 (offline, OCR-driven)
.\.venv\Scripts\python.exe qa\visual_auditor_v3.py analyze --all

# 4. Ver el reporte HTML
start qa\_visual_auditor_v3\latest\index.html

# 5. Ver la cola priorizada
Get-Content qa\_visual_auditor_v3\latest\queue.md
```

## Workflow paso a paso para agentes

### Paso 0: Pre-requisitos
- `qa/_captures_v8/CAPTURE_MANIFEST.json` debe existir (generado por `capture_v8.py`).
- `qa/mockup_reference_normalized/manifest.json` debe existir (output de Fase 1).
- Tesseract OCR debe estar instalado y en PATH.

### Paso 1: Correr `doctor`
Si falla algo, arreglarlo antes de continuar. Los issues comunes:
- `MISSING: qa/_fidelity_current/FIDELITY_REPORT.json` → correr `diff_fidelity.py`.
- `MISSING DEP` → `pip install pytesseract rapidfuzz Pillow numpy scipy`.
- `Tesseract not found` → instalar Tesseract y asegurar que `tesseract` está en PATH.

### Paso 2: Analizar
```powershell
# Modo completo (OCR + color + diff)
.\.venv\Scripts\python.exe qa\visual_auditor_v3.py analyze --all

# Modo superficie única — acepta tanto 'suite:rutina-empty@light' como
# 'suite:rutina-empty:light' (mismo surface, separadores normalizados)
.\.venv\Scripts\python.exe qa\visual_auditor_v3.py analyze --surface suite:rutina-empty@light
.\.venv\Scripts\python.exe qa\visual_auditor_v3.py analyze --surface suite:rutina-empty:light
```

### Paso 3: Leer los outputs

#### `report.json`
Array de objetos (una por superficie). Cada objeto tiene:
- `pairing` — cómo se emparejó mockup↔captura.
- `metrics` — SSIM, MAD, changed_pixel_ratio, bbox_count, ocr_text_mockup, ocr_text_real.
- `classification` — labels, severity, explanation, recommendation, confidence.
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
- `metrics.json` — métricas heredadas de diff_fidelity + OCR + color info.
- `classification.json` — resultado del OCR diff.
- `agent_package.json` — paquete para agente sin visión.
- `crops/bbox_N/` — recortes ampliables de cada región + OCR text files.

### Paso 4: Decidir el próximo fix

Leer `agent_package.json` de la superficie top de `queue.md`.

```json
{
  "surface_key": "suite:rutina-empty@light",
  "decision": "FIX_PRODUCT_STRONG",
  "suspected_module": "shared/components/empty_states.py",
  "evidence_summary": "OCR detectó 'No hay rutinas' en mockup pero 'No hay rutinas' + ghost char en real. Color diff ΔE=12.3 en bg.",
  "confidence": "high",
  "what_to_check_first": "Buscar dónde se construye el empty state de rutina...",
  "do_not_touch_if": "confidence == 'low' o si el diff parece RENDER_NOISE_OK"
}
```

**Regla de oro:** Si `confidence == 'low'`, `decision` siempre es `NEEDS_HUMAN_REVIEW`. No tocar código.

### Paso 5: Iterar
Después de hacer un fix, regenerar capturas (`capture_v8.py --all --theme both`) y re-correr `analyze --all`. El cache evita reprocesar lo que no cambió.

## Commands

```powershell
# Analyze all surfaces
.\.venv\Scripts\python.exe qa\visual_auditor_v3.py analyze --all

# Analyze one surface (Suite example — @ separator, canonical form)
.\.venv\Scripts\python.exe qa\visual_auditor_v3.py analyze --surface suite:avisos-search@light

# Analyze one surface (Hub example — : separator, normalized internally)
.\.venv\Scripts\python.exe qa\visual_auditor_v3.py analyze --surface hub:pacientes:dark

# Analyze one surface (alias form — hyphens instead of separators)
.\.venv\Scripts\python.exe qa\visual_auditor_v3.py analyze --surface suite-rutina-empty-light

# Analyze surface only (skip deep OCR, fast mode)
.\.venv\Scripts\python.exe qa\visual_auditor_v3.py analyze --surface suite:rutina-empty@light --surface-only

# Export prioritized queue
.\.venv\Scripts\python.exe qa\visual_auditor_v3.py queue

# Clear classification cache
.\.venv\Scripts\python.exe qa\visual_auditor_v3.py clear-cache

# Validate environment
.\.venv\Scripts\python.exe qa\visual_auditor_v3.py doctor
```

## Environment

- `TESSDATA_PREFIX` — optional, path to tesseract language data.
- `NM_V3_OCR_LANG` — default `spa+eng`; override for other languages.
- `NM_V3_FUZZ_THRESHOLD` — default `85.0`; rapidfuzz ratio below this triggers
  `TEXT_MISMATCH_PROBABLE`.
- `NM_V3_COLOR_DELTA_E` — default `10.0`; CIE76 delta-E above this triggers
  `COLOR_MISMATCH`.

## Output structure

```
qa/_visual_auditor_v3/latest/
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
          ocr_mockup.txt
          ocr_real.txt
        bbox_1/ ...
```

## Taxonomy

### Labels (closed set)

- `TEXT_MISMATCH_PROBABLE` — OCR strings differ significantly (rapidfuzz < threshold)
- `COLOR_MISMATCH` — per-bbox mean RGB delta exceeds ΔE threshold
- `MISSING_COMPONENT` — expected text/component absent in real capture
- `EXTRA_COMPONENT` — unexpected text/component present in real capture
- `CHROME_MISMATCH` — window chrome / frame differences
- `RENDER_NOISE_OK` — minor anti-aliasing or sub-pixel differences, no fix needed
- `PAIRING_FIX` — mockup↔capture pairing mismatch (filename, theme, state)
- `NEEDS_HUMAN_REVIEW` — ambiguous or low-confidence result

### Decision taxonomy

- `FIX_PRODUCT_STRONG` — high confidence, clear product bug, safe to fix
- `FIX_PRODUCT_REVIEW` — medium confidence, probable product bug, review first
- `NEEDS_HUMAN_REVIEW` — low confidence or ambiguous, human decision required
- `RENDER_NOISE_OK` — deterministic noise, no action needed
- `PAIRING_FIX` — fix pairing/capture/metadata, not product code

### Confidence rules

| Confidence | Condition | Action |
|------------|-----------|--------|
| `high` | rapidfuzz ≥ 95 AND ΔE < 5 AND bbox_count ≤ 3 | `FIX_PRODUCT_STRONG` |
| `medium` | rapidfuzz 85–95 OR ΔE 5–10 OR bbox_count 4–6 | `FIX_PRODUCT_REVIEW` |
| `low` | rapidfuzz < 85 OR ΔE ≥ 10 OR bbox_count > 6 | `NEEDS_HUMAN_REVIEW` |

Confidence is the **minimum** of text, color, and structural confidence.
If any dimension is `low`, overall confidence is `low`.

## Agent package (`agent_package.json`)

Designed for agents without vision. Contains:

- `decision` — `FIX_PRODUCT_STRONG`, `FIX_PRODUCT_REVIEW`, `NEEDS_HUMAN_REVIEW`, `RENDER_NOISE_OK`, `PAIRING_FIX`
- `suspected_module` — file path guess from manifest or heuristic
- `evidence_summary` — textual description of OCR + color diffs
- `confidence` — `high`, `medium`, `low`
- `what_to_check_first` — next step suggestion
- `do_not_touch_if` — guardrail rule

### Example real `agent_package.json`

```json
{
  "surface_key": "suite:rutina-empty@light",
  "decision": "FIX_PRODUCT_STRONG",
  "suspected_module": "shared/components/empty_states.py",
  "evidence_summary": "OCR: mockup='No hay rutinas configuradas' vs real='No hay rutinas configuradas' (fuzz=97.1). Color: ΔE=2.1 en bg. Bboxes: 2. Ambos diffs dentro de tolerancia. Sin embargo, mockup muestra icono '+' que real no renderiza.",
  "confidence": "high",
  "what_to_check_first": "Verificar que el icono '+' del empty state esté condicionado correctamente en el código de rutina.",
  "do_not_touch_if": "confidence == 'low' o si el diff parece RENDER_NOISE_OK"
}
```

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
            ┌────────────────┐    ┌────────────────┐
            │ FIX_PRODUCT_   │    │ decision ==    │
            │ STRONG → fix   │    │ FIX_PRODUCT_   │
            │ FIX_PRODUCT_   │    │ REVIEW?        │
            │ REVIEW → review│    └──────┬─────────┘
            │ first          │           │
            └────────────────┘    ┌────┴────┐
                                  │         │
                                 YES       NO
                                  │         │
                                  ▼         ▼
                          ┌──────────┐ ┌──────────┐
                          │ Revisar  │ │ decision │
                          │ suspected│ │ == PAIR_ │
                          │ _module  │ │ ING_FIX? │
                          └──────────┘ └────┬─────┘
                                           │
                                    ┌──────┴──────┐
                                    │             │
                                   YES           NO
                                    │             │
                                    ▼             ▼
                            ┌──────────┐   ┌──────────┐
                            │ Revisar  │   │ RENDER_  │
                            │ pairing  │   │ NOISE_OK │
                            │ /capture │   │ o NEEDS_ │
                            └──────────┘   │ HUMAN_   │
                                           │ REVIEW   │
                                           └──────────┘
```

## Guardrails

- If `confidence == 'low'`, `decision` is forced to `NEEDS_HUMAN_REVIEW`.
- pHash distance is reported as auxiliary metric but **never** used as sole
  severity criterion.
- No VLM calls. No network. No API keys. 100% offline.
- OCR text is sanitized (strip whitespace, lowercase) before fuzz comparison.
- Empty OCR results on both sides are treated as `RENDER_NOISE_OK`, not
  `TEXT_MISMATCH_PROBABLE`.

### BBox size guardrails

- **Top-K cap.** `_extract_bboxes(..., top_k=5)` keeps at most the **5
  largest** connected diff regions by area. Smaller bboxes are dropped
  before classification, preventing pixel-noise floods from producing
  dozens of low-signal labels.
- **Area ratio tracking.** `bbox_total_area_ratio` and
  `bbox_largest_area_ratio` are surfaced in `metrics.json` and
  `agent_package.json.top_bbox` so agents can detect when a single diff
  dominates the surface (often a sign of a layout regression).
- **Connected-component threshold.** The diff mask is binarized at
  `> 20` (8-bit luminance), so sub-pixel anti-aliasing noise is dropped
  before connected-component labeling runs.
- **Normalization artifact filter.** BBoxes that fall entirely in pad or
  crop zones (per `manifest_entry.lost_pixels_*` / `pad_pixels`) are
  flagged `normalization_artifact=True` and excluded from label
  generation. If **all** bboxes are artifacts, the surface is forced to
  `NEEDS_HUMAN_REVIEW` / `confidence=low`.
- **Unreliable technical conditions.** Surfaces are marked
  `unreliable=true` (and short-circuited to `NEEDS_HUMAN_REVIEW`) when:
  mockup or capture path is missing, file fails `_is_corrupt_or_blank`
  (gray mean > 0.985), image is empty (`(0, 0)`) or absurdly large
  (max dimension > 10000 px), or PIL cannot decode the file.

### OCR noise guardrails

- **Minimum line length.** `_analyze_bbox` only computes a fuzzy ratio
  when at least one OCR line is **longer than 2 characters**
  (`len(ml) > 2 or len(rl) > 2`). Single-letter or 2-char ghost tokens
  do not trigger `TEXT_MISMATCH_PROBABLE`.
- **Deterministic preprocessing.** `_preprocess_for_ocr` does fixed
  2× LANCZOS upscale → contrast 1.5× → mild sharpen. No stochastic
  augmentation; same input always produces the same OCR output.
- **OCR error marker.** When Tesseract raises (binary missing, bad crop,
  OOM, etc.), `_ocr_image` returns `[OCR_ERROR: <message>]` instead of
  crashing the surface. Downstream code skips fuzzy comparison for such
  markers.
- **Empty-on-both-sides = noise.** When both `mockup_ocr` and
  `real_ocr` are empty/whitespace, no `TEXT_MISMATCH_PROBABLE` is
  emitted; the surface is classified as `RENDER_NOISE_OK` (or
  `NEEDS_HUMAN_REVIEW` if other signals exist).
- **Cache invalidation.** OCR results are cached per
  `(mockup_sha256, capture_sha256, bbox_geometry, ocr_version)`. When
  either image changes, the cache is automatically bypassed — no stale
  OCR can leak across renders. `clear-cache` wipes the cache on demand.

## Metrics honesty

`metrics.json` is written per surface as `asdict(Metrics(...))`. Of the 11
fields defined on the `Metrics` dataclass, **only 4 are actually
populated** during analysis. The remaining 7 are placeholders kept for
schema compatibility with `diff_fidelity.py` outputs — agents should
**not** read them as ground truth.

| Field                       | Status        | Source / meaning                                    |
|-----------------------------|---------------|-----------------------------------------------------|
| `ssim`                      | placeholder   | Always `0.0`. V3 does not compute SSIM.             |
| `ssim_method`               | placeholder   | Always `""`.                                         |
| `mean_abs_diff`             | placeholder   | Always `0.0`. V3 does not compute global MAD.       |
| `max_abs_diff`              | placeholder   | Always `0.0`.                                       |
| `changed_pixel_ratio`       | placeholder   | Always `0.0`. Use `bbox_total_area_ratio` instead.  |
| `size_mismatch`             | placeholder   | Always `False`. Pairing guarantees equal sizes.     |
| `phash_distance`            | placeholder   | Always `-1`. Auxiliary only; never a severity       |
|                             |               | criterion.                                            |
| `phash_method`              | placeholder   | Always `"imagehash.phash"` — string only, not run.  |
| `bbox_count`                | **populated** | Number of diff bboxes returned by `_extract_bboxes`. |
| `bbox_total_area_ratio`     | **populated** | Sum of `area_ratio` across all bboxes.              |
| `bbox_largest_area_ratio`   | **populated** | `area_ratio` of the largest bbox (or `0.0`).        |
| `bbox_largest_geometry`     | **populated** | `[x0, y0, x1, y1]` of the largest bbox (or `[]`).   |

**Why so many placeholders?** V3 deliberately does not reimplement SSIM,
global MAD, pHash, or pixel-ratio diffs — those live in `diff_fidelity.py`,
which V3 inherits upstream outputs from. Duplicating them here would be
both slower and a source of false equivalence between two different
implementations. The four bbox fields are the only metrics V3 actually
computes; everything else is schema padding.

**For agents:** rely on `agent_package.json.top_bbox`, `bbox_count`, and
`bbox_*_area_ratio` for structural reasoning. Treat any non-zero value
in `ssim`, `mean_abs_diff`, `phash_distance`, etc. as a bug in V3 —
those should always be at their default placeholder values.

## Hub pairing (corrected)

Hub surfaces are paired identically to Suite surfaces — there is no
separate code path, no app-specific defaults, and no `app="suite"`
fallback.

- The normalized manifest (`qa/mockup_reference_normalized/manifest.json`)
  stores each surface under a `surface_key` of the form
  `{app}:{view}@{theme}`. The `app` segment is **`suite`** or **`hub`**
  and is **always present** in `surface_key`.
- `pair_surfaces()` parses the `app` prefix **from `surface_key`**
  (split on `:`), and only falls back to a default when the manifest
  entry has no `surface_key` at all (a data-quality error, not the
  expected path).
- Capture filenames follow the convention
  `{app}-{view}-{theme}-{WxH}.png` (e.g.
  `hub-pacientes-dark-960x600.png`) and are indexed from
  `CAPTURE_MANIFEST.json` by `(app, view, theme)`.
- Mockup files are looked up at
  `qa/mockup_reference_normalized/{theme}/{view}.png` — the `app`
  prefix is **not** part of the path. Hub and Suite can share view
  names (`home`, `pacientes`, etc.) without collision because their
  mockups live in separate `light/` / `dark/` subdirs per manifest.

**Historical bug (fixed):** earlier versions of `pair_surfaces()` read
`item.get("app", "suite")`, which silently demoted every Hub surface to
`app="suite"` because the normalized manifest entries do not expose a
top-level `app` field — only `surface_key`. Pairings would then either
miss the real capture or grab a Suite capture with the same view name.
The corrected implementation parses `app` from `surface_key`, so
`hub:pacientes@dark` now resolves to the Hub capture and mockup
unambiguously.

## Limitations (honestidad)

- **No detecta LAYOUT_SHIFT puro.** Si un componente se movió 20px pero el
  OCR y el color son idénticos, V3 no lo reporta. Usar V2 o inspección manual.
- **OCR puede fallar.** Texto muy pequeño, fuentes decorativas, o antialiasing
  agresivo pueden producir ghost characters o omissions. Siempre revisar
  `crops/bbox_N/ocr_*.txt`.
- **No entiende semántica.** V3 compara strings, no significado. "Cancelar" vs
  "Cancel" es mismatch aunque sean intencionalmente diferentes por i18n.
- **Color diff es global por bbox.** Gradientes o imágenes complejas pueden
  producir falsos positivos de `COLOR_MISMATCH`.
- **No detecta missing icons sin OCR fallback.** Iconos sin texto asociado
  pueden pasar desapercibidos si no hay cambio de color significativo.
- **Idioma depende de Tesseract.** Si `spa+eng` no cubre el idioma de la UI,
  el OCR será pobre. Ajustar `NM_V3_OCR_LANG`.
- **No reemplaza V2.** V2 (VLM-driven) sigue vivo en Fase 2 y es preferible
  cuando se dispone de backend neural y se necesita análisis semántico.

## Dependencies

| Package | Purpose | Install |
|---------|---------|---------|
| Tesseract | OCR engine | `choco install tesseract` / `apt install tesseract-ocr` |
| pytesseract | Python wrapper | `pip install pytesseract` |
| rapidfuzz | Fast string matching | `pip install rapidfuzz` |
| Pillow | Image I/O | `pip install Pillow` |
| numpy | Arrays + diff | `pip install numpy` |
| scipy | Connected components | `pip install scipy` |

Verificar instalación con `visual_auditor_v3.py doctor`.

## Troubleshooting

| Síntoma | Causa probable | Fix |
|---------|---------------|-----|
| `0 surfaces analyzed` | `manifest.json` vacío o mal parseado | Verificar `qa/mockup_reference_normalized/manifest.json` |
| `all unpaired` | Capturas faltantes o nombres no coinciden | Correr `capture_v8.py --all --theme both` |
| `TesseractNotFoundError` | Tesseract no instalado o no en PATH | Instalar Tesseract; reiniciar terminal |
| `OCR empty on both sides` | Texto muy pequeño o fondo complejo | Revisar crops manualmente; ajustar `--psm` |
| `Cache stale` | Imágenes cambiaron pero SHA-256 coincide (raro) | `clear-cache` y re-correr |
| `doctor` reporta `MISSING DEP` | Dependencia no instalada | `pip install pytesseract rapidfuzz Pillow numpy scipy` |
| `COLOR_MISMATCH` en todo | ΔE threshold muy bajo | Ajustar `NM_V3_COLOR_DELTA_E` |
| `TEXT_MISMATCH_PROBABLE` en todo | Fuzz threshold muy alto | Ajustar `NM_V3_FUZZ_THRESHOLD` |

## Git hygiene

`qa/_visual_auditor_v3/` is in `.gitignore`. Do not commit generated outputs.
Commit only `qa/visual_auditor_v3.py`, `tests/test_visual_auditor_v3.py`, and
`docs/VISUAL_AUDITOR_V3.md`.

## V2 sigue vivo en Fase 2

V3 no reemplaza V2. Ambos coexisten:
- **V2** — VLM-driven, semántico, requiere backend neural (`NM_VLM_BACKEND`).
- **V3** — OCR-driven, determinista, 100% offline, $0 cost.

En Fase 2, los agentes pueden elegir:
- `visual_auditor_v2.py` cuando hay VLM disponible y se necesita análisis profundo.
- `visual_auditor_v3.py` cuando se necesita velocidad, reproducibilidad, o no hay
  acceso a VLM.

Los outputs de ambos (`_visual_auditor_v2/` y `_visual_auditor_v3/`) son
independientes y pueden compararse para validación cruzada.

## What V3 does NOT do (lessons from V2)

- No VLM calls. No semantic understanding. No "suspected module" from neural guess.
- No hardcoded semantic regions (header/sidebar/content/cards/modal/CTA/bottom/right/form).
- No heuristics of "text density delta" / "edge density delta".
- No 7-dimension heuristic scoring queue.
- No crawler (reuses `capture_v8.py`).
- No global diff (reuses `diff_fidelity.py`).
- No manifest reconstruction (reads canonical `manifest.json`).
- No auto-approval. Low confidence means `NEEDS_HUMAN_REVIEW`.
- No blind microfixes. If OCR is empty on both sides, no text mismatch is reported.
