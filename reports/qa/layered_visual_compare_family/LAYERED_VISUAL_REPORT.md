# Layered visual comparison report

Generated: 2026-06-29T11:41:09

Handoff policy:
- Authority: LAYERED_VISUAL_COMPARE
- Use qa/_mockup_canonical plus a fresh complete qa/_captures_v8 run for operational handoff decisions. Zip inputs are archive/forensics only and must not close VISUAL_REPAIR_HANDOFF.md items.
- Canonical source: `qa\_mockup_canonical`
- Actual source: `qa\_captures_v8`
- REPORT_SCOPE: PARTIAL
- REPORT_FILTERS: {'app': None, 'view': None, 'theme': None, 'key': None, 'keys_file': 'reports/qa/registro_family_keys.txt', 'keys_file_keys': ['suite:registro@light', 'suite:registro-step1-emotion@light', 'suite:registro-step3-filled@light', 'suite:registro-step2-distortions@light']}
- REPORT_EVIDENCE_VALID: YES
- HANDOFF_CLOSURE_ALLOWED: NO
- HANDOFF_CLOSURE_REASON: partial_scope; real_divergence_present

Thresholds:
- raw SSIM >= 0.92
- raw mean_abs_diff <= 0.035
- raw changed_pixel_ratio <= 0.08
- odiff diff_percentage <= 8
- content bbox shift <= 18px

Summary:
- Total: 4
- Pass: 0
- Real divergences/review items: 4
- QA missed raw/layout: 4
- State or recipe suspects: 4
- By repair bucket: {'STATE_RECIPE_OR_PRODUCT_FIX': 4}

| Severity | Status | Bucket | Key | Findings | Raw changed | ODiff % | BBox delta | Panel |
|---|---|---|---|---|---:|---:|---:|---|
| high | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:registro-step3-filled@light | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.25729 | 3.27 | 1 | reports\qa\layered_visual_compare_family\panels\suite_registro-step3-filled_light.png |
| high | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:registro@light | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.25073 | 2.15 | 1 | reports\qa\layered_visual_compare_family\panels\suite_registro_light.png |
| high | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:registro-step2-distortions@light | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.24315 | 3.5 | 15 | reports\qa\layered_visual_compare_family\panels\suite_registro-step2-distortions_light.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:registro-step1-emotion@light | raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.11769 | 5.15 | 1 | reports\qa\layered_visual_compare_family\panels\suite_registro-step1-emotion_light.png |
