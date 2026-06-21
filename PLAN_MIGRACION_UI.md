# Plan de migración UI · NeuroMood Suite + Hub → mockup canónico

> ⚠️ **SUPERADO por [`PLAN_MIGRACION_UI_V2.md`](PLAN_MIGRACION_UI_V2.md)** (raíz). Este
> documento se conserva como histórico / fuente del postmortem (§3 del V2). El ADN, fuentes,
> QSS e íconos que describe ya están implementados; usar el V2 para ejecutar.

## Contexto

`neuromood-mockup.html` (raíz, 1680 líneas) es la **única fuente de verdad** visual.
Las dos apps PyQt6 (`app/` = Suite · Paciente, `hub/` = Hub · Clínico) **ya implementan
todas las pantallas del mockup** tras 11 fases de coherencia visual (F0–F11, en `main`),
pero sobre un **ADN distinto** que hoy está *bloqueado por tests*:

| Aspecto | App actual (ADN bloqueado) | Mockup (nuevo ADN objetivo) |
|---|---|---|
| Claro · fondo / brand | lino `#F4EFE5` / salvia `#305A48` | crema `#E9E3D6` / bosque `#2E5D43` |
| Oscuro · fondo / brand | índigo `#07091A` / **lavanda `#A99CFF`** | tinta `#0E121C` / **menta `#56D9A6`** |
| Tipografía | Manrope (sans) + Newsreader (serif) | **Inter** (body) + **Fraunces** (display) |

El cambio mayor es el **tema oscuro**: hoy es violeta, el mockup es verde-menta. Es un
cambio de identidad real, no un retoque.

**Decisiones del owner (confirmadas):**
1. **Adoptar el mockup como nuevo ADN** — re-tokenizar a valores EXACTOS del mockup,
   cambiar fuentes a Inter+Fraunces, **reescribir** los tests de bloqueo y **regenerar**
   las baselines de QA. Máxima fidelidad, idealmente idéntico.
2. **Pantallas obsoletas:** ya estaban eliminadas del código (la memoria estaba stale).
   No queda pantalla funcional por borrar; solo residuo (capturas QA stale + comentarios
   históricos) que limpia la fase de regresión.
3. **Orden:** base compartida → Suite → Hub.

**Resultado esperado:** ambas apps renderizan cada pantalla idéntica al mockup en claro y
oscuro, con conmutador de tema en caliente, preservando lógica/datos/auth/PDF/IA/
notificaciones. **No se replica** la cáscara web del mockup (riel nav, seg Suite/Hub,
selector de pantallas, chip-state, "device window"): solo las PANTALLAS, integradas a la
navegación real (Suite: Home + `NMFadeWidget` + `NMWindowChrome`; Hub: sidebar + stack).

---

## Arquitectura detectada + supuestos

**Tema / tokens (reutilizar, re-apuntar):**
- `shared/theme.py` — catálogo maestro: `V3_LIGHT`, `V3_DARK` (~130 tokens c/u),
  `V3_SPACE`, `V3_RADIUS`, `V3_SHADOWS`, `V3_GRADIENTS`, `TYPOGRAPHY`, `MOOD_PALETTE`.
- `shared/theme_qt.py` (2236 líneas) — puente Qt: `C()/qcolor()/v3c()`, `qfont()`,
  `shadow_effect()/v3_shadow()`, gradientes, y **generadores QSS por tema**
  (`stylesheet_base`, `_lineedit`, `_textedit`, `_combobox`, `_slider`,
  `_tabwidget_segmented`, scrollbars…). Templating por f-string inyectando tokens.
- `shared/theme_manager.py` — `ThemeManager(QObject)` singleton, señal `theme_changed`,
  switch con overlay-fade 350ms. **Hot-reload ya existe** (cada widget conecta
  `theme_changed` → `_apply_theme(modo)` → regenera QSS + `update()`).
- `shared/fonts.py` — `load_fonts()` registra TTF vía `QFontDatabase.addApplicationFont`;
  hoy carga Manrope/Newsreader/JetBrainsMono. **Inter y Fraunces NO están** en
  `assets/fonts/`.
- `shared/icons_svg.py` — catálogo de ~80 SVG (`ICON_BODIES`) + `nm_svg_pixmap()`,
  cacheado. Render vía `QSvgRenderer`.

**Biblioteca de componentes (reutilizar, auditar fidelidad):** `shared/components/*`
(47 widgets). Cobertura vs primitivas del mockup: prácticamente total. Pintura custom
con `pyqtProperty(float)` + `QPropertyAnimation` ya implementada en anillos/sparklines/
toggles/checks. Mapeo en la tabla de primitivas (abajo).

**Navegación Suite** (`app/main_qt.py`): un `QMainWindow` + `NMWindowChrome` (titlebar:
back + título módulo + theme toggle) + `NMFadeWidget` (stack con fade). `_MODULE_MAP` con
8 módulos cacheados. `HomeView` (grid de 8 cards) → módulo. Hooks `on_enter/on_leave`.

**Navegación Hub** (`hub/main_qt.py`): `QMainWindow` + `NMWindowChrome` + stack.
`_nav_views() = {pacientes, textos_globales}`; `DetallePacienteView` on-demand.

**Integraciones a preservar (no reimplementar):** Supabase/auth (`shared/db.py`,
`shared/sync.py`, `shared/config.py`); PDF reportlab (`hub/exportar.py`); IA groq/openai/
gemini (`hub/ia_asistente.py`); notificaciones/bandeja winotify/plyer/pystray
(`app/avisos_daemon.py`). La UI nueva se cablea a estos *seams* existentes.

**Supuestos:** (a) el `NMWindowChrome` actual es el equivalente real del `.titlebar` del
mockup (semáforo + theme toggle + back + icono + título/crumb) → se re-estiliza, no se
reemplaza por la cáscara web. (b) Inter+Fraunces se obtienen como TTF estáticos OFL
(Google Fonts/GitHub) y se versionan en `assets/fonts/`. (c) Dimensiones objetivo
960×600 (vistas) y 520×600 (onboarding/recuperar) — coinciden con el harness QA actual.

---

## Tabla de mapeo de pantallas + análisis de huecos

**SUITE** (`render(state)` del mockup ↔ clase real). Sin huecos de pantalla; la app ya
tiene 8 módulos = mockup.

| Mockup (id · estados) | Clase real | Archivo | Δ fidelidad principal |
|---|---|---|---|
| `home` (score / noscore) | `HomeView` | `app/home_qt.py:861` | hero crema+brand; 8 cards `min-h 148`, badges exactos |
| `animo` | `ModuloAnimo` | `app/modules/animo_qt.py` | grid 0.9/1.1; slider arcoíris; **chart 7/30 días** (tabs) embebido |
| `respiracion` (idle/running/paused) | `ModuloRespiracion` | `app/modules/respiracion_qt.py` | `bigring` 230/200, presets 3·5·10, badges fase, ctl 46/58 |
| `registro` (s0/s1/s1otro/s2/s3/ok) | `ModuloRegistroTCC` | `app/modules/registro_tcc_qt.py` | stepper 4 pasos, chips emoción, tip card gold, éxito |
| `actividades` (default/filtered/marked/empty) | `ModuloActividades` | `app/modules/actividades_qt.py` | fchips categorías, dots, "Hice/No pude", "Hecho" |
| `avisos` (all/active/today/search/empty) | `ModuloAvisos` | `app/modules/avisos_qt.py` | tabs filtro + search, rows icono+badge, "Completar" |
| `rutina` (default/add/done/empty) | `ModuloRutina` | `app/modules/rutina_qt.py` | resumen ring 64, 3 bloques `rt-cb`+ring 40, líneas |
| `timer` (idle/running/paused/empty) | `ModuloTimer` | `app/modules/timer_qt.py` | `bigring` MM:SS, status badge, fchips min+modo |
| `dbtnow` + `dbtlib` (+ STOP modal) | `ModuloDBT` | `app/modules/dbt_qt.py` | seg Ahora/Biblioteca, need-cards, dbt-card, STOP stepper. **Extra app: tab Historial → conservar.** |
| `onboarding` (normal/error) | `run_onboarding`/`onboarding_qt` | `app/onboarding_qt.py` | narrow 560; consent card; check términos; error rose |
| `recuperar` | (flujo recuperación) | `app/onboarding_qt.py` | narrow; email resaltado brand |

**HUB**

| Mockup (id · estados) | Clase real | Archivo | Δ fidelidad principal |
|---|---|---|---|
| `pacientes` (list/empty) | `PacientesView` | `hub/main_qt.py:259` | `prow` avatar+sparkline 78×30+ring uso gold; header `phead`; vacío |
| `detalle` (+ Resumen IA modal) | `DetallePacienteView` | `hub/pacientes_qt.py:74` | **aplanar a 4 tabs** (Recordatorios/Temporizador/Rutina/Activación) + grid form\|panel; Exportar PDF + Resumen IA |
| `textos` | `TextosGlobalesSuiteView` | `hub/config_global_texts.py:170` | top search+filtro+badge "145"; `tg-row` dirty; contador; Restaurar/Guardar |

**Huecos / diferencias de IA (no son pantallas faltantes):**
- DBT: mockup expone "Ahora" y "Biblioteca" como 2 entradas de nav con seg interno; la app
  las tiene como tabs dentro de `ModuloDBT` + **Historial extra** → se conserva la
  estructura de la app (más completa), re-estilando Ahora/Biblioteca al mockup.
- Hub Detalle: mockup = 4 tabs planas + grid form\|panel; app = hero + tab "Plan
  terapéutico" con 4 sub-tabs → **se aplana** al layout del mockup.
- "STOP" es un modal lanzado desde una skill DBT (mockup `openDBTPractice`); la app tiene
  `_SkillPracticeView` con stepper → re-estilar al modal STOP del mockup.

---

## Especificación de tokens + generación de QSS por tema

Fuente canónica: `neuromood-mockup.html` líneas 15–67. Se re-apuntan los dicts de
`shared/theme.py` (no se crea un módulo nuevo; se reutiliza la maquinaria existente).

**Escalas globales (reemplazo de `V3_RADIUS`, transiciones):**
```
radios:  r-xs 8 · r-sm 12 · r-md 16 · r-lg 22 · r-xl 28 · pill 999
trans:   t-fast 140ms cubic-bezier(.4,0,.2,1)
         t      240ms cubic-bezier(.32,.72,.24,1)
         t-slow 480ms cubic-bezier(.32,.72,.24,1)   → ANIM en theme_qt.py + EASE
```

**Paleta CLARO (reemplaza `V3_LIGHT`):**
```
bg #E9E3D6 · bg-grad-a #EEE9DD · bg-grad-b #E3DCCB
surface #FBF8F1 · surface-2 #F3EFE4 · surface-3 #ECE6D8
ink #312D27 · ink-2 #6B6457 · ink-3 #9A9382
line rgba(49,45,39,.10) · line-2 rgba(49,45,39,.06)
brand #2E5D43 · brand-strong #244C37 · brand-ink #F7F3EA
brand-soft rgba(46,93,67,.13) · brand-line rgba(46,93,67,.28)
accent #B0683B · accent-soft rgba(176,104,59,.15)
gold #C2912F · gold-soft rgba(194,145,47,.16)
rose #B24E3D · rose-soft rgba(178,78,61,.14)
mind #3C8A6B · toler #C25A45 · regul #CC8F2C · efect #2E5D43   (tonos DBT)
ring-track rgba(49,45,39,.10) · focus rgba(46,93,67,.45)
chrome #E5DED0 · chrome-line rgba(49,45,39,.10)
shadow-1: 0 1px2px .05 + 0 2px6px .04 · shadow-2/3 (líneas 32–33)
```

**Paleta OSCURO (reemplaza `V3_DARK`):**
```
bg #0E121C · bg-grad-a #121726 · bg-grad-b #0B0E18
surface #191F2E · surface-2 #212838 · surface-3 #283047
ink #E8EAF1 · ink-2 #A7AEC1 · ink-3 #727A90
line rgba(255,255,255,.09) · line-2 rgba(255,255,255,.05)
brand #56D9A6 · brand-strong #3FC592 · brand-ink #06140D
brand-soft rgba(86,217,166,.14) · brand-line rgba(86,217,166,.34)
accent #E0996A · accent-soft rgba(224,153,106,.16)
gold #E3B765 · gold-soft rgba(227,183,101,.16)
rose #F09182 · rose-soft rgba(240,145,130,.16)
mind #5FE0B2 · toler #FF9082 · regul #E9BC66 · efect #7CC6F0
ring-track rgba(255,255,255,.10) · focus rgba(86,217,166,.5)
chrome #141A28 · chrome-line rgba(255,255,255,.07)
shadow-1/2/3 (líneas 53–55, base negra)
```

**Tipografía:** `font-display = Fraunces` (display/h-serif/`.num`/`.h-serif`),
`font-body = Inter` (todo lo demás). Re-apuntar `TYPOGRAPHY.font_family`/`font_serif` y las
cadenas de fallback de `fonts.py`. Tamaños del mockup ya en px (compatibles con `qfont()`):
display 40/30/26, serif headings 22/20/17/16, body 13.5, small 12.5, eyebrow 11
(tracking .14em upper), `.num` 52, slider/ring labels según CSS.

**Generación QSS por tema:** se mantiene el patrón actual (un generador por componente que
inyecta tokens del `modo`). Se re-templan con los nuevos valores: `stylesheet_base`,
botones (`.btn--primary/ghost/soft`), `input/textarea`, `tabs`/`seg`/`fchip`, slider
arcoíris, scrollbars, focus ring (`:focus` border-line + `0 0 0 3px brand-soft`).
**Conmutación en caliente** (ya existe): `app.setStyleSheet(...)` regenerado por
`theme_changed` + `unpolish/polish` en widgets con `setProperty` + `.update()` en pintura
custom. Variantes por propiedad dinámica: `variant=primary|ghost|soft`,
`tone=brand|gold|rose|accent`, selectores `QPushButton[variant="primary"]{…}` (ya en uso).

---

## Catálogo de componentes + orden de construcción

Primitivas y widgets QPainter **primero**, luego pantallas. Mapeo primitiva mockup → widget
existente a auditar (alinear radios/paddings/tamaños/sombra/curva al CSS del mockup):

| Primitiva mockup (línea CSS) | Widget existente | Archivo | Acción |
|---|---|---|---|
| `.card` / `.card.hov` (257) lift -3px | `NMCard` | `cards.py` | retunear radio 22, sombra-1→2, hover translateY(-3) + brand-line |
| `.badge` (.brand/.accent/.gold/.rose) (265) | `NMBadge`/`NMChip` | `surfaces.py` | colores soft + dot `.dt` |
| `.btn` primary/ghost/soft (274) | `NMButton` | `buttons.py` | pill, padding 11×20, active scale .99, hover strong |
| `.input`/`textarea` (287) | `NMInput`/`NMTextArea` | `buttons.py` | radio 16, focus brand-soft 3px |
| `.tabs`/`.seg`/`.fchip` (295) | `NMTabs`/`NMSegmentedChoice` | `buttons.py` | activo brand+ink; fchip pressed |
| `.empty` (306) ico 64 brand-soft | `NMEmptyState` | `overlays.py` | ico 64 r18, h-serif 20 |
| `.ring` conic (320) | `NMModuleRing` | `rings.py` | track + brand arco, label % |
| `.bigring`+`.core`+`.ctl` (207) | `NMFocusArc`/`_BreathCircle` | `rings.py`,`respiracion_qt.py` | 230/200, num 52/46, ctl 46/58 |
| range slider arcoíris (199) | slider mood | `mood.py`/`theme_qt._slider` | track gradiente 6 stops, thumb 22 borde brand |
| `.rt-cb` check (222) | `NMCustomCheck` | `session.py` | 22, r7, on brand, check anim |
| `.stepper` (235) | `NMStepper` | `feedback.py` | línea + fill brand, done/active |
| `.toast` (335) | `NMToast` | `overlays.py` | ink bg, pill, fade+slide, autodismiss 2200ms |
| `.modal-bg`+`.modal` (343) | `NMDialog` | `dialogs.py` | scrim rgba(20,18,14,.5), scale .96→1 |
| `.prow`+`.avatar` (245) | `NMPatientRow` | `patient.py` | avatar 40 r12, hover surface-2 |
| sparkline 78×30 (1360) | `NMSparkline` | `patient.py` | 2px + punto final |
| mood chart área 7/30 (755) | `NMAreaSparkline`/pyqtgraph | `patient.py` | área `mg` gradiente, grid 0/5/10, puntos 7d |
| `.titlebar` semáforo+theme (183) | `NMWindowChrome` | `chrome.py` | chrome bg, dots g/y/r, theme toggle, back, crumb |
| `.themetoggle` dot (148) | toggle en chrome | `chrome.py` | sol/luna + dot animado |
| `.dbt-card`/`.need-card` (228) | `_SkillCard`/`_NeedCard` | `dbt_qt.py` | bar 7×64 color familia, border-left need |

Para íconos: **empaquetar los SVG exactos del mockup** (set `I` del mockup, líneas 465–485)
en `icons_svg.py` para fidelidad idéntica (home, mood, breath, brain, activity, bell,
check, timer, spark, users, user, text, key, shield, smile, flower, doc, sun, moon, arrow),
renderizados con `QSvgRenderer` (ya existe). Recomendado sobre glifos qtawesome.

---

## Checklist por pantalla

Para CADA pantalla (orden Suite luego Hub) verificar: **layout** (grid/medidas del CSS) ·
**estados/variantes** (los del `states:` del mockup) · **interacciones** (handlers del
`mount`) · **animaciones** (curva/duración `t-fast/t/t-slow`) · **paridad claro+oscuro** ·
**textos exactos en español** (del mockup, vía `t()`/remote_config) · **resize** (el
`.window` es max 980/560; las apps son redimensionables → comportarse como el mockup a
960×600 y angosto 520×600). Ejemplos de detalle por pantalla:

- **Home:** hero `linear-gradient(135deg surface→surface-2)` + blob radial brand-soft;
  eyebrow "Bienvenida"; saludo serif 30 contextual; con score: `40 / 10` + badge
  "▲ 0.8 vs semana" + barra brand→mind; sin score: "Aún no registraste…" + botón. 8 cards
  exactas (icono+cat badge+título serif 16.5+sub+badge estado).
- **Termómetro:** col 0.9/1.1; card escala (slider arcoíris, "— / 10", "Guardar registro"
  disabled→enabled); cards progreso 7d/30d; panel chart con tabs "7 días/30 días", grid
  líneas 0/5/10, área brand, puntos 7d. Toast "Registro guardado · N/10".
- **Respiración:** chip-state presets 3/5/10; bigring inhale/hold/exhale (scale 1.12/0.86);
  badges "Inhalá 4s/Mantené 7s/Exhalá 8s"; ctl reset/play/stop; cards Patrón 4·7·8 / Crono
  / Ciclos.
- **Registro TCC:** stepper 4 (Situación/Emoción/Pensamiento/Respuesta) + estado "ok";
  s1 chips emoción + intensidad slider; s1otro input "Otro"; s2 distorsiones rose + tip
  gold; nav Anterior/Siguiente→"Guardar registro".
- **Activación:** card categorías + fchips; grid 2col cards (dots, "No pude" ghost / "Hice"
  soft → "Hecho" badge brand); contador "N actividades sugeridas".
- **Recordatorios:** tabs Todos/Activos/Hoy + search; rows icono color+título+meta cat·hora·
  freq + badge Completado/Hoy/Activo + "Completar"; vacío.
- **Rutina:** resumen ring 64 "N de M tareas"; 3 bloques (sun/smile/moon) con ring 40 + rt-cb
  + tachado; estado add (input+`+`), done (100%), empty.
- **Temporizador:** bigring MM:SS; badge "Lista para empezar/Sesión en curso/En pausa";
  ctl reset/play/skip; fchips min (5/25/45) + modo (Lectura/Pausa activa/Trabajo profundo);
  empty "Sin actividades asignadas".
- **DBT:** seg Ahora/Biblioteca; Ahora = 4 need-cards (border-left tono); Biblioteca =
  fchips familia + dbt-cards (bar color, min, "Práctica guiada"); modal STOP 4 pasos con
  dots + nota de seguridad rose. Conservar tab Historial (extra app).
- **Onboarding/Recuperar:** window narrow; brandmark; campos Nombre/Correo/Contraseña; card
  consentimiento; check "Acepto los términos"; botones Crear cuenta / Iniciar sesión
  (disabled hasta check); error: nombre rose + "Completá tu nombre…"; recuperar: email brand.
- **Pacientes (Hub):** header "Lista activa" + badge "N pacientes" + "Textos globales";
  `phead`; rows (status dot, avatar color, nombre/último, mail/próxima, sparkline, ring uso
  gold, X desvincular); vacío "Sin pacientes vinculados".
- **Detalle (Hub):** hero (avatar 52 r15, eyebrow "Paciente", nombre serif 21, "Seguimiento
  profesional", **Exportar PDF** primary + **Resumen IA** ghost); **4 tabs**; grid
  form\|panel (form con inputs + "Agregar" + "Completar con IA"; panel título + "Restablecer
  por defecto" + empty dashed). Modal Resumen IA (eyebrow nombre + texto + Cerrar).
- **Textos globales (Hub):** top (h-serif + search + select módulo + badge "145 textos");
  `tg-list` filas (mod+nombre, input maxlength, contador `n / max`, Restaurar; dirty =
  brand-line + glow); foot (estado "N cambios sin guardar" + Restaurar todos + Guardar).

---

## Limitaciones de Qt → fallbacks

- **`box-shadow` multicapa** → `QGraphicsDropShadowEffect` es 1 capa: aproximar con la capa
  dominante (blur/offset/alpha del mockup); ya mapeado en `V3_SHADOWS`/`shadow_effect`.
  Cuidar clip con `border-radius` (usar contenedor si hace falta).
- **`backdrop-filter: blur(3px)`** del modal → Qt no lo soporta barato: usar scrim sólido
  `rgba(20,18,14,.5)` sin blur (gap documentado) o snapshot pre-difuminado (costoso, no
  recomendado).
- **transiciones/`transform`** → `QPropertyAnimation`/`QVariantAnimation`/
  `QGraphicsOpacityEffect`. Hover-lift de cards = event filter + animación de pos + sombra.
- **`radial-gradient`/`conic-gradient`** (body, `.screen`, `.bigring`, `.ring`) →
  `qradialgradient`/`qlineargradient` en QSS o `QPainter` en `paintEvent` (ya existe en
  rings y shell background).
- **Render de fuente / sub-pixel** → no será pixel-idéntico; se acepta umbral de diferencia.
- **HiDPI Windows** → política de rounding + `Antialiasing` en todos los `paintEvent`
  (ya presente); validar nitidez a 100% y 125%.

---

## Criterios de aceptación de fidelidad + cómo verificarlos

1. **Targets del mockup** (FASE 0): script Playwright (ya instalado en `.venv`) que carga
   `neuromood-mockup.html` headless, driblea `setTheme/setProduct/go(id,state)` y captura
   cada pantalla×tema×estado a **960×600** (y **520×600** narrow) → `qa/_mockup_targets/`.
2. **Captura de la app:** reutilizar `qa/capture_v8.py` (offscreen `QT_QPA_PLATFORM`) a las
   mismas dimensiones/estados.
3. **Diff lado a lado** por pantalla/tema/estado con Pillow+numpy (deps presentes): SSIM y
   pixel-diff; umbral objetivo **SSIM ≥ 0.92** (o delta documentado con justificación de
   limitación Qt). `QWidget.grab()` para vistas no capturables por el harness estático.
4. **Tests de interacción** con pytest-qt: slider habilita "Guardar", tabs/filtros cambian
   lista, stepper avanza, check habilita login, toast aparece/cierra, modal abre/cierra,
   conmutador de tema repinta.
5. **Re-baseline:** tras aprobar cada pantalla, regenerar baseline; al cierre purgar
   capturas/recetas stale (evolucion/privacy-lock/pin/dashboard/personalizacion/editor).

---

## Lista de tareas incrementales (PR-sized, app ejecutable en cada paso)

**FASE 0 — Targets & tooling** · *S*
- `qa/capture_mockup.py` (Playwright) → `qa/_mockup_targets/` (todas las pantallas×2 temas×
  estados). Harness de diff SSIM `qa/diff_fidelity.py`.
- Copiar este plan a `PLAN_MIGRACION_UI.md` (raíz).

**FASE 1 — Base compartida (tokens/fuentes/QSS)** · *M c/u*
1. Bundle **Inter + Fraunces** (.ttf OFL) en `assets/fonts/`; re-apuntar `fonts.py` +
   `TYPOGRAPHY` (display=Fraunces, body=Inter) + fallbacks. (`tests/test_fonts.py` update.)
2. Re-tokenizar `V3_LIGHT`/`V3_DARK` + `V3_RADIUS` + transiciones a valores exactos del
   mockup; añadir tonos `mind/toler/regul/efect`, `gold`, `rose`, `chrome`, `ring-track`,
   `focus`.
3. **Reescribir** `tests/test_token_parity.py` + `tests/test_no_legacy_visuals.py` al nuevo
   ADN; actualizar `design_tokens.py` (compat) y `V3_SHADOWS`/`V3_GRADIENTS`.
4. Retunear generadores QSS (`stylesheet_base`, botones, inputs, tabs/seg/fchip, slider,
   scrollbars, focus ring) + `app_palette`.
5. Añadir SVG exactos del mockup a `icons_svg.py` (set `I`).
- *Gate:* app arranca, ruff + pytest verdes (tests reescritos), smoke runtime Suite+Hub.

**FASE 2 — Primitivas (fidelidad QPainter/QSS)** · *M c/u, ~6–8 PRs*
- Por grupo: cards/badges/botones · inputs/tabs/fchips · rings (module/breath/timer) +
  slider arcoíris · checks/stepper · toast/modal · titlebar/theme-toggle/sparkline/
  patient-row. Cada PR cierra con diff vs target del componente y ambos temas.

**FASE 3 — Suite pantalla por pantalla** · *M c/u, ~11 PRs* (orden: Acceso → Home →
Termómetro → Respiración → TCC → Activación → Recordatorios → Rutina → Temporizador → DBT)
- Cada PR: layout+estados+interacciones+animación+paridad tema+textos exactos; valida diff
  contra `qa/_mockup_targets/` antes de avanzar.

**FASE 4 — Hub pantalla por pantalla** · *M c/u, ~3–4 PRs*
- Pacientes (list/empty) · Detalle (**aplanar a 4 tabs** + grid form\|panel + Exportar PDF +
  Resumen IA modal) · Textos globales. Preservar seams PDF/IA/Supabase.

**FASE 5 — Regresión & cierre** · *M*
- Re-baseline QA completa (claro+oscuro, todas las vistas/estados); purgar capturas/recetas
  stale; barrido de diff; suite pytest-qt; ruff + pyright; smoke runtime; build `--dry-run`.

**Esfuerzo total estimado:** ~25–30 PRs (S/M). La app queda ejecutable y testeable tras
cada PR; el ADN nuevo se valida desde FASE 1.

---

## Verificación end-to-end (resumen ejecutable)
- `.venv\Scripts\python.exe qa\capture_mockup.py --all --theme both` → targets.
- `.venv\Scripts\python.exe qa\capture_v8.py --all --theme both` → app.
- `.venv\Scripts\python.exe qa\diff_fidelity.py` → reporte SSIM por pantalla.
- `.venv\Scripts\python.exe -m pytest tests/` (incluye tokens reescritos + interacción).
- `ruff check .` · smoke `qa\runtime_live_probe.py --all --theme both`.

**Pausa para aprobación:** no se reescribe UI hasta confirmación. Implementación pantalla
por pantalla, validando fidelidad contra el mockup antes de avanzar.