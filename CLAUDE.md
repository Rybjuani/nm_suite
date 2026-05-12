# NeuroMood V3 — Contexto para Claude Code

## Qué es esto

Plataforma clínica de bienestar mental para Windows. Arquitectura unificada post-refactorización (Mayo 2026):
- **`NeuroMood.exe`** — app del paciente con 7 módulos en una sola ventana
- **`HubProfesional.exe`** — panel del terapeuta con sincronización Supabase e IA (Groq)

## Arquitectura clave

```
app/            → plataforma paciente (main.py + home.py + modules/*.py)
hub/            → hub profesional (main.py + pacientes.py + visualizacion.py + ia_asistente.py + exportar.py)
shared/         → código compartido (theme, components, db, sync, config, identidad, base_module)
installer.py    → instalador paciente (4 páginas, 1 EXE)
hub/            → hub profesional
```

## Decisiones arquitectónicas tomadas (NO revertir)

- **1 EXE paciente** — no volver a 7 apps sueltas. La carpeta `apps/` fue eliminada.
- **IA solo en Hub** — el paciente NO tiene IA. `ia_asistente.py` es exclusivo de `hub/`.
- **Historial/gráficos solo en Hub** — ningún módulo del paciente muestra historial ni stats.
- **Rutina ≠ Actividades** — son módulos distintos con responsabilidades distintas.
- **`shared/theme.py` es el source of truth** de colores, tipografía, layout y CATEGORY_COLORS.
- **`shared/identidad.py`** tiene la función canónica `generar_patient_id(nombre, pwd, install_code)` — no duplicar en installer.py.

## Stack técnico

- Python 3.10+, CustomTkinter 5.2+
- SQLite local en `%APPDATA%\NeuroMood\nm_data.db`
- Supabase para sync (credenciales en `.env`, nunca en código)
- Groq llama3-70b para IA del Hub (clave `GROQ_KEY` en `.env`)
- pystray + winotify para avisos en bandeja/notificaciones del SO
- matplotlib + reportlab para gráficos y PDF en el Hub
- PyInstaller para compilar a .exe

## Patrones de código establecidos

- Todos los módulos del paciente heredan de `shared/base_module.py` → `NMModule`
- `ThemeManager(self, self._modo)` — el primer argumento es la ventana root (widget), NO el string del modo
- `shared/sync.py` usa lazy loading — las credenciales se leen en `_get_client()`, NO al importar el módulo
- `obtener_conexion()` en `shared/db.py` devuelve `sqlite3.Row` + WAL + busy_timeout=5000
- Canvas de gradiente: usar `draw_gradient_arc()` y `draw_glow_arc()` de `shared/components.py`
- `matplotlib.use("TkAgg")` se llama UNA SOLA VEZ al importar `hub/visualizacion.py`, no en cada función
- `hub/pacientes.py` usa `assigned_tasks` y `assigned_reminders` (nombres de tablas en Supabase)

## Archivos eliminados (no recrear)

- `apps/` — carpeta completa con 33 archivos legados
- `shared/theme_hybrid.py`, `shared/components_hybrid.py` — fusionados en theme.py/components.py
- `_preview_*.py` en raíz — movidos a `_dev/`
- `apps/pensamientos/ia.py` — IA eliminada del paciente

## Tablas Supabase (esquema en supabase_schema.sql)

`patients`, `mood_records`, `breathing_sessions`, `thought_records`,
`checklist_completions`, `timer_sessions`, `reminder_logs`,
`assigned_tasks`, `assigned_reminders`, `activity_bank`, `patient_activities`

## Build

```bat
BUILD_ALL.bat           → NeuroMood.exe (dist/) + HubProfesional.exe (dist/pro/)
BUILD_INSTALLER.bat     → Instalar NeuroMood.exe
BUILD_INSTALLER_PRO.bat → Instalar NeuroMood Hub Profesional.exe
BUILD_ALL.bat test      → correr sin compilar (dev)
```
