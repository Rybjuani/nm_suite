# Plan de modularizacion de componentes compartidos

## Objetivo

Reducir de forma segura `shared/components_qt.py`, ordenar `shared/components/`,
eliminar dependencias circulares, mantener `shared.theme` como unica fuente de
datos visuales y lograr que los cambios compartidos se propaguen a Suite y Hub
sin modificar apariencia ni comportamiento.

Este plan no ejecuta ninguna fase. Cada fase debe ser un cambio independiente,
con commit propio, gates completos, smoke runtime minimo y rollback claro.

## Alcance de ejecucion

- Fases 0-5: proyecto de modularizacion mecanica. Se limitan a contratos,
  dependencias, extraccion de `ThemeManager`, empaquetado, facades e imports.
  No deben cambiar apariencia, estilos, tokens, geometria, copy, navegacion ni
  comportamiento.
- Fases 6-8: fuera de esta ejecucion. Quedan como proyecto posterior de
  consolidacion visual y reduccion de estilos duplicados, a planificar y aprobar
  por separado cuando la modularizacion mecanica este estable.

## Estado actual auditado

- `shared/components_qt.py` concentra 101 clases, helpers de layout, widgets,
  dialogs, charts, inputs, navegacion y componentes de Suite/Hub.
- `shared/components/` contiene solo `__init__.py`, que reexporta desde
  `shared.components_qt` para compatibilidad.
- La mayoria de consumidores importan directamente desde
  `shared.components_qt`, especialmente `app/main_qt.py`, `app/home_qt.py`,
  `app/modules/*_qt.py`, `hub/main_qt.py`, `hub/pacientes_qt.py`,
  `hub/plan_terapeutico.py`, `hub/personalizacion_global.py` y QA.
- Hay un ciclo arquitectonico a retirar por fases:
  `shared.theme_qt` importa `ThemeManager` desde `shared.components_qt`, y
  `shared.components_qt` importa muchos helpers desde `shared.theme_qt`.
- `shared.theme` ya es la fuente unica de datos visuales. `shared.theme_qt` debe
  seguir siendo adaptador Qt/helper runtime, y `shared.design_tokens` debe seguir
  siendo adaptador de compatibilidad.
- Hay estilos locales duplicados en pantallas de Suite/Hub mediante
  `setStyleSheet`, `v3c`, `C`, `stylesheet_*` y QSS inline. Esos deben migrarse
  despues de los movimientos mecanicos, nunca antes.

## Reglas globales

- No cambiar colores, tipografia, spacing, radios, tamanos, sombras, copy visible
  ni layout intencional durante fases mecanicas.
- Mantener import paths existentes hasta que todos los consumidores reales hayan
  migrado.
- `shared/components_qt.py` debe quedar como facade de compatibilidad durante la
  transicion, no como archivo borrado de golpe.
- No mover logica clinica, DB, sync, auth, onboarding, persistencia ni navegacion.
- No dividir `shared.theme`: los datos visuales permanecen en `shared.theme`.
- `shared/theme_manager.py` no puede importar `shared.theme_qt`,
  `shared.components` ni `shared.components_qt`. Debe ser un modulo pequeno de
  senales/singleton, independiente de implementaciones de componentes.
- Todo commit debe compilar, pasar tests y permitir arranque/cierre de Suite y Hub.
- Si una fase descubre dependencia nueva no auditada, se detiene la fase y se
  ajusta el plan antes de tocar codigo.

## Gates base para todas las fases

- `git diff --check`
- `.\.venv\Scripts\python.exe -m py_compile` sobre Python modificados
- `.\.venv\Scripts\python.exe -m ruff check` sobre Python modificados
- `.\.venv\Scripts\python.exe -m pytest -q`
- Smoke imports:
  `shared.theme`, `shared.design_tokens`, `shared.theme_qt`,
  `shared.components`, `shared.components_qt`
- Smoke runtime minimo:
  `.\.venv\Scripts\python.exe qa\runtime_live_probe.py --app suite --view home --theme dark`
- Smoke runtime minimo:
  `.\.venv\Scripts\python.exe qa\runtime_live_probe.py --app hub --view dashboard --theme dark`
- `qa/capture_v8.py --all` queda reservado para regresion final completa, no para
  cada fase.

## Fase 0 - Inventario ejecutable sin cambios visuales

Alcance:
- Crear tests de inventario que documenten imports publicos actuales sin fijar
  valores visuales.
- Medir que `shared.components` y `shared.components_qt` exporten los mismos
  nombres publicos esperados mientras dure la compatibilidad.
- No mover clases todavia.

Archivos:
- `tests/test_components_public_api.py`
- `shared/components/__init__.py`
- `shared/components_qt.py`

Cambios permitidos:
- Agregar prueba de API publica.
- Agregar `__all__` explicito en `shared/components_qt.py` si falta y si se
  deriva de exports actuales.

Riesgos:
- Congelar accidentalmente nombres privados como API.
- Bloquear una limpieza posterior si el test es demasiado estricto.

Mitigacion:
- El test debe cubrir solo imports usados por Suite, Hub, QA y build.
- No incluir helpers privados con `_` salvo los que ya son importados por
  consumidores reales.

Gates:
- Gates base.
- Smoke import especifico de varios simbolos: `NMCard`, `NMButton`,
  `NMTabs`, `NMWindowChrome`, `NMPatientRowPremium`.

Commit:
- `test: capture shared component public api`

Rollback:
- Revertir el commit. No debe dejar cambios runtime.

## Fase 1 - Extraer nucleo de tema sin romper imports

Alcance:
- Romper el ciclo `theme_qt -> components_qt -> theme_qt`.
- Mover `ThemeManager` a un modulo pequeno sin dependencias de componentes.
- Mantener reexports desde `shared.components_qt` y `shared.components`.

Archivos:
- `shared/theme_manager.py`
- `shared/theme_qt.py`
- `shared/components_qt.py`
- `shared/components/__init__.py`
- Tests de API/imports.

Cambios permitidos:
- Crear `shared/theme_manager.py` con `ThemeManager`.
- Cambiar `shared.theme_qt._tm()` para importar desde `shared.theme_manager`.
- Reexportar `ThemeManager` desde `shared.components_qt` para compatibilidad.
- Reexportar `ThemeManager` desde `shared.components` para compatibilidad.
- No tocar estilos ni widgets.

Riesgos:
- Orden de import en arranque frozen o QA.
- Senales de tema desconectadas si se duplican singletons.

Mitigacion:
- Una unica clase/singleton vive en `shared.theme_manager`.
- `shared.components_qt.ThemeManager` debe ser alias del mismo objeto, no copia.
- `shared/theme_manager.py` se valida con una prueba/import check que impida
  dependencias hacia `theme_qt`, `components` o `components_qt`.

Gates:
- Gates base.
- Smoke manual de identidad singleton:
  `shared.components_qt.ThemeManager is shared.theme_manager.ThemeManager`.

Commit:
- `refactor: isolate theme manager`

Rollback:
- Revertir commit. Si falla solo en runtime, restaurar import local anterior en
  `theme_qt._tm()`.

## Fase 2 - Crear paquetes mecanicos por familias

Alcance:
- Antes de mover cada familia, analizar dependencias, herencia, uso de helpers y
  grupos fuertemente acoplados. El orden final debe priorizar bloques hoja y
  acoplamiento real, no solo afinidad semantica por nombre.
- Crear estructura de carpetas sin migrar consumidores.
- Mover clases por bloques mecanicos desde `shared/components_qt.py` a modulos
  internos, dejando facade completa.
- No cambiar implementacion de clases salvo imports relativos necesarios.

Estructura objetivo inicial:
- `shared/components/core.py`
- `shared/components/buttons.py`
- `shared/components/inputs.py`
- `shared/components/surfaces.py`
- `shared/components/navigation.py`
- `shared/components/feedback.py`
- `shared/components/data.py`
- `shared/components/mood.py`
- `shared/components/session.py`
- `shared/components/dialogs.py`
- `shared/components/patient.py`
- `shared/components/layout.py`

Archivos:
- `shared/components_qt.py`
- `shared/components/__init__.py`
- Nuevos modulos bajo `shared/components/`

Orden recomendado:
- 2A: mapa de dependencias por clase: bases, helpers globales, imports locales,
  consumidores externos y referencias entre componentes.
- 2B: bloques hoja sin herencia ni dependencias internas pesadas.
- 2C: bloques con herencia simple ya estabilizada por `core.py`.
- 2D: bloques acoplados por dominio, solo cuando sus dependencias previas ya
  esten extraidas.
- 2E: grupos fuertemente acoplados que convenga mover juntos para evitar ciclos
  internos temporales.

Riesgos:
- Dependencias internas cruzadas entre clases movidas.
- Imports circulares nuevos dentro de `shared/components/`.
- Cambios invisibles por orden de inicializacion de Qt.

Mitigacion:
- Mover una familia por commit.
- Usar imports locales dentro de metodos cuando haya dependencia entre familias.
- Mantener `shared/components_qt.py` como facade con imports y `__all__`.
- No migrar consumidores en esta fase.

Gates:
- Gates base en cada subfase.
- Smoke import por familia.
- Smoke runtime Suite/Hub minimo.

Commits:
- `refactor: move core shared components`
- `refactor: move surface shared components`
- `refactor: move button and input components`
- `refactor: move feedback and navigation components`
- `refactor: move data mood session components`

Rollback:
- Revertir el commit de la subfase fallida. Las subfases previas deben quedar
  validas porque la facade conserva imports.

## Fase 3 - Ordenar API publica de `shared.components`

Alcance:
- Convertir `shared.components` en el import publico preferido.
- Mantener `shared.components_qt` como compat facade.
- Documentar API solo en codigo, sin crear documentacion adicional.

Archivos:
- `shared/components/__init__.py`
- `shared/components_qt.py`
- `tests/test_components_public_api.py`

Cambios permitidos:
- Agrupar exports en `__all__` por familias.
- Asegurar que `from shared.components import X` funcione para todos los
  consumidores actuales.
- Mantener `from shared.components_qt import X` funcionando.

Riesgos:
- Duplicar imports pesados si `__init__` importa todo ansiosamente.
- Romper herramientas frozen si cambia demasiado el grafo.

Mitigacion:
- Primero mantener reexports simples.
- Evaluar lazy imports solo si hay medicion de costo real.

Gates:
- Gates base.
- Smoke imports desde ambos paths.

Commit:
- `refactor: define shared components public api`

Rollback:
- Revertir commit; consumidores siguen en `components_qt`.

## Fase 4 - Migrar consumidores gradualmente al paquete publico

Alcance:
- Cambiar imports de consumidores desde `shared.components_qt` hacia
  `shared.components`, una zona por commit.
- No modificar uso de widgets ni estilos locales.

Orden:
- 4A: QA y helpers compartidos (`qa/capture_v8.py`,
  `shared/adaptive_layout_qt.py`).
- 4B: Suite shell (`app/main_qt.py`, `app/home_qt.py`,
  `app/onboarding_qt.py`, `app/privacy_lock_qt.py`).
- 4C: Suite modulos (`app/modules/*_qt.py`).
- 4D: Hub shell (`hub/main_qt.py`, `hub/personalizacion_global.py`).
- 4E: Hub pacientes/plan/editor (`hub/pacientes_qt.py`,
  `hub/plan_terapeutico.py`, `hub/editors/text_overrides_editor.py`).

Riesgos:
- Fallback imports duplicados en modulos con try/except.
- Imports privados usados por QA o widgets internos.

Mitigacion:
- Migrar solo imports que tienen export publico confirmado.
- Si un consumidor usa simbolo privado real, promoverlo explicitamente o dejarlo
  temporalmente en `components_qt` con comentario tecnico corto.

Gates:
- Gates base por subfase.
- Smoke runtime Suite/Hub minimo.
- Para subfase de Suite modulos, probes puntuales de vistas afectadas cuando el
  import cambiado corresponda a una vista concreta.

Commits:
- `refactor: migrate qa shared component imports`
- `refactor: migrate suite shell component imports`
- `refactor: migrate suite module component imports`
- `refactor: migrate hub shell component imports`
- `refactor: migrate hub detail component imports`

Rollback:
- Revertir solo el commit de la zona fallida.

## Fase 5 - Reducir `shared/components_qt.py` a facade minima

Alcance:
- Una vez migrados consumidores, `shared/components_qt.py` queda solo como
  compatibilidad.
- No borrar aun el facade.

Archivos:
- `shared/components_qt.py`
- `tests/test_components_public_api.py`

Cambios permitidos:
- Reemplazar implementaciones remanentes por imports desde `shared.components.*`.
- Mantener `__all__`.
- Mantener tests que garanticen equivalencia de paths publicos.

Riesgos:
- Alguna herramienta externa o installer puede importar `components_qt`.

Mitigacion:
- Mantener facade durante al menos una ronda completa de releases internas.
- No emitir warnings runtime todavia.

Gates:
- Gates base.
- Smoke import exhaustivo de todos los nombres en `__all__` desde ambos paths.
- Smoke runtime Suite/Hub minimo.

Commit:
- `refactor: reduce components_qt to compatibility facade`

Rollback:
- Revertir commit para restaurar la fachada previa. No implica volver al
  monolito original si las fases 2-4 ya quedaron validadas.

## Fase 6 - Consolidar estilos compartidos sin cambios visuales

Estado:
- Fuera de esta ejecucion. Proyecto posterior de consolidacion visual.

Alcance futuro:
- Empezar a mover QSS repetido y helpers de estilo local hacia helpers
  compartidos, manteniendo exactamente los mismos tokens y resultados.
- No cambiar apariencia ni nombres de tokens.

Archivos candidatos:
- `shared/theme_qt.py`
- `shared/components/styles.py`
- `shared/components/inputs.py`
- `shared/components/buttons.py`
- `app/modules/*_qt.py`
- `hub/*_qt.py`

Orden:
- 6A: helpers repetidos de scroll/textedit/lineedit ya existentes en
  `theme_qt`.
- 6B: estilos de botones/chips que duplican `NMButton`, `NMBadge`, `NMChip`.
- 6C: cards/local panels que duplican `NMCard`, `NMSectionCard`, `NMPanel`.
- 6D: labels/metadata repetidos con `label_style`, `qfont`, `v3_font`.

Riesgos:
- Pequenas diferencias visuales por QSS selector specificity.
- Cambios de estado hover/focus si se reemplaza demasiado de una vez.

Mitigacion:
- Comparar texto QSS antes/despues ayuda a revisar regresiones mecanicas, pero
  no prueba equivalencia visual. Cualquier centralizacion visible futura requiere
  captura puntual claro/oscuro de la vista afectada.
- Migrar un componente/vista por commit.
- Usar probes puntuales de vista afectada, no matriz completa.

Gates:
- Gates base.
- Smoke runtime de vista afectada.
- Captura puntual claro/oscuro de la vista tocada cuando se cambie QSS visible.

Commits:
- `refactor: centralize shared input styles`
- `refactor: centralize shared chip styles`
- `refactor: centralize shared card styles`

Rollback:
- Revertir commit de la vista/helper afectado.

## Fase 7 - Propagacion compartida Suite/Hub

Estado:
- Fuera de esta ejecucion. Proyecto posterior de consolidacion visual.

Alcance futuro:
- Asegurar que cambios futuros de componentes compartidos se reflejen en Suite y
  Hub sin duplicar estilos locales.
- Reducir overrides locales solo cuando haya componente compartido equivalente.

Archivos:
- `app/main_qt.py`
- `app/home_qt.py`
- `app/modules/*_qt.py`
- `hub/main_qt.py`
- `hub/pacientes_qt.py`
- `hub/plan_terapeutico.py`
- `shared/components/*`

Cambios permitidos:
- Reemplazar widgets locales por componentes compartidos equivalentes.
- Eliminar QSS local duplicado si el componente compartido produce el mismo
  resultado.
- Mantener adaptadores de datos y comportamiento en cada pantalla.

Riesgos:
- Un componente compartido puede no cubrir una variacion real de Hub o Suite.
- Reuso excesivo puede forzar abstracciones prematuras.

Mitigacion:
- Antes de reemplazar, listar props/estados requeridos por la pantalla.
- Si falta una variacion, agregar parametro compatible al componente compartido
  sin alterar defaults.

Gates:
- Gates base.
- Smoke runtime Suite/Hub minimo.
- Probe puntual de cada vista afectada.
- Captura puntual claro/oscuro de cada vista con cambio visible.

Commits:
- Un commit por pantalla o familia de pantallas.

Rollback:
- Revertir pantalla por pantalla.

## Fase 8 - Deprecacion controlada de imports antiguos

Estado:
- Fuera de esta ejecucion. Proyecto posterior, a evaluar cuando 0-5 esten
  integradas y los consumidores internos hayan migrado.

Alcance futuro:
- Solo cuando no queden consumidores internos directos de `shared.components_qt`.
- Mantener facade por compatibilidad externa, pero agregar test que impida nuevos
  imports internos desde ese path.

Archivos:
- `tests/test_component_import_boundaries.py`
- `shared/components_qt.py`
- Consumidores remanentes si aparecen.

Cambios permitidos:
- Test que permita `shared/components_qt.py` y quizas QA legacy especifica, pero
  falle si `app/`, `hub/` o `shared/` importan directo desde `components_qt`.
- No borrar facade.

Riesgos:
- QA o build pueden seguir necesitando imports antiguos.

Mitigacion:
- Whitelist explicita y pequena, revisada por uso real.

Gates:
- Gates base.
- Smoke imports desde facade y paquete publico.

Commit:
- `test: prevent new internal components_qt imports`

Rollback:
- Revertir el test si bloquea un consumidor real no migrado.

## Fase 9 - Regresion final completa

Alcance:
- Ejecutar validacion completa luego de todas las fases anteriores.
- No mezclar con cambios de codigo.

Gates:
- Gates base.
- Smoke runtime Suite/Hub minimo.
- `.\.venv\Scripts\python.exe qa\capture_v8.py --all`
- `.\.venv\Scripts\python.exe qa\runtime_live_probe.py --all --theme both`

Riesgos:
- Duracion alta y falsos positivos de QA visual.

Mitigacion:
- Si falla, clasificar si es defecto runtime, evidencia insuficiente o cambio
  visual real.
- No arreglar dentro del mismo commit de regresion; abrir fase puntual.

Commit:
- No requiere commit si solo son ejecuciones de QA.

Rollback:
- No aplica salvo outputs generados no versionados.

## Criterio de finalizacion

- `shared/components_qt.py` queda como facade pequena de compatibilidad.
- Implementaciones viven bajo `shared/components/` por familia.
- `app/`, `hub/` y `qa/` importan componentes desde `shared.components` salvo
  excepciones justificadas.
- `shared.theme` sigue siendo la fuente unica de datos visuales.
- `shared.theme_qt` no importa implementaciones de componentes.
- Suite y Hub arrancan y cierran en smoke runtime minimo.
- Tests impiden reintroducir ciclos o imports internos al facade antiguo.
- Los estilos locales duplicados se reducen solo cuando hay equivalencia visual
  comprobada.
