#!/usr/bin/env python3
"""odiff runner — antialiasing-aware pixel comparison via the odiff binary.

Wraps the external ``odiff`` binary (npm: ``odiff-bin``) to provide a
drop-in alternative to the legacy SSIM/MAD comparison in ``diff_fidelity.py``.

odiff with ``--antialiasing`` is specifically designed to suppress the
sub-pixel rasterization differences that plague cross-renderer image
comparisons (Chromium mockup vs Qt capture), which SSIM treats as real diffs.

Usage::

    from qa.odiff_runner import compare_with_odiff
    result = compare_with_odiff(target_path, actual_path, diff_png_path)
    # result = {"diff_pixels": int, "diff_percentage": float, "diff_png_path": str}
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _find_odiff_binary() -> str:
    """Locate the odiff executable in a cross-platform way."""
    # 1) Explicit env override
    env_path = os.environ.get("ODIFF_PATH")
    if env_path and Path(env_path).exists():
        return env_path
    # 2) npm global node_modules (Windows + Unix)
    npm_prefix = os.environ.get("APPDATA") or os.environ.get("HOME", "")
    candidates = [
        Path(npm_prefix) / "npm" / "node_modules" / "odiff-bin" / "bin" / "odiff.exe",
        Path(npm_prefix) / "npm" / "node_modules" / "odiff-bin" / "bin" / "odiff",
        Path("/usr/local/bin/odiff"),
        Path("/usr/bin/odiff"),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    # 3) PATH lookup
    found = shutil.which("odiff")
    if found:
        return found
    raise FileNotFoundError(
        "odiff binary not found. Install with: npm install -g odiff-bin"
    )


def compare_with_odiff(
    target: Path,
    actual: Path,
    diff_png: Path | None = None,
    *,
    threshold: float = 0.1,
    antialiasing: bool = True,
) -> dict[str, int | float | str | bool]:
    """Compare two images with odiff, returning structured diff metrics.

    Parameters
    ----------
    target : Path
        Reference/canonical image (mockup).
    actual : Path
        Image under test (Qt capture).
    diff_png : Path | None
        Where to write the visual diff overlay. If None, a temp file is used.
    threshold : float
        Color difference threshold (0-1). Pixels below this are ignored.
    antialiasing : bool
        If True, enables odiff's --antialiasing flag to suppress cross-renderer
        sub-pixel rasterization noise.

    Returns
    -------
    dict with keys:
        - ``diff_pixels`` (int): count of differing pixels
        - ``diff_percentage`` (float): percentage of image area that differs
        - ``diff_png_path`` (str): path to the diff overlay PNG
        - ``match`` (bool): True if images are pixel-identical
    """
    odiff_bin = _find_odiff_binary()
    if diff_png is None:
        diff_png = target.parent / f"{target.stem}_odiff_diff.png"

    diff_png.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        odiff_bin,
        str(target),
        str(actual),
        str(diff_png),
        "--threshold",
        str(threshold),
    ]
    if antialiasing:
        cmd.append("--antialiasing")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
    )
    # odiff exit codes: 0=match, 1=diff found, 2+=error
    if result.returncode >= 2:
        raise RuntimeError(
            f"odiff failed (exit {result.returncode}): {result.stderr.strip()}"
        )

    output = result.stdout.strip()
    # Parse odiff JSON output if available, otherwise parse text
    diff_pixels = 0
    diff_percentage: float = 0.0
    try:
        data = json.loads(output)
        diff_pixels = int(data.get("diffCount", 0))
        # odiff reports "diffPercentage" as 0-1 float
        diff_percentage = float(data.get("diffPercentage", 0.0)) * 100.0
    except (json.JSONDecodeError, ValueError):
        # Fallback: parse text output lines like "diffCount: 123"
        for line in output.splitlines():
            line = line.strip()
            if "diffCount" in line and ":" in line:
                try:
                    diff_pixels = int(line.split(":")[1].strip())
                except ValueError:
                    pass
            if "diffPercentage" in line and ":" in line:
                try:
                    diff_percentage = float(line.split(":")[1].strip()) * 100.0
                except ValueError:
                    pass

    return {
        "diff_pixels": diff_pixels,
        "diff_percentage": round(diff_percentage, 4),
        "diff_png_path": str(diff_png),
        "match": result.returncode == 0,
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python odiff_runner.py <target.png> <actual.png> [diff.png]")
        sys.exit(2)
    r = compare_with_odiff(Path(sys.argv[1]), Path(sys.argv[2]))
    print(json.dumps(r, indent=2))
