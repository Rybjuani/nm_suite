# MICRO_VISUAL_POST_69BF781

Micro-pasada visual posterior a `69bf781`.

## Alcance

- Avisos empty: tabs mas pill/fchip y search integrado visualmente al mismo sistema.
- Timer: `Lectura` y presets/categorias como chips/filtros, sin agrandar el ring.
- Rutina: suavizar boton/check de agregar tarea y centrar mejor el empty light.
- Hub Detalle Activacion: mejorar panel derecho vacio con empty state consistente.

## Fuera de alcance

- No tocar DBT.
- No tocar TCC.
- No tocar Onboarding.
- No tocar Hub Pacientes.
- No tocar DB/sync/build/installers.
- No redisenar layout ni agregar funciones.
- No generar ZIP ni paquete completo de capturas.

## Cambios aplicados

- Avisos:
  - Track de filtros queda compacto, con radio real de 20 px y ancho maximo.
  - Pills activas siguen gramatica suave, sin CTA solido.
  - Search conserva altura/superficie alineada al track.
- Timer:
  - Se agrega `_TimerChip` local para pintar estado activo suave con borde brand.
  - Duraciones y categorias usan el mismo chip local.
  - Ring permanece en 180 px.
- Rutina:
  - Check inline de agregar tarea pasa de `gradient` a `secondary`, con 36x34 px.
  - Empty state se aloja en host expansible con centrado optico y spacer inferior desactivado cuando esta vacio.
- Hub Detalle Activacion:
  - Panel derecho vacio usa `_activation_empty_state`: icon chip compacto + texto existente.
  - No se agregan acciones ni cambios de datos.

## Evidencia focal

Before:

- `qa/_captures_micro_post_69bf781_before/suite-avisos-empty-light-960x600.png`
- `qa/_captures_micro_post_69bf781_before/suite-avisos-empty-dark-960x600.png`
- `qa/_captures_micro_post_69bf781_before/suite-timer-light-960x600.png`
- `qa/_captures_micro_post_69bf781_before/suite-timer-dark-960x600.png`
- `qa/_captures_micro_post_69bf781_before/suite-timer-preset-5min-light-960x600.png`
- `qa/_captures_micro_post_69bf781_before/suite-timer-preset-5min-dark-960x600.png`
- `qa/_captures_micro_post_69bf781_before/suite-timer-preset-45min-light-960x600.png`
- `qa/_captures_micro_post_69bf781_before/suite-timer-preset-45min-dark-960x600.png`
- `qa/_captures_micro_post_69bf781_before/suite-rutina-empty-light-960x600.png`
- `qa/_captures_micro_post_69bf781_before/suite-rutina-empty-dark-960x600.png`
- `qa/_captures_micro_post_69bf781_before/suite-rutina-add-task-light-960x600.png`
- `qa/_captures_micro_post_69bf781_before/suite-rutina-add-task-dark-960x600.png`
- `qa/_captures_micro_post_69bf781_before/hub-detalle-plan-activacion-light-960x600.png`
- `qa/_captures_micro_post_69bf781_before/hub-detalle-plan-activacion-dark-960x600.png`

After:

- `qa/_captures_micro_post_69bf781_after/suite-avisos-empty-light-960x600.png`
- `qa/_captures_micro_post_69bf781_after/suite-avisos-empty-dark-960x600.png`
- `qa/_captures_micro_post_69bf781_after/suite-timer-light-960x600.png`
- `qa/_captures_micro_post_69bf781_after/suite-timer-dark-960x600.png`
- `qa/_captures_micro_post_69bf781_after/suite-timer-preset-5min-light-960x600.png`
- `qa/_captures_micro_post_69bf781_after/suite-timer-preset-5min-dark-960x600.png`
- `qa/_captures_micro_post_69bf781_after/suite-timer-preset-45min-light-960x600.png`
- `qa/_captures_micro_post_69bf781_after/suite-timer-preset-45min-dark-960x600.png`
- `qa/_captures_micro_post_69bf781_after/suite-rutina-empty-light-960x600.png`
- `qa/_captures_micro_post_69bf781_after/suite-rutina-empty-dark-960x600.png`
- `qa/_captures_micro_post_69bf781_after/suite-rutina-add-task-light-960x600.png`
- `qa/_captures_micro_post_69bf781_after/suite-rutina-add-task-dark-960x600.png`
- `qa/_captures_micro_post_69bf781_after/hub-detalle-plan-activacion-light-960x600.png`
- `qa/_captures_micro_post_69bf781_after/hub-detalle-plan-activacion-dark-960x600.png`

## Checklist visual

| Superficie | Criterio | Estado |
|---|---|---|
| Avisos empty | Tabs dejan de verse como barra rectangular gigante y conviven con search como controles pill. | PASS |
| Timer | `Lectura` no parece CTA principal; play conserva jerarquia primaria. | PASS |
| Timer | Presets/duraciones y categorias comparten gramatica chip/filtro. | PASS |
| Timer | Ring no se agranda. | PASS |
| Rutina add | Check inline queda suave y subordinado al input. | PASS |
| Rutina empty | Empty light queda centrado opticamente. | PASS |
| Hub Detalle Activacion | Panel derecho vacio usa icon chip + texto existente, sin nuevas funciones. | PASS |

## Validacion de apoyo

- `ruff check app/modules/avisos_qt.py app/modules/timer_qt.py app/modules/rutina_qt.py hub/plan_terapeutico.py tests/test_avisos_visual_contract.py tests/test_timer_visual_contract.py tests/test_rutina_visual_contract.py tests/test_hub_visual_contract.py`
- `python -m pytest tests/test_avisos_visual_contract.py tests/test_timer_visual_contract.py tests/test_rutina_visual_contract.py tests/test_hub_visual_contract.py -q`
- `git diff --check`

Resultado:

- Ruff: OK.
- Pytest focal: 17 passed.
- `git diff --check`: OK.

Ruff/tests/probe son apoyo tecnico; el cierre visual esta basado en before/after focal.
