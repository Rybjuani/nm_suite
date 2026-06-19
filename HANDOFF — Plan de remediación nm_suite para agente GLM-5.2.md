# HANDOFF — Plan de remediación nm_suite para agente local GLM-5.2

## 1. Propósito

Este documento reemplaza el flujo anterior basado en un agente web que entregaba patches.

El agente debe trabajar **directamente sobre el repositorio local real**, editar archivos, ejecutar verificaciones y dejar evidencia auditable. No debe reconstruir diffs manualmente, generar archivos `.patch`, usar `git apply` ni crear clones auxiliares por cada fix.

---

## 2. Entorno canónico

- **Sistema operativo:** Windows 10
- **Shell obligatorio:** PowerShell nativo
- **Repositorio local:** `C:\Users\nosom\Desktop\nm_suite`
- **Remoto:** `https://github.com/Rybjuani/nm_suite`
- **Repositorio GitHub:** `Rybjuani/nm_suite`
- **Rama principal:** `main`
- **Python:** `.\.venv\Scripts\python.exe`
- **Stack:** Python 3.12, PyQt6, SQLite, Supabase, pytest y pytest-qt
- **SHA de `main` al generar este handoff:** `8aeb3898c4d319fc4f426a9feb5d596f693b39bb`
- **Último fix funcional mergeado:** RB-1 en `1e82e2fdc4a225010e1da3f918a12d10aba1921d`

El SHA anterior es una referencia histórica. Antes de cada tarea debe verificarse el estado real de `main` y `origin/main`.

---

## 3. Estado ya cerrado: no rehacer

| ID | Commit | Estado |
|---|---|---|
| S0-9 | `5246a59` | Fixture `qapp` centralizado en `tests/conftest.py` |
| S0-1 | `8b4f19a` | Corrección de tablas consultadas por `_fetch_patient_data` |
| S0-2-bis | `e903d34` | Ánimo deja de persistir campos no capturados |
| RA-1 | `455a476` | Retiro de `energia` del contrato activo de Actividades |
| RA-2 | `d2cc96f` | Timer persiste la `categoria` real del preset |
| RA-5 | `3107c3e` | DBT persiste `skill_version` desde `DBT_SKILLS` |
| RA-6 | `485cb1a` | Retiro de `reflexion_ia` del contrato activo de TCC |
| RB-5 | `87d7953` | Actividades dispara sync inmediato tras registrar resultado |
| RB-1 | `1e82e2f` | Los tres subtabs IA reciben el nombre real del paciente |
| RC-3 | `b49333a` | Test congela `.limit(50)+.order+.eq` en `assigned_reminders` (cambio productivo ya en S0-1 `8b4f19a`) |
| RB-3 | `b4c9937` | Fetch de `reminder_logs` (telemetría avisos disparados) bajo key `avisos_disparados` en `_fetch_patient_data` |
| Handoff local | `8aeb389` | Primera versión documental; este archivo la reemplaza |

No modificar estos fixes salvo que una regresión reproducible lo exija.

---

## 4. Inicio obligatorio de cada tarea

Ejecutar desde PowerShell:

```powershell
Set-Location C:\Users\nosom\Desktop\nm_suite
git fetch origin
git status -sb
git branch --show-current
git log -1 --format="%H %s"
git log origin/main -1 --format="%H %s"
```

Condiciones para comenzar:

1. El working tree debe estar limpio.
2. `main` local y `origin/main` deben coincidir.
3. No debe haber otro agente trabajando sobre los mismos archivos.
4. Si `main` cambió respecto del SHA esperado por la tarea, reauditar el contexto antes de editar.
5. No borrar ni sobrescribir cambios locales desconocidos.
6. No usar `git reset --hard`, `git clean`, rebase, force-push ni eliminación de ramas salvo orden explícita del owner.

Preparación de la rama:

```powershell
git switch main
git pull --ff-only origin main
git switch -c fix/<id>-<descripcion-corta>
```

Una rama pequeña por fix. No mezclar IDs ni tareas no relacionadas.

---

## 5. Flujo local obligatorio

Para cada fix:

1. Leer el código productivo, llamadas relacionadas, schemas y tests existentes.
2. Reproducir o demostrar el defecto antes de cambiarlo.
3. Distinguir:
   - hecho comprobado;
   - inferencia;
   - afirmación de auditorías previas;
   - punto todavía no verificado.
4. Implementar el cambio mínimo.
5. Crear tests de comportamiento, no solo búsquedas de texto con `inspect` o regex.
6. Compilar cada archivo Python modificado.
7. Ejecutar tests dirigidos.
8. Ejecutar regresiones cercanas.
9. Ejecutar `git diff --check`.
10. Revisar manualmente el diff completo.
11. Entregar evidencia al owner antes de mergear a `main`.

El agente local **no debe**:

- crear `.patch`;
- usar `git apply`;
- clonar el repo otra vez para trabajar;
- editar encabezados `@@`;
- reconstruir diffs a mano;
- declarar que algo pasó sin mostrar la salida real;
- aprobar porque “la suite pasa” sin revisar el código y el diff;
- agregar UI, columnas o arquitectura nueva fuera del alcance autorizado.

---

## 6. Verificación técnica mínima

### Compilación

```powershell
.\.venv\Scripts\python.exe -m py_compile <archivo1.py> <archivo2.py>
```

### Tests dirigidos

```powershell
.\.venv\Scripts\python.exe -m pytest <tests-del-fix> -v
```

### Regresiones relacionadas

Agregar los tests de los módulos y contratos afectados.

### Suite completa

Ejecutarla cuando el alcance pueda afectar varios módulos, sync, Hub, schemas o componentes compartidos:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

No hardcodear un número histórico de tests. Informar el resultado real y comparar cualquier fallo contra el commit base.

### Calidad Git

```powershell
git diff --check
git diff --stat
git diff -- <archivos-modificados>
git status -sb
```

Antes del commit:

```powershell
git add <solo-los-archivos-del-fix>
git diff --cached --check
git diff --cached --stat
git diff --cached
```

No incluir documentación, temporales ni cambios de otro frente por accidente.

---

## 7. Cierre de una tarea

El agente puede dejar el fix probado y staged o crear el commit en su rama si el owner lo autorizó.

Commit recomendado:

```powershell
git commit -m "fix(<area>): <descripcion> (<ID>)"
```

No mergear ni pushear `main` automáticamente.

Después de aprobación explícita:

```powershell
git push -u origin <rama>
git switch main
git pull --ff-only origin main
git merge --ff-only <rama>
git push origin main
git fetch origin
git log -1 --format="%H %s"
git status -sb
```

Verificar que `main` local y `origin/main` sean idénticos.

---

## 8. Reglas de implementación y tests

1. **UI-first:** comprobar si existe un widget visible que captura el dato.
2. No inferir captura por una columna SQLite, un schema o un comentario.
3. No agregar funciones o UI nuevas salvo autorización explícita.
4. No eliminar columnas SQLite o Supabase por defecto; conservar compatibilidad histórica.
5. Usar `encoding="utf-8"` en todos los `open()`.
6. No duplicar `pytest_plugins` ni `QT_QPA_PLATFORM`; ya están centralizados.
7. Eliminar imports sin uso.
8. Preferir tests de ejecución con DB temporal, mocks controlados y llamadas reales.
9. Un test estructural puede complementar, pero no reemplazar, un test de comportamiento.
10. Los mocks de Supabase deben implementar exactamente la cadena usada por el código.
11. No ocultar errores productivos con `MagicMock` excesivamente permisivos.
12. En sync, un fallo de red no debe revertir un registro local ya guardado.
13. Usar la frase “queda pendiente hasta el próximo sync”; no afirmar un plazo fijo no demostrado.

---

## 9. Trabajo pendiente actualizado

## Fase 2 — Integridad del Hub y sync

### RD-1 — Aislamiento por exportador en sync

**Prioridad:** alta.

**Problema a verificar:** `sync_inmediato` y `sync_completo` ejecutan varios `_exportar_*` en secuencia. Si uno lanza una excepción, puede impedir que los siguientes se ejecuten.

**Objetivo:**

- aislar cada exportador con su propio `try/except`;
- registrar tabla/exportador y error;
- continuar con los exportadores restantes;
- conservar el resultado global de sync sin ocultar fallos.

**Archivo principal:** `shared/sync.py`

**Tests obligatorios:**

- un exportador lanza;
- los posteriores igualmente se ejecutan;
- el error queda registrado o devuelto de forma auditable;
- verificar ambos caminos: inmediato y completo.

No modificar aún lógica de tablas ni contratos.

---

### RB-2 — Métricas fantasma del dashboard

**Problema a verificar:** `hub/main_qt.py` usa defaults como `adherence=0.75` aunque `_cargar_pacientes` no obtiene ni calcula esa métrica. También deben auditarse `mood_data_7d`, `last_session` y `next_session`.

**Decisión requerida del owner antes de implementar:**

1. **Opción A:** eliminar defaults falsos y mostrar “Sin datos”.
2. **Opción B:** calcular métricas reales desde las tablas correspondientes.

No inventar una fórmula de adherencia.

**Archivo:** `hub/main_qt.py`

**Tests:**

- sin datos reales no aparece `0.75`;
- no se presentan fechas o sesiones ficticias;
- si se elige cálculo real, probar la fórmula y sus fuentes.

---

### RB-3 — Telemetría de avisos invisible en el Hub — CERRADO (`b4c9937`)

**Resolución:** `hub/pacientes_qt._fetch_patient_data` agrega fetch #9 a `reminder_logs` bajo la key nueva `avisos_disparados`, usando el helper `_fetch` existente con `select("fecha,hora,mensaje,cerrado")`, `.eq("patient_id", pid)`, `.order("fecha", desc=True)` (default helper) y `.limit(50)`. Schema verificado en `db/supabase_schema.sql:82-90`. El comentario engañoso "S2-1 pendiente" fue reemplazado por una nota que explica la distinción con `assigned_reminders`.

**Problema a verificar (histórico):** Suite exporta `recordatorios_log` a `reminder_logs`, pero el Hub no consultaba esa tabla.

**Objetivo propuesto (cumplido):**

- agregar fetch de `reminder_logs`; ✅
- seleccionar únicamente columnas reales verificadas en schema; ✅ (`fecha, hora, mensaje, cerrado`)
- limitar resultados; ✅ (`.limit(50)`)
- guardar la telemetría en una key nueva y explícita, por ejemplo `avisos_disparados`; ✅
- no confundir `reminder_logs` con `assigned_reminders`. ✅ (test de no-confusión explícito)

**Archivo:** `hub/pacientes_qt.py`

**Tests (agregados en `tests/test_rb3_telemetria_avisos_disparados.py`):**

- captura real de `.table("reminder_logs")`; ✅
- verificación del `.select(...)`; ✅ (con garantía negativa sobre columnas inexistentes)
- límite aplicado; ✅
- resultado almacenado bajo la key correcta. ✅
- test adicional de no-confusión con `assigned_reminders`.
- test smoke de estructura del dict.

Tests de `tests/test_s0_1_fetch_patient_data.py` actualizados para reflejar la 9ª tabla/key (defensa en profundidad).

Antes de implementar, comprobar schema Supabase y exportador actual.

---

### RB-4 + RB-6 — Estado local de avisos y sync inmediato

Estos IDs deben tratarse como un único frente de diseño. **RB-6 no resuelve nada por sí solo** si el sync no exporta el estado modificado.

**Problema:**

- `_on_completar` actualiza `recordatorios.activo=0` localmente;
- no existe un contrato remoto confirmado para ese cambio;
- disparar `sync_inmediato_background()` sin exportador no enviaría el estado.

**Decisión requerida del owner:**

1. crear tabla remota separada, por ejemplo `patient_reminders`;
2. extender/reutilizar `assigned_reminders`;
3. decidir que el estado local no debe sincronizarse.

Solo después de la decisión:

- diseñar schema;
- agregar exportador;
- llamar sync inmediato después del UPDATE local;
- mantener tolerancia a fallos de red.

**Archivos posibles:**

- `app/modules/avisos_qt.py`
- `shared/sync.py`
- `db/supabase_schema.sql`
- políticas RLS relacionadas

No crear tablas ni migraciones sin autorización explícita.

---

### RC-3 — Límite de recordatorios asignados — CERRADO (`b49333a`)

**Resolución:** el cambio productivo (`.limit(50) + .order("hora", desc=False) + .eq("patient_id", pid)`) fue introducido en S0-1 (`8b4f19a`) — el handoff original estaba desactualizado. RC-3 agrega `tests/test_rc3_limit_assigned_reminders.py` (4 tests de comportamiento) que congela el contrato y detecta regresión si se remueve el `.limit()` o se altera su valor.

**Problema a verificar (histórico):** fetch de `assigned_reminders` sin límite.

**Objetivo (cumplido):** aplicar `.limit(50)` o el límite que autorice el owner.

**Archivo:** `hub/pacientes_qt.py` — solo comentario L291 actualizado; sin cambio funcional.

**Test (agregado):** `tests/test_rc3_limit_assigned_reminders.py` captura la cadena Supabase y comprueba límite real, orden, filtro por `patient_id` y garantía negativa.

Puede resolverse antes de RC-1.

---

## Fase 3 — IA con contexto real

### RC-2 — Ventana temporal explícita

**Problema:** limitar cantidad no equivale a limitar período temporal.

El Hub usa Supabase/PostgREST. No usar SQL local como `WHERE fecha >= ?`.

**Implementación esperada:**

```python
.gte("fecha", fecha_desde)
```

o el filtro equivalente según la columna real de cada tabla.

**Requisitos:**

- definir ventana autorizada, inicialmente propuesta: 30 días;
- verificar que todas las tablas tengan una columna temporal comparable;
- no aplicar el mismo filtro ciegamente a tablas con campos distintos;
- ordenar antes de limitar cuando corresponda.

**Archivo:** `hub/pacientes_qt.py`

**Tests:** capturar `.gte(...)`, columna y fecha calculada.

---

### RC-1 — Resumen IA con contenido clínico real

**Problema a verificar:** `generar_resumen_paciente` usa principalmente conteos y promedios, sin contenido textual suficiente.

**Objetivo:**

- incluir hasta cinco registros recientes por módulo;
- seleccionar solo campos clínicamente pertinentes;
- truncar texto de forma segura;
- no incluir secretos, identificadores técnicos ni datos innecesarios;
- mantener el resumen como borrador para revisión profesional;
- controlar tamaño total del prompt.

**Archivo:** `hub/ia_asistente.py`

**Tests:**

- interceptar el prompt pasado a `_llamar`;
- verificar inclusión de contenido real;
- verificar truncado;
- verificar exclusión de campos sensibles/no necesarios;
- verificar comportamiento con módulos vacíos.

RC-1 debe ejecutarse después de estabilizar RB-3, RC-2 y RC-3.

---

## Fase 4 — Exportación PDF

### RB-7 — Cableado y consistencia del PDF

**Problemas a verificar:**

- `hub/exportar.py` puede no tener un botón conectado en la UI;
- las keys consumidas por `_generar()` pueden no coincidir con `_fetch_patient_data`;
- secciones de módulos pueden quedar vacías;
- debe comprobarse cuántos módulos y secciones existen realmente hoy.

**Objetivo:**

1. inventariar keys productoras y consumidoras;
2. unificarlas sin aliases ambiguos;
3. conectar “Exportar PDF” en una ubicación aprobada por el owner;
4. generar PDF con datos de prueba;
5. verificar texto y secciones reales, no solo existencia del archivo.

**Archivos posibles:**

- `hub/exportar.py`
- `hub/pacientes_qt.py`

**Tests:**

- fixture de paciente poblado;
- generación en directorio temporal;
- lectura del contenido o estructura verificable;
- datos reales en cada sección esperada.

No agregar gráficos hasta cerrar primero el cableado y el contrato de datos.

---

## Fase 5 — Limpieza controlada

La limpieza no puede ejecutarse por listas antiguas sin reauditoría.

### RE-1 — Tablas SQLite presuntamente muertas

Candidatas históricas:

- `checklist_snapshot`
- `mensajes_biblioteca`
- `activacion_config`
- `activacion_perfil`
- `timer_presets`
- `checklist_plantillas`
- `checklist_notas_dia`

Antes de eliminar cada una:

- buscar lecturas y escrituras;
- revisar migraciones;
- revisar datos históricos;
- revisar tests;
- confirmar con owner.

### RE-2 — Clases presuntamente muertas

Candidatas:

- `_InsightCard`
- `_StepCard`
- `_CategoriesCard`
- `_CategoryRingTile`
- `_ActivityRow`

Demostrar ausencia de instanciación antes de borrar.

### RE-3 — Funciones IA presuntamente muertas

Candidatas:

- `resumir_evolucion`
- `sugerir_acciones`
- `generar_tarea`

Buscar imports, callbacks, referencias indirectas y tests.

### RE-4 — `ia_chat_history`

Auditar schema, políticas, migraciones y uso remoto antes de eliminar.

### RE-5 — Presets de respiración

Determinar si `breathing_presets_cache` y `breathing_presets_remote` deben cablearse o eliminarse. Requiere decisión de producto.

### RE-6 — Test DBT obsoleto

Reauditar `test_dbt_module.py`. Corregirlo si todavía protege comportamiento vigente; eliminarlo solo si prueba una vista demolida y no aporta regresión útil.

### RE-7 — Docstrings

Corregir únicamente después de comparar cada docstring con comportamiento real.

### RE-8 — Imports huérfanos

Eliminar por archivo, ejecutando compilación y tests relacionados.

### RE-9 — Widgets ocultos de Respiración

Auditar:

- `_calm_badge`
- `_calm_bar`
- `_calm_pct_lbl`
- `_calm_card`
- `_calm_eyebrow`
- `_chrono_meta`
- `_range_lbl`

No borrarlos solo por no verse en una captura; verificar creación, layout, visibilidad, señales y estados.

---

## 10. Orden recomendado actualizado

1. ~~RD-1 — aislamiento del pipeline de sync.~~ — mergeado en `f1f1b6b` (pendiente de mover a "Estado cerrado").
2. ~~RC-3 — límite de `assigned_reminders`.~~ — cerrado en `b49333a`.
3. ~~RB-3 — telemetría de avisos en Hub.~~ — cerrado en `b4c9937`.
4. RB-2 — métricas fantasma, después de decisión del owner.
5. RB-4 + RB-6 — después de decisión del modelo remoto.
6. RC-2 — ventana temporal real.
7. RC-1 — contexto clínico real para IA.
8. RB-7 — contrato de datos y exportación PDF.
9. Fase 5 — limpieza por unidades pequeñas y reauditoría previa.

No ejecutar varias tareas del mismo archivo en paralelo.

---

## 11. Documentación disponible

El agente debe usar como fuente principal:

1. código actual del repo;
2. tests actuales;
3. schemas actuales;
4. este handoff;
5. instrucciones explícitas del owner.

Las antiguas rutas Linux como `/home/z/my-project/download/` no existen en el entorno Windows local y no deben asumirse disponibles.

Los reportes nombrados por auditorías previas solo pueden usarse si el owner los copia realmente al repo o proporciona su contenido. No inventar conclusiones faltantes.

---

## 12. Formato de entrega al terminar cada fix

Entregar exactamente:

```text
ID:
Rama:
SHA base:
Archivos modificados:
Cambio productivo:
Tests agregados/modificados:
Comandos ejecutados:
Resultado de py_compile:
Resultado de tests dirigidos:
Resultado de regresiones:
Resultado de suite completa:
git diff --check:
git diff --stat:
Puntos no verificados:
Riesgos:
Listo para merge: SÍ/NO
```

Adjuntar también:

```powershell
git status -sb
git log -1 --format="%H %s"
git diff --cached --stat
```

No declarar “cerrado”, “mergeado” o “publicado” sin comprobar el SHA en `main` y `origin/main`.

---

## 13. Primera tarea sugerida para el agente local

Comenzar con **RD-1**.

Antes de editar:

1. verificar `main` limpio y sincronizado;
2. localizar las secuencias completas de exportadores en sync inmediato y completo;
3. listar el orden exacto;
4. mostrar cómo un fallo corta actualmente la secuencia;
5. proponer el cambio mínimo;
6. implementar tests de ejecución;
7. detenerse antes del merge para auditoría del owner.
