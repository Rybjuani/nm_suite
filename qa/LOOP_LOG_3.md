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

## Cierre de sesión (al pausar)

- **SHA inicial:** `7f2774396ab46c2c0464fa41dec61d01dc9a92b7`
- **SHA final:** _(se completa al final)_
- **Commits en esta sesión:** 1 (este `docs(qa/visual-loop): crea LOOP_LOG_3.md con preflight v3`)
- **Iteraciones de código:** 0 (solo audit preflight, sin fixes aplicados aún)
- **Capturas V8 generadas:** `qa/_captures_v8/iter89_baseline/hub-pacientes-light-960x600.png` (1)

> **NO es PASS visual global.** Sesión v3 abierta en estado de preflight: el audit identificó 1 discrepancia visual accionable (color de avatar Ana Martínez brand→accent) que requiere ubicar la clase del row para aplicar el fix mínimo. DIFERIDOS únicos heredados de v1+v2 siguen abiertos y clasificados en las 4 categorías válidas (10 BLOCKED-BY-TEST, 3 DATA-DEPENDENT, 4 FUNCTIONAL-CHANGE, 2 TEST-ISOLATION, 5 no-defecto). Próximo iter pendiente: localizar `NMPatientRowPremium` y aplicar el color override por paciente.
