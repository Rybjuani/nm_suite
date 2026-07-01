# Visual Component Catalog — NeuroMood (PyQt6)

Catálogo de los componentes `NM*`/`V3*` de `shared/components/*.py`, cada uno
anclado a su **selector/patrón canónico** y a sus **visual keys**. Es la vista
"por componente" del bridge (la vista "por selector" está en
`CSS_TO_PYQT_EQUIVALENCE_MATRIX.md`).

Para cada componente: archivo:línea · selector canónico (fuente) · spec corta ·
no-equivalencias (`MISMATCH#n` → `QT_HTML_KNOWN_MISMATCHES.md`) · keys.

> Reglas: 1) usar el componente existente antes de QSS local; 2) todo color/
> radio/sombra/fuente viene de `shared.theme` vía `shared.theme_qt`; 3) la
> consolidación de duplicados sigue `docs/PLAN_MODULARIZACION_COMPONENTES.md`.

---

## F1 · Tokens & accessors (no son widgets)

| Símbolo | Archivo:línea | Rol | Fuente |
|---|---|---|---|
| `V3_LIGHT` / `V3_DARK` | `shared/theme.py:13,139` | Paletas crudas por tema | `[data-theme]` L26-67 |
| `V3_RADIUS` / `LAYOUT` | `shared/theme.py:306,431` | Radios y geometría | `--r-*` L19 |
| `V3_SHADOWS` / `V3_LIFT` | `shared/theme.py:320,350` | Sombras (1 capa) + lift | `--shadow-*` L31-33 |
| `TYPOGRAPHY` | `shared/theme.py:363` | Escala tipográfica | `--font-*` L16-17 |
| `MOOD_PALETTE` | `shared/theme.py:276` | 10 niveles de ánimo | slider L202 |
| `C()`, `v3c()`, `colors()` | `shared/theme_qt.py:421,1803,438` | Lookup de color por key | tokens |
| `qfont()`, `v3_font()`, `nm_font()` | `shared/theme_qt.py:536,1966,620` | Fuentes | `.h-serif`/`.eyebrow` |
| `shadow_effect()`, `v3_shadow()`, `paint_card_lift()` | `shared/theme_qt.py:658,1858,1825` | Sombra/lift | `--shadow-*`, lift |
| `conical_arc_gradient()`, `radial_glow()`, `mood_gradient()` | `shared/theme_qt.py:901,859,2031` | Gradientes painter | conic/radial |
| `stylesheet_*()` | `shared/theme_qt.py:1011…1450` | QSS de inputs/tabs/scroll | inputs/tabs |
| `focus_ring_stylesheet()` | `shared/theme_qt.py:234` | Anillo de foco | `:focus` L304 |

## F2 · Typography

- **`NMSectionHeader`** — `components/icons.py:135`. Selector: `.h-serif`/eyebrow
  de sección (L276-277). Título serif + eyebrow. Keys: secciones (home, hub).
- **`_GradientTextLabel`** — `components/surfaces.py:1086`. Selector: texto con
  color/gradiente parcial (`.brand__name b` L106). MISMATCH#8. Keys: brand.
- **`NMElidedLabel`** — `components/data.py:10`. Selector: `text-overflow:ellipsis`
  (L141). MISMATCH#9. Keys: listas/filas.

## F3 · Surfaces / Cards

- **`NMCard`** — `components/cards.py:96`. Selector `.card`/`.card.pad`/`.card.hov`
  (L271-274). Surface + border `borderSoft`→`borderStrong` hover, radius 22,
  padding 20, sombra `_apply_card_shadow` (V3_SHADOWS), `glow` opcional, lift.
  MISMATCH#3 (sombra), #2 (hover). Keys: F3 (home, hub detalle, dbt).
- **`NMSectionCard`** — `components/cards.py:538`. Card con header de sección.
- **`NMCardSecondary`** — `components/cards.py:880`. Variante surface-2.
- **`NMFeaturedCard`** — `components/cards.py:1351`. Card destacada (CTA/feature).
- **`NMFormPanel`** — `components/cards.py:1216`. Panel contenedor de form (hub).
- **`NMPanel`** — `components/surfaces.py:495`. Panel genérico `.hub-panel` (L395).
- **`NMSettingsSection`** — `components/surfaces.py:381`. Sección de ajustes.
- **`NMStatCard` / `NMMetricCard`** — `components/cards.py:741,1107`. Tarjetas de
  métrica (home/hub). Keys: home, hub pacientes.
- **`NMChartPanel`** — `components/cards.py:925`. Panel con chart embebido (F9).

## F4 · Buttons

- **`NMButton`** — `components/buttons.py:124`. Selector `.btn`/`.btn--*`
  (L288-299). Pill, variantes `gradient`/`secondary`/`ghost`/`soft`/`danger`,
  tamaños sm/md/lg, press scale 0.97, hover ring interno. MISMATCH#10
  (hover glow), #2 (scale), opacity disabled 0.65 (DECISIÓN-OWNER). Keys: CTAs.
- **`NMButtonOutline`** — `components/buttons.py:498`. Botón con borde (ghost
  fuerte). Keys: acciones secundarias.
- **`NMIconButton`** — `components/navigation.py:72`. Botón solo-icono (`.back`,
  `.tb-theme`, `.prow-x`). Keys: chrome, filas.
- **`NMPlayButton`** — `components/inputs.py:125`. Selector `.ctl.main` (L220,
  círculo 58). ⚠ **D001**: medido 46×56 vs 58 canónico (ver memoria Plan
  migración V2). Keys: timer, respiracion.

## F5 · Inputs / Forms

- **`NMInput`** — `components/buttons.py:669`. Selector `.input` (L301-304) +
  `stylesheet_lineedit()`. Focus border `brandLine` + ring 3px pintado.
  MISMATCH#5. Keys: registro, hub, recuperar-acceso.
- **`NMTextArea`** — `components/buttons.py:1009`. Selector `textarea.input`
  (L305) + `stylesheet_textedit()`. `line-height` MISMATCH#12. Keys: registro s3.
- **`NMSearchInput`** — `components/buttons.py:841`. Selector `.nav__search input`
  (L116-123). Pill + icono. Keys: avisos-search.
- **`NMSelect`** — `components/inputs.py:27`. Combo + `stylesheet_combobox()`
  (chevron SVG, MISMATCH#13). Keys: hub forms.
- **`NMToggle`** — `components/inputs.py:43`. Selector `.themetoggle .dot`
  (L153-158, knob `::after`). MISMATCH#14. Keys: ajustes.
- **`NMFormRow`** — `components/surfaces.py:585`. Selector `.field-lbl`+input row
  (L306). Keys: forms.
- **`NMFormField`** — `components/session.py:643`. Campo de form con label/estado.
- **`NMSegmentedChoice`** — `components/buttons.py:797`. Selector `.seg` (L109).
  MISMATCH#7 (el `.seg` del mockup es chrome). Keys: — (uso runtime propio).

## F6 · Navigation / Tabs

- **`NMTabs`** — `components/buttons.py:1147`. Selector `.tabs`/`.hub-tabs`
  (L309-313,392) + `stylesheet_tabwidget_segmented()`. Pill, activo brand.
  Keys: hub detalle, dbt.
- **`NMSidebar` / `_SidebarItem`** — `components/navigation.py:335,156`. Selector
  `.nav`/`.nav__item` (L92-145). MISMATCH#7 (no es el `.nav` capturado), #14
  (barra activa). Keys: shells.
- **`NMHubSidebar`** — `components/surfaces.py:1127`. Sidebar del Hub.
- **`NMHeader`** — `components/navigation.py:573`. Header de pantalla
  (`.stage__top` análogo runtime). Keys: shells.
- **`NMModule`** — `components/navigation.py:1233`. Tarjeta/acceso de módulo.

## F7 · Chips / Badges / Pills

- **`NMBadge`** — `components/surfaces.py:234`. Selector `.badge`/`.badge.*`
  (L279-286). Tonos brand/accent/gold/rose. MISMATCH#11. Keys: avisos, listas.
- **`NMChip`** — `components/surfaces.py:134`. Selector `.fchip` (L315-318). Chip
  de filtro toggleable. Keys: actividades/avisos filtros.
- **`NMStatusChip`** — `components/status.py:119`. Chip de estado con dot.
- **`NMPhaseChip`** — `components/status.py:264`. Chip de fase (DBT/plan).
- **`NMCalmBadge`** — `components/status.py:338`. Badge "calm"/estado suave.
- **`NMPresetChip`** — `components/session.py:402`. Chip de preset (rutina).
- **`NMCategoryFilter`** — `components/session.py:1137`. Filtros de categoría
  (`CATEGORY_COLORS`). Keys: actividades.
- **`NMStreakBadge`** — `components/session.py:512`. Racha (home). Keys: home.

## F8 · Feedback / Steppers

- **`NMStepper`** — `components/feedback.py:855`. Selector `.stepper` (L237-244).
  Línea + fill + nodos. Keys: registro pasos.
- **`NMTCCStepper`** — `components/session.py:676`. Stepper específico TCC.
- **`NMInstallStepper`** — `components/onboarding.py:28`. Pasos de instalación.
  Keys: onboarding.
- **`NMProgressBar` / `NMProgressLine`** — `components/feedback.py:102,168`.
  Progreso. Keys: hub plan.
- **`NMSkeleton`** — `components/feedback.py:55`. Placeholder de carga.
- **`NMToast`** — `components/feedback.py:410`. Selector `.toast` (L349-354).
  `position:fixed`→overlay. Keys: — (transitorio).
- **`NMTypingDots`** — `components/feedback.py:318`. Dots "escribiendo" (IA).
- **`NMStatusDot` / `NMStatusBanner`** — `components/status.py:68,174`. Selector
  `.dots`/`.pstatus` (L343,381) y banner. Keys: home, onboarding-error.

## F9 · Rings / Charts

- **`NMFocusArc`** — `components/rings.py:120`. Selector `ringSVG`/`.bigring`
  (L209-216,532). Arco de progreso pintado. Keys: timer, respiracion, home.
- **`NMCycleRing` / `NMModuleRing`** — `components/rings.py:354,399`. Selector
  `.ring` conic (L335). MISMATCH#15. Keys: home rings.
- **`NMRingPulse`** — `components/feedback.py:214`. Pulso del anillo grande.
  Keys: respiracion-running/paused.
- **`NMWaveChart`** — `components/feedback.py:624`. Gráfico de onda.
- **`NMHeatBar`** — `components/feedback.py:962`. Selector `.dbt-card .bar` (L231)
  / heatmap TCC. Keys: dbt, registro.
- **`NMSparkline` / `NMAreaSparkline`** — `components/patient.py:200,293`.
  Sparklines de tendencia. Keys: hub pacientes.

## F10 · Lists / Rows

- **`NMListRow`** — `components/surfaces.py:816`. Selector `.need-card`/filas
  genéricas (L234). Keys: dbt now, listas.
- **`NMRow`** — `components/surfaces.py:965`. Fila genérica.
- **`NMPatientRow` / `NMPatientRowPremium`** — `components/patient.py:83,434`.
  Selector `.prow` (L247). Hover `row_hover_stylesheet()`. Keys: hub pacientes.
- **`NMRoutineSection`** — `components/session.py:777`. Selector `.rt-row`
  (L227). Sección de rutina con filas+check. Keys: rutina.
- **`NMCustomCheck` / `_NMAnimCheckBox`** — `components/session.py:208,82`.
  Selector `.rt-cb` (L224, check 22 r7). MISMATCH#14. Keys: rutina, actividades.
- **`NMActivityCard`** — `components/session.py:292`. Tarjeta de actividad.
  Keys: actividades.

## F11 · Empty / Error states

- **`NMEmptyState`** — `components/overlays.py:123`. Selector `.empty` (L320-326).
  Col centrada + ico + serif h3 + p. Keys: `*-empty` (12 keys).
- **`_NMEmptyStateChip` / `_NMSuccessIconChip`** — `components/overlays.py:65,95`.
  Selector `.empty .ico` (L322). Keys: empties, registro-success.
- **`NMErrorState`** — `components/overlays.py:327`. Estado de error. Keys:
  onboarding-error.

## F12 · Modal / Dialog / Overlay

- **`NMDialog`** — `components/dialogs.py:59`. Selector `.modal-bg`/`.modal`
  (L357-363). Blur/dim/backdrop + surface r-xl + scale-in. MISMATCH#17, #2.
  Keys: hub resumen-ia. Cierre modal requiere `window_overlay`, no `panel_crop`,
  y `tools/qa/audit_modal_backdrop_blur.py`.
- **`NMDialogScaffold`** — `components/dialogs.py:338`. Selector
  `.modal.dbt-practice` (L364). Modal de práctica DBT (560×auto). Keys:
  dbt-practice-stop.
- **`NMTooltip`** — `components/overlays.py:238`. Tooltip overlay. Keys: —.

## F13 · Chrome / Window

- **`NMWindowChrome`** — `components/chrome.py:195`. Selector `.window`/`.titlebar`
  (L175-191). Titlebar + frame. MISMATCH#18. Keys: todas.
- **`_ChromeWinBtn`** — `components/chrome.py:74`. Selector `.tb-dots .tb-dot`
  (L193-196). Hex literales MISMATCH#19. Keys: chrome.
- **`_ChromeThemeToggle`** — `components/chrome.py:130`. Selector `.tb-theme`
  (L197). Keys: chrome.
- **`_ChromeLogoMark`** — `components/navigation.py:1346`. Selector `.brandmark`
  (L99). Keys: brand.
- **`aplicar_captionbar_qt()`** — `shared/theme_qt.py:1559`. Caption bar nativa.

## F14 · Avatar / Brand / Icons

- **`NMAvatar`** — `components/icons.py:227`. Selector `.avatar` (L249, 40 r12
  grad). Keys: hub pacientes.
- **`NMIcon`** — `components/icons.py:41`. Selector icon set `I`/`svg()`
  (L483-505). `nm_icon()`, `icon_stroke_width()`. Keys: todas.
- **`_LogoLabel`** — `components/navigation.py:1089`. Selector `.brand__name`
  (L105). Keys: brand.

## F15 · Mood system

- **`NMMoodSlider` / `V3MoodSlider`** — `components/mood.py:267,651`. Selector
  `input[type=range]` (L201-206). Track 6-stop + thumb pintados. MISMATCH#4.
  Keys: animo.
- **`NMMoodEmoji` / `NMEmojiPicker`** — `components/mood.py:67,141`. Emoji de
  ánimo + picker. Keys: animo, registro emoción.
- **`NMMoodContextHeader`** — `components/session.py:1074`. Header con contexto
  de ánimo. Keys: registro.

---

## Componentes de dominio (no estrictamente visuales primitivos)

Existen además componentes compuestos de dominio que reusan los primitivos
anteriores: `NMWelcomeBar` (home), `NMSessionHistory`, `NMDayNote`,
`NMAIPanel`/`NMChatBubble`/`NMAIDisclaimer`/`NMProviderChip`/`NMQuickAction`
(IA), `NMPatientContext`, `NMAvisoCard` (avisos), `NMSyncOrb`,
`NMDataPreserveCard` (onboarding). Al tocarlos, respetar los primitivos del
bridge en lugar de re-estilar localmente.
