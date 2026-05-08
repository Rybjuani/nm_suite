# NeuroMood Suite V3

Suite de 8 aplicaciones de escritorio para Windows orientadas al bienestar mental y la regulación emocional. Desarrollada en Python con CustomTkinter, basada en la identidad visual de [neuromood.com.ar](https://neuromood.com.ar).

---

## Aplicaciones

### 1. Termómetro Emocional
Registro diario del estado emocional mediante un slider de 0 a 10 (valor inicial centrado en 5). Permite agregar una nota libre por cada registro, consultar el historial del día y exportar los datos en PDF con formato de tabla.

### 2. Visualizador de Evolución
Gráficos de evolución emocional y conductual con tres períodos configurables:
- **7 días** → vista diaria
- **30 días** → agrupado por 4 semanas
- **90 días** → agrupado por 3 meses

Dos paneles independientes: estado emocional (línea + área) y activación conductual (barras apiladas por categoría). Exportación de gráficos en imagen.

### 3. Guía de Respiración
Sesiones de respiración guiada con técnica **4-7-8** (inhalar 4 s · retener 7 s · exhalar 8 s). Indicador visual animado de fase, contador de ciclos completados, duración de sesión configurable (por defecto 3 minutos) y registro automático de cada sesión en la base de datos.

### 4. Asistente de Activación
Sugiere actividades terapéuticas adaptadas al nivel de energía declarado (slider 0-10):
- **Energía baja (0-3):** conductas de activación mínima (respiración, hidratación, contacto sensorial)
- **Energía media (4-6):** actividades con mayor demanda (caminata, escritura, contacto social)
- **Energía alta (7-10):** tareas cognitivas y proyectos más complejos

Incluye retroalimentación sonora mediante síntesis de tono (pygame + numpy).

### 5. Recordatorios de Bienestar
Sistema de recordatorios con horarios programables. Se minimiza a la bandeja del sistema (pystray) y emite notificaciones sonoras en los horarios configurados. Persiste entre sesiones mediante SQLite.

### 6. Checklist de Rutina
Lista de tareas estructurada en tres secciones diarias: **Mañana**, **Tarde** y **Noche**. Historial semanal con navegación por semana. Retroalimentación sonora al completar ítems. Permite agregar, editar y eliminar tareas personalizadas.

### 7. Registro de Pensamientos
Registro estructurado en pasos para el trabajo con pensamientos automáticos:
1. Descripción de la situación
2. Emoción e intensidad
3. Pensamiento automático
4. Identificación de distorsión cognitiva (8 categorías: exageración, pensamiento dicotómico, catastrofización, etc.)
5. Pensamiento alternativo

Incluye buscador de registros anteriores por texto.

### 8. Temporizador de Actividades
Temporizador con categorías terapéuticas (**Relajación, Cognitiva, Física, Social, Autocuidado**). Duración configurable, cuenta regresiva visual con indicador circular, y registro histórico de actividades completadas. Retroalimentación sonora al finalizar.

---

## Capturas de pantalla

Las capturas de pantalla de cada aplicación se encuentran en el directorio `_doc_screenshots/`.

---

## Requisitos del sistema

- Windows 10 / 11 (64-bit)
- Python 3.10 o superior (solo para ejecución en modo desarrollo)

---

## Instalación

### Opción A — Ejecutable (usuarios finales)

Ejecutar `dist/Instalar NeuroMood Suite.exe`. El instalador crea accesos directos en el escritorio y el menú de inicio para cada aplicación.

Para desinstalar: `dist/Desinstalar NeuroMood.exe`

### Opción B — Modo desarrollo

```bash
# Clonar o copiar el directorio del proyecto
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar cualquier app individualmente
python apps/termometro/main.py
python apps/visualizador/main.py
python apps/respiracion/main.py
python apps/activacion/main.py
python apps/recordatorios/main.py
python apps/checklist/main.py
python apps/pensamientos/main.py
python apps/temporizador/main.py
```

---

## Compilación

Para compilar todos los ejecutables:

```bat
BUILD_ALL.bat
```

Para compilar solo el instalador:

```bat
BUILD_INSTALLER.bat
```

Los ejecutables se generan en el directorio `dist/`. La compilación usa PyInstaller con los archivos `.spec` de cada app.

---

## Estructura del proyecto

```
Neuromood V3/
├── apps/
│   ├── activacion/          # Asistente de Activación
│   ├── checklist/           # Checklist de Rutina
│   ├── pensamientos/        # Registro de Pensamientos
│   ├── recordatorios/       # Recordatorios de Bienestar
│   ├── respiracion/         # Guía de Respiración
│   ├── temporizador/        # Temporizador de Actividades
│   ├── termometro/          # Termómetro Emocional
│   └── visualizador/        # Visualizador de Evolución
├── shared/
│   ├── components.py        # Componentes UI reutilizables
│   ├── db.py                # Gestión de base de datos SQLite
│   ├── theme.py             # Sistema de diseño (colores, tipografía, layout)
│   └── utils.py             # Funciones auxiliares
├── dist/                    # Ejecutables compilados
├── _doc_screenshots/        # Capturas de pantalla
├── installer.py             # Instalador personalizado
├── uninstaller.py           # Desinstalador
├── requirements.txt
├── BUILD_ALL.bat
├── BUILD_INSTALLER.bat
└── IDENTIDAD_VISUAL.md      # Sistema de diseño y branding
```

Cada app es independiente y se ejecuta como proceso separado. Todas comparten la misma base de datos SQLite local y el módulo `shared/` para consistencia visual y de datos.

---

## Tecnologías

| Tecnología | Uso |
|---|---|
| [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) | Interfaz gráfica (dark mode nativo) |
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

La suite sigue la identidad visual de neuromood.com.ar: **dark mode profesional** con fondo azul marino (`#0B1928`) y acento teal (`#1EC8D4`). Tipografía Segoe UI (equivalente Windows de Roboto). Modo claro disponible como alternativa.

El sistema de diseño completo está documentado en [`IDENTIDAD_VISUAL.md`](IDENTIDAD_VISUAL.md).

---

## Base de datos

Todas las apps comparten una única base de datos SQLite local almacenada en el directorio de datos del usuario (`%APPDATA%/NeuroMood/`). Las tablas se inicializan automáticamente al primer lanzamiento de cualquier aplicación.

---

## Manual de usuario

El manual completo en PDF se encuentra en [`NeuroMood_Suite_Manual.pdf`](NeuroMood_Suite_Manual.pdf).
