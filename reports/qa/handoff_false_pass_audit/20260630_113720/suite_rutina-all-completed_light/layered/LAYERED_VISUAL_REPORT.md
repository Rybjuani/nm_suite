# Layered visual comparison report

Generated: 2026-06-30T11:46:17

Handoff policy:
- Authority: LAYERED_VISUAL_COMPARE
- Use qa/_mockup_canonical plus a fresh complete qa/_captures_v8 run for operational handoff decisions. Zip inputs are archive/forensics only and must not close VISUAL_REPAIR_HANDOFF.md items.
- Canonical source: `qa\_mockup_canonical`
- Actual source: `qa\_captures_v8`
- REPORT_SCOPE: PARTIAL
- REPORT_FILTERS: {'app': None, 'view': None, 'theme': None, 'key': 'suite:rutina-all-completed@light', 'keys_file': None, 'keys_file_keys': []}
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
- State or recipe suspects: 0
- By repair bucket: {'VISUAL_STYLE_REVIEW': 1}

| Severity | Status | Bucket | Key | Findings | Raw changed | ODiff % | BBox delta | Panel |
|---|---|---|---|---|---:|---:|---:|---|
| medium | FAIL | VISUAL_STYLE_REVIEW | suite:rutina-all-completed@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.11697 | 2.84 | 1 | C:\Users\nosom\Desktop\nm_suite\reports\qa\handoff_false_pass_audit\20260630_113720\suite_rutina-all-completed_light\layered\panels\suite_rutina-all-completed_light.png |
