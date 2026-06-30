# Editor Global de Textos - FASE 0

## Estado base

- Rama creada desde `main` limpio: `codex/editor-global-textos-suite`.
- Commit base: `432d74b` (`feat(suite): TCC Otro placeholder (setPlaceholderText) + Timer empty compactado/centrado`).
- La eliminacion de la antigua configuracion global ya estaba integrada en `2033976` y mergeada en `b778bf7`.
- `git status` estaba limpio antes de iniciar la rama.

## Verificacion de la pantalla vieja

- No existe `hub/config_global_suite.py`.
- No existe `hub/editors/text_overrides_editor.py`.
- No existe `suite_text_preview.py`.
- No existe `_CloneDB`.
- `hub/main_qt.py` no importa `app.modules`.
- El menu del Hub ya no expone vistas globales de Presets/Textos/IA; la configuracion por paciente vive en Detalle.

## Restos corregidos en esta fase

- Docstring de `shared/text_overrides.py`, para marcarlo como aplicador legacy transitorio.
- Docstring del Timer, para reemplazar la mencion a un clon por fixtures QA aislados.
- Los documentos historicos permanecen en su version base de `432d74b`; no forman parte de esta correccion.

## Restos conservados deliberadamente

- `shared/text_overrides.py`.
- `tests/test_text_overrides.py`.
- Los imports de `apply_overrides()` en Suite.

Se conservan porque todavia hay consumidores reales antes de FASE 2. Retirarlos ahora cortaria la compatibilidad de textos existente sin haber migrado todas las pantallas a claves semanticas. La limpieza total queda diferida a FASE 6, tal como pide el plan.

## Temporizador

El fix real del estado vacio del Temporizador sigue intacto:

- `app/modules/timer_qt.py` conserva `NMEmptyState("timer", "Sin actividades asignadas", ...)`.
- El modulo sigue sin fallback a presets globales/locales cuando no hay asignaciones `patient:<id>`.
- No se tocaron layouts ni comportamiento clinico del Temporizador en esta fase.

## Resultado

FASE 0 deja una base auditable para construir el catalogo contractual sin clones, previews ni descubrimiento visual de widgets desde el Hub.
