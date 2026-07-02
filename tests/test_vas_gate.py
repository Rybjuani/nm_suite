"""Contract tests for qa/vas_gate.py — validates the VAS gate logic."""

import json
import hashlib
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


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_file_key(key: str) -> str:
    return (
        key.replace(":", "-")
        .replace("@", "-")
        .replace("/", "-")
        .replace("\\", "-")
    )


def _write_sidecar(tmp_path: Path, entries: list) -> Path:
    sidecar = tmp_path / "introspection.json"
    capture_dir = tmp_path / "_captures_v8"
    capture_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "harness": "capture_v8.py",
        "results": [],
    }
    script_sha = _sha256_file(REPO_ROOT / "qa" / "capture_v8.py")
    enriched_entries = []
    for idx, raw_entry in enumerate(entries):
        entry = dict(raw_entry)
        key = str(entry.get("surface_key", f"suite:missing-{idx}@light"))
        png_path = capture_dir / f"{_safe_file_key(key)}-960x600.png"
        png_path.write_bytes(f"fake png payload for {key}".encode("utf-8"))
        png_sha = _sha256_file(png_path)
        entry_id = hashlib.sha256(f"{key}|{png_sha}|{idx}".encode("utf-8")).hexdigest()
        provenance = {
            "schema": "capture_v8.provenance.v1",
            "key": key,
            "capture_file": png_path.name,
            "capture_path": str(png_path),
            "png_sha256": png_sha,
            "captured_at": "2026-07-02T00:00:00+00:00",
            "command_args": ["qa/capture_v8.py", "--app", "suite", "--view", "test"],
            "cwd": str(REPO_ROOT),
            "git_head": "test-head",
            "git_branch": "test",
            "git_tracked_dirty": False,
            "capture_script": str(REPO_ROOT / "qa" / "capture_v8.py"),
            "capture_script_sha256": script_sha,
            "capture_manifest": str(capture_dir / "CAPTURE_MANIFEST.json"),
            "introspection_sidecar": str(sidecar),
            "introspection_entry_id": entry_id,
        }
        entry.setdefault("provenance", provenance)
        manifest["results"].append({
            "key": key,
            "file": png_path.name,
            "sha256": png_sha,
            "provenance": provenance,
        })
        enriched_entries.append(entry)
    (capture_dir / "CAPTURE_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
    sidecar.write_text(json.dumps(enriched_entries), encoding="utf-8")
    return sidecar


def _write_raw_sidecar(tmp_path: Path, entries: list) -> Path:
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


def test_fail_forged_sidecar_without_capture_provenance(tmp_path):
    """A hand-written clean VAS sidecar is not closure evidence by itself."""
    sidecar = _write_raw_sidecar(tmp_path, [
        {"surface_key": "suite:test@light", "fail_count": 0, "divergences": []},
    ])

    result = _run_gate(sidecar, key="suite:test@light")

    assert result.returncode == 1
    assert "missing capture provenance" in result.stderr


def test_fail_sidecar_with_mismatched_png_sha(tmp_path):
    """The VAS sidecar must be linked to the exact captured PNG bytes."""
    sidecar = _write_sidecar(tmp_path, [
        {"surface_key": "suite:test@light", "fail_count": 0, "divergences": []},
    ])
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    payload[0]["provenance"]["png_sha256"] = "0" * 64
    sidecar.write_text(json.dumps(payload), encoding="utf-8")

    result = _run_gate(sidecar, key="suite:test@light")

    assert result.returncode == 1
    assert "sha256 mismatch" in result.stderr


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
