# Visual Gate Calibration (NON-CLOSURE)

Generated: 2026-06-29T00:33:22

**This is technical evidence only.** It does not close, reclassify or skip any checklist item and does not change any threshold.

Live gate (unchanged): `ssim>=0.92`, `mad<=0.035`, `changed_ratio<=0.08`.

| key | res | class | global ssim | windowed ssim | gate | mad | changed | canon std | ceiling(align) | ceiling(color) |
|---|---|---|---|---|---|---|---|---|---|---|
| suite:recuperar-acceso@light | 520x600 | text_dense | 0.52025 | 0.76797 | windowed>=0.65 | 0.0322 | 0.11752 | 22.461 | 0.54634 | 0.56579 |
| suite:onboarding-error@light | 520x600 | text_dense | 0.55067 | 0.77809 | windowed>=0.65 | 0.03162 | 0.1163 | 23.149 | 0.55329 | 0.59342 |
| suite:onboarding@light | 520x600 | text_dense | 0.414 | 0.69457 | windowed>=0.65 | 0.03809 | 0.17256 | 22.57 | 0.44016 | 0.46869 |
| suite:dbt-practice-stop@light | 960x600 | sparse | 0.95221 | 0.89226 | global>=0.92 | 0.02013 | 0.07785 | 56.852 | 0.95221 | 0.9595 |

Columns: `ceiling(align)` = best SSIM under a +/-3px global shift; `ceiling(color)` = SSIM if every flat/colour pixel were perfectly matched, leaving only strong text edges. The decisive signal is the ceiling: if a surface stays far below the `min_ssim` gate even after alignment AND colour are perfected, the global-SSIM floor is set by text-edge rasterisation (Qt vs Chromium), not by layout or colour that product code could fix. `ink_fraction` conflates text with large dark regions (e.g. a dimmed backdrop) and is informational only.
