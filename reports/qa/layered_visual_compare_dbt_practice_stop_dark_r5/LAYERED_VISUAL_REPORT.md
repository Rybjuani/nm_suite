# Layered visual comparison report

Generated: 2026-06-29T23:38:36

Handoff policy:
- Authority: LAYERED_VISUAL_COMPARE
- Use qa/_mockup_canonical plus a fresh complete qa/_captures_v8 run for operational handoff decisions. Zip inputs are archive/forensics only and must not close VISUAL_REPAIR_HANDOFF.md items.
- Canonical source: `qa\_mockup_canonical`
- Actual source: `qa\_captures_v8`
- REPORT_SCOPE: PARTIAL
- REPORT_FILTERS: {'app': None, 'view': None, 'theme': None, 'key': 'suite:dbt-practice-stop@dark', 'keys_file': None, 'keys_file_keys': []}
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
- Total: 1
- Pass: 0
- Real divergences/review items: 1
- QA missed raw/layout: 1
- State or recipe suspects: 1
- By repair bucket: {'STATE_RECIPE_OR_PRODUCT_FIX': 1}

| Severity | Status | Bucket | Key | Findings | Raw changed | ODiff % | BBox delta | Panel |
|---|---|---|---|---|---:|---:|---:|---|
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:dbt-practice-stop@dark | raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.10218 | 1.24 | 19 | reports\qa\layered_visual_compare_dbt_practice_stop_dark_r5\panels\suite_dbt-practice-stop_dark.png |
