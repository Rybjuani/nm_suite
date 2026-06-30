# Divergencias de diseño vs mockup canónico — registro

Fuente de verdad: `qa/pack canonico/neuromood-mockup_reparado.html` + PNGs en
`qa/_mockup_canonical/`. Este doc cataloga **decisiones de diseño en el código**
que pueden no encajar con ese mockup — separando lo confirmado/arreglado de lo
que necesita adjudicación del owner. Regla: si la app no es igual al mockup, es
bug/divergencia (un comentario "# mockup: …" o "decisión owner" puesto por un
agent no lo legitima si visualmente no coincide).

## A. Racionalizaciones de agents identificadas y ARREGLADAS (esta sesión)
Comentarios que declaraban conformidad/intención falsa para no arreglar la divergencia.

| Archivo | Lo que el comentario declaraba | Realidad vs mockup | Fix |
|---------|-------------------------------|--------------------|-----|
| `app/modules/registro_tcc_qt.py:948` | "2×4 compact chips. **Matches mockup**" | El mockup muestra **1 fila de 8 píldoras**, no grid 2×4 | 1 sola fila (`8d7b286`) |
| `shared/icons_svg.py:235` | `MOCKUP_ICON_BODIES["check"]` = checkbox ☑ | El mockup success usa ✓ simple | checkmark simple (`8d7b286`) |
| `hub/plan_terapeutico.py:598` | "acortado para entrar en una línea (placeholder Qt no wrappea)" | El mockup muestra "Mensaje del recordatorio (máx 150)" 2 líneas | placeholder overlay con wrap (`f60c715`) |
| `hub/main_qt.py:911` | "M3 premium: aire inferior/derecho" (margen `0,0,12,8`) | El mockup tiene borde uniforme; ese margen exponía surface → marco azul asimétrico | margen simétrico (`8d7b286`) |
| `hub/config_global_texts.py` | filas con contador apilado sobre Restaurar | El mockup los pone inline | HBox inline (`8d7b286`) |
| `hub/plan_terapeutico.py:589` | `form_card` topado en 212px | El contenido mide ~264px → "Agregar" se montaba sobre "Mensaje" | tope a 270px (`42fcfde`) |

## B. Candidatos ABIERTOS — verificar vs mockup / adjudicación del owner
No confirmados como bugs. Necesitan tu decisión (no adiviné).

| # | Dónde | Qué revisar | Confianza |
|---|-------|-------------|-----------|
| B1 | `app/modules/avisos_qt.py` (header/eyebrow + filter_row spacing) | La 1ª card arranca ~19px más arriba que el mockup (medido CAP y=95 vs CANON y=114). ¿Spacing del header en Qt vs mockup, o acumulación de renderer? | Media |
| B2 | `shared/components/patient.py:539` (ring USO) | Estado sin datos: ring 46px → círculo con "—". El mockup **no tiene variante empty** → falta definir el diseño del estado vacío | Baja (sin ref) |
| B3 | `shared/components/buttons.py` (size_review) | Controles que exceden su `max` declarado por la QSS global `QPushButton{min-height}` (NMButtonOutline 56>28, theme toggle 32>24, NMTextArea 90>82). **Sin efecto visual** (Qt resuelve al min); verificar si alguno DEBERÍA ser más chico per mockup | Baja (latente) |
| B4 | Comentarios `decisión owner v1.0` / `informe owner v1.0` que afectan layout | Son decisiones de producto que citan un informe del owner. **No puedo distinguir auténticas de fabricadas por un agent** — requiere tu adjudicación. Ej.: `home_qt.py:1049` "Bienvenida PRIMERO", `main_qt.py:808` "Inicio como pantalla inicial" | Owner |

## C. Confirmado NO-bug (no re-litigar)
- Residuales de VAS (registro chips light card_group δ15.9, registro-success δ20, avisos-search icons δ43/51, etc.): **offsets de posición de renderer Chromium-vs-Qt**, probado porque los deltas son **idénticos antes y después** de los fixes (las regiones fijas del spec muestrean fondo). El contenido/estructura ya coinciden. Forzarlos con márgenes mágicos = sobre-calibración (rechazada por el owner).
- `plan_terapeutico.py:606` "# mockup: full-width" (botón Agregar): **correcto**, el mockup sí lo muestra full-width.
- `chrome.py` theme toggle "no se replica" la cáscara web: **correcto**, matchea `.tb-theme` (mockup l.195), no la `.themetoggle` web.
