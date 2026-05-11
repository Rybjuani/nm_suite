# Identidad Visual · Notion (www.notion.com)
> Análisis completo basado en el sitio web oficial — Mayo 2026

---

## 1. Esencia de Marca

| Atributo | Descripción |
|---|---|
| **Tagline actual** | "The AI workspace that works for you" |
| **Propuesta de valor** | Workspace unificado con IA que automatiza el trabajo repetitivo |
| **Personalidad** | Minimalista · Modular · Flexible · Empowering · Confiable |
| **Tono de voz** | Directo, conciso, poderoso — sin jerga corporativa. Habla de igual a igual. |

---

## 2. Paleta de Colores

### 2.1 Colores Primarios del Sitio Web

| Nombre | Hex | RGB | Uso principal |
|---|---|---|---|
| **Notion Black** | `#000000` | `rgb(0, 0, 0)` | Fondo hero, CTA primarios, textos dark |
| **Notion Off-White** | `#FFFFFF` | `rgb(255, 255, 255)` | Texto sobre fondos oscuros, fondos claros |
| **Notion Cream / Beige** | `#E3E2DE` | `rgb(227, 226, 222)` | Fondo principal modo claro, superficies neutras |
| **Dark Background** | `#0F0F0F` | `rgb(15, 15, 15)` | Background del homepage actual (tema "Night Shift") |

### 2.2 Colores Secundarios y de UI

| Nombre | Hex | RGB | Uso |
|---|---|---|---|
| **Light Gray** | `#F7F7F5` | `rgb(247, 247, 245)` | Superficies de tarjetas en modo claro |
| **Mid Gray** | `#CBCAC7` | `rgb(203, 202, 199)` | Bordes, separadores, íconos inactivos |
| **Dark Gray** | `#6B6B6B` | `rgb(107, 107, 107)` | Texto secundario, subtítulos |
| **Text Default** | `#191919` | `rgb(25, 25, 25)` | Cuerpo de texto principal en modo claro |

### 2.3 Colores de Contenido (dentro del producto)

Notion usa 10 colores de sistema dentro de la aplicación para textos y fondos de bloques:

| Color | Texto (aprox. Hex) | Fondo (aprox. Hex) |
|---|---|---|
| Gray | `#9B9A97` | `#EBECED` |
| Brown | `#64473A` | `#E9E5E3` |
| Orange | `#D9730D` | `#FAEBDD` |
| Yellow | `#DFAB01` | `#FBF3DB` |
| Green | `#0F7B6C` | `#DDEDEA` |
| Blue | `#0B6E99` | `#DDEBF1` |
| Purple | `#6940A5` | `#EAE4F2` |
| Pink | `#AD1A72` | `#F4DFEB` |
| Red | `#E03E3E` | `#FBE4E4` |

---

## 3. Tipografía

### 3.1 Fuente Principal

**Inter** — Neo-grotesque sans-serif
- Diseñada por **Rasmus Andersson** (originalmente para Google Fonts, 2017)
- Optimizada para pantallas: x-height alto, apertures abiertas, optical sizing
- Familia tipográfica: misma clase que Roboto, Helvetica, SF Pro

### 3.2 Pesos utilizados

| Peso | Variable CSS | Uso |
|---|---|---|
| Regular (400) | `font-weight: 400` | Cuerpo de texto, párrafos |
| Medium (500) | `font-weight: 500` | Texto de interfaz, navegación |
| SemiBold (600) | `font-weight: 600` | Subtítulos, etiquetas destacadas |
| Bold (700) | `font-weight: 700` | Headlines, CTAs, énfasis fuerte |

### 3.3 Escala Tipográfica (Homepage)

| Elemento | Tamaño aprox. | Peso | Line-height |
|---|---|---|---|
| Hero headline ("Meet the night shift") | `clamp(56px, 6vw, 96px)` | Bold (700) | 1.05 – 1.1 |
| Section headlines (H2) | `40px – 56px` | SemiBold (600) | 1.1 – 1.2 |
| Subheadlines (H3) | `24px – 32px` | SemiBold (600) | 1.2 – 1.3 |
| Body text | `16px – 18px` | Regular (400) | 1.5 – 1.6 |
| Labels / badges | `12px – 14px` | Medium (500) | 1.4 |
| Navigation links | `14px – 16px` | Medium (500) | — |

### 3.4 Fuentes alternativas dentro del producto

| Nombre en app | Fuente real | Estilo |
|---|---|---|
| Default | Inter | Sans-serif |
| Serif | Georgia / Lora (similar) | Serif clásico |
| Mono | Source Code Pro / JetBrains Mono | Monoespaciado |

---

## 4. Logotipo

### 4.1 Forma

- **Símbolo**: Página doblada con la letra "N" inscrita — representa un documento/bloque de contenido
- **Logotipo completo**: Símbolo + wordmark "Notion" en Inter Regular/SemiBold
- **Forma del símbolo**: Cuadrado redondeado con una esquina doblada (simulando papel)

### 4.2 Variantes

| Variante | Fondo recomendado |
|---|---|
| Negro sobre blanco | Fondos claros / blancos |
| Blanco sobre negro | Fondos oscuros / negros |
| Monocromo | Cualquier contexto de alta visibilidad |

### 4.3 Reglas de uso

- No distorsionar proporciones
- Respetar zona de exclusión mínima equivalente a la altura de la "N"
- Nunca añadir sombras, gradientes o efectos al logo
- No rotar ni inclinar

---

## 5. Layout y Composición

### 5.1 Grid System

- **Max-width del contenedor**: `1200px – 1440px`
- **Columnas**: Sistema de 12 columnas
- **Gutter**: `24px – 32px`
- **Padding lateral**: `24px` (mobile) / `48px` (tablet) / `80px+` (desktop)

### 5.2 Espaciado

Notion usa una escala de espaciado basada en múltiplos de `4px` o `8px`:

```
4px  · 8px  · 12px · 16px · 24px · 32px · 48px · 64px · 80px · 96px · 128px
```

### 5.3 Secciones del Homepage

1. **Navbar** — Fijo, fondo semi-transparente/oscuro, logo izquierda, nav centro, CTAs derecha
2. **Hero** — Full viewport, fondo negro, headline grande + subtext + 2 CTAs (primario/secundario) + video de fondo
3. **Logo bar** — "Trusted by 98% of Forbes Cloud 100" con logos de clientes en blanco
4. **Bento Grid** — Cuadrícula asimétrica de tarjetas de producto (Custom Agents, Search, Meeting Notes, etc.)
5. **Features Section** — Docs, Knowledge Base, Projects — alternan izquierda/derecha
6. **Calculator / ROI** — Interactivo, fondo claro, cálculo de ahorro por usuario
7. **Social Proof / Testimonials** — Citas de clientes con logos (OpenAI, Toyota, Vercel, etc.)
8. **Stats Bar** — Números clave en scroll horizontal (100M users, #1 G2, etc.)
9. **Footer** — 4 columnas, fondo oscuro/negro, enlaces + RRSS

### 5.4 Tarjetas (Bento Cards)

- Border radius: `12px – 16px`
- Background: `rgba(255,255,255,0.05)` sobre fondo oscuro / `#F7F7F5` sobre claro
- Border: `1px solid rgba(255,255,255,0.1)` (dark) / `1px solid #E3E2DE` (light)
- Overflow: `hidden`
- Sombras: Sutiles, `box-shadow: 0 2px 16px rgba(0,0,0,0.08)`

---

## 6. Botones y CTAs

### 6.1 Botón Primario

```css
background: #FFFFFF;
color: #000000;
border-radius: 6px;
padding: 10px 20px;
font-family: Inter, sans-serif;
font-weight: 600;
font-size: 15px;
border: none;
cursor: pointer;
transition: opacity 0.15s ease;
```

Hover: `opacity: 0.85` o ligero scale `scale(1.02)`

### 6.2 Botón Secundario / Outline

```css
background: transparent;
color: #FFFFFF;
border: 1px solid rgba(255,255,255,0.35);
border-radius: 6px;
padding: 10px 20px;
font-family: Inter, sans-serif;
font-weight: 500;
font-size: 15px;
```

### 6.3 Pill Badge / Etiquetas de Producto

```css
background: rgba(255,255,255,0.1);
color: rgba(255,255,255,0.7);
border-radius: 999px;  /* full pill */
padding: 4px 12px;
font-size: 12px;
font-weight: 500;
letter-spacing: 0.02em;
text-transform: uppercase;
```

---

## 7. Iconografía e Ilustración

### 7.1 Estilo de íconos

- **Línea fina o outline** con terminaciones redondeadas
- Tamaños estándar: `16px`, `20px`, `24px`
- Color: hereda del contexto (blanco/negro/gris)
- Sin rellenos decorativos — puramente funcionales

### 7.2 Objetos 3D / Decorativos (Homepage 2024-2026)

En la sección hero de Agentes aparecen pequeños objetos 3D flotantes con estética de producto físico:
- Emoji objects / props (libro, globo, buzón, bombilla, manzana, reloj, etc.)
- Render estilo clay/soft 3D, iluminación difusa
- Fondo transparente, flotando sobre el hero oscuro
- Escala: `48px – 96px` en pantalla

### 7.3 Capturas de producto / mockups

- Screenshots reales de la interfaz de Notion embebidos en tarjetas
- Estilo: "floating UI" — la imagen asoma fuera del borde de la tarjeta
- Superposición de capas (front + back card) para crear profundidad
- Sombras profundas para crear sensación de elevación

---

## 8. Fotografía e Imágenes

### 8.1 Estilo fotográfico

- Mínimo uso de fotografía humana en el sitio marketing
- Preferencia por capturas de UI, mockups de producto e ilustraciones
- Cuando se usan fotos de personas: tone neutral, ambiente de trabajo moderno

### 8.2 Logos de clientes

- Siempre en **monocromo blanco** sobre fondo oscuro
- Alineados en fila horizontal con scroll/marquee animado
- Opacidad ~70-80% para no competir visualmente

---

## 9. Animaciones y Motion

### 9.1 Principios

- **Sutil y funcional** — no hay animaciones por el puro espectáculo
- Duración corta: `150ms – 400ms`
- Easing preferido: `ease-out` o `cubic-bezier(0.16, 1, 0.3, 1)` (spring suave)

### 9.2 Transiciones comunes

| Elemento | Tipo | Duración |
|---|---|---|
| Hover en botones | Opacity / scale | `150ms ease` |
| Menú desplegable | Fade + translate Y | `200ms ease-out` |
| Bento cards hover | Scale leve + sombra | `200ms ease` |
| Logo bar | Marquee/scroll infinito | `~30s linear` |
| Secciones al scroll | Fade in + slide up | `400ms ease-out` |
| Video hero | Autoplay, muted, loop | — |

### 9.3 Video

- Video de fondo en el hero (`.mp4`, resolución `1920×1200`)
- Autoplay, muted, loop, poster image de respaldo
- Muestra la interfaz de Notion Agents en acción

---

## 10. Navegación

### 10.1 Estructura del Navbar

```
[Logo]  [Product ▾] [Solutions ▾] [Resources ▾] [Enterprise] [Pricing]  →  [Log in] [Get Notion free]
```

### 10.2 Estilo del Navbar

- Fondo: `transparent` o muy leve `backdrop-filter: blur(12px)` + `background: rgba(0,0,0,0.6)`
- Altura: `~60px – 72px`
- Logo: 24px height
- Links: Inter 14-15px, Medium (500), color blanco con hover suave
- CTA "Get Notion free": botón blanco sólido
- CTA "Log in": texto simple sin fondo

### 10.3 Mega Menús desplegables

Los menús de "Product", "Solutions" y "Resources" despliegan paneles con:
- Iconos de producto (24px)
- Título + descripción corta por ítem
- Fondo oscuro semitransparente con `backdrop-blur`
- Grid de 2-3 columnas

---

## 11. Footer

### 11.1 Estructura

```
[Logo] [Social icons: Instagram / Twitter(X) / LinkedIn / Facebook / YouTube]
[Language selector]  [Cookie settings]  [© 2026 Notion Labs, Inc.]

Columnas:
· Company: About us · Careers · Security · Status · Terms & privacy
· Download: iOS & Android · Mac & Windows · Mail · Calendar · Web Clipper
· Resources: Help center · Pricing · Blog · Community · Integrations · Templates · Partners
· Notion for: Enterprise · Small business · Personal · Explore more →
```

### 11.2 Estilo del Footer

- Fondo: negro (`#000000`) o muy oscuro
- Texto: blanco con opacidad reducida (~60-70%) para links
- Separadores: `1px solid rgba(255,255,255,0.1)`
- Font: Inter 13-14px, Regular

---

## 12. Tono de Voz y Copywriting

### 12.1 Características del copy

- **Corto y directo**: Headlines de 2-6 palabras cuando es posible
- **Segunda persona**: "You assign the tasks. Notion Agent does the work."
- **Beneficio antes que función**: No "multi-database system" sino "One source of truth"
- **Poder implícito**: Las frases transmiten control, eficiencia, calma
- **Sin puntos finales** en headlines y subheadlines

### 12.2 Ejemplos de headlines reales (2026)

- "Meet the night shift."
- "Keep work moving 24/7."
- "One search for everything."
- "Perfect notes, every time."
- "Less tracking. More progress."
- "More productivity. Fewer tools."
- "You assign the tasks. Notion Agent does the work."

### 12.3 Estructura de copy por sección

```
[Badge pill: nombre del producto]
[Headline: propuesta de valor clara — 3-7 palabras]
[Subtext: máx. 1-2 oraciones explicando el beneficio]
[CTA: "Get Notion free" / "Request a demo" / "→ link"]
```

---

## 13. Componentes UI Específicos

### 13.1 Pill / Badge de categoría

- Aparece sobre cada card como etiqueta de producto
- Texto: nombre del producto (ej. "Enterprise Search", "AI Meeting Notes")
- Estilo: texto pequeño, uppercase opcional, opacidad reducida

### 13.2 Scroll / Marquee de stats

```
"Over 100M users worldwide"  ·  "#1 knowledge base 3 years running (G2)"  ·  "#1 AI enterprise search (G2)"  ·  "62% of Fortune 100"  ...
```
- Fondo oscuro, texto blanco
- Loop continuo hacia la izquierda
- Font: Inter Medium, ~14px

### 13.3 Calculator interactivo

- Sliders o checkboxes para seleccionar herramientas
- Cálculo en tiempo real de ahorro mensual/anual
- Fondo claro, contrasta con las secciones oscuras

---

## 14. Modo Oscuro vs. Modo Claro

| Elemento | Modo Claro | Modo Oscuro |
|---|---|---|
| Background | `#FFFFFF` / `#E3E2DE` | `#0F0F0F` / `#191919` |
| Texto principal | `#191919` | `#FFFFFF` |
| Texto secundario | `#6B6B6B` | `rgba(255,255,255,0.6)` |
| Superficies/Cards | `#F7F7F5` | `rgba(255,255,255,0.05)` |
| Bordes | `#E3E2DE` | `rgba(255,255,255,0.1)` |

**El sitio de marketing (www.notion.com) usa principalmente el tema oscuro** desde 2024/2025 para el hero y secciones principales.

---

## 15. Responsive / Breakpoints

| Breakpoint | Nombre | Ancho |
|---|---|---|
| Mobile | sm | `< 768px` |
| Tablet | md | `768px – 1024px` |
| Desktop | lg | `1024px – 1280px` |
| Wide | xl | `> 1280px` |

### Adaptaciones clave en mobile

- Navbar: colapsa en hamburger menu
- Hero headline: escala hacia abajo con `clamp()`
- Bento grid: pasa de multi-columna a stack vertical
- Logo bar: mantiene scroll horizontal
- Footer: columnas pasan a grid 2x2 o stack vertical

---

## 16. Resumen de Design Tokens

```css
/* === COLORES === */
--color-black:        #000000;
--color-dark-bg:      #0F0F0F;
--color-text-dark:    #191919;
--color-white:        #FFFFFF;
--color-cream:        #E3E2DE;
--color-surface:      #F7F7F5;
--color-gray-mid:     #6B6B6B;
--color-gray-border:  #CBCAC7;
--color-overlay:      rgba(255, 255, 255, 0.05);

/* === TIPOGRAFÍA === */
--font-family:        'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
--font-weight-regular: 400;
--font-weight-medium:  500;
--font-weight-semibold: 600;
--font-weight-bold:    700;

/* === TAMAÑOS === */
--text-xs:    12px;
--text-sm:    14px;
--text-base:  16px;
--text-lg:    18px;
--text-xl:    24px;
--text-2xl:   32px;
--text-3xl:   48px;
--text-hero:  clamp(48px, 6vw, 96px);

/* === ESPACIADO === */
--space-1:   4px;
--space-2:   8px;
--space-3:   12px;
--space-4:   16px;
--space-6:   24px;
--space-8:   32px;
--space-12:  48px;
--space-16:  64px;
--space-20:  80px;
--space-24:  96px;
--space-32:  128px;

/* === BORDES === */
--radius-sm:   6px;
--radius-md:   12px;
--radius-lg:   16px;
--radius-full: 9999px;
--border-width: 1px;

/* === SOMBRAS === */
--shadow-sm:   0 1px 4px rgba(0, 0, 0, 0.06);
--shadow-md:   0 2px 16px rgba(0, 0, 0, 0.08);
--shadow-lg:   0 8px 40px rgba(0, 0, 0, 0.15);

/* === ANIMACIONES === */
--duration-fast:   150ms;
--duration-base:   200ms;
--duration-slow:   400ms;
--easing-out:      cubic-bezier(0.16, 1, 0.3, 1);
--easing-standard: ease-out;

/* === LAYOUT === */
--container-max:    1440px;
--container-md:     1200px;
--navbar-height:    64px;
--content-padding:  clamp(24px, 5vw, 80px);
```

---

## 17. Identidad de Productos Asociados

| Producto | Color distintivo | Ícono/Emoji |
|---|---|---|
| Notion (core) | Negro / Blanco | 📄 Página con N |
| Notion AI | Gradiente sutil morado-azul en contexto | ✨ Chispa / estrella |
| Notion Calendar | Azul suave | 📅 Calendario |
| Notion Mail | Verde suave | ✉️ Sobre |
| Notion Agents | Dorado / Ámbar en textos de hero | 🤖 Robot / agente |

---

## Referencias

- Sitio web oficial: [https://www.notion.com](https://www.notion.com)
- Fuente tipográfica: [Inter — rsms.me/inter](https://rsms.me/inter)
- Análisis de marca: Mobbin · Loftlyy · Order Design (Make With Notion event)
- Análisis propio: inspección del HTML/CSS de www.notion.com (Mayo 2026)

---

*Documento generado: Mayo 2026 · Versión 1.0*
*Esta guía refleja la identidad visual pública del sitio www.notion.com en el momento del análisis y puede estar sujeta a actualizaciones por parte de Notion Labs, Inc.*
