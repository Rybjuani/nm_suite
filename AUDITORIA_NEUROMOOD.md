# AUDITORÍA NEUROMOOD — Diagnóstico, ideas y plan

> **Fecha:** 2026-05-20
> **Branch:** `main`
> **Commit base:** `e33dc1f`
> **Modo:** solo lectura — auditoría + diagnóstico + ideas + plan
> **Alcance:** repo local `C:\Users\nosom\Desktop\nm_suite` (GitHub puede estar viejo, se ignora)
> **Fuente de la propuesta:** `Propuesta Base.pdf` (NeuroMood — Dra. Lucía Fazzito y Dr. José Ignacio Ujhelly, Belgrano CABA, especializados en trastornos psiquiátricos refractarios: TEC, ketamina, neuromodulación avanzada)
> **Roles de análisis aplicados:** arquitecto senior + PM salud mental + UX strategist + QA lead + auditor de cumplimiento clínico no médico

---

## Aviso metodológico sobre nomenclatura

Esta auditoría se hizo **por lectura del código local**, no por ejecución. Cuando este informe dice "**Implementado en código**", significa que el código existe en el repo con sintaxis válida y lógica coherente, **pero NO que el runtime fue verificado en Windows**. Aspectos como animaciones, glow, daemon de bandeja, notificaciones del SO, endpoints IA, RLS real de Supabase, instaladores en EXE, SmartScreen, etc. son "**NO verificados en ejecución**" o "**NO VERIFICABLES SIN EJECUTAR**".

Un agente que lea este informe **NO debe saltarse pruebas** asumiendo que algo está "funcional" por el solo hecho de estar implementado en código. Antes de cualquier piloto clínico real hay que correr el plan de QA de la Parte 10 con apps reales sobre Windows.

**Terminología de estado usada en este informe:**

- **Implementado en código:** existe en el repo, sintaxis válida, lógica coherente leída.
- **NO verificado en ejecución:** este informe es por lectura — runtime no se probó en Windows real.
- **NO VERIFICABLE SIN EJECUTAR:** aspectos que ni siquiera por lectura pueden confirmarse (animaciones, glow, beeps, SmartScreen, notificaciones SO, IA endpoint, RLS real, autostart, bandeja del sistema).
- **Incompleto:** UI o lógica con partes faltantes confirmables por lectura (ej: botón sin handler).
- **Roto / Con bug conocido:** sólo si el bug es identificable por lectura del código o documentado en docs internas.

---

## Tabla de contenidos

1. [Resumen ejecutivo](#resumen-ejecutivo)
2. [Decisiones de producto 2026-05-20](#decisiones-de-producto-2026-05-20)
3. [PARTE 1 — Cumplimiento contra Propuesta Base](#parte-1--cumplimiento-contra-propuesta-base)
4. [PARTE 2 — Mapa real del producto actual](#parte-2--mapa-real-del-producto-actual)
5. [PARTE 3 — Matriz Suite / Hub / SQLite / Supabase](#parte-3--matriz-suite--hub--sqlite--supabase)
6. [PARTE 4 — Inventario de utilidades actuales](#parte-4--inventario-de-utilidades-actuales)
7. [PARTE 5 — Matriz de configurabilidad remota desde Hub](#parte-5--matriz-de-configurabilidad-remota-desde-hub)
8. [PARTE 6 — Utilidades que faltan](#parte-6--utilidades-que-faltan)
9. [PARTE 7 — Ideas nuevas para pacientes](#parte-7--ideas-nuevas-para-pacientes)
10. [PARTE 8 — Ideas nuevas para profesionales](#parte-8--ideas-nuevas-para-profesionales)
11. [PARTE 9 — Arquitectura recomendada](#parte-9--arquitectura-recomendada)
12. [PARTE 10 — Plan de QA](#parte-10--plan-de-qa)
13. [PARTE 11 — Mega plan por fases](#parte-11--mega-plan-por-fases)
14. [Cierre — Respuestas directas a las 7 preguntas finales](#cierre--respuestas-directas-a-las-7-preguntas-finales)
15. [Apéndices](#apéndices)

---

## Resumen ejecutivo

**Veredicto general:** el producto cumple **objetivo y utilidad clínica** de la Propuesta Base. Las 8 herramientas pedidas están codificadas (7 como módulos del paciente + 1 transformada justificadamente al Hub profesional). Suite e Hub son aplicaciones PyQt6 robustas, con arquitectura modular limpia, sync bidireccional implementado en código, IA multiproveedor con fallback automático, instaladores con consentimiento legal versionado y desinstaladores con opción de conservar datos. **Sin embargo, para aprobación clínica inmediata por NeuroMood hay cuatro brechas que sí necesitan resolverse antes del piloto.**

> **Recordatorio metodológico:** este informe es por **lectura del código local**. Todo lo que digamos "Implementado en código" no implica que esté verificado en runtime Windows. Ver "Aviso metodológico sobre nomenclatura" al inicio del informe.

**Las 4 brechas críticas:**

1. **Configurabilidad remota desde Hub: prácticamente inexistente.** Hoy solo se pueden editar actividades del banco, asignar tareas y recordatorios individuales, y leer 4 permisos. **Todo el contenido clínicamente sensible está hardcodeado en código Python** (textos, plantillas TCC, presets de respiración 4-7-8, presets timer 5/10/25/45, secciones de rutina mañana/tarde/noche, mensajes de apoyo, etiquetas de ánimo, distorsiones cognitivas, categorías de actividades). Cualquier cambio de redacción que pida el equipo clínico requiere recompilar. La decisión 2026-05-21 lo encuadra: **patrón general `hub_config` 2 niveles (global del equipo + override por paciente) aplicado a TODO el Hub** (subsección 9.4.A). Riesgo de feedback negativo: alto.
2. **ConfigView del Hub es lectura pura** ([hub/main_qt.py:562-707](hub/main_qt.py)). El profesional no puede modificar nada desde UI excepto el tema y forzar sync. Botón "+ Nuevo paciente" existe sin handler ([hub/main_qt.py:453-455](hub/main_qt.py)).
3. **IA sin audit trail clínico.** [hub/ia_asistente.py](hub/ia_asistente.py) tiene multiproveedor (Groq/Gemini/OpenCode/Ollama), pero **no persiste outputs**. El chat global se pierde entre sesiones. Cero trazabilidad de qué sugerencias dio la IA a qué paciente, qué prompt, qué modelo. Para uso clínico real esto es un bloqueante de auditoría.
4. **Tags semáforo clínico en el Hub contradicen la decisión 7.** El Dashboard usa tags hardcoded "Adherencia alta / Riesgo bajo / Agenda al día" ([hub/main_qt.py:171-389](hub/main_qt.py) `DashboardView`) y la vista Pacientes tiene tab filtro "Atención" basado en `adherence<40%` ([hub/main_qt.py:400-557](hub/main_qt.py)). Esto es exactamente lo que la decisión 7 prohíbe (interpretaciones clínicas automáticas sobre uso de la app). **Bloqueante de aprobación** — se debe eliminar en F0.1 antes de cualquier piloto.

**Sobre las 3 apps de variable ánimo (Ánimo Loop, decisión 2026-05-21):**

La Propuesta Base pide 3 herramientas explícitamente conectadas por la variable ÁNIMO declarada por el paciente: **Termómetro Emocional** (registra), **Visualizador Evolución Anímica** (visualiza histórico, principalmente en Hub con mini-stats en Suite), **Asistente de Activación Conductual** (propone actividades según rango de ánimo curado por el profesional). Esto **NO es "automatismo oculto" descartado** — es el corazón explícito del producto. El paciente declara, el profesional configura los rangos desde Hub. Las 3 apps **cumplen función según Propuesta Base** (ver subsección "NeuroMood Ánimo Loop" + Parte 4.A). Lo único pendiente del lado paciente es el mini-visualizador semanal en Home (F1).

**Interpretaciones específicas Propuesta Base (decisión 2026-05-21) — pendientes de implementar:**

- **Timer (item 3):** *"delimitar actividades terapéuticas por tiempo"* — el profesional debe definir presets desde Hub. Hoy paciente elige libre. **NO cumple esta interpretación.** Acción en F2.2.
- **Avisos (item 2):** *"mensajes de apoyo a horarios fijos determinados por el equipo"* — biblioteca de mensajes + plantillas remotas. Hoy paciente crea libre. **Parcial.** Acción en F2.2. + Mover autostart Windows del módulo Avisos al Home Suite como ajuste general (F3).
- **Rutina (item 6):** opción C — sistema híbrido 3 estados configurable por paciente desde Hub (`solo_profesional` / `mixto` / `solo_paciente`). Acción en F2.3.

**Lo que sí está sólido:**

- 7 módulos paciente con DB local + sync remoto: animo, respiracion (4-7-8), registro_tcc (4 pasos + detección de distorsiones), rutina (3 secciones, con campo `origen` ya listo para opción C), actividades (motor activación conductual con fallback), timer (con preset/custom), avisos (con daemon + bandeja + autostart Windows). **Implementados en código — NO verificados en ejecución.**
- Auth Supabase directo sin atajos peligrosos (no Resend, no SMTP, no OAuth, no "sin cuenta"). PBKDF2-SHA256 100k iterations para hashes locales ([shared/identidad.py:5-13](shared/identidad.py)).
- Tabla `legal_consents` con RLS habilitado y 3 políticas correctas ([db/legal_consents.sql](db/legal_consents.sql)). Constancia local + remota + versionada con hash.
- Sync bidireccional con debounce 15s ([shared/sync.py:454-466](shared/sync.py)), 6 streams export + 4 streams import (asignaciones, permisos, actividades).
- Build con 2 modos (interno bundled y externo con payload.zip), aunque la documentación menciona `BUILD_NEUROMOOD.bat` que **no existe** en raíz (solo `BUILDER_NUEVO_RAPIDO.bat` y `BUILDER_VIEJO_LENTO.bat`).
- IA multiproveedor con scoring + retry automático + idioma rioplatense + disclaimer "Nunca hacés diagnósticos ni recomendás medicación" embebido en sistema prompt (versionado en código, decisión 6).

**Estado para uso clínico:**

| Área | Verde | Amarillo | Rojo |
|---|---|---|---|
| 8 herramientas Propuesta Base | 7 módulos paciente + visualizador en Hub | — | — |
| Arquitectura | modular V3 limpia | duplicación menor (2 `build_neuromood.py`, 2 `.bat` builder) | — |
| DB & Sync | esquema completo + migraciones + RLS legal | RLS deshabilitado en clínicas (decisión consciente, defensible si se documenta) | — |
| Auth & Consentimiento | flujo completo + versionado + audit | — | — |
| IA Hub | multiproveedor + fallback | sin audit log + chat no persiste | — |
| Hub UI | Dashboard/Pacientes/Detalle implementados en código + 4 tabs por paciente | ConfigView read-only + "+ Nuevo paciente" sin handler | — |
| Configurabilidad remota | — | banco actividades + tareas + recordatorios + `origen` rutina | textos, plantillas TCC, presets timer/respiración, módulos, idioma, mensajes apoyo, `rutina_modo` **hardcodeados** |
| Tags Hub clínicamente sensibles | — | — | **Dashboard "Adherencia alta/Riesgo bajo" + filtro "Atención"** (decisión 7) — F0.1 |
| Privacidad PC compartida | infraestructura PBKDF2 lista | — | **no hay PIN/login al abrir Suite** |
| Instaladores | Suite con auth+consent / Hub auto-config + fix bug 2026-05-18 | sin firma código | — |

**Lo que haría primero si el objetivo es que NeuroMood lo apruebe:**

1. **F0.1 — Eliminar tags semáforo del Hub** (Dashboard + filtro Atención de Pacientes). **Bloqueante de aprobación clínica.** 1-2 días.
2. **F0.2 — Limpieza de repo** (REDESIGN/, scripts legacy raíz, BUILD_NEUROMOOD.bat consolidado). 2-3 días.
3. **F2.0 — Patrón general `hub_config` 2 niveles + `shared/remote_config.py` + ConfigView reestructurada** (base de TODA la configurabilidad — subsección 9.4.A). 1-2 semanas.
4. **F2.2 — Timer profesional + Avisos plantillas equipo** (interpretación Propuesta Base 2026-05-21). 1-2 semanas.
5. **F2.3 — Rutina sistema 3 estados (opción C)**. 1-2 semanas.
6. **F2.4 — Editor plantillas TCC + textos override genérico**. 2-3 semanas.
7. **F4 — Gestión real de pacientes desde Hub + audit log IA + persistencia chat**. 2-3 semanas.
8. **F3 — Modo privacidad del paciente + autostart al Home Suite + mini-visualizador semanal en Home (F1)**. 1-2 semanas.
9. **F7 — Piloto clínico con 3-5 pacientes reales**. 3-4 semanas.

---

## Decisiones de producto 2026-05-20

Antes de redactar el informe, el usuario fijó **8 decisiones vinculantes** que se aplican a todas las partes (especialmente Partes 7, 8, 9, 11). Las ideas descartadas se documentan con motivo para trazabilidad. **No se proponen aquí automatismos OCULTOS que cambien UI o comportamiento sin que el paciente lo declare o el profesional lo configure** (ej. "modo bajo ánimo automático"), **ni IA para pacientes, ni edición de contenidos legalmente sensibles desde UI, ni semáforos clínicos de adherencia poblacional.** Sí se usa la variable **ÁNIMO declarada manualmente por el paciente** en las 3 apps que la Propuesta Base pide explícitamente (Termómetro Emocional, Visualizador de Evolución Anímica, Asistente de Activación Conductual): eso es el corazón del producto, no automatismo oculto. La sección **"NeuroMood Ánimo Loop"** (más abajo) detalla esta interpretación.

| # | Idea descartada / ajustada | Reemplazo o criterio vigente |
|---|---|---|
| 1 | ❌ "Modo familiar/cuidador" (segundo perfil) | ✅ **"Modo privacidad del paciente"**: Suite pide contraseña/PIN del usuario en cada apertura, para PCs compartidas. Mejora privacidad sin crear tercer rol. |
| 2 | ❌ "Diario de respuesta a tratamiento TEC/ketamina" | **Descartado.** Fuera del scope inicial, alta sensibilidad clínica/legal, riesgo de feedback negativo. |
| 3 | ❌ "Modo bajo ánimo automático" (UI simplificada al detectar ánimo bajo) | **Sin lógica automática basada en umbrales.** ✅ Reemplazo: **configuración/personalización remota desde Hub en 2 niveles — global del equipo + individual por paciente**. |
| 4 | ❌ "Asistente IA de redacción TCC para paciente" | **Descartado por ética terapéutica + riesgo de reencuadres inadecuados.** ✅ Reemplazo: **plantillas TCC configurables por profesionales** desde Hub, sin IA directa al paciente. |
| 5 | ❌ "Editor de consentimiento legal versionado editable desde Hub" | **Descartado: rompería trazabilidad legal.** Los consentimientos siguen versionados en código + migraciones + `db/legal_consents.sql` + instalador. No editables por terapeutas desde UI. |
| 6 | ❌ "Reentrenamiento de prompts IA por equipo desde UI" | **Descartado: resultados impredecibles + difícil de auditar + riesgo legal.** ✅ Reemplazo: **prompts IA versionados en código** ([hub/ia_asistente.py:291-387](hub/ia_asistente.py)) + tabla `ia_audit_log` para auditoría de outputs (no edición). |
| 7 | ❌ "Panel de adherencia poblacional con semáforo riesgo/crítico" | **Descartado: ausencia de uso ≠ baja adherencia terapéutica.** ✅ Reemplazo: **panel neutral de actividad reciente por paciente** (última sync, últimos registros, tareas completadas, recordatorios activos, métricas individuales). Sin semáforos clínicos. |
| 8 | 🔄 "Modo lectura: card no-cerrable hasta marcar como leída" | **Ajustado: card no-cerrable es mala UX (invasiva/paternalista).** ✅ Versión final: **indicación destacada del profesional** que puede minimizarse, queda registrada como leída/no leída, sin bloquear UI. |

**Reglas derivadas — se aplican al resto del informe:**

- **Automatismos OCULTOS por umbrales emocionales: descartados.** Uso EXPLÍCITO de la variable ánimo declarada manualmente por el paciente (en Termómetro, Visualizador y Activación Conductual): **permitido y esperado** — es lo que pide la Propuesta Base. La diferencia clave: el paciente registra su ánimo conscientemente y los rangos/actividades los define el profesional desde Hub. No hay inferencia oculta de estado.
- Toda UI para editar contenido legalmente sensible (consentimientos, disclaimers, prompts IA del propio Hub) queda descartada. Esos contenidos quedan versionados en código.
- Configurabilidad remota se piensa siempre en **dos niveles — global del equipo y override individual por paciente**. Cohorte/grupo queda en categoría D (no MVP).
- Auditoría IA = log de outputs y prompts usados, **no** edición de prompts.
- Información mostrada al profesional sobre adherencia es **neutral/descriptiva**, sin etiquetas tipo "riesgo"/"crítico".
- **IA al paciente: no. IA al profesional: sí, con audit log.**

### NeuroMood Ánimo Loop — interpretación clínica de la Propuesta Base

La Propuesta Base define **tres herramientas conectadas por la variable ÁNIMO declarada manualmente por el paciente**. Esto NO es "detección automática de estado" — es el corazón explícito del producto.

```
   Termómetro Emocional ──→  guarda ánimo 1-10 en `termometro` (SQLite)
                             y `mood_records` (Supabase)
              │
              ├──→  Visualizador Evolución Anímica
              │       Hoy: tab Registros en Hub (pyqtgraph spline + tabla)
              │       Suite: mini-stats 7 días en `animo_qt.py` (NMWaveChart)
              │       Propuesta F1: mini-visualizador semanal en Home Suite
              │
              └──→  Asistente de Activación Conductual
                    Lee último puntaje del Termómetro → consulta
                    `activacion_actividades` con WHERE animo_min<=p AND
                    animo_max>=p → propone 3 actividades curadas por el
                    profesional desde Hub (Tab Banco — `activity_bank` +
                    `patient_activities`).
```

**Interpretaciones vigentes (confirmadas con el cliente 2026-05-21):**

- *"Nivel de energía declarado al inicio de la sesión"* (Propuesta Base 8) se interpretó como **ÁNIMO declarado**. **No se mide energía como variable separada** — la variable energía no se registra ni se usa. Si en el futuro el equipo clínico necesitase una variable energía separada, sería una extensión, no parte del MVP.
- El **Visualizador** es principalmente herramienta profesional (vive como tab Registros en Hub). La **versión mini-stats en Suite** ya existe parcialmente (`animo_qt.py:264-313` con `NMWaveChart` 7 días + 3 stats compactos) y se completa con el mini-visualizador semanal propuesto en F1 (Parte 7 A1).
- El **Activador** **NO infiere automáticamente**: usa el último registro consciente del Termómetro y propone actividades cuyos rangos `animo_min`/`animo_max` fueron definidos por el profesional desde Hub. Si el paciente no registró ánimo, el motor cae en fallback con `ACTIVIDADES_DEFAULT` ([motor_activacion.py:8-19](app/motor_activacion.py)).

**Esto NO contradice la regla "sin automatismos ocultos":**

- El paciente declara su ánimo conscientemente (no se infiere de comportamiento, tiempo en app, frecuencia de uso, etc.).
- El profesional define qué se propone con cada rango de ánimo (configurabilidad desde Hub Tab Banco).
- La UI muestra "según tu último registro" — todo transparente.
- No hay un "modo bajo ánimo automático" que cambie el resto de la Suite. Las 3 apps son explícitamente parte del loop.

**Estado de cumplimiento (resumen):**

| App | Función Propuesta Base | Estado |
|---|---|---|
| Termómetro Emocional | Registro diario 1-10 con almacenamiento local + sync | ✓ cumple — implementado en código en [animo_qt.py:222](app/modules/animo_qt.py) |
| Visualizador Evolución Anímica | Gráfica semanal y mensual + exportación PDF | ✓ cumple (en Hub: [hub/pacientes_qt.py:237-449](hub/pacientes_qt.py) + [hub/exportar.py](hub/exportar.py)) + mini-stats Suite ya parcial, F1 completa con mini-visualizador en Home |
| Asistente Activación Conductual | Propone actividades según variable de paciente | ✓ cumple — implementado en código en [actividades_qt.py:555](app/modules/actividades_qt.py) + [motor_activacion.py](app/motor_activacion.py); las actividades y rangos los configura el profesional desde Hub Tab Banco ([hub/pacientes_qt.py:566-781](hub/pacientes_qt.py)) |

---

## PARTE 1 — Cumplimiento contra Propuesta Base

La Propuesta Base enumera **8 herramientas en 3 módulos progresivos** (`Propuesta Base.pdf`, sección 3). Estado real en repo:

| # | Herramienta propuesta | Objetivo clínico/operativo | Implementación actual | Archivo(s) | Cubierta | Transformada justificadamente | Quién la usa | Cumplimiento | Riesgo de feedback negativo del cliente | Recomendación |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Termómetro Emocional** | Registro diario estado anímico 1-10 con almacenamiento auto | Módulo completo con `V3MoodSlider`, nota 500 chars, gráfico semanal `NMWaveChart`, 3 stats (promedio/racha/progreso), celebración partículas si ≥7 | [app/modules/animo_qt.py:222](app/modules/animo_qt.py) (`ModuloAnimo`) | **Sí** | No | Paciente (+ Hub lectura) | Cumple y supera (animaciones, streaks, partículas) | Bajo | Mantener. Considerar etiquetas configurables desde Hub (Parte 5). |
| 2 | **Recordatorios de Bienestar** | Ventana emergente configurable + horarios fijos | Módulo CRUD + daemon en hilo + bandeja Windows + autostart registry + silencio horario + dispara `winotify`→`plyer`→`winsound` fallback | [app/modules/avisos_qt.py:565](app/modules/avisos_qt.py) (`ModuloAvisos`) + [app/avisos_daemon.py:1-386](app/avisos_daemon.py) | **Sí** | No | Paciente (+ Hub asigna) | Cumple y supera (frecuencia por días, categorización inferida, silencio, autostart) | Bajo | Mantener. Recibe `assigned_reminders` vía [shared/sync.py:226-255](shared/sync.py). |
| 3 | **Temporizador de Actividades** | Timer + alarma suave | `NMFocusArc` 360px + presets 5/10/25/45 + custom (1-120 min) + winsound.Beep doble al finalizar + auto-restore ventana + lista sesiones de hoy | [app/modules/timer_qt.py:158](app/modules/timer_qt.py) (`ModuloTimer`) | **Sí** | No | Paciente | Cumple y supera (UI premium + persistencia ≥30s) | Bajo | Mantener. **Hay tabla local `timer_presets` ([shared/db.py:219-228](shared/db.py)) sin contraparte Supabase → oportunidad para edición remota (Parte 5).** |
| 4 | **Registro de Pensamientos (TCC)** | Formulario situación→emoción→pensamiento→respuesta | Wizard 4 pasos con `NMTCCStepper`, grid 4×2 emociones, `NMHeatBar` intensidad, detección de **10 distorsiones cognitivas** por keywords, tip terapéutico hardcoded, resumen lateral, registros previos | [app/modules/registro_tcc_qt.py:323](app/modules/registro_tcc_qt.py) (`ModuloRegistroTCC`) | **Sí** | No | Paciente | Cumple y supera (detección distorsiones + UI 4 pasos guiados) | **Medio-Alto** — el equipo clínico puede querer editar las preguntas, tips, emociones del grid, keywords. | **Crítico para F2:** este es el módulo con más texto clínicamente sensible. Plantilla TCC editable desde Hub (Parte 8). |
| 5 | **Guía de Respiración Animada** | Ciclo visual 4-7-8 | `_BreathCircle` 340px con `pyqtProperty` animadas (radius/glow/text), 3 fases (Inhala 4s, Mantén 7s, Exhala 8s), 3 NMPlayButton, presets 3/5/10 min, BPM card, calm bar, historial 4 mini-cards | [app/modules/respiracion_qt.py:516](app/modules/respiracion_qt.py) (`ModuloRespiracion`) | **Sí** | No | Paciente | Cumple y supera (animación premium real, no estática) | Medio — el equipo puede pedir presets distintos (4-4-4 box breathing, 5-5-5, etc.) | **Editor de presets respiración** desde Hub (Parte 8). FASES hardcoded líneas [respiracion_qt.py:82-87](app/modules/respiracion_qt.py). |
| 6 | **Checklist de Rutina Diaria** | Tareas + reinicio 00:00 + sonido logro | Hero card con ring 120px, 3 _SectionCard (Mañana/Tarde/Noche con iconos sun/spark/moon), NMCustomCheck items, `_add_task` inline, NMDayNote diaria con lock una vez guardada, winsound.Beep al completar | [app/modules/rutina_qt.py:311](app/modules/rutina_qt.py) (`ModuloRutina`) | **Sí** | No | Paciente (+ Hub asigna tareas con `seccion`) | Cumple y supera (nota del día, secciones horarias, ring de progreso) | Medio — secciones hardcoded ([rutina_qt.py:77-81](app/modules/rutina_qt.py)). | **Editor de rutinas/plantillas** desde Hub (Parte 8). Hay tabla local `checklist_plantillas` ([shared/db.py:230-238](shared/db.py)) sin contraparte Supabase. |
| 7 | **Visualizador de Evolución Anímica** | Gráfica semanal/mensual + export PDF/imagen | **TRANSFORMADO + parcial en Suite**: existe como tab "Registros" en Hub con gráfico pyqtgraph (spline scipy) + adherence ring + export PDF clínico ([hub/pacientes_qt.py:237-449](hub/pacientes_qt.py), [hub/exportar.py:23-150](hub/exportar.py)). En Suite hay **mini-stats embebidos en `animo_qt.py:264-313`** (NMWaveChart 7 días + 3 stats compactos promedio/racha/progreso). Confirmado con cliente 2026-05-21: **OK que sea principalmente profesional** + mini-versión paciente. F1 completa con mini-visualizador semanal en Home Suite. | [hub/pacientes_qt.py:237-449](hub/pacientes_qt.py) (`_TabRegistros`) + [hub/exportar.py:23-150](hub/exportar.py) + [app/modules/animo_qt.py:264-313](app/modules/animo_qt.py) (mini-stats Suite) | **Sí (en Hub) + Parcial (en Suite)** | **Sí, justificación clínica confirmada por cliente 2026-05-21:** el visualizador completo tiene más sentido para el profesional; la versión paciente se complementa con mini-stats por módulo + mini-visualizador semanal en Home (F1). | Profesional (gráfico completo) + Paciente (mini-stats + mini-visualizador F1) | Cubre vista profesional + parcial Suite. F1 cierra el gap del lado paciente. | Bajo (post-F1) | **F1:** agregar mini-visualizador semanal a [app/home_qt.py](app/home_qt.py) reusando `NMWaveChart` ya disponible (~3 días). |
| 8 | **Asistente de Activación Conductual** | Propone actividades según energía declarada | Módulo con `NMMoodContextHeader`, 6 categorías con mini-rings (`_CategoriesCard`), 3 sugeridas filtrables (NMTabs pill), grid responsive, motor sugiere según rango `animo_min/animo_max`, fallback `_FALLBACK_ACTIVIDADES`, registra Hecha/No pude | [app/modules/actividades_qt.py:555](app/modules/actividades_qt.py) (`ModuloActividades`) + [app/motor_activacion.py:38](app/motor_activacion.py) (`sugerir_actividades`) | **Sí** | No | Paciente (banco) + Profesional (CRUD desde Hub) | Cumple y supera (banco editable desde Hub + actividades personalizadas por paciente) | Bajo | Mantener. Es la herramienta con **mejor configurabilidad remota actual** ([hub/pacientes_qt.py:566](hub/pacientes_qt.py) `_TabBanco`). |

### Resumen de transformaciones

- **7 de las 8** herramientas existen como módulo paciente con UI dedicada.
- **1 transformada (Visualizador Evolución)**: convertida en tab profesional + mini-stats embebidos en `animo_qt.py`. Justificación clínica defensible, pero **riesgo de pedido del cliente** para que también esté completa lado paciente.
- **0 ausentes.** Todas tienen al menos representación.
- **0 fusionadas o renombradas** — los nombres vigentes coinciden con los originales (`AI_PROJECT_CONTEXT.md:31-43`).

### Cumplimiento global

**Veredicto:** Propuesta Base cumple en **objetivo y utilidad clínica**. La fidelidad literal a "8 apps separadas" no se preservó (esto era explícitamente aceptable según el prompt maestro), pero el resultado es una Suite integrada + Hub profesional, mucho más profesional que 8 binarios sueltos. **Punto frágil único:** Visualizador Evolución para paciente, que se cubre en F1.

---

## PARTE 2 — Mapa real del producto actual

### 2.A NeuroMood Suite (app del paciente)

**Para qué sirve:** acompañamiento digital diario del paciente entre sesiones con el equipo clínico. Registro emocional, respiración guiada, registro cognitivo TCC, checklist de rutina, sugerencia de actividades conductuales, temporizadores y recordatorios.

**Usuario:** persona en tratamiento por trastorno psiquiátrico refractario (depresión mayor refractaria, TOC, bipolar, esquizofrenia, dolor crónico, Parkinson) bajo supervisión del equipo NeuroMood.

**Entry point:** [app/main_qt.py:101](app/main_qt.py) (`NeuroMoodApp(QMainWindow)`), tamaño 1320×860 ideal / 1100×720 mínimo. Carga dinámica de módulos via `_MODULE_MAP` ([app/main_qt.py:55-63](app/main_qt.py)). Caché de instancias en `_module_cache`. Transiciones fade in/out de 150-200ms.

**7 módulos implementados** (ver Parte 1 para detalle por módulo):
1. Ánimo / Termómetro Emocional
2. Respiración (4-7-8)
3. Registro TCC (4 pasos)
4. Rutina (3 secciones horarias)
5. Actividades (Activación Conductual)
6. Timer (de enfoque)
7. Avisos (Recordatorios de Bienestar)

**Qué datos genera y guarda localmente** (SQLite `%APPDATA%/NeuroMood/nm_data.db`, ver [shared/db.py:93-284](shared/db.py)):
- `termometro` (animo): fecha, hora, puntaje 1-10, nota
- `respiracion`: fecha, hora, tecnica, duracion_minutos, ciclos
- `pensamientos`: fecha, hora, situacion, emocion, intensidad 0-10, pensamiento, respuesta_alternativa, distorsiones, reflexion_ia, evidencia_favor, evidencia_contra, creencia_antes/despues, emocion_resultante
- `checklist_tareas` + `checklist_completadas` + `checklist_notas_dia`: tareas por sección, fecha de completado, nota libre por día
- `activacion`: fecha, hora, energia, animo, actividad, resultado (hecha/intentada/no_pude)
- `actividades_temporizador`: fecha, hora, nombre, categoria, duracion_config, duracion_real, notas
- `recordatorios` + `recordatorios_log`: hora, mensaje, dias, activo + log de disparos
- `activacion_actividades`: banco local (espejo del banco remoto)
- `activacion_config` + `activacion_perfil` + `config`: k/v stores locales
- `checklist_plantillas` + `timer_presets` + `mensajes_biblioteca`: tablas locales **sin contraparte remota**

**Qué datos sincroniza a Supabase** (vía [shared/sync.py](shared/sync.py)):

| SQLite local | → | Supabase remota |
|---|---|---|
| `termometro` | exporta | `mood_records` |
| `respiracion` | exporta | `breathing_sessions` |
| `pensamientos` | exporta | `thought_records` |
| `checklist_completadas` (join `checklist_tareas`) | exporta | `checklist_completions` |
| `actividades_temporizador` | exporta | `timer_sessions` |
| `recordatorios_log` | exporta | `reminder_logs` |
| `patients` | upsert | `patients` (paciente_id, name, pwd hash, install_code, 4 permisos) |

**Qué datos importa desde Supabase:**
- `assigned_tasks` → inserta en `checklist_tareas` con origen='profesional' ([shared/sync.py:189-223](shared/sync.py))
- `assigned_reminders` → inserta en `recordatorios` local ([shared/sync.py:226-255](shared/sync.py))
- `patients.perm_*` → guarda en `config` k/v ([shared/sync.py:335-351](shared/sync.py))
- `activity_bank` (global) + `patient_activities` (individuales) → inserta en `activacion_actividades` ([shared/sync.py:354-391](shared/sync.py))

**Cosas solo locales** (no sincronizan):
- `checklist_notas_dia` (nota libre del día)
- `checklist_plantillas` (plantillas locales)
- `timer_presets` (presets timer)
- `mensajes_biblioteca` (mensajes apoyo)
- `activacion_config` + `activacion_perfil` (config motor)
- `legal_consent.json` local (separado de DB)
- Hash de password (PBKDF2 en `config.patient_pwd`)

**Qué puede ver el Hub:** todos los streams exportados (6 streams clínicos + `patients` + `legal_consents`).

**Qué puede controlar el Hub hoy:**
- ✅ Crear `assigned_tasks` (descripcion + seccion)
- ✅ Crear `assigned_reminders` (mensaje + hora + dias=hardcoded "1,2,3,4,5,6,7")
- ✅ CRUD `activity_bank` (nombre + descripcion + categoria + animo_min/max + activa)
- ✅ Setear 4 permisos: `perm_checklist_activacion`, `perm_checklist_manual`, `perm_temporizador_manual`, `perm_recordatorios_manual` — **pero sin UI** (los inserta el instalador con default True). El Suite los respeta vía [app/home_qt.py:811-841](app/home_qt.py) (`_is_module_available`).

**Utilidades vigentes (verificadas por lectura de código):**
- Sync background al abrir app (`sync_al_abrir` cada apertura + completo si >7 días, [shared/sync.py:418-426](shared/sync.py))
- Sync inmediato 48h al guardar cualquier registro, con debounce 15s ([shared/sync.py:454-466](shared/sync.py))
- Daemon avisos en hilo (`_INTERVALO=30s`) + reactivación medianoche + horario silencio ([app/avisos_daemon.py:43-67](app/avisos_daemon.py), [134-155](app/avisos_daemon.py))
- Bandeja Windows con `pystray` + autostart registry HKCU
- Caption bar DWM Windows dark/light
- Theme transition crossfade 350ms con snapshot QPixmap
- ThemeManager singleton con signal `theme_changed`
- 7 módulos cargan vía `importlib.import_module` con caché

**Utilidades que parecen viejas/duplicadas/incompletas:**
- `_GRAD_PUNTAJE` 11 colores hardcoded en [shared/utils.py:23-26](shared/utils.py) — usado solo por `color_por_puntaje_exacto`, paralelo a `COLORES_PUNTAJE` en [app/modules/animo_qt.py:75-79](app/modules/animo_qt.py). Hay duplicación visual.
- Algunas referencias a `fa5s.*` (Font Awesome) que probablemente son legacy de pre-V3 (e.g. `NMEmptyState("fa5s.list-check", ...)` en [app/modules/rutina_qt.py:350](app/modules/rutina_qt.py)).
- `mensajes_biblioteca` (tabla SQLite) creada en migraciones pero sin escritura ni lectura desde código vigente.
- `activacion_perfil` tabla creada pero sin uso visible.

**Partes que cumplen propuesta:** las 7 explícitas (Termómetro, Respiración, TCC, Rutina, Actividades, Timer, Avisos) + mini-stats en Ánimo cubren parcialmente la 8va.

**Partes que superan propuesta:**
- Sync bidireccional con asignaciones remotas.
- Detección automática de 10 distorsiones cognitivas TCC.
- Motor de activación conductual con sugerencias por rango de ánimo.
- Animaciones premium (breath circle pyqtProperty, mood celebration partículas, fade transitions).
- Theme manager dark/light híbrido.
- Daemon de notificaciones del SO con fallback triple.

**Partes que faltan para práctica clínica real:**
- Visualizador longitudinal en Suite (mini en Home).
- Modo privacidad del paciente (PIN al abrir, para PCs compartidas).
- Bandeja de indicaciones del profesional (minimizable, leída/no leída).
- Textos clínicamente sensibles editables desde Hub.

### 2.B NeuroMood Hub (app profesional)

**Para qué sirve:** panel del terapeuta para ver evolución del paciente, asignar tareas/recordatorios, mantener un banco de actividades terapéuticas, y consultar a IA con contexto clínico.

**Usuario:** terapeuta, psiquiatra o equipo NeuroMood. Acceso por anon key Supabase (sin sesión auth), salvo `legal_consents` que tiene política RLS anon dedicada ([db/legal_consents.sql:86-92](db/legal_consents.sql)).

**Entry point:** [hub/main_qt.py:945](hub/main_qt.py) (`NeuroMoodHub(QMainWindow)`), 1360×920 ideal / 1120×760 mínimo. Sidebar 240px con nav `_HUB_NAV_ITEMS` ([hub/main_qt.py:69-74](hub/main_qt.py)).

**4 vistas principales + vista de detalle de paciente:**

#### Dashboard ([hub/main_qt.py:171-389](hub/main_qt.py) `DashboardView`)
- `NMSectionHeader` "PANEL CLÍNICO · N paciente(s)"
- Si hay pacientes: `NMFeaturedCard` con score promedio + emoji + delta + tags hardcoded ("Adherencia alta", "Riesgo bajo", "Agenda al día" — **etiquetas problemáticas según decisión 7**), grid 2 cols: featured izquierda + 3 metrics ring derecha
- En visual QA: timeline de actividad reciente embebida
- Grid responsive de patient cards 250px min
- **NO modifica nada.** Solo lectura.

#### Pacientes ([hub/main_qt.py:400-557](hub/main_qt.py) `PacientesView`)
- Header con "Pacientes vinculados (N)" + botón "Sincronizar" (handler `_cargar_pacientes`) + **botón "+ Nuevo paciente" SIN handler** ([line 453-455](hub/main_qt.py))
- `NMSearchInput` (búsqueda nombre/ID) + `NMTabs` pill (Todos/Activos/Sin registros/Atención — el filtro "atencion" es `adherence < 0.40`, problemático)
- Tabla con `NMPatientRow` (avatar + nombre + ID/última sesión + adherence ring)
- Click → carga `DetallePacienteView` dinámicamente

#### IA Asistente global ([hub/main_qt.py:712-911](hub/main_qt.py) `IAAssistantView`)
- Chat con `NMChatBubble` izquierda/derecha
- `NMProviderChip` muestra estado IA (Groq llama3, Gemini, etc.)
- 3 quick actions hardcoded ([line 791-795](hub/main_qt.py)): "Analizar animo reciente", "Proponer actividades", "Revisar distorsiones"
- `NMQuickAction` button + `NMInput` + Enviar
- `NMPatientContext` panel derecho con nombre paciente
- **IA real**: llama `ia_asistente._llamar()` con sistema prompt hardcoded ([line 840-846](hub/main_qt.py)): "Sos un asistente clínico para terapeutas... Respondés de forma concisa en lenguaje clínico profesional. Nunca hacés diagnósticos ni recomendás medicación. Paciente en contexto: {nombre}."
- **Chat NO persiste** entre sesiones (no se guarda en DB)

#### Config ([hub/main_qt.py:562-707](hub/main_qt.py) `ConfigView`)
- Hero card: `NMSyncOrb` + status ("Conectado"/"Sin conexión"/"Conectando...") + botón "Sincronizar ahora" (handler `_reconnect`)
- Grid 2×2:
  - **Conexión Supabase**: URL (read-only), API Key masked, Auto-sync hardcoded
  - **Apariencia**: Tema (botón **implementado en código, no verificado en ejecución**), Densidad ("Normal" read-only), Idioma ("Español AR" read-only), Proveedor IA ("Groq · llama3-70b" read-only)
  - **Seguridad**: Cifrado local ("AES-256" read-only), Bloqueo automático ("Después de 30 min" read-only), PIN ("No configurado" read-only)
  - **Log sync**: HTML estático con eventos demo
- **🔴 Es lectura pura.** Solo Toggle de tema y "Sincronizar ahora" hacen algo. Resto son labels.

#### Detalle de Paciente ([hub/pacientes_qt.py:1039-1321](hub/pacientes_qt.py) `DetallePacienteView`)
- Header con `NMAvatar` (iniciales) + `NMSectionHeader` "PACIENTE · {nombre}"
- `NMFeaturedCard` con score + delta + meta ("N semanas en programa · Última sesión: hace X días") + tags derivados
- **Card "Estado legal / Consentimiento"**: estado (vigente/desactualizado/revocado/pendiente), accepted_at_utc, disclaimer_version, privacy_version, hash[:16]. Si NO está vigente → tabs deshabilitados.
- Botón "Descargar constancia" → `hub.exportar.generar_constancia_consentimiento()` ([hub/exportar.py:175-254](hub/exportar.py)) genera PDF auditable separado de evolución clínica.
- **QTabWidget con 4 tabs (pills):**

##### Tab Registros ([hub/pacientes_qt.py:237-449](hub/pacientes_qt.py) `_TabRegistros`)
- "↻ Cargar datos" + "Exportar PDF"
- Carga en hilo daemon 6 tablas (mood_records, breathing_sessions, thought_records, checklist_completions, timer_sessions, reminder_logs), limit 15-30 cada una
- Sección Ánimo con gráfico pyqtgraph (spline scipy si disponible, lineal si no) + ring de adherencia (días con registro / 7) + tabla últimos 5
- 4 secciones más con `_card_frame` + `_row_item` (tabla compacta)
- Botón **Exportar PDF** → `hub.exportar.exportar_pdf()` ([hub/exportar.py:23-150](hub/exportar.py))
- **El "Visualizador de Evolución Anímica" de la Propuesta Base vive aquí.**

##### Tab Asignar ([hub/pacientes_qt.py:454-561](hub/pacientes_qt.py) `_TabAsignar`)
- Card 1: "Asignar tarea de rutina" — `NMInput` descripción + combo sección (manana/tarde/noche) + INSERT a `assigned_tasks` ([line 531-535](hub/pacientes_qt.py))
- Card 2: "Enviar recordatorio remoto" — `NMInput` mensaje + hora HH:MM + INSERT a `assigned_reminders` con `dias` hardcoded `"1,2,3,4,5,6,7"` ([line 550-555](hub/pacientes_qt.py))
- Implementado en código — limitado — NO verificado en ejecución.

##### Tab Banco ([hub/pacientes_qt.py:566-781](hub/pacientes_qt.py) `_TabBanco`)
- Formulario nueva actividad: nombre + descripción + combo categoría (`CATEGORY_COLORS` keys) + combo ánimo (1-4/4-7/7-10 hardcoded) + botón "✦ IA: completar" (llama `ia_asistente.autocompletar_actividad`) + "Agregar"
- Lista con dot de categoría + botón delete (×)
- INSERT/DELETE en `activity_bank`
- **Implementado en código — mejor superficie de configurabilidad remota actual — NO verificado en ejecución.**

##### Tab IA ([hub/pacientes_qt.py:786-1023](hub/pacientes_qt.py) `_TabIA`)
- Card "Resumen de evolución" → `ia_asistente.resumir_evolucion(datos, nombre, ...)` con `NMTypingDots` mientras genera + textarea read-only + botón Copiar
- Card "Sugerencias de acción" → `ia_asistente.sugerir_acciones(datos, nombre, ...)` produce 3 sugerencias en filas con botón "Aplicar" (que solo copia al clipboard)
- Card "Generar tarea personalizada" → `ia_asistente.generar_tarea(contexto, ...)`
- Datos vienen de `_DatosRef` ([hub/pacientes_qt.py:1028-1034](hub/pacientes_qt.py)) compartido con Tab Registros
- **IA real, multiproveedor, sin audit log.**

**Qué puede modificar el profesional desde Hub HOY:**
- ✅ Crear actividades en banco (`activity_bank`)
- ✅ Eliminar actividades del banco
- ✅ Asignar tareas (`assigned_tasks`)
- ✅ Asignar recordatorios (`assigned_reminders`)
- ✅ Cambiar tema light/dark
- ✅ Forzar sincronización
- ✅ Exportar PDF de un paciente
- ✅ Descargar constancia legal de consentimiento

**Qué NO puede modificar (gaps críticos):**
- ❌ Crear nuevos pacientes (botón sin handler)
- ❌ Desactivar/reactivar pacientes
- ❌ Editar nombre/email/perfil de paciente
- ❌ Editar plantillas TCC (preguntas, hints, emociones, distorsiones)
- ❌ Editar presets respiración (FASES 4-7-8 hardcoded)
- ❌ Editar presets timer (5/10/25/45 hardcoded)
- ❌ Editar secciones de rutina (mañana/tarde/noche hardcoded)
- ❌ Editar textos visibles en cualquier módulo de Suite
- ❌ Editar mensajes de apoyo / biblioteca
- ❌ Editar disclaimers o textos legales (correcto, no debe editarse)
- ❌ Activar/desactivar módulos por paciente desde UI (los flags existen en DB pero sin UI)
- ❌ Configurar prompts IA (correcto, no debe editarse desde UI)
- ❌ Auditar outputs IA (no hay audit log)
- ❌ Ver historial de chats IA (no persiste)
- ❌ Ver constancia de mensajes enviados al paciente (no hay log de leído/no leído)
- ❌ Configurar idioma o proveedor IA desde UI
- ❌ Configurar grupo/cohorte/programa de tratamiento

**Funciones IA reales** ([hub/ia_asistente.py](hub/ia_asistente.py)):
- 4 proveedores con scoring: Groq (llama-3.3-70b-versatile 95, deepseek-r1-distill-llama-70b 90, ...), Gemini (gemini-2.0-flash 85, ...), OpenCode (gpt-4o 90, ...), Ollama Cloud (llama3.1:70b 85, ...)
- `_pick_best()` ordena candidatos por score, intenta crear cliente, marca como failed los que fallan, retry cada 30s ([line 188-227](hub/ia_asistente.py))
- 4 funciones públicas: `resumir_evolucion`, `sugerir_acciones`, `generar_tarea`, `autocompletar_actividad`
- Idioma rioplatense hardcoded ([line 75](hub/ia_asistente.py))
- Temperatura 0.4, max_tokens 512 hardcoded
- Sistema prompts hardcoded para cada función ([line 321-325, 354-358, 372, 386](hub/ia_asistente.py)) — todos incluyen "Nunca hacés diagnósticos ni recomendás medicación"

**Exportaciones existentes** ([hub/exportar.py](hub/exportar.py)):
- `exportar_pdf` (clínico) — 6 secciones tabla (ánimo + promedio, respiración, TCC, activación, checklist, timer, recordatorios), header con logo NeuroMood, colores warm linen, guardado en `Downloads/NeuroMood_{nombre}_{timestamp}.pdf`, abre con `os.startfile`. ReportLab.
- `generar_constancia_consentimiento` — PDF legal separado con tabla de 12 filas auditables (paciente, ID, estado, fechas, versiones, hashes, scope, profesional team).

**Controles de permisos:** 4 permisos hardcoded en `patients` (Supabase) leídos por Suite. Sin UI en Hub para tocarlos.

**Configuraciones remotas existentes:** ver matriz en Parte 5. Resumen: solo banco de actividades, tareas y recordatorios.

**Configuraciones remotas faltantes:** prácticamente todas las del prompt maestro líneas 100-127 y 456-481. Detalle en Parte 5.

**Partes placeholder/incompletas:**
- ConfigView 100% labels read-only excepto tema y sync
- "+ Nuevo paciente" sin handler
- Quick actions IA hardcoded
- Tags del Featured Card hardcoded
- Filtro "Atención" usa adherence < 40% (problemático según decisión 7 — etiqueta tipo riesgo)

**Partes necesarias para evitar cambios futuros en código:** ver Parte 5 (matriz de configurabilidad).

### 2.C Instaladores y desinstaladores

**Base común** ([shared/installer_common.py](shared/installer_common.py), 663 líneas): `InstallerShell(QMainWindow)` con header (logo + version badge), `NMInstallStepper` ([shared/components_qt.py](shared/components_qt.py) `NMInstallStepper`), QStackedWidget central con fade 150ms, nav footer (btn_ant ghost + btn_sig gradient). Logo siempre `logos-dark.png`. Stylesheet premium clínico unificado con tokens `V3_DARK` (`BG_PRIMARY=#080c1e`, `ACCENT=#2dd4bf`, `GRAD_FROM`, `GRAD_MID`, `GRAD_TO`, `DANGER_FROM=#ef4444`, etc.). `aplicar_captionbar_installer` aplica DWM Windows.

#### Instalador Suite ([installers/installer.py](installers/installer.py))

**Tamaño:** 820×660 fijo. **5 pasos:** Bienvenida → Cuenta → Consentimiento → Instalar → Finalizar.

**Página Bienvenida** ([installer.py:837-979](installers/installer.py)): 2 columnas. Izq: eyebrow + título "Una herramienta para acompañarte" (con GradientTextLabel) + 3 features (Windows 10/11, cifrado local + sync opcional, ~280 MB). Der: logo card + "SUITE PARA PACIENTES" + badge versión.

**Página Cuenta** ([installer.py:983-1201](installers/installer.py)): NMInput email + NMInput password (echo Password) + botones "Iniciar sesión" / "Crear cuenta" (handler `_start_auth`) + "¿Olvidaste tu contraseña?" (handler `_reset_password`). Dot de conexión Supabase + label estado. `_AuthWorker` ejecuta en hilo (`sign_in_with_password`, `sign_up`, `reset_password_for_email`). Manejo robusto de errores (invalid login, email not confirmed, already registered, network).

**Página Consentimiento** ([installer.py:1203-1408](installers/installer.py)): Card legal con `LEGAL_DISCLAIMER_TEXT` ([installer.py:61-81](installers/installer.py)) versionado (`DISCLAIMER_VERSION = "legal-2026-05-16"`, `PRIVACY_VERSION = "privacy-2026-05-16"`). Hash SHA256 del texto. Checkbox obligatorio. Card de aceptación con badges "Constancia local en AppData" + "Constancia remota auditable". Warning card "NeuroMood Suite no es un servicio de emergencias". `_ConsentWorker` ejecuta INSERT en `legal_consents` Supabase (con auth.uid) + guarda local `legal_consent.json`.

**Página Instalar** ([installer.py:1410-1456](installers/installer.py)): NMInput ruta (default `~/NeuroMood`) + Examinar + `NMInstallProgress` (con timeline de líneas y barra de progreso). `_InstalWorker` ejecuta en hilo:
1. Clean previous payload (con manifest y safe_join anti-traversal)
2. Copy NeuroMood Suite.exe (one-dir o one-file)
3. Copy icon
4. Copy Desinstalador Suite
5. Write install_path.txt oculto
6. Write `.neuromood_install_manifest.json`
7. Registro Windows Uninstall (HKCU)
8. Identidad SQLite local con 9 keys (patient_name, patient_email, patient_id, auth_user_id, install_code, 4 permisos = "1")
9. Copy `.env` a `%APPDATA%/NeuroMood/.env` (oculto)
10. Upsert `patients` en Supabase con install_code + 4 permisos

**Página Finalizar** ([installer.py:1459+](installers/installer.py)): Check circle gradient + glow + "Instalación completada" + opcional Escritorio/Menú Inicio shortcuts.

**Soporte payload externo (Fase 7):** Si junto al .exe existe `payload_suite.zip`, lo extrae a TEMP y usa esos archivos en lugar de los bundleados ([installer.py:154-188](installers/installer.py)). Cleanup al salir.

**Restricciones vigentes** (preservadas correctamente):
- ✅ NO Resend
- ✅ NO SMTP custom
- ✅ NO Google OAuth
- ✅ NO "continuar sin cuenta"
- ✅ NO guardar password local en texto plano (PBKDF2 vía [shared/identidad.py](shared/identidad.py))

#### Instalador Hub ([installers/installer_pro.py](installers/installer_pro.py))

**Tamaño:** 820×660 fijo. **3 pasos:** Bienvenida → Instalar → Finalizar (sin Cuenta, sin Consentimiento — el Hub no es paciente, no requiere consent personal).

**Acentos:** violet (vs teal del Suite).

**Flujo:**
1. Bienvenida con 3 mini-cards (Pacientes / Clínica / Remoto)
2. Ruta destino (default `~/NeuroMood Hub`) + `NMInstallProgress`
3. `_ProWorker` copia Hub.exe + Desinstalador Hub + icon + **`.env` a `%APPDATA%/NeuroMoodHub/.env` (oculto)**
4. Registro Windows uninstall
5. Final con `NMCustomCheck` Escritorio + Menú Inicio

**Configuración automática:** lee `.env` con 5 candidatos ([shared/config.py:19-56](shared/config.py)) — prioridad APPDATA/NeuroMood, luego APPDATA/NeuroMoodHub, luego bundle PyInstaller, luego carpeta exe, luego raíz dev, finalmente env vars del sistema (estas últimas con prioridad sobre todas según [config.py:81](shared/config.py)).

#### Desinstalador Suite ([installers/uninstaller.py](installers/uninstaller.py))

**Tamaño:** 760×620 fijo. **3 pasos:** Confirmar → Eliminando → Finalizado.

**Confirmar:** badge warning + título "¿Desinstalar NeuroMood Suite?" + carpeta a eliminar (mono) + **`NMDataPreserveCard` "Conservar mis datos"** (registros, historial, configuración de la app) checked=True por default + info card.

**Worker `_UninstWorker(install_dir, conservar)`:**
1. Matar procesos NeuroMood Suite.exe + procesos hijos en install_dir (vía taskkill + wmic)
2. Eliminar accesos directos Escritorio + Menú Inicio (con validación target = NeuroMood)
3. Eliminar registro HKCU + HKLM Uninstall
4. Cerrar Explorer en carpeta (PowerShell COM)
5. Vaciar install_dir (con validación de ruta protegida + marcador NeuroMood)
6. Si NO conservar → vaciar `%APPDATA%/NeuroMood`
7. Lanza `_nm_cleanup.bat` desde TEMP que borra ejecutable temp post-exit

**`relanzar_desde_temp()`** ([uninstaller.py:255-284](installers/uninstaller.py)): copia bundle a TEMP antes de borrarse a sí mismo, para soportar one-dir y one-file.

**Validaciones de seguridad:** `_es_ruta_protegida` (PROGRAMFILES, WINDIR, ProgramData), `_es_ruta_neuromood` (marker file requerido), `_es_appdata_neuromood` (path debe estar bajo APPDATA y llamarse "NeuroMood" + tener marker).

#### Desinstalador Hub ([installers/uninstaller_pro.py](installers/uninstaller_pro.py))

Mismo flujo, ajustado:
- Marker: `NeuroMood Hub.exe`, `Desinstalador Hub.exe`, `.neuromood_hub_install_manifest.json`
- AppData esperado: `NeuroMoodHub` con `.env`/`logs`
- **Fix 2026-05-18** ([uninstaller_pro.py:283-291](installers/uninstaller_pro.py)): `_ProUninstWorker.__init__` ahora acepta parámetro `conservar=True` por default. Antes fallaba TypeError. ✅ Verificado en código vigente.

#### Flujo de login/registro existente

**Suite:** Supabase Auth directo:
- Login: `sign_in_with_password(email, password)` → recibe access_token + refresh_token
- Signup: `sign_up(email, password)` → si requiere email confirmation, queda "pendiente"
- Reset: `reset_password_for_email(email)` → envía email Supabase (no Resend)
- Estado almacenado en SQLite local: `patient_name`, `patient_email`, `patient_id`, `auth_user_id`, `install_code`. PBKDF2 hash en `patient_pwd`.

**Hub:** sin login UI. Lee `.env` con anon key. Acceso a tablas clínicas via RLS deshabilitado. `legal_consents` via policy `legal_consents_select_anon_hub` ([db/legal_consents.sql:86-92](db/legal_consents.sql)).

#### Flujo legal existente

**Constancia local:** `%APPDATA%/NeuroMood/legal_consent.json` con email, user_id, patient_id, accepted_at_utc, versiones, hashes, scope, status="vigente".

**Constancia remota:** INSERT en `legal_consents` Supabase con auth bearer (set_session) — protegida por RLS policy `legal_consents_insert_own` (`to authenticated WITH CHECK (auth.uid() = user_id)`).

**Validación:** al abrir Suite, `_load_local_consent` verifica que email/user_id/versions coincidan con vigente.

**Versionado:** Si `DISCLAIMER_VERSION` o `PRIVACY_VERSION` cambian, el instalador re-solicita aceptación.

**Hub muestra:** estado del consentimiento + tabs deshabilitadas si no es "vigente". `legal_consents_select_anon_hub` permite lectura sin sesión.

#### Qué guarda localmente

- `%APPDATA%/NeuroMood/nm_data.db` (SQLite)
- `%APPDATA%/NeuroMood/.env` (oculto, con SUPABASE_URL + SUPABASE_KEY anon)
- `%APPDATA%/NeuroMood/legal_consent.json`
- `%APPDATA%/NeuroMood/logs/{suite|hub|installer_*}.log`
- `%APPDATA%/NeuroMoodHub/.env` (oculto, para Hub)
- HKCU `Software\Microsoft\Windows\CurrentVersion\Uninstall\NeuroMoodSuite` (y `NeuroMoodHub`)
- HKCU `Software\Microsoft\Windows\CurrentVersion\Run\NeuroMood` (si autostart activado vía avisos_qt o avisos_daemon)

#### Qué registra en Supabase

- `patients` con `patient_id`, `patient_name`, `pwd` (hash), `install_code`, 4 permisos
- `legal_consents` (INSERT al aceptar consent)
- `mood_records`, `breathing_sessions`, `thought_records`, `checklist_completions`, `timer_sessions`, `reminder_logs` (vía sync)

#### Riesgos detectados

- **No hay firma de código** en los EXE. Windows Defender SmartScreen va a alertar al usuario en cada instalación. Posible feedback negativo del paciente real.
- **`payload_*.zip` modo externo** asume confianza en el zip (no firmado). Si alguien reemplaza el zip junto al installer, ejecuta otro código.
- **RLS deshabilitado en tablas clínicas** → cualquier persona con la anon key puede leer todos los registros de todos los pacientes. Defensible si la anon key se mantiene "secreta" (en la práctica está en el `.env` distribuido). En entorno clínico controlado puede ser aceptable, pero debe documentarse explícitamente y considerarse para F5.
- **Sin manejo de errores de red en consent remoto:** si falla la inserción Supabase, el instalador muestra error pero **no continúa** ([installer.py:1395-1408](installers/installer.py)). Esto es correcto pero el paciente con mala conexión queda bloqueado del producto.
- **Sin telemetría de uso ni crash reporting remoto** (solo logs locales en `%APPDATA%/NeuroMood/logs/`).
- **`legal_consent.json` local puede borrarse manualmente** → al reinstalar exige nueva aceptación (correcto, pero el paciente puede pensar que es un bug).

#### Qué falta para distribución real

- Firma de código Authenticode (certificate EV idealmente)
- Versionado consistente (`NEUROMOOD_SUITE_VERSION = "1.0.0"` hardcoded en [installer.py:53](installers/installer.py))
- Instalador unificado opcional ("Instalar todo: Suite + Hub")
- Telemetría agregada anónima (¿cuántos instalan, en qué versión, cuántos completan onboarding, sin PII)
- Manejo robusto de "no internet" durante consent (modo offline con cola de sync)
- Auto-actualización (la actual exige reinstalar)
- Modo bilingüe (hoy todo en español)
- Tests automáticos de instalador en CI (smoke test post-build)

#### Qué experiencia tendría un paciente real

1. Recibe link al instalador `Instalador Suite.exe` (probablemente vía email o descarga de [neuromood.com.ar](https://neuromood.com.ar) — no validado en el repo).
2. Windows SmartScreen alerta "Publisher desconocido" → puede asustar o frenar.
3. Pantalla bienvenida amigable, copy correcto, 3 features claras.
4. Cuenta: email + pass (mínimo 6 chars), sin captcha, sin recovery por SMS. Si confirmación Supabase activa, debe ir al email y volver.
5. Consentimiento: scroll de ~80 líneas legales, checkbox, advertencia emergencias, badges. Registro remoto puede fallar si hay problema de red → bloqueo total.
6. Ruta de instalación (default `~/NeuroMood` — visible al usuario).
7. Instalación: progress bar + log de pasos. ~30s típico.
8. Finalizar: shortcut Escritorio + Menú Inicio.
9. Primera apertura: registra autostart con permiso implícito (no se explica al usuario).

**Riesgos UX:** SmartScreen, fallo de red en consent, ruta visible (técnicos pueden no entender el path), autostart sin opt-in explícito.

#### Qué experiencia tendría un profesional real

1. Descarga `Instalador Hub.exe` + (opcional) `payload_hub.zip`.
2. SmartScreen alerta.
3. Bienvenida + 3 features (Pacientes / Clínica / Remoto).
4. Ruta destino (default `~/NeuroMood Hub`).
5. Instala. Copia `.env` a AppData. Sin pedir credenciales (configuración automática).
6. Final: shortcut Escritorio + Menú Inicio.
7. Primera apertura: orbe de sync "Conectando...". Si no encuentra `.env` válido o credenciales no funcionan, el Hub queda en "Sin conexión".
8. Al conectar, carga pacientes vinculados (los que tienen mismo install_code o están en `patients`).

**Riesgos UX:** sin paso de validación de credenciales en instalador (puede instalar y descubrir que falla al abrir Hub). Sin onboarding para terapeutas nuevos al producto.

---

## PARTE 3 — Matriz Suite / Hub / SQLite / Supabase

Una fila por **capacidad cruzada**. Marca `✓` = sí, `✗` = no, `~` = parcial.

| App origen | Archivo / módulo | Función visible para el usuario | Herramienta original Propuesta Base | Tabla SQLite | Tabla Supabase | Dato generado por paciente | Visible en Hub | Hub puede modificarlo | Hub puede configurarlo remotamente | Suite lo consume | Funciona offline | Depende de sync | Depende de permisos | Estado | Riesgo técnico | Riesgo clínico/legal | Riesgo feedback cliente | Recomendación |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Suite | [animo_qt.py:222](app/modules/animo_qt.py) | Registrar ánimo 1-10 + nota | 1 Termómetro | `termometro` | `mood_records` | ✓ | ✓ (Tab Registros) | ✗ | ✗ (etiquetas hardcoded) | — | ✓ | sólo export | ✗ | Implementado en código (no verificado en ejecución) | Bajo | Bajo | Medio (cliente puede pedir etiquetas custom) | Configurar etiquetas (Parte 5) |
| Suite | [animo_qt.py](app/modules/animo_qt.py) | Ver mini-stats semana (promedio/racha/progreso) | 7 Visualizador (parcial) | `termometro` | `mood_records` | ✓ | — (gráfico vive en Hub) | ✗ | ✗ | — | ✓ | ✗ | ✗ | Implementado en código (no verificado en ejecución) | Bajo | Bajo | **Alto** — cliente puede pedir gráfico longitudinal lado paciente | F1: mini-visualizador en Home Suite |
| Suite | [respiracion_qt.py:516](app/modules/respiracion_qt.py) | Hacer respiración 4-7-8 | 5 Respiración | `respiracion` | `breathing_sessions` | ✓ | ✓ (Tab Registros) | ✗ | ✗ (presets hardcoded) | — | ✓ | sólo export | ✗ | Implementado en código (no verificado en ejecución) | Bajo | Bajo | **Medio-Alto** — cliente puede pedir 4-4-4 o 5-5-5 | Editor presets respiración remoto |
| Suite | [registro_tcc_qt.py:323](app/modules/registro_tcc_qt.py) | Registrar pensamiento TCC en 4 pasos | 4 Registro TCC | `pensamientos` | `thought_records` | ✓ | ✓ (Tab Registros) | ✗ | ✗ (preguntas/tips/emociones hardcoded) | — | ✓ | sólo export | ✗ | Implementado en código (no verificado en ejecución) | Bajo | **Alto** — el equipo clínico tiene formación específica TCC, puede querer diferentes preguntas | **Alto** — sin edición remota van a pedir cambios constantes | F2: plantilla TCC editable + remote_config |
| Suite | [registro_tcc_qt.py:700-770](app/modules/registro_tcc_qt.py) | Detectar 10 distorsiones cognitivas | 4 Registro TCC | (lógica en código) | (en `pensamientos.distorsiones`) | inferido | ✓ | ✗ | ✗ (keywords `_KWORDS` hardcoded) | — | ✓ | ✗ | ✗ | Implementado en código (no verificado en ejecución) | Bajo | Medio | Alto — puede haber keywords incorrectas/missing | Configurar `_KWORDS` desde Hub (F2) |
| Suite | [rutina_qt.py:311](app/modules/rutina_qt.py) | Marcar tareas + nota del día | 6 Checklist Rutina | `checklist_tareas` + `checklist_completadas` + `checklist_notas_dia` | `checklist_completions` (sin notas_dia) | ✓ | ✓ (Tab Registros) | ~ (vía assigned_tasks) | ~ (puede asignar tarea individual) | tareas asignadas | ✓ | export + import asignadas | `perm_checklist_manual` | Implementado en código (no verificado en ejecución) | Bajo | Bajo | Medio — secciones hardcoded | Editor plantillas rutina remoto |
| Suite | [actividades_qt.py:555](app/modules/actividades_qt.py) | Recibir sugerencia + registrar resultado | 8 Activación Conductual | `activacion` + `activacion_actividades` | `activity_bank` + `patient_activities` + `activacion` (via checklist_completions origen=activacion) | ✓ | ✓ (Tab Registros, Tab Banco) | ✓ | ✓ CRUD banco + ánimo_min/max | actividades | ✓ | import + export | `perm_checklist_activacion` | Implementado en código (no verificado en ejecución) | Bajo | Bajo | Bajo (caso de éxito) | Mantener como referencia |
| Suite | [timer_qt.py:158](app/modules/timer_qt.py) | Hacer sesión timer | 3 Temporizador | `actividades_temporizador` | `timer_sessions` | ✓ | ✓ (Tab Registros) | ✗ | ✗ (presets 5/10/25/45 hardcoded) | — | ✓ | sólo export | `perm_temporizador_manual` | Implementado en código (no verificado en ejecución) | Bajo | Bajo | Medio | Editor presets timer remoto |
| Suite | [avisos_qt.py:565](app/modules/avisos_qt.py) | Crear recordatorios locales | 2 Recordatorios | `recordatorios` + `recordatorios_log` | `reminder_logs` (logs) + `assigned_reminders` (asignados) | ✓ (locales) o profesional (asignados) | ✓ (Tab Registros) | ~ (vía assigned_reminders) | ~ (puede asignar uno individual) | recordatorios | ✓ | export + import | `perm_recordatorios_manual` | Implementado en código (no verificado en ejecución) | Bajo | Bajo | Medio (categorización keywords hardcoded) | Editor categorías + mensajes biblioteca |
| Suite | [avisos_daemon.py:43-67](app/avisos_daemon.py) | Disparar notificaciones del SO | 2 Recordatorios | `recordatorios` + `recordatorios_log` | `reminder_logs` | inferido | ✓ (logs) | ✗ | ✗ | recordatorios | ✓ | ✗ | ✗ | Implementado en código (no verificado en ejecución) | Medio (depende de pystray/winotify) | Bajo | Bajo | Mantener. Documentar dependencias |
| Suite | [home_qt.py:825-841](app/home_qt.py) | Bloquear módulos según permisos | — | `config.perm_*` | `patients.perm_*` | ✗ | ✓ (en DB) | ~ (puede ALTER vía Supabase, sin UI) | ✗ (sin UI Hub) | — | ✓ (lee local) | sólo import | ✓ | Implementado en código (no verificado en ejecución) | Bajo | Bajo | Medio | **Crítico**: UI Hub para togglear permisos por paciente |
| Hub | [main_qt.py:171-389](hub/main_qt.py) | Dashboard panel clínico | — | — | `patients` + `mood_records` | ✗ | ✓ | ✗ (sólo lee) | — | — | ✗ | ✓ | ✗ | Implementado en código (no verificado en ejecución) | Bajo | 🔴 **Crítico — F0.1 bloqueante** — tags "Adherencia alta", "Riesgo bajo" hardcoded (decisión 7 prohíbe semáforos) | F0.1: Quitar tags tipo riesgo antes del piloto |
| Hub | [main_qt.py:400-557](hub/main_qt.py) | Listar/filtrar pacientes | — | — | `patients` | ✗ | ✓ | ✗ ("Nuevo paciente" sin handler) | — | — | ✗ | ✓ | ✗ | **Incompleto** | Bajo | 🔴 **Crítico — F0.1 bloqueante** — filtro "Atención" usa adherence<40% (decisión 7) | F0.1: reemplazar filtro por criterio neutral + handler "+ Nuevo paciente" |
| Hub | [pacientes_qt.py:237-449](hub/pacientes_qt.py) | Ver registros + gráfico evolución + export PDF | 7 Visualizador | — | 6 tablas clínicas | ✗ | ✓ | ✗ | — | — | ✗ | ✓ | ✓ (consent vigente) | Implementado en código (no verificado en ejecución) | Bajo | Bajo | Bajo (caso de éxito) | Agregar rangos fecha configurables |
| Hub | [pacientes_qt.py:454-561](hub/pacientes_qt.py) | Asignar tarea/recordatorio individual | 6, 2 | — | `assigned_tasks` + `assigned_reminders` | ✗ | ✓ | ✓ | ~ (sólo individuales, no plantillas) | tareas/recordatorios | — | ✓ | ✗ | Implementado en código (no verificado en ejecución) | Bajo | Bajo | Bajo | Mantener + extender con plantillas |
| Hub | [pacientes_qt.py:566-781](hub/pacientes_qt.py) | CRUD banco actividades + IA autocomplete | 8 | — | `activity_bank` + `patient_activities` | ✗ | ✓ | ✓ | ✓ (caso de éxito) | actividades | — | ✓ | ✗ | Implementado en código (no verificado en ejecución) | Bajo | Bajo | Bajo (referencia para Parte 5) | Mantener |
| Hub | [pacientes_qt.py:786-1023](hub/pacientes_qt.py) | IA: resumir/sugerir/generar tarea | — | — | — (no persiste) | ✗ | ✓ | — | ✗ (prompts hardcoded — correcto) | — | — | ✗ (IA online) | ✗ | Implementado en código (no verificado en ejecución) | **Medio — sin audit log** | **Alto** — sin auditoría de outputs IA | Alto — equipo clínico/legal va a pedir audit | F4: tabla `ia_audit_log` + persistir chat |
| Hub | [main_qt.py:712-911](hub/main_qt.py) | Chat IA global | — | — | — (no persiste) | ✗ | ✓ | — | ✗ | — | — | ✗ | ✗ | Implementado en código (no verificado en ejecución) | Medio | Alto | Alto | Persistir + audit log |
| Hub | [main_qt.py:562-707](hub/main_qt.py) | ConfigView | — | — | — | ✗ | ✓ | ✗ (sólo tema y sync hacen algo) | ✗ | — | — | ✗ | ✗ | **Read-only** | Bajo | Bajo | **Muy Alto** — el cliente espera poder configurar desde acá | F2: ConfigView editable/configurable |
| Hub | [exportar.py:23-150](hub/exportar.py) | Exportar PDF clínico | 7 (parcial) | — | 6 tablas (lectura) | ✗ | — (genera artefacto) | ✗ (plantilla hardcoded) | ✗ | — | — | ✓ | ✗ | Implementado en código (no verificado en ejecución) | Bajo | Bajo | Medio (plantilla fija) | Constructor de informes configurable |
| Hub | [exportar.py:175-254](hub/exportar.py) | Exportar constancia legal PDF | — | — | `legal_consents` (lectura) | ✗ | ✓ | ✗ (correcto, decisión 5) | ✗ (correcto) | — | — | ✓ | ✓ | Implementado en código (no verificado en ejecución) | Bajo | Bajo (cumple) | Bajo | Mantener |
| Sistema | [installer.py:340-520](installers/installer.py) | Auth Supabase + Consent | — | `config` | `patients` + `legal_consents` | — | ✓ (legal_consents) | ✗ | ✗ | identidad + 4 permisos | ✗ (online required) | ✓ | ✗ | Implementado en código (no verificado en ejecución) | Bajo | Bajo (cumple) | Medio (bloqueo si red falla) | F6: modo offline en consent (cola) |
| Sistema | [sync.py:303-332](shared/sync.py) | Sync completo paciente↔nube | — | todas | todas | — | ✓ (ve resultado) | ✗ | ✗ | todo | ✗ | ✓ | ✗ | Implementado en código (no verificado en ejecución) | Medio (silencia excepciones) | Bajo | Medio | F6: logs sync visibles |
| Sistema | [avisos_daemon.py:269-305](app/avisos_daemon.py) | Bandeja Windows + autostart | 2 | — | — | — | ✗ | ✗ | ✗ | recordatorios | ✓ | ✗ | ✗ | Implementado en código (no verificado en ejecución) | Medio (pystray opcional) | Bajo | Bajo | Mantener |
| Configuración remota | — | Textos visibles Suite | — | (no existe) | (no existe) | — | ✗ | ✗ | ✗ | ✗ | n/a | n/a | n/a | **No existe** | Alto si se pide cambio | **Alto** | **Muy Alto** | F2: `hub_text_overrides` |
| Configuración remota | — | Plantillas TCC | 4 | (no existe) | (no existe) | — | ✗ | ✗ | ✗ | ✗ | n/a | n/a | n/a | **No existe** | Alto | **Alto** | **Muy Alto** | F2: `tcc_templates` |
| Configuración remota | — | Habilitar módulos por paciente | — | (no existe UI) | `patients.perm_*` (DB sí) | — | ~ (DB sí, UI no) | ~ | ✗ | ✓ | n/a | sólo import | ✓ | **Sin UI** | Bajo | Bajo | Medio | F2: panel permisos por paciente |
| Configuración remota | — | Editor mensajes apoyo | — | `mensajes_biblioteca` (local sin uso) | (no existe) | — | ✗ | ✗ | ✗ | ✗ | n/a | n/a | n/a | **No existe** | Bajo | Bajo | Alto | F2: `support_messages` |
| Configuración remota | — | Bandeja indicaciones profesional → paciente | — | (no existe) | (no existe) | — | ✗ | ✗ | ✗ | ✗ | n/a | n/a | n/a | **No existe** | Bajo | Bajo | Medio-Alto | F4: `professional_messages` |

### Síntesis Parte 3

- **Qué genera el paciente:** 6 streams clínicos (animo, respiracion, pensamientos, checklist, timer, recordatorios) + identidad + log de avisos.
- **Qué ve el profesional:** todo lo anterior vía 6 tablas Supabase, + `legal_consents`.
- **Qué manda el profesional al paciente:** tareas individuales (`assigned_tasks`), recordatorios individuales (`assigned_reminders`), actividades del banco global (`activity_bank`), actividades personalizadas (`patient_activities`), 4 permisos (en DB, sin UI Hub).
- **Qué configura el profesional:** sólo lo anterior. **No textos, no plantillas, no presets, no módulos enabled/disabled vía UI, no mensajes biblioteca, no idioma, no prompts IA.**
- **Qué NO puede configurar todavía:** prácticamente toda la matriz de configurabilidad (Parte 5).
- **Qué depende de sync:** asignaciones, banco actividades, permisos, ver registros desde Hub, exportar PDF.
- **Qué depende de permisos:** 4 módulos paciente (rutina manual, actividades, timer, recordatorios manual).
- **Qué depende de Supabase:** todo lo anterior + IA Hub (requiere internet).
- **Qué funciona offline:** Suite completa para registro local. Sólo se pierde sync hasta volver online. Hub no funciona offline (no tiene UI fallback sin conexión).

---

## PARTE 4 — Inventario de utilidades actuales

### 4.A Utilidades actuales para pacientes

#### Termómetro Emocional ([animo_qt.py](app/modules/animo_qt.py))
- **Nombre vigente:** Ánimo / Mood Tracker
- **Nombre Propuesta Base:** Termómetro Emocional (1)
- **Archivo:** [app/modules/animo_qt.py:222](app/modules/animo_qt.py) `ModuloAnimo`
- **Objetivo:** registro emocional diario 1-10 + nota libre 500 chars
- **Flujo:** abrir → ver wave chart + 3 stats → mover V3MoodSlider → escribir nota → "Guardar registro" → si ≥7 partículas
- **Valor:** consolida la práctica diaria de check-in emocional
- **Datos generados:** `termometro` (fecha, hora, puntaje, nota) + sync a `mood_records`
- **Locales:** todos los registros históricos
- **Sincroniza:** todos los registros (export 6 streams)
- **Visibilidad Hub:** Tab Registros (gráfico + tabla)
- **Configurable Hub:** ✗ — etiquetas, colores, mood emoji, COLORES_PUNTAJE todo hardcoded
- **Debería poder configurar el profesional:** etiquetas semánticas (Muy mal/Mal/Neutro/Bien/Muy bien o custom), nota placeholder, frase de apoyo post-registro
- **Función Propuesta Base:** **cumple ✓** — registro diario 1-10 con almacenamiento automático local + sync.
- **Rol en el Ánimo Loop:** **fuente de verdad de la variable ánimo**. Alimenta al Visualizador (gráfica histórica en Hub + mini-stats en Suite) y al Asistente de Activación Conductual (criterio para filtrar actividades por rango `animo_min`/`animo_max`).
- **Estado:** **Implementado en código — NO verificado en ejecución** (UI premium con V3MoodSlider + NMWaveChart + partículas requiere runtime real para confirmar animaciones, glow, beeps).
- **Problemas:** mini-stats en Suite no es un gráfico longitudinal completo (se cierra con F1).
- **Riesgo feedback:** Medio
- **Mejora:** mini-visualizador en Home (F1) + etiquetas configurables desde Hub

#### Guía de Respiración Animada ([respiracion_qt.py](app/modules/respiracion_qt.py))
- **Nombre vigente:** Respiración
- **Propuesta Base:** Guía de Respiración Animada (5)
- **Archivo:** [app/modules/respiracion_qt.py:516](app/modules/respiracion_qt.py) `ModuloRespiracion`
- **Objetivo:** pausa de respiración guiada 4-7-8
- **Flujo:** elegir preset (3/5/10 min) → Play → ciclo animado → Save al stop si ciclos>0
- **Valor:** autorregulación + presencia
- **Datos:** `respiracion` (fecha, hora, tecnica="4-7-8", duracion, ciclos)
- **Sincroniza:** sí
- **Visibilidad Hub:** Tab Registros (tabla simple)
- **Configurable Hub:** ✗ — FASES hardcoded [respiracion_qt.py:82-87](app/modules/respiracion_qt.py), PRESETS [89-93](app/modules/respiracion_qt.py)
- **Profesional debería:** editar técnicas (4-4-4, 5-5-5, 4-7-8), duraciones, BPM target, instrucciones
- **Estado:** **Implementado en código — NO verificado en ejecución** (animaciones de `pyqtProperty`, glow del círculo, beep al finalizar requieren runtime real)
- **Problemas:** sólo una técnica visible
- **Riesgo feedback:** Medio-Alto (equipo clínico puede pedir variantes)
- **Mejora:** editor presets respiración remoto (Parte 8)

#### Registro de Pensamientos (TCC) ([registro_tcc_qt.py](app/modules/registro_tcc_qt.py))
- **Nombre vigente:** Registro TCC
- **Propuesta Base:** Registro de Pensamientos TCC (4)
- **Archivo:** [app/modules/registro_tcc_qt.py:323](app/modules/registro_tcc_qt.py) `ModuloRegistroTCC`
- **Objetivo:** reestructuración cognitiva en 4 pasos (Situación → Emoción → Pensamiento → Respuesta)
- **Flujo:** wizard guiado con NMTCCStepper + 4×2 emotion tiles + heat bar intensidad 0-10 + detección automática de distorsiones + tip terapéutico + respuesta alternativa
- **Valor:** alta — técnica TCC core
- **Datos:** `pensamientos` con 13 campos (incluye evidencia_favor/contra, creencia_antes/despues, reflexion_ia)
- **Sincroniza:** sí (todos los campos)
- **Visibilidad Hub:** Tab Registros (snippet 60 chars + emoción + intensidad)
- **Configurable Hub:** ✗ — _STEP_NAMES, _EMOTIONS_GRID, _KWORDS distorsiones, _TipCard texto, validaciones por paso todo hardcoded
- **Profesional debería:** editar las 4 preguntas guiadas, las 8 emociones del grid, las 10 distorsiones y sus keywords, el tip terapéutico, los campos requeridos, mensajes de éxito
- **Estado:** **Implementado en código (excelente UX leyendo el wizard 4 pasos + heatbar + tip card) — NO verificado en ejecución** (animaciones del NMTCCStepper y heatbar requieren runtime)
- **Problemas:** **TODO el contenido clínicamente sensible es hardcoded.** Es el módulo de mayor riesgo si el equipo clínico quiere customizar.
- **Riesgo feedback:** **Alto**
- **Mejora:** prioridad #1 para plantillas remotas (F2 — Parte 8)

#### Checklist de Rutina Diaria ([rutina_qt.py](app/modules/rutina_qt.py))
- **Nombre vigente:** Rutina
- **Propuesta Base:** Checklist de Rutina Diaria (6)
- **Archivo:** [app/modules/rutina_qt.py:311](app/modules/rutina_qt.py) `ModuloRutina`
- **Objetivo:** estructura diaria, hábitos
- **Flujo:** ver Hero ring del día + 3 secciones (Mañana/Tarde/Noche) + tareas con NMCustomCheck + nota del día (lock una vez guardada) + "+ Agregar tarea" inline por sección + click hace winsound.Beep
- **Valor:** alta
- **Datos:** `checklist_tareas` (incluye campo `origen` 'manual'/'profesional', [shared/db.py:269](shared/db.py)) + `checklist_completadas` + `checklist_notas_dia`
- **Sincroniza:** completadas sí (no notas), `assigned_tasks` → inserta tareas con `origen='profesional'` ([shared/sync.py:189-223](shared/sync.py))
- **Visibilidad Hub:** Tab Registros (tabla, distingue Profesional vs Paciente vía `origen` — [hub/exportar.py:116](hub/exportar.py))
- **Configurable Hub:** ~ — sólo asignación individual de tareas con `seccion`. **Secciones hardcoded** ([rutina_qt.py:77-81](app/modules/rutina_qt.py)). Tabla local `checklist_plantillas` sin contraparte remota.
- **Profesional debería:** crear plantillas de rutinas semanales (ej. "Rutina depresión leve", "Rutina post-TEC"), editar nombres de secciones, asignar plantillas a paciente
- **Interpretación Propuesta Base + opción C (decisión 2026-05-21):** la lista de tareas debe estar **delimitada por el equipo profesional**, **pero** para no ser paternalista el paciente debería poder crear tareas propias bajo ciertas condiciones. **Opción C propuesta** — sistema híbrido configurable por paciente desde Hub, con 3 modos en un nuevo campo `rutina_modo` en `patients`:
  - `solo_profesional`: paciente recibe plantilla, **NO puede agregar tareas propias**. Para fase aguda, baja capacidad de organización autónoma, foco terapéutico estricto.
  - `mixto` (DEFAULT): paciente recibe plantilla del profesional + puede agregar tareas propias marcadas con badge "Personal" (campo `origen='manual'` ya implementado). Para fase de estabilización y mayoría de casos.
  - `solo_paciente`: paciente autónomo, sin plantilla del profesional impuesta. Para mantenimiento o pacientes con alta autonomía.
- **Justificación opción C:** la opción A (binario habilitar/inhabilitar tareas propias) no respeta gradación clínica. La B (siempre habilitado por default) no respeta fase aguda. **C** reusa infraestructura existente (`origen`, `perm_checklist_manual`, `patients`) y permite al profesional elegir caso a caso desde Hub Tab Asignar → sección Rutina.
- **UI Suite:** las tareas propias del paciente quedan con un pequeño badge "Personal" (no intrusivo) para que el paciente entienda qué viene del equipo y qué creó él. El profesional puede ver las tareas propias del paciente en Hub Tab Registros (ya disponible vía campo `origen`).
- **Estado:** **Implementado en código — NO verificado en ejecución**. Infraestructura para opción C ya parcialmente lista (`origen`, sync `_importar_tareas_asignadas`).
- **Problemas:** secciones fijas, no plantillas remotas, nota del día no se sincroniza, sin sistema 3 estados todavía.
- **Riesgo feedback:** Medio
- **Mejora:** editor de plantillas rutinas + selector modo por paciente (F2 — Parte 8)

#### Asistente de Activación Conductual ([actividades_qt.py](app/modules/actividades_qt.py))
- **Nombre vigente:** Actividades
- **Propuesta Base:** Asistente de Activación Conductual (8)
- **Archivo:** [app/modules/actividades_qt.py:555](app/modules/actividades_qt.py) `ModuloActividades` + [app/motor_activacion.py](app/motor_activacion.py)
- **Objetivo:** proponer actividades según ánimo declarado por el paciente
- **Flujo:** abrir → header con mood actual (leído del último Termómetro) → 6 categorías (Autocuidado, Física, Cognitiva, Placer, Social, Maestría) + tabs filtro → grid 3 cols de sugeridas curadas por profesional → Hice esto / No pude
- **Valor:** alta — única herramienta con full configurabilidad remota
- **Datos:** `activacion` (resultado), `activacion_actividades` (banco local), `activity_bank` + `patient_activities` (remoto)
- **Sincroniza:** sí + importa banco
- **Visibilidad Hub:** Tab Registros + Tab Banco (CRUD)
- **Configurable Hub:** ✓ — caso de éxito. CRUD desde Tab Banco con IA autocomplete
- **Profesional debería:** ya puede. Mejora: categorías editables, intensidad por paciente
- **Función Propuesta Base:** **cumple ✓** — propone actividades según variable declarada por el paciente. **No es automatismo oculto:** el paciente declara su ánimo conscientemente en el Termómetro, el profesional configura los rangos `animo_min`/`animo_max` por actividad desde Hub Tab Banco, y opcionalmente sobrescribe con `patient_activities` por paciente individual. Si no hay registro de ánimo, cae en fallback `ACTIVIDADES_DEFAULT` ([motor_activacion.py:8-19](app/motor_activacion.py)).
- **Decisión interpretativa (2026-05-21):** la Propuesta Base dice "nivel de energía declarado al inicio de la sesión". Se interpretó como **ÁNIMO** (variable ya registrada en Termómetro). **No se mide ni registra energía como variable separada**; reutilizar ánimo evita pedir al paciente declarar dos métricas similares en cada sesión y mantiene el loop Termómetro → Activador coherente.
- **Rol en el Ánimo Loop:** consumidor del último registro del Termómetro. Profesional cura el banco desde Hub.
- **Estado:** **Implementado en código — NO verificado en ejecución** (configuración remota es la única validada parcialmente vía CRUD del banco desde el Hub).
- **Riesgo feedback:** Bajo
- **Mejora:** referencia para el resto. Mantener.

#### Temporizador de Actividades ([timer_qt.py](app/modules/timer_qt.py))
- **Nombre vigente:** Timer
- **Propuesta Base:** Temporizador de Actividades (3)
- **Archivo:** [app/modules/timer_qt.py:158](app/modules/timer_qt.py) `ModuloTimer`
- **Objetivo:** delimitar actividades terapéuticas por tiempo
- **Flujo:** elegir preset (5/10/25/45 min) o custom (1-120) → escribir nombre actividad → Play → tick cada 1s → últimos 10s blink → winsound.Beep doble + restore window
- **Valor:** moderada
- **Datos:** `actividades_temporizador` (fecha, hora, nombre, categoria="Timer", duracion_config, duracion_real)
- **Sincroniza:** sí
- **Visibilidad Hub:** Tab Registros
- **Configurable Hub:** ✗ — PRESETS hardcoded [timer_qt.py:71-76](app/modules/timer_qt.py). Tabla local `timer_presets` sin contraparte remota.
- **Profesional debería:** definir presets (10/15/20/30/40), categorías, nombre default, y limitar acceso a custom
- **Interpretación Propuesta Base (2026-05-21):** *"Temporizador con alarma suave para **delimitar actividades terapéuticas** por tiempo."* — las actividades terapéuticas las **delimita el profesional desde Hub**, no las auto-prescribe el paciente (el paciente no está formado para auto-prescribir tratamiento). **Estado actual: NO cumple esta interpretación** — el paciente elige libremente preset o custom. Permiso `perm_temporizador_manual` existe ([db/supabase_schema.sql:13](db/supabase_schema.sql)) pero hoy sólo bloquea el módulo entero ([home_qt.py:811-841](app/home_qt.py)), no diferencia presets vs custom.
- **Recomendación:** el profesional define presets vía Hub (`timer_presets_remote` por scope global + por paciente). El permiso `perm_temporizador_manual` pasa a significar *"el paciente puede usar custom además de los presets asignados"*. Por defecto el paciente sólo elige entre presets curados por el equipo (interpretación Propuesta Base 3). Reusa tabla local `timer_presets` ya creada en [shared/db.py:219-228](shared/db.py).
- **Estado:** **Implementado en código — NO verificado en ejecución** (countdown, winsound.Beep, auto-restore window son runtime Windows).
- **Problemas:** presets fijos + sin distinción presets vs custom.
- **Riesgo feedback:** **Alto** — contradice interpretación Propuesta Base. Prioridad 🔴 F2.
- **Mejora:** editor presets timer remoto + override de `perm_temporizador_manual` (F2 prioridad alta)

#### Recordatorios de Bienestar ([avisos_qt.py](app/modules/avisos_qt.py))
- **Nombre vigente:** Avisos
- **Propuesta Base:** Recordatorios de Bienestar (2)
- **Archivo:** [app/modules/avisos_qt.py:565](app/modules/avisos_qt.py) `ModuloAvisos` + [app/avisos_daemon.py](app/avisos_daemon.py)
- **Objetivo:** medicación, pausas, hábitos, mensajes de apoyo
- **Flujo:** + Nuevo aviso → hora HH:MM + mensaje + días pills (L M X J V S D) → guardar → daemon dispara notificación Windows + log
- **Valor:** alta (adherencia medicación)
- **Datos:** `recordatorios` + `recordatorios_log`
- **Sincroniza:** logs sí, definiciones sólo se importan desde profesional via `assigned_reminders`
- **Visibilidad Hub:** Tab Registros (logs) + Tab Asignar (crear nuevos)
- **Configurable Hub:** ~ — sólo asignación individual. **Categorización inferida hardcoded** ([avisos_qt.py:79-102](app/modules/avisos_qt.py): keywords "medic", "agua", "respir", etc.). Silencio horario y autostart son configuración local solamente.
- **Profesional debería:** crear biblioteca de mensajes de apoyo + plantillas de recordatorios reutilizables, editar mensajes por categoría
- **Interpretación Propuesta Base (2026-05-21):** *"Ventana emergente configurable con mensajes de apoyo a horarios fijos **determinados por el equipo**."* — los mensajes de apoyo y los horarios fijos los **determina el equipo profesional**, no el paciente. **Estado actual: PARCIAL** — hoy el paciente puede crear recordatorios propios libremente; el profesional sólo puede asignar individuales (no plantillas) vía `assigned_reminders`; el permiso `perm_recordatorios_manual` existe pero hoy sólo bloquea el módulo entero.
- **Recomendación A — plantillas del equipo:** biblioteca de mensajes de apoyo configurable desde Hub (categorías: medicación, hidratación, respiración, descanso, terapia, etc.) + plantillas de recordatorios reutilizables. La tabla local `mensajes_biblioteca` ya existe ([shared/db.py:189-193](shared/db.py)) pero está vacía y sin sync — extender con scope global + por paciente. `perm_recordatorios_manual` pasa a significar *"el paciente puede crear recordatorios propios además de los del equipo"*.
- **Recomendación B — autostart Windows fuera del módulo:** el setting *"abrir con Windows"* hoy vive dentro del módulo Avisos ([avisos_qt.py:13](app/modules/avisos_qt.py) opciones + [avisos_daemon.py:320-352](app/avisos_daemon.py) `_get_autostart`/`_set_autostart`). **Sugerencia 2026-05-21: moverlo al Home de Suite como opción general** (junto con Modo privacidad y Tema), porque no es propio de Avisos sino global de la app. F3 mueve la UI; daemon sigue leyendo el mismo registry HKCU.
- **Estado:** **Implementado en código con daemon `pystray`+`winotify` — NO verificado en ejecución** (notificaciones del SO, autostart Windows, bandeja del sistema requieren runtime real).
- **Problemas:** `mensajes_biblioteca` creada pero sin uso visible. Categorización keywords fija. Autostart en módulo equivocado (debería ser global).
- **Riesgo feedback:** Medio-Alto (interpretación Propuesta Base no cumplida).
- **Mejora:** editor mensajes apoyo + plantillas recordatorios + autostart al Home (F2 plantillas equipo + F3 autostart-to-Home)

### 4.B Utilidades actuales para profesionales

#### Dashboard ([hub/main_qt.py:171-389](hub/main_qt.py))
- **Archivo:** `DashboardView`
- **Objetivo:** panorama clínico de pacientes
- **Flujo de uso:** abrir Hub → click "Dashboard" en sidebar → ver featured card + grid de pacientes
- **Valor:** orientación inicial
- **Consume:** `patients` Supabase + `mood_records` agregados
- **Modifica:** nada
- **Envía a Suite:** nada
- **Impacto Suite:** ninguno
- **Config remota disponible:** ninguna (es read-only)
- **Config remota faltante:** **toda la card de tags** (Adherencia alta, Riesgo bajo, Agenda al día — decisión 7 prohíbe semáforos)
- **Estado:** **Implementado en código — NO verificado en ejecución**, **pero con tags clínicamente problemáticos**.
- **Problemas:** tags hardcoded con semántica clínica subjetiva ("Adherencia alta", "Riesgo bajo", "Agenda al día") que el profesional puede interpretar como interpretación clínica del paciente. En visual QA el timeline está embebido pero en prod no.
- **Riesgo feedback:** 🔴 **CRÍTICO** (decisión 7 — contradice directamente "sin semáforos clínicos ni etiquetas tipo riesgo/crítico" — bloqueante de aprobación clínica).
- **Acción inmediata F0.1:** **eliminar tags 'Adherencia alta/Riesgo bajo/Agenda al día'** del featured card en `DashboardView`. Reemplazar por información **neutral descriptiva** según decisión 7, ejemplos:
  - "Último registro: hace 2 días"
  - "Tareas asignadas: 3 activas"
  - "Próxima sesión: viernes 14:00"
  - "Recordatorios activos: 5"
  Cambio específico en [hub/main_qt.py:171-389](hub/main_qt.py) (zona de `_featured_card_for_patient` o equivalente). Estimado: 1 día.
- **Mejora post-F0:** reusar Panel de actividad reciente neutral (Parte 8 B1) como nueva estructura de la card.

#### Pacientes ([hub/main_qt.py:400-557](hub/main_qt.py))
- **Archivo:** `PacientesView`
- **Objetivo:** listar y filtrar pacientes vinculados
- **Flujo:** sidebar → "Pacientes" → buscar/filtrar → click paciente → DetallePacienteView
- **Valor:** alta
- **Consume:** `patients`
- **Modifica:** nada
- **Envía:** nada
- **Config remota faltante:** crear paciente, desactivar, editar perfil
- **Estado:** **Implementado en código (Incompleto: botón Nuevo sin handler) — NO verificado en ejecución**.
- **Problemas:** filtro/tab "Atención" usa criterio `adherence<40%` — **decisión 7** lo prohíbe (ausencia de uso ≠ baja adherencia terapéutica, puede generar interpretaciones erróneas). Botón "+ Nuevo paciente" no tiene handler conectado ([hub/main_qt.py:453-455](hub/main_qt.py)).
- **Riesgo feedback:** 🔴 **CRÍTICO** (decisión 7).
- **Acción inmediata F0.1:** **quitar tab filtro "Atención"** (criterio interpretativo `adherence<40%`) o **renombrarlo a "Sin sincronización reciente"** usando criterio neutral (ej: "más de 7 días sin sync", "más de 14 días sin registro"). Esto es un dato descriptivo del estado del sync, no una interpretación clínica del paciente. Cambio en [hub/main_qt.py:400-557](hub/main_qt.py) (zona de definición de pill filters). Estimado: 0.5 día.
- **Mejora F4:** handler + gestión completa de pacientes (crear/desactivar/editar perfil) + nueva sub-tab "Configuración individual" (patrón 9.4.A).

#### Detalle Paciente — Tab Registros ([hub/pacientes_qt.py:237-449](hub/pacientes_qt.py))
- **Archivo:** `_TabRegistros`
- **Objetivo:** ver evolución longitudinal
- **Flujo:** click paciente → tab Registros → "↻ Cargar datos" → ver gráfico + tabla
- **Valor:** **muy alta** — es el visualizador profesional
- **Consume:** 6 tablas Supabase
- **Modifica:** nada
- **Envía:** nada
- **Estado:** **Implementado en código (UI premium con pyqtgraph spline) — NO verificado en ejecución** (gráfico pyqtgraph requiere runtime + scipy opcional para spline; SELECT 6 tablas Supabase verificable sólo con backend real)
- **Problemas:** rangos de fecha hardcoded (últimos 15-30 registros), no comparación período vs período
- **Riesgo feedback:** Bajo
- **Mejora:** F2.x — filtros de rango + comparativas individuales (NO multi-paciente comparativo)

#### Detalle Paciente — Tab Asignar ([hub/pacientes_qt.py:454-561](hub/pacientes_qt.py))
- **Archivo:** `_TabAsignar`
- **Objetivo:** asignar tareas + recordatorios individuales
- **Valor:** alta
- **Consume:** nada
- **Modifica:** `assigned_tasks`, `assigned_reminders`
- **Envía a Suite:** tareas/recordatorios (sync)
- **Estado:** **Implementado en código — NO verificado en ejecución** (INSERT a Supabase verificable sólo con backend real)
- **Problemas:** `dias` recordatorio hardcoded "1,2,3,4,5,6,7" (línea 554)
- **Mejora:** selección de días + plantillas reutilizables

#### Detalle Paciente — Tab Banco ([hub/pacientes_qt.py:566-781](hub/pacientes_qt.py))
- **Archivo:** `_TabBanco`
- **Objetivo:** CRUD banco actividades + IA autocomplete
- **Valor:** alta
- **Consume:** `activity_bank`
- **Modifica:** `activity_bank` (INSERT, DELETE)
- **Envía a Suite:** actividades (sync `_importar_actividades`)
- **Estado:** **Implementado en código (caso de éxito de configurabilidad remota — única vista con CRUD remoto completo y disclaimer IA) — NO verificado en ejecución** (CRUD `activity_bank` + IA autocomplete requieren backend + endpoint IA reales)
- **Problemas:** combo ánimo 1-4/4-7/7-10 hardcoded
- **Mejora:** rangos editables

#### Detalle Paciente — Tab IA ([hub/pacientes_qt.py:786-1023](hub/pacientes_qt.py))
- **Archivo:** `_TabIA`
- **Objetivo:** análisis IA con contexto del paciente (resumen, sugerencias, tarea)
- **Valor:** alta
- **Consume:** `_DatosRef.cache` (datos cargados en Tab Registros)
- **Modifica:** nada (no persiste)
- **Envía:** nada
- **Estado:** **Implementado en código (3 funciones IA: resumir, sugerir, generar tarea) — NO verificado en ejecución — sin audit log** (limitación conocida por lectura — outputs no persisten, sin trazabilidad clínica)
- **Problemas:** outputs efímeros, sin trazabilidad
- **Riesgo:** **Alto** (compliance)
- **Mejora:** F4 — `ia_audit_log` + persistencia

#### IA Asistente global ([hub/main_qt.py:712-911](hub/main_qt.py))
- **Archivo:** `IAAssistantView`
- **Objetivo:** chat libre con IA + contexto paciente seleccionado
- **Valor:** alta
- **Estado:** **Implementado en código — NO verificado en ejecución — chat NO persiste** (limitación conocida por lectura; cada sesión empieza vacía)
- **Mejora:** F4 — `ia_chat_history`

#### Config ([hub/main_qt.py:562-707](hub/main_qt.py))
- **Archivo:** `ConfigView`
- **Estado:** Read-only excepto tema y sync
- **Riesgo:** **Muy Alto** (decisión 3 + Parte 5)
- **Mejora:** F2 — ConfigView editable/configurable con 2 niveles (global + por paciente)

#### Exportación PDF clínica ([hub/exportar.py:23-150](hub/exportar.py))
- **Estado:** **Implementado en código (plantilla hardcoded) — NO verificado en ejecución** (ReportLab generación + apertura PDF en SO requieren runtime).
- Mejora: constructor de informes con secciones seleccionables (F2)

#### Exportación constancia legal ([hub/exportar.py:175-254](hub/exportar.py))
- **Estado:** **Implementado en código — NO verificado en ejecución**. **No editable desde UI (decisión 5).** Mantener.

### 4.C Utilidades técnicas / internas

| Nombre | Archivo | Para qué sirve | Quién la usa | Vigente | Vieja | Duplicada | Mantener/Fusionar/Eliminar | Riesgo si se deja |
|---|---|---|---|---|---|---|---|---|
| `sync` | [shared/sync.py](shared/sync.py) | Sync bidireccional Supabase | Suite (auto en bg) + Hub (botón) | ✓ | — | — | Mantener + extender en F2 | — |
| `db` | [shared/db.py](shared/db.py) | SQLite local + migraciones | Suite | ✓ | — | — | Mantener + agregar tablas cache | — |
| `identidad` | [shared/identidad.py](shared/identidad.py) | PBKDF2 hash + patient_id | Suite + Instalador | ✓ | — | — | Mantener (clave para F3 Modo privacidad) | — |
| `config` | [shared/config.py](shared/config.py) | Lectura .env 5 candidatos | Suite + Hub + instaladores | ✓ | — | — | Mantener | — |
| `crash_log` | [shared/crash_log.py](shared/crash_log.py) | Logging excepciones a AppData | Suite + Hub | ✓ | — | — | Mantener + considerar remoto en F6 | — |
| `theme` | [shared/theme.py](shared/theme.py) | Tokens V3 + paletas | todo | ✓ | — | — | Mantener | — |
| `theme_qt` | [shared/theme_qt.py](shared/theme_qt.py) | Qt helpers + fonts loader | todo | ✓ | — | — | Mantener | — |
| `components_qt` | [shared/components_qt.py](shared/components_qt.py) | 54+ widgets V3 | todo | ✓ | — | — | Mantener (referencia para nuevos editores) | — |
| `icons_svg` | [shared/icons_svg.py](shared/icons_svg.py) | 65 iconos SVG | todo | ✓ | — | — | Mantener | — |
| `installer_common` | [shared/installer_common.py](shared/installer_common.py) | InstallerShell base + QSS | 4 instaladores | ✓ | — | — | Mantener (reusar para wizard config remota) | — |
| `visual_qa` | [shared/visual_qa.py](shared/visual_qa.py) | Fixtures demo para QA visual | Suite + Hub si NM_VISUAL_QA=1 | ✓ | — | — | Mantener (útil para capturas y demos) | — |
| `utils` | [shared/utils.py](shared/utils.py) | fecha_hoy, hora_actual, color_por_puntaje | todo | ✓ | — | parcial (`_GRAD_PUNTAJE` también vive en `animo_qt.py` como `COLORES_PUNTAJE`) | Mantener, deduplicar gradientes | Bajo |
| `motor_activacion` | [app/motor_activacion.py](app/motor_activacion.py) | Sugerir actividades por ánimo + fallback | `actividades_qt` | ✓ | — | — | Mantener | — |
| `avisos_daemon` | [app/avisos_daemon.py](app/avisos_daemon.py) | Daemon hilo + bandeja + autostart | Suite (auto) | ✓ | — | — | Mantener (clave para herramienta 2) | — |
| `ia_asistente` | [hub/ia_asistente.py](hub/ia_asistente.py) | Multiproveedor IA + fallback | Hub | ✓ | — | — | Mantener + audit log F4 | — |
| `exportar` | [hub/exportar.py](hub/exportar.py) | PDF clínico + constancia legal | Hub | ✓ | — | — | Mantener + extender F2 | — |
| `home_qt` | [app/home_qt.py](app/home_qt.py) | Home Suite con sidebar + grid | Suite | ✓ | — | — | Mantener + F1 mini-visualizador | — |
| `main_qt` (Suite) | [app/main_qt.py](app/main_qt.py) | Entry point + nav + daemon + sync bg | Suite | ✓ | — | — | Mantener + F3 modo privacidad lock screen | — |
| `main_qt` (Hub) | [hub/main_qt.py](hub/main_qt.py) | Entry point Hub + 4 vistas | Hub | ✓ | — | — | Mantener + F2/F4 | — |
| `pacientes_qt` | [hub/pacientes_qt.py](hub/pacientes_qt.py) | Detalle paciente + 4 tabs | Hub | ✓ | — | — | Mantener + extender tabs (F2 plantillas, F4 audit) | — |
| `mensajes_biblioteca` | (SQLite) | Tabla creada sin uso | nadie | — | sí | — | **Eliminar o usar** — actualmente código muerto | Bajo |
| `activacion_perfil` | (SQLite) | Tabla creada sin uso visible | nadie | — | sí | — | Investigar antes de eliminar | Bajo |
| `checklist_plantillas` | (SQLite) | Plantillas locales rutina | sin lectura UI hoy | — | sí | — | **Usar en F2** o eliminar | Medio |
| `timer_presets` | (SQLite) | Presets timer | sin lectura UI hoy | — | sí | — | **Usar en F2** o eliminar | Medio |
| `edit_script.py` | [edit_script.py](edit_script.py) | One-shot patch de `components_qt.py` (a11y + breakpoints) | manual | — | sí (ya aplicado) | — | **Mover a AI_SCRIPTS/legacy/ o eliminar** | Bajo |
| `edit_script_avisos.py` | [edit_script_avisos.py](edit_script_avisos.py) | One-shot patch `avisos_qt.py` (tamaños + a11y) | manual | — | sí (ya aplicado) | — | **Mover o eliminar** | Bajo |
| `unificar.py` | [unificar.py](unificar.py) | Dump completo del repo a `neuromood_completo.txt` para IA | manual | ✓ (útil) | — | — | **Mover a AI_SCRIPTS/** como `dump_repo_for_ai.py` | Bajo (regla raíz limpia) |
| `BUILDER_NUEVO_RAPIDO.bat` | raíz | Build modo external (con payload.zip) | manual | ✓ | — | parcial | Consolidar en `BUILD_NEUROMOOD.bat` (que no existe) | Bajo |
| `BUILDER_VIEJO_LENTO.bat` | raíz | Build modo bundle (con `--clean-all --clean`) | manual | ✓ | — | parcial | Consolidar | Bajo |
| `build_neuromood.py` raíz (20KB) | [build_neuromood.py](build_neuromood.py) | Build oficial actualizado | bats raíz | ✓ | — | sí | **Es el vigente.** El de `AI_SCRIPTS/` (14KB) está desactualizado | Medio (confusión) |
| `build_neuromood.py` `AI_SCRIPTS/` (14KB) | [AI_SCRIPTS/build_neuromood.py](AI_SCRIPTS/build_neuromood.py) | Build viejo | nadie | — | sí | sí | **Eliminar o redirigir a raíz** | Medio |
| `BUILD_NEUROMOOD.bat` raíz | (NO EXISTE) | Mencionado en docs | — | — | — | — | **Crear consolidado** o actualizar docs | Medio |
| `PLAN_REDISEÑO_FUENTE_DE_LA_VERDAD.txt` | raíz | Plan rediseño viejo | manual | — | sí | — | **Mover a AI_SCRIPTS/notes/ o eliminar** | Bajo |
| `descripcion y manuales desactualizados.txt` | raíz | Doc legacy | nadie | — | sí | — | **Eliminar** (existe PDF generado) | Bajo |
| `build.log` raíz | (artefacto) | Log último build | — | artefacto | — | — | Agregar a `.gitignore` si no está | Bajo |
| `__pycache__/` raíz | (artefacto) | Cache Python | — | artefacto | — | — | Agregar a `.gitignore` | Bajo |
| `REDESIGN/` (123 archivos en `D`) | git status | Capturas y mockups legacy pre-V3 | nadie | — | sí | — | **Confirmar delete + commit** (decisión consciente del usuario) | Bajo |

---

## PARTE 5 — Matriz de configurabilidad remota desde Hub

> **Esta es la sección más crítica del informe.** Cubre los 25+ elementos del prompt maestro (líneas 100-127 y 456-481). Cada fila representa **un elemento configurable** que el equipo clínico podría querer modificar sin abrir código.

**Leyenda:**
- ✓ = sí
- ✗ = no
- ~ = parcial
- ⛔ = explícitamente descartado por decisión de producto 2026-05-20
- 🔴 = prioridad alta (bloquea aprobación clínica realista)
- 🟡 = prioridad media (mejora UX/iteración)
- 🟢 = prioridad baja (premium/diferencial)

### Matriz

| Elemento configurable | Existe hoy en código | Se configura desde Hub | Se sincroniza a Suite | Requiere SQLite | Requiere Supabase | Requiere tabla nueva | Riesgo hardcode actual | Prioridad | Recomendación técnica |
|---|---|---|---|---|---|---|---|---|---|
| **🔝 PATRÓN GENERAL 2 NIVELES (meta-elemento)** — base de TODA configurabilidad remota del Hub: scope `global` (todo el equipo) + scope `patient_id:<id>` (override individual) | ✗ hoy (no existe `hub_config` ni util) | ✗ | ✗ (no hay sync de config) | sí (cache local) | sí | `hub_config` (única tabla, JSONB, columnas: `scope`, `key`, `value`, `updated_at`, `updated_by`, `version`) + util `shared/remote_config.py` | **Crítico** | 🔴 **F2.0** | Esta es la fila madre — habilita todas las demás. Sin este patrón cada feature de Parte 5 necesita su propia tabla y reinventa la rueda. Ver subsección 9.4.A. |
| **Textos visibles Home Suite** (greeting, "TUS MÓDULOS", "BIENESTAR HOY", brand mark) | hardcoded [home_qt.py:160-265](app/home_qt.py) | ✗ | ✗ | sí (cache) | sí | `hub_text_overrides` o claves dentro de `hub_config` | Alto | 🔴 | `t(key, default)` util + tabla con scope global/patient_id |
| **Nombres visibles módulos** (Ánimo, Respiración, etc.) | hardcoded [main_qt.py:65-72](app/main_qt.py) + [home_qt.py:69-84](app/home_qt.py) `MODULES_CONFIG` | ✗ | ✗ | sí (cache) | sí | `hub_module_meta` (campo `display_name`) | Alto | 🔴 | Mismo patrón override |
| **Descripciones cortas módulos** ("Registro emocional diario") | hardcoded `MODULES_CONFIG[i]["desc"]` | ✗ | ✗ | sí | sí | mismo `hub_module_meta` | Alto | 🔴 | Mismo |
| **Chips de categoría módulos** ("Bienestar", "Calma") | hardcoded `MODULES_CONFIG[i]["chip"]` | ✗ | ✗ | sí | sí | mismo | Medio | 🟡 | Mismo |
| **Orden módulos** | hardcoded `MODULES_CONFIG` orden | ✗ | ✗ | sí | sí | `hub_module_meta.orden` | Medio | 🟡 | Campo `orden` en tabla |
| **Módulos habilitados/deshabilitados por paciente** | 4 perms en `patients` DB | ~ (DB sí, UI no) | ✓ (sync_importar_permisos) | ✓ (config k/v) | ✓ | extender `patients` con perm por cada módulo (no sólo 4) | Bajo (UI faltante) | 🔴 | UI Hub en Detalle Paciente — sección "Módulos activos" |
| **Textos de cards / títulos** (eyebrows "ÚLTIMOS 7 DÍAS", "PROGRESO DEL DÍA", etc.) | hardcoded en cada módulo | ✗ | ✗ | sí | sí | `hub_text_overrides` | Alto | 🔴 | Mismo patrón override |
| **Textos de botones** ("Guardar registro", "+ Nuevo aviso", "Hice esto", "No pude") | hardcoded en módulos | ✗ | ✗ | sí | sí | `hub_text_overrides` | Alto | 🔴 | Mismo |
| **Preguntas formulario TCC** (4 pasos hardcoded) | [registro_tcc_qt.py:526-658](app/modules/registro_tcc_qt.py) | ✗ | ✗ | sí | sí | `tcc_templates` (steps, prompts, hints, validation_required) | **Muy Alto** | 🔴 | Editor dedicado en Hub (Parte 8) |
| **Opciones emociones grid 4×2** | hardcoded `_EMOTIONS_GRID` [registro_tcc_qt.py:111-121](app/modules/registro_tcc_qt.py) | ✗ | ✗ | sí | sí | parte de `tcc_templates` | **Muy Alto** | 🔴 | Mismo |
| **Distorsiones cognitivas + keywords** | hardcoded `_KWORDS` + `_DISTORTION_CATEGORY` [registro_tcc_qt.py:79-103](app/modules/registro_tcc_qt.py) | ✗ | ✗ | sí | sí | `tcc_distortions` (lista + keywords + categoria + icon) | **Muy Alto** | 🔴 | CRUD desde Hub |
| **Tip terapéutico TCC** | hardcoded [registro_tcc_qt.py:631-634](app/modules/registro_tcc_qt.py) | ✗ | ✗ | sí | sí | parte de `tcc_templates` | Alto | 🔴 | Editor con preview |
| **Frases de apoyo post-registro** (toasts "Ánimo X registrado") | hardcoded | ✗ | ✗ | sí | sí | `support_messages` por categoría | Medio | 🟡 | Editor biblioteca |
| **Etiquetas semánticas ánimo** (no existe explícitas — sólo numérico 1-10 + emojis hardcoded) | parcial [animo_qt.py:75-79](app/modules/animo_qt.py) `COLORES_PUNTAJE` | ✗ | ✗ | sí | sí | `hub_config_global.mood_labels` JSON | Medio | 🟡 | Slot custom etiquetas 1-10 |
| **Mensajes recordatorios** (categorías hardcoded medic/agua/respir/etc.) | [avisos_qt.py:79-102](app/modules/avisos_qt.py) | ✗ | ✗ | sí (`mensajes_biblioteca` existe) | sí | `support_messages` (categoria, mensaje, target_module) | Medio | 🟡 | CRUD biblioteca |
| **Horarios sugeridos recordatorios** | hardcoded en `assigned_reminders` con `dias="1,2,3,4,5,6,7"` | ~ (sólo individual) | ✓ (sync) | ✓ | ✓ | extender `assigned_reminders` (ya existe) | Bajo | 🟡 | Selector días en Tab Asignar |
| **Actividades terapéuticas (banco)** | existe | ✓ ✓ | ✓ | ✓ | ✓ (existe) | — | Bajo | ✓ implementado | Mantener |
| **Actividades personalizadas por paciente** | existe en `patient_activities` | ~ (vía Supabase directo, no UI) | ✓ | ✓ | ✓ (existe) | — | Bajo | 🟡 | UI Hub para CRUD individuales |
| **Categorías actividades** | hardcoded `CATEGORY_COLORS` + `_CATEGORY_ORDER` | ✗ | ✗ | sí | sí | `activity_categories` (nombre, icon, color, orden) | Medio | 🟡 | Editor categorías |
| **Rangos de ánimo para sugerencias** | hardcoded combo 1-4/4-7/7-10 [pacientes_qt.py:607](hub/pacientes_qt.py) | ✗ | n/a (cálculo Hub) | ✗ | n/a (Hub UI sólo) | — | Bajo | 🟡 | Inputs numéricos |
| **Plantillas de rutinas** | tabla local `checklist_plantillas` sin contraparte remota | ✗ | ✗ | ✓ (existe) | sí | `routine_templates` (nombre, secciones, items) | Medio | 🔴 | Editor con drag-drop |
| **Asignación de plantilla rutina a paciente** | n/a (no existe concepto plantilla remota) | ✗ | ✗ | ✓ | sí | `patient_routine_template` (patient_id, template_id) | Medio | 🔴 | Asignar plantilla en Detalle |
| **Presets timer** (Propuesta Base item 3: actividades terapéuticas delimitadas por el equipo) | `timer_presets` local sin remoto | ✗ | ✗ | ✓ (existe) | sí | `timer_presets_remote` (scope global + patient_id) | **Alto** (NO cumple interpretación Propuesta Base) | 🔴 **F2.2** | Editor presets + override `perm_temporizador_manual` para permitir custom |
| **Presets respiración (técnica + fases + duraciones)** | hardcoded `FASES` + `PRESETS` [respiracion_qt.py:82-93](app/modules/respiracion_qt.py) | ✗ | ✗ | sí (cache nueva) | sí | `breathing_presets_remote` (tecnica, fase_in, fase_hold, fase_out, presets_min) | Medio-Alto | 🔴 | Editor con preview animado |
| **Instrucciones respiración** ("Inhala ↑", "Mantén", "Exhala ↓") | hardcoded `FASES` | ✗ | ✗ | sí | sí | parte de `breathing_presets_remote` | Medio | 🟡 | Mismo |
| **Contenido educativo** (hoy no existe) | — | ✗ | ✗ | sí | sí | `educational_content` (titulo, body, target_module) | Bajo | 🟢 | Si se decide agregar módulo educativo |
| **Disclaimers / textos legales visibles** | hardcoded `LEGAL_DISCLAIMER_TEXT` [installer.py:61-81](installers/installer.py) | ⛔ (decisión 5) | ✗ | ✗ | ✗ | — | Bajo | ⛔ | **NO editable desde UI.** Versionado en código + `legal_consents`. |
| **Consentimiento legal visible** | hardcoded versionado | ⛔ (decisión 5) | ✗ | ✗ | ✗ | — | Bajo | ⛔ | Mantener actual |
| **Exportaciones (secciones del PDF)** | hardcoded [exportar.py:89-127](hub/exportar.py) | ✗ | n/a | ✗ | n/a (Hub UI) | — | Medio | 🟡 | Constructor de informes |
| **Plantillas informes** | n/a | ✗ | n/a | ✗ | sí (opcional) | `report_templates` | Bajo | 🟢 | F2.x |
| **Configuración global (textos por defecto, módulos por defecto, plantillas TCC por defecto)** | n/a | ✗ | ✓ (vía override scope=global) | ✓ cache | ✓ | `hub_config_global` con scope | Alto | 🔴 | Mismo `hub_config` con campo scope |
| **Configuración por paciente (override)** | n/a (excepto permisos en `patients.perm_*`) | ✗ | ✓ (override scope=patient_id) | ✓ cache | ✓ | mismo `hub_config_global` con scope=patient_id o tabla `hub_config_patient` | Alto | 🔴 | Mismo |
| **Configuración por profesional / equipo** | n/a | ✗ | n/a (no llega a Suite) | ✗ | sí | `team_config` | Bajo | 🟢 | Para multi-equipo, no MVP |
| **Configuración por grupo/cohorte** | n/a | ⛔ (decisión 7 parcial — no semáforos) | ✗ | ✗ | sí | `patient_groups` + `group_config` | Bajo | 🟢 | NO MVP — riesgo de derivar en adherencia poblacional |
| **Prompts IA del Hub** | hardcoded [ia_asistente.py:291-387](hub/ia_asistente.py) | ⛔ (decisión 6) | n/a | ✗ | ✗ | — | Bajo | ⛔ | **Versionados en código.** Cambios vía PR + bump versión. |
| **Idioma IA / Suite** | "español rioplatense" hardcoded [ia_asistente.py:75](hub/ia_asistente.py) | ✗ | ~ (afecta sólo Hub IA) | ✗ | sí | `hub_config_global.ia_idioma` + cache | Bajo | 🟢 | Slot config |
| **Modelo IA / proveedor** | scoring automático | ✗ | n/a | ✗ | sí (opcional) | `hub_config_global.ia_provider_preference` | Bajo | 🟡 | Override desde Config |
| **Auditoría de outputs IA** | n/a (no persiste) | n/a | n/a | ✗ | ✓ | `ia_audit_log` | n/a | 🔴 | F4 |
| **Persistencia chat IA** | n/a | n/a | n/a | ✗ | ✓ | `ia_chat_history` | n/a | 🟡 | F4 |
| **Bandeja indicaciones profesional → paciente (decisión 8)** | n/a | ✗ | ✓ | ✓ cache | ✓ | `professional_messages` (id, patient_id, profesional, mensaje, sent_at, read_at, minimized_at) | n/a | 🔴 | F4 — UI Hub + UI Suite (card minimizable) |
| **Gestión de pacientes (crear/desactivar)** | n/a (handler faltante) | ✗ | ✗ | ✗ | extender `patients` con `activo`, `creado_por`, `notas_profesional` | Bajo | 🔴 | F4 |
| **Modo privacidad paciente (PIN/pwd al abrir)** | infraestructura PBKDF2 lista | ✗ (no se setea desde Hub) | ✗ | ✓ `config.privacy_pin_hash` | ✗ (es local) | — | n/a | 🟡 | F3 — UI en Suite settings |

### Resumen de configurabilidad

- **De los ~30 elementos clínicamente sensibles, hoy solo 3 son configurables:** banco de actividades, tareas individuales, recordatorios individuales.
- **27 elementos** quedan hardcoded en código Python. Para cambiar uno se requiere PR + build + redistribución de EXEs.
- **3 elementos quedan explícitamente NO configurables desde UI** (decisión consciente): disclaimers, prompts IA, consentimientos. Esto es correcto y debe mantenerse.

### Arquitectura concreta propuesta para configurabilidad remota

**Pieza 1 — Tablas Supabase nuevas a crear (DDL idempotente con `CREATE TABLE IF NOT EXISTS`):**

```sql
-- 1. Configuración key-value con 2 niveles (global + por paciente)
CREATE TABLE IF NOT EXISTS hub_config (
    id BIGSERIAL PRIMARY KEY,
    scope TEXT NOT NULL DEFAULT 'global',  -- 'global' | 'patient:<patient_id>'
    key TEXT NOT NULL,
    value JSONB NOT NULL,
    content_version_id BIGINT,
    updated_at TIMESTAMPTZ DEFAULT now(),
    updated_by TEXT,
    UNIQUE (scope, key)
);
CREATE INDEX IF NOT EXISTS hub_config_scope_idx ON hub_config (scope);

-- 2. Overrides de textos visibles UI
CREATE TABLE IF NOT EXISTS hub_text_overrides (
    id BIGSERIAL PRIMARY KEY,
    scope TEXT NOT NULL DEFAULT 'global',
    text_key TEXT NOT NULL,                -- 'home.greeting', 'animo.eyebrow_7days', etc.
    value TEXT NOT NULL,
    max_length INTEGER DEFAULT 200,
    content_version_id BIGINT,
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (scope, text_key)
);

-- 3. Visibilidad de módulos por paciente
CREATE TABLE IF NOT EXISTS module_visibility (
    id BIGSERIAL PRIMARY KEY,
    patient_id TEXT NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    module_id TEXT NOT NULL,               -- 'animo'|'respiracion'|'registro'|'rutina'|'actividades'|'timer'|'avisos'
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    orden INTEGER,
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (patient_id, module_id)
);

-- 4. Plantillas TCC
CREATE TABLE IF NOT EXISTS tcc_templates (
    id BIGSERIAL PRIMARY KEY,
    scope TEXT NOT NULL DEFAULT 'global',
    nombre TEXT NOT NULL,                  -- 'estándar', 'depresión', 'ansiedad'
    steps JSONB NOT NULL,                  -- [{name, prompt, hint, required}, ...]
    emotions JSONB NOT NULL,               -- [{label, icon, color_token}, ...]
    distortions JSONB NOT NULL,            -- [{name, keywords:[], category, icon}, ...]
    tip_text TEXT,
    success_message TEXT,
    content_version_id BIGINT,
    activa BOOLEAN DEFAULT TRUE,
    UNIQUE (scope, nombre)
);

-- 5. Plantillas de rutinas
CREATE TABLE IF NOT EXISTS routine_templates (
    id BIGSERIAL PRIMARY KEY,
    scope TEXT NOT NULL DEFAULT 'global',
    nombre TEXT NOT NULL,                  -- 'depresión leve', 'post-TEC semana 1'
    sections JSONB NOT NULL,               -- [{key, label, icon, items:[]}, ...]
    activa BOOLEAN DEFAULT TRUE
);
CREATE TABLE IF NOT EXISTS patient_routine_template (
    patient_id TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
    template_id BIGINT REFERENCES routine_templates(id) ON DELETE CASCADE,
    PRIMARY KEY (patient_id, template_id)
);

-- 6. Presets respiración y timer remotos
CREATE TABLE IF NOT EXISTS breathing_presets_remote (
    id BIGSERIAL PRIMARY KEY,
    scope TEXT NOT NULL DEFAULT 'global',
    nombre TEXT NOT NULL,                  -- '4-7-8', '5-5-5 box', 'coherencia 6-6'
    fases JSONB NOT NULL,                  -- [{label, segundos}]
    presets_min JSONB NOT NULL,            -- [3, 5, 10]
    activa BOOLEAN DEFAULT TRUE
);
CREATE TABLE IF NOT EXISTS timer_presets_remote (
    id BIGSERIAL PRIMARY KEY,
    scope TEXT NOT NULL DEFAULT 'global',
    nombre TEXT NOT NULL,
    duracion_seg INTEGER NOT NULL,
    categoria TEXT,
    orden INTEGER DEFAULT 0,
    activa BOOLEAN DEFAULT TRUE
);

-- 7. Mensajes de apoyo / biblioteca
CREATE TABLE IF NOT EXISTS support_messages (
    id BIGSERIAL PRIMARY KEY,
    scope TEXT NOT NULL DEFAULT 'global',
    categoria TEXT NOT NULL,               -- 'medicacion', 'hidratacion', 'respiracion', 'animo_alto', 'animo_bajo'
    mensaje TEXT NOT NULL,
    target_module TEXT,                    -- opcional: 'avisos', 'animo', etc.
    activa BOOLEAN DEFAULT TRUE
);

-- 8. Indicaciones del profesional al paciente (card minimizable, decisión 8)
CREATE TABLE IF NOT EXISTS professional_messages (
    id BIGSERIAL PRIMARY KEY,
    patient_id TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
    profesional TEXT,
    mensaje TEXT NOT NULL,
    sent_at TIMESTAMPTZ DEFAULT now(),
    read_at TIMESTAMPTZ,
    minimized_at TIMESTAMPTZ,
    activa BOOLEAN DEFAULT TRUE
);

-- 9. Versionado de contenido
CREATE TABLE IF NOT EXISTS content_versions (
    id BIGSERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    record_id BIGINT,
    snapshot JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    created_by TEXT,
    note TEXT
);

-- 10. Auditoría IA (decisión 6)
CREATE TABLE IF NOT EXISTS ia_audit_log (
    id BIGSERIAL PRIMARY KEY,
    patient_id TEXT,
    profesional TEXT,
    function_name TEXT NOT NULL,           -- 'resumir_evolucion' | 'sugerir_acciones' | etc.
    provider TEXT,                         -- 'Groq', 'Gemini', ...
    model TEXT,
    prompt_sistema TEXT NOT NULL,
    prompt_user TEXT NOT NULL,
    output TEXT,
    tokens_in INTEGER,
    tokens_out INTEGER,
    duracion_ms INTEGER,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ia_audit_patient_idx ON ia_audit_log (patient_id, created_at DESC);

-- 11. Persistencia chat IA (decisión 6 — solo log, no edición)
CREATE TABLE IF NOT EXISTS ia_chat_history (
    id BIGSERIAL PRIMARY KEY,
    profesional TEXT,
    patient_id TEXT,
    role TEXT NOT NULL,                    -- 'user' | 'assistant'
    content TEXT NOT NULL,
    provider TEXT,
    model TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 12. Auditoría de cambios profesionales (qué tocó quién y cuándo)
CREATE TABLE IF NOT EXISTS professional_audit (
    id BIGSERIAL PRIMARY KEY,
    profesional TEXT NOT NULL,
    accion TEXT NOT NULL,                  -- 'update_text', 'add_tcc_template', etc.
    table_name TEXT,
    record_id BIGINT,
    before_value JSONB,
    after_value JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Deshabilitar RLS en las nuevas (mismo modelo actual de tablas clínicas)
ALTER TABLE hub_config              DISABLE ROW LEVEL SECURITY;
ALTER TABLE hub_text_overrides      DISABLE ROW LEVEL SECURITY;
ALTER TABLE module_visibility       DISABLE ROW LEVEL SECURITY;
ALTER TABLE tcc_templates           DISABLE ROW LEVEL SECURITY;
ALTER TABLE routine_templates       DISABLE ROW LEVEL SECURITY;
ALTER TABLE patient_routine_template DISABLE ROW LEVEL SECURITY;
ALTER TABLE breathing_presets_remote DISABLE ROW LEVEL SECURITY;
ALTER TABLE timer_presets_remote    DISABLE ROW LEVEL SECURITY;
ALTER TABLE support_messages        DISABLE ROW LEVEL SECURITY;
ALTER TABLE professional_messages   DISABLE ROW LEVEL SECURITY;
ALTER TABLE content_versions        DISABLE ROW LEVEL SECURITY;
ALTER TABLE ia_audit_log            DISABLE ROW LEVEL SECURITY;
ALTER TABLE ia_chat_history         DISABLE ROW LEVEL SECURITY;
ALTER TABLE professional_audit      DISABLE ROW LEVEL SECURITY;
```

**Pieza 2 — Tablas SQLite locales nuevas (cache + offline fallback):**

```sql
-- En shared/db.py:inicializar_tablas() agregar:
CREATE TABLE IF NOT EXISTS remote_config_cache (
    scope TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,   -- JSON serializado
    updated_at TEXT,
    PRIMARY KEY (scope, key)
);
CREATE TABLE IF NOT EXISTS text_overrides_cache (
    scope TEXT NOT NULL,
    text_key TEXT NOT NULL,
    value TEXT NOT NULL,
    updated_at TEXT,
    PRIMARY KEY (scope, text_key)
);
CREATE TABLE IF NOT EXISTS module_visibility_cache (
    module_id TEXT PRIMARY KEY,
    enabled INTEGER NOT NULL DEFAULT 1,
    orden INTEGER
);
```

**Pieza 3 — Lectura unificada en Suite:**

```python
# shared/remote_config.py (nuevo)
from shared.db import obtener_conexion
import json

def t(key: str, default: str = "", patient_id: str = None) -> str:
    """Lookup de texto con orden de precedencia:
       1. text_overrides_cache(scope=patient:<id>, text_key=key)
       2. text_overrides_cache(scope=global, text_key=key)
       3. default hardcoded.
    """
    conn = obtener_conexion()
    try:
        if patient_id:
            row = conn.execute(
                "SELECT value FROM text_overrides_cache WHERE scope=? AND text_key=?",
                (f"patient:{patient_id}", key)
            ).fetchone()
            if row:
                return row[0]
        row = conn.execute(
            "SELECT value FROM text_overrides_cache WHERE scope='global' AND text_key=?",
            (key,)
        ).fetchone()
        if row:
            return row[0]
        return default
    finally:
        conn.close()

def is_module_enabled(module_id: str) -> bool:
    """Override por paciente si existe, sino default True."""
    conn = obtener_conexion()
    try:
        row = conn.execute(
            "SELECT enabled FROM module_visibility_cache WHERE module_id=?",
            (module_id,)
        ).fetchone()
        return row[0] == 1 if row else True
    finally:
        conn.close()

def get_config(key: str, default=None, patient_id: str = None):
    # ...similar a t() pero devuelve JSON decoded.
```

**Pieza 4 — Extensión del sync existente:**

Reusar el patrón `_importar_*` ya probado en [shared/sync.py:189-256](shared/sync.py) y [335-391](shared/sync.py):

```python
# shared/sync.py — agregar funciones nuevas
def _importar_text_overrides(sb, patient_id: str):
    try:
        # Globales primero
        res_g = sb.table("hub_text_overrides").select("text_key,value").eq("scope", "global").execute()
        # Override por paciente después
        res_p = sb.table("hub_text_overrides").select("text_key,value").eq("scope", f"patient:{patient_id}").execute()
    except Exception:
        return
    conn = obtener_conexion()
    try:
        for r in (res_g.data or []):
            conn.execute(
                "INSERT OR REPLACE INTO text_overrides_cache(scope, text_key, value, updated_at) VALUES('global', ?, ?, datetime('now'))",
                (r["text_key"], r["value"])
            )
        for r in (res_p.data or []):
            conn.execute(
                "INSERT OR REPLACE INTO text_overrides_cache(scope, text_key, value, updated_at) VALUES(?, ?, ?, datetime('now'))",
                (f"patient:{patient_id}", r["text_key"], r["value"])
            )
        conn.commit()
    finally:
        conn.close()

def _importar_module_visibility(sb, patient_id: str):
    # similar
    pass

def _importar_tcc_template(sb, patient_id: str):
    # similar — pero JSON serializado en value
    pass

# En sync_completo() agregar las llamadas
def sync_completo(...):
    ...
    _importar_text_overrides(sb, pid)
    _importar_module_visibility(sb, pid)
    _importar_tcc_template(sb, pid)
    _importar_routine_template(sb, pid)
    _importar_breathing_presets(sb, pid)
    _importar_timer_presets(sb, pid)
    _importar_support_messages(sb, pid)
    _importar_professional_messages(sb, pid)
```

**Pieza 5 — UI Hub para editar:**

Reusar `NMSettingsSection`, `NMConfigRow`, `NMFormField`, `NMSegmentedChoice`, `NMInput`, `NMToggle` ya existentes en [shared/components_qt.py](shared/components_qt.py).

ConfigView de [hub/main_qt.py:562-707](hub/main_qt.py) cambia de read-only a tabs:
- **Tab "Equipo (global)"**: textos por defecto, plantillas TCC default, módulos por defecto activos, presets respiración/timer por defecto, biblioteca mensajes apoyo
- **Tab "Visualización Hub"**: tema, proveedor IA preferido, idioma IA
- **Tab "Seguridad y sync"**: estado conexión, log sync, regenerar anon key (con confirmación)

En `DetallePacienteView` agregar tab **"Configuración (override)"** con:
- Toggle por cada módulo (override `module_visibility`)
- Override de plantilla TCC asignada (combo de `tcc_templates`)
- Override de plantilla rutina asignada
- Override de presets respiración/timer
- Inputs de override de textos visibles (limitados a campos clínicamente sensibles)

**Pieza 6 — Fallback offline:**

- Toda función `t(key, default)` siempre tiene `default` hardcoded → la UI nunca queda en blanco si el cache vacío.
- Sync se intenta en background al abrir Suite; si falla, el cache local previo se usa.
- Si falla la primera sync (instalación recién hecha), defaults hardcoded actúan.

**Pieza 7 — Validación mínima:**

- `hub_text_overrides.value` con check de `max_length` (default 200) — evita romper layouts.
- `tcc_templates.steps` con schema JSON validable (debe tener `name` y `prompt` no vacíos).
- `breathing_presets_remote.fases` debe tener al menos 1 fase con `segundos > 0`.
- En Hub UI: preview en vivo antes de "Guardar". Botón "Restaurar default" disponible.

**Pieza 8 — Cómo evitar romper UI si falta configuración:**

- Util `t(key, default)` siempre con `default` no-vacío.
- Las pruebas `_test_visual_auto.py` ([AI_SCRIPTS/_test_visual_auto.py](AI_SCRIPTS/_test_visual_auto.py)) ya capturan PNGs de cada pantalla en dark + light — agregar variante "sin config remota" como tercer modo de captura.
- Cada texto editable tiene `max_length` declarado en la tabla — UI Hub muestra contador para evitar texto excesivo.

**Pieza 9 — Cómo evitar contenido clínico hardcoded a futuro:**

- Regla de lint manual: cualquier string literal en UI debe pasar por `t(key, default)` o quedar marcado como `# i18n-skip: motivo`.
- PR template incluye checklist "¿se agregó algún texto hardcoded sin clave en `hub_text_overrides`?"
- F2 hace migración en bloques de módulo (1 PR por módulo: animo → respiracion → registro_tcc → ...). Cada PR migra todos los textos del módulo a una sección de `hub_text_overrides` y agrega las defaults.

**Pieza 10 — Versionado y rollback:**

- Cada tabla configurable tiene `content_version_id` → cuando se edita desde Hub, se guarda snapshot en `content_versions` con `before_value` y `after_value`.
- UI Hub muestra "Historial" por entrada con rollback a versión anterior.
- `professional_audit` registra autor + timestamp.
- En caso de rollback masivo: SQL manual sobre Supabase.

**Pieza 11 — Migración hardcoded → config:**

Plan por módulo, una iteración por sprint:
1. Sprint A: `animo_qt.py` → migrar 12 textos a `hub_text_overrides` con prefijo `animo.*`
2. Sprint B: `home_qt.py` → 15 textos
3. Sprint C: `registro_tcc_qt.py` → migrar steps, emotions, distortions a `tcc_templates`; tip a `support_messages`
4. Sprint D: `respiracion_qt.py` → migrar FASES + PRESETS a `breathing_presets_remote`
5. Sprint E: `rutina_qt.py` → migrar SECCIONES + plantillas a `routine_templates`
6. Sprint F: `actividades_qt.py` → ya está, solo migrar categorías
7. Sprint G: `timer_qt.py` → migrar PRESETS a `timer_presets_remote`
8. Sprint H: `avisos_qt.py` → migrar `_categorize` keywords a config + mensajes a `support_messages`

Cada PR mantiene los defaults hardcoded como fallback. Tests visuales corren antes/después.

---

## PARTE 6 — Utilidades que faltan

Brechas entre Propuesta Base / práctica clínica real y repo actual, organizadas en 4 categorías.

### A. Faltantes críticos para cumplir Propuesta Base

**A1. Visualizador longitudinal lado paciente**
- **Herramienta original:** 7 (Visualizador Evolución Anímica)
- **Qué falta:** versión paciente del gráfico (hoy solo está en Hub Tab Registros). El paciente sólo ve mini-stats agregados.
- **Por qué importa:** la Propuesta Base lo lista como herramienta paciente explícita.
- **Obligatorio o recomendable:** obligatorio si el cliente lo pide literalmente.
- **Ubicación:** Suite, mejor como sección del Home (no módulo separado, evita 8 cards desbalanceadas).
- **Profesional debería:** habilitar/deshabilitar la sección, configurar rango (7/30 días).
- **Datos:** ya están en `termometro` local + `mood_records` remoto.
- **Tablas necesarias:** ninguna nueva (config visibility de la sección vía `hub_config`).
- **Archivos involucrados:** [app/home_qt.py](app/home_qt.py) (`_SidePanel` o nueva sección debajo del grid) + reusar `NMWaveChart` de [shared/components_qt.py](shared/components_qt.py) ya usado en `animo_qt.py:264`.
- **Complejidad:** Baja (1 día) — reusar componentes existentes.
- **Prioridad:** **Alta** (F1).
- **Validación:** capturar con `_capture_v3_screens.py` antes/después, verificar layout no se rompe a 1100×720.
- **Riesgo si no se implementa:** cliente pide "¿y el visualizador para el paciente?" → feedback negativo medio.

**A2. Gestión real de pacientes desde Hub**
- **Qué falta:** botón "+ Nuevo paciente" sin handler + sin edición de perfil + sin desactivar
- **Por qué importa:** el profesional necesita poder dar de alta a un paciente y enviarle el código de instalación sin tener que tocar Supabase manualmente.
- **Obligatorio:** sí para piloto.
- **Ubicación:** Hub `PacientesView`.
- **Datos necesarios:** patient_id generado server-side (UUID), patient_name, email opcional, install_code, profesional asignado.
- **Tablas:** extender `patients` con `activo BOOLEAN DEFAULT TRUE`, `creado_por TEXT`, `notas_profesional TEXT`.
- **Archivos:** [hub/main_qt.py:453-455](hub/main_qt.py) — agregar handler + dialog modal.
- **Complejidad:** Media (3-5 días).
- **Prioridad:** **Alta** (F4).
- **Validación:** crear paciente, verificar que el código de instalación funciona en Suite limpia.

**A3. Versión Suite del gráfico semanal con export**
- (Sub-parte de A1) — pero específicamente: capacidad de **exportar a PNG/PDF** desde la propia Suite, no solo desde Hub.
- La Propuesta original menciona "exportación a imagen o PDF" para la herramienta 7.
- **Complejidad:** Baja (reusar ReportLab + matplotlib o pyqtgraph.exporters).
- **Prioridad:** Media (F2/F3).

**A4. Timer customizado por profesional (interpretación Propuesta Base item 3)**
- **Qué falta:** el profesional no puede definir presets de timer desde Hub; el paciente elige libremente preset o custom.
- **Por qué importa:** la Propuesta Base dice *"delimitar actividades **terapéuticas** por tiempo"* — las actividades terapéuticas las **delimita el equipo**, no el paciente (no está formado para auto-prescribir tratamiento).
- **Obligatorio:** sí para piloto.
- **Ubicación:** Hub (ConfigView equipo + Detalle Paciente sub-tab Config) + Suite (`timer_qt.py` lee presets remotos).
- **Profesional debería:** definir presets (nombre, duración, categoría), asignar al paciente, opcionalmente habilitar `perm_temporizador_manual` para permitir custom.
- **Datos:** tabla `timer_presets_remote` (scope global + patient_id), reusa `timer_presets` SQLite ya creada.
- **Tablas:** `timer_presets_remote` (nueva en Supabase) o entradas en `hub_config` con `key='timer.presets'`.
- **Archivos:** [app/modules/timer_qt.py:71-76](app/modules/timer_qt.py) (presets ahora desde DB), [shared/sync.py](shared/sync.py) (importar presets), Hub editor (nuevo).
- **Complejidad:** Media (3-5 días).
- **Prioridad:** **Alta** (F2.2).
- **Validación:** crear preset desde Hub, sincronizar, verificar que aparece en Suite y reemplaza los 5/10/25/45 hardcoded.
- **Riesgo si no se implementa:** contradice interpretación Propuesta Base 3 → posible feedback negativo del equipo clínico.

**A5. Rutina con sistema híbrido de 3 estados (opción C, decisión 2026-05-21)**
- **Qué falta:** hoy el paciente puede agregar libremente tareas propias, sin distinción clínica. No hay forma de configurar por paciente si debe seguir sólo la plantilla, sólo lo propio, o mixto.
- **Por qué importa:** la Propuesta Base dice *"Lista de tareas diarias"* — implícitamente delimitadas por el equipo, pero el paciente no debe ser paternalizado completamente. Sistema 3 estados respeta gradación clínica.
- **Obligatorio:** sí para piloto.
- **Ubicación:** Hub (Detalle Paciente Tab Asignar — sección Rutina) + Suite (`rutina_qt.py` distingue origen).
- **Profesional debería:** elegir modo (`solo_profesional` / `mixto` / `solo_paciente`) al asignar/actualizar plantilla.
- **Datos:** nuevo campo `rutina_modo` ENUM en `patients`; reusa campo `origen` ya implementado en `checklist_tareas` ([shared/db.py:269](shared/db.py)); badge "Personal" en UI Suite para tareas con `origen='manual'`.
- **Tablas:** ALTER `patients` ADD COLUMN `rutina_modo TEXT DEFAULT 'mixto'` + `routine_templates` para plantillas (campo `secciones`, `tareas`).
- **Archivos:** [app/modules/rutina_qt.py](app/modules/rutina_qt.py) (lee modo del paciente, condiciona botón "+ Agregar tarea"), [hub/pacientes_qt.py:454-561](hub/pacientes_qt.py) (selector modo + editor plantillas).
- **Complejidad:** Media (5-7 días).
- **Prioridad:** **Alta** (F2.3).
- **Validación:** setear `rutina_modo=solo_profesional`, verificar que botón "+ Agregar tarea" desaparece en Suite; setear `solo_paciente`, verificar que no llegan tareas profesionales.

**A6. Eliminar lenguaje semáforo clínico del Hub (decisión 7, ahora F0.1)**
- **Qué falta:** Dashboard usa tags "Adherencia alta/Riesgo bajo/Agenda al día"; Pacientes tiene filtro "Atención" por adherencia<40%.
- **Por qué importa:** **contradice directamente la decisión 7** (sin semáforos clínicos sobre uso de app). Ausencia de uso ≠ baja adherencia terapéutica. **Bloqueante de aprobación clínica.**
- **Obligatorio:** sí — antes de piloto.
- **Ubicación:** Hub (`DashboardView`, `PacientesView`).
- **Profesional debería:** ver información neutral descriptiva (última sync, registros recientes, tareas activas, próxima sesión), no interpretaciones clínicas hardcoded.
- **Datos:** existentes (`patients`, `mood_records`, `assigned_tasks`, `assigned_reminders`). No nueva tabla.
- **Archivos:** [hub/main_qt.py:171-389](hub/main_qt.py) (DashboardView tags) + [hub/main_qt.py:400-557](hub/main_qt.py) (Pacientes filtro "Atención").
- **Complejidad:** Baja (1-2 días).
- **Prioridad:** **🔴 Crítica F0.1** (bloqueante de aprobación).
- **Validación:** grep en `hub/main_qt.py` y `hub/pacientes_qt.py` no debe encontrar "Riesgo", "Adherencia alta/baja", "Atención" como tags clínicos. Reemplazar con criterios neutrales como "Sin sincronización reciente" (basado en `last_sync_date`).
- **Riesgo si no se implementa:** cliente clínico rechaza el producto por interpretaciones automáticas no autorizadas.

### B. Faltantes importantes para práctica clínica real

**B1. Audit log IA**
- **Qué falta:** no hay registro de qué prompts se le enviaron a la IA por paciente, qué outputs dio, qué modelo se usó.
- **Por qué importa:** auditoría clínica/legal. Equipo o jurídico puede pedir trazabilidad.
- **Obligatorio:** sí para uso clínico real.
- **Ubicación:** Hub (registro en backend).
- **Profesional configura:** nada (es automático). Ve el audit log en una nueva pantalla.
- **Datos:** `ia_audit_log` (ver Parte 5).
- **Archivos:** [hub/ia_asistente.py:230-286](hub/ia_asistente.py) `_llamar()` — agregar INSERT al inicio y al final.
- **Complejidad:** Baja-Media (1-2 días).
- **Prioridad:** **Alta** (F4).

**B2. Editor de plantillas TCC**
- **Qué falta:** el equipo TCC va a querer editar las 4 preguntas, hints, emociones, distorsiones.
- **Por qué importa:** decisión 4 (descartamos IA al paciente, doblamos apuesta a plantillas configurables).
- **Obligatorio:** sí para piloto.
- **Ubicación:** Hub (sub-pantalla en Detalle Paciente o en ConfigView global).
- **Datos:** `tcc_templates` (Parte 5).
- **Complejidad:** Media-Alta (1-2 semanas).
- **Prioridad:** **Alta** (F2).

**B3. Editor de presets respiración + timer**
- **Qué falta:** equipo puede pedir 4-4-4 box breathing o 5-5-5 además del 4-7-8.
- **Datos:** `breathing_presets_remote`, `timer_presets_remote`.
- **Complejidad:** Media (1 semana).
- **Prioridad:** Media (F2).

**B4. Editor de plantillas de rutinas**
- **Qué falta:** plantillas reutilizables ("Rutina depresión leve") que se asignan a paciente.
- **Tabla local `checklist_plantillas` ya existe** ([shared/db.py:230-238](shared/db.py)) sin uso ni sync.
- **Datos:** `routine_templates` + `patient_routine_template`.
- **Complejidad:** Media (1 semana).
- **Prioridad:** Media (F2).

**B5. Editor de mensajes de apoyo / biblioteca**
- **Qué falta:** biblioteca de mensajes por categoría (medicación, hidratación, etc.).
- **Tabla local `mensajes_biblioteca` ya existe sin uso.**
- **Datos:** `support_messages`.
- **Complejidad:** Baja (3 días).
- **Prioridad:** Media (F2).

**B6. Bandeja de indicaciones profesional → paciente (decisión 8)**
- **Qué falta:** mensaje destacado en Suite que el paciente puede minimizar y marcar como leído.
- **Datos:** `professional_messages`.
- **UI Hub:** Tab Asignar agregar "Enviar indicación" + log de mensajes enviados con estado.
- **UI Suite:** Banner top o card en Home que se puede minimizar; estado leído/no leído.
- **Complejidad:** Media (1-2 semanas).
- **Prioridad:** Media (F4).

**B7. Modo privacidad del paciente (PIN/pwd al abrir Suite)** (decisión 1)
- **Qué falta:** ventana de login al abrir Suite, para PCs compartidas.
- **Infraestructura:** PBKDF2 ya está en [shared/identidad.py](shared/identidad.py).
- **Ubicación:** Suite, antes de `NeuroMoodApp._build_ui()` en [app/main_qt.py:151](app/main_qt.py).
- **Recuperación:** vía email Supabase Auth (reusa flujo del instalador).
- **Config Hub:** ✗ — es local solamente (opt-in del paciente desde settings de la Suite).
- **Complejidad:** Media (1 semana).
- **Prioridad:** Media (F3).

**B8. Panel de actividad reciente neutral por paciente (decisión 7)**
- **Qué falta:** vista del Hub con última sincronización, últimos registros, tareas completadas, recordatorios activos, métricas individuales.
- **Reemplazo:** Dashboard tags ("Adherencia alta", "Riesgo bajo") y filtro "Atención" (adherence<40).
- **Datos:** ya existen.
- **Complejidad:** Baja (3-5 días).
- **Prioridad:** Media (F4).

**B9. Persistencia chat IA**
- **Qué falta:** chat global del Hub no se guarda.
- **Datos:** `ia_chat_history`.
- **Complejidad:** Baja (2 días).
- **Prioridad:** Media (F4).

**B10. Constructor de informes paramétrico**
- **Qué falta:** poder elegir qué secciones incluir en el PDF clínico exportado.
- **Datos:** [hub/exportar.py](hub/exportar.py) hoy hardcodea 6 secciones.
- **Complejidad:** Baja-Media (3-5 días).
- **Prioridad:** Media (F2).

**B11. Exportar CSV/Excel además de PDF**
- **Qué falta:** investigadores o el equipo NeuroMood pueden pedir datos crudos.
- **Complejidad:** Baja (2-3 días).
- **Prioridad:** Media-Baja (F2).

**B12. Worklist de revisión (paciente marca registros para compartir)**
- **Qué falta:** el paciente puede marcar un registro TCC o de ánimo como "quiero compartir con mi terapeuta". El Hub muestra una worklist.
- **Datos:** agregar campo `flagged_for_review BOOLEAN` a `mood_records` y `thought_records`.
- **Complejidad:** Media (1 semana).
- **Prioridad:** Media (F4).

### C. Faltantes de configurabilidad para evitar refactors futuros

Toda la matriz de Parte 5 que no esté ya en categoría A/B. Resumen del grupo:
- **C1.** `hub_text_overrides` para todos los textos visibles
- **C2.** `module_visibility` por paciente con UI Hub
- **C3.** `hub_config` global + por paciente para configuración no-textual (idioma IA, etc.)
- **C4.** `content_versions` + `professional_audit` para versionado
- **C5.** `t(key, default)` util en shared
- **C6.** Migración progresiva de textos hardcoded a config (Sprint A-H de Parte 5)

### D. Faltantes premium / diferenciales

**D1. Onboarding interactivo paciente (5 min, primera sesión)**
- Tour guiado por cada módulo, una vez. Reusa `NMTCCStepper`.
- Prioridad: Baja (F8).

**D2. Modo accesibilidad**
- Tamaños tipográficos +1 nivel, alto contraste. Token `TYPOGRAPHY` ya tiene tamaños.
- Prioridad: Baja (F8).

**D3. Plan semanal recibido del profesional (calendario en Suite)**
- View calendario que muestra `assigned_tasks` con `fecha_programada` (nuevo campo).
- Prioridad: Baja (F8 o post-piloto).

**D4. Backup local cifrado**
- Exportar registros del paciente en JSON cifrado para portabilidad/backup.
- Prioridad: Baja (post-piloto).

**D5. Exportación masiva multi-paciente**
- Para análisis externo del equipo, CSV agregado.
- Prioridad: Baja.

**D6. Vista cohorte/grupo (sin semáforos, descriptivo)**
- Agrupar pacientes por programa. **NO MVP** (riesgo de derivar en adherencia poblacional, decisión 7).
- Prioridad: Baja (post-validación piloto).

---

## PARTE 7 — Ideas nuevas para pacientes

Clasificadas A/B/C/D según el prompt maestro. **Las 4 ideas descartadas del 2026-05-20 quedan listadas al final con motivo, para trazabilidad.**

### Categoría A — Must-have para terminar el producto

#### A1. Mini-visualizador semanal en Home Suite

- **Problema real que resuelve:** completa la 7ma herramienta de la Propuesta Base lado paciente. Hoy el paciente sólo ve el último puntaje + mini-stats agregados; sin gráfico longitudinal.
- **Relación Propuesta Base:** herramienta 7 (Visualizador de Evolución Anímica).
- **Usuario objetivo:** paciente.
- **Flujo:** abre Suite → en Home, debajo del grid de módulos, ve un mini-chart de los últimos 7 días con su ánimo. Click en chart → abre módulo Ánimo con vista expandida.
- **Pantalla / módulo:** modifica `home_qt.py`. No es módulo nuevo: es mejora de existente.
- **Datos locales:** `termometro`.
- **Datos sync:** ya sincroniza (`mood_records`).
- **Vista Hub:** ya existe (Tab Registros).
- **Config Hub:** habilitar/deshabilitar la sección (default ON), rango (7/14/30 días).
- **Textos editables:** "ÚLTIMOS 7 DÍAS" header → `hub_text_overrides`.
- **Riesgo clínico/legal:** muy bajo (es visualización descriptiva, no diagnóstico).
- **Cómo mantenerlo seguro:** sólo muestra datos del paciente, no comparaciones con cohorte.
- **Complejidad técnica:** Baja.
- **Prioridad:** Alta.
- **Archivos:** [app/home_qt.py](app/home_qt.py) (probablemente nueva sección debajo del grid) + reusar `NMWaveChart` de [shared/components_qt.py](shared/components_qt.py).
- **Validación mínima:** capturar Home con `_capture_v3_screens.py`, verificar layout no se rompe; abrir con 0 / 1 / 7 registros.
- **Riesgo si no se implementa:** Alto — cliente puede pedir la herramienta 7 explícitamente lado paciente.

#### A2. Modo privacidad del paciente (decisión 1)

- **Problema real:** Suite contiene info muy privada (registros TCC, ánimo bajo, notas personales). Para pacientes que comparten computadora (familia/pareja), no hay protección contra que otros vean.
- **Relación Propuesta Base:** no estaba originalmente, pero refuerza "el paciente tiene una experiencia clara, segura y útil" (objetivo del producto).
- **Usuario objetivo:** paciente.
- **Flujo:** primera apertura tras instalar Suite → "¿Querés activar un PIN/contraseña al abrir?" (opt-in con explicación). Si activa: setea PIN (4-8 dígitos o pwd). Próxima apertura → pantalla de login antes de Home. 3 intentos fallidos → bloqueo 5 min + opción recuperar vía email Supabase Auth.
- **Pantalla:** nueva ventana modal antes de `NeuroMoodApp._build_ui()` en [app/main_qt.py:151](app/main_qt.py).
- **Datos locales:** `config.privacy_pin_hash` (PBKDF2 reusando [shared/identidad.py:9-13](shared/identidad.py)), `config.privacy_enabled`, `config.privacy_recovery_email`.
- **Datos sync:** ✗ (es local — no enviar PIN a Supabase).
- **Vista Hub:** ✗ (es del paciente, no del profesional).
- **Config Hub:** no se setea desde Hub. Es opt-in del paciente.
- **Textos editables:** mensajes de la pantalla de login → `hub_text_overrides`.
- **Riesgo clínico/legal:** bajo. **Importante:** si el paciente olvida PIN y no tiene email recovery → debe poder reinstalar conservando datos (ya soporta esto el desinstalador).
- **Cómo mantenerlo seguro:** PBKDF2 100k iters ya implementado. Salt único por instalación (`install_code`).
- **Complejidad:** Media.
- **Prioridad:** Alta.
- **Archivos:** [app/main_qt.py](app/main_qt.py) + nuevo `app/privacy_lock_qt.py` + extender [shared/identidad.py](shared/identidad.py).
- **Validación:** crear PIN, salir, reabrir, verificar bloqueo. Probar recuperación.
- **Riesgo si no se implementa:** Medio (pacientes en PC compartidas pueden no usar la app por miedo a privacidad).

#### A3. Bandeja de indicaciones del profesional (decisión 8 ajustada)

- **Problema real:** el profesional necesita poder dejar indicaciones específicas al paciente entre sesiones ("esta semana enfocate en respiración", "anotá pensamientos antes de dormir"). Hoy se hace verbalmente o por email externo.
- **Relación Propuesta Base:** refuerza "apoyo terapéutico configurable".
- **Usuario objetivo:** paciente recibe; profesional envía.
- **Flujo paciente:** abre Suite → si hay indicación nueva, banner top destacado (no card sobre el contenido). Click → expande texto completo + botón "Marcar como leída" + botón "Minimizar". Minimizada queda visible como chip discreto. Marca leída → desaparece del top, queda en histórico accesible.
- **Flujo profesional:** Detalle Paciente → Tab Asignar → nueva card "Enviar indicación al paciente" con textarea (max 500 chars).
- **Pantalla:** Suite Home (banner top) + Tab Asignar Hub.
- **Datos locales:** `professional_messages_cache` (espejo de remoto).
- **Datos sync:** `professional_messages` (Parte 5).
- **Vista Hub:** Tab Asignar + log "Mensajes enviados" con estado leído/no leído.
- **Config Hub:** habilitar/deshabilitar feature por paciente. Texto del banner default.
- **Textos editables:** "Indicación de tu profesional" → `hub_text_overrides`.
- **Riesgo clínico/legal:** **medio**. El profesional NO debe enviar mensajes de crisis ("estoy preocupado por vos") por este canal — debe ser para contenido orientativo. UI Hub debe tener un disclaimer al lado del input.
- **Cómo mantenerlo seguro:** disclaimer + límite de longitud + no automatización (cada envío manual).
- **Complejidad:** Media-Alta (UI bidireccional + sync + estado).
- **Prioridad:** Alta.
- **Archivos:** [app/home_qt.py](app/home_qt.py) + nuevo widget banner + [hub/pacientes_qt.py](hub/pacientes_qt.py) extender `_TabAsignar`.
- **Validación:** profesional envía → paciente abre Suite → ve banner → minimiza → reabre app → minimizado correcto → expande → marca leído → estado actualiza en Hub.
- **Riesgo si no se implementa:** Medio (continúa la dependencia de email/WhatsApp externos).

### Categoría B — Muy recomendable

#### B1. Plantillas TCC configurables (refuerzo decisión 4)

- **Problema real:** sin IA al paciente, el valor agregado de TCC viene de **mejor diseño de los formularios** por el equipo clínico.
- **Relación Propuesta Base:** refuerza herramienta 4.
- **Usuario:** paciente (recibe plantilla del equipo).
- **Flujo paciente:** abre Registro TCC → el formulario refleja la plantilla activa (puede ser distinta a la default). Profesional puede haber asignado plantilla "ansiedad" vs "depresión" según paciente.
- **Datos locales:** `tcc_templates_cache`.
- **Datos sync:** `tcc_templates` (Parte 5).
- **Vista Hub:** Editor en Detalle Paciente (ver Parte 8).
- **Config Hub:** completa.
- **Textos editables:** todos (4 steps, 8 emotions, 10 distortions, tip).
- **Riesgo clínico:** medio (si el equipo edita mal, puede empeorar UX). Mitigar con preview en vivo + rollback + validation schema.
- **Complejidad:** Alta (depende de Parte 5 + Editor Hub).
- **Prioridad:** Media.
- **Archivos:** [app/modules/registro_tcc_qt.py](app/modules/registro_tcc_qt.py) (cambiar wizard para leer config) + [hub/pacientes_qt.py](hub/pacientes_qt.py) (nueva sub-pantalla).
- **Validación:** crear plantilla custom, asignar a paciente, verificar Suite refleja cambios al sincronizar.
- **Riesgo si no se implementa:** Alto (Parte 4 lo marca como #1 en feedback negativo del cliente).

#### B2. Onboarding interactivo de 5 min

- **Problema:** paciente nuevo abre Suite y no sabe qué hacer.
- **Flujo:** primera apertura tras login → tour guiado (reusa `NMTCCStepper`) por los 7 módulos, 1 pantalla por módulo, 30s c/u.
- **Datos locales:** `config.onboarding_completed = 1`.
- **Sync:** ✗.
- **Vista Hub:** ✗.
- **Config Hub:** habilitar/deshabilitar + textos del tour.
- **Riesgo clínico:** bajo.
- **Complejidad:** Media.
- **Prioridad:** Media (F8).
- **Archivos:** nuevo `app/onboarding_qt.py`.
- **Validación:** primera apertura muestra tour, segunda no.
- **Riesgo si no se implementa:** Medio (paciente abandona si no entiende).

#### B3. Termómetro emocional con etiquetas semánticas configurables

- **Problema:** hoy 1-10 es solo numérico + emojis. El equipo puede preferir "Muy mal / Mal / Neutral / Bien / Muy bien" o "0=peor que nunca, 10=mejor que nunca".
- **Flujo:** paciente ve el slider con etiqueta semántica debajo del número.
- **Config Hub:** array de 10 etiquetas en `hub_config_global.mood_labels`.
- **Complejidad:** Baja.
- **Prioridad:** Media.
- **Archivos:** [app/modules/animo_qt.py](app/modules/animo_qt.py) + sync.
- **Validación:** cambiar etiquetas desde Hub, verificar Suite refleja.

#### B4. Resumen semanal del paciente (no diagnóstico)

- **Problema:** el paciente abre la app y no ve si avanzó.
- **Flujo:** sección en Home con "Esta semana: X días con registro, Y tareas completadas, Z sesiones de respiración". Sin etiquetas tipo "mejorando/empeorando".
- **Config Hub:** habilitar/deshabilitar.
- **Riesgo:** **bajo** sólo si se mantienen métricas descriptivas, no interpretativas.
- **Complejidad:** Baja.
- **Prioridad:** Media.

#### B5. Modo silencioso de notificaciones

- **Problema:** hoy `silencio_inicio/fin` se setea en `avisos_qt` con dos NMInput. Mejorable: 3 modos quick (Día / Trabajo / Sueño) preset configurables.
- **Datos:** extiende `config` k/v existente.
- **Config Hub:** presets de silencio.
- **Complejidad:** Baja.
- **Prioridad:** Media.

### Categoría C — Premium / diferencial

#### C1. Modo accesibilidad (alto contraste + tamaño tipografía +1)

- **Problema:** pacientes mayores o con discapacidad visual.
- **Config:** toggle local en Settings Suite.
- **Complejidad:** Media (tokens ya están).
- **Prioridad:** Baja.

#### C2. Personalización paleta por equipo

- **Problema:** clínicas distintas pueden querer branding distinto (no MVP — riesgo distrae del foco clínico).
- **Config Hub:** `hub_config_global.palette` JSON.
- **Complejidad:** Media.
- **Prioridad:** Baja.

#### C3. Exportar registros propios en PDF/JSON

- **Problema:** paciente puede querer compartir con otro profesional fuera de NeuroMood.
- **Flujo:** botón "Exportar mis datos" en Settings Suite → PDF resumido + JSON crudo.
- **Riesgo:** **medio** — si el JSON incluye PII y se filtra. Mitigar: PDF sí, JSON cifrado opcional.
- **Complejidad:** Media.
- **Prioridad:** Baja.

### Categoría D — Futuro, no ahora

#### D1. Plan semanal calendario (recibe `assigned_tasks` con `fecha_programada`)

- Vista calendario en Suite con las tareas asignadas distribuidas por día.
- Requiere nuevo campo `fecha_programada` en `assigned_tasks`.
- Complejidad: Media-Alta.
- Prioridad: Baja.

#### D2. Backup local cifrado

- Botón "Exportar backup" → archivo cifrado AES con la pwd del paciente.
- Para portabilidad entre máquinas.
- Complejidad: Media.
- Prioridad: Baja.

#### D3. Sincronización iCal / Google Calendar

- Para que las tareas asignadas aparezcan en el calendario del paciente.
- Requiere OAuth → potencial conflicto con decisión "no Google OAuth" del instalador (aunque ahí es para login, no para cal).
- Prioridad: Baja, requiere revisión clínica/legal antes.

### Ideas descartadas (con motivo, decisión 2026-05-20)

| Idea descartada | Motivo |
|---|---|
| ❌ **Modo bajo ánimo automático** (Home con UI simplificada al detectar ánimo<4) | Decisión 3: sin lógica automática basada en umbrales emocionales. Reemplazado por configurabilidad remota en 2 niveles (Parte 5). |
| ❌ **Asistente IA de redacción TCC para paciente** | Decisión 4: ética terapéutica + riesgo de reencuadres inadecuados. Reemplazado por plantillas TCC configurables (B1). |
| ❌ **Diario de respuesta a tratamiento TEC/ketamina** | Decisión 2: fuera de scope inicial + sensibilidad clínica/legal alta + riesgo feedback negativo cliente. |
| ❌ **Modo familiar/cuidador (segundo perfil)** | Decisión 1: descartado por complejidad de roles. Reemplazado por "Modo privacidad del paciente" (A2). |

---

## PARTE 8 — Ideas nuevas para profesionales

Clasificadas A/B/C/D. Las descartadas de la decisión 2026-05-20 quedan al final.

### Categoría A — Must-have para terminar el producto

#### A1. Panel de configuración remota Suite (global + por paciente)

- **Problema profesional:** hoy no puede cambiar nada desde Hub. ConfigView es read-only. La única superficie configurable es banco de actividades + asignar tareas/recordatorios individuales.
- **Relación Propuesta Base:** desbloquea cumplimiento del **requisito fundamental** del prompt maestro: "el cliente y el equipo profesional tienen formación clínica universitaria… deben configurar remotamente desde el Hub todo lo posible".
- **Flujo:** sidebar Hub → Config (ahora con tabs). Tab "Equipo (global)" = configuración por defecto para todos los pacientes. Tab "Visualización Hub" = tema, IA preferida, idioma. Tab "Seguridad y sync" = ya parecido al actual. + en `DetallePacienteView` agregar Tab "Configuración (override)" para tocar un paciente puntual.
- **Datos necesarios:** todas las tablas de Parte 5.
- **Datos mostrados:** los valores actuales + historial de cambios + autor + fecha.
- **Envío a Suite:** automático vía sync.
- **Config en Suite:** mínima — la Suite respeta lo que reciba.
- **Textos editables:** prácticamente todos los visibles del producto.
- **Cambios Supabase:** 12 tablas nuevas (Parte 5).
- **Cambios SQLite:** 3 tablas cache + extender `config`.
- **Cambios visuales:** Hub `ConfigView` nuevo + Tab "Configuración" en Detalle Paciente.
- **Usa IA:** no.
- **Cómo evitar riesgo clínico/legal:** validaciones de schema, preview en vivo, rollback, `professional_audit`.
- **Complejidad:** Alta (es un sub-proyecto en sí mismo, F2 entero).
- **Prioridad:** **Alta** — bloquea aprobación clínica.
- **Archivos:** [hub/main_qt.py:562-707](hub/main_qt.py), [hub/pacientes_qt.py](hub/pacientes_qt.py), nuevo `hub/config_editors/`, [shared/sync.py](shared/sync.py), [shared/db.py](shared/db.py), nuevo `shared/remote_config.py`, módulos Suite (extracción de strings a `t(key, default)`).
- **Validación mínima:** editar texto "TUS MÓDULOS" desde Hub → forzar sync en Suite → verificar texto actualizado en Home.
- **Riesgo si no se implementa:** **Muy alto** — cliente va a pedir cambios constantes a código → costo de mantenimiento explota.

#### A2. Editor de plantillas TCC

- **Problema profesional:** equipo TCC tiene preferencias específicas (preguntas, hints, distorsiones).
- **Flujo:** Detalle Paciente → "Configuración (override)" → "Plantilla TCC". Combo de plantillas globales ("estándar" / "ansiedad" / "depresión") + botón "Crear plantilla custom". Editor con preview en vivo del wizard Suite.
- **Datos:** `tcc_templates` (Parte 5).
- **Envío a Suite:** sync.
- **Config Suite:** lee plantilla activa.
- **Textos editables:** 4 steps (name + prompt + hint), 8 emotions (label + icon + color), 10 distortions (name + keywords + category), tip text, success message.
- **Cambios Supabase:** sí.
- **Cambios SQLite:** sí (cache).
- **Visuales:** nuevo editor con drag-drop reorder + preview embebido.
- **IA:** opcional para autocomplete de keywords ("¿qué keywords detectarían 'minimización'?")
- **Riesgo:** medio — validar schema JSON antes de guardar.
- **Complejidad:** Alta (es un mini-editor visual).
- **Prioridad:** Alta (F2).
- **Archivos:** nuevo `hub/editors/tcc_template_editor.py` + [app/modules/registro_tcc_qt.py](app/modules/registro_tcc_qt.py) (refactor a lectura de config).
- **Validación:** crear template "ansiedad" con 3 steps en lugar de 4, asignar a paciente, ver Suite refleja.
- **Riesgo si no se implementa:** **Alto** (Parte 4 lo marca como #1).

#### A3. Editor de rutinas semanales (plantillas)

- **Problema:** crear "Rutina depresión leve" + "Rutina post-TEC" + asignar a paciente.
- **Flujo:** Configuración → "Plantillas Rutina" → editor drag-drop por sección (Mañana/Tarde/Noche) con CRUD items.
- **Datos:** `routine_templates` + `patient_routine_template`.
- **Tabla local `checklist_plantillas` ya existe** — solo falta conectarla.
- **Complejidad:** Media-Alta.
- **Prioridad:** Alta (F2).
- **Validación:** crear plantilla, asignar, paciente abre Rutina y ve las tareas pre-cargadas.

#### A4. Editor de mensajes de apoyo (biblioteca)

- **Problema:** mensajes contextuales por categoría (medicación, hidratación, respiración).
- **Datos:** `support_messages` (Parte 5) + tabla local existente `mensajes_biblioteca`.
- **Flujo:** Configuración → "Biblioteca mensajes" → CRUD por categoría.
- **Complejidad:** Baja-Media.
- **Prioridad:** Media-Alta (F2).

#### A5. Editor de presets respiración + timer

- **Problema:** equipo puede pedir 4-4-4 box breathing, 5-5-5, coherencia cardíaca 6-6.
- **Datos:** `breathing_presets_remote`, `timer_presets_remote`. Tabla `timer_presets` local existe.
- **Flujo:** Configuración → "Presets respiración" + "Presets timer" → CRUD.
- **Complejidad:** Media (especialmente preview animado de respiración).
- **Prioridad:** Media (F2).

#### A6. Gestión real de pacientes desde Hub

- **Problema:** hoy "+ Nuevo paciente" sin handler. Para piloto se necesita poder crear/desactivar/editar.
- **Flujo:** click "+ Nuevo paciente" → dialog modal (nombre + email opcional + notas). Server genera `patient_id` UUID + `install_code`. El profesional envía el install_code al paciente (out-of-band, email/WhatsApp).
- **Datos:** extender `patients` con `activo`, `creado_por`, `notas_profesional`.
- **Complejidad:** Media.
- **Prioridad:** Alta (F4).
- **Archivos:** [hub/main_qt.py:453-455](hub/main_qt.py) + nuevo dialog.

#### A7. Editor de plantillas de rutina + selector de modo por paciente (opción C, decisión 2026-05-21)

- **Problema:** hoy no hay forma de definir plantillas de rutina semanales desde Hub ni de elegir cómo el paciente puede usarlas. La Propuesta Base 6 dice *"Lista de tareas diarias"* — implícitamente delimitadas por el equipo, pero el paciente no debe ser paternalizado.
- **Relación Propuesta Base:** refuerza herramienta 6.
- **Flujo profesional:**
  1. Hub Tab Asignar → sección Rutina → "Crear plantilla" → editor drag-drop con 3 secciones (Mañana/Tarde/Noche) + items.
  2. "Asignar plantilla a paciente" → seleccionar paciente → **elegir modo** (`solo_profesional` / `mixto` (default) / `solo_paciente`).
  3. Guardar → sync → Suite del paciente recibe plantilla y respeta modo.
- **Flujo paciente:** en `rutina_modo='solo_profesional'` el botón "+ Agregar tarea" desaparece; en `'mixto'` está visible y las propias salen con badge "Personal"; en `'solo_paciente'` no llega plantilla del profesional.
- **Datos necesarios:** `routine_templates` (id, nombre, secciones JSONB con tareas), `patient_routine_template` (patient_id, template_id, modo), nuevo campo `rutina_modo` en `patients`.
- **Cambios Supabase:** sí — 2 tablas nuevas + 1 ALTER.
- **Cambios SQLite:** menor — cache. La tabla `checklist_plantillas` ya existe ([shared/db.py:230-238](shared/db.py)).
- **Cambios visuales:** sí — editor en Hub + badge "Personal" en Suite.
- **Sin IA:** no aplica.
- **Riesgo clínico:** Bajo (es organización de tareas, no decisión terapéutica). Mitigación: profesional siempre puede ver tareas propias del paciente.
- **Complejidad:** Media (5-7 días).
- **Prioridad:** **Alta** (F2.3).
- **Archivos involucrados:**
  - [app/modules/rutina_qt.py](app/modules/rutina_qt.py): leer `rutina_modo` del config local + ocultar botón "+ Agregar tarea" si `solo_profesional`.
  - [shared/sync.py](shared/sync.py): nuevo `_importar_routine_template(patient_id)` y `_importar_rutina_modo(patient_id)`.
  - [hub/pacientes_qt.py:454-561](hub/pacientes_qt.py) `_TabAsignar`: nuevo card "Plantilla de rutina" con drag-drop + selector modo.
- **Validación:**
  - Setear `rutina_modo=solo_profesional` desde Hub → cerrar/abrir Suite → verificar que botón "+ Agregar tarea" desaparece.
  - Setear `rutina_modo=solo_paciente` → verificar que no llegan tareas profesionales nuevas (las viejas siguen marcadas).
  - Crear tarea propia en modo `mixto` → verificar badge "Personal" y `origen='manual'` en DB local.
- **Riesgo de feedback si no se implementa:** Alto. La Propuesta Base es ambigua aquí y el cliente puede pedir cualquiera de los 3 modos; sin opción C el equipo queda restringido.

#### A8. Panel de Settings Generales en Home de Suite (2026-05-21)

- **Problema:** hoy el setting "abrir con Windows" vive dentro del módulo Avisos ([avisos_qt.py:13](app/modules/avisos_qt.py) Card de opciones + [avisos_daemon.py:320-352](app/avisos_daemon.py) `_get_autostart`/`_set_autostart`), aunque es un setting global de la app. Modo privacidad del paciente (decisión 1) y switch de tema dark/light también necesitan UI clara y centralizada.
- **Relación Propuesta Base:** indirecta (mejora UX general).
- **Flujo:** Home Suite → ícono ⚙ → panel `_SettingsPanel` con secciones:
  - **Inicio con Windows:** toggle ON/OFF (usa `_get_autostart`/`_set_autostart` existentes).
  - **Modo privacidad:** toggle "Pedir contraseña al abrir Suite" + setear/cambiar PIN (usa PBKDF2 existente en [shared/identidad.py:5-13](shared/identidad.py)). Decisión 1.
  - **Apariencia:** switch dark/light (ya existe lógica, sólo mover UI).
- **Idea profesional:** el profesional puede **forzar Modo privacidad activado** desde Hub (vía `hub_config` con `key='suite.require_privacy_lock'`, scope=patient_id) — útil para pacientes en entorno compartido.
- **Datos:** local en `config` k/v ([shared/db.py:325-341](shared/db.py)). Hash del PIN en `config.privacy_pin_hash`.
- **Cambios Supabase:** nada (settings son locales) **excepto** el toggle de "forzar privacy_lock" desde Hub (scope `hub_config`).
- **Cambios SQLite:** nada (reusa `config`).
- **Cambios visuales:** nueva pantalla `_SettingsPanel` en Home Suite + ícono ⚙ en header.
- **Sin IA:** no aplica.
- **Riesgo clínico/legal:** Bajo (es UX de la app). Validar que olvido de PIN tiene flujo de recovery vía email Supabase Auth (reusa flujo del instalador).
- **Complejidad:** Media (3-4 días — incluye lock screen).
- **Prioridad:** **Alta** (F3).
- **Archivos involucrados:**
  - Nuevo: `app/settings_panel_qt.py` (o `app/home_qt.py:_SettingsPanel`).
  - Nuevo: `app/privacy_lock_qt.py` (lock screen).
  - Modificar: [app/avisos_qt.py](app/modules/avisos_qt.py) (eliminar card de autostart, dejar shim de compatibilidad).
  - Modificar: [app/home_qt.py](app/home_qt.py) (agregar ícono ⚙ + integrar `_SettingsPanel`).
  - Modificar: [app/main_qt.py:139-142](app/main_qt.py) (al inicio: si `privacy_lock=on`, mostrar `privacy_lock_qt` antes de Home).
- **Validación:** activar PIN, cerrar Suite, reabrir, verificar lock screen, fallar 3 veces, esperar 5 min, recuperar vía email.

### Categoría B — Muy recomendable

#### B1. Panel de actividad reciente por paciente (decisión 7)

- **Problema:** reemplazar tags "Adherencia alta / Riesgo bajo / Agenda al día" del Dashboard (decisión 7 prohíbe semáforos clínicos).
- **Flujo:** Dashboard → en lugar de tags → "Actividad reciente: última sync hace 2h, 3 registros últimos 7d, 1 tarea completada hoy, 2 recordatorios activos". Click → expande a Tab Registros del paciente.
- **Datos:** ya existen.
- **Sin etiquetas tipo "atención", "riesgo", "crítico".**
- **Complejidad:** Baja-Media.
- **Prioridad:** Media-Alta (F4).
- **Validación:** abrir Dashboard, ver panel neutral, no ver tags clínicos.

#### B2. Visualizador longitudinal individual mejorado

- **Problema:** Tab Registros ya tiene gráfico pero con rangos fijos. Equipo puede querer comparar mes vs mes.
- **Flujo:** Tab Registros → selector de rango (7/14/30/60 días) + botón "Comparar con período anterior".
- **NO multi-paciente comparativo** (decisión 7).
- **Datos:** queries Supabase con filtros de fecha.
- **Complejidad:** Media.
- **Prioridad:** Media (F2).

#### B3. Constructor de informes paramétrico

- **Problema:** [exportar.py](hub/exportar.py) hoy hardcodea 6 secciones.
- **Flujo:** Tab Registros → "Exportar PDF" → modal con checklist de secciones a incluir + rango de fechas + nombre archivo.
- **Datos:** misma data, sólo cambia presentación.
- **Complejidad:** Media.
- **Prioridad:** Media (F2).

#### B4. Worklist de revisión

- **Problema:** paciente marca registros TCC/ánimo como "quiero compartir con mi terapeuta".
- **Flujo paciente:** botón "Marcar para revisión" en cada registro nuevo. **Botón opt-in, no automático.**
- **Flujo profesional:** Hub sidebar → "Worklist" con todos los registros marcados de todos los pacientes, ordenados por fecha.
- **Datos:** agregar `flagged_for_review BOOLEAN DEFAULT FALSE` a `mood_records` y `thought_records`.
- **Complejidad:** Media.
- **Prioridad:** Media (F4).

#### B5. Auditoría IA (log de outputs, decisión 6)

- **Problema:** sin trazabilidad de qué hizo la IA.
- **Flujo:** sidebar Hub → "Auditoría IA" → tabla con todos los outputs IA (por paciente, función, modelo, fecha, prompt, output, duración). Filtros + export.
- **Datos:** `ia_audit_log` (Parte 5).
- **Implementación:** instrumentar `_llamar()` en [hub/ia_asistente.py:230-286](hub/ia_asistente.py).
- **NO incluye edición de prompts** (decisión 6). Solo lectura/audit.
- **Complejidad:** Baja-Media.
- **Prioridad:** Media-Alta (F4).
- **Archivos:** [hub/ia_asistente.py](hub/ia_asistente.py) + nuevo `hub/audit_qt.py`.

#### B6. Persistencia chat IA

- **Problema:** chat global del Hub no se guarda.
- **Datos:** `ia_chat_history`.
- **Flujo:** abrir IA Asistente → muestra últimos N mensajes con paciente actual (si hay) o globales.
- **Complejidad:** Baja.
- **Prioridad:** Media (F4).

#### B7. Bandeja de indicaciones enviadas (espejo Hub de A3 paciente)

- **Problema:** profesional no recuerda qué le mandó a cada paciente.
- **Flujo:** Tab Asignar → sub-card "Mensajes enviados" con log + estado leído/no leído + minimizado.
- **Datos:** `professional_messages`.
- **Complejidad:** Baja (la UI base se hace junto con A3 paciente).
- **Prioridad:** Media (F4).

#### B8. Validación de consentimiento pre-acción

- **Problema:** hoy las tabs se deshabilitan si consent no vigente, pero el botón "Exportar PDF" no chequea.
- **Flujo:** antes de cualquier acción que toque datos del paciente, verificar consent. Si no vigente, mostrar warning.
- **Complejidad:** Baja.
- **Prioridad:** Media (F5).

### Categoría C — Premium / diferencial

#### C1. Exportar CSV/Excel multi-formato

- Para análisis externo.
- Complejidad: Baja (reusar pandas o csv stdlib).
- Prioridad: Baja.

#### C2. Sub-pantalla "Mi equipo" para multi-profesional

- Para clínicas con varios terapeutas.
- Complejidad: Media.
- Prioridad: Baja.

#### C3. Tags de paciente custom (no clínicos)

- Por programa de tratamiento, sin connotación de riesgo.
- Datos: nuevo `patient_tags` con CRUD.
- Complejidad: Baja-Media.
- Prioridad: Baja.

#### C4. Búsqueda avanzada en registros TCC

- Buscar paciente por keyword en sus pensamientos automáticos (con consentimiento explícito en TOS).
- Complejidad: Media.
- Prioridad: Baja, **requiere revisión legal**.

### Categoría D — Futuro, no ahora

#### D1. Vista cohorte/grupo descriptiva

- Agrupar pacientes por programa de tratamiento.
- **NO MVP** por decisión 7 (riesgo de derivar en adherencia poblacional).
- Si se hace post-piloto: solo métricas descriptivas, sin tags tipo "riesgo".
- Complejidad: Media.
- Prioridad: Baja.

#### D2. Multi-equipo / multi-clínica

- Para escalar el producto a varias instituciones.
- Complejidad: Alta.
- Prioridad: Baja.

#### D3. Dashboard de salud del producto

- Métricas del producto en sí (no clínicas): uso, errores, latencia sync.
- Complejidad: Media.
- Prioridad: Baja.

### Ideas descartadas (con motivo, decisión 2026-05-20)

| Idea descartada | Motivo |
|---|---|
| ❌ **Panel de adherencia poblacional con semáforo (riesgo/crítico)** | Decisión 7: ausencia de uso ≠ baja adherencia terapéutica. Reemplazado por panel de actividad reciente neutral (B1). |
| ❌ **Editor de consentimiento legal versionado editable desde Hub** | Decisión 5: rompería trazabilidad legal. Consentimientos siguen versionados en código + `db/legal_consents.sql` + instalador. |
| ❌ **Reentrenamiento de prompts IA por equipo desde UI** | Decisión 6: riesgo legal + difícil de auditar. Prompts permanecen versionados en código ([hub/ia_asistente.py:291-387](hub/ia_asistente.py)). Sí se mantiene `ia_audit_log` (B5). |

---

## PARTE 9 — Arquitectura recomendada

> **Principio rector:** plan **incremental por fases**, NO reescritura. La arquitectura V3 actual es sólida; sólo se extiende.

### 9.1 Estructura de carpetas recomendada (mantener actual)

```
nm_suite/
├── app/                          # Suite paciente (Qt) — sin cambios estructurales
│   ├── main_qt.py                # Entry point + Modo privacidad (F3)
│   ├── home_qt.py                # Home + mini-visualizador (F1) + banner indicaciones (F4)
│   ├── modules/                  # 7 módulos paciente
│   ├── avisos_daemon.py
│   ├── motor_activacion.py
│   ├── onboarding_qt.py          # NUEVO F8 — tour 5 min
│   └── privacy_lock_qt.py        # NUEVO F3 — login PIN/pwd
│
├── hub/                          # Hub profesional (Qt) — extender
│   ├── main_qt.py                # 4 vistas + nueva: Worklist + Auditoría IA
│   ├── pacientes_qt.py           # 4 tabs + nueva tab Configuración (override)
│   ├── ia_asistente.py           # Sin cambios estructurales + audit log
│   ├── exportar.py               # Constructor informes (F2)
│   ├── editors/                  # NUEVO F2 — editores configurables
│   │   ├── tcc_template_editor.py
│   │   ├── routine_template_editor.py
│   │   ├── breathing_preset_editor.py
│   │   ├── timer_preset_editor.py
│   │   ├── support_messages_editor.py
│   │   └── text_overrides_editor.py
│   ├── patient_management.py     # NUEVO F4 — crear/desactivar paciente
│   └── audit_qt.py               # NUEVO F4 — Worklist + Auditoría IA
│
├── shared/                       # Compartido — extender
│   ├── theme.py / theme_qt.py    # Sin cambios
│   ├── components_qt.py          # Sin cambios estructurales (sólo bug fixes)
│   ├── db.py                     # Agregar 3 tablas cache (F2)
│   ├── sync.py                   # Extender _importar_* funciones (F2)
│   ├── identidad.py              # Sin cambios — ya soporta PBKDF2
│   ├── config.py                 # Sin cambios
│   ├── installer_common.py       # Sin cambios
│   ├── visual_qa.py              # Extender fixtures con datos config remota
│   ├── crash_log.py              # Sin cambios + opcional remote en F6
│   ├── icons_svg.py              # Sin cambios
│   ├── utils.py                  # Sin cambios
│   ├── remote_config.py          # NUEVO F2 — t(key, default), is_module_enabled, get_config
│   └── privacy_lock.py           # NUEVO F3 — wrapper de identidad para PIN
│
├── db/                           # Esquemas SQL — extender
│   ├── supabase_schema.sql       # Sin cambios + concat con nuevos
│   ├── legal_consents.sql        # Sin cambios (decisión 5)
│   ├── fix_supabase_rls.sql      # Sin cambios
│   └── hub_config_schema.sql     # NUEVO F2 — 12 tablas nuevas (Parte 5)
│
├── installers/                   # Sin cambios estructurales
│   ├── installer.py              # Sin cambios + F6 modo offline en consent (cola)
│   ├── installer_pro.py
│   ├── uninstaller.py
│   └── uninstaller_pro.py
│
├── assets/                       # Sin cambios
├── AI_SCRIPTS/                   # Consolidar
│   ├── build_neuromood.py        # ELIMINAR (duplicado del raíz)
│   ├── dump_repo_for_ai.py       # NUEVO (mover unificar.py acá)
│   ├── notes/                    # NUEVO (mover PLAN_REDISEÑO_*.txt acá)
│   ├── legacy/                   # NUEVO (mover edit_script*.py acá)
│   └── ... (resto sin cambios)
│
├── BUILD_NEUROMOOD.bat           # NUEVO consolidado (reemplaza BUILDER_*.bat)
├── build_neuromood.py            # MANTENER (es el vigente, 20KB)
├── README.md
├── AI_PROJECT_CONTEXT.md
├── AUDITORIA_NEUROMOOD.md        # ESTE archivo
└── Propuesta Base.pdf
```

### 9.2 Qué lógica vive dónde

| Capa | Responsabilidad | Archivos clave |
|---|---|---|
| **`app/`** | UI paciente + lógica de negocio paciente | `app/modules/*.py`, `app/home_qt.py`, `app/main_qt.py` |
| **`hub/`** | UI profesional + editores + IA | `hub/*.py`, `hub/editors/*.py` |
| **`shared/`** | Lógica reutilizada por Suite + Hub + instaladores | `shared/*.py` |
| **`db/`** | Esquemas SQL fuente de verdad | `db/*.sql` |
| **`installers/`** | Instaladores + desinstaladores | `installers/*.py` |
| **`AI_SCRIPTS/`** | Scripts auxiliares, QA, builds, manuales | `AI_SCRIPTS/*.py` |

### 9.3 Qué va a Supabase vs SQLite

**Supabase = fuente de verdad para:**
- Identidad paciente (`patients` con perms + `legal_consents`)
- Datos clínicos generados por paciente (6 tablas streams)
- Asignaciones del profesional (`assigned_tasks`, `assigned_reminders`)
- Banco actividades (`activity_bank`, `patient_activities`)
- **Configuración remota** (12 tablas nuevas Parte 5)
- **Audit logs** (`ia_audit_log`, `professional_audit`, `content_versions`)

**SQLite (local Suite) = cache + datos efímeros:**
- Espejo de los streams del propio paciente (para offline)
- Cache de configuración remota (`*_cache` tablas Parte 5)
- Identidad local (`config` k/v)
- `legal_consent.json` aparte de DB
- Hash PIN (`config.privacy_pin_hash`)
- Notas del día y plantillas locales que NO sincronizan

**SQLite (local Hub):** **no usa SQLite hoy**. El Hub habla directo con Supabase. Considerar cache local en F6 para offline read-only.

### 9.4 Configuración global vs por paciente

Patrón único `scope`:
- `scope = 'global'`: aplica a todos los pacientes del equipo
- `scope = 'patient:<id>'`: override individual

Precedencia en `remote_config.t(key, default, patient_id)`:
1. Override `scope='patient:<id>'` si existe
2. Override `scope='global'` si existe
3. `default` hardcoded (siempre presente)

**Sin cohorte/grupo en MVP** (decisión 7). Si en futuro se agrega, sería un nivel intermedio: `scope='group:<id>'` entre `global` y `patient:<id>`.

### 9.4.A Patrón arquitectónico general 2 niveles (decisión 2026-05-21)

La estrategia de 2 niveles **NO es una feature de un módulo específico** — es el **patrón general** que aplica a **TODA configuración del Hub**. Toda settings que el profesional pueda tocar desde Hub debe pensarse en esta estructura, no como una solución ad-hoc por módulo:

```
┌──────────────────────────────────────────────────────────────────────┐
│ Capa 1 — Configuración global del equipo (scope='global')           │
│   • Vale para todos los pacientes del equipo salvo override         │
│   • Se setea en ConfigView del Hub → sección "Configuración equipo" │
│   • Ejemplos: textos de Home Suite, plantillas TCC default,         │
│     presets timer default, biblioteca de mensajes de apoyo,         │
│     categorías de actividades, idioma del Hub.                      │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ override si existe
┌──────────────────────────────────────────────────────────────────────┐
│ Capa 2 — Configuración individual por paciente                       │
│       (scope='patient:<patient_id>')                                 │
│   • Sobrescribe valores globales SÓLO para ese paciente              │
│   • Se setea en Hub Detalle Paciente → nueva sub-tab "Configuración" │
│   • Muestra valor efectivo (global + override) y permite override    │
│     por clave. Indicador visual "Override activo" cuando aplica.     │
│   • Ejemplos: rutina_modo, presets timer asignados, plantilla TCC    │
│     asignada, módulos habilitados (perm_*), textos personalizados.   │
└──────────────────────────────────────────────────────────────────────┘
```

> **Excepciones a este patrón:** prompts IA del sistema están versionados en código (decisión 6, no editables desde UI); consentimientos legales versionados en código (decisión 5); banco de actividades ya tiene su propia tabla con FK a paciente.

> **Scope de `hub_config` — qué SÍ y qué NO va acá:**
>
> `hub_config` es **solo para settings/overrides simples** (pares key/value JSON livianos con jerarquía global → paciente).
>
> **NO va en `hub_config`:**
> - **Registros clínicos** (`mood_records`, `breathing_sessions`, `thought_records`, `checklist_completions`, `timer_sessions`, `reminder_logs`) — tablas propias por dato + FK + sync stream.
> - **Consentimientos** (`legal_consents`) — versionados por código + RLS + hash (decisión 5).
> - **Banco de actividades** (`activity_bank`, `patient_activities`) — entidades con FK a paciente, dificultad, rango ánimo, etc. Tabla propia existente.
> - **Mensajes leídos/no leídos** (indicaciones del profesional, decisión 8 ajustada) — tabla `professional_messages` con estado por mensaje, no settings.
> - **Audit log IA** (`ia_audit_log`) — registros append-only por llamada, no configuración.
> - **Reportes / artefactos generados** (PDFs, exportaciones) — no se guardan en `hub_config`.
> - **Entidades con flujo propio** (asignaciones de tareas/recordatorios, plantillas con secciones complejas tipo `tcc_templates` o `routine_templates`) — tablas dedicadas que pueden referenciarse desde `hub_config` por id, pero su contenido vive aparte.
>
> Regla simple: si es **un valor o un toggle que un paciente o el equipo cambian y se aplica al render de la UI**, va en `hub_config`. Si tiene **lifecycle propio** (historial, FK, sync direccional, append-only), va en tabla dedicada.

**Implementación recomendada (única tabla + util):**

```sql
CREATE TABLE hub_config (
  id           BIGSERIAL PRIMARY KEY,
  scope        TEXT NOT NULL,         -- 'global' o 'patient:<uuid>'
  key          TEXT NOT NULL,         -- ej: 'home.greeting', 'timer.presets'
  value        JSONB NOT NULL,        -- payload arbitrario
  updated_at   TIMESTAMPTZ DEFAULT now(),
  updated_by   UUID,                  -- auth.uid() del profesional
  version      INT  DEFAULT 1,        -- bump al cambiar (ver 9.6)
  UNIQUE (scope, key)
);
CREATE INDEX idx_hub_config_scope_key ON hub_config (scope, key);
```

**Util `shared/remote_config.py` (Suite + Hub):**

```python
def t(key, default, patient_id=None):
    """
    Lee valor configurable con jerarquía:
       patient:<id>  →  global  →  default hardcoded
    Cachea en SQLite local `remote_config_cache`. Sync online refresca.
    """
    # 1. Si patient_id, intentar scope='patient:<id>'
    # 2. Si no encuentra, intentar scope='global'
    # 3. Si no encuentra, devolver default
```

**Regla de oro:** **toda feature nueva del Hub que requiera "configurar algo en Suite" pasa por este store, NO por tablas ad-hoc.** Esto incluye todos los puntos del prompt maestro líneas 100-127 y 456-481: textos Home, nombres módulos, orden módulos, módulos enabled/disabled, presets timer/respiración, plantillas TCC, biblioteca de mensajes, etiquetas ánimo, `rutina_modo`, categorías actividades, idiomas, instrucciones, etc.

**ConfigView del Hub reestructurada en 2 secciones:**

- **Sección 1: "Configuración del equipo"** (scope=global) — editores agrupados por área. Cambios afectan a todos los pacientes salvo override individual.
- **Sección 2: "Configuración por paciente"** (scope=patient:<id>) — sub-tab dentro de Detalle Paciente. Muestra valor efectivo (global + override) por cada key. Botón "Override" → setea `scope='patient:<id>'`. Botón "Quitar override" → vuelve al global.

**Beneficio sistémico:** cualquier feature futura de configurabilidad se enchufa al mismo patrón. No hay que decidir cada vez "¿hago una tabla nueva?" — la respuesta es casi siempre "¿es `hub_config` suficiente?" (en el 90% de los casos sí).

### 9.5 Fallback offline

- **Suite:** siempre funciona offline. Sync se reintenta al volver online. Si nunca tuvo conexión (instalación fresh sin sync), defaults hardcoded actúan. Banner sutil "Sin conexión" si lleva >24h sin sync.
- **Hub:** hoy requiere conexión. F6 puede agregar caché local de últimos N pacientes (read-only sin conexión).

### 9.6 Versionado de contenidos configurables

- Cada tabla configurable tiene `content_version_id` BIGINT.
- Tabla `content_versions` guarda snapshots `before_value` y `after_value` con autor + fecha + nota.
- UI Hub muestra "Historial" por entrada. Rollback = INSERT del snapshot anterior como nuevo registro (no DELETE).
- **`legal_consents` ya tiene su propio versionado por hash** ([db/legal_consents.sql:13-17](db/legal_consents.sql)).

### 9.7 Migración hardcoded → configurable

Por módulo, en bloques. Ver Pieza 11 de Parte 5 (Sprints A-H).

### 9.8 Auditoría de cambios profesionales

- Tabla `professional_audit` registra cualquier escritura en tablas configurables.
- Trigger Postgres (opcional) o instrumentación manual en `hub/editors/`.
- UI: panel "Auditoría" en Hub para ver "quién cambió qué cuándo".

### 9.9 Cómo evitar romper UI al cambiar textos

- Util `t(key, default)` siempre con `default` no-vacío.
- `hub_text_overrides.max_length` (default 200) — validación en Hub.
- `_test_visual_auto.py` captura snapshots de todas las pantallas en `_qa_output/v3_capture/` — agregar variante con config remota custom.
- Editor en Hub muestra preview en vivo + contador de caracteres.

### 9.10 Plan de migración hardcoded → configurable (resumen)

| Sprint | Módulo | Strings clave a migrar | Tabla destino |
|---|---|---|---|
| A | `animo_qt.py` | 12 textos UI + COLORES_PUNTAJE | `hub_text_overrides` + `hub_config_global` |
| B | `home_qt.py` | 15 textos UI + nombres módulos | `hub_text_overrides` + `hub_module_meta` |
| C | `registro_tcc_qt.py` | steps + emotions + distortions + tip | `tcc_templates` |
| D | `respiracion_qt.py` | FASES + PRESETS | `breathing_presets_remote` |
| E | `rutina_qt.py` | SECCIONES + plantillas | `routine_templates` |
| F | `actividades_qt.py` | categorías (ya tiene banco editable) | `activity_categories` |
| G | `timer_qt.py` | PRESETS | `timer_presets_remote` |
| H | `avisos_qt.py` | categorización keywords + mensajes | `support_messages` |

**No reescribir todo de una.** Cada sprint mantiene defaults hardcoded como fallback. Tests visuales antes/después.

### 9.11 Resumen arquitectura

- **Mantener:** estructura de carpetas, V3 design system, sync bidireccional, Auth Supabase, RLS legal_consents, instaladores.
- **Extender:** sync con nuevas `_importar_*` funciones, SQLite con 3 tablas cache, Hub con editores + audit + worklist.
- **Crear:** 12 tablas Supabase nuevas, `shared/remote_config.py`, `shared/privacy_lock.py`, `hub/editors/*`, `hub/audit_qt.py`, `hub/patient_management.py`, `app/onboarding_qt.py`, `app/privacy_lock_qt.py`.
- **Eliminar / consolidar:** `AI_SCRIPTS/build_neuromood.py` (duplicado), scripts edit_*.py, BUILDER_*.bat → `BUILD_NEUROMOOD.bat`.
- **NO crear:** UI para editar consentimientos, prompts IA, ni semáforos clínicos (decisiones 5, 6, 7).

---

## PARTE 10 — Plan de QA

### 10.1 Pruebas técnicas

| Prueba | Cómo | Herramienta vigente | Frecuencia |
|---|---|---|---|
| **Imports** | `python -m compileall app hub shared installers` (ya hace `BUILDER_*.bat`) | `BUILDER_VIEJO_LENTO.bat:78` | Cada PR |
| **Smoke tests** | Validar que las 6 apps construyen sin error | [AI_SCRIPTS/smoke_test_runner.py](AI_SCRIPTS/smoke_test_runner.py) + `_runtime_smoke.py` | Cada commit a main |
| **Apertura Suite** | Lanzar `app/main_qt.py` con `NM_VISUAL_QA=1` → verificar Home carga | [AI_SCRIPTS/qa_full_suite.py](AI_SCRIPTS/qa_full_suite.py) | Cada release candidate |
| **Apertura Hub** | Lanzar `hub/main_qt.py` con QA fixtures | Mismo | RC |
| **Navegación módulos** | Abrir cada uno de los 7 módulos paciente → verificar build_ui no crashea | `_test_visual_auto.py` | RC |
| **SQLite migraciones** | Borrar `nm_data.db`, lanzar Suite, verificar `inicializar_tablas()` crea todo | manual + `_runtime_smoke.py` | Cada cambio en `shared/db.py` |
| **Supabase schema** | Aplicar `db/supabase_schema.sql` + `db/fix_supabase_rls.sql` + (futuro) `db/hub_config_schema.sql` en proyecto test | manual desde Supabase Dashboard | Cada cambio schema |
| **Sync** | Crear registro en Suite con `NM_VISUAL_QA=0` y `.env` válido → forzar sync → verificar fila en Supabase | manual + script futuro | RC + cuando se toca `sync.py` |
| **Instaladores** | Ejecutar instalador en VM Windows 10/11 limpia → verificar consent flow, archivo `.env` copiado, registro Uninstall creado | manual VM | Cada release |
| **Desinstaladores** | Instalar → desinstalar con "Conservar datos" → verificar que datos quedan + carpeta install borrada | manual VM | Cada release |
| **Modo offline** | Desconectar internet, abrir Suite, registrar ánimo, reconectar, verificar sync diferido | manual | Cada PR que toca sync |
| **Sin .env** | Borrar .env de AppData y bundle → abrir Suite → verificar mensaje claro "Sin conexión" (no crashea) | manual | Cada PR que toca `config.py` |
| **Errores de red** | Toxiproxy o flaky network → verificar reintentos IA + sync diferido | manual o automatizado | Cada PR que toca IA o sync |
| **Build Windows** | `BUILD_NEUROMOOD.bat --dry-run` (cuando exista) o `BUILDER_NUEVO_RAPIDO.bat --dry-run` | scripts existentes | Cada PR |
| **Capturas visuales** | Generar 22 PNGs (11 pantallas × dark+light) | [AI_SCRIPTS/_capture_v3_screens.py](AI_SCRIPTS/_capture_v3_screens.py) | Cada RC |
| **Test color regression** | Verificar tokens v3 vs spec | [AI_SCRIPTS/_test_color_regression.py](AI_SCRIPTS/_test_color_regression.py) | Cada PR que toca theme |
| **Resize test** | Validar layouts a 375/640/960/1280/1600px | [AI_SCRIPTS/resize_test.py](AI_SCRIPTS/resize_test.py) | RC |
| **Theme switch** | Toggle dark/light → verificar transición 350ms no rompe nada | [AI_SCRIPTS/test_theme_switch.py](AI_SCRIPTS/test_theme_switch.py) | Cada PR que toca theme |
| **PDFs generados** | Manuales + capacidad de exportar PDF clínico | [AI_SCRIPTS/generate_neuromood_manuals.py](AI_SCRIPTS/generate_neuromood_manuals.py) + Hub Tab Registros | Cada RC |

### 10.2 Pruebas de producto

| Escenario | Pasos |
|---|---|
| **Paciente nuevo onboarding** | Instalar Suite → crear cuenta → aceptar consent → instalar → abrir → registrar primer ánimo → marcar primera tarea → cerrar |
| **Paciente con datos históricos** | Verificar que tras reinstalar conservando datos, todo el histórico está intacto |
| **Profesional nuevo onboarding** | Instalar Hub → abrir → conectar a Supabase → ver 0 pacientes → (en F4) crear primer paciente desde "+ Nuevo" |
| **Profesional con N pacientes** | Buscar/filtrar, ordenar, abrir detalle, navegar tabs |
| **Profesional configura Suite (post-F2)** | Editar texto de Home → forzar sync en Suite → verificar reflejo |
| **Profesional asigna tarea/recordatorio** | Tab Asignar → completar formulario → Suite refleja al sincronizar |
| **Profesional asigna plantilla TCC (post-F2)** | Editor → crear plantilla custom → asignar a paciente → Suite muestra wizard custom |
| **Paciente recibe indicación profesional (post-F4)** | Profesional envía → Suite muestra banner → paciente minimiza → marca leída |
| **Paciente registra datos** | Cada módulo → datos persisten local + se exportan a Supabase |
| **Hub visualiza datos del paciente** | Tab Registros → Cargar datos → ver gráfico + tabla |
| **Hub exporta PDF** | Botón Exportar → PDF se abre + se guarda en Downloads |
| **Consentimiento revocado** | Cambiar `legal_consents.status='revocado'` en Supabase → Hub tabs deshabilitadas en Detalle Paciente |
| **Permisos restringen módulos** | Setear `perm_checklist_manual=False` en Supabase → forzar sync Suite → módulo Rutina disabled en Home |
| **Modo privacidad activo (post-F3)** | Setear PIN → cerrar Suite → reabrir → login screen → ingreso correcto → Home |
| **Modo privacidad olvidado** | Setear PIN → reabrir → fallar 3 veces → bloqueo 5min → recuperar vía email Supabase |
| **IA dispone / no dispone** | Con `.env` válido → IA funciona. Sin: muestra "IA no disponible momentáneamente" + reintenta en 30s |
| **IA fallback proveedor** | Setear GROQ_API_KEY incorrecto + GEMINI_API_KEY válido → debe usar Gemini |

### 10.3 Pruebas UX

| Persona / situación | Qué verificar |
|---|---|
| **Paciente con baja energía / ánimo bajo** | UI no debería ser "happy" agresivo. Verificar copy. Verificar partículas de celebración solo si ≥7 (correcto). |
| **Paciente ansioso** | Verificar que la respiración 4-7-8 funciona como debe. Verificar pausa/resume. |
| **Paciente con poca alfabetización digital** | Onboarding (F8) debe usar lenguaje claro. Botones grandes. Sin jerga clínica. |
| **Profesional con poco tiempo** | Dashboard debe dar info al vuelo. Asignar tarea ≤3 clicks. Exportar PDF ≤2 clicks. |
| **Flujo sesión clínica** | Profesional abre Hub → busca paciente por nombre → click → ve gráfico → asigna 1 tarea → cierra. Total ≤30s. |
| **Lectura de gráficos** | Verificar contraste de colores en dark + light. Verificar tooltip verificable en ejecución. |
| **Claridad de botones** | Todo botón con `accessibleName` (validado en `edit_script.py` reciente). Tooltips donde aplique. |
| **Textos configurables largos/cortos** | Probar con strings de 1 char, 200 chars, 500 chars → layout no debe romperse |
| **Accesibilidad visual** | F8 Modo accesibilidad. Mientras tanto: verificar contraste WCAG AA en `_test_color_regression.py` |
| **Light vs Dark theme** | Toda pantalla debe verse legible en ambos modos. Validar con `_capture_v3_screens.py` |
| **PC compartida** | F3 Modo privacidad. Verificar que un usuario no autorizado no ve datos. |

### 10.4 Pruebas de seguridad

| Aspecto | Cómo validar | Acción si falla |
|---|---|---|
| **RLS Supabase legal_consents** | INSERT con anon key → debe fallar (sin auth). SELECT con anon → debe funcionar (policy `legal_consents_select_anon_hub`). INSERT con auth user A intentando user B → debe fallar. | Revisar políticas RLS en Supabase Dashboard |
| **RLS deshabilitado en clínicas (decisión consciente)** | Documentar en `AI_PROJECT_CONTEXT.md` que es intencional + revisar si en F5 sigue siendo defensible | Si no defensible → habilitar RLS por patient_id |
| **Anon key visible** | Está en `.env` distribuido. Asegurar que sólo tiene permisos de anon (no service_role). | Rotación cada 6 meses con plan |
| **Datos clínicos en logs** | Revisar [shared/crash_log.py](shared/crash_log.py) — no debe loguear PII | Filtrar PII antes de log |
| **Consentimiento vigente para acciones Hub** | Antes de cualquier acción de escritura del paciente, verificar consent | F5 + B8 |
| **Permisos paciente-profesional** | Hoy: cualquier Hub con anon key ve cualquier paciente. Para multi-clínica futura: implementar vinculación explícita | F5 (si MVP requiere) |
| **Acceso profesional-paciente** | Hoy implícito por confianza. Documentar para piloto. Eventualmente añadir `profesional_team_id` en `patients` | F5 |
| **Logs locales** | Revisar `%APPDATA%/NeuroMood/logs/*.log` no expone datos sensibles | OK actual — solo excepciones |
| **Errores sin exponer datos** | Toasts Hub no muestran stack traces con PII | Validar manualmente |
| **PIN modo privacidad PBKDF2** | F3 — usar `_hash_pwd` con salt único | OK (infraestructura lista) |
| **`.env` oculto en AppData** | Verificar `SetFileAttributesW(env_dest, 0x2)` aplicado | OK actual ([installer.py:712](installers/installer.py)) |
| **Firma de código** | Hoy SIN firma → Windows SmartScreen alerta | F6 — adquirir certificado |
| **payload_*.zip externo** | Verificar checksums | F6 — agregar hash check |
| **Auditoría IA outputs** | F4 — `ia_audit_log` | Implementar |
| **Auditoría cambios profesionales** | F2 — `professional_audit` | Implementar |
| **Recuperación de PIN (modo privacidad)** | Verificar flujo email Supabase | F3 |

---

## PARTE 11 — Mega plan por fases

Para cada fase: **objetivo, tareas concretas, archivos involucrados, resultado esperado, riesgos, validación mínima, prioridad, qué NO tocar.**

### FASE 0 — Auditoría, limpieza y des-semáforo (3-5 días)

**Objetivo:** dejar el repo en estado limpio + **eliminar lenguaje semáforo clínico del Hub (bloqueante de aprobación)** antes de empezar features.

**🔴 F0.1 — Eliminar lenguaje semáforo clínico del Hub (decisión 7, BLOQUEANTE)**

*Por qué primero:* contradice directamente la decisión 7 ("sin semáforos clínicos ni etiquetas tipo riesgo/crítico") + es bloqueante de aprobación con el cliente clínico. Ausencia de uso ≠ baja adherencia terapéutica; interpretarlo así puede generar decisiones clínicas erróneas.

Cambios:

- [hub/main_qt.py:171-389](hub/main_qt.py) `DashboardView` — eliminar tags "Adherencia alta", "Riesgo bajo", "Agenda al día" del featured card. Reemplazar por información **neutral descriptiva**: "Último registro: hace 2 días", "Tareas asignadas: 3 activas", "Próxima sesión: viernes 14:00", "Recordatorios activos: 5".
- [hub/main_qt.py:400-557](hub/main_qt.py) `PacientesView` — eliminar tab filtro "Atención" (criterio interpretativo `adherence<40%`) o renombrarlo a **"Sin sincronización reciente"** con criterio neutral basado en `last_sync_date` (ej: ">7 días sin sync"). Es un dato descriptivo del estado del sync, no una interpretación clínica.

Validación:

- `grep -E "Riesgo|Adherencia alta|Adherencia baja|Atención"` en `hub/main_qt.py` y `hub/pacientes_qt.py` debe devolver **0 matches como tags clínicos de UI** (las referencias a "Atención" pueden quedar sólo si es contexto neutral como label de campo, nunca como interpretación clínica).
- Capturar Dashboard antes/después con `_capture_v3_screens.py`.

Estimado: 1-2 días.

**F0.2 — Limpieza de raíz y scripts**

1. Commitear el delete del `REDESIGN/` (123 archivos en `D` git status). Confirmar con usuario antes.
2. Mover scripts legacy raíz a `AI_SCRIPTS/legacy/`: `edit_script.py`, `edit_script_avisos.py`.
3. Mover `unificar.py` a `AI_SCRIPTS/dump_repo_for_ai.py`.
4. Mover `PLAN_REDISEÑO_FUENTE_DE_LA_VERDAD.txt` a `AI_SCRIPTS/notes/`.
5. Eliminar `descripcion y manuales desactualizados.txt` (existe PDF generado vigente).
6. Crear `BUILD_NEUROMOOD.bat` consolidado (que llame al `build_neuromood.py` raíz). Mantener `BUILDER_NUEVO_RAPIDO.bat` como alias por compatibilidad temporal.
7. Eliminar `AI_SCRIPTS/build_neuromood.py` (duplicado obsoleto del raíz).
8. Actualizar `AI_PROJECT_CONTEXT.md`: documentar que `BUILD_NEUROMOOD.bat` ahora existe y es el oficial.
9. Agregar a `.gitignore`: `build.log`, `__pycache__/` raíz, `_qa_output/`.
10. Verificar que `_GRAD_PUNTAJE` ([shared/utils.py:23-26](shared/utils.py)) y `COLORES_PUNTAJE` ([app/modules/animo_qt.py:75-79](app/modules/animo_qt.py)) son la misma idea — decidir cuál se queda.

**Archivos:** raíz + `AI_SCRIPTS/` + `AI_PROJECT_CONTEXT.md`.

**Resultado esperado:** raíz limpia (solo lo oficial), sin archivos legacy, build consolidado, docs alineadas con realidad.

**Riesgos:** ninguno (operaciones reversibles via git).

**Validación:** `git status` limpio, `ls raíz` solo muestra estructura oficial, `BUILD_NEUROMOOD.bat --dry-run` funciona.

**Prioridad:** Alta (bloquea higiene del repo).

**Qué NO tocar:** ningún módulo Suite/Hub/instalador.

### FASE 1 — Cumplimiento explícito Propuesta Base (1 semana)

**Objetivo:** cerrar la 7ma herramienta lado paciente.

**Tareas:**
1. Implementar A1 (mini-visualizador semanal en Home Suite) — reusar `NMWaveChart`.
2. Decidir: ¿el visualizador queda como sección de Home o como módulo separado? **Recomendación: sección de Home**, no nuevo módulo (evita 8 cards y desbalance).
3. Capacidad de exportar PDF desde Suite (mini, sólo gráfico).

**Archivos:** [app/home_qt.py](app/home_qt.py) (nueva sección debajo del grid o en `_SidePanel`).

**Resultado:** la 7ma herramienta queda cubierta lado paciente sin agregar superficie nueva.

**Riesgos:** romper layout responsive (mitigar con tests visuales).

**Validación:** capturar Home con 0, 1, 7, 30 registros, verificar legible.

**Prioridad:** Alta.

**Qué NO tocar:** módulo Ánimo separado (sigue siendo el lugar para el detalle).

### FASE 2 — Configurabilidad remota desde Hub (4-8 semanas) **— LA FASE GRANDE**

**Objetivo:** desbloquear toda la matriz de Parte 5 + arquitectura concreta de Parte 9.

**Subfases:**

#### F2.0 — Patrón general `hub_config` 2 niveles (PRIMERO, 1-2 semanas) — decisión 2026-05-21

> **Esta subfase es la base de todo lo demás. No empezar F2.1-F2.5 sin esta.** Subsección 9.4.A del informe.

Tareas:

- Crear tabla `hub_config` única (scope + key + value JSONB) en `db/hub_config_schema.sql`.
- Crear util `shared/remote_config.py` con `t(key, default, patient_id=None)` que aplica jerarquía `patient:<id>` → `global` → `default`.
- Cache local en SQLite (`remote_config_cache` tabla nueva, agregada en `shared/db.py:inicializar_tablas()`).
- Extender [shared/sync.py](shared/sync.py) con `_importar_hub_config(patient_id)` siguiendo el patrón existente de `_importar_*`.
- Reestructurar `ConfigView` del Hub en 2 secciones explícitas: "Configuración del equipo" (scope=global) + "Configuración por paciente" (sub-tab en Detalle Paciente).

Validación: crear key arbitraria en `hub_config` con scope=global, leer con `t("test.key", "default")` desde Suite y verificar valor remoto. Setear override `scope='patient:<id>'`, verificar que prevalece.

#### F2.1 — Backend tablas específicas (1 semana)

- Schemas para excepciones que NO viven en `hub_config` (porque tienen relaciones FK complejas o son colecciones): `tcc_templates`, `routine_templates`, `patient_routine_template`, `breathing_presets_remote`, `timer_presets_remote`, `support_messages`, `ia_audit_log`, `ia_chat_history`.
- Aplicar en Supabase test.
- Agregar tablas cache a [shared/db.py:inicializar_tablas()](shared/db.py).

Validación: SELECT manual en Supabase, INSERT desde código, lectura desde Suite cacheada correctamente.

#### F2.2 — Timer profesional + Avisos plantillas equipo (1-2 semanas) — interpretación Propuesta Base 2026-05-21

> **Por qué F2.2 antes de F2.3:** Timer y Avisos son los módulos donde la Propuesta Base es más explícita sobre que el equipo delimita (item 3 "actividades terapéuticas", item 2 "mensajes a horarios fijos determinados por el equipo").

Tareas:

- **Timer (A4):** Editor de presets timer desde Hub (`timer_presets_remote`). Cambiar [app/modules/timer_qt.py:71-76](app/modules/timer_qt.py) para leer presets desde DB (con fallback hardcoded). El permiso `perm_temporizador_manual` pasa a significar "puede usar custom además de los presets asignados". Por defecto el paciente sólo elige entre presets del equipo.
- **Avisos (interpretación Propuesta Base 2):** Biblioteca de mensajes de apoyo + plantillas de recordatorios reutilizables desde Hub. Extender tabla `mensajes_biblioteca` ya existente ([shared/db.py:189-193](shared/db.py)) con sync remoto + scope global/patient. `perm_recordatorios_manual` pasa a significar "el paciente puede crear los suyos además de los del equipo".
- Extender [shared/sync.py](shared/sync.py) con `_importar_timer_presets`, `_importar_support_messages`, `_importar_assigned_reminders_templates`.

Validación: crear preset desde Hub → forzar sync → verificar que aparece en Suite y reemplaza los hardcoded.

#### F2.3 — Rutina sistema 3 estados + plantillas (1-2 semanas) — opción C decisión 2026-05-21

Tareas:

- ALTER `patients` ADD COLUMN `rutina_modo TEXT DEFAULT 'mixto'` (valores: `solo_profesional` / `mixto` / `solo_paciente`).
- Crear `routine_templates` y `patient_routine_template` (Parte 8 A7).
- [app/modules/rutina_qt.py](app/modules/rutina_qt.py): leer modo del paciente + condicionar botón "+ Agregar tarea" + agregar badge "Personal" a tareas con `origen='manual'`.
- [shared/sync.py](shared/sync.py): nuevo `_importar_routine_template(patient_id)` y `_importar_rutina_modo(patient_id)`.
- [hub/pacientes_qt.py:454-561](hub/pacientes_qt.py) `_TabAsignar`: nuevo card "Plantilla de rutina" con drag-drop + selector modo.

Validación: setear `rutina_modo=solo_profesional` desde Hub → cerrar/abrir Suite → verificar que botón "+ Agregar tarea" desaparece.

#### F2.4 — UI Hub editores TCC + textos + categorías (2-3 semanas)

- Tab "Configuración (override)" en `DetallePacienteView` (depende de F2.0).
- Editor de plantillas TCC ([hub/editors/tcc_template_editor.py](hub/editors/tcc_template_editor.py)).
- Editor de presets respiración (con preview animado).
- Editor de text overrides genérico (con preview en vivo).
- Botones "Restaurar default" + "Historial" + preview en vivo.

Validación: crear template TCC custom → asignar a paciente → verificar Suite refleja al sincronizar.

#### F2.5 — Migración progresiva strings hardcoded → `t(key, default)` (3-4 semanas)

- Sprint A-H (Parte 9.10): migrar strings hardcoded por módulo.
- Tests visuales antes/después con `_capture_v3_screens.py`.

Validación: capturar todas las pantallas, comparar con baseline, verificar que cambiar override desde Hub se refleja.

#### F2.6 — Constructor de informes paramétrico (1 semana)
- B10 / B3 — selector de secciones en exportar PDF.

**Archivos:** [hub/exportar.py](hub/exportar.py).

**Resultado esperado F2:** toda la matriz de Parte 5 cubierta. El cliente puede cambiar textos, plantillas TCC, presets, rutinas, mensajes desde el Hub sin tocar código.

**Riesgos:** romper UI con configuraciones inválidas → validación schema + `default` siempre presente. Costo de implementación alto → planificar con margen.

**Validación final:** cliente puede editar el tip terapéutico del TCC desde Hub y ver el cambio en Suite tras forzar sync.

**Prioridad:** **Muy Alta — esta fase es lo que desbloquea aprobación clínica.**

**Qué NO tocar:** consentimientos, prompts IA (decisiones 5, 6).

### FASE 3 — Estabilización Suite + Modo privacidad + Settings al Home (1-2 semanas)

**Objetivo:** Suite robusta para uso real + Modo privacidad del paciente + reorganización de settings en Home.

**Tareas:**
1. **A2 Modo privacidad del paciente** ([app/main_qt.py](app/main_qt.py) + nuevo `app/privacy_lock_qt.py`).
2. **A8 Panel Settings generales en Home (decisión 2026-05-21):** mover `_get_autostart`/`_set_autostart` desde el módulo Avisos al Home Suite como opción general:
   - Crear nuevo `_SettingsPanel` accesible desde ícono ⚙ del header del Home.
   - Mover **Inicio con Windows** (autostart) desde [app/modules/avisos_qt.py](app/modules/avisos_qt.py) (card de opciones) al `_SettingsPanel` del Home. El daemon ([app/avisos_daemon.py:320-352](app/avisos_daemon.py)) sigue leyendo el mismo registry HKCU — sólo cambia dónde el usuario lo togglea.
   - Agregar **Modo privacidad** (PIN) en el mismo panel.
   - Agregar **Apariencia** (tema dark/light) en el mismo panel.
   - Dejar shim de compatibilidad en `avisos_qt.py` (link "Configurar inicio con Windows → Ajustes generales") por ~1 release.
3. Revisión de textos hardcoded restantes que no se migraron en F2.
4. Performance: verificar animaciones a 60fps en hardware modesto.
5. Testing manual de cada uno de los 7 módulos con configuraciones custom.
6. **No incluir "modo bajo ánimo automático"** (descartado, decisión 3).

**Archivos:** [app/main_qt.py](app/main_qt.py), [app/home_qt.py](app/home_qt.py), nuevo `app/privacy_lock_qt.py`, extender [shared/identidad.py](shared/identidad.py).

**Resultado:** Suite con PIN opt-in, todos los textos clínicos desde Hub.

**Riesgos:** olvido de PIN sin recovery configurado → asegurar que recovery por email funciona.

**Validación:** crear PIN, cerrar, abrir, ingresar, ver Home; olvidar, recuperar.

**Prioridad:** Media.

### FASE 4 — Estabilización Hub + Audit IA + Mensajería (2-3 semanas)

**Objetivo:** Hub completo para uso clínico real.

**Tareas:**
1. **A6 Gestión real de pacientes** (botón "+ Nuevo" con handler).
2. **B5 Audit log IA** + **B6 persistencia chat IA**.
3. **A3 (paciente) + B7 (Hub) Bandeja indicaciones profesional → paciente.**
4. **B1 Panel actividad reciente neutral** (reemplaza tags problemáticos del Dashboard — decisión 7).
5. **B4 Worklist de revisión** (paciente marca registros).
6. **B8 Validación de consent pre-acción.**

**Archivos:** [hub/main_qt.py](hub/main_qt.py), [hub/pacientes_qt.py](hub/pacientes_qt.py), [hub/ia_asistente.py](hub/ia_asistente.py), nuevo `hub/audit_qt.py`, nuevo `hub/patient_management.py`, [app/home_qt.py](app/home_qt.py).

**Resultado:** Hub completo profesional. Audit log activo. Crear pacientes sin tocar Supabase. Mensajería profesional ↔ paciente.

**Riesgos:** mucha UI nueva → testear bien.

**Validación:** profesional crea paciente desde Hub → genera install_code → instala Suite con ese código → vinculación correcta.

**Prioridad:** Alta.

### FASE 5 — Sync, permisos y seguridad (1-2 semanas)

**Objetivo:** producción-ready desde el punto de vista de seguridad.

**Tareas:**
1. Revisar RLS deshabilitado en clínicas. Decidir: ¿se deja así (documentado) o se habilita con políticas por patient_id?
2. Documentar política de anon key + plan de rotación.
3. Validación de vinculación paciente-profesional (si MVP multi-equipo).
4. Filtrar PII de logs.
5. Toasts/errores Hub sin stack traces visibles.
6. Modo privacidad del paciente integrado con Supabase Auth para recovery.

**Archivos:** `db/*.sql`, [shared/crash_log.py](shared/crash_log.py), [hub/main_qt.py](hub/main_qt.py).

**Resultado:** matriz de seguridad de Parte 10.4 cubierta.

**Riesgos:** activar RLS sin políticas correctas → Hub queda sin acceso.

**Validación:** correr [shared/sync.py](shared/sync.py) con anon key restringida → verificar funciona.

**Prioridad:** Media-Alta.

### FASE 6 — QA e instaladores production-ready (1 semana)

**Objetivo:** distribución segura.

**Tareas:**
1. Firma de código Authenticode (adquirir certificado).
2. Modo offline en consent remoto: si falla la inserción, encolar en local y reintentar al volver online (en vez de bloquear).
3. Manejo robusto de errores red en instalador.
4. Telemetría agregada anónima (con consent explícito del usuario).
5. Smoke tests automatizados en CI.
6. Documentar releases.

**Archivos:** `installers/*.py`, `AI_SCRIPTS/smoke_test_runner.py`, build pipeline.

**Resultado:** instalador firmado + manejo robusto offline + CI gates.

**Riesgos:** firma de código tiene costo $$. Confirmar con cliente.

**Validación:** instalar en VM Windows 10/11 limpia → SmartScreen sin alerta tras firma → consent funciona offline → vuelve a sync al recuperar internet.

**Prioridad:** Alta antes de piloto.

### FASE 7 — Piloto clínico (3-4 semanas)

**Objetivo:** validar con pacientes y profesionales reales.

**Tareas:**
1. Reunir 3-5 pacientes voluntarios + 1-2 profesionales del equipo NeuroMood.
2. Instalar Suite a cada paciente. Instalar Hub a profesionales.
3. Onboarding presencial.
4. Recolección de feedback semanal (formulario simple + 1 llamada).
5. Métricas neutrales agregadas (cuántos días con uso, no "adherencia" — decisión 7).
6. Diario de issues + clasificación severidad.

**Archivos:** ninguno (es operativo).

**Resultado:** lista de issues + ideas + cambios pedidos. Validación de hipótesis clínicas.

**Riesgos:** baja adopción → mitigar con onboarding presencial. Issues bloqueantes → fix rápido (F8).

**Validación:** sobrevive 4 semanas de uso real sin crashes graves.

**Prioridad:** Alta (es el momento de la verdad).

**Qué NO tocar:** features nuevas durante el piloto (solo fixes).

### FASE 8 — Ajustes post-feedback (2-3 semanas)

**Objetivo:** materializar el ROI de F2.

**Tareas:**
1. Issues bloqueantes → fix.
2. Ajustes de textos / plantillas / presets vía Hub (sin tocar código — ése es el test real de F2).
3. Onboarding interactivo (B2 paciente).
4. Modo accesibilidad (C1 paciente).
5. UX refinements: tooltips, micro-copy.
6. Refinamiento estético si se identifican issues visuales.

**Archivos:** muchos cambios menores en UI + ediciones vía Hub.

**Resultado:** producto refinado con feedback real.

**Riesgos:** alcance creep — mantener disciplina sobre qué se hace y qué pasa a F9 o futuro.

**Validación:** segundo piloto corto (1 semana) con los cambios.

**Prioridad:** Alta.

### FASE 9 — Release candidato (1-2 semanas)

**Objetivo:** versión 1.0 distribuible.

**Tareas:**
1. Actualizar manuales PDF ([AI_SCRIPTS/generate_neuromood_manuals.py](AI_SCRIPTS/generate_neuromood_manuals.py)).
2. Video tutorial corto (paciente + profesional).
3. Paquete final + signing.
4. Página de descarga (si aplica).
5. Soporte: canal de issues + documentar.
6. Bump versión a 1.0.0 oficial.
7. Tag git + release notes.

**Archivos:** docs + manuales + binaries.

**Resultado:** producto 1.0 listo para uso clínico real en NeuroMood.

**Riesgos:** issues last-minute → reserve 1 semana extra.

**Validación:** 3 voluntarios externos descargan e instalan sin ayuda → completan onboarding sin errores.

**Prioridad:** Alta.

### Mapa visual de fases (estimación tiempo)

```
F0 ████ 3-5 días              (limpieza)
F1 ███████ 1 semana            (mini-visualizador)
F2 ████████████████████████████████████ 4-8 semanas   (configurabilidad — LA FASE)
F3 ████████████ 1-2 semanas    (modo privacidad + estabilizar Suite)
F4 ███████████████████ 2-3 semanas  (estabilizar Hub + audit)
F5 ████████████ 1-2 semanas    (seguridad)
F6 ███████ 1 semana            (QA + instaladores firmados)
F7 ████████████████████ 3-4 semanas  (piloto)
F8 ██████████████ 2-3 semanas  (post-feedback)
F9 ████████████ 1-2 semanas    (release candidate)
```

**Total estimado:** ~5-7 meses (camino realista con margen). Camino agresivo: 4-5 meses si se paraleliza F2 con F3-F4.

**Hitos críticos:**
1. **F2 terminada** = el cliente puede configurar todo desde Hub → desbloquea aprobación clínica.
2. **F7 piloto exitoso** = validación de hipótesis → ir o no ir a release.
3. **F9 release** = producto en producción.

---

## Cierre — Respuestas directas a las 7 preguntas finales

> Las 7 preguntas son las del prompt maestro (líneas 768-774).

### 1. ¿Qué utilidades hay actualmente?

**Para pacientes (Suite):**
- Termómetro Emocional (`animo_qt.py`)
- Guía Respiración Animada 4-7-8 (`respiracion_qt.py`)
- Registro Pensamientos TCC con 4 pasos + detección automática de 10 distorsiones (`registro_tcc_qt.py`)
- Checklist Rutina Diaria con 3 secciones + nota del día (`rutina_qt.py`)
- Asistente Activación Conductual con 6 categorías + sugerencias por ánimo (`actividades_qt.py` + `motor_activacion.py`)
- Temporizador de enfoque con 4 presets + custom (`timer_qt.py`)
- Recordatorios con daemon Windows + bandeja + autostart (`avisos_qt.py` + `avisos_daemon.py`)

**Para profesionales (Hub):**
- Dashboard panel clínico
- Listado/búsqueda/filtros de pacientes
- Detalle de paciente con 4 tabs: Registros (gráfico longitudinal + export PDF), Asignar tareas/recordatorios, Banco actividades (CRUD), IA (resumen + sugerencias + generar tarea)
- IA Asistente global (chat conversacional)
- Config (read-only)
- Exportar PDF clínico + constancia legal

**Sistema:**
- 4 instaladores/desinstaladores con consent legal versionado
- Sync bidireccional con debounce + import asignaciones
- Auth Supabase directo
- 11 tablas Supabase + 18 tablas SQLite locales
- IA multiproveedor con fallback (Groq/Gemini/OpenCode/Ollama)
- Theme V3 dark/light híbrido
- 54+ componentes Qt reutilizables
- 65 iconos SVG nativos

### 2. ¿Qué está implementado en código (NO verificado en ejecución)?

> Renombrado de "¿Qué funciona?" a su forma precisa, según la nota metodológica del inicio del informe. Esta auditoría se hizo por lectura — runtime no fue verificado en Windows real.

✅ **Implementado en código (lógica coherente leída, sintaxis válida, pero NO verificado en runtime):**
- Los 7 módulos paciente con sus respectivas DBs y sync (animo, respiración 4-7-8, registro_tcc 4 pasos, rutina 3 secciones, actividades motor + fallback, timer preset/custom, avisos + daemon).
- Sync background al abrir Suite + inmediato 48h al guardar (`shared/sync.py`).
- Daemon avisos en hilo + bandeja + autostart Windows (depende de `pystray`+`winotify` runtime).
- Hub Dashboard + Pacientes + Detalle con sus 4 tabs.
- IA multiproveedor con scoring + retry + fallback automático (Groq/Gemini/OpenCode/Ollama).
- Exportar PDF clínico + constancia consent vía ReportLab.
- 4 instaladores con auth + consent + payload externo opcional.
- 4 desinstaladores con flag conservar datos (bug 2026-05-18 fixed en `uninstaller_pro.py:283-291`).
- PBKDF2 hash de passwords (`shared/identidad.py:5-13`).
- Theme transitions 350ms crossfade.
- Visual QA fixtures opt-in via env vars.

⚠️ **Para verificar antes de piloto:** correr el plan de QA de la Parte 10 con apps reales en Windows. Animaciones, glow, beeps, daemon system tray, notificaciones SO, autostart, instaladores empacados, SmartScreen, IA endpoint real, RLS Supabase real son **NO VERIFICABLES SIN EJECUTAR**.

### 3. ¿Qué utilidades no funcionan, están incompletas o son dudosas?

❌ **Incompleto (por evidencia textual):**
- **Botón "+ Nuevo paciente" sin handler** ([hub/main_qt.py:453-455](hub/main_qt.py)).
- **ConfigView es read-only** excepto Tema y Sincronizar ([hub/main_qt.py:562-707](hub/main_qt.py)).
- **`BUILD_NEUROMOOD.bat` mencionado en docs NO existe** — solo `BUILDER_NUEVO_RAPIDO.bat` y `BUILDER_VIEJO_LENTO.bat`.
- **Persistencia chat IA** ([hub/main_qt.py:712-911](hub/main_qt.py)) — se pierde entre sesiones.
- **Audit log IA** — no existe ninguna tabla.

⚠️ **Dudoso / problemático (prioridad crítica):**
- 🔴 **Tags Dashboard hardcoded** "Adherencia alta", "Riesgo bajo", "Agenda al día" ([hub/main_qt.py:171-389](hub/main_qt.py)) — contra decisión 7. **F0.1 BLOQUEANTE.**
- 🔴 **Filtro "Atención"** ([hub/main_qt.py:419-420](hub/main_qt.py)) usa adherence<40% — interpretación clínica automática prohibida por decisión 7. **F0.1 BLOQUEANTE.**
- **RLS deshabilitado en tablas clínicas** — defensible para entorno controlado, debe documentarse explícitamente para auditoría legal.
- **`mensajes_biblioteca`, `activacion_perfil`, `checklist_plantillas`, `timer_presets`** son tablas SQLite locales creadas pero sin uso / sin contraparte remota. Oportunidad para F2.2/F2.3 (reusar antes de eliminar).
- **`AI_SCRIPTS/build_neuromood.py` duplicado obsoleto** (14KB vs el del raíz que es 20KB).
- **Scripts `edit_script.py`, `edit_script_avisos.py`, `unificar.py`** en raíz sin documentación clara (son legacy de patches one-shot ya aplicados).

🔴 **NO VERIFICABLE SIN EJECUTAR (runtime Windows real):**
- Si los EXEs compilados arrancan en una Windows fresh sin Python.
- Si la firma de código está ausente (asumido por defecto, no firmado).
- Si la animación del breath circle (`_BreathCircle`) corre a 60fps en hardware modesto.
- Si la notificación winotify dispara correctamente en Windows 11 sin permisos especiales.
- Si el autostart Windows escribe el HKCU correctamente.
- Si la integración con Supabase auth funciona sin Email Confirmation activado.
- Si la IA real responde dentro del timeout de 15s.
- Si el daemon `pystray` mantiene el ícono de bandeja sin crashear.

> **Nota metodológica:** los ítems de las primeras dos categorías están marcados como incompletos/dudosos por **evidencia textual** (botón sin handler, tabla sin uso, tag clínico hardcoded), no por testeo en Windows real. Los de la tercera categoría requieren correr el plan de QA Parte 10.

### 4. ¿Qué utilidades faltan para cumplir o superar la Propuesta Base?

**Para CUMPLIR (críticos):**
- ❗ **Visualizador Evolución Anímica lado paciente** (mini-visualizador en Home Suite — F1).
- ❗ **Gestión real de pacientes desde Hub** (handler "+ Nuevo paciente" — F4).
- ❗ **Configurabilidad remota de plantillas TCC, presets respiración, rutinas, mensajes** (F2 — la fase grande).

**Para SUPERAR (lo que diferencia al producto):**
- Modo privacidad del paciente con PIN.
- Bandeja de indicaciones profesional → paciente (minimizable).
- Audit log IA + persistencia chat.
- Constructor de informes paramétrico.
- Worklist de revisión (paciente marca registros).
- Onboarding interactivo de 5 min.
- Panel actividad reciente neutral (reemplaza tags de riesgo).

### 5. ¿Qué utilidades nuevas conviene implementar?

**Top 5 paciente** (orden de impacto + factibilidad):

1. **Mini-visualizador semanal en Home Suite** (A1, F1) — completa Propuesta Base + alto valor + baja complejidad
2. **Modo privacidad del paciente con PIN** (A2, F3) — privacidad real + reusa PBKDF2 ya implementado
3. **Panel Settings generales en Home Suite** (A8, F3) — autostart + privacidad + tema en un solo lugar; mueve autostart fuera del módulo Avisos
4. **Bandeja de indicaciones del profesional minimizable** (A3, F4) — canal directo terapeuta-paciente sin email externo
5. **Plantillas TCC configurables por profesional** (B1, F2.4) — habilita ajuste clínico sin código + valor TCC

**Top 5 profesional:**

1. **Patrón general `hub_config` 2 niveles + ConfigView reestructurada** (F2.0, subsección 9.4.A) — base de toda la configurabilidad
2. **Timer customizado por profesional + Avisos plantillas equipo** (A4 Parte 6, F2.2) — interpretación Propuesta Base ítems 2 y 3
3. **Editor plantillas de rutina + selector modo por paciente (opción C)** (A7 Parte 8, F2.3) — sistema híbrido 3 estados
4. **Editor de plantillas TCC** (A2 Parte 8, F2.4) — para el módulo con más contenido clínicamente sensible
5. **Gestión real de pacientes + audit log IA + panel actividad reciente neutral** (A6 Parte 8, B5, B1, F0.1+F4) — gestión completa de pacientes desde Hub + reemplazo de tags semáforo

### 6. ¿Qué debe poder configurar el Hub para evitar refactors futuros?

**Patrón #1 (meta-elemento, subsección 9.4.A):** TODO lo configurable del Hub se piensa con el patrón **`hub_config` 2 niveles** (scope `global` + scope `patient:<id>`). Toda feature nueva pasa por aquí, no por tablas ad-hoc. Esto es el bloque base de F2.0.

**Top 10 prioridades de configurabilidad remota** (con el patrón anterior aplicado):

1. **Textos visibles en Suite** (greetings, eyebrows, descripciones módulos, chips) → claves en `hub_config` con prefijo `text.*`
2. **Habilitar/deshabilitar módulos por paciente** → `perm_*` ya en `patients` + UI Hub para togglearlos (hoy DB pero sin UI)
3. **Plantillas TCC completas** (4 steps + 8 emotions + 10 distortions + tip + success) → tabla `tcc_templates` (excepción a `hub_config` por estructura compleja)
4. **Plantillas de rutinas reutilizables** + selector modo `rutina_modo` por paciente (opción C) → `routine_templates` + `patient_routine_template` + ALTER `patients`
5. **Presets de timer (Propuesta Base 3 — actividades terapéuticas delimitadas por el equipo)** → `timer_presets_remote`
6. **Plantillas de mensajes apoyo + recordatorios (Propuesta Base 2 — mensajes determinados por el equipo)** → `support_messages` + extender `mensajes_biblioteca` con sync
7. **Presets de respiración** (técnicas + fases + duraciones) → `breathing_presets_remote`
8. **Etiquetas semánticas de ánimo 1-10** → `hub_config` con `key='mood.labels'`
9. **Categorías de actividades** (nombre + icon + color + orden) → `activity_categories`
10. **Settings generales de Suite** (autostart Windows, modo privacidad, tema) — vienen de `hub_config` para override desde el equipo, pero también editables en el Home Suite (panel `_SettingsPanel`, A8 Parte 8)

**Lo que NO debe ser configurable desde UI** (decisiones 5, 6, 7):
- Consentimientos legales (versionados en código + migraciones)
- Disclaimers (versionados en código)
- Prompts IA del sistema (versionados en código + `ia_audit_log` para auditoría)
- Métricas de adherencia poblacional con semáforos (tags Dashboard "Adherencia alta/Riesgo bajo/Atención" — F0.1 elimina lo existente)
- Lógica de detección automática de estado emocional (modo bajo ánimo automático, etc.)

> **Excepción explícita al patrón `hub_config`:** las 3 apps del Ánimo Loop (Termómetro, Visualizador, Activación Conductual) **sí usan la variable ánimo declarada por el paciente** — eso no es "automatismo oculto" sino la lógica explícita pedida por la Propuesta Base. El profesional configura desde Hub los rangos `animo_min`/`animo_max` por actividad (en `activity_bank`) y las etiquetas visibles (en `hub_config`). Ver subsección "NeuroMood Ánimo Loop".

### 7. ¿Qué haría primero si el objetivo es que NeuroMood lo apruebe para uso clínico real?

**Orden estricto recomendado:**

```
0. F0.1 DES-SEMÁFORO HUB        (1-2 días) 🔴 BLOQUEANTE
   - Eliminar tags Dashboard "Adherencia alta/Riesgo bajo/Agenda al día"
   - Quitar filtro "Atención" de Pacientes o renombrar a "Sin sync reciente"
   ↓ Hub clínicamente aceptable (decisión 7 cumplida).

1. F0.2 LIMPIEZA REPO          (2-3 días)
   - REDESIGN/ commit + scripts legacy a AI_SCRIPTS/legacy/
   - BUILD_NEUROMOOD.bat consolidado
   - .gitignore extendido
   ↓ Raíz limpia, build oficial.

2. F2.0 PATRÓN GENERAL hub_config (1-2 semanas) — base de TODO
   - Tabla `hub_config` única + scope global/patient
   - `shared/remote_config.py` con `t(key, default, patient_id)`
   - ConfigView reestructurada en 2 secciones (equipo + por paciente)
   ↓ Plataforma de configurabilidad lista (subsección 9.4.A).

3. F2.2 TIMER + AVISOS INTERPRETACIÓN PROPUESTA BASE (1-2 semanas)
   - Editor presets timer desde Hub + override `perm_temporizador_manual`
   - Biblioteca mensajes apoyo + plantillas recordatorios del equipo
   ↓ Items 2 y 3 de Propuesta Base correctamente interpretados.

4. F2.3 RUTINA SISTEMA 3 ESTADOS (1-2 semanas) — opción C
   - Nuevo `rutina_modo` en `patients` + editor plantillas + selector modo
   ↓ Item 6 de Propuesta Base con gradación clínica.

5. F2.4 UI HUB EDITORES TCC + textos (2-3 semanas)
   - Editor de plantillas TCC (mayor impacto clínico)
   - Editor de text_overrides genérico
   - Tab "Configuración (override)" en Detalle Paciente
   ↓ El equipo clínico puede editar lo más sensible desde Hub.

6. F4 GESTIÓN PACIENTES + AUDIT IA (2-3 semanas)
   - "+ Nuevo paciente" con handler
   - `ia_audit_log` + persistencia chat IA
   - Panel actividad reciente neutral (B1, completa F0.1)
   ↓ Hub completo profesional.

7. F3 MODO PRIVACIDAD + SETTINGS HOME + F1 MINI-VISUALIZADOR (1-2 semanas)
   - Modo privacidad con PIN + Settings panel en Home
   - Autostart Windows movido de Avisos a Home
   - Mini-visualizador semanal en Home (cierra 7ma herramienta lado paciente)
   ↓ Suite madura.

8. F7 PILOTO con 3-5 pacientes reales (3-4 semanas)
   ↓ Validación con feedback real.

9. F8 AJUSTES POST-FEEDBACK (2-3 semanas)
   ↓ Iteración rápida vía Hub (sin recompilar).

10. F2.5 + F2.6 MIGRACIÓN TEXTOS + INFORMES (paralelizado con F8) (2-4 semanas)
    ↓ Sprints A-H + constructor informes paramétrico.

11. F5 SEGURIDAD + F6 INSTALADORES FIRMADOS (2-3 semanas)
    ↓ Producción-ready.

12. F9 RELEASE 1.0 (1-2 semanas)
```

**Justificación del orden:**

- **F0.1 PRIMERO Y SOLO** — los tags semáforo del Hub contradicen decisión 7 y son bloqueantes de aprobación clínica. Antes que cualquier feature.
- **F0.2 limpieza** porque sin repo limpio cualquier trabajo es ruido.
- **F2.0 antes que cualquier otra config** porque la subsección 9.4.A define el patrón general. Sin él, cada feature reinventa la rueda con tabla ad-hoc.
- **F2.2 (Timer + Avisos) + F2.3 (Rutina)** son las interpretaciones explícitas de Propuesta Base — prioridad sobre features nuevas.
- **F2.4 (TCC)** sigue por mayor impacto clínico en contenido.
- **F4 antes de F7** porque sin "+ Nuevo paciente" con handler implementado, el piloto se traba.
- **F3 + F1 pueden paralelizarse** (no dependen entre sí).
- **F7 piloto** sólo cuando se puede ajustar textos sin recompilar (post F2.0-F2.4).
- **F8 es el momento de la verdad** — ahí se ve si la inversión en F2 paga: si el cliente puede pedir ajustes y se hacen vía Hub en lugar de PR + build.

**Tiempo total estimado al release 1.0:** ~5-7 meses (con margen). Camino agresivo: 4-5 meses.

---

## Apéndices

### Apéndice A — Lista completa de archivos del repo con propósito

#### Raíz del repo

| Archivo | Propósito | Estado |
|---|---|---|
| `AI_PROJECT_CONTEXT.md` | Documentación maestra del proyecto (568 líneas) — **única fuente de verdad** | Vigente |
| `README.md` | Intro corto (~60 líneas) que remite a `AI_PROJECT_CONTEXT.md` | Vigente |
| `Propuesta Base.pdf` | Propuesta original del cliente NeuroMood (4 páginas, 8 herramientas) | Vigente |
| `prompt maestro.txt` | Prompt del usuario que originó esta auditoría | Vigente (input) |
| `AUDITORIA_NEUROMOOD.md` | ESTE archivo | Vigente |
| `build_neuromood.py` (20KB) | **Build oficial** PyInstaller — vigente | Vigente |
| `BUILDER_NUEVO_RAPIDO.bat` | Build modo external (con `payload_*.zip`) | Vigente con caveat |
| `BUILDER_VIEJO_LENTO.bat` | Build modo bundle todo-en-uno | Vigente |
| `BUILD_NEUROMOOD.bat` | **NO EXISTE** — mencionado en docs | F0 — crear |
| `edit_script.py` | One-shot patch a `components_qt.py` (a11y + breakpoints) | Legacy aplicado |
| `edit_script_avisos.py` | One-shot patch a `avisos_qt.py` (tamaños + a11y) | Legacy aplicado |
| `unificar.py` | Dump del repo para IA | Útil — mover a `AI_SCRIPTS/` |
| `PLAN_REDISEÑO_FUENTE_DE_LA_VERDAD.txt` | Plan viejo | Legacy — mover/eliminar |
| `descripcion y manuales desactualizados.txt` | Doc legacy | Eliminar |
| `Manual_Usuario_Profesional_NeuroMood.pdf` | Manual usuario generado | Artefacto distribución |
| `Manual_Tecnico_Descriptivo_NeuroMood.pdf` | Manual técnico generado | Artefacto distribución |
| `build.log` | Log último build | Artefacto (gitignore) |
| `__pycache__/` | Cache Python | Artefacto (gitignore) |
| `requirements.txt` | Dependencias | Vigente |
| `.env` / `.env.example` | Credenciales Supabase | Vigente |
| `.gitignore` | Git ignore | Vigente |

#### `app/` — Suite paciente

| Archivo | Propósito |
|---|---|
| `app/main_qt.py` (487 líneas) | Entry point Suite |
| `app/home_qt.py` (872 líneas) | Home con sidebar + grid 7 módulos |
| `app/avisos_daemon.py` (386 líneas) | Daemon notificaciones + bandeja Windows |
| `app/motor_activacion.py` (95 líneas) | Sugerencias actividades + fallback |
| `app/modules/animo_qt.py` (626 líneas) | Termómetro Emocional |
| `app/modules/respiracion_qt.py` (1032 líneas) | Respiración 4-7-8 |
| `app/modules/registro_tcc_qt.py` (1103 líneas) | TCC 4 pasos + detección distorsiones |
| `app/modules/rutina_qt.py` (767 líneas) | Checklist Rutina |
| `app/modules/actividades_qt.py` (865 líneas) | Activación Conductual |
| `app/modules/timer_qt.py` (634 líneas) | Timer enfoque |
| `app/modules/avisos_qt.py` (1040 líneas) | Recordatorios |

#### `hub/` — App profesional

| Archivo | Propósito |
|---|---|
| `hub/main_qt.py` (1429 líneas) | Entry point Hub + 4 vistas |
| `hub/pacientes_qt.py` (1321 líneas) | DetallePacienteView + 4 tabs |
| `hub/ia_asistente.py` (388 líneas) | IA multiproveedor |
| `hub/exportar.py` (254 líneas) | PDF clínico + constancia legal |

#### `shared/` — Compartido

| Archivo | Propósito |
|---|---|
| `shared/db.py` (342 líneas) | SQLite local + migraciones (18 tablas) |
| `shared/sync.py` (489 líneas) | Sync bidireccional Supabase |
| `shared/identidad.py` (64 líneas) | PBKDF2 hash + patient_id |
| `shared/config.py` (90 líneas) | Lectura .env (5 candidatos) |
| `shared/crash_log.py` (40 líneas) | Logging excepciones |
| `shared/utils.py` (37 líneas) | fecha_hoy/hora_actual + gradient |
| `shared/visual_qa.py` (123 líneas) | Fixtures QA opt-in env vars |
| `shared/theme.py` | Tokens V3 + paletas |
| `shared/theme_qt.py` | Qt helpers + fonts |
| `shared/components_qt.py` | 54+ widgets Qt |
| `shared/icons_svg.py` | 65 iconos SVG |
| `shared/installer_common.py` (663 líneas) | InstallerShell base + QSS |

#### `installers/` — Instaladores y desinstaladores

| Archivo | Propósito | Tamaño |
|---|---|---|
| `installers/installer.py` | Instalador Suite (5 pasos) | ~80KB |
| `installers/installer_pro.py` | Instalador Hub (3 pasos) | ~30KB |
| `installers/uninstaller.py` | Desinstalador Suite | ~25KB |
| `installers/uninstaller_pro.py` | Desinstalador Hub | ~26KB |

#### `db/` — Esquemas SQL

| Archivo | Propósito |
|---|---|
| `db/supabase_schema.sql` (172 líneas) | 11 tablas clínicas + RLS off |
| `db/legal_consents.sql` (93 líneas) | Tabla consents + 3 policies RLS |
| `db/fix_supabase_rls.sql` (52 líneas) | Fix RLS + columnas faltantes + policy anon legal_consents |

#### `assets/`

- `logos-light.png`, `logos-dark.png`, `logos-icon-light.png`, `logos-icon-dark.png`, `LOGO.png`
- `NM_icon.ico`
- `assets/fonts/` con 9 TTF (Plus Jakarta Sans 4 pesos + DM Sans 3 + JetBrains Mono 2)

#### `AI_SCRIPTS/` — Scripts auxiliares

20 scripts (build, captures, audits, tests, manuals). Ver [AI_SCRIPTS/README.md](AI_SCRIPTS/README.md).

Notables:
- `build_neuromood.py` — duplicado obsoleto del raíz (eliminar en F0)
- `generate_neuromood_manuals.py` — genera 2 PDFs manuales
- `qa_full_suite.py`, `smoke_test_runner.py` — QA
- `_capture_v3_screens.py` — 22 PNGs (11 pantallas × dark+light)
- `_test_color_regression.py`, `_test_visual_auto.py`, `_test_home_auto.py`, `_test_responsive_final.py` — tests visuales
- `_audit_scan.py`, `_audit_mockup_grid.py` — auditorías visuales

#### `REDESIGN/` — Legacy

123 archivos en `D` (git status). Pre-V3 mockups y capturas. **Decisión consciente del usuario:** delete. Commitear en F0.

### Apéndice B — Mapa de tablas Supabase actuales vs propuestas

#### Vigentes (db/supabase_schema.sql + legal_consents.sql)

| Tabla | Propósito | RLS |
|---|---|---|
| `patients` | Identidad + 4 perms | OFF |
| `mood_records` | Ánimo | OFF |
| `breathing_sessions` | Respiración | OFF |
| `thought_records` | TCC | OFF |
| `checklist_completions` | Tareas completadas | OFF |
| `timer_sessions` | Timer | OFF |
| `reminder_logs` | Recordatorios disparados | OFF |
| `assigned_tasks` | Tareas asignadas por profesional | OFF |
| `assigned_reminders` | Recordatorios asignados | OFF |
| `activity_bank` | Banco global actividades | OFF |
| `patient_activities` | Actividades personalizadas | OFF |
| `legal_consents` | Consentimientos auditables | ON con 3 policies |

#### Propuestas nuevas (Parte 5)

| Tabla | Propósito |
|---|---|
| `hub_config` | Config k/v global + por paciente |
| `hub_text_overrides` | Overrides de textos UI |
| `hub_module_meta` | Display name + descripción + chip + orden de módulos |
| `module_visibility` | Habilitar/deshabilitar módulos por paciente |
| `tcc_templates` | Plantillas TCC completas |
| `tcc_distortions` | Distorsiones (opcional separado o dentro de tcc_templates) |
| `routine_templates` | Plantillas rutinas |
| `patient_routine_template` | Asignación rutina → paciente |
| `breathing_presets_remote` | Presets respiración |
| `timer_presets_remote` | Presets timer |
| `support_messages` | Biblioteca mensajes apoyo |
| `activity_categories` | Categorías actividades configurables |
| `professional_messages` | Indicaciones profesional → paciente |
| `content_versions` | Versionado snapshots |
| `ia_audit_log` | Audit IA outputs |
| `ia_chat_history` | Persistencia chat IA |
| `professional_audit` | Audit cambios profesionales |

### Apéndice C — Mapa de tablas SQLite locales actuales vs propuestas

#### Vigentes ([shared/db.py:93-244](shared/db.py))

| Tabla | Propósito | En uso |
|---|---|---|
| `termometro` | Ánimo local | ✓ |
| `recordatorios` | Recordatorios locales | ✓ |
| `actividades_temporizador` | Timer local | ✓ |
| `pensamientos` | TCC local | ✓ |
| `respiracion` | Respiración local | ✓ |
| `checklist_tareas` | Tareas | ✓ |
| `checklist_completadas` | Completadas | ✓ |
| `checklist_notas_dia` | Nota del día | ✓ |
| `checklist_snapshot` | Snapshot diario | ✓ (parcial) |
| `activacion` | Resultados activación | ✓ |
| `activacion_actividades` | Banco local | ✓ |
| `recordatorios_log` | Log avisos disparados | ✓ |
| `config` | k/v general | ✓ |
| `mensajes_biblioteca` | Mensajes apoyo locales | **sin uso** |
| `activacion_config` | Config motor activación | ~ (limitado) |
| `activacion_perfil` | Perfil motor activación | **sin uso** |
| `timer_presets` | Presets timer locales | **sin uso UI** |
| `checklist_plantillas` | Plantillas rutina locales | **sin uso UI** |

#### Propuestas nuevas (cache de remoto)

| Tabla | Propósito |
|---|---|
| `remote_config_cache` | Cache de `hub_config` |
| `text_overrides_cache` | Cache de `hub_text_overrides` |
| `module_visibility_cache` | Cache de `module_visibility` |
| `tcc_template_cache` | Cache plantilla TCC activa |
| `routine_template_cache` | Cache plantilla rutina activa |
| `breathing_presets_cache` | Cache presets respiración |
| `timer_presets_cache` | Cache presets timer (reusar tabla existente con nuevos campos) |
| `support_messages_cache` | Cache mensajes (reusar `mensajes_biblioteca` existente) |
| `professional_messages_cache` | Cache indicaciones |

### Apéndice D — Glosario clínico

| Término | Definición operativa para el equipo de software |
|---|---|
| **TCC** | Terapia Cognitivo-Conductual. Enfoque psicoterapéutico que trabaja sobre la relación entre situaciones, pensamientos automáticos, emociones, y conductas. Las 4 pasos del wizard (Situación → Emoción → Pensamiento → Respuesta alternativa) son la columna vertebral del registro TCC. |
| **Distorsiones cognitivas** | Patrones de pensamiento sesgados que generan malestar (Catastrofización, Lectura mental, Filtro mental, Etiquetado, Debería, Personalización, Sobregeneralización, Descalificación, Pensamiento dicotómico, Magnificación). El módulo TCC las detecta por keywords ([registro_tcc_qt.py:79-103](app/modules/registro_tcc_qt.py)). |
| **Activación conductual** | Técnica que propone realizar actividades específicas (físicas, placer, social, maestría, autocuidado, cognitiva) para mejorar estado emocional. Implementada en `actividades_qt.py` con sugerencias por rango de ánimo. |
| **Refractario** | Pacientes que no responden a tratamientos convencionales. Población foco de NeuroMood. Incluye depresión mayor refractaria, TOC refractario, bipolar refractario, esquizofrenia, dolor crónico, Parkinson. |
| **TEC** | Terapia Electroconvulsiva. Tratamiento médico que aplica corriente eléctrica controlada al cerebro bajo anestesia. Usado en depresión mayor refractaria. Mencionado en Propuesta Base. |
| **Ketamina endovenosa** | Tratamiento experimental para depresión refractaria. Mencionado en Propuesta Base. |
| **Neuromodulación** | Conjunto de técnicas que modifican actividad cerebral (estimulación magnética transcraneal, estimulación cerebral profunda, etc.). Mencionado en Propuesta Base. |
| **Adherencia** | Grado de cumplimiento del paciente con un tratamiento o rutina. **Importante:** en este informe, decisión 7 explícitamente prohíbe usar adherencia con etiquetas tipo "riesgo" / "crítico" porque ausencia de uso de la app ≠ baja adherencia al tratamiento real. |
| **Consentimiento informado** | Proceso por el cual el paciente acepta el uso del producto con conocimiento de su alcance y limitaciones. Implementado vía `legal_consents` con versionado por hash + fecha + scope. |
| **Activación conductual conductual** | Sinónimo de la herramienta 8. El equipo NeuroMood usa este término en la Propuesta Base. |

### Apéndice E — Glosario técnico interno

**Nomenclatura de estado (CRÍTICO — aplicar consistentemente):**

| Término | Definición |
|---|---|
| **Implementado en código** | El código existe en el repo con sintaxis válida y lógica coherente leída. **NO significa que el runtime fue verificado.** Es el default para casi todas las fichas de módulos/vistas de este informe, ya que la auditoría fue por lectura. |
| **NO verificado en ejecución** | Complemento literal de "Implementado en código" — este informe es por lectura — runtime no se probó en Windows real ni con Supabase real ni con endpoint IA real ni con bandeja del SO. Antes de cualquier piloto, correr plan de QA Parte 10. |
| **NO VERIFICABLE SIN EJECUTAR** | Aspectos que ni siquiera por lectura pueden confirmarse — requieren correr la app. Incluye: animaciones (NMFocusArc, breath circle, theme crossfade, partículas mood ≥7), glow effects, winsound.Beep, notificaciones SO (winotify/plyer), SmartScreen, autostart Windows real, bandeja del sistema (pystray), IA endpoint en vivo (Groq/Gemini/OpenAI), RLS real de Supabase, instaladores empacados como EXE, payload externo (zip junto al installer), DPI scaling. |
| **Incompleto** | UI o lógica con partes faltantes confirmables por **lectura** (ej: botón sin handler, tabla creada sin uso). |
| **Roto / Con bug conocido** | Sólo se marca así si el bug es identificable por lectura del código o documentado explícitamente en docs internas (ej: bug 2026-05-18 en `_ProUninstWorker` ya corregido y documentado en AI_PROJECT_CONTEXT.md). |

**Glosario técnico de componentes:**

| Término | Definición |
|---|---|
| **NMModule** | Clase base en `shared/components_qt.py` de la que heredan los 7 módulos paciente. Provee `build_ui()`, `on_enter`, `on_leave`, `back_requested` signal, `set_context_title`. |
| **`_MODULE_MAP`** | Dict en `app/main_qt.py:55` que mapea `module_id` → `(módulo Python, clase)`. Permite carga dinámica con `importlib`. |
| **`_MODULE_CACHE`** | Cache de instancias para evitar reinicializar módulos al navegar. |
| **V3 design system** | Versión 3 del design system NeuroMood. Tokens en `shared/theme.py` (`V3_LIGHT`, `V3_DARK`, `V3_SPACE`, `V3_RADIUS`, `V3_SHADOWS`, `V3_GRADIENTS`). |
| **`hub_config`** (propuesto, F2.0) | Tabla única de configuración remota del Hub. Columnas: `scope` (TEXT) + `key` (TEXT) + `value` (JSONB) + `updated_at` + `updated_by` + `version`. Patrón 2 niveles según subsección 9.4.A. |
| **`scope`** | Valor de configuración: `'global'` (todo el equipo) o `'patient:<patient_id>'` (override individual). |
| **`t(key, default, patient_id=None)`** (propuesto, F2.0) | Util en `shared/remote_config.py` para lookup con jerarquía: `patient:<id>` → `global` → `default` hardcoded. |
| **Ánimo Loop** | Las 3 herramientas de la Propuesta Base conectadas por la variable ÁNIMO declarada por el paciente: Termómetro (registra) → Visualizador (visualiza) + Activación Conductual (consume). No es automatismo oculto: el paciente declara conscientemente, el profesional cura los rangos desde Hub. Ver subsección al inicio del informe. |
| **`rutina_modo`** (propuesto, F2.3) | Campo nuevo en `patients` con 3 valores: `solo_profesional` / `mixto` (default) / `solo_paciente`. Opción C de la decisión 2026-05-21. Reusa campo `origen` ya existente en `checklist_tareas`. |
| **`origen`** (existente, [shared/db.py:269](shared/db.py)) | Campo en `checklist_tareas` con valores `'manual'` (paciente) o `'profesional'`. Ya en uso por [shared/sync.py:215](shared/sync.py) e [hub/exportar.py:116](hub/exportar.py). Base del sistema opción C de rutina. |
| **Anon key** | Clave pública de Supabase con permisos limitados. Se distribuye en `.env`. RLS controla acceso fino. |
| **PBKDF2-SHA256** | Algoritmo de derivación de claves usado en `shared/identidad.py` con 100k iteraciones para hash de password local. Reusado en F3 para Modo privacidad del paciente. |
| **Sync bidireccional** | Patrón en `shared/sync.py`: export 6 streams clínicos → Supabase + import asignaciones/permisos/actividades. F2.0 lo extiende con `_importar_hub_config`. |
| **Visual QA** | Modo opt-in via env vars (`NM_VISUAL_QA=1`) que usa fixtures de `shared/visual_qa.py` en lugar de DB real. Útil para capturas. |
| **Daemon avisos** | Hilo daemon que revisa `recordatorios` cada 30s y dispara notificaciones Windows. |
| **Caption bar DWM** | API Windows para customizar la barra de título de la ventana (dark mode, color). |
| **F0.1 / F2.0** | Subfases agregadas en la decisión 2026-05-21. F0.1 = eliminación de tags semáforo del Hub (bloqueante de aprobación). F2.0 = patrón general `hub_config` 2 niveles + util + ConfigView reestructurada (base de toda configurabilidad). |

---

**Fin del informe.**

> Generado el 2026-05-20 sobre el commit `e33dc1f`. Para reproducir, leer en orden:
> 1. `Propuesta Base.pdf` (cliente)
> 2. `AI_PROJECT_CONTEXT.md` (estado vigente del proyecto)
> 3. `prompt maestro.txt` (qué pidió el usuario)
> 4. Este archivo (auditoría + diagnóstico + plan)
>
> Próximo paso esperado: discusión con cliente NeuroMood sobre orden de fases + decisión go/no-go de F0.





