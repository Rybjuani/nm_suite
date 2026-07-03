# Layered visual comparison report

Generated: 2026-07-02T00:25:29

Handoff policy:
- Authority: LAYERED_VISUAL_COMPARE
- Use qa/_mockup_canonical plus a fresh complete qa/_captures_v8 run for operational handoff decisions. Zip inputs are archive/forensics only and must not close VISUAL_REPAIR_HANDOFF.md items.
- Canonical source: `qa\_mockup_canonical`
- Actual source: `qa\_captures_v8`
- REPORT_SCOPE: PARTIAL
- REPORT_FILTERS: {'app': None, 'view': None, 'theme': None, 'key': None, 'keys_file': 'C:\\Users\\nosom\\AppData\\Local\\Temp\\tmp84DE.tmp', 'keys_file_keys': ['suite:dbt-library@light', 'suite:dbt-library@dark', 'suite:dbt-practice-wise-mind@light', 'suite:dbt-practice-wise-mind@dark', 'suite:dbt-practice-stop@light', 'suite:dbt-practice-stop@dark', 'suite:dbt-practice-check-facts@light', 'suite:dbt-practice-check-facts@dark', 'suite:dbt-practice-dear-man@light', 'suite:dbt-practice-dear-man@dark', 'suite:dbt-practice-fast@light', 'suite:dbt-practice-fast@dark']}
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
- Pass: 5
- Real divergences/review items: 7
- QA missed raw/layout: 7
- State or recipe suspects: 1
- By repair bucket: {'VISUAL_STYLE_REVIEW': 6, 'NONE': 5, 'STATE_RECIPE_OR_PRODUCT_FIX': 1}

| Severity | Status | Bucket | Key | Findings | Raw changed | ODiff % | BBox delta | Panel |
|---|---|---|---|---|---:|---:|---:|---|
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-library@dark | raw_pixel_delta,qa_missed_raw_or_layout | 0.1514 | 4.38 | 16 | reports\qa\dbt_representative_compare\panels\suite_dbt-library_dark.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-library@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.14311 | 4.04 | 14 | reports\qa\dbt_representative_compare\panels\suite_dbt-library_light.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-practice-dear-man@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.11311 | 1.57 | 1 | reports\qa\dbt_representative_compare\panels\suite_dbt-practice-dear-man_light.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:dbt-practice-stop@light | raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.11188 | 1.5 | 1 | reports\qa\dbt_representative_compare\panels\suite_dbt-practice-stop_light.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-practice-fast@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.11105 | 1.48 | 1 | reports\qa\dbt_representative_compare\panels\suite_dbt-practice-fast_light.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-practice-wise-mind@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.10717 | 0.88 | 1 | reports\qa\dbt_representative_compare\panels\suite_dbt-practice-wise-mind_light.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-practice-check-facts@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.10663 | 0.86 | 1 | reports\qa\dbt_representative_compare\panels\suite_dbt-practice-check-facts_light.png |
