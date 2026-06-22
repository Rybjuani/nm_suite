# C4-HUB-CRITICAL

Cluster ejecutado después de `C2-SUITE-CRITICAL` follow-up (125872f).

## Alcance

- Resolver P0/P1 críticos del Hub listados en FIX_PLAN.md para C4.
- Tocar solo Hub Pacientes (`hub/main_qt.py`), Hub Detalle (`hub/pacientes_qt.py`),
  y componente compartido `shared/components/patient.py`.
- No tocar Suite, Actividades, Rutina, Timer, Avisos, DB/sync/build/installers.

## Defectos resueltos

| Defecto    | Severidad | Descripción                                           | Fix aplicado                                                   |
|------------|-----------|-------------------------------------------------------|----------------------------------------------------------------|
| V2-P0-004  | P0        | Última fila (Laura Gomez) parcialmente cortada         | Overhead formula 80→100 en `_sync_table_card_height`          |
| V2-P1-008  | P1        | Badge "5 pacientes" no pill canónica                  | NMBadge ya es pill; scrollbar se elimina al fijar P0-004       |
| V2-P1-009  | P1        | Scrollbar agresivo (aparece cuando fila cabe)         | Resuelto como consecuencia de V2-P0-004                        |
| V2-P1-010  | P1        | Columnas header desalineadas con filas                | th_lay left margin 76→94 (94 = 16+10+14+40+14)               |
| V2-P1-012  | P1        | "Textos globales" flota en header, no en esquina derecha | `addStretch()` movido antes del botón en roster_meta         |
| V2-P1-013  | P1        | Rings demasiado pesados (46px) en columna Uso         | `_NM_PATIENT_RING_SIZE` 46→36 px                             |
| V2-P1-001  | P1        | "Exportar PDF" variant secondary/apagado              | `variant="gradient"` (acción primaria del hero)               |
| V2-P1-002  | P1        | "Resumen IA" ghost barato                             | `variant="secondary"` (acción secundaria visible)             |

## Defectos fuera de alcance C4 (diferidos a C5/C6 o deliberados)

| Defecto    | Nota                                                                      |
|------------|---------------------------------------------------------------------------|
| V2-P2-001  | Avatar colors ya usan ADN palette correcta; diferido                      |
| V2-P1-003  | Tabs density plan terapéutico: riesgo de regresión sin visual feedback    |
| V2-P1-004  | Form placeholders: layout complejo, diferido                              |
| V2-P1-005  | IA button en subtab: menor, diferido                                      |
| V2-P1-006  | Empty panel compacto ya es deliberado (NMEmptyState vuela en panel chico) |
| V2-P1-007  | Card radius/shadow: NMCard provee consistencia; diferido                  |

## Cambios técnicos

### hub/main_qt.py
- Elimina `C`, `nm_icon`, `NMPageHeader` del import (F401 pre-existentes).
- `_sync_table_card_height`: overhead 80 → 100 (P0-004).
- `roster_meta`: `addStretch()` movido antes de `texts_btn` (P1-012).
- `th_lay.setContentsMargins`: 76 → 94 (P1-010).

### shared/components/patient.py
- `_NM_PATIENT_RING_SIZE`: 46 → 36 (P1-013).

### hub/pacientes_qt.py
- Elimina `QScrollArea`, `NMBadge` del import (F401 pre-existentes, ambos bloques try/except).
- `_btn_exportar_pdf`: `variant="secondary"` → `variant="gradient"` (P1-001).
- `_btn_resumen_ia`: `variant="ghost"` → `variant="secondary"` (P1-002).

### tests/test_component_visual_contract.py
- Ajuste del contrato de ring: `== 46` → `== 36`.

## Validación técnica

- `ruff check --select=F401,F811,F821`: ✓ All checks passed
- `pytest tests/test_hub_visual_contract.py tests/test_components_public_api.py tests/test_component_visual_contract.py`: ✓ 47/47 passed

## Archivos tocados

- `hub/main_qt.py`
- `hub/pacientes_qt.py`
- `shared/components/patient.py`
- `tests/test_component_visual_contract.py`
- `agent_harness/episodes/20260622_C4_HUB_CRITICAL/EPISODE.md`
- `agent_harness/episodes/20260622_C4_HUB_CRITICAL/VISUAL_CHECKLIST.md`

## Handoff

Siguiente cluster: `C3-SUITE-MODULES` (Actividades, Rutina, Timer, Avisos).
