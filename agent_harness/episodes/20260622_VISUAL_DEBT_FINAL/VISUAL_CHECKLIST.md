# VISUAL_CHECKLIST — Deuda visual final

| Área | Defecto | Fix aplicado | Estado |
|------|---------|-------------|--------|
| Avisos | Track filtro sin altura fija → se deforma | `setFixedHeight(40)` en `_filter_segment` | ✓ |
| Avisos | Search no alineado al track | `setFixedHeight(40)` + `AlignVCenter` | ✓ |
| Timer | Ring 230px domina viewport | `NMFocusArc(size=180)` (V2-P1-040 cerrado) | ✓ |
| Timer | Empty card ocupa todo el viewport | `stretch=0` + `addStretch(1)` posterior | ✓ |
| Rutina | Botón "✓" se ve blob/cuadrado | Eliminar `width=36`, usar `setFixedWidth(40)` | ✓ |
| Rutina | Espacio vacío inferior en empty state | `addStretch(1)` después del grid en `build_ui()` | ✓ |
| Hub Pacientes | Scrollbar visible con 5 filas | Overhead 108, política dinámica ≤5→Off | ✓ |
| Hub Activación | Tabs densidad/jerarquía floja | padding `6px 12px`, font-size 12px | ✓ |
| Hub Activación | "Completar con IA" desconectado | Fusionado en `action_row` junto a save button | ✓ |
| Hub Activación | Márgenes sin tokens | `V3_SP["sm"]`/`["md"]` en form + list cards | ✓ |
| Sistémico | V2-P1-040 diferido sin propuesta | Propuesta 180px implementada y documentada | ✓ |
