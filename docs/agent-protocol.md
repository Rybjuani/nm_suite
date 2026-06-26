# Protocolo de agente — uso del grafo graphify

Cuando un agente recibe una **divergencia** (p.ej. `SHADOW_MISMATCH`,
`COLOR_MISMATCH`, `TEXT_MISSING`, un FAIL de `diff_fidelity`/`visual_auditor_spec`)
debe **consultar el grafo antes de leer archivos**, para localizar el código
responsable gastando ~94% menos tokens que leyendo todo `qa/`.

## Pasos

1. Asegurar el grafo (regenerable, no commiteado):
   ```bash
   graphify update qa/        # qa/graphify-out/graph.json
   ```
2. Buscar el origen de la divergencia:
   ```bash
   graphify query "que produce SHADOW_MISMATCH"
   graphify explain "vas_introspect"      # nodo + vecinos
   graphify path "diff_fidelity" "odiff_runner"   # camino entre nodos
   graphify affected "compare_odiff"      # qué se impacta si cambia X
   ```
3. Recién con los archivos/símbolos identificados, abrir y editar.

## Cuándo NO usarlo

- Cambios triviales de un solo archivo ya conocido.
- El grafo cubre `qa/`; para otras carpetas, regenerar con `graphify update <dir>`.

## Mapa divergencia → verificador (punto de entrada)

| Divergencia | Verificador | Archivo |
|---|---|---|
| COLOR_MISMATCH / TEXT_MISSING / canvas bg | `visual_auditor_spec` | `qa/visual_auditor_spec.py`, specs en `qa/specs/specs.json` |
| diff de píxeles (AA-aware) | `diff_fidelity --engine odiff` | `qa/diff_fidelity.py`, `qa/odiff_runner.py` |
| SHADOW/RADIUS/GRADIENT (árbol Qt) | `vas_introspect` (opt-in `--introspect`) | `qa/vas_introspect.py` |
| hang / no cierra / hash duplicado | `runtime_live_probe` | `qa/runtime_live_probe.py` |
