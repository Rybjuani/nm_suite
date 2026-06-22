# Visual Sentinel

Auditor visual **canonico, independiente y autodescubrible** para NeuroMood Suite + Hub.
Reemplaza conceptualmente a `qa/capture_v8.py` y `qa/runtime_live_probe.py` como
herramienta principal de auditoria visual, **sin depender de ellos**: no los
importa, no reusa su lista manual de pantallas ni sus recetas.

## Por que es distinto

- **Autodescubrible.** No tiene una lista hardcoded de pantallas. Descubre la UI
  navegando la app real (registro de modulos de la propia app para Suite;
  vistas declaradas en `_nav_views()` para Hub) e introspectando en vivo el
  arbol Qt para encontrar sub-estados (`QStackedWidget`, `QTabWidget`/`QTabBar`,
  `NMTabs`, `NMSegmentedPanel`, `NMPanelTabs`, botones clickeables, dialogs).
- **Contratos globales reutilizables** en `qa/visual_sentinel_contracts/` que
  corren sobre TODAS las pantallas descubiertas. No hay YAML sesgado por 3
  pantallas.
- **Honesto por diseno.** `audit --all` es el UNICO modo que puede emitir
  resultado general. `capture`/`inspect --screen` nunca imprimen PASS general:
  marcan `TARGETED_INSPECTION_ONLY` y `GENERAL_AUDIT_NOT_RUN`.
- **Autoupdateable seguro** (no autoaprueba): descubre pantallas nuevas, las
  marca `NEW_STATE_UNREVIEWED`, genera baselines propuestas y bloquea el cierre
  general hasta revision humana.

## Uso

```powershell
# Listar estados descubiertos
.\.venv\Scripts\python.exe qa\visual_sentinel.py --list

# Auditoria general (unico modo con resultado general)
.\.venv\Scripts\python.exe qa\visual_sentinel.py audit --all --theme both
.\.venv\Scripts\python.exe qa\visual_sentinel.py audit --app suite --theme light
.\.venv\Scripts\python.exe qa\visual_sentinel.py audit --app hub --theme dark

# Captura / inspeccion puntual (sin resultado general)
.\.venv\Scripts\python.exe qa\visual_sentinel.py capture --screen suite:animo --theme both
.\.venv\Scripts\python.exe qa\visual_sentinel.py inspect --screen hub:detalle --theme light

# Baselines (opcionales, complemento — no dependencia principal)
.\.venv\Scripts\python.exe qa\visual_sentinel.py propose-baselines
.\.venv\Scripts\python.exe qa\visual_sentinel.py approve-baseline --screen suite:home --theme dark --reason "baseline inicial"
```

`--screen` acepta el `screen_id` mostrado por `--list` con formato
`app:surface[:substate]` (ej. `suite:dbt:NMTabs0-tab-1`).

## Salida

```
qa/_visual_sentinel/latest/
  manifest.json        # metadatos de la corrida + estados + resultado
  findings.json        # todos los hallazgos
  coverage.json        # descubiertos / capturados / nuevos / stale
  index.html           # reporte visual
  screenshots/         # PNG por estado x tema
  widget_trees/        # arbol Qt completo + textos/geometrias/clickable/... en JSON
  crops/               # recortes de regiones importantes
  contact_sheets/      # mosaico de thumbnails
  logs/run.log
```

## Resultado de consola

```
VISUAL_SENTINEL_RESULT: FAIL
GENERAL_AUDIT_COMPLETE: YES
DISCOVERED_STATES: 25
CAPTURED_STATES: 25
NEW_STATE_UNREVIEWED: 25
STALE_STATES: 0
P0: 0
P1: 25
P2: 0
```

El resultado es **FAIL** si: no corrio `--all`; faltan capturas; hay estados
nuevos sin revisar; hay stale states; hay duplicados/fallback; hay P0 o P1.

## Contratos

`qa/visual_sentinel_contracts/`:
- `global.yaml` — contratos sobre todas las pantallas (blank/flat, duplicados,
  out-of-viewport, solapes, elision, estados nuevos, progress en color de error).
- `components/` — `buttons`, `tabs`, `cards`, `scrollbars`, `forms`,
  `empty_states`, `progress`, `dialogs`, `onboarding_legal`.

Cada contrato referencia un `check` implementado en `qa/visual_sentinel.py`
(registro `_CHECKS`). Los `params` son umbrales ajustables sin tocar codigo.

## Reglas visuales cubiertas

- No permitir pantallas blank/flat (P0).
- No permitir capturas duplicadas sospechosas entre estados distintos (P1).
- No permitir fallback silencioso (P1).
- No permitir widgets visibles fuera del viewport (P1).
- No permitir solapes claros entre widgets visibles (P2).
- No permitir texto principal cortado/elidido sin justificacion (P2).
- No permitir scrollbars internas inesperadas en legales/onboarding (P1).
- Detectar checkbox legal dentro de scroll area (P1).
- Detectar CTAs semanticos sin icono: Exportar PDF, Resumen IA, Completar con IA (P2).
- Detectar tabs secundarias gigantes (P2).
- Detectar tabs con labels largos que rompen densidad (P2).
- Detectar progress dots con color de error/warning fuera de estado de error (P2).
- Detectar estados nuevos no revisados (P1).
- Detectar estados stale/desaparecidos (P1).
- Detectar recetas/pantallas obsoletas referenciadas en metadata propia (P2).

## Baselines

Opcionales. `propose-baselines` genera fingerprints propuestos; `approve-baseline`
los aprueba registrando commit SHA, fecha y motivo en
`qa/visual_sentinel_baselines/registry.json`. **Nunca se autoaprueba.**

## Dependencias

PyQt6, Pillow, numpy, scikit-image, imagehash, PyYAML, rich, networkx (ya en el
venv). No usa cv2, jinja2, torch ni lpips.

## Limitaciones honestas

El Sentinel es **mucho menos propenso a falsos PASS que V8/runtime**, pero no es
infalible:
- La revision semantica humana sigue siendo necesaria.
- Algunos checks (solapes, elision, colores de progress) son heuristicos
  conservativos y pueden generar falsos positivos o perder casos sutiles.
- No cubre estados que requieren datos persistentes reales ni interaccion de
  red (ej. un resumen IA generado en runtime); esos siguen necesitando validacion
  manual o de runtime.
- La cobertura depende de que la navegacion de la app sea drivable por
  introspeccion Qt (modulos, tabs). Componentes muy custom pueden requerir
  nuevos `check` en `_CHECKS`.
