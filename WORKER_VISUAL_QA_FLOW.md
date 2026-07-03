# WORKER VISUAL QA FLOW — nm_suite

> **Doc operacional para trabajar un target set de keys, declarado por el
> owner. Entry-point canónico** (ver `docs/README.md`).
> El scope por defecto es **el que declare el owner** (ver §0
> `OWNER_TARGET_MODE`) — no es "1 key" fijo. El agente no achica ese scope
> por costo/cansancio/riesgo percibido, ni lo amplía por cuenta propia.
> Si seguís esto no necesitás leer el protocolo completo archivado
> (`docs/_archive/protocol_v1.md`) ni `VISUAL_REPAIR_HANDOFF.md` completo
> para **intentar** el target set declarado.
> El gate fuerte (`close_visual_key.py`, replay, anti-fraud, R0) queda reservado
> para el **cierre oficial de cada key**, no para cada intento de reparación.
>
> **Mantenimiento**: este doc puede quedar stale. Antes de cada uso verificá
> que las rutas y los flags coincidan con el repo actual. Si el handoff tiene
> sección `## NEXT_KEY`, esa es la fuente de verdad para la key `next-key` —
> ignorá cualquier key hardcodeada que veas abajo como ejemplo.

---

## 0. Cómo resolver el target set a trabajar

El **owner declara el scope en su prompt** — el agente lo resuelve
mecánicamente, no lo re-interpreta ni lo negocia.

### OWNER_TARGET_MODE

| Modo | Selección | Disparador ejemplo |
|---|---|---|
| `next-key` | `## NEXT_KEY` (1 key) | "ejecutá ese flujo para `## NEXT_KEY`" |
| `first-N` | primeras N keys abiertas, orden del handoff | "las primeras X keys abiertas del orden del handoff" |
| `batch` | misma selección que `first-N`; difiere sólo en granularidad de commit (§4a) | "en modo batch para las primeras X keys" |
| `family` | `## NEXT_KEY` (u otra seed) + keys de la misma sección `###` | "`## NEXT_KEY` y su familia equivalente" |
| `all-open-keys` | todas las keys abiertas actuales | "para todas las keys abiertas" |
| `explicit-list` | exactamente la lista dada | "para esta lista explícita: <keys>" |

**Reglas del contrato:**
- El prompt del owner es la autoridad del scope. Si declara 1 key, trabajás 1
  key; si declara batch/family/all-open-keys, trabajás ese conjunto en una
  corrida.
- El agente **no achica** el scope por costo, cansancio, límite interno o
  "riesgo" percibido, ni **lo amplía** por cuenta propia — la única excepción
  es evidencia objetiva de que una key declarada no existe, está duplicada,
  o ya no está abierta (reportá esa desviación explícitamente, no la
  silencies).
- Reportá el target set resuelto al inicio de tu respuesta. No pidas
  confirmación si el owner ya declaró el scope — eso ya es autoridad
  suficiente.

**Resolución mecánica** (no derives la lista a mano):

```powershell
.\.venv\Scripts\python.exe qa\target_scope.py --mode <modo> [--n N] [--seed-key <key>] [--keys "k1,k2,..."]
```

Lee `VISUAL_REPAIR_HANDOFF.md` en vivo (nunca una copia stale) e imprime la
lista exacta de keys en el orden correcto. Agregá `--plan` para obtener filas
`app,view,theme,key` listas para `qa\run_visual_family.ps1 -PlanFile` (§2.2).

> No uses "Repair Order" del handoff como guía aunque exista: históricamente
> quedó stale (sprint pin apuntando a familia fully closed).
> No leas los `[x]` cerrados: son ruido histórico. La evidencia canónica
> vive en `docs/closure_evidence/<key_safe>.json`.
> Para una vista humana rápida del scope disponible, ver
> `VISUAL_REPAIR_HANDOFF.md` § "OPEN KEYS — family/complexity order".

Estructura de la key: `<app>:<view>@<theme>` donde `app ∈ {suite, hub}`,
`theme ∈ {light, dark}`. Ej: `suite:dbt-library@light` → app=suite, view=dbt-library, theme=light.
(**Este es un ejemplo**, no necesariamente la key `next-key` actual — resolvé
con `target_scope.py` o leé `## NEXT_KEY`.)

---

## 1. Pre-flight (1 comando, ~30 s)

Antes de tocar código, mapeá la divergencia al design system:

```powershell
# Opcional pero recomendado: grafo de dependencias si vas a tocar shared/
graphify . --update

# Consulta rápida (no hace falta leer completos):
# - docs/CSS_TO_PYQT_EQUIVALENCE_MATRIX.md  (familia dominante de tu key)
# - docs/QT_HTML_KNOWN_MISMATCHES.md        (¿es MISMATCH#N conocido? ¿IRREDUCIBLE?)
# - docs/VISUAL_COMPONENT_CATALOG.md        (familia F{n} de tu key)
```

Si la divergencia corresponde a un **MISMATCH IRREDUCIBLE** (ver
`QT_HTML_KNOWN_MISMATCHES.md` secciones marcadas como irreducibles, ej.
text-AA en surfaces densas), **pará y reportá** — no hay ciclo de reparación
que converja. Posteá el MISMATCH# y la key en el canal de handoff.

---

## 2. Reparación visual por ciclos cortos

Cada iteración de **una key** cuesta ~15-45 s (1 captura + 1 compare filtrado
por key). Si tu target set tiene más de 1 key, iterás key por key dentro del
set — no saltás fuera del set declarado por el owner, y no lo abandonás por
costo. No corras full-suite ni replay durante reparación (eso es post-cierre,
§4).

### 2.1 Editá el código del producto (app/ hub/ shared/)

Hacé el cambio más directo y necesario para cerrar la divergencia de la key
que estás trabajando. No agregues refactor lateral ni cambios cosméticos
adyacentes — cuanto más chico el diff, más fácil de auditar y menos riesgo de
regresión en otra key. Si el target mode es `family`/`batch`/`all-open-keys`
y varias keys del set comparten causa raíz en un componente compartido, un
fix compartido es válido (el contrato lo permite) — pero **medí el impacto
en cada key del set por separado**: un fix compartido puede mejorar una key
y no otra, o incluso regresionar una tercera fuera del set (correlo contra
neighbors si tocás `shared/`).
No toques **ningún** archivo de la lista R0 (sección 5 abajo) en el mismo PR.

### 2.2 Validá

**1 key** (Windows / PowerShell):

```powershell
.\qa\run_visual_item.ps1 `
  -App <app> `
  -View <view> `
  -Theme <theme> `
  -Key <key> `
  -OutDir reports\qa\layered_visual_compare_item
```

**N keys del target set** (`first-N`/`batch`/`family`/`all-open-keys`/
`explicit-list` con más de 1 key) — generá el plan con `target_scope.py
--plan` (§0) y corré `run_visual_family.ps1`:

```powershell
.\.venv\Scripts\python.exe qa\target_scope.py --mode <modo> [--n N] --plan `
  > reports\qa\visual_family_keys_plan.csv
.\qa\run_visual_family.ps1 `
  -PlanFile reports\qa\visual_family_keys_plan.csv `
  -OutDir reports\qa\layered_visual_compare_family
```

`run_visual_family.ps1` ya existe y ya es multi-key: corre anti-fraude,
captura cada key (con manejo de modal/back-screen), UN compare batcheado
(`--keys-file`), audit modal para las keys modales, y VAS gate — todo en una
corrida. No corras `capture_v8.py --all --clean` / `run_visual_full.ps1`
salvo target mode `all-open-keys` con un cambio verdaderamente transversal
(theme/chrome/`NMCard`/shell); para `all-open-keys` sin cambio transversal,
seguí usando `run_visual_family.ps1` con el plan de las 56 keys.

Ambos caminos ejecutan en secuencia, abortando en el primer fallo:
1. `anti_fraud_scan.py` (modo full — bloquea si hay canonical injection)
2. `capture_v8.py` por key (`NM_VAS_INTROSPECT=1`)
3. `layered_visual_compare.py` (filtrado por `--key` o por `--keys-file`)
4. Para cada key modal del set: `audit_modal_backdrop_blur.py --key <key>`
5. `vas_gate.py`

### 2.3 Criterio de PASS del pre-flight

Por cada key del target set, abrí el reporte correspondiente
(`reports\qa\layered_visual_compare_item\LAYERED_VISUAL_REPORT.json` para 1
key, o `reports\qa\layered_visual_compare_family\LAYERED_VISUAL_REPORT.json`
para N keys) y verificá, para ESA key:
- `REPORT_EVIDENCE_VALID: YES`
- `exact key status: PASS`
- `suspicious_perfect_match: false`
- `near_perfect_match: false`

Y en `qa\_visual_auditor_spec\introspection.json` para esa key:
- `fail_count: 0`
- cero `divergences` con `severity ∈ {high, medium}`

> **`HANDOFF_CLOSURE_ALLOWED: NO` es normal** para un pre-flight de scope
> parcial (motivo: `partial_scope`), incluso si tu target mode es
> `all-open-keys` (el reporte cubre las keys abiertas, no las 116 del canon
> completo). NO bloquea el cierre individual de cada key que sí está `PASS`.

### 2.4 Cuándo parar de iterar

Esta regla aplica **por key**: si una key del target set no converge, aplicá
lo de abajo para ESA key sin abandonar el resto del set declarado por el
owner.

Si 3 iteraciones consecutivas no mejoran las métricas de una key, no sigas
con ajustes locales del mismo tipo.

En ese punto:

1. preservá el mejor diff si corrige un bug real;
2. identificá la causa dominante restante. Mirá, en este orden, en
   `LAYERED_VISUAL_REPORT.json`:
   - `metrics.largest_region_ratio`: si > 0.04, hay una región concentrada
     (estructural).
   - `layout.bbox_dy` / `layout.bbox_dh`: si `|bbox_dy| > 8` o `|bbox_dh| > 8`,
     hay desplazamiento vertical (estructural).
   - los primeros 4 `regions[]`: su `hint` indica qué bloque diverge
     (`component_region`/`layout_shift_or_spacing` = reparable;
     `text_icon_or_antialiasing` = candidato a IRREDUCIBLE si se repite
     sin cambiar tras un fix real).
3. cambiá de estrategia sólo si la causa está localizada;
4. si la causa toca componente compartido, evaluá opción scoped primero;
5. si no hay ruta técnica clara, reportá bloqueo con métricas y diffs.

La regla frena loops ciegos; no autoriza abandonar una key con causa
reparable identificada.

---

## 3. Cierre oficial (~30-90 s por key)

**Sólo cuando el pre-flight da PASS para esa key.** No antes.

El cierre es **siempre por key** — `close_visual_key.py` no tiene modo
multi-key, y eso es intencional (cada cierre es atómico en su propio
worktree aislado). Para un target set de N keys, invocalo una vez por key
que alcanzó PASS:

```powershell
.\.venv\Scripts\python.exe qa\close_visual_key.py --key <key>
```

(Opcional, recomendado para iteraciones baratas: agregar `--preflight` corre
el pipeline en working tree antes de armar el worktree, ahorrando ~30-60 s
si el código sigue roto. La evidencia siempre se construye dentro del worktree;
`--preflight` es sólo un guard de early-exit, no afecta al gate.)

Cada invocación hace, atómicamente, en un **worktree separado** al commit HEAD:
1. Verifica working tree limpio en rutas scoped (app, hub, shared, qa, tools/qa, handoff, .github/workflows).
2. Verifica la key está abierta en el handoff.
3. Crea `git worktree add --detach <tmp> <HEAD>` (aislamiento anti-tamper).
4. Re-ejecuta **todo** el pipeline (anti-fraud + capture + compare + VAS) sobre el worktree.
5. Construye `docs/closure_evidence/<key_safe>.json` con schema `nm_suite.evidence_record.v1`:
   - `commit_head`, `anti_fraud_sha256`, `capture_v8_sha256`, `layered_compare_sha256`, `vas_gate_sha256`
   - `capture_png_sha256`, `manifest_sha256`, `report_sha256`, `sidecar_sha256`
   - `result: PASS`, `metrics{changed_pixel_ratio, mean_abs_diff, windowed_ssim, max_bbox_delta_px}`
   - `record_sha256` = hash canónico del propio record (sin campos volátiles)
6. Marca el checkbox `[ ]` → `[x]` en el handoff y agrega 3 notas:
   - `evidence: <record_sha256>`
   - `evidence-record: docs/closure_evidence/<key_safe>.json`
   - `commit: <HEAD>`
7. Escribe atómicamente (rename) para evitar corrupt-write.

Si tu target set tiene N keys en PASS, repetí la invocación N veces
(secuencial — el working tree debe estar limpio antes de cada una, así que
si vas a commitear en batch, esperá a haber cerrado todas antes del commit;
ver §4a). Cada invocación construye su **propio** `docs/closure_evidence/
<key>.json` y agrega sus **propias** notas al checkbox de esa key
exclusivamente. No hay cierre sin evidence propio — para ninguna key, sea
cual sea el target mode.

> **No edites el handoff ni los records de evidencia por fuera de `close_visual_key.py`.**
> Cualquier mutación fuera de ese script rompe el hash y
> `replay_visual_closure.py` lo detecta como `evidence_hash_mismatch`.

---

## 4. Post-cierre

El post-cierre tiene **2 etapas separadas**: cierre local (vos) y publicación
(owner). No las mezcles.

### 4a. Cierre local (vos)

Después de correr `close_visual_key.py` para cada key del target set que
llegó a PASS:

```powershell
git add -A
git status
```

**Granularidad de commit según target mode** (el owner ya la definió al
declarar el modo, no la elegís vos):
- `next-key` / `first-N` / `explicit-list`: default 1 commit por key cerrada
  (secuencial — cerrar key → verificar diff → commit → repetir con la
  siguiente).
- `batch` / `all-open-keys` / `family`: el owner autorizó agrupar — cerrá
  todas las keys del set que llegaron a PASS primero, y recién ahí hacé **1
  commit que bundlea las N closures**. El evidence sigue siendo por key (N
  records en `docs/closure_evidence/`, N sets de notas en el handoff) — sólo
  el commit se agrupa.

Verificá que el staged diff muestra ÚNICAMENTE:
- `VISUAL_REPAIR_HANDOFF.md` (1 checkbox flip + 3 notas por cada key cerrada)
- 1 archivo nuevo por key en `docs/closure_evidence/<key_safe>.json`

Si hay más archivos staged (capturas temporales, logs, cambios en `app/` que
no commiteaste antes del cierre), deshacelos con `git restore --staged <file>`.
El commit de cierre debe ser limpio: handoff + evidence record(s), nada más.

```powershell
git commit -m "close: <key>"                              # 1 key
git commit -m "close: batch <N> keys — <family/modo>"      # batch/all-open-keys/family
```

### 4b. Verificación local pre-push (vos)

Antes de pensar en publicar, corré el replay local con `--regen`. La máquina
que cierra es la **única** que verifica pixeles:

```powershell
.\.venv\Scripts\python.exe qa\replay_visual_closure.py --base <base-real>
```

**Cómo resolver `<base-real>`**: el replay audita el rango `base..HEAD`. Tenés
que elegir `base` como el último commit **anterior** a tus cierres. Opciones:

- Si tu local está al día con `origin/main` y sólo agregaste commits de cierre:
  ```powershell
  git rev-parse origin/main
  # usá ese hash como --base
  .\.venv\Scripts\python.exe qa\replay_visual_closure.py --base <hash-de-origin/main>
  ```

- Si tu local está atrasado respecto a `origin/main` (alguien más pusheó):
  pará. Hacé `git fetch origin` y `git rebase origin/main` ANTES del replay,
  porque sino el rango auditado no incluye tus cierres o incluye commits de
  otros que vas a falsamente flaguear.

- Si tu local está adelantado a `origin/main` con varios commits de cierre:
  ```powershell
  # base = commit inmediatamente anterior al primer cierre
  git log --oneline -20
  # identificá el primer commit "close: <key>" y usá su padre:
  git rev-parse <primer-close>^
  ```

- **Atajo simple**: si tenés un solo commit de cierre encima de `origin/main`:
  ```powershell
  .\.venv\Scripts\python.exe qa\replay_visual_closure.py --base HEAD~1
  ```

El replay re-captura + re-compara + re-VAS cada key cerrada en el rango y
compara el hash. **Si una sola key no reproduce el hash, todo falla** —
es el gate fuerte. Si falla, NO intentes arreglar el hash; reportá el
stderr completo.

### 4c. Publicación (decisión del owner)

**Vos no decidís el push.** El owner decide cuándo y cómo publicar.

Después de que 4a + 4b pasan, el estado es:
- 1 o más commits locales de cierre (1 por key, o 1 batch — según §4a)
- Replay `--regen` PASS para el rango completo

Reportá al owner:
```
Target set: <modo declarado> — <N> keys
Keys cerradas: <key1>, <key2>, ...
Commit(s): <hash1> [, <hash2>, ...]
Replay base: <base-real>
Replay: PASS
Ready to push: awaiting owner decision
```

Si el owner autoriza el push:
```powershell
git push origin main
```

CI (`.github/workflows/visual-closure-replay.yml`) corre automáticamente
después del push con `--no-regen` (estructural): valida hashes, paths, R0,
schema — pero no re-renderiza pixeles. Es la verificación barata de integridad.
Si CI falla, NO intentes fixear — reportá el log al owner.

---

## 5. R0 — Kernel inmutable (NO tocar en mismo PR que cierre)

Estos archivos **no pueden modificarse** en el mismo rango auditado que un
cierre. Si los tocás, todas las keys cerradas en ese rango fallan con
`kernel_changed_with_visual_closure`. Hacé el cambio del kernel en un PR
separado, mergealo, y después cerrá keys.

```
qa/capture_v8.py
qa/layered_visual_compare.py
qa/vas_gate.py
qa/vas_engine.py
qa/vas_introspect.py
qa/anti_fraud_scan.py
qa/close_visual_key.py
qa/replay_visual_closure.py
qa/spec_generator.py
qa/specs/specs.json
.github/workflows/visual-closure-replay.yml
qa/_mockup_canonical/                  (dir, recursivo)
qa/pack canonico/                       (dir, recursivo)
```

Lista sincronizada con `R0_KERNEL_PATHS` en `qa/replay_visual_closure.py` (fuente
de verdad en código). `vas_engine.py`, `vas_introspect.py`, `spec_generator.py`
y `specs/specs.json` ya están en vigor ahí — sin ellos un agente podría debilitar
los contratos VAS y cerrar una key en el mismo PR sin disparar el gate.

---

## 6. Reglas de cierre prohibidas (lo que NO cuenta como PASS)

Estos criterios **no son evidencia de cierre** y nunca deben invocarse:

- **Frases subjetivas de aceptación visual o aprobación no reproducible** no son medibles,
  no son reproducibles, no cuentan.
- **Frases de progreso parcial** ("mayormente arreglado", "residuo aceptable",
  "avance parcial", "cosmético", "menor") — un fix parcial no es un cierre.
- **Frases de abandono** ("bloqueado", "demasiado difícil", "no se puede arreglar",
  "downgrade") — si no se puede cerrar, reportá el bloqueo; no lo enmascares como cierre.
- `diff_fidelity.py PASS` (es LEGACY, no cierra)
- `capture_v8.py` exit 0 solito (no es PASS)
- "fidelity PASS" sin `REPORT_EVIDENCE_VALID: YES`
- zip-based / desktop zip evidence
- `REPORT_EVIDENCE_VALID: NO`

Tampoco podés:
- Modificar QA scripts, comparators, thresholds, capture scripts, canonical
  images o fixtures para hacer pasar una divergencia.
- Hacer que código del producto lea/renderice/monte/copie/blit/overlay
  cualquier artefacto canonical/reference/mockup.
- Deshabilitar odiff o panels para cerrar.
- Cerrar una key sin que `close_visual_key.py` haya escrito el record propio
  de esa key — sin importar el target mode (batch/all-open-keys incluidos).
- **Achicar el target set** que declaró el owner por costo, cansancio, límite
  interno o "riesgo" percibido. Si una key del set bloquea, reportala
  bloqueada (§2.4) y seguí con el resto del set — no la saltees en silencio
  y no abandones el set completo por ella.
- **Ampliar el target set** más allá de lo declarado por el owner, salvo
  evidencia objetiva de que una key no existe, está duplicada, o ya no está
  abierta (reportá la desviación, no la apliques en silencio).
- Invocar antialiasing/text-rendering (MISMATCH#20 o similar) como excusa de
  bloqueo sin evidencia real de `regions[]` / `largest_region_ratio` /
  `bbox_dy` que lo respalde — seguí el procedimiento mecánico de §2.4 antes
  de declarar una divergencia "irreducible".

---

## 7. Cierre bloqueado — cuándo parar

Si `close_visual_key.py` falla, NO intentes reproducir el PASS por fuera del script.
El script falla ruidosamente con uno de estos códigos:

| exit | motivo | acción |
|------|-------|--------|
| 2 | `dirty_working_tree` | commiteá o descartá cambios en scoped paths |
| 2 | `unknown_key` / `key_already_closed` | verificá la key en el handoff |
| 2 | `open_key_not_found` | la key no está abierta en el handoff |
| 1 | `anti_fraud_failed` | tu código tiene canonical injection — leé `anti_fraud_scan.py` output |
| 1 | `capture_failed` | Qt/app error — mirá `capture_v8.py` stderr |
| 1 | `comparator_failed` / `comparator_not_pass` | la key no está en PASS — volvé a sección 2 |
| 1 | `missing_metric_*` | el reporte del comparator está mal formado — posiblemente kernel dañado |
| 1 | `vas_failed` | VAS gate falló — mirá `vas_gate.py` output |
| 1 | `preflight failed: ...` (con `--preflight`) | el guard de early-exit detectó fallo antes del worktree — volvé a sección 2 |

Cualquier otro error → pará, reportá el stderr completo en el canal de handoff.

**Con target set de N keys**: si `close_visual_key.py` falla para UNA key del
set, no aborta el set completo — reportá esa key bloqueada con su motivo,
seguí cerrando el resto de las keys del set que sí están en PASS. Excepción:
`dirty_working_tree` sí bloquea todo el set hasta que resolvés el working
tree, porque ninguna invocación posterior puede correr sobre un tree sucio.

---

## 8. Lo que NO tenés que hacer

- ❌ Leer `VISUAL_REPAIR_HANDOFF.md` completo (1120 líneas) para trabajar el
  target set declarado — usá `qa\target_scope.py` + `## OPEN KEYS —
  family/complexity order` (vista compacta en el handoff).
- ❌ Correr `capture_v8.py --all --clean` salvo target mode `all-open-keys`
  con un cambio verdaderamente transversal (theme/chrome/`NMCard`/shell).
- ❌ Correr `run_visual_full.ps1` fuera de ese mismo caso o de una regresión
  final oficial.
- ❌ Correr `audit_mockup_parity_baseline.py` (sólo si cambiaste canonical HTML/recipe/PNGs).
- ❌ Correr `replay_visual_closure.py` antes de cerrar (es post-cierre).
- ❌ Correr los 5 `audit_*.py` por separado (ya están integrados en
  `run_visual_item.ps1` / `run_visual_family.ps1` y `close_visual_key.py`).
- ❌ Editar `docs/closure_evidence/*.json` por fuera de `close_visual_key.py`.
- ❌ Editar el handoff por fuera de `close_visual_key.py`.
- ❌ Tocar kernel R0 en el mismo PR que un cierre.
- ❌ Cerrar una key sin su propio evidence record — sin importar si el
  commit es individual o batch (§3, §4a).
- ❌ Achicar o ampliar el target set que declaró el owner sin evidencia
  objetiva de key inexistente/duplicada/ya cerrada (§6).
- ❌ Decidir el `git push` vos — el owner decide.

---

## 9. Resumen del flujo (recordatorio de 1 pantalla)

```
[Resolver target set] → owner declara modo → target_scope.py --mode <modo> [...]
   ↓
[Pre-flight mapping] → graphify + matriz + mismatches (≤2 min, por key nueva)
   ↓
[Ciclo de reparación] → editar app/ + run_visual_item.ps1 (1 key) o
                         run_visual_family.ps1 -PlanFile (N keys) — 15-45 s/key
   ↓           ↑
   ↓  PASS? (por key) ↑
   ↓           ↑ NO
   ↓           └── (3 sin mejora → preservar diff real, localizar causa,
   ↓               scoped antes que shared, o reportar bloqueo — §2.4)
   ↓ SÍ (repetir para cada key del target set)
[close_visual_key.py [--preflight] --key <key>]  (30-90 s/key, worktree aislado)
   ↓
─── ETAPA 4a: CIERRE LOCAL ───
[git add + commit]  (1 commit/key, o 1 commit batch si el modo lo autoriza — §4a)
   ↓
─── ETAPA 4b: VERIFICACIÓN LOCAL ───
[replay_visual_closure.py --base <base-real>]  (valida TODO el rango cerrado, --regen)
   ↓ PASS
─── ETAPA 4c: PUBLICACIÓN (owner decide) ───
[reportar al owner: target set + keys cerradas + commit(s) + replay PASS]
   ↓ owner autoriza
[git push origin main]
   ↓
[CI corre --no-regen automáticamente]  (1-2 min)
   ↓
[Fin]
```

**Costo total por key exitosa**: ~10-30 min wall-clock + tiempo de doc proporcional al target set (no todo el handoff).
**Costo por intento fallido (pre-flight sin cerrar)**: ~1-5 min (1-7 ciclos pre-flight) por key.
**Costo de replay local `--regen`**: ~5-15 min por corrida, cubre todas las keys cerradas en el rango auditado (no escala 1:1 con N si se hizo en batch).
