# Resumen Manifest V8 — Estado Post-Auditoria 2026-06-21

Manifest completo (gitignored): `qa/_captures_v8_fresh/CAPTURE_MANIFEST.json`
Comando para regenerar: `python qa/capture_v8.py --all --clean --out-dir qa/_captures_v8_fresh`

## Ultima Ejecucion (fresca)

- Fecha: 2026-06-21T02:34:12 (HEAD 51f4448, post-auditoria)
- Harness: `qa/capture_v8.py`
- Total recetas: 49 × 2 temas = 98 capturas esperadas
- Resultado: 98/98 generadas, 0 fallos tecnicos
- State-valid: 92/98 (6 marcan `REQUIRES_DATA_STATE` por dependencia de datos
  reales — pacientes/detalle en Hub)
- Duracion: ~5-6 min

## Distribucion Por Estado

| Estado | Count | Descripcion |
|---|---|---|
| CAPTURED_VALID + state_valid | 92 | Estado correcto reproducible en headless |
| REQUIRES_DATA_STATE | 6 | Necesita datos Supabase reales (detalle hub) |

## Diferencia vs Mockup (gate endurecido)

- Targets Playwright: 96 (48 vistas × 2 temas) en `qa/_mockup_targets/`
- Diff: `qa/_fidelity_fresh/FIDELITY_REPORT.md`
- Gate: SSIM>=0.92, MAD<=0.035, changed_pixel_ratio<=0.08
- Resultado: 0/96 PASS — ninguna pantalla cruza el gate compuesto

## Purgado de artifacts stale (post-auditoria)

Se eliminaron del repo:
- `qa/_mockup_verify/` (4 archivos — capturas previas a V8)
- `qa/_mockup_verify2/` (177 archivos — capturas pre-migracion UI)
- `qa/_fidelity_current/` (3 archivos — reporte contra commit 1bfba84, stale)
- `qa/_fidelity_selfcheck/` (3 archivos — autocomparacion mockup-vs-mockup, trivial)

Estos artifacts estaban referenciados en docs/previos como evidencia de fidelidad
pero NO eran válidos: los primeros por stale, el último por ser una comparacion
tautologica (target==actual → SSIM=1.0 trivial).

## Deuda visual abierta

Ver `docs/VISUAL_QA_AUDIT.md` seccion "Re-auditoria 2026-06-21" para el detalle
completo de deuda por pantalla y los hallazgos estructurales nuevos.
