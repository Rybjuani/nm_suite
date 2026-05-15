# NeuroMood V3 — UI/UX Guide

## Paleta Oficial Dark (modo principal)

| Token | Hex | Uso |
|---|---|---|
| `bg_primary` | `#080910` | Fondo principal de ventana |
| `bg_secondary` | `#111420` | Header, sidebar, footer |
| `bg_surface` | `#1a1f2e` | Cards, frames |
| `bg_elevated` | `#1e293b` | Hover states, elevated panels |
| `bg_input` | `#141925` | Inputs de texto |
| `accent` | `#6366f1` | Botones primarios, highlights |
| `accent_hover` | `#818cf8` | Hover de botón primario |
| `teal` | `#14b8a6` | Gradientes secundarios, scrollbars |
| `violet` | `#a855f7` | Gradientes, glow |
| `text_primary` | `#f1f5f9` | Títulos, textos principales |
| `text_secondary` | `#94a3b8` | Textos secundarios |
| `text_tertiary` | `#64748b` | Subtítulos, placeholder |
| `text_on_accent` | `#ffffff` | Texto sobre fondo accent |
| `border` | `#2a3040` | Bordes de cards |
| `border_card` | `#2a3040` | Borde de card (mismo que border) |
| `border_focus` | `#6366f1` | Borde de input en focus |
| `success` | `#10b981` | Éxito, completado |
| `warning` | `#f59e0b` | Advertencia |
| `error` | `#ef4444` | Error, danger |

---

## Gradientes

### Primario (3-stop) — Botones, accent
```css
background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
    stop:0 #6366f1, stop:0.45 #14b8a6, stop:1 #a855f7);
```

### Scrollbar handle
```css
background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 #14b8a6, stop:1 #6366f1);
```

### Scrollbar hover
```css
background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 #6366f1, stop:1 #a855f7);
```

### Left bar (cards)
```css
/* Usar SessionColor para el top, accent para bottom */
SessionColor.qcolor(modo, 180) → QColor(accent)
```

---

## Cards (NMCard)

```python
card = NMCard(accent_color="#6366f1", clickable=True, modo=self._modo)
```

- **Border**: `1px solid border_card` con alpha 60
- **Left bar**: 5px, gradiente vertical session→accent
- **Hover glow**: 3 capas concéntricas de `drawRoundedRect` con session color, alpha decreciente
- **Noise overlay**: `noise_overlay()` con opacity 0.025
- **Radius**: `RADIUS_CARD = 12px`
- **Padding**: `PAD_CARD = 16px`

---

## Botones

### Primario (NMButton)
Gradiente 3-stop fill, texto white, ripple animado. Usar para: Siguiente, Guardar, Finalizar, Iniciar.

```python
btn = NMButton("Siguiente →", modo=self._modo, width=140, height=36)
```

### Secundario / Outline (NMButtonOutline)
Fondo transparente, borde `2px solid accent`, texto accent. Usar para: Cancelar, Anterior, Opciones.

```python
btn = NMButtonOutline("Cancelar", modo=self._modo)
# Default: toggleable=False — NO alterna estado al click
```

### Segmented Choice (NMSegmentedChoice)
Grupo de NMButtonOutline con selección exclusiva. Emite `choice_made(value)`.

```python
seg = NMSegmentedChoice([("Hecha", "hecha"), ("No pude", "no_pude")], modo=self._modo)
seg.choice_made.connect(lambda v: self._handle(v))
```

### Danger
Usar `NMButton` con texto claro. El color danger se aplica vía `set_accent()` en NMCard, no en botones directamente.

---

## Componentes Reutilizables

| Componente | Uso |
|---|---|
| `NMButton` | Botón primario con gradiente |
| `NMButtonOutline` | Botón secundario con borde |
| `NMCard` | Card con glow + barra izquierda |
| `NMInput` | Input estilizado con focus animation |
| `NMToggle` | Toggle switch pill |
| `NMProgressBar` | Barra de progreso con shimmer |
| `NMSkeleton` | Loading placeholder |
| `NMToast` | Notificación flotante |
| `NMStatusChip` | Pill de estado con color semántico |
| `NMSectionCard` | Card con título decorativo + content_layout() |
| `NMFormField` | Label + input en fila horizontal |
| `NMSegmentedChoice` | Grupo de botones con selección exclusiva |
| `NMHeader` | Header de 56px con logo + toggle |
| `NMSidebar` | Sidebar de navegación 220px |
| `NMFadeWidget` | QStackedWidget con transición fade |

---

## Empty States

- **Texto**: `QLabel` centrado con `text_tertiary`, informativo
- **Sin carga**: No mostrar `NMSkeleton` si ya se sabe que no hay datos
- **Con carga**: `NMSkeleton` shimmer mientras se espera respuesta

```python
empty = QLabel("Sin pacientes registrados.\nUsa la seccion Pacientes para vincular.")
empty.setFont(qfont("size_body"))
empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
empty.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
```

---

## Iconografía

- **Módulos paciente**: Emojis en HomeView (`🎭`, `🌬️`, `📝`, `✅`, `⚡`, `⏱️`, `🔔`)
- **Hub sidebar**: `nm_icon(key, color, size)` — sistema vectorial unificado
- **Installers**: Sin iconos decorativos — solo logo y pasos numerados
- **Estados**: `NMStatusChip` para pills de estado (éxito, error, warning)

---

## Spacing / Padding

| Constante | Valor | Uso |
|---|---|---|
| `PAD_CONTAINER` | 24px | Márgenes de container |
| `PAD_CARD` | 16px | Márgenes internos de card |
| `GAP_CARDS` | 16px | Espacio entre cards en grid |
| `GAP_ELEMENTS` | 12px | Espacio entre controles |
| `RADIUS_CARD` | 12px | Bordes de card |
| `RADIUS_BUTTON` | 8px | Bordes de botón |
| `RADIUS_INPUT` | 8px | Bordes de input |
| `RADIUS_PILL` | 16px | Bordes de chip/pill |

**Installer Shell**: header 50px, footer 52px, content area stretch, step indicators 22px circles.

---

## Reglas para Installers / Uninstallers

1. **Header**: Logo + nombre de app + pasos numerados
2. **Footer**: `btn_ant` (outline, oculto en página 0) + `btn_sig` (gradient)
3. **Tamaños**: Suite 740×540, Hub 680×500, Uninstallers 480×340
4. **Colores**: Usar `shared/installer_common.py` — misma paleta dark que la app
5. **Scrollbars**: Mismo diseño glass que la app
6. **Dark siempre**: Title bar forzado dark mode
7. **Base class**: `InstallerShell` — provee header, footer, stack, fade transitions

---

## SessionColor (Aura Dinámica)

Selecciona aleatoriamente cyan o violeta al iniciar sesión:

| Modo | Cyan | Violet |
|---|---|---|
| Dark | `#00F2FE` | `#7367F0` |
| Light | `#89F7FE` | `#E0C3FC` |

- **Aura radial**: `NMModule.paintEvent` / `DashboardView.paintEvent` — centro-izquierda, alpha 20-30
- **Hover glow**: 3 capas `drawRoundedRect` con alpha decreciente
- **Left bar**: Gradiente vertical `session(180)→session(40)`

---

## Assets

| Archivo | Uso | Tamaño en UI |
|---|---|---|
| `LOGO.png` | Header paciente | 140×28 px |
| `LOGO.png` | Sidebar Hub | 168×36 px |
| `LOGO.png` | Installer header | 110×30 px (thumbnail) |
| `NM_icon.ico` | Icono de ventana | Sistema |
| `installer_icon.ico` | Icono installer | Sistema |
| `no_symbol.ico` | Icono uninstaller | Sistema |

**Pendiente**: No existen variantes light/dark/compact de LOGO.png. En light mode se recolorea automáticamente vía `recolorear_logo_light()`.

---

## Scrollbars

Handle: gradiente `teal→accent` idle, `accent→violet` hover. Track: `rgba(255,255,255,0.05)`. 6px ancho. Cápsula 3px. Sin flechas. Aplicado en:
- `stylesheet_base()` — global
- `stylesheet_scrollarea()` — QScrollArea específicas
- `stylesheet_installer()` — installers

---

## Validación final

- [x] compileall . pasa
- [x] 28/28 imports OK
- [x] Sin textos cortados en tamaños mínimos
- [x] Sin botones superpuestos
- [x] Sin overflow horizontal
- [x] Sin emojis como icono principal (Hub usa nm_icon)
- [x] Sin skeletons en estado vacío
- [x] Botones con lenguaje visual unificado
- [x] Cards con padding/radio/borde coherente
- [x] Installers parecen mismo producto
- [x] Dark mode completo y consistente
- [x] Light mode funcional (stylesheet_base se reaplica en toggle)
