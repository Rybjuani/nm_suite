# Layered visual comparison report

Generated: 2026-06-29T18:44:59

Handoff policy:
- Authority: LAYERED_VISUAL_COMPARE
- Use qa/_mockup_canonical plus a fresh complete qa/_captures_v8 run for operational handoff decisions. Zip inputs are archive/forensics only and must not close VISUAL_REPAIR_HANDOFF.md items.
- Canonical source: `qa\_mockup_canonical`
- Actual source: `qa\_captures_v8`
- REPORT_SCOPE: PARTIAL
- REPORT_FILTERS: {'app': None, 'view': None, 'theme': None, 'key': None, 'keys_file': 'reports/qa/registro_family_keys.txt', 'keys_file_keys': ['suite:registro@light', 'suite:registro@dark', 'suite:registro-step1-emotion@light', 'suite:registro-step1-emotion@dark', 'suite:registro-step1-emotion-otro@light', 'suite:registro-step1-emotion-otro@dark', 'suite:registro-step2-distortions@light', 'suite:registro-step2-distortions@dark', 'suite:registro-step3-filled@light', 'suite:registro-step3-filled@dark', 'suite:registro-success@light', 'suite:registro-success@dark']}
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
- Total: 12
- Pass: 4
- Real divergences/review items: 8
- QA missed raw/layout: 8
- State or recipe suspects: 8
- By repair bucket: {'STATE_RECIPE_OR_PRODUCT_FIX': 8, 'NONE': 4}

| Severity | Status | Bucket | Key | Findings | Raw changed | ODiff % | BBox delta | Panel |
|---|---|---|---|---|---:|---:|---:|---|
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:registro-step1-emotion-otro@dark | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.10279 | 5.52 | 112 | reports\qa\layered_visual_compare_registro\panels\suite_registro-step1-emotion-otro_dark.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:registro-step1-emotion-otro@light | raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.10213 | 5.49 | 1 | reports\qa\layered_visual_compare_registro\panels\suite_registro-step1-emotion-otro_light.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:registro-step2-distortions@dark | layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.09795 | 2.57 | 112 | reports\qa\layered_visual_compare_registro\panels\suite_registro-step2-distortions_dark.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:registro-step1-emotion@dark | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.09227 | 5.4 | 112 | reports\qa\layered_visual_compare_registro\panels\suite_registro-step1-emotion_dark.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:registro-step1-emotion@light | raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.09157 | 5.36 | 1 | reports\qa\layered_visual_compare_registro\panels\suite_registro-step1-emotion_light.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:registro-step3-filled@dark | layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.06593 | 2.39 | 140 | reports\qa\layered_visual_compare_registro\panels\suite_registro-step3-filled_dark.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:registro@dark | layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.06031 | 1.43 | 140 | reports\qa\layered_visual_compare_registro\panels\suite_registro_dark.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:registro-success@dark | layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.04122 | 0.98 | 281 | reports\qa\layered_visual_compare_registro\panels\suite_registro-success_dark.png |
