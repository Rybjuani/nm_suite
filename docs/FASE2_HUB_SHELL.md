# Fase 2 - Hub Shell Y Navegación

## Cambios Aplicados

### Chrome / Ventana
- `NMWindowChrome.setFixedHeight`: 38 → 32 px
- `_ChromeWinBtn.setFixedSize`: 46×38 → 46×32 px
- Recupera 6 px de viewport vertical en toda vista del Hub.

### Sidebar expandida
- Layout margins top/bottom: 10 → 6 px
- Logo icon height: 56 → 44 px; margins (12,10,12,10) → (12,6,12,6)
- Section title (Suite mode) bottom margin: 10 → 6 px
- Footer label top margin: 10 → 6 px
- Nav button height: 38 → 34 px; padding 8px → 6px

### Sidebar colapsada
- Logo icon height: 48 → 40 px; margins (0,10,0,10) → (0,6,0,6); icon 30→28 px
- Tooltips ya activos desde antes (`set_collapsed` → `btn.setToolTip(label)`)

### Sidebar footer (main_qt.py)
- `footer_layout.setContentsMargins`: (12,8,12,12) → (10,6,10,8)

### Área derecha (main_qt.py)
- `rl.setContentsMargins` bottom: 12 → 8 px (recupera 4 px viewport)

### Patient header (pacientes_qt.py)
- `top_wrap` margins: (16,6,16,2) → (12,4,12,2) — recupera 2 px viewport
- `tabs_wrap` margins: (16,0,16,8) → (12,0,12,4) — recupera 4 px viewport

### Hub density QSS (theme_qt.py)
- `#HubMain QTabBar::tab` ahora incluye `margin: 2px 2px` — reduce tab bar height ~4 px

## Viewport recovery total (DetallePacienteView, 960×600)
| Componente | Antes | Después | Ganancia |
|---|---|---|---|
| Chrome | 38 px | 32 px | 6 px |
| Right area bottom | 12 px | 8 px | 4 px |
| Patient header top margin | 6 px | 4 px | 2 px |
| Tabs wrap bottom | 8 px | 4 px | 4 px |
| QTabBar margin (tab bar) | 3+3 px | 2+2 px | ~4 px |
| **Total** | | | **~20 px** |

## Restricciones Respetadas
- Densidad Hub ≤ Suite en todas las dimensiones (test_token_parity).
- Ninguna regla de densidad toca `QApplication`.
- `#HubMain` presente en QSS (test parity).
- 85/85 tests OK. Ruff 0 errores. py_compile OK.

## Cierre Pendiente
- Sin commit aún (esperando que el owner limpie la rama).
- Capturas evidencia: pendiente — ejecutar `python qa/capture_v8.py --all` para dashboard, pacientes, detalle y sidebar colapsada light+dark.
- Luego commit Fase 2 conjunto con Fase 0+1.
