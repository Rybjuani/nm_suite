# Documentación de Handoff: Sincronización Supabase para DBT (Diferido)

Este documento detalla el diseño de persistencia y la estrategia de sincronización para migrar los registros del módulo de **Habilidades DBT** a Supabase una vez que el candidato local offline sea adoptado y se decida avanzar con las fases remotas.

---

## 1. Esquema SQLite final (Persistencia Local)

La tabla local está implementada e integrada de manera idempotente en SQLite mediante el siguiente esquema:

```sql
CREATE TABLE IF NOT EXISTS dbt_practicas (
    record_id TEXT PRIMARY KEY,
    fecha TEXT NOT NULL,
    hora TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    skill_version INTEGER NOT NULL DEFAULT 1,
    familia TEXT NOT NULL CHECK (
        familia IN (
            'mindfulness',
            'distress_tolerance',
            'emotion_regulation',
            'interpersonal_effectiveness'
        )
    ),
    necesidad TEXT DEFAULT '',
    malestar_antes INTEGER NULL CHECK (
        malestar_antes IS NULL OR malestar_antes BETWEEN 0 AND 10
    ),
    malestar_despues INTEGER NULL CHECK (
        malestar_despues IS NULL OR malestar_despues BETWEEN 0 AND 10
    ),
    resultado TEXT NOT NULL DEFAULT 'sin_evaluar' CHECK (
        resultado IN ('ayudo', 'parcial', 'no_esta_vez', 'sin_evaluar')
    ),
    duracion_seg INTEGER NOT NULL DEFAULT 0 CHECK (duracion_seg >= 0),
    nota TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
```

---

## 2. Esquema Remoto Propuesto (Supabase)

Se propone crear la tabla en el esquema público de Supabase con una estructura equivalente a SQLite, agregando la relación con el paciente:

```sql
CREATE TABLE IF NOT EXISTS public.dbt_practice_records (
    record_id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL REFERENCES public.patients(patient_id) ON DELETE CASCADE,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    skill_id TEXT NOT NULL,
    skill_version INTEGER NOT NULL DEFAULT 1,
    familia TEXT NOT NULL,
    necesidad TEXT DEFAULT '',
    malestar_antes INTEGER,
    malestar_despues INTEGER,
    resultado TEXT NOT NULL DEFAULT 'sin_evaluar',
    duracion_seg INTEGER NOT NULL DEFAULT 0,
    nota TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Constraints equivalentes:
* `CHECK (familia IN ('mindfulness', 'distress_tolerance', 'emotion_regulation', 'interpersonal_effectiveness'))`
* `CHECK (malestar_antes IS NULL OR malestar_antes BETWEEN 0 AND 10)`
* `CHECK (malestar_despues IS NULL OR malestar_despues BETWEEN 0 AND 10)`
* `CHECK (resultado IN ('ayudo', 'parcial', 'no_esta_vez', 'sin_evaluar'))`
* `CHECK (duracion_seg >= 0)`

---

## 3. Estrategia de Sincronización (Sync & Upsert)

Para sincronizar los registros de forma idempotente y segura offline-first:

1. **UUIDs Locales:** `record_id` se genera en la app del paciente con un UUID v4 estable. Esto previene colisiones y duplicados durante reintentos de red.
2. **Upsert por record_id:** La sincronización remota debe usar la estrategia de Upsert en la base de datos central de Supabase basada en el identificador único `record_id`.
3. **Flujo de exportación (`shared/sync.py`):**
   * Crear la función `_exportar_dbt_practicas(sb, patient_id, desde)`.
   * Realizar una consulta local a `dbt_practicas` buscando filas con `created_at > desde`.
   * Realizar una llamada de upsert por lotes (upsert batch) utilizando el cliente Supabase (con bypass/control de errores para conservar la resiliencia offline si no hay red).
   * Integrar la llamada en `sync_completo()`.

---

## 4. Políticas de Seguridad RLS (Row Level Security)

Se debe restringir el acceso a la tabla remota en Supabase para proteger la privacidad del paciente bajo las políticas vigentes de la suite:

```sql
ALTER TABLE public.dbt_practice_records ENABLE ROW LEVEL SECURITY;

-- Política para Pacientes (lectura y escritura de sus propios registros)
CREATE POLICY "Patients can manage their own DBT practices"
    ON public.dbt_practice_records
    FOR ALL
    USING (auth.uid()::text = patient_id)
    WITH CHECK (auth.uid()::text = patient_id);

-- Política para Profesionales (lectura de los registros de sus pacientes asignados)
CREATE POLICY "Professionals can view assigned patients' DBT practices"
    ON public.dbt_practice_records
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.patient_assignments pa
            WHERE pa.patient_id = dbt_practice_records.patient_id
              AND pa.professional_id = auth.uid()::text
        )
    );
```

---

## 5. Integración futura con el Hub Profesional y Exportaciones

Una vez sincronizados los datos en Supabase, la UI profesional debe consumir y reportar los registros:

1. **Hub Vista Paciente (`hub/pacientes_qt.py`):**
   * Añadir una pestaña o sección `Prácticas DBT` en la ficha detallada del paciente.
   * Mostrar un listado histórico que contenga: Fecha/Hora, Habilidad, Familia, Duración (minutos), Malestar (Antes/Después si no son nulos), Resultado Autopercibido y Nota clínica.
   * Calcular descriptivos estadísticos básicos agregados (como el promedio de diferencia antes/después cuando existan pares completos), etiquetándolo claramente como autoinforme y sin interpretación diagnóstica.
2. **Exportación de informes (`hub/exportar.py`):**
   * Incluir la tabla descriptiva de prácticas de habilidades DBT en las exportaciones PDF y CSV del historial de registros clínicos del paciente.

---

## 6. Orden recomendado de implementación manual

Cuando se elija e integre el candidato final en el repositorio real, se recomienda seguir este orden paso a paso para completar la sincronización:

1. **Paso 1: Migración Remota.** Desplegar el script de migración SQL en Supabase (tabla y políticas RLS descritas en la sección 4).
2. **Paso 2: Sincronización Local.** Modificar `shared/sync.py` para añadir la consulta local de registros e invocar el upsert central de Supabase.
3. **Paso 3: Integración en el Hub.** Actualizar `hub/pacientes_qt.py` y `hub/exportar.py` para visualizar y exportar el historial de prácticas de DBT en la suite del profesional.
4. **Paso 4: Verificación Final.** Ejecutar regresiones con Supabase en red y en simulación offline para asegurar que no se bloquee el flujo ante fallos de conexión.
