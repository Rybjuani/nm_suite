# Dev setup — herramientas out-of-band

Herramientas de desarrollo que **no** son dependencias del proyecto (no van en
`pyproject.toml`). Cada dev las instala en su shell.

## graphify (grafo de código para agentes)

Herramienta oficial: <https://github.com/safishamsi/graphify> (PyPI: `graphifyy`).
Genera un grafo de símbolos/relaciones que los agentes consultan en vez de leer
todos los archivos (ver `docs/agent-protocol.md`).

### Instalación (una vez)

```bash
uv tool install "git+https://github.com/safishamsi/graphify"
# binario: ~/.local/bin/graphify
```

### Generar el grafo de `qa/` (sin LLM)

```bash
graphify update qa/
# escribe qa/graphify-out/{graph.json, graph.html, GRAPH_REPORT.md}
```

`update` usa solo extracción AST (no requiere API key). **No** usar `graphify
extract` salvo que quieras extracción semántica con LLM (necesita backend/API key).

`qa/graphify-out/` está en `.gitignore`: es un artefacto regenerable, no se commitea.

### Verificación (último run)

| Métrica | Valor |
|---|---|
| Nodos | 683 |
| Edges | 1013 |
| Reducción de tokens por query (benchmark) | 17.9× (~94%) |

## odiff (diff de imágenes AA-aware)

```bash
npm install -g odiff-bin   # binario odiff
```

Lo consume `qa/odiff_runner.py` (capa odiff de `qa/layered_visual_compare.py`).

## Capturas canónicas

Receta única oficial: ver `qa/_mockup_canonical/README.md`.
