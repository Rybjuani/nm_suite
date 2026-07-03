# Layered visual comparison report

Generated: 2026-07-02T01:05:38

Handoff policy:
- Authority: LAYERED_VISUAL_COMPARE
- Use qa/_mockup_canonical plus a fresh complete qa/_captures_v8 run for operational handoff decisions. Zip inputs are archive/forensics only and must not close VISUAL_REPAIR_HANDOFF.md items.
- Canonical source: `qa\_mockup_canonical`
- Actual source: `qa\_captures_v8`
- REPORT_SCOPE: PARTIAL
- REPORT_FILTERS: {'app': None, 'view': None, 'theme': None, 'key': None, 'keys_file': 'reports\\qa\\dbt_keys_full_after_shadow.txt', 'keys_file_keys': ['suite:dbt-library@dark', 'suite:dbt-library@light', 'suite:dbt-now@dark', 'suite:dbt-now@light', 'suite:dbt-practice-check-facts@dark', 'suite:dbt-practice-check-facts@light', 'suite:dbt-practice-dear-man@dark', 'suite:dbt-practice-dear-man@light', 'suite:dbt-practice-fast@dark', 'suite:dbt-practice-fast@light', 'suite:dbt-practice-give@dark', 'suite:dbt-practice-give@light', 'suite:dbt-practice-non-judgmental@dark', 'suite:dbt-practice-non-judgmental@light', 'suite:dbt-practice-observe-describe@dark', 'suite:dbt-practice-observe-describe@light', 'suite:dbt-practice-opposite-action@dark', 'suite:dbt-practice-opposite-action@light', 'suite:dbt-practice-participate@dark', 'suite:dbt-practice-participate@light', 'suite:dbt-practice-please@dark', 'suite:dbt-practice-please@light', 'suite:dbt-practice-problem-solving@dark', 'suite:dbt-practice-problem-solving@light', 'suite:dbt-practice-radical-acceptance@dark', 'suite:dbt-practice-radical-acceptance@light', 'suite:dbt-practice-self-soothe@dark', 'suite:dbt-practice-self-soothe@light', 'suite:dbt-practice-stop@dark', 'suite:dbt-practice-stop@light', 'suite:dbt-practice-tipp@dark', 'suite:dbt-practice-tipp@light', 'suite:dbt-practice-validation-limits@dark', 'suite:dbt-practice-validation-limits@light', 'suite:dbt-practice-wise-mind@dark', 'suite:dbt-practice-wise-mind@light']}
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
- Pass: 34
- Real divergences/review items: 2
- QA missed raw/layout: 2
- State or recipe suspects: 0
- By repair bucket: {'VISUAL_STYLE_REVIEW': 2, 'NONE': 34}

| Severity | Status | Bucket | Key | Findings | Raw changed | ODiff % | BBox delta | Panel |
|---|---|---|---|---|---:|---:|---:|---|
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-library@dark | raw_pixel_delta,qa_missed_raw_or_layout | 0.14219 | 4.03 | 16 | reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-library_dark.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:dbt-library@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.13243 | 3.84 | 14 | reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-library_light.png |
