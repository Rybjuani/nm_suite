# VisualParity V3.1 — Gobernanza y arquitectura

> **ARCHIVADO 2026-07-12 — programa SUPERSEDED.** El plan vigente es
> "V1 saneado" (`Plan Harness Fable.md`, raíz): la cadena de cierre corregida
> vive en `qa/` (closure_policy, closer v2, replay independiente, CI
> solo-BLOCK). Los skeletons `harness/`, `harness/v3/` y `tools/visualparity/`
> fueron eliminados del árbol; ver `OWNER_DECISIONS_LOCKED.md` (LOCK-3/LOCK-4
> SUPERSEDED) y el tag `forensic-pre-v3.1`.

> **Fase 0A skeleton — no runtime authority.** Este directorio contiene documentación
> y skeletons de gobernanza. Ningún archivo aquí constituye autoridad operativa de
> cierre, medición o policy hasta que Fases posteriores implementen runtime real.

## Tesis no negociable

> **VisualParity mide y muestra. El harness decide.**

VisualParity produce métricas crudas y estados de medición. El harness `v3`
consume esos bundles, aplica la política de cierre y decide. La separación
entre medición y política es absoluta; cualquier mezcla reproduce los
defectos de V1/V2.

## Alcance V3.1

V3.1 es el reemplazo limpio del sistema fallido de QA visual de `nm_suite`.
Reemplaza — no endurece — a V1 (`qa/` closer/comparator/replay/anti-fraud
viejos) y a V2 (`harness/` stubs no funcionales).

V3.1 vive **dentro de `nm_suite`** como monorepo. No se crea repo externo
`github.com/Rybjuani/visualparity`. La propuesta previa `docs/VisualParity_V3/`
es material forense, no base operativa.

## Rutas oficiales V3.1

| Ruta | Rol |
|---|---|
| `tools/visualparity/` | VisualParity Core/CLI (.NET 8, futuro). Medición pura. |
| `harness/v3/` | Harness consumidor (Python, futuro). Política + aplicación + persistencia. |
| `docs/VisualParity_V3_1/` | Documentación V3.1 (este directorio). |
| `qa/capture_v8.py` | Generador transitorio. Sólo invocado por `harness/v3/capture_orchestrator.py`. |
| `qa/_mockup_canonical/` | Canon único tras reconciliación (ver `CANON_RECONCILIATION_PLAN.md`). |

## No-go absolutos

Estos items son violaciones de invariante. Cualquier PR que los introduzca
debe ser rechazado.

1. **No crear repo `Rybjuani/visualparity`.** V3.1 vive en `nm_suite`.
2. **No archivar V1/V2 código, scripts, evidence records, tarballs o bundles
   dentro de `main`.** Preservación forense sólo vía tag + git bundle externo
   + SHA256 + MANIFEST puntero (ver `MIGRATION_A_PLUS.md`).
3. **`docs/_archive/` sólo contiene documentación histórica no ejecutable.**
   Prohibido: scripts V1/V2, evidence records V1, tarballs ejecutables,
   copias completas del harness viejo.
4. **VisualParity Core/CLI no puede invocar `qa/capture_v8.py`.** La captura
   es responsabilidad exclusiva del harness v3 vía `capture_orchestrator.py`.
5. **`--introspect` deshabilitado** hasta que se audite `vas_introspect.py`
   a profundidad (ver `CAPTURE_V8_TRANSITION.md`).
6. **`--no-regen` no existe como cierre.** Replay válido = recaptura +
   recomparación + cardinalidad exacta.
7. **`LOW_DIFF` no cierra.** Requiere `HUMAN_REVIEWED_PASS` individual.
8. **`HIGH_DIFF` no tiene override.** Si se sospecha falso positivo, el path
   es `MEASUREMENT_DISPUTE` (recalibración versionada + regeneración de
   bundle), no override.
9. **Bulk `HUMAN_REVIEWED_PASS` prohibido.** Un `review_annotation.json`
   por surface.
10. **CI sólo bloquea; no autoriza cierre.**
11. **`signature.sha256` prohibido como firma.** Cadena de custodia con
    `bundle_sha256`, `vp_build_sha256`, `policy_sha256`,
    `closure_decision_sha256` separados + `integrity/checksums.json`.
12. **`DECISIÓN-OWNER` prohibido en docs activos.** `OWNER_EXCEPTION_ACTIVE`
    sólo como registro firmado con `reason` + `reviewer` + `timestamp`,
    nunca como flag o bypass.
13. **No mixed commits** entre producto, VisualParity Core, policy, canon y
    closure evidence.
14. **UI (WPF, fase futura) sólo produce `review_annotation.json`.** El
    harness emite `HUMAN_REVIEWED_PASS/FAIL`, nunca VisualParity. WinUI
    queda fuera de V3.1.

## Documentación V3.1

| Archivo | Contenido |
|---|---|
| `README.md` | Este archivo. Tesis, alcance, rutas, no-go. |
| `MIGRATION_A_PLUS.md` | Plan de archivo forense A+ pre-V3.1. |
| `ARCHITECTURE.md` | Separación de capas, módulos, estados. |
| `THREAT_MODEL.md` | Matriz de amenazas VQA-RT-001. |
| `POLICY.md` | Reglas de cierre V3.1. |
| `CORPUS.md` | Corpus mínimo de pruebas. |
| `PHASE_0A_DECISIONS.md` | Owner decisions pendientes. |
| `CANON_RECONCILIATION_PLAN.md` | Reconciliación `pack canonico/` vs `_mockup_canonical/`. |
| `CAPTURE_V8_TRANSITION.md` | Límites de `capture_v8.py` como generador transitorio. |
| `CHANGELOG.md` | Historial de cambios V3.1. |

## Estado actual (Fase 0A)

- **Implementado:** sólo documentación y skeletons no funcionales.
- **No implementado:** VisualParity Core, harness v3 funcional, CI V3.1.
- **V1/V2:** intactos en `main` (sin borrar, sin mover). Preservación forense
  planificada pero no ejecutada en Fase 0A.
- **Producto (`app/`, `hub/`, `shared/`, `db/`, `assets/`, `installers/`):**
  sin modificaciones.
- **Canon (`qa/_mockup_canonical/`, `qa/pack canonico/`):** sin
  modificaciones. Plan de reconciliación documentado.
- **Evidence records (`docs/closure_evidence/`):** sin modificaciones.

## Próximas fases (no ejecutadas en Fase 0A)

- **Fase 0B:** tests de schemas, denylist, mixed commit, corpus inventory,
  bundle determinism.
- **Fase 1A:** VisualParity Core/CLI (.NET 8) — `compare`, `batch`,
  `verify-bundle`, `inspect`. Sin UI, sin cierre.
- **Fase 1B+:** harness v3 funcional, CI V3.1, agent runner.
- **Fase futura:** UI WPF (sólo `review_annotation.json`).
