# Qt ↔ HTML/CSS Known Mismatches

Registro de mecanismos CSS del mockup canónico que **PyQt6 no reproduce 1:1**.
Cada entrada define: el mecanismo CSS, por qué Qt no lo hace igual, el workaround
canónico ya usado en el runtime, y el impacto en el gate visual
(`qa/layered_visual_compare.py`).

> Uso: cuando una key diverge, antes de "reparar" verificá acá si la diferencia
> es **irreductible** (techo Qt — no se cierra cambiando código) o **reparable**
> (flat-region real). No inventes QSS para tapar una no-equivalencia estructural.

Clasificación de impacto:

- **IRREDUCIBLE** — diferencia física Qt-vs-Chromium; no se elimina con código.
  El gate ya la contempla (gate density-aware, tolerancias). No cuenta como fix.
- **WORKAROUND** — Qt no tiene el primitivo CSS pero hay equivalente fiel por
  painter/efecto/layout. La paridad se logra usando ese equivalente.
- **DECISIÓN-OWNER** — el runtime difiere a propósito por decisión de diseño
  documentada; no se "corrige" hacia el mockup.

---

## MISMATCH#1 · Fuentes web (Fraunces / Inter) — WORKAROUND

- **CSS:** `--font-display:"Fraunces"`, `--font-body:"Inter"` vía Google Fonts
  (`L9,L16-17`). Chromium las descarga.
- **Qt:** no descarga fuentes; usa las registradas en `QFontDatabase`. Si no
  están embebidas cae al fallback (`Segoe UI`), cambiando métrica y rasterizado.
- **Workaround:** embeber/registrar las familias (`shared/fonts.py`,
  `_ensure_ui_font()`); `_resolve_default_family()` resuelve la cadena de
  fallback (`TYPOGRAPHY["font_family_fallback_chain"]`).
- **Impacto:** la rasterización de texto Qt-vs-Chromium nunca es idéntica (ver
  MISMATCH#20). Si la familia correcta no carga, la divergencia es mayor y **sí**
  es reparable (registrar la fuente).

## MISMATCH#2 · `transform` / `cubic-bezier` — WORKAROUND

- **CSS:** `transform:translateY(-3px)`, `scale(.99)`, easing
  `cubic-bezier(.32,.72,.24,1)` (`L20-22,274,292`).
- **Qt:** QSS no anima `transform`. Se usa `QPropertyAnimation` + `QEasingCurve`,
  cuyo perfil aproxima el cubic-bezier pero no es bit-exacto.
- **Workaround:** animaciones en los componentes (`NMButton` press 0.97,
  `NMCard` lift). Las capturas son estáticas, así que el estado final importa más
  que la curva.
- **Impacto:** intermedios de animación no se capturan → bajo. El offset final
  (p.ej. card elevada) sí debe coincidir.

## MISMATCH#3 · `box-shadow` multi-capa — IRREDUCIBLE (parcial)

- **CSS:** sombras de 2–3 capas, p.ej. `--shadow-2:0 2px 8px ..., 0 10px 28px ...`
  (`L31-33,53-55`).
- **Qt:** `QGraphicsDropShadowEffect` aplica **una sola** sombra por widget.
- **Workaround:** `V3_SHADOWS` colapsa cada multi-capa a una capa equivalente
  (`shadow_effect()`, `v3_shadow()`, `shadow_1/2/3()`); el "lift" superior se
  pinta aparte (`paint_card_lift`, `V3_LIFT`).
- **Impacto:** halo/penumbra nunca idéntico a 3 capas reales. Pequeña divergencia
  en bordes de cards es esperable; el grueso se cierra acertando la capa
  dominante. No apilar varios efectos por widget (coste/artefactos).

## MISMATCH#4 · `radial-gradient` / `linear-gradient` multi-stop en fondos — WORKAROUND

- **CSS:** `body{radial-gradient(...)}` (`L71-80`), `.screen-frame`/`.bigring`
  radiales (`L209-213,251-265`), track del slider 6-stop (`L202`).
- **Qt:** QSS soporta `qlineargradient`/`qradialgradient` limitado y frágil en
  algunas properties; no replica bien estos fondos.
- **Workaround:** pintar con `QRadialGradient`/`QLinearGradient` en `paintEvent`
  (`radial_glow()`, `radial_glow_double()`, `linear_gradient()`,
  `mood_gradient()`).
- **Impacto:** WORKAROUND fiel si se respetan stops/centro/radio. Divergencia si
  se aproxima con un color plano.

## MISMATCH#5 · Focus ring `box-shadow 0 0 0 3px` + `:focus-visible` — WORKAROUND

- **CSS:** `:focus-visible{outline:2px+offset}` (`L84`) y inputs
  `:focus{box-shadow:0 0 0 3px var(--brand-soft)}` (`L123,304`).
- **Qt:** no existe `:focus-visible` ni `outline-offset`; el `box-shadow` de foco
  no se puede emular con QSS `border` solo (ocupa layout).
- **Workaround:** `focus_ring_stylesheet()` + ring pintado en `NMCard`/`NMInput`.
- **Impacto:** el grosor/blando del ring puede diferir. En `recuperar-acceso` el
  ring de foco del email es una flat-region reparable citada en el handoff.

## MISMATCH#6 · `letter-spacing` em (tracking) — WORKAROUND

- **CSS:** `.eyebrow{letter-spacing:.14em}`, `.h-serif{-.015em}` (`L276-277`).
- **Qt:** `QFont.setLetterSpacing(QFont.SpacingType.PercentageSpacing, pct)` usa
  porcentaje del ancho del glifo, no `em`.
- **Workaround:** `qfont()`/`v3_font()` aplican spacing porcentual aproximando el
  em. `TYPOGRAPHY["tracking_eyebrow"]=".14em"` documenta el objetivo.
- **Impacto:** ancho de texto trackeado puede variar 1–2px; menor.

## MISMATCH#7 · Chrome del mockup (`.nav`, `.stage`, `.seg`, `.chip-state`) — N/A (no se captura)

- **CSS:** `.app` grid `300px 1fr` con `.nav` rail + `.stage` (`L89-173`).
- **Realidad:** las capturas canónicas usan selector `.window` (ver
  `INDICE_CAPTURAS.csv` col `capture_selector`). El `.nav`/`.stage`/`.seg`/
  `.chip-state` son el navegador del *mockup tool*, **fuera** de `.window`.
- **Workaround:** el sidebar runtime (`NMSidebar`/`NMHubSidebar`) es UI propia del
  runtime y no debe compararse contra el `.nav` del mockup. No portar estilos del
  `.nav` del mockup al runtime como si fueran canónicos.
- **Impacto:** ninguno sobre las 86 keys; evita falsos objetivos.

## MISMATCH#8 · Texto bicolor / gradiente (`.brand__name b`) — WORKAROUND

- **CSS:** color parcial de texto (`<b>` con `color:var(--brand)`) y headings con
  gradiente (`L106`).
- **Qt:** QSS no aplica color por sub-span ni gradiente de texto.
- **Workaround:** `_GradientTextLabel` pinta el texto con brush/gradiente; o dos
  `QLabel` adyacentes.
- **Impacto:** WORKAROUND fiel.

## MISMATCH#9 · `text-overflow:ellipsis` — WORKAROUND

- **CSS:** `.lbl{text-overflow:ellipsis}` (`L141,817`).
- **Qt:** no hay property; se calcula con `QFontMetrics.elidedText`.
- **Workaround:** `NMElidedLabel` (`components/data.py`).
- **Impacto:** punto de corte puede diferir 1 glifo; menor.

## MISMATCH#10 · Hover glow exterior de botón primario — DECISIÓN-OWNER

- **CSS:** `.btn--primary:hover{box-shadow:var(--shadow-2)}` (`L294`).
- **Runtime:** `NMButton gradient` usa un **ring interno** en hover, no glow
  exterior (decisión documentada en el código, `buttons.py:241`).
- **Impacto:** los hovers no se capturan; bajo. No "corregir" hacia glow exterior.

## MISMATCH#11 · `rgba()` soft en QSS → variantes `*Solid` — WORKAROUND

- **CSS:** tonos translúcidos `--brand-soft:rgba(46,93,67,.13)` etc.
- **Qt:** algunas properties QSS no resuelven bien `rgba` sobre fondos variables;
  el resultado real depende del compositing.
- **Workaround:** `shared/theme.py` provee gemelos opacos pre-mezclados
  (`primarySoftSolid`, `accentSoftSolid`, `goldSoftSolid`, `roseSoftSolid`,
  `*SoftSolid`) calculados sobre el surface del tema. Para painter sí se usa rgba
  real (`v3c(alpha=...)`).
- **Impacto:** si se usa el solid correcto, fiel. Usar rgba donde el solid era
  necesario (o viceversa) produce divergencia de tono.

## MISMATCH#12 · `line-height` en textarea — WORKAROUND

- **CSS:** `textarea.input{line-height:1.55}` (`L305`).
- **Qt:** se controla con `QTextBlockFormat.setLineHeight(...)`, no por property.
- **Workaround:** aplicar line-height en `NMTextArea`.
- **Impacto:** alto total del textarea puede variar; afecta `registro-step3`.

## MISMATCH#13 · Chevron de combo — WORKAROUND

- **CSS:** flecha del select nativa del navegador.
- **Qt:** el truco `image:none` + borders renderiza un **cuadrado** sólido en Qt6.
- **Workaround:** `_qss_chevron_url()` genera un SVG chevron temable cacheado;
  `stylesheet_combobox()` lo usa.
- **Impacto:** WORKAROUND fiel; no volver al truco de bordes.

## MISMATCH#14 · Pseudo-elementos `::before`/`::after` con `content` — WORKAROUND

- **CSS:** barra activa del sidebar (`.nav__item.is-active::before`, `L138`),
  knob del toggle (`.themetoggle .dot::after`, `L155`), inner circle del ring
  (`.ring::before`, `L338`).
- **Qt:** QSS soporta `::before/::after` muy limitado (no `content` arbitrario
  ni posicionamiento libre).
- **Workaround:** pintar el elemento o añadir un sub-widget dedicado.
- **Impacto:** WORKAROUND fiel; no intentar replicar con QSS pseudo-elements.

## MISMATCH#15 · `conic-gradient` (progress ring) — WORKAROUND

- **CSS:** `.ring{background:conic-gradient(var(--brand) calc(p%), track)}`
  (`L336`).
- **Qt:** QSS no tiene `conic-gradient`.
- **Workaround:** `conical_arc_gradient()` + `QConicalGradient` en
  `NMModuleRing`/`NMCycleRing`/`NMFocusArc`.
- **Impacto:** WORKAROUND fiel; verificar con `vas_introspect --introspect`
  (familia GRADIENT).

## MISMATCH#16 · `@container` / `@media` queries — WORKAROUND

- **CSS:** `container-type:inline-size` + `@container (max-width:...)` ocultan
  columnas (`.pcol-mail`, `.cols-4→2`) (`L180,332,389,397,414`).
- **Qt:** no hay container queries; el layout responsivo es imperativo.
- **Workaround:** `shared/adaptive_layout_qt.py` y la lógica `fitScreen` del
  mockup definen breakpoints. A 960×600 fijo, la mayoría no dispara, pero el
  estado de columnas debe coincidir con el ancho capturado.
- **Impacto:** si el runtime oculta/muestra columnas distinto al breakpoint
  canónico → layout_drift real reparable.

## MISMATCH#17 · `backdrop-filter:blur()` — WORKAROUND

- **CSS:** `.modal-bg{backdrop-filter:blur(3px)}` (`L357`), `.surfaceGlass`.
- **Qt:** no existe `backdrop-filter`. Difuminar lo que está detrás requiere
  capturar y aplicar `QGraphicsBlurEffect`, costoso y frágil.
- **Workaround:** `window_overlay` con snapshot real de la pantalla trasera del
  modal + blur/dim/backdrop equivalente al mockup HTML. Dim sólido, blur
  excesivo o panel crop no son salidas válidas.
- **Impacto:** todo modal debe validar centrado, bbox, región de backdrop,
  blur/dim y dependencia de pantalla trasera con el auditor modal/backdrop.
  Si el modal falla por la pantalla trasera, se corrige esa pantalla/familia
  dependiente; no se tapa con opacidad o densidad inventada.

## MISMATCH#18 · `border-radius` + `box-shadow` en top-level window — WORKAROUND

- **CSS:** `.window{border-radius:28px; box-shadow:shadow-3; overflow:hidden}`
  (`L175-181`).
- **Qt:** una top-level window con bordes redondeados y sombra requiere ventana
  frameless + máscara/compositing del SO.
- **Workaround:** `NMWindowChrome` + `aplicar_captionbar_qt()` /
  `_aplicar_acento_win10()`. Las esquinas de la ventana son una flat-region
  citada en el handoff (`recuperar-acceso`).
- **Impacto:** esquinas/sombra de ventana pueden diferir levemente; parte es
  reparable (corners).

## MISMATCH#19 · Colores de semáforo del titlebar literales — WORKAROUND

- **CSS:** `.tb-dot.r{#E0695A} .y{#E0B23E} .g{#56B27A}` (`L196`) — literales, no
  tokens de tema.
- **Qt:** `_ChromeWinBtn` debe usar esos hex literales (no `danger/warning/
  success` del tema, que difieren).
- **Impacto:** usar tokens de tema en vez de los literales produce un tono
  distinto (citado: chrome amber dot en `recuperar-acceso`).

## MISMATCH#20 · Rasterización de texto Qt-vs-Chromium — IRREDUCIBLE

- **Realidad:** Qt (FreeType/DirectWrite) y Chromium hintean/antialias el texto
  distinto. En superficies **text-dense** (canon grayscale std < 35, p.ej. los
  forms 520×600 de Acceso) el SSIM global tiene un techo medido ~0.47–0.59 aun con
  alineación y color perfectos.
- **Gate:** el comparador ya es **density-aware** (windowed SSIM ≥ 0.65 y
  `changed_pixel_ratio ≤ 0.10` para esas superficies); ~0.077 del changed es
  AA de texto irreducible. Ver `VISUAL_REPAIR_HANDOFF.md` "Gate Calibration
  Snapshot".
- **Impacto:** **no** se cierra cambiando código de texto. Lo reparable en esas
  keys son las flat-regions (ring de foco, dot del chrome, sombra de card,
  esquinas, brandmark, líneas tinte), no el texto.

---

## Resumen por impacto

| Impacto | Mismatches |
|---|---|
| IRREDUCIBLE | #3 (parcial), #20 |
| WORKAROUND (paridad lograble) | #1, #2, #4, #5, #6, #8, #9, #11, #12, #13, #14, #15, #16, #17, #18 |
| DECISIÓN-OWNER | #10, #19, y opacity disabled de botón (matriz F4) |
| N/A (no se captura) | #7 |
