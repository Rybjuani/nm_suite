# Plan Maestro de Migración UI · V2 · NeuroMood (Suite + Hub → mockup canónico)

> **Estado vivo · documento de handoff entre agentes.** Supera a `PLAN_MIGRACION_UI.md`
> (intento anterior, conservado como histórico). Fuente visual: `neuromood-mockup.html`.
> Marco de ejecución: `agent_harness/`. Regla de oro: **fidelidad perceptual alta, estable
> y verificable en runtime 960×600 — NO pixel-perfect HTML/CSS.**

---

## 1. Resumen ejecutivo

La migración al ADN del mockup **ya pasó su fase de cimientos**: tokens, fuentes
(Inter+Fraunces), generadores QSS por tema e íconos están implementados y **bloqueados por
tests**; las primitivas compartidas tienen **contratos verificables**; las pantallas son
**estructuralmente fieles**. Lo que queda NO es re-tokenizar ni reescribir pantallas desde
cero: es **bajar deuda real, verificada y acotada** —clipping, densidad, proporciones,
estados, microfidelidad— por **clusters chicos**, cada uno cerrado con evidencia de runtime.

Este V2 evita el modo de fallo del V1 (planes monolíticos, SSIM como gate, revivir UI
eliminada, gigantismo). Aporta tres cosas que el V1 no tenía operativas:

1. **Diccionario de Traducción Web→PyQt6** (§5): recetas-ley para que ningún agente
   reinvente una card, un tab, una sombra o una animación.
2. **Secuencia por olas → episodios del harness** (§8–§9): unidades chicas con scope,
   validación, criterio de corte y handoff explícito; si una sesión se corta, otra retoma.
3. **Protocolo QA runtime-first** (§10): gate = `qa/runtime_live_probe.py` + tests de
   contrato + tests anti-legacy. **SSIM es señal auxiliar, nunca gate** (saturado por fuente).

**Definición de "terminado":** probe `OK` en todas las vistas (suite+hub, light+dark,
960×600), suite de contratos verde, cero strings/visuales prohibidos, y revisión humana
lado-a-lado de las pantallas clave. No hay número de SSIM que cierre la migración.

---

## 2. Estado actual detectado del repo

*(verificado en HEAD `e95bc2b`, `main` == `origin/main`, working tree limpio)*

### 2.1 Cimientos — DONE y bloqueados

| Área | Archivo(s) | Estado | Lock |
|---|---|---|---|
| Tokens claro/oscuro | `shared/theme.py` (`V3_LIGHT`/`V3_DARK`/`V3_RADIUS`/`V3_SPACE`) | = mockup exacto | `tests/test_token_parity.py`, `tests/test_no_legacy_visuals.py` |
| Fuentes | `shared/fonts.py` + `assets/fonts/` (Inter, Fraunces TTF) | cargan | `tests/test_fonts.py` |
| Generadores QSS | `shared/theme_qt.py` (`stylesheet_base`, `stylesheet_slider`, `stylesheet_tabwidget_segmented`, `stylesheet_lineedit`, `stylesheet_textedit`, `stylesheet_combobox`, `stylesheet_scrollarea`…) | re-templados al ADN | tests de contrato por componente |
| Íconos | `shared/icons_svg.py` (`ICON_BODIES` + set `I` del mockup) | empaquetados | `tests/test_icons_svg.py` |
| Compat tokens | `shared/design_tokens.py` (fachada sobre `theme`) | ok | `test_no_legacy_visuals.py` |

> **No re-tokenizar. No tocar `V3_SPACE`/`V3_RADIUS`/colores.** El "grid 8px" se logra por
> *uso* (16/24/32), no cambiando tokens. Cualquier cambio de token rompe `test_token_parity`.

### 2.2 Primitivas compartidas — contract-tested

`shared/components/*` (≈47 widgets). Contratos vigentes en `tests/test_component_visual_contract.py`:

- `NMButton` — alto `_NM_CONTROL_HEIGHT=42` / `_NM_CONTROL_COMPACT_HEIGHT=34`; variantes
  `gradient|secondary|ghost|danger|soft`; **press NO muta geometry** (anim sobre propiedad
  visual); alto sobrevive a QSS global de `QPushButton`.
- `NMTabs` pill/seg — contenedor pintado, pad 5 / gap 4 / alto botón 30, selección `brand`.
- `NMBadge` — tonos `brand|accent|gold|rose`, radio pill, padding 4×11.
- `NMCard` — contrato de radio/sombra/padding alineado (commits `0b8f779`, `c24e71e`).
- `NMSearchInput` — density bounds acotados (`632d6a2`).
- `NMEmptyState` — subtítulo no se trunca a 1 línea (`85fa180`).
- `NMPatientRow*` — sin clipping de fila (`33fde08`).

### 2.3 Pantallas — estructuralmente fieles

Suite: Home, Ánimo, Respiración, Registro TCC, Activación/Actividades, Avisos, Rutina,
Timer, DBT (Ahora/Biblioteca + **Historial extra conservado**), Onboarding/Recuperar.
Hub: Pacientes, Detalle (**aplanado a 4 tabs + grid form|panel**), Configuración global
Suite (clon navegable de la Suite para editar textos), modales IA/PDF.

### 2.4 Frente activo (cierre E5)

La deuda operativa de UI V2 quedó cerrada al commit `c0c692e`: probe runtime 22/22,
capturas finales 98/98, suite de contratos verde y barrido visual técnico sin deuda
accionable. Los commits previos de integridad runtime / densidad / clipping quedan como
histórico de ejecución, no como frente abierto.

### 2.5 Tooling QA presente

- `qa/runtime_live_probe.py` — **gate de runtime** (subproceso real, ghost windows,
  no-cierre, size 960×600, hashes dup). Vistas: suite `home/animo/respiracion/timer/avisos/
  registro/rutina/actividades/dbt`, hub `pacientes/detalle`.
- `qa/capture_v8.py` — matriz offscreen in-process (≈96 PNG suite+hub, light/dark).
- `qa/capture_mockup.py` (Playwright) → `qa/_mockup_targets/` (targets del mockup).
- `qa/diff_fidelity.py` — SSIM/MAD vs targets. **Auxiliar, no gate.**
- Tests: ≈269 (pytest+pytest-qt), `ruff`. Pyright **no** instalado en el venv.

### 2.6 Hallazgos viejos que quedaron STALE (no re-actuar)

- ADN lavanda / Manrope+Newsreader → **superado**, hoy prohibido por test.
- "Re-tokenizar a valores del mockup" (FASE 1 del V1) → **hecho**.
- Sidebar/nav-rail web, selector Suite/Hub, chip-state, "device window" → **andamios del
  mockup, nunca fueron producto**. No revivir.
- Strings eliminados: **"Registrar ánimo", "Registrar ahora", "Sin registro hoy", "Sin
  registros hoy", "Notas del día"** → no revivir (ver §12 guardas).
- Capturas QA stale de `qa/_fidelity_fresh/` con SSIM bajo por fuente -> no son defectos;
  los reports frescos son efimeros y ese directorio ya no se versiona.

---

## 3. Postmortem del plan anterior

El V1 (`PLAN_MIGRACION_UI.md`) acertó el ADN pero falló en ejecución. Causas y corrección:

| # | Falla del V1 | Síntoma | Qué cambia en V2 |
|---|---|---|---|
| 1 | **Supuestos peligrosos** (memoria stale = estado real) | Re-auditar lo ya hecho, perseguir pantallas inexistentes | §2 fija estado verificado en HEAD; "no asumir, verificar contra código + captura" |
| 2 | **Instrucciones globales** ("retunear todo", "polish global") | Diffs gigantes, regresiones | Olas→episodios de **1 cluster** (una pantalla/componente); `git add` explícito |
| 3 | **No runtime-first** | Lindo en captura, roto a 960×600 (clip, off-viewport) | Gate = `runtime_live_probe.py`; OLA 0 antes de fidelidad fina |
| 4 | **SSIM como gate (0.92)** | "94 failures" que no eran defectos; falsa tranquilidad o falsa alarma | SSIM **auxiliar**; gate = probe + contratos + revisión humana |
| 5 | **Sin diccionario web→Qt** | Cada pantalla reinventaba card/tab/sombra/anim distinto | §5 Diccionario-ley, primitivas compartidas obligatorias |
| 6 | **Sin contratos de primitivas** | Drift entre consumidores | Contratos en `tests/test_*_visual_contract.py` (ya existen, se extienden) |
| 7 | **Regresiones viewport/clipping/gigantismo** | Padding 24 global empuja acciones fuera, botones clipeados | OLA 0 dedicada + reglas anti-gigantismo (§5.6) |
| 8 | **Riesgo de revivir UI eliminada** | CTAs/sidebar/strings borrados reaparecen | Guardas anti-legacy (§12) + tests `test_no_legacy_*` |
| 9 | **Sin handoff entre agentes** | Sesión cortada = re-interpretar toda la estrategia | Episodios con estado/criterio-corte/handoff (§9) + harness |
| 10 | **Filosofar (SSIM/font-ceiling/"fiel")** | Pasadas simbólicas sin bajar deuda | Regla dura: si el delta es real, arreglarlo; si no, callar. No ensayos. |

---

## 4. Jerarquía de fuentes de verdad

Ante conflicto, **gana el número más bajo**:

1. **App real en runtime 960×600 (light+dark), navegada de verdad.** Si rompe aquí, es bug.
2. **Decisiones explícitas del owner** (eliminaciones, deltas aceptados — ver §12).
3. **Código actual** (`shared/theme.py`, primitivas, tests de contrato vigentes).
4. **`neuromood-mockup.html`** como referencia visual **filtrada** (sin la cáscara web).
5. **Auditorías externas / PPT / SSIM reports** = evidencia **secundaria**, nunca autoridad.

Corolarios:
- El mockup NO se obedece ciegamente. Si muestra algo que el owner eliminó, gana el owner.
- Un sidebar/nav del mockup **no vuelve** si la app real ya no lo usa.
- Se preserva 100% de lógica clínica, datos, auth, PDF, IA, notificaciones, persistencia,
  señales y navegación real. La UI se recablea a los *seams* existentes, no se reimplementan.

---

## 5. Diccionario de Traducción Web → PyQt6  *(LEY para implementadores)*

> Regla 0: **no traducir CSS literal.** Traducir la *intención* a la receta estable de abajo.
> Antes de crear un widget, buscar la primitiva en `shared/components/` — si existe, se usa
> y se respeta su contrato; no se improvisa una variante local.
> Valores canónicos: `neuromood-mockup.html` líneas 15–360 (tokens y CSS de componentes).

### 5.1 Layout

| Web | Receta PyQt6 estable | Notas |
|---|---|---|
| `display:flex; flex-direction:row; gap:N` | `QHBoxLayout`, `setSpacing(N)`, `setContentsMargins(...)` explícitos | nunca dejar margins por defecto |
| `flex-direction:column; gap:N` | `QVBoxLayout`, `setSpacing(N)` | |
| `padding:N` (contenedor) | `layout.setContentsMargins(N,N,N,N)` **del layout interno**, no del widget | evita doble margen |
| `display:grid; grid-template-columns:A B` | `QGridLayout` con `setColumnStretch` + `setColumnMinimumWidth`; o `QHBoxLayout` con stretch factors | declarar columnas, stretch y mínimos |
| `grid form\|panel` (Hub detalle) | `QGridLayout` 2 col, form `stretch 1`, panel `stretch 1`, `min-width` por col | patrón ya usado en `hub/pacientes_qt.py` |
| `overflow:auto` (scroll local) | `QScrollArea` + `stylesheet_scrollarea(modo)` (10px clínico) o `stylesheet_hidden_scrollbar` | no anidar scrolls salvo textarea editable |
| narrow `max-width:560` (onboarding/recuperar) | ventana 520×600; layout que **no** dependa de ancho fijo | el footer de CTAs es UX, puede caer bajo fold (delta aceptado) |
| `max-width:980; margin:0 auto` (`.window`) | **andamio** del mockup; en la app es la ventana real 960×600 | no replicar el "device window" |

### 5.2 Visual (sombra, radio, borde, gradiente, fondo, elevación)

| Web | Receta PyQt6 | Trampa a evitar |
|---|---|---|
| `box-shadow` 1 capa | `QGraphicsDropShadowEffect` via `v3_shadow(name, modo, parent)` / `shadow_effect(...)` | un effect por widget; setear en wrapper si hay clip |
| `box-shadow` multicapa (`--shadow-2/3`) | aproximar con la **capa dominante** (blur/offset/alpha mayor) | no apilar varios effects |
| `border-radius + box-shadow` juntos | **contenedor externo** para la sombra + **widget interno** con el radio (el effect no respeta el radio del mismo widget) | sombra cuadrada sobre card redonda |
| `border-radius` | QSS `border-radius:` en el widget; para pintura custom, `QPainterPath.addRoundedRect` | radios del mockup: xs8 sm12 md16 lg22 xl28 pill999 |
| `border:1px solid var(--line)` | QSS `border:1px solid <line>`; en `paintEvent` `QPen(qcolor("line",modo))` | usar el token, no hex suelto |
| `linear-gradient` | `qlineargradient` en QSS, o `QLinearGradient` en `paintEvent` | |
| `radial-gradient` (body, `.bigring`, blobs) | `QRadialGradient` en `paintEvent` (QSS no lo hace fino) | el fondo radial del shell ya existe |
| `conic-gradient` (`.ring` progreso) | `QConicalGradient` o arco con `QPainter.drawArc` + `QPen` grueso | rings ya implementados en `rings.py` |
| `opacity` | `QGraphicsOpacityEffect` (estático) o `QPropertyAnimation` sobre él (transición) | no `setWindowOpacity` en sub-widgets |
| `backdrop-filter:blur` (modal) | **no replicar**: scrim sólido `rgba(20,18,14,.5)` | delta documentado; blur real es caro |

### 5.3 Componentes — usar la primitiva, respetar el contrato

| Primitiva mockup (línea CSS aprox) | Widget existente | Archivo | Contrato/receta |
|---|---|---|---|
| `.btn` primary/ghost/soft (274) | `NMButton` | `components/buttons.py` | alto 42/34, pill, variantes `gradient/secondary/ghost/danger/soft`; press anima sin mutar geometry |
| `.input` / `textarea` (287) | `NMInput`/`NMTextArea`/`NMSearchInput` | `buttons.py` | radio 16, focus `0 0 0 3px brand-soft`; density bounds |
| `.tabs`/`.seg`/`.fchip` (295) | `NMTabs`/`NMSegmentedChoice` | `buttons.py` | pill: pad 5/gap 4/alto 30; activo `brand`/`brand-ink` |
| `.card`/`.card.hov` (257) | `NMCard` | `cards.py` | radio 22, `--shadow-1→2`; hover = solo `brand-line` (lift no capturable, ver §11) |
| `.badge` brand/accent/gold/rose (265) | `NMBadge`/`NMChip` | `surfaces.py` | pill, padding 4×11, tono `*-soft` + dot |
| `.empty` ico64 brand-soft (306) | `NMEmptyState` | `overlays.py` | ico 64 r18, título `.h-serif` 20, subtítulo multilínea |
| `.stepper` (235) | `NMStepper` | `feedback.py` | línea + fill brand; estados done/active |
| `input[type=range]` arcoíris (199) | slider mood | `mood.py` / `stylesheet_slider` | track gradiente 6 stops, thumb 22 borde 3px brand |
| `.rt-cb` check (222) | `NMCustomCheck` | `session.py` | 22, r7, on=brand, check animado |
| `.ring` conic (320) | `NMModuleRing` | `rings.py` | track + arco brand, label % |
| `.bigring`+`.core`+`.ctl` (207) | `NMFocusArc`/`_BreathCircle` | `rings.py`, `respiracion_qt.py` | 230/200, num 52, ctl 46 / main 58 |
| `.toast` (335) | `NMToast` | `overlays.py` | ink bg, pill, fade+slide, autodismiss ~2200ms |
| `.modal-bg`+`.modal` (343) | `NMDialog` | `dialogs.py` | scrim `rgba(20,18,14,.5)`, scale .96→1, sin blur |
| `.titlebar` (183) | `NMWindowChrome` | `chrome.py` | chrome bg, dots g/y/r, theme toggle (glifo sol/luna), back, crumb |
| `.prow`+`.avatar` (245) | `NMPatientRow*` | `patient.py` | avatar 40 r12, hover surface-2, sin clip |
| sparkline 78×30 / área 7-30d | `NMSparkline`/`NMAreaSparkline` | `patient.py` | `QPainter`; pyqtgraph solo si se justifica |
| `.dbt-card`/`.need-card` (228) | `_SkillCard`/`_NeedCard` | `dbt_qt.py` | bar 7×64 color familia, border-left need, pad 20 |

### 5.4 Animación

| Web | Receta PyQt6 | Regla |
|---|---|---|
| `transition` hover (color/border) | `QPropertyAnimation` sobre color/prop visual, o repintar en `enterEvent/leaveEvent` | duración `t-fast 140ms` |
| `transform:translateY(-3)` hover-lift | **no mutar geometry** si el widget está en layout; preferir `brand-line` + sombra | ver §11 (delta aceptado) |
| `:active` press (scale/translate) | propiedad visual animable; **nunca** cambiar `setGeometry`/rect permanente | lock: `test_button_press_animation_does_not_mutate_layout_geometry` |
| `fade` (opacity) | `QPropertyAnimation` sobre `QGraphicsOpacityEffect` | usado por `NMFadeWidget` |
| `slide` | `QPropertyAnimation` sobre `pos`/`geometry` de overlay (no de widget en layout) | toasts/overlays |
| progress / ring breathing | `QVariantAnimation` → `pyqtProperty(float)` → `update()` en `paintEvent` | ya implementado en rings |
| modal open/close | scale `.96→1` + fade vía effect | sin blur |
| theme switch | `ThemeManager.theme_changed` → regenerar QSS + `unpolish/polish` + `update()` | hot-reload ya existe |

Curvas/duración canónicas: `t-fast 140ms cubic(.4,0,.2,1)` · `t 240ms cubic(.32,.72,.24,1)`
· `t-slow 480ms cubic(.32,.72,.24,1)`.

### 5.5 Restricciones Qt — qué va por dónde

- **QSS:** colores/borde/radio/padding de widgets estándar, focus ring, hover simple,
  gradientes lineales simples. (generadores en `theme_qt.py`).
- **QPainter (`paintEvent`):** rings/arcos, sparklines/charts, gradientes radial/cónico,
  fondos del shell, checks animados, cualquier forma no expresable en QSS. Siempre
  `Antialiasing`.
- **QGraphicsDropShadowEffect:** sombras (1 capa, via `v3_shadow`). Wrapper si hay clip.
- **QPropertyAnimation/QVariantAnimation:** toda transición; sobre propiedad visual, no rect.
- **No replicar literal:** `backdrop-filter:blur`, sombras multicapa exactas, sub-pixel
  font, hover-lift por geometry. Usar la aproximación estable indicada.

### 5.6 Reglas anti-gigantismo / anti-clipping  *(OLA 0)*

1. Todo debe entrar en **960×600** (y 520×600 onboarding/recuperar) sin scroll forzado en
   pantallas que el mockup no scrollea.
2. **No aplicar padding 24 global a ciegas**: duplica márgenes y empuja CTAs fuera. Padding
   por contenedor, medido.
3. `setMinimumHeight`/`setFixedHeight` solo con razón; preferir `sizePolicy` + stretch.
4. Un control con texto debe tener su **rect completo dentro del clip efectivo acumulado**
   del árbol de parents y su **centro clickeable dentro del viewport**.
5. Densidad Hub = `NM_DENSITY["compact"]`; Suite = `comfortable`. No mezclar.

---

## 6. Sistema de diseño actual vs mockup

| Categoría | Estado |
|---|---|
| **Tokens existentes y correctos** | paleta claro/oscuro, radios (xs8..pill999), `V3_SPACE` (xs4 sm6 md10 lg14 xl16 2xl20 3xl24 4xl32), `V3_SHADOWS`, `V3_GRADIENTS`, `TYPOGRAPHY` (Fraunces display / Inter body), `MOOD_PALETTE`, tonos DBT (mind/toler/regul/efect) → **= mockup, lock-tested. No tocar.** |
| **Tokens antes mal consumidos** | hallazgos de serif-titles/card titles quedaron cerrados o aceptados al cierre E5; no reabrir DBT/recordatorios/rutina/timer sin defecto nuevo reproducible |
| **Primitivas ya corregidas** | `NMButton`, `NMTabs`, `NMBadge`, `NMCard`, `NMSearchInput`, `NMEmptyState`, `NMPatientRow`, theme-toggle (glifo sol/luna) |
| **Primitivas antes divergentes** | slider, `NMToast`, `NMDialog`, `NMStepper` y sparkline quedaron cubiertos por contratos/probes o aceptados bajo las recetas Qt estables de §12 |
| **Divergencias locales por pantalla** | sin divergencias accionables al cierre E5; cualquier delta nuevo requiere evidencia runtime/captura fresca |
| **Elementos del mockup que NO se replican** | nav-rail web, `.seg` Suite/Hub, `.chip-state`, `.window`/device-frame, `.stage`; CTAs/strings eliminados (§12) |
| **Decisiones owner** | confirmadas; sin pendientes operativos al cierre E5 (ver §12) |

Cobertura por categoría (paleta light/dark, tipografía, radios, sombras, espaciados,
tamaños de control, z-index visual, duración/curvas, iconografía, densidad, estados
hover/pressed/disabled/focus, tema en caliente): **cimientos completos**. No hay deuda viva
operativa al cierre E5; los marcadores de consumo/microfidelidad anteriores son historicos
o señales auxiliares, no backlog activo.

---

## 7. Tabla de mapeo pantalla real ↔ mockup

`Brecha`: A=estructura, B=densidad/clipping, C=microfidelidad. `Riesgo runtime`: alto si
toca viewport/clip.

### SUITE

| Pantalla real (clase / archivo) | Estados | Mockup | Brecha | Riesgo | Prio | Episodio |
|---|---|---|---|---|---|---|
| `HomeView` `app/home_qt.py` | score / no-score | `home` | B+C (serif title ok) | medio | P1 | E-S-HOME |
| `ModuloAnimo` `modules/animo_qt.py` | base | `animo` | B+C (grid .9/1.1, slider, chart 7/30) | medio | P2 | E-S-ANIMO |
| `ModuloRespiracion` `modules/respiracion_qt.py` | idle/running/paused/presets | `respiracion` | C (bigring idle fix hecho) | bajo | P2 | E-S-RESP |
| `ModuloTimer` `modules/timer_qt.py` | idle/running/paused/empty/presets | `timer` | B+C | medio | P2 | E-S-TIMER |
| `ModuloRegistroTCC` `modules/registro_tcc_qt.py` | s0/s1/s1otro/s2/s3/ok | `registro` | B+C (stepper, chips, tip gold) | medio | P3 | E-S-TCC |
| `ModuloActividades` `modules/actividades_qt.py` | default/filtered/marked/empty | `actividades` | B+C (fchips, serif title) | medio | P3 | E-S-ACT |
| `ModuloAvisos` `modules/avisos_qt.py` | all/active/today/search/empty | `avisos` | B+C | medio | P3 | E-S-AVISOS |
| `ModuloRutina` `modules/rutina_qt.py` | default/add/done/empty | `rutina` | B+C (ring 64/40, rt-cb) | medio | P3 | E-S-RUTINA |
| `ModuloDBT` `modules/dbt_qt.py` | now/library/STOP/closure (+Historial extra) | `dbtnow`/`dbtlib` | B+C (dbt-card pad20 hecho; serif) | medio | P3 | E-S-DBT |
| `run_onboarding` `app/onboarding_qt.py` | normal/error | `onboarding` | B+C (narrow 520; consent card legal real) | alto | P1 | E-S-ACCESO |
| recuperar acceso `app/onboarding_qt.py` | base | `recuperar` | C | medio | P1 | E-S-ACCESO |

### HUB

| Pantalla real | Estados | Mockup | Brecha | Riesgo | Prio | Episodio |
|---|---|---|---|---|---|---|
| `PacientesView` `hub/main_qt.py` | list / empty | `pacientes` | B+C (prow, sparkline, ring uso) | medio | P4 | E-H-PAC |
| `DetallePacienteView` `hub/pacientes_qt.py` | 4 tabs + Resumen IA modal | `detalle` | B+C (grid form\|panel; densidad/clip) | alto | P4 | E-H-DET |
| `TextosGlobalesSuiteView` / `ConfigGlobalSuiteView` `hub/config_global_texts.py` | search/filtro/dirty/empty | `textos` | B+C (densidad de filas) | medio | P4 | E-H-TEXTOS |
| Modales IA/PDF `hub/ia_asistente.py` / `hub/exportar.py` | resumen IA / exportar PDF | `modal` | C | bajo | P4 | E-H-MODALES |

> **DBT Historial** y **texto legal real** en onboarding son **deltas aprobados** (la app es
> más completa que el mockup): no se eliminan para "parecerse" al mockup.

---

## 8. Plan maestro por olas

Cada ola: objetivo · razón del orden · archivos candidatos · pantallas · riesgos ·
validación mínima · criterio de corte · entregable · handoff.

### OLA 0 — Integridad runtime  *(CERRADA — ver cierre E5)*
- **Objetivo:** cero bloqueos reales antes de fidelidad fina: clipping, off-viewport, centro
  no-clickeable, widget tapado por parent/layout, gigantismo >960×600, strings/CTAs
  prohibidos revividos, falsos negativos del probe.
- **Razón del orden:** una pantalla rota en runtime no se "embellece"; se arregla primero.
- **Archivos:** consumidores con overflow (`hub/config_global_texts.py`, `hub/main_qt.py`,
  `modules/dbt_qt.py`, `home_qt.py`) + primitivas de borde (`cards.py`, `buttons.py`,
  `patient.py`).
- **Validación:** `runtime_live_probe.py --all --theme both` (OK en las 22), tests de
  contrato, navegación real `QTest.mouseClick`, rect⊆clip efectivo, centro clickeable.
- **Corte:** probe sin `DEFECTS_FOUND` para las vistas del cluster; deuda residual listada.
- **Handoff:** ledger de defectos cerrados/abiertos por pantalla.

### OLA 1 — Primitivas compartidas seguras  *(mayormente CERRADA)*
- **Objetivo:** alinear componentes base con efecto sistémico sin tocar pantallas locales.
- **Cubre:** titlebar/chrome, botones, tabs/pills/fchips, inputs, empty states,
  overlays/toasts/modales, stepper, slider, checkbox, cards (si la primitiva es segura).
- **Estado:** botones/tabs/badge/card/search/empty/chrome ya contract-locked. **Resto real:**
  slider arcoíris, toast timing, modal scale, stepper estados, sparkline área.
- **Validación:** test de contrato por primitiva (extender `test_component_visual_contract.py`),
  ambos temas.
- **Corte:** contrato verde + no rompe consumidores (probe).
- **Handoff:** lista de primitivas restantes con su contrato objetivo.

### OLA 2 — Cards, densidad y layout compartido
- **Objetivo:** padding/proporción/radio/sombra/min-max-height/densidad correctos **sin
  romper 960×600**.
- **Advertencia:** no padding 24 global ciego (§5.6).
- **Validación:** probe + capturas antes/después + revisión humana de densidad.
- **Corte:** sin overflow nuevo; CTAs visibles/clickeables.

### OLA 3 — Suite por módulos
Clusters: (a) Home+Ánimo · (b) Respiración+Timer · (c) TCC · (d) DBT · (e)
Rutina+Actividades · (f) Avisos · (g) Onboarding/Recuperar.
- **Validación:** por cluster, probe + estados navegados + serif-titles + paridad tema +
  textos exactos ES (vía `t()`/`text_overrides`).

### OLA 4 — Hub
Clusters: (a) Pacientes · (b) Detalle (grid form|panel, 4 tabs) · (c) Textos globales/Config
global Suite · (d) Modales PDF/IA. Preservar seams Supabase/PDF/IA.

### OLA 5 — Fidelidad fina y QA visual
Microespaciado, contraste, iconos, animaciones, capturas finales, deuda residual, **revisión
humana lado-a-lado** de pantallas clave. SSIM solo como señal relativa (¿mejoró/empeoró?).

**Orden y dependencias:** OLA 0 → 1 → 2 habilitan 3/4 (Suite y Hub pueden ir en paralelo por
agentes distintos una vez estable la base). OLA 5 cierra.

---

## 9. Backlog ejecutable por episodios *(formato harness)*

Cada episodio se crea con
`agent_harness\scripts\start_episode.ps1 -Name "<id>" -Profile "nm_suite_safe_bugfix"`
(o `nm_suite_visual_qa` para read-only). **Un episodio = un cluster.** Plantilla:

```
ID · Nombre · Objetivo (1 línea verificable)
Perfil: nm_suite_safe_bugfix | nm_suite_visual_qa
Archivos permitidos: <lista explícita>
Archivos prohibidos: DB/sync/lógica clínica, build/dist/installers, todo lo no listado
Defectos que baja: <del ledger / probe>
Estado inicial esperado: <probe/captura antes>
Pasos: <traducción web→Qt usando §5; primitiva existente; sin reinventar>
Validación mínima: probe vista(s) light+dark · tests de contrato · ruff archivos tocados
Tests probables: tests/test_<x>_visual_contract.py (+pytest-qt interacción)
Evidencia: captura antes/después + sidecar probe + git diff --stat
Riesgos: <viewport/clip/legacy>
Criterio de corte: probe OK del cluster | STOP_RULES
Commit sugerido: "fix(ui): <cluster> <qué bajó>"  (git add explícito)
Handoff: defectos restantes + siguiente episodio
```

### Episodios concretos (semilla)

| ID | Objetivo | Archivos permitidos | Baja | Validación |
|---|---|---|---|---|
| **E0-PROBE-BASELINE** | Correr probe+contratos, escribir DEFECT_LEDGER inicial (read-only) | *(ninguno — audit)* | inventario | `runtime_live_probe --all`; `pytest tests/` |
| **E0-HUB-OVERFLOW** | Cerrar overflow/densidad residual Hub detalle/textos | `hub/config_global_texts.py`, `hub/main_qt.py`, `hub/pacientes_qt.py` | B | probe `hub/*` |
| **E0-SUITE-OVERFLOW** | Idem Suite (dbt/home/timer) | `app/home_qt.py`, `modules/dbt_qt.py`, `modules/timer_qt.py`, `shared/components/cards.py` | B | probe `suite/*` |
| **E1-SLIDER** | Slider arcoíris 6 stops + thumb 22 borde brand | `shared/components/mood.py`, `theme_qt.py` (`stylesheet_slider`) | C | contrato + ánimo |
| **E1-TOAST-MODAL** | `NMToast` slide/timing + `NMDialog` scale .96→1 | `shared/components/overlays.py`, `dialogs.py` | C | pytest-qt abrir/cerrar |
| **E1-STEPPER** | `NMStepper` estados done/active al mockup | `shared/components/feedback.py` | C | contrato TCC |
| **E2-SERIF-TITLES** | Títulos de card serif (Fraunces) en DBT/rutina/timer/avisos | `modules/dbt_qt.py`, `rutina_qt.py`, `timer_qt.py`, `avisos_qt.py` | C | captura + probe |
| **E3-S-HOME** … **E3-S-ACCESO** | Suite por cluster (§8 OLA3) | el módulo del cluster + primitiva si aplica | B+C | probe vista + estados |
| **E4-H-PAC** … **E4-H-MODALES** | Hub por cluster (§8 OLA4) | el archivo Hub del cluster | B+C | probe + seams intactos |
| **E5-FIDELITY** | Microfidelidad + capturas finales (read-only salvo ajustes puntuales) | por defecto | C | revisión humana |

> El backlog es **continuable**: si una sesión se corta, el siguiente agente abre el episodio
> con el último DEFECT_LEDGER y el handoff del episodio previo; no re-interpreta la estrategia.

---

## 10. Protocolo QA y evidencia  *(runtime-first; SSIM NO es gate)*

### 10.1 Runtime  *(gate primario)*
```
.venv\Scripts\python.exe qa\runtime_live_probe.py --all --theme both
```
Exige por vista (suite+hub, light+dark, 960×600): navegación real OK, **sin ventanas
fantasma**, **cierre limpio** (sin top-levels residuales), size 960×600, **sin hashes
duplicados** entre vistas. Para interacción/clip: pytest-qt con `QTest.mouseClick`, verificar
rect⊆clip efectivo acumulado y centro clickeable dentro del viewport. **Sin QA artifacts
commiteados** (`qa/_runtime_probe/`, `qa/_captures_v8/` son gitignored/efímeros).

### 10.2 Visual
```
.venv\Scripts\python.exe qa\capture_v8.py --view <id> --theme both --no-clean
.venv\Scripts\python.exe qa\diff_fidelity.py --actual-dir qa/_captures_v8 --view <id>
```
- Capturas por pantalla/tema/estado; **comparación lado-a-lado vs mockup** (triptych
  mockup|app|heat en `qa/_fidelity_*`).
- **SSIM/MAD = señal auxiliar relativa** (¿la estructura mejoró o empeoró?). **Nunca** gate:
  está saturado por render de fuente Qt-vs-Chromium (texto denso cae a ~0.6 sin ser defecto).
- **Revisión humana obligatoria** para pantallas clave (Home, Pacientes, Detalle, Acceso).
- OJO: `capture_v8.py --view X` **sin** `--no-clean` archiva el resto del set.

### 10.3 Tests
```
.venv\Scripts\python.exe -m pytest tests/      # ≈269; contratos + interacción
ruff check <archivos tocados>
```
- `test_*_visual_contract.py` (contratos de primitivas/pantallas) · `test_no_legacy_visuals.py`
  + `test_no_legacy_text_override_system.py` (anti-legacy) · pytest-qt (slider habilita
  Guardar, tabs/filtros, stepper, check habilita login, toast/modal, theme switch repinta).
- Pyright: no instalado en el venv → no es gate local (documentar si se agrega).

### 10.4 Cierre de episodio (obligatorio, `HARNESS_CONTRACT.md` regla 12)
`git status -sb` · `git diff --stat` · archivos tocados · defectos bajados · defectos
restantes · evidencia antes/después · commit sugerido (`git add` explícito) · handoff.
Cierre asistido: `agent_harness\scripts\close_episode.ps1` + `summarize_diff.ps1`.

---

## 11. Riesgos y fallbacks Qt

| Riesgo | Fallback estable | Estado |
|---|---|---|
| `box-shadow` multicapa | capa dominante en `QGraphicsDropShadowEffect` (`v3_shadow`) | mapeado |
| Sombra + radio en mismo widget | wrapper externo (sombra) + interno (radio) | receta §5.2 |
| `backdrop-filter:blur` modal | scrim sólido sin blur | delta documentado |
| `.card.hov` translateY(-3) | solo `brand-line` + sombra (no mutar geometry en layout) | **delta aceptado** (no capturable estático) |
| `transform`/transitions | `QPropertyAnimation`/`QVariantAnimation` sobre prop visual | regla §5.4 |
| radial/conic gradient | `QPainter` (`QRadialGradient`/`QConicalGradient`) | rings/shell ya lo hacen |
| Render de fuente sub-pixel | umbral de diff aceptado; **no perseguir SSIM** | regla §10.2 |
| HiDPI Windows (100%/125%) | `Antialiasing` en todo `paintEvent`; validar nitidez | presente |
| Onboarding 520×600 footer bajo fold | UX > pixel; footer visible aunque el target lo recorte | **delta aceptado** |
| Texto legal real vs resumen mockup | card estilo mockup + `LEGAL_DISCLAIMER_TEXT` completo | **decisión owner** |
| Segfault al destruir módulo con timers | cachear vistas en `QStackedWidget`, no destruir en transición | patrón Config global |

---

## 12. Decisiones confirmadas del owner

**Confirmadas (NO re-litigar):**
1. ADN = mockup (crema/bosque claro, tinta/menta oscuro, Inter+Fraunces). Hecho y lock-tested.
2. Consentimiento Acceso = card estilo mockup **con texto legal real completo** (no el
   resumen del mockup). Delta de contenido documentado.
3. Theme toggle del chrome = **glifo sol/luna** (`.tb-theme`), NO la píldora label+dot de la
   cáscara web.
4. **Conservar** DBT Historial y la estructura más completa de la app donde supera al mockup.
5. **NO replicar** la cáscara web (nav-rail, seg Suite/Hub, chip-state, device-window).
6. **NO revivir** strings/CTAs eliminados: "Registrar ánimo", "Registrar ahora", "Sin
   registro hoy", "Sin registros hoy", "Notas del día". (Guardas: `test_no_legacy_*`.)
7. Densidad: Suite `comfortable`, Hub `compact`.

**Sin pendientes operativos al cierre E5:**
- Slider, stepper, toast/modal, cards y estados principales quedaron lock-tested por contrato.
- Chart de ánimo y hover-lift quedan aceptados bajo las recetas Qt estables de §5/§11.
- Cualquier delta de contenido nuevo (texto/orden) que no esté en §12 vuelve a ser frontera
  de producto: saltar y reportar, no inventar.

---

## 13. Handoff final para agentes

**Para empezar (cualquier agente, sesión fría):**
1. `cd C:\Users\nosom\Desktop\nm_suite` · `git fetch origin` · `git status -sb` (debe estar
   limpio y al día). Python: `.\.venv\Scripts\python.exe`. Shell: PowerShell nativo.
2. Leer este doc §2 (estado), §5 (diccionario-ley), §9 (backlog), §10 (QA).
3. Correr baseline: `runtime_live_probe.py --all --theme both` + `pytest tests/`.
4. Elegir **un** episodio del backlog (§9) por su DEFECT_LEDGER. Abrirlo con
   `start_episode.ps1` + perfil. Respetar `HARNESS_CONTRACT.md` y `STOP_RULES.md`.

**Reglas no negociables:**
- Un episodio = un cluster. `git add` explícito, nunca `git add .`. No push sin permiso.
- No tocar DB/sync/lógica clínica/build/installers. No revivir UI eliminada.
- Traducir web→Qt **solo** con las recetas §5; usar la primitiva existente, no reinventar.
- **No filosofar** sobre SSIM/font-ceiling/stale/"fidelidad global": si el delta es real,
  arreglarlo; si no, callar. Un fix que no baja un contador del probe/contrato no es avance.
- Cerrar SIEMPRE con evidencia (§10.4). Sin diff + validación + antes/después = no hay éxito.

**Estado de avance (actualizado al cierre E5, 2026-06-21):**
- OLA 0 runtime: CERRADA (`runtime_live_probe.py --all --theme both` → OK=22,
  DEFECTS_FOUND=0, FAILED=0).
- OLA 1/2/3/4: CERRADAS por contratos y probes de clusters previos; E5 no detectó deuda
  visual accionable restante.
- OLA 5 fidelidad: CERRADA técnicamente (`capture_v8.py --all --theme both` → 98/98
  capturas, 0 failed; barrido visual de hojas de contacto sin clipping/blank/wrong-view/
  overlap accionable).
- `diff_fidelity.py` queda como señal auxiliar: 96 comparadas, 0 missing actuals, 0 partial
  evidence, 92 failures por umbrales SSIM/MAD no-gate ya documentados en §10.2.
- **Terminado operativo:** probe OK en las 22 vistas (light+dark) + suite de contratos verde
  + cero legacy + capturas finales completas + revisión visual técnica sin deuda accionable.

---
*Fin de `PLAN_MIGRACION_UI_V2.md`. Supera a `PLAN_MIGRACION_UI.md` (histórico).*
