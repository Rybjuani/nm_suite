# qa/_mockup_canonical — Fuente canónica única (aprobada por owner)

Mirror exacto de la salida oficial del pack canónico. **NO editar a mano.**

| Campo | Valor |
|---|---|
| Mockup canónico (ÚNICO) | `qa/pack canonico/neuromood-mockup_reparado.html` |
| Receta oficial (ÚNICA) | `qa/pack canonico/generate_captures.js` |
| Salida del pack | `qa/pack canonico/capturas_test/` |
| Capturas | 86 (43 vistas × 2 temas) |
| Naming | `{app}-{view}-{theme}-{WxH}.png` |
| Integridad | sha256 + size en `MANIFEST.json` (86/86 match) |

**PROHIBIDO:** `neuromood-mockup.html` (ROTO) y cualquier receta distinta de
`generate_captures.js` (p.ej. el viejo `capture_mockup_canonical.py`).

## Regenerar (reproducible)

```bash
# 1) Regenerar la salida del pack con la receta oficial (Chrome como Chromium)
PUPPETEER_EXECUTABLE_PATH="/c/Program Files/Google/Chrome/Application/chrome.exe" \
  node "qa/pack canonico/generate_captures.js" \
       "qa/pack canonico/neuromood-mockup_reparado.html" \
       "qa/pack canonico/capturas_test"

# 2) Espejar a la canónica que consume QA
rm -rf qa/_mockup_canonical && cp -r "qa/pack canonico/capturas_test" qa/_mockup_canonical

# 3) Verificar integridad: 86/86 sha256 == MANIFEST.json
```
