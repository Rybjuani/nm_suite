# Protocolo De Agente - QA Visual

Cuando un agente recibe una divergencia visual debe ubicar primero el origen con
el grafo, y despues leer o editar archivos concretos. Esto evita barridos amplios
por `qa/` y reduce el riesgo de tocar infraestructura equivocada.

Nota de cierre visual: `diff_fidelity.py`, `visual_auditor_spec` y los manifests
de `capture_v8.py` son senales auxiliares. No autorizan marcar items del handoff
como PASS, STALE o completados. El gate operativo es `qa/layered_visual_compare.py`
con `qa/_mockup_canonical` y una corrida fresca completa en `qa/_captures_v8`,
mas inspeccion manual de los paneles.

## Pasos

1. Asegurar el grafo, regenerable y no versionado:

   ```bash
   graphify update qa/
   ```

2. Buscar el origen de la divergencia:

   ```bash
   graphify query "que produce SHADOW_MISMATCH"
   graphify explain "layered_visual_compare"
   graphify path "layered_visual_compare" "capture_v8"
   graphify affected "compare_pair"
   ```

3. Con los archivos o simbolos identificados, abrir y editar solo el area
   necesaria.

## Cuando No Usarlo

- Cambios triviales de un solo archivo ya conocido.
- El grafo cubre `qa/`; para otras carpetas, regenerar con `graphify update <dir>`.

## Mapa Divergencia A Verificador

| Divergencia | Verificador | Archivo |
|---|---|---|
| divergencia visual mockup vs V8 | `layered_visual_compare` | `qa/layered_visual_compare.py`, `qa/_mockup_canonical`, `qa/_captures_v8` |
| COLOR_MISMATCH / TEXT_MISSING / canvas bg | auxiliar: `visual_auditor_spec` | `qa/visual_auditor_spec.py`, specs en `qa/specs/specs.json` |
| diff de pixeles AA-aware | auxiliar: `diff_fidelity --engine odiff` | `qa/diff_fidelity.py`, `qa/odiff_runner.py` |
| SHADOW/RADIUS/GRADIENT en arbol Qt | auxiliar: `vas_introspect` con `--introspect` | `qa/vas_introspect.py` |
| hang / no cierra / hash duplicado | auxiliar: `runtime_live_probe` | `qa/runtime_live_probe.py` |
