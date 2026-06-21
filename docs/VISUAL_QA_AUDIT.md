# Auditoria QA visual contra mockup canonico

Fecha de revalidacion local: 2026-06-20

## Conclusion

El sistema previo de validacion visual no era suficiente para certificar fidelidad real
contra `neuromood-mockup.html`.

La captura tecnica estaba razonablemente cubierta, pero el gate de fidelidad era demasiado
debil: `qa/diff_fidelity.py` aprobaba por SSIM solamente. Eso produjo falsos positivos:

| Pantalla | Tema | SSIM | MAD | Pixel changed | Resultado viejo | Resultado endurecido |
|---|---:|---:|---:|---:|---|---|
| `suite-actividades-empty` | light | 0.93639 | 0.08137 | 0.92001 | PASS | FAIL |
| `suite-rutina-empty` | light | 0.93416 | 0.08175 | 0.91915 | PASS | FAIL |

Ambas pantallas superaban `SSIM >= 0.92`, pero cambiaban demasiados pixeles y tenian una
distancia media incompatible con fidelidad visual real.

## Cambios aplicados al QA

- `qa/diff_fidelity.py` ahora exige gate compuesto:
  - `SSIM >= 0.92`
  - `mean_abs_diff <= 0.035`
  - `changed_pixel_ratio <= 0.08`
  - si existe `CAPTURE_MANIFEST.json`, la captura debe ser tecnicamente valida y
    `state_evidence_valid`.
- El reporte ahora incluye `acceptance_failures`, `capture_status`,
  `capture_technical_valid`, `capture_state_valid` y `capture_evidence_flags`.
- Tests nuevos fijan los dos riesgos:
  - SSIM alto con delta visual grande no puede pasar.
  - una captura marcada `REQUIRES_DATA_STATE` no puede certificar fidelidad final aunque
    la imagen sea identica.

## Revalidacion actual

Comando:

```powershell
.venv\Scripts\python.exe qa\diff_fidelity.py --target-dir qa\_mockup_targets --actual-dir qa\nm_capturas_actualizadas --out-dir qa\_fidelity_current
```

Resultado:

| Total targets | PASS | FAIL | Missing |
|---:|---:|---:|---:|
| 96 | 0 | 96 | 0 |

Reporte generado:

- `qa/_fidelity_current/FIDELITY_REPORT.md`
- `qa/_fidelity_current/FIDELITY_REPORT.csv`
- `qa/_fidelity_current/FIDELITY_REPORT.json`

Captura tecnica actual (`qa/nm_capturas_actualizadas/CAPTURE_MANIFEST.json`):

| Total capturas | Tecnicas validas | State-valid | `REQUIRES_DATA_STATE` |
|---:|---:|---:|---:|
| 96 | 96 | 90 | 6 |

Esto significa que la app renderiza capturas no-blancas/no-duplicadas, pero ninguna pantalla
alcanza fidelidad suficiente contra el mockup canonico.

### Vigencia de las capturas completas

Durante los bloques posteriores se verifico que `qa/nm_capturas_actualizadas` habia sido
generado contra un commit anterior (`1bfba84`) y no contra el codigo actual. Por lo tanto:

- El reporte full en `qa/_fidelity_current` es valido para auditar el metodo previo, probar
  los falsos positivos y dimensionar deuda visual historica.
- No debe usarse como certificacion final del estado actual despues de nuevos commits.
- Cada bloque corregido debe recapturarse en fresco con `qa/capture_v8.py` y medirse con
  `qa/diff_fidelity.py`; al final de una fase hace falta una recaptura completa de los 96
  targets.

## Bloques corregidos tras la auditoria

| Bloque | Captura fresca | Resultado endurecido | Evidencia |
|---|---|---|---|
| Chrome Suite/Hub: icono de marca canonico | `qa/_captures_block_chrome_home` | Home seguia FAIL | Se reemplazo el logo multicolor por iconos `home`/`brain` del mockup. |
| Chrome Suite/Hub: titlebar 48px | `qa/_captures_block_chrome_height_home` | Home seguia FAIL | El titlebar paso al alto del `.titlebar` canonico. |
| Home: ritmo vertical | `qa/_captures_block_home_layout` | Home seguia FAIL | Home score mejoro a SSIM `0.66026` dark / `0.66040` light. |
| Home: cards + fixture QA | `qa/_captures_block_home_cards` | Home seguia FAIL | Textos/badges/icon box alineados; Home score mejoro a SSIM `0.67851` dark / `0.67435` light. |
| Home: barra del hero | `qa/_captures_block_home_hero_bar` | Home seguia FAIL | Barra 8px con fill `brand->mind`; Home score subio a SSIM `0.68378` dark / `0.67964` light. |
| F2 botones: `.btn--soft` | `qa/_captures_block_buttons_actividades` | Actividades seguia FAIL | `NMButton` soporta `soft`; Actividades usa `ghost`/`soft`. SSIM `0.68200` dark / `0.69674` light. |
| F2 focus/input | `qa/_captures_block_focus_textos` | Textos seguia FAIL | `NMInput`/`NMTextArea` usan `brand-line` + halo `brand-soft`. SSIM `0.61929` dark / `0.63264` light. |
| F2 slider Animo | `qa/_captures_block_slider_animo` | Animo seguia FAIL | Thumb activo 22px con borde `brand`. SSIM `0.76828` dark / `0.78618` light. |
| F4 Textos Globales dirty | `qa/_captures_block_textos_dirty` | Textos seguia FAIL | Fila dirty pinta borde `brand-line` + halo `brand-soft`. SSIM default `0.61886` dark / `0.63223` light. |

Deuda Home restante tras estos bloques: aun no alcanza el gate compuesto. En la variante
score quedan diferencias de tipografia fina, distribucion vertical de cards, radios/sombras,
blob radial del hero y algunos offsets de badges. La variante no-score requiere recaptura
fresca despues de la correccion de fixtures.

## Insumo externo GLM verificado

Se incorporo `C:\Users\nosom\Desktop\Informe.md` como insumo externo read-only. No se asume
correcto: se cruzo contra repo, `PLAN_MIGRACION_UI.md` y `neuromood-mockup.html`.

Hallazgos confirmados:

- `_fidelity_selfcheck` no certifica fidelidad: `qa/_fidelity_selfcheck/FIDELITY_REPORT.json`
  tiene 96 filas y en las 96 `target_file == actual_file`. Es una autocomparacion
  mockup-vs-mockup, por eso SSIM=1.0/MAD=0.0 es trivial y no debe usarse como evidencia.
- Targets stale: `qa/_mockup_targets/MOCKUP_TARGET_MANIFEST.json` fue generado en commit
  `0fcb0cc6...`. Ademas `qa/nm_capturas_actualizadas` tambien quedo stale frente al codigo
  actual. Se requiere recaptura completa fresca antes de cierre de fase.
- Tests visuales debiles: varios `tests/*_visual_contract.py` son contratos estructurales
  o de texto; no sustituyen el diff pixel/manifest. Los tests nuevos de QA evitan falsos
  positivos del gate, pero aun falta cobertura visual fuerte por componente/pantalla.
- F2 botones: `NMButton` no tenia variante `soft`; el mockup exige `.btn--soft` en acciones
  como `Actividades > Hice`. Confirmado y corregido.
- F2 focus/input: `NMSearchInput` ya pintaba halo `brand-soft`, pero `NMInput` y
  `NMTextArea` seguian usando foco/glow `accent`. Confirmado y corregido.
- F2 slider: `stylesheet_slider()` ya usaba thumb 22px con borde brand, pero el slider custom
  de Animo (`_MoodTrackBar`) conservaba thumb activo 16px con borde por color de nivel.
  Confirmado y corregido.
- F4 Textos Globales: `tg-row.dirty` estaba confirmado como faltante; el mockup exige
  `brand-line` + glow `brand-soft` cuando una fila queda modificada. Confirmado y corregido.

Hallazgos parcialmente confirmados o superados por cambios posteriores:

- Home hero bar, colores de badges y fixtures QA ya fueron corregidos en los commits
  posteriores a la auditoria inicial; no se arrastran como deuda abierta en esos terminos.
- Slider global QSS no mantiene los 10 stops denunciados por GLM; ese punto aplica al
  componente custom de Animo, no al QSS global actual.
- Divergencias Hub/Suite listadas por GLM quedan como backlog a verificar por fase. Solo se
  integran como deuda abierta cuando hay evidencia local o coinciden con el plan.

## Deuda visual por fase y pantalla

### Fase 0 - Targets & tooling

Estado: gate corregido. Deuda residual: el reporte aun es pixel/manifest driven; no reemplaza
una inspeccion semantica humana para excepciones de Qt, pero ya no deja pasar falsos positivos
por SSIM global.

### Fase 1/2 - Base compartida y primitivas

Deuda transversal observada en muchas pantallas:

- Cuerpo y chrome siguen cerca del mockup, pero no identicos: theme toggle, espaciados,
  pesos de fuente y jerarquia de etiquetas producen cambios masivos aunque los tokens base
  existan.
- Cards, badges, chips, vacios y rows necesitan ajuste fino de paddings, alturas y texto real.
- F2 ya corregida en los puntos destacados por GLM: `.btn--soft`, foco
  `brand-line/brand-soft` en `NMInput`/`NMTextArea`, y thumb canonico del slider custom
  de Animo. Siguen pendientes otras primitivas no abordadas en este bloque (por ejemplo
  hover-lift de cards y ajustes finos de tabs/fchips/patient rows).
- Los estados empty son peligrosos: son los mas parecidos por estructura, pero fallan por
  color/espaciado de superficie y no deben usarse como prueba de fidelidad global.

### Fase 3 - Suite

| Pantalla | Estados cubiertos | Rango SSIM | Deuda concreta |
|---|---|---:|---|
| Acceso | onboarding, error, recuperar | 0.480-0.511 | Mayor deuda: layout narrow, branding, campos, consentimiento/error y jerarquia tipografica no coinciden. |
| Home | score, no-score | 0.638-0.656 | Hero, cards, textos, labels y chips difieren; el no-score ademas depende de estado QA. |
| Termometro | default | 0.762-0.778 | Slider/chart/paneles no llegan a composicion del mockup. |
| Respiracion | idle, presets, running, paused | 0.841-0.855 | Es de las mas cercanas, pero anillo, controles y badges aun cambian >16% de pixeles. |
| Registro TCC | s0, s1, otro, s2, s3, ok | 0.738-0.831 | Stepper, grillas, inputs y cierre no tienen medidas/jerarquia finales. |
| Rutina | default, add, done, empty | 0.748-0.934 | Empty parecia PASS por SSIM, pero falla por MAD/changed; filas, rings y add state siguen fuera. |
| Activacion | default, filtered, marked, empty | 0.675-0.936 | Cards y filtros lejos; empty es falso positivo visual si se mira solo SSIM. |
| Recordatorios | all, active, search, empty, completed | 0.718-0.912 | Search/empty se acercan, pero rows, badges y acciones no pasan thresholds. |
| Temporizador | idle, running, paused, empty, presets | 0.861-0.911 | Cerca en estructura; falta ajustar ring, controles, chips y empty. |
| DBT | now, library, STOP, closure | 0.624-0.778 | Cards/familias/modal/practica tienen diferencias grandes; practice tiene MAD alto. |

### Fase 4 - Hub

| Pantalla | Estados cubiertos | Rango SSIM | Deuda concreta |
|---|---|---:|---|
| Pacientes | list, empty | 0.722-0.883 | Rows/sparkline/ring/header difieren; list y empty tienen `REQUIRES_DATA_STATE`. |
| Detalle | recordatorios, timer, rutina, activacion, resumen IA | 0.675-0.737 | Hero, tabs planas, grid form/panel y modal IA no alcanzan el mockup. |
| Textos globales | default | 0.593-0.595 | Mayor deuda Hub: toolbar, lista, inputs, contadores, footer y estado `tg-row.dirty` no coinciden. |

## Criterio de avance

No avanzar una pantalla como "fiel" hasta que:

1. `qa/capture_v8.py` recapture el bloque/pantalla sin fallos tecnicos.
2. `qa/diff_fidelity.py` pase con el gate compuesto.
3. Cualquier excepcion por limitacion Qt quede documentada junto al diff y no oculte deuda de
   layout, color, texto o estado.
