# Evidence: suite:dbt-library@light — blocked (NOT a closure)

> **NO cierre.** Esta key sigue **abierta** (`- [ ]`) en `VISUAL_REPAIR_HANDOFF.md`.
> No hay record en `docs/closure_evidence/` para esta key ni se generó uno con
> este archivo. Este bundle es únicamente evidencia versionada del último run
> validado antes de que quedara bloqueada, para no perder los números del
> intento de reparación.

## Contexto

- **Key:** `suite:dbt-library@light`
- **Base commit auditado:** `b882248f0` (HEAD al momento de la captura;
  working tree tenía el diff de reparación sin commitear —
  `git_tracked_dirty: true` en el manifest de captura).
- **Commit que codificó ese mismo diff:** `9a5b47600` — `repair: improve dbt
  library light visual alignment` (creado ~16 min después de esta captura).
- **Capturado:** 2026-07-03T06:16:13 (hora local, `-03:00`).

## Reparación aplicada (resumen)

1. `_TwoLineElideLabel` en `app/modules/dbt_qt.py` — corrige overlap real de
   texto de descripción sobre la fila de duración/práctica.
2. Altura del chip `NMTabs` variant=`filter` density=`compact` en
   `shared/components/buttons.py`: 28px → 24px (content-box Qt), alineado a
   los 26px border-box medidos en el canónico. Único consumidor de esa
   combinación variant+density es `dbt_qt.py` — sin blast radius a otros
   screens.
3. Ajustes de tamaño de fuente (11px→10px) en `summary_lbl`, `dur_lbl`,
   `guide_lbl` para acercarse al 10.5px del mockup.

## Métricas finales (bloqueado, no PASS)

| métrica | valor | umbral | resultado |
|---|---:|---:|---|
| `changed_pixel_ratio` | **0.11175** | ≤0.10 (dense-aware) | **FALLA** (único bloqueante) |
| `mean_abs_diff` | 0.03414 | ≤0.035 | pasa |
| `windowed_ssim` | 0.73494 | ≥0.65 (dense-aware) | pasa |
| `largest_region_ratio` | 0.005872 | ≤0.08 | pasa |
| `odiff diff_percentage` | 3.05% | ≤8% | pasa |
| `layout.max_bbox_delta_px` | 14 | ≤18 | pasa |
| VAS `fail_count` / `divergences` | 0 / `[]` | — | limpio |

**Causa del bloqueo:** residuo de anti-aliasing de texto Qt-vs-Chromium en
superficie text-dense (`canonical_gray_std=26.48<35`), consistente con
MISMATCH#20 (`docs/QT_HTML_KNOWN_MISMATCHES.md`). Tres iteraciones
consecutivas de ajuste fino no movieron la métrica de forma significativa
tras corregir los bugs estructurales reales (overlap de texto, altura de
chip). No hay ruta técnica local adicional identificada sin tocar más
superficie compartida.

## Archivos

- `LAYERED_VISUAL_REPORT.json` — reporte completo del comparador para esta key.
- `introspection.json` — sidecar VAS/introspección de la misma captura
  (`fail_count: 0`, sin divergencias semánticas).
- `panel_suite_dbt-library_light.png` — panel canonical/actual/diff.
