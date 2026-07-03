# Layered visual comparison report

Generated: 2026-06-30T12:48:07

Handoff policy:
- Authority: LAYERED_VISUAL_COMPARE
- Use qa/_mockup_canonical plus a fresh complete qa/_captures_v8 run for operational handoff decisions. Zip inputs are archive/forensics only and must not close VISUAL_REPAIR_HANDOFF.md items.
- Canonical source: `qa\_mockup_canonical`
- Actual source: `qa\_captures_v8`
- REPORT_SCOPE: PARTIAL
- REPORT_FILTERS: {'app': None, 'view': None, 'theme': None, 'key': None, 'keys_file': 'C:\\Users\\nosom\\AppData\\Local\\Temp\\tmpBE29.tmp', 'keys_file_keys': ['\ufeffhub:detalle-plan-timer@dark', 'hub:detalle-plan-timer@light', 'hub:detalle-plan-rutina@dark', 'hub:detalle-plan-rutina@light', 'hub:detalle@dark', 'hub:detalle@light', 'hub:detalle-plan-activacion@dark']}
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
- Total: 6
- Pass: 1
- Real divergences/review items: 5
- QA missed raw/layout: 5
- State or recipe suspects: 0
- By repair bucket: {'NONE': 1, 'VISUAL_STYLE_REVIEW': 5}

| Severity | Status | Bucket | Key | Findings | Raw changed | ODiff % | BBox delta | Panel |
|---|---|---|---|---|---:|---:|---:|---|
| medium | FAIL | VISUAL_STYLE_REVIEW | hub:detalle-plan-timer@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.11789 | 3.76 | 15 | reports\qa\codex_audit_hub_detail_plan_anchors_after_activacion_dark\panels\hub_detalle-plan-timer_light.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | hub:detalle-plan-rutina@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.11073 | 3.67 | 15 | reports\qa\codex_audit_hub_detail_plan_anchors_after_activacion_dark\panels\hub_detalle-plan-rutina_light.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | hub:detalle@light | raw_pixel_delta,qa_missed_raw_or_layout | 0.10902 | 3.45 | 15 | reports\qa\codex_audit_hub_detail_plan_anchors_after_activacion_dark\panels\hub_detalle_light.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | hub:detalle@dark | raw_pixel_delta,qa_missed_raw_or_layout | 0.10531 | 3.65 | 16 | reports\qa\codex_audit_hub_detail_plan_anchors_after_activacion_dark\panels\hub_detalle_dark.png |
| medium | FAIL | VISUAL_STYLE_REVIEW | hub:detalle-plan-rutina@dark | raw_pixel_delta,qa_missed_raw_or_layout | 0.10503 | 3.86 | 16 | reports\qa\codex_audit_hub_detail_plan_anchors_after_activacion_dark\panels\hub_detalle-plan-rutina_dark.png |
