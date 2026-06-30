# Discrepancias Sentinel (app real) vs mockup canónico

> Nota 2026-06-27: documento histórico. Donde este reporte menciona
> `qa/mockup_reference_static/`, debe leerse como snapshot legado; la referencia
> canónica vigente del repo hoy es `qa/_mockup_canonical/`.

**Fecha:** 2026-06-22 · **Commit Sentinel:** `fd51354` · **Tema comparado:** light
**Fuente repo:** capturas de `qa/visual_sentinel.py audit --all` en `qa/_visual_sentinel/latest/screenshots/`
**Referencia canónica:** `qa/mockup_reference_static/` (86 capturas, 43/tema)

## Contexto de la pasada

- La auditoría `audit --all --theme both` completó **3 de 4 combos** (suite light, hub light, suite dark) → **524 capturas**. El 4º combo (hub dark) abortó con un *access violation* esporádico de Qt (crash de C++ no atrapable desde Python; el watchdog solo cubre cuelgues). La comparación usa **tema light** (Suite + Hub completos).
- El Sentinel **no compara** automáticamente contra el mockup (registry vacío → reportó `NEW_STATE_UNREVIEWED` + `CRAWL_TRUNCATED`, sin auto-aprobar). Su aporte fue **generar capturas fieles, sin tofu y sin ruido de chrome** que habilitan esta comparación, hecha a mano captura↔captura.

## Leyenda de gravedad

🔴 alta (defecto funcional) · 🟠 media (inconsistencia de diseño) · 🟡 baja (pulido) · ⚪ no-defecto (estado/datos/copy editable, fuera de alcance visual)

## Listado por superficie (12 principales, light)

| # | Pantalla | Captura Sentinel | Discrepancias vs mockup |
|---|---|---|---|
| 1 | Home | `suite__home-view-light` | 🟡 títulos de tarjeta envuelven a 2 líneas ("Termómetro emocional", "Registro de pensamientos") → desalinean contenido · 🟡 pill "0.8 vs semana" con fondo más marcado |
| 2 | Termómetro emocional | `suite__modulo-animo_act__bienestar-light` | 🟠 header **"Termómetro Emocional"** (Title Case) vs "emocional" · 🟠 íconos de tarjetas de progreso = gráfico 📈 vs **sparkle ✦** · 🟠 toggle "7 días" seleccionado **beige** vs verde oscuro · 🟡 dots blancos sobre el slider |
| 3 | Guía de respiración | `suite__modulo-respiracion_act__calma-light` | 🟠 header **"Guía de Respiración Animada"** (Title Case) · 🟡 pills patrón (Inhalá/Mantené/Exhalá) con relleno **tenue** vs verde/amarillo/naranja · 🟡 CICLOS "—" vs "0" |
| 4 | Temporizador | `suite__modulo-timer_act__enfoque-light` | 🟠 header **"Temporizador de Actividades"** (Title Case) · 🟠 chips "25 min"/"Lectura" seleccionados **beige** vs verde oscuro |
| 5 | Checklist de rutina | `suite__modulo-rutina_act__habitos-light` | 🟠 header **"Checklist de Rutina Diaria"** (Title Case) · 🟠 **checkbox a la derecha** del texto vs izquierda · 🟡 subtítulo banner "60% del día completado" vs "Vas por buen camino, seguí así" |
| 6 | Activación conductual | `suite__modulo-actividades_act__accion-light` | 🟠 header **"Asistente de Activación Conductual"** (Title Case) · ⚪ copy sin voseo ("Arma"/"Escribe" vs "Armá"/"Escribí") |
| 7 | Recordatorios | `suite__modulo-avisos_act__diario-light` | 🟠 header **"Recordatorios de Bienestar"** (Title Case) · 🟠 toggle "Todos" seleccionado **claro** vs verde oscuro · 🟡 badges de estado sin dot de color · 🟡 separador "·" inconsistente |
| 8 | Registro TCC | `suite__modulo-registro-t-c-c_act__cognitivo-light` | 🟠 header **"Registro de Pensamientos (TCC)"** (Title Case) · 🟠 título de paso "¿Qué pasó?" vs "Situación" + copy distinto · 🟡 contador "0/500" fuera de la card vs dentro |
| 9 | Habilidades DBT | `suite__modulo-d-b-t_act__habilidades-light` | 🟡 íconos de card difieren (ambos válidos) · ⚪ "superar crisis" vs "superar la crisis". Header **OK** (sigla) |
| 10 | Pacientes (Hub) | `hub__pacientes-view-light` | ✅ alta fidelidad, sin discrepancias significativas |
| 11 | Detalle de paciente (Hub) | `hub__detalle-paciente-view_act__am-light` | ✅ alta fidelidad · 🟡 wrap de placeholder/empty-state a 2 líneas |
| 12 | Textos globales (Hub) | `hub__textos-globales-suite-view_act__textos-globales-light` | 🔴 **layout de fila roto**: valor como texto plano + **input vacío** separado (contador 0/N) vs valor dentro del input editable · 🟠 título "Textos globales **de Suite**" vs "Textos globales" · ⚪ "158 textos" vs "145" (datos) |

## Patrones sistemáticos

1. **🟠 Capitalización de headers de módulo** — la app usa **Title Case** en 7 pantallas; el mockup usa *sentence case*. Hallazgo más repetido. (DBT no afectado: sigla.)
2. **🟠 Segmented / chips seleccionados** — fondo **beige/claro** en Termómetro, Temporizador, Avisos vs **verde oscuro relleno** del mockup. **Inconsistente**: Respiración, Pacientes y Detalle sí usan verde oscuro → componente con dos variantes conviviendo.
3. **🔴 Textos globales** — valor fuera del input editable (defecto funcional, no solo cosmético).
4. **🟠 Posición de checkbox en Rutina** (derecha vs izquierda).
5. **🟡 Pills/badges con menos color** (respiración, avisos) e íconos de tarjetas (termómetro).

## Síntesis

~31 puntos observados → **~15 discrepancias de diseño accionables en 5 patrones**. El resto son estado/datos/copy editable. **Hub = el más fiel**; el Suite concentra headers Title Case + segmented beige + el layout de Textos globales.
