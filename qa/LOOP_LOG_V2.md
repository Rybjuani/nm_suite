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

### Intento 2: cablear VLM backend (turno 2 de la sesión, owner pidió "instala lo necesario")

- **Instalado**: `zai-sdk` 0.2.3 en `.venv/` (paquete PyPI oficial de Z.AI; el nombre `z_ai_web_dev_sdk` que importa `qa/visual_auditor_v2.py:541` **no existe en PyPI** — el path GLM-4V del código está roto de origen).
- **Probé la key GLM-4V que pasó el owner**:
  - Auth OK (`zai.ZaiClient` instancia sin error).
  - Modelos testeados: `glm-4v`, `glm-4v-plus-0111`, `glm-4v-flash`, `glm-4.6v`, `glm-4.6v-flash`, `glm-4.5v`, `glm-4.5v-flash`.
  - **Único que responde contenido**: `glm-4.6v-flash` (devuelve `content=''` con reasoning de 299 tokens — el modelo gasta todo el budget en pensar).
  - Resto: 429 `code:1113 Insufficient balance or no resource package`.
  - **Diagnóstico final**: la key autentica pero **no tiene saldo/paquete de vision**. No es error de integración, es saldo.
- **Probé Gemini CLI OAuth (gemini-3.1-pro-preview, gemini-3.5-flash)**:
  - Texto plano: funciona (`gemini-3.5-flash -p "OK"` responde OK).
  - **Con imagen adjunta**: el CLI routea internamente a `generativelanguage.googleapis.com` (free tier API-key) y devuelve 429 `Quota exceeded for metric: ... free_tier_requests, limit: 0`. El OAuth Advanced **no se está usando para vision** — bug o limitación del CLI actual.
- **No modifiqué `qa/visual_auditor_v2.py`** — el cambio mínimo habría sido agregar `_call_vlm_gemini_cli` que envuelva `subprocess.run(['gemini.cmd', ...])`, pero al estar el endpoint de visión bloqueado por cuota en todos los backends probados, no tiene sentido cablear algo que no va a funcionar.

### Estado consolidado al cierre del turno 2

- `zai-sdk` instalado en `.venv/` (listo para cuando haya saldo o key con paquete de vision).
- `qa/visual_auditor_v2.py` **NO modificado** (no introduje código que no se pueda probar).
- `GLM_API_KEY` queda en memoria operativa para uso futuro cuando se recargue saldo.
- No se tocó producto en esta sesión (0 fixes).

### Turno 3: skill canónico + analyze --no-vlm

- Owner carga skill canónico `SKILL.md` (2603 tokens) → idéntico a la regla ya aplicada.
- Comando nuevo probado: `qa/visual_auditor_v2.py analyze --all --no-vlm` → 86/86 surfaces procesadas, queue regenerada con `--no-vlm`.
- `qa/visual_auditor_v2.py doctor` → `NM_VLM_BACKEND not set` (idéntico al turno previo).
- Queue regenerada: 86/86 `severity: needs_review`, `confidence: low`. Diff_fidelity: 8/86 PASS (empty states), 78/86 FAIL.

### Aplicación del template no-vision del skill

```text
I cannot inspect the PNGs directly in this environment. I will use V2 text evidence only.
Selected surface: NINGUNA (queue tiene 86/86 confidence=low, bloqueado por falta de VLM backend con cuota)
Evidence source: queue.md + metrics.json + classification.json + report.json + diff_fidelity
Decision: NEEDS_HUMAN_REVIEW (forzado por regla dura del skill: "If confidence != high, do not FIX_PRODUCT")
Reason:
  - NM_VLM_BACKEND no configurado (qa/visual_auditor_v2.py doctor)
  - qa/visual_auditor_v2.py:541 importa z_ai_web_dev_sdk que NO existe en PyPI (paquete real es zai-sdk 0.2.3, instalado en .venv/)
  - GLM-4V key (provista por owner este turno): auth OK pero 429 code:1113 Insufficient balance
  - Gemini CLI OAuth: texto funciona, con imagen adjunta routea a free tier quota 0
  - 86/86 surfaces en severity=needs_review, confidence=low, recommendation=NEEDS_HUMAN_REVIEW
  - diff_fidelity.py (gate real): 8/86 PASS (empty states), 78 FAIL
Risk:
  - Sin VLM no hay verificación visual posible
  - Cualquier fix sería "blind attempt, unverified" (patrón condenado por owner en LOOP_LOG_7)
  - Stop rule del owner: "0 mejoras medibles después de varios intentos → NO seguir grindando"
  - Loop sigue bloqueado en pre-loop hasta tener VLM con cuota
```

### Commits de la sesión

- `c1f84ba` docs(qa): LOOP_LOG_V2 initial blocker report (no VLM backend, 0 fixes)
- `577376e` docs(qa): LOOP_LOG_V2 attempt 2 — VLM cableado bloqueado por cuota (GLM sin saldo, Gemini free tier quota 0)

Pendientes para próximas sesiones (no es PASS visual global):

- **Recargar saldo / comprar paquete vision en Z.AI** para que la key GLM-4V (provista por owner en este turno) pueda usarse para `glm-4.6v-flash`.
- **O** habilitar vision en otro backend con cuota (MiniMax vision API, Gemini Advanced con imagen vía CLI/mcp, etc.).
- Con VLM funcional, **recién entonces** cablear `_call_vlm_zai_sdk` (o el que corresponda) en `qa/visual_auditor_v2.py` con patch ≤30 líneas, regenerar la queue, y entrar al loop 1-discrepancia-por-ciclo.
- Hasta entonces, el loop 1-discrepancia-por-ciclo sigue bloqueado en pre-loop.

## Ciclos

(ninguno — ver Decisión arriba)