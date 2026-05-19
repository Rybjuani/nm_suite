# NeuroMood Design Sources

Fuentes visuales para el rediseño de NeuroMood Suite y NeuroMood Hub.

## Estructura

```text
REDESIGN/
  design_sources/
    01_new_models/
    02_old_models/
    03_current_app/
    04_logo/
```

## Carpetas

### `01_new_models/`

Contiene los nuevos candidatos visuales prefabricados:

- `new_light_mockup.html`
- `new_light_mockup.png`
- `new_dark_mockup.html`
- `new_dark_mockup.png`

Estos archivos sirven como dirección visual principal para el nuevo diseño.

### `02_old_models/`

Contiene modelos visuales anteriores. Deben usarse solo como referencia secundaria para rescatar componentes, jerarquías o decisiones que todavía sirvan.

### `03_current_app/`

Contiene los mockups y capturas de la aplicación actual. Esta carpeta es la referencia funcional más importante, porque representa lo que ya existe en NeuroMood Suite y NeuroMood Hub.

### `04_logo/`

Contiene el logo principal de NeuroMood usado como referencia visual.

## Nota para implementación

Estos archivos no deberían ser importados como dependencias runtime de la app PyQt6. Para producción, los assets definitivos deben copiarse a carpetas productivas como:

```text
assets/
  branding/
    neuromood.png
```
