# Plan de propagación — dirección visual aprobada → app PyQt6 real

## Context

El mockup `design/mockup_completo.html` (49 pantallas‑estado, Suite + Hub, claro/oscuro) fue **aprobado** como la dirección visual definitiva. Ahora hay que llevar ese polish a la **app PyQt6 real**, completa.

Hallazgos de la auditoría que enmarcan el trabajo:
- **El mockup derivó sus tokens del propio `shared/theme.py`** (V3_LIGHT/V3_DARK). La paleta, spacing y radius base **ya coinciden** — el polish real es de **tratamiento de superficie/jerarquía/estados**, no de paleta.
- **Las fuentes reales ya existen** (`assets/fonts/`: Newsreader, Manrope, JetBrains Mono) y `shared/fonts.py` las carga; varios componentes ya usan serif (`v3_font(..., serif=True)`). La tipografía es de *consistencia*, no de introducir nada nuevo.
- **`NMCard` hoy es plano a propósito** (`cards.py:263` comenta "card limpia, sin glass ni highlights"). El mockup agrega un *lift* superior, sombras más calibradas y bordes que “se leen” en claro.
- **Los tests de tokens son estructurales, no de valores**: `tests/test_token_parity.py` verifica que los adaptadores de `design_tokens` sigan a `V3_LIGHT/V3_DARK` y que se reusen los objetos (`SPACING is V3_SPACE`, etc.); `tests/test_no_legacy_visuals.py` solo verifica helpers + módulos removidos. **Cambiar valores de `V3_SHADOWS`/bordes es seguro** mientras se conserve la estructura (adaptadores y objetos reusados).

**Decisiones del owner:**
1. **Evolucionar tokens globales** — ajustar `V3_SHADOWS`/bordes/lift en `shared/theme.py` + helpers para que el cambio sea sistémico (afecta todas las superficies, no solo las del mockup).
2. **Rollout por fases con checkpoints** — Foundation → Suite → Hub → Regresión; cada fase regenera capturas + corre tests para revisión antes de seguir.

**Fuentes de verdad (orden):** el **código activo** + las **capturas reales** (`qa/nm_capturas_actualizadas/`) definen el **inventario funcional** = qué funciones, textos, controles y estados existen. El mockup `design/mockup_completo.html` es **solo referencia estética** — no se copia literalmente (menos aún sus layouts defectuosos).

**Libertad de layout (corrección bloqueante del owner — reemplaza la restricción de "densidad" del pedido original, que fue retirada por errónea):**
- **Invariantes duros (lo único bloqueado):** no agregar funciones/textos/controles/estados que no existan; no eliminar nada que exista hoy en la app.
- **Libre:** redistribuir, redimensionar y **cambiar densidad / espaciado / tamaños** cuando mejore el resultado. Corregir gigantismos, compresión, desalineaciones, espacios vacíos excesivos y tamaños incoherentes. La disposición y densidad de la captura **NO están bloqueadas** — la captura solo fija el *set de elementos presentes*, no su geometría exacta.
- **Meta:** conservar el polish global y hacer ajustes concretos y perceptibles; la app **no debe quedar igual al diseño original**.

**Guardrail:** trabajar en rama feature `visual/propagacion-mockup` (ya creada). Commit + capturas + tests por fase. Nada en `main` hasta aprobación.

---

## Estado actual (ya ejecutado y committeado)

- **Fase 0 — DONE** (`ba1bc28`): `V3_LIFT` + recalibración de sombra de card en `theme.py`; helper `paint_card_lift` en `theme_qt.py`; lift aplicado a la familia `NMCard`. 225 tests verdes, 0 ruff nuevos.
- **Fase 1 — HECHA** (`7352652` + revisita Codex): se conservó lo válido de la primera pasada y se profundizó con libertad de layout en Home, TCC, Ánimo, Rutina y DBT. Checkpoint Suite completo: 82 capturas claro/oscuro generadas, 0 fallos técnicos; flags parciales solo en estados QA dependientes de datos/duplicados (`home-no-score`, `animo-note-filled`, `rutina-add-task`).
- **Fase 2 — HECHA** (Codex): se conservó lo válido de la pasada Hub (título serif en Textos globales, jerarquía en detalle, filas asignadas unificadas, recetas QA para Textos globales y Resumen IA) y se profundizó corrigiendo el vacío interno de Pacientes y Plan terapéutico. Checkpoint Hub completo: 18 capturas claro/oscuro generadas, 0 fallos técnicos.

**Esta revisión del plan** retira la restricción de densidad → **Fase 1 se revisita con libertad** para atacar los gigantismos / vacíos que esa restricción había frenado, y la libertad aplica también a Fase 2 (Hub) y al cierre.

---

## Fase 0 — Foundation (tokens globales + componentes compartidos)  ✅ HECHA

Es el grueso del valor: al refinar la capa compartida, la mayoría de las pantallas heredan el polish sin tocarlas una por una.

**Tokens globales — `shared/theme.py`:**
- `V3_SHADOWS` (línea ~246): recalibrar a las sombras del mockup (más suaves, en capas; tinta de marca en light, negro estratificado en dark). Mantener estructura `{blur, offset, color}` para no romper `v3_shadow()`/`shadow_*`.
- Agregar spec de **lift** (highlight superior interno): `V3_LIFT = {"light": alpha, "dark": alpha}` (equivalente al `linear-gradient(180deg, rgba(255,255,255,.55), transparent 42%)` del mockup).
- Bordes: subir el borde de reposo de cards en light al nivel `borderStrong` del mockup (que “lee” sin gritar). Ajuste de valor, no de estructura.

**Helpers — `shared/theme_qt.py`:**
- `paint_card_lift(painter, rect, radius, modo)` — pinta el highlight superior (QLinearGradient vertical translúcido). Qt no tiene inner‑gradient CSS; se dibuja en `paintEvent` tras el relleno de superficie.
- (opcional) `card_border_pen(modo, state)` para unificar reposo/hover/active/selected.

**Componentes compartidos (aplicar tratamiento aprobado):**
- `shared/components/cards.py` — `NMCard.paintEvent` (`:249`): llamar `paint_card_lift` tras el relleno; borde de reposo `borderStrong` en light; conservar hover/active. Replicar lift+sombra en los `paintEvent` propios de `NMStatCard`, `NMMetricCard`, `NMFeaturedCard`, `NMAvisoCard`, `NMCardSecondary`.
- `shared/components/surfaces.py` — `NMChip` (`:112`) y `NMBadge` (`:212`): alinear al patrón del mockup (fondo tintado del tono + tinta del mismo tono + borde hairline; radius 8 pills / 999 badges; semibold 11px).
- `shared/components/buttons.py` — `NMButton` (`:86`): refinar estados primary/secondary/ghost/danger (hover con leve `translateY`/brillo, focus‑ring `primary-soft`). `NMInput`/`NMTextArea`/`NMSearchInput`: focus‑ring `primary-soft`. `NMTabs` (`:909`): segmento activo = relleno `primary` con tinta invertida (como el mockup).
- `shared/components/overlays.py` — `NMEmptyState` (`:53`): título serif + tile de icono `primary-soft` (ya cercano; verificar).
- `shared/components/rings.py` y `patient.py` (`NMModuleRing`, `NMSparkline`, `NMAreaSparkline`, `NMPatientRowPremium`): ya reproducen el arco firma + sparkline de área del mockup → **cambios mínimos/nulos** (solo validar contra el mockup).
- `shared/components/chrome.py` — `NMWindowChrome` (`:160`): glyph en tile `primary-soft`, hover de controles, close → danger (paridad con el chrome del mockup).

**Checkpoint Fase 0:** regenerar set V8 + tests (ver Verificación). Inspeccionar 6–8 superficies representativas claro/oscuro contra el mockup. Pausa para revisión del owner.

---

## Fase 1 — Consumidores Suite (revisita con libertad)  ✅ HECHA

Las cards heredan el polish de Fase 0. Acá se atacan, **con libertad de redistribuir/redimensionar/cambiar densidad**, los problemas reales de cada pantalla (respetando los invariantes funcionales). Issues detectados en las capturas actuales y fixes candidatos:

- **TCC** — `app/modules/registro_tcc_qt.py`: **gigantismo** del textarea (~340px para “contá en pocas palabras”). Reducir a un alto coherente con el contenido esperado y rebalancear el paso (stepper/heading/textarea/contador/footer) para que no sea un campo enorme casi vacío. Mismo criterio en los pasos pensamiento/respuesta.
- **Home** — `app/home_qt.py` (`ModuleCard`): **vacío interno** de las module cards (icono+chip arriba, título/desc, hueco grande, pill abajo por el `addStretch`). Compactar/redistribuir el contenido y/o revisar `setMaximumHeight(288)` para que las cards no sean altas con un void central; mantener las 8 cards y el grid.
- **Ánimo** — `app/modules/animo_qt.py`: card izquierda “Escala emocional” con **gran vacío arriba** del slider mood (el slider y los números quedan abajo). Subir/centrar el bloque slider+números+CTA para repartir el aire; revisar el alto relativo de las dos columnas.
- **Rutina** — `app/modules/rutina_qt.py`: columnas Mañana/Tarde/Noche a **altura completa con pocas tareas** → void inferior grande. Dimensionar las section cards a su contenido (top-align) o repartir el aire, sin perder la lectura de 3 columnas.
- **DBT Ahora** — `app/modules/dbt_qt.py` (`_NeedCard`): cards 2×2 **grandes con vacío interno** (swatch arriba, título/desc abajo, hueco). Compactar y distribuir el contenido; Biblioteca/Práctica/Cierre revisar densidad y alineación.
- **Respiración / Timer / Actividades** — primera pasada ya mejoró orb, centrado y 2×2; afinar solo si la nueva latitud revela algo (p.ej. tamaño del orb, columnas).
- **Avisos** — `app/modules/avisos_qt.py`: filas y segmented OK; ajustar solo si se detecta compresión/void.
- **Onboarding** — `app/onboarding_qt.py`: distribución OK; ajustar solo si hace falta.

Criterio por pantalla: nada de “porque sí” — solo donde haya gigantismo, void, compresión, desalineación o tamaño incoherente. Cambio perceptible, polish conservado, inventario funcional intacto.

**Checkpoint Fase 1:** regenerar recetas `suite/*` (todos los estados), inspeccionar claro/oscuro, tests. Pausa para revisión.

---

## Fase 2 — Consumidores Hub (con la misma libertad de layout)  ✅ HECHA

Aplica la misma latitud: corregir gigantismos/voids/compresión del Hub (p.ej. los paneles derechos del Detalle con empty-states centrados en cards muy altas; distribución de los formularios izquierdos; alineación del header del detalle), sin tocar el inventario funcional.

- Pacientes — `hub/main_qt.py` (`PacientesView`, ~`:258`): meta roster + badge + botón Textos globales, header de columnas, filas (`NMPatientRowPremium` ya pulido), empty state.
- Detalle + Plan — `hub/pacientes_qt.py` (`DetallePacienteView`) + `hub/plan_terapeutico.py`: header con avatar + Exportar PDF/Resumen IA, tabs segmentadas, formularios izquierda + panel derecho con empty states (Recordatorios/Temporizador/Rutina/Activación).
- Resumen IA (dialog) — el modal de muestra (paridad con `detalle-resumen-ia`).
- Textos globales — `hub/config_global_texts.py`: título serif, buscador, dropdown módulo, badge “N textos”, filas editables (módulo/nombre/default/input/contador/Restaurar), footer.

**Checkpoint Fase 2:** regenerar recetas `hub/*`, comparar con el mockup, tests. Pausa para revisión.

---

## Fase 3 — Regresión y evidencia

- Regenerar V8 completo y confirmar 0 fallos / 0 duplicados.
- Revisión final pantalla‑a‑pantalla, claro y oscuro: polish aplicado + layout sano (sin gigantismo/void/compresión) + inventario funcional intacto. El mockup se usa como referencia estética, no como geometría a calcar.
- Actualizar `docs/QA_V8_BASELINE_MATRIX.md` si corresponde.
- Gates verdes (ruff + pytest + smoke). Commit final + push de la rama; abrir PR para revisión.

---

## Verificación (end‑to‑end)

Comandos (Windows, `.venv`):
- Capturas: `.venv\Scripts\python.exe qa\capture_v8.py --all` → `qa/_captures_v8/` (132 capturas). Por pantalla: `... --app suite --view animo --theme both`.
- Tests: `.venv\Scripts\python.exe -m pytest tests/` — debe seguir verde, en especial `test_token_parity.py` y `test_no_legacy_visuals.py` (estructura intacta).
- Lint: `ruff check --select E,F` sobre archivos tocados + `py_compile`.
- Smoke runtime: `.venv\Scripts\python.exe qa\runtime_live_probe.py --all --theme both` (OK esperado, 0 defects).
- **Diff visual contra el spec**: renderizar la pantalla del mockup (Playwright, ya en `.venv`: iterar `.nav` + `setTheme()`, como `qa/_mockup_verify2/`) y comparar lado a lado con la captura V8 equivalente.

Criterio de “hecho” por fase: gates verdes + cada superficie inspeccionada claro/oscuro con el polish aplicado y los problemas de layout (gigantismo/void/compresión/desalineación) corregidos, conservando el inventario funcional. El mockup orienta la estética; **no** es el patrón de geometría a calcar.

## Riesgos / guardrails

- **Blast radius global**: al evolucionar `V3_SHADOWS`/bordes/lift, superficies fuera del set del mockup también cambian. Mitigación: el set V8 (132 capturas) cubre prácticamente toda la UI navegable → la regresión por fase detecta regresiones; inspección claro/oscuro obligatoria.
- **Tests estructurales**: no redefinir la *forma* de los tokens (mantener `dict` de shadows con `{blur,offset,color}`, reusar objetos `V3_SPACE`/`V3_RADIUS`/`V3_SHADOWS`, adaptadores que siguen a V3). Cambiar valores es seguro; cambiar estructura rompe parity.
- **Inventario funcional intacto (único bloqueo)**: no agregar ni quitar funciones/textos/controles/estados; no eliminar nada que exista. La **disposición/densidad/tamaños SÍ son libres** de mejorar. No se inventan buscadores/filtros/acciones inexistentes ni se eliminan los existentes.
- **Regresión de layout**: cambiar densidad/tamaños puede romper otros estados (empty, datos abundantes, dark). Mitigación: regenerar **todos** los estados de la receta (no solo el principal) y verificar light/dark antes de cerrar cada pantalla.
- Rama feature + commits por fase; nada en `main` hasta aprobación.
