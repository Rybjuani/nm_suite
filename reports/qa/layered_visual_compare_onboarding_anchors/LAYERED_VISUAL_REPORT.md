# Layered visual comparison report

Generated: 2026-06-29T13:51:13

Handoff policy:
- Authority: LAYERED_VISUAL_COMPARE
- Use qa/_mockup_canonical plus a fresh complete qa/_captures_v8 run for operational handoff decisions. Zip inputs are archive/forensics only and must not close VISUAL_REPAIR_HANDOFF.md items.
- Canonical source: `qa\_mockup_canonical`
- Actual source: `qa\_captures_v8`
- REPORT_SCOPE: PARTIAL
- REPORT_FILTERS: {'app': None, 'view': None, 'theme': None, 'key': None, 'keys_file': 'reports\\qa\\visual_family_onboarding_keys.txt', 'keys_file_keys': ['suite:onboarding@light', 'suite:onboarding-error@light', 'suite:recuperar-acceso@light']}
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
- Total: 3
- Pass: 1
- Real divergences/review items: 2
- QA missed raw/layout: 2
- State or recipe suspects: 2
- By repair bucket: {'STATE_RECIPE_OR_PRODUCT_FIX': 2, 'NONE': 1}

| Severity | Status | Bucket | Key | Findings | Raw changed | ODiff % | BBox delta | Panel |
|---|---|---|---|---|---:|---:|---:|---|
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:recuperar-acceso@light | raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.10565 | 2.17 | 15 | reports\qa\layered_visual_compare_onboarding_anchors\panels\suite_recuperar-acceso_light.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:onboarding-error@light | raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.10141 | 2.14 | 15 | reports\qa\layered_visual_compare_onboarding_anchors\panels\suite_onboarding-error_light.png |
