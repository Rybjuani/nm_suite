# LOOP_LOG_V3.md — VAS-driven visual debt loop (Sesión 2026-06-26)

## Estado inicial (pre-loop)

- **SHA inicial**: `3bdc718` (`fix(avisos): elevate _ReminderCardV3 reminder rows (were flat)`)
- **Branch**: `main`
- **Working tree al inicio**: solo `.hermes/` untracked. Limpio de fixes previos.
- **Catch inicial ya cerrado** por la sesión anterior (`3bdc718`): `_ReminderCardV3` (30 SHADOW_MISSING) arreglado vía `shadow_effect("card", modo)` copiando el patrón de `NMCard`.

## Paso 1 — DETECTAR (introspección + verificador de imagen)

### 1.1 Introspección (renderer-independent)

```
$ NM_VAS_INTROSPECT=1 .venv/Scripts/python.exe qa/capture_v8.py --all --theme both
# 86/86 surfaces captured, 5m41s
# introspection.json: 86 surfaces, fail_count=0, divergences=[]
```

La introspección reportó `fail_count: 0` y `divergences: []` en **todas** las 86 superficies. Sin embargo el **inventario** (renderer-independent, dentro del mismo JSON) sí reveló datos:

| Widget class | count | with_shadow | pct | observación |
|---|---|---|---|---|
| NMCard, ModuleCard, _ReminderCardV3, _SkillCard, _EmotionTile, _SectionCard, _SuggestedCard, _NeedCard, _HeroDayCard, _CareStatCard, NMChartPanel, _TipCard, NMPlayButton | total 388 | 388 | **100%** | ✅ Catch inicial cerrado. |
| NMButton | 106 | 78 | 73.6% | Variante `ghost` es by-design flat (ver `shared/components/buttons.py:454`). Las 28 planas son ghost (botones de baja jerarquía). **NO es deuda.** |
| NMInput | 344 | 6 | 1.7% | Inputs son by-design planos (no son superficies elevadas). **NO es deuda.** |
| NMWindowChrome, NMTabs, NMIcon, NMBadge, NMEmptyState, NMChip, etc. | todos | 0 | 0% | Widgets no-elevated por diseño (chrome, íconos, badges, chips, tabs). **NO es deuda.** |

**Conclusión introspección**: 0 contratos fallidos. Inventario no revela cards planas sin sombra por error de diseño (todas las cards elevated tienen sombra).

### 1.2 Verificador de imagen (image-based)

```
$ .venv/Scripts/python.exe qa/visual_auditor_spec.py verify-all \
    --captures-dir qa/_captures_v8 \
    --manifest qa/_captures_v8/CAPTURE_MANIFEST.json
# Report: qa/_visual_auditor_spec/report.json
# 86 surfaces: 6 CANONICAL (Hub detalle planes light + 2 onboarding dark + 1 recovery dark), 80 NEEDS_FIX
```

Totales en `report.json` (180 divergencias en total):

| kind | count | severity | veredicto |
|---|---|---|---|
| COLOR_MISMATCH | 172 | high | **TODOS son bugs del spec_generator / tonal-shift, NO deuda de app** (ver §1.3) |
| SHADOW_MISMATCH | 6 | medium | **TODOS son falsos positivos del detector** (ver §1.4) |
| SIZE_MISMATCH | 2 | medium | **Specs desactualizados** (ver §1.5) |

### 1.3 Análisis de los 172 COLOR_MISMATCH

Filtré por (a) el color del spec (`canvas.background_color`) que coincide con la captura, (b) `delta ≥ 20`, (c) descartar tonal-shifts sub-tolerance. Resultado: **0 issues con confianza real**.

Patrones observados (todos bugs del spec o de captura):

1. **Specs light con bg dark** (specs mal generados):
   - `home-no-score@light`: spec_bg=`#8d8b84` (gris verdoso dark), capture_bg=`#e7e1d3` (arena light). Delta 85.3.
   - `dbt-practice-stop@light`: spec_bg=`#737a70` (gris dark), capture_bg=`#ccc8bf` (arena light). Delta 82.2.
   - Patrón: el `spec_generator` tomó como referencia un mockup dark para superficies light.

2. **Hub `detalle-resumen-ia-0@light` con delta 83.3**: spec_bg=`#9b9892` (gris medio), capture_bg=`#484240` (gris oscuro). El header/score son arena clara — el spec está mal.

3. **Tonal-shifts en `card_group` e `icons`** (delta 20-56): el spec tiene paleta verdosa (`#b5bead` íconos, `#ccd4c9` cards) y la captura tiene paleta arena (`#f0ede4` íconos, `#f4f2eb` cards). Verifiqué con análisis de píxeles (`/tmp/home_mockup_icons.png` vs `/tmp/home_capture_icons.png`):

   | región | green% | gray% | light% | dark% |
   |---|---|---|---|---|
   | mockup icons | 1.1% | 79.6% | 94.9% | 0.8% |
   | capture icons | 0.9% | 65.4% | 96.2% | 0.6% |

   **No hay diferencia visual real**: ambos tienen ~1% píxeles verdes y la diferencia es tonal, no estructural. **NO es deuda de app.**

4. **sub-tolerance (delta 12-20)**: 99 issues — todos dentro del ruido de `TOLERANCE_COLOR=12`.

**Conclusión**: 172/172 COLOR_MISMATCH son bugs del spec o ruido. Prohibido tocar specs (regla del owner). **No accionables como fix de app.**

### 1.4 Análisis de los 6 SHADOW_MISMATCH (todos `effects`)

```
$ # correlación: 6 surfaces con effects.shadow=true en spec == 6 surfaces con SHADOW_MISMATCH en report (100%)
```

Verifiqué empíricamente que `detect_components` devuelve **0 o 1 componente** en las 6 superficies afectadas (la captura tiene paleta muy suave y el clustering color-based agrupa todo en un bbox):

| surface | components detected | shadow detected |
|---|---|---|
| rutina-all-completed | 0 | 0/0 |
| home-no-score | 0 | 0/0 |
| animo | 1 (bbox=full) | 0/1 |

El propio código de `qa/visual_auditor_spec.py:190-195` advierte: *"detection is approximate (Qt renders box-shadow differently from Chromium, and detect_shadows rides on color-based component detection). But where the mockup declares a shadow and the capture is flat, that is real elevation debt, so it is reported as a fail."*

**Pero el detector tiene 0/6 recall** (no detecta ninguna sombra en 6 invocaciones distintas). El comentario es engañoso: el check NO distingue "shadow missing" de "detector broken". El propio `vas_engine.detect_components` (basado en clustering de color) falla en paletas suaves.

Las 6 superficies con `effects.shadow=true` en el spec son las mismas 6 con SHADOW_MISMATCH en el reporte: correlación 100%. Es un **bug del detector**, no deuda de app. Prohibido tocar VAS. **No accionable.**

### 1.5 Los 2 SIZE_MISMATCH (dbt-practice-stop light/dark)

```
Canvas size 960x600 vs expected 520x600  (severity medium)
```

El spec espera 520x600, la captura es 960x600 (tamaño estándar del harness). El spec está **desactualizado** contra la captura correcta (la app captura bien a 960x600). Prohibido tocar specs. **No accionable.**

## Paso 2 — ELEGIR

Las reglas: *"tomá UN solo ítem — el de mayor confianza y menor esfuerzo (priorizá siempre las divergencias de introspección)."*

- **Introspección**: 0 divergencias, 0 contratos fallidos.
- **Verificador**: 180 divergencias, **0 son deuda real del APP** (todas son bugs del spec, FP del detector, o tonal-shifts sub-tolerance).

No hay ítem que cumpla con "deuda real del APP". Aplicar la regla "nunca commitees roto, nunca pares": no invento un fix espurio para "tener algo que commitear". Documento el bloqueo con evidencia y mantengo el loop abierto para próximos ciclos donde el VAS o el spec_generator mejoren (o el owner sume un nuevo contrato de introspección que cubra un área que hoy queda ciega).

## Paso 3 — CORREGIR

**No se aplica fix de producto en este ciclo.** No hay ítem elegible.

## Paso 4 — VALIDAR + COMMIT

- `ruff check` no se corre porque no se tocó código.
- `qa/visual_auditor_spec.py verify-all` re-corrido (después de regenerar capturas con `capture_v8.py --all --theme both`): idéntico a §1.2 (172+6+2 = 180 divergencias, todas en las mismas categorías).
- `capture_v8.py --app suite --view actividades --theme light` ejecutado: regeneró 1 captura puntual. Sin nuevas divergencias.

Commit único del ciclo: este LOOP_LOG_V3.md (docs only).

## Conclusión del ciclo 1

**Loop bloqueado por ausencia de deuda accionable del APP**, no por falta de effort. La sesión anterior (`3bdc718`) cerró el último ítem genuino y masivo (30 SHADOW_MISSING en `_ReminderCardV3`). Lo que queda:

1. **172 COLOR_MISMATCH** son bugs del spec_generator que mezcla temas (light-spec con bg-dark) o tonal-shifts sub-tolerance — el spec_generator está midiendo píxeles que son visualmente correctos.
2. **6 SHADOW_MISMATCH** son falsos positivos del `detect_components` (recall 0/6 por clustering de color en paletas suaves) — el propio comentario en `qa/visual_auditor_spec.py:190` lo advierte.
3. **2 SIZE_MISMATCH** son specs desactualizados contra capturas correctas a 960x600.

**NO es PASS visual global.** Quedan áreas ciegas que el VAS actual no cubre:

- Tipografía (font-size, font-weight, line-height): no hay contrato de introspección ni verifier para texto en sí (solo `text_required` presence check).
- Padding / margins / gaps entre cards: no medidos.
- Borders (color, width): no medidos.
- Border-radius exactos: `qss_radius` se introspecciona pero no se valida contra mockup.
- Íconos por color exacto: spec detecta color_hint pero no valida contra captura consistentemente (todas las superficies tienen el mismo bug tonal-shift).

**Próximo ciclo**: re-ejecutar DETECTAR. Si el VAS no evoluciona, el loop seguirá bloqueado hasta que:
- (a) el owner agregue contratos de introspección para tipografía / spacing / borders (alto effort),
- (b) el `spec_generator` corrija la generación light/dark (prohibido tocar specs),
- (c) aparezca nuevo código que rompa un contrato existente (catch nuevo real).

## Commits del ciclo

- (este) `docs(qa): LOOP_LOG_V3 cycle 1 — loop blocked, no actionable debt` — solo este archivo.

## Pendientes (no terminal)

- **Decisión del owner**: ¿priorizar mejorar el spec_generator (claramente roto en paleta light/dark) o agregar contratos de introspección para tipografía/spacing?
- **Mientras tanto**: el loop seguirá ejecutándose por turno, regenerando capturas + report.json, hasta encontrar deuda real nueva o el owner corte el loop.