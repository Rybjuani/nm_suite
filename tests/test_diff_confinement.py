from __future__ import annotations

import json
import subprocess
from pathlib import Path

from tools.qa import audit_diff_confinement as audit


def _git(repo: Path, *args: str) -> None:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "qa@example.test")
    _git(repo, "config", "user.name", "QA Test")
    return repo


def _commit(repo: Path) -> None:
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "seed")


def test_pass_with_allowed_path(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / "qa").mkdir()
    (repo / "qa" / "gate.txt").write_text("one\n", encoding="utf-8")
    _commit(repo)
    (repo / "qa" / "gate.txt").write_text("two\n", encoding="utf-8")

    out_dir = tmp_path / "report"
    rc = audit.main(["--repo", str(repo), "--base", "HEAD", "--allow-path", "qa", "--out-dir", str(out_dir)])

    payload = json.loads((out_dir / "DIFF_CONFINEMENT_REPORT.json").read_text(encoding="utf-8"))
    assert rc == 0
    assert payload["summary"]["verdict"] == "PASS"
    assert payload["files"][0]["path"] == "qa/gate.txt"


def test_fail_with_prohibited_file(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / "app.py").write_text("one\n", encoding="utf-8")
    _commit(repo)
    (repo / "app.py").write_text("two\n", encoding="utf-8")

    out_dir = tmp_path / "report"
    rc = audit.main(["--repo", str(repo), "--base", "HEAD", "--allow-path", "qa", "--out-dir", str(out_dir)])
    payload = json.loads((out_dir / "DIFF_CONFINEMENT_REPORT.json").read_text(encoding="utf-8"))

    assert rc == 1
    assert payload["summary"]["verdict"] == "FAIL"
    assert payload["prohibited_files"] == ["app.py"]


def test_pass_with_hunk_inside_allowed_block(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    doc = repo / "docs.md"
    doc.write_text("alpha\n<!-- START QA -->\nold\n<!-- END QA -->\nomega\n", encoding="utf-8")
    _commit(repo)
    doc.write_text("alpha\n<!-- START QA -->\nnew\n<!-- END QA -->\nomega\n", encoding="utf-8")

    out_dir = tmp_path / "report"
    rc = audit.main(
        [
            "--repo",
            str(repo),
            "--base",
            "HEAD",
            "--allow-path",
            "docs.md",
            "--allow-block",
            "docs.md",
            "<!-- START QA -->",
            "<!-- END QA -->",
            "--out-dir",
            str(out_dir),
        ]
    )
    payload = json.loads((out_dir / "DIFF_CONFINEMENT_REPORT.json").read_text(encoding="utf-8"))

    assert rc == 0
    assert payload["summary"]["hunks_outside_block_count"] == 0
    assert payload["files"][0]["hunks"][0]["reason"] == "inside_allowed_block"


def test_fail_with_hunk_outside_allowed_block(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    doc = repo / "docs.md"
    doc.write_text("alpha\n<!-- START QA -->\nold\n<!-- END QA -->\nomega\n", encoding="utf-8")
    _commit(repo)
    doc.write_text("alpha\n<!-- START QA -->\nold\n<!-- END QA -->\nchanged\n", encoding="utf-8")

    out_dir = tmp_path / "report"
    rc = audit.main(
        [
            "--repo",
            str(repo),
            "--base",
            "HEAD",
            "--allow-path",
            "docs.md",
            "--allow-block",
            "docs.md",
            "<!-- START QA -->",
            "<!-- END QA -->",
            "--out-dir",
            str(out_dir),
        ]
    )
    payload = json.loads((out_dir / "DIFF_CONFINEMENT_REPORT.json").read_text(encoding="utf-8"))

    assert rc == 1
    assert payload["summary"]["hunks_outside_block_count"] == 1
    assert payload["hunks_outside_block"][0]["reason"] == "outside_allowed_block"


def test_json_report_contains_summary_and_files(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / "qa").mkdir()
    (repo / "qa" / "x.txt").write_text("a\n", encoding="utf-8")
    _commit(repo)
    (repo / "qa" / "x.txt").write_text("b\n", encoding="utf-8")

    out_dir = tmp_path / "report"
    assert audit.main(["--repo", str(repo), "--base", "HEAD", "--allow-path", "qa", "--out-dir", str(out_dir)]) == 0
    payload = json.loads((out_dir / "DIFF_CONFINEMENT_REPORT.json").read_text(encoding="utf-8"))

    assert "summary" in payload
    assert "files" in payload
    assert payload["summary"]["diff_confined"] is True
