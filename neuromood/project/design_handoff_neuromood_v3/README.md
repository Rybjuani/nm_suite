# Handoff · NeuroMood v3 — Rediseño visual unificado

## Resumen

Este paquete contiene el **rediseño visual completo** de la suite NeuroMood:

- **NeuroMood Suite** (paciente, PyQt6): Inicio, Mood Tracker, Respiración, TCC, Rutina, Activación conductual, Timer, Recordatorios.
- **NeuroMood Hub** (profesional, PyQt6): Pacientes / Dashboard, Detalle de paciente (con tabs Registros / Asignar / Banco / IA), IA Asistente clínico, Configuración.
- **Instalador Suite** (PyQt6): wizard de 5 pasos (Bienvenida → Cuenta → Consentimiento → Instalación → Finalizar).
- **Desinstalador Suite** (PyQt6): wizard de 3 pasos (Confirmar → Eliminando → Finalizado).

## Sobre los archivos de este bundle

> ⚠️ **Los archivos `.html`, `.jsx`, `.js` de este bundle son REFERENCIAS DE DISEÑO**, no código para copiar directamente.
>
> Son prototipos hechos en HTML + React que muestran cómo debe verse y comportarse cada pantalla. Tu tarea es **recrear este diseño en el codebase Python/PyQt6 existente**, usando los componentes que ya están definidos en `shared/components_qt.py` y los tokens de `shared/theme.py` — refactorizándolos donde haga falta para que coincidan con el nuevo sistema visual.
>
> **No** instales React, **no** uses HTML embebido en Qt. La traducción es pixel-a-pixel pero usando QWidget, QLayout, QPainter, stylesheets de Qt, etc.

## Fidelidad

**Alta (hi-fi)**: paleta, tipografía, sombras, anillos, gradientes, espaciados y comportamientos están definidos pixel-perfect en el HTML. El dev debe respetarlos exactamente, mapeándolos a Qt.

---

## Stack del codebase destino

- **Lenguaje**: Python 3
- **Framework UI**: PyQt6
- **Empaquetado**: PyInstaller (.exe Windows 10/11)
- **DB**: SQLite local + Supabase remoto (sync)
- **IA**: Groq (llama3-70b) vía `hub.ia_asistente`

**Carpetas reales:**

```
app/                      — Suite paciente
  home_qt.py              — HomeView (grid de módulos)
  main_qt.py              — Entry point + navegación
  modules/                — Módulos individuales (animo, respiracion, tcc, rutina, actividades, timer, avisos)
  avisos_daemon.py        — Daemon de notificaciones
  motor_activacion.py
hub/                      — Hub profesional
  main_qt.py              — NeuroMoodHub QMainWindow
  pacientes_qt.py         — Detalle paciente con tabs
  exportar.py             — PDF export
  ia_asistente.py         — Cliente Groq
installers/               — Instalador + Desinstalador
  installer.py            — Wizard 5 pasos
  uninstaller.py          — Wizard 3 pasos
shared/                   — Sistema de diseño + utilidades
  theme.py                — Tokens (COLORS, TYPOGRAPHY, LAYOUT, GRADIENTS) ⭐ REFACTORIZAR
  theme_qt.py             — Helpers Qt (qcolor, qfont, gradient builders) ⭐ REFACTORIZAR
  components_qt.py        — Biblioteca de widgets (NMCard, NMButton, …) ⭐ REFACTORIZAR
  db.py                   — SQLite helpers
  sync.py                 — Supabase sync
  identidad.py            — Patient ID
  installer_common.py     — Shell común installer
  visual_qa.py            — Modo demo
db/                       — Migraciones SQL
```

**No modificar lógica de negocio** — solo el layer visual. Cualquier cambio que toque DB, sync, autenticación o motor de activación debe consultarse.

---

## Sistema de diseño v3

### Paleta de colores

#### Light theme

```python
V3_LIGHT = {
    # Backgrounds
    "bg":              "#eef2f8",
    "bgAlt":           "#e6ecf5",
    "bgSidebar":       "#ffffff",
    "surface":         "#ffffff",
    "elevated":        "#f5f7fb",

    # Borders
    "border":          "#e3e9f1",
    "borderSoft":      "#eef1f6",
    "borderStrong":    "#cdd5e2",

    # Text
    "text":            "#0f172a",
    "text2":           "#475569",
    "text3":           "#94a3b8",
    "text4":           "#cbd5e1",

    # Brand signature (gradiente firma teal → violet)
    "gradFrom":        "#2dd4bf",
    "gradMid":         "#5eead4",
    "gradTo":          "#a855f7",

    # Mood slashbar (paleta emocional, NO se cambia con el theme)
    "moodGradFrom":    "#2dd4bf",
    "moodGradMid":     "#5eead4",
    "moodGradTo":      "#a855f7",

    # Tones
    "teal":            "#14b8a6",
    "tealSoft":        "#d3f5ef",
    "violet":          "#a855f7",
    "violetSoft":      "#ede5fc",
    "cyan":            "#06b6d4",
    "cyanSoft":        "#cef3f9",

    # Semantic
    "success":         "#10b981",
    "successSoft":     "#d1fae5",
    "warning":         "#f59e0b",
    "warningSoft":     "#fef3c7",
    "danger":          "#ef4444",
    "dangerSoft":      "#fee2e2",

    # Streak
    "streak":          "#f97316",
    "streakSoft":      "#ffedd5",
}
```

#### Dark theme

```python
V3_DARK = {
    "bg":              "#060912",
    "bgAlt":           "#0a0f1f",
    "bgSidebar":       "#0a0f1f",
    "surface":         "rgba(18, 25, 45, 0.7)",   # translúcido con backdrop blur
    "surfaceSolid":    "#121c2d",                   # cuando no se puede blur
    "elevated":        "rgba(30, 41, 65, 0.6)",

    "border":          "rgba(94, 234, 212, 0.10)",
    "borderSoft":      "rgba(255, 255, 255, 0.06)",
    "borderStrong":    "rgba(94, 234, 212, 0.25)",

    "text":            "#f1f5f9",
    "text2":           "#94a3b8",
    "text3":           "#64748b",
    "text4":           "#475569",

    "gradFrom":        "#22d3ee",
    "gradMid":         "#5eead4",
    "gradTo":          "#c084fc",

    "moodGradFrom":    "#22d3ee",
    "moodGradMid":     "#5eead4",
    "moodGradTo":      "#c084fc",

    "teal":            "#5eead4",
    "tealSoft":        "rgba(20, 184, 166, 0.18)",
    "violet":          "#c084fc",
    "violetSoft":      "rgba(168, 85, 247, 0.20)",
    "cyan":            "#22d3ee",
    "cyanSoft":        "rgba(6, 182, 212, 0.18)",

    "success":         "#34d399",
    "successSoft":     "rgba(16, 185, 129, 0.20)",
    "warning":         "#fbbf24",
    "warningSoft":     "rgba(245, 158, 11, 0.20)",
    "danger":          "#f87171",
    "dangerSoft":      "rgba(239, 68, 68, 0.20)",

    "streak":          "#fb923c",
    "streakSoft":      "rgba(249, 115, 22, 0.18)",
}
```

> **Nota PyQt6**: Qt no soporta `rgba()` con alpha en stylesheets stringly-typed para todos los properties. Usar `QColor(r, g, b, a)` programáticamente y `QGraphicsBlurEffect` para el blur de superficies dark, o pre-renderizar el blur como pixmap.

### Tipografía

```python
TYPOGRAPHY = {
    "font_family":     "Plus Jakarta Sans, DM Sans, system-ui, sans-serif",
    "font_mono":       "JetBrains Mono",   # timers, IDs, hashes, métricas

    # Escala (px)
    "size_display":    28,    # títulos hero
    "size_h1":         24,    # títulos de pantalla
    "size_h2":         18,    # títulos de card
    "size_h3":         15,    # subtítulos
    "size_body":       13,
    "size_small":      12,
    "size_caption":    11,
    "size_caption_xs": 10,

    # Pesos
    "weight_regular":  400,
    "weight_medium":   500,
    "weight_semibold": 600,
    "weight_bold":     700,

    # Letter spacing
    "tracking_tight":  "-.02em",   # display
    "tracking_normal": "0",
    "tracking_eyebrow":".15em",    # eyebrow uppercase
}
```

Cargar las dos familias con `QFontDatabase.addApplicationFont`. Si no están instaladas, fallback a DM Sans (que ya está en `assets/fonts/`).

### Spacing / Radii / Shadows

```python
SPACE  = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "xxl": 32, "xxxl": 48}
RADIUS = {"sm": 6, "md": 10, "lg": 14, "xl": 18, "xxl": 22, "pill": 999}

# Shadows — usar QGraphicsDropShadowEffect
SHADOWS = {
    "light": {
        "sm":    {"blur": 4,  "offset": (0, 1),  "color": "rgba(15,23,42,.04)"},
        "md":    {"blur": 16, "offset": (0, 4),  "color": "rgba(15,23,42,.06)"},
        "card":  {"blur": 12, "offset": (0, 4),  "color": "rgba(15,23,42,.05)"},
        "ring":  {"blur": 20, "offset": (0, 4),  "color": "rgba(20,184,166,.30)"},
    },
    "dark": {
        "sm":    {"blur": 8,  "offset": (0, 2),  "color": "rgba(0,0,0,.4)"},
        "md":    {"blur": 24, "offset": (0, 8),  "color": "rgba(0,0,0,.5)"},
        "card":  {"blur": 30, "offset": (0, 10), "color": "rgba(0,0,0,.45)"},
        "glow":  {"blur": 40, "offset": (0, 0),  "color": "rgba(94,234,212,.18)"},
    },
}
```

### Gradiente firma

Para anillos de progreso, líneas de chart, botones primarios, badges destacados:

- **Light**: `linear-gradient(135deg, #2dd4bf 0%, #5eead4 50%, #a855f7 100%)`
- **Dark**: `linear-gradient(135deg, #22d3ee 0%, #5eead4 50%, #c084fc 100%)`

> En PyQt6 se usa `QLinearGradient(p1, p2)` con `setColorAt(t, QColor)`. Ya existe el helper en `shared/theme_qt.py` — actualizar las paradas de color.

---

## Componentes principales

> Los nombres en **bold** son los componentes JSX del prototipo HTML. La columna "Qt equivalente" indica qué clase / función ya existente en `shared/components_qt.py` debe actualizarse o ser sustituida.

| JSX (referencia)        | Qt equivalente                              | Notas |
|-------------------------|----------------------------------------------|-------|
| **V3Logo**              | `obtener_ruta_recurso("LOGO.png")` + QPixmap | Usar los logos cropeados `assets/logos-{light,dark}.png` y `assets/logos-icon-{light,dark}.png`. Aplicar `QGraphicsDropShadowEffect` con blur 8 + color teal para dark, sutil para light. |
| **V3Shell**             | `NeuroMoodApp` / `NeuroMoodHub` (QMainWindow)| Ya existen; aplicar la nueva paleta de fondo (`bg + bgAlt` gradient), border-radius 16 en ventana. |
| **V3Sidebar**           | `NMHubSidebar` (en `components_qt.py`)       | Sidebar 240px, logo 48px arriba, lista de nav items con icono + label + estado activo (background `tealSoft` + borde left 3px gradient). |
| **V3Header**            | `NMHeader` (existe)                          | 56px de alto, padding 28px. Slots: título h1 + subtítulo + chip streak + theme toggle + avatar. |
| **V3Card**              | `NMCard` (existe)                            | radius 14, border 1px `borderSoft`, padding 20-24. En dark con `glow=True`: gradiente translúcido + glow teal alrededor. |
| **V3Button**            | `NMButton` + `NMButtonOutline` (existen)     | 3 variantes: `gradient` (primary teal→violet), `secondary` (surface + border), `ghost`. Sizes sm/md/lg → height 32/40/48. Border radius pill. |
| **V3Ring** ⭐            | Repintar `_MiniRing` con `QConicalGradient`  | Anillo de progreso, **gradient teal→violet** consistente en TODA la app. Stroke proporcional al tamaño: `size <= 40 → stroke 3-4`, `size 60-100 → stroke 6-8`, `size 100+ → stroke 10-12`. |
| **V3WaveChart**         | pyqtgraph (ya integrado)                     | Spline + área bajo curva con gradiente teal→violet. Highlight = punto resaltado con halo. |
| **NMIcon** ⭐            | `nm_icon()` (existe, usa QtAwesome)          | **REEMPLAZAR QtAwesome por un sistema propio de SVG icons**. Ver lista de iconos abajo. Stroke 1.4-2.0 según tamaño. Sin círculo decorativo alrededor. |
| **NMMoodEmoji** ⭐ NUEVO | Crear `NMMoodEmoji` en `components_qt.py`    | 10 niveles. SVG line-style (no emoji Apple). Cara circular con ojos, boca curva, cejas (extremos), lágrimas (1-2), blush (7-10), sparkles (9-10). Color del nivel definido en MOOD_PALETTE. |
| **V3MoodSlider** ⭐ NUEVO| Crear como QWidget custom                    | Slashbar 1-10 con barra gradiente arcoíris emocional (azul→amarillo→verde→teal→violet). Emoji grande dinámico que cambia con el nivel. Click en número o emoji actualiza estado. |
| **NMPlayButton** ⭐ NUEVO| QPushButton circular pequeño                 | Background neutro (surface), border sutil, sombra suave. Icono play/pause/stop/skip/refresh interior. NO usar gradient. NO usar texto. Tamaños 40/48/56. |
| **V3Tabs**              | `stylesheet_tabwidget()` o pills custom      | Pills con padding 8x18, background `teal` en activo, surface en inactivos. Border-radius pill. |
| **V3Stepper** (inst.)   | `InstallerShell` (en `installer_common.py`)  | 3 o 5 pasos. Número en círculo (gradient si activo/done) + label. Línea conectora entre pasos. |
| **NMConfigRow**         | `NMSettingsSection.add_row()` (existe)       | Key-value row con separador `borderSoft`. Right slot acepta toggle, badge, valor. |
| **NMToggle**            | `NMToggle` (existe)                          | Switch pill 42x24 con knob blanco. Activo = gradient teal→violet con shadow. |
| **NMField**             | `NMInput` (existe)                           | Input con label arriba, fondo `surface`, border `border`. Soporta variant `mono` (JetBrains Mono) y `select` (con chevron). |
| **V3ChatBubble**        | `NMChatBubble` (existe)                      | Burbuja redondeada. User = gradient teal→violet, IA = surface + border. Soporta `typing` con 3 dots animados. |

### Lista de iconos (NMIcon)

Reemplazar QtAwesome por SVGs internos. Los paths exactos están en `js/v3-emojis.jsx` función `NMIcon`. Iconos disponibles:

```
home, mood, breath, lungs, brain, bulb, thought, routine, spark, sparkle,
timer, bell, user, cog, dashboard, users, ai, therapy, report, bookmark,
download, flame, heart, leaf, medicine, water, moon, sun, run,
check, plus, minus, arrowRight, arrowLeft, chevronDown, chevronRight,
play, pause, stop, skip, chart, barchart, search, calendar, clock,
edit, book, note, send, save, dots, list, grid, bolt, gem,
warning, info, close, refresh, target, trophy, handshake, palette
```

**Reglas de grosor de stroke según tamaño**:

```python
def icon_stroke_width(size):
    if size <= 14: return 1.4
    if size <= 18: return 1.5
    if size <= 24: return 1.6
    if size <= 32: return 1.7
    if size <= 48: return 1.8
    return 2.0
```

En PyQt6: cargar los SVGs como `QSvgRenderer` y pintarlos en un `QPixmap`, o renderizar paths con `QPainter` directamente.

---

## Mood emoji system (10 niveles)

Define en `shared/theme.py`:

```python
MOOD_PALETTE = {
    1:  {"from": "#5b6cb8", "to": "#3a4585", "glow": "#5b6cb8", "name": "Devastada"},
    2:  {"from": "#6c84d6", "to": "#445a9e", "glow": "#6c84d6", "name": "Muy triste"},
    3:  {"from": "#7ba8e6", "to": "#4c7cc4", "glow": "#7ba8e6", "name": "Triste"},
    4:  {"from": "#9eb4d8", "to": "#6a87b6", "glow": "#9eb4d8", "name": "Decaída"},
    5:  {"from": "#f5d76a", "to": "#daa520", "glow": "#f5d76a", "name": "Neutral"},
    6:  {"from": "#aee279", "to": "#7eb83a", "glow": "#aee279", "name": "Bien"},
    7:  {"from": "#5dd6a3", "to": "#1da678", "glow": "#5dd6a3", "name": "Contenta"},
    8:  {"from": "#36cfb8", "to": "#0d8f7f", "glow": "#36cfb8", "name": "Feliz"},
    9:  {"from": "#34cfd1", "to": "#7a72d8", "glow": "#7a72d8", "name": "Muy feliz"},
    10: {"from": "#a78bfa", "to": "#ec4899", "glow": "#c084fc", "name": "Eufórica"},
}
```

La función `NMMoodEmoji(level: int, size: int, glow: bool, is_dark: bool)` debe:

1. Dibujar un **círculo de línea** del color `palette[lv]["to"]`, sin relleno interior.
2. Dibujar dos ojos (círculos pequeños, mismo color).
3. Boca **curva** cuya forma depende del nivel (ver `MoodFeatures` en `js/v3-emojis.jsx` para los paths exactos).
4. Cejas solo en niveles 1-3 y 9-10 (líneas inclinadas).
5. **Lágrimas** en 1-2 (forma de gota).
6. **Blush** (mejillas) en 7-10 (círculos pequeños del color `from`).
7. **Sparkles** en 9-10 (estrellas de 4 puntas alrededor).
8. Si `glow=True`: halo radial detrás del círculo del color `glow` con opacidad 0.22 (dark) o 0.15 (light).

Implementar con `QPainter` sobre un `QPixmap` cuadrado, o renderizar SVG inline.

---

## Pantallas

### Suite · Inicio

- **Header**: título 26px "¡Hola, [nombre]!", subtítulo, chip de racha (🔥 + número días), theme toggle, avatar circular.
- **Hero card**: Ring de bienestar grande (size 120, stroke 11) + texto "Bienestar general" + número + nombre del estado en gradient text + microcopy.
- **Wave chart**: evolución de ánimo 7 días, gradient teal→violet, highlights en cada punto, eje Y con escala 0-10.
- **3 KPI bars**: Sesiones completadas, Minutos respiración, Actividades. Cada uno con icono + label + valor + barra de progreso gradient.
- **4 cards de módulos** (grid 4 col, 7° centrado en fila siguiente): cada card con título + chip de subcontexto + icono SVG (size 48, sin círculo) + estado + subtexto + botón gradient full-width.
- **3-col bottom**: Actividades recomendadas (lista 3 items con NMPlayButton), Sesión rápida (ring + NMPlayButton centrado), Avisos y agenda (lista 3 items).
- **Footer card**: cita motivacional + CTA gradient.

### Suite · Mood Tracker

- Header con selector de rango (7 días dropdown), botones export/chart.
- **Big wave chart** (height 280) con tooltip flotante mostrando emoji + fecha + valor.
- **Slashbar 1-10**: 
  - Header con título + descripción a la izquierda; a la derecha número grande del estado + emoji grande dinámico con halo de color.
  - Track con gradient arcoíris emocional (azul→amarillo→verde→teal→violet→rosa).
  - 10 dots clickables. El activo es 16x16 blanco con borde 3px del color del nivel + halo.
  - Mini-fila de 10 emojis preview abajo. El seleccionado escalado 1.18 con glow.
- **Nota del día**: textarea con contador 103/500 + botón Guardar.
- **3 insights cards**: Promedio (Ring), Racha (Ring), Progreso semanal (Ring). Todos con el mismo lenguaje visual.

### Suite · Respiración

- Big ring (size 340, stroke 14) animado con conteo regresivo + label "Inhala / Mantén / Exhala".
- 3 step cards con tiempos de cada fase.
- Historial: 4 cards mini con fecha + duración + ring chico.
- Right rail: cronometro mono + ritmo cardíaco + calma con barra gradient.

### Suite · TCC

- Stepper horizontal 4 pasos.
- Grid 4x2 de emociones (Ansiedad, Tristeza, Enojo, Miedo, Culpa, Vergüenza, Soledad, Otro). Cada una con icono + label, seleccionada con background `tonalSoft` + border + shadow.
- Slashbar de intensidad (fría → caliente, gradient azul→amarillo→rojo).
- Resumen lateral con los pasos previos llenados.
- Tip terapéutico (card glow).
- Tabla de registros anteriores.

### Suite · Rutina

- Hero card: Ring grande de progreso del día + label + descripción + botón "Nueva tarea".
- 3 cards (Mañana / Tarde / Noche): icono temático, ring chico de progreso, lista de tareas con checkbox custom, botón ghost "Agregar tarea".

### Suite · Actividades

- Card de categorías con 6 mini-rings (cada uno con icono dentro).
- 3 cards "Sugeridas para ti" con icono grande, badge categoría, intensidad (3 dots).
- Tabla "Otras opciones" con icono + nombre + cat + rango ánimo + intensidad + botón play.

### Suite · Timer

- Big ring (size 340, stroke 14) con tiempo grande mono + descripción + chip "Sesión en curso".
- 3 botones de control circulares (skip / play|pause / refresh).
- Right rail: detalles de sesión + lista de sesiones del día.

### Suite · Recordatorios

- Stepper 3 pasos.
- Card de búsqueda + tabs + filtro por categoría.
- Grid 3 col de cards de recordatorio: icono grande coloreado, categoría, nombre, descripción, hora (chip teal/violet/etc), frecuencia, status badge, botón "Completar". Cards con background tinted según highlight.
- Footer card de progreso del día.

### Hub · Pacientes (Dashboard)

- Header con título "Pacientes" + N vinculados + botones sincronizar/nuevo.
- Card de búsqueda + chips de filtro (Todos / Activos / Sin registros / Atención).
- Tabla de pacientes con: avatar gradient, nombre + ID, etiqueta clínica, ánimo numérico (color por valor), adherencia (ring 32px + %), última sesión, botón abrir/ver.

### Hub · Detalle paciente

- Header: avatar 56px con dot online + nombre 22px + breadcrumb (ID, semana, etiqueta).
- 4 tabs: Registros, Asignar, Banco, IA.
- **Registros**: wave chart 30 días + adherencia por módulo + tabla de eventos recientes.
- **Asignar**: 2 cards (tarea de rutina + recordatorio remoto) + lista de asignaciones vigentes.
- **Banco**: form de nueva actividad (con CTA IA completar) + lista del banco.
- **IA**: resumen ejecutivo en card glow + 3 acciones sugeridas con CTA aplicar.

### Hub · IA Asistente

- Layout 2-col: chat principal + sidebar de contexto.
- Chat con burbujas user (gradient) y IA (surface). Soporta typing dots.
- Las respuestas IA pueden tener `MiniStat` tiles y cards de acciones inline.
- Quick prompts arriba del input (chips).
- Input con icon + textarea + botón send gradient.
- Sidebar derecho: paciente activo + contexto + datos cargados.

### Hub · Configuración

- Sync hero card con orb verde + última verificación + botón sincronizar.
- 4 grid 2x2: Conexión Supabase, Apariencia (Tema/Densidad/Idioma/IA), Seguridad, Log de sincronización (mono).

### Installer (5 pasos)

- Shell común con logo arriba + stepper compacto + footer con botones.
- Dark theme **por defecto** (siempre).
- Tipo de botón gradient teal→violet.
- Pasos: Bienvenida (3 features), Cuenta (form email+pass con confirmación), Consentimiento (texto legal scrollable + checkbox + warning crisis), Instalación (progress bar gradient + log mono), Finalizar (check grande gradient + 4 cards de info).

### Uninstaller (3 pasos)

- Dark theme **por defecto**.
- Accent danger (rojo → amarillo) en stepper y progress.
- Pasos: Confirmar (warning + carpeta + toggle conservar datos), Eliminando (progress rojo + log mono), Finalizado (check verde + card de datos conservados).

---

## Interacciones y transiciones

- **Theme toggle**: switch en el header funciona individualmente por ventana. Transición CSS de 350ms en `background-color, color, border-color, box-shadow, filter`. En Qt: usar `QPropertyAnimation` sobre los properties relevantes.
- **Hover en cards**: leve elevación + cambio de border-color a `borderStrong` (sin scale, sin movimiento horizontal).
- **Click en botones**: scale 0.97 durante 100ms.
- **Sesiones de respiración/timer**: el ring se anima de 0% a 100% a lo largo de la duración. Usar `QPropertyAnimation` sobre una property custom `progress`.
- **Mood slider**: al arrastrar, el emoji grande y el label de estado se actualizan en tiempo real con `transition: filter .3s ease`.
- **Chat typing dots**: 3 dots con animación `translateY(-4px)` escalonada (delay 0/0.15/0.3s).
- **Sync orb**: punto verde con halo pulsante (escala 1→1.6 + fade out, infinite).

---

## Theme toggle global

Botón único en el header de cada app cambia entre light y dark de forma persistente:

1. Guardar preferencia en SQLite (`config` table key `theme_mode`).
2. Al toggle: aplicar transición de 350ms en root QWidget palette + stylesheet base.
3. Todos los widgets que respeten `ThemeAwareWidgetMixin` se actualizan automáticamente.
4. **Instaladores siempre dark**, sin toggle.

Para que la transición sea fluida sin bugs:
- No reconstruir widgets, solo cambiar stylesheets / repaint.
- Usar `QGraphicsBlurEffect` solo donde sea estrictamente necesario (dark surfaces translúcidas).
- Cachear pixmaps de íconos por modo.

---

## Assets

Logos cropeados y listos para usar (fondos transparentes):

- `assets/logos-light.png` — logo completo (brain + wordmark) para light theme
- `assets/logos-dark.png` — logo completo para dark theme
- `assets/logos-icon-light.png` — solo brain, para sidebar / titlebar light
- `assets/logos-icon-dark.png` — solo brain, para sidebar / titlebar dark
- `assets/LOGO.png` — fuente original (no usar directamente)

El logo debe llevar `QGraphicsDropShadowEffect` con:
- Light: blur 4, offset (0,2), color `rgba(15,23,42,.10)`
- Dark: aplicar dos drop shadows (no soportado nativo, simular con dos efectos en cascada o pintar el glow como QPixmap previo): blur 8 + `rgba(94,234,212,.45)`, encima blur 14 + `rgba(168,85,247,.30)`.

---

## Cómo trabajar con este bundle

1. **Abrí `NeuroMood Redesign.html`** en un browser local para ver todas las pantallas finales. Usá el panel Tweaks (esquina inferior derecha) para alternar entre light/dark globalmente. Cada artboard también tiene su propio toggle.
2. **Para cada pantalla del codebase Python**:
   - Identificá la pantalla equivalente en el HTML (sección 01-04).
   - Abrí el archivo `.jsx` correspondiente (`js/v3-screens.jsx`, `js/v3-screens-extra.jsx`, `js/v3-installers.jsx`) para ver el código de referencia con valores exactos (colores, paddings, sizes).
   - Refactorizá el archivo `.py` equivalente en `app/`, `hub/`, `installers/` para reflejar el nuevo diseño usando los componentes Qt actualizados.
3. **Orden recomendado**:
   1. Refactorizar `shared/theme.py` con los tokens v3 completos.
   2. Refactorizar `shared/theme_qt.py` con gradient builders y helpers actualizados.
   3. Refactorizar `shared/components_qt.py`: NMCard, NMButton, NMRing, NMIcon (reemplazar QtAwesome), NMMoodEmoji (nuevo), V3MoodSlider (nuevo), NMPlayButton (nuevo), V3Tabs.
   4. Pantallas Suite en orden: Inicio → Mood Tracker → Respiración → TCC → Rutina → Actividades → Timer → Avisos.
   5. Pantallas Hub: Dashboard → Detalle → IA → Configuración.
   6. Installer + Uninstaller.

## Validación

Después de cada pantalla migrada:

- Compará visualmente con el HTML correspondiente (mismas proporciones, colores, espaciado).
- Verificá que el toggle de tema funcione sin bugs (no se rompan widgets, no haya flashes).
- Verificá que TODOS los anillos de progreso usen el mismo gradiente y stroke proporcional al tamaño.
- Verificá que NINGÚN emoji de Apple / Unicode quede en la UI — todos deben ser NMIcon SVG o NMMoodEmoji.
- Verificá que los logos se vean correctamente en ambos temas (con glow apropiado en dark).
- Corré el modo `visual_qa` (`NM_VISUAL_QA=1`) para tener datos demo cargados y validar todas las pantallas con contenido.

## Restricciones (NO TOCAR)

- Lógica de DB / SQLite.
- Sincronización con Supabase.
- Autenticación.
- Motor de activación.
- Daemon de avisos.
- Nombres de archivos críticos.
- API de `hub/ia_asistente.py`.

Los cambios son **estrictamente visuales**.

---

## Archivos en este bundle

```
design_handoff_neuromood_v3/
├── README.md                       ← este archivo
├── NeuroMood Redesign.html         ← canvas con todas las pantallas (abrir en browser)
├── design-canvas.jsx               ← starter del canvas (no tocar)
├── tweaks-panel.jsx                ← panel de tweaks (no tocar)
├── js/
│   ├── app.jsx                     ← composer del canvas
│   ├── v3-kit.jsx                  ← Shell, Sidebar, Header, Card, Button, Ring, WaveChart, Tabs
│   ├── v3-emojis.jsx               ← MOOD_PALETTE, NMMoodEmoji, NMIcon, V3MoodSlider
│   ├── v3-neural.jsx               ← NMPlayButton (control circular minimal)
│   ├── v3-screens.jsx              ← Suite: Inicio, Mood Tracker, Respiración, Avisos + Hub Dashboard
│   ├── v3-screens-extra.jsx        ← Suite: TCC, Rutina, Actividades, Timer + Hub Detalle/IA/Config
│   └── v3-installers.jsx           ← Installer (5 pasos) + Uninstaller (3 pasos)
└── assets/
    ├── LOGO.png                    ← logo source
    ├── logos-light.png             ← logo completo light
    ├── logos-dark.png              ← logo completo dark
    ├── logos-icon-light.png        ← solo brain light
    └── logos-icon-dark.png         ← solo brain dark
```
