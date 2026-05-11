# NeuroMood Suite V3

Suite de aplicaciones de escritorio para Windows orientadas al bienestar mental y la regulación emocional. Desarrollada en Python con CustomTkinter, basada en la identidad visual de [neuromood.com.ar](https://neuromood.com.ar).

Disponible en dos ediciones:
- **Suite paciente** — 7 apps independientes para uso clínico diario
- **Hub Profesional** — panel de gestión de pacientes con sincronización en la nube (Supabase)

---

## Aplicaciones — Suite Paciente

### 1. Termómetro Emocional
Registro diario del estado emocional mediante un slider de 1 a 10. Permite agregar nota libre por registro, consultar historial del día, y exportar datos en PDF. Al registrar, sugiere actividades al checklist según el nivel de ánimo.

### 2. Visualizador de Evolución
Gráficos de evolución emocional y conductual con tres períodos: 7 días (diario), 30 días (semanal) y 90 días (mensual). Panel de estado emocional (línea + área) y panel de activación conductual (barras por categoría). Exportación de gráficos en imagen.

### 3. Guía de Respiración
Sesiones de respiración guiada con técnica 4-7-8 y otras técnicas configurables. Indicador visual animado, contador de ciclos, duración configurable y registro automático en base de datos.

### 4. Recordatorios de Bienestar
Recordatorios con horarios programables. Se minimiza a la bandeja del sistema (pystray) y emite notificaciones sonoras en los horarios configurados.

### 5. Checklist de Rutina
Lista de tareas en tres secciones: Mañana, Tarde y Noche. Incluye:
- Filtrado por nivel de ánimo (`animo_rango`: Bajo / Medio / Alto)
- Tareas asignadas por el terapeuta vía Hub Profesional
- **Pestaña Propuestas**: actividades del banco conductual filtradas por ánimo actual
- Historial semanal navegable, estadísticas de 30 días, nota del día
- Retroalimentación sonora al completar ítems

### 6. Registro de Pensamientos
Registro estructurado para el trabajo con pensamientos automáticos: situación, emoción e intensidad, pensamiento automático, distorsión cognitiva (8 categorías), pensamiento alternativo, evidencias y creencia antes/después. Buscador de registros por texto.

### 7. Temporizador de Actividades
Temporizador con presets terapéuticos (Relajación, Cognitiva, Física, Social, Autocuidado). Presets configurables por el terapeuta vía Hub. Cuenta regresiva visual con indicador circular y registro histórico de sesiones.

---

## Hub Profesional

Panel de gestión clínica con sincronización en la nube (Supabase). Acceso exclusivo mediante instalador Pro.

**Funcionalidades:**
- Gestión de pacientes: alta, baja, código de vinculación
- Asignación de tareas al checklist del paciente con filtro de ánimo
- Programación de recordatorios remotos
- Visualización de progreso: checklist, termómetro, activación
- **Herramientas de terapeuta:**
  - Banco de actividades conductuales (editor de `activacion_actividades`)
  - Plantillas de checklist (editor de `checklist_plantillas`)
  - Editor de presets del temporizador
  - Editor de pasos del Registro de Pensamientos

---

## Sincronización en la nube

La suite Pro usa [Supabase](https://supabase.com) para sincronización bidireccional:
- `sync_al_abrir()` — importa tareas y recordatorios asignados por el terapeuta
- `verificar_asignaciones()` — polling periódico de nuevas asignaciones
- `sync_inmediato_background()` — sube completados en background tras cada acción del paciente

La clave anon pública y la URL del proyecto están en `shared/sync.py`. No se requiere configuración por parte del paciente — la sincronización es automática.

---

## Capturas de pantalla

Las capturas de cada aplicación están en `_doc_screenshots/`.

---

## Requisitos del sistema

- Windows 10 / 11 (64-bit)
- Python 3.10 o superior (solo para modo desarrollo)

---

## Instalación

### Opción A — Ejecutable para paciente (Suite estándar)

Ejecutar `dist/Instalar NeuroMood Suite.exe`. Crea accesos directos en escritorio y menú de inicio.

Para desinstalar: `dist/Desinstalar NeuroMood.exe`

### Opción B — Ejecutable Pro (Hub Profesional)

Ejecutar `dist/pro/Instalar NeuroMood Pro.exe`. Instala el Hub Profesional.

Para desinstalar: `dist/pro/Desinstalar NeuroMood Pro.exe`

### Opción C — Modo desarrollo

```bash
pip install -r requirements.txt

# Apps paciente
python apps/termometro/main.py
python apps/visualizador/main.py
python apps/respiracion/main.py
python apps/recordatorios/main.py
python apps/checklist/main.py
python apps/pensamientos/main.py
python apps/temporizador/main.py

# Hub Profesional
python apps/hub_profesional/main.py

# Previews de tema (herramientas de desarrollo)
python _preview_neuromood.py   # nueva identidad visual
python _preview_fusion.py      # fusión de identidades con comparador
```

---

## Compilación

```bat
:: Compilar toda la suite paciente + Hub
BUILD_ALL.bat

:: Compilar instalador de la suite paciente
BUILD_INSTALLER.bat

:: Compilar instalador Pro
BUILD_INSTALLER_PRO.bat
```

Los ejecutables se generan en `dist/` (suite) y `dist/pro/` (Hub).

---

## Estructura del proyecto

```
Neuromood V3/
├── apps/
│   ├── activacion/              # Motor conductual (no app standalone)
│   │   ├── motor.py             # Sugerencias de actividades por ánimo
│   │   ├── terapeuta.py         # Editor del banco de actividades (Hub)
│   │   ├── analisis.py          # Análisis de patrones conductuales
│   │   └── perfil.py            # Perfil de preferencias del paciente
│   ├── checklist/               # Checklist de Rutina
│   │   ├── main.py
│   │   ├── plantillas.py        # Plantillas de tareas
│   │   └── editor_checklist.py  # Editor de plantillas (Hub)
│   ├── hub_profesional/         # Hub Profesional
│   │   ├── main.py
│   │   └── editor_pensamientos.py
│   ├── pensamientos/            # Registro de Pensamientos
│   │   ├── main.py
│   │   ├── ia.py                # Análisis asistido (Groq)
│   │   └── editor_pensamientos.py
│   ├── recordatorios/           # Recordatorios de Bienestar
│   ├── respiracion/             # Guía de Respiración
│   ├── temporizador/            # Temporizador de Actividades
│   │   ├── main.py
│   │   ├── presets.py           # Presets terapéuticos
│   │   ├── editor_presets.py    # Editor de presets (Hub)
│   │   └── sonido.py
│   ├── termometro/              # Termómetro Emocional
│   └── visualizador/            # Visualizador de Evolución
├── shared/
│   ├── components.py            # Componentes UI reutilizables (HeaderFrame, CardFrame, …)
│   ├── db.py                    # Base de datos SQLite + migraciones
│   ├── theme.py                 # Tokens de diseño: colores, tipografía, layout
│   ├── utils.py                 # Funciones auxiliares
│   ├── sync.py                  # Sincronización Supabase (paciente ↔ terapeuta)
│   └── identidad.py             # Identidad visual de marca
├── _doc_screenshots/            # Capturas de pantalla para documentación
├── _preview_neuromood.py        # Preview de la nueva identidad visual
├── _preview_fusion.py           # Preview de la fusión de identidades (con comparador)
├── _preview_light.py            # Preview del tema claro Notion
├── dark-theme-tests.md          # Especificación del dark theme (neuromood.com.ar)
├── white-theme-tests.md         # Especificación del white theme (neuromood.com.ar)
├── notion-visual-identity.md    # Análisis de identidad visual Notion
├── supabase_schema.sql          # Schema de tablas Supabase
├── installer.py                 # Instalador suite paciente
├── installer_pro.py             # Instalador Pro (Hub)
├── uninstaller.py               # Desinstalador suite
├── uninstaller_pro.py           # Desinstalador Pro
├── NeuroMood_Suite_Manual.pdf   # Manual de usuario
├── requirements.txt
├── BUILD_ALL.bat
├── BUILD_INSTALLER.bat
└── BUILD_INSTALLER_PRO.bat
```

---

## Tecnologías

| Tecnología | Uso |
|---|---|
| [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) | Interfaz gráfica con soporte dark/light mode |
| [Supabase Python](https://github.com/supabase/supabase-py) | Sincronización en la nube (Hub Pro) |
| [Pillow](https://python-pillow.org/) | Manejo de imágenes y logo |
| [matplotlib](https://matplotlib.org/) | Gráficos del Visualizador |
| [ReportLab](https://www.reportlab.com/) | Exportación a PDF |
| [pygame](https://www.pygame.org/) | Síntesis y reproducción de sonido |
| [numpy](https://numpy.org/) | Generación de tonos de audio |
| [pystray](https://github.com/moses-palmer/pystray) | Icono en bandeja del sistema |
| [PyInstaller](https://pyinstaller.org/) | Compilación a .exe |
| SQLite (stdlib) | Persistencia de datos local |

---

## Diseño visual

El sistema de diseño está centralizado en dos archivos:

- **`shared/theme.py`** — tokens de color (`COLORS["dark"]` / `COLORS["light"]`), tipografía (`TYPOGRAPHY`) y layout (`LAYOUT`)
- **`shared/components.py`** — componentes reutilizables: `HeaderFrame`, `CardFrame`, `BotonPrimario`, `BotonSecundario`, `NMToplevel`, etc.

La identidad visual se documenta en `dark-theme-tests.md` y `white-theme-tests.md` (análisis completo de neuromood.com.ar). Las herramientas de preview (`_preview_*.py`) permiten visualizar variantes de tema sin modificar las apps.

---

## Base de datos

Base de datos SQLite local en `%APPDATA%/NeuroMood/nm_data.db`, compartida entre todas las apps. Las tablas se inicializan y migran automáticamente en el primer lanzamiento. El esquema de la capa Supabase (Hub Pro) está en `supabase_schema.sql`.

---

## Manual de usuario

[`NeuroMood_Suite_Manual.pdf`](NeuroMood_Suite_Manual.pdf)
