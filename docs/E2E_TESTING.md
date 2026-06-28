# E2E Testing

## Objetivo

El sistema E2E cubre flujos UX reales de la app PyQt6 con servicios externos mockeados: Suite paciente, Hub profesional, smoke de arranque y evidencia visual en fallos.

## Stack

- `pytest`
- `pytest-qt`
- `PyQt6`
- fakes locales para Supabase, IA y sync
- Page Object Pattern
- smoke tests por subprocess

No requiere dependencias nuevas.

## Estructura

- `tests/e2e/conftest.py`: markers, fixtures, auto-screenshot.
- `tests/e2e/_helpers/qt_helpers.py`: busqueda e interaccion con widgets Qt.
- `tests/e2e/fakes/`: `FakeSupabase`, `FakeIAResponder`, parches de sync.
- `tests/e2e/pages/`: Page Objects de Suite y Hub.
- `tests/e2e/suite/`: flujos de Suite paciente.
- `tests/e2e/hub/`: flujos del Hub profesional.
- `tests/e2e/smoke/`: arranque subprocess de entry points.
- `scripts/e2e/`: wrappers PowerShell.

## Como Correr

Todo:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\e2e -q
```

Suite:

```powershell
.\scripts\e2e\run-e2e.ps1 -Suite
```

Hub:

```powershell
.\scripts\e2e\run-e2e.ps1 -Hub
```

Smoke:

```powershell
.\scripts\e2e\run-e2e-smoke.ps1
```

Con reporte JUnit:

```powershell
.\scripts\e2e\run-e2e.ps1 -Report
```

## Fakes

`FakeSupabase` implementa tablas en memoria con `select`, `insert`, `update`, `delete`, `upsert`, filtros y `execute`.

`FakeIAResponder` usa colas para respuestas de resumen, asignaciones y actividades, mas helpers para fallar la siguiente llamada.

`sync_fake.py` evita hilos/red en tests que ejercitan guardados locales.

## Page Objects

Los Page Objects son delgados: solo exponen acciones usadas por tests. Si un widget no tiene API publica estable, el Page Object usa atributos privados verificados previamente con `rg -n "self\._"`.

## Screenshots

En fallos de fase `call`, el hook guarda PNG en:

```text
reports/e2e/screenshots/
```

Para elegir el widget capturado, usar el fixture `e2e_screenshot(widget)`.

## Troubleshooting

- Si un test Qt queda inestable, verificar timers activos y detenerlos en `close()` del Page Object.
- Si un selector falla, revisar `accessibleName`, texto visible y clase real del componente.
- Si smoke falla, revisar `stderr`; cualquier `Traceback` es fallo.
- Si una ruta toca red o Supabase real, aplicar fake antes de instanciar la vista.

## Limitaciones

- `NM_VISUAL_QA=1` estabiliza datos y evita sync en varios modulos; no debe usarse para validar persistencia real.
- Los fakes cubren el contrato usado por E2E, no todo Supabase.
- PDF se prueba llamando `_generar` directo para evitar thread y `os.startfile`.

## Agregar Tests Nuevos

1. Verificar atributos privados con `rg -n "self\._" archivo.py`.
2. Preferir Page Objects existentes.
3. Usar fakes locales para red, IA y sync.
4. Mantener el test enfocado en una conducta observable.
5. Ejecutar la carpeta especifica y luego `tests\e2e` completo.
