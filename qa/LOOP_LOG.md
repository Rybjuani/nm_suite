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
- **SHA después:** _(pending)_
- **Pantalla:** Suite · DBT Práctica guiada (STOP) — safety_note de cualquier paso
- **Tema:** light (960×600)
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Habilidades DBT/Habilidades DBT · Práctica guiada/STOP · Paso 1.png` — neuromood-mockup.html l.1181: "Esta habilidad es un apoyo inmediato. Si sentís malestar extremo o peligro inminente, recurrí a asistencia profesional." (sin "un")
- **Captura real antes:** `qa/_captures_v8/iter_loop_2026_06_24_baseline/suite-dbt-practice-stop-light/suite-dbt-practice-stop-light-960x600.png` — decía "Si sentís un malestar extremo..." (con "un" extra)
- **Captura real después:** _(pending)_

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

---
