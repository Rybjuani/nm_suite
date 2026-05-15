# QA Report — NeuroMood V3

**Fecha**: 2026-05-15  
**Ejecutado por**: qa_full_suite.py (automatizado)  
**Resultado final**: 134 PASS / 0 BUGS / 0 WARNS  

---

## Resumen ejecutivo

Se ejecuto una pasada completa de QA/estabilizacion sobre NeuroMood V3 cubriendo:
- App Paciente (NeuroMood Suite): 7 modulos, dark/light, resize 4 resoluciones
- Hub Profesional: 4 vistas + IA mock, sidebar collapse, dark/light, resize 4 resoluciones
- 4 installers/uninstallers: instanciacion UI y navegacion de paginas seguras
- Analisis estatico de codigo (compileall + tokens + credenciales)
- Regresiones de logica (db, theme, identidad, sync, daemon)

Se encontraron y corrigieron **2 bugs reales** + **1 bug adicional** descubierto durante el setup.

---

## Bugs encontrados y corregidos

### BUG 01 — ThemeManager zombie al ejecutar multiples apps en el mismo proceso

**Archivo**: `shared/components_qt.py`  
**Linea**: 90  
**Severidad**: Crash critico (RuntimeError al inicializar cualquier componente NM_____)  

**Reproduccion**: Abrir NeuroMoodApp, cerrarla, luego abrir HubProfesional o
InstaladorNeuroMood en el mismo proceso Python. Qt destruye el C++ del singleton
ThemeManager al cerrar la primera app, pero `_inst` en Python no queda `None`, por
lo que `instance()` devuelve un wrapper zombie.

**Error**:
```
RuntimeError: wrapped C/C++ object of type ThemeManager has been deleted
  at components_qt.py:1169  ->  _tm().theme_changed.connect(self._apply_theme)
```

**Fix aplicado** — `shared/components_qt.py` linea 90:
```python
# Antes:
if cls._inst is None:
    cls._inst = cls()

# Despues:
if cls._inst is None or sip.isdeleted(cls._inst):
    cls._inst = cls()
```

Beneficio adicional: protege en produccion ante cualquier escenario donde Qt
destruya el ThemeManager antes de que el codigo Python lo detecte.

---

### BUG 02 — InstaladorNeuroMood crash al instanciar NMInput (misma causa que BUG 01)

**Archivo**: `installers/installer.py`  
**Linea**: 404  
**Severidad**: Crash al abrir el instalador en run combinado  

**Causa raiz**: `NMInput.__init__` llama a `_tm()` -> `ThemeManager.instance()` ->
retorna objeto zombie -> crash.

**Fix**: resuelto al corregir BUG 01 (mismo `sip.isdeleted` check).

---

### BUG 03 — NameError: `obtener_conexion` no importada en avisos_daemon.py

**Archivo**: `app/avisos_daemon.py`  
**Linea**: 50 (y 135, 174, 214, 229)  
**Severidad**: Runtime error silencioso en reactivacion de recordatorios a medianoche  

**Reproduccion**: El daemon llama a `_reactivar_medianoche()` cuando cambia la fecha
y falla con `NameError`. La funcion `obtener_conexion` se usaba 5 veces sin haber
sido importada nunca.

**Error detectado en consola**:
```
reactivar_medianoche: fallo al actualizar BD
NameError: name 'obtener_conexion' is not defined
```

**Fix aplicado** — `app/avisos_daemon.py` (despues del bloque sys.path):
```python
from shared.db import obtener_conexion
```

---

## Archivos modificados

| Archivo | Cambio | Linea |
|---|---|---|
| `shared/components_qt.py` | ThemeManager.instance(): check `sip.isdeleted` | 90 |
| `app/avisos_daemon.py` | Agregar `from shared.db import obtener_conexion` | 25 |

Cambios minimos: 2 lineas en total. Sin tocar DB, sync, config, ni pantallas.

---

## Resultados detallados del QA runner

### Fase 1 — Compilacion (compileall)

| Modulo | Estado |
|---|---|
| `app/` | PASS |
| `hub/` | PASS |
| `shared/` | PASS |
| `installers/` | PASS |

### Fase 2 — App Paciente (NeuroMood Suite)

| Check | Estado |
|---|---|
| Inicializacion (887x567px) | PASS |
| 7 modulos dark mode (animo, respiracion, registro, rutina, actividades, timer, avisos) | PASS x7 |
| Toggle dark->light sin crash | PASS |
| Header dark!=light (delta=635, min=60) | PASS |
| 3 modulos en light mode | PASS x3 |
| Resize 800x600, 1024x768, 1366x768, 1280x720 | PASS x4 |
| Navegacion completa a 1280x720 | PASS x7 |
| Sin widgets tamano cero | PASS en todas las vistas |
| Sin desbordamiento de widgets | PASS en todas las vistas |

### Fase 3 — Hub Profesional (NeuroMood Hub Pro)

| Check | Estado |
|---|---|
| Inicializacion | PASS |
| Vistas dashboard, pacientes, config | PASS x3 |
| DetallePacienteView mock + 4 tabs | PASS x5 |
| Sidebar collapse/expand | PASS |
| Toggle dark->light, 3 vistas en light | PASS x4 |
| Restaurar dark mode | PASS |
| Resize 1024x720, 1280x800, 1366x768, 1920x1080 | PASS x4 |
| Sin widgets tamano cero | PASS en todas las vistas |
| Sin desbordamiento de widgets | PASS en todas las vistas |

### Fase 4 — Installers / Uninstallers

| Componente | Paginas testeadas | Estado |
|---|---|---|
| InstaladorNeuroMood | p0 (Bienvenida) + p1 (Cuenta) | PASS |
| InstaladorPro | p0 (Carpeta) + p1 (pre-Instalar) | PASS |
| DesinstaladorNeuroMood | p0 (Bienvenida) | PASS |
| DesinstaladorPro | p0 (Bienvenida) | PASS |

### Fase 5 — Regresiones de logica

| Check | Estado |
|---|---|
| shared/db.py importa sin errores | PASS |
| Tokens design system completos (dark + light) | PASS |
| `generar_patient_id()` devuelve ID valido | PASS |
| shared/sync.py sin credenciales hardcodeadas | PASS |
| app/avisos_daemon.py importa sin errores | PASS |
| _MODULE_MAP contiene los 7 IDs de modulo | PASS |

---

## Advertencias estaticas (no criticas)

62 WARNs de tipo `font-size: <n>px` en los instaladores. Son **intencionales**: los
instaladores tienen su propio sistema de estilo independiente del design system V3.
No requieren accion.

Un hex adicional: `#c83040` en `installer_common.py:108` (hover boton peligroso).
Aceptable como variante darker de `error` para hover.

---

## Herramientas de QA disponibles

```
python qa_full_suite.py                  # Suite completa: Suite + Hub + Installers
python qa_full_suite.py --patient        # Solo app paciente
python qa_full_suite.py --hub            # Solo Hub Pro
python qa_full_suite.py --installers     # Solo installers UI
python qa_full_suite.py --compile        # Solo sintaxis + logica (sin UI, rapido)

python _test_audit_visual.py             # Auditoria visual completa con baselines
python _test_audit_visual.py --static    # Solo analisis estatico de codigo
python _test_audit_visual.py --update-baseline  # Regenerar referencias visuales

python _test_color_regression.py         # Regresion de colores vs design tokens
python smoke_test_runner.py --app patient
python smoke_test_runner.py --app hub
```

Los reportes automaticos de cada run se guardan en `_test_screens/qa/qa_report_<timestamp>.md`.

---

## Pendiente

- **Installers: paginas de instalacion real** — el QA no ejecuta las paginas que
  disparan la copia de archivos (requieren permisos de admin y rutas reales).
  Probar manualmente antes de distribucion.

- **Avisos daemon — integracion real** — verificar el ciclo completo del daemon
  (notificacion -> disparo -> desactivacion -> reactivacion al dia siguiente) en uso real.

- **Supabase sync** — el QA no prueba el flujo de sincronizacion real (requiere
  credenciales `.env` activas). Probar manualmente.

- **Windows limpio** — verificar checklist de distribucion de CLAUDE.md en una VM
  sin Python instalado antes de publicar.
