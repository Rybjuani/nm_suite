# NeuroMood V3

Plataforma clínica de bienestar mental para Windows. Dos ejecutables: **NeuroMood Suite.exe** para el paciente con 7 módulos y **NeuroMood Hub Pro.exe** para el terapeuta con sincronización Supabase e IA.

---

## Requisitos del sistema

| Componente | Requisito |
|---|---|
| SO | Windows 10 / 11 (64-bit) |
| Python (solo dev) | 3.12 |
| Internet | Opcional — solo para sync Supabase |
| Disco | ~150 MB instalado |

---

## Instalación (usuario final)

### Paciente
1. Ejecutar **`Instalador NeuroMood Suite.exe`**
2. Ingresar nombre y contraseña (mín 6 caracteres)
3. Anotar el **código de instalación** generado
4. Elegir carpeta (por defecto: `%USERPROFILE%\NeuroMood`)

Desinstalar: **`Desinstalador NeuroMood.exe`** en la carpeta instalada, o Panel de Control.

### Profesional (Hub)
1. Ejecutar **`Instalador NeuroMood Hub Pro.exe`**
2. Configurar `.env` con credenciales Supabase
3. Ejecutar `NeuroMood Hub Pro.exe`

---

## Desarrollo

```bash
pip install -r requirements.txt

# App paciente
python app/main_qt.py

# Hub Profesional
python hub/main_qt.py

# Modo test interactivo sin compilar
BUILD_ALL.bat test
```

---

## Configuración

Crear `.env` en la raíz (nunca se commitea):

```
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-clave-anon-publica
GROQ_KEY=tu-clave-groq
```

`GROQ_KEY` solo para el Hub (IA asistente). Gemini, OpenAI y Ollama Cloud opcionales.

---

## Compilación

```bat
BUILD_ALL.bat              → NeuroMood Suite + NeuroMood Hub Pro (onedir, arranque <1s)
BUILD_ALL.bat release      → onefile para distribución (más lento al abrir)
BUILD_INSTALLER.bat        → Instalador NeuroMood Suite
BUILD_INSTALLER_PRO.bat    → Instalador NeuroMood Hub Pro
```

Salidas:
- `dist\NeuroMood Suite\NeuroMood Suite.exe`
- `dist\NeuroMood Hub Pro\NeuroMood Hub Pro.exe`
- `dist\Instalador NeuroMood Suite\Instalador NeuroMood Suite.exe`
- `dist\Instalador NeuroMood Hub Pro\Instalador NeuroMood Hub Pro.exe`

---

## Estructura del proyecto

```
NeuroMood V3/
├── app/                        ← paciente
│   ├── main_qt.py              ← entry point
│   ├── home_qt.py              ← home con 7 ModuleCards
│   ├── motor_activacion.py     ← motor de activación conductual
│   ├── avisos_daemon.py        ← daemon de recordatorios
│   └── modules/
│       ├── animo_qt.py         ← registro de ánimo con slider + emoji
│       ├── respiracion_qt.py   ← respiración guiada 4-7-8 con arco
│       ├── registro_tcc_qt.py  ← diario de pensamientos TCC
│       ├── rutina_qt.py        ← checklist diario
│       ├── actividades_qt.py   ← sugerencias según ánimo
│       ├── timer_qt.py         ← temporizador con canvas circular
│       └── avisos_qt.py        ← recordatorios con daemon
├── hub/                        ← Hub Profesional
│   ├── main_qt.py              ← entry point
│   ├── pacientes_qt.py         ← gestión de pacientes + gráficos
│   ├── ia_asistente.py         ← IA multi-proveedor (Groq/Gemini/OpenAI)
│   └── exportar.py             ← PDF / reportes
├── shared/                     ← código compartido
│   ├── theme.py / theme_qt.py  ← design system (source of truth)
│   ├── components_qt.py        ← NMButton, NMCard, NMInput, etc.
│   ├── db.py                   ← SQLite local
│   ├── sync.py                 ← Supabase (lazy loading)
│   ├── identidad.py            ← generar_patient_id()
│   ├── installer_common.py     ← paleta + helpers para instaladores
│   ├── config.py               ← lectura de .env
│   └── utils.py
├── installers/                 ← instaladores / desinstaladores
│   ├── installer.py            ← Instalador NeuroMood Suite
│   ├── installer_pro.py        ← Instalador NeuroMood Hub Pro
│   ├── uninstaller.py          ← Desinstalador NeuroMood
│   └── uninstaller_pro.py      ← Desinstalador NeuroMood Hub Pro
├── assets/                     ← iconos y logo
├── db/supabase_schema.sql      ← esquema Supabase
├── BUILD_ALL.bat
├── BUILD_INSTALLER.bat
├── BUILD_INSTALLER_PRO.bat
├── requirements.txt
└── .env
```

---

## Stack técnico

| Tecnología | Uso |
|---|---|
| Python 3.12 | Lenguaje |
| PyQt6 ≥6.6 | UI completa |
| pyqtgraph ≥0.13 | Gráficos en Hub |
| scipy | Interpolación spline en gráfico Hub (opcional, fallback lineal) |
| SQLite | DB local (`%APPDATA%\NeuroMood\nm_data.db`) |
| Supabase | Sync cloud paciente↔Hub |
| Groq / Gemini / OpenAI | IA asistente Hub |
| pystray + winotify | Bandeja y notificaciones Windows |
| reportlab | PDFs en Hub |
| PyInstaller | Compilación a .exe |

---

## Design System

### SessionColor (aura dinámica)
Color aleatorio cyan o violeta al iniciar sesión. Aura radial en fondo de módulos, glow en hover de cards, barra izquierda con gradiente.

### Scrollbars Premium Glass
Handle gradiente `#00F2FF→#4A00E0`, track translúcido, 6px ancho, cápsula 3px, sin flechas.

### Componentes
**Base**: `NMButton`, `NMButtonOutline`, `NMCard`, `NMInput`, `NMProgressBar`, `NMToggle`, `NMToast`, `NMSkeleton`, `NMFadeWidget`, `NMHeader`, `NMSidebar`, `NMModule`, `NMEmptyState`

**Estructura**: `NMStatusChip`, `NMSectionCard`, `NMFormField`, `NMSegmentedChoice`

**V3 — App Paciente**: `NMStreakBadge`, `NMWelcomeBar`, `NMEmojiPicker`, `NMWaveChart`, `NMPhaseChip`, `NMCycleRing`, `NMCalmBadge`, `NMTCCStepper`, `NMHeatBar`, `NMRoutineSection`, `NMDayNote`, `NMMoodContextHeader`, `NMCategoryFilter`, `NMAvisoCard`, `NMProgressLine`

**V3 — Hub Profesional**: `NMFeaturedCard`, `NMModuleRing`, `NMChatBubble`, `NMTypingDots`, `NMSyncOrb`

**V3 — Instaladores**: `NMInstallStepper`, `NMDataPreserveCard`

Todos los componentes V3 se auto-suscriben a `ThemeManager.theme_changed` y manejan dark/light mode internamente. Ver `shared/components_qt.py` para APIs completas.

### Logo
`assets/LOGO.png` con sombra blur 28px, glow radial animado, recolor automático en light mode.

---

## Tablas Supabase

`patients`, `mood_records`, `breathing_sessions`, `thought_records`, `checklist_completions`, `timer_sessions`, `reminder_logs`, `assigned_tasks`, `assigned_reminders`, `activity_bank`, `patient_activities`

---

## Decisiones arquitectónicas (no revertir)

- **1 EXE paciente** — no recrear `apps/`
- **IA solo en Hub** — `ia_asistente.py` exclusivo de `hub/`
- **Historial solo en Hub** — módulos paciente no muestran stats
- **Rutina ≠ Actividades** — checklist estático vs sugerencias dinámicas
- **`shared/theme.py`** source of truth de colores y tipografía
- **`shared/identidad.py`** función canónica `generar_patient_id()`
- **Supabase lazy** — `hub/main_qt.py` importa bajo demanda (arranque 65ms)
- **`--onedir`** por defecto en builds (arranque <1s, sin extracción a temp)