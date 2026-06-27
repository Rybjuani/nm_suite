# Documentos de UI y QA visual

## Fuente de verdad vigente

La migración UI Suite + Hub está **cerrada operativamente**. La referencia de cómo se llegó
aquí (diccionario Web→Qt, decisiones owner, postmortem, crónica del cierre) es **histórica**:

- [`./PLAN_MIGRACION_UI_V2.md`](./PLAN_MIGRACION_UI_V2.md) — plan maestro de la migración,
  **cerrado** (ver su header: documento histórico, no plan vivo ni backlog activo).
- `agent_harness/episodes/20260621_202526_E5_FIDELITY_final_visual_qa/EPISODE.md`

Estado actual: UI V2 cerrada operativamente, último reconcile visual en `5bad967`.
Evidencia de cierre:

- `runtime_live_probe.py --all --theme both` → OK=22, DEFECTS_FOUND=0, FAILED=0.
- `pytest tests/` → 315 passed.
- Barrido visual técnico de las capturas finales → sin deuda accionable.
- `qa/_mockup_canonical/` (86 PNGs = 43 estados × 2 temas + `README.md` + `MANIFEST.{csv,json}`)
  es la **referencia mockup canónica estática** vigente. Su README apunta a
  `qa/pack canonico/neuromood-mockup_reparado.html` como fuente única y el set
  queda **trackeado en el repo** (89 archivos, NO gitignored) como snapshot
  canónico.
- `qa/mockup_reference_static/` queda sólo como snapshot **histórico/no canónico**
  de flujos anteriores. No debe usarse como fuente de verdad operativa ni para
  abrir deuda nueva.
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
- `_scratch_trash/` — scratch local; 155 MB de runs históricos pre-F0 y mockup_targets stale.

Si un agente futuro necesita evidencia histórica, regenerar con `python qa/capture_v8.py
--all --clean --out-dir <dir>`. Para el canonical vigente, seguir la receta
documentada en `qa/_mockup_canonical/README.md`.

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

`PLAN_MIGRACION_UI_V2.md` (V2) es el plan maestro de la migración, ya **cerrada**: se conserva
en `docs/` como referencia técnica (su header lo marca como histórico, no plan vivo). El V1
(`PLAN_MIGRACION_UI.md`) fue eliminado en su momento; el §3 del V2 contiene el postmortem del
V1 y el §13 el handoff final.

Usarlos como referencia histórica está bien; no deben usarse como backlog vivo. La fuente de
verdad actual es el código en `main`, este README y los tests de contrato — no un plan cerrado.

## Episodes del harness (agent_harness/episodes/)

Los episodios son el historial operativo de tareas ejecutadas por el harness. Se conservan
los **hitos técnicos**; los runs intermedios de tipo `DOCS_*` (tareas documentales ya
consolidadas en este README o en el V2) fueron podados. Permanecen:

- E0–E6: gates de baseline, fidelidad, continuidad, owner audit.
- C0–C6: gates críticos (gate harness, primitives, suite critical, suite modules,
  hub critical, missing screens audit, final evidence).
- MICRO_VISUAL_POST_69BF781: pass micro-visual post-fix.
- VISUAL_DEBT_FINAL: cierre de deuda visual.
