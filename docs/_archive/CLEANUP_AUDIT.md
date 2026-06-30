# Auditoría de limpieza · nm_suite

**Fecha:** 2026-06-22
**Rama auditada:** `main` @ `5bad967` (HEAD actual)
**Tipo:** DRY-RUN · ningún archivo ha sido borrado todavía.
**Objetivo:** aislar evidencia contaminante, docs viejas, planes obsoletos, capturas/zips stale y
artefactos que puedan sesgar a agentes futuros. Una sola fuente de verdad visual y documental.

---

## TL;DR

- **El gate de git está limpio.** `git status -sb` solo reporta `?? neuromood_mockup_capturas/`,
  que ya está gitignored (línea 113 del `.gitignore`). No hay tracked sucio.
- **Toda la "contaminación" detectada es a nivel de filesystem**, no del gate. Está en directorios
  ya cubiertos por `.gitignore` (`_scratch_trash/`, `qa/_captures*/`, `qa/_baseline_*/`,
  `qa/_fidelity_*/`, `qa/_runtime_probe/`, `qa/_visual_sentinel/`, `qa/_build*.txt`,
  `qa/_capture_run.log`, etc.).
- **`koki.zip`:** 0 hits en todo el repo. No hay contaminación por ZIP contaminado.
- **Strings contaminantes (`preset-3min`, `preset-10min`, `preset-5min`, `preset-45min`,
  `avisos-completed`, `suite-dbt-practice-closure`):** en código activo = 0. Solo aparecen en:
  - Comentarios de `qa/capture_v8.py` documentando la purga (correcto).
  - Artefactos gitignored (PNGs stale, manifests stale, logs).
  - `docs/FASE9*` y `docs/FASE10*` (docs históricos, no son backlog).
  - `agent_harness/episodes/*` viejos (histórico).
- **`docs/README.md` está desactualizado:** cita commits viejos (`c0c692e`, `5c12ab5`), paths
  inexistentes (`qa/_mockup_targets/`), y un conteo "98 capturas" que no coincide con el set
  canónico actual (86 = 43 × 2).
- **Mockup canónico confirmado:** `neuromood-mockup.html` (raíz). El README de las capturas dice
  "neuromood-mockup(6).html" pero el SHA256 `0944e651…` del manifest matchea exactamente el
  archivo en disco. Es el mismo archivo; el "(6)" es vestigio histórico de versionado.
- **Set canónico actual:** `neuromood_mockup_capturas/` (86 PNGs = 43 estados × 2 temas, 7.5 MB,
  con `manifest.csv` + `manifest.json` + `README.txt`). Regenerable con `capture_mockup.py`.

### Tamaño total de artefactos stale gitignored
| Directorio | Tamaño |
|---|---|
| `_scratch_trash/` | 155 MB |
| `qa/_visual_sentinel/` | 42 MB |
| `qa/_fidelity_diff/` | 20 MB |
| `qa/_baseline_f0_phase01/` | 6.9 MB |
| `qa/_captures_v8_fresh/` | 4.3 MB |
| `qa/_captures_c1/c2/micro_*` | 3.5 MB |
| `qa/_runtime_probe/` | 1.2 MB |
| `qa/_captures_block_*` | 1.2 MB |
| `qa/_captures_v8/` | 109 KB |
| **TOTAL stale** | **≈234 MB** |

---

## Clasificación de hallazgos

### 1. KEEP_CANONICAL — fuente de verdad vigente

| Path | Tipo | Justificación |
|---|---|---|
| `neuromood-mockup.html` | Mockup HTML canónico | SHA256 `0944e651…` matchea el manifest de las 86 capturas; único mockup en git. |
| `neuromood_mockup_capturas/` | Set visual canónico (86 PNGs) | 43 estados × 2 temas; `manifest.csv`, `manifest.json`, `README.txt`. Regenerable con `qa/capture_mockup.py`. Ya gitignored (línea 113). |
| `qa/capture_mockup.py` | Generador del set canónico | Regenera `neuromood_mockup_capturas/` con `--all --theme both --clean`. |
| `qa/capture_v8.py` | Generador del set runtime v8 | 49 recetas × 2 temas. Comentarios en líneas 271/281/446/487/1152 documentan correctamente que `dbt-practice-closure`, `respiracion-preset-3min/10min`, `timer-preset-5min/45min`, `avisos-completed` están **fuera del gate** y movidos a `extended_runtime_qa`. |
| `qa/visual_sentinel.py` | Sentinel visual autodiscoverable | Auditor visual independiente, introducido en commit `0a64caf`. |
| `qa/visual_sentinel_contracts/` | Contratos del sentinel | Tracked, fuente de verdad del sistema de auditoría. |
| `qa/runtime_live_probe.py` | Probe runtime | 22 checks (`--all --theme both` → OK=22). |
| `qa/diff_fidelity.py` | Diff auxiliar (no gate) | `docs/README.md` lo declara "señal auxiliar, no un gate final". |
| `qa/README_VISUAL_SENTINEL.md` | Doc del sentinel | Documenta el sistema de auditoría visual. |
| `PLAN_MIGRACION_UI_V2.md` | Plan vigente | Su propio header: "Estado vivo · documento de handoff entre agentes. Supera a PLAN_MIGRACION_UI.md". |
| `agent_harness/` (completo) | Harness de agentes | Perfiles, prompts, scripts, ejemplos. |
| `agent_harness/episodes/20260621_202526_E5_FIDELITY_final_visual_qa/` | Handoff canónico de cierre UI V2 | Citado por `docs/README.md` como fuente de verdad del cierre. |
| `docs/README.md` | Índice de docs | Vigente pero **necesita UPDATE** (ver §3). |
| `app/`, `hub/`, `shared/`, `db/`, `assets/`, `tests/`, `design/`, `installer_style_debug.txt` (gitignored) | Producto real | Out of scope: NO TOCAR (regla: no lógica clínica, DB, auth, sync, IA). |

### 2. DELETE_STALE — artefactos obsoletos fuera del gate

**Todos gitignored. Limpieza es segura (no afecta `git diff` ni `git status`).**

| Path | Tamaño | Motivo |
|---|---|---|
| `_scratch_trash/` (todo) | 155 MB | 111 dirs `captures_v8_*` (runs históricos pre-F0), 3 dirs `mockup_targets_*`, 1 dir `mockup_audit_contact_sheets`. Evidencia muerta de iteraciones previas. |
| `qa/_captures_v8_fresh/` | 4.3 MB | 98 PNGs (86 canónicos + 10 stale: `respiracion-preset-3min/10min`, `timer-preset-5min/45min`, `avisos-completed`). Manifest inconsistente (declara 2, hay 98). Generado en commit `6aceefc`, pre-purga `5bad967`. |
| `qa/_captures_v8/` | 109 KB | Última ejecución del script (2 PNGs: `suite-avisos-today-{dark,light}`). Output regenerable. |
| `qa/_baseline_f0_phase01/` | 6.9 MB | Baseline inicial con 132 capturas, incluye los 5 microestados eliminados (`preset-*`, `avisos-completed`). Generado contra `ad9f5b4` (commit muy anterior). |
| `qa/_fidelity_diff/` | 20 MB | Diffs contra baseline stale; incluye los 5 microestados purgados. `docs/README.md` dice: "son artefactos efímeros y no deben versionarse como estado vigente". |
| `qa/_captures_block_*` (8 dirs) | 1.2 MB | Runs de bloques temáticos (`buttons_actividades`, `chrome_height_home`, `focus_textos`, `home_cards`, `home_hero_bar`, `home_layout`, `slider_animo`, `textos_dirty`). Históricos de pre-C0. |
| `qa/_captures_c1_primitives_before/`, `qa/_captures_c1_primitives_after/` | 929 KB | Episodio C1. Before/after. |
| `qa/_captures_c2_suite_critical_before/`, `qa/_captures_c2_suite_critical_after/` | 1.1 MB | Episodio C2 suite critical. |
| `qa/_captures_c2_dbt_fit_after/`, `qa/_captures_c2_onboarding_check_after/` | 325 KB | C2 subruns. |
| `qa/_captures_micro_post_69bf781_before/`, `qa/_captures_micro_post_69bf781_after/` | 1.1 MB | Micro pass post-fix `69bf781`. Histórico. |
| `qa/_runtime_probe/` | 1.2 MB | Sidecars JSON + PNGs del runtime probe. Regenerable. |
| `qa/_visual_sentinel/` | 42 MB | Outputs regenerables del sentinel (`latest/`, `runs/`, `visual_sentinel_run.log`). El registry.json SÍ está versionado. |
| `qa/_capture_run.log` | 4.4 KB | Log efímero de ejecución de captura. Gitignored por `*.log`. |
| `qa/_build_run.txt` | 1.1 KB | Log efímero de build. Gitignored por `qa/_build*.txt`. |
| `qa/_pf3.log` | 6.6 KB | Log efímero. Gitignored por `*.log`. |

**Total DELETE_STALE: ≈234 MB en disco, 0 impacto en `git diff`/`git status`.**

### 3. MOVE_TO_ARCHIVE_OUTSIDE_GATE — no aplica

Todo lo detectado como stale YA está gitignored. No hay archivos tracked que requieran moverse.

(Excepción: si en la pasada 2 decides preservar `qa/_captures_v8_fresh/` o `_baseline_f0_phase01/`
como evidencia histórica, lo correcto es **moverlos** fuera de `qa/` a un directorio como
`docs/_archive/baselines/` antes de eliminarlos del filesystem, NO dejarlos en el lugar
original donde se regeneran. Ver §5 — OWNER.)

### 4. UPDATE_REFERENCE — referencias desactualizadas en gate

| Path | Problema | Acción propuesta |
|---|---|---|
| `docs/README.md` | 1) Cita HEAD `c0c692e`/`5c12ab5` (real = `5bad967`). 2) "98 capturas, 0 failed" (set canónico actual = 86). 3) "`qa/_mockup_targets/` está versionado como referencia canónica" (path inexistente; el real es `neuromood_mockup_capturas/`, regenerable, gitignored). 4) Menciona `qa/_fidelity_fresh/` además de `_fidelity_diff/` (también gitignored, igual de efímero). | Reescribir el bloque "Fuente de verdad vigente" para que refleje: HEAD real, conteo canónico 86, ubicación real del set (`neuromood_mockup_capturas/`), política de artefactos efímeros. |
| `docs/CAPTURE_MANIFEST_SUMMARY.md` | Título dice "Manifest V8 — Estado Post-Auditoría 2026-06-21", pero el set canónico mockup es `neuromood_mockup_capturas/`, no `qa/_captures_v8_fresh/`. Comando de regeneración apunta al dir stale. | Renombrar o reescribir para que apunte al set canónico (`qa/capture_mockup.py --all --theme both --clean --out-dir neuromood_mockup_capturas`), o marcarlo como histórico del gate v8 runtime. |
| `docs/FASE9_SUITE_RESPIRACION_TIMER.md` | Menciona `preset-3min` y `preset-5min` como estados canónicos. | Aclarar en el doc que son microestados históricos, fuera del gate canónico (mover a `extended_runtime_qa`). O re-marcar como histórico. |
| `docs/FASE10_SUITE_RUTINA_ACTIVIDADES_AVISOS.md` | Menciona `avisos-completed` como estado canónico. | Idem. |

**Nota:** `PLAN_MIGRACION_UI.md` (V1) **no requiere update** — su propio header dice:
"⚠️ SUPERADO por PLAN_MIGRACION_UI_V2.md. Este documento se conserva como histórico".
Es histórico auto-declarado. Ver §5 para decisión de mantener/eliminar.

### 5. NEEDS_OWNER_DECISION — ambigüedades o costos de decisión

| # | Pregunta | Opciones | Recomendación del agente |
|---|---|---|---|
| 5.1 | ¿Eliminar `PLAN_MIGRACION_UI.md` (V1, raíz) o dejarlo como histórico explícito? | (a) Eliminar — el V2 lo reemplaza, ya está auto-marcado como histórico. (b) Mantener — fuente del postmortem que cita el V2. | (a) Eliminar: el V2 ya cita "conservado como histórico / fuente del postmortem (§3 del V2)" → se puede mover esa nota al V2 y borrar el archivo. Riesgo bajo: el V2 sigue siendo legible sin el V1. |
| 5.2 | ¿Limpiar episodios viejos en `agent_harness/episodes/`? | (a) Mantener los 20 episodios (tracked, 4–40 KB cada uno, ~325 KB total). (b) Conservar solo los hitos estructurales: E0, E5_FIDELITY, C0–C6, MICRO_VISUAL_POST_69BF781, VISUAL_DEBT_FINAL, E6_OWNER_VISUAL_AUDIT. Eliminar runs intermedios DOCS_*. | (b) Recomendable: 9 episodios bastan para reconstruir la trazabilidad. Los `DOCS_*` son runs de cierre de sub-tareas ya consolidadas. Impacto: bajo (pocos KB), valor: reduce ruido para futuros episodios que referencien episodes/. |
| 5.3 | ¿Limpiar logs efímeros (`_capture_run.log`, `_build_run.txt`, `_pf3.log`)? | (a) Sí. (b) No, son baratos y ya gitignored. | (a) Sí en la pasada de limpieza general — pesan <12 KB total y ya están gitignored. |
| 5.4 | ¿`neuromood_mockup_capturas/` debe quedar gitignored o trackearse? | (a) Gitignored (output regenerable, como ahora). (b) Trackear como fuente de verdad visual. | (a) Mantener gitignored. El `capture_mockup.py` lo regenera deterministamente y su contenido se valida por SHA256 del HTML fuente. Trackear 7.5 MB de PNGs que pueden regenerarse añade ruido a diffs. Si el owner quiere tener un snapshot inmutable, la opción correcta es CI/storage externo, no git. |
| 5.5 | ¿Eliminar `qa/_captures_v8_fresh/` y `_baseline_f0_phase01/` antes o después de validar que el set canónico regenerado es idéntico? | (a) Borrar primero, regenerar después. (b) Regenerar primero (`capture_v8.py --all --theme both --clean`), comparar SHA256 con `neuromood_mockup_capturas/`, y solo entonces borrar. | (b) Más seguro: confirma que el set canónico real produce exactamente los 86 PNGs esperados antes de destruir evidencia. Si la regeneración falla o produce un set distinto, conservamos el fallback hasta diagnosticar. |
| 5.6 | ¿`qa/_runtime_probe/` y `qa/_visual_sentinel/` se limpian ahora? | (a) Sí, son outputs regenerables y pesan 43 MB total. (b) No, dejarlos como historial del último run. | (a) Sí. Ambos son regenerables (`runtime_live_probe.py --all --theme both`, `visual_sentinel.py --run`). El registry.json del sentinel (tracked) es la fuente de verdad, no las imágenes. |

---

## Validación previa a la pasada 2

Antes de aplicar cambios, verificar:

```bash
# 1. Working tree limpio (ya lo está)
git status -sb
# Salida esperada: solo ?? neuromood_mockup_capturas/ (gitignored)

# 2. Tamaño actual de artefactos stale
du -sh _scratch_trash/ qa/_captures*/ qa/_baseline_*/ qa/_fidelity_*/ qa/_runtime_probe/ qa/_visual_sentinel/

# 3. Búsqueda de strings contaminantes (esperado: 0 en tracked, solo en .gitignored/)
git grep -n "suite-dbt-practice-closure\|koki.zip\|preset-3min\|preset-10min\|preset-5min\|preset-45min\|avisos-completed"
```

Tras la pasada 2, volver a correr:

```bash
git status -sb
git diff --stat
git grep -n "suite-dbt-practice-closure\|koki.zip\|preset-3min\|preset-10min\|preset-5min\|preset-45min\|avisos-completed"
.venv\Scripts\python.exe -m pytest tests/
ruff check .
git diff --check
```

---

## Notas

- Esta auditoría **NO borra nada todavía.** Es DRY-RUN.
- La pasada 2 empezará solo tras aprobación del owner (especialmente para §5).
- Ningún archivo tracked será borrado sin reemplazo o justificación explícita.
- Ningún test funcional será tocado. Ningún archivo de producto real (`app/`, `hub/`,
  `shared/`, `db/`, `assets/`, `tests/`, `design/`) será modificado.
- Ningún instalador (`installers/`, `dist/`, `build/`) será tocado.
