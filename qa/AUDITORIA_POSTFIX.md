# Auditoría visual POST-FIX — pantalla por pantalla vs mockup

> Nota 2026-06-27: documento histórico. La ruta `qa/mockup_reference_static/`
> que aparece abajo refiere al snapshot legado; el canonical vigente del repo es
> `qa/_mockup_canonical/`.

**Fecha:** 2026-06-23 · **Tema:** light · **NO declara PASS visual global.**
**Capturas actuales:** `qa/_postfix/*.png` (generadas con el Sentinel SOLO como
generador de capturas — no aprueba nada; la comparación es manual).
**Referencia:** `qa/mockup_reference_static/light/...`

> Caveat de captura: el Sentinel graba a **960px** de ancho; varios mockups son
> **980px**. Esa diferencia de 20px provoca por sí sola algunos *wrap* de título
> (Home, empty-state del Detalle) que podrían no ocurrir al ancho natural de la app.

## Severidad
🔴 alta (defecto funcional) · 🟠 media (estructura/diseño) · 🟡 baja (pulido/copy) · ⚪ no-defecto (estado/dato)

## Tabla

| # | Pantalla | Captura actual | Mockup | Diferencias restantes | Sev. | ¿Requiere fix? |
|---|---|---|---|---|---|---|
| 1 | **Home** | `_postfix/suite_home.png` | Inicio/Home/Con puntaje | Títulos "Termómetro emocional" y "Registro de pensamientos" hacen **wrap a 2 líneas** (1 en mockup) → desalinea el contenido de esas cards. Pill "0.8 vs semana" con fondo más marcado. | 🟡 | Opcional (DIFERIDO). Verificar antes si el wrap persiste a 980px. |
| 2 | **Termómetro emocional** | `_postfix/suite_animo.png` | Bienestar/Termómetro emocional | **Dots del slider** visibles sobre el gradiente (mockup sin dots) — son los 10 niveles **clickeables** (DIFERIDO). Tarjetas de progreso: estructura de texto "7 días" + "Días seguidos con registro esta semana." vs mockup "7 días seguidos" + "con registro esta semana". | 🟡 | Slider DIFERIDO (cambia función). Texto = copy, opcional. |
| 3 | **Guía de respiración** | `_postfix/suite_respiracion.png` | Bienestar/Guía de respiración/En reposo | Sin diferencias significativas. Header sentence-case ✓, pills con color ✓, CICLOS "0" ✓. | — | No |
| 4 | **Temporizador** | `_postfix/suite_timer.png` | Hábitos/Temporizador/En reposo | Sin diferencias significativas. Header sentence-case ✓, chips seleccionados verde oscuro ✓. | — | No |
| 5 | **Checklist de rutina** | `_postfix/suite_rutina.png` | Hábitos/Checklist de rutina/Con tareas | Subtítulo del banner "60% del día completado." vs mockup "Vas por buen camino, seguí así." (copy). Header sentence-case ✓, checkbox a la izquierda ✓. | 🟡 | Copy, opcional |
| 6 | **Activación conductual** | `_postfix/suite_actividades.png` | Cognitivo/Activación conductual/Sugerencias | Copy sin voseo ("Arma"/"Escribe" vs "Armá"/"Escribí"; "estado de ánimo de manera" vs "ánimo de forma"). Íconos por categoría (la app es posiblemente **mejor**). Header sentence-case ✓. | 🟡 | Copy = decisión aparte. Íconos = no |
| 7 | **Recordatorios** | `_postfix/suite_avisos.png` | Hábitos/Recordatorios de bienestar/Todos | Sin diferencias significativas. Header sentence-case ✓, toggle verde ✓, badges con dot de color ✓. | — | No |
| 8 | **Registro TCC** | `_postfix/suite_registro_tcc.png` | Cognitivo/Registro de pensamientos (TCC)/Situación | **Título de paso**: app "¿Qué pasó?" + "Contá en pocas palabras…" vs mockup "Situación" (nombre del paso) + "¿Qué pasó? Describí…". Contador "0/500" **fuera** de la card (DIFERIDO). Placeholder "Escribí lo que pasó…" vs "Ej: En la reunión…". Header sentence-case ✓. | 🟠 | Título de paso: requiere DECISIÓN. Contador DIFERIDO. Placeholder copy. |
| 9 | **Habilidades DBT** | `_postfix/suite_dbt.png` | Habilidades DBT/Ahora | Íconos de card distintos (ambos válidos). "superar crisis" vs "superar la crisis" (copy). | 🟡 | Opcional |
| 10 | **Pacientes (Hub)** | `_postfix/hub_pacientes_fix.png` | Hub/Pacientes/Lista activa | **DEFECTO HALLADO Y CORREGIDO**: la última fila (Laura Gómez) tenía sparkline+ring corridos ~44px a la derecha porque su X (oculta por la optimización de scroll al ser fila parcial) **colapsaba su espacio** en el layout. Fix: `retainSizeWhenHidden` en `NMPatientRowPremium` → el espacio se reserva, las columnas alinean. **Resta**: la X sigue oculta en la última fila (la optimización la trata como fila parcial; el mockup la muestra) + botón "Textos globales" sin ícono hamburguesa. | 🟠→🟢 / 🟡 | Alineación: HECHO. X en última fila: decisión (ver nota). |
| 11 | **Detalle de paciente (Hub)** | `_postfix/hub_detalle.png` | Hub/Detalle de paciente | "Sin recordatorios asignados aún." hace wrap a 2 líneas; borde dashed del empty-state menos visible. Tabs en Title Case = correcto (coinciden con su mockup). | 🟡 | Opcional menor (posible artefacto de ancho) |
| 12 | **Textos globales (Hub)** | `_postfix/hub_textos.png` | Hub/Configuración/Textos globales | Conteo "158 textos" vs "145" (DATO, no defecto). Header con flecha ← vs hamburguesa ☰. Filas algo más espaciadas. **Fase 1 confirmada**: valor dentro del input + contador real ✓. | ⚪/🟡 | No (dato/chrome) |

## Corrección posterior (Pacientes)

Al revisar la pantalla de Pacientes señalada por el owner se detectó un **defecto
real que esta auditoría había pasado por alto** (lo había marcado "alta fidelidad"
sin mirar bien): la última fila desalineada. Causa raíz: la X (unlink) se oculta
en filas parciales (optimización de scroll) con `setVisible(False)`, lo que
**colapsaba su espacio** y corría sparkline+ring a la derecha. Fix:
`retainSizeWhenHidden` → el botón oculto conserva su hueco, las columnas alinean.
Verificado por geometría (sparkline_x = 701 en las 5 filas) y captura.

**Nota — X oculta en la última fila**: con el viewport actual la 5ª fila se trata
como "parcial" y su X queda oculta (comportamiento deliberado y **testeado**:
`test_pacientes_view_hides_unlink_action_on_partial_rows`). El mockup muestra las
5 X. Mostrar la 5ª X **sin** romper ese test requeriría que el viewport de la lista
encaje las 5 filas completas (cambio de layout), no relajar la optimización. Queda
como decisión del owner; NO se tocó el test para forzarlo.

## Conclusión honesta (sin PASS global)

- **Defecto de alineación en Pacientes**: hallado y corregido (arriba).
- El defecto funcional de Textos globales (Fase 1) está corregido y verificado.
- **1 diferencia 🟠 media abierta**: estructura del título de paso en **Registro TCC** (la app usa la pregunta como título; el mockup usa el nombre del paso + la pregunta como subtítulo). Requiere decisión de diseño antes de tocar.
- **Diferidos confirmados pendientes** (🟡): dots del slider del Termómetro (niveles clickeables — cambiar es funcional), contador 0/500 de TCC, wrap de títulos del Home.
- **Copy/voseo** (🟡): rutina, activación, DBT, TCC — son textos editables; alinearlos al mockup es una decisión aparte, no un fix de layout.
- **Chrome/dato** (⚪): ícono hamburguesa, 158 vs 145 textos — no son defectos de UI.

Las pantallas 3, 4, 7 (Respiración, Temporizador, Recordatorios) quedaron sin
diferencias significativas tras los fixes. El resto conserva diferencias menores
documentadas arriba. **Esto NO constituye un cierre visual global**: quedan ítems
diferidos y decisiones de copy/estructura pendientes de owner.
