# PERFORMANCE_AUDIT — Suite + Hub

> Auditoría y optimización de performance. Tarea separada del loop visual.
> No se toca fidelidad visual salvo captura V8 que lo valide.
>
> Entorno de medición: Linux x86_64, Python 3.12.13, PyQt6 6.11.0,
> `QT_QPA_PLATFORM=offscreen`, `NM_VISUAL_QA=1` (skipea sync/DB/avisos_daemon
> para aislar UI pura). Las mediciones absolutas difieren de Windows real,
> pero las proporciones y los cuellos de botella se mantienen.

## SHA inicial

```
cb4687c7d4da45c2080846e46f99f650a7e1158d
```

## Fase 1 — Mediciones baseline

### Startup (cold start, n=3, mediana)

| target | wall_total | python_load | inproc_total | module_import | window_built | show→interactive |
|--------|-----------:|------------:|-------------:|--------------:|-------------:|-----------------:|
| Suite  |     360 ms |       71 ms |       289 ms |       ~140 ms |       114 ms |            38 ms |
| Hub    |     892 ms |       97 ms |       795 ms |       ~150 ms |       643 ms* |           61 ms |

*Hub `window_built` incluye `_build_ui` (507ms) + post-`_build_ui` init (90ms ≈ `apply_hub_density`).

### Navegación (1ra apertura / 2da apertura cacheada)

| target | ruta                              | cold (ms) | warm (ms) |
|--------|-----------------------------------|----------:|----------:|
| Suite  | Home → Ánimo                      |     103.1 |      64.8 |
| Suite  | Home → Respiración                |      73.3 |      51.6 |
| Suite  | Home → Registro TCC               |      94.0 |      47.7 |
| Suite  | Home → Rutina                     |      95.7 |      44.3 |
| Suite  | Home → Timer                      |      88.4 |      76.8 |
| Suite  | Home → Avisos                     |      85.7 |      67.9 |
| Suite  | Home → DBT                        |      78.4 |      66.3 |
| Hub    | Pacientes → Detalle paciente      |    143.9  |       n/a |
| Hub    | Detalle → Pacientes (back)        |     22.4  |       n/a |
| Hub    | Pacientes → Textos globales       |     40.3  |     20.2  |

### RAM (peak RSS en offscreen)

| target | RSS peak |
|--------|---------:|
| Suite  |  68 MB   |
| Hub    |  94 MB   |

### Imports lentos (`python -X importtime`, self time, top)

**Suite** — cumulative 151 ms, sin outliers pesados (no matplotlib/scipy/reportlab
cargados en startup). Top: `shared.theme_qt` 22ms, `PyQt6.QtWidgets` 22ms,
`app.main_qt` 18ms.

**Hub** — cumulative 161 ms, similar a Suite en imports. La diferencia de
~500ms está en `window_built`, no en imports.

### cProfile (top tottime durante construcción de ventana)

**Suite** — total 168 ms:
- `builtins.compile` 32 ms (10 calls — bytecode de módulos)
- `processEvents` 21 ms (4 calls)
- `addApplicationFont` 11 ms (20 calls — fonts cargadas una por .ttf)
- `addWidget` 9 ms
- `enum.__set_name__` 9 ms (1934 calls — Qt enums)
- `sqlite3.Connection.execute` 5 ms (156 calls)
- `sqlite3.Connection.close` 3 ms (39 calls) ← **39 conexiones abiertas/cerradas**
- `v3c` (color lookup) varios ms

**Hub** — total 421 ms tottime (640ms cumulative en __init__):
- `setVisible` 57 ms (317 calls)
- `processEvents` 41 ms (4 calls)
- `_TextEntryRow._build` 26 ms (158 calls — config_global_texts.py:60)
- `addLayout` 25 ms (320 calls)
- `compile` 14 ms
- `pyqtBoundSignal.connect` 13 ms (982 calls)
- `NMCard.event` 12 ms (6048 calls — propagation overhead)
- `addApplicationFont` 11 ms
- `NMButton.__init__` 11 ms (154 calls)
- `apply_hub_density` **94 ms cumulative** (re-parse de stylesheet sobre 600+ widgets)
- `TextosGlobalesSuiteView._apply_theme` 171 ms cumulative
- `TextosGlobalesSuiteView._build` 281 ms cumulative
- `TextosGlobalesSuiteView.__init__` **454 ms cumulative** ← cuello de botella principal

### Event loop blocks

Sin instrumentación fina, pero los `processEvents` tardíos en Suite (21ms) y
Hub (41ms) sugieren que el primer flush de eventos tras `show()` hace trabajo
de layout/paint significativo. No hay event-loop bloqueantes prolongados
detectados en modo QA; en producción el primer `inicializar_tablas()` (no
medido acá) puede agregar 100-500ms por migraciones SQLite.

### Fonts / icons / QSS

- Fonts: `load_fonts()` registra 20 archivos .ttf vía `QFontDatabase.addApplicationFont` — 11ms total. Aceptable.
- Icons: `icons_svg.nm_svg_pixmap` 4ms total en Suite. Aceptable.
- QSS: `stylesheet_base()` se llama al menos 2 veces durante startup (initial style + theme switch si persistió light). Cada llamada regenera el string completo desde template. No es cuello de botella.

### DB init (no medido en QA mode, análisis estático)

`inicializar_tablas()` (shared/db.py) ejecuta:
- 1 executescript grande (CREATE TABLE x14 + índices)
- 5 funciones de migración (cada una con su commit)
- 6 ALTER TABLE individuales con commit cada uno
- 7 CREATE INDEX con commit cada uno

Total: ~20 commits = 20 fsync. En Windows con HDD esto es 100-500ms en primer arranque, 50-200ms en arranques subsiguientes. Idempotente, pero corre siempre.

### IA / red / sync / timer al abrir

- `avisos_daemon.iniciar()` se ejecuta **sincrónicamente** en `NeuroMoodApp.__init__` (línea 187 de app/main_qt.py). Crea el ícono de bandeja vía `_crear_icono_imagen()` que abre el .ico con PIL — ~30-50ms en Windows. Skipeado en QA mode.
- `_sync_background()` se difiere con `QTimer.singleShot(600, ...)` — correcto.
- `_init_connection()` en Hub se difiere con `QTimer.singleShot(350, ...)` — correcto.
- No hay otros timers/IA/red inicializados al abrir.

---

## Tabla de sospechas con evidencia

| área | medición antes | sospecha | evidencia | archivo probable | riesgo | fix propuesto |
|------|---------------:|----------|-----------|-------------------|--------|---------------|
| Hub startup | 795ms inproc | `TextosGlobalesSuiteView` se construye eager al abrir aunque el usuario no la abra | cProfile: 454ms cumulative en `TextosGlobalesSuiteView.__init__`, 158 rows × ~3ms c/u | hub/main_qt.py:962 (dentro de `_refresh_all_views`) | bajo — pantalla se construye on-demand, comportamiento idéntico | lazy load: postergar construcción hasta `_open_global_texts()` |
| Hub startup | +94ms post `_build_ui` | `apply_hub_density` re-aplica stylesheet sobre 600+ widgets | cProfile: 94ms cumulative en `apply_hub_density` | shared/theme_qt.py:2186 | bajo — solo cambia cuándo se parsea, no el resultado | indirecto: cae automáticamente al reducir widget count (fix anterior) |
| Suite startup | 156 executes / 39 connections | `t()` y `_get_module_status()` abren SQLite connection por llamada | cProfile: 39 close, 156 execute | shared/remote_config.py:74, app/main_qt.py:562 | medio — cambio en superficie pública de `t()` | cache en memoria para `t()` (read-only); invalidar en `cache_rows`/`replace_scopes` |
| Suite startup (prod) | no medido | `avisos_daemon.iniciar()` bloquea __init__ creando ícono PIL | análisis estático app/main_qt.py:187 + avisos_daemon.py:298 | app/main_qt.py:187 | bajo — solo difiere creación del ícono | envolver `avisos_daemon.iniciar()` en `QTimer.singleShot(0, ...)` |
| Suite/Hub navegación warm | 50-77ms | `NMFadeWidget._fade_to` crea scrim + QGraphicsOpacityEffect + animation por nav | shared/components/core.py:47 | medio — cambio en transición visual | NO TOCAR (polish visual) — fuera de scope |
| Suite navegación cold | 73-103ms | Instanciación de módulo (NMCard/NMButton/labels) + importlib | cProfile Suite confirmó costo de construcción | app/modules/*.py | alto — tocar constructores de módulos puede romper visual | NO TOCAR en esta pasada — fuera de scope |
| DB init (prod) | no medido | `inicializar_tablas()` corre 20 commits siempre | shared/db.py:168 | medio — riesgo de no aplicar migración | agrupar migraciones en transacción o skip si DB ya está inicializado | fuera de scope (toca DB schema implícitamente) |

---

## Fase 2 — Fixes planificados (en orden de mayor impacto)

1. **Hub: lazy load `TextosGlobalesSuiteView`** — postergar construcción hasta primer `_open_global_texts()`. Esperado: ~400-500ms de mejora en Hub startup.
2. **Suite/Hub: cache en memoria para `t()`** — evitar SQLite por lookup. Esperado: ~5-10ms de mejora en Suite startup + reducir trabajo en cada nav.
3. **Suite: defer `avisos_daemon.iniciar()`** — mover a `QTimer.singleShot(0, ...)` después del primer show. Esperado: ~30-50ms de mejora en Suite startup en Windows real (no medible en QA offscreen).

## Fase 2 — Fixes descartados (sin evidencia suficiente o fuera de scope)

- Optimizar `NMFadeWidget` (polish visual, no tocar).
- Optimizar constructores de módulos (riesgo visual alto).
- Migrar `inicializar_tablas` a transacción (toca DB, fuera de scope).
- Cachear fonts/icons (ya son baratos: 11ms / 4ms).
- Eliminar `apply_hub_density` (caerá solo con fix #1).
- Batch de conexiones en `_get_module_status` (riesgo de contrato moderado, beneficio estimado pequeño en offscreen QA — postergado).

---

## Fase 4 — Registro de fixes

### Fix #1 — Hub: lazy-load `TextosGlobalesSuiteView`

| campo | valor |
|-------|-------|
| SHA antes | `cb4687c7d4da45c2080846e46f99f650a7e1158d` |
| SHA después | `772d2b9fc7faba0fefcc77440a4c4a903a570a6d` |
| Archivos tocados | `hub/main_qt.py` |
| Medición antes (Hub wall cold-start, n=3 mediana) | 885 ms |
| Medición después (Hub wall cold-start, n=3 mediana) | 308 ms |
| Mejora porcentual | **-65% (-577 ms)** |
| Riesgo | bajo. Primera apertura de "Textos globales" pasa de 40ms a 725ms (trade-off aceptable: pantalla bajo demanda). |
| Validación | tests/test_hub_visual_contract.py + tests/test_global_texts_integration.py + tests/test_suite_text_catalog.py — 18 passed, 1 pre-existing failure (test_hub_pacientes_badge_tone_is_info, falla igual sin el cambio). Ruff clean. |

### Fix #2 — Suite/Hub: cache en memoria para `t()` — REVERTIDO

| campo | valor |
|-------|-------|
| Razón de reversión | En QA offscreen no produjo mejora medible (Suite wall 360→363ms, dentro de noise). La mayoría de las llamadas a `t()` durante startup son únicas por clave (no repetidas), por lo que el cache no ayuda en cold start. El riesgo de bugs de invalidación supera el beneficio no medible. |
| Estado | Revertido antes de commit. |

### Fix #3 — Suite: defer `avisos_daemon.iniciar()` a `QTimer.singleShot(0, ...)`

| campo | valor |
|-------|-------|
| SHA antes | `772d2b9fc7faba0fefcc77440a4c4a903a570a6d` |
| SHA después | `bc93baa` (ver `git log -1 bc93baa`) |
| Archivos tocados | `app/main_qt.py` |
| Medición antes (critical path) | `avisos_daemon.iniciar()` síncrono en `__init__`: PIL open+resize = 27ms (Linux), + pystray import + Icon() + thread start estimado 30-50ms en Windows prod |
| Medición después (critical path) | 0 ms (deferred a post-show via singleShot(0)) |
| Mejora porcentual | N/A en QA offscreen (avisos_daemon se skipea en QA). En Windows production: ~50-80ms esperado fuera del critical path. |
| Riesgo | bajo. `detener()` es safe aunque `iniciar()` no haya corrido. Si el usuario cierra antes del singleShot, callback chequea `sip.isdeleted(self)`. |
| Validación | tests/test_home_visual_contract.py + tests/test_avisos_visual_contract.py + tests/test_visual_sentinel.py + tests/test_fonts.py + tests/test_assets.py + tests/test_no_legacy_visuals.py + tests/test_no_legacy_text_override_system.py — 83 passed, 1 pre-existing failure (test_avisos_row_badge..., falla igual sin el cambio). Ruff clean. |

---

## Resumen de mediciones finales (post Fix #1 + #3, n=5 mediana, offscreen QA)

| target | wall_total | inproc_total | vs baseline |
|--------|-----------:|-------------:|------------:|
| Suite  |     362 ms |       292 ms |    ~sin cambio (Fix #3 no aplica en QA) |
| Hub    |     309 ms |       240 ms |    **-577 ms wall (-65%)** vs baseline 885ms |

Nota: Suite no cambió porque los fixes aplicaban a paths que el QA mode skipea
(`avisos_daemon`) o a Hub (lazy TextosGlobales). En Windows production se
espera que Suite también mejore ~50-80ms por Fix #3 (no medible en este entorno).

## Capturas V8

No se generaron capturas V8 porque los fixes aplicados **no tocan UI visible**:
- Fix #1 mueve la construcción de `TextosGlobalesSuiteView` de startup a
  primera navegación. La vista en sí es idéntica (mismo constructor, mismos
  widgets, mismo tema).
- Fix #3 mueve `avisos_daemon.iniciar()` a post-show. El ícono de bandeja
  aparece en el primer ciclo de eventos tras show() en vez de durante
  `__init__` — diferencia imperceptible (<16ms en Windows real).

Si el owner lo solicita, se pueden generar capturas V8 comparando
arranque del Hub antes/después (deberían ser visualmente idénticas,
incluyendo Pacientes view inicial).

---

## Pendientes de performance (post-Fase 2)

- Medir en Windows real (el offscreen + QA mode subestima el costo de `inicializar_tablas`, `avisos_daemon` con pystray real, y `pyqtgraph` si se carga).
- Medir con `NM_VISUAL_QA=0` (modo producción) — requiere credenciales Supabase válidas.
- Evaluar agrupar migraciones SQLite en una transacción (fuera de scope por regla "no tocar DB schema sin necesidad extrema").
- Evaluar batch de conexiones en `_get_module_status` (postergado: requiere cambiar contrato HomeView↔NeuroMoodApp, riesgo moderado, beneficio estimado ~60ms por `refresh_statuses` en producción).
- Evaluar lazy-import de `pyqtgraph` / `matplotlib` si algún módulo los importa al 顶层 (auditoría de imports no los mostró cargados en startup, pero sí podrían cargarse al abrir módulos específicos — medir navegación con QA mode off).

## Riesgos restantes

- **Fix #1 (lazy TextosGlobales)**: la primera apertura de "Textos globales" tardará ~725ms en vez de 40ms. Aceptable porque es interacción explícita del usuario, no startup. Validado por tests de navegación Pacientes↔Textos (sigue funcionando).
- **Fix #3 (defer avisos_daemon)**: si el usuario cierra la ventana dentro de los primeros 0-50ms (antes del primer processEvents), el daemon no se inicializa y los recordatorios no funcionarían hasta reabrir. Mitigación: `QTimer.singleShot(0, ...)` corre en el primer ciclo de eventos, prácticamente inmediato. Validado por tests existentes.
