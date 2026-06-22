# Documentos de UI y QA visual

## Fuente de verdad vigente

Para la migracion UI Suite + Hub, la fuente operativa vigente es:

- [`../PLAN_MIGRACION_UI_V2.md`](../PLAN_MIGRACION_UI_V2.md)
- `agent_harness/episodes/20260621_202526_E5_FIDELITY_final_visual_qa/EPISODE.md`

Estado actual: UI V2 cerrada operativamente en `c0c692e` y reconciliada en `5c12ab5`.
Evidencia de cierre:

- `runtime_live_probe.py --all --theme both` -> OK=22, DEFECTS_FOUND=0, FAILED=0.
- `capture_v8.py --all --theme both` -> 98 capturas, 0 failed.
- `pytest tests/` -> 317 passed.
- Barrido visual tecnico de las capturas finales -> sin deuda accionable.

`qa/diff_fidelity.py` sigue siendo una senal auxiliar, no un gate final: sus umbrales
SSIM/MAD son utiles para comparar tendencias, pero no declaran deuda por si solos.

## Documentos historicos

Los documentos `FASE*.md`, `PLAN FASEADO.md`, `PLAN_COHERENCIA_VISUAL_ACTUALIZADO.md`,
`VISUAL_QA_AUDIT.md` y `HANDOFF_CONTINUACION_LOCAL.md` conservan contexto de auditorias,
planes y handoffs anteriores. Pueden mencionar commits antiguos, capturas stale, fases
pendientes o deuda visual que ya fue cerrada por el flujo V2.

Usarlos como referencia historica esta bien; no deben usarse como backlog vivo sin
revalidar contra `PLAN_MIGRACION_UI_V2.md`, el harness y el estado actual de `main`.
