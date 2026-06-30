"""Contract tests for qa/vas_gate.py — validates the VAS gate logic."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
GATE_SCRIPT = REPO_ROOT / "qa" / "vas_gate.py"


def _run_gate(sidecar_path: Path, key: str | None = None) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(GATE_SCRIPT), "--sidecar", str(sidecar_path)]
    if key:
        cmd += ["--key", key]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )


def _write_sidecar(tmp_path: Path, entries: list) -> Path:
    sidecar = tmp_path / "introspection.json"
    sidecar.write_text(json.dumps(entries), encoding="utf-8")
    return sidecar


# ─── PASS cases ──────────────────────────────────────────────────────────────


def test_pass_single_clean_entry(tmp_path):
    """A single entry with fail_count=0 and no divergences passes."""
    sidecar = _write_sidecar(tmp_path, [
        {
            "surface_key": "suite:test@light",
            "fail_count": 0,
            "divergences": [],
            "size_review": [],
        }
    ])
    result = _run_gate(sidecar, key="suite:test@light")
    assert result.returncode == 0, result.stderr
    assert "VAS GATE PASS" in result.stdout


def test_pass_multiple_clean_entries_no_key(tmp_path):
    """Without --key, all clean entries pass."""
    sidecar = _write_sidecar(tmp_path, [
        {"surface_key": "suite:a@light", "fail_count": 0, "divergences": []},
        {"surface_key": "suite:b@dark", "fail_count": 0, "divergences": []},
    ])
    result = _run_gate(sidecar)
    assert result.returncode == 0, result.stderr


def test_pass_low_severity_divergence_allowed(tmp_path):
    """Low/info severity divergences do not block closure."""
    sidecar = _write_sidecar(tmp_path, [
        {
            "surface_key": "suite:test@dark",
            "fail_count": 0,
            "divergences": [
                {"kind": "RADIUS_INFO", "severity": "low", "message": "cosmetic"},
            ],
        }
    ])
    result = _run_gate(sidecar, key="suite:test@dark")
    assert result.returncode == 0, result.stderr


def test_pass_skips_other_keys_when_key_specified(tmp_path):
    """When --key is given, other entries with failures are ignored."""
    sidecar = _write_sidecar(tmp_path, [
        {"surface_key": "suite:other@light", "fail_count": 5, "divergences": [
            {"kind": "X", "severity": "high"}
        ]},
        {"surface_key": "suite:target@dark", "fail_count": 0, "divergences": []},
    ])
    result = _run_gate(sidecar, key="suite:target@dark")
    assert result.returncode == 0, result.stderr


# ─── FAIL cases ──────────────────────────────────────────────────────────────


def test_fail_missing_sidecar(tmp_path):
    """Non-existent sidecar file fails with exit 1."""
    missing = tmp_path / "nonexistent.json"
    result = _run_gate(missing, key="suite:test@light")
    assert result.returncode == 1
    assert "sidecar not found" in result.stderr


def test_fail_key_not_in_sidecar(tmp_path):
    """Key not present in sidecar fails."""
    sidecar = _write_sidecar(tmp_path, [
        {"surface_key": "suite:other@light", "fail_count": 0, "divergences": []},
    ])
    result = _run_gate(sidecar, key="suite:missing@light")
    assert result.returncode == 1
    assert "not found" in result.stderr


def test_fail_fail_count_nonzero(tmp_path):
    """fail_count > 0 fails the gate."""
    sidecar = _write_sidecar(tmp_path, [
        {"surface_key": "suite:test@light", "fail_count": 3, "divergences": []},
    ])
    result = _run_gate(sidecar, key="suite:test@light")
    assert result.returncode == 1
    assert "fail_count=3" in result.stderr


def test_fail_high_severity_divergence(tmp_path):
    """High severity divergence blocks closure."""
    sidecar = _write_sidecar(tmp_path, [
        {
            "surface_key": "suite:test@light",
            "fail_count": 0,
            "divergences": [
                {"kind": "GEOMETRY_BROKEN", "severity": "high", "message": "bad"},
            ],
        }
    ])
    result = _run_gate(sidecar, key="suite:test@light")
    assert result.returncode == 1
    assert "blocking divergence" in result.stderr.lower()


def test_fail_medium_severity_divergence(tmp_path):
    """Medium severity divergence blocks closure."""
    sidecar = _write_sidecar(tmp_path, [
        {
            "surface_key": "suite:test@light",
            "fail_count": 0,
            "divergences": [
                {"kind": "RADIUS_MISSING", "severity": "medium", "message": "bad"},
            ],
        }
    ])
    result = _run_gate(sidecar, key="suite:test@light")
    assert result.returncode == 1
    assert "blocking divergence" in result.stderr.lower()


def test_fail_missing_fail_count_key(tmp_path):
    """Missing fail_count key (exact key required) fails."""
    sidecar = _write_sidecar(tmp_path, [
        {"surface_key": "suite:test@light", "divergences": []},
    ])
    result = _run_gate(sidecar, key="suite:test@light")
    assert result.returncode == 1
    assert "missing key" in result.stderr.lower() and "fail_count" in result.stderr


def test_fail_empty_sidecar(tmp_path):
    """Empty sidecar array fails."""
    sidecar = _write_sidecar(tmp_path, [])
    result = _run_gate(sidecar)
    assert result.returncode == 1
    assert "empty" in result.stderr.lower()


def test_fail_invalid_json(tmp_path):
    """Malformed JSON fails."""
    sidecar = tmp_path / "introspection.json"
    sidecar.write_text("{not valid json", encoding="utf-8")
    result = _run_gate(sidecar)
    assert result.returncode == 1
    assert "not valid JSON" in result.stderr


def test_fail_all_entries_when_no_key_and_one_bad(tmp_path):
    """Without --key, any entry with a blocking divergence fails."""
    sidecar = _write_sidecar(tmp_path, [
        {"surface_key": "suite:good@light", "fail_count": 0, "divergences": []},
        {"surface_key": "suite:bad@dark", "fail_count": 1, "divergences": [
            {"kind": "X", "severity": "high"}
        ]},
    ])
    result = _run_gate(sidecar)
    assert result.returncode == 1


# ─── Edge cases ──────────────────────────────────────────────────────────────


def test_size_review_not_blocking(tmp_path):
    """size_review entries (even high severity) do not block — only divergences do."""
    sidecar = _write_sidecar(tmp_path, [
        {
            "surface_key": "suite:test@light",
            "fail_count": 0,
            "divergences": [],
            "size_review": [
                {"kind": "GEOMETRY_FIXED_SIZE_VIOLATED", "severity": "high", "message": "info only"},
            ],
        }
    ])
    result = _run_gate(sidecar, key="suite:test@light")
    assert result.returncode == 0, result.stderr
