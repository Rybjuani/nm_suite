# VISUAL_DEBT_FINAL — Deuda visual residual owner

**Fecha:** 2026-06-22  
**Base:** main (post C6-FINAL-EVIDENCE, `7807c06`)

## Clusters ejecutados

### CA · Avisos — filtros y track segmentado
- `_filter_segment.setFixedHeight(40)` — track pill-shape fijo, sin colapso ni expansión
- `_search_input.setFixedHeight(40)` — búsqueda alineada al track
- `filter_row.setAlignment(AlignVCenter)` — alineación vertical uniforme

### CB · Timer — ring viewport + V2-P1-040 resuelto
- `NMFocusArc(size=230)` → `size=180`, `num_size=46` → `40` — ring no domina viewport
- Fuente del arco 48→40 (`v3_font(40, ...)`)
- `timer_card.setMinimumHeight(300)` → `280`
- Empty state: `stretch=0` + `addStretch(1)` después → card compacta cuando no hay actividad
- Test actualizado: `assert width==180`, `assert _num_size_override==40`
- **V2-P1-040 cerrado** — propuesta visual aprobada por owner

### CC · Rutina — botón "✓" blob + empty state vacío inferior
- `NMButton("✓", ..., width=36)` → eliminar `width=36`, agregar `setFixedWidth(40)` explícito
- `lay.addStretch(1)` después de `_sections_grid_widget` en `build_ui()` — elimina vacío inferior

### CD · Hub Pacientes — scrollbar visible innecesaria
- Overhead 100→108 en `_sync_table_card_height`
- Scrollbar `AlwaysOff` cuando `visible ≤ 5`, `AsNeeded` cuando más

### CE · Hub Activación Conductual — form comprimido + IA desconectado + tabs
- Tabs: padding `4px 9px 11px` → `6px 12px 12px` — jerarquía/densidad mejorada
- Márgenes form: `(0, 8, 0, 8)` → `V3_SP["sm"]` × 4
- Espaciado form: `setSpacing(8)` → `V3_SP["sm"]`
- Placeholders de inputs con descripciones más claras
- "Completar con IA" fusionado en `action_row` junto a "Agregar actividad" — ya no flota sola
- Card form alto: 316 → 340 (espacio extra por action_row combinado)
- Card lista: `ContentsMargins(10,10,10,10)` → `V3_SP["md"]`; alto 316 → 340

## Tests focales

```
47 passed (test_timer_visual_contract, test_rutina_visual_contract,
           test_avisos_visual_contract, test_hub_visual_contract,
           test_component_visual_contract)
```

## Capturas focales after

20 PNGs (10 views × 2 temas):
- avisos, avisos-empty
- timer, timer-empty
- rutina, rutina-empty, rutina-add-task
- pacientes, pacientes-empty
- detalle-plan-activacion
