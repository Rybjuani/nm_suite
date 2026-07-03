# Layered visual comparison report

Generated: 2026-06-30T12:51:02

Handoff policy:
- Authority: LAYERED_VISUAL_COMPARE
- Use qa/_mockup_canonical plus a fresh complete qa/_captures_v8 run for operational handoff decisions. Zip inputs are archive/forensics only and must not close VISUAL_REPAIR_HANDOFF.md items.
- Canonical source: `qa\_mockup_canonical`
- Actual source: `qa\_captures_v8`
- REPORT_SCOPE: PARTIAL
- REPORT_FILTERS: {'app': None, 'view': None, 'theme': None, 'key': None, 'keys_file': 'C:\\Users\\nosom\\AppData\\Local\\Temp\\tmp6AF9.tmp', 'keys_file_keys': ['\ufeffhub:detalle-plan-timer@dark', 'hub:detalle-plan-timer@light', 'hub:detalle-plan-rutina@dark', 'hub:detalle-plan-rutina@light', 'hub:detalle@dark', 'hub:detalle@light', 'hub:detalle-plan-activacion@dark']}
- REPORT_EVIDENCE_VALID: YES
- HANDOFF_CLOSURE_ALLOWED: NO
- HANDOFF_CLOSURE_REASON: partial_scope

Thresholds:
- raw SSIM >= 0.92
- raw mean_abs_diff <= 0.035
- raw changed_pixel_ratio <= 0.08
- odiff diff_percentage <= 8
- content bbox shift <= 18px

Summary:
- Total: 6
- Pass: 6
- Real divergences/review items: 0
- QA missed raw/layout: 0
- State or recipe suspects: 0
- By repair bucket: {'NONE': 6}

| Severity | Status | Bucket | Key | Findings | Raw changed | ODiff % | BBox delta | Panel |
|---|---|---|---|---|---:|---:|---:|---|
