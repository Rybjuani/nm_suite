#!/usr/bin/env python3
"""VAS Gate — validates the VAS introspection sidecar for closure approval.

Usage:
    python qa/vas_gate.py [--key KEY] [--sidecar PATH]

Exit codes:
    0  PASS — the sidecar is valid and the key (or all entries) meet closure bar.
    1  FAIL — sidecar missing, key missing, fail_count > 0, or critical divergences.

Closure bar (all must hold):
    1. Sidecar file exists and is valid JSON.
    2. If --key is given, that surface_key must be present.
    3. fail_count == 0 for the validated entry(ies).
    4. Zero divergences of severity "high" or "medium".
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

DEFAULT_SIDECAR = Path("qa/_visual_auditor_spec/introspection.json")
_PROJ = Path(__file__).resolve().parent.parent

try:
    from qa.state_probes import (
        STATE_ASSERTION_SCHEMA,
        state_assertion_required,
        state_assertion_sha256,
    )
except ModuleNotFoundError:
    from state_probes import (
        STATE_ASSERTION_SCHEMA,
        state_assertion_required,
        state_assertion_sha256,
    )

BLOCKING_SEVERITIES = {"high", "medium"}


def _check_state_assertion(
    entry: dict,
    matching_result: dict,
    provenance: dict,
    surface: str,
) -> list[str]:
    reasons: list[str] = []
    sidecar_assertion = entry.get("state_assertion")
    manifest_assertion = matching_result.get("state_assertion")
    sidecar_sha = entry.get("state_assertion_sha256")
    manifest_sha = matching_result.get("state_assertion_sha256")
    provenance_sha = provenance.get("state_assertion_sha256")
    required = state_assertion_required(surface)
    exists = sidecar_assertion is not None or manifest_assertion is not None
    if required and not exists:
        return [f"[{surface}] required state_assertion is missing"]
    if not exists:
        return reasons
    if not isinstance(sidecar_assertion, dict) or not isinstance(manifest_assertion, dict):
        return [f"[{surface}] state_assertion must exist in sidecar and manifest"]
    if sidecar_assertion != manifest_assertion:
        reasons.append(f"[{surface}] state_assertion sidecar/manifest mismatch")
    expected_sha = state_assertion_sha256(sidecar_assertion)
    if not expected_sha or any(
        value != expected_sha for value in (sidecar_sha, manifest_sha, provenance_sha)
    ):
        reasons.append(f"[{surface}] state_assertion sha256 mismatch")
    if sidecar_assertion.get("schema") != STATE_ASSERTION_SCHEMA:
        reasons.append(f"[{surface}] state_assertion schema mismatch")
    if sidecar_assertion.get("key") != surface:
        reasons.append(f"[{surface}] state_assertion key mismatch")
    if sidecar_assertion.get("pass") is not True:
        reasons.append(f"[{surface}] state_assertion.pass must be true")
    return reasons


def _sha256_file(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def _resolve_path(value: object, *, sidecar_path: Path) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    candidates = [
        (_PROJ / path),
        (sidecar_path.parent / path),
        (sidecar_path.parent.parent / "_captures_v8" / path.name),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _key_from_manifest_result(result: dict) -> str:
    if isinstance(result.get("key"), str):
        return result["key"]
    app = result.get("app")
    view = result.get("view")
    theme = result.get("theme")
    if all(isinstance(part, str) and part for part in (app, view, theme)):
        return f"{app}:{view}@{theme}"
    return ""


def _load_capture_manifest(path: Path | None) -> dict | None:
    if path is None or not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError, OSError):
        return None
    return payload if isinstance(payload, dict) else None


def _load_sidecar(path: Path) -> list[dict]:
    """Load and validate the sidecar is a JSON list of entries."""
    if not path.exists():
        print(f"VAS GATE FAIL: sidecar not found: {path}", file=sys.stderr)
        sys.exit(1)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"VAS GATE FAIL: sidecar is not valid JSON: {exc}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(data, list):
        print(
            f"VAS GATE FAIL: sidecar root is {type(data).__name__}, expected a JSON array",
            file=sys.stderr,
        )
        sys.exit(1)
    if len(data) == 0:
        print("VAS GATE FAIL: sidecar is empty (no VAS entries)", file=sys.stderr)
        sys.exit(1)
    return data


def _check_provenance(entry: dict, sidecar_path: Path) -> list[str]:
    reasons: list[str] = []
    surface = entry.get("surface_key", "<missing surface_key>")
    provenance = entry.get("provenance")
    if not isinstance(provenance, dict):
        return [f"[{surface}] missing capture provenance"]

    required = [
        "key",
        "capture_path",
        "png_sha256",
        "captured_at",
        "command_args",
        "git_head",
        "capture_script_sha256",
        "capture_manifest",
        "introspection_sidecar",
        "introspection_entry_id",
    ]
    for field in required:
        if field not in provenance or provenance.get(field) in ("", None, []):
            reasons.append(f"[{surface}] provenance missing '{field}'")

    if provenance.get("key") != surface:
        reasons.append(f"[{surface}] provenance key mismatch: {provenance.get('key')!r}")

    command_args = provenance.get("command_args")
    if not isinstance(command_args, list) or not any("capture_v8.py" in str(arg) for arg in command_args):
        reasons.append(f"[{surface}] provenance command_args do not reference capture_v8.py")

    png_path = _resolve_path(provenance.get("capture_path"), sidecar_path=sidecar_path)
    if png_path is None or not png_path.exists():
        reasons.append(f"[{surface}] provenance capture_path does not exist")
    else:
        actual_sha = _sha256_file(png_path)
        if actual_sha != provenance.get("png_sha256"):
            reasons.append(f"[{surface}] PNG sha256 mismatch for provenance capture_path")

    sidecar_link = _resolve_path(provenance.get("introspection_sidecar"), sidecar_path=sidecar_path)
    try:
        if sidecar_link is None or sidecar_link.resolve() != sidecar_path.resolve():
            reasons.append(f"[{surface}] provenance introspection_sidecar does not match validated sidecar")
    except OSError:
        reasons.append(f"[{surface}] provenance introspection_sidecar cannot be resolved")

    script_sha = _sha256_file(_PROJ / "qa" / "capture_v8.py")
    if script_sha and provenance.get("capture_script_sha256") != script_sha:
        reasons.append(f"[{surface}] capture_v8.py sha256 mismatch")

    manifest_path = _resolve_path(provenance.get("capture_manifest"), sidecar_path=sidecar_path)
    manifest = _load_capture_manifest(manifest_path)
    if manifest is None:
        reasons.append(f"[{surface}] capture manifest missing or invalid")
        return reasons

    matches = [
        result
        for result in manifest.get("results", [])
        if isinstance(result, dict) and _key_from_manifest_result(result) == surface
    ]
    if not matches:
        reasons.append(f"[{surface}] capture manifest has no matching key")
        return reasons

    expected_file = Path(str(provenance.get("capture_path", ""))).name
    matching_result = None
    for result in matches:
        if result.get("file") == expected_file:
            matching_result = result
            break
    if matching_result is None:
        reasons.append(f"[{surface}] capture manifest has no matching capture file")
        return reasons

    result_provenance = matching_result.get("provenance")
    if not isinstance(result_provenance, dict):
        reasons.append(f"[{surface}] capture manifest result lacks provenance")
        return reasons
    for field in (
        "png_sha256",
        "introspection_entry_id",
        "capture_script_sha256",
        "state_assertion_sha256",
    ):
        if result_provenance.get(field) != provenance.get(field):
            reasons.append(f"[{surface}] capture manifest provenance mismatch for '{field}'")

    if matching_result.get("sha256") and matching_result.get("sha256") != provenance.get("png_sha256"):
        reasons.append(f"[{surface}] capture manifest sha256 does not match provenance")

    if matching_result.get("success") is not True:
        reasons.append(f"[{surface}] capture manifest success must be true")
    if matching_result.get("technical_capture_valid") is not True:
        reasons.append(f"[{surface}] technical_capture_valid must be true")
    if matching_result.get("state_evidence_valid") is not True:
        reasons.append(f"[{surface}] state_evidence_valid must be true")
    if matching_result.get("capture_status") != "CAPTURED_VALID":
        reasons.append(f"[{surface}] capture_status must be CAPTURED_VALID")

    reasons.extend(_check_state_assertion(entry, matching_result, provenance, surface))

    return reasons


def _check_entry(entry: dict, key: str | None, sidecar_path: Path) -> list[str]:
    """Return a list of failure reasons for a single entry. Empty = pass."""
    reasons: list[str] = []
    surface = entry.get("surface_key", "<missing surface_key>")

    if key is not None and entry.get("surface_key") != key:
        return []  # Not the key we're checking; skip silently.

    # fail_count
    fail_count = entry.get("fail_count")
    if fail_count is None:
        reasons.append(f"[{surface}] missing key 'fail_count'")
    elif not isinstance(fail_count, int):
        reasons.append(f"[{surface}] 'fail_count' is {type(fail_count).__name__}, expected int")
    elif fail_count != 0:
        reasons.append(f"[{surface}] fail_count={fail_count} (must be 0)")

    # divergences — blocking severities
    divergences = entry.get("divergences", [])
    if not isinstance(divergences, list):
        divergences = []
    blocking = [
        d for d in divergences
        if isinstance(d, dict) and d.get("severity", "").lower() in BLOCKING_SEVERITIES
    ]
    if blocking:
        kinds = ", ".join(
            f"{d.get('kind', '?')}({d.get('severity', '?')})" for d in blocking
        )
        reasons.append(
            f"[{surface}] {len(blocking)} blocking divergence(s): {kinds}"
        )

    reasons.extend(_check_provenance(entry, sidecar_path))
    return reasons


def validate(path: Path, key: str | None) -> bool:
    """Run the gate. Returns True on PASS, exits non-zero on FAIL."""
    entries = _load_sidecar(path)

    if key is not None:
        matching = [e for e in entries if e.get("surface_key") == key]
        if not matching:
            print(
                f"VAS GATE FAIL: key '{key}' not found in sidecar "
                f"(has {len(entries)} entries: "
                f"{[e.get('surface_key', '?') for e in entries[:5]]}...)",
                file=sys.stderr,
            )
            return False
        to_check = matching
    else:
        to_check = entries

    all_reasons: list[str] = []
    for entry in to_check:
        if not isinstance(entry, dict):
            all_reasons.append(f"Non-dict entry in sidecar: {entry!r}")
            continue
        all_reasons.extend(_check_entry(entry, None, path))  # check all filtered entries

    if all_reasons:
        print("VAS GATE FAIL:", file=sys.stderr)
        for r in all_reasons:
            print(f"  - {r}", file=sys.stderr)
        return False

    if key is not None:
        print(f"VAS GATE PASS: key '{key}' — fail_count=0, zero high/medium divergences.")
    else:
        print(f"VAS GATE PASS: all {len(to_check)} entries — fail_count=0, zero high/medium divergences.")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate VAS sidecar for closure approval."
    )
    parser.add_argument(
        "--key",
        default=None,
        help="Exact surface_key to validate (e.g. 'suite:recuperar-acceso@light'). "
        "If omitted, validates all entries.",
    )
    parser.add_argument(
        "--sidecar",
        type=Path,
        default=DEFAULT_SIDECAR,
        help=f"Path to introspection.json (default: {DEFAULT_SIDECAR})",
    )
    args = parser.parse_args()

    ok = validate(args.sidecar, args.key)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
