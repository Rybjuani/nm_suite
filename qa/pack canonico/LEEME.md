# NeuroMood · Pack canonico de capturas (v2-reparado)

Pack descargable que genera **exactamente 86 PNG canonicas** con nombres y
tamanos fijos, sin romper la coherencia visual entre estados hermanos.

## Contenido del zip

```
pack_canonico/
  neuromood-mockup_reparado.html      # Mockup reparado (fuentes embebidas + CSS fijo)
  generate_captures.js                # Generador Playwright/Puppeteer (43 vistas x 2 temas = 86)
  LEEME.md                            # Este archivo
  collage_revision.png                # Collage con 14 capturas de comparacion
  capturas_test/                      # 86 PNG + INDICE_CAPTURAS.csv + MANIFEST.json
    hub-detalle-light-960x600.png
    hub-detalle-dark-960x600.png
    ...
    suite-timer-empty-light-960x600.png
    suite-timer-empty-dark-960x600.png
    ...
    INDICE_CAPTURAS.csv
    MANIFEST.json
```

## Requisitos

- Node.js 18+
- puppeteer-core + Chromium (o Playwright + Chromium)

## Comandos

```bash
# Instalar puppeteer-core
npm install puppeteer-core

# Ejecutar generador (usa /usr/bin/chromium por defecto)
# Se puede sobreescribir con PUPPETEER_EXECUTABLE_PATH
node ./generate_captures.js ./neuromood-mockup_reparado.html ./capturas_test
```

## Tamanos canonicos

| Surface | Tamano | Cantidad |
|---|---|---|
| `.window` (suite/hub normal) | 960 x 600 | 76 |
| `.window.narrow` (onboarding/recuperar) | 520 x 600 | 6 |
| `.modal` panel crop parcial | no cierra modal | 0 |
| `.window` con modal abierto (DBT practice + Resumen IA) | 960 x 600 | 4 |
| **Total** | | **86** |

Todos los PNG miden **exactamente** el tamano indicado en el nombre. No hay
980 px, no hay alturas variables, no hay nombres alternativos.

## Correcciones aplicadas en v2-reparado

### 1. Home (suite-home-*, suite-home-no-score-*)
- Reducidas cards de herramientas: min-height 148px -> 100px, padding 14px
- Reducido saludo: 30px -> 22px, score: 40px -> 28px
- Reducido gap del grid: 14px -> 10px
- Reducido padding de hero card y margins
- **Resultado**: 8 cards + hero card caben en 960x600 sin scroll global
- Layout base identico entre `score` y `no-score`, solo cambia contenido interno de la hero card

### 2. Actividades (suite-actividades-*)
- Reducido padding de cards: 20px -> 14px
- Reducido tamano de fuentes, badges y botones
- Reducido min-height de descripcion: 42px -> 34px
- Reducido gap del grid: 14px -> 10px
- Reducido padding del card de categorias
- **Resultado**: 4 cards (default/marked/filtered) caben sin scroll. Estados empty mantienen estructura
- Todos los estados hermanos comparten layout base identico (categorias + grid)

### 3. DBT Library (suite-dbt-library-*)
- Reducido padding de cards: 20px -> 14px
- Reducido tamano de barra y fuentes
- Reducido min-height de descripcion: 54px -> 34px
- Reducido gap del grid: 14px -> 10px
- Reducido padding del filter
- **Resultado**: 8 skills en 3 filas caben en 960x600 sin scroll global

### 4. Avisos Search (suite-avisos-search-*)
- Reemplazado texto parcial `respir` por `respiracion` (texto completo y documentado)
- **Resultado**: estado de busqueda deliberado y limpio, con resultado coincidente visible

### 5. Registro Success (suite-registro-success-*)
- CTA cambiado de `<button class="btn btn--ghost" disabled>Guardar</button>` (mini, sin peso)
  a `<button class="btn btn--primary" disabled>Guardar registro</button>` (mismo patron que step3)
- **Resultado**: continuidad visual con suite-registro-step3-filled-*; CTA estable en tamano/peso/posicion

### 6. Onboarding / Recuperar (suite-onboarding-*, suite-recuperar-acceso-*)
- Reducido padding del `.screen`: 26px 28px -> 16px 20px
- Reducido margins entre campos: 14px -> 8px
- Reducido max-height del bloque de consentimiento: 150px -> 120px
- Reducido tamano de fuentes y padding de botones
- Agregado `overflow:hidden` al `.screen` para prevenir scroll global
- Bloque de consentimiento mantiene `overflow-y:auto` (scroll interno disenado)
- **Resultado**: todo el contenido cabe en 520x600 sin scroll global visible. El mensaje de error inferior se ve completo

## Regla de scroll

- **Scroll permitido**:
  - Bloque de consentimiento en onboarding/recuperar (scroll interno, max-height:120px)
  - Textos globales (lista larga de 30+ textos editables)
  - Listas largas reales (pacientes, recordatorios)

- **Scroll prohibido** (corregido):
  - Home (8 cards + hero caben sin scroll)
  - Actividades (4 cards + filtros caben sin scroll)
  - DBT Library (8 skills caben sin scroll)
  - Registro (stepper + card caben sin scroll)
  - Onboarding/Recuperar (campos + consentimiento + botones caben sin scroll)

## Coherencia entre estados hermanos

- Home `score` y `no-score`: misma posicion de hero card, mismas 8 cards en grid identico
- Actividades `default`/`marked`/`filtered`/`empty`: mismo card de categorias, mismo grid, mismos gaps
- Registro step3-filled y success: stepper identico, CTA en misma posicion con mismo peso visual
- Onboarding normal/error/recuperar: mismos campos, mismo bloque de consentimiento, mismos botones
- No hay reglas por `data-screen`, `data-state` o `data-hub-tab` que alteren posiciones base

## Validacion del pack

- **86/86 PNG fisicas** generadas y verificadas
- **0 faltantes, 0 extra**
- **0 nombres fuera de la lista obligatoria**
- **0 tamanos fuera del tamano indicado en el nombre**
- **light/dark mismo tamano** para cada surface
- **MANIFEST.json coincide con archivos reales** (sha256 + size + DOM size = 86/86)
- **Sin recortes falsos:** cada captura valida que el bounding box DOM del selector
  (`.window` o `.modal`) coincide con el tamano declarado antes de disparar el screenshot
- **Sin :hover** residual (mouse movido fuera del viewport antes de capturar)
- Collage de revision incluido
