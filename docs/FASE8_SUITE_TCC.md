# Fase 8 — Suite TCC

## Objetivo (PLAN FASEADO §Fase 8)
- Wizard estable, menos vacío, navegación equilibrada.
- `Anterior` como secondary real; CTA final distinguible.
- Éxito determinista sin toast de error.
- Mantener intensidad solo como `/10`.

## Cambios Aplicados (`app/modules/registro_tcc_qt.py`)

### `Anterior` como botón secondary real (navegación equilibrada)
- **Problema:** `_btn_prev` usaba `variant="ghost"` → sin borde ni fondo se leía como **texto suelto**, no como botón. En los 4 pasos el control de "volver" parecía un enlace perdido frente al CTA gradient de la derecha.
- **Fix:** `variant="ghost"` → **`variant="secondary"`**. Ahora "Anterior" tiene borde visible (botón real) y jerarquía clara: secondary a la izquierda + gradient primario a la derecha. En el paso 0 queda deshabilitado (no se puede retroceder) pero se sigue leyendo como botón.

### CTA final distinguible
- "Siguiente" (pasos 0-2) y "Guardar" (paso 3) son el mismo botón **gradient** primario; el cambio de copy + el contraste con el nuevo "Anterior" bordeado hace que el CTA final quede distinguible. Sin cambios de tamaño (se mantiene `width=160`).

### Éxito determinista sin toast de error
- **Problema:** `_guardar()` hacía un `INSERT` real en `pensamientos` y, ante un fallo de DB, mostraba `NMToast` de error. La evidencia de la página de éxito dependía de que la DB estuviera disponible/escribible → no determinista, y además ensuciaba la DB con registros de captura.
- **Fix:** guard `visual_qa_enabled()` antes del `INSERT`: en modo QA visual se va directo a `_show_success_page()` (sin INSERT ni sync, sin riesgo de toast de error). **Producción conserva el INSERT + toast ante un fallo genuino de guardado.**

### Intensidad solo como `/10` (verificado, ya correcto)
- Header del paso Emoción muestra `Intensidad: N/10`; el `_ResumenCard` muestra `N/10`. El `NMHeatBar` (0-100) se mapea a `round(value/10)`. No queda ningún `%` de intensidad en el módulo.

## Restricciones respetadas
- Cambio acotado a `app/modules/registro_tcc_qt.py` (Suite-only) → Hub intacto.
- Sin tocar tokens ni componentes compartidos (`test_token_parity`, `test_components_public_api` OK).
- `NMButton variant="secondary"` ya existe en la familia de botones (no se crea nada nuevo).
- Lógica de negocio de guardado preservada en producción (el guard solo afecta modo QA).

## Gates
- `py_compile` OK
- `ruff check` OK (All checks passed)
- `pytest tests/` → **85 passed**

## Capturas evidencia (inspeccionadas 2026-06-14, light + dark)
| Vista | Resultado |
|---|---|
| `suite-registro-{dark,light}` (paso 0 Situación) | revisado — "Anterior" secondary real, textarea de escritura |
| `suite-registro-step1-emotion-{dark,light}` | revisado — tiles con selección real, intensidad "5/10", nav equilibrada |
| `suite-registro-step2-distortions-{dark,light}` | revisado — distorsiones (chips) + tip terapéutico, nav equilibrada |
| `suite-registro-step3-filled-{dark,light}` | revisado — CTA final "Guardar" gradient distinguible |
| `suite-registro-success-{dark,light}` | revisado — éxito determinista, sin toast de error, auto-reset 3s |

## Deuda pendiente exacta
- Ninguna en el alcance de Fase 8. Las 5 vistas TCC quedan `revisado`.
- (Nota: la página de éxito mantiene contenido centrado en una card amplia; es una confirmación transitoria (auto-reset 3s) y se priorizó el requisito explícito de determinismo + intensidad /10.)

## Estado
- **CERRADA** — implementación + capturas inspeccionadas + matriz actualizada + doc.
- Próxima: Fase 9 (Suite Respiración y Timer).
