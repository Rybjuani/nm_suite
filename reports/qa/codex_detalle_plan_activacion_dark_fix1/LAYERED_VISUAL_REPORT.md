# Layered visual comparison report

Generated: 2026-06-30T07:03:50

Handoff policy:
- Authority: LAYERED_VISUAL_COMPARE
- Use qa/_mockup_canonical plus a fresh complete qa/_captures_v8 run for operational handoff decisions. Zip inputs are archive/forensics only and must not close VISUAL_REPAIR_HANDOFF.md items.
- Canonical source: `qa\_mockup_canonical`
- Actual source: `qa\_captures_v8`
- REPORT_SCOPE: PARTIAL
- REPORT_FILTERS: {'app': None, 'view': None, 'theme': None, 'key': 'hub:detalle-plan-activacion@dark', 'keys_file': None, 'keys_file_keys': []}
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
| medium | FAIL | VISUAL_STYLE_REVIEW | hub:detalle-plan-activacion@dark | raw_pixel_delta,qa_missed_raw_or_layout | 0.11264 | 4.24 | 16 | reports\qa\codex_detalle_plan_activacion_dark_fix1\panels\hub_detalle-plan-activacion_dark.png |
