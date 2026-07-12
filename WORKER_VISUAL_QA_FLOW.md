# WORKER VISUAL QA FLOW — nm_suite

> **Doc operacional para trabajar un target set de keys, declarado por el
> owner. Entry-point canónico** (ver `docs/README.md`).
> El scope por defecto es **el que declare el owner** (ver §0
> `OWNER_TARGET_MODE`) — no es "1 key" fijo. El agente no achica ese scope
> por costo/cansancio/riesgo percibido, ni lo amplía por cuenta propia.
> Si seguís esto no necesitás leer `VISUAL_REPAIR_HANDOFF.md` completo para
> **intentar** el target set declarado. El handoff es una vista generada: no
> se edita nunca. La única autoridad de cierre es un record v2 validable en
> `docs/closure_evidence/active/`.
>
> El gate fuerte (`close_visual_key.py`, replay, anti-fraud, R0) queda
> reservado para el **cierre oficial de cada key**, no para cada intento de
> reparación. Los comandos de este documento corresponden al schema v2.

---

## 0. Cómo resolver el target set a trabajar

El **owner declara el scope en su prompt** — el agente lo resuelve
mecánicamente, no lo re-interpreta ni lo negocia.

### OWNER_TARGET_MODE

| Modo | Selección | Disparador ejemplo |
|---|---|---|
| `next-key` | primera key abierta de la vista generada | "ejecutá el flujo para la próxima key" |
| `first-n` | primeras N keys abiertas, orden del handoff | "las primeras X keys abiertas del orden del handoff" |
| `batch` | misma selección que `first-n`; difiere sólo en granularidad de trabajo | "en modo batch para las primeras X keys" |
| `family` | primera key abierta (u otra seed) + keys abiertas de su sección `###` | "la próxima key y su familia equivalente" |
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
  suficiente. El owner puede cambiar el scope sólo con un prompt nuevo y
  explícito; el worker no debe pedir permiso para saltear, aceptar o achicar
  keys dentro del scope ya declarado.

**Resolución mecánica** (no derives la lista a mano):

```powershell
.\.venv\Scripts\python.exe qa\target_scope.py --mode <modo> [--n N] [--seed-key <key>] [--keys "k1,k2,..."]
```

Lee `VISUAL_REPAIR_HANDOFF.md` en vivo (nunca una copia stale) e imprime la
lista exacta de keys en el orden correcto. Agregá `--plan` para obtener filas
`app,view,theme,key` listas para `qa\run_visual.ps1 -PlanFile` (§2.2).

> No derives la lista a mano ni edites checkboxes. Los `[x]` son sólo una
> proyección de `docs/closure_evidence/active/*.json`; los `[~]` provienen de
> `qa/surface_notes.json` y no pertenecen al conjunto abierto.

Estructura de la key: `<app>:<view>@<theme>` donde `app ∈ {suite, hub}`,
`theme ∈ {light, dark}`. Ej: `suite:dbt-library@light` → app=suite, view=dbt-library, theme=light.
(**Este es un ejemplo**, no necesariamente la próxima key actual: resolvé
siempre con `target_scope.py`.)

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
neighbors si tocás `shared/`). El alcance transversal o que el cambio pueda
afectar muchas keys no es bloqueo: es una señal para validar más, no para
abandonar el target set.
No toques **ningún** archivo de la lista R0 (sección 5 abajo) en el mismo PR.

### 2.2 Validá

Hay UN solo runner de validación: `qa\run_visual.ps1`, con tres modos
mutuamente excluyentes.

**1 key** (Windows / PowerShell):

```powershell
.\qa\run_visual.ps1 -Key <app>:<view>@<theme>
```

**N keys del target set** (`first-N`/`batch`/`family`/`all-open-keys`/
`explicit-list` con más de 1 key) — generá el plan con `target_scope.py
--plan` (§0):

```powershell
.\.venv\Scripts\python.exe qa\target_scope.py --mode <modo> [--n N] --plan `
  | Set-Content -Encoding ascii reports\qa\visual_keys_plan.csv
.\qa\run_visual.ps1 -PlanFile reports\qa\visual_keys_plan.csv
```

**Regresión completa** (SOLO cambio transversal real — theme/chrome/`NMCard`/
shell — o regresión final):

```powershell
.\qa\run_visual.ps1 -All
```

`-OutDir` es opcional (default `reports\qa\run_visual`; `-All` escribe en
`reports\qa\layered_visual_compare_fresh`). Para `all-open-keys` sin cambio
transversal, usá `-PlanFile` con el plan de las keys abiertas, no `-All`.

Todos los modos ejecutan en secuencia, abortando en el primer fallo:
1. `anti_fraud_scan.py --mode all` (runtime + qa-harness — bloquea si hay
   canonical injection)
2. `capture_v8.py` por key (`NM_VAS_INTROSPECT=1`, con manejo de
   modal/back-screen) + `vas_gate.py --key <key>` inmediatamente después de
   cada captura (el sidecar vivo se reescribe por invocación, así que el gate
   es POR KEY; el runner archiva cada sidecar en
   `<OutDir>\introspection\<key_safe>.json`)
3. `layered_visual_compare.py` (batcheado por `--keys-file`, o full en `-All`)
4. Para cada key modal del set: `audit_modal_backdrop_blur.py --key <key>`
   (en `-All`: `--all`)

Si un modal falla por la pantalla trasera, se repara esa pantalla/familia
dependiente; **no se tapa con blur, opacidad, alpha, crop, bbox detector ni
densidad** (regla MISMATCH#17 / back-screen-first).

### 2.3 Criterio de PASS del pre-flight

Por cada key del target set, abrí el reporte
(`<OutDir>\LAYERED_VISUAL_REPORT.json`, default
`reports\qa\run_visual\LAYERED_VISUAL_REPORT.json`) y verificá, para ESA key:
- `REPORT_EVIDENCE_VALID: YES`
- `exact key status: PASS`
- `suspicious_perfect_match: false`
- `near_perfect_match: false`

Y en el sidecar VAS de esa key:
- `fail_count: 0`
- cero `divergences` con `severity ∈ {high, medium}`

> El `qa\_visual_auditor_spec\introspection.json` vivo sólo retiene la ÚLTIMA
> key capturada. Para un set de N keys, el sidecar de cada key queda archivado
> por `run_visual.ps1` en `<OutDir>\introspection\<key_safe>.json`
> (y el gate por key ya corrió durante la captura — ver §2.2).

> **`HANDOFF_CLOSURE_ALLOWED: NO` es normal** para un pre-flight de scope
> parcial (motivo: `partial_scope`), incluso si tu target mode es
> `all-open-keys` (el reporte cubre las keys abiertas, no las 116 del canon
> completo). Esto no es cierre: el cierre oficial requiere PASS completo del
> target set salvo que el owner cambie explícitamente el scope antes del cierre.

### 2.4 Freno permitido antes de declarar bloqueo

Partial PASS is not closure. Si cualquier key del target set queda `FAIL`, el
worker debe seguir iterando reparación de producto hasta `PASS`. "Bloqueado",
"riesgo alto", "afecta muchas keys", "requiere decisión", "cercana al umbral"
o "no conviene tocar" no son estados operativos; sin el paquete mínimo de abajo
son **ABANDONO NO VÁLIDO**.

Un worker sólo puede detener una key `FAIL` si demuestra una de estas
condiciones:
1. MISMATCH activo marcado **IRREDUCIBLE** en
   `docs/QT_HTML_KNOWN_MISMATCHES.md`.
2. **DECISIÓN-OWNER** activa y explícita en una fuente vigente listada por
   `docs/README.md`.
3. Bug R0/gate/capture/comparator demostrado y reportado como tarea R0
   separada, sin cierre de keys.
4. Key inexistente, duplicada o ya cerrada.
5. Bloqueo técnico del entorno que impide ejecutar el flujo, con comando
   exacto, error completo, ruta alternativa intentada y alcance del bloqueo.
   Si sólo bloquea una operación puntual, no autoriza detener las demás keys.

Paquete mínimo antes de invocar bloqueo:
- key exacta y bucket del comparator;
- métricas antes/después, incluyendo `largest_region_ratio`, `bbox_dy`,
  `bbox_dh` y los primeros 4 `regions[]` con `hint`;
- 3 estrategias distintas probadas, o descartadas sólo por contraindicación
  técnica verificable, con evidencia objetiva, archivos tocados por hipótesis
  y por qué la siguiente ruta de producto no sirve;
- próxima hipótesis mínima si no hay bug R0.

MISMATCH#18 no es `IRREDUCIBLE`; es `WORKAROUND`. No autoriza bloqueo por sí
solo. Si aparece `bbox_dh`/`bbox_dy` alto, tratá primero como
layout/producto/estado. Comentarios de código, `docs/_archive/`, logs
históricos o "user feedback" no son `DECISIÓN-OWNER`.

Cada key conserva elegibilidad independiente. Una hermana en `FAIL` sigue
dentro del trabajo pendiente y no se saltea ni se saca del scope, pero no
bloquea el cierre de otra key que sí alcanza PASS y policy ALLOW.

Durante reparacion/cierre visual queda prohibido modificar `qa/`, `tools/qa/`,
`.github/`, `docs/closure_evidence/`, canon, thresholds, comparator, capture
harness, replay, close scripts o evidence. Si parece bug del gate, deten la
tarea visual y reporta una tarea R0 separada, sin cierre de keys, sin handoff
ni evidence.

## Canon-first precedence override

For the current Visual QA closure phase, the owner's active directive is:
canonical PNG / canonical HTML parity is the closure target.

Precedence order:

1. Current explicit owner instruction for this Visual QA phase.
2. Active canonical PNG / canonical HTML for the exact key.
3. Active Visual QA protocol and gate outputs.
4. Active bridge/reference docs, only as CSS→PyQt translation aids.
5. Historical owner decisions, old comments, archived notes, previous episode docs, and bridge-era deviations.

Historical `DECISIÓN-OWNER` entries do not block canon-first closure unless they are revalidated by the owner after this rule and explicitly marked as current active exception.

A worker must not use old `DECISIÓN-OWNER`, bridge notes, comments, episode docs, `docs/_archive`, or prior UX decisions to:
- stop a key;
- keep a visual divergence;
- request partial scope;
- avoid implementing canonical parity;
- mark a FAIL as acceptable.

If a previous owner decision conflicts with the active canonical PNG/HTML, the worker must implement canonical parity for this phase and report the prior decision as a post-closure product follow-up, not as a blocker.

Exceptions are allowed only if the owner explicitly creates a new current exception after this rule, with:
- exact key or component;
- exact visual property;
- active source file;
- reason;
- date;
- whether it blocks closure or only records post-closure product debt.

### 2.5 Cuándo cambiar de estrategia

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
5. si no hay ruta técnica clara, no declares bloqueo visual por defecto:
   cambia de estrategia, reduce el cambio a producto o arma el paquete mínimo
   de §2.4. No pidas al owner aceptar/saltear una key dentro del scope ya
   autorizado. Si no aplica una condición de §2.4, la siguiente acción es otra
   hipótesis mínima de producto; un bug de gate/R0 se reporta como tarea R0
   separada.

La regla frena loops ciegos; no autoriza abandonar una key con causa
reparable identificada.

---

## 3. Cierre oficial (~30-90 s por key)

**Sólo cuando la key candidata da PASS y pertenece al target set declarado.**
El target set limita alcance; no impone cierre all-or-nothing. Una key que
sigue `FAIL` permanece pendiente y debe seguir trabajándose, pero no bloquea
el cierre independiente de sus hermanas que sí cumplen la policy.

El cierre es **siempre por key** — `close_visual_key.py` no tiene modo
multi-key, y eso es intencional (cada cierre es atómico en su propio
worktree aislado). Para un target set de N keys, invocalo una vez por cada key
que alcance PASS, sin retirar del scope las que todavía estén pendientes:

```powershell
.\.venv\Scripts\python.exe qa\target_scope.py --mode <modo> [opciones] `
  | Set-Content -Encoding ascii reports\qa\target-set.txt
.\.venv\Scripts\python.exe qa\close_visual_key.py `
  --key <key> `
  --target-set-file reports\qa\target-set.txt
```

El archivo de target set es obligatorio en el flujo owner-directed: congela
el scope exacto que se resolvió en §0. No lo sustituyas por una lista manual ni
dependas del default de "todas las abiertas" del closer.

Cada invocación hace, atómicamente, en un **worktree separado** al commit HEAD:
1. Verifica working tree limpio en rutas scoped, incluida la evidencia activa.
2. Verifica `key ∈ target_set`, que pertenece al MANIFEST y que no está cerrada.
3. Crea un worktree detached al `HEAD` que quedará firmado como `commit_head`.
4. Corre anti-fraud completo, dos capturas independientes, comparator, VAS,
   assertion de estado y audit modal cuando corresponde.
5. Entrega todas las mediciones a `closure_policy.decide`; el closer no decide
   PASS por su cuenta ni acepta overrides de thresholds.
6. Si la policy permite, construye un record `nm_suite.evidence_record.v2` con
   provenance exacta (canonical, manifest, herramientas, thresholds y scope),
   mediciones, determinism, target set y aprobación externa si aplica.
7. Publica en `docs/closure_evidence/active/<key_safe>.json` y regenera el
   handoff desde MANIFEST + records activos + `surface_notes.json` en una sola
   transición atómica.

Si tu target set tiene N keys en PASS, repetí la invocación N veces
(secuencial). **El gate exige working tree limpio — incluido el handoff —
antes de CADA invocación**, así que después de cada cierre tenés que
commitear ese cierre antes de cerrar la siguiente key (ver §4a). Cada
invocación construye su **propio** record activo v2. No hay cierre sin record
propio validable — para ninguna key, sea cual sea el target mode.

> **Prohibición total:** no edites el handoff, un record activo ni un recibo
> revocado. El closer es el único escritor; `render_handoff.py` produce la
> vista. Una edición manual rompe la igualdad byte a byte o el replay.

**Carril near-threshold.** Configurá desde el secret store una credencial
fine-grained con lectura de metadata/issues y sin permisos de escritura, más
el issue fijo y el owner esperado:

```powershell
$env:GH_TOKEN = "<PAT-restringido-solo-lectura>"
$env:NM_VISUAL_APPROVAL_REPO = "Rybjuani/nm_suite"
$env:NM_VISUAL_APPROVAL_OWNER = "Rybjuani"
$env:NM_VISUAL_APPROVAL_ISSUE = "<numero-del-issue-fijo>"
```

El verifier nunca infiere el número de issue desde una URL no confiable. Si
sólo falta la aprobación externa, el primer
intento sale con código 3 y escribe un candidato inmutable bajo
`reports/qa/visual_closure_pending/`. El owner, desde su cuenta separada,
comenta en el issue fijo la key y los primeros 12 caracteres de
`report_sha256`. Luego se reanuda sin re-medir:

```powershell
.\.venv\Scripts\python.exe qa\close_visual_key.py `
  --resume-pending <pending.json> `
  --approval-url <https://github.com/...#issuecomment-...>
```

El verifier exige repo, issue, comment ID, autor owner y contenido exacto. El
token del agente no debe poder escribir comentarios ni aprobar su propio PR.

### 3.1 Reapertura sancionada (revocar un cierre comprometido)

Si se demuestra que un cierre dependió de fraude/gaming (overlay, blur/alpha,
manipulación de evidence), la ÚNICA forma de reabrirlo es:

```powershell
.\.venv\Scripts\python.exe qa\close_visual_key.py --key <key> --reopen --reason "<motivo objetivo con métricas>"
```

Exige tree limpio + record íntegro; mueve el record a
`docs/closure_evidence/active/revoked/`, escribe un recibo inmutable con el
motivo y regenera la vista. Borrar o editar a mano un record no equivale a
reabrir. La reapertura es visible y auditable; nunca la uses para "resetear"
una key sin causa.

**Staleness.** Tras cambios de fuente, refrescá sólo lo alcanzado por el scope:

```powershell
.\.venv\Scripts\python.exe qa\close_visual_key.py --refresh-evidence --stale
# o una selección explícita:
.\.venv\Scripts\python.exe qa\close_visual_key.py --refresh-evidence --keys <k1> <k2>
```

Cada key se vuelve a medir. PASS reemplaza su record con nota de refresh;
policy FAIL la reabre como `stale_fail`. Un error operativo no autoriza una
revocación silenciosa.

Si el ÚNICO bloqueo de una key es la aprobación externa (near-threshold), el
refresh NO la reabre: deja el record viejo activo (sigue stale), escribe un
candidato inmutable en `reports/qa/visual_closure_pending/` y sale con código 3.
El owner comenta la key y el prefijo del `report_sha256` NUEVO del candidato en
el issue fijo, y se reanuda con el mismo carril del cierre:

```powershell
.\.venv\Scripts\python.exe qa\close_visual_key.py `
  --resume-pending <pending.json> `
  --approval-url <https://github.com/...#issuecomment-...>
```

El resume de un refresh reemplaza el record activo sólo si sigue siendo el
mismo del que partió la medición (`pending_refresh_source_mismatch` si cambió).

---

## 4. Post-cierre

El post-cierre tiene **3 etapas separadas**: commit local, replay full y
publicación por decisión owner. No las mezcles.

### 4a. Cierre local (vos)

Después de correr `close_visual_key.py` para cada key del target set que
llegó a PASS:

```powershell
git add -- VISUAL_REPAIR_HANDOFF.md docs/closure_evidence/active
git status
```

**Granularidad de commit**: siempre **1 commit por key cerrada**, secuencial
(cerrar key → verificar diff → commit → repetir con la siguiente). El gate de
`close_visual_key.py` exige el handoff limpio antes de cada cierre, así que
bundlear N closures en un commit no es ejecutable — para TODOS los target
modes, incluidos `batch`/`family`/`all-open-keys`. Lo que agrupan esos modos
es el **trabajo**, no el commit. Cada key conserva su record v2 propio.

Verificá que el staged diff muestra ÚNICAMENTE:
- `VISUAL_REPAIR_HANDOFF.md` regenerado;
- 1 record nuevo por key en `docs/closure_evidence/active/<key_safe>.json`.

Si hay más archivos staged (capturas temporales, logs, cambios en `app/` que
no commiteaste antes del cierre), deshacelos con `git restore --staged <file>`.
Los fixes de producto deben estar commiteados antes de iniciar el closer.
El commit de cierre debe ser limpio: handoff + evidence record(s), nada más.

```powershell
git commit -m "close: <key>"      # uno por key, antes de cerrar la siguiente
```

### 4b. Verificación local pre-push (vos)

Antes de pensar en publicar, corré el replay full local. La máquina que cierra
es la **única** que vuelve a medir pixeles:

```powershell
.\.venv\Scripts\python.exe qa\replay_visual_closure.py --base <base-real>
```

En hitos de familia y al final, reproducí todos los records activos:

```powershell
.\.venv\Scripts\python.exe qa\replay_visual_closure.py --all-closed
```

El replay verifica la clase A de provenance de forma exacta y re-deriva la
clase B con capturas nuevas. La recaptura y sus métricas pueden variar dentro
de los bars; lo obligatorio es que la policy vuelva a dar ALLOW. Nunca exijas
un hash PNG o un reporte nuevo byte-idéntico al almacenado. Para keys
near-threshold, el replay reutiliza la aprobación almacenada de forma
EXPLÍCITA (`binding: stored_record_reuse`): el hash verificado por GitHub no
se reescribe nunca sobre el reporte regenerado, y el reuso sólo vale mientras
los findings near-threshold regenerados no excedan los aprobados
(`approval_reuse_findings_exceeded` si aparecen nuevos).

**Cómo resolver `<base-real>`**: el replay audita el rango `base..HEAD`. Tenés
que elegir `base` como el último commit **anterior** a tus cierres. Opciones:

- Si tu local está al día con `origin/main` y sólo agregaste commits de cierre:
  ```powershell
  git rev-parse origin/main
  # usá ese hash como --base
  .\.venv\Scripts\python.exe qa\replay_visual_closure.py --base <hash-de-origin/main>
  ```

- Sincronizá/rebaseá la rama de producto **antes** de ejecutar el closer. Si
  `origin/main` avanza después de crear records, no rebases esos records a
  ciegas: el rebase cambia ancestros y vuelve inválido `commit_head`. Actualizá
  la rama y recreá/refrescá la evidencia por el carril sancionado antes del PR.

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
vuelve a consultar la policy. **Si una sola key no alcanza ALLOW, todo
falla.** No arregles el record para acomodarlo a la nueva medición: corregí
producto/receta o reabrí/refrescá por el carril sancionado.

> **Por qué `base` debe ser el padre del primer `close:`** (no un commit
> arbitrario). `close_visual_key.py` registra `commit_head = HEAD` **antes**
> de que el worker cree el commit `close: <key>`, así que el evidence de un
> cierre se captura contra el HEAD previo al commit de cierre. Para una
> secuencia de cierres `c1 → c2 → ... → cN`, eso significa que el record del
> PRIMER cierre tiene `commit_head == padre(c1)`. Si elegís `base =
> padre(c1)` (los atajos `HEAD~1` o `<primer-close>^` hacen exactamente
> eso), el replay acepta ese `commit_head == base` como punto legítimo de
> captura. Cualquier otro record de la secuencia tiene `commit_head` dentro
> de `(base, HEAD]` y se valida normalmente.
>
> **Guardia conceptual — esto NO habilita marker commits ni bases
> arbitrarias**: aceptar `commit_head == base` SÓLO es válido cuando `base`
> es el commit real inmediatamente anterior al primer `close:` del rango.
> No es una licencia para elegir `base` en otro punto del historial y
> esquivar así commits de producto o kernel fuera del rango auditado: el
> replay sigue verificando hashes, R0 dentro del rango y la integridad del
> record, y un `base` mal elegido (no el padre inmediato del primer
> `close:`) deja fuera del rango a commits reales que tocaron código.
>
> **RIESGO RESIDUAL**: al aceptar `base_commit` como `commit_head` válido
> se elimina el falso negativo del off-by-one entre cómo se captura
> `commit_head` y cómo se define el rango, pero esto vuelve MÁS IMPORTANTE
> la elección correcta de `<base-real>`. Un `base` mal elegido (p.ej. un
> commit de marker, o un commit más nuevo para "achicar" el rango y que
> R0 no flaggee cambios kernel) reabre superficie de manipulación. Regla
> operativa: `base` = `git rev-parse <primer-close-de-la-secuencia>^`,
> SIEMPRE. Si duda, derivelo mecánicamente del `git log --oneline`, no lo
> elija a mano.

### 4c. Publicación (decisión del owner)

**Vos no decidís el push, el merge ni una aprobación.** El owner decide cuándo
y cómo publicar. Trabajá en una rama; nunca empujes directo a `main`.

Después de que 4a + 4b pasan, el estado es:
- 1 o más commits locales de cierre, siempre 1 por key cerrada (§4a)
- Replay full PASS para el rango completo

Reportá al owner:
```
Target set: <modo declarado> — <N> keys
Keys cerradas: <key1>, <key2>, ...
Commit(s): <hash1> [, <hash2>, ...]
Replay base: <base-real>
Replay full: PASS
Ready for owner review: no push/merge performed
```

Sólo si el owner autoriza publicar la rama:
```powershell
git push origin <rama-de-trabajo>
```

CI (`.github/workflows/visual-closure-replay.yml`) corre automáticamente
en el PR con `--structural-precheck`: valida clase A, cardinalidad, staleness,
approvals, handoff generado y R0, pero no re-renderiza pixeles. Es un gate
**solo-BLOCK**: jamás crea o valida un cierre por sí mismo.

La credencial del agente debe estar restringida a la rama/PR necesarios, sin
admin, sin bypass de rulesets, sin merge y sin escritura de issues/comentarios.
La cuenta owner separada aplica branch protection, revisa CODEOWNERS, publica
aprobaciones near-threshold y decide el merge.

---

## 5. R0 — Kernel inmutable (NO tocar en mismo PR que cierre)

Estos archivos **no pueden modificarse** en el mismo rango auditado que un
cierre. Si los tocás, todas las keys cerradas en ese rango fallan con
`kernel_changed_with_visual_closure`. Hacé el cambio del kernel en un PR
separado, mergealo, y después cerrá keys.

```
qa/anti_fraud_scan.py
qa/approval_verifier.py
qa/capture_v8.py
qa/close_visual_key.py
qa/closure_policy.py
qa/hash_utils.py
qa/layered_visual_compare.py
qa/odiff_runner.py
qa/render_handoff.py
qa/replay_visual_closure.py
qa/run_visual.ps1
qa/spec_generator.py
qa/specs/specs.json
qa/state_probes.py
qa/surface_notes.json
qa/surface_scope.py
qa/target_scope.py
qa/vas_gate.py
qa/vas_engine.py
qa/vas_introspect.py
qa/_mockup_canonical/                  (dir, recursivo)
qa/pack canonico/                       (dir, recursivo)
tools/qa/                                (dir, recursivo)
.github/workflows/                       (dir, recursivo)
.github/CODEOWNERS
```

Lista sincronizada con `KERNEL_PATHS` en `qa/replay_visual_closure.py` (fuente
de verdad en código). `.github/CODEOWNERS` asigna estos namespaces a
`@Rybjuani`; el owner debe activar en `main` require PR + code-owner review,
sin force-push ni bypass para la credencial del agente. CODEOWNERS sin ese
ruleset no alcanza.

---

## 6. Reglas de cierre prohibidas (lo que NO cuenta como PASS)

Estos criterios **no son evidencia de cierre** y nunca deben invocarse:

- **Frases subjetivas de aceptación visual o aprobación no reproducible** no son medibles,
  no son reproducibles, no cuentan.
- **Frases de progreso parcial** ("mayormente arreglado", "residuo aceptable",
  "avance parcial", "cosmético", "menor") — un fix parcial no es un cierre.
- **Frases de abandono** ("bloqueado", "demasiado difícil", "no se puede arreglar",
  "downgrade") no son resultado operativo de Visual QA; segui iterando producto
  o detenete sólo bajo las condiciones de §2.4.
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
  interno o "riesgo" percibido. Una key `FAIL` sigue pendiente y no se
  saltea; esto no impide cerrar por separado las keys que sí dan ALLOW.
- **Ampliar el target set** más allá de lo declarado por el owner, salvo
  evidencia objetiva de que una key no existe, está duplicada, o ya no está
  abierta (reportá la desviación, no la apliques en silencio).
- Invocar antialiasing/text-rendering (MISMATCH#20 o similar) como excusa de
  bloqueo sin evidencia real de `regions[]` / `largest_region_ratio` /
  `bbox_dy` que lo respalde — seguí el procedimiento mecánico de §2.5 antes
  de declarar una divergencia "irreducible".
- Invocar MISMATCH#18, riesgo transversal, históricos, comentarios UX o
  "user feedback" como bloqueo si no existe una entrada activa
  `IRREDUCIBLE`/`DECISIÓN-OWNER` en las fuentes vigentes.

### 6.1 Disclosure obligatorio de intentos revertidos

El reporte final debe declarar cualquier intento revertido que haya tocado
rutas R0, shared sensibles o rutas prohibidas, aunque el diff final quede
limpio.

Debe incluir:
- archivo tocado;
- cambio intentado;
- motivo de reversión;
- evidencia de reversión (`git diff -- <archivo>` vacío o equivalente).

Omitir un intento revertido sobre rutas sensibles se considera reporte
incompleto. Un diff final limpio no reemplaza la trazabilidad del camino.

Rutas sensibles incluyen, como mínimo: `qa/`, `tools/qa/`, `.github/`,
`docs/closure_evidence/`, canon, thresholds, comparator, capture harness,
close/replay scripts, evidence y componentes compartidos que afecten múltiples
visual keys, como modales/base dialogs.

Tocar y revertir puede ser tolerable si queda limpio.
Tocar, revertir y no declararlo deja el reporte incompleto.
Tocar y commitear sin autorización invalida la tarea.

---

## 7. Cierre bloqueado — cuándo parar

Si `close_visual_key.py` falla, NO intentes reproducir el PASS por fuera del script.
El script falla ruidosamente con uno de estos códigos:

| exit | motivo | acción |
|------|-------|--------|
| 2 | `dirty_working_tree` | commiteá o descartá cambios en scoped paths |
| 2 | `key_already_closed` | el record activo ya existe; no edites el handoff |
| 2 | `key_outside_target_set` / `target_key_not_in_manifest` | regenerá el target set desde §0 |
| 1 | `closure_policy_blocked: ...` | corregí la medición indicada; no cambies policy/record |
| 3 | `pending-approval: <path>` | obtené aprobación owner externa y usá `--resume-pending` |
| 1 | fallo de anti-fraud/capture/comparator/VAS/modal | revisá stderr y volvé a §2 |

Cualquier otro error → pará, reportá el stderr completo en el canal de handoff.

**Con target set de N keys**: si `close_visual_key.py` falla para una key, no
modifiques gate/harness para destrabarla. Esa key sigue pendiente; las demás
pueden cerrar independientemente si alcanzan ALLOW y pertenecen al set. Si
parece bug R0, reportá una tarea separada sin fabricar evidencia. Un
`dirty_working_tree` impide cualquier invocación hasta resolver el tree.

---

## 8. Lo que NO tenés que hacer

- ❌ Derivar el target set leyendo o copiando el handoff a mano: usá
  `qa\target_scope.py` sobre la vista actual.
- ❌ Correr `capture_v8.py --all --clean` salvo target mode `all-open-keys`
  con un cambio verdaderamente transversal (theme/chrome/`NMCard`/shell).
- ❌ Correr `run_visual.ps1 -All` fuera de ese mismo caso o de una regresión
  final oficial.
- ❌ Correr `audit_mockup_parity_baseline.py` (sólo si cambiaste canonical HTML/recipe/PNGs).
- ❌ Correr `replay_visual_closure.py` antes de cerrar (es post-cierre).
- ❌ Correr `audit_modal_backdrop_blur.py` a mano por separado (ya está
  integrado en el runner y en `close_visual_key.py`).
- ❌ Editar `docs/closure_evidence/active/**` por fuera de `close_visual_key.py`.
- ❌ Editar el handoff manualmente, incluso para cambiar un checkbox o nota.
- ❌ Editar `surface_notes.json` en el mismo PR/rango que cierra keys.
- ❌ Tocar kernel R0 en el mismo PR que un cierre.
- ❌ Cerrar una key sin su propio evidence record — sin importar si el
  commit es individual o batch (§3, §4a).
- ❌ Achicar o ampliar el target set que declaró el owner sin evidencia
  objetiva de key inexistente/duplicada/ya cerrada (§6).
- ❌ Pushear directo a `main`, aprobar o mergear: el owner decide.

---

## 9. Resumen del flujo (recordatorio de 1 pantalla)

```
[Resolver target set] → owner declara modo → target_scope.py --mode <modo> [...]
   ↓
[Pre-flight mapping] → graphify + matriz + mismatches (≤2 min, por key nueva)
   ↓
[Ciclo de reparación] → editar app/ + run_visual.ps1 -Key <key> (1 key) o
                         run_visual.ps1 -PlanFile <csv> (N keys) — 15-45 s/key
   ↓           ↑
   ↓  PASS? (por key) ↑
   ↓           ↑ NO
   ↓           └── (3 sin mejora → preservar diff real, localizar causa,
   ↓               cambiar estrategia de producto — §2.5)
   ↓ SÍ (repetir para cada key del target set)
[close_visual_key.py --key <key> --target-set-file <archivo>]  (doble captura, worktree aislado)
   ↓
─── ETAPA 4a: CIERRE LOCAL ───
[git add + commit]  (SIEMPRE 1 commit por key, antes del siguiente cierre — §4a)
   ↓
─── ETAPA 4b: VERIFICACIÓN LOCAL ───
[replay_visual_closure.py --base <base-real>]  (full regen independiente del rango)
   ↓ PASS
─── ETAPA 4c: PUBLICACIÓN (owner decide) ───
[reportar al owner: target set + keys cerradas + commit(s) + replay PASS]
   ↓ owner autoriza
[git push origin <rama-de-trabajo>]
   ↓
[CI corre --structural-precheck + pytest stdlib]  (solo-BLOCK, sin pixeles)
   ↓
[owner review + merge según ruleset]
```

**Costo total por key exitosa**: ~10-30 min wall-clock + tiempo de doc proporcional al target set (no todo el handoff).
**Costo por intento fallido (pre-flight sin cerrar)**: ~1-5 min (1-7 ciclos pre-flight) por key.
**Costo de replay full local**: ~5-15 min por corrida, cubre todas las keys cerradas en el rango auditado (no escala 1:1 con N si se hizo en batch).
