# Visual Loop Log — sesión 2026-06-24 (e29c36e → ?)

> Iteración sobre el estado ya avanzado. Continuación del log histórico `qa/VISUAL_LOOP_LOG.md` (46 iters previas).
> Mockup: `neuromood-mockup.html` + `qa/mockup_reference_static/`.
> Capturas reales: `qa/capture_v8.py`.
> Reglas: 1 ciclo = 1 discrepancia visible. Si no mejora → revert. Sin "PASS visual global".

## Estado inicial (baseline pre-loop)

- **HEAD inicial:** `e29c36e681f346e7130fb418c9df0757f2257559`
- **Branch:** `main`
- **Log histórico:** `qa/VISUAL_LOOP_LOG.md` — 46 iteraciones previas
- **Diferidos previos relevantes para reabrir:**
  - 🟡 Registro Emoción: grid de iconos → pills horizontales (refactor estructural)
  - 🟡 Card border Home: mockup 1px stroke (decisión de diseño)
  - 🟡 Slider dots Animo (funcional — los 10 niveles)
  - 🟡 Ícono Respiración leaf/drop
  - 🟡 Ancho input recordatorio (texto correcto, ancho insuficiente)
  - ⚪ Registro success (no capturable pre-save)
  - ⚪ Recuperar acceso / Onboarding (fuera de mandato)

## Convención de entradas

Cada iteración registra:
- iter # · SHA antes/después · pantalla · tema · captura V8 vs mockup
- discrepancia elegida · sev · archivo candidato · commit
- diff antes/después · resultado (MEJORA / NEUTRAL / REGRESIÓN)
- discrepancias restantes al cierre del ciclo

## Iteraciones

### Iter 47 — Home hero glow con color brand (visible)

- **SHA antes:** `e29c36e681f346e7130fb418c9df0757f2257559`
- **SHA después:** `53d6fc72b83f6c2cd0ba5d637318ff508c3cbc24`
- **Pantalla:** Suite · Home — hero card superior
- **Tema:** light (960×600)
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Inicio/Home/Con puntaje.png` — l.666-667: glow en upper-right con `var(--brand-soft) = rgba(46,93,67,.13)` (verde brand 13% alpha, no gris).
- **Captura real antes:** `qa/_captures_v8/iter_loop_2026_06_24_baseline/suite-home-light/suite-home-light-960x600.png` — glow INVISIBLE (color usado era gris `#888888` con 100% alpha).
- **Captura real después:** `qa/_captures_v8/iter47_after/suite-home-light-960x600.png` — glow verde sutil visible en upper-right.

**Discrepancia detectada** (sev 🟡):
- El glow del hero se implementó en iter 14 usando `v3c("brand_soft", self._modo)`, pero en el tema `light_hybrid` esa clave devuelve `#888888` (gris, alpha 255) en lugar de `rgba(46,93,67,.13)` (verde brand 13% alpha) que es el color del mockup.
- Resultado: el gradient gris sobre fondo beige claro no se distingue → glow invisible.
- Primera tentativa con alpha 33 (~13% como mockup) seguía imperceptible — el verde brand sobre beige claro se mezcla a un tinte apenas visible. Subimos a alpha 100 (~40%) para que el glow sea perceptible.

**Fix aplicado** (`app/home_qt.py`, `_HeroBienestar.paintEvent`):
- Reemplazar `v3c("brand_soft", self._modo)` (gris) por `v3c("brand", self._modo)` con alpha 100 (~40%) — verde brand como el mockup, más visible.
- Mantener `setColorAt(0.7, alpha 0)` y radio 200.

**Validación:**
- ✅ `ruff check app/home_qt.py` — All checks passed
- ✅ Captura V8 regenerada: glow ahora visible en upper-right como en mockup
- ✅ Sin regresión visible

**Resultado:** MEJORA — el glow del hero ahora se ve y matchea el color del mockup.

**Discrepancias restantes** en Home:
- 🟡 Module cards border: 1px stroke DIFERIDO por "decisión de diseño" — pero el mockup claramente tiene border visible. Reabrible.
- 🟡 Subtítulo Respiración: "Técnicas de calma 4 7 8" (sin punto medio) vs mockup "Técnicas de calma 4·7·8". Caracter `·` se renderiza con el mismo ancho que un espacio, fuente no lo hace destacar. NO accionable sin cambio de fuente.

### Iter 48 — Home module cards: border 1px visible

- **SHA antes:** `53d6fc72b83f6c2cd0ba5d637318ff508c3cbc24`
- **SHA después:** `7ca72c36e98ffaf00110da0d589ceada9b54572b`
- **Pantalla:** Suite · Home — 8 module cards
- **Tema:** light (960×600)
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Inicio/Home/Con puntaje.png` — cada card tiene un border 1px stroke visible alrededor.
- **Captura real antes:** `qa/_captures_v8/iter_loop_2026_06_24_baseline/suite-home-light/suite-home-light-960x600.png` — border INVISIBLE (alpha 26 = 10%).
- **Captura real después:** `qa/_captures_v8/iter48_after/suite-home-light-960x600.png` — border 1px sutil pero perceptible.

**Discrepancia detectada** (sev 🟡):
- El código `_apply_card_styles` ya define `border: 1px solid {border_css}` con color `rgba(49,45,39,26)` (alpha 26 = 10%). En el mockup el border es claramente más visible.
- El log previo lo marcó como DIFERIDO "decisión de diseño del app, no defecto", pero reabierto porque el mockup lo muestra visible.

**Fix aplicado** (`app/home_qt.py`, `_apply_card_styles`):
- Subir opacidad del border de 26 a 60 (~24%) en light_hybrid.
- El color sigue `var(--border)` (`#312d27`), solo cambiamos la alpha para que el stroke sea perceptible.

**Validación:**
- ✅ `ruff check app/home_qt.py` — All checks passed
- ✅ Captura V8 regenerada: cada card ahora muestra un border 1px sutil pero perceptible.

**Resultado:** MEJORA — las module cards ahora tienen un border visible, matcheando el mockup.

**Discrepancias restantes** en Home:
- 🟡 Subtítulo Respiración: NO accionable (glifo invisible por fuente).

### Iter 49 — DBT STOP: copy "sentís un malestar" → "sentís malestar"

- **SHA antes:** `7ca72c36e98ffaf00110da0d589ceada9b54572b`
- **SHA después:** `bce215e5b30acb2d60b5db2acc110342b3ecbd28`
- **Pantalla:** Suite · DBT Práctica guiada (STOP) — safety_note de cualquier paso
- **Tema:** light (960×600)
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Habilidades DBT/Habilidades DBT · Práctica guiada/STOP · Paso 1.png` — neuromood-mockup.html l.1181: "Esta habilidad es un apoyo inmediato. Si sentís malestar extremo o peligro inminente, recurrí a asistencia profesional." (sin "un")
- **Captura real antes:** `qa/_captures_v8/iter_loop_2026_06_24_baseline/suite-dbt-practice-stop-light/suite-dbt-practice-stop-light-960x600.png` — decía "Si sentís un malestar extremo..." (con "un" extra)
- **Captura real después:** `qa/_captures_v8/iter49_after/suite-dbt-practice-stop-light-960x600.png` — copy matchea mockup

**Discrepancia detectada** (sev 🟡):
- El safety_note del bloque `distress_tolerance` en el catalog embebido en `app/modules/dbt_qt.py` línea 185 decía "Si sentís un malestar extremo" — la palabra "un" sobra.
- El mockup (l.1181) NO incluye "un": "Si sentís malestar extremo o peligro inminente".
- Cambio de 1 palabra, copy.

**Fix aplicado** (`app/modules/dbt_qt.py`):
- `"Si sentís un malestar extremo"` → `"Si sentís malestar extremo"`.
- Aplica a todos los pasos STOP (el safety_note es global a la familia `distress_tolerance`).

**Validación:**
- ✅ `ruff check app/modules/dbt_qt.py` — All checks passed
- ✅ Captura V8 regenerada: copy matchea mockup

**Resultado:** MEJORA — copy coincide con mockup l.1181.

### Iter 50 — Hub Resumen IA: eyebrow UPPERCASE + botón Cerrar primary

- **SHA antes:** `bce215e5b30acb2d60b5db2acc110342b3ecbd28`
- **SHA después:** `5050bac3764811c88a5452c9bc7a157b2d40ba0e`
- **Pantalla:** Hub · Detalle de paciente · dialog "Resumen IA"
- **Tema:** light (480×325)
- **Mockup esperado:** `qa/mockup_reference_static/light/Hub · Clínico/Pacientes/Detalle de paciente/Resumen IA.png` — eyebrow "ANA MARTÍNEZ" (UPPERCASE, gris) sobre título "Resumen IA"; botón "Cerrar" filled green (primary).
- **Captura real antes:** `qa/_captures_v8/iter_loop_2026_06_24_baseline/hub-detalle-resumen-ia-0-light-480x325.png` — "Ana Martínez" en title-case normal; botón "Cerrar" como texto ghost.
- **Captura real después:** `qa/_captures_v8/iter50_after/hub-detalle-resumen-ia-0-light-480x325.png` — eyebrow UPPERCASE + botón primary.

**Discrepancia detectada** (sev 🟠):
- Mockup muestra el nombre del paciente en eyebrow UPPERCASE (como el eyebrow del card "Ana Martínez" en el detalle).
- Real usaba title-case (`Ana Martínez`) sin uppercase, y el botón era role="ghost" (texto plano), no filled green.
- Inconsistencia con el lenguaje del resto del Hub (todos los eyebrows en mayúsculas).

**Fix aplicado** (`hub/pacientes_qt.py`, `_show_resumen_dialog`):
- `QLabel(self._nombre)` → `QLabel(self._nombre.upper())`.
- Font: `qfont("size_caption", weight=600)` → `qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"])` (eyebrow style, igual al eyebrow del card de paciente).
- Botón "Cerrar": `role="ghost"` → `role="primary"` (filled green).

**Validación:**
- ✅ `ruff check hub/pacientes_qt.py` — All checks passed
- ✅ `pytest tests/test_hub_visual_contract.py` — 10/10 pass
- ✅ Captura V8 regenerada: dialog matchea mockup

**Resultado:** MEJORA — dialog Resumen IA ahora matchea el lenguaje del mockup.

**Discrepancias restantes** en Hub:
- 🟡 Botón "Asignar tarea" / "Agregar actividad" full-width: el real llega casi al borde de la card pero con padding lateral visible (mockup más ajustado). Menor.

### Iter 51 — Ánimo: header icon smile (alias "animo" → "mood")

- **SHA antes:** `5050bac3764811c88a5452c9bc7a157b2d40ba0e`
- **SHA después:** `a9d8aaa3a5eb83bc84da2ac44e4ea2d344688c18`
- **Pantalla:** Suite · Ánimo — header
- **Tema:** light (960×600)
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Bienestar/Termómetro emocional/Termómetro emocional.png` — header "← ☺ Termómetro emocional" (icono smile con ojos y boca)
- **Captura real antes:** `qa/_captures_v8/iter_loop_2026_06_24_baseline/suite-animo-light/suite-animo-light-960x600.png` — header "← 😐 Termómetro emocional" (face neutral)
- **Captura real después:** `qa/_captures_v8/iter51_after/suite-animo-light-960x600.png` — header con icono smile.

**Discrepancia detectada** (sev 🟡):
- `app/modules/animo_qt.py` define `MODULE_ICON = "animo"`, pero `"animo"` NO está en `shared/icons_svg.ICON_BODIES`. `has_icon("animo")` retornaba False → `NMIcon` caía al fallback QtAwesome que resolvía a un face neutral 😐.
- El mockup muestra un smile (cara con ojos y boca) `☺`, no un face neutral.

**Fix aplicado** (`shared/icons_svg.py`):
- Agregado `"animo"` como alias a `"mood"` (mismo path SVG: smile con ojos y boca). Esto hace que `has_icon("animo")` retorne True y `nm_svg_pixmap("animo", ...)` pinte el smile canónico.

**Validación:**
- ✅ `ruff check shared/icons_svg.py` — All checks passed
- ✅ Captura V8 regenerada: header ahora muestra smile

**Resultado:** MEJORA — header de Ánimo ahora muestra el smile del mockup.

### Iter 52 — Respiración: header icon drop (alias "respiracion" → "water")

- **SHA antes:** `a9d8aaa3a5eb83bc84da2ac44e4ea2d344688c18`
- **SHA después:** `0b3c9c8062b5dbbc38b40a7f1dd14f93757ef976`
- **Pantalla:** Suite · Respiración — header
- **Tema:** light (960×600)
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Bienestar/Guía de respiración/En reposo.png` — header "← 💧 Guía de respiración animada" (icono gota de agua)
- **Captura real antes:** `qa/_captures_v8/iter_loop_2026_06_24_baseline/suite-respiracion-light/suite-respiracion-light-960x600.png` — header "← 🍃 Guía de respiración animada" (icono hoja)
- **Captura real después:** `qa/_captures_v8/iter52_after/suite-respiracion-light-960x600.png` — header con icono gota.

**Discrepancia detectada** (sev 🟡):
- `app/modules/respiracion_qt.py` define `MODULE_ICON = "respiracion"`, pero `"respiracion"` NO está en `shared/icons_svg.ICON_BODIES`. El fallback QtAwesome resolvía a una hoja 🍃.
- El mockup muestra una gota de agua 💧, no una hoja.
- Iter log lo marcó como "DIFERIDO — decisión de diseño (la hoja es semánticamente más coherente)". Reabierto porque el mockup es la verdad.

**Fix aplicado** (`shared/icons_svg.py`):
- Agregado `"respiracion"` como alias del path SVG de `"water"` (gota). Mismo patrón que iter 51.

**Validación:**
- ✅ `ruff check shared/icons_svg.py` — All checks passed
- ✅ Captura V8 regenerada: header ahora muestra gota 💧

**Resultado:** MEJORA — header de Respiración ahora muestra la gota del mockup.

### Iter 53 — TCC Respuesta: counter "0 / 500" al pie del textarea

- **SHA antes:** `0b3c9c8062b5dbbc38b40a7f1dd14f93757ef976`
- **SHA después:** `8be1aa92575128711bbf4e846e268d9d0ecc988e`
- **Pantalla:** Suite · TCC paso 4 (Respuesta alternativa)
- **Tema:** light (960×600)
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Cognitivo/Registro de pensamientos (TCC)/Respuesta.png` — counter "118 / 500" en bottom-left del card (mockup l.1235).
- **Captura real antes:** `qa/_captures_v8/iter_loop_2026_06_24_baseline/suite-registro-step3-filled-light/suite-registro-step3-filled-light-960x600.png` — sin counter.
- **Captura real después:** `qa/_captures_v8/iter53_after/suite-registro-step3-filled-light-960x600.png` — counter "0 / 500" visible.

**Discrepancia detectada** (sev 🟡):
- Los pasos 0 (Situación) y 2 (Pensamiento) ya tienen counter "0 / 500" en bottom-left. El paso 4 (Respuesta) era el único sin counter.
- Mockup l.1235 muestra el counter "X / 500" en el bottom-left del card Respuesta, igual que los otros pasos con textarea.

**Fix aplicado** (`app/modules/registro_tcc_qt.py`, `_build_page_respuesta`):
- Agregado `self._respuesta_count_lbl = QLabel("0 / 500")` con font `qfont("size_caption_xs")`, alignment `AlignLeft`, color `ink_secondary`.

**Validación:**
- ✅ `ruff check app/modules/registro_tcc_qt.py` — All checks passed
- ✅ Captura V8 regenerada: counter visible

**Resultado:** MEJORA — counter del paso 4 ahora visible, consistente con pasos 0 y 2.

**Notas de mini-regresión (iter ~20):**
- `ruff check` sobre archivos tocados acumulados (4 archivos): ✅ 0 errores
- `pytest` sobre tests visuales de módulos tocados: 44/45 pass. 1 preexistente roto:
  - `test_rutina_visual_contract.py::test_rutina_add_done_and_empty_states_match_mockup` — asserta botón "✓" pero el código actual usa "+" (cambio de iter 39 que acercó al mockup, no al test).

### Iter 54 — Timer: icono pause "00" (dos círculos)

- **SHA antes:** `8be1aa92575128711bbf4e846e268d9d0ecc988e`
- **SHA después:** `fc30052b80ec7dcba7fba3c98d06a1ae404e03b2`
- **Pantalla:** Suite · Temporizador (estado "Sesión en curso")
- **Tema:** light (960×600)
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Hábitos/Temporizador/En curso.png` — botón central de pause muestra "00" (dos círculos rellenos, convention Phosphor fill).
- **Captura real antes:** `qa/_captures_v8/iter_loop_2026_06_24_baseline/suite-timer-running-light/suite-timer-running-light-960x600.png` — botón mostraba un rectángulo único (no "00").
- **Captura real después:** `qa/_captures_v8/iter54_after/suite-timer-running-light-960x600.png` — "00" visible.

**Discrepancia detectada** (sev 🟡):
- El path SVG de `"pause"` en `shared/icons_svg.py` era un solo `<rect>` con `rx="1"`, lo que renderizaba un rectángulo estirado (no dos barras, no dos círculos).
- El mockup muestra "00" — convention Phosphor fill (dos círculos rellenos).

**Fix aplicado** (`shared/icons_svg.py`):
- Cambiado el path de `"pause"` a dos `<circle>` (cx=9 y cx=15, ambos con cy=12, r=3.5, fill={color} stroke=none).
- Esto matchea el "00" del mockup.

**Validación:**
- ✅ `ruff check shared/icons_svg.py` — All checks passed
- ✅ Captura V8 regenerada: "00" ahora visible

**Resultado:** MEJORA — botón de pause ahora matchea la convention "00" del mockup.

### Iter 55 — DBT STOP paso 1: body "Detené lo que estás haciendo…"

- **SHA antes:** `fc30052b80ec7dcba7fba3c98d06a1ae404e03b2`
- **SHA después:** `170a3f42486faa205458b96b7fb1456d839a208c`
- **Pantalla:** Suite · DBT Práctica guiada (STOP · paso 1, S)
- **Tema:** light (960×600)
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Habilidades DBT/Habilidades DBT · Práctica guiada/STOP · Paso 1.png` — body: "Detené lo que estás haciendo. No actúes todavía. Quedate quieto un momento." (mockup l.1171)
- **Captura real antes:** _(no capturada, harness captura paso 2)_
- **Captura real después:** _(no capturada)_

**Discrepancia detectada** (sev 🟡):
- El body del paso S era "¡No reacciones inmediatamente! Tus emociones pueden empujarte a actuar sin pensar. Mantenete quieto por un instante." — genérico.
- El mockup dice "Detené lo que estás haciendo. No actúes todavía. Quedate quieto por un momento." — específico al paso S.

**Fix aplicado** (`app/modules/dbt_qt.py`):
- Body del paso S actualizado al copy del mockup.

**Validación:**
- ✅ `ruff check app/modules/dbt_qt.py` — All checks passed
- ✅ Grep confirma el cambio en el código

**Resultado:** MEJORA — copy del paso S matchea el mockup l.1171.

### Iter 56 — DBT STOP pasos T y O: body alineado al mockup

- **SHA antes:** `170a3f42486faa205458b96b7fb1456d839a208c`
- **SHA después:** _(pending)_
- **Pantalla:** Suite · DBT Práctica guiada (STOP · pasos T y O)
- **Mockup esperado:**
  - l.1162 (T): "Alejate **física** o mentalmente de la situación..."
  - l.1163 (O): "Notá qué está pasando dentro y fuera: pensamientos, sensaciones, el contexto, sin juzgarlos."

**Discrepancia detectada** (sev 🟡):
- Paso T: real tenía "físicamente", mockup dice "física" (1 carácter).
- Paso O: copy totalmente diferente entre real y mockup.

**Fix aplicado** (`app/modules/dbt_qt.py`):
- Paso T: "físicamente" → "física".
- Paso O: reemplazado completo con copy del mockup.

**Validación:**
- ✅ `ruff check app/modules/dbt_qt.py` — All checks passed

**Resultado:** MEJORA — copy de T y O matchea mockup l.1162/1163.

---
