# NeuroMood V3 — Contexto para Claude Code

## Qué es esto

Plataforma clínica de bienestar mental para Windows. Arquitectura unificada post-refactorización (Mayo 2026):
- **`NeuroMood.exe`** — app del paciente con 7 módulos en una sola ventana
- **`HubProfesional.exe`** — panel del terapeuta con sincronización Supabase e IA (Groq)

## Arquitectura clave

```
app/                → plataforma paciente (main_qt.py + home_qt.py + modules/*_qt.py)
hub/                → hub profesional (main_qt.py + pacientes_qt.py + ia_asistente.py + exportar.py)
shared/             → código compartido (theme, theme_qt, components_qt, db, sync, config, identidad, installer_common)
installers/         → instalador.py, installer_pro.py, uninstaller.py, uninstaller_pro.py
assets/             → LOGO.png, NM_icon.ico, installer_icon.ico, no_symbol.ico
db/                 → supabase_schema.sql
```

## Decisiones arquitectónicas tomadas (NO revertir)

- **1 EXE paciente** — no volver a 7 apps sueltas. La carpeta `apps/` fue eliminada.
- **IA solo en Hub** — el paciente NO tiene IA. `ia_asistente.py` es exclusivo de `hub/`.
- **Historial/gráficos solo en Hub** — ningún módulo del paciente muestra historial ni stats.
- **Rutina ≠ Actividades** — son módulos distintos con responsabilidades distintas.
- **`shared/theme.py` es el source of truth** de colores, tipografía, layout y CATEGORY_COLORS.
- **`shared/identidad.py`** tiene la función canónica `generar_patient_id(nombre, pwd, install_code)` — no duplicar en installer.py.

## Stack técnico

- Python 3.12, PyQt6 6.6+
- SQLite local en `%APPDATA%\NeuroMood\nm_data.db`
- Supabase para sync (credenciales en `.env`, nunca en código)
- IA multi-proveedor para Hub (Groq, Gemini, OpenCode, Ollama Cloud) — ver `hub/ia_asistente.py`
- pystray + winotify para avisos en bandeja/notificaciones del SO
- matplotlib + pyqtgraph + reportlab para gráficos y PDF en el Hub
- google-generativeai + openai para proveedores IA alternativos
- PyInstaller para compilar a .exe

## Design System (Mayo 2026)

- Paleta premium: indigo `#6366f1` (accent), teal `#14b8a6`, violet `#a855f7`
- GRADIENTS 3-stop: indigo→teal→violet con posiciones (0.0, 0.45, 1.0)
- Componentes premium: NMButton (ripple + gradiente), NMCard (glow + noise + scale),
  NMProgressBar (shimmer), NMSkeleton (shimmer loading), NMInput (focus animation)
- Navegación sin sidebar en paciente (HomeView cards); sidebar solo en Hub
- NMHeader con `set_back_action(callback)` para botón volver
- Light mode funcional: toggle vía palette (sin setStyleSheet en path de toggle)
- Glassmorphism: `bg_glass` en overlays y panels inline (`_NuevoAvisoPanel`)

## QA & Testing

```bat
python _test_visual_auto.py       → 15 capturas de componentes core
python _test_home_auto.py         → 6 capturas de HomeView + ModuleCards
python _test_responsive_final.py  → 17 capturas responsive + light/dark
python smoke_test_runner.py       → Smoke test automático paciente/Hub
python resize_test.py             → Detección de layouts rotos en 5 resoluciones
python ui_crawler.py              → Introspección widget tree → JSON
```

## Patrones de código establecidos

- `shared/sync.py` usa lazy loading — las credenciales se leen en `_get_client()`, NO al importar el módulo
- `obtener_conexion()` en `shared/db.py` devuelve `sqlite3.Row` + WAL + busy_timeout=5000
- `hub/pacientes_qt.py` usa `assigned_tasks` y `assigned_reminders` (nombres de tablas en Supabase)
- `recurso(nombre)` en `shared/installer_common.py` busca primero en `assets/` (dev) o `sys._MEIPASS` (frozen)

## Archivos eliminados (no recrear)

- `apps/` — carpeta completa con 33 archivos legados
- `shared/theme_hybrid.py`, `shared/components_hybrid.py` — fusionados en theme.py/components.py
- `_preview_*.py` en raíz — movidos a `_dev/`
- `apps/pensamientos/ia.py` — IA eliminada del paciente
- `installer.spec`, `installer_pro.spec`, `uninstaller.spec`, `uninstaller_pro.spec` — reemplazados por flags inline en los .bat
- `AGENTS.md`, `PLAN.md`, `PLAN.txt`, `README_new.md` — contenido consolidado en README.md

## Tablas Supabase (esquema en db/supabase_schema.sql)

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

## Estabilización (Mayo 2026) — Zero-Bug Mandate

Se ejecutó una auditoría de 20 antipatrones y corrección quirúrgica en 6 fases:

### Reglas de seguridad vigentes (NO vulnerar)
- **`sip.isdeleted(self)`** obligatorio en todo `QTimer.singleShot` con lambda que capture `self`
- **`removeWidget()` antes de `deleteLater()`** en todo widget dentro de un layout
- **`with _lock:`** en toda lectura/escritura del estado global de IA (`hub/ia_asistente.py`)
- **`QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)`** en installers
- **Sin `__del__`** en widgets PyQt6 — Qt maneja parent-child cleanup
- **Sin `except Exception: pass`** en `app/modules/` — reemplazado por `logging.getLogger(__name__).exception()`
- **`stylesheet_scrollarea(modo)`** en vez de stylesheet hardcodeado en QScrollArea
- **`p.save()` / `p.restore()`** en paintEvents con múltiples cambios de estado del QPainter

### Helpers disponibles
- `label_style(modo, key)` en `shared/theme_qt.py` — shortcut para `f"color: {C(key, modo)}; background: transparent;"`
- `_log = logging.getLogger(__name__)` en todos los módulos de app/
- `NMToast.show(parent, msg, variant)` para errores visibles al usuario

### Archivos touchados en estabilización
- `shared/components_qt.py` — eliminados 3 helpers muertos (`v_spacer`, `separator`, `styled_label`), `h_spacer` conservado como stub, NMSidebar con `_theme_labels` + `sip.isdeleted` guard
- `shared/theme_qt.py` — añadido `label_style()`, `logging` en captionbar DWM, estructura try/except restaurada
- `app/modules/*.py` (7 archivos) — `import logging`, 80+ `except:pass` → `_log.exception()`, `setFixedHeight` → `setMinimumHeight` en QTextEdit, `sip.isdeleted` guards en QTimer.singleShot
- `app/home_qt.py` — `C("success", modo)` reemplaza magic hex, `stylesheet_scrollarea()`, `_eff.deleteLater()` cleanup
- `app/main_qt.py` — `logging` en sync y get_module_status
- `hub/main_qt.py` — `_AnimoIndicator` theme-aware, `sip.isdeleted` guard en thread callback, imports muertos removidos
- `hub/pacientes_qt.py` — 11 `sip.isdeleted` guards, `QObject` import, `r.get("id")` defensivo
- `hub/ia_asistente.py` — `is_available()`/`status_msg()` con `with _lock:`, guard en respuestas IA malformadas
- `installers/installer.py`, `installer_pro.py` — `processEvents(ExcludeUserInputEvents)`
