# Fase 7 — Suite Base, Acceso Y Estado Emocional

## Objetivo (PLAN FASEADO §Fase 7)
- Home: hero/cards menos altos, estados legibles y **nombre capitalizado**.
- Onboarding/Ajustes/PIN/Bloqueo/Recuperar acceso: familia visual común, legal legible, acciones claras y contraste correcto.
- Ánimo/Evolución: **sin falso valor inicial 0**, chips como selección real, **sparse/empty states compactos** y métricas coherentes.

## Cambios Aplicados

### Home — nombre capitalizado (`app/home_qt.py` · `_HeroBienestar`)
- El saludo del hero mostraba **"Hola, juan"** (minúscula) cuando el nombre venía así de la cuenta.
- Fix: se toma el primer nombre y se **capitaliza** → "Hola, Juan". Guarda anti-`split` vacío (nombre sólo-espacios → "Paciente").
- Hero/cards: alturas y estados ya legibles (con-score y sin-score); el estado vacío muestra "Registrar" claro. Sin cambios adicionales necesarios.

### Evolución — sparse compacto (`app/modules/evolucion_qt.py`)
- En estado sparse (<2 registros) el `setMinimumHeight(160)` previo **no alcanzaba**: sin tope de máximo, la card del chart se estiraba a todo el alto y el mensaje quedaba dentro de una card enorme.
- Fix: en sparse se **capa el máximo** (`setMaximumHeight(176)`, min 140) → card compacta; con datos se libera el tope (`QWIDGETSIZE_MAX`) para que el chart vuelva a crecer (verificado sin regresión en el estado con datos).

### Ánimo — verificado, ya correcto (sin cambios)
- **Sin falso valor inicial 0:** `V3MoodSlider(unset=True)` deja el thumb estacionado en la muesca 0 (no registrable), el header muestra "—/10" + "Sin registro" y "Guardar registro" está deshabilitado hasta mover a 1-10. Ya cumple el contrato.
- **Chips como selección real:** el chip seleccionado ("Tristeza") muestra borde accent vs los no seleccionados (filled). Selección real verificada.
- Métricas pos/neg coherentes (Positivo / Negativo 7 días).

### Acceso — verificado, familia coherente (sin cambios)
- Onboarding, Onboarding-error, PIN setup, Privacy Lock, Privacy Lock-error y Recuperar acceso comparten la **misma familia visual** (branding NeuroMood + inputs/botones del sistema de diálogos compartido).
- Legal en caja scrolleable **legible**; acciones claras (primario gradient / outline); errores en tono danger con **contraste correcto** ("El nombre es obligatorio.", "PIN incorrecto. Quedan 2 intentos.").
- Ya migrados al sistema de diálogos compartido en fases previas → no requirieron cambios.

## Restricciones respetadas
- Cambios acotados a `app/` (Suite). Sin tocar componentes compartidos ni tokens ADN.
- `test_token_parity`, `test_no_legacy_visuals`, `test_components_public_api` OK.

## Gates
- `py_compile` OK (2 archivos)
- `ruff check` OK (All checks passed)
- `pytest tests/` → **85 passed**

## Capturas evidencia (inspeccionadas 2026-06-14, light + dark)
| Vista | Resultado |
|---|---|
| `suite-home-{dark,light}` | revisado — "Hola, Juan" capitalizado |
| `suite-home-no-score-{dark,light}` | parcial (REQUIRES_DATA_STATE) — nombre capitalizado verificado |
| `suite-animo-{dark,light}` | revisado — sin falso 0, métricas coherentes |
| `suite-animo-emotion-chips-{dark,light}` | revisado — selección real |
| `suite-evolucion-{dark,light}` | revisado — chart con datos sin regresión |
| `suite-evolucion-sparse-{dark,light}` | revisado — card sparse compacta |
| `suite-onboarding(-error)-{dark,light}` | revisado — familia coherente, legal legible |
| `suite-pin-setup / privacy-lock(-error)-{dark,light}` | parcial (REQUIRES_RUNTIME) — visual coherente |
| `suite-recuperar-acceso-{dark,light}` | revisado — misma familia, hint legible |

## Deuda pendiente exacta
- Estados *data/runtime-dependent* siguen `parcial` por diseño (no es deuda de Fase 7): `home-no-score` (REQUIRES_DATA_STATE), `pin-setup`/`privacy-lock`/`privacy-lock-error` (REQUIRES_RUNTIME, standalone no prueba ruta/lifecycle invocados).
- `home-settings-open` sigue `bloqueado` (overlay transitorio, fuera de alcance).
- Código muerto detectado (no tocado para no mezclar alcances): `HomeView._greeting_text` no se invoca; mostraría nombre sin capitalizar si se reactivara.

## Estado
- **CERRADA** — implementación + capturas inspeccionadas (light/dark) + matriz actualizada + doc.
- Fases 3–7 completas. Próximas (fuera de este pedido): Fase 8 (Suite TCC) … Fase 11 (regresión final).
