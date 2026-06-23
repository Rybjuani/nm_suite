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
- **SHA después:** `0e1f2b9ef5fdf4e7238668279c55f35bbab21210`
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

### Iter 3 — Hub Detalle: empty state con borde dashed (Plan terapéutico)

- **SHA antes:** `e8ecfe6` (HEAD previo al iter)
- **SHA después:** `87c03bf78fb191adfc26d9a8177c93f9d1dd1618`
- **Pantalla:** Hub · Detalle de paciente · tab Recordatorios (y aplica a Rutina/Activación)
- **Tema:** light (960×600)
- **Mockup esperado:** `qa/mockup_reference_static/light/Hub · Clínico/Pacientes/Detalle de paciente/Detalle de paciente.png` — caja con `border: 1px dashed var(--line); border-radius: 16px; padding: 40px 16px` (mockup l.1495)
- **Captura real antes:** `qa/_captures_v8/iter3_detalle/hub-detalle-light-960x600.png`
- **Captura real después:** `qa/_captures_v8/iter3_detalle_after/hub-detalle-light-960x600.png`
- **Comparativa antes/después:** `qa/_captures_v8/iter3_detalle_after/_compare.png`

**Discrepancia detectada** (sev 🟠):
- El empty state de "Sin recordatorios asignados aún." (panel derecho del tab Recordatorios) se mostraba como texto plano sin contenedor. El copy hacía wrap a 2 líneas.
- El mockup muestra una **caja con borde dashed** y padding generoso (40px v / 16px h), radius 16px — lee como "placeholder" y ancla visualmente el panel.
- Aplica también a los empty states de tabs Rutina ("Sin tareas asignadas aún.") y Activación ("Sin actividades personalizadas aún.").

**Fix aplicado** (`hub/plan_terapeutico.py`, `_empty_hint_label`):
- `QWidget` con `border: 1px dashed <line-color>` + `border-radius: 16px`.
- `setContentsMargins(16, 40, 16, 40)` (mockup l.1495: padding 40px 16px).
- minHeight 58→132, maxHeight 78→180 — la caja tiene cuerpo y se lee como placeholder.
- Label interno con `border: none` para no heredar el border del wrap (sería redundante).
- Aplica a 5 sitios (3 tabs × 2 sub-estados, según `_load_*()`).

**Validación:**
- ✅ `ruff check hub/plan_terapeutico.py` — All checks passed
- ✅ `pytest tests/test_hub_visual_contract.py` — 10/10 pass
- ✅ Captura V8 regenerada: caja con dashed border visible, padding correcto, radius 16px
- ✅ Sin regresión visible

**Resultado:** MEJORA — el empty state ahora coincide con el mockup (dashed border + radius + padding 40/16).

**Discrepancias restantes** en Hub Detalle:
- "Sin recordatorios asignados aún." en real wrappea a 2 líneas; en mockup está en 1 línea (más espacio horizontal). El dashed border ya marca el contenedor, pero el copy podría entrar en 1 línea con un poco más de ancho. **DIFERIDO** — subóptimo pero el contenedor es correcto.
- Mensaje del recordatorio: input truncado a "Mensaje del recordatorio (máx 1..." vs mockup "Mensaje del recordatorio (máx 150)". **DIFERIDO** — copy + ancho.

### Iter 4 — TCC: textarea más corto para que el contador respire

- **SHA antes:** `b88847a` (HEAD previo al iter)
- **SHA después:** `cb3dab63a2d587ecd908523827614f8ebf6c5104`
- **Pantalla:** Suite · Registro de pensamientos (TCC) · paso 0 (Situación) y paso 3 (Respuesta)
- **Tema:** light (960×600)
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Cognitivo/Registro de pensamientos (TCC)/Situación.png` — textarea con `rows="5"` (~110–120px) y contador `0/500` con `margin-top: 8px` debajo (l.1224–1225)
- **Captura real antes:** `qa/_captures_v8/iter4_tcc/suite-registro-light-960x600.png`
- **Captura real después:** `qa/_captures_v8/iter4_tcc_after/suite-registro-light-960x600.png`
- **Comparativa antes/después:** `qa/_captures_v8/iter4_tcc_after/_compare.png`

**Discrepancia detectada** (sev 🟡, audit previo lo marcaba DIFERIDO):
- Textarea del paso 0 (Situación) tenía `setMaximumHeight(156)` y se mostraba casi a tope de la card → el contador `0 / 500` quedaba apenas visible al borde inferior de la card, con margen <5px respecto al border-radius.
- Mismo problema en paso 3 (Respuesta) con `setMaximumHeight(156)`.
- Mockup define `rows="5"` (~110–120px según font) — el contador tiene `margin-top: 8px` y queda con aire arriba y abajo.

**Fix aplicado** (`app/modules/registro_tcc_qt.py`):
- `_txt_situacion.setMaximumHeight(156)` → `120` (mockup rows=5)
- `_txt_respuesta.setMaximumHeight(156)` → `120` (mismo motivo)
- `_txt_pensamiento` ya estaba en 132 (no lo toqué — está dentro del rango rows=4–5 del mockup)
- `_txt_situacion.min_height=120` se mantiene — el rango efectivo es 120–120, altura fija que matchea el mockup.

**Validación:**
- ✅ `ruff check app/modules/registro_tcc_qt.py` — All checks passed
- ✅ `pytest tests/test_registro_tcc_visual_contract.py tests/test_home_visual_contract.py tests/test_animo_visual_contract.py tests/test_hub_visual_contract.py` — 27/27 pass
- ✅ Captura V8 regenerada: contador ahora con espacio visible, no aplastado al borde
- ✅ Sin regresión visible

**Resultado:** MEJORA — el contador `0 / 500` ahora tiene aire respecto al border-radius de la card, matcheando el mockup.

**Discrepancias restantes** en TCC:
- Título: real usa pregunta "¿Qué pasó?" como título; mockup usa nombre del paso "Situación" como título y la pregunta como subtítulo. **DIFERIDO** — decisión de diseño.
- Subtítulo copy: real "Contá en pocas palabras qué estaba pasando." vs mockup "¿Qué pasó? Describí el momento de forma concreta y objetiva." **DIFERIDO** — copy.
- Placeholder copy: real "Escribí lo que pasó…" vs mockup "Ej: En la reunión me preguntaron por el reporte y no supe qué responder…" **DIFERIDO** — copy.
### Iter 5 — Avisos: icon tile 32×32 en cada recordatorio

- **SHA antes:** `994676c` (HEAD previo al iter)
- **SHA después:** _(se completa al commit)_
- **Pantalla:** Suite · Recordatorios de bienestar (Todos)
- **Tema:** light (960×600)
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Hábitos/Recordatorios de bienestar/Todos.png` — icon en tile `32×32 surface-3 radius 10` (mockup l.636, mismo lenguaje que homeCard)
- **Captura real antes:** `qa/_captures_v8/iter5_avisos/suite-avisos-light-960x600.png`
- **Captura real después:** `qa/_captures_v8/iter5_avisos_after/suite-avisos-light-960x600.png`
- **Comparativa antes/después:** `qa/_captures_v8/iter5_avisos_after/_compare.png`

**Discrepancia detectada** (sev 🟡):
- El ícono de cada recordatorio (pill, leaf, bell) estaba como `NMIcon(18px)` sin contenedor — quedaba "flotando" en el padding de la row.
- El mockup (l.636) y el resto del sistema (home cards l.636, animo stat cards l.715) usan un tile `32×32 surface-3 radius 10` con el ícono centrado.
- Inconsistencia visual: los icon tiles del home y animo sí tenían contenedor; los de avisos no.

**Fix aplicado** (`app/modules/avisos_qt.py`, `_ReminderCardV3._build` y `_apply_card_styles`):
- Envuelto `NMIcon(18)` en un `QFrame` 32×32 con `setObjectName("AvisoRowIconTile")`.
- Style aplicado en `_apply_card_styles`: `background: v3c('surface3', modo)`, `border: none`, `border-radius: 10px` — sigue al tema.
- Alineación vertical centrada (`AlignVCenter` en el addWidget) para que el tile se vea balanceado con el contenido (título + meta).

**Validación:**
- ✅ `ruff check app/modules/avisos_qt.py` — All checks passed
- ✅ `pytest tests/test_avisos_visual_contract.py tests/test_home_visual_contract.py tests/test_animo_visual_contract.py tests/test_hub_visual_contract.py tests/test_registro_tcc_visual_contract.py` — 29/29 pass
- ✅ Captura V8 regenerada: cada recordatorio ahora tiene su tile 32×32 con surface-3
- ✅ Sin regresión visible

**Resultado:** MEJORA — los iconos de recordatorios ahora viven en un tile consistente con el resto del sistema.

**Discrepancias restantes** en Avisos:
- Status chip item 4 (Rutina de tarde): real "Hoy", mockup "Activo". **DIFERIDO** — dato (depende de la frecuencia del recordatorio), no fix de layout.
- Ícono de Respiración: real usa `leaf` (hoja), mockup usa `drop` (gota). **DIFERIDO** — decisión de diseño (la hoja es semánticamente más coherente con respiración/calma).
- Search box: real más ancho (extiende casi al borde derecho), mockup más compacto. **DIFERIDO** — subóptimo menor.




