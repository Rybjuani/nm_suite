# C2-SUITE-CRITICAL

Cluster ejecutado despues de `C1-PRIMITIVES-SYSTEM`.

## Alcance

- Resolver los P0/P1 criticos de Suite listados para C2.
- Tocar solo DBT Biblioteca/Cierre/Historial, Registro TCC step1 y Onboarding default/error.
- Eliminar DBT Historial del flujo UI V2 y alinear QA/tests.
- No tocar Hub, Actividades, Rutina, Timer, Avisos, PLAN_MIGRACION_UI_V2.md ni C5/C6.
- No generar ZIP.
- No regenerar el paquete completo de capturas.

## Cambios aplicados

- `ModuloDBT`
  - Biblioteca usa cards con barra superior reservada en layout, no pintada sobre texto.
  - Grid de biblioteca pasa a tracks regulares de 3 columnas, sin scrollbar horizontal.
  - Navegacion DBT queda en `Ahora` y `Biblioteca`; se elimina `Historial`.
  - Se remueve la receta QA `dbt-history` y quedan 96 capturas en el listado total.
  - Modal de cierre reduce escala de ratings, jerarquia de evaluacion y fuerza del scrim.
- `Registro TCC`
  - Emotion tiles separan icono/label con cajas fijas y altura estable.
  - Estado seleccionado usa borde/superficie consistente, sin artefacto vertical.
  - Slider queda contenido y CTAs reducen peso/ancho.
- `Onboarding`
  - Inputs compactos en 520x600.
  - Consentimiento integra checkbox y texto legal dentro de la misma card.
  - Checkbox se pinta localmente con check visible en dark/light.
  - El dialog evita focus inicial accidental y conserva footer/acciones visibles.

## Evidencia focal

Before focal minimo:

- `qa/_captures_c2_suite_critical_before/suite-dbt-library-light-960x600.png`
- `qa/_captures_c2_suite_critical_before/suite-dbt-library-dark-960x600.png`
- `qa/_captures_c2_suite_critical_before/suite-dbt-practice-closure-light-960x600.png`
- `qa/_captures_c2_suite_critical_before/suite-dbt-practice-closure-dark-960x600.png`
- `qa/_captures_c2_suite_critical_before/suite-dbt-history-light-960x600.png`
- `qa/_captures_c2_suite_critical_before/suite-dbt-history-dark-960x600.png`
- `qa/_captures_c2_suite_critical_before/suite-registro-step1-emotion-light-960x600.png`
- `qa/_captures_c2_suite_critical_before/suite-registro-step1-emotion-dark-960x600.png`
- `qa/_captures_c2_suite_critical_before/suite-onboarding-light-520x600.png`
- `qa/_captures_c2_suite_critical_before/suite-onboarding-dark-520x600.png`
- `qa/_captures_c2_suite_critical_before/suite-onboarding-error-light-520x600.png`
- `qa/_captures_c2_suite_critical_before/suite-onboarding-error-dark-520x600.png`

After focal minimo:

- `qa/_captures_c2_suite_critical_after/suite-dbt-library-light-960x600.png`
- `qa/_captures_c2_suite_critical_after/suite-dbt-library-dark-960x600.png`
- `qa/_captures_c2_suite_critical_after/suite-dbt-practice-closure-light-960x600.png`
- `qa/_captures_c2_suite_critical_after/suite-dbt-practice-closure-dark-960x600.png`
- `qa/_captures_c2_suite_critical_after/suite-registro-step1-emotion-light-960x600.png`
- `qa/_captures_c2_suite_critical_after/suite-registro-step1-emotion-dark-960x600.png`
- `qa/_captures_c2_suite_critical_after/suite-onboarding-light-520x600.png`
- `qa/_captures_c2_suite_critical_after/suite-onboarding-dark-520x600.png`
- `qa/_captures_c2_suite_critical_after/suite-onboarding-error-light-520x600.png`
- `qa/_captures_c2_suite_critical_after/suite-onboarding-error-dark-520x600.png`

Nota: no hay after de `dbt-history` porque la pantalla/receta fue eliminada por alcance C2.
Estas capturas son evidencia focal local, no paquete final C6.

## Resultado visual

Decision C2: `PASS_FOR_CLUSTER_SCOPE`.

- DBT Biblioteca: barras ya no pisan titulos, el grid queda regular y `Historial` desaparece.
- DBT Cierre: modal mantiene funcion con ratings mas contenidos, botones secundarios menos pesados y CTA claro.
- Registro TCC: iconos y labels no se superponen; el selected state queda limpio.
- Onboarding: consentimiento queda agrupado, checkbox visible y texto legal con scroll local deliberado cuando no entra completo.

## Defectos trazados

| Defecto | Estado C2 | Nota |
|---|---|---|
| V2-P0-001 | Resuelto | Barra de skill ahora reserva alto en layout; ningun titulo queda tapado. |
| V2-P0-002 | Resuelto | Emotion tiles separan icono/label y evitan invasion de texto. |
| V2-P0-003 | Resuelto | Legal real queda dentro de card con scroll local visible; no hay corte roto ni checkbox perdido. |
| V2-P0-005 | Resuelto | DBT Historial eliminado de tabs, stack, recipe QA y tests. |
| V2-P1-019 | Resuelto | Navegacion DBT compacta de dos tabs, sin Historial. |
| V2-P1-020 | Resuelto | Filtros de familia quedan como pills/fchips desde C1 y se verifican en C2. |
| V2-P1-021 | Resuelto | Grid regular de 3 columnas, sin scrollbar horizontal ni columna incompleta perceptual. |
| V2-P2-004 | Resuelto | Descripciones dark quedan legibles sin volverse primarias. |
| V2-P2-005 | Resuelto | Meta row separa duracion y practica guiada con aire. |
| V2-P1-022 | Resuelto | Modal de cierre baja escala y mejora jerarquia. |
| V2-P1-023 | Resuelto | Ratings 0-10 reducidos a 32 px y no dominan la modal. |
| V2-P1-024 | Resuelto | Evaluacion queda secundaria frente a `Guardar practica`. |
| V2-P2-006 | Resuelto | Scrim atenua el fondo sin endurecerlo. |
| V2-P1-025 | Resuelto | Checkbox custom visible y alineado en dark/light. |
| V2-P1-026 | Resuelto | Fila legal/checkbox queda integrada a la card de consentimiento. |
| V2-P1-027 | Resuelto | Footer y acciones permanecen visibles en 520x600. |
| V2-P1-028 | Resuelto | Jerarquia entre `Crear cuenta` e `Iniciar sesion` queda diferenciada. |
| V2-P1-029 | Resuelto | Inputs compactos reducen compresion del consentimiento/footer. |
| V2-P2-007 | Resuelto | Estado inicial evita focus accidental con apariencia de error. |
| V2-P2-008 | Resuelto | Lockup mantiene integracion visual en ambos temas. |
| V2-P1-030 | Resuelto | Card principal de Registro sube y reduce vacio superior. |
| V2-P1-031 | Resuelto | Emotion grid se lee como opciones refinadas, no cajas rigidas. |
| V2-P1-032 | Resuelto | Selected state no tiene linea vertical rara. |
| V2-P1-033 | Resuelto | Slider queda contenido y subordinado al flujo. |
| V2-P2-009 | Resuelto | CTA `Siguiente` mantiene jerarquia sin ancho excesivo. |

No quedan P0/P1 de C2 diferidos.

## Validacion tecnica de apoyo

- `python -m pytest tests/test_dbt_visual_contract.py tests/test_component_visual_contract.py tests/test_registro_tcc_visual_contract.py tests/test_onboarding_visual_contract.py tests/test_mockup_qa_tools.py -q`
- `ruff check app/modules/dbt_qt.py app/modules/registro_tcc_qt.py app/onboarding_qt.py qa/capture_v8.py tests/test_dbt_visual_contract.py tests/test_component_visual_contract.py tests/test_registro_tcc_visual_contract.py tests/test_onboarding_visual_contract.py tests/test_mockup_qa_tools.py`
- `git diff --check`
- `python qa/capture_v8.py --list`

Estos checks son apoyo tecnico; el cierre del cluster depende del checklist visual trazado.

## Diff stat

`git diff --cached --stat` antes del commit:

```text
.../20260622_005603_C2_SUITE_CRITICAL/EPISODE.md   | 157 ++++++++++++
.../VISUAL_CHECKLIST.md                            |  66 +++++
app/modules/dbt_qt.py                              | 272 +++++----------------
app/modules/registro_tcc_qt.py                     |  38 +--
app/onboarding_qt.py                               | 131 +++++-----
qa/capture_v8.py                                   |  17 --
tests/test_component_visual_contract.py            |  19 +-
tests/test_dbt_visual_contract.py                  |  14 +-
tests/test_mockup_qa_tools.py                      |  10 +-
tests/test_onboarding_visual_contract.py           |  14 ++
tests/test_registro_tcc_visual_contract.py         |  24 ++
11 files changed, 441 insertions(+), 321 deletions(-)
```

## Archivos tocados

- `app/modules/dbt_qt.py`
- `app/modules/registro_tcc_qt.py`
- `app/onboarding_qt.py`
- `qa/capture_v8.py`
- `tests/test_component_visual_contract.py`
- `tests/test_dbt_visual_contract.py`
- `tests/test_mockup_qa_tools.py`
- `tests/test_onboarding_visual_contract.py`
- `tests/test_registro_tcc_visual_contract.py`
- `agent_harness/episodes/20260622_005603_C2_SUITE_CRITICAL/EPISODE.md`
- `agent_harness/episodes/20260622_005603_C2_SUITE_CRITICAL/VISUAL_CHECKLIST.md`

## Handoff

Siguiente cluster en orden segun plan: `C4-HUB-CRITICAL`.

Deuda restante fuera de C2:

- C3-SUITE-MODULES: Actividades, Rutina, Timer, Avisos.
- C4-HUB-CRITICAL: Hub Pacientes y Hub Detalle Activacion.
- C5-MISSING-SCREENS-AUDIT: pantallas no auditadas por owner.
- C6-FINAL-EVIDENCE: paquete final post-fix, ZIP y capturas completas.
