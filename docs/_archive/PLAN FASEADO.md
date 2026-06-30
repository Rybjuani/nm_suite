# Plan Visual Faseado — NeuroMood Suite + Hub

## Resumen
- Cerrar la deuda visual con fases independientes, transferibles y cerrables por commit.
- Regla central: **Hub necesita compactación y mejor uso del espacio**, no aumentos globales de textos, botones, cards o paddings.
- Suite y Hub mantienen densidades distintas: `Suite comfortable` y `Hub professional compact`.
- Si queda cualquier deuda del alcance, el estado global del plan es `parcial`.

## Fase 0 — V8 Línea Base Y Matriz
- Inventariar todas las vistas y estados existentes en código y cruzarlos contra recetas V8 actuales.
- Ampliar `qa/capture_v8.py` para cubrir estados faltantes: `actividades-empty`, `avisos-empty`, `recuperar-acceso`, `evolucion-monthly`, éxito real TCC y vacíos deterministas.
- Generar baseline light/dark de todas las vistas cubiertas.
- Crear matriz por fila: producto, vista, estado, tema, resolución, receta, captura, inspección manual, resultado y deuda pendiente.
- El commit de fase debe incluir harness y matriz; las imágenes baseline pueden quedar fuera del repo si son pesadas o están ignoradas.
- Regla: contar capturas no equivale a cobertura; solo cuenta una fila si la receta reproduce el estado correcto y la captura fue inspeccionada.
- Cierre: commit QA + matriz inicial con estados `revisado`, `pendiente`, `parcial` o `bloqueado`.

## Fase 1 — Contrato Visual Y Densidades
- Definir tokens/componentes base para `Suite comfortable` y `Hub professional compact`.
- Prohibición: ningún cambio compartido puede agrandar simultáneamente Hub y Suite; si una escala degrada un producto, crear variante por densidad.
- Separar roles visuales: tabs, subtabs, filtros, badges, chips, botones, inputs, textareas, scrollbars y estados disabled/focus.
- Cierre: commit de sistema visual comparado contra baseline Fase 0.

## Fase 2 — Hub Shell Y Navegación
- Compactar sidebar expandida y mejorar colapsada con iconos legibles, tooltips y footer limpio.
- Reducir chrome/header y header de paciente para recuperar viewport.
- Resolver acumulación sidebar + tabs + subtabs sin agrandar controles globalmente.
- Cierre: commit + evidencia light/dark de dashboard, pacientes, detalle y sidebar colapsada.

## Fase 3 — Hub Dashboard, Pacientes Y Personalización
- Dashboard: KPIs compactos, menos vacío y métricas jerarquizadas.
- Pacientes: filas escaneables, metadatos/sparklines legibles y acción quitar paciente clara con tono danger.
- Personalización/editor: selección primary consistente, paneles integrados al Hub, acciones alineadas y sin scrollbars invasivas.
- Cierre: commit + matriz actualizada.

## Fase 4 — Hub Resumen Y Registros
- Resumen: foco principal claro; corregir glifo inválido junto a `6.4 /10`; legal, nota, ánimo y perfil sin competir.
- Registros: gráfico menos dominante, porcentaje circular explicado o integrado, lista visible sin scroll inicial innecesario.
- Cierre: commit + capturas light/dark de resumen, registros top y registros bottom.

## Fase 5 — Hub Plan Terapéutico
- Reorganizar subtabs del Plan para lectura compacta.
- Equilibrar formularios, listados y previews; evitar paneles enormes vacíos.
- Acercar acciones a sus campos y diferenciar `Agregar`, `Asignar`, `Restablecer` y estados vacíos.
- Cierre: commit + evidencia light/dark de recordatorios, timer, rutina y activación.

## Fase 6 — Hub IA
- Reemplazar banner amarillo dominante por aviso neutral.
- Reducir ruido de `borrador/generado/editable`.
- Textareas más útiles, flujo claro por bloque y sin contenido inicial cortado.
- Cierre: commit + evidencia light/dark de IA resumen y asignación.

## Fase 7 — Suite Base, Acceso Y Estado Emocional
- Home: hero/cards menos altos, estados legibles y nombre capitalizado.
- Onboarding/Ajustes/PIN/Bloqueo/Recuperar acceso: familia visual común, legal legible, acciones claras y contraste correcto.
- Ánimo/Evolución: sin falso valor inicial `0`, chips como selección real, sparse/empty states compactos y métricas coherentes.
- Cierre: commit + evidencia light/dark.

## Fase 8 — Suite TCC
- Wizard estable, menos vacío, navegación equilibrada.
- `Anterior` como secondary real; CTA final distinguible.
- Éxito determinista sin toast de error.
- Mantener intensidad solo como `/10`.
- Cierre: commit + evidencia light/dark de pasos y éxito.

## Fase 9 — Suite Respiración Y Timer
- Reducir superficies sobredimensionadas.
- Controles reconocibles y proporcionados.
- Historial sin corte inicial ni scrollbar dominante.
- Evitar métricas que parezcan biométricas reales si no lo son.
- Cierre: commit + evidencia light/dark de idle, running/paused, presets e historial.

## Fase 10 — Suite Rutina, Actividades Y Avisos
- Rutina: menos columnas comprimidas, checkboxes y acciones legibles, empty state coherente.
- Actividades: cards menos apretadas, `No pude` y `Hice` con jerarquía equivalente, filtros y empty state deterministas.
- Avisos: eliminar duplicación visual `Completado`/`Hecho`, filtros/badges/acciones claros, listas cortas sin vacío absurdo.
- Cierre: commit + evidencia light/dark de estados con contenido, filtrados y vacíos.

## Fase 11 — Regresión Final Y Cierre
- Ejecutar `compileall`, `ruff`, `pytest`, smoke runtime Suite, smoke runtime Hub, `python build_neuromood.py --dry-run`.
- Ejecutar V8 completo con sintaxis soportada: `python qa/capture_v8.py --all --clean --theme both --out-dir C:\Users\nosom\Desktop\NM_Review_after_visual_fix`.
- Revisar manualmente la matriz completa.
- Estado global: `terminada` solo si todas las fases, recetas, capturas y verificaciones están cerradas; `parcial` si queda cualquier pendiente; `bloqueada` solo con bloqueo externo documentado.

## Plantilla De Handoff
- Fase retomada:
- Último commit:
- Estado:
- Archivos tocados:
- Vistas/estados cubiertos:
- Recetas V8 agregadas o modificadas:
- Capturas revisadas:
- Deuda pendiente exacta:
- Comandos ejecutados y resultado:
- Bloqueos:
- Próximo paso recomendado:
