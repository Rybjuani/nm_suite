# nm_suite — Documentación

## Fuentes de verdad del proceso Visual QA

Estos son los **únicos** documentos activos que gobiernan el proceso de Visual QA:

| Documento | Rol |
|---|---|
| [`../VISUAL_QA_AGENT_PROTOCOL.md`](../VISUAL_QA_AGENT_PROTOCOL.md) | Protocolo operativo: flujo obligatorio, anti-fraude, gate VAS, criterios de cierre técnicos. |
| [`../VISUAL_REPAIR_HANDOFF.md`](../VISUAL_REPAIR_HANDOFF.md) | Checklist de reparación visual con evidencia de cierre por exact-key. |

Todo agente que opere Visual QA debe leer ambos **antes** de tocar código de UI/runtime.

## Documentos de referencia activos (bridge)

| Documento | Rol |
|---|---|
| [`BRIDGE_USAGE_FOR_AGENTS.md`](BRIDGE_USAGE_FOR_AGENTS.md) | Cómo resolver un check visual vía el Design-System Translation Bridge. |
| [`CSS_TO_PYQT_EQUIVALENCE_MATRIX.md`](CSS_TO_PYQT_EQUIVALENCE_MATRIX.md) | Selector HTML → token/helper/widget PyQt → claves visuales afectadas. |
| [`VISUAL_COMPONENT_CATALOG.md`](VISUAL_COMPONENT_CATALOG.md) | Catálogo de componentes `NM*` y tokens `shared.theme` a reutilizar. |
| [`QT_HTML_KNOWN_MISMATCHES.md`](QT_HTML_KNOWN_MISMATCHES.md) | Clasificación IRREDUCIBLE / WORKAROUND / DECISIÓN-OWNER. |
| [`DESIGN_SYSTEM_TRANSLATION_BRIDGE.md`](DESIGN_SYSTEM_TRANSLATION_BRIDGE.md) | Puente de diseño Web → Qt (especificación de tokens y helpers). |

## Setup

- [`dev-setup.md`](dev-setup.md) — entorno de desarrollo.

## Archivo histórico

Todo documento de QA histórico, manual de auditoría retirada, plan cerrado o log
de loop fue movido a [`_archive/`](_archive/). Ese directorio **no es fuente de
verdad**: no debe usarse como backlog activo, ni para abrir deuda nueva, ni para
justificar cierres. Contiene referencias a herramientas retiradas (Visual Auditor
V2/V3, Sentinel) y planes de reestructuración que ya no aplican.

Si se necesita contexto histórico, consultarlo en `_archive/` con esa premisa.
