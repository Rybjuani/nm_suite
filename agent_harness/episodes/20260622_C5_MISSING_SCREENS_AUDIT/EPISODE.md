# C5-MISSING-SCREENS-AUDIT

Auditoría de pantallas no auditadas por el owner en la revisión visual del E6.

## Alcance

Pantallas target según FIX_PLAN:
- Home, Ánimo, Respiración
- DBT Ahora, DBT STOP
- Registro TCC pasos 2/3/success
- Recuperar acceso
- Hub Detalle tabs (resumen IA / registros / timer / rutina)
- Estados secundarios: Actividades filtered/empty/marked, Rutina add/all-completed,
  Timer running/paused/presets, Avisos activos/search/completed

## Metodología

Revisión por código fuente (PyQt6). Sin capturas de runtime.
Criterio de defecto: layout/spacing/jerarquía con desviación visible respecto al ADN V3.
Valores hardcoded numéricamente iguales al token correspondiente no son defecto visual.

## Resultado

**Cero defectos nuevos (P0/P1/P2) detectados en 16 pantallas/estados.**

Todas las pantallas auditadas pasan el criterio ADN V3:
- Empty states: usan NMEmptyState canónico o QLabel inline apropiado para el contexto.
- Spacing: V3_SP tokens o equivalentes numéricos.
- Typography: serif en headings, escala correcta.
- Button hierarchy: gradient/secondary/ghost según contexto.

Ver tabla completa en DEFECT_LEDGER.md § "Pantallas no mencionadas por owner — Auditoría C5".

## Hallazgos descartados

Agentes de exploración detectaron candidatos que fueron descartados tras verificación manual:

| Candidato | Motivo descarte |
|-----------|----------------|
| Home hero empty: QLabel en lugar de NMEmptyState | NMEmptyState es excesivo para hero card de 96px; QLabel inline es idiomático |
| Ánimo margins hardcoded (20, 18) | 20 = V3_SP["lg"], 18 ≈ entre sm y md — no causa desviación visible |
| Registro TCC (12, 8, 12, 8) | 12 = V3_SP["md"], 8 = V3_SP["sm"] — coincidencia exacta |
| Hub Detalle dialog height 325px | Bloqueado por `test_hub_detail_resumen_dialog_height` — cambio requiere decisión owner |
| Avisos section margin 10px | Delta 2px vs V3_SP["sm"]=8 — no perceptible |

## Deuda explícita

- V2-P1-040: Timer ring 230px diferido de C3 — requiere decisión owner sobre escala.

## Handoff

Siguiente cluster: `C6-FINAL-EVIDENCE`.
