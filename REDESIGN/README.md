# REDESIGN

Carpeta de trabajo para el rediseño visual de NeuroMood.

Esta carpeta contiene fuentes de diseño, mockups HTML, capturas PNG, modelos actuales, modelos viejos, nuevos candidatos visuales y logo de referencia. Su objetivo es servir como material de análisis e importación en Figma/Stitch/IA, sin mezclarse con el código productivo de la aplicación.

## Uso recomendado

1. Importar los HTML nuevos con `html.to.design`.
2. Importar las capturas PNG con `image.to.design` o Codia.
3. Usar `03_current_app` como referencia funcional real de la app actual.
4. Crear el sistema visual final en Figma.
5. Recién después traducir el diseño a PyQt6/QSS dentro del código fuente.

## Regla importante

No renombrar archivos internos de `03_current_app/extracted/model_01` ni `03_current_app/extracted/model_02` sin revisar primero las rutas relativas, porque los HTML/JSON pueden depender del orden y nombres de las capturas.
