# Layered visual comparison report

Generated: 2026-07-01T22:17:36

Handoff policy:
- Authority: LAYERED_VISUAL_COMPARE
- Use qa/_mockup_canonical plus a fresh complete qa/_captures_v8 run for operational handoff decisions. Zip inputs are archive/forensics only and must not close VISUAL_REPAIR_HANDOFF.md items.
- Canonical source: `qa\_mockup_canonical`
- Actual source: `qa\_captures_v8`
- REPORT_SCOPE: PARTIAL
- REPORT_FILTERS: {'app': None, 'view': None, 'theme': None, 'key': None, 'keys_file': 'C:\\Users\\nosom\\AppData\\Local\\Temp\\nm_dbt_v2_keys.txt', 'keys_file_keys': ['suite:dbt-now@light', 'suite:dbt-now@dark', 'suite:dbt-library@light', 'suite:dbt-library@dark', 'suite:dbt-practice-observe-describe@light', 'suite:dbt-practice-observe-describe@dark', 'suite:dbt-practice-wise-mind@light', 'suite:dbt-practice-wise-mind@dark', 'suite:dbt-practice-participate@light', 'suite:dbt-practice-participate@dark', 'suite:dbt-practice-non-judgmental@light', 'suite:dbt-practice-non-judgmental@dark', 'suite:dbt-practice-stop@light', 'suite:dbt-practice-stop@dark', 'suite:dbt-practice-tipp@light', 'suite:dbt-practice-tipp@dark', 'suite:dbt-practice-self-soothe@light', 'suite:dbt-practice-self-soothe@dark', 'suite:dbt-practice-radical-acceptance@light', 'suite:dbt-practice-radical-acceptance@dark', 'suite:dbt-practice-check-facts@light', 'suite:dbt-practice-check-facts@dark', 'suite:dbt-practice-opposite-action@light', 'suite:dbt-practice-opposite-action@dark', 'suite:dbt-practice-problem-solving@light', 'suite:dbt-practice-problem-solving@dark', 'suite:dbt-practice-please@light', 'suite:dbt-practice-please@dark', 'suite:dbt-practice-dear-man@light', 'suite:dbt-practice-dear-man@dark', 'suite:dbt-practice-give@light', 'suite:dbt-practice-give@dark', 'suite:dbt-practice-fast@light', 'suite:dbt-practice-fast@dark', 'suite:dbt-practice-validation-limits@light', 'suite:dbt-practice-validation-limits@dark']}
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
- Total: 36
- Pass: 18
- Real divergences/review items: 18
- QA missed raw/layout: 18
- State or recipe suspects: 1
- By repair bucket: {'VISUAL_STYLE_REVIEW': 17, 'NONE': 18, 'STATE_RECIPE_OR_PRODUCT_FIX': 1}

| Severity | Status | Bucket | Key | Findings | Raw changed | ODiff % | BBox delta | Panel |
|---|---|---|---|---|---:|---:|---:|---|
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-library@dark | raw_pixel_delta,qa_missed_raw_or_layout | 0.1514 | 4.38 | 16 | reports\qa\layered_visual_compare_dbt_v2\panels\suite_dbt-library_dark.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-library@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.14311 | 4.04 | 14 | reports\qa\layered_visual_compare_dbt_v2\panels\suite_dbt-library_light.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-practice-opposite-action@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.11394 | 1.63 | 1 | reports\qa\layered_visual_compare_dbt_v2\panels\suite_dbt-practice-opposite-action_light.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-practice-validation-limits@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.11335 | 1.6 | 1 | reports\qa\layered_visual_compare_dbt_v2\panels\suite_dbt-practice-validation-limits_light.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-practice-dear-man@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.11311 | 1.57 | 1 | reports\qa\layered_visual_compare_dbt_v2\panels\suite_dbt-practice-dear-man_light.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-practice-tipp@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.11307 | 1.59 | 1 | reports\qa\layered_visual_compare_dbt_v2\panels\suite_dbt-practice-tipp_light.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-practice-please@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.11299 | 1.6 | 1 | reports\qa\layered_visual_compare_dbt_v2\panels\suite_dbt-practice-please_light.png |
| medium | FAIL | STATE_RECIPE_OR_PRODUCT_FIX | suite:dbt-practice-stop@light | raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout | 0.11188 | 1.5 | 1 | reports\qa\layered_visual_compare_dbt_v2\panels\suite_dbt-practice-stop_light.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-practice-radical-acceptance@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.11166 | 1.52 | 1 | reports\qa\layered_visual_compare_dbt_v2\panels\suite_dbt-practice-radical-acceptance_light.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-practice-self-soothe@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.11122 | 1.47 | 1 | reports\qa\layered_visual_compare_dbt_v2\panels\suite_dbt-practice-self-soothe_light.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-practice-fast@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.11105 | 1.48 | 1 | reports\qa\layered_visual_compare_dbt_v2\panels\suite_dbt-practice-fast_light.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-practice-observe-describe@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.11076 | 1.51 | 1 | reports\qa\layered_visual_compare_dbt_v2\panels\suite_dbt-practice-observe-describe_light.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-practice-non-judgmental@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.11069 | 1.46 | 1 | reports\qa\layered_visual_compare_dbt_v2\panels\suite_dbt-practice-non-judgmental_light.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-practice-participate@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.10982 | 1.43 | 1 | reports\qa\layered_visual_compare_dbt_v2\panels\suite_dbt-practice-participate_light.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-practice-give@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.10963 | 1.42 | 1 | reports\qa\layered_visual_compare_dbt_v2\panels\suite_dbt-practice-give_light.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-practice-problem-solving@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.10882 | 0.96 | 1 | reports\qa\layered_visual_compare_dbt_v2\panels\suite_dbt-practice-problem-solving_light.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-practice-wise-mind@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.10717 | 0.88 | 1 | reports\qa\layered_visual_compare_dbt_v2\panels\suite_dbt-practice-wise-mind_light.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-practice-check-facts@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.10663 | 0.86 | 1 | reports\qa\layered_visual_compare_dbt_v2\panels\suite_dbt-practice-check-facts_light.png |
