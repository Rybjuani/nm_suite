# Fase 3 — Hub Dashboard, Pacientes Y Personalización

## Objetivo (PLAN FASEADO §Fase 3)
- Dashboard: KPIs compactos, menos vacío y métricas jerarquizadas.
- Pacientes: filas escaneables, metadatos/sparklines legibles, acción quitar paciente clara con tono danger.
- Personalización: selección primary consistente, paneles integrados, acciones alineadas, sin scrollbars invasivas.

## Cambios Aplicados

### Dashboard (`hub/main_qt.py` · `DashboardView`)
- **KPIs compactos:** las dos cards superiores (`NMMetricCard`) pasan a altura **90px** (antes 96 fija). Hub-only: se hace vía el nuevo kwarg `height` de `NMMetricCard` con default = `FIXED_H` (96) → Suite/Respiración no cambian.
- **Menos vacío + jerarquía:** la card "Pacientes" tenía el número suelto sobre vacío. Ahora ambas KPI llevan **badge contextual** (`vinculados` / `promedio 7 módulos`), simétricas y sin hueco inferior. El badge va en tono neutro (`default`); el color de jerarquía vive en el número (primary/violet).
- **Card "Uso promedio por módulo":** dejó de estirarse a todo el alto (`stretch=1` + `addStretch` interno eliminados; `SizePolicy.Fixed`). Antes quedaba un hueco vacío grande dentro de la card (se veía "rota"). Ahora dimensiona a sus 7 barras y el sobrante baja como respiro al pie.

### Pacientes (`shared/components/patient.py` · `NMPatientRowPremium`)
- **Ring "Uso" legible:** 30 → **36px**. A 30px el `NN%` interior quedaba comprimido contra el arco (el propio `NMModuleRing` documenta que `<32px` el label es ilegible). 36px entra en la altura de fila (58px, área útil 44px) y da aire al porcentaje. Componente Hub-only.
- **Quitar paciente con tono danger:** la `✕` (`_btn_unlink`) llevaba icono gris neutro (se leía como "cerrar"). Ahora el icono está en **tono danger en reposo** y el hover refuerza con fondo danger translúcido (alpha 0.18). Acción irreversible que se ve como tal sin gritar.

### Personalización
- **Acciones alineadas:** la ruta de personalización revisada en esta fase quedo integrada al Hub, con acciones alineadas y controles compactos.
- **Selección primary / sin scrollbars invasivas:** sin cambios — la biblioteca ya usaba selección `accentSoft` consistente y scrollbars clinicas compactas (verificado en captura).

## Restricciones respetadas
- `NMMetricCard.height` es opcional con default `FIXED_H`: ningún cambio agranda Suite y Hub a la vez (densidad Hub ≤ Suite).
- `NMPatientRowPremium` es Hub-only (sólo `hub/main_qt.py`) → no toca Suite.
- API pública de componentes intacta (`test_components_public_api` 56 símbolos OK).
- Tokens ADN sin tocar (`test_token_parity`, `test_no_legacy_visuals` OK).

## Gates
- `py_compile` OK (4 archivos)
- `ruff check` OK (All checks passed)
- `pytest tests/` → **85 passed**

## Capturas evidencia (inspeccionadas 2026-06-14, light + dark)
| Vista | Inspección | Resultado matriz |
|---|---|---|
| `hub-dashboard-{dark,light}` | revisado_f3 — KPIs compactos + badges, card módulos sin hueco | **parcial** (conserva REQUIRES_DATA_STATE) |
| `hub-pacientes-{dark,light}` | revisado_f3 — ring 36px legible, X danger, filas escaneables | **parcial** (conserva REQUIRES_DATA_STATE) |
| `hub-personalizacion-{dark,light}` | revisado_f3 — lista alineada, botones consistentes y acciones en fila | revisado |

## Deuda pendiente exacta
- `dashboard` y `pacientes` (vistas default): la inspección visual de los cambios de Fase 3 quedó OK (`revisado_f3`), pero el **resultado de matriz se mantiene `parcial`** porque conservan el flag `REQUIRES_DATA_STATE` — el estado de datos real (no el mock QA) no queda probado. Corrección aplicada 2026-06-14.
- Estados *data-dependent* siguen `parcial` por diseño (no es deuda de Fase 3): `dashboard-empty`, `pacientes-empty`, `pacientes-filter-*`, `pacientes-search` → requieren ausencia/composición real de datos, no mock QA.
- La variante standalone legacy del editor fue retirada; la ruta vigente de personalizacion quedo cubierta por las capturas del Hub.

## Estado
- **CERRADA** — implementación + capturas inspeccionadas + matriz actualizada + doc.
- Próxima: Fase 4 (Hub Resumen y Registros) — incluye el glifo □ junto a `6.4 /10` heredado de Fase 2.
