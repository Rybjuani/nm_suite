# HANDOFF — Plan de remediación nm_suite para agente GLM-5.2

## Estado del repositorio

**Repo:** `github.com/Rybjuani/nm_suite`
**HEAD de main al momento del handoff:** buscar con `git log --oneline -5`
**Stack:** Python 3.12, PyQt6, Supabase, SQLite, pytest + pytest-qt

## Fixes ya aplicados y mergeados a main (NO tocar)

| ID | Commit | Descripción |
|---|---|---|
| S0-9 | `5246a59` | Fixture `qapp` en `tests/conftest.py` |
| S0-1 | `8b4f19a` | 4 tablas inexistentes en `_fetch_patient_data` |
| S0-2-bis | `e903d34` | No persistir `emocion/valencia/intensidad` en Ánimo |
| RA-1 | `455a476` | Retirar `energia` del contrato activo (Actividades) |
| RA-2 | `d2cc96f` | Persistir `categoria` real del preset en Timer |
| RA-5 | `3107c3e` | `skill_version` desde `DBT_SKILLS`, no hardcodeado |
| RA-6 | `485cb1a` | Retirar `reflexion_ia` del sync y Hub SELECT |
| RB-5 | `87d7953` | `sync_inmediato_background` en `actividades_qt._register_result` |
| RB-1 | (pendiente merge) | `generar_asignacion` recibe `self._nombre` en 3 subtabs |

## Metodología obligatoria

1. **UI-first:** para cada fix, verificar primero si existe widget visible que captura el campo. No asumir que un campo es "capturado" solo porque hay una columna SQLite o un comentario que lo dice.
2. **No agregar UI nueva** salvo que el owner lo pida explícitamente.
3. **No eliminar columnas** del schema SQLite ni de Supabase. Conservar por compatibilidad con datos históricos. Solo hacer nullable si es necesario.
4. **No mezclar fixes** en un mismo patch. Un patch por ID.
5. **Generar patches con `git diff --cached --binary`** contra el commit exacto de main donde se aplica. No editar hunks manualmente. Verificar con `git apply --check` en clone fresco antes de entregar.
6. **`py_compile`** antes de cada entrega: `python3 -m py_compile <archivo_modificado>`.
7. **Tests:** sin duplicar `pytest_plugins` o `QT_QPA_PLATFORM` (ya están en `tests/conftest.py`). Usar `encoding="utf-8"` en todos los `open()`. Eliminar imports sin uso.
8. **Mock de Supabase:** usar `MagicMock()` con cadena fluida completa. Ejemplo:
   ```python
   sb = MagicMock()
   query = sb.table.return_value
   query.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []
   query.select.return_value.eq.return_value.execute.return_value.data = []
   query.upsert.return_value.execute.return_value.data = []
   ```
9. **Fraseología:** usar "queda pendiente hasta el próximo sync" (no "tarda hasta 7 días").

## Fixes pendientes

### Fase 2 — Fixear Hub (Grupo B restante)

#### RB-2 — Métricas fantasma del dashboard

**Problema:** `hub/main_qt.py` línea ~465 lee `p.get("adherence", 0.75)` — siempre cae al default 0.75 porque `_cargar_pacientes` (línea ~972) solo selecciona 5 columnas de `patients` y nunca computa adherencia. Lo mismo aplica a `mood_data_7d` (siempre None), `last_session` (siempre ""), `next_session` (siempre "").

**Fix:**
- Eliminar los defaults fantasma: cambiar `p.get("adherence", 0.75)` → `p.get("adherence")` y mostrar "Sin datos" si es None.
- O computar las métricas reales en `_cargar_pacientes` (más trabajo, requiere queries a `mood_records`, `breathing_sessions`, etc.).

**Recomendación del owner:** confirmar si prefiere eliminar defaults (rápido) o computar reales (más trabajo).

**Archivos:** `hub/main_qt.py`
**Tests:** verificar que el dashboard no muestra 0.75 cuando no hay datos.

#### RB-3 — `recordatorios_log` no se lee en el Hub

**Problema:** `shared/sync.py` exporta `recordatorios_log` → `reminder_logs` en Supabase, pero `hub/pacientes_qt.py:_fetch_patient_data` NO lee `reminder_logs`. Solo lee `assigned_reminders` (config del profesional, no telemetría de avisos disparados). El profesional es ciego a la telemetría de avisos.

**Fix:**
- Agregar un 9no fetch en `_fetch_patient_data` que lea `reminder_logs` con `SELECT fecha,hora,mensaje,cerrado` limitado a 50 registros.
- Guardar en `datos["avisos_disparados"]` (nueva key).

**Archivos:** `hub/pacientes_qt.py`
**Tests:** mock de Supabase que captura el `.table("reminder_logs")` call.

#### RB-4 — `recordatorios.activo` no se sincroniza

**Problema:** cuando el paciente completa un aviso (`avisos_qt._on_completar`), se hace `UPDATE recordatorios SET activo=0` local pero ese cambio nunca llega al Hub. No hay `_exportar_recordatorios` en `shared/sync.py`.

**Fix:**
- Crear `_exportar_recordatorios(sb, patient_id, desde)` en `shared/sync.py` que lea `recordatorios` y haga upsert a una tabla Supabase. **Problema:** no hay tabla Supabase para `recordatorios` (solo `assigned_reminders` que es del profesional). Decisión de diseño: ¿crear tabla nueva `patient_reminders` o reutilizar `assigned_reminders` con un campo `completada`?
- Llamar `sync_inmediato_background()` desde `avisos_qt._on_completar` (hoy no lo hace).

**Archivos:** `shared/sync.py`, `app/modules/avisos_qt.py`, posiblemente `db/supabase_schema.sql`
**Requiere decisión del owner** sobre el modelo de datos.

#### RB-6 — `avisos_qt._on_completar` no llama `sync_inmediato_background`

**Problema:** igual que RB-5 pero para Avisos. `_on_completar` hace `UPDATE recordatorios SET activo=0` pero no dispara sync.

**Fix:**
- Agregar `try: from shared.sync import sync_inmediato_background; sync_inmediato_background() except: pass` después del UPDATE.
- Mismo patrón que RB-5.

**Archivos:** `app/modules/avisos_qt.py`
**Tests:** mismo patrón que RB-5 (mock de sync, verificar call_count == 1).

#### RB-7 — `hub/exportar.py` sin botón en UI + mismatch de keys

**Problema:** `hub/exportar.py` (505 LOC) tiene `exportar_pdf()` y `generar_constancia_consentimiento()` pero ningún botón en el Hub las invoca. Además, `_generar()` lee keys del dict `datos` que no coinciden con las que produce `_fetch_patient_data`:
- `exportar._generar` lee `datos["resp"]`, `datos["pens"]`, `datos["reclog"]`
- `_fetch_patient_data` produce `datos["respiracion"]`, `datos["tcc"]`, `datos["recordatorios"]`

Aún si se cableara el botón, 3 de 7 secciones del PDF quedarían vacías.

**Fix:**
- Unificar keys: cambiar `exportar._generar` para que lea las mismas keys que produce `_fetch_patient_data`.
- Cablear un botón "Exportar PDF" en el header del detalle del paciente (`hub/pacientes_qt.py`).
- Agregar secciones faltantes: `actividades` y `avisos` (hoy el PDF solo tiene 7 de 8 módulos).

**Archivos:** `hub/exportar.py`, `hub/pacientes_qt.py`
**Tests:** generar PDF con paciente de test poblado, verificar que tiene 8 secciones con datos.

### Fase 2 — Aislamiento por tabla en sync (Grupo D)

#### RD-1 — `sync_inmediato`/`sync_completo` no aislan por tabla

**Problema:** `shared/sync.py` líneas ~996-1003 y ~1221-1228 llaman a los 8 `_exportar_*` sin try/except individual. Si `_exportar_animo` lanza, se saltan los 5 exportadores siguientes.

**Fix:**
- Envolver cada `_exportar_*` en su propio `try/except Exception as e: _log.warning(...)`.

**Archivos:** `shared/sync.py`
**Tests:** mock que hace que un `_exportar_*` lance y verifica que los demás siguen ejecutándose.

### Fase 3 — IA real (Grupo C)

#### RC-1 — `generar_resumen_paciente` solo recibe conteos

**Problema:** `hub/ia_asistente.py:636` `generar_resumen_paciente` construye un prompt que solo incluye `len()` de cada módulo. El LLM recibe "Animo: 5 registros, promedio 6.2/10" pero no recibe `nota`, `pensamiento`, `actividad`, `malestar_antes/despues`, `resultado`, etc.

**Fix:**
- Reescribir el prompt para incluir hasta 5 registros recientes por módulo con contenido textual truncated a 200 chars.
- Usar los campos textuales que ya llegan al dict `datos` gracias a S0-1.

**Archivos:** `hub/ia_asistente.py`
**Tests:** mock de LLM que verifica que el prompt incluye contenido textual real.

#### RC-2 — Sin ventana temporal explícita en el prompt de IA

**Problema:** `_fetch_patient_data` usa `.limit(30)` pero no `WHERE fecha >= hoy - 30d`. Un paciente con 30 registros repartidos en 2 años se presenta igual que uno con 30 en el último mes.

**Fix:**
- Agregar `WHERE fecha >= ?` con fecha de hace 30 días en cada fetch de `_fetch_patient_data`.

**Archivos:** `hub/pacientes_qt.py`
**Tests:** verificar que el SELECT incluye el filtro de fecha.

#### RC-3 — `assigned_reminders` sin límite

**Problema:** `pacientes_qt.py` fetch de `assigned_reminders` no tiene `.limit()`. Si un paciente acumula cientos de recordatorios, todos entran al prompt.

**Fix:** Agregar `.limit(50)`.

**Archivos:** `hub/pacientes_qt.py` (ya tiene `.limit(50)` si RB-3 se aplicó — verificar)

### Fase 4 — PDF (depende de RB-7)

Ver RB-7 arriba. Una vez cableado el botón y unificadas las keys, agregar:
- Gráficos simples (línea de evolución de ánimo, barras de actividad por módulo).
- Campos extendidos TCC y de ánimo que ya se persisten pero no se muestran.

### Fase 5 — Limpieza de cadáveres (Grupo E)

#### RE-1 — 7 tablas SQLite cadáver

Eliminar CREATE TABLE de: `checklist_snapshot`, `mensajes_biblioteca`, `activacion_config`, `activacion_perfil`, `timer_presets` (local), `checklist_plantillas`, `checklist_notas_dia`.

**Archivos:** `shared/db.py`

#### RE-2 — Clases muertas

Eliminar: `_InsightCard`, `_StepCard`, `_CategoriesCard`, `_CategoryRingTile`, `_ActivityRow`.

#### RE-3 — 3 funciones IA cadáver

Eliminar: `resumir_evolucion`, `sugerir_acciones`, `generar_tarea` de `hub/ia_asistente.py`.

#### RE-4 — Tabla `ia_chat_history` cadáver

Eliminar tabla + policies de `db/feature_schemas.sql` y `db/secure_rls_hardening.sql`.

#### RE-5 — `breathing_presets_cache` y `breathing_presets_remote`

Feature F2.4 no cableada. El cache se llena desde Supabase pero `respiracion_qt.py` no lo consume. Decidir: cablear o eliminar.

#### RE-6 — Test roto `test_dbt_module.py`

Importa `_PracticeHistoryRow` y `_load_history` que no existen (vista Historial de DBT eliminada). Arreglar o eliminar.

#### RE-7 — Docstrings mentirosos

En los 8 módulos Suite. Lista completa en `reaudit_A_*.md`, `reaudit_B_*.md`, `reaudit_C_*.md`.

#### RE-8 — Imports huérfanos

~50 entre todos los módulos. Lista completa en los reportes de reauditoría.

#### RE-9 — 7 widgets ocultos en Respiración

`_calm_badge`, `_calm_bar`, `_calm_pct_lbl`, `_calm_card`, `_calm_eyebrow`, `_chrono_meta`, `_range_lbl` se actualizan cada tick sin estar visibles.

## Documentación de referencia

Los siguientes archivos están en `/home/z/my-project/download/`:

- `REAUDITORIA_UI_first_nm_suite.md` — matriz completa campo por campo
- `RA_1_a_9_analisis_individual.md` — análisis individual de cada campo
- `reaudit_A_animo_respiracion_tcc.md` — reporte parcial módulos 1-3
- `reaudit_B_rutina_actividades_timer.md` — reporte parcial módulos 4-6
- `reaudit_C_dbt_avisos.md` — reporte parcial módulos 7-8
- `reaudit_D_hub_y_sync.md` — reporte parcial Hub + sync
- `reaudit_E_schemas_y_revalidacion.md` — reporte parcial schemas + revalidación
- `AUDITORIA_PROFUNDA_nm_suite.md` — auditoría original (puede estar desactualizada respecto a los fixes aplicados)

## Orden recomendado de ejecución

1. **RB-1** (mergear el patch pendiente si no se mergeó)
2. **RB-6** (sync_inmediato en avisos — trivial, mismo patrón que RB-5)
3. **RD-1** (aislamiento por tabla en sync — protege todo el pipeline)
4. **RB-2** (métricas fantasma — requiere decisión del owner)
5. **RB-3** (recordatorios_log invisible en Hub)
6. **RB-4** (recordatorios.activo no se sincroniza — requiere decisión del owner)
7. **RC-1 + RC-2 + RC-3** (IA real — depende de que RB-3 esté hecho para tener datos completos)
8. **RB-7** (PDF — depende de que las keys estén unificadas)
9. **Fase 5** (limpieza de cadáveres — puede hacerse en paralelo)

## Reglas críticas para el agente

1. **Clonar fresco** antes de cada patch: `git clone --depth 10 --single-branch https://github.com/Rybjuani/nm_suite.git`
2. **Verificar HEAD** con `git log --oneline -5` antes de aplicar cambios.
3. **`py_compile`** antes de entregar: `python3 -m py_compile <archivo>`.
4. **`git apply --check`** en clone fresco antes de entregar el patch.
5. **`git diff --cached --binary`** para generar el patch — nunca editar hunks manualmente.
6. **Tests sin `import pytest`** si no se usa (los fixtures `qapp` y `isolated_db` vienen de `conftest.py`).
7. **`encoding="utf-8"`** en todos los `open()`.
8. **Un patch por fix** — no mezclar.
9. **No asumir** que un campo es capturado sin verificar el widget real en el código.
10. **No eliminar columnas** del schema — solo hacer nullable si es necesario.