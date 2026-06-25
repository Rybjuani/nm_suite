# Análisis Técnico: Causa Raíz de ~68 Superficies NEEDS_HUMAN_REVIEW en visual_auditor_v3.py

## Resumen Ejecutivo

De 86 superficies analizadas, **68 caen en NEEDS_HUMAN_REVIEW (79%)**. La causa raíz **NO es OCR** en la mayoría de los casos. El problema principal es un **guardrail de bbox dominante (LARGEST_BBOX_GUARDRAIL = 0.35) que captura masivamente las diferencias de tema (light vs dark)** como "background-dominated image", forzando NHR aunque las métricas de similitud sean excelentes (SSIM ~1.0, changed_pixel_ratio < 0.25).

---

## 1. Distribución de Decisiones

| Decisión | Count | % |
|----------|-------|---|
| NEEDS_HUMAN_REVIEW | 68 | 79% |
| FIX_PRODUCT_REVIEW | 18 | 21% |
| FIX_PRODUCT_STRONG | 0 | 0% |
| RENDER_NOISE_OK | 0 | 0% |

**Problema fundamental**: Ninguna superficie llega a RENDER_NOISE_OK o FIX_PRODUCT_STRONG. El algoritmo es demasiado defensivo.

---

## 2. Causa Raíz #1: Guardrail de BBox Dominante (Líneas 553, 992-1152)

### El Problema

```python
# Línea 553
LARGEST_BBOX_GUARDRAIL = 0.35

# Líneas 992-993
largest_bbox_area = max((b.area_ratio for b in bboxes), default=0.0)
biggest_bbox_dominates = largest_bbox_area > LARGEST_BBOX_GUARDRAIL

# Líneas 1126-1152: Si biggest_bbox_dominates, FORZAR NHR
if biggest_bbox_dominates:
    confidence = "low"
    confidence_reason = f"largest_bbox_area_ratio={largest_bbox_area:.3f} >{LARGEST_BBOX_GUARDRAIL}; background-dominated image..."
    labels = [lbl for lbl in labels if lbl not in ("TEXT_MISMATCH_PROBABLE", "COLOR_MISMATCH")]
    decision = "NEEDS_HUMAN_REVIEW"
    return Classification(...)
```

### Impacto Real

**33 superficies light-theme** caen en este guardrail con `largest_bbox_area_ratio` entre 0.81 y 1.0. Ejemplos:

| Superficie | SSIM | changed_pixel_ratio | largest_bbox | Razón real del diff |
|------------|------|---------------------|--------------|---------------------|
| suite:home@light | 0.9999 | 0.2465 | 0.8865 | Tema light vs dark (fondo blanco vs gris) |
| suite:avisos@light | 1.0 | 0.1111 | 0.9283 | Tema light vs dark |
| suite:dbt-library@light | 1.0 | 0.1579 | 1.0 | Tema light vs dark |
| hub:pacientes@dark | 0.9993 | 0.0954 | 0.8114 | Fondo oscuro difuso |

**Observación crítica**: Estas superficies tienen **SSIM ~1.0 y changed_pixel_ratio < 0.25**, lo que indica que las diferencias son **mínimas y globales** (cambio de fondo de tema), no localizadas. El algoritmo las trata como "background-dominated" y las manda a revisión humana.

### Por Qué Sucede

1. **El diff threshold es 20** (línea 462: `mask = diff_arr > 20`), lo cual es razonable para capturar cambios visibles.
2. **Pero en temas light**, el fondo blanco del mockup vs el fondo gris/azulado de la captura real genera un **diff global uniforme** que `ndimage.label` agrupa en **1-2 bboxes enormes** que cubren casi toda la imagen.
3. **El guardrail de 0.35** asume que cualquier bbox >35% es "background noise", pero en este caso el diff global ES el cambio de tema intencional.

---

## 3. Causa Raíz #2: Clasificación Demasiado Defensiva en Tema Light (Líneas 1004-1024)

### El Problema

El texto en capturas light-theme tiene bajo contraste (gris claro sobre blanco), lo que hace que OCR falle o produzca "worst_fuzzy_real = 0". Como `_looks_like_real_text_pair()` devuelve False (líneas 636-677), el algoritmo no puede emitir `TEXT_MISMATCH_PROBABLE` ni `FIX_PRODUCT_REVIEW`.

Ejemplo: `suite:respiracion@dark` tiene `worst_fuzzy_real=0` → "No strong textual or color evidence" → NHR.

### Impacto

9 superficies dark-theme caen en NHR por `worst_fuzzy_real=0` a pesar de tener diffs visibles. Esto sugiere que:
- El preprocesamiento OCR (`_preprocess_for_ocr`, línea 527) no es suficiente para dark theme con bajo contraste.
- La heurística `_looks_like_real_text_pair` es demasiado estricta cuando OCR devuelve strings cortas o incompletas.

---

## 4. Causa Raíz #3: CHROME_MISMATCH No Produce Decision Accionable (Líneas 1046-1053)

### El Problema

```python
# Líneas 1046-1053
if analysis["touches_borders"]:
    chrome_mismatch = True  # Se marca pero NO empuja FIX_PRODUCT_REVIEW
```

52 superficies tienen `CHROME_MISMATCH` en labels, pero este label **no contribuye a ninguna decision** (línea 1154: "chrome_mismatch is intentionally excluded"). Esto está bien diseñado, pero significa que si el único diff detectado es chrome/borde, la superficie cae en NHR por falta de "actionable evidence".

Esto es correcto para chrome, pero el problema es que **en light theme, el diff global se detecta como CHROME_MISMATCH** (porque el bbox grande toca los bordes), y como no hay otros labels accionables, cae en NHR.

---

## 5. Causa Raíz #4: changed_pixel_ratio No Se Usa en la Decisión

### El Problema

Aunque `changed_pixel_ratio` se computa (línea 784), **nunca se usa en la lógica de decisión**. Una superficie con `changed_pixel_ratio = 0.02` (2% de píxeles cambiados) y `SSIM = 0.999` se trata igual que una con `changed_pixel_ratio = 0.8`.

Esto significa que **no hay umbral de "insignificancia"** basado en métricas globales. Si hay un diff (aunque sea 1% de píxeles), y el bbox resultante es grande, cae en NHR.

---

## 6. Causa Raíz #5: diff_fidelity vs V3 No Está Integrado

### El Problema

El código tiene `_check_fidelity_available()` (líneas 266-283) y `fidelity_available` se propaga al agent package, pero **los números de diff_fidelity (SSIM, MSE, etc.) no se usan para ponderar la decisión del V3**.

Si diff_fidelity ya reportó que una superficie tiene SSIM > 0.99 y MSE bajo, el V3 debería poder usar eso para decidir `RENDER_NOISE_OK` o al menos no forzar NHR.

---

## 7. Propuestas de Fix

### Fix A: Ajustar LARGEST_BBOX_GUARDRAIL con Métricas Globales (Línea 553, 1126-1152)

**Cambio**: No forzar NHR solo porque `largest_bbox_area > 0.35`. Considerar también métricas globales:

```python
# Líneas 1126-1152 (propuesto)
if biggest_bbox_dominates:
    # Si el diff es global pero pequeño (tema light), es RENDER_NOISE_OK
    if metrics.changed_pixel_ratio < 0.30 and metrics.ssim > 0.99:
        return Classification(
            labels=["RENDER_NOISE"] if chrome_mismatch else [],
            severity="low",
            explanation="Global low-magnitude diff consistent with theme variation",
            decision="RENDER_NOISE_OK",
            confidence="high",
            confidence_reason="SSIM>0.99 and changed_pixel_ratio<0.30 indicate theme-level variation, not actionable defect",
        )
    # Si el diff es global y grande, mantener NHR
    confidence = "low"
    ...
```

**Impacto esperado**: ~30 superficies light-theme pasarían de NHR a RENDER_NOISE_OK.

### Fix B: Usar changed_pixel_ratio como Umbral de Insignificancia (Líneas 1164-1167)

**Cambio**: Añadir un umbral de `changed_pixel_ratio` antes de forzar NHR:

```python
# Líneas 1164-1167 (propuesto)
if render_noise and not any([text_mismatch, color_mismatch, missing_component, extra_component]):
    decision = "RENDER_NOISE_OK"
elif metrics.changed_pixel_ratio < 0.05 and metrics.ssim > 0.995:
    # Diferencias imperceptibles / tema
    decision = "RENDER_NOISE_OK"
    labels = ["RENDER_NOISE"]
    confidence = "high"
else:
    decision = "NEEDS_HUMAN_REVIEW"
```

### Fix C: Separar Diff de Tema (Light/Dark) del Diff de Producto (Líneas 460-462)

**Cambio**: Detectar si el diff es principalmente un cambio de fondo global (tema) vs un cambio localizado (componente):

```python
# Líneas 460-462 (propuesto)
# Añadir análisis de "diff uniformity"
diff_arr = np.array(diff.convert("L"))
mask = diff_arr > 20
# Si el diff es uniforme (baja varianza espacial), es probablemente tema
if mask.mean() > 0 and mask.std() < threshold:
    # Diff uniforme = tema, no defecto
    pass
```

### Fix D: Integrar Métricas de diff_fidelity en la Decisión (Línea 1763)

**Cambio**: Leer el FIDELITY_REPORT.json por superficie y usar SSIM/MSE como señal adicional:

```python
# En analyze_surface() (línea 1763)
fidelity_entry = fidelity_data.get(surface_key, {})
fidelity_ssim = fidelity_entry.get("ssim", 0)
if fidelity_ssim > 0.99 and metrics.ssim > 0.99:
    # Consenso entre diff_fidelity y V3: es noise
    ...
```

### Fix E: Relajar _looks_like_real_text_pair para Capturas de Bajo Contraste (Líneas 636-677)

**Cambio**: Permitir pares de OCR con `worst_fuzzy < 85` aunque no pasen el test de tokens compartidos, siempre que ambos lados tengan al menos una palabra real:

```python
# Líneas 663-677 (propuesto)
# Si no hay overlap de tokens pero ambos lados tienen texto real,
# permitir el par si fuzzy < 50 (indica cambio de contenido real)
if overlap == 0:
    if len(m_words) >= 2 and len(r_words) >= 2 and worst_fuzzy < 50:
        return True
    ...
```

### Fix F: Ajustar el Diff Threshold por Tema (Línea 462)

**Cambio**: Usar un threshold adaptativo basado en el brillo medio de la imagen:

```python
# Línea 462 (propuesto)
mean_luminance = np.array(mockup.convert("L")).mean()
if mean_luminance > 200:  # Tema light (fondo blanco)
    threshold = 35  # Requiere diff más grande para ser significativo
else:
    threshold = 20  # Tema dark, threshold normal
mask = diff_arr > threshold
```

---

## 8. Conclusiones

1. **La causa raíz principal** es el guardrail `LARGEST_BBOX_GUARDRAIL = 0.35` combinado con la falta de consideración de métricas globales (SSIM, changed_pixel_ratio) en la decisión final.

2. **El diff en light theme** es global (cambio de fondo) y se agrupa en bboxes enormes que activan el guardrail. Esto no es un defecto del producto, es una variación de tema.

3. **El algoritmo necesita un "escape hatch"** para diffs globales de baja magnitud: si SSIM > 0.99 y changed_pixel_ratio < 0.30, debería poder decidir `RENDER_NOISE_OK` aunque el bbox sea grande.

4. **La integración con diff_fidelity** es superficial (solo verifica existencia). Debería usar los números de diff_fidelity como señal de calidad.

5. **Recomendación inmediata**: Implementar Fix A (ajustar guardrail con métricas globales) + Fix B (umbral de changed_pixel_ratio). Esto reduciría NHR de 68 a aproximadamente 20-25 superficies, dejando solo las que realmente tienen evidencia accionable.
