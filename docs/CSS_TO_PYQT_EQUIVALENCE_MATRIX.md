# CSS → PyQt6 Equivalence Matrix

Matriz de traducción **selector/patrón CSS canónico → equivalente PyQt6**.
Fuente CSS: `qa/pack canonico/neuromood-mockup_reparado.html` (los `Lnnn` son
líneas de ese archivo). Tokens: `shared/theme.py`. Helpers: `shared/theme_qt.py`.

Convenciones de columnas:

- **Selector / patrón** — clase o regla CSS canónica.
- **Fuente** — línea(s) del HTML canónico.
- **PyQt actual / propuesto** — token/helper/widget que ya lo implementa
  (*actual*) o el que debería usarse (*propuesto* — marcado con ⟂).
- **No-equiv** — `→ MISMATCH#n` apunta a `QT_HTML_KNOWN_MISMATCHES.md`.
- **Archivos** — dónde vive la implementación Qt.
- **Tests/probes** — cómo verificar.
- **Keys** — visual keys afectadas (familias o ejemplos).

> Regla: si una fila no tiene **Fuente** canónica, no es una equivalencia válida
> y no puede usarse para cerrar un check (ver `BRIDGE_USAGE_FOR_AGENTS.md`).

---

## F1 · Tokens

| Selector / patrón | Fuente | PyQt actual / propuesto | No-equiv | Archivos | Tests/probes | Keys |
|---|---|---|---|---|---|---|
| `:root --font-display/--font-body` | L16-17 | `TYPOGRAPHY["font_serif"]`, `["font_family"]`; `_serif_family()`, `_font_family()` | fuentes Fraunces/Inter deben estar embebidas → MISMATCH#1 | `shared/theme.py:363`, `shared/theme_qt.py:343` | `runtime_live_probe` | todas |
| `--r-xs..--r-pill` (8/12/16/22/28/999) | L19 | `V3_RADIUS`, `LAYOUT["radius_*"]` | — | `shared/theme.py:306` | `vas_introspect --introspect` (RADIUS) | todas |
| `--t-fast/--t/--t-slow` (cubic-bezier) | L20-22 | `TRANSITIONS`; `QEasingCurve` en animaciones | cubic-bezier exacto ≈ `QEasingCurve` → MISMATCH#2 | `shared/theme.py:703` | n/a (animación) | interacción |
| `[data-theme=light]` paleta | L26-45 | `V3_LIGHT` + `_bridge_light()` → `COLORS["light"]` | — | `shared/theme.py:13,597` | `C("brand","light")` | `*@light` |
| `[data-theme=dark]` paleta | L48-67 | `V3_DARK` + `_bridge_dark()` → `COLORS["dark"]` | — | `shared/theme.py:139,543` | `C("brand","dark")` | `*@dark` |
| `--shadow-1/2/3` (multi-capa) | L31-33,53-55 | `V3_SHADOWS[modo][sm/md/card/lg]`; `shadow_effect()`, `v3_shadow()`, `shadow_1/2/3()` | box-shadow multi-capa → **una sola** `QGraphicsDropShadowEffect` → MISMATCH#3 | `shared/theme.py:320`, `shared/theme_qt.py:658,1858` | `vas_introspect --introspect` (SHADOW) | todas |
| `body { background: radial-gradient(...) }` | L71-80 | `radial_glow()`, `radial_glow_double()`; pintado en main window | QSS no soporta `radial-gradient` → painter `QRadialGradient` → MISMATCH#4 | `shared/theme_qt.py:859,883` | panel side-by-side | fondos |
| `--focus` + `:focus-visible{outline+offset}` | L43,65,84 | `focus_ring_stylesheet()`; ring pintado en `NMCard`/`NMButton` | `outline-offset` y `:focus-visible` no existen en QSS → MISMATCH#5 | `shared/theme_qt.py:234` | foco manual | forms |

## F2 · Typography

| Selector / patrón | Fuente | PyQt actual / propuesto | No-equiv | Archivos | Tests/probes | Keys |
|---|---|---|---|---|---|---|
| `.h-serif` (Fraunces 600, -.015em) | L277 | `v3_font(size, serif=True, weight=600)`; `NMSectionHeader` | `letter-spacing` em → `QFont.setLetterSpacing(PercentageSpacing)` → MISMATCH#6 | `shared/theme_qt.py:1966`, `components/icons.py:135` | side-by-side | home, registro, empty |
| `.eyebrow` (11px/700/.14em/upper) | L276 | `qfont("size_eyebrow", weight=700)` + `QFont.Capitalization.AllUppercase` | tracking em → PercentageSpacing → MISMATCH#6 | `shared/theme.py:398`, `theme_qt.py:536` | side-by-side | secciones |
| `.stage__title` / títulos serif | L166 | `v3_font(..., serif=True)` (nota: `.stage*` es chrome del mockup, no runtime) | `.stage` no se captura → MISMATCH#7 | `components/icons.py` | n/a | — |
| `.brand__name b{color:var(--brand)}` (texto bicolor) | L106 | `_GradientTextLabel` (texto con gradiente/tinte pintado) | color parcial de texto en QSS limitado → painter → MISMATCH#8 | `components/surfaces.py:1086` | side-by-side | brand |
| ellipsis `text-overflow:ellipsis` | L141,L817 | `NMElidedLabel` (`QFontMetrics.elidedText`) | no hay `text-overflow` en QSS → MISMATCH#9 | `components/data.py:10` | side-by-side | listas |

## F3 · Surfaces / Cards

| Selector / patrón | Fuente | PyQt actual / propuesto | No-equiv | Archivos | Tests/probes | Keys |
|---|---|---|---|---|---|---|
| `.card` (surface, border 1px line, r-lg, shadow-1) | L271-272 | `NMCard` (border `borderSoft`→`borderStrong` hover, radius 22, `_apply_card_shadow`) | — | `components/cards.py:96` | `test_component_visual_contract.py`; `vas_introspect` | F3 keys |
| `.card.pad{padding:20px}` | L273 | `NMCard._sync_layout_padding` → `_NM_CARD_PADDED_MARGINS` (20) | margin de layout, no `padding` QSS | `components/cards.py:181` | introspect bbox | home, detalle |
| `.card.hov:hover{translateY(-3px)+shadow-2+brand-line}` | L274 | `NMCard` hover (lift anim + shadow swap) | `transform:translateY` → `QPropertyAnimation`/offset → MISMATCH#2 | `components/cards.py` | hover manual | cards clickeables |
| "lift" highlight superior interno | (dirección owner) | `paint_card_lift()` + `V3_LIFT` | gradiente blanco interno no es box-shadow → painter | `shared/theme.py:350`, `theme_qt.py:1825` | side-by-side | cards light |
| `.screen-frame{radial-gradient}` | L251-265 | painter `QRadialGradient` en contenedor de pantalla | radial-gradient → MISMATCH#4 | runtime shells | panel | todas |
| section card / panel / featured | L271 (variantes) | `NMSectionCard`, `NMPanel`, `NMCardSecondary`, `NMFeaturedCard`, `NMFormPanel` | — | `components/cards.py:538,880,1351,1216`, `surfaces.py:495` | introspect | hub detalle, dbt |

## F4 · Buttons

| Selector / patrón | Fuente | PyQt actual / propuesto | No-equiv | Archivos | Tests/probes | Keys |
|---|---|---|---|---|---|---|
| `.btn` (pill, 11x20, 13.5/600) | L288-291 | `NMButton` (pill `LAYOUT["radius_button"]`, `qfont`) | — | `components/buttons.py:124` | contract test | botones |
| `.btn--primary{brand + shadow-1; hover brand-strong}` | L293-294 | `NMButton variant="gradient"` (fill `v3c("primary")`, hover ring) | hover glow ≈ ring interno (no outer glow) → MISMATCH#10 | `components/buttons.py:232` | side-by-side | CTAs |
| `.btn--ghost{surface+line; hover brand-line}` | L295-296 | `NMButton variant="secondary"`/`ghost` | — | `components/buttons.py:251` | side-by-side | acciones sec. |
| `.btn--soft{brand-soft}` | L297-298 | `NMButton variant="soft"` | rgba soft → `*SoftSolid` en QSS → MISMATCH#11 | `components/buttons.py` | side-by-side | chips-acción |
| `.btn:disabled{opacity:.5}` | L299 | `NMButton` `_disabled_opacity=0.65` (ajuste owner) | opacity disabled difiere por decisión owner | `components/buttons.py:230` | side-by-side | animo |
| `.btn:active{scale(.99)}` | L292 | press scale 0.97 (`QPropertyAnimation`) | transform scale → anim → MISMATCH#2 | `components/buttons.py` | n/a | interacción |
| `.ctl` / `.ctl.main` (botón circular 46/58) | L217-221 | `NMPlayButton`, `NMIconButton` | ⚠ ver D001 (NMPlayButton 46×56 vs 58) | `components/inputs.py:125`, `navigation.py:72` | `--key suite:timer-running@*` | timer, respiracion |
| `.titlebar .back` / `.tb-theme` (icon btn) | L187,197 | `_ChromeWinBtn`, `_ChromeThemeToggle`, `NMIconButton` | — | `components/chrome.py:74,130` | side-by-side | chrome |

## F5 · Inputs / Forms

| Selector / patrón | Fuente | PyQt actual / propuesto | No-equiv | Archivos | Tests/probes | Keys |
|---|---|---|---|---|---|---|
| `.input` (surface-2, line, r-md, 12x14) | L301-302 | `NMInput` + `stylesheet_lineedit()` | — | `components/buttons.py:669`, `theme_qt.py:1231` | `--key suite:registro*` | registro, hub |
| `.input:focus{brand-line + box-shadow 0 0 0 3px brand-soft}` | L304 | `NMInput` focus border `brandLine`; ring 3px **pintado** | `box-shadow` ring de input → no QSS, painter/efecto → MISMATCH#5 | `components/buttons.py`, `theme_qt.py:1250` | foco manual | recuperar-acceso |
| `textarea.input{resize:none; line-height:1.55}` | L305 | `NMTextArea` + `stylesheet_textedit()` | `line-height` → `QTextBlockFormat.setLineHeight` → MISMATCH#12 | `components/buttons.py:1009`, `theme_qt.py:1257` | side-by-side | registro s3 |
| `.field-lbl` (12.5/600 + span ink-3) | L306-307 | `NMFormRow`, `NMFormField` label | — | `components/surfaces.py:585`, `session.py:643` | side-by-side | forms |
| `.nav__search input` (pill, icono abs left) | L116-123 | `NMSearchInput` (icono + pill) | icono posicionado abs → layout + paint | `components/buttons.py:841` | `--key suite:avisos-search@*` | avisos-search |
| `input[type=range]` (mood gradient track + thumb) | L201-206 | `NMMoodSlider`, `V3MoodSlider`, `stylesheet_slider()` | thumb/track multi-stop → painter; ver F15 | `components/mood.py:267,651`, `theme_qt.py:1138` | `--key suite:animo@*` | animo, registro s1 |
| select / combo | (forms) | `NMSelect` + `stylesheet_combobox()` (chevron SVG) | chevron por borde renderiza cuadrado en Qt6 → SVG url → MISMATCH#13 | `components/inputs.py:27`, `theme_qt.py:1308` | side-by-side | hub forms |

## F6 · Navigation / Tabs

| Selector / patrón | Fuente | PyQt actual / propuesto | No-equiv | Archivos | Tests/probes | Keys |
|---|---|---|---|---|---|---|
| `.tabs` (pill container, brand activo) | L309-313 | `NMTabs` + `stylesheet_tabwidget_segmented()` | `aria-selected` → estado Qt | `components/buttons.py:1147`, `theme_qt.py:1185` | `--key hub:detalle@*` | hub detalle, dbt |
| `.seg` (segmented producto) | L109-114 | `NMSegmentedChoice` | `.seg` vive en `.nav` (chrome mockup), no runtime → MISMATCH#7 | `components/buttons.py:797` | n/a | — |
| `.hub-tabs button{12px/8x12}` | L392 | `NMTabs` size compact (hub density) | densidad hub vs suite → `VISUAL_DENSITIES` | `components/buttons.py`, `theme.py:470` | `--key hub:detalle*` | hub detalle |
| `.nav` / `.nav__item` / `.nav__group` | L92-145 | `NMSidebar`, `_SidebarItem`, `NMHubSidebar`, `NMHeader`, `NMModule` | el `.nav` del mockup es su navegador propio (no se captura); el sidebar runtime es interno a la ventana → MISMATCH#7 | `components/navigation.py:335,156,573,1233`, `surfaces.py:1127` | n/a | shells |
| `.nav__item.is-active::before` (barra 3px) | L138-139 | barra activa pintada / widget | `::before` con content → painter o sub-widget → MISMATCH#14 | `components/navigation.py` | side-by-side | sidebar |

## F7 · Chips / Badges / Pills

| Selector / patrón | Fuente | PyQt actual / propuesto | No-equiv | Archivos | Tests/probes | Keys |
|---|---|---|---|---|---|---|
| `.badge` (pill 4x11, surface-3) | L279-280 | `NMBadge` | — | `components/surfaces.py:234` | side-by-side | listas, avisos |
| `.badge.brand/accent/gold/rose` | L281-286 | `NMBadge` tono + `NMStatusChip`, `NMPhaseChip`, `NMCalmBadge` | rgba soft → `*SoftSolid` en QSS → MISMATCH#11 | `components/surfaces.py:234`, `status.py:119,264,338` | side-by-side | avisos, dbt |
| `[data-theme=dark] .badge.brand{color:mind}` | L286 | tono dark mapeado en tokens (`mind`) | — | `shared/theme.py` | `--key *@dark` | dark |
| `.fchip` (filtro, brand activo) | L315-318 | `NMChip`, `NMCategoryFilter`, `NMPresetChip` | `aria-pressed` → estado Qt | `components/surfaces.py:134`, `session.py:1137,402` | `--key suite:actividades-filtered@*` | actividades, avisos filtros |
| `.tag` / `.nav__item .tag` (mini badge) | L142-145 | badge pequeño / `NMBadge` size sm | rgba(255,255,255,.4) sobre activo → MISMATCH#11 | `components/surfaces.py` | side-by-side | sidebar |
| streak badge | (home) | `NMStreakBadge` | — | `components/session.py:512` | `--key suite:home@*` | home |

## F8 · Feedback / Steppers

| Selector / patrón | Fuente | PyQt actual / propuesto | No-equiv | Archivos | Tests/probes | Keys |
|---|---|---|---|---|---|---|
| `.toast` (fixed bottom, pill, ink/surface) | L349-354 | `NMToast` | `position:fixed` → overlay Qt; `transform:translateX(-50%)` → centrado manual | `components/feedback.py:410` | n/a (transitorio) | — |
| `.stepper` (línea + fill + nodos) | L237-244 | `NMStepper`, `NMTCCStepper` | línea con `::` y fill width → painter | `components/feedback.py:855`, `session.py:676` | `--key suite:registro-step*@*` | registro pasos |
| install stepper | (onboarding) | `NMInstallStepper` | — | `components/onboarding.py:28` | `--key suite:onboarding@*` | onboarding |
| `.dots` / `.dots i.on/.miss` | L343-346 | `NMStatusDot` + dots pintados | — | `components/status.py:68` | side-by-side | home racha |
| progress bar / line | (varios) | `NMProgressBar`, `NMProgressLine` | — | `components/feedback.py:102,168` | side-by-side | hub plan |
| skeleton / typing dots | (loading) | `NMSkeleton`, `NMTypingDots` | animación → `QPropertyAnimation` | `components/feedback.py:55,318` | n/a | ia |
| status banner | (estado) | `NMStatusBanner` | — | `components/status.py:174` | side-by-side | onboarding-error |

## F9 · Rings / Charts

| Selector / patrón | Fuente | PyQt actual / propuesto | No-equiv | Archivos | Tests/probes | Keys |
|---|---|---|---|---|---|---|
| `.ring{conic-gradient(brand calc(p%), track)}` | L335-341 | `conical_arc_gradient()`, `NMModuleRing`, `NMCycleRing` | QSS no soporta `conic-gradient` → `QConicalGradient` painter → MISMATCH#15 | `shared/theme_qt.py:901`, `components/rings.py:354,399` | `vas_introspect` (GRADIENT) | home rings |
| `.bigring` + `.core` (radial bg, num serif 52) | L209-216 | `NMFocusArc`, `NMRingPulse` (anillo grande + core) | radial-gradient → painter → MISMATCH#4 | `components/rings.py:120`, `feedback.py:214` | `--key suite:respiracion*@*`, `timer*` | respiracion, timer |
| `ringSVG(pct)` (svg progress) | L532-541 | `NMFocusArc` / arco pintado con `stroke-dashoffset`→ arco Qt | dash animation → painter | `components/rings.py:120` | side-by-side | timer, home |
| `.dbt-card .bar` (barra 7px tono skill) | L231 | barra pintada / `NMHeatBar` | gradiente tono → fill | `components/feedback.py:962`, `cards.py` | `--key suite:dbt-library@*` | dbt |
| wave / sparkline / chart panel | (hub, animo) | `NMWaveChart`, `NMSparkline`, `NMAreaSparkline`, `NMChartPanel` | charts pintados (no canvas web) | `components/feedback.py:624`, `patient.py:200,293`, `cards.py:925` | `--key hub:pacientes@*` | hub, animo |

## F10 · Lists / Rows

| Selector / patrón | Fuente | PyQt actual / propuesto | No-equiv | Archivos | Tests/probes | Keys |
|---|---|---|---|---|---|---|
| `.prow` / `.avatar` (fila paciente + avatar) | L247-249 | `NMPatientRow`, `NMPatientRowPremium`, `NMAvatar` | hover row → `row_hover_stylesheet()` | `components/patient.py:83,434`, `icons.py:227` | `--key hub:pacientes@*` | hub pacientes |
| `.phead` / `.plist` / `.pstatus` | L377-389 | header de columnas + `NMStatusDot`; `pcol-*` widths | `@container` width hide → MISMATCH#16 | `components/patient.py`, `status.py:68` | `--key hub:pacientes@*` | hub pacientes |
| `.rt-row` / `.rt-cb` (checkbox rutina 22, r7) | L224-227 | `NMRoutineSection`, `NMCustomCheck`, `_NMAnimCheckBox` | check animado → painter | `components/session.py:777,208,82` | `--key suite:rutina*@*` | rutina, actividades |
| `.tg-row` / `.tg-list` (texto global editable) | L400-414 | `NMFormRow`/`NMListRow` + `NMInput` (dirty state) | `.tg-row.dirty{box-shadow ring}` → painter/border | `components/surfaces.py:585,816` | `--key hub:textos-globales@*` | hub textos |
| `.need-card{border-left 3px}` | L234 | `NMListRow`/`NMCard` con borde acento | border-left acento → `NMCard` border o paint | `components/surfaces.py:816` | side-by-side | dbt now |

## F11 · Empty / Error states

| Selector / patrón | Fuente | PyQt actual / propuesto | No-equiv | Archivos | Tests/probes | Keys |
|---|---|---|---|---|---|---|
| `.empty` (col centrada, 50x24) | L320-321 | `NMEmptyState` | centrado vertical → layout stretch | `components/overlays.py:123` | `--key *-empty@*` | *-empty (12 keys) |
| `.empty .ico` (64×64 r18 brand-soft) | L322-324 | `_NMEmptyStateChip`, `_NMSuccessIconChip` | rgba soft → solid | `components/overlays.py:65,95` | side-by-side | empties |
| `.empty h3/p` (serif + ink-2) | L325-326 | labels `v3_font` dentro de `NMEmptyState` | — | `components/overlays.py` | side-by-side | empties |
| error state | (onboarding-error) | `NMErrorState`, `NMStatusBanner` | — | `components/overlays.py:327`, `status.py:174` | `--key suite:onboarding-error@*` | onboarding-error |

## F12 · Modal / Dialog / Overlay

| Selector / patrón | Fuente | PyQt actual / propuesto | No-equiv | Archivos | Tests/probes | Keys |
|---|---|---|---|---|---|---|
| `.modal-bg{rgba dim + backdrop-filter:blur(3px)}` | L357-358 | `NMDialog` backdrop (dim) | `backdrop-filter:blur` no existe en Qt → dim sin blur o `QGraphicsBlurEffect` → MISMATCH#17 | `components/dialogs.py:59` | `--key suite:dbt-practice-stop@*` | dbt practice, ia modal |
| `.modal` (surface, r-xl, shadow-3, scale-in) | L360-363 | `NMDialog`, `NMDialogScaffold` | `transform:scale(.96)` enter → anim | `components/dialogs.py:59,338` | side-by-side | modales |
| `.modal.dbt-practice{560×auto min356 r28}` | L364 | `NMDialogScaffold` práctica DBT | tamaño fijo modal | `components/dialogs.py:338` | `--key suite:dbt-practice-stop@*` | dbt practice |
| resumen IA (modal 560×220) | (csv) | `NMDialog` / panel IA | surface `modal` 560×220 | `hub/ia_asistente.py` | `--key hub:detalle-resumen-ia-0@*` | hub resumen ia |
| tooltip | (hover) | `NMTooltip` | `position:fixed` → overlay | `components/overlays.py:238` | n/a | — |

## F13 · Chrome / Window

| Selector / patrón | Fuente | PyQt actual / propuesto | No-equiv | Archivos | Tests/probes | Keys |
|---|---|---|---|---|---|---|
| `.window{960×600 surface r-xl shadow-3 overflow:hidden}` | L175-181 | ventana runtime + `NMWindowChrome` (la key captura `.window`) | `border-radius` de top-level window con sombra → frameless + `aplicar_captionbar_qt` → MISMATCH#18 | `components/chrome.py:195`, `theme_qt.py:1559` | todas las keys | todas |
| `.window.narrow{520×600}` | L182 | ventana narrow (onboarding/recuperar) | tamaño fijo | `app/onboarding_qt.py` | `--key suite:onboarding@*` | onboarding, recuperar |
| `.titlebar{chrome bg, 11x16}` | L185-191 | `NMWindowChrome` titlebar | — | `components/chrome.py:195` | side-by-side | todas |
| `.tb-dots .tb-dot.r/.y/.g` (semáforo) | L193-196 | `_ChromeWinBtn` (dots/botones ventana) | colores `#E0695A/#E0B23E/#56B27A` literales (no token) → MISMATCH#19 | `components/chrome.py:74` | side-by-side | chrome (recuperar) |
| `.tb-theme` toggle | L197 | `_ChromeThemeToggle` | — | `components/chrome.py:130` | side-by-side | chrome |

## F14 · Avatar / Brand / Icons

| Selector / patrón | Fuente | PyQt actual / propuesto | No-equiv | Archivos | Tests/probes | Keys |
|---|---|---|---|---|---|---|
| `.avatar{40×40 r12 grad}` | L249 | `NMAvatar` | gradiente avatar → fill painter | `components/icons.py:227` | `--key hub:pacientes@*` | hub pacientes |
| `.brandmark{34×34 r10 grad brand→accent}` | L99-104 | `_LogoLabel`, `_ChromeLogoMark` | gradiente diagonal → painter | `components/navigation.py:1089,1346` | side-by-side | brand |
| icon set `I` + `svg(p,w)` (stroke 1.8) | L483-505 | `NMIcon` + `nm_icon()` + `icon_stroke_width()` | SVG stroke recolor → `icons_svg.py` | `components/icons.py:41`, `theme_qt.py:267`, `shared/icons_svg.py` | side-by-side | todas |
| `.nav__item .ic{17×17 opacity .85}` | L140 | `NMIcon` tamaño 17 | — | `components/icons.py:41` | n/a | sidebar |

## F15 · Mood system

| Selector / patrón | Fuente | PyQt actual / propuesto | No-equiv | Archivos | Tests/probes | Keys |
|---|---|---|---|---|---|---|
| `input[type=range]` track (6-stop mood gradient) | L201-202 | `NMMoodSlider`, `V3MoodSlider` track pintado; `mood_gradient()` | gradiente lineal multi-stop en track → painter (no QSS) → MISMATCH#4 | `components/mood.py:267,651`, `theme_qt.py:2031` | `--key suite:animo@*` | animo |
| `::-webkit-slider-thumb{22×22 surface, border 3px brand}` | L203-206 | thumb pintado en `NMMoodSlider` | pseudo-elemento thumb → painter | `components/mood.py` | side-by-side | animo |
| `MOOD_PALETTE` 10 niveles | (theme) | `MOOD_PALETTE`, `get_mood()`, `mood_qcolor()` | — | `shared/theme.py:276`, `theme_qt.py:2017` | `--key suite:registro-step1*@*` | registro emoción |
| emoji mood / picker | (animo, registro) | `NMMoodEmoji`, `NMEmojiPicker`, `NMMoodContextHeader` | emoji glyph render | `components/mood.py:67,141`, `session.py:1074` | side-by-side | animo, registro |

---

## Keys → familias dominantes

Para no concentrar el trabajo en una sola familia, esta tabla cruza cada grupo de
keys con las familias que más impactan su render. Detalle exacto por key en
`qa/_mockup_canonical/INDICE_CAPTURAS.csv` y `VISUAL_REPAIR_HANDOFF.md`.

| Grupo de keys | Familias dominantes | Archivo runtime |
|---|---|---|
| `suite:home*` | F3 cards, F9 rings, F2 typo, F7 chips | `app/home_qt.py` |
| `suite:animo` | F15 mood, F4 buttons | `app/modules/animo_qt.py` |
| `suite:respiracion*` | F9 rings, F4 ctl | `app/modules/respiracion_qt.py` |
| `suite:timer*` | F9 rings, F4 ctl, F11 empty | `app/modules/timer_qt.py` |
| `suite:rutina*` | F10 rows/checks, F8, F11 | `app/modules/rutina_qt.py` |
| `suite:avisos*` | F7 chips, F10 rows, F5 search, F11 | `app/modules/avisos_qt.py` |
| `suite:actividades*` | F10 rows, F7 filtros, F11 | `app/modules/actividades_qt.py` |
| `suite:registro*` | F8 stepper, F5 forms, F15 mood, F2 | `app/modules/registro_tcc_qt.py` |
| `suite:dbt-*` | F9 bars, F3 cards, F12 modal | `app/modules/dbt_qt.py` |
| `suite:onboarding*`, `recuperar-acceso` | F5 forms, F13 chrome, F2 | `app/onboarding_qt.py` |
| `hub:pacientes*` | F10 rows, F14 avatar, F11 | `hub/pacientes_qt.py` |
| `hub:detalle*` | F6 tabs, F5 forms, F3 panels | `hub/pacientes_qt.py`, `hub/plan_terapeutico.py` |
| `hub:detalle-plan-*` | F6 tabs, F9 rings, F10 rows | `hub/plan_terapeutico.py` |
| `hub:detalle-resumen-ia-0` | F12 modal, F8 feedback | `hub/ia_asistente.py` |
| `hub:textos-globales` | F10 rows, F5 inputs | `hub/config_global_texts.py` |
