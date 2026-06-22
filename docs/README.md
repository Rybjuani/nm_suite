# Documentos de UI y QA visual

## Fuente de verdad vigente

Para la migración UI Suite + Hub, la fuente operativa vigente es:

- [`../PLAN_MIGRACION_UI_V2.md`](../PLAN_MIGRACION_UI_V2.md) (único plan activo)
- `agent_harness/episodes/20260621_202526_E5_FIDELITY_final_visual_qa/EPISODE.md`

Estado actual: UI V2 cerrada operativamente, último reconcile visual en `5bad967`.
Evidencia de cierre:

- `runtime_live_probe.py --all --theme both` → OK=22, DEFECTS_FOUND=0, FAILED=0.
- `pytest tests/` → 317 passed.
- Barrido visual técnico de las capturas finales → sin deuda accionable.
- `qa/mockup_reference_static/` (86 PNGs = 43 estados × 2 temas) es la **referencia mockup
  canónica estática** contra `neuromood-mockup.html` (SHA256
  `0944e6516c0da83cf3d68d5e1ae3ebdf1f9dd9fe3261a0d49131b03634587b4e`, verificado).
  Se regenera con `qa/capture_mockup.py --all --theme both --clean --out-dir
  qa/mockup_reference_static`. **No trackeado** (gitignored), vive como snapshot regenerable.
- `qa/capture_v8.py` produce el set **runtime v8** (recetas de la app corriendo, state_ids
  del harness). Es **distinto** del set mockup estático: las pantallas se solapan pero los
  `state_id` difieren. Ambos dominios se complementan, no se contradicen.

`qa/diff_fidelity.py` sigue siendo una señal auxiliar, no un gate final: sus umbrales
SSIM/MAD son útiles para comparar tendencias, pero no declaran deuda por sí solos.
Los reportes de diff (`qa/_fidelity_diff/`, `qa/_fidelity_fresh/`) son **artefactos efímeros**
gitignored; no deben versionarse ni usarse como estado vigente.

## Artefactos regenerables (gitignored)

Los siguientes directorios son outputs del harness; se regeneran con cada corrida y no
deben trackearse:

- `qa/_captures*/` — runs de captura v8.
- `qa/_baseline_*/` — baselines históricos del harness.
- `qa/_fidelity_diff/`, `qa/_fidelity_fresh/` — diffs SSIM/MAD.
- `qa/_runtime_probe/`, `qa/_probe_*/`, `qa/_verify_*/` — outputs del runtime probe.
- `qa/_visual_sentinel/`, `qa/visual_sentinel_baselines/{proposed,approved}/` — outputs
  regenerables del sentinel visual (el `registry.json` del sentinel sí se versiona).
- `qa/_build*.txt`, `qa/_capture_run.log`, `qa/_pf3.log`, `*.log` — logs efímeros.
- `qa/mockup_reference_static/` — snapshot regenerable del set mockup canónico (86 PNGs).
- `_scratch_trash/` — scratch local; 155 MB de runs históricos pre-F0 y mockup_targets stale.

Si un agente futuro necesita evidencia histórica, regenerar con `python qa/capture_v8.py
--all --clean --out-dir <dir>` y/o `python qa/capture_mockup.py --all --theme both --clean
--out-dir qa/mockup_reference_static`.

## Microestados fuera del gate canónico

Estos `state_id` **no pertenecen** al set canónico (86 PNGs mockup). Aparecen solo en
comentarios del harness documentando su exclusión:

- `respiracion-preset-3min`, `respiracion-preset-10min` — microestados de interacción con
  chips de duración. Movidos a `extended_runtime_qa`.
- `timer-preset-5min`, `timer-preset-45min` — idem para Timer.
- `avisos-completed` — microestado de marcar aviso como hecho. Movido a `extended_runtime_qa`.
- `dbt-practice-closure` — pantalla de cierre DBT removida del producto (C4-05); la
  evidencia era stale y generaba falsos positivos.

No usar como referencia de estado. No regenerar como parte del gate.

## Documentos históricos

Los documentos `FASE*.md`, `PLAN FASEADO.md`, `PLAN_COHERENCIA_VISUAL_ACTUALIZADO.md`,
`PLAN_MODULARIZACION_COMPONENTES.md`, `PLAN_MODULO_DBT.md`, `VISUAL_QA_AUDIT.md`,
`HANDOFF_CONTINUACION_LOCAL.md`, `HANDOFF_DBT_SUPABASE.md`,
`COMPARACION_F0_F1_EXACTA.md`, `EDITOR_GLOBAL_TEXTOS_FASE0_AUDIT.md` y
`CAPTURE_MANIFEST_SUMMARY.md` conservan contexto de auditorías, planes y handoffs anteriores.
Pueden mencionar commits antiguos, capturas stale, fases pendientes o deuda visual que ya
fue cerrada por el flujo V2.

`PLAN_MIGRACION_UI.md` (V1) fue eliminado en favor del V2, cuyo §3 contiene el postmortem
del V1 y §13 el handoff final.

Usarlos como referencia histórica está bien; no deben usarse como backlog vivo sin
revalidar contra `PLAN_MIGRACION_UI_V2.md`, el harness y el estado actual de `main`.

## Episodes del harness (agent_harness/episodes/)

Los episodios son el historial operativo de tareas ejecutadas por el harness. Se conservan
los **hitos técnicos**; los runs intermedios de tipo `DOCS_*` (tareas documentales ya
consolidadas en este README o en el V2) fueron podados. Permanecen:

- E0–E6: gates de baseline, fidelidad, continuidad, owner audit.
- C0–C6: gates críticos (gate harness, primitives, suite critical, suite modules,
  hub critical, missing screens audit, final evidence).
- MICRO_VISUAL_POST_69BF781: pass micro-visual post-fix.
- VISUAL_DEBT_FINAL: cierre de deuda visual.
