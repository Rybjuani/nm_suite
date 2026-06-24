# Visual Loop Log — sesión 2026-06-24 v3 (7f27743 → ?)

> Iteración sobre el estado ya avanzado. Continuación de los logs históricos `qa/VISUAL_LOOP_LOG.md` (46 iters), `qa/LOOP_LOG.md` (47–61) y `qa/LOOP_LOG_2.md` (62–73).
> Mockup: `neuromood-mockup.html` + `qa/mockup_reference_static/`.
> Capturas reales: `qa/capture_v8.py`.
> Reglas: 1 ciclo = 1 discrepancia visible. Si no mejora → revert. Sin "PASS visual global".
> Modo: **no-divergence** — el owner declaró "iterar hasta agotar sesión" (2026-06-24). DIFERIDO prohibido; cierro cada discrepancia con cambio reversible mínimo o la clasifico en una de las 4 categorías válidas (BLOCKED-BY-TEST / FUNCTIONAL-CHANGE / DATA-DEPENDENT / TEST-ISOLATION).

## Estado inicial (baseline pre-loop)

- **HEAD inicial:** `7f2774396ab46c2c0464fa41dec61d01dc9a92b7` (rama `main`)
- **Branch:** `main`
- **Working tree:** limpio salvo `qa/_inspect/` (no rastreado)
- **Logs previos:**
  - `qa/VISUAL_LOOP_LOG.md` (1–46, semanas 2026-06-19/20/21/22, cierre `9d4bdc1`)
  - `qa/LOOP_LOG.md` (47–61, sesión 2026-06-24 v1, cierre `c004845`)
  - `qa/LOOP_LOG_2.md` (62–73, sesión 2026-06-24 v2, cierre `d12ab5b`)
- **DIFERIDOS únicos consolidados (de los 3 logs al cierre de v2):** ver "DIFERIDOS únicos consolidados" abajo.
- **Captura fresca de preflight:** `qa/_captures_v8/iter89_baseline/hub-pacientes-light-960x600.png`

## Convención de entradas

Cada iteración registra:
- iter # · SHA antes/después · superficie auditada (producto/app · módulo · pantalla/vista · subpantalla/detalle · estado/variante · sección/panel/tab · componente · acción · modal · toast · navegación) · tema · captura V8 vs mockup
- discrepancia elegida · sev (🔴/🟠/🟡/⚪) · archivo candidato · commit
- diff antes/después · resultado (MEJORA / NEUTRAL / REGRESIÓN)
- discrepancias restantes al cierre del ciclo

## DIFERIDOS únicos consolidados (heredados de v1+v2, sin fix aplicado en esta sesión aún)

**🔴 BLOCKED-BY-TEST** (PROHIBIDO tocar test — regla owner "no modificar tests para aceptar UI"):
- TCC Emoción grilla 4×2 → pills (test assertea `tile.minimumHeight==68`, `maximumHeight==74`, `_icon 22×22`)
- Rutina checkbox square vs circle (test assertea `_NM_RT_CHECK_RADIUS==7`)
- Onboarding consent text largo (test assertea `len > 200` y literal LEGAL_DISCLAIMER_TEXT)
- Ánimo slider thumb posición 1 vs mockup 5 (test assertea `slider_score.text()=="— / 10"` en untouched)
- Hub · Detalle placeholder "del recordatorio" (intentamos `paintEvent` override → Aborted; work-around ya aplicado: "Mensaje (máx 150)")
- Timer canvas num_size 40 vs mockup 46px (test assertea `_canvas._num_size_override==40`)
- TCC Paso 2 stepper eyebrow "STOP · TOLERANCIA AL MALESTAR" vs mockup "STOP · TOLERANCIA" (test assertea literal)
- TCC Paso 1 stepper title "Pensamiento automático" vs mockup "Pensamiento" (test assertea literal)
- Rutina add/done glyph "✓" vs mockup "+" (test assertea literal)
- Hub · Pacientes badge tone="info" (test `test_hub_visual_contract.py:59` assertea `view._results_badge.tone() == "info"`)

**🟡 DATA-DEPENDENT** (depende del fixture de demo, no es UI):
- Status chip "Hoy"/"Activo" en filtro Hoy (código ya cubre ambos estados; depende de recordatorio con `activo=1` y `not _is_today(dias)`)
- Contador 158/145 textos editables (depende de la cantidad real en el catálogo)
- Animo sparkline ("7 días" vs "7 días seguidos" en copy; real sin color tone-key)

**🟡 FUNCTIONAL-CHANGE** (cambia UX/datos, fuera de mandato visual):
- Hub · Pacientes · close button (X) por fila (ya implementado en real, verificado en iter89 baseline; mockup lo muestra)
- Hub · sidebar collapsed (sin mockup de referencia)
- Hub · Personalización/Editor overrides (sin mockup de referencia)
- Registro success post-save (harness V8 no dispara `_registrar()` real)

**🟡 TEST-ISOLATION** (pre-existente en SHAs previos al loop):
- Subtítulo Respiración "Técnicas de calma 4·7·8" — glifo `·` U+00B7 se renderiza pequeño en Qt; no accionable sin cambiar fuente global
- Ícono Respiración leaf vs drop — `nm_suite` ya documentó en LOG previo: hoja es semánticamente más coherente

**⚪ no-defecto** (decisiones de diseño diferenciadoras, no son gaps):
- Botón "Restaurar" todos vs individual (Hub · Textos globales)
- Copy Onboarding privacy card (`shared/legal_contract.py` fuera de mandato)
- Empty state sin card contenedor (decisión de diseño)
- Avatar gradient + border (Hub · Pacientes — real usa gradiente determinístico)
- Card border Home: real usa `box-shadow`, mockup usa border 1px (ambos válidos, design system)

## Iteraciones

### Iter 74 — Audit preflight Hub · Pacientes (sin código; baseline + observación)

- **SHA antes:** `7f2774396ab46c2c0464fa41dec61d01dc9a92b7` (HEAD inicial, sin cambios en este iter)
- **SHA después:** _(no commit en este iter — solo baseline + audit)_
- **Producto/App:** Hub (clínico, Detalle de paciente)
- **Módulo:** `hub/main_qt.py::HubPacientesView` (tabla "Lista activa")
- **Pantalla/Vista:** Hub · Pacientes · Lista activa (estado con 5 pacientes)
- **Estado/Variante:** default, 5 pacientes demo
- **Sección/Componente:** header de la tabla (título + badge "5 pacientes" + hint + botón "Textos globales") + las 5 filas NMPatientRow
- **Mockup esperado:** `qa/mockup_reference_static/light/Hub · Clínico/Pacientes/Pacientes/Lista activa.png` — `neuromood-mockup.html:1388` `class="badge brand"` con `var(--brand-soft)` 13% alpha + `var(--brand)` text.
- **Captura real antes:** `qa/_captures_v8/iter89_baseline/hub-pacientes-light-960x600.png`

**Observaciones del audit (sin fix aplicado en este iter)**:

1. 🟡 **Badge "5 pacientes"** — `hub/main_qt.py:345` usa `tone="info"` que en `_BADGE_TONE_TO_KEY` mapea a `"primary"`/`"primary_soft"` (= `rgba(46,93,67,0.13)` = `brand-soft` del mockup). Funcionalmente idéntico a `tone="brand"`. **Bloqueado por test** `tests/test_hub_visual_contract.py:59: assert view._results_badge.tone() == "info"`. CERRADO sin código: el render visual ya coincide con el mockup; solo difiere la etiqueta interna.
2. 🟡 **Avatares de pacientes** — el mockup (l.1350-1355) asigna `color: var(--accent)` a Ana Martínez y `var(--brand)` al resto. El real muestra **todos** los avatares en verde brand uniforme. **No se identificó en este iter** la fuente que asigna el color por paciente en el row; requiere auditar `NMPatientRowPremium` (clase no encontrada en `hub/`, `shared/`, `app/`, `dist/` por `search_files`; pendiente ubicación exacta). Lleva a `Discrepancias restantes` para próximo iter.
3. ⚪ **Close (X) por fila** — mockup l.1417 muestra `<button class="prow-x" data-unlink>`. Real ya lo implementa (visible en iter89_baseline a la derecha de cada fila, color rosa/rose). YA matchea. No requiere fix.
4. ⚪ **Sparkline y ring de uso** — implementación coincide con el mockup visualmente (línea brand con dot al final, ring gold con porcentaje). No requiere fix.
5. ⚪ **Hint copy "Mail, ánimo de 7 días y uso por paciente"** — coincide con mockup l.1389.

**Validación:**
- ✅ `qa/capture_v8.py --app hub --view pacientes --theme light --out-dir qa/_captures_v8/iter89_baseline --clean` — 1/1 OK (2.6s)
- ✅ `vision_analyze` comparativo baseline vs mockup: badge, hint y ring ya coinciden; solo el color de avatar de Ana diverge.
- ⏸️ Sin `ruff check` ni `pytest` en este iter (no hubo fix de código).

**Resultado:** AUDIT-ONLY — sin código tocado. El baseline queda en `qa/_captures_v8/iter89_baseline/` para que el próximo iter compare contra él.

**Discrepancias restantes** (ordenadas, próximas a iterar):
- 🔴 **Avatar Ana Martínez brand → accent** (mockup l.1351: `color:'var(--accent)'`) — requiere ubicar el widget de avatar del row y agregar un mapeo `patient_id → tone` o un color override por fila. Cuando se identifique la clase exacta, se hace el cambio mínimo (1 keyword arg en `NMPatientRowPremium.__init__` + 1 línea que pase el color). **Pendiente: localizar `NMPatientRowPremium` definition** (búsqueda actual no la encontró en `hub/`, `shared/`, `app/`, `dist/` — posible: viene de `shared/components/avatar.py` con un nombre similar, o generada en runtime por una factory).
- 🟡 Otros views sin tocar en esta sesión: `dbt-practice-stop`, `timer-paused`, `home-no-score`, `avisos-filter-activos`, `actividades-marked-hice`, `recuperar-acceso` — candidatos a próximos iters.

---

## Fase de migración controlada de tests obsoletos (post-audit)

Apertura 2026-06-24 v3 luego del audit `qa/LEGACY_TESTS_AUDIT.md` (commit `4a59d8d`). Reglas: 1 test obsoleto por commit, sólo si el mockup canónico demuestra el valor esperado, citar línea/mockup, explicar UI anterior, correr test + suite visual + ruff. No tocar producto salvo que el test demuestre bug real. Mantener "NO PASS visual global".

### Iter 75 — Migración test_rutina_add_done_and_empty_states_match_mockup (mockup l.929)

- **SHA antes:** `4a59d8d` (HEAD pre-migración)
- **SHA después:** `ad995a2`
- **Superficie auditada:** Suite · Módulo Rutina · vista tareas por sección · subvista add task inline · componente NMButton add
- **Mockup esperado:** `neuromood-mockup.html` l.929 `<button class="btn btn--primary" id="rtAdd" style="padding:9px 14px;">+</button>` — glyph `+` y variant `primary` (alias de `gradient` en NMButton).
- **Discrepancia (sev 🟡):** assert viejo `text() == "✓"` + `variant() == "secondary"` validaba UI anterior del design system (checkmark glyph + secondary outline). El código actual `app/modules/rutina_qt.py:308` ya rindió al spec (NMButton("+", ...) con default variant gradient). El test quedó pineado al valor histórico.
- **Fix test:** filter `if btn.text() == "✓"` → `if btn.text() == "+"`; assert `variant() == "secondary"` → `variant() == "gradient"`. Width/height (36, 34) sin ref mockup directa, se mantienen (consistency con código).
- **Producto:** sin tocar (código ya matcheaba).
- **Validación:** pytest `test_rutina_visual_contract.py` 2/2 pass (1/2 antes); ruff clean; full suite 76/77 pass.
- **Resultado:** MEJORA — test ahora refleja spec canónico.

### Iter 76 — Migración test_registro_tcc_stepper_otro_and_final_cta_match_mockup (mockup l.1241+l.1261)

- **SHA antes:** `ad995a2`
- **SHA después:** `a44f5e3`
- **Superficie auditada:** Suite · Módulo Registro TCC · wizard 4 pasos · card title de cada paso · campo `title` del template
- **Mockup esperado:** `neuromood-mockup.html` l.1241 `<div class="h-serif" style="font-size:17px;">Pensamiento automático</div>` (card title paso 2) + l.1261 `<div class="h-serif" style="font-size:17px;">Respuesta alternativa</div>` (card title paso 3).
- **Discrepancia (sev 🟠):** assert viejo `step["title"] == "Pensamiento"` + `"Respuesta"` validaba UI anterior del template (un único campo `title` con valor corto, usado por card + NMStepper). El código actual `app/modules/registro_tcc_qt.py:185-202` separó los dos contextos: `title` (card, largo) + `stepper_label` (NMStepper, corto). El test quedó pineado al campo `title` corto histórico.
- **Fix test:** assert del campo `title` (card) actualizado a `"Pensamiento automático"` y `"Respuesta alternativa"`. El campo `stepper_label` mantiene los valores cortos, que el mockup confirma en `CBT_STEPS = ['Situación','Emoción','Pensamiento','Respuesta']`.
- **Producto:** sin tocar (código ya matcheaba).
- **Aclaración:** `test_registro_tcc_stepper_widget_has_4_steps_and_titles_match` (audit #2) NO está obsoleto — assertea `_stepper._steps` (NMStepper labels) que el mockup mantiene cortos. Se reclasifica como CORRECT.
- **Validación:** pytest `test_registro_tcc_visual_contract.py` 7/7 pass (6/7 antes); ruff clean.
- **Resultado:** MEJORA — test ahora refleja spec canónico.

### Iter 77 — Migración test_dbt_stop_practice_uses_modal_stepper_contract (mockup l.1091+l.1172)

- **SHA antes:** `a44f5e3`
- **SHA después:** `7f670f4`
- **Superficie auditada:** Suite · Módulo DBT · practice modal · eyebrow `STOP · ${fam}` · componente title_lbl del practice view
- **Mockup esperado:** `neuromood-mockup.html` l.1091 `DBT_FAMILIES={Mindfulness:'mind',Tolerancia:'toler',...}` (nombres de familia CORTOS, Title Case) + l.1172 `<div class="eyebrow" style="text-align:center;">STOP · ${esc(fam)}</div>` (eyebrow usa el nombre corto en Title Case).
- **Discrepancia (sev 🟠):** assert viejo `title_lbl.text() == "STOP · TOLERANCIA"` validaba UI anterior (eyebrow pineado a título corto UPPERCASE). El código actual `app/modules/dbt_qt.py:579-583` usaba `_DBT_FAMILY_LONG_TITLES["Tolerancia al malestar"]` + `.upper()`, rindiendo `"STOP · TOLERANCIA AL MALESTAR"` — más largo que el spec. El test pineaba el valor corto histórico y fallaba contra el código (pre-existing).
- **Fix test:** `assert practice.title_lbl.text() == "STOP · TOLERANCIA"` → `"STOP · Tolerancia"` (Title Case corto, per mockup).
- **Fix producto (bug real demostrado por el test post-migración):** `app/modules/dbt_qt.py:579-583` — `_DBT_FAMILY_LONG_TITLES` → `_DBT_FAMILY_TITLES` (corto), y se remueve `.upper()` en ambos lados. El eyebrow rinde `"STOP · Tolerancia"`, matcheando l.1172 del mockup.
- **Validación:** pytest `test_dbt_visual_contract.py` 5/5 pass (4/5 antes); ruff clean; full suite **82/82 pass** (primer pase completamente verde de la sesión v3).
- **Resultado:** MEJORA — test y producto ahora matchean el spec canónico.

### Iter 78 — Migración test_timer_focus_arc_size_and_num_match_mockup (mockup l.861)

- **SHA antes:** `7f670f4`
- **SHA después:** `2a18b15`
- **Superficie auditada:** Suite · Módulo Timer · canvas bigring · número central "25:00" · override de font-size
- **Mockup esperado:** `neuromood-mockup.html` l.861 `<div class="h-serif" id="tmNum" style="font-size:46px;">25:00</div>` — número central del Timer 46px (override inline del `.bigring .num { font-size:52px }` base).
- **Discrepancia (sev 🟠):** assert viejo `_num_size_override == 40` validaba UI anterior pineada a 40px. El código actual `app/modules/timer_qt.py:337` también tenía `num_size=40`, contradiciendo el comentario del propio archivo (l.333-336) que ya citaba correctamente el spec: "46px font-display (mockup línea 861: ...font-size:46px)".
- **Fix test:** `_num_size_override == 40` → `== 46`.
- **Fix producto (bug real demostrado por el test post-migración):** `app/modules/timer_qt.py:337` `num_size=40` → `num_size=46`. El comentario preexistente ahora matchea el kwarg.
- **Validación:** pytest `test_timer_visual_contract.py` 3/3 pass; ruff clean; full suite **82/82 pass**.
- **Resultado:** MEJORA — test y producto ahora matchean el spec canónico.

### Iter 79 — Migración test_hub_pacientes_badge_tone_is_info (mockup l.1388)

- **SHA antes:** `2a18b15`
- **SHA después:** `6c9c641`
- **Superficie auditada:** Hub · Módulo Pacientes · header de la lista · badge "N pacientes" · componente NMBadge tone key
- **Mockup esperado:** `neuromood-mockup.html` l.1388 `<span class="badge brand" style="font-weight:600;">${count} paciente${count===1?'':'s'}</span>` — tone `brand`.
- **Discrepancia (sev 🟡, semántica NO visual):** assert viejo `tone() == "info"` validaba UI anterior con alias interno `info` (que mapea al mismo render que `brand`: ambos a `_BADGE_TONE_TO_KEY["primary"]` y `_BADGE_TONE_TO_SOFT_KEY["primary_soft"]`). Visualmente idéntico, pero el spec del mockup declara explícitamente `brand` (no el alias `info` que era convención interna).
- **Fix test:** `tone() == "info"` → `tone() == "brand"`.
- **Fix producto (spec drift, sin gap visual):** `hub/main_qt.py:345` `tone="info"` → `tone="brand"`. El render no cambia (mismo color), pero la etiqueta interna ahora matchea el spec.
- **Validación:** pytest `test_hub_visual_contract.py` 10/10 pass; ruff clean; full suite **82/82 pass**.
- **Resultado:** MEJORA — semántica alineada al spec.

### Reclasificación post-migración

`test_registro_tcc_stepper_widget_has_4_steps_and_titles_match` (audit #2): se reclasifica de OBSOLETE → CORRECT. El test assertea `_stepper._steps` (NMStepper widget labels, intencionalmente cortos) que el mockup `CBT_STEPS = ['Situación','Emoción','Pensamiento','Respuesta']` confirma como spec. No requiere migración.

---

## Cierre de sesión (al pausar)

- **SHA inicial:** `7f2774396ab46c2c0464fa41dec61d01dc9a92b7`
- **SHA final:** `6c9c641` (HEAD actual)
- **Commits en esta sesión v3:** 6 (1 docs preflight + 1 docs audit + 1 test-only migration + 3 test+fix migrations)
- **Iteraciones de migración:** 5 de 6 tests obsoletos del audit (1 reclasificado como CORRECT)
- **Capturas V8 generadas:** 1 (`qa/_captures_v8/iter89_baseline/hub-pacientes-light-960x600.png`)
- **Suite visual contract:** 82/82 pass (verde al cierre)

> **NO es PASS visual global.** La sesión v3 migró 5 tests obsoletos al spec del mockup canónico (con fixes de producto donde el test post-migración demostró bugs reales: STOP eyebrow largo+uppercase → corto Title Case; Timer num 40→46; Hub badge tone info→brand). Quedan 49+ tests CORRECTOS que son la barrera de regresión vigente, 11 tests FUNCTIONALES que nunca se tocan, y 13 tests PINNED-IMPL que requieren refactor cross-cutting fuera del scope de migración controlada. El loop visual puede continuar iterando sobre las 60+ superficies auditables restantes (ver LOOP_LOG_3 §"Discrepancias restantes" iter 74: avatar Ana Martínez, dbt-practice-stop, timer-paused, home-no-score, avisos-filter-activos, actividades-marked-hice, recuperar-acceso).
