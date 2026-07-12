# VisualParity V3 — Propuesta Técnica

> **ARCHIVADO 2026-07-12 — propuesta SUPERSEDED.** La plataforma V3 (.NET) no
> se construye; el plan vigente es "V1 saneado" (`Plan Harness Fable.md`,
> raíz), que implementa las reglas de este audit en el harness Python
> existente. El forensic audit (`forensic_audit/FORENSIC_AUDIT_V3.md`) sigue
> siendo el registro de referencia de la invalidación de los 116 cierres V1.

Esta carpeta contiene la propuesta técnica V3 para resolver el problema estructural de QA visual de `nm_suite`.

## Tesis central

> **VisualParity mide y muestra. El harness decide.**

Cualquier PASS que VisualParity emita es `AUTO_PASS` (señal de medición), no `CLOSURE_PASS` (autoridad de cierre). Esta separación estricta entre medición y política es la invariante fundamental que V1 y V2 violaron.

## Contenido

```
docs/VisualParity_V3/
├── VisualParity_V3_Propuesta_Tecnica.pdf      # Propuesta completa (54 páginas)
├── VisualParity_V3_Propuesta_Tecnica.docx     # Versión Word editable
├── README.md                                   # Este archivo
├── diagrams/                                   # 7 diagramas técnicos + cover
│   ├── 00_cover.png
│   ├── 01_layered_architecture.png             # Capas medición/política/aplicación/persistencia
│   ├── 02_core_engine_pipeline.png             # Pipeline del Core Engine
│   ├── 03_evidence_bundle_structure.png        # Estructura del ZIP .vpbundle
│   ├── 04_state_machine.png                    # 8 estados + transiciones
│   ├── 05_end_to_end_flow.png                  # Flujo agent_runner → cierre
│   ├── 06_mvp_roadmap.png                      # 5 fases MVP
│   └── 07_antifraud_matrix.png                 # Matriz V1 vs V2 vs V3
└── forensic_audit/
    └── FORENSIC_AUDIT_V3.md                    # Auditoría forense completa (38 hipótesis validadas)
```

## Resumen ejecutivo

- **V1 (`qa/`)** fue fraude sistémico: 3 razones técnicas independientes invalidaron los 116/116 closures.
- **V2 (`harness/`, HEAD commit `fbdcbf2`)** es peor que V1: stubs que PASS, anti-fraud al 11% de cobertura, auto-rechazo del propio scope resolver, dependencia de VisualParity inexistente. **No usar V2 como base.**
- **V3** es el primer diseño que respeta la invariante. 4 capas separadas (Medición / Política / Aplicación / Persistencia), 5 fases MVP (19-26 semanas), 9/9 vectores anti-fraud.

## Cifras clave

| Métrica | Valor |
|---|---|
| Commits analizados | 214 |
| Closures V1 declarados PASS | 116/116 (todos inválidos) |
| LOC V1 (`qa/`) | 5917 |
| LOC V2 (`harness/`) | 1668 (con stubs) |
| Tests en CI | 0 |
| Hipótesis red-team confirmadas | 30/38 |
| Defectos concretos V2 | 14 |
| Reglas V3 derivadas | 22 |
| Cobertura anti-fraud V1 → V2 → V3 | 56% → 11% → 100% |

## Recomendación final

1. No reutilizar V1 ni V2 salvo assets canónicos (PNGs, HTML, receta) y utilitarios limpios (`vas_engine`, `vas_introspect`, `capture_v8` con extensión).
2. Re-abrir los 116 closures V1 como OPEN en el handoff V3.
3. Empezar Fase 1 (CLI/Core de VisualParity) inmediatamente.
4. Eliminar `--no-regen` y `reopen_legacy_all` del harness.
5. Self-hosted runner para cierre; CI sólo bloquea.
6. Audit log inmutable para todas las decisiones humanas.

## Stack propuesto

- **VisualParity Workbench**: .NET 8 + WPF/WinUI (repo nuevo: `github.com/Rybjuani/visualparity`)
- **Harness nm_suite**: Python (preserva compatibilidad con `capture_v8.py`, PyQt6, VAS engine)

## Referencias

- Propuesta técnica completa: `VisualParity_V3_Propuesta_Tecnica.pdf` (secciones 1-7 + anexos)
- Auditoría forense detallada con 38 hipótesis validadas: `forensic_audit/FORENSIC_AUDIT_V3.md`
- Diagramas fuente: `diagrams/` (PNG a 2x resolución)
