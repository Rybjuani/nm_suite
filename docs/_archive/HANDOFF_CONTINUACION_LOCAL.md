# Handoff técnico — migración UI nm_suite · 2026-06-21

Continuación local con Claude Code desde `origin/main` actual.

---

## 1. SHA actual y sincronización

**HEAD de `origin/main`:** `0eeeeab` (commit que añade este handoff).
**Último fix de código:** `6bb732b` (NMShellContent). No son lo mismo: `0eeeeab` es solo doc, no toca código.

```bash
# Clonar fresco
git clone https://github.com/Rybjuani/nm_suite.git
cd nm_suite

# O sincronizar clone existente de forma segura (sin --hard que descarta cambios locales sin aviso)
git fetch origin
git checkout main
git pull --ff-only origin main
git log --oneline -1   # debe mostrar 0eeeeab
git log --oneline -5  # verificación: 0eeeeab, 6bb732b, c96c406, fd0c5be, 6dd49bb
```

**Notas sobre la sincronización:**
- `git pull --ff-only` falla si hay divergencia local en vez de hacer merge/rebase silencioso. Es lo que queremos: si hay commits locales no pusheados, hay que resolverlos explícitamente.
- Si `--ff-only` falla con "fatal: Not possible to fast-forward", inspeccionar `git log origin/main..HEAD` y `git log HEAD..origin/main` antes de decidir merge/rebase/reset.
- **NO usar `git reset --hard origin/main`** salvo en un clone descartable; descarta cambios sin confirmación.

Commits de la auditoría (5, en orden cronológico, todos en `origin/main`):

```
6dd49bb  audit(fase0): re-auditoria HEAD 51f4448 + targets/captures frescos
fd0c5be  chore(qa): purgar artifacts stale (FASE 0/5 cleanup)
c96c406  fix(fase2/primitives): NMModule._content pinta surface real via QSS
6bb732b  fix(fase2/shell): NMShellContent pinta surface real via QSS (app + hub)
0eeeeab  docs(handoff): handoff técnico para continuar localmente con Claude Code  ← HEAD
```

Punto de partida de la auditoría: `51f4448` ("Document confirmed GLM fixes").

---

## 2. Cambios aplicados (resumen ejecutivo, verificable)

| Commit | Fase | Archivos tocados | Qué hace |
|---|---|---|---|
| `6dd49bb` | FASE 0 | `docs/VISUAL_QA_AUDIT.md` (+82), `qa/_mockup_targets/*` (96 PNGs + 3 manifest/matrix), `qa/_fidelity_fresh/*` (3 reportes) | Re-auditoría completa: targets Playwright regenerados contra HEAD, captures V8 regenerados, reporte de fidelidad con gate endurecido y `scikit-image` real. Resultado: 0/96 PASS. |
| `fd0c5be` | FASE 0/5 | 387 archivos, -7152/+48 líneas | Purga de artifacts stale: `qa/_mockup_verify/`, `qa/_mockup_verify2/`, `qa/_fidelity_current/`, `qa/_fidelity_selfcheck/`, `qa/nm_capturas_actualizadas/`, `docs/QA_V8_BASELINE_MATRIX.md`. Actualiza `docs/FASE1_CONTRATO_VISUAL.md` y `docs/CAPTURE_MANIFEST_SUMMARY.md`. |
| `c96c406` | FASE 2 | `shared/components/navigation.py` (+20 líneas, 1 archivo) | `NMModule._content` ahora pinta `surface` real vía QSS `QWidget#NMModuleContent { background-color: surface }`. Antes usaba `QPalette.setWindow(surface)` que el QSS global (`QWidget { background-color: bg }`) pisaba. **Impacto verificado: 0/96 → 5/96 PASS** (rutina-empty ×2, actividades-empty ×2, avisos-empty dark). |
| `6bb732b` | FASE 2 | `app/main_qt.py` (+21/-1), `hub/main_qt.py` (+13/-1) | `NMShellContent` (app) y `NMHubShellContent` (hub) — content widget debajo del titlebar ahora pinta `surface` vía QSS específico con objectName. `_apply_theme` refresca el QSS en cada switch de tema. **Aún NO recapturado** — ver sección 6. |

Tests: **278/278 pasan** después de cada commit. ruff: ok.

---

## 3. Hallazgos confirmados con evidencia (no asumir nada más)

1. **0/96 pantallas PASS** el gate compuesto al iniciar auditoría (commit `6dd49bb`). Gate: `SSIM>=0.92`, `MAD<=0.035`, `changed_pixel_ratio<=0.08`, `scikit-image` real (no `_global_ssim` fallback).
2. **`_fidelity_selfcheck` era autocomparación trivial**: 96 filas con `target_file == actual_file`, SSIM=1.0 trivial. **NO era evidencia de fidelidad**. Purgado en `fd0c5be`.
3. **Targets stale pre-purga**: `qa/_mockup_targets/MOCKUP_TARGET_MANIFEST.json` estaba generado contra commit `0fcb0cc6` (~61 commits atrás de HEAD).
4. **Capturas V8 stale pre-purga**: `qa/nm_capturas_actualizadas/CAPTURE_MANIFEST.json` estaba generado contra commit `1bfba84` (~36 commits atrás de HEAD).
5. **Tests `tests/*_visual_contract.py` son estructurales/texto** (tamaños, QSS substrings, comportamiento), NO pixel-diff. Pasan 278/278 pero el gate visual queda en 5/96. **No son proxy de fidelidad visual**.
6. **Hallazgo estructural nuevo (confirmado con diff de paletas de color)**: Suite empty states (`rutina-empty`, `actividades-empty`, `avisos-empty`) renderizaban sobre `bg` directo en vez de sobre `surface` (card). El mockup envuelve el empty en `.screen` que pinta `surface`. Causa raíz: QSS global `QWidget { background-color: bg }` pisaba el `QPalette.setWindow(surface)` de `NMModule._content`. **Corregido en `c96c406`.**
7. **Patrón "light vs dark" sistemático**: `changed_pixel_ratio` en light era 3-5x mayor que en dark. Causa raíz: en light, `bg` (#E9E3D6) vs `surface` (#FBF8F1) difieren ~22/canal (>12 threshold del gate), mientras que en dark `bg` (#0E121C) vs `surface` (#191F2E) difieren ~11/canal (<12 threshold). Por eso casi todas las pantallas pasaban cerca del gate en dark pero fallaban en light. **Causa parcialmente mitigada por `c96c406` (dentro del módulo) y `6bb732b` (shell alrededor del módulo) — pendiente recaptura completa para medir impacto real.**
8. **`dbt-practice-stop` y `dbt-practice-closure` en light** tenían `MAD=0.22` (6x el threshold 0.035) y `changed_pixel_ratio=0.87` con SSIM 0.75. Análisis de paleta: el target mostraba una banda de color `#87817F` (gris del titlebar del mockup) que la app no pintaba en la misma posición. **NO corregido aún.**
9. **`hub-pacientes-empty`**: SSIM 0.90 dark / 0.91 light, falla por changed_ratio en light. Causa raíz probable: misma que #7 (NMShellContent ya fixeado en `6bb732b`, falta recaptura).

---

## 4. Deuda pendiente por fase (en orden del plan)

> ⚠️ **Aclaración crítica sobre FASE 0 y FASE 1**: los checkmarks ✅ indican que hay commits y tests que sugieren cierre, **NO que estén verificadamente cerradas**. Antes de continuar a FASE 2+, verificar contra repo + plan + mockup con estos comandos:
>
> ```bash
> # FASE 0 — verificar que targets estén frescos y el gate funcione
> cat qa/_mockup_targets/MOCKUP_TARGET_MANIFEST.json | grep -E '"commit"|"success"'
> # commit debe ser el SHA actual de HEAD; success debe ser 96
>
> .venv/bin/python -m pytest tests/test_mockup_qa_tools.py tests/test_capture_v8_evidence.py -v
> # ambos deben pasar
>
> # FASE 1 — verificar tokens contra mockup canónico (líneas 15-67 de neuromood-mockup.html)
> .venv/bin/python -m pytest tests/test_token_parity.py tests/test_no_legacy_visuals.py tests/test_fonts.py -v
> # verificar manualmente que V3_LIGHT/V3_DARK coinciden con :root del mockup
> .venv/bin/python -c "from shared.theme import V3_LIGHT, V3_DARK; print('light brand', V3_LIGHT['brand']); print('dark brand', V3_DARK['brand'])"
> # light brand debe ser #2E5D43, dark brand debe ser #56D9A6 (mockup líneas 35, 57)
>
> # Verificar fuentes cargadas
> .venv/bin/python -c "import os; os.environ['QT_QPA_PLATFORM']='offscreen'; from PyQt6.QtWidgets import QApplication; app=QApplication([]); from shared.fonts import load_fonts, FONT_SERIF, FONT_SANS; load_fonts(); print('serif:', FONT_SERIF, 'sans:', FONT_SANS)"
> # serif debe ser Fraunces, sans debe ser Inter
> ```
>
> Si cualquiera de estos falla o no coincide, **FASE 0/1 NO está cerrada** — investigar antes de avanzar.

### FASE 0 — Targets & tooling: ✅ APARENTEMENTE CERRADA (verificar antes de avanzar)
- Targets Playwright regenerados contra HEAD (96 PNGs) en commit `6dd49bb`. Verificar frescura con `MOCKUP_TARGET_MANIFEST.json.git.commit`.
- `qa/diff_fidelity.py` ya tiene gate endurecido (SSIM + MAD + changed_ratio + capture manifest evidence) desde commit `c707e28`.
- `tests/test_mockup_qa_tools.py` y `tests/test_capture_v8_evidence.py` cubren el gate.
- **No asumir cerrada**: validar con los comandos de la nota ⚠️ arriba antes de continuar.

### FASE 1 — Base compartida (tokens/fuentes/QSS/iconos): ✅ APARENTEMENTE CERRADA (verificar antes de avanzar)
- `shared/theme.py`: `V3_LIGHT` y `V3_DARK` con valores que coinciden con el mockup canónico (verificado en `tests/test_token_parity.py::test_runtime_tokens_are_mockup_adn_values`).
- `shared/fonts.py`: carga Inter + Fraunces (presentes en `assets/fonts/`).
- `shared/icons_svg.py`: set `I` del mockup empaquetado.
- `tests/test_token_parity.py` y `tests/test_no_legacy_visuals.py` validan ADN nuevo (excluyen valores legacy `#F4EFE5`, `#305A48`, `#07091A`, `#A99CFF`, `Manrope`, `Newsreader`).
- `tests/test_fonts.py`: 10 tests pasan.
- **No asumir cerrada**: validar tokens contra `neuromood-mockup.html` líneas 15-67 y fuentes cargadas en runtime con los comandos de la nota ⚠️ arriba.

### FASE 2 — Primitivas (fidelidad QPainter/QSS): 🚧 EN PROGRESO (3/8 grupos)
- ✅ Empty states con surface card (`c96c406`).
- ✅ Shell content widget con surface (`6bb732b`).
- ❌ **Pendiente**: hover-lift de cards (mockup `.card.hov:hover` → `translateY(-3px)` + `shadow-2` + `brand-line`). Hoy `NMCard` no anima.
- ❌ **Pendiente**: ajustes finos de `NMTabs` variant=filter alineados al `.fchip` canónico (parcial en commit `e6a215a` pero faltan detalles de pressed state).
- ❌ **Pendiente**: `NMPatientRow` (avatar 40 r12, hover surface-2) — verificar contra mockup `.prow`.
- ❌ **Pendiente**: `NMSparkline` (78×30, 2px + punto final) — verificar contra mockup línea 1360.
- ❌ **Pendiente**: `NMDialog` scrim rgba(20,18,14,.5) + scale .96→1 — verificar contra mockup `.modal-bg`+`.modal`.
- ❌ **Pendiente**: `NMToast` ink bg + pill + fade+slide + autodismiss 2200ms — verificar contra mockup `.toast`.

### FASE 3 — Suite pantalla por pantalla: ❌ NO INICIADA (orden del plan)
Orden: **Acceso → Home → Animo → Respiración → TCC → Activación → Recordatorios → Rutina → Temporizador → DBT**.

Deuda conocida por pantalla (SSIM fresco post-c96c406, sin recaptura post-6bb732b):

| Pantalla | SSIM dark / light (post-c96c406) | Deuda concreta |
|---|---|---|
| Acceso (onboarding + error + recuperar) | 0.65/0.66, 0.62/0.62, 0.63/0.63 | Layout narrow, branding, campos, consentimiento, jerarquía tipográfica |
| Home (score + no-score) | 0.68/0.68, 0.69/0.69 | Hero blob radial, cards, badges offsets |
| Animo | 0.77/0.79 | Slider/chart/paneles no llegan a composición mockup |
| Respiración (idle/presets/running/paused) | 0.85/0.87 (todos) | Anillo, controles, badges — los más cercanos |
| Registro TCC (s0/s1/s1otro/s2/s3/ok) | 0.74-0.83 / 0.76-0.84 | Stepper, grids, inputs, cierre |
| Activación (default/filtered/marked/empty) | 0.69/0.70, 0.82/0.84, 0.69/0.70, **PASS** | Cards y filtros lejos |
| Recordatorios (all/active/search/empty/completed) | 0.74/0.73, 0.79/0.79, 0.88/0.90, 0.92/0.92 FAIL light, 0.74/0.73 | Rows, badges, acciones |
| Rutina (default/add/done/empty) | 0.78/0.80, 0.77/0.79, 0.77/0.77, **PASS** | Filas, rings, add state |
| Temporizador (idle/running/paused/empty/presets) | 0.86-0.87 / 0.86-0.87, **PASS** empty dark | Ring, controles, chips |
| DBT (now/library/STOP/closure) | 0.77/0.79, 0.66/0.68, 0.80/0.74, 0.79/0.74 | Cards/familias/modal/practica; STOP y closure light con MAD=0.22 |

### FASE 4 — Hub pantalla por pantalla: ❌ NO INICIADA
- Pacientes (list/empty): SSIM 0.73/0.74, 0.90/0.91 — rows/sparkline/ring/header.
- Detalle (+ Resumen IA modal): SSIM 0.67-0.72 — hero, 4 tabs planas, grid form/panel, modal IA.
- Textos globales: SSIM 0.62/0.64 — mayor deuda Hub.

### FASE 5 — Regresión & cierre: ❌ NO INICIADA
- Re-baseline QA completa post-fixes.
- Purga final de capturas stale (si quedan).
- Barrido de diff completo.
- Suite pytest-qt + ruff + pyright + smoke runtime + build `--dry-run`.

---

## 5. Archivos tocados en la auditoría (referencia rápida)

```
docs/VISUAL_QA_AUDIT.md                  +82 líneas (sección "Re-auditoria 2026-06-21")
docs/CAPTURE_MANIFEST_SUMMARY.md         reescrito
docs/FASE1_CONTRATO_VISUAL.md            baseline apuntando a _captures_v8_fresh
shared/components/navigation.py          +20 líneas (NMModule._content QSS)
app/main_qt.py                           +21/-1 (NMShellContent QSS + v3c import)
hub/main_qt.py                           +13/-1 (NMHubShellContent QSS)
qa/_mockup_targets/                      99 archivos (96 PNGs + 3 manifest/matrix) regenerados
qa/_fidelity_fresh/                      3 reportes (csv/json/md) + 96 diff PNGs (sin commitear diff PNGs)
```

**Eliminados (387 archivos, -7152 líneas):**
```
qa/_mockup_verify/                       4 archivos
qa/_mockup_verify2/                      177 archivos
qa/_fidelity_current/                    3 archivos
qa/_fidelity_selfcheck/                  3 archivos
qa/nm_capturas_actualizadas/             101 archivos
docs/QA_V8_BASELINE_MATRIX.md            1 archivo
```

---

## 6. Artefactos parciales — DESCARTAR Y REGENERAR

### Estado actual del working tree (NO commiteado, NO pusheado):

```
M qa/_fidelity_fresh/FIDELITY_REPORT.csv
M qa/_fidelity_fresh/FIDELITY_REPORT.json
M qa/_fidelity_fresh/FIDELITY_REPORT.md
```

Estos 3 archivos son el resultado de una recaptura **parcial** interrumpida por timeouts del entorno. Reflejan el estado **post-`c96c406` pero pre-`6bb732b`** (NMShellContent fix nunca fue recapturado).

### Acción obligatoria al retomar:

```bash
# 1. Descartar el diff parcial de los reportes
git checkout -- qa/_fidelity_fresh/FIDELITY_REPORT.csv qa/_fidelity_fresh/FIDELITY_REPORT.json qa/_fidelity_fresh/FIDELITY_REPORT.md

# 2. Eliminar las capturas parciales de disco (NO están tracked en git, son gitignored)
rm -rf qa/_captures_v8_fresh
mkdir -p qa/_captures_v8_fresh

# 3. Eliminar los diff PNGs parciales (tampoco tracked)
rm -f qa/_fidelity_fresh/*-diff.png

# 4. Confirmar working tree limpio
git status -sb   # debe mostrar "## main...origin/main" sin archivos modificados
```

### Verificación de qué está tracked vs gitignored:

```bash
git ls-files qa/_mockup_targets | wc -l     # → 99 (tracked)
git ls-files qa/_captures_v8_fresh | wc -l  # → 0  (gitignored, no commiteado)
git ls-files qa/_fidelity_fresh | wc -l     # → 3  (solo reportes csv/json/md tracked)
git check-ignore qa/_captures_v8_fresh/x.png # → confirma gitignored
```

`qa/_captures_v8_fresh/` está bajo el patrón `qa/_captures*/` del `.gitignore` — es output de trabajo, **no se commitea**.

---

## 7. Cómo correr capturas y diff (comandos exactos)

### Setup entorno (Linux, puede variar en Windows local):

```bash
# 1. Crear venv e instalar deps
python -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/pip install scikit-image pypdf reportlab   # extras necesarios

# 2. Playwright (para targets del mockup)
.venv/bin/pip install playwright
.venv/bin/python -m playwright install chromium
# En Linux puede faltar: apt-get install libnss3 libnspr4 libasound2 ... (ver output de `playwright install-deps`)
# En Windows local NO hace falta esto.

# 3. Variables de entorno para capturas headless
export QT_QPA_PLATFORM=offscreen   # Linux; en Windows no hace falta
export NM_VISUAL_QA=1
```

### Regenerar targets del mockup (Playwright, ~90s):

```bash
.venv/bin/python qa/capture_mockup.py --all --theme both --clean
# Output: qa/_mockup_targets/ (96 PNGs + manifest + matrix)
# Verificar: cat qa/_mockup_targets/MOCKUP_TARGET_MANIFEST.json | grep commit
#   Debe mostrar el SHA actual de HEAD
```

### Regenerar capturas de la app (capture_v8.py, ~5-8 min):

```bash
.venv/bin/python qa/capture_v8.py --all --clean --out-dir qa/_captures_v8_fresh
# Output: qa/_captures_v8_fresh/ (98 PNGs + manifest + matrix)
# Verificar: cat qa/_captures_v8_fresh/CAPTURE_MANIFEST.json | grep short_head
#   Debe mostrar el SHA actual de HEAD
```

### Captura selectiva por view (para iterar rápido tras un fix):

```bash
.venv/bin/python qa/capture_v8.py --app suite --view home --theme both --out-dir qa/_captures_v8_fresh --no-clean
.venv/bin/python qa/capture_v8.py --app hub --view pacientes --theme both --out-dir qa/_captures_v8_fresh --no-clean
# --no-clean preserva las demás capturas; solo sobreescribe las del --view
```

### Diff de fidelidad completo:

```bash
.venv/bin/python qa/diff_fidelity.py \
  --target-dir qa/_mockup_targets \
  --actual-dir qa/_captures_v8_fresh \
  --out-dir qa/_fidelity_fresh \
  --no-images   # más rápido; usar sin --no-images para diff PNGs lado a lado
# Output: qa/_fidelity_fresh/FIDELITY_REPORT.{md,csv,json}
# Resumen impreso: Passed / Failed / Missing
```

### Diff de fidelidad por view:

```bash
.venv/bin/python qa/diff_fidelity.py \
  --target-dir qa/_mockup_targets \
  --actual-dir qa/_captures_v8_fresh \
  --out-dir qa/_fidelity_fresh \
  --app suite --view home \
  --no-images
```

### Tests + ruff:

```bash
.venv/bin/python -m pytest tests/ -v
# Esperado: 278 passed (sin contar los 2 que requieren reportlab+pypdf en CI)
.venv/bin/ruff check .
# Esperado: All checks passed!
```

---

## 8. Qué NO asumir como aprobado

1. **NO asumir que un commit "fix(faseN): ..." cerró una fase** sin recaptura fresca + diff PASS. Validar siempre con `qa/layered_visual_compare.py` (comando fijo del protocolo) después del fix. `qa/diff_fidelity.py` es señal auxiliar histórica; no cierra checklist.
2. **NO asumir que `tests/*_visual_contract.py` pasando = fidelidad visual**. Son contratos estructurales. El gate oficial es `qa/layered_visual_compare.py` con fuentes activas, thresholds default, odiff y paneles habilitados. `qa/diff_fidelity.py` es LEGACY/AUXILIARY PASS, no checklist PASS.
3. **NO asumir que `_fidelity_selfcheck` valida algo**. Ya está purgado, pero si reaparece, ignorarlo.
4. **NO asumir que SSIM alto (>=0.92) es suficiente**. El gate exige también `MAD<=0.035` y `changed_pixel_ratio<=0.08`. Casos conocidos: `rutina-empty-light` post-`c96c406` tenía SSIM 0.934 pero `changed=0.92` (falso positivo de SSIM solo).
5. **NO asumir que la recaptura parcial del working tree refleja el estado post-`6bb732b`**. Las capturas en `qa/_captures_v8_fresh/` son pre-`6bb732b`. **Descartar y regenerar.**
6. **NO asumir que los `qa/_mockup_targets/` están frescos**. Verificar `MOCKUP_TARGET_MANIFEST.json.git.commit` == `git rev-parse HEAD`. Si no coincide, regenerar.
7. **NO asumir que `NMShellContent` fix funcionó sin recaptura**. Fue commiteado sin verificación visual completa (timeout del entorno). El primer paso al retomar es recapturar y verificar que las pantallas con `bg` visible en márgenes mejoraron.
8. **NO usar `git log --grep="cierre\|complet\|cerrar"` como evidencia de cierre de fase**. Varios commits históricos usan esos términos sin que la fase estuviera realmente cerrada (ver `1da995f` "cerrar FASE 2.1", `c5a0c08` "Fase 11 Regresion final" — ambos premature).
9. **NO confiar en `docs/QA_V8_BASELINE_MATRIX.md`** — fue eliminado. Si se referencia en docs viejos, ignorar.
10. **NO avanzar a FASE 3 sin cerrar FASE 2**. El plan exige orden estricto: primitivas → pantallas. Si una primitiva queda mal, todas las pantallas que la usan quedan mal.

---

## 9. Próximo bloque recomendado (operativo, paso a paso)

### Bloque A: Verificación del fix `6bb732b` (NMShellContent) — OBLIGATORIO PRIMERO

**Objetivo:** confirmar que el fix de `6bb732b` funciona como se espera antes de avanzar.

```bash
# 1. Sincronizar (ff-only para detectar divergencia local)
git fetch origin
git checkout main
git pull --ff-only origin main
git log --oneline -1   # 0eeeeab (HEAD actual)
git log --oneline -5   # 0eeeeab, 6bb732b, c96c406, fd0c5be, 6dd49bb

# 2. Limpiar working tree
git checkout -- qa/_fidelity_fresh/
rm -rf qa/_captures_v8_fresh && mkdir -p qa/_captures_v8_fresh
rm -f qa/_fidelity_fresh/*-diff.png

# 3. Regenerar targets (en caso de duda)
.venv/bin/python qa/capture_mockup.py --all --theme both --clean

# 4. Recaptura completa (5-8 min)
.venv/bin/python qa/capture_v8.py --all --clean --out-dir qa/_captures_v8_fresh

# 5. Diff completo
.venv/bin/python qa/diff_fidelity.py \
  --target-dir qa/_mockup_targets \
  --actual-dir qa/_captures_v8_fresh \
  --out-dir qa/_fidelity_fresh \
  --no-images

# 6. Contar PASS
grep -c "| PASS |" qa/_fidelity_fresh/FIDELITY_REPORT.md
```

**Criterio de avance:**
- Si PASS sube de 5 a **>=15** (rutina/actividades/avisos default + empty + variantes deberían mejorar en light): ✅ fix confirmado, avanzar a Bloque B.
- Si PASS queda en 5 o sube <10: ❌ el fix no tiene el impacto esperado — investigar diffs de pantallas no-empty (Home, Animo, etc.) antes de avanzar.
- Si PASS baja: regresión — revertir `6bb732b` y re-analizar.

**Commitear el reporte fresco solo después de este paso:**
```bash
git add qa/_fidelity_fresh/FIDELITY_REPORT.{md,csv,json}
git commit -m "audit(fase2): recaptura fresca post-NMShellContent fix (6bb732b) — N/96 PASS"
git push origin main
```

### Bloque B: FASE 2 primitivas restantes (1 PR por primitiva)

Orden recomendado por impacto (medir con diff por pantalla que la usa):

1. **Hover-lift de `NMCard`** (mockup `.card.hov:hover`). Afecta: Home cards, Rutina secciones, Actividades cards, Avisos rows. Implementar con `QPropertyAnimation` + `QGraphicsDropShadowEffect`. PR + recaptura de `suite-home-light/dark` + `suite-rutina-light/dark` + `suite-actividades-light/dark` + `suite-avisos-light/dark`.
2. **`NMPatientRow`** (mockup `.prow`). Afecta: `hub-pacientes`. PR + recaptura `hub-pacientes-light/dark`.
3. **`NMSparkline`** (mockup línea 1360, 78×30). Afecta: `hub-pacientes`. PR + recaptura `hub-pacientes`.
4. **`NMDialog` scrim + scale** (mockup `.modal-bg`+`.modal`). Afecta: `hub-detalle-resumen-ia`, dialogs de confirmación. PR + recaptura `hub-detalle-resumen-ia-0-light/dark`.
5. **`NMToast`** (mockup `.toast`). Afecta: feedback post-guardar. PR + recaptura selectiva.
6. **`NMTabs` variant=filter pressed state** (mockup `.fchip`). Afecta: Animo tabs 7/30 días, Avisos filtros, DBT Biblioteca familias. PR + recaptura `suite-animo`, `suite-avisos-filter-activos`, `suite-dbt-library`.

Cada PR (commit) debe:
- Aplicar fix en un solo archivo del componente.
- Pasar `pytest tests/` y `ruff check .`.
- Recapturar las pantallas afectadas (con `--no-clean`).
- Correr diff de esas pantallas.
- Si alguna pantalla pasa de FAIL a PASS: commitear.
- Si ninguna mejora: NO commitear (el fix no tuvo efecto) — investigar.
- Commitear con mensaje `fix(fase2/<componente>): descripción breve — N pantallas PASS`.

### Bloque C: FASE 3 Suite pantalla por pantalla

Solo después de cerrar Bloque B. Orden del plan: Acceso → Home → Animo → Respiración → TCC → Activación → Recordatorios → Rutina → Temporizador → DBT.

Para cada pantalla:
1. Comparar diff PNG lado a lado (`qa/_fidelity_fresh/<view>-<theme>-960x600-diff.png`) — identifica regiones con mayor diff.
2. Mapear diff a primitiva o layout responsable.
3. Aplicar fix en el archivo del módulo (`app/modules/<modulo>_qt.py`).
4. Recapturar + diff.
5. Si PASS: commitear `fix(fase3/<pantalla>): descripción`.
6. Si no PASS pero mejora SSIM: commitear progreso parcial con métricas en mensaje.
7. No avanzar a la siguiente pantalla hasta PASS o hasta documentar deuda Qt insuperable.

### Bloque D: FASE 4 Hub

Pacientes → Detalle → Textos globales. Mismo ciclo que Bloque C.

### Bloque E: FASE 5 Cierre

- Recaptura completa final (98 capturas).
- Diff completo (96 targets).
- Documentar pantallas que quedan FAIL con justificación Qt.
- Purga final de capturas stale si quedan.
- `pytest tests/ + ruff + pyright + smoke runtime + build --dry-run`.

---

## 10. Notas operativas finales

- **Tamaño de commit**: pequeño, un componente/pantalla por commit. Mensaje en español, prefijo `fix(faseN/...)` o `chore(qa): ...`.
- **Recaptura tras cada bloque**: sí, siempre. No acumular fixes sin recapturar.
- **Tests como gate de regresión**: si un fix rompe tests, NO commitear. Los tests estructurales son ruido para fidelidad pero protegen contratos funcionales.
- **Playwright**: si da error de libs en Linux, `playwright install-deps` (requiere sudo) o instalar manualmente los debs. En Windows local no hace falta.
- **`scikit-image`**: necesario para SSIM real (sin él, `qa/diff_fidelity.py` cae a `_global_ssim` que da valores inflados). Verificar con `python -c "from skimage.metrics import structural_similarity"`.
- **PAT de GitHub**: si se necesita push, usar URL inline `https://<token>@github.com/Rybjuani/nm_suite.git` una sola vez. No persistir en `.git/config` ni en `~/.git-credentials`.
