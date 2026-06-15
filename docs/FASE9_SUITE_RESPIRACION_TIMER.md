# Fase 9 — Suite Respiración y Timer

## Objetivo (PLAN FASEADO §Fase 9)
- Reducir superficies sobredimensionadas.
- Controles reconocibles y proporcionados.
- Historial sin corte inicial ni scrollbar dominante.
- Evitar métricas que parezcan biométricas reales si no lo son.

## Cambios Aplicados (`app/modules/respiracion_qt.py`)

### Métrica biométrica falsa "BPM" → "Ciclos" (núcleo de la fase)
- **Problema:** la tercera stat card mostraba **"BPM"** con un valor que **simulaba un pulso cardíaco** (`base 68 - …`, arritmia sinusal respiratoria + `random.uniform(-0.6, 0.6)`). La app **no mide pulso** — era una lectura que aparentaba ser biométrica real sin serlo (66, 64, …), justo lo que el plan prohíbe.
- **Fix:** la card pasa a **"Ciclos"** y muestra `self._ciclos`, el **conteo real de ciclos 4-7-8 completados** en la sesión (0 al iniciar, +1 por ciclo). Métrica honesta, determinista y verificable, coherente con el vocabulario del historial ("N ciclos"). Se eliminó el bloque de simulación y el `import random` del tick. El `NMCalmBadge` (badge de pulso) ya estaba oculto y permanece dormido por theme-compat.
- Renombrado interno `_bpm_card/_bpm_eyebrow/_bpm_value_lbl` → `_ciclos_card/_ciclos_eyebrow/_ciclos_value_lbl` para no dejar nombres engañosos.

### Historial sin corte inicial ni scrollbar dominante
- **Poblado (verificado, ya correcto):** el panel "Historial reciente" lista las mini-cards sin scrollbar visible ni recorte de la primera fila a 960×600.
- **Vacío (fix):** "Sin sesiones." quedaba **suelto arriba-izquierda** en un panel alto (se veía "roto"). Ahora se **centra (h+v)** con stretch arriba/abajo + `AlignCenter` → estado vacío intencional, consistente con el patrón calmo del resto de la Suite.

### Controles reconocibles y proporcionados (verificado, ya correcto)
- Respiración: `Reiniciar` y `Detener` ya son `NMButton variant="secondary"` (borde visible, botones reales), `Iniciar/Pausar` gradient primario, tamaño `md`. Jerarquía clara.
- Timer: controles media (reiniciar/play/skip) como íconos reconocibles; presets en pills; ring focal proporcionado. Sin cambios necesarios.

### Superficies sobredimensionadas (verificado)
- El círculo guía de Respiración y el ring del Timer son los elementos **focales** de cada pantalla (animación de fase / cuenta regresiva); a 960×600 quedan proporcionados. No se redujeron para no romper el foco; no se detectó superficie rota o sobredimensionada fuera de ellos.

## Restricciones respetadas
- Cambios acotados a `app/modules/respiracion_qt.py` (Suite-only) → Hub y Timer intactos (el Timer ya cumplía: sin métricas biométricas).
- Sin tocar tokens ni componentes compartidos (`test_token_parity`, `test_components_public_api` OK).
- Lógica de guardado de sesión (`_save_session`, schema `respiracion`) preservada exacta.

## Gates
- `py_compile` OK (respiracion + timer)
- `ruff check` OK (All checks passed)
- `pytest tests/` → **85 passed**
- Sin duplicados de hash: 22/22 capturas respiración+timer con MD5 distinto.

## Capturas evidencia (inspeccionadas 2026-06-14, light + dark)
| Vista | Resultado |
|---|---|
| `suite-respiracion-{dark,light}` (idle) | revisado — card "Ciclos" (no BPM), historial poblado sin corte |
| `suite-respiracion-running-{dark,light}` | revisado — "Ciclos 0" en lugar de pulso simulado, círculo con fase+countdown |
| `suite-respiracion-paused-{dark,light}` | revisado — pausa (Reanudar), Ciclos honesto |
| `suite-respiracion-preset-3min-{dark,light}` | revisado — preset 3 min, card Ciclos |
| `suite-respiracion-preset-10min-{dark,light}` | revisado — preset 10 min, card Ciclos |
| `suite-respiracion-historial-{dark,light}` | revisado — "Sin sesiones." centrado |
| `suite-timer-{dark,light}` (idle) | revisado — ring focal, controles media, sesiones sin corte inicial |
| `suite-timer-running-{dark,light}` | revisado — "Sesión en curso", sin métricas falsas |
| `suite-timer-paused-{dark,light}` | revisado — pausa, controles reconocibles |
| `suite-timer-preset-5min-{dark,light}` | revisado — preset 5 min |
| `suite-timer-preset-45min-{dark,light}` | revisado — preset 45 min |

## Deuda pendiente exacta
- Ninguna en el alcance de Fase 9. Las 11 vistas (22 capturas) quedan `revisado`.
- Se retiró el flag `DUPLICATE_SUSPECT` de respiracion/respiracion-historial: con "Ciclos" + estado vacío centrado las capturas dejaron de compartir hash.

## Estado
- **CERRADA** — implementación + capturas inspeccionadas + matriz actualizada + doc.
- Próxima: Fase 10 (Suite Rutina, Actividades y Avisos).
