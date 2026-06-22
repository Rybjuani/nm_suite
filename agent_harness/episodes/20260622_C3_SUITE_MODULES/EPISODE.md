# C3-SUITE-MODULES

Cluster ejecutado después de C4-HUB-CRITICAL (ba65e15).

## Alcance

- Auditar y resolver deuda de Actividades, Rutina, Timer, Avisos.
- Limpiar importaciones F401 pre-existentes en los cuatro módulos.
- No tocar Hub, DBT, Registro TCC, Onboarding, DB/sync/build/installers.

## Estado de defectos por módulo

### Actividades (V2-P1-014 a V2-P2-003)

Todos resueltos previamente por C1-PRIMITIVES-SYSTEM o refactors anteriores:

| Defecto | Estado | Evidencia en código |
|---------|--------|---------------------|
| V2-P1-014 | Resuelto-C1 | `NMTabs(variant="filter")` — pills canónicas |
| V2-P1-015 | Resuelto-C1 | `setMinimumSize(208,176)` + sizePolicy Expanding/Fixed |
| V2-P1-016 | Resuelto-C1 | chip QLabel con `border-radius: 10px; padding: 2px 8px` |
| V2-P1-017 | Resuelto-C1 | `NMBadge(tone="brand", with_dot=True)` para estado Hecho |
| V2-P1-018 | Resuelto-C1 | `_btn_no` ghost + `_btn_yes` soft — jerarquía clara |
| V2-P2-002 | Resuelto | footer_layout `setContentsMargins(16,0,16,8)` — respira |
| V2-P2-003 | Resuelto-C1 | `NMIcon(size=18)` integrado a top row con aire |

### Rutina (V2-P1-034 a V2-P1-039)

Todos resueltos previamente:

| Defecto | Estado | Evidencia en código |
|---------|--------|---------------------|
| V2-P1-034 | Resuelto-C1 | `NMCustomCheck` — componente refinado |
| V2-P1-035 | Resuelto | `NMButton(variant="secondary", "+ Agregar tarea")` |
| V2-P1-036 | Resuelto | `_SectionCard` min 154 / max 260 con `_sync_height_to_content` |
| V2-P1-037 | Resuelto | `_HeroDayCard.setMaximumHeight(116)` — no sobredimensionado |
| V2-P1-038 | Resuelto | Checks en scroll body alineados por NMCustomCheck |
| V2-P1-039 | Resuelto | NMEmptyState con centrado óptico correcto |

### Timer (V2-P1-040 a V2-P1-043)

| Defecto | Estado | Nota |
|---------|--------|------|
| V2-P1-040 | **Diferido** | Ring 230px coincide con "mockup canónico línea 207"; override requiere decisión owner explícita sobre escala final. Test `test_timer_focus_arc_size_and_num_match_mockup` bloquea cambio sin aval. |
| V2-P1-041 | Resuelto | Presets usan `NMButtonOutline(toggleable=False, size="sm")` — gramática unificada |
| V2-P1-042 | Resuelto | Category chips usan el mismo patrón NMButtonOutline |
| V2-P1-043 | Resuelto | Empty state usa `NMEmptyState` canónico (icono + título + subtítulo, compacto) |

### Avisos (V2-P1-044 a V2-P2-010)

Todos resueltos previamente:

| Defecto | Estado | Evidencia en código |
|---------|--------|---------------------|
| V2-P1-044 | Resuelto-C1 | `_StepPill(QPushButton)` con `border-radius: 16px` — pills |
| V2-P1-045 | Resuelto-C1 | `NMSearchInput` + pills en mismo `filter_row` |
| V2-P1-046 | Resuelto-C1 | `NMEmptyState("bell", ...)` — patrón canónico |
| V2-P2-010 | Resuelto-C1 | NMIcon en ReminderCardV3 + NMEmptyState normalizados |

## Cambios técnicos

Solo limpieza de importaciones F401 pre-existentes en los cuatro módulos:

### app/modules/timer_qt.py
Elimina del try-block: `NMButton`, `ThemeManager`, `NMIcon`, `C`, `colors`, `norm_modo`, `qfont_mono`, `V3_RD`, `stylesheet_lineedit`, `PAD_CONTAINER`, `timer_sessions`.

### app/modules/avisos_qt.py
Elimina globales: `redact`, `QLineEdit`, `QComboBox`.
Elimina del try-block: `NMButtonOutline`, `NMToggle`, `NMProgressBar`, `NMSkeleton`, `ThemeManager`, `NMProgressLine`, `NMPlayButton`, `NMFormPanel`, `colors`, `qfont_mono`, `V3_RD`, `stylesheet_textedit`, `stylesheet_lineedit`, `PAD_CONTAINER`.

### app/modules/rutina_qt.py
Elimina del try-block: `ThemeManager`, `NMProgressLine`, `C`, `colors`, `norm_modo`, `V3_RD`, `PAD_CONTAINER`, `leer_config`.

## Validación técnica

- `ruff check --select=F401,F811,F821`: ✓ All checks passed (4 archivos)
- `pytest tests/test_timer_visual_contract.py tests/test_rutina_visual_contract.py tests/test_avisos_visual_contract.py`: ✓ 7/7 passed

## Archivos tocados

- `app/modules/timer_qt.py`
- `app/modules/avisos_qt.py`
- `app/modules/rutina_qt.py`
- `agent_harness/episodes/20260622_C3_SUITE_MODULES/EPISODE.md`
- `agent_harness/episodes/20260622_C3_SUITE_MODULES/VISUAL_CHECKLIST.md`

## Handoff

Siguiente cluster: `C5-MISSING-SCREENS-AUDIT`.

Deuda explícita:
- V2-P1-040: Timer ring 230px diferido — requiere decisión owner sobre escala.
