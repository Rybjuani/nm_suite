# LOOP_LOG_V2.md — Visual Fidelity Loop sobre Auditor V2 (Sesión 2026-06-24 v8)

## Estado inicial (pre-loop)

- **SHA inicial**: `58b4938` (`docs(qa): expand VISUAL_AUDITOR_V2.md with agent workflow, decision tree, troubleshooting`)
- **Branch**: `main`
- **Working tree al inicio**: limpio salvo `qa/LOOP_LOG_6.md`, `qa/LOOP_LOG_7.md`, `qa/_blind_diff_classifier.py`, `qa/_fidelity_current/` (todos untracked, pre-existentes).

### Hallazgo estructural previo al primer ciclo

- **Captura base (`qa/capture_v8.py --all --theme both`)**: 86/86 PNGs, 0 fallos, 270.2s.
- **Diff base (`qa/diff_fidelity.py`)**: 8/86 PASS (gate `SSIM≥0.92 ∧ MAD≤0.035 ∧ Changed≤0.08`); 78/86 FAIL.
  - 8 PASS son todos **empty states**: `suite actividades-empty / avisos-empty / rutina-empty / timer-empty` (light+dark).
  - 78 FAIL incluye pantallas con contenido real.
- **Auditor V2 (`qa/visual_auditor_v2.py analyze --all`)**:
  - **doctor**: `NM_VLM_BACKEND not set` — sin backend de visión, TODAS las clasificaciones caen en `NEEDS_HUMAN_REVIEW / confidence=low`.
  - **cache stale detectada**: `qa/_visual_auditor_v2/cache/5792fb9405da555eb55921da2ff4e1a850c6b065872ee6419170739f6bc5ed3b.json` (superficie `suite:home-score:light`) contenía `severity=high`, `confidence=high`, `labels=[COLOR_MISMATCH]`, `suspected_module="shared/components/empty_states.py"`, `explanation="Mocked: color mismatch detected."`. Esa cadena **ya no existe en `qa/visual_auditor_v2.py` actual** (grep 0 matches). **Eliminada** para que el ranking sea honesto.
  - **Después de limpieza + re-`analyze --all`**: queue V2 muestra `86/86 severity=needs_review, confidence=low`. La queue NO es accionable mientras no haya VLM backend.

### Diagnóstico estructural (sin VLM)

Análisis independiente con `execute_code` + PIL sobre `metrics.json`:

- **Mockups**: alturas variables (571 a 642 px), todas 980px ancho.
- **Capturas**: 78/86 hardcoded 960x600, 6 a 520x600, 2 a 480x325.
- **`size_mismatch=true` en 74/74 superficies con bbox≥1**: comparación mockup↔captura resizeada distorsiona todas las métricas estructurales (MAD, SSIM, Changed). Es artefacto de harness, **no es bug de producto**.
- **Mockup targets en `qa/_mockup_targets/`** (que `diff_fidelity.py` usa) son versiones re-escaladas de los mockups a 960x600. Por eso `diff_fidelity.py` puede comparar sin resize y produce los 8 PASS reales (empty states).

### Trabajo de pre-loop (ya en disco)

- `qa/LOOP_LOG_V2.md` creado.
- 1 entrada de cache stale eliminada (`5792fb9…ed3b.json`).
- `qa/_visual_auditor_v2/latest/{index.html, report.json, queue.md}` regenerados con cache limpia.
- Inspección de la superficie `suite:avisos-search:light` (SSIM=0.905, MAD=0.016, Changed=8.3%, cerca del gate pero fuera):
  - Per-region diff: **header (y=0-100) = 0.060**, mid = 0.015, bottom = 0.002.
  - Bbox más grande = banda horizontal 641×69 en zona header.
  - Block-diff del bbox: bloque izquierdo con delta alto → probable **filtro tabs / search input con tamaño o posición distinta** entre mockup y real.
  - Hipótesis técnica: `_StepPill.setMinimumWidth(96)` en `app/modules/avisos_qt.py:536` vs padding `8px 16px` con auto-size en CSS mockup → track segmentado real más ancho que el mockup. **No verificada sin VLM**.

### Bloqueador para entrar al loop

- `NM_VLM_BACKEND` no configurado → V2 clasifica 86/86 como `NEEDS_HUMAN_REVIEW` con `confidence=low`.
- No hay tool de visión (browser no renderiza PNGs locales; no hay `vision_analyze`).
- Sin visión, **cada fix candidato requiere verificación ciega**: medir solo MAD/SSIM estructural es proxy ruidoso por el `size_mismatch` sistemático.
- Reglas aplicables del owner:
  - "Prohibido: usar pHash como juez único" → no puedo usar solo MAD/SSIM como verdad.
  - "Si un fix genera bug latente, resolverlo en el mismo turno" → en blind mode no puedo detectar bug latente.
  - "Stop rule: 0 mejoras medibles después de varios intentos → NO seguir grindando" → todavía no fueron "varios intentos", pero el setup inicial ya muestra que sin VLM no hay guía accionable.
  - "no busques perfección declarativa: buscá mejoras verificables una por una" → sin visión no puedo verificar.

### Decisión

**STOP reportado al owner con este LOOP_LOG_V2.md como evidencia.** No se tocó producto en este turno. No se cometió fix ciego.

Pendientes (no es PASS visual global):

- Configurar `NM_VLM_BACKEND` para activar V2 con visión real (opciones: `z-ai-web-dev-sdk` con `VisionClient` — único backend cableado en `qa/visual_auditor_v2.py:541`; o extender V2 con backend Gemini CLI / MiniMax-vision si están disponibles).
- Con VLM activo, regenerar `qa/_visual_auditor_v2/latest/{report.json,queue.md,index.html}` y entrar al loop 1-discrepancia-por-ciclo sobre la queue real.
- Sin VLM, alternativa `B` aceptable: 1 ciclo blind por sesión con leyenda explícita `blind attempt, unverified` en el commit, midiendo solo MAD/SSIM, pero solo después de confirmación explícita del owner.

## Ciclos

(ninguno — ver Decisión arriba)