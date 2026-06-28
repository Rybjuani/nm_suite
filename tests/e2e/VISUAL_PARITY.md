# E2E Visual Parity

El E2E visual compara una captura real de Qt contra la fuente canonica
`qa/_mockup_canonical/MANIFEST.json`.

## Uso En Page Objects

```python
page.assert_visual_parity("hub:pacientes@light")
```

Esto hace tres cosas:

- guarda la captura E2E normal en `reports/e2e/screenshots`;
- resuelve la superficie contra `qa/_mockup_canonical`;
- escribe `result.json` y un PNG comparativo en `reports/e2e/visual_parity`.

## Decisiones Del Reparador

- `PAIRING_FIX`: la captura no corresponde al canonico actual. Revisar
  `surface_key`, tema, tamano, selector, modal o UI transitoria antes de tocar
  producto.
- `FIX_PRODUCT_STRONG`: delta grande. Empezar por layout, estado, modal,
  widget faltante o estructura general.
- `FIX_PRODUCT_REVIEW`: delta localizado. Revisar texto, wrap, iconos, color,
  spacing o tipografia dentro de las regiones marcadas.
- `RENDER_NOISE_OK`: ruido pequeno de rasterizado. No pide cambio de producto.

## Runner

```powershell
.\scripts\e2e\run-e2e-visual.ps1
```

Los artefactos quedan bajo `reports/`, que es regenerable e ignorado por git.
