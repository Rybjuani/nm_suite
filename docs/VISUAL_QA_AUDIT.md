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
| Textos globales | default | 0.593-0.595 | Mayor deuda Hub: toolbar, lista, inputs, contadores y footer no coinciden. |

## Criterio de avance

No avanzar una pantalla como "fiel" hasta que:

1. `qa/capture_v8.py` recapture el bloque/pantalla sin fallos tecnicos.
2. `qa/diff_fidelity.py` pase con el gate compuesto.
3. Cualquier excepcion por limitacion Qt quede documentada junto al diff y no oculte deuda de
   layout, color, texto o estado.
