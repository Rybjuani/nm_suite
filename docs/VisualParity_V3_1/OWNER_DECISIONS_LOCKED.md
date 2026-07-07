# Owner Decisions Locked — Fase 0D

> **Fase 0D — migration planning. No runtime authority. No visual closure.**
>
> Este documento registra las decisiones owner cerradas en Fase 0D y las
> decisiones aún pendientes. Es autoridad de gobernanza para Fases posteriores;
> no es runtime authority.

## Tesis

Fase 0D cierra 5 decisiones owner mínimas requeridas para preparar la
migración forense A+ y dejar el plan operativo auditable. Las decisiones
cerradas aquí son **vinculantes** para Fases posteriores: cualquier cambio
requiere un nuevo prompt explícito del owner y un nuevo commit que actualice
este documento.

## LOCKED_FOR_V3_1

Decisiones cerradas en Fase 0D. No se reabren sin prompt explícito del owner.

### LOCK-1 — Bundle forense A+ ubicación

**Decisión:** Usar GitHub Release asset del propio `nm_suite` como opción
primaria. Storage owner privado permitido sólo como fallback documentado.
**No crear repo externo** (`github.com/Rybjuani/visualparity` prohibido).

**Razón:** Mantiene todo dentro de `nm_suite`; no crea dependencia externa;
el bundle es descargable por cualquiera con acceso al repo. El fallback a
storage owner privado se documenta en `FORENSIC_SNAPSHOT_PREFLIGHT.md` por
si GitHub cambia políticas de tamaño de Release assets.

**Impacto:** Desbloquea el Paso 1 del plan de ejecución A+
(`MIGRATION_A_PLUS_EXECUTION_PLAN.md`).

**Referencias:** `FORENSIC_SNAPSHOT_PREFLIGHT.md`, `MIGRATION_A_PLUS.md`,
`MIGRATION_A_PLUS_EXECUTION_PLAN.md`.

---

### LOCK-2 — `capture_v8.py` conservado como generador transitorio

**Decisión:** `qa/capture_v8.py` se conserva como generador transitorio con
límites estrictos:

- Sólo el futuro `harness/v3/capture_orchestrator.py` podrá invocarlo.
- VisualParity Core/CLI nunca lo invoca.
- `--introspect` queda deshabilitado hasta auditar `vas_introspect.py`
  (decisión STILL_OWNER_DECISION_REQUIRED #1).

**Razón:** `capture_v8.py` (3089 LOC) es autónomo respecto a V1
closers/comparators/replay. Reescribirlo es costo alto sin beneficio claro
en Fase 1A. Los límites aíslan el riesgo.

**Impacto:** Desbloquea Fase 1A (`capture_orchestrator.py` depende de esto).

**Referencias:** `CAPTURE_V8_TRANSITION.md`, `ARCHITECTURE.md`.

---

### LOCK-3 — Stack VisualParity

**Decisión:**

- VisualParity Core/CLI = .NET 8.
- CLI/Core primero (Fase 1A).
- WPF después (fase futura, sólo `review_annotation.json`).
- WinUI fuera de V3.1.

**Razón:** Alineado con el prompt V5 y la redline V5.1. .NET 8 es LTS hasta
noviembre 2026. CLI primero permite validar la medición antes de construir
UI. WPF después porque la UI no es bloqueante para Fase 1A. WinUI fuera
porque añade complejidad sin valor en V3.1.

**Impacto:** Desbloquea Fase 1A (implementación VisualParity Core/CLI).

**Referencias:** `ARCHITECTURE.md`, `README.md`.

---

### LOCK-4 — Timing migración

**Decisión:** Avanzar con migración A+ por fases.

- Fase 0D prepara (este commit).
- Fase posterior ejecutará tag/bundle/remoción sólo con prompt explícito.
- No se ejecuta tag/bundle/release/remoción en Fase 0D.

**Razón:** La migración A+ es irreversible (remoción de V1/V2 del working
tree). Requiere prompt explícito del owner confirmando que el bundle está
publicado y es descargable antes de proceder.

**Impacto:** Fase 0D deja preflight + plan auditable; la ejecución real
queda pendiente de prompt.

**Referencias:** `FORENSIC_SNAPSHOT_PREFLIGHT.md`,
`MIGRATION_A_PLUS_EXECUTION_PLAN.md`, `PHASE_0D_CHECKLIST.md`.

---

### LOCK-5 — Canon

**Decisión:**

- Target canónico futuro: `qa/_mockup_canonical/`.
- No eliminar `qa/pack canonico/` hasta reconciliación.
- MANIFEST futuro con paths relativos.
- Comparar PNGs por SHA256 raw bytes (sin EOL normalization — PNGs son
  binarios).

**Razón:** Canon único elimina ambigüedad. Paths relativos hacen el canon
cross-platform reproducible. SHA256 raw bytes es correcto para binarios.

**Impacto:** Desbloquea Paso 6 del plan de ejecución A+ (reconciliar canon).

**Referencias:** `CANON_RECONCILIATION_PLAN.md`.

---

## STILL_OWNER_DECISION_REQUIRED

Decisiones aún pendientes. No bloquean Fase 0D pero bloquean Fases
posteriores específicas.

### PEND-1 — `vas_introspect.py` auditoría profunda

**Pregunta:** ¿Cuándo y quién audita `vas_introspect.py` a profundidad para
rehabilitar `--introspect`?

**Opciones:**
- (a) Auditar en Fase 0B/1A antes de habilitar `--introspect`.
- (b) Eliminar flag `--introspect` definitivamente.

**Recomendación:** (a). VAS widget tree audit es señal valiosa para
`state_assertion`; eliminarla pierde información. Pero la auditoría debe
preceder a la habilitación.

**Bloquea:** Habilitación de `--introspect` en `capture_orchestrator.py`
(futuro). No bloquea Fase 1A si `--introspect` queda deshabilitado por
defecto.

---

### PEND-2 — Handoff eliminar vs view read-only

**Pregunta:** ¿Se elimina `VISUAL_REPAIR_HANDOFF.md` como autoridad, o se
conserva como view read-only generado mecánicamente por el harness desde
records?

**Opciones:**
- (a) Eliminar (autoridad es `closure_decision.json` por surface).
- (b) Conservar como view read-only.

**Recomendación:** (a). El handoff fue fuente de ambigüedad y bypass en
V1/V2 (duplicate keys, semántica FAIL persistente).

**Bloquea:** Diseño de `evidence_records/` y del flujo de cierre en Fase 1B+.

---

### PEND-3 — `qa/tessdata/`

**Pregunta:** ¿Se conserva `qa/tessdata/` o se elimina?

**Opciones:**
- (a) Conservar (si V3.1 usa tesseract para OCR de state fingerprint).
- (b) Eliminar (si V3.1 no usa OCR).

**Recomendación:** Sin recomendación fuerte; depende de si
`state_assertion.py` usará OCR. En Fase 0D, `tessdata/` queda congelado.

**Bloquea:** No bloquea Fase 1A. Decide dependencia de OCR en
`state_assertion.py`.

---

### PEND-4 — Self-hosted runner

**Pregunta:** ¿CI self-hosted runner en GitHub Actions, o máquina owner
local con script de cierre?

**Opciones:**
- (a) GitHub Actions self-hosted (integración nativa con workflow).
- (b) Máquina owner local con script de cierre.

**Recomendación:** (a).

**Bloquea:** Flujo de cierre post-CI en Fase 1B+.

---

### PEND-5 — `WORKER_VISUAL_QA_FLOW.md`

**Pregunta:** ¿Se reescribe para V3.1, o se archiva?

**Opciones:**
- (a) Reescribir (referencia operativa para agentes V3.1).
- (b) Archivar (V3.1 docs nuevos reemplazan).

**Recomendación:** (a).

**Bloquea:** Protocolo operativo para agentes en Fase 1B+.

---

### PEND-6 — 116 closures V1: reabrir vs `INVALIDATED_PRE_V3.1`

**Pregunta:** ¿Re-abrir todos los 116 closures V1 como OPEN, o marcarlos
como `INVALIDATED_PRE_V3.1` sin re-abrir?

**Opciones:**
- (a) Re-abrir como OPEN (alineado con FORENSIC_AUDIT_V3).
- (b) Marcar `INVALIDATED_PRE_V3.1` en record.

**Recomendación:** (a). Si el handoff se elimina (PEND-2), los closures V1
dejan de tener sentido operacional. Re-abrir como OPEN es estado limpio.

**Bloquea:** Estado de closures post-migración A+.

---

## NOT_DECIDED_IN_THIS_PHASE

Decisiones explícitamente no tomadas en Fase 0D. Se deferencian a Fases
posteriores o a prompts futuros del owner.

- **Edición del workflow legacy** (`.github/workflows/visual-closure-replay.yml`):
  se reemplaza en Paso 7 del plan A+, no en Fase 0D.
- **Implementación de VisualParity Core/CLI**: Fase 1A.
- **Implementación de harness v3 runtime**: Fase 1B+.
- **Reconciliación canónica real** (migrar assets, eliminar `pack canonico/`):
  Paso 6 del plan A+, fase posterior.
- **Cierre o reapertura de keys**: no en ninguna fase de gobernanza; sólo
  en runtime con harness v3 funcional.

## Resumen

| Categoría | Cantidad | Decisiones |
|---|---|---|
| LOCKED_FOR_V3_1 | 5 | LOCK-1 bundle ubicación, LOCK-2 capture_v8, LOCK-3 stack, LOCK-4 timing, LOCK-5 canon |
| STILL_OWNER_DECISION_REQUIRED | 6 | PEND-1 vas_introspect, PEND-2 handoff, PEND-3 tessdata, PEND-4 self-hosted runner, PEND-5 WORKER_VISUAL_QA_FLOW, PEND-6 116 closures |
| NOT_DECIDED_IN_THIS_PHASE | 5 | workflow legacy, VisualParity Core, harness v3 runtime, reconciliación canónica, cierre/reapertura keys |

## Cambio de decisiones

Cualquier cambio a una decisión `LOCKED_FOR_V3_1` requiere:

1. Prompt explícito del owner.
2. Nuevo commit que actualice este documento moviendo la decisión de
   `LOCKED_FOR_V3_1` a `REVOKED` con `reason` + `reviewer` + `timestamp`.
3. Actualización de docs dependientes (`MIGRATION_A_PLUS_EXECUTION_PLAN.md`,
   `FORENSIC_SNAPSHOT_PREFLIGHT.md`, etc.).
4. Re-ejecución del validador Fase 0B para confirmar consistencia.
