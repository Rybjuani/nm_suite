# IDENTIDAD_VISUAL.md — NeuroMood
# Extraído de neuromood.com.ar · Para uso en la Suite de Apps de Escritorio
# Este archivo debe estar en la raíz del proyecto. Claude Code debe leerlo antes de diseñar cualquier interfaz.

---

## 1. PALETA DE COLORES

### Colores principales (extraídos del sitio)

| Nombre                | Hex        | RGB                  | Uso en el sitio                          |
|-----------------------|------------|----------------------|------------------------------------------|
| Azul marino profundo  | `#0B1928`  | rgb(11, 25, 40)      | Fondo principal, header, hero section    |
| Azul marino medio     | `#0D2137`  | rgb(13, 33, 55)      | Fondo de secciones secundarias           |
| Azul oscuro superficie| `#112740`  | rgb(17, 39, 64)      | Cards, contenedores, nav                 |
| Teal / cian acento    | `#1EC8D4`  | rgb(30, 200, 212)    | Botones CTA, links activos, highlights   |
| Teal claro hover      | `#2EDDE9`  | rgb(46, 221, 233)    | Hover de botones, estados activos        |
| Teal muy suave        | `#1EC8D420`| rgba(30,200,212,0.12)| Fondos de tarjetas activas, selección    |
| Blanco puro           | `#FFFFFF`  | rgb(255,255,255)     | Texto principal sobre fondos oscuros     |
| Blanco suave          | `#E8EEF4`  | rgb(232,238,244)     | Texto secundario, subtítulos             |
| Gris azulado claro    | `#8BA4BE`  | rgb(139,164,190)     | Texto terciario, placeholders, hints     |
| Gris separador        | `#1A3050`  | rgb(26, 48, 80)      | Bordes, líneas divisoras, separadores    |
| Blanco cards          | `#FFFFFF`  | rgb(255,255,255)     | Cards en modo claro (modo alternativo)   |

### Colores funcionales (estados)

| Estado     | Hex        | Uso                                      |
|------------|------------|------------------------------------------|
| Éxito      | `#22D47E`  | Checklist completado, logros, validación |
| Advertencia| `#F0A500`  | Alertas suaves, recordatorios            |
| Error      | `#E8505B`  | Errores, validaciones fallidas           |
| Info       | `#1EC8D4`  | Tooltips, información (mismo teal)       |

---

## 2. TIPOGRAFÍA

### Fuente del sitio
El sitio usa **Roboto** como fuente principal (Google Fonts, confirmado por Elementor + google_font-enabled).
Fuente de fallback: `Segoe UI, Arial, sans-serif` (nativa de Windows — perfecta para apps de escritorio).

### Escala tipográfica

| Elemento           | Fuente      | Tamaño  | Peso       | Color             | Uso                               |
|--------------------|-------------|---------|------------|-------------------|-----------------------------------|
| H1 — Título hero   | Roboto      | 36–42px | 700 (Bold) | `#FFFFFF`         | Títulos principales de sección    |
| H2 — Sección       | Roboto      | 26–30px | 600        | `#FFFFFF`         | Subtítulos de sección             |
| H3 — Card title    | Roboto      | 18–20px | 500        | `#FFFFFF`         | Títulos de cards y servicios      |
| H4 — Label grande  | Roboto      | 14–15px | 500        | `#E8EEF4`         | Labels en mayúsculas              |
| Párrafo / cuerpo   | Roboto      | 15–16px | 400        | `#E8EEF4`         | Texto descriptivo largo           |
| Texto secundario   | Roboto      | 13–14px | 400        | `#8BA4BE`         | Subtítulos, hints, fechas         |
| Botón CTA          | Roboto      | 14px    | 500        | `#FFFFFF`         | Texto en botones principales      |
| Nav / menú         | Roboto      | 14px    | 500        | `#E8EEF4`         | Links de navegación               |
| Caption / micro    | Roboto      | 12px    | 400        | `#8BA4BE`         | Notas al pie, copyright           |

### Para apps de escritorio (CustomTkinter):
- Usar `Segoe UI` como equivalente directo a Roboto en Windows
- Es la fuente nativa de Windows y más cercana al look del sitio
- Fallback: `Arial`

---

## 3. COMPONENTES UI

### Botones

#### Botón primario (CTA — "Conózcanos", "Contáctenos")
```
Fondo:          #1EC8D4  (teal)
Texto:          #FFFFFF  (blanco)
Border-radius:  8px
Padding:        12px × 28px
Font:           Segoe UI, 14px, weight 500
Hover fondo:    #2EDDE9  (teal más claro)
Hover efecto:   leve escala 1.02 + brillo
Sin borde visible en estado normal
```

#### Botón secundario / outline
```
Fondo:          transparente
Texto:          #1EC8D4  (teal)
Borde:          1.5px solid #1EC8D4
Border-radius:  8px
Padding:        10px × 24px
Hover:          fondo rgba(30,200,212,0.12)
```

#### Botón de icono / acción pequeña
```
Fondo:          rgba(30,200,212,0.15)
Icono:          #1EC8D4
Border-radius:  6px
Tamaño:         36×36px mínimo
```

### Cards / Tarjetas

#### Card principal (servicios, contenido)
```
Fondo:          #112740  (azul oscuro superficie)
Borde:          1px solid #1A3050  (muy sutil)
Border-radius:  12px
Padding:        24px
Sombra:         ninguna (diseño flat)
Título:         Segoe UI 16px 500 #FFFFFF
Cuerpo:         Segoe UI 14px 400 #E8EEF4
```

#### Card destacada / activa
```
Fondo:          #112740
Borde:          1.5px solid #1EC8D4  (teal)
Border-radius:  12px
Acento top:     3px solid #1EC8D4 en borde superior
```

### Header / Navbar
```
Fondo:          #0B1928  (azul marino profundo)
Altura:         68–72px
Logo:           alineado a la izquierda
Links nav:      Segoe UI 14px 500, color #E8EEF4, hover #1EC8D4
CTA nav:        botón teal a la derecha ("Contacto")
Borde inferior: 1px solid #1A3050
```

### Inputs / Formularios
```
Fondo input:    #112740
Borde:          1px solid #1A3050
Borde focus:    1.5px solid #1EC8D4
Border-radius:  8px
Texto:          #FFFFFF, Segoe UI 14px
Placeholder:    #8BA4BE
Padding:        10px 14px
```

### Separadores / Divisores
```
Color:          #1A3050
Grosor:         1px
Estilo:         sólido
```

### Badges / Etiquetas
```
Fondo:          rgba(30,200,212,0.15)
Texto:          #1EC8D4
Border-radius:  20px (pill)
Font:           Segoe UI 12px 500
Padding:        4px 12px
```

### Barras de progreso
```
Fondo track:    #1A3050
Fill activo:    #1EC8D4
Border-radius:  4px
Altura:         6px
```

### Íconos / SVG
```
Color primario: #1EC8D4  (teal)
Color neutral:  #8BA4BE  (gris azulado)
Color sobre teal: #FFFFFF
Tamaño UI:      20×20px
Tamaño feature: 40×40px
```

---

## 4. ESPACIADO Y LAYOUT

```
Padding contenedor:   24px
Gap entre cards:      16px
Gap elementos UI:     12px
Margen secciones:     32–48px
Radio estándar:       8px   (botones, inputs, badges)
Radio card:           12px  (cards y contenedores)
Radio modal:          16px  (ventanas y dialogs)
Border grosor normal: 1px solid #1A3050
Border grosor acento: 1.5px solid #1EC8D4
```

---

## 5. ESTILO VISUAL GENERAL

- **Estética:** Dark mode profesional-médico. Minimalista, tecnológico, confiable.
- **Sensación:** Sofisticado y calmante. No frío ni hospitalario — calidez lograda con el teal.
- **Contraste:** Muy alto — texto blanco sobre fondos muy oscuros. Sin ambigüedades.
- **Movimiento:** Sutil. Hover suaves, transiciones de 150–200ms. Sin animaciones llamativas.
- **Imágenes:** Fotos médicas profesionales + infografías en teal y blanco sobre fondo marino.
- **Iconografía:** Línea fina, estilo outline, color teal o blanco.

---

## 6. MODO CLARO (alternativo)

El sitio es mayormente oscuro. Para las apps, el modo claro debe ser:
```
Fondo principal:      #F0F4F8  (gris azulado muy claro)
Fondo superficie:     #FFFFFF  (blanco puro)
Fondo card:           #FFFFFF  con borde #D0DCE8
Texto principal:      #0B1928  (azul marino — mismo que el fondo oscuro, invertido)
Texto secundario:     #4A6480
Texto terciario:      #8BA4BE
Acento:               #0BA8B5  (teal más oscuro para contraste en fondo claro)
Botón CTA fondo:      #0BA8B5
Botón CTA texto:      #FFFFFF
Borde:                #D0DCE8
Input fondo:          #FFFFFF
Input borde focus:    #1EC8D4
```

---

## 7. VARIABLES PYTHON (para theme.py en CustomTkinter)

```python
# ============================================================
# theme.py — NeuroMood Design System
# Basado en la identidad visual de neuromood.com.ar
# ============================================================

COLORS = {
    # --- MODO OSCURO (dark mode — predeterminado) ---
    "dark": {
        # Fondos
        "bg_primary":       "#0B1928",   # Fondo principal
        "bg_secondary":     "#0D2137",   # Secciones secundarias
        "bg_surface":       "#112740",   # Cards, contenedores
        "bg_input":         "#112740",   # Inputs y formularios
        "bg_hover":         "#1A3050",   # Estado hover en items

        # Acentos
        "accent":           "#1EC8D4",   # Teal principal
        "accent_hover":     "#2EDDE9",   # Teal hover
        "accent_subtle":    "#1EC8D420", # Teal transparente (fondos)

        # Texto
        "text_primary":     "#FFFFFF",   # Texto principal
        "text_secondary":   "#E8EEF4",   # Subtítulos y descripciones
        "text_tertiary":    "#8BA4BE",   # Hints, placeholders, captions
        "text_on_accent":   "#FFFFFF",   # Texto sobre botones teal

        # Bordes
        "border":           "#1A3050",   # Borde estándar
        "border_accent":    "#1EC8D4",   # Borde destacado
        "border_focus":     "#1EC8D4",   # Borde de input en foco

        # Estados
        "success":          "#22D47E",
        "warning":          "#F0A500",
        "error":            "#E8505B",
        "info":             "#1EC8D4",

        # Progress bars
        "progress_track":   "#1A3050",
        "progress_fill":    "#1EC8D4",
    },

    # --- MODO CLARO (light mode) ---
    "light": {
        # Fondos
        "bg_primary":       "#F0F4F8",
        "bg_secondary":     "#E4EBF3",
        "bg_surface":       "#FFFFFF",
        "bg_input":         "#FFFFFF",
        "bg_hover":         "#E4EBF3",

        # Acentos
        "accent":           "#0BA8B5",
        "accent_hover":     "#1EC8D4",
        "accent_subtle":    "#0BA8B515",

        # Texto
        "text_primary":     "#0B1928",
        "text_secondary":   "#2A4A6A",
        "text_tertiary":    "#6A8AA8",
        "text_on_accent":   "#FFFFFF",

        # Bordes
        "border":           "#D0DCE8",
        "border_accent":    "#0BA8B5",
        "border_focus":     "#1EC8D4",

        # Estados
        "success":          "#1AAE60",
        "warning":          "#D48F00",
        "error":            "#C83040",
        "info":             "#0BA8B5",

        # Progress bars
        "progress_track":   "#D0DCE8",
        "progress_fill":    "#0BA8B5",
    }
}

TYPOGRAPHY = {
    "font_family":      "Segoe UI",      # Equivalente Windows de Roboto
    "font_fallback":    "Arial",
    "size_h1":          28,
    "size_h2":          22,
    "size_h3":          17,
    "size_body":        14,
    "size_small":       12,
    "size_caption":     11,
    "weight_regular":   "normal",
    "weight_medium":    "bold",          # CTk solo soporta normal/bold
}

LAYOUT = {
    "padding_container":    24,
    "padding_card":         20,
    "padding_button_x":     24,
    "padding_button_y":     10,
    "gap_cards":            16,
    "gap_elements":         12,
    "radius_button":        8,
    "radius_card":          12,
    "radius_modal":         16,
    "radius_input":         8,
    "radius_badge":         20,
    "border_width":         1,
    "border_accent_width":  2,
    "header_height":        68,
    "min_touch_target":     44,
}
```

---

## 8. INSTRUCCIONES PARA CLAUDE CODE

1. **Leer este archivo completo** antes de escribir cualquier línea de interfaz.
2. El modo oscuro es el **predeterminado** — así es como se ve el sitio de NeuroMood.
3. El **teal `#1EC8D4`** es el color de acción: todos los botones primarios, links activos, indicadores de progreso y highlights deben usarlo.
4. El **azul marino `#0B1928`** es el fondo — no usar negro puro nunca.
5. Todas las apps deben sentirse como **extensiones naturales del sitio web** de NeuroMood.
6. El logo (LOGO.PNG) va en el header de cada app — sobre fondo `#0B1928`.
7. La tipografía es **Segoe UI** en Windows (equivalente visual de Roboto).
8. Animaciones: máximo 200ms, `ease-out`. Nada llamativo.
9. Nunca usar `#000000` ni `#FFFFFF` puros como fondo — usar los valores de este archivo.
10. En modo claro, el teal se oscurece a `#0BA8B5` para mantener contraste WCAG AA.
