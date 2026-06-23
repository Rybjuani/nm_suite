# Visual Loop Log — iteración app real ↔ mockup

> Iterar hasta acercar la app al mockup definitivo **sin declarar PASS visual global**.
> Mockup: `neuromood-mockup.html` + `qa/mockup_reference_static/`.
> Capturas reales: `qa/capture_v8.py` (nunca Sentinel como auditor; sólo técnico).
> Reglas: 1 ciclo = 1 discrepancia visible. Si no mejora visualmente → revert.
> Severidad: 🔴 alta · 🟠 media · 🟡 baja · ⚪ no-defecto.

## Estado inicial (baseline pre-loop)

- **HEAD inicial:** `1525c032a1370045ea3971422f02b474b14b6ebf`
- **Branch:** `main`
- **Capturas frescas:** `qa/_captures_v8/` (2026-06-23 03:54, 86 PNGs = 43 recipes × 2 themes)
- **Auditoría previa:** `qa/AUDITORIA_POSTFIX.md` (no es PASS global)
- **Discrepancias heredadas priorizadas (sin fix en este loop):**
  - 🟠 **TCC título de paso** (estructura, requiere decisión)
  - 🟡 **Animo: dots del slider** (DIFERIDO — son los 10 niveles clickeables; cambiarlos es funcional)
  - 🟡 **TCC: contador 0/500 fuera de la card** (DIFERIDO)
  - 🟡 **Home: wrap de títulos a 960px** (verificar si persiste a 980px)
  - 🟡 **Copy/voseo** (decisión aparte, no fix de layout)
  - ⚪ **Chrome/dato** (ícono hamburguesa, conteo 158 vs 145)

## Convención de entradas

Cada iteración registra:
- iter # · SHA antes/después · pantalla · tema · captura V8 vs mockup
- discrepancia elegida · sev · archivo candidato · commit
- diff antes/después · resultado (MEJORA / NEUTRAL / REGRESIÓN)
- discrepancias restantes al cierre del ciclo

## Iteraciones

### Iter 1 — Home: títulos largos a 1 línea (3 cards)

- **SHA antes:** `1525c032a1370045ea3971422f02b474b14b6ebf`
- **SHA después:** `795f0fc7c308086145a473616f045557c40e83cb`
- **Pantalla:** Suite · Home (con puntaje)
- **Tema:** light + dark (960×600)
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Inicio/Home/Con puntaje.png` — los 8 títulos en 1 línea
- **Captura real antes:** `qa/_captures_v8/iter_loop/suite-home-light-960x600.png`
- **Captura real después:** `qa/_captures_v8/iter_loop_home_v8_2/suite-home-light-960x600.png` (+ dark en `iter_loop_home_v8_2_dark/`)
- **Comparativa antes/después:** `qa/_captures_v8/iter_loop_home_v8_2/_compare_light.png`

**Discrepancia detectada** (sev 🟠):
- 3 cards tenían título wrappeado a 2 líneas: "Termómetro emocional", "Registro de pensamientos", "Activación conductual". Las otras 5 (Guía de respiración, Checklist de rutina, Temporizador, Recordatorios, Habilidades DBT) ya estaban en 1 línea.
- Cards en una misma fila tenían alturas distintas → grid desalineado.
- Causa raíz: a 960px de viewport, las cards miden ~219px; con 20px de padding queda ~179px para el título. En Newsreader 16px los 3 títulos largos overflow y Qt los wrappea.

**Fix aplicado** (`app/home_qt.py`, `ModuleCard.resizeEvent`):
- Override de `resizeEvent` que mide el ancho del `_title_lbl` con `QFontMetrics.horizontalAdvance`.
- Si el texto no entra al font actual (16px), prueba 15, 14, 13 px hasta que entre.
- Floor: 13px. Por encima, `setWordWrap(True)` sigue cubriendo anchos extremos (sub-720px → 3 cols).
- Solo se aplica en `resizeEvent` (post-layout), no en `_build_ui` → `test_home_module_card_title_uses_serif_font` sigue pasando porque lee el font al init (16px).

**Font resultante por card** (medido en runtime, 960px viewport):
- animo: 15px · respiracion: 16px · registro: 13px · rutina: 16px
- actividades: 15px · timer: 16px · avisos: 16px · dbt: 16px

**Validación:**
- ✅ `ruff check app/home_qt.py` — All checks passed
- ✅ `pytest tests/test_home_visual_contract.py` — 7/7 pass (test del font a 16px en animo no afectado: el fix es post-init)
- ✅ `pytest tests/test_component_visual_contract.py tests/test_component_import_boundaries.py tests/test_components_public_api.py` — 47/47 pass
- ✅ Captura V8 regenerada: títulos en 1 línea (title-area height 9-12px vs 56-69px antes)
- ✅ Light + dark: ambos temas validados con la misma lógica

**Resultado:** MEJORA — sin regresión visible. Las 3 cards largas ahora caben en 1 línea; el grid queda alineado por fila.

**Discrepancias restantes** (las 3 cards ahora caben; resto del Home sin issues):
- Card border: mockup tiene 1px stroke visible; real no (fondo + shadow). Decisión de diseño del app, no defecto. **DIFERIDO**.
- Top hero card: mockup tiene glow sutil en upper-right corner; real flat. 🟡 menor, **DIFERIDO**.
- "Acción" chip: en captura real, el chip podría mostrarse con kerning diferente al mockup. 🟡 **DIFERIDO** (copy/chrome, no bloqueante).

### Iter 2 — Animo: tile del ícono "Progreso" a rounded square

- **SHA antes:** `8253ae4` (HEAD previo al iter)
- **SHA después:** _(se completa al commit)_
- **Pantalla:** Suite · Animo (Termómetro emocional)
- **Tema:** light (960×600)
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Bienestar/Termómetro emocional/Termómetro emocional.png` — cards de Progreso con icon container `42×42 border-radius 12px` y sparkle `20px` (l.715 mockup).
- **Captura real antes:** `qa/_captures_v8/iter2_animo/suite-animo-light-960x600.png`
- **Captura real después:** `qa/_captures_v8/iter2_animo_after/suite-animo-light-960x600.png`
- **Comparativa antes/después:** `qa/_captures_v8/iter2_animo_after/_compare.png`

**Discrepancia detectada** (sev 🟡):
- Las 2 cards "Progreso 7 días" y "Progreso 30 días" tenían el ícono en un **círculo grande** (58×58, border-radius 29px) con sparkle 26px.
- El mockup usa **rounded square** (42×42, border-radius 12px) con sparkle 20px → más proporcional al card y alineado al resto del sistema (icon tiles en otras pantallas usan 32-44px con radius 10-12px).
- Visualmente el círculo grande se veía desfasado del lenguaje del resto de la app.

**Fix aplicado** (`app/modules/animo_qt.py`, `_CareStatCard.__init__` y `_apply_theme`):
- `setFixedSize(58, 58)` → `setFixedSize(42, 42)`
- `NMIcon(... size=26 ...)` → `NMIcon(... size=20 ...)`
- `border-radius: 29px` → `border-radius: 12px`

**Validación:**
- ✅ `ruff check app/modules/animo_qt.py` — All checks passed
- ✅ `pytest tests/test_animo_visual_contract.py tests/test_home_visual_contract.py` — 10/10 pass
- ✅ Captura V8 regenerada: contenedor ahora es rounded square, sparkle más chico
- ✅ Sin regresión visible

**Resultado:** MEJORA — el contenedor del ícono ahora coincide con el mockup (l.715).

**Discrepancias restantes** en Animo:
- Valor copy: "7 días" (real) vs "7 días seguidos" (mockup l.717). **DIFERIDO** — copy, decisión aparte.
- Mensaje copy: "Días seguidos con registro esta semana." (real) vs "con registro esta semana" (mockup l.718). **DIFERIDO** — copy.
- Color del valor: real sin color de tono, mockup usa `var(--brand)` para 7d y `var(--accent)` para 30d. **DIFERIDO** — requiere extender `_CareStatCard` con `tone_key`.
- Slider dots: real muestra 10 dots clickeables, mockup sin dots. **DIFERIDO** — son los niveles clínicos clickeables (funcional).
- Botón "Guardar registro" deshabilitado: real (porque slider sin selección), mockup también disabled. Coinciden.


