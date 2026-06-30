# Comparacion Exacta F0 vs Fase 1 (aislada)

Verificacion post-hoc de que Fase 1 ("contrato visual y densidades") produjo
exactamente los cambios esperados y nada mas.

## Metodologia

- **Commit examinado**: `4e9961e` — "Fase 1 contrato visual y densidades"
- **Worktree aislado**: `git worktree add <tmp> 4e9961e` — codigo Fase 1 puro,
  sin ningun cambio de Fases 2 ni correcciones posteriores.
- **Harness**: `qa/capture_v8.py --all --no-clean` desde el worktree.
- **Baseline**: `qa/_baseline_f0_phase01/` (132 PNGs, commit `e3d37a2`).
- **Diff**: MD5 hash por archivo, todos los PNGs presentes en ambas fuentes.

## Resultado De Las Capturas Fase 1

| Campo | Valor |
|---|---|
| generated_at | 2026-06-14T19:52:25 |
| total / success / failed | 132 / 132 / 0 |
| unique_hash_count | 130 |
| CAPTURED_VALID | 102 |
| REQUIRES_DATA_STATE | 16 |
| REQUIRES_RUNTIME | 8 |
| WRONG_VIEW | 2 |
| DUPLICATE_SUSPECT | 4 (2 pares) |

### Duplicados en Fase 1 (esperado)

`suite-respiracion-{dark,light}` produce el mismo PNG que
`suite-respiracion-historial-{dark,light}` porque `_btn_hist_toggle` fue
eliminado y el helper de toggle era un no-op. Corregido en `748c909`.

## Diff F0 Baseline vs Fase 1

- **Cambiadas : 15 / 132**
- **Sin cambio: 117 / 132**

### Archivos cambiados (15)

Todos Suite, todos en estados activos o con botones visibles:

| Archivo | Categoria |
|---|---|
| suite-actividades-dark-960x600.png | Actividades con items |
| suite-actividades-light-960x600.png | Actividades con items |
| suite-actividades-filtered-dark-960x600.png | Actividades filtradas (dark) |
| suite-actividades-marked-hice-dark-960x600.png | Item marcado como hecho |
| suite-actividades-marked-hice-light-960x600.png | Item marcado como hecho |
| suite-privacy-lock-light-440x520.png | Pantalla de bloqueo (light) |
| suite-privacy-lock-error-light-440x520.png | Bloqueo con error (light) |
| suite-registro-success-dark-960x600.png | Pantalla exito de registro |
| suite-registro-success-light-960x600.png | Pantalla exito de registro |
| suite-respiracion-running-dark-960x600.png | Respiracion en curso |
| suite-respiracion-running-light-960x600.png | Respiracion en curso |
| suite-respiracion-paused-dark-960x600.png | Respiracion pausada |
| suite-respiracion-paused-light-960x600.png | Respiracion pausada |
| suite-timer-running-dark-960x600.png | Timer en curso |
| suite-timer-running-light-960x600.png | Timer en curso |

### Patron observado

- **Solo Suite cambia**: Fase 1 solo toca `shared/theme.py` y `shared/theme_qt.py`.
  La densidad Hub (`hub_density_qss`) queda definida pero no esta cableada en
  `hub/main_qt.py` en este commit — por eso ningun archivo Hub cambia.
- **Solo estados activos/poblados**: los cambios de densidad `suite_comfortable`
  (NMButton, NMTabs) son visibles unicamente en vistas que renderizan esos
  componentes en estados no-vacios.
- **Estados vacios sin cambio**: `suite-actividades-empty`, `suite-avisos-empty`,
  `suite-rutina-empty` etc. permanecen identicos al baseline.

### Archivos sin cambio (117)

- 42 archivos Hub: todos sin cambio (densidad Hub no aplicada todavia).
- 75 archivos Suite: estados vacios, REQUIRES_RUNTIME, vistas sin componentes
  afectados por la densidad.

## Contribucion Incremental Por Fase

| Fase | Archivos cambiados vs F0 | Detalle |
|---|---|---|
| Fase 0 → Fase 1 (este doc) | **15** | Suite active states — NMButton/NMTabs density |
| Fase 1 → Fase 2 (`748c909`) | **+42** | Hub (chrome 32px, sidebar, margenes) |
| Fases 0 → 1 + 2 (acumulado) | **57** | Ver `CAPTURE_MANIFEST_SUMMARY.md` |

## Conclusion

Fase 1 introdujo exactamente los cambios esperados: afecto componentes de Suite
(`NMButton`, `NMTabs`) en vistas con contenido visible, sin regresion en Hub y
sin afectar estados vacios. La densidad Hub fue definida en Fase 1 pero cableada
en Fase 2, lo que explica el patron de 0 cambios Hub en esta comparacion.
