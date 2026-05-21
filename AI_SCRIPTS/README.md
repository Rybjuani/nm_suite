# AI_SCRIPTS - Reglas Para Agentes IA

Esta es la carpeta única para scripts, automatizaciones, QA, capturas, auditorías, generadores, mantenimiento y utilidades del proyecto NeuroMood.

Reglas obligatorias:

- Buscar primero aquí antes de crear un script nuevo.
- Crear scripts nuevos solamente dentro de `AI_SCRIPTS/`, no en la raíz.
- No generar basura en la raíz del proyecto: nada de logs, capturas, reportes, zips, specs, builds temporales ni archivos auxiliares sueltos.
- Si un flujo necesita salidas temporales, crear una subcarpeta clara dentro de `AI_SCRIPTS/` o una carpeta específica del proyecto, y limpiarla al terminar cuando corresponda.
- Mantener `dist/` como salida oficial de ejecutables.
- Mantener `AI_PROJECT_CONTEXT.md` como única documentación viva del proyecto.

Scripts principales:

- `build_neuromood.py`: build oficial completo usado por `BUILD_NEUROMOOD.bat`.
- `generate_neuromood_manuals.py`: genera los dos manuales PDF finales.
- `qa_exe_capture.py`: capturas QA de EXEs reales.
- `qa_full_suite.py`: recorrido QA amplio.
- `smoke_test_runner.py`: smoke tests.

