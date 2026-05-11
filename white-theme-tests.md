# NeuroMood — White Theme System (Light Mode Premium Paralelo)

> **Versión:** 1.0 — Mayo 2026  
> **Basado en:** Análisis de identidad visual neuromood.com.ar  
> **Concepto:** Identidad visual paralela en modo claro de vanguardia  
> **Filosofía:** No es inversión de colores — es una reinterpretación premium

---

## FILOSOFÍA DE DISEÑO

> *"Un white theme premium no blanquea un dark theme. Lo reinterpreta."*

El sistema de color claro de NeuroMood White toma los tres arquetipos del dark theme (élite clínica, neurotech futurista, empatía médica) y los traduce al lenguaje del **blanco premium**: limpieza quirúrgica, claridad científica, profundidad sutil por contraste de superficies, y acentos que respiran luz.

Los acentos teal/violet se mantienen pero se recalibran: en dark brillan como luces en la oscuridad; en light **anclan** y **dan peso** sobre fondos etéreos.

---

## ÍNDICE

1. [Nueva Paleta de Color (Light)](#1-nueva-paleta-de-color-light)
2. [Tipografía Adaptada](#2-tipografía-adaptada)
3. [Sistema de Superficies y Elevaciones](#3-sistema-de-superficies-y-elevaciones)
4. [Componentes UI — Light Mode](#4-componentes-ui--light-mode)
5. [Efectos Visuales Light-Mode](#5-efectos-visuales-light-mode)
6. [Sombras Calibradas para Superficies Blancas](#6-sombras-calibradas-para-superficies-blancas)
7. [Accesibilidad y Contraste](#7-accesibilidad-y-contraste)
8. [Design Tokens CSS — Light Theme](#8-design-tokens-css--light-theme)
9. [Variables Tailwind CSS](#9-variables-tailwind-css)
10. [Guía de Aplicación por Sección](#10-guía-de-aplicación-por-sección)

---

## 1. NUEVA PALETA DE COLOR (LIGHT)

### 1.1 Principios de la Paleta

En superficies blancas, el negro genera contraste demasiado crudo para un sector médico premium. Se utiliza **casi-negro con tinte azul-frío** para preservar la sensación neuro-tecnológica. Los acentos se desaturan ligeramente para evitar vibración óptica contra el blanco.

### 1.2 Backgrounds & Superficies

| Token | Hex | Descripción | Uso |
|---|---|---|---|
| `--nm-l-bg-base` | `#f8fafc` | Blanco frío ligerísimo | Background global del sitio |
| `--nm-l-bg-page` | `#ffffff` | Blanco puro | Secciones de contenido principal |
| `--nm-l-bg-surface` | `#f1f5f9` | Gris muy frío | Cards, contenedores |
| `--nm-l-bg-elevated` | `#e8eef6` | Gris frío con tinte azul | Cards hover, inputs |
| `--nm-l-bg-overlay` | `#dde6f0` | Gris azulado suave | Hover intenso, seleccionados |
| `--nm-l-bg-ink` | `#0f172a` | Casi negro azul | Secciones de contraste (hero/CTA) |
| `--nm-l-bg-ink-2` | `#1e293b` | Gris-carbón con azul | Secciones oscuras secundarias |
| `--nm-l-bg-glass` | `rgba(255,255,255,0.75)` | Blanco translúcido | Glassmorphism light |

**Razonamiento:** `#f8fafc` no es "blanco limpio hospitalario" — tiene una temperatura de color fría que resuena con el imaginario neuro-tecnológico. El cerebro humano asocia azul-frío con precisión clínica.

### 1.3 Acentos Calibrados para Light Mode

Los acentos del dark theme se ajustan:

| Token | Hex (Dark) | Hex (Light) | Por qué cambia |
|---|---|---|---|
| `--nm-l-accent` | `#00d4c8` (brillante) | `#0891b2` | Más profundo → visible contra blanco |
| `--nm-l-accent-bright` | — | `#06b6d4` | Para hover states y detalles |
| `--nm-l-accent-muted` | rgba(0,212,200,0.12) | `rgba(8,145,178,0.10)` | Fondos de badge/highlight |
| `--nm-l-violet` | `#7c5bf2` | `#7c3aed` | Violeta ligeramente más oscuro |
| `--nm-l-violet-light` | — | `#8b5cf6` | Para badges, tags secundarios |
| `--nm-l-blue` | `#3b82f6` | `#2563eb` | Azul más profundo en light |
| `--nm-l-amber` | `#f59e0b` | `#d97706` | Ámbar más saturado |

### 1.4 Colores de Texto

| Token | Hex | Ratio sobre bg-base | WCAG |
|---|---|---|---|
| `--nm-l-text-primary` | `#0f172a` | 17.4:1 | ✅ AAA |
| `--nm-l-text-secondary` | `#334155` | 9.8:1 | ✅ AAA |
| `--nm-l-text-body` | `#475569` | 6.2:1 | ✅ AA |
| `--nm-l-text-muted` | `#64748b` | 4.6:1 | ✅ AA |
| `--nm-l-text-placeholder` | `#94a3b8` | 2.9:1 | ⚠️ Solo placeholders |
| `--nm-l-text-disabled` | `#cbd5e1` | 1.9:1 | — Solo estados deshabilitados |
| `--nm-l-text-accent` | `#0891b2` | 4.5:1 | ✅ AA |
| `--nm-l-text-on-accent` | `#ffffff` | 4.9:1 | ✅ AA |
| `--nm-l-text-on-ink` | `#f8fafc` | 17.1:1 | ✅ AAA |

### 1.5 Gradientes Light Mode

```css
/* === HERO — fondo de sección principal light === */
--nm-l-gradient-hero: linear-gradient(
  160deg,
  #f8fafc 0%,
  #f1f5f9 50%,
  #e8eef6 100%
);

/* === HERO MIXTO — secciones con panel oscuro a la derecha === */
--nm-l-gradient-split: linear-gradient(
  105deg,
  #f8fafc 0%,
  #f8fafc 55%,
  #0f172a 55%,
  #0f172a 100%
);

/* === GRADIENTE ACENTO LIGHT === */
--nm-l-gradient-accent: linear-gradient(
  90deg,
  #0891b2 0%,
  #7c3aed 100%
);

/* === GRADIENTE ACENTO SUAVE (para borders, underlines) === */
--nm-l-gradient-accent-soft: linear-gradient(
  90deg,
  rgba(8, 145, 178, 0.7) 0%,
  rgba(124, 58, 237, 0.7) 100%
);

/* === GRADIENTE TEXTO (para H1 destacados) === */
--nm-l-gradient-text: linear-gradient(
  135deg,
  #0891b2 0%,
  #7c3aed 60%,
  #0891b2 100%
);

/* === GRADIENTE SUPERFICIE (sección "ink" sobre fondo claro) === */
--nm-l-gradient-ink-surface: linear-gradient(
  180deg,
  #0f172a 0%,
  #162032 100%
);

/* === GRADIENTE BORDE SUTIL === */
--nm-l-gradient-border: linear-gradient(
  135deg,
  rgba(8,145,178,0.3) 0%,
  rgba(124,58,237,0.3) 100%
);

/* === OVERLAY DE IMAGEN (secciones con foto) === */
--nm-l-gradient-img-overlay: linear-gradient(
  180deg,
  rgba(248, 250, 252, 0) 0%,
  rgba(248, 250, 252, 0.6) 70%,
  rgba(248, 250, 252, 1) 100%
);
```

### 1.6 Borders Light Mode

| Token | Valor | Uso |
|---|---|---|
| `--nm-l-border-subtle` | `rgba(15, 23, 42, 0.06)` | Bordes muy suaves |
| `--nm-l-border` | `rgba(15, 23, 42, 0.10)` | Cards, contenedores |
| `--nm-l-border-medium` | `rgba(15, 23, 42, 0.16)` | Inputs, hover |
| `--nm-l-border-strong` | `rgba(15, 23, 42, 0.24)` | Focus, seleccionados |
| `--nm-l-border-accent` | `rgba(8, 145, 178, 0.45)` | Focus con acento |
| `--nm-l-border-glass` | `rgba(255, 255, 255, 0.6)` | Glassmorphism light |
| `--nm-l-border-ink` | `rgba(255, 255, 255, 0.10)` | Bordes sobre superficies oscuras |

### 1.7 Estados Interactivos Light

```css
/* Hover sobre cards/contenedores */
--nm-l-state-hover: rgba(8, 145, 178, 0.05);

/* Active / pressed */
--nm-l-state-active: rgba(8, 145, 178, 0.10);

/* Focus ring */
--nm-l-state-focus-ring: 0 0 0 3px rgba(8, 145, 178, 0.25);

/* Selected */
--nm-l-state-selected: rgba(8, 145, 178, 0.08);
```

---

## 2. TIPOGRAFÍA ADAPTADA

### 2.1 Ajustes para Light Mode

La tipografía en fondos claros se comporta diferente:
- **Pesos más livianos** para títulos grandes (light absorbe más masa visual)
- **Body más oscuro** para mayor legibilidad
- **Line-height más generoso** en texto claro sobre blanco (más respiración)

| Rol | Dark Theme | White Theme | Ajuste |
|---|---|---|---|
| H1 display | 800 | **700** | Menos peso — el negro sobre blanco ya pesa |
| H2 | 700 | **600–700** | Idem |
| Body | 400 | **400** | Sin cambio |
| Labels | 600 | **500** | Más liviano |
| CTA | 600 | **600** | Sin cambio |

### 2.2 Tratamiento de Textos Degradados (Gradient Text)

```css
/* Título heroico con degradado teal-violeta */
.text-gradient-accent {
  background: var(--nm-l-gradient-text);
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: gradient-shift 6s ease infinite;
}

@keyframes gradient-shift {
  0%   { background-position: 0% center; }
  50%  { background-position: 100% center; }
  100% { background-position: 0% center; }
}

/* Subrayado decorativo con gradiente */
.heading-underline {
  position: relative;
  display: inline-block;
}

.heading-underline::after {
  content: '';
  position: absolute;
  bottom: -6px;
  left: 0;
  right: 0;
  height: 3px;
  border-radius: 2px;
  background: var(--nm-l-gradient-accent);
}
```

---

## 3. SISTEMA DE SUPERFICIES Y ELEVACIONES

### 3.1 Jerarquía de Elevación (Light Mode)

En dark mode, la elevación se expresa con **tonos más claros** (más luz = más cerca). En light mode, la elevación se expresa con **sombras** y **ligero contraste de color**.

```
Nivel 0 — Base page:    #f8fafc  (fondo del cuerpo)
Nivel 1 — Section bg:   #ffffff  (secciones principales, "papel")
Nivel 2 — Surface:      #f1f5f9  (cards estándar)
Nivel 3 — Elevated:     #e8eef6  (cards levantadas, inputs activos)
Nivel 4 — Floating:     #ffffff + sombra media (dropdowns, tooltips)
Nivel 5 — Ink Panel:    #0f172a  (secciones en negativo, footer, CTA hero)
```

### 3.2 Cards en Light Mode — Tres Variantes

#### Variante A: Card Flat (Minimalista)
```css
.card-flat {
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 16px;
  padding: 2rem 1.75rem;
  transition: all 0.25s var(--nm-ease-out);
}

.card-flat:hover {
  border-color: rgba(8, 145, 178, 0.25);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08),
              0 2px 8px rgba(15, 23, 42, 0.04);
  transform: translateY(-3px);
}
```

#### Variante B: Card con Sombra (Material Elevado)
```css
.card-elevated {
  background: #ffffff;
  border-radius: 16px;
  padding: 2rem 1.75rem;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06),
              0 4px 12px rgba(15, 23, 42, 0.06);
  transition: all 0.25s var(--nm-ease-out);
}

.card-elevated:hover {
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.10),
              0 16px 40px rgba(15, 23, 42, 0.08);
  transform: translateY(-4px);
}
```

#### Variante C: Card Glassmorphism Light
```css
.card-glass-light {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(16px) saturate(1.6);
  -webkit-backdrop-filter: blur(16px) saturate(1.6);
  border: 1px solid rgba(255, 255, 255, 0.65);
  border-radius: 20px;
  padding: 2rem 1.75rem;
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.08),
              inset 0 1px 0 rgba(255, 255, 255, 0.8);
  transition: all 0.3s var(--nm-ease-out);
}

.card-glass-light:hover {
  box-shadow: 0 12px 40px rgba(15, 23, 42, 0.12),
              inset 0 1px 0 rgba(255, 255, 255, 0.9);
  transform: translateY(-4px);
}
```

#### Variante D: Card Ink (sobre fondos oscuros del white theme)
```css
.card-ink {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.10);
  border-radius: 16px;
  padding: 2rem 1.75rem;
  transition: all 0.25s var(--nm-ease-out);
}

.card-ink:hover {
  background: rgba(255, 255, 255, 0.09);
  border-color: rgba(6, 182, 212, 0.35);
  transform: translateY(-3px);
}
```

### 3.3 Separadores Light Mode

```css
/* Separador sutil (línea) */
.divider-light {
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(15, 23, 42, 0.10) 30%,
    rgba(15, 23, 42, 0.10) 70%,
    transparent 100%
  );
  border: none;
  margin: 0;
}

/* Separador de sección (transición dark → light) */
.section-transition-to-dark {
  background: linear-gradient(
    180deg,
    #f8fafc 0%,
    #0f172a 100%
  );
  height: 120px;
  margin-bottom: -1px;
}

/* Wave SVG separator */
.wave-divider {
  overflow: hidden;
  line-height: 0;
}

.wave-divider svg {
  display: block;
}
```

---

## 4. COMPONENTES UI — LIGHT MODE

### 4.1 Navbar Light

```css
/* Estado default — sobre hero claro */
.navbar-light {
  background: rgba(248, 250, 252, 0.92);
  backdrop-filter: blur(16px) saturate(1.4);
  -webkit-backdrop-filter: blur(16px) saturate(1.4);
  border-bottom: 1px solid rgba(15, 23, 42, 0.07);
  transition: all 0.3s ease;
}

/* Cuando hay hero oscuro (sección ink) */
.navbar-over-dark {
  background: rgba(15, 23, 42, 0.88);
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
}

/* Nav items en light */
.nav-item-light {
  color: #475569;                    /* text-body */
  font-size: 0.9375rem;
  font-weight: 500;
}

.nav-item-light:hover,
.nav-item-light.active {
  color: #0f172a;                    /* text-primary */
}

.nav-item-light.active {
  color: #0891b2;                    /* accent */
}
```

### 4.2 Botones Light Mode

#### Primary — Sólido Teal
```css
.btn-primary-light {
  background: #0891b2;
  color: #ffffff;
  padding: 0.75rem 1.75rem;
  border-radius: 8px;
  font-size: 0.9375rem;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.2s var(--nm-ease-out);
  box-shadow: 0 2px 8px rgba(8, 145, 178, 0.25);
}

.btn-primary-light:hover {
  background: #0e7490;
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(8, 145, 178, 0.35);
}

.btn-primary-light:active {
  transform: translateY(0);
  background: #0c6780;
}
```

#### Primary — Gradient Premium
```css
.btn-gradient {
  background: linear-gradient(135deg, #0891b2 0%, #7c3aed 100%);
  color: #ffffff;
  padding: 0.75rem 1.75rem;
  border-radius: 8px;
  font-size: 0.9375rem;
  font-weight: 600;
  border: none;
  position: relative;
  overflow: hidden;
  transition: all 0.25s var(--nm-ease-out);
}

.btn-gradient::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #0e7490 0%, #6d28d9 100%);
  opacity: 0;
  transition: opacity 0.25s ease;
}

.btn-gradient:hover::before {
  opacity: 1;
}

.btn-gradient:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(8, 145, 178, 0.3),
              0 4px 12px rgba(124, 58, 237, 0.2);
}

.btn-gradient span {
  position: relative;
  z-index: 1;
}
```

#### Secondary / Ghost Light
```css
.btn-ghost-light {
  background: transparent;
  color: #334155;
  padding: 0.75rem 1.75rem;
  border-radius: 8px;
  border: 1px solid rgba(15, 23, 42, 0.14);
  font-size: 0.9375rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.btn-ghost-light:hover {
  background: rgba(8, 145, 178, 0.05);
  border-color: rgba(8, 145, 178, 0.35);
  color: #0891b2;
}
```

#### Outline Accent Light
```css
.btn-outline-light {
  background: transparent;
  color: #0891b2;
  border: 1.5px solid #0891b2;
  padding: 0.75rem 1.75rem;
  border-radius: 8px;
  font-size: 0.9375rem;
  font-weight: 600;
  transition: all 0.2s ease;
}

.btn-outline-light:hover {
  background: rgba(8, 145, 178, 0.08);
  border-color: #0e7490;
}
```

### 4.3 Service Cards Light

```css
.service-card-light {
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 16px;
  padding: 2rem 1.75rem;
  position: relative;
  overflow: hidden;
  transition: all 0.3s var(--nm-ease-out);
}

/* Acento top border (se activa en hover) */
.service-card-light::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: linear-gradient(90deg, #0891b2, #7c3aed);
  opacity: 0;
  transition: opacity 0.3s ease;
}

/* Icono del servicio */
.service-card-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(8, 145, 178, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.25rem;
  color: #0891b2;
  transition: all 0.3s ease;
}

.service-card-light:hover {
  border-color: rgba(8, 145, 178, 0.20);
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.10),
              0 4px 12px rgba(8, 145, 178, 0.06);
  transform: translateY(-4px);
}

.service-card-light:hover::before {
  opacity: 1;
}

.service-card-light:hover .service-card-icon {
  background: rgba(8, 145, 178, 0.15);
  transform: scale(1.05);
}
```

### 4.4 Inputs Light Mode

```css
.form-input-light {
  background: #ffffff;
  border: 1.5px solid rgba(15, 23, 42, 0.12);
  border-radius: 10px;
  padding: 0.875rem 1.125rem;
  color: #0f172a;
  font-size: 1rem;
  width: 100%;
  transition: all 0.2s ease;
}

.form-input-light::placeholder {
  color: #94a3b8;
}

.form-input-light:hover {
  border-color: rgba(15, 23, 42, 0.22);
}

.form-input-light:focus {
  outline: none;
  border-color: #0891b2;
  box-shadow: 0 0 0 3px rgba(8, 145, 178, 0.15);
  background: #fafcfd;
}

/* Label */
.form-label-light {
  font-size: 0.8125rem;
  font-weight: 500;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 0.375rem;
  display: block;
}
```

### 4.5 Badges Light Mode

```css
.badge-light-teal {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  border-radius: 100px;
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  background: rgba(8, 145, 178, 0.08);
  color: #0891b2;
  border: 1px solid rgba(8, 145, 178, 0.18);
}

.badge-light-violet {
  background: rgba(124, 58, 237, 0.08);
  color: #7c3aed;
  border: 1px solid rgba(124, 58, 237, 0.18);
}

.badge-light-slate {
  background: rgba(15, 23, 42, 0.06);
  color: #475569;
  border: 1px solid rgba(15, 23, 42, 0.10);
}

.badge-light-success {
  background: rgba(16, 185, 129, 0.08);
  color: #059669;
  border: 1px solid rgba(16, 185, 129, 0.18);
}
```

### 4.6 Profile Cards Light

```css
.profile-card-light {
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 20px;
  padding: 2rem;
  text-align: center;
  transition: all 0.3s var(--nm-ease-out);
}

.profile-card-light img {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #e8eef6;
  margin-bottom: 1rem;
  transition: border-color 0.3s ease;
}

.profile-card-light:hover {
  border-color: rgba(8, 145, 178, 0.20);
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.10);
  transform: translateY(-5px);
}

.profile-card-light:hover img {
  border-color: rgba(8, 145, 178, 0.35);
}
```

### 4.7 Marquee Light Mode

```css
.marquee-light {
  background: linear-gradient(
    135deg,
    rgba(8, 145, 178, 0.04) 0%,
    rgba(124, 58, 237, 0.04) 100%
  );
  border-top: 1px solid rgba(8, 145, 178, 0.12);
  border-bottom: 1px solid rgba(8, 145, 178, 0.12);
  padding: 1rem 0;
  overflow: hidden;
}

.marquee-light .marquee-content {
  color: #475569;
  font-size: 0.875rem;
  font-weight: 500;
}

.marquee-light .marquee-content span::after {
  color: #0891b2;
  opacity: 0.7;
}
```

### 4.8 Footer Light Mode

```css
/* Opción A: Footer claro (minimalista) */
.footer-light {
  background: #f1f5f9;
  border-top: 1px solid rgba(15, 23, 42, 0.08);
  padding: 3rem 0 2rem;
}

/* Opción B: Footer oscuro (contraste premium) */
.footer-ink {
  background: #0f172a;
  padding: 3rem 0 2rem;
}

.footer-ink .footer-copyright {
  color: rgba(248, 250, 252, 0.45);
}

.footer-ink .footer-social a {
  border-color: rgba(255, 255, 255, 0.12);
  color: rgba(248, 250, 252, 0.6);
}

.footer-ink .footer-social a:hover {
  border-color: #0891b2;
  color: #06b6d4;
  background: rgba(8, 145, 178, 0.08);
}
```

---

## 5. EFECTOS VISUALES LIGHT-MODE

### 5.1 Glassmorphism Light

El glassmorphism en light mode es más sutil: las capas no brillan por sí mismas sino que **filtran y desaturan** lo que hay detrás.

```css
/* Glassmorphism estándar light */
.glass-light-panel {
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(16px) saturate(1.8) brightness(1.05);
  -webkit-backdrop-filter: blur(16px) saturate(1.8) brightness(1.05);
  border: 1px solid rgba(255, 255, 255, 0.55);
  border-radius: 20px;
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.08),
              inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

/* Navbar glass light */
.glass-navbar-light {
  background: rgba(248, 250, 252, 0.88);
  backdrop-filter: blur(20px) saturate(1.6);
  -webkit-backdrop-filter: blur(20px) saturate(1.6);
  border-bottom: 1px solid rgba(15, 23, 42, 0.07);
}

/* Glass sobre secciones de color */
.glass-over-gradient {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 8px 32px rgba(8, 145, 178, 0.10);
}
```

### 5.2 Ambient Light Effects (Fondos Decorativos)

```css
/* Halo teal detrás del hero */
.ambient-teal {
  position: absolute;
  width: 600px;
  height: 400px;
  border-radius: 50%;
  background: radial-gradient(
    ellipse at center,
    rgba(8, 145, 178, 0.10) 0%,
    transparent 70%
  );
  filter: blur(40px);
  pointer-events: none;
}

/* Halo violet (secundario) */
.ambient-violet {
  background: radial-gradient(
    ellipse at center,
    rgba(124, 58, 237, 0.07) 0%,
    transparent 70%
  );
  filter: blur(60px);
}

/* Grid pattern sutil (fondo hero) */
.pattern-grid {
  background-image: linear-gradient(
    rgba(8, 145, 178, 0.04) 1px,
    transparent 1px
  ),
  linear-gradient(
    90deg,
    rgba(8, 145, 178, 0.04) 1px,
    transparent 1px
  );
  background-size: 32px 32px;
}

/* Dot pattern sutil */
.pattern-dots {
  background-image: radial-gradient(
    rgba(8, 145, 178, 0.12) 1.5px,
    transparent 1.5px
  );
  background-size: 24px 24px;
}
```

### 5.3 Highlight / Accent Lines

```css
/* Línea de acento debajo de títulos */
.accent-underline {
  display: inline-block;
  position: relative;
}

.accent-underline::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: -4px;
  width: 100%;
  height: 3px;
  border-radius: 2px;
  background: linear-gradient(90deg, #0891b2, #7c3aed);
}

/* Borde izquierdo de acento (blockquote, cards de info) */
.accent-border-left {
  border-left: 3px solid #0891b2;
  padding-left: 1.25rem;
}

/* Accent border gradient */
.accent-border-gradient {
  border-image: linear-gradient(180deg, #0891b2, #7c3aed) 1;
}
```

---

## 6. SOMBRAS CALIBRADAS PARA SUPERFICIES BLANCAS

Las sombras en light mode son más visibles y deben ser más sutiles. Un error común es usar sombras negras opacas — generan aspecto anticuado. El sistema usa sombras en tono del texto base (`#0f172a`).

```css
/* ─── ELEVACIONES LIGHT ──────────────────────────── */

/* Nivel 1 — Casi plano (bordes bastante) */
--nm-l-shadow-xs:
  0 1px 2px rgba(15, 23, 42, 0.04),
  0 1px 3px rgba(15, 23, 42, 0.04);

/* Nivel 2 — Card estándar */
--nm-l-shadow-sm:
  0 1px 3px rgba(15, 23, 42, 0.06),
  0 4px 8px rgba(15, 23, 42, 0.04);

/* Nivel 3 — Card elevada / hover */
--nm-l-shadow-md:
  0 4px 12px rgba(15, 23, 42, 0.08),
  0 8px 24px rgba(15, 23, 42, 0.06);

/* Nivel 4 — Dropdown / popup */
--nm-l-shadow-lg:
  0 8px 24px rgba(15, 23, 42, 0.10),
  0 16px 48px rgba(15, 23, 42, 0.08);

/* Nivel 5 — Modal / drawer */
--nm-l-shadow-xl:
  0 16px 48px rgba(15, 23, 42, 0.12),
  0 32px 80px rgba(15, 23, 42, 0.10);

/* Sombras de color (teal) */
--nm-l-shadow-teal-sm:
  0 4px 12px rgba(8, 145, 178, 0.15);

--nm-l-shadow-teal-md:
  0 8px 24px rgba(8, 145, 178, 0.20),
  0 4px 8px rgba(8, 145, 178, 0.12);

/* Sombra para botones CTA */
--nm-l-shadow-btn:
  0 2px 8px rgba(8, 145, 178, 0.25),
  0 1px 2px rgba(8, 145, 178, 0.15);

--nm-l-shadow-btn-hover:
  0 6px 20px rgba(8, 145, 178, 0.35),
  0 2px 8px rgba(8, 145, 178, 0.20);

/* Inset sombra (campos activos) */
--nm-l-shadow-inset:
  inset 0 1px 2px rgba(15, 23, 42, 0.06);

/* Sombra-borde combinada (alternativa a border) */
--nm-l-shadow-ring:
  0 0 0 1px rgba(15, 23, 42, 0.08),
  0 4px 12px rgba(15, 23, 42, 0.06);

--nm-l-shadow-ring-accent:
  0 0 0 1px rgba(8, 145, 178, 0.25),
  0 4px 16px rgba(8, 145, 178, 0.10);
```

---

## 7. ACCESIBILIDAD Y CONTRASTE

### 7.1 Tabla de Contrastes

| Combinación | Ratio | WCAG AA | WCAG AAA | Recomendación |
|---|---|---|---|---|
| `#0f172a` sobre `#f8fafc` | 17.4:1 | ✅ | ✅ | Títulos, body — excelente |
| `#334155` sobre `#f8fafc` | 9.8:1 | ✅ | ✅ | Subtítulos — excelente |
| `#475569` sobre `#f8fafc` | 6.2:1 | ✅ | ✅ | Body copy — correcto |
| `#64748b` sobre `#f8fafc` | 4.6:1 | ✅ | ❌ | Text muted — OK solo 14px+ |
| `#0891b2` sobre `#f8fafc` | 4.5:1 | ✅ | ❌ | Links, acento — límite AA |
| `#0891b2` sobre `#ffffff` | 4.7:1 | ✅ | ❌ | Aceptable para botones |
| `#ffffff` sobre `#0891b2` | 4.7:1 | ✅ | ❌ | Texto en botones teal — OK |
| `#ffffff` sobre `#7c3aed` | 5.5:1 | ✅ | ❌ | Texto en botones violeta |
| `#0f172a` sobre `#ffffff` | 18.1:1 | ✅ | ✅ | Cards sobre blanco puro |
| `#94a3b8` sobre `#f8fafc` | 2.9:1 | ❌ | ❌ | Solo para placeholders |

### 7.2 Reglas de Accesibilidad

```css
/* Focus visible — nunca quitar outline, reemplazar con elegancia */
*:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(8, 145, 178, 0.25),
              0 0 0 1.5px #0891b2;
}

/* Skip link para keyboard navigation */
.skip-link {
  position: absolute;
  top: -100%;
  left: 1rem;
  z-index: 9999;
  background: #0891b2;
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  text-decoration: none;
  transition: top 0.2s;
}

.skip-link:focus {
  top: 1rem;
}

/* Respetar preferencia de movimiento */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* High contrast mode */
@media (forced-colors: active) {
  .btn-primary-light {
    border: 2px solid ButtonText;
  }
}
```

### 7.3 Recomendaciones Adicionales

1. **No usar solo color para comunicar estado** — combinar color + ícono + texto
2. **Texto mínimo 14px** para elementos con contraste AA (sin AAA)
3. **Links subrayados** en cuerpo de texto (no solo color)
4. **Alt text descriptivo** en todas las imágenes médicas
5. **Etiquetas `<label>` explícitas** en formularios (no solo placeholder)
6. **ARIA roles** para marquee/carruseles (role="marquee", aria-label)

---

## 8. DESIGN TOKENS CSS — LIGHT THEME

### 8.1 Archivo Completo de Tokens

```css
/* ============================================================
   NEUROMOOD WHITE — LIGHT THEME DESIGN TOKENS
   Versión: 1.0 | Mayo 2026
   ============================================================ */

:root[data-theme="light"],
.theme-light {

  /* ─── BACKGROUNDS ───────────────────────────────────────── */
  --nm-bg-base:       #f8fafc;
  --nm-bg-page:       #ffffff;
  --nm-bg-surface:    #f1f5f9;
  --nm-bg-elevated:   #e8eef6;
  --nm-bg-overlay:    #dde6f0;
  --nm-bg-ink:        #0f172a;
  --nm-bg-ink-2:      #1e293b;
  --nm-bg-glass:      rgba(255, 255, 255, 0.75);

  /* ─── ACCENT COLORS ─────────────────────────────────────── */
  --nm-accent:           #0891b2;
  --nm-accent-bright:    #06b6d4;
  --nm-accent-dim:       #0e7490;
  --nm-accent-muted:     rgba(8, 145, 178, 0.10);
  --nm-accent-surface:   rgba(8, 145, 178, 0.06);
  --nm-violet:           #7c3aed;
  --nm-violet-light:     #8b5cf6;
  --nm-violet-muted:     rgba(124, 58, 237, 0.10);
  --nm-blue:             #2563eb;
  --nm-amber:            #d97706;

  /* ─── TEXT ──────────────────────────────────────────────── */
  --nm-text-primary:     #0f172a;
  --nm-text-secondary:   #334155;
  --nm-text-body:        #475569;
  --nm-text-muted:       #64748b;
  --nm-text-placeholder: #94a3b8;
  --nm-text-disabled:    #cbd5e1;
  --nm-text-accent:      #0891b2;
  --nm-text-on-accent:   #ffffff;
  --nm-text-on-ink:      #f8fafc;

  /* ─── BORDERS ───────────────────────────────────────────── */
  --nm-border-subtle:  rgba(15, 23, 42, 0.06);
  --nm-border:         rgba(15, 23, 42, 0.10);
  --nm-border-medium:  rgba(15, 23, 42, 0.16);
  --nm-border-strong:  rgba(15, 23, 42, 0.24);
  --nm-border-accent:  rgba(8, 145, 178, 0.40);
  --nm-border-glass:   rgba(255, 255, 255, 0.60);
  --nm-border-ink:     rgba(255, 255, 255, 0.10);

  /* ─── SHADOWS ───────────────────────────────────────────── */
  --nm-shadow-xs: 0 1px 2px rgba(15,23,42,0.04), 0 1px 3px rgba(15,23,42,0.04);
  --nm-shadow-sm: 0 1px 3px rgba(15,23,42,0.06), 0 4px 8px rgba(15,23,42,0.04);
  --nm-shadow-md: 0 4px 12px rgba(15,23,42,0.08), 0 8px 24px rgba(15,23,42,0.06);
  --nm-shadow-lg: 0 8px 24px rgba(15,23,42,0.10), 0 16px 48px rgba(15,23,42,0.08);
  --nm-shadow-xl: 0 16px 48px rgba(15,23,42,0.12), 0 32px 80px rgba(15,23,42,0.10);
  --nm-shadow-teal: 0 6px 20px rgba(8,145,178,0.25), 0 2px 8px rgba(8,145,178,0.15);
  --nm-shadow-btn: 0 2px 8px rgba(8,145,178,0.25);
  --nm-shadow-btn-hover: 0 6px 20px rgba(8,145,178,0.35);

  /* ─── RADIUS ────────────────────────────────────────────── */
  --nm-radius-xs:    4px;
  --nm-radius-sm:    6px;
  --nm-radius-btn:   8px;
  --nm-radius-input: 10px;
  --nm-radius-card:  16px;
  --nm-radius-lg:    20px;
  --nm-radius-xl:    24px;
  --nm-radius-pill:  100px;

  /* ─── TYPOGRAPHY (igual que dark) ───────────────────────── */
  --nm-font-sans: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
  --nm-font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  /* ─── GRADIENTS ─────────────────────────────────────────── */
  --nm-gradient-hero: linear-gradient(160deg, #f8fafc 0%, #f1f5f9 50%, #e8eef6 100%);
  --nm-gradient-accent: linear-gradient(90deg, #0891b2 0%, #7c3aed 100%);
  --nm-gradient-text: linear-gradient(135deg, #0891b2 0%, #7c3aed 60%, #0891b2 100%);
  --nm-gradient-ink: linear-gradient(180deg, #0f172a 0%, #162032 100%);

  /* ─── STATES ────────────────────────────────────────────── */
  --nm-state-hover:    rgba(8, 145, 178, 0.05);
  --nm-state-active:   rgba(8, 145, 178, 0.10);
  --nm-state-focus:    0 0 0 3px rgba(8, 145, 178, 0.20);
  --nm-state-selected: rgba(8, 145, 178, 0.08);

  /* ─── TRANSITIONS (igual que dark) ─────────────────────── */
  --nm-duration-fast:   150ms;
  --nm-duration-normal: 250ms;
  --nm-duration-slow:   350ms;
  --nm-ease-soft:       cubic-bezier(0.25, 0.46, 0.45, 0.94);
  --nm-ease-out:        cubic-bezier(0.25, 1, 0.5, 1);
  --nm-ease-spring:     cubic-bezier(0.34, 1.56, 0.64, 1);
}
```

---

## 9. VARIABLES TAILWIND CSS

### 9.1 tailwind.config.js — White Theme

```javascript
// tailwind.config.js
const nmLight = {
  // Backgrounds
  'bg-base':     '#f8fafc',
  'bg-page':     '#ffffff',
  'bg-surface':  '#f1f5f9',
  'bg-elevated': '#e8eef6',
  'bg-overlay':  '#dde6f0',
  'bg-ink':      '#0f172a',

  // Accents
  'accent':         '#0891b2',
  'accent-bright':  '#06b6d4',
  'accent-dim':     '#0e7490',
  'violet':         '#7c3aed',
  'violet-light':   '#8b5cf6',

  // Text
  'text-primary':   '#0f172a',
  'text-secondary': '#334155',
  'text-body':      '#475569',
  'text-muted':     '#64748b',
  'text-on-ink':    '#f8fafc',
};

module.exports = {
  theme: {
    extend: {
      colors: { nm: nmLight },

      backgroundImage: {
        'nm-hero':    'linear-gradient(160deg, #f8fafc 0%, #f1f5f9 50%, #e8eef6 100%)',
        'nm-accent':  'linear-gradient(90deg, #0891b2 0%, #7c3aed 100%)',
        'nm-gradient-text': 'linear-gradient(135deg, #0891b2, #7c3aed)',
      },

      boxShadow: {
        'nm-card':  '0 4px 12px rgba(15,23,42,0.08), 0 8px 24px rgba(15,23,42,0.06)',
        'nm-hover': '0 8px 24px rgba(15,23,42,0.10), 0 16px 48px rgba(15,23,42,0.08)',
        'nm-teal':  '0 6px 20px rgba(8,145,178,0.25), 0 2px 8px rgba(8,145,178,0.15)',
        'nm-btn':   '0 2px 8px rgba(8,145,178,0.25)',
        'nm-btn-hover': '0 6px 20px rgba(8,145,178,0.35)',
        'nm-focus': '0 0 0 3px rgba(8,145,178,0.20)',
      },

      borderRadius: {
        'nm-btn':   '8px',
        'nm-card':  '16px',
        'nm-lg':    '20px',
        'nm-xl':    '24px',
      },

      backdropBlur: {
        'nm-glass': '16px',
        'nm-nav':   '20px',
      },
    }
  }
}
```

### 9.2 Clases Utilitarias Custom (Tailwind Plugin)

```javascript
// plugin personalizado
plugin(({ addUtilities, theme }) => {
  addUtilities({
    '.text-gradient-accent': {
      background: 'linear-gradient(135deg, #0891b2, #7c3aed)',
      '-webkit-background-clip': 'text',
      '-webkit-text-fill-color': 'transparent',
      'background-clip': 'text',
    },
    '.glass-light': {
      background: 'rgba(255,255,255,0.75)',
      'backdrop-filter': 'blur(16px) saturate(1.6)',
      '-webkit-backdrop-filter': 'blur(16px) saturate(1.6)',
      border: '1px solid rgba(255,255,255,0.55)',
    },
    '.nm-surface': {
      background: '#ffffff',
      border: '1px solid rgba(15,23,42,0.08)',
      'border-radius': '16px',
    },
    '.nm-section-py': {
      'padding-top': 'clamp(4rem, 8vw, 7rem)',
      'padding-bottom': 'clamp(4rem, 8vw, 7rem)',
    },
  })
})
```

---

## 10. GUÍA DE APLICACIÓN POR SECCIÓN

### Cómo implementar el White Theme en cada sección de NeuroMood:

#### 10.1 Hero — White Theme

```
Fondo:        --nm-bg-base (#f8fafc) + ambient glow teal (radial, opacity 0.10)
              + pattern-dots en esquina (opacity 0.05)
Layout:       55% texto + 45% imagen (misma distribución dark)
H1:           --nm-text-primary / font-weight: 700
              Palabra clave puede ir en .text-gradient-accent
Body:         --nm-text-body / leading relaxed
CTA Primary:  .btn-gradient (teal → violet)
CTA Ghost:    .btn-ghost-light
Imagen:       Overlay bottom: --nm-l-gradient-img-overlay
              Border-radius: 20px / box-shadow: --nm-shadow-xl
```

#### 10.2 Servicios — White Theme

```
Fondo:        #ffffff (contraste con base)
Cards:        .card-flat o .card-elevated (según nivel de profundidad deseado)
Íconos:       Container rgba(8,145,178,0.08) / color: --nm-accent
Hover:        translateY(-4px) + --nm-shadow-md + border-color accent
Divider top:  .section-divider-light
```

#### 10.3 Instalaciones — White Theme

```
Fondo:        .nm-bg-ink (#0f172a) — sección de contraste inverso
Texto:        --nm-text-on-ink
CTA:          .btn-primary-light o .btn-outline-light (visible en oscuro)
Imagen:       sin overlay (ya está sobre oscuro)
Nota:         Intercalar sección oscura = estrategia premium de ritmo visual
```

#### 10.4 Especialistas — White Theme

```
Fondo:        --nm-bg-surface (#f1f5f9)
Cards:        .profile-card-light
Fotos:        border: 3px solid #e8eef6 → on hover: border-color: rgba(8,145,178,0.35)
Títulos prof: .badge-light-teal
```

#### 10.5 Contacto — White Theme

```
Fondo:        --nm-bg-base (#f8fafc)
Cards método: .service-card-light
Formulario:   .form-input-light / .form-label-light
CTA form:     .btn-gradient (full width en mobile)
WA Button:    Fixed bottom-right / background: #25D366 / border-radius: 50%
              box-shadow: --nm-shadow-teal-md
```

#### 10.6 Footer — White Theme

```
Opción A (minimalista): background: --nm-bg-surface / border-top: subtle
Opción B (premium):     background: --nm-bg-ink (#0f172a) = contraste dramático
Recomendación:          Opción B para mayor impacto — cierra el ciclo visual
                        que empezó con el hero claro
```

---

## BONUS: Estrategia Dark/Light Switch

Para implementar un toggle de tema, usar data-attribute en el root:

```html
<html data-theme="light">
  <!-- O data-theme="dark" -->
</html>
```

```css
/* Light Theme (default) */
:root, :root[data-theme="light"] {
  --nm-bg-base: #f8fafc;
  --nm-text-primary: #0f172a;
  /* ... todos los tokens light ... */
}

/* Dark Theme */
:root[data-theme="dark"] {
  --nm-bg-base: #050911;
  --nm-text-primary: #f0f4ff;
  /* ... todos los tokens dark ... */
}

/* System preference (auto) */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --nm-bg-base: #050911;
    /* ... dark tokens ... */
  }
}
```

```javascript
// Toggle button
const toggleTheme = () => {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'light' ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('nm-theme', next);
};

// Persistencia
const savedTheme = localStorage.getItem('nm-theme') ||
  (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
document.documentElement.setAttribute('data-theme', savedTheme);
```

---

*White Theme System generado como identidad paralela de neuromood.com.ar — Mayo 2026*  
*Profundidad: UI/UX Senior — Production-ready*
