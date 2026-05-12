# NeuroMood V3

Plataforma clínica de bienestar mental para Windows. Un único ejecutable unificado para el paciente y un Hub Profesional separado para el terapeuta. Desarrollada en Python con CustomTkinter sobre la identidad visual de [neuromood.com.ar](https://neuromood.com.ar).

---

## Requisitos del sistema

| Componente | Requisito |
|---|---|
| Sistema operativo | Windows 10 / 11 (64-bit) |
| Python (solo desarrollo) | 3.10 o superior |
| Conexión a internet | Opcional — solo para sincronización con Hub |
| Espacio en disco | ~150 MB (instalación completa) |
| RAM | 256 MB mínimo |

---

## Instalación

### Para el paciente

1. Ejecutar **`Instalar NeuroMood.exe`**
2. Completar nombre de usuario y contraseña (mínimo 6 caracteres)
3. Anotar el **código de instalación** generado — lo necesitarás si reinstalás la app
4. Elegir carpeta de instalación (por defecto: `%USERPROFILE%\NeuroMood`)
5. Al finalizar, hacer clic en **"Abrir NeuroMood ahora"**

Para desinstalar: ejecutar **`Desinstalar NeuroMood.exe`** dentro de la carpeta de instalación, o desde *Panel de Control → Agregar o quitar programas*.

### Para el profesional (Hub)

1. Ejecutar **`Instalar NeuroMood Hub Profesional.exe`**
2. Configurar credenciales Supabase en el archivo `.env` (ver sección [Configuración](#configuración))
3. Ejecutar `HubProfesional.exe`

### Modo desarrollo

```bash
pip install -r requirements.txt

# App paciente (PyQt6)
python app/main_qt.py

# Hub Profesional (PyQt6)
python hub/main_qt.py

# Modo test sin compilar
BUILD_ALL.bat test
```

---

## Configuración

Crear un archivo `.env` en la raíz del proyecto con las credenciales de Supabase:

```
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-clave-anon-publica
GROQ_KEY=tu-clave-groq          # Solo necesaria para el Hub (IA asistente)
```

El archivo `.env` **nunca se commitea** — está en `.gitignore`.

---

## Compilación

```bat
:: Compilar NeuroMood.exe + HubProfesional.exe
BUILD_ALL.bat

:: Compilar instalador del paciente (requiere BUILD_ALL primero)
BUILD_INSTALLER.bat

:: Compilar instalador del Hub (requiere BUILD_ALL primero)
BUILD_INSTALLER_PRO.bat

:: Probar sin compilar
BUILD_ALL.bat test
```

Los ejecutables se generan en `dist/` (paciente) y `dist/pro/` (Hub).

---

## Plataforma Paciente — NeuroMood.exe

Ventana unificada con 7 módulos accesibles desde una pantalla de inicio con cards. Un click abre el módulo; el botón `←` vuelve al inicio. Los avisos/recordatorios continúan activos en la bandeja del sistema incluso con la ventana cerrada.

### Módulo: Ánimo

**Descripción:** Registro del estado emocional del día con escala del 1 al 10.

**Cómo usar:**
1. Mover el slider hasta el valor que representa cómo te sentís (1 = muy mal, 10 = excelente)
2. El emoji y el color cambian en tiempo real para acompañar el valor
3. Escribir una nota opcional en el campo de texto
4. Presionar **Registrar**

Se pueden hacer múltiples registros por día. Los datos se sincronizan automáticamente con el Hub del terapeuta.

---

### Módulo: Respirar

**Descripción:** Sesiones de respiración guiada con la técnica 4-7-8 (inhala 4 s → retén 7 s → exhala 8 s). Reduce la activación del sistema nervioso simpático.

**Cómo usar:**
1. Elegir duración: **3 min**, **5 min** o **10 min**
2. Presionar **Iniciar**
3. Seguir el círculo animado y las instrucciones de cada fase (Inhala / Mantén / Exhala)
4. Las step-cards en la parte inferior se iluminan con la fase activa
5. El cronómetro acumula el tiempo total de la sesión
6. Presionar **Pausa** para interrumpir temporalmente o **Detener** para finalizar

Al completar la sesión, suena un tono y se guarda el registro automáticamente.

---

### Módulo: Registro TCC

**Descripción:** Registro estructurado de pensamientos automáticos siguiendo el modelo de Terapia Cognitivo-Conductual (4 pasos).

**Cómo usar:**

| Paso | Campo | Descripción |
|------|-------|-------------|
| 1 | Situación | ¿Qué pasó? Descripción objetiva del evento |
| 2 | Emoción + intensidad | ¿Qué emoción sentiste? Slider de 0–10 |
| 3 | Pensamiento | El pensamiento automático que apareció. El módulo sugiere distorsiones cognitivas detectadas por palabras clave |
| 4 | Respuesta alternativa | Una interpretación más equilibrada del evento |

Cada paso requiere completar el campo antes de avanzar. El historial de registros es accesible desde el Hub del terapeuta.

---

### Módulo: Rutina

**Descripción:** Lista de tareas diarias organizada en tres secciones (Mañana / Tarde / Noche). Las tareas pueden ser creadas por el paciente o asignadas por el terapeuta desde el Hub.

**Cómo usar:**
- Presionar `+` en cualquier sección para agregar una tarea nueva
- Marcar el checkbox para completar una tarea (suena un tono de confirmación)
- La barra de progreso de cada sección muestra el avance visual
- El contador superior indica cuántas tareas completaste en total
- Sección **Nota del día** para escribir observaciones libres

Las tareas completadas se registran por fecha y se sincronizan con el Hub.

---

### Módulo: Actividades

**Descripción:** Sugerencias de actividades conductuales adaptadas al nivel de ánimo registrado. Las actividades provienen del banco configurado por el terapeuta.

**Cómo usar:**
1. **Primero registrá tu ánimo** en el módulo Ánimo — las sugerencias se adaptan a tu estado
2. El módulo muestra 2–3 actividades del banco según tu ánimo actual
3. Al realizar una actividad, indicar el resultado: **Hecha**, **Intentada** o **No pude**
4. La card cambia de color según el resultado registrado

Si no hay registro de ánimo del día, el módulo lo indica y solicita registrarlo primero.

---

### Módulo: Timer

**Descripción:** Temporizador de cuenta regresiva con indicador circular animado. Útil para estructurar actividades terapéuticas con tiempo definido.

**Cómo usar:**
1. Elegir duración: **5 min**, **10 min**, **15 min**, **20 min** o ingresar un valor personalizado (1–120 min)
2. Presionar **Iniciar**
3. El arco de progreso avanza con gradiente teal → violeta
4. Usar **Pausa** / **Reanudar** según necesidad
5. Al finalizar, suena doble tono y aparece "¡Tiempo! ✓"

Las sesiones de más de 30 segundos se guardan automáticamente con fecha y duración real.

---

### Módulo: Avisos

**Descripción:** Recordatorios programados con notificación sonora del sistema operativo. Funcionan en segundo plano incluso con la app cerrada.

**Cómo usar:**
1. Presionar **+ Nuevo aviso**
2. Ingresar hora en formato HH:MM
3. Seleccionar los días de la semana
4. Escribir el mensaje del aviso
5. Presionar **Guardar**

**Opciones adicionales (sección Opciones):**
- **Horario de silencio:** definir un rango horario donde los avisos no suenan (ej: 22:00 → 08:00)
- **Iniciar con Windows:** la app se activa automáticamente al encender la computadora

Los avisos del terapeuta se descargan automáticamente al abrir la app.

---

## Hub Profesional — HubProfesional.exe

Panel de gestión clínica. Requiere conexión a Supabase configurada en `.env`.

### Flujo de trabajo

```
Dashboard → seleccionar paciente → ver detalle → asignar tareas / ver gráficos / usar IA
```

### Vista: Dashboard

Muestra una card por cada paciente vinculado con su nombre e ID. Hacer click en **"Ver detalle"** abre el panel completo del paciente.

### Vista: Pacientes

Lista completa de pacientes con acceso directo al detalle de cada uno. Botón **↻ Actualizar** para refrescar la lista desde Supabase.

### Detalle del paciente — tabs

#### Tab Registros

Carga todos los registros del paciente desde Supabase:
- Ánimo (con promedio), sesiones de respiración, registros TCC, checklist, timer, recordatorios
- Botón **"Ver gráfico"** abre una ventana con el gráfico de evolución del ánimo (matplotlib)
- Botón **"⬇ Exportar PDF"** genera un reporte completo en `~/Downloads/NeuroMood_[nombre]_[fecha].pdf`

#### Tab Asignar

- **Asignar tarea de rutina:** ingresar descripción + sección (mañana/tarde/noche) → **Asignar tarea**
- **Enviar recordatorio remoto:** ingresar mensaje + hora → **Enviar** (el paciente lo recibe al abrir la app)

#### Tab Banco

Editor del banco de actividades conductuales:
- Agregar actividades con nombre, descripción, categoría y rango de ánimo
- Botón **"✦ IA: completar descripción"** usa Groq para generar una descripción automáticamente
- Eliminar actividades existentes con el botón `✕`

Las actividades del banco se sincronizan al paciente al abrir la app.

#### Tab IA

Asistente basado en Groq (llama3-70b). **El terapeuta siempre revisa antes de aplicar.**

- **Resumen de evolución:** párrafo narrativo del progreso clínico del paciente
- **Sugerencias de acción:** 3 acciones concretas con botón `[Aplicar]` (copia al portapapeles)
- **Generar tarea personalizada:** ingresá contexto libre → la IA genera un borrador de tarea

> Requiere haber cargado los registros del paciente (Tab Registros) antes de usar la IA.

---

## Estructura del proyecto

```
Neuromood V3/
├── app/                         # Plataforma paciente (NeuroMood.exe)
│   ├── main.py                  # Entry point: ventana principal + navegación
│   ├── home.py                  # Home con grid de 7 cards
│   ├── modules/
│   │   ├── animo.py             # Módulo Ánimo
│   │   ├── respiracion.py       # Módulo Respiración
│   │   ├── registro_tcc.py      # Módulo Registro TCC
│   │   ├── rutina.py            # Módulo Rutina
│   │   ├── actividades.py       # Módulo Actividades
│   │   ├── timer.py             # Módulo Timer
│   │   └── avisos.py            # Módulo Avisos
│   ├── motor_activacion.py      # Motor de sugerencias conductuales
│   └── avisos_daemon.py         # Daemon de bandeja + scheduler de notificaciones
├── hub/                         # Hub Profesional (HubProfesional.exe)
│   ├── main.py                  # Entry point: nav lateral + routing
│   ├── pacientes.py             # Vista detallada con tabs por paciente
│   ├── visualizacion.py         # Gráficos matplotlib integrados
│   ├── ia_asistente.py          # Asistente IA (Groq)
│   └── exportar.py              # Exportación a PDF (reportlab)
├── shared/                      # Código compartido
│   ├── theme.py                 # Design system: colores, tipografía, layout, CATEGORY_COLORS
│   ├── components.py            # Componentes UI + ThemeManager + helpers de gradiente
│   ├── base_module.py           # Clase base NMModule (herencia para todos los módulos)
│   ├── db.py                    # SQLite local con migraciones versionadas
│   ├── sync.py                  # Sincronización bidireccional con Supabase
│   ├── config.py                # Lectura de .env (lazy loading)
│   ├── identidad.py             # Generación y persistencia de patient_id
│   ├── utils.py                 # Utilidades de fecha/hora y color
│   └── installer_common.py      # Utilidades compartidas entre instaladores
├── installer.py                 # Instalador paciente
├── installer_pro.py             # Instalador Hub
├── uninstaller.py               # Desinstalador paciente
├── uninstaller_pro.py           # Desinstalador Hub
├── installer.spec               # PyInstaller spec — instalador paciente
├── installer_pro.spec           # PyInstaller spec — instalador Hub
├── uninstaller.spec             # PyInstaller spec — desinstalador paciente
├── uninstaller_pro.spec         # PyInstaller spec — desinstalador Hub
├── BUILD_ALL.bat                # Compila NeuroMood.exe + HubProfesional.exe
├── BUILD_INSTALLER.bat          # Compila instalador paciente
├── BUILD_INSTALLER_PRO.bat      # Compila instalador Hub
├── supabase_schema.sql          # Schema de tablas Supabase (ejecutar una vez)
├── requirements.txt             # Dependencias Python
├── PLAN.md                      # Plan de refactorización integral
├── _dev/                        # Herramientas de desarrollo (previews de tema)
└── .env                         # Credenciales locales (NO commitear)
```

---

## Base de datos

**Local (SQLite):** `%APPDATA%\NeuroMood\nm_data.db`

Las tablas se crean y migran automáticamente al iniciar la app. No requiere configuración manual.

| Tabla | Contenido |
|---|---|
| `termometro` | Registros de ánimo (puntaje, nota, fecha) |
| `respiracion` | Sesiones de respiración (técnica, duración, ciclos) |
| `pensamientos` | Registros TCC (4 campos + distorsiones) |
| `checklist_tareas` | Tareas de rutina (secciones, orden) |
| `checklist_completadas` | Tareas completadas por fecha |
| `checklist_notas_dia` | Nota libre del día |
| `activacion` | Resultados de actividades (hecha/intentada/no_pude) |
| `activacion_actividades` | Banco de actividades con rangos de ánimo |
| `actividades_temporizador` | Sesiones del timer |
| `recordatorios` | Avisos configurados (hora, días, mensaje) |
| `recordatorios_log` | Historial de avisos disparados |
| `config` | Configuración local (patient_id, nombre, credenciales) |

**Nube (Supabase):** `supabase_schema.sql` — ejecutar una vez desde el dashboard de Supabase para crear las tablas del Hub.

---

## Sincronización paciente ↔ Hub

Al abrir la app del paciente se ejecutan automáticamente en background:

- **Exportación:** sube registros de las últimas 48 h a Supabase (ánimo, respiración, TCC, checklist, timer, logs de avisos)
- **Importación:** descarga tareas y recordatorios asignados por el terapeuta desde el Hub
- **Intervalo de sync completo:** cada 7 días se hace un sync completo de los últimos 8 días

---

## Design system

Centralizado en `shared/theme.py`:

| Token | Descripción |
|---|---|
| `COLORS["dark_hybrid"]` | Paleta oscura: `#050911` bg, `#00d4c8` accent (teal), `#7c5bf2` violet |
| `COLORS["light_hybrid"]` | Paleta clara: `#f8fafc` bg, `#0891b2` accent, `#7c3aed` violet |
| `TYPOGRAPHY` | Segoe UI — h1: 28pt, body: 14pt, caption: 11pt |
| `LAYOUT` | Padding: 24px container, radius card: 12px, gap: 16px |
| `GRADIENTS` | Teal → violeta para arcos y efectos visuales |
| `CATEGORY_COLORS` | 6 colores canónicos para categorías de activación conductual |

El `ThemeManager` en `shared/components.py` propaga los cambios dark/light a todos los widgets registrados sin reiniciar la app.

---

## Tecnologías

| Tecnología | Versión mínima | Uso |
|---|---|---|
| [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) | 6.6.0 | Interfaz gráfica principal (migrado desde CustomTkinter) |
| [pyqtgraph](https://www.pyqtgraph.org/) | 0.13.0 | Gráficos interactivos en el Hub |
| [Pillow](https://python-pillow.org/) | 10.0.0 | Imágenes, logo, gradientes en Canvas |
| [matplotlib](https://matplotlib.org/) | 3.7.0 | Gráficos de evolución en el Hub |
| [ReportLab](https://www.reportlab.com/) | 4.0.0 | Exportación a PDF |
| [pystray](https://github.com/moses-palmer/pystray) | 0.19.0 | Ícono en bandeja del sistema |
| [winotify](https://github.com/versa-syahptr/winotify) | 1.1.0 | Notificaciones nativas Windows 10/11 |
| [groq](https://github.com/groq/groq-python) | 0.9.0 | IA asistente del Hub (llama3-70b) |
| [supabase-py](https://github.com/supabase/supabase-py) | 2.0.0 | Sincronización en la nube |
| [pygame](https://www.pygame.org/) | 2.5.0 | Audio (dependencia de matplotlib) |
| [numpy](https://numpy.org/) | 1.24.0 | Cálculos numéricos para gráficos |
| [PyInstaller](https://pyinstaller.org/) | 6.0.0 | Compilación a .exe |
| SQLite (stdlib) | — | Persistencia local |
