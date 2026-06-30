# Fase 4 — Hub Resumen Y Registros

## Objetivo (PLAN FASEADO §Fase 4)
- Resumen: foco principal claro; **corregir glifo inválido junto a `6.4 /10`**; legal, nota, ánimo y perfil sin competir.
- Registros: gráfico menos dominante, porcentaje circular explicado o integrado, lista visible sin scroll inicial innecesario.

## Cambios Aplicados

### Resumen — glifo □ corregido (`shared/components/cards.py` · `NMFeaturedCard`)
- **Causa raíz:** la card "Ánimo promedio · semana" mostraba `6.4 / 10` seguido de un **emoji** (`😊/😐/😞`, default `\U0001f610`). La fuente del app no trae glifos de color → se renderizaba como **□ (tofu)**.
- **Fix:** el `_emoji_lbl` se reemplaza por un **punto de valencia** (`_mood_dot`, 12×12, `border-radius`) cuyo color sale de tokens del tema según banda de score: `<4 → warning`, `<7 → accent`, `≥7 → teal`. Siempre renderiza, sin depender de fuentes de emoji.
- API estable: `set_score(score, emoji=...)` mantiene el parámetro `emoji` por compatibilidad (consumidores en `hub/pacientes_qt.py` no cambian) pero ya no se pinta como glifo. Color re-aplicado en `_apply_theme` (helper `_paint_mood_dot`).
- Componente **Hub-only** (sólo `hub/pacientes_qt.py`) → no afecta Suite.

### Registros (`hub/pacientes_qt.py`)
- **Gráfico menos dominante:** `_build_animo_graph` (modo no-compact) baja de `min 156 / max 176` a **`min 132 / max 148`**. Antes empujaba la lista de registros fuera del viewport 960×600.
- **Porcentaje circular explicado:** el ring de adherencia (`distinct_days / 7`, p.ej. 71%) flotaba sin contexto. Ahora va envuelto con caption **"Adherencia 7d"** y tooltip `N de 7 días con registro` (ring 48→44 para alojar la caption sin crecer).
- **Lista visible sin scroll inicial:** con el gráfico más bajo, la primera fila de registros (`23/05 · Termómetro Emocional · Ánimo 7/10 · "Me siento tranquilo…"`) queda visible sin scrollear.

## Restricciones respetadas
- `NMFeaturedCard` es Hub-only → Suite intacto.
- API pública de componentes intacta (`set_score` conserva firma) — `test_components_public_api` OK.
- Tokens ADN sin tocar (`test_token_parity`, `test_no_legacy_visuals` OK).

## Gates
- `py_compile` OK (2 archivos)
- `ruff check` OK (All checks passed)
- `pytest tests/` → **85 passed**

## Capturas evidencia (inspeccionadas 2026-06-14, light + dark)
| Vista | Resultado |
|---|---|
| `hub-detalle-{dark,light}` | revisado — glifo □ → punto de valencia (sin tofu), cards sin competir |
| `hub-detalle-registros-{dark,light}` | revisado — gráfico menos dominante, ring "Adherencia 7d" explicado, primera fila visible |
| `hub-detalle-registros-bottom-{dark,light}` | revisado — lista completa legible (Hizo/No pudo, Energía N/10) |

## Deuda pendiente exacta
- Ninguna en el alcance de Fase 4. Resumen y Registros quedan `revisado`.
- (Nota fuera de alcance: las sub-pestañas Plan terapéutico e IA del detalle son Fases 5 y 6.)

## Estado
- **CERRADA** — implementación + capturas inspeccionadas + matriz actualizada + doc.
- Próxima: Fase 5 (Hub Plan Terapéutico).
