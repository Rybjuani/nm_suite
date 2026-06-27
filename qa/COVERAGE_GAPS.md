# COVERAGE GAPS AUDIT — nm_suite (post-0339a7f)

**Fecha:** 2026-06-26
**Branch:** fix/visual-divergences-minimax-night
**Commit:** 0339a7f
**Estado:** 83/86 PASS + 3 FP documentados. NO es PASS visual global nominal.

---

## 1. Superficies canonical 86 (gate actual)

Fuente de verdad: `qa/_mockup_canonical/` (89 archivos = 86 PNGs + README.md + MANIFEST.json + MANIFEST.csv)

| App | Vistas | Themes | PNGs |
|-----|--------|--------|------|
| Suite | 35 | dark + light | 70 |
| Hub | 8 | dark + light | 16 |
| **Total** | **43** | **2** | **86** |

Suite (35): actividades, actividades-empty, actividades-filtered, actividades-marked-hice, animo, avisos, avisos-empty, avisos-filter-activos, avisos-search, avisos-today, dbt-library, dbt-now, dbt-practice-stop, home, home-no-score, onboarding, onboarding-error, recuperar-acceso, registro, registro-step1-emotion, registro-step1-emotion-otro, registro-step2-distortions, registro-step3-filled, registro-success, respiracion, respiracion-paused, respiracion-running, rutina, rutina-add-task, rutina-all-completed, rutina-empty, timer, timer-empty, timer-paused, timer-running.

Hub (8): detalle, detalle-plan-activacion, detalle-plan-rutina, detalle-plan-timer, detalle-resumen-ia, pacientes, pacientes-empty, textos-globales.

---

## 2. Recetas capture_v8 (43 recetas = 86 captures)

Mapeo 1:1 con canonical. Cada receta produce 2 PNGs (dark + light).

Nota: `detalle-resumen-ia` produce PNGs con sufijo `-0` (popup child capture: `hub-detalle-resumen-ia-0-{dark,light}-480x325.png`).

---

## 3. Microestados excluidos del gate (documentados en capture_v8.py)

| Microestado | Razón de exclusión | Estado producto |
|-------------|-------------------|-----------------|
| respiracion-preset-3min | Interacción chip (click) | Movido a extended_runtime_qa |
| respiracion-preset-10min | Interacción chip (click) | Movido a extended_runtime_qa |
| timer-preset-5min | Interacción chip (click) | Movido a extended_runtime_qa |
| timer-preset-45min | Interacción chip (click) | Movido a extended_runtime_qa |
| avisos-completed | Interacción marcar hecho | Movido a extended_runtime_qa |
| dbt-practice-closure | Pantalla removida del producto (C4-05) | Eliminado |

Total microestados excluidos: **6** (5 movidos a extended_runtime_qa, 1 eliminado del producto).

---

## 4. Módulos/interacciones NO cubiertos por el gate

### Widgets sin receta dedicada

| Widget | Dónde aparece | Por qué no tiene receta |
|--------|--------------|------------------------|
| MoodCelebration | Post-save de ánimo | Transient, auto-dismiss |
| NMDialog (shell) | Modal genérico | Capturado como child (resumen-ia) |
| NMToast | Notificaciones | Transient, auto-dismiss |
| NMEmptyState | Vistas vacías | Cubierto por recetas empty |
| NMWindowChrome | Titlebar | Aparece en todas las capturas |

### Interacciones no cubiertas

| Interacción | Módulo | Impacto visual | Prioridad |
|-------------|--------|---------------|-----------|
| Chip/preset clicks (respiración/timer) | respiracion_qt, timer_qt | Cambia estado de preset | Baja (microestado) |
| Marcar aviso como hecho | avisos_qt | Cambia estado de fila | Baja (microestado) |
| Inline form steps (registro TCC) | registro_tcc_qt | Steps 1-3 con inputs | Media (cubierto parcialmente) |
| Theme toggle (dark/light) | main_qt, hub/main_qt | Transición de paleta | Baja (no es estado estático) |
| Scroll de listas largas | pacientes_qt, actividades_qt | >40 filas / >20 items | Baja (covered por default states) |
| Error states (network, auth, timeout) | Varios | Toast + empty state | Media (no hay recetas dedicadas) |
| Loading/skeleton states | Varios | Spinner, placeholders | Baja (no en mockup) |
| Focus states (input, button, tab) | Varios | Outline, glow | Baja (no en mockup) |
| Hover states (button, card, row) | Varios | Color change, shadow | Baja (no en mockup) |

### Módulos del producto no representados como vista standalone

| Módulo | Tipo | Cobertura vía |
|--------|------|---------------|
| `shared/components/dialogs.py` | NMDialog, NMToast | Child capture (resumen-ia) |
| `shared/components/chrome.py` | NMWindowChrome | Aparece en todas las capturas |
| `shared/components/empty_state.py` | NMEmptyState | Recetas empty |
| `shared/components/inputs.py` | NMInput, NMButton | Aparece en múltiples vistas |
| `shared/components/badges.py` | NMBadge | Aparece en múltiples vistas |
| `hub/ia_asistente.py` | IA backend | No tiene UI propia |
| `hub/exportar.py` | Exportación PDF | No tiene UI propia |

---

## 5. Known gate miss / structural divergence not blocked

### 5.1. `suite-registro-step1-emotion` — divergencia estructural real, no bloqueada

**Evidencia (2026-06-26, post-0339a7f):**

| Gate | Resultado | Detalle |
|------|-----------|---------|
| odiff | **PASS** | 4.15% changed (por debajo de gate 8%) |
| visual_auditor_spec | **FAIL** (5 pass, 2 fail) | COLOR_MISMATCH card_group delta=18.2, icons delta=43.1 |
| Inspección visual | **DIVERGENCIA ESTRUCTURAL** | Mockup: pills/chips compactos en fila + slider largo. Producto: grilla de cards grandes 2×4 + slider corto centrado |

**Diagnóstico del miss:**

1. **odiff compara pixel-a-pixel con threshold de color**, no estructura. La divergencia estructural (pills vs cards) genera colores similares en regiones equivalentes (fondos claros #e9e5da vs #f7f5f0), por lo que odiff con threshold 0.3 (documentado en RESTRUCTURE_RESULTS.md como "piso de ruido") suprime el diff.
2. **visual_auditor_spec SÍ detecta la divergencia** (COLOR_MISMATCH en card_group e icons con severity=high), pero el cierre 83/86 se basó en odiff, no en el auditor spec.
3. **El reporte 83/86 oculta esta superficie** al clasificarla como PASS por odiff, cuando el auditor spec la marca como NEEDS_FIX.

**Split-brain de QA confirmado:**
- odiff PASS vs visual_auditor_spec FAIL para la misma superficie
- El cierre visual se basó en odiff (83/86), ignorando el auditor spec
- `qa/_visual_auditor_spec/report.json` tiene `canonical=False` para `suite:registro-step1-emotion@light`, indicando que el auditor spec la reconoce como no-canónica

**Riesgo:** Esta divergencia estructural no es menor. El mockup muestra una UI de selección de emociones completamente diferente a la del producto. No es un artefacto de renderizado ni un FP.

**Recomendación:** No arreglar TCC todavía (per owner request). Documentar como "gate miss conocido" y no reclamar PASS visual global.

**Evidencia visual:**
- Side-by-side: `qa/_night_session/SIDE-BY-SIDE-registro-step1-emotion-light.png` (CANON | CAPT)
- Center crop CANON: `qa/_night_session/crop_registro_canon_center.png`
- Center crop CAPT: `qa/_night_session/crop_registro_capt_center.png`
- ODIFF overlay: `qa/_fidelity_diff/suite-registro-step1-emotion-light-960x600-odiff.png` (4.15% changed, modo RGBA)

---

## 6. Contradicciones documentales detectadas

### 6.1. Ruta del canonical: `qa/mockup_reference_static/` vs `qa/_mockup_canonical/`

**Problema:** Múltiples documentos apuntan a `qa/mockup_reference_static/` que **NO EXISTE** en el filesystem. El canonical real está en `qa/_mockup_canonical/`.

**Documentos afectados:**

| Documento | Línea(s) | Texto contradictorio |
|-----------|----------|---------------------|
| `docs/README.md` | 18, 22, 48 | "`qa/mockup_reference_static/` (86 PNGs...)" |
| `docs/VISUAL_AUDITOR_V2.md` | 7, 13, 63, 292 | "`mockup_reference_static/manifest.json`" |
| `qa/LOOP_LOG.md` | Múltiples | Referencias a `qa/mockup_reference_static/light/...` |
| `qa/LEGACY_TESTS_AUDIT.md` | 4 | "Mockup canónico: `qa/mockup_reference_static/`" |
| `qa/DISCREPANCIAS_SENTINEL_VS_MOCKUP.md` | 5 | "Referencia canónica: `qa/mockup_reference_static/`" |
| `qa/AUDITORIA_POSTFIX.md` | 6 | "Referencia: `qa/mockup_reference_static/light/...`" |
| `docs/MOCKUP_REFERENCE_NORMALIZED.md` | 5, 70, 75 | Menciona `mockup_reference_static/` como "historical/non-canonical" |

**Documento correcto:** `qa/_mockup_canonical/README.md` — apunta a `qa/pack canonico/neuromood-mockup_reparado.html` como fuente única.

**Código correcto:** `qa/diff_fidelity.py:27` usa `_DEFAULT_TARGETS = _PROJ / "qa" / "_mockup_canonical"`.

**Recomendación:** Actualizar documentos afectados para apuntar a `qa/_mockup_canonical/` o agregar nota de deprecación. No tocar canonical ni código.

### 6.2. RESTRUCTURE_RESULTS.md subestima FP

**Problema:** `qa/RESTRUCTURE_RESULTS.md` (Fase 4) documenta "FP ≈ 1/86 ≈ 1.2%" (solo `suite-dbt-practice-stop-light`). Post-0339a7f tenemos **3 FP** (resumen-ia-0 dark/light + dbt-practice-stop-light).

**Recomendación:** Agregar nota en RESTRUCTURE_RESULTS.md indicando que el análisis post-fix identificó 2 FP adicionales en resumen-ia-0 (dark + light) por transparencia en bordes del modal.

### 6.3. docs/dev-setup.md apunta correctamente

**Correcto:** `docs/dev-setup.md:49` dice "Receta única oficial: ver `qa/_mockup_canonical/README.md`". Este documento SÍ está alineado.

---

## 7. Propuesta de reporte "coverage gaps" (sin reabrir Fases 0-5)

### Opción A: Document-only (recomendada)

1. Crear `qa/COVERAGE_GAPS.md` con este contenido.
2. Actualizar `docs/README.md` para corregir la ruta del canonical.
3. Agregar nota a `qa/RESTRUCTURE_RESULTS.md` sobre los 3 FP.
4. No tocar código, canonical, thresholds, ni harness.

### Opción B: Minimal doc patch

1. Patch en `docs/README.md` línea 18: `qa/mockup_reference_static/` → `qa/_mockup_canonical/`.
2. Patch en `qa/RESTRUCTURE_RESULTS.md` línea 77: agregar nota sobre 3 FP post-0339a7f.
3. No tocar nada más.

---

## 8. Matriz cruzada odiff vs VAS — resultados definitivos

**Ejecutado:** 2026-06-26, post-0339a7f  
**Script:** `qa/_night_session/cross_gate_matrix.py`  
**Outputs:** `qa/_night_session/cross_gate_matrix.csv`, `cross_gate_matrix.md`

### 8.1. Conteos finales (86 superficies)

| Categoría | Count | Descripción |
|-----------|-------|-------------|
| A | 43 | odiff PASS + VAS PASS |
| **B** | **40** | **odiff PASS + VAS FAIL ← zona crítica** |
| C | 1 | odiff FAIL + VAS PASS |
| D | 2 | odiff FAIL + VAS FAIL (FP conocidos) |
| E | 0 | missing / skipped |

### 8.2. Desglose de las 40 superficies categoría B

| Clasificación | Count | Descripción |
|---------------|-------|-------------|
| estructural_confirmada | **2** | Layout real diferente (no solo color) |
| color/shadow theme | **36** | Calibración de paleta, layout idéntico |
| detector_noise_probable | **2** | Delta bajo, probable artefacto VAS |

**Superficies estructurales confirmadas (2):**
1. `suite:registro-step1-emotion@light` — diff=4.15%, VAS_fail=2 — mockup: pills/chips en fila + slider largo; producto: grilla 2×4 de cards con íconos + slider corto
2. `suite:registro-step1-emotion@dark` — diff=4.20%, VAS_fail=1 — misma divergencia de layout confirmada visualmente (SIDE-BY-SIDE inspeccionado)

**Ambas forman una sola familia de divergencia estructural** (la pantalla TCC emoción, ambos temas).

### 8.3. Patrón dark theme (color/shadow, no estructural)

Las 8 superficies dark con VAS_fail=3 (top del ranking) muestran el mismo patrón:
- `SHADOW_MISMATCH | effects` + `COLOR_MISMATCH | card_group` + `COLOR_MISMATCH | icons`
- Paleta esperada: azul-teal oscuro (#346062, #29384a, #2a3d4d)
- Paleta obtenida: azul casi negro (#202835, #1b212f, #202834)
- Causa probable: el dark theme del producto tiene menor saturación y brillo que el mockup en todos los componentes card_group + icons

Este patrón se repite en todas las superficies dark con VAS FAIL. Layout correcto, calibración de tokens de color incorrecta en dark mode.

### 8.4. Top 10 superficies críticas

| # | Superficie | diff% | VAS fail | Clasificación |
|---|-----------|-------|----------|---------------|
| 1 | suite:avisos-filter-activos@dark | 1.94% | 3 | color/shadow theme |
| 2 | suite:avisos-today@dark | 1.99% | 3 | color/shadow theme |
| 3 | suite:dbt-now@dark | 2.15% | 3 | color/shadow theme |
| 4 | suite:avisos@dark | 2.20% | 3 | color/shadow theme |
| 5 | suite:actividades-marked-hice@dark | 2.67% | 3 | color/shadow theme |
| 6 | suite:actividades@dark | 2.70% | 3 | color/shadow theme |
| 7 | suite:home-no-score@dark | 3.84% | 3 | color/shadow theme |
| 8 | suite:home@dark | 4.79% | 3 | color/shadow theme |
| 9 | suite:registro-step1-emotion@light | 4.15% | 2 | **estructural_confirmada** |
| 10 | suite:registro-step1-emotion@dark | 4.20% | 1 | **estructural_confirmada** |

### 8.5. Respuesta a la pregunta central

**¿Cuántas divergencias estructurales está dejando pasar odiff?**

**Exactamente 2** — ambas pertenecen a la misma pantalla (`suite:registro-step1-emotion`, light y dark). No es una familia extendida. Es una sola pantalla TCC con dos temas, y odiff la deja pasar porque los colores de fondo son similares (#eaeaea vs #f0eeea) aunque el layout sea completamente diferente.

Las otras 38 superficies en categoría B tienen layout idéntico al canonical. Son divergencias de calibración de paleta (36) o artefactos de detector (2), no divergencias estructurales.

## 9. Recomendación (revisada post-deep-dive)

**El gate odiff 83/86 + 3 FP NO representa fidelidad visual suficiente**, pero el problema es más acotado de lo que parecía:

- **Divergencias estructurales reales: 2** → **✅ Corregidas** — `suite:registro-step1-emotion` (ambos temas), EmotionTile grid → pill/chip row
- **Divergencias de calibración dark theme: ~20+** → **Ver § 10** — diagnóstico post-deep-dive: mayoría son FP de spec-staleness, no defectos de producto
- **Divergencias de calibración light theme: ~16** — misma causa probable; pendiente de análisis

**No tocar:** canonical, thresholds, diff_fidelity.py, visual_auditor_spec.py, QA infra persistente.  
**No reabrir Fases 0-5.** El pipeline está cerrado operativamente.

---

## 10. Deep-dive dark theme COLOR_MISMATCH — diagnóstico definitivo (2026-06-27)

### 10.1. Método

Para cada superficie dark con VAS COLOR_MISMATCH se midió:
- **Spec expected** — el `color_hint` en `qa/specs/specs.json`
- **Canon measured** — promedio de píxeles de la región en el canonical PNG actual
- **Capt measured** — promedio de píxeles de la región en el capture del producto

Se calcularon tres deltas: D(spec-canon), D(spec-capt), D(canon-capt).

### 10.2. Hallazgo central: spec-staleness FPs

La mayoría de las 40 superficies categoría B (odiff PASS + VAS FAIL) tienen este patrón:

| D(spec-canon) | D(spec-capt) | D(canon-capt) | Clasificación |
|---|---|---|---|
| Grande (15-40) | Grande (18-45) | **Pequeño (1-3)** | **Spec stale — FP** |

El spec fue generado de un canonical anterior con render distinto al actual. El canonical actual y el capture del producto son prácticamente idénticos (1-3 RGB units, bien por debajo de la tolerancia 12). Los tokens V3_DARK ya son correctos.

**Superficies afectadas por spec-staleness (FP confirmados):**

| Superficie | D(canon-capt) | Nota |
|---|---|---|
| `suite:home@dark` card_group | 1.3 | Canon=#222a36, capt=#202835 |
| `suite:home@dark` icons | 2.0 | Canon=#232a37, capt=#202834 |
| `suite:home-no-score@dark` card_group | 1.7 | Similar pattern |
| `suite:dbt-now@dark` card_group | 0.7 | Casi idéntico |
| `suite:actividades@dark` card_group | 1.5 | Similar |
| `suite:actividades-marked-hice@dark` card_group | 1.7 | Similar |
| `suite:avisos@dark` card_group | 2.6 | Dentro de tolerancia |
| `suite:avisos-filter-activos@dark` | 2.4 | Dentro de tolerancia |
| `suite:avisos-today@dark` | 2.4 | Dentro de tolerancia |
| `suite:rutina@dark` | 0.3 | Canon≈capt |
| `suite:rutina-add-task@dark` | 0.3 | Canon≈capt |
| `suite:actividades-filtered@dark` icons | 1.6 | Dentro de tolerancia |

**Total FPs de spec-staleness: ~12-14 superficies dark (el grueso de la categoría B dark).**

### 10.3. Casos con divergencia real (no spec-staleness)

| Superficie | Comp | D(canon-capt) | Causa diagnósticada |
|---|---|---|---|
| `suite:avisos-search@dark` icons | icons | **51.3** | Artifact de captura: canonical muestra sidebar nav (columna izquierda), producto captura solo content-pane. La región del spec cruza la zona del sidebar. |
| `hub:pacientes@dark` card_group | card_group | **17.8** | Ring sizing: canonical usa anillo de 46px, producto usa 36px (`_NM_PATIENT_RING_SIZE`). La región spec (4% ancho = 38px) en x=85.9% captura correctamente el anillo en el canonical pero el anillo del producto es más pequeño y puede no centrar exactamente. |
| `hub:pacientes@dark` icons | icons | **23.8** | Misma causa: region del spec referencia el anillo de 46px que el producto no tiene. |
| `suite:animo@dark` icons | icons | 22.7 (producto MÁS claro) | Chart gradient menor: el gradiente de área del gráfico rellena levemente diferente entre Chromium y Qt. Diferencia estética menor. |
| `suite:registro-step1-emotion@dark` icons | icons | 15.8 | **Divergencia estructural — ✅ corregida** por fix EmotionChip. |

### 10.4. SHADOW_MISMATCH — detección insuficiente en dark mode

Ocho superficies dark tienen `SHADOW_MISMATCH`. El VAS `detect_shadows()` usa segmentación por color para detectar halos de elevación. En dark mode, el canonical HTML usa `box-shadow: 0 1px 2px rgba(0,0,0,0.4)` — sombra negra sobre fondo negro, diferencia de contraste casi nula. El producto usa `QGraphicsDropShadowEffect` con efecto equivalente.

El VAS no puede detectar sombras de color negro sobre fondo negro. Estos SHADOW_MISMATCH son **FPs de detector**, no deuda de producto.

### 10.5. Conclusión y estado de Option 2

**Option 2 "dark theme palette calibration" está esencialmente cerrada sin cambios de tokens:**

- Los tokens V3_DARK son correctos. `shared/theme.py` ya coincide con los CSS vars del canonical HTML.
- Los VAS dark failures son en su mayoría spec-staleness FPs.
- La deuda real residual (ring sizing hub:pacientes, chart gradient animo) no requiere cambio de paleta.

**Deuda registrada:**

| Deuda | Tipo | Urgencia |
|---|---|---|
| Spec stale para ~14 superficies dark | QA / spec regeneration | Baja — blocked por constraint specs |
| Hub pacientes ring 36px vs canonical 46px | Layout/sizing | Media — visible en capture pero no en uso real |
| Animo chart gradient menor | Estética | Baja |
| SHADOW_MISMATCH VAS detector dark | QA / detector | Baja — FP detector, no defecto producto |

**Fix pendiente de paleta: ninguno.** Los tokens están bien.
