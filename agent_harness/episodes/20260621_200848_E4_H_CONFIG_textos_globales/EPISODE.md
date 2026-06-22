# Episode: E4_H_CONFIG_textos_globales

## Identificación

- **ID episodio:** 20260621_200848_E4_H_CONFIG_textos_globales
- **Fecha:** 2026-06-21
- **Repo objetivo:** nm_suite (`main` @ `d75cd41`)
- **Perfil usado:** nm_suite_safe_bugfix
- **Agente/Modelo:** Codex

## Objetivo

Cerrar el cluster Hub Config/Textos globales preparado en el checkpoint: contratos de
tipografia serif del titulo, boton Guardar deshabilitado al iniciar y presencia de busqueda
+ filtro de modulos, sin tocar seams de persistencia/sync.

## No objetivos

- No modificar logica de guardado, validacion clinica, DB, sync ni auth.
- No re-trabajar Pacientes/Detalle ni otros clusters Hub/Suite.
- No perseguir SSIM ni hacer polish global.

## Presupuesto

- **Presupuesto maximo:** 1 reproduccion focal + fix acotado si falla + validacion focal +
  probe del cluster si el runtime lo permite.

## Scope

### Archivos permitidos

- `hub/config_global_texts.py`
- `tests/test_hub_visual_contract.py`
- `agent_harness/episodes/20260621_200848_E4_H_CONFIG_textos_globales/EPISODE.md`

### Archivos prohibidos

- DB/sync/logica clinica/auth/build/dist/installers.
- Todo archivo no listado arriba.

## Estado inicial

- **Baseline antes:** `main` en `d75cd41`, worktree limpio antes de crear este episodio.

## Plan

- **Plan corto:**
  1. Reproducir con `pytest tests/test_hub_visual_contract.py -k hub_config_textos`.
  2. Leer solo `hub/config_global_texts.py` en las zonas del cluster.
  3. Aplicar fix minimo si hay contrato roto.
  4. Validar test focal y probe Hub/config si aplica.
  5. Cerrar con diff/stat/deuda.

## Ejecución

- **Cambios realizados:**
  - No se tocaron archivos de producto: los contratos sembrados por `d75cd41` ya estaban
    satisfechos por `hub/config_global_texts.py`.

## Validación

- **Validación ejecutada:**
  - `.\.venv\Scripts\python.exe -m pytest tests\test_hub_visual_contract.py -k hub_config_textos -q`
    → 3 passed, 5 deselected.
  - `.\.venv\Scripts\python.exe qa\runtime_live_probe.py --app hub --theme both --all`
    → OK=4, DEFECTS_FOUND=0, FAILED=0.

## Evidencia

- **Antes:** contratos E4-H-CONFIG agregados en `tests/test_hub_visual_contract.py` por
  checkpoint `d75cd41`.
- **Después:** contratos focales verdes; probe Hub light/dark verde para `pacientes` y
  `detalle`. El probe no expone una vista separada de Textos globales.

## Resultado

- **Diff stat:** solo este `EPISODE.md`.
- **Archivos tocados:**
  - `agent_harness/episodes/20260621_200848_E4_H_CONFIG_textos_globales/EPISODE.md`
- **Commit:** `7efd3ce`
- **Deuda restante:** sin deuda accionable en E4-H-CONFIG. E4-H-MODALES quedó cerrado en
  `4059a74`; E5-FIDELITY quedó cerrado en `c0c692e`.

## Decisión final

- [x] Commit
- [ ] Rollback
- [ ] Pedir revisión
- [ ] Descartar
