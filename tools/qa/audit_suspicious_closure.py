import argparse
import csv
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path.cwd()
HANDOFF = ROOT / "VISUAL_REPAIR_HANDOFF.md"
OUT_ROOT = ROOT / "reports" / "qa" / "suspicious_closure_audit"

KEY_RE = re.compile(r"(suite|hub):([^@\s`\"'\]\)]+)@(light|dark)")
CHECKED_LINE_RE = re.compile(r"^\+\s*-\s*\[x\].*?(suite|hub):([^@\s`\"'\]\)]+)@(light|dark)")

def run(cmd, check=False):
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace")
    if check and p.returncode != 0:
        raise SystemExit(f"Command failed: {' '.join(cmd)}\n{p.stderr}")
    return p

def safe(s):
    return re.sub(r"[^A-Za-z0-9_.-]", "_", re.sub(r"[:@\\/\s]+", "_", s))

def parse_key(key):
    m = KEY_RE.fullmatch(key)
    if not m:
        raise SystemExit(f"Invalid key: {key}")
    return m.group(1), m.group(2), m.group(3)

def keys_from_diff(base, head):
    diffs = []

    if base and head:
        diffs.append(run(["git", "diff", "--unified=0", base, head, "--", "VISUAL_REPAIR_HANDOFF.md"]).stdout)

    diffs.append(run(["git", "diff", "--unified=0", "--", "VISUAL_REPAIR_HANDOFF.md"]).stdout)
    diffs.append(run(["git", "diff", "--cached", "--unified=0", "--", "VISUAL_REPAIR_HANDOFF.md"]).stdout)

    found = []
    for diff in diffs:
        for line in diff.splitlines():
            m = CHECKED_LINE_RE.search(line)
            if m:
                found.append(f"{m.group(1)}:{m.group(2)}@{m.group(3)}")

    return sorted(set(found))

def classify(text):
    t = text.lower()
    if "anti-fraud scan failed" in t or "anti-fraud failed" in t or "result: fail" in t or "result: suspicious" in t:
        return "ANTI_FRAUD_FAIL"
    if "layered visual compare failed" in t:
        return "LAYERED_FAIL"
    if "vas gate" in t and ("fail" in t or "failed" in t):
        if "sidecar not found" in t:
            return "VAS_SIDECAR_MISSING"
        if "not found in sidecar" in t:
            return "VAS_KEY_MISSING"
        if "fail_count" in t or "blocking divergence" in t or "radius_missing" in t:
            return "VAS_DIVERGENCE_FAIL"
        return "VAS_FAIL"
    if "capture" in t and ("failed" in t or "error" in t):
        return "CAPTURE_FAIL"
    return "UNKNOWN_FAIL"

def audit_key(key, out_dir):
    app, view, theme = parse_key(key)
    item_dir = out_dir / safe(key)
    item_dir.mkdir(parents=True, exist_ok=True)

    stdout = item_dir / "stdout.log"
    stderr = item_dir / "stderr.log"
    report = item_dir / "layered"

    sidecar = ROOT / "qa" / "_visual_auditor_spec" / "introspection.json"
    try:
        sidecar.unlink()
    except FileNotFoundError:
        pass

    cmd = [
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(ROOT / "qa" / "run_visual_item.ps1"),
        "-App", app,
        "-View", view,
        "-Theme", theme,
        "-Key", key,
        "-OutDir", str(report),
    ]

    with stdout.open("w", encoding="utf-8", errors="replace") as so, stderr.open("w", encoding="utf-8", errors="replace") as se:
        p = subprocess.run(cmd, cwd=ROOT, stdout=so, stderr=se)

    text = stdout.read_text(encoding="utf-8", errors="replace") + "\n" + stderr.read_text(encoding="utf-8", errors="replace")
    return {
        "key": key,
        "exit_code": p.returncode,
        "result": "PASS" if p.returncode == 0 else "FAIL",
        "cause": "OK" if p.returncode == 0 else classify(text),
        "stdout": str(stdout),
        "stderr": str(stderr),
        "report_dir": str(report),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="HEAD~1")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--keys", nargs="*", default=[])
    args = ap.parse_args()

    if not HANDOFF.exists():
        raise SystemExit("Missing VISUAL_REPAIR_HANDOFF.md")

    keys = sorted(set(args.keys or keys_from_diff(args.base, args.head)))
    if not keys:
        raise SystemExit("No newly closed [x] keys detected. Use --keys.")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = OUT_ROOT / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for i, key in enumerate(keys, 1):
        print(f"[{i}/{len(keys)}] {key}")
        rows.append(audit_key(key, out_dir))

    with (out_dir / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    (out_dir / "summary.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

    bad = [r for r in rows if r["exit_code"] != 0]

    md = [
        "# Suspicious closure audit",
        "",
        f"- Date: {datetime.now().isoformat(timespec='seconds')}",
        f"- Base: `{args.base}`",
        f"- Head: `{args.head}`",
        f"- Keys audited: {len(rows)}",
        f"- PASS: {len(rows) - len(bad)}",
        f"- FAIL: {len(bad)}",
        "",
    ]

    if bad:
        md += ["## FAIL", ""]
        for r in bad:
            md.append(f"- `{r['key']}` — `{r['cause']}` — exit `{r['exit_code']}`")
            md.append(f"  - stdout: `{r['stdout']}`")
            md.append(f"  - stderr: `{r['stderr']}`")
            md.append(f"  - report: `{r['report_dir']}`")
        md.append("")

    md += ["## PASS", ""]
    for r in rows:
        if r["exit_code"] == 0:
            md.append(f"- `{r['key']}`")

    (out_dir / "AUDIT.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print("")
    print(f"OUT_DIR={out_dir}")
    print(f"REPORT={out_dir / 'AUDIT.md'}")
    print(f"FAIL={len(bad)}")

    raise SystemExit(2 if bad else 0)

if __name__ == "__main__":
    main()