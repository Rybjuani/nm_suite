# Fix Plan - UI V2 Owner Visual Audit

Este plan reemplaza el cierre visual de E5. No reemplaza los gates tecnicos: los degrada a
soporte. Ningun cluster puede cerrar con "tests verdes" solamente.

## Decisiones bloqueadas

- `c0c692e` = cierre tecnico exitoso, cierre visual fallido. No es rollback.
- DBT Historial se planifica para eliminacion dentro de UI V2.
- Copy legal/clinico/producto gana en texto; mockup/sistema gana en composicion visual.
- No usar diferencias de texto como excusa para dejar layout, densidad, clipping o empty
  states rotos.
- No generar ZIP ni 98 capturas al inicio.
- Captura focal minima solo si falta evidencia para un cluster/pantalla.

## Reglas de cierre por cluster

Cada cluster debe cerrar con:

1. Captura focal **before/after** del cluster.
2. Checklist visual trazado por pantalla/estado/tema.
3. Defectos P0/P1 del cluster resueltos o diferidos explicitamente con justificacion owner.
4. `ruff`, tests y probe solo como apoyo tecnico.
5. `git diff --stat`, archivos tocados, deuda restante y handoff.

Prohibido cerrar con:

- "pytest verde" como unica evidencia.
- "capture_v8 genero PNG" como aprobacion visual.
- SSIM/MAD como gate final.
- Revision visual sin checklist.

## C0-GATE-HARNESS

**Objetivo:** invalidar E5 como cierre visual y definir el nuevo gate trazado.

**Baja:** V2-P0-006, V2-P0-007, V2-P0-008.

**Cambios esperados:**

- Actualizar docs/harness para separar:
  - evidencia tecnica: probe, pytest, capture manifest;
  - aprobacion visual: checklist owner/humano por pantalla/tema/estado.
- Crear formato de checklist visual con campos: pantalla, estado, tema, defectos esperados,
  resultado, evidencia before/after, reviewer, decision.
- Registrar que `c0c692e` no se revierte; simplemente no es cierre visual.

**Validacion de cierre:** checklist template existe y E5 queda marcado como fallido
visualmente, no rollback.

## C1-PRIMITIVES-SYSTEM

**Objetivo:** unificar gramatica visual compartida antes de fixes locales.

**Baja:** V2-P1-047 a V2-P1-051 y apoya C2/C3/C4.

**Cambios esperados:**

- Normalizar variantes y uso de botones, tabs, fchips, badges, checkbox, cards y empty
  states.
- Definir que Suite y Hub pueden tener densidades distintas, pero no familias visuales
  incompatibles.
- Agregar tests solo donde midan algo real: clipping, overlap, size bounds, visible rects.

**No hacer:** redisenar pantallas completas dentro de este cluster.

**Validacion de cierre:** before/after en una pantalla representante por primitiva
afectada y checklist que confirme convergencia visual.

## C2-SUITE-CRITICAL

**Objetivo:** resolver los P0/P1 criticos de Suite que invalidan UI V2.

**Baja:** V2-P0-001 a V2-P0-003, V2-P0-005, V2-P1-019 a V2-P1-033, V2-P2-004 a V2-P2-009.

**Pantallas:**

- DBT Biblioteca: barras/titulos, tabs/fchips, grid, contraste, meta row, scrollbar.
- DBT Cierre: escala modal, ratings, botones de evaluacion, CTA, overlay.
- DBT Historial: eliminar tab/pantalla y limpiar recetas/tests/targets afectados.
- Registro TCC: emotion cards, selected state, slider, top spacing, CTA.
- Onboarding: legal real legible, checkbox, footer, botones, inputs, focus inicial, lockup.

**Validacion de cierre:**

- Capturas focales before/after: DBT library light/dark, DBT closure light/dark,
  Registro step1 light/dark, Onboarding default+error light/dark.
- Checklist muestra P0 en cero para estas pantallas.

## C3-SUITE-MODULES

**Objetivo:** resolver pantallas Suite con deuda de sistema/densidad que owner marco como
no premium o incoherentes.

**Baja:** V2-P1-014 a V2-P1-018, V2-P2-002, V2-P2-003, V2-P1-034 a V2-P1-046, V2-P2-010.

**Pantallas:**

- Actividades: fchips, card balance, badges, `Hecho`, `No pude/Hice`, footer, icon chips.
- Rutina: checkbox, add task, franjas, progress header, alineacion, empty light.
- Timer: ring/card scale, presets, category chips, empty state.
- Avisos: tabs, search integration, empty layout, icon/spacing.

**Validacion de cierre:**

- Capturas focales before/after por pantalla y estado clave.
- Copy de producto puede permanecer en Timer/Avisos si composicion y patron visual quedan
  correctos.

## C4-HUB-CRITICAL

**Objetivo:** resolver Hub Pacientes y Hub Detalle Activacion.

**Baja:** V2-P0-004, V2-P1-001 a V2-P1-013, V2-P2-001.

**Pantallas:**

- Hub Pacientes: corte de ultima fila, badge, scrollbar, columnas, densidad, avatares,
  header action, usage rings.
- Hub Detalle Activacion: PDF/Resumen IA/Completar IA, tabs, formulario, panel empty,
  cards/radius/shadow.

**Validacion de cierre:**

- Capturas focales before/after: pacientes light/dark, detalle-plan-activacion light/dark.
- P0 de corte de fila resuelto: ninguna fila queda parcialmente visible de forma accidental.

## C5-MISSING-SCREENS-AUDIT

**Objetivo:** auditar pantallas que owner no reviso y agregar defectos antes de corregirlos.

**Regla:** no ejecutar 98 capturas. Usar evidencia existente si alcanza; si no, captura focal
minima por pantalla/tema del cluster.

**Pantallas minimas a revisar:**

- Home, Animo, Respiracion.
- DBT Ahora y STOP.
- Registro TCC pasos 2/3/success.
- Recuperar acceso.
- Hub Detalle resumen/registros/timer/rutina y Textos globales.
- Estados secundarios: Actividades filtered/empty/marked, Rutina add/all-completed,
  Timer running/paused/presets, Avisos activos/search/completed.

**Salida:** append al `DEFECT_LEDGER.md` con IDs nuevos o declaracion "sin defecto visual
accionable" por pantalla revisada.

## C6-FINAL-EVIDENCE

**Objetivo:** evidencia final post-fix, no baseline inicial.

**Pasos:**

1. `.\.venv\Scripts\python.exe qa\runtime_live_probe.py --all --theme both`.
2. `.\.venv\Scripts\python.exe -m pytest tests/`.
3. `.\.venv\Scripts\python.exe qa\capture_v8.py --all --theme both --clean`.
4. Generar paquete ZIP en Desktop con capturas finales, manifest, indice, comandos, HEAD,
   estado git y checklist final.

**Criterio de cierre:** no hay P0/P1 abiertos sin diferimiento owner; checklist visual final
trazado y paquete auditable generado.

## Orden recomendado

1. C0-GATE-HARNESS.
2. C1-PRIMITIVES-SYSTEM.
3. C2-SUITE-CRITICAL.
4. C4-HUB-CRITICAL.
5. C3-SUITE-MODULES.
6. C5-MISSING-SCREENS-AUDIT.
7. C6-FINAL-EVIDENCE.

El orden prioriza solapes/cortes y gate roto antes de refinamiento amplio.
