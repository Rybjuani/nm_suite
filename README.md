# NeuroMood V3

Plataforma clínica de bienestar mental para Windows. Dos ejecutables: **NeuroMood Suite.exe** para el paciente y **NeuroMood Hub Pro.exe** para el terapeuta.

---

## Requisitos del sistema

| Componente | Requisito |
|---|---|
| Sistema operativo | Windows 10 / 11 (64-bit) |
| Python (solo desarrollo) | 3.12 |
| Conexión a internet | Opcional — solo para sincronización Supabase |
| Espacio en disco | ~150 MB (instalación completa) |

---

## Instalación (usuario final)

### Paciente
1. Ejecutar **`Instalador NeuroMood Suite.exe`**
2. Ingresar nombre y contraseña (mínimo 6 caracteres)
3. Anotar el **código de instalación** generado — necesario para reinstalar
4. Elegir carpeta de instalación (por defecto: `%USERPROFILE%\NeuroMood`)

Para desinstalar: **`Desinstalador NeuroMood.exe`** dentro de la carpeta instalada, o desde *Panel de Control → Agregar o quitar programas*.

### Profesional (Hub)
1. Ejecutar **`Instalador NeuroMood Hub Pro.exe`**
2. Configurar credenciales Supabase en `.env` (ver sección Configuración)
3. Ejecutar `NeuroMood Hub Pro.exe`

---

## Desarrollo

```bash
pip install -r requirements.txt

# App paciente
python app/main_qt.py

# NeuroMood Hub Pro
python hub/main_qt.py

# Modo test interactivo sin compilar
BUILD_ALL.bat test
```

---

## Configuración

Crear `.env` en la raíz del proyecto (nunca se commitea):

```
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-clave-anon-publica
GROQ_KEY=tu-clave-groq
```

`GROQ_KEY` solo es necesaria para el Hub (IA asistente).

---

## Compilación

```bat
:: Paso 1 — compilar los 2 EXEs principales
BUILD_ALL.bat

:: Paso 2 — empaquetar instalador paciente
BUILD_INSTALLER.bat

:: Paso 3 — empaquetar instalador Hub
BUILD_INSTALLER_PRO.bat
```

Salidas:
- `dist\NeuroMood Suite.exe`
- `dist\NeuroMood Hub Pro.exe`
- `dist\Instalador NeuroMood Suite.exe` ← distribuir al paciente
- `dist\Instalador NeuroMood Hub Pro.exe` ← distribuir al profesional

---

## Estructura del proyecto

```
Neuromood V3/
├── app/                        ← plataforma paciente
│   ├── main_qt.py              ← entry point
│   ├── home_qt.py              ← home con 7 cards
│   ├── motor_activacion.py     ← motor activación conductual
│   ├── avisos_daemon.py        ← daemon de recordatorios
│   └── modules/
│       ├── animo_qt.py
│       ├── respiracion_qt.py
│       ├── registro_tcc_qt.py
│       ├── rutina_qt.py
│       ├── actividades_qt.py
│       ├── timer_qt.py
│       └── avisos_qt.py
├── hub/                        ← hub profesional
│   ├── main_qt.py              ← entry point
│   ├── pacientes_qt.py         ← gestión de pacientes
│   ├── ia_asistente.py         ← IA Groq (solo Hub)
│   └── exportar.py             ← PDF / reportes
├── shared/                     ← código compartido
│   ├── theme.py / theme_qt.py  ← colores, tipografía (source of truth)
│   ├── components_qt.py        ← componentes UI reutilizables
│   ├── db.py                   ← SQLite local
│   ├── sync.py                 ← Supabase (lazy loading)
│   ├── identidad.py            ← generar_patient_id()
│   ├── installer_common.py     ← compartido entre instaladores
│   ├── config.py               ← lectura de .env
│   └── utils.py
├── installers/                 ← instaladores y desinstaladores
│   ├── installer.py
│   ├── installer_pro.py
│   ├── uninstaller.py
│   └── uninstaller_pro.py
├── assets/                     ← iconos y logos
│   ├── LOGO.png
│   ├── NM_icon.ico
│   ├── installer_icon.ico
│   └── no_symbol.ico
├── db/
│   └── supabase_schema.sql     ← esquema de tablas Supabase
├── _dev/                       ← herramientas de desarrollo (no distribuir)
├── BUILD_ALL.bat
├── BUILD_INSTALLER.bat
├── BUILD_INSTALLER_PRO.bat
├── requirements.txt
└── .env                        ← credenciales (no commitear)
```

---

## Stack técnico

| Tecnología | Uso |
|---|---|
| Python 3.12 | Lenguaje principal |
| PyQt6 ≥6.6.0 | UI completa |
| pyqtgraph ≥0.13.0 | Gráficos en Hub |
| SQLite | Base de datos local (`%APPDATA%\NeuroMood\nm_data.db`) |
| Supabase | Sincronización cloud paciente↔Hub |
| Groq llama3-70b | IA asistente del Hub |
| pystray + winotify | Bandeja del sistema y notificaciones Windows |
| matplotlib + reportlab | Gráficos y PDFs en Hub |
| PyInstaller | Compilación a .exe |

---

## Tablas Supabase (ver `db/supabase_schema.sql`)

`patients`, `mood_records`, `breathing_sessions`, `thought_records`,
`checklist_completions`, `timer_sessions`, `reminder_logs`,
`assigned_tasks`, `assigned_reminders`, `activity_bank`, `patient_activities`

---

## Decisiones arquitectónicas (no revertir)

- **1 EXE paciente** — la carpeta `apps/` fue eliminada, no recrear.
- **IA solo en Hub** — `ia_asistente.py` es exclusivo de `hub/`. El paciente no tiene IA.
- **Historial y gráficos solo en Hub** — ningún módulo del paciente muestra historial ni estadísticas.
- **Rutina ≠ Actividades** — son módulos distintos: Rutina = prescripción del terapeuta (estática); Actividades = sugerencias adaptativas por ánimo (dinámicas).
- **`shared/theme.py`** es el source of truth de colores, tipografía y layout.
- **`shared/identidad.py`** tiene la función canónica `generar_patient_id()` — no duplicar.
- **`shared/sync.py`** usa lazy loading — credenciales se leen en `_get_client()`, no al importar.
