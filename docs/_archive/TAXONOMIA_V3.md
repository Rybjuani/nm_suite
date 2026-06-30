# Taxonomía de Salida Operativa V3 — Diseño Completo

## Objetivo

Reorientar Visual Auditor V3 para que **86/86 superficies** produzcan salida útil para agentes, con **0 NEEDS_HUMAN_REVIEW** al nivel operativo. La taxonomía reemplaza la decisión interna `NEEDS_HUMAN_REVIEW` con categorías operativas que enrutan trabajo a agentes especializados, nunca al owner humano.

## Principios Fundamentales

1. **Zero owner review**: `requires_owner_review` siempre es `False`. Si no podemos decidir, es una limitación del auditor, no una tarea humana.
2. **Cada superficie es enrutable**: No existe "no sé qué hacer con esto". Siempre hay un agente siguiente.
3. **Evidencia explícita**: Cada categoría debe incluir `evidence_quality`, `diagnostic_labels`, y `why_not_owner_review`.
4. **Acciones concretas**: `agent_next_action` debe ser un paso específico, no genérico.
5. **Jerarquía de decisión**: Las reglas se evalúan en orden; la primera que califica gana.

---

## Taxonomía de Agent Routes (6 categorías)

### 1. `PRODUCT_ACTIONABLE`
**Definición**: Hay evidencia suficiente de un bug de producto (texto, color, estructura) que un agente puede investigar y potencialmente arreglar.

**Criterios de asignación**:
- Evidencia estructural (`MISSING_COMPONENT` o `EXTRA_COMPONENT`) con confianza `high` o `medium`
- O evidencia de texto real con `worst_fuzzy < 70` y confianza `high` o `medium`
- El bbox no domina la imagen (>35%)
- Hay par de OCR real confirmado (`_looks_like_real_text_pair`)
- `evidence_quality` = `strong` o `medium`

**Agente destino**: Agentes de producto / código (investigar módulo sospechado)

**Ejemplo**:
```json
{
  "agent_route": "PRODUCT_ACTIONABLE",
  "agent_next_action": "Investigate app/modules/avisos_qt.py. OCR mismatch: 'Activos' vs 'ctivo:' (fuzzy=35) at header band, center-left quadrant. Confirm setMinimumWidth or padding issue before changing product.",
  "requires_owner_review": false,
  "evidence_quality": "strong",
  "diagnostic_labels": ["TEXT_MISMATCH", "STRUCTURAL_SIGNAL"],
  "why_not_owner_review": "Clear text mismatch with real OCR pair and sufficient confidence is actionable by an agent investigating font metrics, padding, or truncation."
}
```

---

### 2. `QA_TOOLING_ACTIONABLE`
**Definición**: Hay una señal débil o parcial que necesita mejor tooling (OCR, bbox extraction, preprocesamiento) antes de que un agente de producto pueda actuar con confianza.

**Criterios de asignación**:
- Texto detectado pero `worst_fuzzy >= 70` o confianza `low`
- Color detectado pero confianza `low` o bbox es grande
- Bbox domina imagen (>35%) pero SÍ hay evidencia de texto real localizada
- OCR es ruidoso (`worst_fuzzy < 30` sin par real)
- `evidence_quality` = `weak` o `medium`

**Agente destino**: Agentes de QA / tooling (mejorar extracción, OCR, heurísticas)

**Ejemplo**:
```json
{
  "agent_route": "QA_TOOLING_ACTIONABLE",
  "agent_next_action": "OCR detected possible text mismatch (worst_fuzzy=78) but confidence is low. Improve OCR preprocessing (upscale 3x, adaptive contrast, sharpen) or split bboxes into smaller crops before claiming product action. Current OCR may be noisy or partial.",
  "requires_owner_review": false,
  "evidence_quality": "weak",
  "diagnostic_labels": ["TEXT_MISMATCH", "OCR_WEAK"],
  "why_not_owner_review": "Weak text evidence should be strengthened by tooling improvements, not thrown to a human for visual inspection."
}
```

---

### 3. `CAPTURE_OR_PAIRING_ACTIONABLE`
**Definición**: El problema está en la infraestructura de captura o emparejamiento, no en el producto.

**Criterios de asignación**:
- Decisión interna era `PAIRING_FIX`
- No hay capture path (`pairing.real_capture_path` vacío)
- Tamaños no coinciden drasticamente
- Faltan archivos de captura
- `evidence_quality` = `none` o `weak`

**Agente destino**: Agentes de infraestructura / pipeline (re-run capture, fix manifest)

**Ejemplo**:
```json
{
  "agent_route": "CAPTURE_OR_PAIRING_ACTIONABLE",
  "agent_next_action": "Check capture pairing and normalized target path for surface 'hub:detalle-resumen-ia@light'. Capture file missing; verify CAPTURE_MANIFEST.json entry and re-run capture_v8.py for this surface.",
  "requires_owner_review": false,
  "evidence_quality": "none",
  "diagnostic_labels": ["PAIRING_MISSING"],
  "why_not_owner_review": "Capture/pairing issues are resolved by re-running capture pipeline, not by manual visual review."
}
```

---

### 4. `AUDITOR_IMPROVEMENT_ACTIONABLE`
**Definición**: V3 no pudo clasificar la superficie en una ruta confiada. Es una limitación del auditor que necesita mejores heurísticas o reglas.

**Criterios de asignación**:
- Fallback cuando ninguna otra categoría aplica
- Señales contradictorias (ej. confianza `high` pero sin evidencia real)
- Patrones de superficie no cubiertos por heurísticas actuales
- `evidence_quality` = `weak` o `none`

**Agente destino**: Agentes de mejora del auditor (agregar reglas, ajustar umbrales)

**Ejemplo**:
```json
{
  "agent_route": "AUDITOR_IMPROVEMENT_ACTIONABLE",
  "agent_next_action": "V3 could not classify surface 'suite:home@dark' into a confident route. Evidence: diagnostic_labels=['NO_SIGNIFICANT_SIGNAL'], confidence=low, worst_fuzzy=100. Improve bbox extraction, OCR preprocessing, or add heuristic rules for this surface pattern (home screen with dark theme).",
  "requires_owner_review": false,
  "evidence_quality": "none",
  "diagnostic_labels": ["NO_SIGNIFICANT_SIGNAL"],
  "why_not_owner_review": "Unclear signal is an auditor limitation, not a human task. The agent should improve V3 heuristics or tooling for this surface type."
}
```

---

### 5. `RENDER_NOISE_AUTO_IGNORED`
**Definición**: Las diferencias son ruido de renderizado, artefactos de tema, o varianza esperada de captura. No requieren acción.

**Criterios de asignación**:
- `RENDER_NOISE` en labels y no hay señal estructural/texto/color
- Bbox domina imagen (>35%) sin evidencia localizada
- Diferencias solo en chrome/bordes/scrollbars
- `changed_pixel_ratio < 0.05` y no hay señales fuertes
- `evidence_quality` = `none` o `weak`

**Agente destino**: Ninguno (auto-ignored, logged for audit)

**Ejemplo**:
```json
{
  "agent_route": "RENDER_NOISE_AUTO_IGNORED",
  "agent_next_action": "No product action. Differences are limited to window chrome, scrollbar, or titlebar areas. No product action needed.",
  "requires_owner_review": false,
  "evidence_quality": "none",
  "diagnostic_labels": ["CHROME_MISMATCH", "RENDER_NOISE"],
  "why_not_owner_review": "Chrome differences are expected capture variance, not product bugs."
}
```

---

### 6. `NO_ACTION_NEEDED_WITH_EVIDENCE`
**Definición**: La superficie está visualmente estable. No hay diferencias significativas.

**Criterios de asignación**:
- `bbox_count == 0` (no diff bboxes detectados)
- O `changed_pixel_ratio < 0.01` y `mean_abs_diff < 5`
- No hay labels de acción
- `evidence_quality` = `strong` (porque la ausencia de señal es evidencia fuerte de estabilidad)

**Agente destino**: Ninguno (surface stable, pass)

**Ejemplo**:
```json
{
  "agent_route": "NO_ACTION_NEEDED_WITH_EVIDENCE",
  "agent_next_action": "No action. V3 found no diff bboxes after pixel-level comparison. Surface is visually stable.",
  "requires_owner_review": false,
  "evidence_quality": "strong",
  "diagnostic_labels": ["NO_SIGNIFICANT_SIGNAL"],
  "why_not_owner_review": "No pixel differences detected; nothing to review or fix."
}
```

---

## Jerarquía de Decisión (Orden de Evaluación)

```
1. ¿No hay bboxes? → NO_ACTION_NEEDED_WITH_EVIDENCE
2. ¿Problema de capture/pairing? → CAPTURE_OR_PAIRING_ACTIONABLE
3. ¿Solo chrome/bordes sin otra señal? → RENDER_NOISE_AUTO_IGNORED
4. ¿BBox domina (>35%) sin evidencia localizada? → RENDER_NOISE_AUTO_IGNORED
5. ¿BBox domina (>35%) con evidencia de texto real? → QA_TOOLING_ACTIONABLE
6. ¿Evidencia estructural fuerte? → PRODUCT_ACTIONABLE
7. ¿Texto real con fuzzy < 70 y confianza suficiente? → PRODUCT_ACTIONABLE
8. ¿Texto/color débil o confianza baja? → QA_TOOLING_ACTIONABLE
9. ¿Ninguna de las anteriores? → AUDITOR_IMPROVEMENT_ACTIONABLE
```

---

## Campos Requeridos en Cada Salida

Cada `agent_package.json` debe incluir:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `agent_route` | `str` | Una de las 6 categorías arriba |
| `agent_next_action` | `str` | Paso concreto siguiente para el agente |
| `requires_owner_review` | `bool` | Siempre `False` |
| `evidence_quality` | `str` | `strong` / `medium` / `weak` / `none` |
| `diagnostic_labels` | `list[str]` | Labels técnicos (TEXT_MISMATCH, COLOR_MISMATCH, etc.) |
| `why_not_owner_review` | `str` | Justificación de por qué no necesita humano |
| `product_action_allowed` | `bool` | Si el agente de producto puede actuar |
| `qa_action_allowed` | `bool` | Si el agente de QA puede actuar |
| `capture_action_allowed` | `bool` | Si el agente de capture puede actuar |

---

## Reglas de Guardia (Guardrails) para Zero Owner Review

1. **Si `confidence == low`**: No forzar `NEEDS_HUMAN_REVIEW`. En su lugar, enrutar a `QA_TOOLING_ACTIONABLE` o `AUDITOR_IMPROVEMENT_ACTIONABLE` según si hay señal débil o ninguna señal.
2. **Si `worst_fuzzy >= 95`**: No forzar `NEEDS_HUMAN_REVIEW`. Si no hay evidencia estructural, enrutar a `NO_ACTION_NEEDED_WITH_EVIDENCE` o `RENDER_NOISE_AUTO_IGNORED`.
3. **Si `diff_summary == "No significant OCR difference"`**: No forzar `NEEDS_HUMAN_REVIEW`. Enrutar según otras señales (color, estructura) o a `NO_ACTION_NEEDED_WITH_EVIDENCE`.
4. **Si `what_to_check_first` es genérico**: No forzar `NEEDS_HUMAN_REVIEW`. Enrutar a `QA_TOOLING_ACTIONABLE` para mejorar la concreción del hint.
5. **Si `fidelity_available == False`**: No forzar `NEEDS_HUMAN_REVIEW`. Solo marcar el flag; la ruta operativa sigue siendo válida.
6. **Si `biggest_bbox_dominates`**: No forzar `NEEDS_HUMAN_REVIEW`. Si hay texto real localizado → `QA_TOOLING_ACTIONABLE`. Si no → `RENDER_NOISE_AUTO_IGNORED`.
7. **Si `all_bboxes_are_artifacts`**: No forzar `NEEDS_HUMAN_REVIEW`. Enrutar a `RENDER_NOISE_AUTO_IGNORED` o `NO_ACTION_NEEDED_WITH_EVIDENCE`.
8. **Si `unreliable` (missing file, corrupt)**: No forzar `NEEDS_HUMAN_REVIEW`. Enrutar a `CAPTURE_OR_PAIRING_ACTIONABLE`.

---

## Métricas de Éxito

- **86/86 superficies** tienen `agent_route != null`
- **0/86 superficies** tienen `requires_owner_review == true`
- **0/86 superficies** tienen `agent_route == "NEEDS_HUMAN_REVIEW"` (la categoría no existe operativamente)
- **100%** de `agent_next_action` son concretos (no genéricos)
- **Cada** `why_not_owner_review` justifica explícitamente por qué es tarea de agente

---

## Notas de Implementación

### Cambios en `visual_auditor_v3.py`

1. **Eliminar `NEEDS_HUMAN_REVIEW` de `DECISION_ORDER`** y de la salida operativa. Mantenerlo solo como decisión interna transitoria si es necesario para compatibilidad, pero nunca exponerlo en `agent_package`.

2. **Reescribir `_enforce_decision_guardrails`**: En lugar de forzar `NEEDS_HUMAN_REVIEW`, debe ajustar la ruta operativa según las reglas de guardia nuevas. Por ejemplo:
   - `confidence == low` + señal débil → `QA_TOOLING_ACTIONABLE`
   - `confidence == low` + sin señal → `AUDITOR_IMPROVEMENT_ACTIONABLE`
   - `worst_fuzzy >= 95` + sin estructural → `NO_ACTION_NEEDED_WITH_EVIDENCE`
   - `biggest_bbox_dominates` + sin texto real → `RENDER_NOISE_AUTO_IGNORED`
   - `unreliable` → `CAPTURE_OR_PAIRING_ACTIONABLE`

3. **Ajustar `_classify_surface`**: La decisión interna puede seguir usando `NEEDS_HUMAN_REVIEW` como fallback, pero `_map_to_agent_route` y `_enforce_decision_guardrails` deben traducirlo siempre a una ruta operativa.

4. **Ajustar `analyze_surface`**: Cuando `unreliable=True`, emitir `CAPTURE_OR_PAIRING_ACTIONABLE` en lugar de `NEEDS_HUMAN_REVIEW`.

5. **Ajustar tests**: Actualizar `test_visual_auditor_v3.py` para verificar que:
   - Ninguna superficie produce `requires_owner_review=True`
   - Todas las superficies producen `agent_route` en `AGENT_ROUTES`
   - `NEEDS_HUMAN_REVIEW` nunca aparece en `agent_route`

---

## Ejemplo de Flujo Completo

**Superficie**: `suite:avisos-search@light`
**Estado**: Texto truncado en botón "Activos" → "ctivo:" en captura real

1. `_extract_bboxes` → encuentra bbox pequeño en header (area_ratio=0.03)
2. `_analyze_bbox` → OCR: mockup="Activos", real="ctivo:", fuzzy=35
3. `_classify_surface` → labels=[TEXT_MISMATCH_PROBABLE], confidence=medium, decision=FIX_PRODUCT_REVIEW (interno)
4. `_map_to_agent_route` → has_real_text=True, worst_fuzzy=35 < 70, confidence=medium → `PRODUCT_ACTIONABLE`
5. `_build_agent_package` → agent_next_action concreto, why_not_owner_review justificado
6. `_enforce_decision_guardrails` → verifica que no hay contradicciones, mantiene `PRODUCT_ACTIONABLE`

**Resultado final**:
```json
{
  "agent_route": "PRODUCT_ACTIONABLE",
  "agent_next_action": "Investigate app/modules/avisos_qt.py. OCR mismatch: 'Activos' vs 'ctivo:' (fuzzy=35) at header band, center-left quadrant. Confirm setMinimumWidth or padding issue before changing product.",
  "requires_owner_review": false,
  "evidence_quality": "strong",
  "diagnostic_labels": ["TEXT_MISMATCH"],
  "why_not_owner_review": "Clear text mismatch with real OCR pair and sufficient confidence is actionable by an agent investigating font metrics, padding, or truncation.",
  "product_action_allowed": true,
  "qa_action_allowed": false,
  "capture_action_allowed": false
}
```
