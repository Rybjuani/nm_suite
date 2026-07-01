# Design-System Translation Bridge — NeuroMood

> Capa interna de equivalencias **HTML/CSS canonical → PyQt6**. Su propósito es
> que los próximos checks visuales se resuelvan con **patrones reutilizables y
> trazables a la fuente canónica**, no con fixes artesanales por pantalla.

Este documento es el **índice y contrato** del bridge. No repara pantallas y no
cierra checkboxes del handoff. Solo define el vocabulario compartido entre el
mockup canónico y el runtime Qt.

## Estado

| Campo | Valor |
|---|---|
| Creado | 2026-06-29 |
| Fuente CSS canónica | `qa/pack canonico/neuromood-mockup_reparado.html` (líneas 11–415) |
| Capturas canónicas | `qa/_mockup_canonical/` (86 PNG = 43 vistas × 2 temas) |
| Índice de keys | `qa/_mockup_canonical/INDICE_CAPTURAS.csv` |
| Tokens runtime | `shared/theme.py` (fuente única de datos visuales) |
| Adaptador Qt | `shared/theme_qt.py` (helpers QSS/painter) |
| Componentes runtime | `shared/components/*.py` (101 clases `NM*`/`V3*`) |
| Gate operativo | `qa/layered_visual_compare.py` (no lo toca este bridge) |
| Grafo navegable | `graphify-out/` + `graphify update .` |

## Mapa de documentos del bridge

| Documento | Contenido | Cuándo usarlo |
|---|---|---|
| `DESIGN_SYSTEM_TRANSLATION_BRIDGE.md` (este) | Índice, familias, principios, reglas de uso | Punto de entrada |
| `CSS_TO_PYQT_EQUIVALENCE_MATRIX.md` | Matriz selector/patrón CSS → token/helper/widget Qt → keys | Traducir un selector concreto |
| `VISUAL_COMPONENT_CATALOG.md` | Catálogo por componente `NM*` con specs, props y archivos | Saber qué widget usar |
| `QT_HTML_KNOWN_MISMATCHES.md` | No-equivalencias Qt↔Chromium y su workaround canónico | Entender por qué algo no matchea |
| `BRIDGE_USAGE_FOR_AGENTS.md` | Protocolo para resolver un check usando el bridge | Antes de tocar una pantalla |

## Principios

1. **Fuente única de tokens.** Todo valor visual (color, radio, sombra, fuente,
   spacing, transición) vive en `shared/theme.py` y se lee con accessors de
   `shared/theme_qt.py` (`C()`, `v3c()`, `colors()`, `qfont()`, `v3_font()`,
   `shadow_effect()`, `v3_shadow()`, `paint_card_lift()`, `stylesheet_*`). El
   bridge **no** introduce constantes nuevas: mapea a las existentes.
2. **Equivalencia con fuente.** Cada equivalencia debe citar un selector/patrón
   real del HTML canónico (con número de línea) y/o una captura canónica. Una
   equivalencia sin fuente canónica es inválida (ver
   `BRIDGE_USAGE_FOR_AGENTS.md`).
3. **No-equivalencias declaradas.** Cuando Qt no puede reproducir un mecanismo
   CSS 1:1 (conic-gradient, backdrop-filter, multi-layer box-shadow, container
   queries, pseudo-elementos), se documenta el workaround canónico en
   `QT_HTML_KNOWN_MISMATCHES.md`. No se inventa QSS para tapar la diferencia.
4. **Reuso antes que override.** Si existe un componente `NM*` que cubre el
   patrón, se usa ese componente; no se duplica QSS local con `setStyleSheet`.
   La consolidación de overrides locales sigue el plan por fases de
   `docs/PLAN_MODULARIZACION_COMPONENTES.md` (fases 6–8, fuera de ejecución).
5. **El bridge no es un gate.** No cierra items, no cambia thresholds, no toca
   `qa/`. El cierre sigue exigiendo `qa/layered_visual_compare.py` + revisión
   manual, según `VISUAL_QA_AGENT_PROTOCOL.md`.

## Familias visuales (cobertura del sistema completo)

El sistema canónico se agrupa en **15 familias**. Cada una mapea a tokens de
`shared.theme` y a componentes de `shared/components/`. La matriz completa está
en `CSS_TO_PYQT_EQUIVALENCE_MATRIX.md`; el detalle por componente en
`VISUAL_COMPONENT_CATALOG.md`.

| # | Familia | Selectores canónicos (ej.) | Componentes/Helpers Qt | Archivo principal |
|---|---|---|---|---|
| F1 | **Tokens** | `:root`, `[data-theme]`, `--brand`, `--r-lg`, `--shadow-2`, `--t` | `V3_LIGHT/DARK`, `V3_RADIUS`, `V3_SHADOWS`, `TRANSITIONS`, `C()`, `v3c()` | `shared/theme.py`, `shared/theme_qt.py` |
| F2 | **Typography** | `--font-display`, `--font-body`, `.h-serif`, `.eyebrow`, `.stage__title` | `TYPOGRAPHY`, `qfont()`, `v3_font()`, `nm_font()`, `NMSectionHeader`, `_GradientTextLabel` | `shared/theme.py`, `shared/components/icons.py` |
| F3 | **Surfaces / Cards** | `.card`, `.card.pad`, `.card.hov`, `.screen-frame` | `NMCard`, `NMSectionCard`, `NMPanel`, `NMCardSecondary`, `NMFeaturedCard`, `NMFormPanel`, `paint_card_lift`, `v3_shadow` | `shared/components/cards.py`, `surfaces.py` |
| F4 | **Buttons** | `.btn`, `.btn--primary/ghost/soft`, `.ctl`, `.ctl.main`, `.back` | `NMButton`, `NMButtonOutline`, `NMIconButton`, `NMPlayButton` | `shared/components/buttons.py`, `inputs.py`, `navigation.py` |
| F5 | **Inputs / Forms** | `.input`, `textarea.input`, `.field-lbl`, `.nav__search input` | `NMInput`, `NMTextArea`, `NMSearchInput`, `NMSelect`, `NMFormRow`, `NMFormField`, `stylesheet_lineedit/textedit/combobox` | `shared/components/buttons.py`, `inputs.py`, `surfaces.py`, `session.py` |
| F6 | **Navigation / Tabs** | `.tabs`, `.seg`, `.hub-tabs`, `.nav`, `.nav__item` | `NMTabs`, `NMSegmentedChoice`, `NMSidebar`, `NMHubSidebar`, `NMHeader`, `NMModule` | `shared/components/buttons.py`, `navigation.py`, `surfaces.py` |
| F7 | **Chips / Badges / Pills** | `.badge`, `.badge.brand/accent/gold/rose`, `.fchip`, `.tag` | `NMBadge`, `NMChip`, `NMStatusChip`, `NMPhaseChip`, `NMCalmBadge`, `NMPresetChip`, `NMCategoryFilter`, `NMStreakBadge` | `shared/components/surfaces.py`, `status.py`, `session.py` |
| F8 | **Feedback / Steppers** | `.toast`, `.dots`, `.stepper`, progress | `NMToast`, `NMStepper`, `NMTCCStepper`, `NMInstallStepper`, `NMProgressBar`, `NMProgressLine`, `NMSkeleton`, `NMStatusBanner`, `NMTypingDots` | `shared/components/feedback.py`, `status.py`, `onboarding.py`, `session.py` |
| F9 | **Rings / Charts** | `.bigring`, `.ring` (conic), `ringSVG`, `.dbt-card .bar` | `NMFocusArc`, `NMCycleRing`, `NMModuleRing`, `NMRingPulse`, `NMWaveChart`, `NMHeatBar`, `NMSparkline`, `NMAreaSparkline`, `NMChartPanel`, `conical_arc_gradient` | `shared/components/rings.py`, `feedback.py`, `patient.py`, `cards.py` |
| F10 | **Lists / Rows** | `.prow`, `.phead`, `.plist`, `.rt-row`, `.rt-cb`, `.tg-row` | `NMListRow`, `NMRow`, `NMPatientRow`, `NMPatientRowPremium`, `NMRoutineSection`, `NMCustomCheck` | `shared/components/surfaces.py`, `patient.py`, `session.py` |
| F11 | **Empty / Error states** | `.empty`, `.empty .ico` | `NMEmptyState`, `NMErrorState`, `_NMEmptyStateChip`, `_NMSuccessIconChip` | `shared/components/overlays.py` |
| F12 | **Modal / Dialog / Overlay** | `.modal-bg`, `.modal`, `.modal.dbt-practice`, `backdrop-filter` | `NMDialog`, `NMDialogScaffold`, `NMTooltip` | `shared/components/dialogs.py`, `overlays.py` |
| F13 | **Chrome / Window** | `.window`, `.titlebar`, `.tb-dots`, `.tb-dot`, `--chrome` | `NMWindowChrome`, `_ChromeWinBtn`, `_ChromeThemeToggle`, `_ChromeLogoMark`, `aplicar_captionbar_qt` | `shared/components/chrome.py`, `shared/theme_qt.py` |
| F14 | **Avatar / Brand / Icons** | `.avatar`, `.brandmark`, `.nav__item .ic`, set `I` | `NMAvatar`, `NMIcon`, `_LogoLabel`, `nm_icon()`, `icon_stroke_width()` | `shared/components/icons.py`, `navigation.py`, `shared/icons_svg.py` |
| F15 | **Mood system** | `input[type=range]` (mood gradient), MOOD_PALETTE | `NMMoodSlider`, `V3MoodSlider`, `NMMoodEmoji`, `NMEmojiPicker`, `NMMoodContextHeader`, `mood_gradient()` | `shared/components/mood.py`, `session.py` |

> Cobertura: las 15 familias cubren las 86 keys. Ninguna familia concentra el
> bridge: el reparto por keys está en `CSS_TO_PYQT_EQUIVALENCE_MATRIX.md` §
> "Keys → familias dominantes".

## Las 86 visual keys (resumen por superficie)

Detalle completo (screen/state/surface/selector/tamaño) en
`qa/_mockup_canonical/INDICE_CAPTURAS.csv`. Resumen:

| App | Pantalla (screen) | Keys | Surface | Familias dominantes |
|---|---|---|---|---|
| suite | home / home-no-score | 4 | window 960×600 | F3,F9,F2,F7 |
| suite | animo | 2 | window | F15,F4,F3 |
| suite | respiracion (idle/running/paused) | 6 | window | F9,F4 |
| suite | timer (idle/running/paused/empty) | 8 | window | F9,F4,F11 |
| suite | rutina (default/add/done/empty) | 8 | window | F10,F8,F11 |
| suite | avisos (all/active/today/search/empty) | 10 | window | F7,F10,F5,F11 |
| suite | actividades (default/filtered/marked/empty) | 8 | window | F10,F7,F11 |
| suite | registro TCC (s0/s1/s1otro/s2/s3/ok) | 12 | window | F8,F5,F15,F2 |
| suite | dbt (now/library/practice-stop) | 6 | window + window_modal | F9,F3,F12 |
| suite | onboarding (normal/error) | 4 | narrow 520×600 | F5,F13,F2 |
| suite | recuperar-acceso | 2 | narrow 520×600 | F5,F2,F13 |
| hub | pacientes (list/empty) | 4 | window | F10,F11,F14 |
| hub | detalle (recordatorios) | 2 | window | F6,F5,F3 |
| hub | detalle-plan (timer/rutina/activacion) | 6 | window | F6,F9,F10 |
| hub | detalle-resumen-ia | 2 | window_modal 960×600 (panel 720×462) | F12,F8 |
| hub | textos-globales | 2 | window | F10,F5 |

(76 window + 6 narrow + 0 modal + 4 window_modal = 86)

## Cómo retomar los checks con el bridge

Ver `BRIDGE_USAGE_FOR_AGENTS.md`. Flujo corto:

1. Tomar la key del handoff (`VISUAL_REPAIR_HANDOFF.md`).
2. `graphify explain "<key o pantalla>"` → ubicar el componente/archivo runtime.
3. Buscar el selector canónico en `CSS_TO_PYQT_EQUIVALENCE_MATRIX.md`.
4. Verificar contra `QT_HTML_KNOWN_MISMATCHES.md` si la divergencia es
   irreductible (techo Qt) o reparable (flat-region real).
5. Reparar usando el token/helper/componente del catálogo, no QSS inventado.
6. Cerrar con el gate oficial (`qa/layered_visual_compare.py`), nunca con el
   bridge.

## Estrategia de componentes (Fase 3 — plan, no ejecución)

Esta sección documenta qué consolidar; **no** crea módulos ni toca runtime. Se
subordina a `docs/PLAN_MODULARIZACION_COMPONENTES.md`: las fases mecánicas 0–5
(estructura `shared/components/` por familias) ya están materializadas
(`components_qt.py` es facade y los `NM*` viven por familia). La consolidación
**visual** es fases 6–8 de ese plan y está **fuera de ejecución** hasta aprobarse
por separado. El bridge solo prioriza candidatos y los ancla a la fuente canónica.

### Deuda medida (QSS local a absorber)

`setStyleSheet` directos en `app/` + `hub/` (≈290, sin `__pycache__`), top:

| Archivo | `setStyleSheet` | `v3c()/C()` | Familias del bridge a reusar |
|---|---:|---:|---|
| `app/modules/registro_tcc_qt.py` | 37 | 40 | F8 stepper, F5 forms, F15 mood |
| `app/onboarding_qt.py` | 33 | — | F5 forms, F13 chrome, F8 stepper |
| `hub/main_qt.py` | 26 | 20 | F6 nav/tabs, F13 chrome |
| `hub/plan_terapeutico.py` | 25 | 12 | F6 tabs, F9 rings, F10 rows |
| `app/home_qt.py` | 24 | 31 | F3 cards, F9 rings, F7 chips |
| `app/modules/dbt_qt.py` | 21 | 23 | F9 bars, F3 cards, F12 modal |
| `app/modules/avisos_qt.py` | 18 | 26 | F7 chips, F10 rows, F5 search |

> Que un archivo use `v3c()/C()` es bueno (lee tokens canónicos). El objetivo de
> consolidación es el **QSS inline duplicado**, no el lookup de tokens.

### Candidatos de consolidación (alineados a PLAN_MODULARIZACION fases 6–8)

1. **6A — helpers de scroll/textedit/lineedit.** Reemplazar QSS inline de
   inputs/scroll por `stylesheet_lineedit/textedit/scrollarea/combobox` ya
   existentes. Mayor impacto: `registro_tcc_qt`, `onboarding_qt`,
   `config_global_texts`.
2. **6B — chips/badges.** Unificar chips de filtro/estado locales en `NMChip`,
   `NMBadge`, `NMStatusChip`, `NMCategoryFilter`. Impacto: `avisos_qt`,
   `actividades_qt`, `dbt_qt`.
3. **6C — cards/paneles.** Reemplazar paneles con QSS inline por `NMCard`,
   `NMSectionCard`, `NMPanel`, `NMFormPanel`. Impacto: `home_qt`,
   `plan_terapeutico`, `dbt_qt`, `hub/pacientes_qt`.
4. **6D — labels/typography.** Centralizar labels con `v3_font()`/`label_style()`
   y `NMSectionHeader`. Impacto: transversal.

Regla de ejecución futura: una vista/componente por commit, con captura puntual
claro/oscuro de la vista tocada (fases 6–7 del plan). El bridge aporta la fuente
canónica y la no-equivalencia esperada para cada caso.

### Huecos detectados (componentes a evaluar — NO crear ahora)

- **Focus ring de input** (`box-shadow 0 0 0 3px brand-soft`, MISMATCH#5): el
  ring de foco está repartido entre `focus_ring_stylesheet()` y pintura por
  componente. Evaluar un único `NMInput` que pinte el ring 3px de forma uniforme
  para cerrar `recuperar-acceso`/forms sin QSS por pantalla. Propuesta, no acción.
- **Mood track compartido** (F15): `NMMoodSlider` y `V3MoodSlider` coexisten;
  evaluar consolidar en uno (track 6-stop + thumb 22px) para `animo` y
  `registro-step1`. Propuesta.
- **D001 `NMPlayButton` 46×56 vs 58** (F4, `.ctl.main`): defecto abierto de
  geometría; corregir tamaño al reparar `timer/respiracion`, no crear componente
  nuevo.

> Ubicación segura ya existente: cualquier consolidación va a `shared/components/`
> (familia correspondiente) y `shared/theme_qt.py` (helpers), **sin** crear
> carpetas nuevas ni romper la facade `shared/components_qt.py`.
