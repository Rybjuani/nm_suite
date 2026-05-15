# NeuroMood V3 — Contexto para Claude Code

## Qué es esto

Plataforma clínica de bienestar mental para Windows. Arquitectura unificada post-refactorización (Mayo 2026):
- **`NeuroMood Suite.exe`** — app del paciente con 7 módulos en una sola ventana
- **`NeuroMood Hub Pro.exe`** — panel del terapeuta con sincronización Supabase e IA

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
- **`shared/identidad.py`** tiene la función canónica `generar_patient_id(nombre, pwd, install_code)`.

### Seguridad (Junio 2026)

- `guardar_password(pwd, install_code)` → PBKDF2-SHA256 (100k iteraciones, salt = install_code).
- `obtener_password_hash(install_code)` → hash almacenado con auto-migración de texto plano.
- `.env` NO se bundlea en instaladores públicos; credenciales reales solo por `%APPDATA%` o variables de entorno. Ver `docs/SECURITY_NOTES.md`.

## Stack técnico

- Python 3.12, PyQt6 6.6+
- SQLite local en `%APPDATA%\NeuroMood\nm_data.db`
- Supabase para sync (credenciales en `.env`, nunca en código)
- IA multi-proveedor para Hub (Groq, Gemini, OpenCode, Ollama Cloud) — ver `hub/ia_asistente.py`
- pystray + winotify para avisos en bandeja/notificaciones del SO
- pyqtgraph + reportlab para gráficos y PDF en el Hub
- PyInstaller para compilar a .exe (--onedir por defecto, arranque <1s)

## Design System (Mayo 2026)

- Paleta premium: indigo `#6366f1` (accent), teal `#14b8a6`, violet `#a855f7`
- GRADIENTS 3-stop: indigo→teal→violet con posiciones (0.0, 0.45, 1.0)
- Componentes premium: NMButton (ripple + gradiente), NMCard (glow + noise + hover aura),
  NMProgressBar (shimmer), NMSkeleton (shimmer loading), NMInput (focus animation)
- Navegación sin sidebar en paciente (HomeView cards); sidebar solo en Hub
- NMHeader con `set_back_action(callback)` para botón volver
- Light mode funcional: toggle vía palette + stylesheet_base re-aplicado en ambos modos
- Glassmorphism: `bg_glass` en overlays y panels inline (`_NuevoAvisoPanel`)

### SessionColor — Aura dinámica

- Singleton `SessionColor` en `shared/theme_qt.py` — elige aleatoriamente cyan `#00F2FF` o violet `#7367F0` al iniciar la sesión
- **Aura radial**: `NMModule.paintEvent` y `DashboardView.paintEvent` dibujan un gradiente radial desde centro-izquierda (`w*0.2, h*0.5`, radio `w*0.85`) con alpha 20-30
- **Hover glow**: `NMCard` y `ModuleCard` renderizan 3 capas concéntricas de `drawRoundedRect` con alpha decreciente en hover
- **Barra izquierda**: gradiente vertical con session color en ambas cards
- **Paleta**: dark `cyan=#00F2FE, violet=#7367F0` / light `cyan=#89F7FE, violet=#E0C3FC`

### Scrollbars Premium Glass

- Handle: gradiente `#00F2FF → #4A00E0`, borde `1px solid #00F2FF`, `border-radius: 3px`
- Track: `rgba(255,255,255,0.05)`, 6px ancho/alto fijo
- Hover: gradiente `#E0FFFF → #7B2FF7`, borde `1px solid #E0FFFF`
- Sin flechas (0px)
- Aplicado en `stylesheet_base()`, `stylesheet_scrollarea()`, y `stylesheet_installer()`

### Logo

- `_LogoLabel` (header paciente) y `add_logo()` (sidebar Hub) cargan `assets/LOGO.png`
- Sombra `QGraphicsDropShadowEffect` con blur 28px + alpha 30
- Recoloreo automático en light mode vía `recolorear_logo_light()`
- Glow radial animado (breathing) de 3s

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

## Build

```bat
BUILD_ALL.bat              → NeuroMood Suite.exe + NeuroMood Hub Pro.exe (onedir, arranque <1s)
BUILD_ALL.bat release      → onefile para distribucion (mas lento al abrir)
BUILD_ALL.bat test         → correr sin compilar (dev)
BUILD_INSTALLER.bat        → Instalador NeuroMood Suite
BUILD_INSTALLER_PRO.bat    → Instalador NeuroMood Hub Pro
```

Flags de compilación: `--onedir` (default), `--clean`, `--optimize 2`, `--log-level WARN`, `--noconfirm`.

## Estabilización (Mayo 2026) — Zero-Bug Mandate

Se ejecutó una auditoría de 20 antipatrones y corrección quirúrgica.

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
- `NMToast.show(parent, msg, variant)` para feedback visual al usuario

### Módulos — fixes clave

| Módulo | Fixes |
|---|---|
| **Ánimo** | `_on_theme` con recarga de historial, light mode funcional |
| **Respiración** | `_on_theme` propaga tema al círculo, eliminado "●" inicial y "Calm/60 BPM", crash `_breath→_circle` corregido |
| **Registro TCC** | `_on_theme` con recarga de stylesheets, 3 textareas expandibles |
| **Rutina** | `_on_theme` actualiza checkboxes, nota diaria con toast + readonly hasta día siguiente, tareas deshabilitadas al completar con beep |
| **Actividades** | `NMToast` al marcar actividad, botones exclusivos (no múltiple selección), `_on_theme` |
| **Temporizador** | Input de nombre de actividad, toast al finalizar con nombre, auto-restore de ventana minimizada |
| **Avisos** | Validación de hora expirada, daemon deshabilita recordatorios tras disparo + reactiva a medianoche, light mode con `_load_reminders`, reset progress/counter al vaciar |

### Hub — fixes clave

- Supabase lazy-import (arranque 65ms vs 1200ms)
- Verificación de conexión real con query antes de mostrar "Conectado"
- Toast feedback en Reconectar y Actualizar
- `_AnimoIndicator` theme-aware sin condición de parent
- Sidebar logo con recolor automático light/dark
- Barra de tema duplicada eliminada de Config
- Dashboard responsive grid con `_rebuild_dash_grid()`
- Empty state sin skeletons
- `_datos_cache` sincronizado con `_datos_ref.cache` para PDF export

### Installers — fixes clave

- Nombres: "Instalador NeuroMood Suite" + "Instalador NeuroMood Hub Pro" + "Desinstalador NeuroMood" + "Desinstalador NeuroMood Hub Pro"
- Los 4 heredan de `InstallerShell` (clase base común)
- Íconos de acceso directo corregidos (sin atributo oculto)
- `_on_done` con navegación manual para leer logs
- Copytree solo cuando el nombre de carpeta coincide con el .exe (onedir/onefile seguro)
- `os._exit(0)` reemplazado por cierre limpio con toast
- `vaciar_carpeta` ahora borra directorio raíz + limpia AppData/NeuroMoodPro
- Titulo siempre dark mode (sin flash)
- `btn_ant` oculto en página 0
- Conservar registros: card premium con toggle switch gradiente
- Limpieza de residuos: `dist/`, `build/`, `.spec` eliminados en cada build

### Nuevos componentes (Junio 2026)

| Componente | Archivo | Uso |
|---|---|---|
| `NMStatusChip` | `shared/components_qt.py` | Pill de estado con color semántico |
| `NMSectionCard` | `shared/components_qt.py` | Card con título + `content_layout()` |
| `NMFormField` | `shared/components_qt.py` | Label + input en fila horizontal |
| `NMSegmentedChoice` | `shared/components_qt.py` | Grupo de botones con selección exclusiva |
| `responsive_columns()` | `shared/components_qt.py` | Helper de columnas responsive |
| `InstallerShell` | `shared/installer_common.py` | Clase base para los 4 instaladores |

### Reglas de componentes

- **NMButtonOutline**: `toggleable=False` por defecto. Solo alterna estado si `toggleable=True`.
- **Scrollbars**: Tokenizadas con `C("teal")`/`C("accent")`/`C("violet")`. Sin colores neón hardcodeados.
- **Círculos**: `_BreathingCircle` y `_TimerCanvas` usan `setMinimumSize` + `Expanding` + escala dinámica en `paintEvent`.
- **Aura**: `SessionColor` (cyan/violet aleatorio) + `NMModule.paintEvent` / `DashboardView.paintEvent` con gradiente radial.

### QA — Tests automáticos

```bat
python smoke_test_runner.py --app patient    → 31/31 PASS
python smoke_test_runner.py --app hub         → 16/16 PASS
python _test_visual_auto.py                   → 15/15 PASS
python _test_home_auto.py                     → 6/6 PASS
python _test_responsive_final.py              → 17/17 PASS
```

## Distribución

### Windows limpio (sin Python) — checklist de prueba

1. Instalar Suite: ejecutar `Instalador NeuroMood Suite.exe`
2. Abrir Suite: ejecutar `NeuroMood Suite.exe` desde carpeta instalada
3. Instalar Hub Pro: ejecutar `Instalador NeuroMood Hub Pro.exe`
4. Abrir Hub Pro: ejecutar `NeuroMood Hub Pro.exe`
5. Desinstalar Suite: `Desinstalador NeuroMood.exe`
6. Desinstalar Hub: `Desinstalador NeuroMood Hub Pro.exe`
7. Verificar accesos directos en Escritorio y Menú Inicio
8. Verificar `%APPDATA%\NeuroMood\` (debe quedar vacío o eliminado tras desinstalar)
9. Verificar `%APPDATA%\NeuroMoodPro\` (Hub)

### Build para distribución

```bat
BUILD_ALL.bat              → compila Suite + Hub (onedir)
BUILD_ALL.bat release      → onefile (más lento al abrir, .exe único)
BUILD_INSTALLER.bat        → empaqueta instalador Suite
BUILD_INSTALLER_PRO.bat    → empaqueta instalador Hub
```

**IMPORTANTE**: Los instaladores públicos no deben bundlear `.env`.
Verificar que no exista `.env` dentro de `dist\Instalador NeuroMood Suite\_internal\` ni `dist\Instalador NeuroMood Hub Pro\_internal\`.
Ver `docs/SECURITY_NOTES.md`.
