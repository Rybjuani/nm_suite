# Episode: E4_H_MODALES_ia_pdf

## Identificación

- **ID episodio:** 20260621_201112_E4_H_MODALES_ia_pdf
- **Fecha:** 2026-06-21
- **Repo objetivo:** nm_suite (`main` @ `7efd3ce`)
- **Perfil usado:** nm_suite_safe_bugfix
- **Agente/Modelo:** Codex

## Objetivo

Cerrar el cluster E4-H-MODALES para Hub Detalle: bloquear por contrato la estructura visual
y lifecycle del modal de Resumen IA/PDF sin modificar IA, PDF, sync ni datos clinicos.

## No objetivos

- No cambiar prompts, proveedores IA, generacion PDF ni fetch de datos.
- No redisenar Plan terapeutico ni Pacientes.
- No tocar primitivas globales salvo evidencia directa.

## Presupuesto

- **Presupuesto maximo:** 1 contrato nuevo + fix minimo si falla + validacion focal + probe
  Hub `detalle` light/dark.

## Scope

### Archivos permitidos

- `hub/pacientes_qt.py`
- `tests/test_hub_visual_contract.py`
- `agent_harness/episodes/20260621_201112_E4_H_MODALES_ia_pdf/EPISODE.md`

### Archivos prohibidos

- `hub/ia_asistente.py`, `hub/exportar.py`, DB/sync/logica clinica/auth/build/dist/installers.
- Todo archivo no listado arriba.

## Estado inicial

- **Baseline antes:** `main` en `7efd3ce`, worktree limpio antes de crear este episodio.

## Plan

- **Plan corto:**
  1. Agregar contrato focal del modal Resumen IA.
  2. Reproducir fallo si el contrato descubre deuda.
  3. Aplicar fix minimo en `hub/pacientes_qt.py` si corresponde.
  4. Validar contrato focal + tests relacionados.
  5. Validar runtime probe Hub detalle light/dark.

## Ejecución

- **Cambios realizados:**
  - `hub/pacientes_qt.py`: `Resumen IA` deja de abrir `QDialog.exec()` y usa `NMDialog`
    como overlay hijo de la ventana, con scrim/scale canónicos y cierre no bloqueante.
  - `tests/test_hub_visual_contract.py`: contrato E4-H-MODALES para bloquear overlay
    `NMDialog`, ancho 480, texto renderizado y limpieza al cerrar.

## Validación

- **Validación ejecutada:**
  - `.\.venv\Scripts\python.exe -m pytest tests\test_hub_visual_contract.py -q`
    → 9 passed.
  - `.\.venv\Scripts\python.exe -m pytest tests\test_rb7_pdf_consistency.py tests\test_component_visual_contract.py -k "dialog or toast or detalle_paciente_view_tiene_boton_exportar_pdf or on_exportar_pdf" -q`
    → 6 passed, 29 deselected.
  - `.\.venv\Scripts\python.exe qa\runtime_live_probe.py --app hub --view detalle --theme both`
    → OK=2, DEFECTS_FOUND=0, FAILED=0.
  - `.\.venv\Scripts\python.exe -m ruff check hub\pacientes_qt.py tests\test_hub_visual_contract.py`
    → All checks passed.

## Evidencia

- **Antes:** `Resumen IA` usaba `QDialog` nativo con `NMDialogScaffold`, sin scrim ni
  animacion `.96 -> 1`, y bloqueaba con `exec()`.
- **Después:** `Resumen IA` usa `NMDialog.show_centered()`; contrato verifica overlay
  visible, escala inicial canonica, texto IA y cleanup de `_resumen_dialog`.

## Resultado

- **Diff stat:** `hub/pacientes_qt.py` y `tests/test_hub_visual_contract.py` + este episodio.
- **Archivos tocados:**
  - `hub/pacientes_qt.py`
  - `tests/test_hub_visual_contract.py`
  - `agent_harness/episodes/20260621_201112_E4_H_MODALES_ia_pdf/EPISODE.md`
- **Commit:** pendiente
- **Deuda restante:** E4-H-MODALES cerrado para Resumen IA. No se modifico PDF porque sus
  flujos funcionales ya quedaron verdes; visual review humana sigue pendiente para OLA 5.

## Decisión final

- [x] Commit
- [ ] Rollback
- [ ] Pedir revisión
- [ ] Descartar
