# Fase 0A — Owner Decisions pendientes

> **Fase 0A skeleton — no runtime authority.** Este documento lista las
> decisiones reales que requieren input del owner antes de avanzar a Fase 0B
> y Fase 1A. No son tareas de auditoría.

## Tesis

Fase 0A crea documentación y skeletons no funcionales. Antes de Fase 0B
(tests) y Fase 1A (implementación VisualParity Core), el owner debe
resolver estas decisiones. Cada decisión tiene una recomendación clara;
el owner puede aceptar la recomendación o elegir otra opción.

## Decisiones pendientes

### #1 — Bundle forense A+: ubicación

**Decisión:** ¿Dónde se publica el `git bundle` forense pre-V3.1?

**Opciones:**
- (a) **GitHub Release asset en `nm_suite`** (recomendado: mismo repo, no
  externo, descargable públicamente o restringido al owner).
- (b) Storage owner privado (S3, drive, etc.).

**Recomendación:** (a). Mantiene todo dentro de `nm_suite`; no crea
dependencia externa; el bundle es descargable por cualquiera con acceso al
repo.

**Impacto si no se decide:** No se puede iniciar la migración A+ (Paso 1
del plan en `MIGRATION_A_PLUS.md`). V1/V2 quedan en path activo
indefinidamente.

---

### #2 — `capture_v8.py` conservado como generador transitorio

**Decisión:** ¿Se conserva `qa/capture_v8.py` como generador transitorio
con los límites declarados en `CAPTURE_V8_TRANSITION.md`?

**Opciones:**
- (a) **Conservar con límites** (recomendado: 3089 LOC funcionales,
  autónomo respecto a V1 closers; sólo `harness/v3/capture_orchestrator.py`
  lo invoca; `--introspect` deshabilitado hasta auditar `vas_introspect.py`).
- (b) Reescribir desde cero (trabajo de ~2-3 fases adicionales).

**Recomendación:** (a). Reescribir captura es costo alto sin beneficio
claro en Fase 1A. Los límites aíslan el riesgo.

**Impacto si no se decide:** Fase 1A no puede empezar
(`capture_orchestrator.py` depende de esto).

---

### #3 — `vas_introspect.py`: auditoría futura

**Decisión:** ¿Cuándo y quién audita `vas_introspect.py` a profundidad
para rehabilitar `--introspect`?

**Opciones:**
- (a) **Auditar en Fase 0B/1A** antes de habilitar `--introspect`.
- (b) **Eliminar flag `--introspect` definitivamente** (capture_v8 sin
  VAS widget tree audit).

**Recomendación:** (a). VAS widget tree audit es señal valiosa para
`state_assertion`; eliminarla pierde información. Pero la auditoría debe
preceder a la habilitación.

**Impacto si no se decide:** `--introspect` queda en estado limbo
(deshabilitado por defecto, no auditable).

---

### #4 — Handoff (`VISUAL_REPAIR_HANDOFF.md`)

**Decisión:** ¿Se elimina el handoff como autoridad, o se conserva como
view read-only generado mecánicamente por el harness desde records?

**Opciones:**
- (a) **Eliminar** (recomendado: autoridad es `closure_decision.json` por
  surface en `harness/v3/evidence_records/active/`).
- (b) Conservar como view read-only generado mecánicamente.

**Recomendación:** (a). El handoff fue fuente de ambigüedad y bypass en
V1/V2 (duplicate keys, semántica FAIL persistente). Eliminarlo como
autoridad cierra esos vectores.

**Impacto si no se decide:** Persiste ambigüedad de autoridad.

---

### #5 — `qa/tessdata/`

**Decisión:** ¿Se conserva `qa/tessdata/` o se elimina?

**Opciones:**
- (a) Conservar (si V3.1 usa tesseract para OCR de state fingerprint).
- (b) Eliminar (si V3.1 no usa OCR).

**Recomendación:** Sin recomendación fuerte; depende de si
`state_assertion.py` usará OCR. En Fase 0A, `tessdata/` queda congelado
(no se elimina, no se modifica).

**Impacto si no se decide:** Dependencia incierta. No bloquea Fase 1A.

---

### #6 — Self-hosted runner

**Decisión:** ¿CI self-hosted runner en GitHub Actions, o máquina owner
local con script de cierre?

**Opciones:**
- (a) **GitHub Actions self-hosted** (recomendado: integración nativa con
  el workflow existente).
- (b) Máquina owner local con script de cierre.

**Recomendación:** (a). Self-hosted runner integra con CI existente; el
cierre es un step del workflow, no un proceso manual separado.

**Impacto si no se decide:** No se puede definir flujo de cierre post-CI.

---

### #7 — Stack VisualParity

**Decisión:** ¿Confirmar .NET 8 + CLI primero, WPF después, WinUI fuera?

**Opciones:**
- (a) **.NET 8 + CLI primero + WPF después + WinUI fuera** (alineado con
  prompt V5).
- (b) Otra variante.

**Recomendación:** (a). Alineado con el prompt V5 y la redline V5.1.

**Impacto si no se decide:** Fase 1A no puede empezar.

---

### #8 — `WORKER_VISUAL_QA_FLOW.md`

**Decisión:** ¿Se reescribe para V3.1, o se archiva?

**Opciones:**
- (a) **Reescribir** (referencia operativa para agentes V3.1).
- (b) Archivar (V3.1 docs nuevos reemplazan).

**Recomendación:** (a). Agentes necesitan un protocolo operativo V3.1
claro. Archivar sin reemplazar deja vacío operacional.

**Impacto si no se decide:** Agentes no tienen protocolo operativo V3.1.

---

### #9 — Timing migración

**Decisión:** ¿Fase 0 inmediatamente, o ventana de freeze?

**Opciones:**
- (a) **Inmediatamente** (recomendado: V1/V2 en path activo es riesgo
  activo; cualquier commit puede invocarlos vía CI).
- (b) Ventana de freeze (ej. post-release).

**Recomendación:** (a). El riesgo de V1/V2 wired al CI es activo.

**Impacto si no se decide:** V1/V2 siguen wired al CI.

---

### #10 — 116 closures V1

**Decisión:** ¿Re-abrir todos como OPEN, o marcar `INVALIDATED_PRE_V3.1`
sin re-abrir?

**Opciones:**
- (a) **Re-abrir como OPEN** (recomendado: alineado con FORENSIC_AUDIT_V3;
  los 116 son forense débiles).
- (b) Marcar `INVALIDATED_PRE_V3.1` en record (sin re-abrir handoff si
  handoff se elimina).

**Recomendación:** (a). Si el handoff se elimina (decisión #4), los
closures V1 dejan de tener sentido operacional. Re-abrir como OPEN es
estado limpio.

**Impacto si no se decide:** Estado de closures es ambiguo.

---

### #11 — Reconciliación canónica `pack canonico/` vs `_mockup_canonical/`

**Decisión:** ¿Confirmar que `_mockup_canonical/` es canon único tras
reconciliación, y qué hacer con assets únicos de `pack canonico/` si los
hay?

**Opciones:**
- (a) **Canon único en `_mockup_canonical/` con paths relativos; migrar
  assets únicos de `pack canonico/` antes de eliminarlo** (recomendado).
- (b) Mantener ambos directorios si la reconciliación revela
  divergencias irreconciliables.

**Recomendación:** (a). Canon único elimina ambigüedad. La reconciliación
(ver `CANON_RECONCILIATION_PLAN.md`) determina si hay assets únicos.

**Impacto si no se decide:** Coexistencia ambigua de dos directorios
canónicos.

---

## Resumen

| # | Decisión | Recomendación | Bloquea Fase 0B | Bloquea Fase 1A |
|---|---|---|---|---|
| 1 | Bundle forense ubicación | (a) GitHub Release asset | No | No (pero bloquea migración) |
| 2 | `capture_v8.py` conservado | (a) Conservar con límites | No | Sí |
| 3 | `vas_introspect.py` auditoría | (a) Auditar en 0B/1A | No | No (pero `--introspect` en limbo) |
| 4 | Handoff eliminar | (a) Eliminar | No | No (pero ambigüedad) |
| 5 | `tessdata/` conservar | Sin recomendación fuerte | No | No |
| 6 | Self-hosted runner | (a) GitHub Actions self-hosted | No | No (pero bloquea cierre) |
| 7 | Stack VisualParity | (a) .NET 8 + CLI + WPF + no WinUI | No | Sí |
| 8 | `WORKER_VISUAL_QA_FLOW.md` reescribir | (a) Reescribir | No | No (pero vacío operacional) |
| 9 | Timing migración | (a) Inmediatamente | No | No (pero riesgo activo) |
| 10 | 116 closures V1 | (a) Re-abrir como OPEN | No | No (pero ambigüedad) |
| 11 | Canon reconciliación | (a) Canon único + migrar únicos | No | No (pero ambigüedad) |

**Bloqueantes para Fase 1A:** #2, #7.

**Bloqueantes para migración A+:** #1.

**Riesgo activo si se posterga:** #9.
