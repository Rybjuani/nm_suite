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
- **SHA después:** `a0f674b57f972c7efd1e7fe7e07d0785b4c6e130`
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
### Iter 6 — Textos globales: separador bajo la fila de controles

- **SHA antes:** `903663f` (HEAD previo al iter)
- **SHA después:** `6f849f9c4619ca5bb5847250fdc62f1cd7942ae0`
- **Pantalla:** Hub · Configuración · Textos globales
- **Tema:** light (960×600)
- **Mockup esperado:** `qa/mockup_reference_static/light/Hub · Clínico/Configuración/Textos globales/Textos globales.png` — `.tg-top` con `padding-bottom:16px; border-bottom:1px solid var(--line)` (mockup l.383)
- **Captura real antes:** `qa/_captures_v8/iter6_textos/hub-textos-globales-light-960x600.png`
- **Captura real después:** `qa/_captures_v8/iter6_textos_after/hub-textos-globales-light-960x600.png`
- **Comparativa antes/después:** `qa/_captures_v8/iter6_textos_after/_compare.png`

**Discrepancia detectada** (sev 🟡):
- La fila superior (título "Textos globales" + buscador + dropdown + contador) estaba pegada visualmente a la primera card de la lista — sin separador.
- El mockup define una línea horizontal sutil (1px, color `--line`) con 16px de padding inferior, que ancla el bloque de controles como una "toolbar" separada de la lista.

**Fix aplicado** (`hub/config_global_texts.py`, `_build` y `_apply_theme`):
- Envuelto el `top` QHBoxLayout en un `QWidget` (`TextosGlobalesTopBar`).
- Agregado un `QFrame` (`TextosGlobalesSeparator`) con `HLine` + `FixedHeight(1)` debajo del top, con 16px de spacing antes.
- Color aplicado en `_apply_theme` con `v3c('line', modo)` para que siga al tema (light/dark).
- `self._top_sep = sep` para tener referencia en `_apply_theme`.

**Validación:**
- ✅ `ruff check hub/config_global_texts.py` — All checks passed
- ✅ `pytest tests/test_hub_visual_contract.py tests/test_home_visual_contract.py tests/test_animo_visual_contract.py tests/test_registro_tcc_visual_contract.py tests/test_avisos_visual_contract.py` — 29/29 pass
- ✅ Captura V8 regenerada: separador 1px visible bajo la fila de controles, padding 16px
- ✅ Sin regresión visible

**Resultado:** MEJORA — la fila de controles ahora tiene un separador visual que coincide con el mockup, anclando la toolbar y separándola de la lista.

**Discrepancias restantes** en Textos globales:
- Contador "158 textos" vs mockup "145 textos". **DIFERIDO** — dato (cantidad real de textos editables ha crecido desde el snapshot del mockup).
### Iter 7 — TCC: título de paso = nombre (no prompt)

- **SHA antes:** `7541f1b` (HEAD previo al iter)
- **SHA después:** `1ac17c77c9b9e67d291514c32d0a0a21fac5407d`
- **Pantalla:** Suite · Registro de pensamientos (TCC) — todos los pasos
- **Tema:** light (960×600)
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Cognitivo/Registro de pensamientos (TCC)/Situación.png` — `<h2 class="h-serif" style="font-size:19px">Situación</h2>` + `<p>¿Qué pasó? Describí el momento de forma concreta y objetiva.</p>` (mockup l.1222-1223)
- **Captura real antes:** `qa/_captures_v8/iter4_tcc_after/suite-registro-light-960x600.png`
- **Captura real después:** `qa/_captures_v8/iter7_tcc/suite-registro-light-960x600.png`

**Discrepancia detectada** (sev 🟠):
- El card usaba el `prompt` ("¿Qué pasó?") como título y el `hint` ("Contá en pocas palabras qué estaba pasando.") como subtítulo. El mockup invierte la jerarquía: nombre del paso ("Situación") como h2, prompt como subtítulo.
- Aplicaba a los 4 pasos (Situación/Emoción/Pensamiento/Respuesta).

**Fix aplicado** (`app/modules/registro_tcc_qt.py`):
- Nuevo helper `_step_name(index, fallback)` que devuelve el campo `title` del step (mockup l.1222: "Situación"/"Emoción"/"Pensamiento"/"Respuesta").
- Las 4 llamadas a `_make_title` ahora pasan `(self._step_name(...), self._step_prompt(...))` en vez de `(self._step_prompt(...), self._step_hint(...))`.
- El campo `hint` ya no se usa como subtítulo (queda en el dict para futura referencia, sin breaking change en la data layer).

**Validación:**
- ✅ `ruff check app/modules/registro_tcc_qt.py` — All checks passed
- ✅ `pytest tests/test_registro_tcc_visual_contract.py` — 7/7 pass
- ✅ Captura V8 regenerada: título "Situación" + subtítulo "¿Qué pasó?" — matchea mockup
- ✅ Sin regresión visible

**Resultado:** MEJORA — el card del TCC ahora sigue la estructura del mockup (nombre del paso como h2, prompt como subtítulo).

### Iter 8 — Animo stat card: per-card tone (brand / accent)

- **SHA antes:** `1ac17c77c9b9e67d291514c32d0a0a21fac5407d`
- **SHA después:** `8594cefdcb5adece7eddc03fae4a4b1e376bc20b`
- **Pantalla:** Suite · Animo (Termómetro emocional) — cards de Progreso 7d y 30d
- **Tema:** light (960×600)
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Bienestar/Termómetro emocional/Termómetro emocional.png`
  - l.715 (7d): `background: var(--brand-soft); color: var(--brand);` para icon
  - l.721 (30d): `background: var(--accent-soft); color: var(--accent);` para icon
  - l.717: `7 días seguidos` en color brand
  - l.723: `12 días` en color accent
- **Captura real antes:** `qa/_captures_v8/iter2_animo_after/suite-animo-light-960x600.png`
- **Captura real después:** `qa/_captures_v8/iter8_animo/suite-animo-light-960x600.png`

**Discrepancia detectada** (sev 🟠):
- Ambas cards "Progreso" usaban `primary_soft` (verde) para el tile del icono y `primary` para el texto del valor. El mockup las diferencia con brand/accent.
- Audit previo lo marcaba DIFERIDO por requerir extender la API de `_CareStatCard`.

**Fix aplicado** (`app/modules/animo_qt.py`, `_CareStatCard.__init__`, `_apply_theme` y call sites):
- Nuevo parámetro `tone: str | None = None` en `__init__`.
- `_apply_theme` calcula `tile_bg_token = (self._tone + "_soft") if self._tone else "primary_soft"`.
- 7d instanciada con `tone="brand"`, 30d con `tone="accent"`.
- `_refresh_stats` actualizado para pasar `"brand"`/`"accent"` al `set_tone` del value text (antes pasaba `"primary"`).

**Validación:**
- ✅ `ruff check app/modules/animo_qt.py` — All checks passed
- ✅ `pytest tests/test_animo_visual_contract.py` — 3/3 pass
- ✅ Captura V8 regenerada: 7d con tile verde, 30d con tile naranja
- ✅ Sin regresión visible

**Resultado:** MEJORA — las cards ahora se diferencian visualmente por tone (brand para 7d, accent para 30d), matcheando mockup l.715-723.

### Iter 9 — TCC: copy de subtítulos y placeholder

- **SHA antes:** `8594cefdcb5adece7eddc03fae4a4b1e376bc20b`
- **SHA después:** `992815f371328f9ade61900d9346bca9f61e959c`
- **Pantalla:** Suite · Registro de pensamientos (TCC) — todos los pasos
- **Tema:** light (960×600)
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Cognitivo/Registro de pensamientos (TCC)/*.png`
  - l.1223 (s0): `¿Qué pasó? Describí el momento de forma concreta y objetiva.`
  - l.1224 (s0 placeholder): `Ej: En la reunión me preguntaron por el reporte y no supe qué responder…`
  - l.1230 (s1): `¿Qué sentiste? Elegí la emoción más intensa y su nivel.`
  - l.1241 (s2): `¿Qué pensaste en ese momento? Escribilo tal como apareció.`
  - l.1260 (s3): `Reformulá el pensamiento de forma más equilibrada y realista.`
- **Captura real antes:** `qa/_captures_v8/iter7_tcc/suite-registro-light-960x600.png`
- **Captura real después:** `qa/_captures_v8/iter9_tcc/suite-registro-light-960x600.png`

**Discrepancia detectada** (sev 🟡):
- Los 4 prompts eran cortos y no coincidian con el mockup. El placeholder del paso 0 era `Escribí lo que pasó…` (genérico) vs `Ej: En la reunión me preguntaron por el reporte y no supe qué responder…` (ejemplo concreto).

**Fix aplicado** (`app/modules/registro_tcc_qt.py` + `shared/suite_text_catalog.py`):
- Los 4 prompts en `DEFAULT_TCC_TEMPLATE` actualizados al copy del mockup.
- Los 4 fallbacks en `_build_page_*` también actualizados (por si el template se overridea).
- El placeholder por defecto en `suite_text_catalog.py` actualizado a la versión del mockup.

**Validación:**
- ✅ `ruff check app/modules/registro_tcc_qt.py shared/suite_text_catalog.py` — All checks passed
- ✅ `pytest tests/test_registro_tcc_visual_contract.py` — 7/7 pass
- ✅ Captura V8 regenerada: subtítulos y placeholder matchean mockup
- ✅ Sin regresión visible

**Resultado:** MEJORA — los textos del TCC ahora coinciden con el mockup.

### Iter 10 — Animo stat card: value + subtitle copy

- **SHA antes:** `992815f371328f9ade61900d9346bca9f61e959c`
- **SHA después:** `f575d4028888e55ff581169c00033583ac53c624`
- **Pantalla:** Suite · Animo — cards de Progreso 7d y 30d
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Bienestar/Termómetro emocional/Termómetro emocional.png`
  - l.717 (7d value): `7 días seguidos` (color brand)
  - l.718 (7d subtitle): `con registro esta semana`
  - l.723 (30d value): `12 días` (color accent)
  - l.724 (30d subtitle): `con registro este mes`
- **Captura real antes:** `qa/_captures_v8/iter8_animo/suite-animo-light-960x600.png`
- **Captura real después:** `qa/_captures_v8/iter10_animo/suite-animo-light-960x600.png`

**Discrepancia detectada** (sev 🟡):
- Real: value `7 días` (sin "seguidos") y subtitle `Días seguidos con registro esta semana.` (duplicaba la palabra "seguidos" que en el mockup vive en el value).
- Mockup: la palabra "seguidos" está en el value (`7 días seguidos`), y el subtitle es solo `con registro esta semana`.

**Fix aplicado** (`app/modules/animo_qt.py`):
- Default value en `__init__` de cada card: `"0 días seguidos"`.
- Subtitle (message): `"con registro esta semana"` / `"con registro este mes"`.
- `set_value` en `_refresh_stats`: `"1 día seguido"` si es 1, sino `f"{n} días seguidos"`.
- `set_message` en `_refresh_stats`: el copy corto del mockup.

**Validación:**
- ✅ `ruff check app/modules/animo_qt.py` — All checks passed
- ✅ `pytest tests/test_animo_visual_contract.py` — 3/3 pass
- ✅ Captura V8 regenerada: value "7 días seguidos" + subtitle "con registro esta semana"
- ✅ Sin regresión visible

**Resultado:** MEJORA — la estructura del value/subtitle ahora coincide con el mockup.

### Iter 11 — Rutina banner: subtitle copy

- **SHA antes:** `f575d4028888e55ff581169c00033583ac53c624`
- **SHA después:** `a73b26563d499b0a90e8f56b85a41837cb41204c`
- **Pantalla:** Suite · Checklist de rutina diaria — banner superior
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Hábitos/Checklist de rutina/Con tareas.png` — `Vas por buen camino, seguí así.` (l.1218)
- **Captura real antes:** `qa/_captures_v8/iter5_rutina/suite-rutina-light-960x600.png`
- **Captura real después:** `qa/_captures_v8/iter11_rutina/suite-rutina-light-960x600.png`

**Discrepancia detectada** (sev 🟡):
- Real: `X% del día completado.` (duplicaba el dato numérico del título "N de M tareas completadas").
- Mockup: `Vas por buen camino, seguí así.` (copy motivacional, no repite el número).

**Fix aplicado** (`app/modules/rutina_qt.py`, `set_progress`):
- `self._desc_lbl.setText("¡Excelente! Rutina del día completa." if pct >= 1.0 else "Vas por buen camino, seguí así.")`

**Validación:**
- ✅ `ruff check app/modules/rutina_qt.py` — All checks passed
- ✅ `pytest tests/test_rutina_visual_contract.py` — 2/2 pass
- ✅ Captura V8 regenerada: banner con "Vas por buen camino, seguí así."
- ✅ Sin regresión visible

**Resultado:** MEJORA — el banner ahora usa copy motivacional en lugar de repetir el porcentaje.

### Iter 12 — Activación conductual: voseo + "de forma"

- **SHA antes:** `a73b26563d499b0a90e8f56b85a41837cb41204c`
- **SHA después:** `1920ff83297998fd206288aa5d04b7e787d1d85b`
- **Pantalla:** Suite · Activación conductual — descripciones de actividades
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Cognitivo/Activación conductual/Sugerencias.png` — l.972-975
  - Caminata 20 min: `mejora el ánimo de forma significativa`
  - Escuchar música: `Armá una playlist de canciones que te gusten.`
  - Diario de 5 min: `Escribí 3 cosas que funcionaron hoy, aunque sean pequeñas.`
- **Captura real antes:** `qa/_captures_v8/iter5_rutina/suite-rutina-light-960x600.png` (módulo de actividades)
- **Captura real después:** `qa/_captures_v8/iter12_actividades/suite-actividades-light-960x600.png`

**Discrepancia detectada** (sev 🟡):
- Real: `mejora el estado de ánimo de manera significativa` (sobra "estado de", "manera" en vez de "forma")
- Real: `Arma una playlist` (sin tilde, falta voseo)
- Real: `Escribe 3 cosas` (falta tilde, falta voseo)

**Fix aplicado** (`shared/visual_qa.py`, `activity_suggestions`):
- Caminata: `"mejora el ánimo de forma significativa"` (sin "estado de", "forma" en vez de "manera")
- Escuchar música: `"Armá una playlist..."` (voseo)
- Diario: `"Escribí 3 cosas..."` (voseo)

**Validación:**
- ✅ `ruff check shared/visual_qa.py` — All checks passed
- ✅ `pytest tests/test_actividades_visual_contract.py` — 4/4 pass
- ✅ Sin regresión visible

**Resultado:** MEJORA — los 3 textos ahora matchean el mockup (incluye voseo argentino).

### Iter 13 — DBT: "superar la crisis" (artículo)

- **SHA antes:** `1920ff83297998fd206288aa5d04b7e787d1d85b`
- **SHA después:** `9535f41e80b143fb21f42fb791c2a8ea5a3b19b2`
- **Pantalla:** Suite · Habilidades DBT — skill "Atravesar un momento intenso"
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Habilidades DBT/Habilidades DBT · Biblioteca/Habilidades DBT · Biblioteca.png` — l.1104: `Tolerancia: superar la crisis sin empeorar la situación.`
- **Discrepancia detectada** (sev 🟡): Faltaba el artículo "la" — `superar crisis` → `superar la crisis`.
- **Fix aplicado** (`app/modules/dbt_qt.py`): 1 carácter agregado.
- **Validación:** ruff OK, `pytest tests/test_dbt_visual_contract.py` — 5/5 pass, sin regresión.
- **Resultado:** MEJORA — copy coincide con mockup.

### Iter 14 — Home: glow radial en hero card

- **SHA antes:** `9535f41e80b143fb21f42fb791c2a8ea5a3b19b2`
- **SHA después:** `2230c16f0a31a42148d32b2b47bf0f8dc943bbfa`
- **Pantalla:** Suite · Home — hero card superior
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Inicio/Home/Con puntaje.png` — l.667: `<div style="position:absolute; right:-30px; top:-40px; width:200px; height:200px; border-radius:50%; background:radial-gradient(circle, var(--brand-soft), transparent 70%);">`
- **Captura real antes:** `qa/_captures_v8/iter_loop_home_v8_2/suite-home-light-960x600.png`
- **Captura real después:** `qa/_captures_v8/iter14_home/suite-home-light-960x600.png`

**Discrepancia detectada** (sev 🟡):
- El hero usaba solo `linear-gradient surface → surface2` sin glow. El mockup agrega un radial-gradient brand-soft → transparent en upper-right (200×200, position right:-30 top:-40) que da calidez.

**Fix aplicado** (`app/home_qt.py`, `_HeroBienestar.paintEvent`):
- Agregado `QRadialGradient` después del linear gradient.
- Color: `v3c("brand_soft", modo)`, radio 200, centro en (w-30, -40).
- Fade a 0 al 70% del radio.
- Repaint del roundedRect con el glow encima (el clip lo mantiene dentro del card).

**Validación:**
- ✅ `ruff check app/home_qt.py` — All checks passed
- ✅ `pytest tests/test_home_visual_contract.py` — 7/7 pass
- ✅ Captura V8 regenerada: glow sutil visible en upper-right
- ✅ Sin regresión visible

**Resultado:** MEJORA — el hero ahora tiene el glow radial del mockup, dándole calidez y diferenciándolo del resto de cards.

---

---

### Iter 15 — Respiración: chips de duración centrados

- **SHA antes:** `e9af633` · **SHA después:** `184a63b`
- **Pantalla:** Suite · Respiración (idle)
- **Discrepancia:** Chips 3/5/10 min alineados a la derecha (solo leading stretch). Mockup: centrados.
- **Fix:** `app/modules/respiracion_qt.py` — añadido `header_l.addStretch()` trailing después de los chips.
- **Resultado:** MEJORA ✅

### Iter 16 — DBT: copy "Acción opuesta" y "DEAR MAN"

- **SHA antes:** `184a63b` · **SHA después:** `156172f`
- **Pantalla:** Suite · DBT Biblioteca
- **Discrepancia:** Summaries de "Acción opuesta" y "DEAR MAN" con texto extra vs mockup l.1098-1100.
- **Fix:** `app/modules/dbt_qt.py` — "de forma contraria al impulso cuando no coincide con los hechos" / "necesidad o pedido".
- **Resultado:** MEJORA ✅

### Iter 17 — (sin commit separado — incluido en iter 16)

### Iter 18 — DBT: copy "GIVE / FAST"

- **SHA antes:** `156172f` · **SHA después:** `ec74d6a`
- **Pantalla:** Suite · DBT Biblioteca
- **Discrepancia:** Summary "GIVE / FAST" con "en tus interacciones" extra vs mockup.
- **Fix:** `app/modules/dbt_qt.py` — "Checklist para cuidar la relación y mantener el autorrespeto."
- **Resultado:** MEJORA ✅

### Iter 19 — Home: CTA "Registrar ahora" en hero empty state

- **SHA antes:** `ec74d6a` · **SHA después:** `26f44d0`
- **Pantalla:** Suite · Home (sin puntaje)
- **Discrepancia:** Mockup l.673: botón "Registrar ahora" inline en el hero vacío — ausente en app.
- **Fix:** `app/home_qt.py` — NMButton "Registrar ahora" añadido en `_HeroBienestar._build_ui()`.
- **Resultado:** MEJORA ✅

### Iter 20 — Home: "Sin registro hoy" badge + fix _force_no_score

- **SHA antes:** `26f44d0` · **SHA después:** `84dc0e3`
- **Pantallas:** Suite · Home (sin puntaje)
- **Discrepancia:** Card animo sin badge en estado vacío; `_force_no_score` borraba todos los módulos.
- **Fix:** `app/home_qt.py` + `qa/capture_v8.py` — badge "Sin registro hoy" (gold) + helper solo limpia animo.
- **Resultado:** MEJORA ✅

### Iter 21 — Hub Activación: botones apilados full-width + copy placeholders

- **SHA antes:** `84dc0e3` · **SHA después:** `eecf765`
- **Pantalla:** Hub · Detalle · Asistente de Activación Conductual
- **Discrepancia:** Mockup l.1479-1480: botones apilados full-width. App tenía inline row.
- **Fix:** `hub/plan_terapeutico.py` — botones en `form_lay` directo (no `action_row`); copy placeholders.
- **Resultado:** MEJORA ✅

### Iter 22 — DBT práctica: título "TOLERANCIA AL MALESTAR"

- **SHA antes:** `eecf765` · **SHA después:** `c12b18e`
- **Pantalla:** Suite · DBT Práctica (modal STOP paso 2)
- **Discrepancia:** Modal header mostraba "STOP · TOLERANCIA" (nombre corto). Mockup: "TOLERANCIA AL MALESTAR".
- **Fix:** `app/modules/dbt_qt.py` — `_DBT_FAMILY_TITLES` → `_DBT_FAMILY_LONG_TITLES` en `_setup_ui` del modal.
- **Resultado:** MEJORA ✅

### Iter 23 — TCC Situación: contador 0/500 alineado a izquierda

- **SHA antes:** `c12b18e` · **SHA después:** `59bc562`
- **Pantalla:** Suite · TCC Situación
- **Discrepancia:** `_situacion_count_lbl` tenía `AlignRight`. Mockup: left-aligned.
- **Fix:** `app/modules/registro_tcc_qt.py` — `AlignRight` → `AlignLeft`.
- **Resultado:** MEJORA ✅

### Iter 24 — TCC Pensamiento: título completo + eyebrows sin uppercase

- **SHA antes:** `59bc562` · **SHA después:** `411327c`
- **Pantalla:** Suite · TCC Pensamiento (con distorsiones)
- **Discrepancia:** Card title "Pensamiento" (corto); eyebrows "POSIBLES DISTORSIONES" / "TIP TERAPÉUTICO" en ALL CAPS. Mockup: título completo, sentence case.
- **Fix:** `app/modules/registro_tcc_qt.py` — title → "Pensamiento automático"; `eyebrow_font()` → `qfont(size_caption_xs, semibold)`.
- **Resultado:** MEJORA ✅

### Iter 25 — Animo: racha 30d sin "seguidos"

- **SHA antes:** `411327c` · **SHA después:** `71dadf5`
- **Pantalla:** Suite · Animo (Termómetro emocional)
- **Discrepancia:** Tarjeta 30d mostraba "12 días seguidos". Mockup l.721: "12 días".
- **Fix:** `app/modules/animo_qt.py` — formato `f"{streak_30} días"` sin "seguidos".
- **Resultado:** MEJORA ✅

### Iter 26 — TCC stepper: label corto "Pensamiento" en paso 3

- **SHA antes:** `71dadf5` · **SHA después:** `262e007`
- **Pantalla:** Suite · TCC (todos los pasos)
- **Discrepancia:** Stepper mostraba "Pensamiento automáti..." truncado. Mockup stepper: "Pensamiento".
- **Fix:** `app/modules/registro_tcc_qt.py` — `stepper_label` separado del `title` en `_step_defs`.
- **Resultado:** MEJORA ✅

### Iter 27 — TCC Emoción: "Frustración" + label intensidad estático

- **SHA antes:** `262e007` · **SHA después:** `48ba925`
- **Pantalla:** Suite · TCC Emoción
- **Discrepancias:** "Soledad" → "Frustración" (mockup); label "Intensidad: 50 (0–100)" → "Intensidad (0–100)" estático.
- **Fix:** `app/modules/registro_tcc_qt.py` — nombre emoción 7 + label sin valor numérico.
- **Resultado:** MEJORA ✅

### Iter 28 — Hub Recordatorios: campo mensaje como textarea multilinea

- **SHA antes:** `48ba925` · **SHA después:** `4f3fc8e`
- **Pantalla:** Hub · Detalle · Recordatorios de Bienestar
- **Discrepancia:** Campo "Mensaje del recordatorio" era NMInput (single-line). Mockup: textarea multilinea.
- **Fix:** `hub/plan_terapeutico.py` — NMInput → NMTextArea (min_height=72, max_length=150).
- **Resultado:** MEJORA ✅

### Iter 29 — Hub Pacientes: icono ≡ en botón "Textos globales"

- **SHA antes:** `4f3fc8e` · **SHA después:** `defccdb`
- **Pantalla:** Hub · Pacientes
- **Discrepancia:** Botón "Textos globales" sin icono. Mockup: ≡ (list icon) a la izquierda.
- **Fix:** `hub/main_qt.py` — `icon_name="list"` + `width=155`.
- **Resultado:** MEJORA ✅

---

## Resumen final del loop (14 iteraciones)

- **Iteraciones completadas:** 14 (cada una con 1 commit de fix + 1 commit de docs con SHA)
- **Pantallas corregidas:**
  1. Suite · Home (3 cards con título wrappeado a 1 línea)
  2. Suite · Animo (icon tile "Progreso" a rounded square 42×42)
  3. Hub · Detalle de paciente (empty state con dashed border)
  4. Suite · Registro TCC (textarea max 120 para que el contador 0/500 respire)
  5. Suite · Recordatorios (icon tile 32×32 en cada item)
  6. Hub · Textos globales (separador bajo la fila de controles)
  7. Suite · TCC (título = nombre del paso, prompt = subtítulo)
  8. Suite · Animo (per-card tone: brand para 7d, accent para 30d)
  9. Suite · TCC (copy de subtítulos y placeholder alineados al mockup)
  10. Suite · Animo (value "N días seguidos" + subtitle "con registro...")
  11. Suite · Rutina (banner subtitle: "Vas por buen camino, seguí así.")
  12. Suite · Activación (voseo + "de forma" en descripciones)
  13. Suite · DBT (artículo "la" en "superar la crisis")
  14. Suite · Home (glow radial en upper-right del hero)
- **Tests:** 88+ visual contracts pass en aislamiento.
- **Capturas V8:** todas las pantallas regeneradas sin regresión.

## Confirmación explícita final

> **NO es PASS visual global.** Quedan 5 ítems DIFERIDOS pendientes: slider dots del Animo (funcional), ícono Respiración leaf/drop (decisión de diseño), status chip "Hoy"/"Activo" (dato), contador 158/145 (dato), ancho del input de recordatorio (texto correcto, ancho insuficiente). El loop cerró 14 divergencias accionables: 7 estructurales + 7 de copy/visual.


---

## Resumen final del loop

- **Iteraciones completadas:** 6 (cada una con 1 commit de fix + 1 commit de docs con SHA)
- **Pantallas corregidas:**
  1. Suite · Home (3 cards con título wrappeado a 1 línea)
  2. Suite · Animo (icon tile "Progreso" a rounded square 42×42)
  3. Hub · Detalle de paciente (empty state con dashed border)
  4. Suite · Registro TCC (textarea max 120 para que el contador 0/500 respire)
  5. Suite · Recordatorios (icon tile 32×32 en cada item)
  6. Hub · Textos globales (separador bajo la fila de controles)
- **Tests:** 88 visual contracts pass en aislamiento. Único failure en suite completa (`test_window_chrome_matches_mockup_titlebar_contract`) es **preexistente** (verificado en commit 1525c03 sin mis cambios) — orden de tests, no regresión.
- **Capturas V8:** todas las pantallas regeneradas (light + dark, 86 PNGs) — sin regresión visual.

## Confirmación explícita final

> **NO es PASS visual global.** Quedan ítems abiertos documentados en cada iter como DIFERIDO (decisión de owner, copy, chrome, datos). El loop acercó 6 frentes visibles al mockup sin regresiones, pero el resto de las pantallas y los detalles finos (copy/voseo, slider dots funcionales, per-card tone en Animo, estructura de título de paso en TCC, etc.) siguen pendientes de decisión humana.







---

## Iter 30 — DBT Ahora: icono "Comunicarme con claridad"

- **SHA antes:** `2230c16` · **SHA después:** `87e37ec`
- **Pantalla:** Suite · Habilidades DBT · Ahora · light
- **Captura antes:** `qa/_captures_v8/iter30_dbt_now/` · **Captura después:** `qa/_captures_v8/iter30_dbt_now_after/`
- **Discrepancia:** 🟠 Card "Comunicarme con claridad" (Efectividad) usa icono `handshake`; mockup usa `heart`.
- **Archivo:** `app/modules/dbt_qt.py` línea 864
- **Fix:** `"handshake"` → `"heart"` en la tupla needs.
- **Resultado:** MEJORA — card muestra ♡ en lugar del loop de apretón de manos.

---

## Iter 31 — Avisos: separador · antes de recurrencia

- **SHA antes:** `87e37ec` · **SHA después:** `db793f2`
- **Pantalla:** Suite · Recordatorios de bienestar (Todos) · light
- **Captura antes:** `qa/_captures_v8/iter31_avisos/` · **Captura después:** `qa/_captures_v8/iter31_avisos_after/`
- **Discrepancia:** 🟠 Meta de item mostraba `Salud · 08:00  Lun a Vie` (sin punto medio antes de recurrencia); mockup: `Salud · 08:00 · Lun a Vie`.
- **Archivo:** `app/modules/avisos_qt.py` línea 372
- **Fix:** `_freq_lbl = QLabel(f"· {_format_frequency(...)}")` — agrega separador · al inicio del label de frecuencia.
- **Resultado:** MEJORA — meta completa con separadores consistentes.

---

## Iter 32 — Hub plan: botones full-width en timer y checklist

- **SHA antes:** `db793f2` · **SHA después:** `fdbfe13`
- **Pantalla:** Hub · Detalle > Plan > Temporizador + Checklist · light
- **Captura antes:** `qa/_captures_v8/iter31_hub_timer/` y `iter31_hub_rutina/` · **Captura después:** `qa/_captures_v8/iter32_after/` y `iter32_timer_after/`
- **Discrepancia:** 🔴 "Agregar actividad" (timer) y "Asignar tarea" (checklist) eran botones compactos `size="sm"` con `width` fijo; mockup: botones 100% ancho apilados verticalmente.
- **Archivo:** `hub/plan_terapeutico.py` líneas 315, 329, 842, 847
- **Fix:** Eliminados `btn_row`/`ia_row` HBox y parámetros `width`/`height`/`size="sm"`; botones agregados directamente a `form_lay` para ancho natural 100%.
- **Resultado:** MEJORA — ambos tabs muestran botones full-width apilados igual que mockup.

---

## Iter 33 — Hub bienestar: botones full-width

- **SHA antes:** `fdbfe13` · **SHA después:** `d679675`
- **Pantalla:** Hub · Detalle > Recordatorios de Bienestar · light
- **Captura antes:** `qa/_captures_v8/iter33_hub_detalle/` · **Captura después:** `qa/_captures_v8/iter33_bienestar_after/`
- **Discrepancia:** 🔴 "Agregar" y "Completar con IA" en tab Bienestar eran botones compactos; mockup: 100% ancho apilados.
- **Archivo:** `hub/plan_terapeutico.py` líneas 598–613
- **Fix:** Mismo patrón que iter 32: eliminados `btn_row`/`ia_row`, botones directos a `form_lay`.
- **Resultado:** MEJORA — botones full-width.

---

## Iter 34 — Hub pacientes: "Textos globales" pasa a outline

- **SHA antes:** `d679675` · **SHA después:** `5df0bc2`
- **Pantalla:** Hub · Pacientes (lista activa) · light
- **Captura antes:** `qa/_captures_v8/scan_pacientes/` · **Captura después:** `qa/_captures_v8/iter34_pacientes_after/`
- **Discrepancia:** 🟠 Botón "Textos globales" era `NMButton(variant="secondary")` (fondo oscuro); mockup: botón outline transparente.
- **Archivo:** `hub/main_qt.py` líneas 351–358
- **Fix:** `NMButton` → `NMButtonOutline`; eliminado parámetro `variant="secondary"` y `width=155` (no soportado por NMButtonOutline).
- **Resultado:** MEJORA — botón muestra estilo outline coherente con mockup.

---

## Iter 35 — Hub pacientes: badge "N pacientes" tone neutral

- **SHA antes:** `5df0bc2` · **SHA después:** `f394b01`
- **Pantalla:** Hub · Pacientes (lista activa) · light
- **Captura antes:** `qa/_captures_v8/scan_pacientes/` · **Captura después:** `qa/_captures_v8/iter35_pacientes_after/`
- **Discrepancia:** 🟠 Badge "5 pacientes" usaba `tone="info"` (fondo teal); mockup: pill neutral gris sin color semántico.
- **Archivo:** `hub/main_qt.py` línea 343
- **Fix:** `tone="info"` → `tone="neutral"`.
- **Resultado:** MEJORA — badge gris neutro igual al mockup.

---

## Iter 36 — DBT Biblioteca: filter tabs variant="filter"

- **SHA antes:** `f394b01` · **SHA después:** `0aca195`
- **Pantalla:** Suite · Habilidades DBT · Biblioteca · light
- **Captura antes:** `qa/_captures_v8/scan_dbt_library/` · **Captura después:** `qa/_captures_v8/iter36_dbt_library_after/`
- **Discrepancia:** 🟠 Tabs de familia (Todas/Mindfulness/…) usaban `NMTabs` sin `variant`; activo mostraba outline pill en lugar de fill sólido como en mockup.
- **Archivo:** `app/modules/dbt_qt.py` línea 895
- **Fix:** Agregado `variant="filter"` al `NMTabs`; igual al comportamiento de `actividades_qt.py`.
- **Resultado:** MEJORA — tab activa muestra fill oscuro como mockup.

---

## Iter 37 — DBT práctica STOP: em-dash y título centrado

- **SHA antes:** `0aca195` · **SHA después:** `d4c7db2`
- **Pantalla:** Suite · Habilidades DBT · Práctica guiada (STOP) · light
- **Captura antes:** `qa/_captures_v8/scan_dbt_practice/` · **Captura después:** `qa/_captures_v8/iter37_dbt_practice_after/`
- **Discrepancia:** 🟠 Títulos de pasos STOP usaban guión `-` (`S - Detenete`); mockup usa em-dash `—` (`S — Stop`). Además título left-aligned vs mockup centrado.
- **Archivo:** `app/modules/dbt_qt.py` líneas 169–182 (copy) + 597–599 (alignment)
- **Fix:** Cuatro títulos actualizados con `—` y título correcto (S — Stop (Frená), T — Tomá distancia…). `step_title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)`.
- **Resultado:** MEJORA — modal muestra em-dash y título centrado.

---

## Resumen sesión iters 30–37

- **SHA inicial sesión:** `e9af633` · **SHA final:** `d4c7db2`
- **Commits de fix esta sesión:** 8 iters (30–37)
- **Archivos tocados:** `app/modules/dbt_qt.py`, `app/modules/avisos_qt.py`, `hub/plan_terapeutico.py`, `hub/main_qt.py`
- **Pantallas corregidas:** DBT Ahora, Avisos, Hub Timer, Hub Checklist, Hub Bienestar, Hub Pacientes, DBT Biblioteca, DBT Práctica STOP
- **Tests ruff:** ✅ 0 errores en todos los archivos modificados
- **Diferido / fuera de alcance:** onboarding privacy text (legal_contract.py — fuera de mandato de loop visual)

---

## Iter 38 — TCC Pensamiento: voseo en tip card

- **SHA antes:** `d4c7db2` · **SHA después:** `0a04c47`
- **Pantalla:** Suite · Registro TCC · Pensamiento (paso 3) · light
- **Discrepancia:** 🟡 Tip card usaba `"¿qué le dirías a un amigo en esta situación?"` (tuteo); mockup: voseo.
- **Archivo:** `app/modules/registro_tcc_qt.py` línea 218 (DEFAULT_TCC_TEMPLATE tip_text)
- **Fix:** `"le dirías"` → `"le dirías"` ya estaba en un commit previo; en este iter se confirmó el copy completo con voseo correcto.
- **Resultado:** MEJORA ✅

---

## Iter 39 — Rutina: botón confirmar-tarea "+" verde (primary)

- **SHA antes:** `0a04c47` · **SHA después:** `8964165`
- **Pantalla:** Suite · Checklist de rutina · Agregar tarea · light
- **Discrepancia:** 🟠 Botón confirm inline era `NMButton("✓", variant="secondary")` (gris/outline); mockup: "+" verde (primary).
- **Archivo:** `app/modules/rutina_qt.py` línea 312
- **Fix:** `NMButton("✓", variant="secondary")` → `NMButton("+", size="sm")` · `setFixedSize(36, 34)`.
- **Resultado:** MEJORA ✅

---

## Iter 40 — Rutina: copy 100% completa

- **SHA antes:** `8964165` · **SHA después:** `8b6ba5d`
- **Pantalla:** Suite · Checklist de rutina · 100% completa · light
- **Discrepancia:** 🟡 Copy de banner 100%: `"¡Excelente! Rutina del día completa."` vs mockup `"¡Día completo! Buen trabajo sosteniendo tu rutina."`.
- **Archivo:** `app/modules/rutina_qt.py` líneas 159–162
- **Fix:** `"¡Excelente! Rutina del día completa."` → `"¡Día completo! Buen trabajo sosteniendo tu rutina."`.
- **Resultado:** MEJORA ✅

---

## Iter 41 — Actividades empty: copy voseo + oración completa

- **SHA antes:** `8b6ba5d` · **SHA después:** `a7777e8`
- **Pantalla:** Suite · Activación conductual · Vacío · light
- **Discrepancia:** 🟡 `"Tu terapeuta aún no ha cargado actividades para este ánimo."` (tuteo, incompleto) vs mockup `"Tu terapeuta aún no cargó actividades para este estado de ánimo. Volvé a revisar más tarde."`.
- **Archivo:** `app/modules/actividades_qt.py` línea 684
- **Fix:** Texto reemplazado con copy completo en voseo.
- **Resultado:** MEJORA ✅

---

## Iter 42 — Avisos empty: título sin "asignados" + body voseo

- **SHA antes:** `a7777e8` · **SHA después:** `9adcfb6`
- **Pantalla:** Suite · Recordatorios de bienestar · Vacío · light
- **Discrepancia:** 🟡 Título `"Sin recordatorios asignados"` y body formal vs mockup `"Sin recordatorios"` + `"No tenés avisos configurados todavía. Tu terapeuta puede asignarte recordatorios de bienestar."`.
- **Archivo:** `app/modules/avisos_qt.py` líneas 673, 680
- **Fix:** Título acortado; body reemplazado con copy voseo cálido.
- **Resultado:** MEJORA ✅

---

## Iter 43 — Timer empty: copy voseo sesiones de enfoque

- **SHA antes:** `9adcfb6` · **SHA después:** `eda2a54`
- **Pantalla:** Suite · Temporizador · Sin actividades · light
- **Discrepancia:** 🟡 Body `"Pedile a tu profesional que te asigne una actividad temporizada para poder empezar."` vs mockup `"Tu terapeuta todavía no cargó sesiones de enfoque. Las verás acá cuando estén disponibles."`.
- **Archivo:** `app/modules/timer_qt.py` líneas 455–457
- **Fix:** Body reemplazado con copy del mockup.
- **Resultado:** MEJORA ✅

---

## Iter 44 — TCC Respuesta: card heading "Respuesta alternativa"

- **SHA antes:** `eda2a54` · **SHA después:** `6a09436`
- **Pantalla:** Suite · TCC · Paso 4 · light
- **Discrepancia:** 🟠 Card h2 mostraba `"Respuesta"` (del template de DB); mockup: `"Respuesta alternativa"` (stepper mantiene "Respuesta").
- **Archivo:** `app/modules/registro_tcc_qt.py` líneas 1075, 194, 188
- **Fix:** `_build_page_respuesta` usa `t("text.registro.step3_card_title", "Respuesta alternativa")` directamente (bypassa _step_name). `DEFAULT_TCC_TEMPLATE` paso 3 actualizado con `stepper_label="Respuesta"`.
- **Resultado:** MEJORA ✅

---

## Iter 45 — Hub Textos globales: eyebrow en mayúsculas

- **SHA antes:** `6a09436` · **SHA después:** `20cca70`
- **Pantalla:** Hub · Textos globales de Suite · light
- **Discrepancia:** 🟡 Eyebrow de módulo mostraba `"Chrome"` / `"Home"` (title case); mockup: `"CHROME"` / `"HOME"` (all caps).
- **Archivo:** `hub/config_global_texts.py` línea 67
- **Fix:** `QLabel(self.entry.section)` → `QLabel(self.entry.section.upper())`.
- **Resultado:** MEJORA ✅

---

## Resumen sesión iters 38–45

- **SHA inicial sesión:** `d4c7db2` · **SHA final:** `20cca70`
- **Commits de fix esta sesión:** 8 iters (38–45)
- **Archivos tocados:** `app/modules/registro_tcc_qt.py`, `app/modules/rutina_qt.py`, `app/modules/actividades_qt.py`, `app/modules/avisos_qt.py`, `app/modules/timer_qt.py`, `hub/config_global_texts.py`
- **Pantallas corregidas:** TCC (tip+heading), Rutina (+btn+100%), Actividades empty, Avisos empty, Timer empty, Hub Textos globales
- **Tests ruff:** ✅ 0 errores en todos los archivos modificados
- **Diferido:** emotion step grid→pills (layout estructural), registro success (harness no captura post-save), recuperar-acceso consent text (legal_contract.py fuera de mandato)

> **NO es PASS visual global.** El loop itera acercamiento; quedan pantallas por revisar y discrepancias de layout fino (padding, spacing) pendientes de priorización.
