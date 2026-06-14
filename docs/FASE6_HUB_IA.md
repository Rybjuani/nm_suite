# Fase 6 — Hub IA

## Objetivo (PLAN FASEADO §Fase 6)
- Reemplazar banner amarillo dominante por aviso neutral.
- Reducir ruido de `borrador/generado/editable`.
- Textareas más útiles, flujo claro por bloque y sin contenido inicial cortado.

## Cambios Aplicados

### Banner amarillo → aviso neutral (`shared/components/session.py` · `NMAIDisclaimer`)
- El disclaimer permanente del tab IA ("Borrador generado por IA · requiere validación de un profesional. No constituye diagnóstico.") era una **caja amber/warning** que dominaba la vista y competía con el contenido.
- Ahora es un **aviso neutral**: `background = surface2`, `border = borderSoft`, texto e icono (escudo) en `ink_secondary`. Sigue siempre visible y legible, pero se lee como nota, no como alarma.
- `NMAIDisclaimer` es **Hub-only** (único consumidor: `hub/pacientes_qt.py`) → Suite intacto.

### Reducir ruido borrador/generado/editable (`hub/pacientes_qt.py` · `_mk_ia_meta`)
- Cada uno de los 4 bloques IA (Resumen, Sugerencias, Asignación, Generar tarea) repetía un mono **"generado · editable"** junto al chip "Borrador". Con el banner ya advirtiendo el estado borrador, era redundante ×4.
- `_mk_ia_meta` ahora devuelve un label **vacío** → desaparece el "generado · editable". Cada bloque conserva **un solo cue**: el chip "Borrador" + el botón "Editar" (que ya comunica editabilidad).
- El QLabel vacío se mantiene (0px) para no tocar los ~9 call sites que togglean su visibilidad (cambio acotado y de bajo riesgo).

### Textareas / flujo por bloque (verificado, sin contenido cortado)
- Las áreas de contenido (resumen, sugerencias, asignación, tarea) muestran el texto completo sin recorte inicial (`min_height` adecuados ya existentes).
- Flujo por bloque claro: `Generar` (primario) → contenido → `Editar` / `Guardar como nota` / `Copiar`; en Asignación: `Editar` / `Aprobar y asignar` / `Descartar`.

## Restricciones respetadas
- `NMAIDisclaimer` Hub-only → Suite intacto. Sin tocar tokens ADN.
- API pública de componentes intacta (`test_components_public_api` OK).

## Gates
- `py_compile` OK (2 archivos)
- `ruff check` OK (All checks passed)
- `pytest tests/` → **85 passed**

## Capturas evidencia (inspeccionadas 2026-06-14, light + dark)
| Vista | Resultado |
|---|---|
| `hub-detalle-ia-{dark,light}` | revisado — banner neutral, sin "generado·editable", bloques limpios |
| `hub-detalle-ia-asignacion-{dark,light}` | revisado — banner neutral, flujo Aprobar/Editar/Descartar claro, contenido sin cortar |

## Deuda pendiente exacta
- Ninguna en el alcance de Fase 6. IA resumen y asignación quedan `revisado`.

## Estado
- **CERRADA** — implementación + capturas inspeccionadas + matriz actualizada + doc.
- Próxima: Fase 7 (Suite Base, Acceso y Estado Emocional) — primera fase de Suite.
