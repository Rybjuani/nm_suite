# Plan de reestructuración del sistema QA — nm_suite (v3.0)

> **Documento ejecutable para entregar a un agente LLM que lo implemente en el repo local `nm_suite`.**
>
> **Versión 3.0** — reescrita tras descubrir que las 4 carpetas canónicas de referencia visual son inconsistentes entre sí y no son representaciones fieles del HTML. Esto invalida cualquier auditoría previa basada en ellas.
>
> Basado en: (1) auditoría de 15 logs `.md` históricos del repo, (2) research web de mejores prácticas profesionales, (3) **5 PoCs ejecutadas con datos reales** (incluyendo comparación de las 4 carpetas canónicas entre sí y vs captura V8 real y vs captura Playwright fresca del HTML).

---

## 0. Hallazgo crítico (lo que cambia todo)

### 0.1. Las 4 carpetas canónicas no son canónicas

El owner sospechaba que las 4 carpetas de referencia visual tenían problemas. La auditoría lo confirma con datos:

**Comparación de `suite:home@light` (Con puntaje) entre las 4 carpetas:**

| Carpeta | Tamaño | KB | SSIM vs Playwright fresco del HTML |
|---|---|---|---|
| `mockup_reference_static/light/.../Con puntaje.png` | 980×618 | 143.0 | **0.125** |
| `mockup_reference_normalized/light/home.png` | 960×600 | 221.0 | **0.124** |
| `_mockup_targets/suite-home-light-960x600.png` | 960×600 | 146.3 | **0.070** |
| `_mockup_targets_normalized/suite-home-light-960x600.png` | 960×600 | 221.0 | **0.124** |

(SSIM < 0.15 = las imágenes son **completamente distintas**. SSIM > 0.95 = imágenes idénticas.)

**Comparación entre las 4 carpetas (sin Playwright):**

| Par | SSIM | Interpretación |
|---|---|---|
| `static` vs `normalized` | 0.847 | Diferentes tamaños (980×618 vs 960×600), diff real |
| `static` vs `targets` | **0.126** | Imágenes totalmente distintas |
| `normalized` vs `targets` | **0.107** | Imágenes totalmente distintas |
| `normalized` vs `targets_norm` | **1.000** | Idénticas byte-a-byte (duplicadas) |
| `targets` vs `targets_norm` | **0.107** | Imágenes totalmente distintas |

**Decisión del owner confirmada**: las 4 carpetas son obsoletas. `_mockup_targets_normalized` es duplicado de `mockup_reference_normalized` (idénticas). `_mockup_targets` contiene imágenes completamente distintas a las otras 3.

### 0.2. PoC 3 — Verificación con Playwright fresco del HTML

Se capturó `neuromood-mockup.html` con Playwright navegando vía `go('home','score')` a 960×600. Resultado:

- Captura Playwright: 188.1 KB, colores claros (233,227,214 = bg beige consistente con `specs.json` `#e2ddd1`).
- SSIM vs las 3 carpetas: **0.07-0.12** (imágenes totalmente distintas).

Esto valida que **el HTML renderizado fresco NO coincide con ninguna de las 4 carpetas "canónicas"**. Las carpetas son snapshots obsoletos o corruptos.

### 0.3. PoC 4 — Verificación con captura V8 real vs las 4 carpetas

Se comparó `suite-registro-step1-emotion-otro-dark-960x600.png` (captura V8 real del owner) contra las 4 carpetas para la misma superficie:

| Carpeta | SSIM | MAD | changed |
|---|---|---|---|
| `static/Emoción · Otro.png` | 0.071 | 0.040 | 0.144 |
| `normalized/registro-step1-emotion-otro.png` | 0.087 | 0.043 | 0.207 |
| `targets/suite-registro-step1-emotion-otro-dark-960x600.png` | 0.114 | 0.039 | 0.138 |
| `targets_norm/suite-registro-step1-emotion-otro-dark-960x600.png` | 0.087 | 0.043 | 0.207 |

Los 4 dicen FAIL (correcto en superficie — la captura V8 difiere del mockup), pero con números **completamente distintos**: SSIM varía 0.071-0.114 (60% de variación), changed varía 0.138-0.207 (50% de variación). Cualquier decisión basada en estos números da resultados distintos según qué carpeta se use. **El sistema no puede decidir nada consistente.**

### 0.4. Por qué ningún agente detectó esto en 50+ auditorías

Los logs históricos muestran que V2, V3, Sentinel, V8 y revisión visual humana iteraron sobre estas carpetas sin notar que eran inconsistentes entre sí. La causa raíz:

1. Cada herramienta apuntaba a una carpeta distinta (`diff_fidelity` → `_mockup_targets`, `spec_generator` → `mockup_reference_normalized`, `visual_auditor_spec` → specs generadas desde `mockup_reference_normalized`).
2. Ningún agente comparó las carpetas entre sí para validar que representaban lo mismo.
3. Los FPs sistemáticos (76/86 FAIL en SSIM) se atribuyeron a "ruido cross-renderer" cuando en realidad parte del ruido venía de que las imágenes comparadas no eran el mismo contenido.
4. Cuando una auditoría manual encontraba "alta fidelidad" (ej: `AUDITORIA_POSTFIX.md` marcó Pacientes como ✅), era inspección subjetiva, no validación de que la carpeta canónica era correcta.

### 0.5. Implicación para el plan

**Toda auditoría previa basada en estas carpetas es cuestionable.** Los "fixes" aplicados en 50+ iteraciones pueden haber estado alineando la app a una referencia incorrecta. Antes de cualquier nueva auditoría o fix, hay que establecer **una única fuente canónica confiable y verificada**. Hasta eso no exista, **cualquier auditoría nueva amplificará el error** (efecto bola de nieve que el owner previene).

---

## 1. Evidencia empírica de las PoCs (resumen)

| PoC | Hipótesis | Resultado | Evidencia |
|---|---|---|---|
| **PoC 1 — graphify sobre `qa/`** | graphify ahorra tokens para navegar código | **PASS** — 50.79% ahorro | Baseline 59,356 tokens → grafo 29,211 tokens. Setup 0.83s, 291 nodos, 613 edges, sin LLM. |
| **PoC 2 — odiff AA vs SSIM (sintético)** | odiff AA reduce ruido vs SSIM | **PASS parcial** — 50% reducción | Pair A solo ruido: odiff AA 1,482 px vs SSIM 2,943 px. |
| **PoC 2b — odiff AA vs SSIM (imágenes reales)** | odiff AA reporta diff accionable | **PASS** — 57% menos píxeles que SSIM | Mockup vs captura V8: SSIM changed 80,116 px vs odiff AA 34,368 px. |
| **PoC 3 — Playwright fresco vs 4 carpetas** | Las 4 carpetas no representan el HTML actual | **PASS** — confirmado | Playwright `home_light_score` vs las 3 carpetas: SSIM 0.07-0.12 (imágenes totalmente distintas). |
| **PoC 4 — Captura V8 real vs 4 carpetas** | Las 4 carpetas dan 4 verdicts distintos | **PASS** — confirmado | SSIM varía 0.071-0.114 (60% variación) para la misma captura V8 contra las 4 carpetas. |

---

## 2. Decisiones de diseño del plan

### 2.1. Nueva fuente canónica única: `qa/_mockup_canonical/`

Se reemplazan las 4 carpetas obsoletas por **una única carpeta canónica** generada fresca desde el HTML vía Playwright. Reglas:

- **Una sola fuente de verdad**: `qa/_mockup_canonical/{theme}/{view}.png` (ej: `qa/_mockup_canonical/light/home.png`).
- **Generada por Playwright** navegando el HTML con `go(view, state)` a 960×600 (o 520×600 para onboarding/recuperar, 480×325 para resumen-ia).
- **Reproducible**: un script `qa/capture_mockup_canonical.py` regenera toda la carpeta desde el HTML en un solo comando. Cualquier dev puede correrlo y obtener el mismo output.
- **Verificada**: tras generar, el script valida que cada PNG tiene el tamaño esperado y un bg color consistente con el HTML.
- **Gitignored o committed** (decisión del owner): si se commitea, es la referencia definitiva; si se gitignorea, cada dev la regenera con el script.

### 2.2. Las 4 carpetas obsoletas se eliminan

Tras validar que `qa/_mockup_canonical/` es correcta:

- `qa/mockup_reference_static/` → `git rm -r`
- `qa/_mockup_targets/` → `git rm -r`
- `qa/mockup_reference_normalized/` → `git rm -r`
- `qa/_mockup_targets_normalized/` → `git rm -r`

### 2.3. Limpieza de código que las referencia

Archivos a modificar o eliminar:

| Archivo | Cambio | Razón |
|---|---|---|
| `qa/diff_fidelity.py` L25-27 | Cambiar `_DEFAULT_TARGETS` a `qa/_mockup_canonical` | Apunta a `_mockup_targets` |
| `qa/spec_generator.py` L9 | Cambiar `_STATIC_DIR`/`_NORM_DIR` a `qa/_mockup_canonical` | Apunta a `mockup_reference_normalized` |
| `qa/normalize_mockup_reference.py` | **Eliminar archivo entero** | Ya no se normaliza: la canonical viene directa del HTML |
| `qa/capture_mockup.py` | **Eliminar archivo entero** | Reemplazado por `capture_mockup_canonical.py` |
| `qa/_fidelity_diff/` | **Eliminar carpeta** | Output de diff_fidelity contra carpeta obsoleta |
| `qa/_fidelity_current/` | **Eliminar carpeta** | Ídem |
| `qa/_visual_auditor_spec/` | **Regenerar** tras fix | Contiene `report.json` y `introspection.json` basados en specs viejas |
| `qa/specs/specs.json` | **Regenerar** tras fix | Specs auto-generadas desde carpeta obsoleta |
| `tests/test_normalize_mockup_reference.py` | **Eliminar** | Test de un módulo eliminado |
| `tests/test_mockup_qa_tools.py` | **Eliminar o adaptar** | Apunta a `_mockup_targets` |
| `tests/test_visual_auditor_v2.py` | **Eliminar** (ya estaba roto) | Importa módulo eliminado |
| `tests/test_visual_auditor_v3.py` | **Eliminar** (ya estaba roto) | Importa módulo eliminado |
| `tessdata/` | **Auditar uso** — si no se usa, eliminar | Sin hits en código Python; verificar si hay OCR en alguna parte |

### 2.4. Pipeline QA reestructurado (estado final)

```
neuromood-mockup.html
        ↓ (Playwright, capture_mockup_canonical.py)
qa/_mockup_canonical/{theme}/{view}.png   ← ÚNICA fuente canónica
        ↓
        ├── spec_generator (specs manuales o auto-generadas SIN color_hint)
        │       ↓
        │   qa/specs/specs.json
        │
        ├── odiff --antialiasing (reemplaza SSIM)
        │       ↓
        │   qa/_diff_results/{surface}.json (diff_pixels, diff_pct, diff_png)
        │
        └── vas_introspect (Qt widget tree, opt-in vía --introspect)
                ↓
            qa/_introspection/{surface}.json

PyQt6 app → capture_v8 → qa/_captures_v8/{surface}.png
                                ↓
                    alimentado a los 3 verificadores de arriba

graphify (dev-tool out-of-band) → docs/graphify-out/graph.json
                                ↓
                    contexto para agentes que consumen divergencias
```

---

## 3. Plan por fases

Cada fase tiene **gate de salida medible** (no hipótesis). Si no se cumple, no se avanza.

### Fase 0 — Establecer fuente canónica única confiable (4-6h)

**Esta es la fase más crítica. Sin esto, nada de lo demás tiene sentido.**

**Branch**: `qa/canonical-source` desde `main`. **No tocar main hasta Fase 4.**

**0.1 — Escribir `qa/capture_mockup_canonical.py`**

- Script Playwright que:
  1. Abre `neuromood-mockup.html` con `file://`.
  2. Lista las superficies a capturar (mapear `surface_key` → `go(view, state)` call). Obtener la lista del objeto `SCREENS` del HTML (parsearlo con regex o JS evaluate).
  3. Para cada superficie × tema (light/dark):
     - Setea `document.documentElement.dataset.theme`
     - Llama `go(view, state)` via `page.evaluate()`
     - Espera 800ms (fonts + animations)
     - Captura a 960×600 (o 520×600 para onboarding/recuperar, 480×325 para resumen-ia)
     - Guarda en `qa/_mockup_canonical/{theme}/{view}.png`
  4. Genera `qa/_mockup_canonical/MANIFEST.json` con: surface_key, theme, file, size, bg_color_sample, sha256.
- **Validación post-captura** (en el mismo script):
  - Cada PNG tiene el tamaño esperado (no cortes, no compresiones raras).
  - El bg color de las 4 esquinas + centro es consistente con el tema (light: claro, dark: oscuro).
  - `sha256` de cada PNG se registra en el manifest (para detectar cambios futuros).
- **Gate**: ≥80 superficies capturadas (86 esperadas). 0 PNGs con tamaño inesperado. 0 PNGs con bg color inconsistente con el tema.

**0.2 — Verificación humana de 5 superficies sampleadas**

- El agente NO decide si la canonical es correcta. El owner sí.
- Generar un collage PNG con 5 superficies sampleadas (home light, animo dark, registro-step1 dark, pacientes light, dbt-now dark) en `qa/_mockup_canonical/_review_collage.png`.
- El owner revisa visualmente y aprueba o rechaza.
- **Gate**: aprobación explícita del owner en texto. Si rechaza, diagnosticar qué superficie está mal y arreglar el script de captura.

**0.3 — NO eliminar las carpetas obsoletas todavía**

- Las 4 carpetas se eliminan en Fase 3, después de que la canonical esté validada y los verificadores migrados.
- Mantener las obsoletas en `main` hasta entonces como fallback de comparación.

**Gate de salida Fase 0**: 
- `qa/_mockup_canonical/` existe con ≥80 PNGs.
- `MANIFEST.json` generado con sha256 de cada PNG.
- Owner aprobó visualmente el collage de 5 superficies.
- Script `capture_mockup_canonical.py` corre sin errores y es reproducible (`rm -rf qa/_mockup_canonical && python qa/capture_mockup_canonical.py` produce el mismo output).

Si el owner NO aprueba el collage, **stop**. No avanzar a Fase 1. Diagnosticar qué superficie está mal y arreglar el script.

---

### Fase 1 — Migrar verificadores a la nueva canonical (4-6h)

**Branch**: misma `qa/canonical-source`.

**1.1 — Migrar `diff_fidelity.py` a `qa/_mockup_canonical/`**

- L25-27: cambiar `_DEFAULT_TARGETS` de `qa/_mockup_targets` a `qa/_mockup_canonical`.
- **No tocar SSIM todavía** — se hace en Fase 2. Por ahora solo apuntar a la nueva fuente.
- **Validación**: correr `diff_fidelity` contra `qa/_captures_v8/` con la nueva canonical. Comparar FAIL count con baseline (carpeta obsoleta). Gate: FAIL count cambia (no necesariamente baja — la canonical nueva puede revelar diffs reales que la obsoleta ocultaba).

**1.2 — Re-generar `specs.json` desde la nueva canonical**

- `qa/spec_generator.py` L9: cambiar path a `qa/_mockup_canonical`.
- **Aplicar fix P0 del PDF de auditoría**: borrar L73-86 que agregan `header_band` y `score_widget` con `color_hint` hardcoded al bg.
- Re-generar `qa/specs/specs.json`.
- **Validación**: correr `visual_auditor_spec verify-all` contra `qa/_captures_v8/` con las nuevas specs. Comparar divergencias con baseline. Gate: drop ≥30% en divergencias (el `color_hint` hardcoded generaba COLOR_MISMATCH sistemático).

**1.3 — Fix canvas_bg check en `visual_auditor_spec.py`**

- L255-270: reescribir `_check_canvas_bg` con 4 esquinas + mediana + tol=25 (en vez de 5 muestras + media + tol=12).
- **Validación**: drop ≥10% en COLOR_MISMATCH kind específicamente. 0 falsos COLOR_MISMATCH en superficies dark con bg sólido.

**1.4 — Habilitar `vas_introspect` con flag `--introspect` (NO por default)**

- `qa/capture_v8.py:2212`: agregar `--introspect` al CLI. Default off.
- Ampliar contratos en `qa/vas_introspect.py`: agregar `_contract_radius_present` y `_contract_gradient_when_specified`.
- **Validación**: 0 FPs en superficies canonical. ≥1 deuda real nueva detectada. Tiempo de `capture_v8 --all --introspect` ≤115% del baseline sin flag.

**1.5 — Borrar tests rotos y obsoletos**

- `git rm tests/test_visual_auditor_v2.py tests/test_visual_auditor_v3.py` (importan módulos eliminados).
- `git rm tests/test_normalize_mockup_reference.py` (test de módulo a eliminar en Fase 3).
- `git rm tests/test_mockup_qa_tools.py` (apunta a `_mockup_targets`).
- **Validación**: `pytest --collect-only` retorna 0 errores de collection.

**Gate de salida Fase 1**:
- `diff_fidelity` corre contra `_mockup_canonical`.
- `specs.json` regenerado sin `header_band`/`score_widget` hardcoded.
- `visual_auditor_spec verify-all` reporta ≥30% menos divergencias que baseline.
- `pytest --collect-only` sin errores.
- `vas_introspect` opt-in medido (≤+15% tiempo).

Si algún gate no cumple, **stop**. Diagnosticar antes de seguir.

---

### Fase 2 — Reemplazar SSIM por odiff + integrar graphify (4-6h)

**Branch**: misma `qa/canonical-source`.

**2.1 — Reemplazar SSIM por odiff con --antialiasing en `diff_fidelity.py`**

- Instalar `odiff-bin` (npm) como dependencia de dev. Documentar en `pyproject.toml` `[project.optional-dependencies] dev`.
- Nuevo módulo `qa/odiff_runner.py` que envuelva la llamada a `odiff-bin` con `--antialiasing --threshold 0.1`.
- `qa/diff_fidelity.py`: agregar función `compare_with_odiff(target, actual)` que produzca `{diff_pixels, diff_percentage, diff_png_path}`.
- **Mantener** `compare()` con SSIM como `compare_legacy()` (no borrar todavía). Marcarlo legacy.
- **Validación**: correr ambos motores sobre 86 superficies contra `_mockup_canonical`. Gate: odiff AA reporta ≥40% menos FAILs que SSIM con gate estricto (gate owner: SSIM≥0.92, MAD≤0.035, Changed≤0.08).

**2.2 — Integrar graphify como dev-tool out-of-band**

- Instalar `graphify` en dev shell del owner (NO en `pyproject.toml` del proyecto). Link oficial: https://github.com/safishamsi/graphify. Documentar en `docs/dev-setup.md`.
- Correr `graphify extract qa/` → produce `docs/graphify-out/graph.json`.
- Verificar que el grafo cubre los archivos `.py` de `qa/` (PoC 1 ya validó: 291 nodos, 613 edges, 50.79% ahorro de tokens).
- Documentar en `docs/agent-protocol.md`: cuando un agente reciba una divergencia, consultar `docs/graphify-out/graph.json` para identificar archivos involucrados.
- **Validación**: medir tokens consumidos por un agente respondiendo "¿qué archivo produce SHADOW_MISMATCH?" con vs sin grafo. Gate: ≥30% menos tokens con grafo.

**2.3 — Separar runtime vs visual manifestos en `runtime_live_probe.py`**

- Separar `reasons` en `runtime_reasons` (hang, duplicate_hash, png_missing) y `visual_reasons` (vacío por ahora).
- Generar `PROBE_RUNTIME.json` y `PROBE_VISUAL.json` por separado.
- Subir timeout de 90s a 180s.
- **Validación**: `PROBE_RUNTIME.json` no contiene reasons visuales.

**Gate de salida Fase 2**:
- `odiff_runner.py` funciona. `diff_fidelity` con odiff reporta ≥40% menos FAILs que SSIM legacy.
- `docs/graphify-out/graph.json` existe con ≥200 nodos.
- `docs/agent-protocol.md` especifica cuándo consultarlo.
- `PROBE_RUNTIME.json` y `PROBE_VISUAL.json` separados.

---

### Fase 3 — Eliminar las 4 carpetas obsoletas + cleanup (2-3h)

**Branch**: misma `qa/canonical-source`. **Solo después de Fase 1+2 validados.**

**3.1 — Eliminar las 4 carpetas obsoletas**

```bash
git rm -r qa/mockup_reference_static
git rm -r qa/_mockup_targets
git rm -r qa/mockup_reference_normalized
git rm -r qa/_mockup_targets_normalized
```

**3.2 — Eliminar archivos que las referencian**

- `git rm qa/normalize_mockup_reference.py` (ya no se normaliza).
- `git rm qa/capture_mockup.py` (reemplazado por `capture_mockup_canonical.py`).
- `git rm -r qa/_fidelity_diff qa/_fidelity_current` (outputs obsoletos).
- Auditar `tessdata/` — si no se usa en código Python (búsqueda ya hecha: 0 hits), `git rm -r tessdata`.

**3.3 — Regenerar outputs de QA con la nueva canonical**

- `rm -rf qa/_visual_auditor_spec && python qa/visual_auditor_spec.py verify-all` (regenera `report.json` + `introspection.json` con specs nuevas).
- `rm -rf qa/_diff_results && python qa/diff_fidelity.py --target-dir qa/_mockup_canonical --actual-dir qa/_captures_v8` (regenera reports de diff con odiff).

**3.4 — Verificar que no quedan referencias rotas**

```bash
grep -rn "mockup_reference_static\|_mockup_targets\|mockup_reference_normalized\|_mockup_targets_normalized\|_fidelity_diff\|_fidelity_current" qa/ tests/ shared/ app/ hub/
```

- Gate: 0 hits en código Python activo. Los únicos hits permitidos son en archivos `.md` históricos (logs) que se conservan como registro.

**Gate de salida Fase 3**:
- Las 4 carpetas obsoletas eliminadas.
- 0 referencias rotas en código Python.
- `qa/_visual_auditor_spec/` y `qa/_diff_results/` regenerados con la nueva canonical.
- `pytest tests/` corre sin errores de import.

---

### Fase 4 — Medición de impacto y decisión de merge (2-3h)

**Branch**: se hace sobre la branch `qa/canonical-source` vs `main`.

**4.1 — Captura baseline final de `main`**

- `git stash` los cambios de la branch.
- `git checkout main`.
- Correr `capture_v8 --all` → guardar `report.json`, `FIDELITY_REPORT.csv`, `introspection.json` como `baseline_pre_restructure/`.
- `git checkout qa/canonical-source`.
- `git stash pop`.

**4.2 — Captura post-reestructuración**

- Correr `capture_v8 --all --introspect` sobre la branch con todos los fixes.
- Guardar como `post_restructure/`.

**4.3 — Comparar métricas**

| Métrica | Cómo se mide | Target |
|---|---|---|
| Divergencias totales (86 superficies) | `report.json` count + `introspection.json` count | ≤35% del baseline |
| Falsos positivos estimados | Sample manual de 20 divergencias, clasificar real vs FP | ≤20% FP (era ~80%) |
| Tiempo de pipeline `--all` | `time python qa/capture_v8.py --all --introspect` | ≤115% del baseline |
| Deuda visual real detectada | Nuevas divergencias de contracts ampliados | ≥5 nuevas deudas reales |
| Tokens por query de agente | `tiktoken` sobre el payload del agente con vs sin grafo | ≥30% menos con grafo |
| Consistencia de canonical | Captura Playwright fresca vs `qa/_mockup_canonical/` | SSIM ≥0.95 para ≥80/86 superficies |

**4.4 — Documentar resultados**

- `qa/RESTRUCTURE_RESULTS.md` (archivo nuevo, **solo tabla de métricas, sin prosa**).
- Si alguna métrica no cumple target, diagnosticar y decidir:
  - Si es fix P0 que no aportó → revertir ese fix específico.
  - Si es introspection que ralentizó → dejarla opt-in.
  - Si es odiff que no generalizó → mantener SSIM como fallback.

**Gate de salida Fase 4**:
- Si todos los targets cumplen → **PR a `main`**.
- Si no → merge parcial de lo que sí cumplió, dejar el resto en branch temporal.
- El owner decide merge final.

---

### Fase 5 — Hipotética, decisión del owner post-Fase 4

**NO ejecutar sin decisión explícita del owner.** Queda escrito como menú de opciones para cuando Fase 4 cierre.

**Opción 5.A — VLM como sidecar explicativo (NO oráculo)**

- Cuando odiff AA reporta `0.5% < diff_pct < 5%` (zona gris), llamar a un VLM (GLM-4V, Claude Vision, etc.) con ambas imágenes + el diff PNG y pedir: "¿esta diferencia es un bug de layout o solo variación de rendering? Responder en 1 frase."
- El VLM **nunca** decide PASS/FAIL — solo explica. La decisión la toma odiff.
- **Riesgo conocido**: VLM inestable (LOOP_LOG_V2.md documentó Kimi 1/4 OK, 5/5 timeouts). Mitigación: timeout 10s, fallback a "undecided" si falla.
- **Costo**: ~$0.01-0.05 por query VLM. Solo se llama en zona gris (estimado 10-20% de las superficies).

**Opción 5.B — Eliminar cross-renderer con QWebEngineView**

- Renderizar el mockup HTML dentro de Qt con `QWebEngineView` (que internamente es Chromium). Ambas capturas (mockup y app) salen del mismo Chromium → cae al caso "single-renderer diff" que odiff resuelve trivialmente.
- **Requisito**: instalar `PyQt6-WebEngine` + system deps (`libEGL.so.1`, `libnss3`, etc.).
- **Costo**: +150MB al installer. +1-2s al startup de captura.
- **Validación**: si se adopta, los FPs cross-renderer deben ir a ~0. Pero requiere que el mockup HTML sea HTML/CSS puro sin dependencias externas.
- **Nota**: esta opción NO reemplaza `qa/_mockup_canonical/` (sigue siendo la fuente para specs y odiff). La reemplaza por capturas QWebEngineView si el owner prefiere single-renderer.

**Opción 5.C — Applitools Eyes SDK (comercial)**

- SDK genérico de imágenes: se le pasa la captura Qt como baseline y el mockup como check.
- Costo: decenas de miles de euros/año (según delta-qa). Black-box.
- **Solo evaluar si 5.A y 5.B no cierran el gap.**

**Opción 5.D — Cerrar y mantener**

- Si Fase 4 deja el sistema con ≤15% FP y el owner está conforme, no hacer Fase 5.
- Documentar el estado final y cerrar el roadmap.

**Decisión**: la toma el owner al cierre de Fase 4. El agente NO debe iniciar Fase 5 sin confirmación explícita.

---

## 4. Qué NO hace este plan (limitaciones explícitas)

1. **No re-arquitectura el pipeline a introspection-first puro desde el día 1.** Eso era la propuesta P2 del PDF original. Es demasiado riesgo sin validación previa. Fase 5.B lo introduce gradualmente si el owner lo decide.
2. **No integra VLM como oráculo binario.** La literatura peer-reviewed (Ju et al. 2024, 89% FP) y la experiencia del owner (Kimi 5/5 timeouts) lo descartan. Si se usa VLM, es como sidecar explicativo en Fase 5.A opcional.
3. **No mueve specs a manuales para las 86 superficies.** Specs auto-generadas (con fixes P0 aplicados) cubren todo. Specs manuales solo se introducirían en Fase 5 si el owner decide ampliar.
4. **No toca lógica clínica, DB, auth, sync, IA, PDF, builder, instaladores.** Regla del owner.
5. **No declara PASS global.** Regla del owner.
6. **No confía en las auditorías previas.** Dado que las 4 carpetas canónicas eran inconsistentes, cualquier "fix" pasado basado en ellas es cuestionable. El plan NO revierte fixes pasados (sería demasiado riesgo), pero sí establece que **la nueva canonical es la fuente de verdad going forward**.

---

## 5. Riesgos identificados y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| **El HTML no es navegable vía `go(view, state)` para todas las superficies** | Media | Alto | Fase 0.1 valida las 86 superficies. Si alguna no es navegable, mapearla manualmente o marcarla como "no capturable" en el manifest. |
| **Playwright no reproduce el HTML exactamente como el browser del owner** | Baja | Medio | Fase 0.2 requiere aprobación humana del collage de 5 superficies. Si el owner rechaza, se ajusta el script. |
| **La canonical nueva revela diffs reales que la obsoleta ocultaba** | Alta | Medio (ruido temporal) | Es esperado y deseado. Los nuevos FAILs son signal real, no ruido. Documentar en Fase 4. |
| **odiff AA no generaliza a otras superficies** | Media | Alto | Fase 2.1 mide sobre 86 superficies antes de comprometer. Si no generaliza, mantener SSIM como fallback. |
| **`vas_introspect` ralentiza capture_v8 >15%** | Media | Medio | Fase 1.4 mide antes de habilitar. Si >15%, dejar opt-in vía `--introspect`. |
| **graphify API inestable (branches v1...v8)** | Media | Bajo | Dev-tool out-of-band. Si rompe, no afecta el pipeline runtime. |
| **System deps PyQt6-WebEngine faltan** | Alta (ya visto) | Bloquea Fase 5.B | Documentar install instructivo. Fase 5.B es opcional. |
| **Agente se convierte en escritor de informes** | Media | Medio | Fase 0 y 4 prohiben prosa en archivos `.md` de QA. Solo tablas de métricas. |
| **Eliminación de carpetas obsoletas rompe algo no detectado** | Baja | Alto | Fase 3.4 hace grep exhaustivo antes de eliminar. Fase 3 solo corre tras Fase 1+2 validados. |
| **El HTML del mockup no es la fuente de verdad real** | Baja | Crítico | Si el owner confirma que el HTML es canónico (que lo es — `LOOP_LOG.md` lo cita como referencia), esto no aplica. Si el owner dice "el HTML también está mal", stop total y reauditar el HTML primero. |

---

## 6. Auto-review del plan

Antes de entregar este `.md`, se verificó:

### ✅ Chequeos lógicos

1. **Orden de fases**: Fase 0 establece canonical → Fase 1 migra verificadores → Fase 2 reemplaza SSIM + graphify → Fase 3 elimina obsoletas → Fase 4 mide → Fase 5 decide owner. Sin dependencias circulares.
2. **Fase 0 es bloqueante**: sin canonical confiable, nada de lo demás tiene sentido. Si Fase 0 no valida, no se avanza.
3. **Fase 3 solo tras Fase 1+2**: las carpetas obsoletas se eliminan solo después de que los verificadores apuntan a la nueva canonical.
4. **Gate criteria medibles**: cada fase tiene target numérico basado en PoCs reales.
5. **Owner aprueba canonical**: Fase 0.2 requiere aprobación humana explícita antes de avanzar.

### ✅ Hipótesis reemplazadas por mediciones

| Hipótesis | Reemplazada por | Evidencia |
|---|---|---|
| "Las 4 carpetas son canónicas" | **FALSO** — 4 carpetas inconsistentes entre sí y vs HTML fresco | PoC 3 y PoC 4: SSIM 0.07-0.12 entre carpetas y vs Playwright |
| "45% drop P0" | "Medir en Fase 1.2, gate ≥30%" | PoC 2b muestra variación real por superficie |
| "80% FP reduction" | "Medir en Fase 4, gate ≤20% FP" | Sample manual de 20 divergencias |
| "≥30% menos tokens con graphify" | **Medido: 50.79%** | PoC 1 sobre qa/ real |
| "odiff AA reduce 50% diff vs SSIM" | **Medido: 57% en imágenes reales** | PoC 2b sobre Emoción.png vs captura Qt |
| "Playwright puede capturar el HTML canónico" | **Medido: sí, vía `go(view, state)`** | PoC 3 capturó home, animo, home dark |

### ✅ Errores corregidos durante el auto-review

- **Error detectado**: Plan v2 no contemplaba que las carpetas canónicas eran obsoletas. **Corregido**: Fase 0 entera dedicada a establecer canonical nueva.
- **Error detectado**: Plan v2 decía "habilitar introspection por default". **Corregido**: ahora es opt-in vía `--introspect` (Fase 1.4 mide impacto antes).
- **Error detectado**: Plan v2 no validaba que odiff generalice a otras superficies. **Corregido**: Fase 2.1 mide 86 superficies antes de comprometer.
- **Error detectado**: Plan v2 mezclaba Fase 4 con Fase 5. **Corregido**: Fase 5 es hipotética, decisión del owner, con 4 opciones explícitas.
- **Error detectado**: Plan v2 no decía qué hacer si una PoC no valida. **Corregido**: cada PoC tiene gate explícito + acción "stop y reportar al owner".
- **Error detectado**: "Agente se convierte en escritor de informes" (riesgo del owner). **Corregido**: Fase 0 y 4 prohiben prosa en `.md` de QA; solo tablas de métricas.
- **Error detectado**: Plan v2 asumía que `_mockup_targets_normalized` y `mockup_reference_normalized` eran independientes. **Corregido**: PoC confirmó que son idénticas byte-a-byte (duplicadas).
- **Error detectado**: Plan v2 no contemplaba que los fixes pasados (50+ iteraciones) pueden haber alineado la app a una referencia incorrecta. **Corregido**: §0.6 lo documenta explícitamente y §4.6 establece que no se revierten fixes pasados pero la nueva canonical es la fuente going forward.

### ✅ Lecciones históricas respetadas

- **NO repite Sentinel/pHash** (descartado en SENTINEL_REMOVAL.md).
- **NO repite V3 LARGEST_BBOX_GUARDRAIL** (descartado en ANALISIS_CAUSA_RAIZ_V3.md).
- **NO repite GLM-4V/Gemini/Kimi como oráculo visual** (descartado en LOOP_LOG_V2.md). VLM solo como sidecar en Fase 5.A opcional.
- **NO repite `paintEvent` override** (descartado en LOOP_LOG_2.md iter 73).
- **NO repite cache en `t()`** (descartado en PERFORMANCE_AUDIT.md Fix #2).
- **Conserva migración controlada 1-test-por-commit** (funcionó en LOOP_LOG_3.md).
- **Conserva `vas_introspect`** (ya existe, solo falta habilitar y ampliar).
- **Conserva `retainSizeWhenHidden`** como patrón (funcionó en AUDITORIA_POSTFIX.md).
- **NO elimina carpetas obsoletas sin validar canonical nueva primero** (regla del owner: "hasta no tener capturas fiables del mockup, que esten auditadas y aprobadas, no se podra hacer ninguna auditoria QA ni fixes visuales").

---

## 7. Instrucciones para el agente que ejecuta este plan

1. **Leer primero**: este documento + `qa/SENTINEL_REMOVAL.md` + `qa/ANALISIS_CAUSA_RAIZ_V3.md` + `qa/LOOP_LOG_V2.md` + `qa/LOOP_LOG_3.md`. Entender qué ya se intentó antes de empezar.
2. **Branch**: `git checkout -b qa/canonical-source` desde `main`. Todo el trabajo de Fase 0-3 va ahí.
3. **Fase 0 es bloqueante**: si el owner no aprueba el collage de 5 superficies en Fase 0.2, **NO avanzar a Fase 1**. Reportar al owner con los datos.
4. **Fase por fase**: no saltar fases. Cada fase tiene gate de salida medible.
5. **Sin prosa en `.md` de QA**: `qa/RESTRUCTURE_RESULTS.md` y cualquier `.md` de PoC son tablas de datos, no informes. Si encontrás escribiendo párrafos, pará y convertí a tabla.
6. **Si una PoC no valida**: stop. Reportar al owner con los datos. No inventar fix para tener algo que commitear (regla "nunca commitees roto, nunca pares" del LOOP_LOG_V3.md).
7. **Commits atómicos**: 1 commit por paso de cada fase. Mensaje: `feat(qa): <paso>` o `fix(qa): <paso>`.
8. **No tocar main hasta Fase 4**. Si Fase 4 valida, PR a main. Si no, dejar en branch temporal.
9. **Fase 5 NO se ejecuta sin confirmación explícita del owner** al cierre de Fase 4.
10. **Regla crítica de Fase 0**: si al generar `qa/_mockup_canonical/` alguna superficie no es navegable vía `go(view, state)`, **no inventar la captura**. Mapearla manualmente o marcarla como "no capturable" en el manifest y reportar al owner.

---

## 8. Estado del plan

- **Versión**: 3.0 (post-PoCs reales + hallazgo de carpetas obsoletas).
- **Fecha**: 2026-06-26.
- **PoCs ejecutadas**: 5 (graphify tokens, odiff sintético, odiff imágenes reales, Playwright vs 4 carpetas, captura V8 vs 4 carpetas).
- **Hallazgo crítico nuevo**: las 4 carpetas canónicas son inconsistentes entre sí y vs HTML fresco. Deben eliminarse y reemplazarse por una única canonical generada vía Playwright.
- **Basado en**: 15 logs históricos auditados + research web (delta-qa, OverlayQA, Trilogy AI, odiff GitHub, PerceptualDiff paper) + 5 PoCs reales.
- **Estado**: **CERRADO (2026-06-26)**. Fases 0-4 ejecutadas en branch `qa/canonical-source`,
  mergeadas a `main` vía PR #4. Fase 5 = **5.D (cerrar y mantener)**. Resultados en
  `qa/RESTRUCTURE_RESULTS.md`.
- **Decisiones del owner (resueltas)**:
  - Fase 0.2: canonical aprobada (pack `neuromood-mockup_reparado.html` + `generate_captures.js`).
  - Fase 4: PR #4 mergeado a main.
  - Fase 5: **5.D** elegida (FP ≈1.2% ≤15%); no se ejecutan 5.A/5.B/5.C.
- **Nota de ejecución**: la canonical NO se generó vía Playwright (§2.1 obsoleto); la
  receta ÚNICA y oficial aprobada por el owner es `generate_captures.js` (puppeteer)
  sobre `neuromood-mockup_reparado.html`. graphify = herramienta oficial out-of-band.
- **Deuda real abierta**: hub-detalle offset vertical sistemático (~10-15px) → UI migration.
