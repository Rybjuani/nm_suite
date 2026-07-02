from __future__ import annotations

from pathlib import Path

from tools.qa import audit_handoff_false_pass as audit


def test_parse_closed_checkbox_keys_from_diff():
    diff = """
@@ -10 +10 @@
- - [ ] `suite:home@light` pendiente
+ - [x] `suite:home@light` cierre
"""

    assert audit.parse_closed_checkbox_keys(diff) == ["suite:home@light"]


def test_restricted_paths_block_visual_closure_objective():
    files = [
        "VISUAL_REPAIR_HANDOFF.md",
        "qa/layered_visual_compare.py",
        "reports/qa/layered_visual_compare_item/LAYERED_VISUAL_REPORT.json",
    ]

    assert audit.restricted_touched(files) == [
        "qa/layered_visual_compare.py",
        "reports/qa/layered_visual_compare_item/LAYERED_VISUAL_REPORT.json",
    ]


def test_layered_report_rejects_near_perfect_match(tmp_path):
    report = tmp_path / "LAYERED_VISUAL_REPORT.json"
    report.write_text(
        """
{
  "authority": "LAYERED_VISUAL_COMPARE",
  "report_evidence_valid": true,
  "results": [
    {
      "key": "suite:home@light",
      "status": "NEAR_PERFECT_MATCH",
      "near_perfect_match": true
    }
  ]
}
""",
        encoding="utf-8",
    )

    assert audit.layered_report_valid_for_key([report], "suite:home@light") is False


def test_layered_report_accepts_clean_exact_pass(tmp_path):
    report = tmp_path / "LAYERED_VISUAL_REPORT.json"
    report.write_text(
        """
{
  "authority": "LAYERED_VISUAL_COMPARE",
  "report_evidence_valid": true,
  "results": [
    {
      "key": "suite:home@light",
      "status": "PASS",
      "suspicious_perfect_match": false,
      "near_perfect_match": false
    }
  ]
}
""",
        encoding="utf-8",
    )

    assert audit.layered_report_valid_for_key([report], "suite:home@light") is True


def test_hardening_objective_cannot_close_visual_checkbox(monkeypatch):
    monkeypatch.setattr(audit, "handoff_diff", lambda base, handoff: """
@@ -1 +1 @@
- - [ ] `suite:home@light` pendiente
+ - [x] `suite:home@light` cierre
""")
    monkeypatch.setattr(audit, "changed_files", lambda base: ["qa/anti_fraud_scan.py"])
    monkeypatch.setattr(audit, "layered_report_valid_for_key", lambda reports, key: True)
    monkeypatch.setattr(audit, "vas_gate_valid", lambda sidecar, key: True)

    result = audit.audit(
        base="main",
        handoff=Path("VISUAL_REPAIR_HANDOFF.md"),
        layered_reports=[Path("report.json")],
        sidecar=Path("introspection.json"),
        objective="hardening-qa",
        skip_anti_fraud=True,
    )

    assert result.ok is False
    assert "hardening_objective_must_not_close_visual_checkboxes" in result.reasons


def test_hardening_objective_allows_restricted_paths_without_closure(monkeypatch):
    monkeypatch.setattr(audit, "handoff_diff", lambda base, handoff: "")
    monkeypatch.setattr(audit, "changed_files", lambda base: ["qa/anti_fraud_scan.py"])

    result = audit.audit(
        base="main",
        handoff=Path("VISUAL_REPAIR_HANDOFF.md"),
        layered_reports=[],
        sidecar=Path("introspection.json"),
        objective="hardening-qa",
    )

    assert result.ok is True
