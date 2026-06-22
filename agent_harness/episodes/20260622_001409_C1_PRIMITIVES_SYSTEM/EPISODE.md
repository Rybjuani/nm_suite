# C1-PRIMITIVES-SYSTEM

Cluster ejecutado despues de `C0-GATE-HARNESS`.

## Alcance

- Normalizar gramatica visual de primitives compartidas antes de fixes locales.
- Tocar solo primitives compartidas y duplicados locales directos de primitives.
- No redisenar pantallas completas.
- No generar ZIP.
- No regenerar las 98 capturas.

## Cambios aplicados

- `NMTabs`
  - `pill`: seleccion suave con superficie elevada + borde brand, ya no bloque/CTA verde.
  - `seg`: seleccion elevada con borde brand y alto estable.
  - `filter`: alto estable y radio concreto.
  - `pill` deja de estirarse como columnas; el excedente va a stretch.
- Avisos `_StepPill`
  - Se alinea con la gramatica `seg`: seleccion suave, radio concreto, altura estable.
  - Se elimina la seleccion primaria fuerte dentro del filtro segmentado.
- `NMBadge`
  - Radio concreto para que Qt renderice pills reales en vez de rectangulos.
- Actividades chip local de categoria
  - Padding y radio explicitos para converger con badges/chips.
- Tests visual-contract actualizados para medir estados visuales observables, no solo existencia.

## Evidencia focal

Before focal minimo:

- `qa/_captures_c1_primitives_before/suite-actividades-light-960x600.png`
- `qa/_captures_c1_primitives_before/suite-actividades-dark-960x600.png`
- `qa/_captures_c1_primitives_before/suite-avisos-light-960x600.png`
- `qa/_captures_c1_primitives_before/suite-avisos-dark-960x600.png`
- `qa/_captures_c1_primitives_before/suite-rutina-light-960x600.png`
- `qa/_captures_c1_primitives_before/suite-rutina-dark-960x600.png`
- `qa/_captures_c1_primitives_before/suite-timer-empty-light-960x600.png`
- `qa/_captures_c1_primitives_before/suite-timer-empty-dark-960x600.png`
- `qa/_captures_c1_primitives_before/suite-dbt-library-light-960x600.png`
- `qa/_captures_c1_primitives_before/suite-dbt-library-dark-960x600.png`

After focal minimo:

- `qa/_captures_c1_primitives_after/suite-actividades-light-960x600.png`
- `qa/_captures_c1_primitives_after/suite-actividades-dark-960x600.png`
- `qa/_captures_c1_primitives_after/suite-avisos-light-960x600.png`
- `qa/_captures_c1_primitives_after/suite-avisos-dark-960x600.png`
- `qa/_captures_c1_primitives_after/suite-rutina-light-960x600.png`
- `qa/_captures_c1_primitives_after/suite-rutina-dark-960x600.png`
- `qa/_captures_c1_primitives_after/suite-timer-empty-light-960x600.png`
- `qa/_captures_c1_primitives_after/suite-timer-empty-dark-960x600.png`
- `qa/_captures_c1_primitives_after/suite-dbt-library-light-960x600.png`
- `qa/_captures_c1_primitives_after/suite-dbt-library-dark-960x600.png`

Nota: capturas son evidencia tecnica local y revision focal del cluster. No son
el paquete final C6.

## Resultado visual

Decision C1: `PASS_FOR_CLUSTER_SCOPE`.

- DBT Biblioteca: tabs de familia dejan de ser barras verdes/columnas y pasan a chips.
- Avisos: filtro segmentado activo deja de ser CTA verde y pasa a seleccion suave.
- Actividades: badges/chips de categoria se renderizan como pills suaves, no rectangulos.
- Rutina: checkboxes conservan contrato visual, sin regresion focal.
- Timer empty: primitive empty state no tuvo cambio estructural; composicion de pantalla queda para C3.

## Defectos trazados

| Defecto | Estado C1 | Nota |
|---|---|---|
| V2-P1-047 | Parcial resuelto en primitives | Variantes base de botones conservadas; C1 evita que tabs/segmentos usen estilo CTA. Misusos por pantalla quedan en C2/C3/C4. |
| V2-P1-048 | Resuelto para primitive system | `NMTabs`, `_StepPill`, filter chips y badges tienen gramatica por rol y alturas/radios estables. |
| V2-P1-049 | Diferido trazado | `NMCard` ya tenia contrato focal; densidad/composicion por pantalla se corrige en C2/C3/C4. |
| V2-P1-050 | Diferido trazado | `NMEmptyState` se mantuvo estable; composicion y escala por pantalla se corrige en C3/C4. |
| V2-P1-051 | Parcial resuelto | Light/dark mejoran en controls/badges; calidad compositiva final queda para clusters de pantalla y C6. |

## Validacion tecnica de apoyo

- `python -m pytest tests/test_component_visual_contract.py tests/test_avisos_visual_contract.py tests/test_actividades_visual_contract.py -q`
- `ruff check shared/components/buttons.py shared/components/surfaces.py app/modules/avisos_qt.py app/modules/actividades_qt.py tests/test_component_visual_contract.py tests/test_avisos_visual_contract.py tests/test_actividades_visual_contract.py`
- `git diff --check`

Resultado: verde. Estos checks son apoyo tecnico; el cierre del cluster depende
del checklist visual trazado.
