# qa/_mockup_canonical - Fuente canonica unica

Mirror exacto de la salida oficial del pack canonico. **NO editar a mano.**

| Campo | Valor |
|---|---|
| Mockup canonico unico | `qa/pack canonico/neuromood-mockup_reparado.html` |
| Receta oficial unica | `qa/pack canonico/generate_captures.js` |
| Salida del pack | `qa/pack canonico/capturas_test/` |
| Capturas | 86 (43 vistas x 2 temas) |
| Naming | `{app}-{view}-{theme}-{WxH}.png` |
| Integridad | sha256 + size + DOM size en `MANIFEST.json` |

**Prohibido:** `neuromood-mockup.html` (roto) y cualquier receta distinta de
`generate_captures.js`.

## Tamanos Vigentes

| Surface | Tamano | Cantidad |
|---|---:|---:|
| `window` | 960 x 600 | 76 |
| `narrow` | 520 x 600 | 6 |
| `modal` (Resumen IA) | 560 x 220 | 2 |
| `window_modal` (DBT practice sobre ventana) | 960 x 600 | 2 |

La receta falla si el DOM real del elemento capturado no coincide con el tamano
declarado. Esto evita recortes falsos donde el PNG mide bien pero no es fiel al
mockup HTML.

## Regenerar

```bash
# 1) Regenerar la salida del pack con la receta oficial.
PUPPETEER_EXECUTABLE_PATH="/c/Program Files/Google/Chrome/Application/chrome.exe" \
  node "qa/pack canonico/generate_captures.js" \
       "qa/pack canonico/neuromood-mockup_reparado.html" \
       "qa/pack canonico/capturas_test"

# 2) Espejar solo artefactos generados a la canonica que consume QA.
cp "qa/pack canonico/capturas_test"/*.png qa/_mockup_canonical/
cp "qa/pack canonico/capturas_test/INDICE_CAPTURAS.csv" qa/_mockup_canonical/
cp "qa/pack canonico/capturas_test/MANIFEST.json" qa/_mockup_canonical/

# 3) Verificar integridad:
#    - total_captures == expected_captures == 86
#    - all_sizes_match == true
#    - all_dom_sizes_match == true
```
