# Defect Ledger — E0-PROBE-BASELINE

Baseline de evidencia para `PLAN_MIGRACION_UI_V2.md`. Audit read-only en HEAD `e95bc2b`
(`main` == `origin/main`; working tree solo con los `.md` del plan V2 — el fallo NO fue
introducido en esta sesión, es pre-existente en `main`).

> Nota de cierre: D001 fue resuelto posteriormente por `8638035`
> (`fix(ui): guard NMPlayButton size against global QPushButton QSS`) y validado en el
> cierre E5 (`c0c692e`) con `pytest tests/` → 317 passed y runtime probe 22/22.

## Baseline de gates

| Gate | Comando | Resultado |
|---|---|---|
| Runtime probe | `qa\runtime_live_probe.py --all --theme both` | **OK=22 / DEFECTS=0 / FAILED=0** (suite+hub × light/dark, 960×600). Manifest: `qa/_runtime_probe/PROBE_MANIFEST.json` |
| Pytest (suite completa) | `-m pytest tests/` | **289 passed / 1 failed** en 456s |
| Pytest (aislado, el que falla) | `pytest …::test_respiracion_matches_mockup_idle_contract` | **passed** en 1.25s |

Lectura: el runtime (lifecycle/ghost/size/dup) está **limpio**. El único fallo es de
contrato y **order-dependiente** (pasa aislado, falla en suite) → apunta a una primitiva no
robusta + contaminación de stylesheet entre tests, con **eco en runtime real**.

## Defectos

| ID | Severidad | Módulo/Pantalla | Evidencia | Causa sospechada | Estado | Commit corrige | Validación | Deuda restante |
|----|-----------|-----------------|-----------|------------------|--------|----------------|------------|----------------|
| D001 | Medio | Primitiva `NMPlayButton` → Respiración (`.ctl` reset/stop) y Timer | `pytest tests/` full → 1 failed en `tests/test_respiracion_visual_contract.py:49` (`_btn_reset.height()` = **56**, esperado 46). Aislado → pasa. | `NMPlayButton` (`shared/components/inputs.py:125`, `_SIZE_MAP md=46`, `setFixedSize(d,d)`) **no resiste** el QSS global `QPushButton{min-height:_NM_CONTROL_INNER_HEIGHT}` (+padding ≈56px) de `stylesheet_base` (`shared/theme_qt.py:1036-1042`). `NMButton` sí lo resiste (lock `test_button_keeps_contract_height_under_global_pushbutton_qss`). El alto fijado por `setFixedSize` lo pisa el `min-height` del stylesheet. | Closed | `8638035` | `pytest tests/` → 317 passed; runtime probe 22/22 en `c0c692e` | — |

### D001 — detalle y alcance runtime (no es solo un test)

- **Disparador en tests:** `tests/test_tcc_otro_placeholder.py:47` hace
  `qapp.setStyleSheet(stylesheet_base("dark_hybrid"))` **sin restaurar** (a diferencia de
  `test_component_visual_contract.py` que usa `old_qss` en `finally`). Eso deja el QSS global
  contaminando los tests posteriores → infla `NMPlayButton` y rompe el contrato de Respiración.
- **Eco en runtime REAL:** la app aplica el mismo QSS app-wide
  (`app/main_qt.py:357` y `:387` → `setStyleSheet(stylesheet_base(modo))`). Como el play
  secundario (`size="md"` = 46) es **menor** que el `min-height` global (~56), los controles
  `.ctl` de Respiración (reset/stop) y de Timer salen **46×56 (óvalo)** en vez del **46×46
  redondo** del mockup (`.ctl{width:46;height:46}`). El play principal (`lg`=58 ≥ 56) NO se
  deforma. El probe no lo detecta porque mide la ventana, no la geometría por-widget.
- **Severidad Medio:** deformación visible de controles focales; la app sigue usable.

### Fix recomendado (episodio E1-PLAYBUTTON-GUARD — NO ejecutado en este audit)

- **Perfil:** `nm_suite_safe_bugfix`. **Cluster:** primitiva `NMPlayButton`.
- **Opción A (raíz, preferida):** endurecer `NMPlayButton` para conservar su diámetro bajo
  QSS global app-wide — replicar la guarda de `NMButton` (p.ej. QSS widget-level
  `min-height/max-height: {d}px` o property que el `stylesheet_base` excluya). Cierra el
  defecto de runtime real, no solo el test.
- **Opción B (complementaria):** que `tests/test_tcc_otro_placeholder.py` restaure el
  stylesheet (`try/finally` con `old_qss`) para no contaminar el orden de tests.
- **Contrato nuevo:** test tipo `test_playbutton_keeps_diameter_under_global_pushbutton_qss`
  (análogo al de NMButton), md=46×46 y lg=58×58 bajo `stylesheet_base`.
- **Validación:** suite completa verde + `runtime_live_probe suite/respiracion,timer`.
- **Archivos permitidos:** `shared/components/inputs.py`,
  `tests/test_component_visual_contract.py` (+ `tests/test_tcc_otro_placeholder.py` si opción B).

## Handoff

- Frente OLA 0 (runtime lifecycle): **limpio** (probe 22/22).
- Deuda inmediata OLA 1 (primitiva): **D001** → abrir **E1-PLAYBUTTON-GUARD**.
- Próximos baselines: capturas `capture_v8.py` + revisión humana de densidad por pantalla
  (OLA 2) — no ejecutado aquí (este episodio es solo evidencia de gates).
