import argparse
import csv
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

KEY_RE = re.compile(r"(suite|hub):([^@\s`\"'\]\)]+)@(light|dark)")
CHECKED_RE = re.compile(r"^\s*-\s*\[x\]")
OPEN_RE = re.compile(r"^\s*-\s*\[\s\]")

ROOT = Path.cwd()
SIDECAR = ROOT / "qa" / "_visual_auditor_spec" / "introspection.json"

def safe_name(key: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", re.sub(r"[:@\\/\s]+", "_", key))

def parse_handoff(path: Path, include_open: bool):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    items = []

    for i, line in enumerate(lines):
        checked = bool(CHECKED_RE.search(line))
        open_item = bool(OPEN_RE.search(line))

        if not checked and not (include_open and open_item):
            continue

        keys = [m.group(0) for m in KEY_RE.finditer(line)]

        if not keys:
            for j in range(i + 1, min(i + 14, len(lines))):
                if CHECKED_RE.search(lines[j]) or OPEN_RE.search(lines[j]):
                    break
                keys.extend(m.group(0) for m in KEY_RE.finditer(lines[j]))

        for key in sorted(set(keys)):
            m = KEY_RE.fullmatch(key)
            if not m:
                raise RuntimeError(f"Invalid key at line {i + 1}: {key}")
            items.append({
                "line": i + 1,
                "checked": checked,
                "open": open_item,
                "app": m.group(1),
                "view": m.group(2),
                "theme": m.group(3),
                "key": key,
                "text": line.strip(),
            })

    return items

def run_item(item, out_dir: Path):
    item_dir = out_dir / safe_name(item["key"])
    item_dir.mkdir(parents=True, exist_ok=True)

    stdout_path = item_dir / "stdout.log"
    stderr_path = item_dir / "stderr.log"
    report_dir = item_dir / "layered"

    try:
        SIDECAR.unlink()
    except FileNotFoundError:
        pass

    cmd = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", str(ROOT / "qa" / "run_visual_item.ps1"),
        "-App", item["app"],
        "-View", item["view"],
        "-Theme", item["theme"],
        "-Key", item["key"],
        "-OutDir", str(report_dir),
    ]

    with stdout_path.open("w", encoding="utf-8", errors="replace") as out, stderr_path.open("w", encoding="utf-8", errors="replace") as err:
        p = subprocess.run(cmd, cwd=ROOT, stdout=out, stderr=err)

    return {
        "key": item["key"],
        "line": item["line"],
        "checked": item["checked"],
        "open": item["open"],
        "exit_code": p.returncode,
        "result": "PASS_CURRENT" if p.returncode == 0 else "FALSE_PASS_OR_STILL_FAIL",
        "report_dir": str(report_dir),
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "sidecar_exists": SIDECAR.exists(),
    }

def write_reports(out_dir: Path, items, rows):
    with (out_dir / "audit_plan.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["line", "checked", "open", "app", "view", "theme", "key", "text"])
        w.writeheader()
        w.writerows(items)

    with (out_dir / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["key"])
        w.writeheader()
        w.writerows(rows)

    (out_dir / "summary.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

    bad = [r for r in rows if r["checked"] and r["exit_code"] != 0]
    good = [r for r in rows if r["checked"] and r["exit_code"] == 0]

    md = []
    md.append("# Handoff false PASS audit")
    md.append("")
    md.append(f"- Date: {datetime.now().isoformat(timespec='seconds')}")
    md.append(f"- Checked keys audited: {len(good) + len(bad)}")
    md.append(f"- Current PASS: {len(good)}")
    md.append(f"- False PASS / still failing: {len(bad)}")
    md.append("")

    if bad:
        md.append("## FALSE PASS / still failing")
        md.append("")
        for r in bad:
            md.append(f"- `{r['key']}` — handoff line {r['line']} — exit {r['exit_code']}")
            md.append(f"  - stdout: `{r['stdout']}`")
            md.append(f"  - stderr: `{r['stderr']}`")
            md.append(f"  - report: `{r['report_dir']}`")
        md.append("")

    md.append("## Current PASS")
    md.append("")
    for r in good:
        md.append(f"- `{r['key']}` — handoff line {r['line']}")

    (out_dir / "FALSE_PASS_REPORT.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return bad

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handoff", default="VISUAL_REPAIR_HANDOFF.md")
    ap.add_argument("--out-root", default=r"reports\qa\handoff_false_pass_audit")
    ap.add_argument("--include-open", action="store_true")
    args = ap.parse_args()

    handoff = ROOT / args.handoff
    if not handoff.exists():
        raise SystemExit(f"Missing handoff: {handoff}")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = ROOT / args.out_root / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    items = parse_handoff(handoff, args.include_open)
    if not items:
        raise SystemExit("No checklist keys found.")

    rows = []
    for n, item in enumerate(items, 1):
        print(f"[{n}/{len(items)}] {item['key']}")
        rows.append(run_item(item, out_dir))

    bad = write_reports(out_dir, items, rows)

    print("")
    print("DONE")
    print(f"OutDir: {out_dir}")
    print(f"Report: {out_dir / 'FALSE_PASS_REPORT.md'}")
    print(f"False PASS count: {len(bad)}")

    raise SystemExit(2 if bad else 0)

if __name__ == "__main__":
    main()