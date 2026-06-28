# Recalibracion Canonica Del Mockup - 2026-06-28

## Resultado

- Fuente HTML: `qa/pack canonico/neuromood-mockup_reparado.html`
- HTML sha256: `0fa4b834e50a8936e829a493b6b31c9e181edb84621f9f7861f98ea609a07c87`
- Receta: `qa/pack canonico/generate_captures.js`
- Salidas sincronizadas:
  - `qa/pack canonico/capturas_test/`
  - `qa/_mockup_canonical/`

La receta genero 86/86 capturas con:

- `all_captured=true`
- `all_sizes_match=true`
- `all_dom_sizes_match=true`
- `size_mismatches=[]`
- `dom_size_mismatches=[]`

## Cambio Critico De Receta

La receta anterior podia producir PNGs con tamano correcto pero contenido
incorrecto: despues de capturar `suite-dbt-practice-stop`, el modal quedaba
abierto y contaminaba las capturas siguientes.

El generador ahora:

- limpia UI transitoria antes de cada vista;
- cierra cualquier modal abierto despues de capturarlo, incluso si la captura
  fue de `.window`;
- valida el bounding box DOM del selector antes del screenshot;
- registra `mockup_sha256`, `generated_at`, `chromium`, `capture_selector`,
  `dom_w`, `dom_h` y `dom_size_match`.

## Cambio De Superficie

`hub-detalle-resumen-ia-0` ya no mide `480x325` en el HTML reparado. El DOM real
del modal canonico mide `560x220`.

Archivos nuevos:

- `hub-detalle-resumen-ia-0-light-560x220.png`
- `hub-detalle-resumen-ia-0-dark-560x220.png`

Archivos retirados:

- `hub-detalle-resumen-ia-0-light-480x325.png`
- `hub-detalle-resumen-ia-0-dark-480x325.png`

## Delta Contra Canon Anterior

- 84 PNG conservan nombre pero cambian contenido.
- 2 PNG cambian nombre por resolucion (`Resumen IA`).
- No queda ningun PNG igual byte-a-byte contra el canon anterior.

Mayores deltas por changed-pixel-ratio:

- `suite-home-dark-960x600.png`
- `hub-textos-globales-light-960x600.png`
- `suite-home-light-960x600.png`
- `suite-home-no-score-light-960x600.png`
- `suite-home-no-score-dark-960x600.png`
- `hub-detalle-plan-activacion-light-960x600.png`
- familia `onboarding` / `recuperar-acceso`
- familia `actividades`

## Comparacion Contra V8 Actual

Comando:

```powershell
.\.venv\Scripts\python.exe qa\diff_fidelity.py `
  --target-dir qa\_mockup_recalibration_20260628 `
  --actual-dir qa\_captures_v8 `
  --out-dir qa\_mockup_recalibration_20260628\_diff_vs_v8
```

Resultado:

- Targets considerados: 86
- Comparados: 84
- PASS: 83
- MISSING_ACTUAL: 2
- FAIL: 1

Brechas detectadas:

- `hub-detalle-resumen-ia-0-{light,dark}-560x220`: V8 todavia captura
  `480x325`, por lo que falta recaptura/adaptacion de runtime.
- `suite-dbt-practice-stop-light-960x600`: sigue fallando por diff de modal
  light/backdrop/posicion.

Nota: `tests/test_hub_visual_contract.py` todavia valida el modal runtime de
Resumen IA como `480x325`. No se actualizo en esta recalibracion porque eso ya
implica adaptar producto/runtime y debe entrar en el paso del E2E comparativo.

## Capas Necesarias Para El E2E Comparativo/Reparador

1. **Contrato de pairing:** `surface_key`, app, view, theme, resolution y
   selector. Debe detectar `MISSING_ACTUAL` por cambio de resolucion sin
   clasificarlo como bug visual de producto.
2. **Contrato DOM/captura:** bounding box real, selector capturado,
   scroll/transient UI limpio, hover neutralizado y modales cerrados.
3. **Diff visual:** odiff/SSIM/MAD/changed ratio como gate numerico, con
   tolerancias por superficie.
4. **BBoxes de divergencia:** regiones conectadas para separar layout, texto,
   color y ruido de antialiasing.
5. **OCR/texto:** textos faltantes/sobrantes/cambiados; especialmente util en
   onboarding, recuperar acceso, modales y CTAs.
6. **Estado semantico Qt:** checkboxes, botones enabled/disabled, tabs activas,
   modal abierto/cerrado y wiring de acciones. Esto cubre falsos positivos
   visuales y fachadas funcionales.
7. **Clasificador reparador:** `PAIRING_FIX`, `FIX_PRODUCT_STRONG`,
   `FIX_PRODUCT_REVIEW`, `RENDER_NOISE_OK`, `NEEDS_HUMAN_REVIEW`.

El hallazgo clave: tamano correcto de PNG no alcanza. La receta y el futuro E2E
visual deben validar tambien estado DOM/runtime y limpieza de transiciones.
