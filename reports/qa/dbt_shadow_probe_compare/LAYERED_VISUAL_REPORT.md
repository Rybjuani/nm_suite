# Layered visual comparison report

Generated: 2026-07-02T00:54:14

Handoff policy:
- Authority: LAYERED_VISUAL_COMPARE
- Use qa/_mockup_canonical plus a fresh complete qa/_captures_v8 run for operational handoff decisions. Zip inputs are archive/forensics only and must not close VISUAL_REPAIR_HANDOFF.md items.
- Canonical source: `qa\_mockup_canonical`
- Actual source: `qa\_captures_v8`
- REPORT_SCOPE: PARTIAL
- REPORT_FILTERS: {'app': None, 'view': None, 'theme': None, 'key': None, 'keys_file': 'C:\\Users\\nosom\\AppData\\Local\\Temp\\dbt_shadow_probe_keys.txt', 'keys_file_keys': ['suite:dbt-practice-check-facts@dark']}
- REPORT_EVIDENCE_VALID: NO
- REPORT_EVIDENCE_REASON: panels_disabled
- HANDOFF_CLOSURE_ALLOWED: NO
- HANDOFF_CLOSURE_REASON: panels_disabled

Thresholds:
- raw SSIM >= 0.92
- raw mean_abs_diff <= 0.035
- raw changed_pixel_ratio <= 0.08
- odiff diff_percentage <= 8
- content bbox shift <= 18px

Summary:
- Total: 1
- Pass: 1
- Real divergences/review items: 0
- QA missed raw/layout: 0
- State or recipe suspects: 0
- By repair bucket: {'NONE': 1}

| Severity | Status | Bucket | Key | Findings | Raw changed | ODiff % | BBox delta | Panel |
|---|---|---|---|---|---:|---:|---:|---|
