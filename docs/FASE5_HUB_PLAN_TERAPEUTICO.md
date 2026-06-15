# Fase 5 — Hub Plan Terapéutico

## Objetivo (PLAN FASEADO §Fase 5)
- Reorganizar subtabs del Plan para lectura compacta.
- Equilibrar formularios, listados y previews; evitar paneles enormes vacíos.
- Acercar acciones a sus campos y diferenciar `Agregar`, `Asignar`, `Restablecer` y estados vacíos.

## Cambios Aplicados

### Estados vacíos centrados — evitar paneles enormes vacíos (`hub/plan_terapeutico.py`)
- **Problema:** los 4 subtabs (Recordatorios, Temporizador, Rutina, Activación) tienen un panel-listado a la derecha que, sin ítems propios, mostraba un `QLabel` suelto **arriba-izquierda** dentro de una card grande → el panel se veía "roto"/vacío.
- **Fix (v1):** `_empty_hint_label` devolvía un bloque centrado (h+v) con `minimumHeight 220` + stretches.
- **Refinamiento (v2, 2026-06-14):** a 960×600 el panel derecho hereda la altura del formulario (muy alto), así que el bloque de 220px hacía flotar el mensaje en el centro de un **panel enorme y vacío**. Ahora `_empty_hint_label` es una **banda compacta** (`sizePolicy` horizontal=Expanding / vertical=Maximum, `minimumHeight 96`, `maximumHeight 132`) centrada en horizontal y **anclada bajo el encabezado** (la lista usa `AlignTop`): se lee como "lista vacía" sin reservar un vacío gigante. Un solo helper → arregla los **5 estados vacíos**:
  - Recordatorios: "…no tiene mensajes propios." y "Sin horarios configurados aún."
  - Temporizador: "…no tiene temporizadores propios."
  - Rutina: "Sin tareas asignadas aún."
  - Activación: "Sin actividades personalizadas aún."
- `_empty_hint` y `_empty_hint_label` actualizan su anotación de retorno a `QWidget`.

### Subtabs — lectura compacta (sin cambios de copy, por decisión owner)
- Los 4 subtabs ya usan el estilo **segmentado compacto** (`stylesheet_tabwidget_segmented` + `font-size 10px`, `padding 3px 7px`) que entra los 4 nombres en una fila a 960px sin scroll.
- Los nombres se mantienen **completos** ("Recordatorios de Bienestar", etc.) por decisión documentada del owner v1.0 (el profesional ve el mismo nombre que el paciente). No se renombraron para no contradecirla; la compactación es vía densidad del segmento, no abreviatura.

### Acciones diferenciadas y cerca de sus campos (verificado, ya correcto)
- `Agregar` / `Asignar` → botón **primario gradient** ubicado **directamente debajo** de su formulario (cerca del campo).
- `Restablecer por defecto` → **outline** en el header del panel-listado (resetea la lista asignada, su contexto natural), con confirmación `nm_confirm`.
- Las tres familias quedan visualmente distinguibles; no requirió cambios.

## Restricciones respetadas
- Cambio acotado a `hub/plan_terapeutico.py` (Hub-only) → Suite intacto.
- Sin tocar tokens ni componentes compartidos (`test_token_parity`, `test_components_public_api` OK).

## Gates
- `py_compile` OK
- `ruff check` OK (All checks passed)
- `pytest tests/` → **85 passed**

## Capturas evidencia (inspeccionadas 2026-06-14, light + dark; re-capturadas tras v2)
| Vista | Resultado |
|---|---|
| `hub-detalle-plan-{dark,light}` (Recordatorios) | revisado — vacíos compactos bajo encabezado, acciones diferenciadas |
| `hub-detalle-plan-activacion-{dark,light}` | revisado — "Sin actividades…" banda compacta |
| `hub-detalle-plan-rutina-{dark,light}` | revisado — "Sin tareas asignadas…" banda compacta |
| `hub-detalle-plan-timer-{dark,light}` | revisado — "…no tiene temporizadores…" banda compacta |

## Deuda pendiente exacta
- Ninguna en el alcance de Fase 5. Las 4 subtabs quedan `revisado`.
- (Tensión registrada: el plan pide "subtabs más compactos" pero el owner v1.0 fijó nombres completos; se priorizó la decisión del owner + densidad del segmento.)

## Estado
- **CERRADA** — implementación + capturas inspeccionadas + matriz actualizada + doc.
- Próxima: Fase 6 (Hub IA).
