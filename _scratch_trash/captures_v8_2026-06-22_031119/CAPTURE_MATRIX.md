# Matriz Baseline V8

- Generada: 2026-06-22T03:11:18
- Filas: 2
- Resultados: parcial=2
- Inspeccion manual: pendiente hasta revisar captura por captura.

| producto | vista | estado | tema | resolucion | receta | captura | inspeccion manual | resultado | deuda pendiente |
|---|---|---|---|---|---|---|---|---|---|
| hub | pacientes-empty | Pacientes empty state | dark | 960x600 | navigate:pacientes > call:_clear_hub_patients > navigate:pacientes > drain:8 > capture:pacientes-empty | hub-pacientes-empty-dark-960x600.png | pendiente | parcial | flags=REQUIRES_DATA_STATE ; notes=Empty patients view depends on real data absence, not only QA in-memory clearing. |
| hub | pacientes-empty | Pacientes empty state | light | 960x600 | navigate:pacientes > call:_clear_hub_patients > navigate:pacientes > drain:8 > capture:pacientes-empty | hub-pacientes-empty-light-960x600.png | pendiente | parcial | flags=REQUIRES_DATA_STATE ; notes=Empty patients view depends on real data absence, not only QA in-memory clearing. |
