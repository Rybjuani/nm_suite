# Transición de `capture_v8.py`

> **Fase 0A skeleton — no runtime authority.** Este documento declara los
> límites de `qa/capture_v8.py` como generador transitorio en V3.1.

## Tesis

`qa/capture_v8.py` (3089 LOC) es el capturador PyQt6 offscreen de `nm_suite`.
Fue parte de V1 pero es **autónomo** respecto a los closers/comparators/
replay/anti-fraud V1: no invoca `close_visual_key.py`,
`replay_visual_closure.py`, `anti_fraud_scan.py`, `vas_gate.py`,
`vas_engine.py`, `odiff_runner.py`, `spec_generator.py`. Su única
referencia a V1 es un comentario en docstring mencionando
`layered_visual_compare.py` (no invocación).

Por esto, V3.1 lo conserva como **generador transitorio** sujeto a límites
estrictos. La meta a largo plazo es reescribirlo o reemplazarlo, pero eso
no es trabajo de Fase 1A.

## Límites no negociables (redline)

### L1 — Sólo lo invoca `harness/v3/capture_orchestrator.py`

Ningún otro módulo del harness, ni VisualParity Core/CLI, ni agentes, ni
CI pueden invocar `qa/capture_v8.py`.

- `harness/v3/capture_orchestrator.py` (futuro) es el **único** invocador.
- VisualParity Core/CLI no tiene dependencia sobre `qa/capture_v8.py`.
- Agentes no pueden invocar captura directamente; piden captura al
  harness, que la orquesta vía `capture_orchestrator.py`.
- CI no invoca `capture_v8.py` directamente; si necesita capturas, las
  consume del bundle generado por el harness.

### L2 — VisualParity no lo invoca

VisualParity Core/CLI **no puede** invocar `qa/capture_v8.py`. La
separación medición/orquestación es absoluta:

- VisualParity recibe PNGs ya capturados (CANON + ACTUAL).
- VisualParity no orquesta captura.
- VisualParity no conoce `capture_v8.py`, `PyQt6`, `QT_QPA_PLATFORM`,
  `NM_VISUAL_QA`, ni ningún detalle de captura.

### L3 — `--introspect` deshabilitado hasta auditar `vas_introspect.py`

`capture_v8.py` tiene un flag `--introspect` (línea 2879) que habilita
`vas_introspect.audit_tree(win, surface_key)` (línea 2371-2375).
`vas_introspect.py` (549 LOC) no ha sido auditado a profundidad.

- `capture_orchestrator.py` (futuro) **no pasa `--introspect`** en
  invocación por defecto.
- Si un caso futuro requiere VAS introspect, se audita `vas_introspect.py`
  primero, se documenta, y se habilita con flag explícito + registro en
  `capture_provenance.json`.
- Hasta entonces, `--introspect` queda deshabilitado.

## Dependency audit `capture_v8.py` (resumen)

| Item | Resultado |
|---|---|
| LOC | 3089 |
| Imports stdlib | argparse, ast, csv, datetime, hashlib, importlib, json, os, shutil, subprocess, sys, time, unicodedata, pathlib, typing |
| Imports externos | PyQt6 vía importlib dinámico |
| Subprocess | 2 usos: `_git_value()` (git metadata, línea 1661) + child re-launch con `--_child-single` (línea 2795) |
| Referencia a V1 closers/comparators/replay | Sólo en docstring (línea 63 menciona `layered_visual_compare.py` como comentario, no invocación) |
| Importa `vas_introspect` | Sí, condicional (línea 2371, opt-in vía `--introspect`) |
| Invoca `close_visual_key` | No |
| Invoca `replay_visual_closure` | No |
| Invoca `anti_fraud_scan` | No |
| Invoca `vas_gate` | No |
| Invoca `vas_engine` | No |
| Invoca `odiff_runner` | No |
| Invoca `spec_generator` | No |
| Escribe a `_mockup_canonical/` | No |
| Output | `qa/_captures_v8/{...}.png` + `CAPTURE_MANIFEST.json` |

**Conclusión:** `capture_v8.py` es autónomo respecto a V1
closers/comparators/replay. Única dependencia blanda: `vas_introspect`
(opt-in, deshabilitado por defecto en V3.1 hasta auditoría).

## Flujo de captura V3.1 (objetivo, no implementado)

```
1. harness/v3/capture_orchestrator.py recibe surface_key + theme
2. capture_orchestrator.py invoca:
   python qa/capture_v8.py --key <key> --theme <theme> --out-dir qa/_captures_v8
   (sin --introspect)
3. capture_v8.py genera:
   - qa/_captures_v8/<key>.png
   - qa/_captures_v8/CAPTURE_MANIFEST.json
4. capture_orchestrator.py genera:
   - capture_provenance.json (run_id, git_head, mtime, capture_v8_sha256,
     vp_build_sha256_expected, invocation_args)
5. harness/v3/state_assertion.py genera:
   - capture_state_assertion.json (window title, button labels, timer value,
     state fingerprint, captured_at, capture_v8_sha256)
6. capture_orchestrator.py pasa CANON + ACTUAL a VisualParity CLI:
   visualparity compare --canon qa/_mockup_canonical --actual qa/_captures_v8
                       --out vp_report --profile strict --git-head <HEAD>
```

## Estado actual (Fase 0A)

- `qa/capture_v8.py` intacto en `main`.
- `harness/v3/capture_orchestrator.py` no existe (futuro).
- `harness/v3/state_assertion.py` no existe (futuro).
- `capture_provenance.json` schema no definido (futuro, Fase 0B).
- `capture_state_assertion.json` schema no definido (futuro, Fase 0B).
- `--introspect` sigue habilitado en `capture_v8.py` (no se modifica en
  Fase 0A); el límite se aplica a nivel de `capture_orchestrator.py`
  (futuro).

## Riesgos residuales

- **`capture_v8.py` monolito (3089 LOC):** cualquier bug contamina la
  cadena V3.1. Mitigación: `capture_orchestrator.py` valida output
  (PNG existe, MANIFEST válido, no exception) antes de pasar a
  VisualParity.
- **`vas_introspect.py` no auditado:** si se habilita `--introspect` sin
  auditoría, podría introducir vectores no analizados. Mitigación: L3
  (deshabilitado por defecto).
- **Subprocess child re-launch:** `capture_v8.py` línea 2795 lanza un
  child process con `--_child-single`. Si el child falla, el parent
  puede no detectar. Mitigación: `capture_orchestrator.py` verifica
  exit code del parent y existencia del PNG output.
- **Paths Windows en `CAPTURE_MANIFEST.json`:** `capture_v8.py` puede
  heredar paths Windows del entorno. Mitigación: `capture_provenance.json`
  registra `invocation_args` y `git_head` para reproducibilidad.

## Owner decision requerida

Ver `PHASE_0A_DECISIONS.md`:
- #2: `capture_v8.py` conservado como generador transitorio (recomendado: sí).
- #3: `vas_introspect.py` auditoría futura (recomendado: auditar en 0B/1A).
