from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "visual-closure-replay.yml"
CODEOWNERS = ROOT / ".github" / "CODEOWNERS"


def test_workflow_runs_only_supported_structural_replay_contract():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "--structural-precheck" in text
    assert "--base" in text
    assert "--no-regen" not in text
    assert "--skip-legacy" not in text
    assert "--handoff" not in text
    assert "issues: read" in text
    assert 'git merge-base --is-ancestor "$base_commit" HEAD' in text


def test_workflow_pins_an_explicit_stdlib_test_set():
    text = WORKFLOW.read_text(encoding="utf-8")
    required = {
        "tests/test_hash_utils.py",
        "tests/test_closure_policy.py",
        "tests/test_approval_verifier.py",
        "tests/test_surface_scope.py",
        "tests/test_handoff_integrity.py",
        "tests/test_replay_visual_closure.py",
    }

    assert "pytest-stdlib:" in text
    assert "pytest==9.0.3" in text
    assert all(path in text for path in required)


def test_codeowners_protects_all_visual_kernel_namespaces():
    rules = {
        line.split()[0]: line.split()[1]
        for line in CODEOWNERS.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert rules == {
        "/qa/**": "@Rybjuani",
        "/tools/qa/**": "@Rybjuani",
        "/.github/workflows/**": "@Rybjuani",
        "/.github/CODEOWNERS": "@Rybjuani",
    }
