# WORKER VISUAL QA FLOW — nm_suite

> **Doc operacional para cerrar una exact key.**
> Si seguís esto no necesitás leer `VISUAL_QA_AGENT_PROTOCOL.md`
> ni `VISUAL_REPAIR_HANDOFF.md` completos para **intentar** una key.
> El gate fuerte (`close_visual_key.py`, replay, anti-fraud, R0) queda reservado
> para el **cierre oficial**, no para cada intento de reparación.
>
> **Mantenimiento**: este doc puede quedar stale. Antes de cada uso verificá
> que las rutas y los flags coincidan con el repo actual. Si el handoff tiene
> sección `## NEXT_KEY`, esa es la fuente de verdad para la key activa —
> ignorá cualquier key hardcodeada que veas abajo como ejemplo.

---

## 0. Cómo elegir la key a trabajar

La key activa es el **primer `- [ ]`** de `VISUAL_REPAIR_HANDOFF.md`.

**Fuente de verdad preferida**: si el handoff tiene una sección `## NEXT_KEY`
al inicio (agregada por `nm_suite_optimization.patch`), leé de ahí.
Si no existe esa sección, hacé `grep -n "^- \[ \]" VISUAL_REPAIR_HANDOFF.md | head -1`
y tomá la primera línea.

> No uses "Repair Order" del handoff como guía aunque exista: históricamente
> quedó stale (sprint pin apuntando a familia fully closed).
> No leas los `[x]` cerrados: son ruido histórico. La evidencia canónica
> vive en `docs/closure_evidence/<key_safe>.json`.

Estructura de la key: `<app>:<view>@<theme>` donde `app ∈ {suite, hub}`,
`theme ∈ {light, dark}`. Ej: `suite:dbt-library@light` → app=suite, view=dbt-library, theme=light.
(**Este es un ejemplo**, no es la key activa actual — leé NEXT_KEY.)

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

Cada iteración cuesta **~15-45 s** (1 captura + 1 compare filtrado por key).
No corras `--all`, no corras full-suite, no corras replay.

### 2.1 Editá el código del producto (app/ hub/ shared/)

Hacé el cambio más directo y necesario para cerrar la divergencia. No agregues
refactor lateral ni cambios cosméticos adyacentes — cuanto más chico el diff,
más fácil de auditar y menos riesgo de regresión en otra key.
No toques **ningún** archivo de la lista R0 (sección 5 abajo) en el mismo PR.

### 2.2 Validá con UN comando (Windows / PowerShell)

Reemplazá `<app>`, `<view>`, `<theme>`, `<key>` con los valores de tu key
(leídos de NEXT_KEY):

```powershell
.\qa\run_visual_item.ps1 `
  -App <app> `
  -View <view> `
  -Theme <theme> `
  -Key <key> `
  -OutDir reports\qa\layered_visual_compare_item
```

Esto ejecuta en secuencia, abortando en el primer fallo:
1. `anti_fraud_scan.py` (modo full — bloquea si hay canonical injection)
2. `capture_v8.py --app <app> --view <view> --theme <theme> --out-dir qa\_captures_v8 --no-clean` con `NM_VAS_INTROSPECT=1`
3. `layered_visual_compare.py --canonical qa\_mockup_canonical --actual qa\_captures_v8 --out-dir reports\qa\layered_visual_compare_item --key <key>`
4. **Si la key es modal**: `audit_modal_backdrop_blur.py --key <key>`
5. `vas_gate.py --key <key>`

### 2.3 Criterio de PASS del pre-flight

Abrí `reports\qa\layered_visual_compare_item\LAYERED_VISUAL_REPORT.json` y verificá:
- `REPORT_EVIDENCE_VALID: YES`
- `exact key status: PASS` (la línea de tu key)
- `suspicious_perfect_match: false`
- `near_perfect_match: false`

Y en `qa\_visual_auditor_spec\introspection.json` para tu key:
- `fail_count: 0`
- cero `divergences` con `severity ∈ {high, medium}`

> **`HANDOFF_CLOSURE_ALLOWED: NO` es normal** para un pre-flight de 1 key
> (motivo: `partial_scope`). NO bloquea el cierre individual.

### 2.4 Cuándo parar de iterar

Regla dual según señal métrica:

- **Si 3 iteraciones consecutivas no mueven el `changed_pixel_ratio`**
  (no hay mejora objetiva iteración a iteración): **pará a las 3**. No hay
  convergencia visible; seguir iterando sin input es tirar tokens.

- **Si cada iteración mejora objetivamente el `changed_pixel_ratio`**
  (aunque sea por 0.001): podés iterar **hasta 7**. Si a las 7 seguís sin
  PASS, pará.

- **Tope duro absoluto: 10 iteraciones**. Aunque la métrica siga bajando,
  después de 10 pará y reportá. El riesgo de falso PASS por desesperación
  (el agente "afina" thresholds en vez de arreglar el problema) crece
  exponencialmente después de 7-10 ciclos.

Cuando pares, posteá en el canal:
- Key exacta
- Número de iteraciones hechas y por qué paraste (sin mejora / alcanzó 7 / tope 10)
- Cambios intentados (commit hashes si los hay, o diff summary por iteración)
- `changed_pixel_ratio`, `mean_abs_diff`, `windowed_ssim` de cada una de las
  últimas 3 iteraciones (para que se vea la tendencia)
- Hipótesis sobre MISMATCH# relevante (¿es IRREDUCIBLE?)
- ¿Cuál fue la iteración que más se acercó al PASS y qué cambió?

---

## 3. Cierre oficial (1 comando, ~30-90 s)

**Sólo cuando el pre-flight da PASS.** No antes.

```powershell
.\.venv\Scripts\python.exe qa\close_visual_key.py --key <key>
```

(Opcional, recomendado para iteraciones baratas: agregar `--preflight` corre
el pipeline en working tree antes de armar el worktree, ahorrando ~30-60 s
si el código sigue roto. La evidencia siempre se construye dentro del worktree;
`--preflight` es sólo un guard de early-exit, no afecta al gate.)

Esto hace, atómicamente, en un **worktree separado** al commit HEAD:
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

> **No edites el handoff ni los records de evidencia por fuera de `close_visual_key.py`.**
> Cualquier mutación fuera de ese script rompe el hash y
> `replay_visual_closure.py` lo detecta como `evidence_hash_mismatch`.

---

## 4. Post-cierre

El post-cierre tiene **2 etapas separadas**: cierre local (vos) y publicación
(owner). No las mezcles.

### 4a. Cierre local (vos)

Después de que `close_visual_key.py` escribió el record + mutó el handoff:

```powershell
git add -A
git status
```

Verificá que el staged diff muestra:
- 1 archivo modificado: `VISUAL_REPAIR_HANDOFF.md` (checkbox flip + 3 notas)
- 1 archivo nuevo: `docs/closure_evidence/<key_safe>.json`

Si hay más archivos staged (capturas temporales, logs, cambios en `app/` que
no commiteaste antes del cierre), deshacelos con `git restore --staged <file>`.
El commit de cierre debe ser limpio: handoff + evidence record, nada más.

```powershell
git commit -m "close: <key>"
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
- 1 commit local con `close: <key>`
- Replay `--regen` PASS

Reportá al owner:
```
Key: <key>
Commit: <hash>
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
qa/anti_fraud_scan.py
qa/close_visual_key.py
qa/replay_visual_closure.py
.github/workflows/visual-closure-replay.yml
qa/_mockup_canonical/                  (dir, recursivo)
qa/pack canonico/                       (dir, recursivo)
```

**Propuesto agregar (gap detectado en auditoría, en `nm_suite_optimization.patch`):**
```
qa/vas_engine.py
qa/vas_introspect.py
qa/specs/specs.json
qa/spec_generator.py
```
Sin estos en R0, un agente puede debilitar los contratos VAS y cerrar una key
en el mismo PR sin disparar el gate. Si el patch NO está aplicado, asumí que
este gap sigue abierto y evitá tocar esos 4 archivos en el mismo rango que un
cierre (auto-restricción defensiva).

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
- Cerrar una key sin que `close_visual_key.py` haya escrito el record.

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

---

## 8. Lo que NO tenés que hacer

- ❌ Leer `VISUAL_REPAIR_HANDOFF.md` completo (1120 líneas) para 1 key.
- ❌ Correr `capture_v8.py --all --clean` (prohibido por PROTOCOL L217, contradice L96-100).
- ❌ Correr `run_visual_full.ps1` (es para regresión final transversal, no microfix).
- ❌ Correr `audit_mockup_parity_baseline.py` (sólo si cambiaste canonical HTML/recipe/PNGs).
- ❌ Correr `replay_visual_closure.py` antes de cerrar (es post-cierre).
- ❌ Correr los 5 `audit_*.py` por separado (ya están integrados en `run_visual_item.ps1` y `close_visual_key.py`).
- ❌ Editar `docs/closure_evidence/*.json` por fuera de `close_visual_key.py`.
- ❌ Editar el handoff por fuera de `close_visual_key.py`.
- ❌ Tocar kernel R0 en el mismo PR que un cierre.
- ❌ Cerrar más de 1 key por commit (secuencial, 1 commit → verificar → commit → verificar).
- ❌ Saltar de familia sin cerrar o bloquear la current.
- ❌ Decidir el `git push` vos — el owner decide.

---

## 9. Resumen del flujo (recordatorio de 1 pantalla)

```
[Elegir key] → leer NEXT_KEY del handoff (o primer `- [ ]`)
   ↓
[Pre-flight mapping] → graphify + matriz + mismatches (≤2 min)
   ↓
[Ciclo de reparación] → editar app/ + run_visual_item.ps1 (15-45 s)
   ↓           ↑
   ↓     PASS?  ↑
   ↓           ↑ NO
   ↓           └── (3 sin mejora / 7 con mejora / tope 10 → parar y reportar)
   ↓ SÍ
[close_visual_key.py [--preflight] --key <key>]  (30-90 s, worktree aislado)
   ↓
─── ETAPA 4a: CIERRE LOCAL ───
[git add + git commit -m "close: <key>"]  (1 commit, handoff + evidence JSON)
   ↓
─── ETAPA 4b: VERIFICACIÓN LOCAL ───
[replay_visual_closure.py --base <base-real>]  (5-15 min, --regen)
   ↓ PASS
─── ETAPA 4c: PUBLICACIÓN (owner decide) ───
[reportar al owner: key + commit + replay PASS]
   ↓ owner autoriza
[git push origin main]
   ↓
[CI corre --no-regen automáticamente]  (1-2 min)
   ↓
[Fin]
```

**Costo total por key exitosa**: ~10-30 min wall-clock + ~250 líneas de doc leídas.
**Costo por intento fallido (pre-flight sin cerrar)**: ~1-5 min (1-7 ciclos pre-flight).
**Costo de replay local `--regen`**: ~5-15 min por cada key cerrada en el rango auditado.
