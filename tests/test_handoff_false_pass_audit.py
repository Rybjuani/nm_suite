from __future__ import annotations

import hashlib
import json
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


def test_workspace_paths_normalize_relative_inputs():
    assert audit._workspace_path(Path("VISUAL_REPAIR_HANDOFF.md")) == audit.ROOT / "VISUAL_REPAIR_HANDOFF.md"


def test_select_objective_uses_hardening_only_without_visual_closure(monkeypatch):
    monkeypatch.setattr(audit, "handoff_diff", lambda base, handoff: "")
    monkeypatch.setattr(audit, "changed_files", lambda base: ["qa/anti_fraud_scan.py"])

    assert audit.select_objective_for_diff(base="origin/main", handoff=Path("VISUAL_REPAIR_HANDOFF.md")) == "hardening-qa"


def test_select_objective_does_not_mark_visual_closure_as_hardening(monkeypatch):
    monkeypatch.setattr(audit, "handoff_diff", lambda base, handoff: """
@@ -1 +1 @@
- - [ ] `suite:home@light` pendiente
+ - [x] `suite:home@light` cierre
""")
    monkeypatch.setattr(audit, "changed_files", lambda base: ["qa/anti_fraud_scan.py"])

    assert audit.select_objective_for_diff(base="origin/main", handoff=Path("VISUAL_REPAIR_HANDOFF.md")) == ""


def test_workflow_selects_objective_without_hardcoded_hardening():
    workflow = (audit.ROOT / ".github" / "workflows" / "visual-handoff-audit.yml").read_text(encoding="utf-8")

    assert "git merge-base origin/main HEAD" in workflow
    assert "select_handoff_audit_objective.py" in workflow
    assert "--objective hardening-qa" not in workflow
    assert "61eec259" not in workflow


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


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _make_report(tmp_path: Path, key: str, *, perfect: bool = False) -> Path:
    report = tmp_path / "LAYERED_VISUAL_REPORT.json"
    report.write_text(
        json.dumps(
            {
                "authority": "LAYERED_VISUAL_COMPARE",
                "report_evidence_valid": True,
                "report_scope": "PARTIAL",
                "handoff_closure_allowed": False,
                "summary": {"total": 1, "pass": 1, "real_divergence": 0},
                "results": [
                    {
                        "key": key,
                        "status": "PASS",
                        "suspicious_perfect_match": False,
                        "near_perfect_match": False,
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    if perfect:
        payload = json.loads(report.read_text(encoding="utf-8"))
        payload["results"][0]["suspicious_perfect_match"] = True
        report.write_text(json.dumps(payload), encoding="utf-8")
    return report


def _make_sidecar(tmp_path: Path, key: str, provenance: dict | None = None) -> Path:
    sidecar = tmp_path / "introspection.json"
    png = tmp_path / f"{key.replace(':', '-').replace('@', '-')}.png"
    png.write_bytes(b"png-bytes-for-test")
    script = Path(__file__).resolve().parents[1] / "qa" / "capture_v8.py"
    script_sha = _sha256_file(script)
    prov = provenance or {
        "schema": "capture_v8.provenance.v1",
        "key": key,
        "capture_file": png.name,
        "capture_path": str(png),
        "png_sha256": _sha256_file(png),
        "captured_at": "2026-07-02T00:00:00+00:00",
        "command_args": ["qa/capture_v8.py", "--app", "suite", "--view", "test"],
        "cwd": str(Path(__file__).resolve().parents[1]),
        "git_head": "head-sha",
        "git_branch": "main",
        "git_tracked_dirty": False,
        "capture_script": str(script),
        "capture_script_sha256": script_sha,
        "capture_manifest": str(tmp_path / "CAPTURE_MANIFEST.json"),
        "introspection_sidecar": str(sidecar),
        "introspection_entry_id": "a" * 64,
    }
    sidecar.write_text(
        json.dumps(
            [
                {
                    "surface_key": key,
                    "fail_count": 0,
                    "divergences": [],
                    "provenance": prov,
                }
            ],
            indent=2,
        ),
        encoding="utf-8",
    )
    manifest = {
        "harness": "capture_v8.py",
        "results": [
            {
                "key": key,
                "file": png.name,
                "sha256": prov["png_sha256"],
                "provenance": prov,
            }
        ],
    }
    (tmp_path / "CAPTURE_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return sidecar


def _make_bundle(
    tmp_path: Path,
    *,
    key: str,
    commit_hashes: list[str],
    report: Path,
    sidecar: Path,
    base_commit: str = "base-sha",
    head_commit: str = "head-sha",
    provenance: dict | None = None,
) -> Path:
    report_payload = json.loads(report.read_text(encoding="utf-8"))
    sidecar_payload = json.loads(sidecar.read_text(encoding="utf-8"))
    sidecar_entry = sidecar_payload[0]
    provenance = provenance or sidecar_entry["provenance"]
    bundle = tmp_path / "visual_closure_bundle.json"
    payload = {
        "schema": "visual_closure_bundle.v1",
        "generated_at": "2026-07-02T00:00:00+00:00",
        "audited_range": {
            "base_ref": "main",
            "base_commit": base_commit,
            "head_ref": "HEAD",
            "head_commit": head_commit,
        },
        "closures": [
            {
                "key": key,
                "closure_note_hashes": commit_hashes,
                "report": {
                    "path": str(report),
                    "sha256": _sha256_file(report),
                    "summary": {
                        "authority": report_payload["authority"],
                        "report_evidence_valid": report_payload["report_evidence_valid"],
                        "report_scope": report_payload["report_scope"],
                        "handoff_closure_allowed": report_payload["handoff_closure_allowed"],
                        "summary": report_payload["summary"],
                        "result": report_payload["results"][0],
                    },
                },
                "sidecar": {
                    "path": str(sidecar),
                    "sha256": _sha256_file(sidecar),
                    "summary": {
                        "surface_key": sidecar_entry["surface_key"],
                        "fail_count": sidecar_entry["fail_count"],
                        "divergence_count": len(sidecar_entry["divergences"]),
                        "blocking_divergence_count": 0,
                        "provenance_key": provenance["key"],
                        "provenance_png_sha256": provenance["png_sha256"],
                        "provenance_capture_script_sha256": provenance["capture_script_sha256"],
                        "provenance_introspection_entry_id": provenance["introspection_entry_id"],
                    },
                },
                "provenance": provenance,
            }
        ],
    }
    bundle.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return bundle


def _patch_audit_context(
    monkeypatch,
    *,
    base_text: str,
    diff_text: str,
    base_commit: str = "base-sha",
    head_commit: str = "head-sha",
    commit_map: dict[str, str] | None = None,
    audited_commits: set[str] | None = None,
    bundle_payload: dict | None = None,
    changed_files: list[str] | None = None,
):
    monkeypatch.setattr(audit, "handoff_diff", lambda base, handoff: diff_text)
    monkeypatch.setattr(audit, "changed_files", lambda base: changed_files or ["qa/anti_fraud_scan.py"])
    def _rev_parse(rev: str) -> str | None:
        if commit_map and rev in commit_map:
            return commit_map[rev]
        if rev == "HEAD":
            return head_commit
        if rev == base_commit:
            return base_commit
        if rev == "base":
            return base_commit
        if rev == "main":
            return base_commit
        return commit_map.get(rev) if commit_map else base_commit

    monkeypatch.setattr(audit, "_git_rev_parse", _rev_parse)
    monkeypatch.setattr(audit, "_git_show_text", lambda base, handoff: base_text)
    monkeypatch.setattr(audit, "_resolve_commit_range", lambda base: audited_commits or {head_commit})
    monkeypatch.setattr(audit, "_load_bundle", lambda path: bundle_payload)
    monkeypatch.setattr(audit, "anti_fraud_clean", lambda: True)


def test_hardening_objective_cannot_close_visual_checkbox(monkeypatch, tmp_path):
    key = "suite:home@light"
    report = _make_report(tmp_path, key)
    sidecar = _make_sidecar(tmp_path, key)
    bundle = _make_bundle(
        tmp_path,
        key=key,
        commit_hashes=["abc1234"],
        report=report,
        sidecar=sidecar,
        base_commit="b" * 40,
        head_commit="c" * 40,
    )
    base_text = """
- [ ] `suite:home@light` pendiente
"""
    current_text = """
- [x] `suite:home@light` cierre
  - fix commit `abc1234`
"""
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text(current_text, encoding="utf-8")
    _patch_audit_context(
        monkeypatch,
        base_text=base_text,
        diff_text="""
@@ -1 +1 @@
- - [ ] `suite:home@light` pendiente
+ - [x] `suite:home@light` cierre
""",
        commit_map={"abc1234": "a" * 40, "main": "b" * 40, "HEAD": "c" * 40},
        audited_commits={"a" * 40},
        bundle_payload=json.loads(bundle.read_text(encoding="utf-8")),
        changed_files=["qa/anti_fraud_scan.py"],
    )

    result = audit.audit(
        base="main",
        handoff=handoff,
        bundle=bundle,
        layered_reports=[report],
        sidecar=sidecar,
        objective="hardening-qa",
        skip_anti_fraud=True,
    )

    assert result.ok is False
    assert "hardening_objective_must_not_close_visual_checkboxes" in result.reasons


def test_bundle_required_for_b_plus_k_style_closure(monkeypatch, tmp_path):
    key = "suite:dbt-library@light"
    report = _make_report(tmp_path, key)
    sidecar = _make_sidecar(tmp_path, key)
    current_text = """
- [x] `suite:dbt-library@light` cierre
  - fix commit `abc1234`
"""
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text(current_text, encoding="utf-8")
    _patch_audit_context(
        monkeypatch,
        base_text="""
- [ ] `suite:dbt-library@light` pendiente
""",
        diff_text="""
@@ -1 +1 @@
- - [ ] `suite:dbt-library@light` pendiente
+ - [x] `suite:dbt-library@light` cierre
""",
        commit_map={"abc1234": "a" * 40, "main": "b" * 40, "HEAD": "c" * 40},
        audited_commits={"a" * 40},
        bundle_payload=None,
        changed_files=["qa/_captures_v8/suite-dbt-library-light-960x600.png", "qa/_visual_auditor_spec/introspection.json", "reports/qa/layered_visual_compare_item/LAYERED_VISUAL_REPORT.json"],
    )

    result = audit.audit(
        base="main",
        handoff=handoff,
        bundle=tmp_path / "missing_bundle.json",
        layered_reports=[report],
        sidecar=sidecar,
        objective="",
        skip_anti_fraud=True,
    )

    assert result.ok is False
    assert "checkbox_closure_without_versioned_bundle" in result.reasons


def test_commit_hash_inventado_fails(monkeypatch, tmp_path):
    key = "suite:dbt-library@light"
    report = _make_report(tmp_path, key)
    sidecar = _make_sidecar(tmp_path, key)
    bundle = _make_bundle(
        tmp_path,
        key=key,
        commit_hashes=["audit-fraud-test"],
        report=report,
        sidecar=sidecar,
        base_commit="b" * 40,
        head_commit="c" * 40,
    )
    base_text = """
- [ ] `suite:dbt-library@light` pendiente
"""
    current_text = """
- [x] `suite:dbt-library@light` cierre
  - fix commit `audit-fraud-test`
"""
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text(current_text, encoding="utf-8")
    _patch_audit_context(
        monkeypatch,
        base_text=base_text,
        diff_text="""
@@ -1 +1 @@
- - [ ] `suite:dbt-library@light` pendiente
+ - [x] `suite:dbt-library@light` cierre
""",
        commit_map={"main": "b" * 40, "HEAD": "c" * 40},
        audited_commits={"d" * 40},
        bundle_payload=json.loads(bundle.read_text(encoding="utf-8")),
        changed_files=["qa/anti_fraud_scan.py"],
    )

    result = audit.audit(
        base="main",
        handoff=handoff,
        bundle=bundle,
        layered_reports=[report],
        sidecar=sidecar,
        objective="",
        skip_anti_fraud=True,
    )

    assert result.ok is False
    assert any("does not exist in git" in reason for reason in result.reasons)


def test_base_manipulado_fails(monkeypatch, tmp_path):
    key = "suite:dbt-library@light"
    report = _make_report(tmp_path, key)
    sidecar = _make_sidecar(tmp_path, key)
    bundle = _make_bundle(
        tmp_path,
        key=key,
        commit_hashes=["abc1234"],
        report=report,
        sidecar=sidecar,
        base_commit="b" * 40,
        head_commit="c" * 40,
    )
    closed_text = """
- [x] `suite:dbt-library@light` cierre
  - fix commit `abc1234`
"""
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text(closed_text, encoding="utf-8")
    _patch_audit_context(
        monkeypatch,
        base_text=closed_text,
        diff_text="",
        commit_map={"abc1234": "a" * 40, "main": "b" * 40, "HEAD": "c" * 40},
        audited_commits={"a" * 40},
        bundle_payload=json.loads(bundle.read_text(encoding="utf-8")),
        changed_files=["qa/anti_fraud_scan.py"],
    )

    result = audit.audit(
        base="main",
        handoff=handoff,
        bundle=bundle,
        layered_reports=[report],
        sidecar=sidecar,
        objective="",
        skip_anti_fraud=True,
    )

    assert result.ok is False
    assert any("open checkbox transition" in reason for reason in result.reasons)


def test_fresh_clone_bundle_evidence_does_not_require_gitignored_artifacts(monkeypatch, tmp_path):
    key = "suite:dbt-library@light"
    report = _make_report(tmp_path, key)
    sidecar = _make_sidecar(tmp_path, key)
    bundle = _make_bundle(
        tmp_path,
        key=key,
        commit_hashes=["abc1234"],
        report=report,
        sidecar=sidecar,
        base_commit="b" * 40,
        head_commit="c" * 40,
    )
    (tmp_path / "CAPTURE_MANIFEST.json").unlink()
    report.unlink()
    sidecar.unlink()
    current_text = """
- [x] `suite:dbt-library@light` cierre
  - fix commit `abc1234`
"""
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text(current_text, encoding="utf-8")
    _patch_audit_context(
        monkeypatch,
        base_text="""
- [ ] `suite:dbt-library@light` pendiente
""",
        diff_text="""
@@ -1 +1 @@
- - [ ] `suite:dbt-library@light` pendiente
+ - [x] `suite:dbt-library@light` cierre
""",
        commit_map={"abc1234": "a" * 40, "main": "b" * 40, "HEAD": "c" * 40},
        audited_commits={"a" * 40},
        bundle_payload=json.loads(bundle.read_text(encoding="utf-8")),
        changed_files=["VISUAL_REPAIR_HANDOFF.md", "docs/visual_closure_bundle.json"],
    )

    result = audit.audit(
        base="main",
        handoff=handoff,
        bundle=bundle,
        layered_reports=[],
        sidecar=tmp_path / "missing_introspection.json",
        objective="",
        skip_anti_fraud=True,
    )

    assert result.ok is True
    assert result.bundle_keys == [key]
    assert result.validated_commits == ["a" * 40]


def test_hardening_objective_allows_restricted_paths_without_closure(monkeypatch, tmp_path):
    empty_bundle = tmp_path / "empty_bundle.json"
    empty_bundle.write_text(
        json.dumps(
            {
                "schema": "visual_closure_bundle.v1",
                "generated_at": None,
                "audited_range": {
                    "base_ref": "",
                    "base_commit": "",
                    "head_ref": "",
                    "head_commit": "",
                },
                "closures": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text("", encoding="utf-8")
    _patch_audit_context(
        monkeypatch,
        base_text="",
        diff_text="",
        bundle_payload=json.loads(empty_bundle.read_text(encoding="utf-8")),
        changed_files=["qa/anti_fraud_scan.py"],
    )

    result = audit.audit(
        base="main",
        handoff=handoff,
        bundle=empty_bundle,
        layered_reports=[],
        sidecar=Path("introspection.json"),
        objective="hardening-qa",
    )

    assert result.ok is True
