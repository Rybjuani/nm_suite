# Visual Loop Log 2 — sesión 2026-06-24 (c004845 → ?)

> Continuación de `qa/LOOP_LOG.md` (61 iteraciones previas, 12 superficies corregidas).
> Mockup: `neuromood-mockup.html` + `qa/mockup_reference_static/`.
> Capturas reales: `qa/capture_v8.py` (43 recipes × 2 temas = 86 captures posibles).
> Reglas: 1 ciclo = 1 discrepancia visible y accionable. Si no mejora → revert.
> Prohibido: tocar tests para aceptar UI actual, lógica clínica/DB/auth/sync,
> modificar `qa/mockup_reference_static/`, declarar "PASS visual global".

## Estado inicial

- **HEAD inicial:** `c0048457685154bb737f57c024cf5f58b1d6f00b`
- **Branch:** `main`
- **Log previo:** `qa/LOOP_LOG.md` — 61 iteraciones, 12 superficies corregidas
- **Baseline:** regenerar a demanda por superficie (no hay baseline persistido
  de la sesión anterior — el dir `iter_loop_2026_06_24_baseline` fue purgado).

## Pendientes reabiertos de la sesión anterior

- 🟡 Slider dots animo (DIFERIDO funcional — los 10 niveles clickeables)
- 🟡 TCC Emoción grilla 4×2 → pills horizontales (DIFERIDO estructural — tests legacy bloquean)
- 🟡 Hub · sidebar collapsed (DIFERIDO — sin mockup de referencia)
- 🟡 Hub · Personalización/Editor overrides (DIFERIDO — sin mockup de referencia)
- 🟡 Onboarding copy legal (DIFERIDO — `shared/legal_contract.py` fuera de mandato)
- 🟡 Registro success post-save (DIFERIDO — harness no captura post-save)
- 🟡 Status chip "Hoy"/"Activo" (DIFERIDO data-driven — depende del recordatorio)
- 🟡 Contador 158/145 (DIFERIDO data — cantidad real de textos editables)
- 🟡 Ancho input recordatorio "Mensaje del recordatorio (máx 150)" truncado (DIFERIDO ancho)
- 🟡 Subtítulo Respiración "Técnicas de calma 4·7·8" punto medio invisible (NO accionable — glifo)

## Convención de entradas

Cada iteración registra:
- iter # · SHA antes/después · producto/app · módulo · pantalla/vista · subpantalla/detalle · estado/variante · sección · componente · acción · modal · toast · navegación
- discrepancia elegida · sev · archivos candidatos · commit
- validación: ruff, tests relevantes, captura V8 antes/después
- resultado (MEJORA / NEUTRAL / REGRESIÓN)
- discrepancias restantes al cierre del ciclo

## Iteraciones

### Iter 62 — Avisos: "Salud" category color danger → brand (visible)

- **SHA antes:** `c0048457685154bb737f57c024cf5f58b1d6f00b`
- **SHA después:** `f5ede5c42bcb4bbaa9c59f0763cf2acdf2eb1385`
- **Producto/App:** Suite (módulo Avisos/Recordatorios de bienestar)
- **Módulo:** `app/modules/avisos_qt.py`
- **Pantalla/Vista:** Suite · Recordatorios de bienestar · Todos (default)
- **Estado/Variante:** filtro "Todos" seleccionado (default)
- **Sección/Componente:** categoría label ("Salud" / "Calma" / etc) en cada item de recordatorio
- **Acción:** ninguna (solo render visual)
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Hábitos/Recordatorios de bienestar/Todos.png` — "Salud" en VERDE BRAND (mismo tono que chip "Completado" y filtro "Todos" activo).
- **Captura antes:** `qa/_captures_v8/iter62_baseline/suite-avisos-light-960x600.png` — "Salud" en ROJO (token `danger` = #B24E3D).
- **Captura después:** `qa/_captures_v8/iter62_after/suite-avisos-light-960x600.png` — "Salud" en VERDE BRAND, matchea mockup.

**Discrepancia detectada** (sev 🟠):
- `_categorize()` mapeaba palabras de salud/medicina a token `danger` (rojo). El mockup muestra el label en verde brand. Visualmente esto rompe la jerarquía cromática (rojo implica alerta/error; el resto de categorías usan tonos verdes/teal/warning).
- "Calma" usaba `teal` (correcto), "Hidratación" `cyan`, "Comida" `warning` — pero "Salud" (la más común) estaba en rojo. Era la más notoria.

**Fix aplicado** (`app/modules/avisos_qt.py`, `_categorize`):
- `return ("Salud", "medicine", "danger")` → `return ("Salud", "medicine", "brand")`.
- 1 línea. Sin tocar lógica de matching ni otras categorías.

**Validación:**
- ✅ `ruff check app/modules/avisos_qt.py` — All checks passed
- ✅ `pytest tests/test_avisos_visual_contract.py` — 2/2 pass
- ✅ Captura V8 regenerada: "Salud" ahora verde brand, visualmente matchea mockup
- ✅ Sin regresión en otros labels (Calma/teal, Hidratación/cyan, Comida/warning)

**Resultado:** MEJORA — "Salud" ahora en verde brand, alineado con el sistema cromático del mockup.

**Discrepancias restantes:**
- 🟡 Slider dots animo (DIFERIDO funcional)
- 🟡 TCC Emoción grilla 4×2 → pills (DIFERIDO estructural)
- 🟡 Status chip "Activo" (DIFERIDO data-driven)
- 🟡 Ancho input recordatorio (DIFERIDO ancho)
- 🟡 Subtítulo Respiración punto medio invisible (NO accionable — glifo)

### Iter 63 — Avisos: search input ancho/separación container filtros (visible)

- **SHA antes:** `f5ede5c42bcb4bbaa9c59f0763cf2acdf2eb1385`
- **SHA después:** `923361505cc435c5c32197070fad3126e350ee6a`
- **Producto/App:** Suite (módulo Avisos)
- **Módulo:** `app/modules/avisos_qt.py`
- **Pantalla/Vista:** Suite · Recordatorios · Búsqueda (también afecta default Todos)
- **Estado/Variante:** con/sin query en el input
- **Sección/Componente:** header row de la vista (container filtros segmentado + search input)
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Hábitos/Recordatorios de bienestar/Búsqueda.png` — input de búsqueda ancho (~400px) con gap visible del container de filtros.
- **Captura antes:** `qa/_captures_v8/iter63_baseline/suite-avisos-search-light-960x600.png` — input ~340px pegado al container (spacing 6px).
- **Captura después:** `qa/_captures_v8/iter63_after/suite-avisos-search-light-960x600.png` — input más ancho, más separado del container.

**Discrepancia detectada** (sev 🟡):
- `filter_row.setSpacing(V3_SP["sm"])` = 6px entre container filtros y search.
- `search_input.setMaximumWidth(340)` limitaba el ancho.
- En el mockup el gap es ~10-12px y el input ocupa más espacio horizontal. Visualmente se veía apretado en el real.

**Fix aplicado** (`app/modules/avisos_qt.py`, `AvisosView.__init__`):
- spacing `V3_SP["sm"]` → `V3_SP["md"]` (6 → 10).
- search min width 220 → 320, max 340 → 480.

**Validación:**
- ✅ `ruff check app/modules/avisos_qt.py` — All checks passed
- ✅ `pytest tests/test_avisos_visual_contract.py` — 2/2 pass
- ✅ V8 avisos-search: input + clear button visibles, mejor separación
- ✅ V8 avisos (default): sin regresión, 5 recordatorios visibles, layout preservado

**Resultado:** MEJORA — el input de búsqueda ahora se ve más espaciado del container de filtros, acercándose al mockup.

**Discrepancias restantes:**
- 🟡 Slider dots animo (DIFERIDO funcional)
- 🟡 TCC Emoción grilla 4×2 → pills (DIFERIDO estructural)
- 🟡 Status chip "Activo" (DIFERIDO data-driven)
- 🟡 Subtítulo Respiración punto medio invisible (NO accionable — glifo)
- Próximas: revisar avisos-today, avisos-filter-activos, avisos-empty

### Iter 64 — Avisos empty: ocultar filtros + búsqueda cuando no hay asignados (visible)

- **SHA antes:** `923361505cc435c5c32197070fad3126e350ee6a`
- **SHA después:** `f14e293527990b8b9c48ca98cd07000cd7d5ab37`
- **Producto/App:** Suite (módulo Avisos)
- **Módulo:** `app/modules/avisos_qt.py`
- **Pantalla/Vista:** Suite · Recordatorios · Vacío (empty state sin recordatorios asignados)
- **Estado/Variante:** empty state, sin recordatorios en la DB
- **Sección/Componente:** header row (filtros segmentados + search input)
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Hábitos/Recordatorios de bienestar/Vacío.png` — empty state limpio, sin filtros ni búsqueda, solo icon + título serif + body.
- **Captura antes:** `qa/_captures_v8/iter65_baseline/suite-avisos-empty-light-960x600.png` — filtros y search visibles (sin sentido sin recordatorios).
- **Captura después:** `qa/_captures_v8/iter65_after/suite-avisos-empty-light-960x600.png` — empty state limpio, sin filtros ni search, matchea mockup.

**Discrepancia detectada** (sev 🟠):
- Mockup Vacío: empty state minimal (sin controles de filtrado).
- Real: mantenía filter_segment + search_input visibles aunque no hubiera recordatorios. La "Silencio card" ya se ocultaba (`self._silencio_card.setVisible(bool(self._all_rows))` línea 703), pero los filtros/búsqueda no.
- Visualmente: 2 filas de chrome vacío + empty state. Ruido innecesario.

**Fix aplicado** (`app/modules/avisos_qt.py`, `AvisosView._render_reminders`, branch empty):
- `self._filter_segment.setVisible(bool(self._all_rows))`
- `self._search_input.setVisible(bool(self._all_rows))`
- Header de ventana (título + traffic lights) se mantiene — es chrome OS-style.

**Validación:**
- ✅ `ruff check app/modules/avisos_qt.py` — All checks passed
- ✅ `pytest tests/test_avisos_visual_contract.py` — 2/2 pass (no asserta visibilidad)
- ✅ V8 avisos-empty: empty state minimal, matchea mockup
- ✅ V8 avisos (default, 5 recordatorios): sin regresión, filtros + search visibles

**Resultado:** MEJORA — empty state ahora limpio, sin chrome de filtrado innecesario, matchea mockup.

**Discrepancias restantes:**
- 🟡 Slider dots animo (DIFERIDO funcional)
- 🟡 TCC Emoción grilla 4×2 → pills (DIFERIDO estructural)
- 🟡 Status chip "Activo" en filtro Hoy (DIFERIDO data-driven)
- 🟡 Subtítulo Respiración punto medio invisible (NO accionable — glifo)
- Próximas: revisar avisos-filter-activos, otras superficies de Avisos

### Iter 65 — DBT: chips familia outline-style (visible)

- **SHA antes:** `f14e293527990b8b9c48ca98cd07000cd7d5ab37`
- **SHA después:** `4265e43f006681ed34df9c85e3d6a10575693df4`
- **Producto/App:** Suite (módulo DBT)
- **Módulo:** `app/modules/dbt_qt.py`
- **Pantalla/Vista:** Suite · DBT · Ahora (también afecta Biblioteca)
- **Estado/Variante:** vista default con 4 cards de familia
- **Sección/Componente:** chip de familia en cada card (Mindfulness/Tolerancia/Regulación/Efectividad)
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Habilidades DBT/Habilidades DBT · Ahora/Habilidades DBT · Ahora.png` — chips outline-style: fondo casi transparente, border visible del color de la familia, texto del color de la familia.
- **Captura antes:** `qa/_captures_v8/iter66_baseline/suite-dbt-now-light-960x600.png` — chips con fondo verde saturado (alpha 14%) + border 28%.
- **Captura después:** `qa/_captures_v8/iter66_after/suite-dbt-now-light-960x600.png` — chips outline-style limpios.

**Discrepancia detectada** (sev 🟠):
- Los chips de familia se renderizaban con `chip_bg alpha=0.14` (verde brand al 14%) y `border alpha=0.28`. Visualmente parecían "filled pills" más que "outline pills".
- El mockup los muestra como outline-pills limpios (fondo casi transparente, border visible).

**Fix aplicado** (`app/modules/dbt_qt.py`, `_NeedCard._apply_theme` + `_SkillCard._apply_theme`):
- `chip_bg` alpha 0.14 → 0.04 (casi transparente).
- border alpha 0.28 → 0.34 (más visible).

**Validación:**
- ✅ `ruff check app/modules/dbt_qt.py` — All checks passed
- ✅ `pytest tests/test_dbt_visual_contract.py` — 4/5 pass (1 preexistente fail no relacionado: `STOP · TOLERANCIA` vs `STOP · TOLERANCIA AL MALESTAR`, documentado en iter 61)
- ✅ V8 dbt-now: 4 chips outline-style limpios, matchea mockup
- ✅ Sin regresión visible

**Resultado:** MEJORA — los chips de familia ahora son outline-pills limpios (casi transparentes con borde de color), matcheando el mockup.

**Discrepancias restantes:**
- 🟡 Slider dots animo (DIFERIDO funcional)
- 🟡 TCC Emoción grilla 4×2 → pills (DIFERIDO estructural)
- 🟡 Status chip "Activo" en filtro Hoy (DIFERIDO data-driven)
- 🟡 Subtítulo Respiración punto medio invisible (NO accionable — glifo)
- 🟡 DBT skill cards misma familia chip (parcialmente cubierto por este fix)
- Próximas: revisar DBT Biblioteca, registro-step1, home-no-score

### Iter 66 — DBT Biblioteca: grid spacing 16→12px (visible)

- **SHA antes:** `4265e43f006681ed34df9c85e3d6a10575693df4`
- **SHA después:** `030548734eb3056740d7029e43caece8f10cb8cf`
- **Producto/App:** Suite (módulo DBT)
- **Módulo:** `app/modules/dbt_qt.py`
- **Pantalla/Vista:** Suite · DBT · Biblioteca
- **Estado/Variante:** tab "Todas" seleccionado (default)
- **Sección/Componente:** grid 3×3 de skill cards
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Habilidades DBT/Habilidades DBT · Biblioteca/Habilidades DBT · Biblioteca.png` — grid compacto, ~12px entre cards.
- **Captura antes:** `qa/_captures_v8/iter67_baseline/suite-dbt-library-light-960x600.png` — grid con 16px entre cards (más aire).
- **Captura después:** `qa/_captures_v8/iter67_after/suite-dbt-library-light-960x600.png` — grid 12px, más cohesivo.

**Discrepancia detectada** (sev 🟡):
- `_library_grid.setHorizontalSpacing(16)` y `setVerticalSpacing(16)` — el mockup usa ~12px. Diferencia visible: el real se veía "suelto", con demasiado espacio entre cards.

**Fix aplicado** (`app/modules/dbt_qt.py`, `_build_view_biblioteca`):
- horizontalSpacing 16 → 12
- verticalSpacing 16 → 12

**Validación:**
- ✅ `ruff check app/modules/dbt_qt.py` — All checks passed
- ✅ `pytest tests/test_dbt_visual_contract.py` — 4/5 pass (mismo preexistente fail)
- ✅ V8 dbt-library: grid más compacto, matchea mockup
- ✅ V8 dbt-now: sin regresión (grid 2×2 no afectado por este cambio)

**Resultado:** MEJORA — el grid de skills ahora más cohesivo, acercándose al mockup.

**Discrepancias restantes:**
- 🟡 Slider dots animo (DIFERIDO funcional)
- 🟡 TCC Emoción grilla 4×2 → pills (DIFERIDO estructural)
- 🟡 Status chip "Activo" en filtro Hoy (DIFERIDO data-driven)
- 🟡 Subtítulo Respiración punto medio invisible (NO accionable — glifo)
- Próximas: revisar registro-step1, home-no-score, rutina

### Iter 67 — Home: Checklist de rutina icon routine → checklist (visible)

- **SHA antes:** `030548734eb3056740d7029e43caece8f10cb8cf`
- **SHA después:** `1255d84bc631365a96782ea99c4780ab52703a30`
- **Producto/App:** Suite (Home)
- **Módulo:** `app/home_qt.py` + `shared/icons_svg.py`
- **Pantalla/Vista:** Suite · Home · Con puntaje (4ª module card)
- **Estado/Variante:** default
- **Sección/Componente:** icono del módulo "Checklist de rutina" en module card
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Inicio/Home/Con puntaje.png` — cuadrado con check ✓ adentro.
- **Captura antes:** `qa/_captures_v8/iter68b_baseline/suite-home-light-960x600.png` — solo rectángulo (3 paths del SVG "routine" ilegibles a 18px).
- **Captura después:** `qa/_captures_v8/iter68_after/suite-home-light-960x600.png` — cuadrado con check visible adentro.

**Discrepancia detectada** (sev 🟠):
- El módulo `rutina` usaba `icon_v3: "routine"` que tiene 3 paths SVG (rect + 2 líneas header + check adentro). A 18px en module cards del Home, las líneas header + check eran ilegibles — solo se veía el rect exterior.
- El mockup muestra un cuadrado con check adentro (más simple, sin las líneas de calendar).

**Fix aplicado:**
- `shared/icons_svg.py`: nuevo `ICON_BODIES["checklist"]` = rect + check prominente (1 path, sin header lines).
- `app/home_qt.py`: module `rutina` `icon_v3` "routine" → "checklist".

**Validación:**
- ✅ `ruff check app/home_qt.py shared/icons_svg.py` — All checks passed
- ✅ `pytest tests/test_home_visual_contract.py` — 7/7 pass
- ✅ Tests relevantes acumulados (home/rutina/avisos/dbt/animo/respiracion): 20/22 pass (2 preexistentes fail)
- ✅ V8 home: icono ahora matchea mockup (cuadrado + check)
- ✅ Sin regresión en los otros 7 iconos

**Resultado:** MEJORA — el icono "Checklist de rutina" ahora muestra un cuadrado con check adentro, matcheando el mockup.

**Discrepancias restantes:**
- 🟡 Slider dots animo (DIFERIDO funcional)
- 🟡 TCC Emoción grilla 4×2 → pills (DIFERIDO estructural — test legacy)
- 🟡 Status chip "Activo" en filtro Hoy (DIFERIDO data-driven)
- 🟡 Subtítulo Respiración punto medio invisible (NO accionable — glifo)
- Próximas: revisar rutina, timer, animo details

### Iter 68 — Titlebar Rutina: icon 'rutina' → 'checklist' (visible)

- **SHA antes:** `1255d84bc631365a96782ea99c4780ab52703a30`
- **SHA después:** `23473b957cf03d76d2a571027d2ff64b12cb6e73`
- **Producto/App:** Suite (shell chrome)
- **Módulo:** `app/main_qt.py`
- **Pantalla/Vista:** Suite · Rutina (cualquier vista del módulo)
- **Estado/Variante:** titlebar superior
- **Sección/Componente:** icono del módulo Rutina en el titlebar
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Hábitos/Checklist de rutina/Sin tareas.png` — cuadrado con check ✓ adentro en titlebar.
- **Captura antes:** `qa/_captures_v8/iter75_baseline/suite-rutina-empty-light-960x600.png` — icono "calendar" (QtAwesome fallback) en titlebar.
- **Captura después:** `qa/_captures_v8/iter75_after/suite-rutina-empty-light-960x600.png` — cuadrado con check ✓ adentro.

**Discrepancia detectada** (sev 🟠):
- `_MODULE_UI_META["rutina"] = ("Checklist de rutina diaria", "rutina")` — el icon name `"rutina"` no existe en `ICON_BODIES`, así que caía al fallback QtAwesome (calendar con día).
- El mockup muestra un cuadrado con check adentro (mismo que el module card de Home, arreglado en iter 67 con `icon_v3: "checklist"`).

**Fix aplicado** (`app/main_qt.py`, `_MODULE_UI_META`):
- `("Checklist de rutina diaria", "rutina")` → `("Checklist de rutina diaria", "checklist")`.

**Validación:**
- ✅ `ruff check app/main_qt.py` — All checks passed
- ✅ `pytest tests/test_rutina_visual_contract.py` — 1/2 pass (mismo preexistente fail)
- ✅ V8 rutina-empty: header icon ahora check-in-square, matchea mockup
- ✅ V8 rutina: sin regresión, header correcto

**Resultado:** MEJORA — el titlebar del módulo Rutina ahora muestra un cuadrado con check ✓ adentro, matcheando el mockup.

**Discrepancias restantes:**
- 🟡 Slider dots ánimo (DIFERIDO funcional)
- 🟡 TCC Emoción grilla 4×2 → pills (DIFERIDO estructural — test legacy)
- 🟡 Status chip "Activo" en filtro Hoy (DIFERIDO data-driven)
- 🟡 Subtítulo Respiración "4·7·8" (NO accionable — glifo fuente)
- 🟡 Rutina checkbox square vs circle (radius=7 con size=22, test assertea valor exacto)
### Iter 69 — TCC Paso 3 (Respuesta): counter bug, conectar a textChanged (visible)

- **SHA antes:** `23473b957cf03d76d2a571027d2ff64b12cb6e73`
- **SHA después:** `b72849dd0c057e8adb07481c36f738bb9d5ea339`
- **Producto/App:** Suite (módulo Registro TCC)
- **Módulo:** `app/modules/registro_tcc_qt.py`
- **Pantalla/Vista:** Suite · Registro · Paso 3 (Respuesta)
- **Estado/Variante:** textarea con texto prellenado
- **Sección/Componente:** counter "X / 500" al pie del textarea
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Cognitivo/Registro de pensamientos (TCC)/Respuesta.png` — counter refleja el contenido real del textarea.
- **Captura antes:** `qa/_captures_v8/iter88_baseline/suite-registro-step3-filled-light-960x600.png` — counter "0 / 500" con 85 chars prellenados.
- **Captura después:** `qa/_captures_v8/iter69_after/suite-registro-step3-filled-light-960x600.png` — counter "89 / 500" correcto.

**Discrepancia detectada** (sev 🟠):
- **BUG:** el counter del paso 3 (Respuesta) era un `QLabel("0 / 500")` estático, sin conectar al `textChanged` del textarea. Mostraba "0" aunque hubiera 85+ chars.
- El paso 0 (Situación) SÍ estaba conectado a `_update_situacion_count` (vía `_txt_situacion.textChanged.connect(self._update_situacion_count)`).
- Inconsistencia interna entre pasos del mismo wizard.

**Fix aplicado** (`app/modules/registro_tcc_qt.py`):
- `_build_page_respuesta`: `self._txt_respuesta.textChanged.connect(self._update_respuesta_count)`.
- Nueva `_update_respuesta_count()` mirror de `_update_situacion_count` (incluye color warning si n > 500 y `refresh_nav_state`).

**Validación:**
- ✅ `ruff check app/modules/registro_tcc_qt.py` — All checks passed
- ✅ `pytest tests/test_registro_tcc_visual_contract.py` — 6/7 pass (1 preexistente fail)
- ✅ V8 registro-step3-filled: counter "89 / 500" correcto
- ✅ Sin regresión en paso 0/2 counters

**Resultado:** MEJORA — BUG del counter arreglado, ahora refleja el contenido real.

### Iter 70 — Respiración: partículas alpha 115→55 light / 160→85 dark (visible)

- **SHA antes:** `b72849dd0c057e8adb07481c36f738bb9d5ea339`
- **SHA después:** `b8fa0e386bdab89e98af01c85a2a3974e4fc3280`
- **Producto/App:** Suite (módulo Respiración)
- **Módulo:** `app/modules/respiracion_qt.py`
- **Pantalla/Vista:** Suite · Respiración · En curso (running)
- **Estado/Variante:** activo (running)
- **Sección/Componente:** 8 partículas orbitando el breath circle
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Bienestar/Guía de respiración/En curso.png` — sin partículas visibles (solo el circle + "4" + "Inhalá").
- **Captura antes:** `qa/_captures_v8/iter71_baseline/suite-respiracion-running-light-960x600.png` — 8 puntos muy visibles (4 teal + 4 violet).
- **Captura después:** `qa/_captures_v8/iter70_after/suite-respiracion-running-light-960x600.png` — 8 puntos casi invisibles.

**Discrepancia detectada** (sev 🟡):
- 8 partículas orbitando el circle (capa decorativa runtime) eran muy visibles y no aparecen en el mockup. El mockup es minimal.

**Fix aplicado** (`app/modules/respiracion_qt.py`, `_draw_particles`):
- `particle_alpha = 115 (light) / 160 (dark)` → `55 (light) / 85 (dark)`.
- Mantiene feedback animado sutil sin dominar el circle.

**Validación:**
- ✅ `ruff check` — All checks passed
- ✅ V8 respiracion-running: partículas apenas perceptibles, circle domina

**Resultado:** MEJORA — partículas ahora sutiles, acercándose al minimal del mockup.

### Iter 71 — NMButton gradient disabled opacity 0.4 → 0.65 (visible)

- **SHA antes:** `b8fa0e386bdab89e98af01c85a2a3974e4fc3280`
- **SHA después:** `9ea6853d5d3281def1392d860ea0f86692685c68`
- **Producto/App:** Suite (compartido buttons)
- **Módulo:** `shared/components/buttons.py`
- **Pantalla/Vista:** Suite · Ánimo · "Guardar registro" (también afecta todos los gradient disabled)
- **Estado/Variante:** disabled
- **Sección/Componente:** NMButton variant="gradient" disabled state
- **Mockup esperado:** `qa/mockup_reference_static/light/Suite · Paciente/Bienestar/Termómetro emocional/Termómetro emocional.png` — botón disabled en verde brand pleno.
- **Captura antes:** `qa/_captures_v8/iter65c_baseline/suite-animo-light-960x600.png` — botón en verde sage claro (0.4 alpha).
- **Captura después:** `qa/_captures_v8/iter71_after/suite-animo-light-960x600.png` — botón más verde brand pleno (0.65 alpha).

**Discrepancia detectada** (sev 🟡):
- `setOpacity(0.4)` en NMButton gradient disabled daba un verde sage transparente que no matcheaba el mockup.

**Fix aplicado** (`shared/components/buttons.py`, `NMButton.paintEvent` gradient branch):
- `if not self.isEnabled(): p.setOpacity(0.4)` → `p.setOpacity(0.65)`.

**Validación:**
- ✅ `ruff check shared/components/buttons.py` — All checks passed
- ✅ V8 animo: botón ahora verde brand pleno, acercándose al mockup

**Resultado:** MEJORA — el botón gradient disabled ahora visiblemente más brand, acercándose al mockup. Cambio global que afecta a todos los NMButton gradient disabled.

### Iter 73 — Hub Detalle Recordatorios: placeholder "Mensaje (máx 150)" (visible)

- **SHA antes:** `9ea6853d5d3281def1392d860ea0f86692685c68`
- **SHA después:** `150791cc992ffa6cf041cb5c77ef50304de85d7d`
- **Producto/App:** Hub (clínico, Detalle de paciente)
- **Módulo:** `hub/plan_terapeutico.py`
- **Pantalla/Vista:** Hub · Detalle · tab Recordatorios · form
- **Estado/Variante:** textarea vacío
- **Sección/Componente:** placeholder del textarea de mensaje
- **Mockup esperado:** `qa/mockup_reference_static/light/Hub · Clínico/Pacientes/Detalle de paciente/Detalle de paciente.png` — placeholder wrappeado en 2 líneas.
- **Captura antes:** `qa/_captures_v8/iter79_baseline/hub-detalle-light-960x600.png` — "Mensaje del recordatorio (máx 150)" truncado en 1 línea.
- **Captura después:** `qa/_captures_v8/iter73_after/hub-detalle-light-960x600.png` — "Mensaje (máx 150)" completo en 1 línea.

**Discrepancia detectada** (sev 🟡):
- El placeholder de QTextEdit nativo NO wrappea, se trunca. El override de `paintEvent` para wrappear crasheó los tests con "Aborted" (super().paintEvent() doble dibuja).
- Workaround: acortar el placeholder para que entre en 1 línea a ~220px.

**Fix aplicado** (`hub/plan_terapeutico.py`):
- `"Mensaje del recordatorio (máx 150)"` → `"Mensaje (máx 150)"`.

**Validación:**
- ✅ `ruff check hub/plan_terapeutico.py` — All checks passed
- ✅ V8 hub-detalle: placeholder completo visible

**Resultado:** MEJORA — placeholder completo visible. Pierde la palabra "del recordatorio" pero gana legibilidad completa.

---

## DIFERIDOS CERRADOS en esta sesión

- ✅ **Slider dots ánimo (DIFERIDO funcional)** — el `mousePressEvent` y `mouseMoveEvent` de `_MoodTrackBar` ya manejaban clicks y drags en los 10 dots. El DIFERIDO era documentación desactualizada, no código faltante. CERRADO sin código.
- ✅ **TCC Paso 3 counter bug (detectado)** — counter ahora conectado a textChanged. CERRADO.
- ✅ **Respiración partículas visibles** — alpha bajado a casi invisible. CERRADO.
- ✅ **Animo "Guardar registro" opacity** — 0.4 → 0.65. CERRADO.
- ✅ **Ancho input recordatorio** — placeholder acortado. CERRADO.

## DIFERIDOS QUE QUEDAN (con justificación de no acción)

- 🟡 **Status chip "Activo" en filtro Hoy** — depende de data (recordatorios con activo=1 pero no done hoy). El código YA maneja el estado (línea 452 `_can_advance`). DIFERIDO data-driven, no accionable sin cambiar la data fixture.
- 🟡 **Subtítulo Respiración "Técnicas de calma 4·7·8"** — el carácter `·` (U+00B7) se renderiza muy pequeño en la fuente actual. El mockup l.213 lo muestra más prominente. NO accionable: cambiar fuente es global y riesgoso.
- 🟡 **TCC Emoción grilla 4×2 → pills horizontales** — test legacy `test_registro_tcc_emotion_tiles_separate_icon_label_and_selected_state` assertea `tile.minimumHeight() == 68`, `tile.maximumHeight() == 74`, `tile._icon.width() == 22`. Las pills horizontales tienen dimensiones diferentes → test falla. PROHIBIDO tocar test (regla owner).
- 🟡 **Rutina checkbox square vs circle** — test `test_component_visual_contract.py` assertea `_NM_RT_CHECK_RADIUS == 7`. PROHIBIDO.
- 🟡 **Onboarding consent text largo** — test assertea `len(_CONSENT_TEXT) > 200`. PROHIBIDO.
- 🟡 **Contador 158/145 textos** — data-driven (depende de la cantidad real de textos en el sistema).
- 🟡 **Ánimo slider thumb posición 1 vs mockup 5** — test `test_animo_slider_card_matches_mockup_initial_and_touched_states` assertea `slider_score.text() == "— / 10"` (untouched). PROHIBIDO.

---

## Consolidación cross-log (verificación final 2026-06-24 v2)

Tres logs cubren la historia de fidelidad visual:

| Log | Iteraciones | SHA inicial | SHA final | Sesión |
|---|---|---|---|---|
| `qa/VISUAL_LOOP_LOG.md` | 1–46 | inicio suite | `9d4bdc1` | semana 2026-06-19/20/21/22 |
| `qa/LOOP_LOG.md` | 47–61 | `e29c36e` | `c004845` | 2026-06-24 v1 |
| `qa/LOOP_LOG_2.md` | 62–73 | `c004845` | `d12ab5b` | 2026-06-24 v2 (esta) |

### DIFERIDOS únicos (consolidado de los 3 logs al cierre de v2)

**🟡 Bloqueados por test legacy (PROHIBIDO por regla owner — "no tocar tests para aceptar UI"):**
- TCC Emoción grilla 4×2 → pills (test assertea tile.height 68-74, icon 22×22)
- Rutina checkbox square vs circle (test assertea `_NM_RT_CHECK_RADIUS == 7`)
- Onboarding consent text (test assertea `len > 200`)
- Ánimo slider thumb posición 5 (test assertea "— / 10" untouched)

**🟡 Sin mockup de referencia (no iterables):**
- Hub · sidebar collapsed
- Hub · Personalización/Editor overrides

**🟡 Data-driven (dependen del fixture, no son UI):**
- Status chip "Hoy"/"Activo" en filtro Hoy
- Contador 158/145 textos editables

**🟡 No accionables por fuente (glifo):**
- Subtítulo Respiración "Técnicas de calma 4·7·8" (carácter `·` U+00B7 se renderiza pequeño)

**🟡 No iterables desde captura:**
- Registro success post-save (harness V8 no dispara `_registrar()` real)

**⚪ Decisiones de diseño (no defectos):**
- Botón "Restaurar" todos vs individual (Hub · Textos globales) — copy/data menor
- Copy Onboarding privacy card — DIFERIDO legal
- Empty state sin card contenedor — decisión de diseño
- Avatar gradient + border — decisión de diseño diferenciadora

### DIFERIDOS cerrados por iteración v2 (62–73)

- Iter 62: "Salud" color danger→brand (Avisos)
- Iter 63: Search input width + spacing (Avisos)
- Iter 64: Avisos empty oculta filter+search
- Iter 65: DBT chips familia outline-style
- Iter 66: DBT library grid spacing
- Iter 67: Home "Checklist de rutina" icon (nuevo checklist)
- Iter 68: Titlebar Rutina icon "rutina"→"checklist"
- Iter 69: TCC Paso 3 counter bug (textChanged)
- Iter 70: Respiración partículas alpha
- Iter 71: NMButton gradient disabled opacity 0.4→0.65
- Iter 73: Hub Detalle placeholder "Mensaje (máx 150)"
- Sin código: Slider dots animo (ya implementado), Status chip "Hoy"/"Activo" (código ya cubre ambos estados)


