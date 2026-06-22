# Plan de implementación — Módulo Habilidades DBT

**Fecha:** 2026-06-14  
**Estado:** implementación técnica validada contra `fba804a` el 2026-06-21; la revisión
profesional DBT sigue siendo gate externo de release, no trabajo de código local.  
**Objetivo:** retirar el módulo paciente **Visualizador de Evolución Anímica** y ocupar su lugar con un módulo de práctica de habilidades DBT claramente distinto del Registro de Pensamientos TCC.

## Estado de cierre técnico

- `app/modules/evolucion_qt.py` no existe y no quedan consumidores directos de
  `ModuloEvolucion`, `app.modules.evolucion_qt`, `text.module.evolucion.*` ni navegación
  `evolucion` en código vivo.
- `app/modules/dbt_qt.py`, Home/main, QA, build, SQLite, Supabase, sync, Hub, PDF e IA Hub
  referencian DBT con los seams actuales.
- Validación focal DBT: `pytest tests\test_dbt_module.py tests\test_dbt_visual_contract.py tests\test_ra5_dbt_skill_version_canonico.py tests\test_home_visual_contract.py::test_visual_qa_home_statuses_match_mockup tests\test_rb7_pdf_consistency.py tests\test_s0_1_fetch_patient_data.py -q` -> 37 passed.
- Validación global reciente: `pytest tests/` -> 317 passed, `runtime_live_probe.py --all --theme both` -> 22/22, `capture_v8.py --all --theme both` -> 98/98, `build_neuromood.py --dry-run` -> preflight OK.

---

## 1. Decisión de producto

1. Eliminar de la Suite paciente el módulo `evolucion` y su pantalla `app/modules/evolucion_qt.py`.
2. Mantener intactos los registros de ánimo (`termometro`), sus gráficos en el Hub, exportaciones clínicas y funciones genéricas que hablen de “evolución” del paciente. Se elimina la herramienta redundante de la Suite, no el historial clínico ni el análisis profesional.
3. Crear en la misma posición del Home un módulo nuevo con id `dbt`, título **Habilidades DBT** y foco en práctica guiada breve.
4. No copiar el flujo del módulo TCC ni convertir DBT en otro registro de situación-pensamiento-respuesta.
5. No incorporar IA generativa en el MVP. El contenido será determinista, versionado y revisable.

---

## 2. Diagnóstico del repo actual

### 2.1 Registro TCC existente

`app/modules/registro_tcc_qt.py` implementa un recorrido lineal de cuatro pasos:

1. Situación.
2. Emoción e intensidad.
3. Pensamiento automático y detección de posibles distorsiones.
4. Respuesta alternativa.

Guarda una narrativa cognitiva en `pensamientos`, carga plantillas TCC y muestra registros previos. Esa identidad debe preservarse sin reutilizarla como molde funcional del nuevo módulo.

### 2.2 Visualizador de Evolución actual

`app/modules/evolucion_qt.py`:

- no genera una intervención propia;
- vuelve a leer datos ya capturados por el Termómetro Emocional;
- presenta gráfico semanal/mensual y promedio, máximo y mínimo;
- ocupa una de las ocho tarjetas principales del Home;
- replica en la Suite información que ya tiene más sentido en el Hub profesional.

Por eso el reemplazo no requiere migrar datos del módulo: no existe una tabla local exclusiva de Evolución que conservar o transformar.

### 2.3 Consumidores directos que deben cambiar

| Archivo | Cambio requerido |
|---|---|
| `app/modules/evolucion_qt.py` | Eliminar cuando el reemplazo esté integrado y verificado. |
| `app/main_qt.py` | Reemplazar `evolucion` por `dbt` en `_MODULE_MAP` y `_MODULE_UI_META`. |
| `app/home_qt.py` | Sustituir la octava tarjeta del Home. |
| `hub/personalizacion_global.py` | Sustituir la entrada de textos del Visualizador por Habilidades DBT. |
| `hub/editors/text_overrides_editor.py` | Retirar las tres claves `text.module.evolucion.*`; agregar solo copys seguros del shell DBT. |
| `build_neuromood.py` | Cambiar el hidden import de `app.modules.evolucion_qt` por `app.modules.dbt_qt`. |
| `qa/capture_v8.py` | Retirar la receta `evolucion`; agregar estados DBT. |
| `qa/runtime_live_probe.py` | Actualizar cualquier inventario o navegación que todavía espere `evolucion`. |
| `shared/visual_qa.py` | Agregar fixtures/estado DBT si el módulo los necesita. |

### 2.4 Referencias que no deben borrarse por coincidencia de nombre

No eliminar automáticamente usos genéricos de “evolución” en:

- `hub/pacientes_qt.py`;
- `hub/exportar.py`;
- `hub/ia_asistente.py`;
- gráficos del ánimo del Hub;
- reportes que resumen cambios en el tiempo.

Esas superficies son profesionales y siguen teniendo utilidad. La limpieza debe buscar consumidores concretos de `ModuloEvolucion`, `app.modules.evolucion_qt`, el id de navegación `evolucion` y las claves `text.module.evolucion.*`.

---

## 3. Investigación de referencias DBT

Ejemplos revisados como referencia de categoría:

- **DBT Coach**.
- **DBT Diary Card and Skills Coach**.
- **DBT Travel Guide**.
- **Wysa**, que mezcla ejercicios guiados basados en CBT, DBT y mindfulness.
- **IMBUE**, prototipo de práctica de efectividad interpersonal con simulación y feedback.
- **Glow**, prototipo reciente de coaching DBT con IA generativa y evaluación explícita de riesgos.

Patrones útiles que se repiten en productos y literatura DBT:

1. Biblioteca de habilidades organizada por necesidad o familia.
2. Ejercicios guiados breves, utilizables en el momento.
3. Tarjeta/diario de práctica para registrar qué habilidad se usó.
4. Acceso rápido a habilidades favoritas o recientes.
5. Seguimiento de práctica, no solo lectura de contenido.
6. Separación entre aprender una habilidad y aplicarla en una situación real.
7. Cuatro familias reconocibles: mindfulness, tolerancia al malestar, regulación emocional y efectividad interpersonal.

Conclusión para NeuroMood: tomar el patrón **necesidad → habilidad → práctica → cierre breve**, sin copiar textos, diseños, bases de datos ni flujos exactos de terceros.

---

## 4. Concepto propuesto

### 4.1 Nombre

**Habilidades DBT**

Alternativa de copy para la tarjeta: **Kit de Habilidades DBT**. El id técnico debe ser `dbt`.

### 4.2 Propósito

Ayudar al paciente a elegir y practicar una habilidad concreta ante una necesidad presente, dejando un registro breve de uso para revisarlo después con su profesional.

### 4.3 Qué no es

- No es una segunda versión de TCC.
- No es un chatbot.
- No diagnostica.
- No interpreta clínicamente el resultado.
- No sustituye terapia ni atención de urgencia.
- No vuelve a mostrar gráficos de ánimo.
- No detecta distorsiones cognitivas.
- No exige escribir una historia extensa para poder usar una herramienta.

### 4.4 Diferencia explícita frente a TCC

| TCC actual | DBT propuesto |
|---|---|
| Recorrido lineal de reestructuración cognitiva. | Biblioteca no lineal de habilidades prácticas. |
| Parte de una situación y un pensamiento automático. | Parte de “¿qué necesitás ahora?”. |
| Detecta posibles distorsiones. | No analiza ni etiqueta pensamientos. |
| Busca una respuesta alternativa. | Guía una acción o práctica observable. |
| Registro narrativo relativamente detallado. | Registro breve de habilidad, contexto opcional y resultado percibido. |
| Un único flujo de cuatro pasos. | Varias microprácticas agrupadas en cuatro familias. |

---

## 5. Arquitectura de experiencia

### 5.1 Navegación interna

Usar tres vistas principales dentro del módulo:

1. **Ahora**
   - pregunta: “¿Qué necesitás en este momento?”;
   - cuatro tarjetas de necesidad;
   - acceso rápido a últimas habilidades usadas.

2. **Biblioteca**
   - filtro por las cuatro familias DBT;
   - cards compactas con nombre, propósito, duración estimada y nivel de acompañamiento;
   - búsqueda no necesaria en el MVP.

3. **Historial**
   - últimas prácticas;
   - habilidad, familia, fecha, duración y resultado autopercibido;
   - sin gráficos ni conclusiones automáticas.

La práctica guiada se abre como estado interno del módulo y vuelve a la vista anterior al finalizar o cancelar.

### 5.2 Entrada por necesidad

Las cuatro tarjetas de **Ahora** deben usar lenguaje cotidiano y mapear internamente a familias DBT:

| Necesidad visible | Familia DBT |
|---|---|
| “Volver al presente” | Mindfulness |
| “Atravesar un momento intenso” | Tolerancia al malestar |
| “Regular una emoción” | Regulación emocional |
| “Comunicarme con claridad” | Efectividad interpersonal |

Esto evita que la primera pantalla parezca un manual académico.

### 5.3 Catálogo MVP

Limitar el MVP a dos habilidades por familia. Ocho prácticas bien resueltas son preferibles a una biblioteca extensa y superficial.

#### Mindfulness

- **Observar y describir:** notar sensaciones, pensamientos y entorno sin intentar corregirlos.
- **Mente sabia:** pausa guiada para integrar emoción, hechos y objetivo del momento.

#### Tolerancia al malestar

- **STOP:** detenerse, tomar distancia, observar y proceder deliberadamente.
- **Autocalma con los sentidos:** elegir estímulos seguros de vista, oído, tacto, olfato o gusto.

#### Regulación emocional

- **Verificar los hechos:** separar hechos observables, interpretación y emoción.
- **Acción opuesta:** evaluar si la emoción encaja con los hechos y elegir una conducta alternativa segura.

#### Efectividad interpersonal

- **DEAR MAN:** preparar una petición, límite o conversación difícil.
- **GIVE / FAST:** checklist para cuidar relación, objetivo y autorrespeto.

### 5.4 Práctica guiada

Cada habilidad debe definir un objeto de contenido versionado:

```python
{
    "id": "distress_stop",
    "version": 1,
    "family": "distress_tolerance",
    "title": "STOP",
    "summary": "Hacé una pausa antes de actuar.",
    "duration_min": 2,
    "steps": [
        {"title": "Detenete", "body": "..."},
        {"title": "Tomá distancia", "body": "..."}
    ],
    "safety_note": "",
}
```

Requisitos de UI:

- una sola instrucción principal por pantalla;
- progreso visible, pero no reutilizar el resumen lateral ni la composición visual de TCC;
- botones `Anterior`, `Siguiente`, `Terminar` y `Salir`;
- timer opcional solo cuando aporte valor;
- ningún campo obligatorio antes de empezar;
- cierre accesible en menos de tres clics;
- contenido usable en 960×600, light y dark;
- sin scrollbar global invisible; scroll local únicamente para contenido que realmente lo requiera.

### 5.5 Cierre de una práctica

Al terminar:

- intensidad/malestar antes: opcional, escala 0–10;
- intensidad/malestar después: opcional, escala 0–10;
- resultado: `Me ayudó`, `Un poco`, `No esta vez`, `Prefiero no evaluar`;
- nota opcional corta;
- botón `Guardar práctica`.

**Regla de neutralidad:** ambas escalas deben iniciar sin selección. No mostrar ni persistir `5/10` por defecto y no asumir un punto medio si el usuario no interactúa.

---

## 6. Seguridad clínica y de contenido

1. Incluir una leyenda breve y no invasiva: herramienta educativa para practicar habilidades; no reemplaza atención profesional ni de emergencia.
2. En “Atravesar un momento intenso”, mostrar acceso visible a recursos de ayuda configurables, sin convertir la app en un evaluador de riesgo.
3. No preguntar ni inferir diagnóstico.
4. No emitir mensajes como “esta técnica es la correcta para vos”. Usar “podés probar”, “elegí” y “registrá cómo te resultó”.
5. No calcular eficacia clínica a partir del antes/después.
6. No usar IA generativa en el MVP. La investigación reciente sobre coaching DBT generativo encontró errores de seguridad y desinformación de habilidades; el módulo debe permanecer determinista hasta contar con evaluación clínica específica.
7. Dejar fuera del MVP componentes físicos de TIPP —temperatura intensa o ejercicio intenso— hasta definir contraindicaciones, copy seguro y revisión profesional.
8. Redactar contenido propio. No copiar instrucciones, nombres comerciales, ilustraciones ni textos protegidos de apps o manuales.
9. Someter las ocho prácticas a revisión de un profesional con formación DBT antes del release.

---

## 7. Diseño técnico del módulo

### 7.1 Archivo nuevo

`app/modules/dbt_qt.py`

Clase pública:

```python
class ModuloDBT(NMModule):
    MODULE_TITLE = "Habilidades DBT"
    MODULE_ICON = "skills"
```

Si `skills` no existe en `shared/icons_svg.py`, elegir un icono existente coherente —por ejemplo `spark`, `tool` o `heart`— antes de crear un asset nuevo.

### 7.2 Componentes internos sugeridos

- `_NeedCard`: necesidad cotidiana → familia DBT.
- `_SkillCard`: resumen de habilidad.
- `_SkillPracticeView`: recorrido guiado de una habilidad.
- `_PracticeClosure`: evaluación opcional y guardado.
- `_PracticeHistory`: lista de registros recientes.

Reutilizar `NMModule`, `NMCard`, `NMTabs`, `NMButton`, `NMButtonOutline`, `NMToast`, `NMTextArea` y tokens compartidos. No duplicar estilos en QSS locales si ya existe un componente común.

### 7.3 Estado interno

```python
self._current_family: str | None
self._current_skill_id: str | None
self._current_step: int
self._started_at: datetime | None
self._origin_view: str
```

Cancelar una práctica no guarda un registro parcial en el MVP.

### 7.4 Estado de tarjeta en Home

`get_card_status()` debe devolver texto descriptivo y no clínico:

- `Sin prácticas`;
- `1 práctica hoy`;
- `3 prácticas esta semana`.

No mostrar mejora, empeoramiento ni porcentajes de eficacia.

---

## 8. Persistencia local

Agregar en `shared/db.py` una tabla idempotente:

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
    duracion_seg INTEGER NOT NULL DEFAULT 0,
    nota TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
```

Decisiones:

- `record_id` se genera localmente con UUID para evitar conflictos de sync.
- guardar `skill_version` permite interpretar registros aunque el contenido cambie después;
- no persistir cada respuesta interna de la práctica en el MVP;
- `necesidad` y `nota` son opcionales;
- no reutilizar la tabla `pensamientos` ni agregar columnas DBT a TCC.

---

## 9. Supabase, sincronización y Hub

### 9.1 Migración remota

Crear una migración nueva y específica, por ejemplo:

`db/dbt_practice_records.sql`

Tabla remota sugerida:

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

Agregar constraints equivalentes a SQLite y RLS paciente/profesional siguiendo `db/secure_rls_hardening.sql`.

### 9.2 Sync

En `shared/sync.py`:

- agregar `_exportar_dbt_practicas(sb, patient_id, desde)`;
- upsert por `record_id`;
- llamarlo desde `sync_completo()`;
- mantener funcionamiento offline si Supabase no está disponible;
- no bloquear todo el sync si la tabla remota todavía no fue desplegada: registrar el error de forma visible en logs y documentar el orden de migración/release, sin ocultarlo silenciosamente.

### 9.3 Hub profesional

En `hub/pacientes_qt.py`, dentro de **Registros**, agregar una sección `Prácticas DBT` con:

- fecha/hora;
- habilidad;
- familia;
- duración;
- antes/después solo cuando fueron completados;
- resultado autopercibido;
- nota.

Métricas permitidas:

- cantidad de prácticas;
- habilidades más usadas;
- familias practicadas;
- promedio descriptivo de diferencia antes/después solo si hay suficientes pares completos, rotulado como autoinforme y sin interpretación clínica.

No agregar un “score DBT”, semáforo de riesgo ni ranking del paciente.

En `hub/exportar.py`, incluir una tabla de prácticas DBT en PDF/CSV si el registro ya forma parte del informe completo.

La IA del Hub no debe recibir automáticamente notas DBT en el primer release. Esa integración requiere una decisión separada de privacidad, prompt y revisión clínica.

---

## 10. Textos personalizables

Eliminar de `TEXT_KEYS`:

- `text.module.evolucion.eyebrow`;
- `text.module.evolucion.weekly_title`;
- `text.module.evolucion.monthly_title`.

Agregar solo textos de presentación, no instrucciones clínicas editables:

- `text.module.dbt.eyebrow` → `Práctica de habilidades`;
- `text.module.dbt.now_prompt` → `¿Qué necesitás en este momento?`;
- `text.module.dbt.empty_history` → `Todavía no guardaste prácticas.`;
- `text.module.dbt.safety_note` → copy aprobado para alcance/no emergencia.

El contenido paso a paso de las habilidades debe permanecer versionado en código en el MVP. Permitir que el Hub lo edite libremente aumentaría el riesgo clínico y volvería imposible garantizar qué instrucción recibió cada paciente.

---

## 11. Retiro seguro del Visualizador

Orden recomendado:

1. Crear `dbt_qt.py` y hacerlo navegable con id `dbt`.
2. Sustituir la tarjeta y metadatos en Home/main.
3. Actualizar personalización, QA y build.
4. Ejecutar búsqueda global de consumidores directos.
5. Verificar que la Suite abre, navega y construye correctamente.
6. Eliminar `app/modules/evolucion_qt.py`.
7. Repetir búsqueda global y gates.

Búsquedas mínimas posteriores:

```text
ModuloEvolucion
app.modules.evolucion_qt
"id": "evolucion"
text.module.evolucion
Visualizador de Evolución Anímica
```

No usar una búsqueda/reemplazo masiva sobre la palabra `evolucion`, porque rompería funcionalidades profesionales válidas.

---

## 12. QA y capturas

### 12.1 Recetas nuevas en `qa/capture_v8.py`

- `dbt-now` — entrada por necesidad.
- `dbt-library` — catálogo de cuatro familias.
- `dbt-practice-stop` — paso intermedio de práctica.
- `dbt-practice-closure` — cierre sin ratings seleccionados.
- `dbt-history-empty` — historial vacío.
- `dbt-history-filled` — historial con registros QA.

Eliminar la receta `evolucion`.

### 12.2 Escenarios funcionales

1. Abrir cada familia desde **Ahora**.
2. Abrir cada habilidad desde **Biblioteca**.
3. Avanzar y retroceder sin perder el paso actual.
4. Salir/cancelar sin persistir.
5. Completar sin elegir escalas: guardar `NULL`, nunca `5` implícito.
6. Completar con antes/después y nota.
7. Refrescar historial y estado de Home.
8. Reiniciar app y comprobar persistencia.
9. Ejecutar offline.
10. Sincronizar dos veces sin duplicar.
11. Visualizar el registro en el Hub.
12. Cambiar tema durante una práctica.
13. Redimensionar en 960×600 y resoluciones mayores.
14. Confirmar navegación por teclado y foco visible.

### 12.3 Gates sugeridos

En PowerShell nativo desde la raíz:

```powershell
.\.venv\Scripts\python.exe -m compileall app shared hub qa
.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view dbt-now --theme dark
.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view dbt-practice-closure --theme light
.\.venv\Scripts\python.exe qa\runtime_live_probe.py
.\.venv\Scripts\python.exe build_neuromood.py --dry-run
```

Agregar o ejecutar los tests de DB existentes para creación idempotente, constraints y serialización de `NULL`.

---

## 13. Fases de implementación

### Fase 0 — Contenido y seguridad

- validar nombre final;
- redactar las ocho habilidades con contenido propio;
- revisión DBT profesional;
- aprobar nota de alcance y recursos de ayuda;
- congelar `skill_id` y `version` iniciales.

### Fase 1 — Shell y reemplazo visual

- crear `app/modules/dbt_qt.py`;
- integrar Home/main;
- adaptar light/dark y 960×600;
- sustituir textos personalizables;
- actualizar build y QA;
- todavía sin sync remoto.

### Fase 2 — Registro local

- crear `dbt_practicas`;
- guardar cierre opcional;
- implementar historial y `get_card_status()`;
- probar migración idempotente y reinicio.

### Fase 3 — Supabase y Hub

- desplegar migración remota y RLS;
- exportar desde `shared/sync.py`;
- visualizar en Registros del Hub;
- incluir en exportaciones profesionales.

### Fase 4 — Demolición final y regresión

- eliminar `evolucion_qt.py`;
- confirmar cero consumidores directos;
- ejecutar capturas completas, runtime probe y build dry-run;
- validar instalador antes del release.

---

## 14. Fuera de alcance del MVP

- IA conversacional o recomendador generativo.
- Análisis de cadena conductual completo.
- Plan de crisis editable.
- Contenido físico TIPP sin revisión médica.
- Gamificación, rachas, puntos o premios.
- Recomendaciones basadas en diagnóstico.
- Catálogo DBT editable libremente desde el Hub.
- Notificaciones automáticas específicas de DBT.
- Compartir registros fuera del sync clínico existente.
- Simulaciones conversacionales tipo IMBUE.

Estos puntos pueden evaluarse después de observar uso real y completar revisión de seguridad.

---

## 15. Criterios de aceptación

- La Suite conserva ocho tarjetas y **Habilidades DBT** ocupa exactamente el lugar del Visualizador.
- `Visualizador de Evolución Anímica` ya no aparece en Home, navegación, personalización, QA ni build.
- `app/modules/evolucion_qt.py` no existe al finalizar la implementación.
- Los gráficos de ánimo y reportes profesionales del Hub siguen funcionando.
- TCC permanece sin cambios de alcance ni esquema.
- DBT se puede usar sin escribir una situación o pensamiento.
- El módulo ofrece cuatro familias y ocho habilidades aprobadas.
- Ninguna escala comienza preseleccionada.
- Cancelar no guarda; terminar guarda una sola práctica.
- El historial es descriptivo y no emite conclusiones clínicas.
- El sync es idempotente por `record_id`.
- No hay IA generativa en el módulo.
- Capturas light/dark a 960×600 válidas y sin cortes.
- Build dry-run y runtime probe pasan.

---

## 16. Riesgos principales

| Riesgo | Mitigación |
|---|---|
| Terminar con una copia visual/funcional de TCC. | Navegación por necesidad, biblioteca no lineal y registro de práctica, no de pensamiento. |
| Contenido DBT incorrecto o demasiado simplificado. | Catálogo pequeño, versionado y revisión profesional previa al release. |
| Confundir una herramienta educativa con atención de crisis. | Nota de alcance, recursos visibles y ausencia de promesas clínicas. |
| Borrar gráficos o reportes útiles al eliminar “evolución”. | Eliminar solo consumidores directos del módulo paciente. |
| Duplicar respiración u otras herramientas. | DBT puede referenciar habilidades breves; no reconstruir la Guía de Respiración dentro del MVP. |
| Duplicados de sincronización. | UUID local estable y upsert por `record_id`. |
| Cambios de contenido que vuelvan ilegibles registros viejos. | Persistir `skill_id`, `skill_version` y snapshot de título en Hub si se considera necesario. |
| IA que valide conductas dañinas o enseñe mal una habilidad. | Sin IA en MVP; evaluación separada antes de cualquier experimento futuro. |

---

## 17. Referencias consultadas

- Descripción general de DBT, sus cuatro familias de habilidades y uso de diary cards.
- Wysa como ejemplo de app de apoyo que combina ejercicios guiados basados en CBT, DBT y mindfulness.
- **IMBUE: Improving Interpersonal Effectiveness through Simulation and Just-in-time Feedback with Human-Language Model Interaction** (2024), como referencia futura para práctica de comunicación.
- **Initial Risk Probing and Feasibility Testing of Glow: a Generative AI-Powered Dialectical Behavior Therapy Skills Coach** (2026), especialmente por sus hallazgos de seguridad y desinformación en coaching DBT generativo.

La investigación inspira patrones de interacción; no autoriza copiar contenido de terceros. Todo copy clínico final debe ser propio y revisado.
