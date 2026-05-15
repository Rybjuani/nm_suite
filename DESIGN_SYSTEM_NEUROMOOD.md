# DESIGN SYSTEM — NeuroMood V3
*Versión 1.0 — Mayo 2026*

> Source of truth visual para Suite, Hub, instaladores y desinstaladores.
> Toda pantalla nueva debe derivarse de este documento.

---

## 1. PALETA OFICIAL

### Dark Hybrid (modo principal)

| Token | Hex | Uso |
|---|---|---|
| `bg_primary` | `#080910` | Fondo de ventana |
| `bg_secondary` | `#111420` | Fondo de sección / caption bar |
| `bg_surface` | `#181c30` | Superficie de cards |
| `bg_elevated` | `#1f243b` | Cards elevadas, hover de lista |
| `bg_overlay` | `#282d48` | Overlays, paneles flotantes |
| `bg_glass` | `#181c30bb` | Glassmorphism (panels inline) |
| `bg_input` | `#1a1e33` | Inputs, textareas |
| `accent` | `#6366f1` | Indigo — acción principal, foco, barra izquierda |
| `accent_hover` | `#4f52d4` | Estado hover del accent |
| `accent_glow` | `#1e1f5e` | Fondo sutil bajo accent |
| `teal` | `#14b8a6` | Confirmación, scrollbar handle |
| `teal_hover` | `#0d9488` | Hover de teal |
| `violet` | `#a855f7` | Acento secundario, scrollbar fin |
| `violet_hover` | `#9333ea` | Hover de violet |
| `cyan` | `#22d3ee` | Info, badges de estado activo |
| `text_primary` | `#f0f6ff` | Texto principal |
| `text_secondary` | `#8892a4` | Texto secundario, placeholders |
| `text_tertiary` | `#4e5668` | Texto desactivado, captions |
| `text_on_accent` | `#ffffff` | Texto sobre fondo accent |
| `border` | `#1e2238` | Bordes sutiles |
| `border_accent` | `#2d2f7a` | Bordes con acento suave |
| `border_focus` | `#6366f1` | Borde de foco en inputs |
| `border_card` | `#1a1d30` | Borde de cards |
| `success` | `#10b981` | Completado, guardado |
| `warning` | `#f59e0b` | Advertencia |
| `error` | `#ef4444` | Error, validación fallida |
| `info` | `#3b82f6` | Información neutra |
| `progress_track` | `#181b2e` | Pista de progreso |
| `progress_fill` | `#6366f1` | Relleno de progreso |

### Light Hybrid (modo diurno)

| Token | Hex | Uso |
|---|---|---|
| `bg_primary` | `#f4f7fb` | Fondo de ventana |
| `bg_surface` | `#ffffff` | Cards |
| `bg_elevated` | `#e8eef7` | Cards elevadas |
| `accent` | `#4f46e5` | Indigo oscuro |
| `teal` | `#0d9488` | Confirmación |
| `violet` | `#7c3aed` | Acento secundario |
| `text_primary` | `#0f172a` | Texto principal |
| `text_secondary` | `#334155` | Texto secundario |
| `border_focus` | `#4f46e5` | Borde de foco |
| `success` | `#059669` | |
| `warning` | `#d97706` | |
| `error` | `#dc2626` | |

---

## 2. GRADIENTE OFICIAL

Siempre 3 paradas: **indigo → teal → violet**

```
Dark:  #6366f1 @ 0.0 → #14b8a6 @ 0.45 → #a855f7 @ 1.0
Light: #4f46e5 @ 0.0 → #0d9488 @ 0.45 → #9333ea @ 1.0
```

**Uso en código:**
```python
grad = rich_gradient(self.rect(), modo)        # linear 135°
grad = conical_arc_gradient(center, 90, modo)  # para arcos
```

---

## 3. TIPOGRAFÍA

### Familia
- **Primaria:** Inter Variable / Satoshi (si están en `assets/fonts/`)
- **Fallback:** Segoe UI → Arial

### Escala (usar `nm_font()` o `qfont()`)

| Nivel | Tamaño | Peso | Función |
|---|---|---|---|
| `display` | 28pt | 700 | Pantallas de celebración, onboarding |
| `h1` | 22pt | 600 | Títulos de módulo |
| `h2` | 18pt | 600 | Subtítulos de sección |
| `h3` | 15pt | 500 | Labels de grupo, encabezados de card |
| `body` | 13pt | 400 | Texto de contenido |
| `sm` | 12pt | 400 | Texto secundario, chips |
| `caption` | 11pt | 400 | Metadata, timestamps |

```python
# Correcto
lbl.setFont(nm_font("h2"))
lbl.setFont(qfont("size_h2", bold=True))

# Incorrecto — NO hacer
lbl.setFont(QFont("Segoe UI", 18))
```

---

## 4. ESPACIADO

Usar la función `sp()` y el diccionario `SPACE`:

| Token | Valor | Uso |
|---|---|---|
| `xs` | 4px | Gap mínimo, padding de chips |
| `sm` | 8px | Gap entre elementos inline |
| `md` | 16px | Gap entre cards |
| `lg` | 24px | Padding de contenedor |
| `xl` | 32px | Espacio entre secciones |
| `xxl` | 48px | Espacio mayor, separadores de página |

Tokens de LAYOUT:
```python
PAD_CONTAINER = 24   # padding_container
PAD_CARD      = 20   # padding_card
GAP_CARDS     = 16   # gap_cards
GAP_ELEMENTS  = 12   # gap_elements
HEADER_H      = 56   # header_height
```

---

## 5. RADIOS DE BORDE

Siempre usar constantes, nunca pixeles hardcodeados:

| Constante | Valor | Aplicar en |
|---|---|---|
| `RADIUS_BUTTON` | 10px | Botones primarios y outline |
| `RADIUS_CARD` | 16px | Cards, paneles, frames de sección |
| `RADIUS_INPUT` | 10px | Inputs, textareas, combobox |
| `RADIUS_PILL` | 24px | Chips de preset, badges, pills |
| `RADIUS_BADGE` | 20px | Badges de estado |
| `RADIUS_MODAL` | 20px | Modales, paneles flotantes |

```python
# Correcto
f"border-radius: {RADIUS_CARD}px;"
f"border-radius: {LAYOUT['radius_input']}px;"

# Incorrecto — NO hacer
f"border-radius: 16px;"
```

---

## 6. SOMBRAS Y GLOW

Usar `shadow_effect()` de `theme_qt.py`:

```python
# Card normal
widget.setGraphicsEffect(shadow_effect("card", modo))

# Card en hover
widget.setGraphicsEffect(shadow_effect("card_hover", modo))

# Glow de accent (indigo)
widget.setGraphicsEffect(shadow_effect("glow_teal", modo))

# Glow de violet
widget.setGraphicsEffect(shadow_effect("glow_violet", modo))
```

---

## 7. COMPONENTES BASE

### NMButton
```python
NMButton("Guardar", modo=self._modo, parent=self)
```
- Gradiente indigo→teal→violet
- Ripple click animado
- `play_success()` para confirmación verde
- Nunca usar QPushButton directamente para acciones primarias

### NMButtonOutline
```python
NMButtonOutline("Cancelar", modo=self._modo, toggleable=False)
```
- `toggleable=False` por defecto — solo alterna si `toggleable=True`
- Para grupos exclusivos, usar `NMSegmentedChoice`

### NMCard
```python
card = NMCard(modo=self._modo, parent=self)
card.content_layout.addWidget(...)
```
- Glow en hover (3 capas concéntricas)
- Noise texture sutil
- Barra izquierda con SessionColor

### NMInput
```python
inp = NMInput(placeholder="Nombre", modo=self._modo)
```
- Focus ring animado (borde accent 200ms)
- Nunca usar QLineEdit directamente en formularios

### NMToast
```python
NMToast.display(self.window(), "Guardado", variant="success")
NMToast.display(self.window(), "Advertencia", variant="warning")
NMToast.display(self.window(), "Error", variant="error")
```
- Siempre mostrar sobre `self.window()` para que persista en navegación

### NMHeader
```python
header = NMHeader(modo=self._modo)
header.set_back_action(self._go_home)  # botón volver
header.set_back_action(None)           # ocultar botón
```

### NMEmptyState
```python
NMEmptyState("animo", "Sin registros", "Registrá tu primer ánimo", parent=self)
```
- Usar SIEMPRE en lugar de dejar layouts vacíos
- NUNCA mostrar NMSkeleton como estado vacío real

### NMSkeleton
```python
sk = NMSkeleton(width=240, height=16, radius=4, modo=self._modo)
```
- Solo durante carga asíncrona (mientras se hace fetch)
- Reemplazar con contenido real o NMEmptyState al terminar

### NMStatusChip
```python
NMStatusChip("Activo", color="success", modo=self._modo)
```

### NMSectionCard
```python
sec = NMSectionCard("Sección", modo=self._modo)
sec.content_layout().addWidget(...)
```

### NMSegmentedChoice
```python
seg = NMSegmentedChoice(["Opción A", "Opción B"], modo=self._modo)
seg.choice_made.connect(self._on_choice)
```

---

## 8. SCROLLBARS

**Siempre** usar las funciones de stylesheet, nunca hardcodear:

```python
# En QScrollArea
scroll.setStyleSheet(stylesheet_scrollarea(modo))

# En QApplication (global)
app.setStyleSheet(stylesheet_base(modo))
```

Tokens usados internamente (teal handle, accent hover):
- Handle: `C("teal") → C("accent")` gradiente
- Hover: `C("accent") → C("violet")` gradiente
- Track: `rgba(255,255,255,0.05)`, 6px

---

## 9. FOCUS RINGS

Aplicar en todos los widgets interactivos:
```python
widget.setStyleSheet(focus_ring_stylesheet(modo))
widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
```

NMInput, NMButton y NMButtonOutline ya lo incluyen internamente.
Para QLineEdit custom, usar `stylesheet_lineedit(modo)`.

---

## 10. SESSION COLOR (aura dinámica)

`SessionColor` elige aleatoriamente cyan o violet al iniciar sesión:

```python
sc = SessionColor.instance()
color = sc.hex_for(modo)         # hex
aura  = sc.aura_qcolor(modo)    # QColor alpha 20-30 (para fondo radial)
glow  = sc.glow_qcolor(modo)    # QColor alpha 180 (para sombras)
```

**Aura radial** (en `paintEvent` de módulos):
- Centro: `(w*0.2, h*0.5)`, radio `w*0.85`
- Alpha 20 dark / 30 light

**Barra izquierda de cards**: gradiente vertical con SessionColor top → accent bottom.

---

## 11. REGLAS DE USO — LO QUE NO SE HACE

| ❌ Incorrecto | ✅ Correcto |
|---|---|
| `"color: #6366f1"` | `f"color: {C('accent', modo)}"` |
| `QFont("Segoe UI", 14)` | `qfont("size_body")` o `nm_font("body")` |
| `"border-radius: 16px"` | `f"border-radius: {RADIUS_CARD}px"` |
| `"padding: 24px"` | `f"padding: {PAD_CONTAINER}px"` |
| `"font-size: 12pt"` | `f"font-size: {TYPOGRAPHY['size_small']}pt"` |
| `except: pass` en widgets | `_log.exception("contexto")` |
| `NMSkeleton` en estado vacío | `NMEmptyState(...)` |
| `QPushButton` para acción principal | `NMButton(...)` |
| `QLineEdit` sin estilo | `NMInput(...)` o `stylesheet_lineedit(modo)` |
| Color hardcodeado en `paintEvent` | `QColor(C("accent", modo))` |

---

## 12. STYLESHEETS ESTÁNDAR DISPONIBLES

| Función | Widget | Cuándo usar |
|---|---|---|
| `stylesheet_base(modo)` | QApplication | Al iniciar o cambiar tema (global) |
| `stylesheet_scrollarea(modo)` | QScrollArea | En cada scroll area |
| `stylesheet_slider(modo)` | QSlider | En módulo Ánimo y similares |
| `stylesheet_textedit(modo)` | QTextEdit / QPlainTextEdit | En textareas de Registro TCC |
| `stylesheet_lineedit(modo)` | QLineEdit | En inputs no-NMInput |
| `stylesheet_combobox(modo)` | QComboBox | En selects del Hub |
| `stylesheet_timeedit(modo)` | QTimeEdit | En Avisos |
| `stylesheet_tabwidget(modo)` | QTabWidget | En Hub pacientes tabs |

---

## 13. CATEGORY COLORS (activación conductual)

```python
CATEGORY_COLORS = {
    "Autocuidado": "#6366f1",   # accent
    "Física":      "#22D47E",   # verde
    "Cognitiva":   "#9B8FE8",   # lavanda
    "Placer":      "#F0A500",   # amber
    "Social":      "#E8505B",   # coral
    "Maestría":    "#4A9EE8",   # azul
}
```

---

## 14. ICONOS (QtAwesome)

```python
nm_icon("animo",       color, size)  # fa5s.heart
nm_icon("respiracion", color, size)  # fa5s.wind
nm_icon("registro_tcc",color, size)  # fa5s.brain
nm_icon("rutina",      color, size)  # fa5s.tasks
nm_icon("actividades", color, size)  # fa5s.running
nm_icon("timer",       color, size)  # fa5s.hourglass-half
nm_icon("avisos",      color, size)  # fa5s.bell
```

Fallbacks automáticos definidos en `_ICON_FALLBACKS`.
Color siempre desde `C("text_primary", modo)` o token semántico.

---

## 15. INSTALADORES — REGLAS ESPECÍFICAS

- Usar `stylesheet_installer()` de `shared/installer_common.py`
- Caption bar siempre dark (sin flash de tema al abrir)
- `InstallerShell` como clase base obligatoria
- `recurso(nombre)` para rutas de assets (dev + frozen)
- `QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)` en pasos largos

---

## 16. CHECKLIST PARA PANTALLAS NUEVAS

Antes de dar por terminada cualquier pantalla nueva:

- [ ] Todos los colores usan `C()` o tokens del tema
- [ ] Todas las fuentes usan `nm_font()` o `qfont()`
- [ ] Todos los radios usan constantes `RADIUS_*`
- [ ] Todos los paddings/gaps usan `sp()`, `PAD_*`, `GAP_*`
- [ ] QScrollArea tiene `stylesheet_scrollarea(modo)`
- [ ] QTextEdit tiene `stylesheet_textedit(modo)`
- [ ] Los widgets interactivos tienen `focus_ring_stylesheet(modo)`
- [ ] Toda acción principal usa `NMButton`, no `QPushButton`
- [ ] Todo estado vacío usa `NMEmptyState`, no widget vacío ni skeleton
- [ ] `NMToast.display(self.window(), ...)` para feedback al usuario
- [ ] `_apply_theme(modo)` implementado y conectado a `ThemeManager`
- [ ] `sip.isdeleted(self)` en todo `QTimer.singleShot` con lambda que capture `self`
- [ ] `removeWidget()` antes de `deleteLater()` en widgets con layout
- [ ] `python -m compileall .` sin errores
- [ ] `smoke_test_runner.py --app patient` 31/31 PASS
- [ ] `smoke_test_runner.py --app hub` 16/16 PASS

---

## 17. ESTADO DE AUDITORÍA — MAYO 2026

> Auditoría automatizada ejecutada tras commit `49db9a7`. **0 inconsistencias pendientes.**

### Tokens aplicados (fases A–E)

| Archivo | Fix aplicado |
|---|---|
| `shared/theme.py` | `RADIUS_SMALL=6`, `CHECKBOX_SIZE=18` agregados a `LAYOUT` |
| `shared/theme_qt.py` | `RADIUS_SMALL`, `CHECKBOX_SIZE`, `qcolor_to_rgba_css()` exportados |
| `shared/components_qt.py` | Re-exporta los nuevos tokens |
| `app/modules/avisos_qt.py` | `font-size` → `TYPOGRAPHY['size_caption']`; banner → `RADIUS_INPUT` |
| `app/modules/rutina_qt.py` | Checkbox → `CHECKBOX_SIZE`/`RADIUS_SMALL`; form → `RADIUS_INPUT`; input → `RADIUS_SMALL`; eliminado `font-size` redundante |
| `app/modules/animo_qt.py` | rgba manual → `qcolor_to_rgba_css(fill)` |
| `app/modules/registro_tcc_qt.py` | Badge distorsión → `RADIUS_BADGE` |
| `hub/exportar.py` | `AC="#6366f1"` → `_PDF_ACCENT` desde `COLORS`; `#555555` → `_PDF_CAPTION` |
| `hub/pacientes_qt.py` | `row_item` → `RADIUS_SMALL`; `btn_del` → `RADIUS_PILL` |
| `installers/*` | Sin cambios — ya usaban tokens de `installer_common.py` |

### Checklist de auditoría automática

| Check | Resultado |
|---|---|
| Hex literals hardcodeados en app/ hub/ | ✅ 0 |
| `border-radius` px literales sin token | ✅ 0 |
| `font-size` pt/px literales sin token | ✅ 0 |
| `QFont()` directo sin `qfont()`/`nm_font()` | ✅ 0 |
| `setContentsMargins` con literales directos | ✅ 0 |
| `setSpacing` con literales directos | ✅ 0 |
| `QScrollArea` sin `stylesheet_scrollarea()` | ✅ 0 |
| `QComboBox` sin `stylesheet_combobox()` | ✅ 0 |
| `QTimeEdit` sin `stylesheet_timeedit()` | ✅ 0 |
| `NMModule` sin `_apply_theme()` | ✅ 0 |
| `NMModule` sin conexión a `ThemeManager` | ✅ 0 |
| `except: pass` silenciosos en widgets | ✅ 0 |
| smoke patient | ✅ 31/31 |
| smoke hub | ✅ 16/16 |
| resize 5 resoluciones | ✅ 0 issues |
| `python -m compileall .` | ✅ sin errores |

---

## 18. ARCHIVOS CLAVE DE REFERENCIA

| Propósito | Archivo |
|---|---|
| Tokens de color / tipografía / layout | `shared/theme.py` |
| Funciones Qt (C, qfont, shadow_effect, stylesheets) | `shared/theme_qt.py` |
| Componentes UI (NMButton, NMCard, etc.) | `shared/components_qt.py` |
| Logo, íconos | `assets/LOGO.png`, `assets/NM_icon.ico` |
| Clase base instaladores | `shared/installer_common.py` |
