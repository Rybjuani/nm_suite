# Resumen Manifest V8 — Estado Post-Fases 0-2

Manifest completo (gitignored): `qa/_captures_v8/CAPTURE_MANIFEST.json`
Comando para regenerar: `python qa/capture_v8.py --all --no-clean`

## Ultima Ejecucion

- Fecha: 2026-06-14T19:23:30 (post-fix chrome parametrico — Suite=38px, Hub=32px)
- Harness: `qa/capture_v8.py`
- Total recetas: 66 × 2 temas = 132 capturas esperadas
- Resultado: 132/132 generadas, 0 fallos, 0 duplicados
- unique_hash_count: 132 (sin duplicados)
- Duracion: 423.7s

## Distribucion Por Estado

| Estado | Count | Descripcion |
|---|---|---|
| CAPTURED_VALID | 106 | Estado correcto reproducible en headless |
| REQUIRES_DATA_STATE | 16 | Necesita datos Supabase reales (dashboard, pacientes y variantes) |
| REQUIRES_RUNTIME | 8 | No capturable headless (privacy-lock, pin-setup, settings-overlay, editor) |
| WRONG_VIEW | 2 | home-settings-open: overlay transitorio no capturado desde main-window |

## Comparacion Baseline F0 vs Post-F1+F2

- Baseline Fase 0: `qa/_baseline_f0_phase01/` (132 PNGs, pre-Fase 1)
- Capturas actuales: `qa/_captures_v8/` (132 PNGs, post-Fases 1+2, re-run 2026-06-14T19:21)
- Archivos cambiados: **57/132**
- Archivos sin cambio: **75/132**

### Patron de cambios
- **57 cambiados** = capturas Hub (densidad compacta Fase 1 + chrome 32px Fase 2).
  Todos los Hub excepto REQUIRES_RUNTIME.
- **75 sin cambio** = capturas Suite (densidad `suite_comfortable` codifica valores
  ya presentes en la base; headless no detecta diferencia) + REQUIRES_RUNTIME/WRONG_VIEW.

### Archivos sin cambio — muestra representativa
- Vistas standalone legacy del editor retirado (REQUIRES_RUNTIME en corridas antiguas)
- `suite-pin-setup-dark/light` (REQUIRES_RUNTIME)
- `suite-privacy-lock-light` (REQUIRES_RUNTIME)
- `suite-home-settings-open-dark/light` (WRONG_VIEW / bloqueado)
- Resto: vistas Suite sin cambio visual detectable en headless.

### Por fase
- **Fase 1 (Suite):** 0 cambios detectables en headless — valores comfortable
  coinciden con defaults previos del stylesheet.
- **Fase 1 (Hub):** ~55 cambios — densidad compacta scoped a `#HubMain`.
- **Fase 2 (Hub):** incluida en los mismos 57 — chrome 32px + sidebar compacta.

### Nota: run invalida previa
El diff anterior (pre-fix chrome) mostraba 125 cambiados porque Suite estaba
regresada a 32px chrome, inflando los cambios. El dato valido es 57/132.

## Deuda De Capturas
- Suite: re-run completado (19:21). Suite en 38px, igual que baseline F0.
- Hub: capturas correctas post-Fase-2 (chrome 32px, sidebar compacta).
- 8 vistas Fase 2 inspeccionadas manualmente (ver `FASE2_HUB_SHELL.md`).
