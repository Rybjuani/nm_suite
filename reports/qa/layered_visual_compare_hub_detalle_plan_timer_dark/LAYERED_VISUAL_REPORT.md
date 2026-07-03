# Layered visual comparison report

Generated: 2026-06-30T04:12:14

Handoff policy:
- Authority: LAYERED_VISUAL_COMPARE
- Use qa/_mockup_canonical plus a fresh complete qa/_captures_v8 run for operational handoff decisions. Zip inputs are archive/forensics only and must not close VISUAL_REPAIR_HANDOFF.md items.
- Canonical source: `qa\_mockup_canonical`
- Actual source: `qa\_captures_v8`
- REPORT_SCOPE: PARTIAL
- REPORT_FILTERS: {'app': None, 'view': None, 'theme': None, 'key': None, 'keys_file': 'qa/_temp_keys3.txt', 'keys_file_keys': ['hub:detalle-plan-timer@dark', 'suite:dbt-practice-stop@dark', 'suite:dbt-practice-stop@light', 'suite:dbt-library@dark', 'suite:dbt-library@light', 'suite:dbt-now@dark', 'suite:dbt-now@light']}
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
- Total: 7
- Pass: 6
- Real divergences/review items: 1
- QA missed raw/layout: 1
- State or recipe suspects: 0
- By repair bucket: {'LAYOUT_FIX': 1, 'NONE': 6}

| Severity | Status | Bucket | Key | Findings | Raw changed | ODiff % | BBox delta | Panel |
|---|---|---|---|---|---:|---:|---:|---|
| high | FAIL | LAYOUT_FIX | hub:detalle-plan-timer@dark | raw_pixel_delta,layout_drift,qa_missed_raw_or_layout | 0.42743 | 5.87 | 140 | reports\qa\layered_visual_compare_hub_detalle_plan_timer_dark\panels\hub_detalle-plan-timer_dark.png |
