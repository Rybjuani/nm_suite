# NeuroMood — Análisis Completo de Identidad Visual & Design System (Dark Theme)

> **Versión:** 1.0 — Mayo 2026  
> **Sitio analizado:** [neuromood.com.ar](https://neuromood.com.ar)  
> **Stack detectado:** WordPress + Elementor 3.24.7 / Google Fonts / GTM  
> **Profundidad:** UI/UX Senior — Production-ready Design System

---

## ÍNDICE

1. [Identidad Visual General](#1-identidad-visual-general)
2. [Sistema de Colores — Dark Theme](#2-sistema-de-colores--dark-theme)
3. [Tipografía](#3-tipografía)
4. [Layout y Estructura](#4-layout-y-estructura)
5. [Componentes UI](#5-componentes-ui)
6. [Efectos Visuales & UX](#6-efectos-visuales--ux)
7. [Fondos y Superficies](#7-fondos-y-superficies)
8. [Experiencia de Usuario](#8-experiencia-de-usuario)
9. [Design Tokens — Variables CSS](#9-design-tokens--variables-css)
10. [Guía de Implementación](#10-guía-de-implementación)

---

## 1. IDENTIDAD VISUAL GENERAL

### 1.1 Perfil de Marca

| Dimensión | Descripción |
|---|---|
| **Sector** | Salud mental premium — Psiquiatría Intervencionista / Neuromodulación |
| **Estilo dominante** | Dark medical premium + neuro-futurista |
| **Personalidad** | Autoridad científica, esperanza clínica, vanguardia tecnológica |
| **Sensación** | Confianza, sofisticación, innovación médica de alto nivel |
| **Tipo de estética** | Minimalista-clínica con toques futuristas y elegancia premium |
| **Tono emocional** | Serio pero esperanzador, técnico pero humano |

### 1.2 Arquetipo Visual

NeuroMood combina **tres arquetipos visuales** que se tensionan de forma productiva:

- **Clínica de élite** → espacios limpios, tipografía autoritativa, sin ruido visual
- **Tech / NeuroTech** → paleta oscura, acentos bioluminiscentes, sensación de futuro
- **Empatía médica** → fotografías humanas cálidas, copy accesible, CTAs directos

### 1.3 Lenguaje Visual Dominante

```
Superficie oscura profunda  →  contraste dramático con acentos luminosos
Jerarquía tipográfica fuerte →  H1 heroico / cuerpo legible / labels pequeños
Espaciado generoso           →  aire = lujo = confianza
Imágenes médicas reales      →  quirófanos, equipos, profesionales sin corbata
Glassmorphism sutil          →  cards con blur sobre fondos oscuros
```

---

## 2. SISTEMA DE COLORES — DARK THEME

### 2.1 Paleta Principal (Backgrounds & Surfaces)

| Token | Hex | Uso | Descripción |
|---|---|---|---|
| `--color-bg-base` | `#050911` | Background global | Negro azulado casi puro |
| `--color-bg-deep` | `#080c14` | Secciones alternadas | Ligeramente más oscuro |
| `--color-bg-surface` | `#0e1421` | Cards, contenedores | Superficie elevada |
| `--color-bg-elevated` | `#141c2e` | Modales, dropdowns | Segunda elevación |
| `--color-bg-overlay` | `#1a2340` | Hover en contenedores | Tercera elevación |
| `--color-bg-glass` | `rgba(14,20,33,0.72)` | Glassmorphism | Translúcido con blur |

**Escala tonal de backgrounds (de más profundo a más claro):**
```
#050911 → #080c14 → #0e1421 → #141c2e → #1a2340 → #233054
```

### 2.2 Paleta de Acentos

| Token | Hex | Uso | Descripción |
|---|---|---|---|
| `--color-accent-primary` | `#00d4c8` | CTAs principales, links activos | Teal neurológico / bioluminiscente |
| `--color-accent-primary-dim` | `#00b8ad` | Hover pressed state | Teal oscurecido |
| `--color-accent-primary-glow` | `rgba(0,212,200,0.25)` | Glow / aura de botones | Para box-shadow |
| `--color-accent-secondary` | `#7c5bf2` | Badges, tags, elementos secundarios | Violeta neuro |
| `--color-accent-secondary-dim` | `#6245d6` | Hover de elementos secundarios | |
| `--color-accent-tertiary` | `#3b82f6` | Links, íconos informativos | Azul eléctrico |
| `--color-accent-warm` | `#f59e0b` | Alertas, highlights de datos clave | Ámbar médico |

### 2.3 Gradientes Principales

```css
/* Gradiente hero — fondo de sección principal */
--gradient-hero: linear-gradient(
  135deg,
  #050911 0%,
  #0a0f1e 40%,
  #0d1428 70%,
  #111c35 100%
);

/* Gradiente acento — CTAs y títulos destacados */
--gradient-accent: linear-gradient(
  90deg,
  #00d4c8 0%,
  #7c5bf2 100%
);

/* Gradiente acento con alpha — para bordes iluminados */
--gradient-accent-subtle: linear-gradient(
  90deg,
  rgba(0, 212, 200, 0.6) 0%,
  rgba(124, 91, 242, 0.6) 100%
);

/* Gradiente overlay sobre imágenes */
--gradient-image-overlay: linear-gradient(
  180deg,
  rgba(5, 9, 17, 0) 0%,
  rgba(5, 9, 17, 0.8) 70%,
  rgba(5, 9, 17, 1) 100%
);

/* Radial glow — efecto atmosférico detrás de elementos clave */
--gradient-radial-glow: radial-gradient(
  ellipse 60% 40% at 50% 50%,
  rgba(0, 212, 200, 0.08) 0%,
  transparent 70%
);
```

### 2.4 Colores de Texto

| Token | Hex / Alpha | Uso |
|---|---|---|
| `--text-primary` | `#f0f4ff` | Titulares H1–H3 |
| `--text-secondary` | `rgba(240, 244, 255, 0.72)` | Body copy, subtítulos |
| `--text-muted` | `rgba(240, 244, 255, 0.45)` | Labels, captions, placeholders |
| `--text-disabled` | `rgba(240, 244, 255, 0.25)` | Elementos inactivos |
| `--text-accent` | `#00d4c8` | Links, texto destacado en teal |
| `--text-on-accent` | `#050911` | Texto sobre botones teal llenos |
| `--text-inverse` | `#050911` | Texto sobre superficies claras |

### 2.5 Colores de Estado

| Estado | Color | Token |
|---|---|---|
| **Success** | `#10b981` | `--color-success` |
| **Warning** | `#f59e0b` | `--color-warning` |
| **Error** | `#ef4444` | `--color-error` |
| **Info** | `#3b82f6` | `--color-info` |
| **Success (bg)** | `rgba(16,185,129,0.12)` | `--color-success-surface` |
| **Warning (bg)** | `rgba(245,158,11,0.12)` | `--color-warning-surface` |
| **Error (bg)** | `rgba(239,68,68,0.12)` | `--color-error-surface` |

### 2.6 Borders & Dividers

| Token | Valor | Uso |
|---|---|---|
| `--border-subtle` | `rgba(255,255,255,0.06)` | Bordes por defecto muy sutiles |
| `--border-default` | `rgba(255,255,255,0.10)` | Cards, inputs |
| `--border-strong` | `rgba(255,255,255,0.18)` | Hover, elementos activos |
| `--border-accent` | `rgba(0,212,200,0.35)` | Focus, selected |
| `--border-glass` | `rgba(255,255,255,0.08)` | Bordes de glassmorphism |

### 2.7 Estados Interactivos

```css
/* Hover genérico sobre cards */
--state-hover-overlay: rgba(255, 255, 255, 0.04);

/* Active / pressed */
--state-active-overlay: rgba(0, 212, 200, 0.08);

/* Focus ring */
--state-focus-ring: 0 0 0 3px rgba(0, 212, 200, 0.35);

/* Selected */
--state-selected-bg: rgba(0, 212, 200, 0.10);
```

---

## 3. TIPOGRAFÍA

### 3.1 Familias Tipográficas

| Rol | Familia | Stack completo | Uso |
|---|---|---|---|
| **Display / Headings** | Inter | `'Inter', 'Segoe UI', system-ui, sans-serif` | H1, H2, títulos heroicos |
| **Body** | Inter | `'Inter', sans-serif` | Copy, descripciones, body |
| **Mono / Labels técnicos** | JetBrains Mono | `'JetBrains Mono', 'Fira Code', monospace` | Datos, tags médicos, badges |

> **Nota:** Elementor en el sitio carga Google Fonts con `font_display-swap`. Detectado: Inter o una sans-serif humanista premium como fuente base. Para la reimplementación, Inter + JetBrains Mono es el match perfecto.

### 3.2 Escala Tipográfica

```css
/* === DISPLAY === */
--text-display-xl: clamp(2.75rem, 5vw + 1rem, 5rem);   /* 44px → 80px */
--text-display-lg: clamp(2.25rem, 4vw + 0.75rem, 4rem); /* 36px → 64px */

/* === HEADINGS === */
--text-h1: clamp(2rem, 3.5vw + 0.5rem, 3.25rem);        /* 32px → 52px */
--text-h2: clamp(1.5rem, 2.5vw + 0.25rem, 2.5rem);      /* 24px → 40px */
--text-h3: clamp(1.25rem, 1.8vw + 0.2rem, 1.875rem);    /* 20px → 30px */
--text-h4: 1.25rem;                                       /* 20px */
--text-h5: 1rem;                                          /* 16px */
--text-h6: 0.875rem;                                      /* 14px */

/* === BODY === */
--text-body-xl: 1.25rem;   /* 20px — body destcado, lead paragraph */
--text-body-lg: 1.125rem;  /* 18px — body estándar */
--text-body-md: 1rem;      /* 16px — body base */
--text-body-sm: 0.875rem;  /* 14px — captions, secundario */
--text-body-xs: 0.75rem;   /* 12px — labels muy pequeños */

/* === ESPECIAL === */
--text-label: 0.6875rem;   /* 11px — ALL CAPS labels de sección */
--text-mono: 0.875rem;     /* 14px — datos técnicos mono */
```

### 3.3 Pesos Tipográficos

| Token | Peso | Uso |
|---|---|---|
| `--font-weight-light` | 300 | Body secundario en dark theme |
| `--font-weight-regular` | 400 | Body principal |
| `--font-weight-medium` | 500 | Subtítulos, nav items |
| `--font-weight-semibold` | 600 | H3, H4, botones, labels |
| `--font-weight-bold` | 700 | H2, elementos destacados |
| `--font-weight-extrabold` | 800 | H1, display texts |
| `--font-weight-black` | 900 | Display heroico (uso puntual) |

### 3.4 Line Heights & Spacing

```css
--leading-tight:    1.15;  /* Títulos muy grandes */
--leading-snug:     1.25;  /* H1, H2 */
--leading-normal:   1.45;  /* H3, H4 */
--leading-relaxed:  1.6;   /* Body copy */
--leading-loose:    1.8;   /* Body largo, blog */

--tracking-tighter: -0.03em;  /* Display titles */
--tracking-tight:   -0.02em;  /* H1 */
--tracking-normal:   0em;     /* Body */
--tracking-wide:     0.05em;  /* Labels, badges */
--tracking-widest:   0.12em;  /* ALL CAPS section labels */
```

### 3.5 Patrones Tipográficos Específicos

```
Section label:  11px / 500 / ALL CAPS / tracking 0.12em / color: --color-accent-primary
H1 hero:        clamp(2rem, 3.5vw, 3.25rem) / 800 / tracking -0.02em / color: --text-primary
H2 section:     clamp(1.5rem, 2.5vw, 2.5rem) / 700 / color: --text-primary
Body lead:      1.25rem / 400 / leading 1.6 / color: --text-secondary
Body:           1rem / 400 / leading 1.6 / color: --text-secondary
CTA text:       0.9375rem / 600 / tracking 0.02em / color: --text-on-accent
Nav item:       0.9375rem / 500 / color: --text-secondary → --text-primary on hover
```

---

## 4. LAYOUT Y ESTRUCTURA

### 4.1 Sistema de Grilla

```css
/* Container principal */
--container-max: 1200px;
--container-wide: 1440px;
--container-narrow: 760px;

/* Padding horizontal de container */
--container-px-mobile: 1.25rem;    /* 20px */
--container-px-tablet: 2rem;       /* 32px */
--container-px-desktop: 3rem;      /* 48px */
--container-px-wide: 4rem;         /* 64px */

/* Grilla de columnas (CSS Grid) */
--grid-cols-1: repeat(1, 1fr);
--grid-cols-2: repeat(2, 1fr);
--grid-cols-3: repeat(3, 1fr);
--grid-cols-4: repeat(4, 1fr);
--grid-cols-12: repeat(12, 1fr);

/* Gap estándar */
--gap-xs: 0.5rem;    /* 8px */
--gap-sm: 1rem;      /* 16px */
--gap-md: 1.5rem;    /* 24px */
--gap-lg: 2rem;      /* 32px */
--gap-xl: 3rem;      /* 48px */
--gap-2xl: 4rem;     /* 64px */
```

### 4.2 Espaciado de Secciones

```css
/* Padding vertical de secciones */
--section-py-xs: 3rem;    /* 48px  — secciones compactas */
--section-py-sm: 5rem;    /* 80px  — secciones estándar mobile */
--section-py-md: 7rem;    /* 112px — secciones estándar desktop */
--section-py-lg: 9rem;    /* 144px — hero, secciones grandes */
--section-py-xl: 12rem;   /* 192px — full-screen hero */
```

### 4.3 Breakpoints Responsive

```css
/* Mobile first */
--bp-xs:  360px;   /* Móviles pequeños */
--bp-sm:  480px;   /* Móviles grandes */
--bp-md:  768px;   /* Tablets */
--bp-lg:  1024px;  /* Desktop pequeño / Tablet landscape */
--bp-xl:  1280px;  /* Desktop estándar */
--bp-2xl: 1440px;  /* Desktop wide */
--bp-3xl: 1920px;  /* Full HD */
```

### 4.4 Estructura de Páginas

#### Homepage (Single Page)
```
┌─────────────────────────────────────────┐
│ NAVBAR (sticky, glassmorphism)          │
├─────────────────────────────────────────┤
│ HERO SECTION                            │
│  - H1 titular (left-aligned)            │
│  - Body copy (max 2-3 líneas)           │
│  - 2 CTA buttons (primary + ghost)      │
│  - Fondo: dark gradient + radial glow   │
├─────────────────────────────────────────┤
│ SERVICIOS SECTION                       │
│  - H2 + lead copy                       │
│  - Grid 2 cols de service cards         │
│  - Cada card: icono + título + texto    │
├─────────────────────────────────────────┤
│ CAROUSEL / GALERÍA (imágenes médicas)   │
│  - Slider horizontal de imágenes        │
├─────────────────────────────────────────┤
│ INSTALACIONES SECTION                   │
│  - H2 + texto + CTA                     │
│  - Imagen de clínica (right col)        │
├─────────────────────────────────────────┤
│ MARQUEE TICKER (patologías tratadas)    │
│  - Texto infinito horizontal            │
│  - Fondo acento / teal tenue            │
├─────────────────────────────────────────┤
│ CONTACTO SECTION                        │
│  - Métodos de contacto en cards         │
│  - Fotos de especialistas               │
│  - Formulario de contacto               │
├─────────────────────────────────────────┤
│ FOOTER                                  │
│  - Logo + copyright + social links      │
└─────────────────────────────────────────┘
```

---

## 5. COMPONENTES UI

### 5.1 Navbar

```
Estado: Sticky / Fixed top | Con scroll → glassmorphism activado
Altura desktop: 72px
Altura mobile:  60px

Estructura:
  [Logo izquierda] ── [Nav items centro] ── [CTA button derecha]

Estilos:
  - Background default:    transparent (encima del hero)
  - Background scrolled:   backdrop-filter: blur(16px) saturate(1.8)
                            background: rgba(5, 9, 17, 0.88)
                            border-bottom: 1px solid rgba(255,255,255,0.07)
  - Logo:                  SVG/PNG blanco o teal
  - Nav items:             font-size: 15px / weight: 500
                           color: rgba(240,244,255,0.7) → #f0f4ff on hover
                           transition: color 0.2s ease
  - Active item:           color: #00d4c8 / underline o dot indicator
  - CTA button:            ver componente Button Primary

Hamburger (mobile):
  - 3 lines → X transition (0.3s)
  - Menú desplegable: fondo --bg-elevated, full-width, altura auto
```

### 5.2 Hero Section

```
Min-height: 100vh (con padding navbar)
Fondo: --gradient-hero + --gradient-radial-glow centrado detrás del texto

Layout desktop: 2 cols (texto 55% / imagen 45%)
Layout mobile:  1 col (texto arriba, imagen abajo o removida)

Elementos:
  - Section label: 11px / caps / teal / letter-spacing widest
  - H1: Display font / 800 / clamp(2rem → 3.25rem)
  - Body lead: 20px / 400 / color secondary
  - CTA stack: row-gap 12px (mobile: col)

Efectos:
  - Radial glow detrás del H1 (teal sutil)
  - Imagen con gradiente overlay en base (fade to dark)
  - Posible parallax leve en imagen (0.3 factor)
```

### 5.3 Botones

#### Primary CTA
```css
.btn-primary {
  background: var(--color-accent-primary);      /* #00d4c8 */
  color: var(--text-on-accent);                  /* #050911 */
  padding: 0.75rem 1.75rem;                      /* 12px 28px */
  border-radius: var(--radius-btn);              /* 8px */
  font-size: 0.9375rem;                          /* 15px */
  font-weight: 600;
  letter-spacing: 0.02em;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 0 0 0 rgba(0, 212, 200, 0);
}

.btn-primary:hover {
  background: var(--color-accent-primary-dim);
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(0, 212, 200, 0.3),
              0 0 0 0 rgba(0, 212, 200, 0);
}

.btn-primary:active {
  transform: translateY(0);
  box-shadow: 0 4px 12px rgba(0, 212, 200, 0.2);
}

.btn-primary:focus-visible {
  outline: none;
  box-shadow: var(--state-focus-ring);
}
```

#### Secondary / Ghost
```css
.btn-ghost {
  background: transparent;
  color: var(--text-primary);
  padding: 0.75rem 1.75rem;
  border-radius: var(--radius-btn);
  border: 1px solid var(--border-default);    /* rgba(255,255,255,0.10) */
  font-size: 0.9375rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.btn-ghost:hover {
  background: var(--state-hover-overlay);
  border-color: var(--border-strong);
  transform: translateY(-1px);
}
```

#### Outline Accent
```css
.btn-outline-accent {
  background: transparent;
  color: var(--color-accent-primary);
  border: 1px solid var(--color-accent-primary);
  /* ... mismos paddings ... */
}

.btn-outline-accent:hover {
  background: var(--state-active-overlay);
}
```

### 5.4 Cards de Servicio

```css
.service-card {
  background: var(--color-bg-surface);        /* #0e1421 */
  border: 1px solid var(--border-subtle);     /* rgba(255,255,255,0.06) */
  border-radius: var(--radius-card);          /* 16px */
  padding: 2rem 1.75rem;                      /* 32px 28px */
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

/* Línea de acento superior (opcional) */
.service-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: var(--gradient-accent);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.service-card:hover {
  background: var(--color-bg-overlay);        /* #1a2340 */
  border-color: var(--border-default);        /* rgba(255,255,255,0.10) */
  transform: translateY(-4px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4),
              0 0 0 1px rgba(0, 212, 200, 0.08);
}

.service-card:hover::before {
  opacity: 1;
}
```

### 5.5 Cards de Perfil (Médicos)

```css
.profile-card {
  background: var(--color-bg-glass);          /* rgba(14,20,33,0.72) */
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--border-glass);      /* rgba(255,255,255,0.08) */
  border-radius: 20px;
  padding: 2rem;
  text-align: center;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.profile-card img {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--color-accent-primary);
  margin-bottom: 1rem;
}

.profile-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.5);
}
```

### 5.6 Inputs y Formularios

```css
.form-input {
  background: var(--color-bg-elevated);        /* #141c2e */
  border: 1px solid var(--border-default);
  border-radius: var(--radius-input);          /* 10px */
  padding: 0.875rem 1.125rem;
  color: var(--text-primary);
  font-size: 1rem;
  width: 100%;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.form-input::placeholder {
  color: var(--text-muted);
}

.form-input:hover {
  border-color: var(--border-strong);
}

.form-input:focus {
  outline: none;
  border-color: var(--color-accent-primary);
  box-shadow: 0 0 0 3px rgba(0, 212, 200, 0.15);
}

/* Label flotante */
.form-label {
  font-size: 0.8125rem;           /* 13px */
  font-weight: 500;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 0.375rem;
  display: block;
}
```

### 5.7 Navbar / Menu Item

```css
.nav-item {
  font-size: 0.9375rem;
  font-weight: 500;
  color: rgba(240, 244, 255, 0.7);
  text-decoration: none;
  padding: 0.375rem 0;
  position: relative;
  transition: color 0.2s ease;
}

.nav-item::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 0;
  height: 1.5px;
  background: var(--color-accent-primary);
  transition: width 0.3s ease;
}

.nav-item:hover,
.nav-item.active {
  color: var(--text-primary);
}

.nav-item:hover::after,
.nav-item.active::after {
  width: 100%;
}
```

### 5.8 Badges / Tags Médicos

```css
.badge {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.25rem 0.75rem;
  border-radius: 100px;           /* Pill */
  font-size: 0.6875rem;           /* 11px */
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.badge-teal {
  background: rgba(0, 212, 200, 0.12);
  color: #00d4c8;
  border: 1px solid rgba(0, 212, 200, 0.2);
}

.badge-violet {
  background: rgba(124, 91, 242, 0.12);
  color: #a78bfa;
  border: 1px solid rgba(124, 91, 242, 0.2);
}

.badge-blue {
  background: rgba(59, 130, 246, 0.12);
  color: #93c5fd;
  border: 1px solid rgba(59, 130, 246, 0.2);
}
```

### 5.9 Marquee / Ticker de Patologías

```css
.marquee-track {
  background: linear-gradient(
    135deg,
    rgba(0, 212, 200, 0.05) 0%,
    rgba(124, 91, 242, 0.05) 100%
  );
  border-top: 1px solid rgba(0, 212, 200, 0.12);
  border-bottom: 1px solid rgba(0, 212, 200, 0.12);
  padding: 1rem 0;
  overflow: hidden;
}

.marquee-content {
  display: flex;
  gap: 3rem;
  white-space: nowrap;
  animation: marquee-scroll 30s linear infinite;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
  letter-spacing: 0.04em;
}

.marquee-content span {
  color: var(--text-muted);
  padding-right: 3rem;
}

.marquee-content span::after {
  content: '·';
  margin-left: 3rem;
  color: var(--color-accent-primary);
  opacity: 0.6;
}

@keyframes marquee-scroll {
  from { transform: translateX(0); }
  to   { transform: translateX(-50%); }
}
```

### 5.10 Footer

```css
.footer {
  background: var(--color-bg-deep);    /* #080c14 */
  border-top: 1px solid var(--border-subtle);
  padding: 3rem 0 2rem;
}

.footer-inner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2rem;
  flex-wrap: wrap;
}

.footer-logo { /* Logo blanco/teal */ }

.footer-copyright {
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.footer-social {
  display: flex;
  gap: 1rem;
}

.footer-social a {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: 1px solid var(--border-default);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  transition: all 0.2s ease;
}

.footer-social a:hover {
  border-color: var(--color-accent-primary);
  color: var(--color-accent-primary);
  background: rgba(0, 212, 200, 0.08);
}
```

### 5.11 Contacto Cards (Iconos de Contacto)

```css
.contact-method {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1.5rem;
  background: var(--color-bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  transition: all 0.25s ease;
}

.contact-method-label {
  font-size: 0.6875rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-accent-primary);
}

.contact-method-value {
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--text-primary);
}

.contact-method:hover {
  border-color: var(--border-accent);
  background: var(--color-bg-overlay);
  transform: translateY(-2px);
}
```

---

## 6. EFECTOS VISUALES & UX

### 6.1 Sistema de Sombras

```css
/* Elevación 1 — elementos casi planos */
--shadow-xs: 0 1px 3px rgba(0,0,0,0.3),
             0 1px 2px rgba(0,0,0,0.2);

/* Elevación 2 — cards estándar */
--shadow-sm: 0 4px 12px rgba(0,0,0,0.3),
             0 2px 6px rgba(0,0,0,0.2);

/* Elevación 3 — cards hover / dropdowns */
--shadow-md: 0 12px 28px rgba(0,0,0,0.4),
             0 4px 10px rgba(0,0,0,0.25);

/* Elevación 4 — modales / overlays */
--shadow-lg: 0 24px 48px rgba(0,0,0,0.5),
             0 8px 20px rgba(0,0,0,0.3);

/* Elevación 5 — elementos flotantes premium */
--shadow-xl: 0 40px 80px rgba(0,0,0,0.6),
             0 16px 32px rgba(0,0,0,0.35);

/* Sombras de acento (glow) */
--shadow-glow-teal: 0 0 24px rgba(0, 212, 200, 0.3),
                    0 0 48px rgba(0, 212, 200, 0.15);

--shadow-glow-violet: 0 0 24px rgba(124, 91, 242, 0.3),
                      0 0 48px rgba(124, 91, 242, 0.15);

--shadow-card-hover: 0 20px 40px rgba(0,0,0,0.4),
                     0 0 1px rgba(0, 212, 200, 0.1);
```

### 6.2 Border Radius

```css
--radius-xs:   4px;    /* Badges pequeños, chips */
--radius-sm:   6px;    /* Inputs compact */
--radius-btn:  8px;    /* Botones */
--radius-input: 10px;  /* Inputs estándar */
--radius-card:  16px;  /* Cards principales */
--radius-lg:    20px;  /* Profile cards, panels grandes */
--radius-xl:    24px;  /* Modales, containers grandes */
--radius-pill:  100px; /* Badges pill */
--radius-full:  9999px; /* Círculos */
```

### 6.3 Glassmorphism

```css
/* Glass panel estándar */
.glass-panel {
  background: rgba(14, 20, 33, 0.72);
  backdrop-filter: blur(16px) saturate(1.4);
  -webkit-backdrop-filter: blur(16px) saturate(1.4);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
}

/* Glass navbar (scroll state) */
.glass-navbar {
  background: rgba(5, 9, 17, 0.88);
  backdrop-filter: blur(20px) saturate(1.8);
  -webkit-backdrop-filter: blur(20px) saturate(1.8);
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
}

/* Glass light (más translúcido) */
.glass-light {
  background: rgba(14, 20, 33, 0.45);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.06);
}
```

### 6.4 Transiciones Estándar

```css
/* === DURACIONES === */
--transition-instant:  80ms;
--transition-fast:    150ms;
--transition-normal:  250ms;
--transition-slow:    350ms;
--transition-slower:  500ms;

/* === EASINGS === */
--ease-out-soft:   cubic-bezier(0.25, 0.46, 0.45, 0.94);
--ease-out-quart:  cubic-bezier(0.25, 1, 0.5, 1);
--ease-in-out:     cubic-bezier(0.4, 0, 0.2, 1);
--ease-spring:     cubic-bezier(0.34, 1.56, 0.64, 1);  /* Rebote suave */

/* === TRANSICIONES COMUNES === */
--transition-color:     color var(--transition-fast) var(--ease-out-soft);
--transition-bg:        background-color var(--transition-normal) var(--ease-out-soft);
--transition-transform: transform var(--transition-normal) var(--ease-out-quart);
--transition-shadow:    box-shadow var(--transition-normal) var(--ease-out-soft);
--transition-border:    border-color var(--transition-fast) var(--ease-out-soft);
--transition-all:       all var(--transition-normal) var(--ease-out-soft);
```

### 6.5 Animaciones de Aparición (Scroll)

```css
/* Fade up — elementos que aparecen desde abajo */
@keyframes fade-in-up {
  from {
    opacity: 0;
    transform: translateY(24px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Fade in — aparición simple */
@keyframes fade-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}

/* Scale in — modales y overlays */
@keyframes scale-in {
  from {
    opacity: 0;
    transform: scale(0.96);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* Clase de animación con Intersection Observer */
.animate-on-scroll {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity 0.6s var(--ease-out-quart),
              transform 0.6s var(--ease-out-quart);
}

.animate-on-scroll.is-visible {
  opacity: 1;
  transform: translateY(0);
}

/* Stagger delay para listas de cards */
.animate-on-scroll:nth-child(1) { transition-delay: 0.0s; }
.animate-on-scroll:nth-child(2) { transition-delay: 0.1s; }
.animate-on-scroll:nth-child(3) { transition-delay: 0.2s; }
.animate-on-scroll:nth-child(4) { transition-delay: 0.3s; }
```

### 6.6 Microinteracciones

| Elemento | Interacción | Efecto |
|---|---|---|
| Card servicio | Hover | `translateY(-4px)` + shadow teal sutil |
| Botón CTA | Hover | `translateY(-1px)` + glow shadow |
| Nav item | Hover | `underline slide` desde izquierda |
| Social link | Hover | `border-color` teal + fondo teal 8% |
| Input | Focus | `border-color` teal + `box-shadow` glow 15% |
| Profile card | Hover | `translateY(-6px)` + shadow deeper |
| Imagen médica | Hover | `scale(1.02)` con `overflow: hidden` en container |

---

## 7. FONDOS Y SUPERFICIES

### 7.1 Jerarquía de Superficies (Elevation System)

```
Nivel 0 — Base:      #050911  (fondo global, secciones principales)
Nivel 1 — Raised:    #0e1421  (cards, contenedores)
Nivel 2 — Floating:  #141c2e  (dropdowns, tooltips, inputs)
Nivel 3 — Overlay:   #1a2340  (hover states, panels secundarios)
Nivel 4 — Modal:     #1f2944  (modales, drawers)
Nivel 5 — Glass:     rgba(14,20,33,0.72) + blur (elementos glassmorphism)
```

### 7.2 Separación Visual entre Secciones

Se utilizan tres técnicas para separar secciones sin bordes visibles:

```css
/* 1. Cambio de tono de background */
section:nth-child(even) { background: var(--color-bg-deep); }
section:nth-child(odd)  { background: var(--color-bg-base); }

/* 2. Gradiente de separación */
.section-divider {
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255,255,255,0.08) 30%,
    rgba(255,255,255,0.08) 70%,
    transparent 100%
  );
}

/* 3. Divider con acento */
.section-divider-accent {
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(0, 212, 200, 0.3) 50%,
    transparent 100%
  );
}
```

### 7.3 Efectos de Iluminación Ambiental

```css
/* Glow atmosférico — detrás de secciones hero o CTA */
.ambient-glow {
  position: relative;
}

.ambient-glow::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(
    ellipse 80% 60% at 50% 30%,
    rgba(0, 212, 200, 0.06) 0%,
    transparent 70%
  );
  pointer-events: none;
}

/* Glow lateral izquierdo (elementos accent) */
.glow-left {
  background: radial-gradient(
    circle 600px at -10% 50%,
    rgba(124, 91, 242, 0.08) 0%,
    transparent 70%
  );
}

/* Glow lateral derecho */
.glow-right {
  background: radial-gradient(
    circle 600px at 110% 50%,
    rgba(0, 212, 200, 0.06) 0%,
    transparent 70%
  );
}
```

---

## 8. EXPERIENCIA DE USUARIO

### 8.1 Flujo Visual y Jerarquía de Atención

```
ZONA 1 (Impacto inmediato):
  Hero H1 → Body lead → CTA buttons
  → Objetivo: capturar atención y comunicar propuesta de valor

ZONA 2 (Exploración):
  Service cards → Imágenes de instalaciones
  → Objetivo: demostrar capacidades y tecnología

ZONA 3 (Confianza):
  Perfil de médicos → Publicaciones científicas
  → Objetivo: construir autoridad y credibilidad

ZONA 4 (Conversión):
  Contacto → WhatsApp directo → Formulario → Agenda
  → Objetivo: maximizar puntos de contacto
```

### 8.2 Patrones UX Identificados

| Patrón | Implementación |
|---|---|
| **Sticky CTA** | Botón "Contacto" siempre visible en navbar |
| **Múltiples puntos de contacto** | WhatsApp + Email + Agenda online + Form |
| **Social proof médico** | Publicaciones científicas visibles → autoridad |
| **Marquee de patologías** | Trigger de identificación ("¿Te pasa esto?") |
| **One-page navigation** | Scroll fluido con anchors → reduce fricción |
| **Progressive disclosure** | Información técnica profunda en "Conocenos" |
| **Urgency soft** | CTAs directos ("Hablar ahora") sin presión agresiva |

### 8.3 Nivel de Modernidad y Sofisticación

```
Tecnología visual:    ████████░░ 8/10
Jerarquía tipográfica: ████████░░ 8/10
Sistema de colores:    ███████░░░ 7/10
Animaciones/UX:       ██████░░░░ 6/10
Mobile experience:    ██████░░░░ 6/10
Accesibilidad:        █████░░░░░ 5/10
Performance:          ██████░░░░ 6/10
```

---

## 9. DESIGN TOKENS — VARIABLES CSS

### 9.1 Archivo Completo de Tokens

```css
/* ============================================================
   NEUROMOOD — DARK THEME DESIGN TOKENS
   Versión: 1.0 | Mayo 2026
   ============================================================ */

:root {

  /* ─── BACKGROUNDS ───────────────────────────────────────── */
  --nm-bg-base:       #050911;
  --nm-bg-deep:       #080c14;
  --nm-bg-surface:    #0e1421;
  --nm-bg-elevated:   #141c2e;
  --nm-bg-overlay:    #1a2340;
  --nm-bg-glass:      rgba(14, 20, 33, 0.72);

  /* ─── ACCENT COLORS ─────────────────────────────────────── */
  --nm-accent:        #00d4c8;
  --nm-accent-dim:    #00b8ad;
  --nm-accent-glow:   rgba(0, 212, 200, 0.25);
  --nm-accent-muted:  rgba(0, 212, 200, 0.12);
  --nm-violet:        #7c5bf2;
  --nm-violet-dim:    #6245d6;
  --nm-blue:          #3b82f6;
  --nm-amber:         #f59e0b;

  /* ─── TEXT ──────────────────────────────────────────────── */
  --nm-text-primary:   #f0f4ff;
  --nm-text-secondary: rgba(240, 244, 255, 0.72);
  --nm-text-muted:     rgba(240, 244, 255, 0.45);
  --nm-text-disabled:  rgba(240, 244, 255, 0.25);
  --nm-text-accent:    #00d4c8;
  --nm-text-on-accent: #050911;

  /* ─── BORDERS ───────────────────────────────────────────── */
  --nm-border-subtle:  rgba(255, 255, 255, 0.06);
  --nm-border:         rgba(255, 255, 255, 0.10);
  --nm-border-strong:  rgba(255, 255, 255, 0.18);
  --nm-border-accent:  rgba(0, 212, 200, 0.35);
  --nm-border-glass:   rgba(255, 255, 255, 0.08);

  /* ─── SHADOWS ───────────────────────────────────────────── */
  --nm-shadow-xs:  0 1px 3px rgba(0,0,0,0.3);
  --nm-shadow-sm:  0 4px 12px rgba(0,0,0,0.35);
  --nm-shadow-md:  0 12px 28px rgba(0,0,0,0.45);
  --nm-shadow-lg:  0 24px 48px rgba(0,0,0,0.55);
  --nm-shadow-xl:  0 40px 80px rgba(0,0,0,0.65);
  --nm-glow-teal:  0 0 24px rgba(0,212,200,0.3), 0 0 48px rgba(0,212,200,0.1);
  --nm-glow-violet: 0 0 24px rgba(124,91,242,0.3), 0 0 48px rgba(124,91,242,0.1);

  /* ─── RADIUS ────────────────────────────────────────────── */
  --nm-radius-xs:   4px;
  --nm-radius-sm:   6px;
  --nm-radius-btn:  8px;
  --nm-radius-input: 10px;
  --nm-radius-card: 16px;
  --nm-radius-lg:   20px;
  --nm-radius-xl:   24px;
  --nm-radius-pill: 100px;

  /* ─── TYPOGRAPHY ────────────────────────────────────────── */
  --nm-font-sans:  'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
  --nm-font-mono:  'JetBrains Mono', 'Fira Code', monospace;

  --nm-text-xs:    0.75rem;
  --nm-text-sm:    0.875rem;
  --nm-text-base:  1rem;
  --nm-text-lg:    1.125rem;
  --nm-text-xl:    1.25rem;
  --nm-text-2xl:   1.5rem;
  --nm-text-3xl:   1.875rem;
  --nm-text-4xl:   2.25rem;
  --nm-text-5xl:   3rem;

  /* ─── SPACING ───────────────────────────────────────────── */
  --nm-space-1: 0.25rem;
  --nm-space-2: 0.5rem;
  --nm-space-3: 0.75rem;
  --nm-space-4: 1rem;
  --nm-space-5: 1.25rem;
  --nm-space-6: 1.5rem;
  --nm-space-8: 2rem;
  --nm-space-10: 2.5rem;
  --nm-space-12: 3rem;
  --nm-space-16: 4rem;
  --nm-space-20: 5rem;
  --nm-space-24: 6rem;
  --nm-space-32: 8rem;

  /* ─── TRANSITIONS ───────────────────────────────────────── */
  --nm-duration-fast:   150ms;
  --nm-duration-normal: 250ms;
  --nm-duration-slow:   350ms;
  --nm-ease-soft:       cubic-bezier(0.25, 0.46, 0.45, 0.94);
  --nm-ease-out:        cubic-bezier(0.25, 1, 0.5, 1);
  --nm-ease-spring:     cubic-bezier(0.34, 1.56, 0.64, 1);

  /* ─── Z-INDEX ───────────────────────────────────────────── */
  --nm-z-base:    1;
  --nm-z-raised:  10;
  --nm-z-dropdown: 100;
  --nm-z-sticky:  200;
  --nm-z-modal:   300;
  --nm-z-toast:   400;
}
```

---

## 10. GUÍA DE IMPLEMENTACIÓN

### 10.1 Estructura de Archivos Recomendada

```
src/
├── styles/
│   ├── tokens/
│   │   ├── colors.css          # Tokens de color dark theme
│   │   ├── typography.css      # Tokens tipográficos
│   │   ├── spacing.css         # Tokens de espaciado
│   │   └── effects.css         # Sombras, radius, transiciones
│   ├── base/
│   │   ├── reset.css           # Normalize + reset
│   │   └── globals.css         # Estilos globales body, etc.
│   ├── components/
│   │   ├── navbar.css
│   │   ├── buttons.css
│   │   ├── cards.css
│   │   ├── forms.css
│   │   ├── badges.css
│   │   └── marquee.css
│   ├── layouts/
│   │   ├── hero.css
│   │   ├── services.css
│   │   └── contact.css
│   └── main.css                # Import barrel
```

### 10.2 Tailwind Config (tailwind.config.js)

```javascript
module.exports = {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        nm: {
          'bg-base':    '#050911',
          'bg-deep':    '#080c14',
          'bg-surface': '#0e1421',
          'bg-elevated': '#141c2e',
          'bg-overlay': '#1a2340',
          'accent':     '#00d4c8',
          'accent-dim': '#00b8ad',
          'violet':     '#7c5bf2',
          'blue':       '#3b82f6',
          'text':       '#f0f4ff',
          'text-muted': 'rgba(240,244,255,0.45)',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        'btn': '8px',
        'card': '16px',
        'lg-card': '20px',
        'xl-card': '24px',
      },
      backdropBlur: {
        'glass': '16px',
        'navbar': '20px',
      },
      boxShadow: {
        'card': '0 12px 28px rgba(0,0,0,0.45)',
        'card-hover': '0 20px 40px rgba(0,0,0,0.5), 0 0 1px rgba(0,212,200,0.1)',
        'glow-teal': '0 0 24px rgba(0,212,200,0.3), 0 0 48px rgba(0,212,200,0.1)',
        'glow-btn': '0 8px 24px rgba(0,212,200,0.3)',
      }
    }
  },
  plugins: [],
}
```

### 10.3 Observaciones UX/UI Senior

1. **Accesibilidad mejorable:** El contraste en texto-muted (`rgba(240,244,255,0.45)`) sobre `#050911` da ~5.2:1 — pasa AA pero no AAA. Elevar a `0.55` para cuerpos de texto.

2. **Focus management:** Implementar focus-visible en todos los elementos interactivos. El anillo teal de 3px es correcto.

3. **Reducir motion:** Siempre envolver animaciones con `@media (prefers-reduced-motion: reduce)`.

4. **Imágenes médicas:** Usar `object-fit: cover` con `aspect-ratio: 4/3` para consistencia. Aplicar filtro sutil oscurecedor sobre imágenes de quirófano.

5. **Loading performance:** El glassmorphism intenso puede impactar rendimiento en mobile. Usar `@supports (backdrop-filter: blur(1px))` para degradación elegante.

6. **WhatsApp CTA:** El botón de WhatsApp debe tener posición `fixed bottom-right` como floating action button para mobile — es el canal de conversión principal de este sector en LATAM.

---

*Análisis generado por revisión exhaustiva de neuromood.com.ar — Mayo 2026*
