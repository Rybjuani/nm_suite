# PROMPTS_CODEX_IMPLEMENTACION.md

> **Fecha:** 2026-05-21
> **Fuente:** [AUDITORIA_NEUROMOOD.md](AUDITORIA_NEUROMOOD.md) — fases F0 a F9
> **Para:** Codex (o cualquier agente que reciba prompts atómicos)
> **Regla de oro:** un prompt = una tarea concreta = un diff revisable. Cada bloque `###` es autocontenido. Copiar/pegar tal cual.

---

## Cómo usar este archivo

1. Identificá la fase actual del proyecto (F0 → F9). El orden recomendado está al final del archivo.
2. Elegí el prompt atómico (ej: `F0.1.A`). Cada prompt apunta a **un cambio chico y verificable**.
3. Copiá el bloque "Prompt para Codex" tal cual, sin agregar contexto.
4. Codex devuelve un diff. Revisar contra **Criterios de aceptación**.
5. Mergear cuando todos los criterios pasen.

**Si un prompt parece grande, partilo en sub-prompts antes de enviarlo.** Mejor 3 PRs chicos que 1 grande sin revisión.

---

## Convenciones globales (válidas para TODOS los prompts)

- **Repo:** `nm_suite` (Python 3.12 + PyQt6).
- **Estructura oficial:** `app/` (Suite), `hub/` (Hub), `shared/`, `db/`, `installers/`, `AI_SCRIPTS/`.
- **Contexto vigente:** [AI_PROJECT_CONTEXT.md](AI_PROJECT_CONTEXT.md) — leer antes de tocar áreas sensibles.
- **Auditoría:** [AUDITORIA_NEUROMOOD.md](AUDITORIA_NEUROMOOD.md) — referencia de decisiones clínicas y técnicas.
- **No tocar sin permiso explícito en el prompt:**
  - `db/legal_consents.sql` (versionado legal, decisión 5)
  - `installers/installer.py` líneas de consent (`LEGAL_DISCLAIMER_TEXT`, `DISCLAIMER_VERSION`, `PRIVACY_VERSION`)
  - `hub/ia_asistente.py` prompts del sistema (versionados en código, decisión 6)
  - `.env` / `SUPABASE_KEY` / `service_role`
- **Convención commit:** `<fase>: <título corto>`. Ej: `F0.1.A: eliminar tags semáforo Dashboard`.
- **Convención branch:** `feat/<fase>-<slug>` ej: `feat/f0.1.a-deshazte-tags-dashboard`.
- **Validación universal antes de PR:**
  - `python -m compileall app hub shared installers`
  - `BUILDER_NUEVO_RAPIDO.bat --dry-run` (o equivalente)
  - Smoke test runtime cuando aplique (apertura Suite/Hub sin crash).

---

## FASE 0 — Higiene + des-semáforo clínico (3-5 días)

### F0.1.A — Eliminar tags semáforo del Dashboard

**Prompt para Codex:**
> Eliminar tags "Adherencia alta", "Riesgo bajo", "Agenda al día" del Dashboard del NeuroMood Hub. Estas etiquetas hacen interpretación clínica automática sobre uso de la app y contradicen la decisión 7 del proyecto (sin semáforos clínicos). Reemplazarlas por información neutral descriptiva.
>
> En `hub/main_qt.py` `DashboardView` (aprox. líneas 171-389), ubicá la card destacada (`NMFeaturedCard`) y remové los chips/tags hardcoded con esas tres frases. Insertá en su lugar 4 KPIs neutrales construidos con datos existentes:
> - "Último registro: hace N días" (calcular vs `mood_records` más reciente).
> - "Tareas asignadas: N activas" (`assigned_tasks WHERE activa=true`).
> - "Recordatorios activos: N" (`assigned_reminders WHERE activa=true`).
> - "Próxima sesión: <texto libre o "—">" (placeholder hasta tener tabla de sesiones agendadas).
>
> No agregar lógica que interprete clínicamente al paciente. Solo datos descriptivos.

**Archivos permitidos:** `hub/main_qt.py`, `shared/visual_qa.py` (si tiene fixtures de tags).
**Archivos prohibidos:** `app/`, `installers/`, `db/`, `shared/db.py`, `shared/sync.py`, `shared/components_qt.py`, `shared/theme*`.
**Validación:**
```
grep -E "Adherencia alta|Riesgo bajo|Agenda al día" hub/main_qt.py
# debe devolver 0
python -m compileall hub
python hub/main_qt.py   # no debe crashear; render OK
```
**Criterios de aceptación:**
- 0 matches del grep en `hub/main_qt.py`.
- Dashboard abre sin errores con un paciente seleccionado.
- Los 4 KPIs muestran valores reales (o "—" si no hay datos).
- Visual QA fixtures (`shared/visual_qa.py:hub_patients`) actualizadas si contenían los tags.

---

### F0.1.B — Reemplazar filtro "Atención" en vista Pacientes

**Prompt para Codex:**
> En `hub/main_qt.py` `PacientesView` (aprox. líneas 400-557), eliminar el tab/filtro "Atención" que hoy usa el criterio interpretativo `adherence < 40%`. Reemplazarlo por **"Sin sincronización reciente"** con criterio neutral: paciente cuya `last_sync_date` es de hace más de 7 días.
>
> El filtro debe seguir siendo un pill clickeable en la barra superior junto a "Todos / Activos / Sin registros". Reusar el mismo componente de tab pill que ya existe.
>
> Importante: el dato `last_sync_date` ya se guarda local en `shared/db.py:guardar_config`. Para el Hub viene de columna `patients.last_sync_date` (agregar columna si no existe — coordinar con prompt F5.A si ya está en F5).

**Archivos permitidos:** `hub/main_qt.py`, `db/supabase_schema.sql` (solo si falta `last_sync_date` en `patients`).
**Archivos prohibidos:** `app/`, `installers/`, `shared/sync.py`.
**Validación:**
```
grep -E '"Atención"|adherence\s*<\s*40' hub/main_qt.py
# debe devolver 0
```
**Criterios de aceptación:**
- Tab "Atención" reemplazado por "Sin sincronización reciente".
- Criterio: `last_sync_date < hoy - 7 días`.
- Sin etiquetas tipo "riesgo/crítico/atención clínica".
- Si la columna `last_sync_date` no existía, se agrega con `ALTER TABLE patients ADD COLUMN IF NOT EXISTS last_sync_date TIMESTAMPTZ`.

---

### F0.2.A — Commit limpieza REDESIGN/ + scripts legacy

**Prompt para Codex:**
> El `git status` actual muestra 123 archivos en `D` bajo `REDESIGN/` (deletes sin commitear). Adicionalmente, hay scripts legacy sueltos en la raíz que deben moverse o eliminarse según `AI_PROJECT_CONTEXT.md` (regla "raíz limpia").
>
> Acciones:
> 1. Confirmar `git rm` de los archivos `D` bajo `REDESIGN/` y commitear con mensaje `chore(F0.2): commit deletes legacy REDESIGN/`.
> 2. Crear carpeta `AI_SCRIPTS/legacy/` (si no existe).
> 3. Mover (`git mv`) a `AI_SCRIPTS/legacy/`:
>    - `edit_script.py`
>    - `edit_script_avisos.py`
> 4. Mover `unificar.py` → `AI_SCRIPTS/dump_repo_for_ai.py` (rename incluido).
> 5. Mover `PLAN_REDISEÑO_FUENTE_DE_LA_VERDAD.txt` → `AI_SCRIPTS/notes/PLAN_REDISEÑO_FUENTE_DE_LA_VERDAD.txt` (crear `notes/` si falta).
> 6. Eliminar `descripcion y manuales desactualizados.txt` de la raíz (existen PDFs generados vigentes).
> 7. Verificar `.gitignore`: si no contiene `build.log`, `__pycache__/`, `_qa_output/` y `*.spec`, agregarlos.

**Archivos permitidos:** raíz del repo (mover/eliminar), `.gitignore`, `AI_SCRIPTS/`.
**Archivos prohibidos:** `app/`, `hub/`, `shared/`, `installers/`, `db/`.
**Validación:**
```
git status
# REDESIGN/ ya no debe aparecer
ls raíz | findstr /R "edit_script unificar PLAN_REDISEÑO descripcion"
# debe devolver 0 (Windows: dir /b | findstr ...)
```
**Criterios de aceptación:**
- `REDESIGN/` deletes commiteados.
- Raíz solo contiene estructura oficial documentada en `AI_PROJECT_CONTEXT.md` §6.
- `git status` limpio tras la operación.

---

### F0.2.B — Crear `BUILD_NEUROMOOD.bat` consolidado

**Prompt para Codex:**
> Hoy existen `BUILDER_NUEVO_RAPIDO.bat` y `BUILDER_VIEJO_LENTO.bat` en la raíz, pero `AI_PROJECT_CONTEXT.md` referencia un `BUILD_NEUROMOOD.bat` oficial que **no existe**. Hay además `build_neuromood.py` duplicado (raíz 20KB es el vigente, `AI_SCRIPTS/build_neuromood.py` 14KB es obsoleto).
>
> Acciones:
> 1. Crear `BUILD_NEUROMOOD.bat` en la raíz que delega al `build_neuromood.py` raíz. Soportar flags `--dry-run` y `--clean`.
> 2. Mantener `BUILDER_NUEVO_RAPIDO.bat` como alias temporal (que llame a `BUILD_NEUROMOOD.bat`) por compatibilidad, con un `echo` de deprecación.
> 3. Eliminar `BUILDER_VIEJO_LENTO.bat`.
> 4. Eliminar `AI_SCRIPTS/build_neuromood.py` (duplicado obsoleto).
> 5. Actualizar `AI_PROJECT_CONTEXT.md` §10 para documentar que `BUILD_NEUROMOOD.bat` ahora existe y es el oficial.

**Archivos permitidos:** raíz (`*.bat`, `build_neuromood.py`), `AI_SCRIPTS/build_neuromood.py` (delete), `AI_PROJECT_CONTEXT.md`.
**Archivos prohibidos:** todo lo demás.
**Validación:**
```
BUILD_NEUROMOOD.bat --dry-run
# debe imprimir comandos esperados, no compilar
```
**Criterios de aceptación:**
- `BUILD_NEUROMOOD.bat` existe y delega al `build_neuromood.py` raíz.
- `--dry-run` y `--clean` funcionan.
- `AI_SCRIPTS/build_neuromood.py` eliminado.
- `AI_PROJECT_CONTEXT.md` actualizado.

---

## FASE 2 — Configurabilidad remota desde Hub

### F2.0.A — Crear tabla `hub_config` en Supabase

**Prompt para Codex:**
> Crear el bloque base de configurabilidad remota: una sola tabla `hub_config` con scope `global` u `patient:<id>`, según subsección 9.4.A de `AUDITORIA_NEUROMOOD.md`.
>
> Crear archivo `db/hub_config_schema.sql` con:
> ```sql
> CREATE TABLE IF NOT EXISTS public.hub_config (
>     id           BIGSERIAL PRIMARY KEY,
>     scope        TEXT NOT NULL,
>     key          TEXT NOT NULL,
>     value        JSONB NOT NULL,
>     updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
>     updated_by   UUID,
>     version      INT NOT NULL DEFAULT 1,
>     UNIQUE (scope, key)
> );
> CREATE INDEX IF NOT EXISTS idx_hub_config_scope_key ON public.hub_config (scope, key);
>
> ALTER TABLE public.hub_config DISABLE ROW LEVEL SECURITY;
> -- (mismo modelo que tablas clínicas: anon key + entorno controlado)
> ```
>
> NO modificar `db/legal_consents.sql` ni `db/supabase_schema.sql`.
> NO ejecutar el SQL en Supabase desde el código (eso es deploy manual). Solo crear el archivo .sql + documentar en `AI_PROJECT_CONTEXT.md` §6 que existe.

**Archivos permitidos:** `db/hub_config_schema.sql` (nuevo), `AI_PROJECT_CONTEXT.md`.
**Archivos prohibidos:** todo lo demás.
**Validación:**
```
test -f db/hub_config_schema.sql && echo OK
# Validar SQL con psql --dry-run si se tiene acceso a Supabase test
```
**Criterios de aceptación:**
- Archivo SQL creado con sintaxis válida Postgres.
- Sin RLS habilitado en `hub_config` (consistente con tablas clínicas del proyecto).
- Unique `(scope, key)` presente.
- Documentación actualizada.

---

### F2.0.B — Util `shared/remote_config.py`

**Prompt para Codex:**
> Crear `shared/remote_config.py` con la función `t(key, default, patient_id=None)` que implementa la jerarquía `patient:<id>` → `global` → `default` hardcoded, según subsección 9.4.A de `AUDITORIA_NEUROMOOD.md`.
>
> Requisitos:
> 1. Cache local en SQLite: nueva tabla `remote_config_cache (scope TEXT, key TEXT, value TEXT, fetched_at TEXT, PRIMARY KEY (scope, key))`. Agregar el `CREATE TABLE IF NOT EXISTS` a `shared/db.py:inicializar_tablas()`.
> 2. La función `t()` lee primero del cache local. Lookup orden:
>    - `scope = 'patient:<patient_id>'` si patient_id no es None
>    - `scope = 'global'`
>    - `default` hardcoded (último recurso).
> 3. Valores en `hub_config.value` son JSONB; en cache local se serializa como JSON string. `t()` deserializa antes de devolver.
> 4. Función adicional `refresh_from_supabase(patient_id)` que descarga `hub_config` scope=global + scope=patient:<id> y refresca cache. Llamada desde `shared/sync.py` (prompt F2.0.C).
> 5. Si Supabase no está disponible: log warn + usar cache local existente + si tampoco hay cache, devolver `default`.
> 6. Cero panics: cualquier error de red/parse cae al `default`.
>
> NO importar PyQt6 desde `remote_config.py` — debe ser librería pura (Suite + Hub la consumen).

**Archivos permitidos:** `shared/remote_config.py` (nuevo), `shared/db.py` (solo `inicializar_tablas` para agregar tabla cache).
**Archivos prohibidos:** todo lo demás. Especialmente NO tocar `shared/sync.py` aquí (eso es F2.0.C).
**Validación:**
```
python -c "from shared.remote_config import t; print(t('test.key', 'default'))"
# Sin crashear; debe devolver 'default'
```
**Criterios de aceptación:**
- `t(key, default)` y `t(key, default, patient_id='X')` funcionan.
- Cache local creada y se persiste entre llamadas.
- Sin importes Qt.
- Tests opcional: agregar `AI_SCRIPTS/_test_remote_config.py` con 5 casos básicos (default, global, override, error de red, JSON inválido).

---

### F2.0.C — Extender `shared/sync.py` con `_importar_hub_config`

**Prompt para Codex:**
> Extender [shared/sync.py](shared/sync.py) siguiendo el patrón existente de `_importar_permisos`, `_importar_actividades`, etc. Agregar:
>
> ```python
> def _importar_hub_config(sb, patient_id: str):
>     """Descarga hub_config scope='global' + scope='patient:<id>' y cachea local."""
>     # SELECT scope, key, value FROM hub_config WHERE scope IN ('global', 'patient:<id>')
>     # INSERT OR REPLACE en remote_config_cache local
> ```
>
> Y llamarla desde `sync_completo()` y `verificar_asignaciones()` ya existentes.
>
> Reusar el patrón de try/except + acceso a `sb.table().select().eq().execute()` ya presente en el archivo.

**Archivos permitidos:** `shared/sync.py`.
**Archivos prohibidos:** todo lo demás.
**Validación:**
```
python -c "from shared.sync import _importar_hub_config; print('OK')"
python -m compileall shared
```
**Criterios de aceptación:**
- Función `_importar_hub_config(sb, patient_id)` presente con la firma indicada.
- Llamada agregada a `sync_completo()` y `verificar_asignaciones()`.
- Sigue el mismo patrón silencioso (try/except local) que el resto.
- Smoke test: forzar `sync_completo()` con cuenta test, verificar que el cache local se actualiza.

---

### F2.0.D — Reestructurar `ConfigView` del Hub en 2 secciones

**Prompt para Codex:**
> Reestructurar `ConfigView` de [hub/main_qt.py](hub/main_qt.py) (aprox. líneas 562-707) en 2 secciones verticales:
>
> 1. **Sección "Configuración del equipo" (scope=global):** placeholder con texto "Aquí van las configuraciones globales del equipo (textos, plantillas, presets). Próximamente: editores específicos por área." + un botón "Sincronizar configuración" que llama a `shared.remote_config.refresh_from_supabase(None)`.
> 2. **Sección "Configuración por paciente" (scope=patient:<id>):** placeholder con texto "Para configurar un paciente individual, ir a Pacientes → seleccionar paciente → sub-tab Configuración (próximamente)."
>
> Las cards de conexión Supabase, apariencia (tema), seguridad y log de sync **se mantienen** abajo, sin cambios.
>
> Reusar `NMSettingsSection` de [shared/components_qt.py](shared/components_qt.py). No crear componentes nuevos.

**Archivos permitidos:** `hub/main_qt.py`.
**Archivos prohibidos:** `shared/components_qt.py` (si necesitás un nuevo widget, parar y avisar), `app/`, `installers/`.
**Validación:**
```
python hub/main_qt.py
# ConfigView abre con 2 secciones nuevas + las existentes
```
**Criterios de aceptación:**
- 2 secciones nuevas visibles arriba.
- Botón "Sincronizar configuración" hace la llamada (puede ser stub).
- Tema/sync/idioma existentes intactos.

---

### F2.1.A — Schemas Supabase para entidades complejas (NO en `hub_config`)

**Prompt para Codex:**
> Crear `db/feature_schemas.sql` con las tablas para entidades que NO van en `hub_config` (porque tienen lifecycle propio, FKs, o estructura compleja). Schema mínimo:
>
> ```sql
> -- Plantillas TCC (4 steps + 8 emotions + N distortions)
> CREATE TABLE IF NOT EXISTS public.tcc_templates (
>     id BIGSERIAL PRIMARY KEY,
>     name TEXT NOT NULL,
>     scope TEXT NOT NULL DEFAULT 'global', -- 'global' o 'patient:<id>'
>     steps JSONB NOT NULL,         -- [{order, title, prompt, hint, required}]
>     emotions JSONB NOT NULL,      -- [{label, icon, color_token}]
>     distortions JSONB NOT NULL,   -- [{label, keywords, category, icon}]
>     tip_text TEXT,
>     version INT DEFAULT 1,
>     updated_at TIMESTAMPTZ DEFAULT now()
> );
>
> -- Plantillas de rutina (secciones + items)
> CREATE TABLE IF NOT EXISTS public.routine_templates (
>     id BIGSERIAL PRIMARY KEY,
>     name TEXT NOT NULL,
>     scope TEXT NOT NULL DEFAULT 'global',
>     sections JSONB NOT NULL,  -- [{key, label, items: [{descripcion, categoria, dificultad}]}]
>     version INT DEFAULT 1,
>     updated_at TIMESTAMPTZ DEFAULT now()
> );
>
> -- Asignación de plantilla rutina a paciente
> CREATE TABLE IF NOT EXISTS public.patient_routine_template (
>     patient_id TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
>     template_id BIGINT REFERENCES routine_templates(id),
>     assigned_at TIMESTAMPTZ DEFAULT now(),
>     PRIMARY KEY (patient_id)
> );
>
> -- Presets remotos respiración
> CREATE TABLE IF NOT EXISTS public.breathing_presets_remote (
>     id BIGSERIAL PRIMARY KEY,
>     scope TEXT NOT NULL DEFAULT 'global',
>     name TEXT NOT NULL,                     -- ej "4-7-8", "Box 4-4-4-4"
>     fase_in INT NOT NULL,
>     fase_hold INT DEFAULT 0,
>     fase_out INT NOT NULL,
>     fase_hold_after INT DEFAULT 0,
>     duracion_min_default INT DEFAULT 5,
>     activa BOOLEAN DEFAULT TRUE,
>     orden INT DEFAULT 0,
>     UNIQUE (scope, name)
> );
>
> -- Presets remotos timer
> CREATE TABLE IF NOT EXISTS public.timer_presets_remote (
>     id BIGSERIAL PRIMARY KEY,
>     scope TEXT NOT NULL DEFAULT 'global',
>     name TEXT NOT NULL,
>     duracion_seg INT NOT NULL,
>     categoria TEXT DEFAULT '',
>     activo BOOLEAN DEFAULT TRUE,
>     orden INT DEFAULT 0,
>     UNIQUE (scope, name)
> );
>
> -- Biblioteca de mensajes (respaldo + remoto)
> CREATE TABLE IF NOT EXISTS public.support_messages (
>     id BIGSERIAL PRIMARY KEY,
>     scope TEXT NOT NULL DEFAULT 'global',
>     categoria TEXT NOT NULL,    -- "medicacion", "hidratacion", etc
>     mensaje TEXT NOT NULL,
>     activa BOOLEAN DEFAULT TRUE
> );
>
> -- Audit log IA
> CREATE TABLE IF NOT EXISTS public.ia_audit_log (
>     id BIGSERIAL PRIMARY KEY,
>     patient_id TEXT,
>     called_at TIMESTAMPTZ DEFAULT now(),
>     provider TEXT,
>     model TEXT,
>     fn_name TEXT,              -- "resumir_evolucion", "sugerir_acciones", etc
>     prompt_user TEXT,
>     prompt_system TEXT,
>     output TEXT,
>     error TEXT
> );
>
> -- Persistencia chat IA global
> CREATE TABLE IF NOT EXISTS public.ia_chat_history (
>     id BIGSERIAL PRIMARY KEY,
>     patient_id TEXT,
>     created_at TIMESTAMPTZ DEFAULT now(),
>     role TEXT NOT NULL,       -- 'user' o 'assistant'
>     content TEXT NOT NULL
> );
>
> ALTER TABLE public.tcc_templates           DISABLE ROW LEVEL SECURITY;
> ALTER TABLE public.routine_templates       DISABLE ROW LEVEL SECURITY;
> ALTER TABLE public.patient_routine_template DISABLE ROW LEVEL SECURITY;
> ALTER TABLE public.breathing_presets_remote DISABLE ROW LEVEL SECURITY;
> ALTER TABLE public.timer_presets_remote    DISABLE ROW LEVEL SECURITY;
> ALTER TABLE public.support_messages        DISABLE ROW LEVEL SECURITY;
> ALTER TABLE public.ia_audit_log            DISABLE ROW LEVEL SECURITY;
> ALTER TABLE public.ia_chat_history         DISABLE ROW LEVEL SECURITY;
>
> -- ALTER patients (campo nuevo para opción C, F2.3)
> ALTER TABLE public.patients ADD COLUMN IF NOT EXISTS rutina_modo TEXT DEFAULT 'mixto'
>     CHECK (rutina_modo IN ('solo_profesional', 'mixto', 'solo_paciente'));
> ```
>
> NO ejecutar en Supabase desde código. Solo crear el archivo + agregar referencia en `AI_PROJECT_CONTEXT.md` §6.

**Archivos permitidos:** `db/feature_schemas.sql` (nuevo), `AI_PROJECT_CONTEXT.md`.
**Archivos prohibidos:** `db/legal_consents.sql`, `db/supabase_schema.sql`, `db/fix_supabase_rls.sql`.
**Validación:** sintaxis SQL válida Postgres (manual o con `psql -f` contra DB test).
**Criterios de aceptación:**
- 8 tablas nuevas + 1 ALTER `patients`.
- RLS deshabilitado en todas (consistente con resto clínico).
- Sin tocar tablas existentes salvo el ALTER.

---

### F2.1.B — Tablas SQLite cache locales

**Prompt para Codex:**
> Extender `shared/db.py:inicializar_tablas()` para crear las tablas cache locales correspondientes a F2.1.A. Agregar al `executescript()`:
>
> ```sql
> CREATE TABLE IF NOT EXISTS tcc_templates_cache (
>     id INTEGER PRIMARY KEY,
>     scope TEXT NOT NULL,
>     name TEXT NOT NULL,
>     payload TEXT NOT NULL,    -- JSON serializado (steps+emotions+distortions+tip)
>     version INTEGER DEFAULT 1,
>     fetched_at TEXT NOT NULL,
>     UNIQUE (scope, name)
> );
>
> CREATE TABLE IF NOT EXISTS routine_templates_cache (
>     id INTEGER PRIMARY KEY,
>     scope TEXT NOT NULL,
>     payload TEXT NOT NULL,
>     fetched_at TEXT NOT NULL
> );
>
> CREATE TABLE IF NOT EXISTS breathing_presets_cache (
>     id INTEGER PRIMARY KEY,
>     scope TEXT NOT NULL,
>     name TEXT NOT NULL,
>     payload TEXT NOT NULL,
>     UNIQUE (scope, name)
> );
>
> CREATE TABLE IF NOT EXISTS timer_presets_cache (
>     id INTEGER PRIMARY KEY,
>     scope TEXT NOT NULL,
>     name TEXT NOT NULL,
>     payload TEXT NOT NULL,
>     UNIQUE (scope, name)
> );
>
> CREATE TABLE IF NOT EXISTS support_messages_cache (
>     id INTEGER PRIMARY KEY,
>     scope TEXT NOT NULL,
>     categoria TEXT NOT NULL,
>     mensaje TEXT NOT NULL
> );
> ```
>
> Migración: si en una DB existente faltan estas tablas, el `IF NOT EXISTS` las crea en boot. No tocar tablas existentes.

**Archivos permitidos:** `shared/db.py`.
**Archivos prohibidos:** todo lo demás.
**Validación:**
```
python -c "from shared.db import inicializar_tablas; inicializar_tablas(); print('OK')"
```
**Criterios de aceptación:**
- 5 tablas nuevas creadas con `IF NOT EXISTS`.
- Sin alterar tablas existentes.
- Migración idempotente (correr 2 veces no rompe).

---

### F2.2.A — Suite Timer lee presets remotos (con fallback)

**Prompt para Codex:**
> Modificar [app/modules/timer_qt.py](app/modules/timer_qt.py) líneas 71-76 (`PRESETS` hardcoded) para leer presets desde `timer_presets_cache` local. Si no hay datos en cache (offline o primer arranque), usar fallback hardcoded.
>
> Cambios:
> 1. Nueva función `_load_presets()` en el módulo que:
>    - Lee primero `timer_presets_cache WHERE scope='patient:<patient_id>'` (override individual).
>    - Si vacío, lee `WHERE scope='global'`.
>    - Si vacío, devuelve los hardcoded `[("5 min", 300), ("10 min", 600), ("25 min", 1500), ("45 min", 2700)]`.
> 2. Al hacer build de UI, llamar `_load_presets()` y mostrar la lista resultante.
> 3. El permiso `perm_temporizador_manual` (leído de `config` local vía `shared.db.leer_config`) ahora controla si el input "Custom (1-120 min)" está visible/habilitado. Por defecto `True` para no romper.
>
> NO eliminar los hardcoded — quedan como fallback. NO tocar lógica del countdown.

**Archivos permitidos:** `app/modules/timer_qt.py`.
**Archivos prohibidos:** `shared/db.py`, `shared/sync.py` (el sync de presets es prompt aparte).
**Validación:**
```
python app/main_qt.py
# Abrir Timer → si DB tiene presets en cache, deben verse; si no, los 4 default
```
**Criterios de aceptación:**
- Si `timer_presets_cache` vacía, comportamiento idéntico al actual.
- Si tiene datos scope=global, se ven esos presets.
- Si tiene datos scope=patient:<id>, prevalecen.
- Input custom respeta `perm_temporizador_manual`.

---

### F2.2.B — Hub editor de presets timer

**Prompt para Codex:**
> Crear UI en el Hub para que el profesional defina presets de timer (decisión 2026-05-21: Propuesta Base ítem 3 — el equipo delimita actividades terapéuticas).
>
> Donde:
> - Nueva sub-pantalla en `hub/pacientes_qt.py` → `_TabAsignar` (líneas aprox 454-561): agregar una tercera card "Presets de timer (override individual)".
> - Sección equivalente global en `hub/main_qt.py` `ConfigView` → "Configuración del equipo" (de F2.0.D).
>
> Funcionalidad:
> - Lista de presets (`name` + `duracion_seg` + `categoria`).
> - Botones: agregar, editar, eliminar, toggle activo.
> - Selector scope: si está en ConfigView del equipo → scope=global; si está en detalle paciente → scope=patient:<id>.
> - Toggle `perm_temporizador_manual` por paciente (lee/escribe `patients.perm_temporizador_manual`).
> - Escribe en Supabase `timer_presets_remote` con upsert.
>
> Reusar `NMCard`, `NMButton`, `NMInput`, `NMSettingsSection` ya existentes.

**Archivos permitidos:** `hub/pacientes_qt.py`, `hub/main_qt.py`.
**Archivos prohibidos:** `app/`, `shared/components_qt.py`.
**Validación:** flujo end-to-end: crear preset → forzar sync en Suite del paciente test → ver preset en módulo Timer.
**Criterios de aceptación:**
- CRUD funcional contra `timer_presets_remote`.
- Toggle `perm_temporizador_manual` por paciente.
- UI consistente con tabs existentes.

---

### F2.2.C — Suite Avisos lee biblioteca de mensajes remota

**Prompt para Codex:**
> Modificar [app/modules/avisos_qt.py](app/modules/avisos_qt.py) para que **los mensajes sugeridos** al crear un recordatorio vengan de `support_messages_cache` (interpretación Propuesta Base ítem 2 — el equipo determina los mensajes de apoyo).
>
> Cambios:
> 1. En `_NuevoAvisoPanel` agregar un combo/autocomplete que pre-sugiera mensajes por categoría, leyendo de `support_messages_cache`.
> 2. El paciente sigue pudiendo escribir libre si `perm_recordatorios_manual=True` (default). Si `False`, solo puede elegir de la lista.
> 3. La categorización inferida automática actual ([avisos_qt.py:79-102](app/modules/avisos_qt.py) `_categorize()`) **se mantiene** como fallback visual cuando no hay match en biblioteca.
>
> NO tocar el daemon ni la lógica de disparo de notificaciones.

**Archivos permitidos:** `app/modules/avisos_qt.py`.
**Archivos prohibidos:** `app/avisos_daemon.py`, `shared/`.
**Validación:** insertar 3 mensajes en `support_messages_cache`, abrir Avisos en Suite → ver sugeridos.
**Criterios de aceptación:**
- Combo de mensajes sugeridos visible.
- Si `perm_recordatorios_manual=False`, paciente solo puede elegir, no escribir libre.
- Daemon de notificaciones intacto.

---

### F2.2.D — Hub editor biblioteca de mensajes

**Prompt para Codex:**
> En `hub/main_qt.py` `ConfigView` → sección "Configuración del equipo" (de F2.0.D), agregar card "Biblioteca de mensajes de apoyo".
>
> Funcionalidad:
> - Lista paginada de mensajes (categoría + mensaje + activo).
> - Filtro por categoría: "Salud / Hidratación / Calma / Actividad / Comida / Trabajo / Descanso / Terapia / Recordatorio".
> - CRUD contra `support_messages` Supabase, scope=global por default.
> - Botón "Importar default" que carga los mensajes hardcoded actuales de `avisos_qt.py:_categorize` como semilla.

**Archivos permitidos:** `hub/main_qt.py`.
**Archivos prohibidos:** `app/`, `shared/`.
**Validación:** crear 3 mensajes desde Hub → forzar sync Suite → ver en combo (F2.2.C).
**Criterios de aceptación:**
- CRUD funcional.
- Importar default semilla los 9 grupos actuales.
- Scope=global por default; scope=patient:<id> opcional vía toggle.

---

### F2.3.A — Suite Rutina respeta `rutina_modo`

**Prompt para Codex:**
> Modificar [app/modules/rutina_qt.py](app/modules/rutina_qt.py) para implementar el sistema de 3 estados de la decisión 2026-05-21 (opción C):
>
> 1. Leer `rutina_modo` desde `config` local (sync trae `patients.rutina_modo` y lo guarda en `config.rutina_modo`). Default `'mixto'`.
> 2. Comportamiento por modo:
>    - `solo_profesional`: ocultar botón "+ Agregar tarea" en cada sección. El paciente solo marca/desmarca lo que vino del Hub.
>    - `mixto` (default): mostrar botón "+ Agregar tarea" como hoy.
>    - `solo_paciente`: igual que mixto, pero no llegan tareas profesionales (es responsabilidad del sync, no del módulo — acá solo asegurar que NO se rompe si la lista está vacía).
> 3. **Badge "Personal"** visible al lado de cada tarea con `origen='manual'`. Reusar un pill chico con tono `text3`. El campo `origen` ya existe en `checklist_tareas` ([shared/db.py:269](shared/db.py)).
>
> NO romper la lógica actual de marcado, ring de progreso, ni nota del día.

**Archivos permitidos:** `app/modules/rutina_qt.py`.
**Archivos prohibidos:** `shared/db.py`, `shared/sync.py`.
**Validación:**
```
# Setear manualmente:
python -c "from shared.db import guardar_config; guardar_config('rutina_modo', 'solo_profesional')"
# Abrir Suite → módulo Rutina → botón "+ Agregar tarea" no debe aparecer
```
**Criterios de aceptación:**
- 3 modos visibles según el config local.
- Badge "Personal" en tareas `origen='manual'`.
- Lógica existente intacta (marcado, ring, nota).

---

### F2.3.B — Sync importa `rutina_modo` y plantillas rutina

**Prompt para Codex:**
> Extender [shared/sync.py](shared/sync.py) siguiendo el patrón existente:
>
> 1. Nueva función `_importar_rutina_modo(sb, patient_id)`:
>    - SELECT `rutina_modo` FROM `patients` WHERE patient_id = ?
>    - Guardar en `config.rutina_modo` vía `guardar_config()`.
> 2. Nueva función `_importar_routine_template(sb, patient_id)`:
>    - SELECT del JOIN `patient_routine_template` con `routine_templates`.
>    - Si hay plantilla asignada, insertar/actualizar las tareas en `checklist_tareas` con `origen='profesional'` (reusar lógica de `_importar_tareas_asignadas`).
> 3. Llamar ambas desde `sync_completo()` y `verificar_asignaciones()`.

**Archivos permitidos:** `shared/sync.py`.
**Archivos prohibidos:** todo lo demás.
**Validación:** setear `rutina_modo='solo_profesional'` en Supabase, forzar sync, leer `config.rutina_modo` local.
**Criterios de aceptación:**
- Función creada y llamada desde los hooks de sync.
- Sin romper sync existente.

---

### F2.3.C — Hub editor de plantillas rutina + selector modo

**Prompt para Codex:**
> Agregar a `hub/pacientes_qt.py` `_TabAsignar` (líneas 454-561) una nueva card "Plantilla de rutina".
>
> Funcionalidad:
> 1. Selector de plantilla (combo poblado de `routine_templates WHERE scope IN ('global', 'patient:<id>')`).
> 2. Selector de modo: 3 radio buttons (`solo_profesional` / `mixto` / `solo_paciente`).
> 3. Editor simple drag-drop con 3 secciones (Mañana/Tarde/Noche) + items (descripción + categoría + dificultad). Crear plantilla nueva o editar existente.
> 4. Botón "Asignar a este paciente" → UPSERT `patient_routine_template` + UPDATE `patients.rutina_modo`.
> 5. Lista lateral muestra plantillas globales y específicas del paciente.
>
> Reusar componentes existentes. No inventar widgets nuevos.

**Archivos permitidos:** `hub/pacientes_qt.py`.
**Archivos prohibidos:** `app/`, `shared/components_qt.py`.
**Validación:** crear plantilla "Rutina post-TEC" con 3 tareas mañana, asignar a paciente test con modo `solo_profesional` → sync → Suite muestra solo esas 3 tareas, botón "+" oculto.
**Criterios de aceptación:**
- CRUD de plantillas funcional.
- Asignación + modo escriben en Supabase.
- UX consistente con `_TabAsignar` actual.

---

### F2.4.A — Editor de plantillas TCC en Hub

**Prompt para Codex:**
> Crear [hub/editors/tcc_template_editor.py](hub/editors/tcc_template_editor.py) (crear carpeta `hub/editors/` si no existe) con un editor visual de plantillas TCC.
>
> Estructura UI:
> 1. Lista lateral de plantillas (scope=global + scope=patient:<id>).
> 2. Panel principal con tabs: "Pasos (4)" / "Emociones (8 default)" / "Distorsiones (10 default)" / "Tip terapéutico".
> 3. Cada tab tiene editor inline + preview en vivo a la derecha que renderiza un mini-stepper (reusar `NMTCCStepper`).
> 4. Botones: Guardar (upsert en `tcc_templates`), Restaurar default, Asignar a paciente.
>
> El módulo Suite ([app/modules/registro_tcc_qt.py](app/modules/registro_tcc_qt.py)) NO se toca en este prompt — solo el editor Hub. La integración Suite es prompt aparte (F2.5).
>
> Integrar el editor desde `hub/pacientes_qt.py` `_TabAsignar` con un botón "Editar plantilla TCC".

**Archivos permitidos:** `hub/editors/` (nuevo), `hub/pacientes_qt.py`.
**Archivos prohibidos:** `app/`, `shared/`, `hub/ia_asistente.py`.
**Validación:** crear plantilla custom con 1 paso menos, guardarla, ver en lista.
**Criterios de aceptación:**
- Editor visual funcional contra `tcc_templates`.
- Preview en vivo.
- Sin tocar Suite (eso queda para F2.5).

---

### F2.4.B — Editor de text overrides genérico

**Prompt para Codex:**
> Crear `hub/editors/text_overrides_editor.py` con un editor key/value para `hub_config` con prefijo `text.*`.
>
> Funcionalidad:
> 1. Lista de keys conocidas (semilla): `text.home.greeting`, `text.home.subtitle`, `text.home.modules_eyebrow`, `text.module.animo.title`, `text.module.animo.desc`, ... (~15 keys iniciales).
> 2. Para cada key: mostrar `default` hardcoded + input "Override global" + input "Override por paciente" (selector paciente).
> 3. Preview en vivo con un mini-render del texto.
> 4. Botón "Guardar" → upsert en `hub_config`.
> 5. Validación: longitud máxima 200 chars por default.

**Archivos permitidos:** `hub/editors/`, `hub/main_qt.py` (para integrar en ConfigView).
**Archivos prohibidos:** `app/`, `shared/`.
**Validación:** cambiar greeting global → forzar sync Suite → ver greeting nuevo en Home.
**Criterios de aceptación:**
- ~15 keys editables.
- Upsert global y por paciente.
- Validación longitud.

---

### F2.5 — Sprints de migración por módulo (A-H)

> Esta sub-fase NO es un prompt único — son **8 sprints** que migran strings hardcoded a `t(key, default)` por módulo. Ejecutar de a uno por PR para mantener diffs revisables.

#### F2.5.A — Migrar `home_qt.py`

**Prompt para Codex:**
> En [app/home_qt.py](app/home_qt.py) reemplazar strings hardcoded de UI por llamadas `t(key, default)` de `shared.remote_config`. Strings a migrar:
> - "TUS MÓDULOS" → `t("text.home.modules_eyebrow", "TUS MÓDULOS")`
> - "BIENESTAR HOY" → `t("text.home.wellbeing_eyebrow", "BIENESTAR HOY")`
> - "Registrá tu ánimo\npara comenzar" → `t("text.home.wellbeing_default", "Registrá tu ánimo\npara comenzar")`
> - "PRÓXIMA SESIÓN" → `t("text.home.next_session_eyebrow", "PRÓXIMA SESIÓN")`
> - "Sin sesión\nprogramada" → `t("text.home.next_session_default", "Sin sesión\nprogramada")`
> - Greetings ("Buenos días," / "Buenas tardes," / "Buenas noches,") → claves por momento del día.
> - "NeuroMood Suite" brand mark.
>
> Importar `from shared.remote_config import t` arriba del archivo. NO eliminar los defaults hardcoded; el `default` del `t()` los cubre.

**Archivos permitidos:** `app/home_qt.py`.
**Archivos prohibidos:** todo lo demás.
**Validación:**
```
python -m compileall app
python app/main_qt.py
# Home abre idéntico (porque los defaults coinciden)
# Insertar override en hub_config con key='text.home.modules_eyebrow' value='"NUEVO TÍTULO"'
# Forzar sync, reabrir Home, debe verse "NUEVO TÍTULO"
```
**Criterios de aceptación:**
- Comportamiento idéntico sin override.
- Override se refleja tras sync.

#### F2.5.B-H — Plantilla para el resto de módulos

> Repetir el patrón de F2.5.A para los archivos:
> - **B:** `app/modules/animo_qt.py` (eyebrows + nota placeholder + frases post-registro)
> - **C:** `app/modules/registro_tcc_qt.py` (4 paso titles + tips + emotion labels — leer también de `tcc_templates_cache`)
> - **D:** `app/modules/respiracion_qt.py` (FASES + PRESETS — leer de `breathing_presets_cache`)
> - **E:** `app/modules/rutina_qt.py` (SECCIONES — leer de `routine_templates_cache`)
> - **F:** `app/modules/actividades_qt.py` (CATEGORIAS + labels)
> - **G:** `app/modules/timer_qt.py` (eyebrows + labels — presets ya migrados en F2.2.A)
> - **H:** `app/modules/avisos_qt.py` (eyebrows + labels — mensajes ya migrados en F2.2.C)
>
> Cada uno = un PR. Cada uno = mismo formato que F2.5.A (defaults hardcoded preservados como argumento de `t()`).

---

### F2.6 — Constructor de informes paramétrico

**Prompt para Codex:**
> Modificar [hub/exportar.py](hub/exportar.py) `exportar_pdf()` para aceptar un parámetro `secciones: list[str]` (default: todas).
>
> Las 6 secciones actuales (Ánimo, Respiración, TCC, Checklist, Timer, Recordatorios) se vuelven opcionales. Cada una solo se renderiza si está en `secciones`.
>
> En `hub/pacientes_qt.py` `_TabRegistros` botón "Exportar PDF" → abrir modal con checklist de secciones + rango fechas + nombre archivo + botón Exportar.

**Archivos permitidos:** `hub/exportar.py`, `hub/pacientes_qt.py`.
**Archivos prohibidos:** `app/`, `shared/`.
**Validación:** exportar con solo "Ánimo + TCC" → PDF tiene esas 2 secciones, no las otras 4.
**Criterios de aceptación:**
- Modal de selección visible.
- PDF refleja selección.
- Default (sin selección) preserva comportamiento actual.

---

## FASE 3 — Suite madura (Modo privacidad + Settings + mini-visualizador)

### F3.A — Modo privacidad: lock screen al abrir Suite

**Prompt para Codex:**
> Crear `app/privacy_lock_qt.py` con una pantalla `PrivacyLockScreen(QWidget)` que pide PIN antes de mostrar el Home.
>
> Comportamiento:
> 1. Lee `config.privacy_lock_enabled` (0/1). Si 0, no hace nada — `main_qt.py` salta directo a Home.
> 2. Si 1, muestra una pantalla minimalista con:
>    - Logo + saludo ("Bienvenido, {nombre}")
>    - Input PIN (NMInput con echoMode Password)
>    - Botón "Desbloquear" + link "Olvidé mi PIN" (recovery vía email Supabase).
> 3. Compara hash PBKDF2 contra `config.privacy_pin_hash`. Reusar funciones de [shared/identidad.py](shared/identidad.py) (`_hash_pwd`, `_verify_pwd`).
> 4. 3 intentos fallidos → bloqueo de 5 minutos (guardar `config.privacy_lock_until` con timestamp).
> 5. Recovery: dispara `supabase.auth.reset_password_for_email(email)` y muestra confirmación.
>
> Integrar en [app/main_qt.py](app/main_qt.py): tras `inicializar_tablas()` y antes de mostrar Home, si `privacy_lock_enabled=1` mostrar `PrivacyLockScreen` modal. Solo seguir al Home si pasa.

**Archivos permitidos:** `app/privacy_lock_qt.py` (nuevo), `app/main_qt.py`, `shared/identidad.py` (solo extender si falta función).
**Archivos prohibidos:** `installers/`, `db/`, `hub/`.
**Validación:**
```
python -c "from shared.db import guardar_config; from shared.identidad import _hash_pwd; guardar_config('privacy_lock_enabled', '1'); guardar_config('privacy_pin_hash', _hash_pwd('1234'))"
python app/main_qt.py
# Debe pedir PIN. Con "1234" entra. Con cualquier otro → error.
```
**Criterios de aceptación:**
- Lock screen funcional.
- 3 intentos + bloqueo 5min.
- Recovery vía email Supabase.
- Si lock desactivado → comportamiento actual sin cambios.

---

### F3.B — Settings panel en Home Suite + mover autostart

**Prompt para Codex:**
> Crear un `_SettingsPanel` en [app/home_qt.py](app/home_qt.py) accesible desde un ícono ⚙ en el header del Home.
>
> Secciones del panel:
> 1. **Inicio con Windows:** toggle ON/OFF. Reusar `_get_autostart` y `_set_autostart` de [app/avisos_daemon.py:320-352](app/avisos_daemon.py) (importar, no reescribir).
> 2. **Modo privacidad:** toggle "Pedir PIN al abrir" + botón "Configurar / cambiar PIN" → dialog que pide PIN nuevo, lo hashea con `shared.identidad._hash_pwd`, guarda en `config`.
> 3. **Apariencia:** selector dark/light (reusar `ThemeManager.switch_mode`).
>
> Cambios adicionales:
> - En [app/modules/avisos_qt.py](app/modules/avisos_qt.py): **remover** la card de autostart Windows. Dejar un link/label informativo "Configurá inicio con Windows en Ajustes generales del Home" por 1 release como shim de compatibilidad.
> - NO tocar `app/avisos_daemon.py` (sigue leyendo el mismo registry HKCU).

**Archivos permitidos:** `app/home_qt.py`, `app/modules/avisos_qt.py`.
**Archivos prohibidos:** `app/avisos_daemon.py`, `shared/`.
**Validación:**
```
python app/main_qt.py
# Home → ícono ⚙ → ver 3 secciones. Toggle autostart debe escribir HKCU igual que antes.
# Abrir módulo Avisos → no debe haber card de autostart, solo el shim link.
```
**Criterios de aceptación:**
- Panel funcional con las 3 secciones.
- Autostart se controla desde Home, no desde Avisos.
- Daemon sin cambios.

---

### F3.C — Mini-visualizador semanal en Home Suite (F1)

**Prompt para Codex:**
> Agregar al Home de la Suite ([app/home_qt.py](app/home_qt.py)) una sección **"Tu semana"** con un mini gráfico de ánimo de los últimos 7 días, debajo del grid de módulos.
>
> Implementación:
> 1. Nueva `_WeeklyMoodSection(QWidget)` con altura ~160px.
> 2. Reusar `NMWaveChart` ya importado en `animo_qt.py:264` (mover a `shared/components_qt.py` si todavía está privado en `animo_qt.py`).
> 3. Datos: misma query que `animo_qt._get_weekly_series()` (extraer a `shared/utils.py` como helper reusable).
> 4. Click sobre la sección → abre módulo Ánimo (`on_module_open("animo")`).
> 5. Configurabilidad: leer `t("home.weekly_mood_visible", "true")` para mostrar/ocultar.

**Archivos permitidos:** `app/home_qt.py`, `shared/components_qt.py` (si hay que mover `NMWaveChart` a público), `shared/utils.py`, `app/modules/animo_qt.py` (solo para extraer helper).
**Archivos prohibidos:** `installers/`, `db/`, `hub/`.
**Validación:** abrir Home con datos en `termometro` → ver curva semanal; click navega a Ánimo.
**Criterios de aceptación:**
- Sección visible bajo el grid.
- Click navega correctamente.
- Si no hay datos, mostrar empty state ("Registrá tu ánimo para ver tu semana").

---

## FASE 4 — Hub completo

### F4.A — Gestión real de pacientes desde Hub

**Prompt para Codex:**
> El botón "+ Nuevo paciente" en [hub/main_qt.py:453-455](hub/main_qt.py) no tiene handler. Implementar el flujo completo.
>
> Cambios:
> 1. ALTER `patients` (schema en `db/feature_schemas.sql`): agregar `activo BOOLEAN DEFAULT TRUE`, `creado_por TEXT`, `notas_profesional TEXT`.
> 2. Dialog modal `NuevoPacienteDialog(QDialog)` con campos:
>    - Nombre completo (required).
>    - Email (opcional).
>    - Notas internas profesional (opcional, textarea).
> 3. Al guardar: server genera `patient_id` UUID + `install_code` (8 chars alfanuméricos). INSERT en `patients` con `activo=true`, `creado_por=<auth.uid()>`.
> 4. Tras guardar, muestra modal de éxito con el `install_code` + botón "Copiar al portapapeles". El profesional lo manda al paciente fuera de la app.
> 5. PacientesView refresca la lista.
> 6. Filtro adicional: tab pill "Inactivos" muestra `activo=false`.

**Archivos permitidos:** `hub/main_qt.py`, `db/feature_schemas.sql` (extender con ALTER).
**Archivos prohibidos:** `app/`, `installers/`.
**Validación:** crear paciente test → verificar fila en `patients` con UUID + install_code → instalar Suite en VM con ese install_code → entra OK.
**Criterios de aceptación:**
- Handler funcional.
- UUID + install_code generados server-side.
- Copiar al portapapeles.
- Pacientes inactivos filtrables.

---

### F4.B — Audit log IA + persistencia chat

**Prompt para Codex:**
> Instrumentar [hub/ia_asistente.py](hub/ia_asistente.py) para loggear cada llamada IA en `ia_audit_log` Supabase.
>
> Cambios:
> 1. En `_llamar(prompt, sistema, on_result, on_error)` (líneas 230-286): al inicio insertar registro placeholder en `ia_audit_log` (estado pendiente). Al recibir result/error, UPDATE con el output o error + provider + model usados.
> 2. Patient_id se pasa como parámetro opcional a las funciones públicas (`resumir_evolucion`, `sugerir_acciones`, `generar_tarea`, `autocompletar_actividad`). Default `None`.
> 3. En `hub/pacientes_qt.py` `_TabIA` (786-1023) y `hub/main_qt.py` `IAAssistantView` (712-911): pasar `patient_id` del paciente actual.
> 4. Persistencia chat global: cada mensaje user/assistant en `IAAssistantView` se inserta en `ia_chat_history`. Al abrir la vista, cargar los últimos N (50) mensajes del paciente activo.
>
> **NO modificar** los prompts del sistema (decisión 6, versionados en código).

**Archivos permitidos:** `hub/ia_asistente.py`, `hub/pacientes_qt.py`, `hub/main_qt.py`.
**Archivos prohibidos:** `app/`, `shared/`, prompts del sistema dentro de `ia_asistente.py` (las constantes `_IDIOMA`, `sistema=...`).
**Validación:** llamar `resumir_evolucion()` con paciente test → verificar fila en `ia_audit_log` con prompt + output + provider.
**Criterios de aceptación:**
- Audit log captura prompt + output + provider + model + patient_id.
- Chat global persiste y se restaura al reabrir.
- Sin cambios en los prompts del sistema.

---

### F4.C — Panel de actividad reciente neutral (reemplazo final de tags semáforo)

**Prompt para Codex:**
> Tras F0.1.A removimos tags clínicos del Dashboard con KPIs simples. Ahora construimos el reemplazo definitivo: una card "Actividad reciente" por paciente, descriptiva y sin interpretación.
>
> Crear en `hub/main_qt.py` `DashboardView` (o `_FeaturedCard`) un componente `_RecentActivityCard(QWidget)` con:
> - Última sincronización (timestamp humanizado).
> - Último registro de ánimo (fecha + puntaje numérico, sin emoji interpretativo).
> - Tareas completadas hoy / asignadas activas.
> - Recordatorios disparados últimos 7 días / activos.
> - Sesiones de respiración / timer / TCC últimos 7 días (contadores).
>
> Sin etiquetas tipo "riesgo", "atención", "adherencia alta/baja". Solo datos descriptivos.

**Archivos permitidos:** `hub/main_qt.py`.
**Archivos prohibidos:** `app/`, `installers/`, `db/`.
**Validación:**
```
grep -iE "riesgo|adherencia|atención clínica|crítico" hub/main_qt.py
# debe devolver 0 matches como labels de UI (sí pueden quedar comentarios)
```
**Criterios de aceptación:**
- Card visible para el paciente seleccionado.
- Solo datos descriptivos.
- Cumple decisión 7.

---

## FASE 5 — Sync, permisos y seguridad

### F5.A — Auditar RLS Supabase + columna `last_sync_date`

**Prompt para Codex:**
> 1. Agregar a `db/supabase_schema.sql` el ALTER `patients ADD COLUMN IF NOT EXISTS last_sync_date TIMESTAMPTZ` (usado por F0.1.B).
> 2. Crear `db/rls_audit_2026-05.sql` con:
>    - Documento de cada tabla y su estado RLS actual.
>    - Política sugerida si se quiere endurecer (sin aplicar — solo documentar).
> 3. En `shared/sync.py` `sync_completo()`: actualizar `patients.last_sync_date = now()` al finalizar.

**Archivos permitidos:** `db/supabase_schema.sql`, `db/rls_audit_2026-05.sql` (nuevo), `shared/sync.py`.
**Archivos prohibidos:** `db/legal_consents.sql`.
**Validación:** `sync_completo()` → verificar columna `patients.last_sync_date` actualizada en Supabase.
**Criterios de aceptación:**
- Columna agregada idempotente.
- Documento de RLS por tabla.
- Sync escribe `last_sync_date`.

---

### F5.B — Sanear logs: no PII en `crash_log` ni `hub.log`

**Prompt para Codex:**
> Auditar `shared/crash_log.py` y los lugares donde se llama `_log.error(...)` en el proyecto. Asegurar que **no se loggee PII** (emails, patient_id, contenido de notas, registros, mensajes IA).
>
> Cambios:
> 1. En `shared/crash_log.py` agregar `_PII_PATTERNS = [r"@\S+\.\S+", r"\bpat_[A-Za-z0-9]{8,}\b"]` y un wrapper `redact(text)` que reemplaza por `<redacted>`.
> 2. Reemplazar usos de `_log.error(f"... {email} ...")` por `_log.error(redact(f"... {email} ..."))`.
> 3. Documentar en `AI_PROJECT_CONTEXT.md` §8 que los logs son redacted.

**Archivos permitidos:** `shared/crash_log.py`, cualquier archivo con `_log.error` que reciba PII (greppear primero).
**Archivos prohibidos:** `installers/installer.py` líneas de consent.
**Validación:** correr Suite con email test → buscar email en `%APPDATA%/NeuroMood/logs/` → no debe aparecer.
**Criterios de aceptación:**
- `redact()` implementada y usada.
- Logs limpios de PII (verificado por grep en logs locales tras correr smoke).

---

### F5.C — Sync con anon key restringida

**Prompt para Codex:**
> Hoy el anon key tiene acceso a todas las tablas porque RLS está deshabilitado. Documentar y validar que el comportamiento con anon key sea el esperado.
>
> Crear `AI_SCRIPTS/_audit_anon_key.py` que:
> 1. Conecta con la anon key.
> 2. Hace SELECT a cada tabla clínica + INSERT a `legal_consents` (debe fallar sin auth).
> 3. Reporta qué operaciones funcionan y cuáles no.
> 4. Genera `_qa_output/anon_key_audit.txt` con el resultado.

**Archivos permitidos:** `AI_SCRIPTS/_audit_anon_key.py` (nuevo).
**Archivos prohibidos:** todo lo demás.
**Validación:** correr el script → archivo generado con matriz de permisos.
**Criterios de aceptación:**
- Script funcional.
- Reporte legible.
- Sin modificar nada en runtime.

---

## FASE 6 — QA e instaladores production-ready

### F6.A — Smoke tests CI

**Prompt para Codex:**
> Crear `AI_SCRIPTS/smoke_test_runner.py` (si no existe expandirlo) con:
>
> 1. `python -m compileall app hub shared installers`
> 2. Importar todos los módulos sin crashear: `import app.main_qt`, `import hub.main_qt`, los 7 módulos paciente, los 4 instaladores.
> 3. Inicializar DB local: `shared.db.inicializar_tablas()` debe correr 2 veces sin error (idempotencia).
> 4. Lectura mock de `t()` con default → debe devolver default.
> 5. Test del sync sin red: forzar `_get_client()` a devolver None → `sync_completo()` no debe crashear.
> 6. Salida exit 0 si todo OK, exit 1 si algo falla.

**Archivos permitidos:** `AI_SCRIPTS/smoke_test_runner.py`.
**Archivos prohibidos:** todo lo demás.
**Validación:** `python AI_SCRIPTS/smoke_test_runner.py` → exit 0.
**Criterios de aceptación:**
- Cubre los 6 checks.
- Exit codes correctos.
- Salida legible (no traceback ruidoso si pasa).

---

### F6.B — Modo offline en consent (cola de sync)

**Prompt para Codex:**
> Hoy `installers/installer.py` bloquea la instalación si Supabase no responde al insertar `legal_consents`. Hacer que esto sea **resiliente**:
>
> 1. Si la inserción remota falla por red: guardar el consent local (ya pasa hoy en `legal_consent.json`).
> 2. Encolar el INSERT pendiente en un archivo `%APPDATA%/NeuroMood/pending_consent.json`.
> 3. La Suite, al abrirse, al hacer `sync_al_abrir()`, intenta reenviar el consent pendiente. Si tiene éxito, borra el archivo.
> 4. Si tras 7 días el consent sigue pendiente, mostrar warning en Suite ("Aún no se pudo registrar tu consentimiento en la nube. Verificá tu conexión.").
>
> NO cambiar `LEGAL_DISCLAIMER_TEXT`, `DISCLAIMER_VERSION`, `PRIVACY_VERSION` ni el flujo de hashes.

**Archivos permitidos:** `installers/installer.py`, `shared/sync.py`, `app/main_qt.py`.
**Archivos prohibidos:** `db/legal_consents.sql`, prompts del sistema IA.
**Validación:** desconectar red durante install → instala OK con pending; reconectar → al abrir Suite, fila aparece en `legal_consents`.
**Criterios de aceptación:**
- Install no se bloquea por red.
- Pending consent se reenvía al recuperar red.
- Warning a 7 días.

---

### F6.C — Firma de código (documento de proceso)

**Prompt para Codex:**
> No automatizar la firma (requiere certificado EV). Crear `AI_SCRIPTS/notes/SIGNING_PROCESS.md` con:
>
> 1. Pasos para firmar los 6 EXEs con `signtool.exe` (Windows SDK).
> 2. Comandos exactos (placeholders para path del certificado y timestamp server).
> 3. Verificación con `signtool verify /pa <exe>`.
> 4. Smoke test post-firma: instalar en VM Windows fresh, verificar que SmartScreen no alerta.

**Archivos permitidos:** `AI_SCRIPTS/notes/SIGNING_PROCESS.md` (nuevo).
**Archivos prohibidos:** todo lo demás.
**Validación:** documento existe y es ejecutable manualmente.
**Criterios de aceptación:**
- Pasos completos y reproducibles.
- Comandos exactos.

---

## FASES 7-9 — Proceso, no implementación

Estas fases **no requieren prompts de Codex** porque son actividades operativas / clínicas:

- **F7 Piloto clínico:** elegir 3-5 pacientes reales, instalar producto, recolectar feedback estructurado.
- **F8 Ajustes post-feedback:** iterar sobre la matriz de Parte 5 del informe usando los editores ya creados en F2. Si aparece algo nuevo que requiere código, **se vuelve a este archivo y se crea un prompt nuevo**.
- **F9 Release 1.0:** regenerar manuales PDF con `AI_SCRIPTS/generate_neuromood_manuals.py`, etiquetar versión, deploy.

---

## Orden recomendado de ejecución

```
F0.1.A    ← 🔴 BLOQUEANTE — Dashboard sin tags semáforo
F0.1.B    ← 🔴 BLOQUEANTE — Pacientes sin filtro "Atención"
F0.2.A    ← Limpieza REDESIGN/ + scripts legacy
F0.2.B    ← BUILD_NEUROMOOD.bat consolidado
─────────────────────────────────────────────────────
F2.0.A    ← Schema hub_config
F2.0.B    ← Util remote_config.py
F2.0.C    ← Sync extendido
F2.0.D    ← ConfigView reestructurada (2 secciones)
─────────────────────────────────────────────────────
F2.1.A    ← Schemas Supabase entidades complejas
F2.1.B    ← Caches SQLite locales
─────────────────────────────────────────────────────
F2.2.A    ← Suite Timer lee remotos
F2.2.B    ← Hub editor presets timer
F2.2.C    ← Suite Avisos lee biblioteca
F2.2.D    ← Hub editor biblioteca mensajes
─────────────────────────────────────────────────────
F2.3.A    ← Suite Rutina respeta rutina_modo
F2.3.B    ← Sync importa rutina_modo + plantillas
F2.3.C    ← Hub editor plantillas rutina + selector modo
─────────────────────────────────────────────────────
F2.4.A    ← Editor plantillas TCC
F2.4.B    ← Editor text overrides genérico
─────────────────────────────────────────────────────
F4.A      ← Gestión real pacientes
F4.B      ← Audit log IA + persistencia chat
F4.C      ← Panel actividad reciente neutral (cierre F0.1)
─────────────────────────────────────────────────────
F3.A      ← Modo privacidad lock screen
F3.B      ← Settings panel Home + autostart move
F3.C      ← Mini-visualizador semanal Home
─────────────────────────────────────────────────────
F2.5.A-H  ← Migración por módulo (8 PRs)
F2.6      ← Constructor informes paramétrico
─────────────────────────────────────────────────────
F5.A      ← RLS audit + last_sync_date
F5.B      ← Logs sin PII
F5.C      ← Anon key audit
─────────────────────────────────────────────────────
F6.A      ← Smoke tests CI
F6.B      ← Consent offline + cola sync
F6.C      ← Doc firma código
─────────────────────────────────────────────────────
F7        ← Piloto clínico (no es prompt Codex)
F8        ← Ajustes (volver a este archivo si surge código)
F9        ← Release 1.0
```

---

## Cómo agregar un prompt nuevo a este archivo

Si durante F7-F8 surgen cambios de código no previstos, agregar un bloque con el mismo formato:

```markdown
### F<fase>.<letra> — <título corto>

**Prompt para Codex:**
> <descripción autocontenida>

**Archivos permitidos:** <lista>
**Archivos prohibidos:** <lista>
**Validación:** <comando o pasos>
**Criterios de aceptación:**
- <bullet>
```

Mantener cada prompt **chico, verificable y aislado**. Si necesitás más de 5 archivos modificados o más de 200 líneas de diff esperadas, partilo.
