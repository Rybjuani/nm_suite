"""
Cross-gate matrix: odiff FIDELITY_REPORT vs visual_auditor_spec report.

Classifies all 86 surfaces into:
  A. odiff PASS + VAS PASS
  B. odiff PASS + VAS FAIL   <- critical zone
  C. odiff FAIL + VAS PASS
  D. odiff FAIL + VAS FAIL
  E. missing / skipped / stale

Usage:
  python qa/_night_session/cross_gate_matrix.py
"""

import json
import csv
from pathlib import Path

PROJ = Path(__file__).resolve().parents[2]
FIDELITY = PROJ / "qa" / "_fidelity_diff" / "FIDELITY_REPORT.json"
VAS_REPORT = PROJ / "qa" / "_visual_auditor_spec" / "report.json"
OUT_DIR = Path(__file__).resolve().parent
CSV_OUT = OUT_DIR / "cross_gate_matrix.csv"
MD_OUT = OUT_DIR / "cross_gate_matrix.md"

KNOWN_FP = {
    "hub:detalle-resumen-ia-0@dark",
    "hub:detalle-resumen-ia-0@light",
    "suite:dbt-practice-stop@light",
}

PRELIM_STRUCTURAL = {
    "suite:registro-step1-emotion@light",
    "suite:registro-step1-emotion@dark",
}

# Known dark-theme shadow/color noise pattern: VAS FAIL due to
# shadow/color theme differences that are likely calibration, not structural.
SHADOW_THEME_CANDIDATES = {
    "suite:home@dark",
    "suite:home-no-score@dark",
    "suite:avisos@dark",
    "suite:avisos-today@dark",
    "suite:dbt-now@dark",
    # Visually inspected 2026-06-26: same layout, only color calibration diff
    "suite:actividades-empty@light",
    "suite:rutina-empty@light",
    "suite:timer-empty@light",
    "suite:registro-success@dark",
    "suite:animo@dark",
    "suite:rutina-all-completed@dark",
}


def load_fidelity():
    data = json.loads(FIDELITY.read_text(encoding="utf-8"))
    index = {}
    for row in data:
        app = row["app"]
        view = row["view"]
        theme = row["theme"]
        key = f"{app}:{view}@{theme}"
        index[key] = {
            "odiff_status": row["status"],
            "diff_percentage": row.get("diff_percentage", 0.0),
        }
    return index


def load_vas():
    data = json.loads(VAS_REPORT.read_text(encoding="utf-8"))
    index = {}
    for row in data:
        key = row["surface_key"]
        index[key] = {
            "vas_pass": row["pass_count"],
            "vas_fail": row["fail_count"],
            "canonical": row.get("canonical", False),
            "divergences": row.get("divergences", []),
            "summary": row.get("summary", ""),
        }
    return index


def classify_preliminary(key, odiff, vas):
    """Return preliminary classification string."""
    if key in PRELIM_STRUCTURAL:
        return "estructural_confirmada"
    if key in KNOWN_FP:
        return "FP_conocido"
    if key in SHADOW_THEME_CANDIDATES:
        return "color/shadow theme"

    kinds = {d["kind"] for d in vas.get("divergences", [])}
    max_delta = max(
        (d["evidence"]["delta"] for d in vas.get("divergences", []) if "evidence" in d and "delta" in d["evidence"]),
        default=0.0,
    )
    severities = {d.get("severity", "") for d in vas.get("divergences", [])}

    if "LAYOUT_MISMATCH" in kinds:
        return "estructural_probable"
    if max_delta > 60:
        return "color/shadow theme"
    if max_delta > 30 and "high" in severities:
        return "color/shadow theme"
    if "SHADOW_MISMATCH" in kinds and kinds == {"SHADOW_MISMATCH"}:
        return "detector_noise_probable"
    if max_delta < 10:
        return "detector_noise_probable"
    return "requiere_inspeccion_visual"


def main():
    odiff_idx = load_fidelity()
    vas_idx = load_vas()

    all_keys = sorted(set(odiff_idx) | set(vas_idx))

    rows = []
    for key in all_keys:
        odiff = odiff_idx.get(key)
        vas = vas_idx.get(key)

        odiff_status = odiff["odiff_status"] if odiff else "MISSING"
        diff_pct = odiff["diff_percentage"] if odiff else None

        if vas:
            vas_pass = vas["vas_pass"]
            vas_fail = vas["vas_fail"]
            vas_status = "PASS" if vas_fail == 0 else "FAIL"
        else:
            vas_pass = None
            vas_fail = None
            vas_status = "MISSING"

        if odiff_status == "MISSING" or vas_status == "MISSING":
            cat = "E"
        elif odiff_status == "PASS" and vas_status == "PASS":
            cat = "A"
        elif odiff_status == "PASS" and vas_status == "FAIL":
            cat = "B"
        elif odiff_status == "FAIL" and vas_status == "PASS":
            cat = "C"
        else:
            cat = "D"

        prelim = ""
        if cat == "B" and vas:
            prelim = classify_preliminary(key, odiff or {}, vas)

        div_summary = ""
        if vas and vas.get("divergences"):
            parts = []
            for d in vas["divergences"]:
                delta = d.get("evidence", {}).get("delta", "?")
                if isinstance(delta, float):
                    delta = f"{delta:.1f}"
                parts.append(f"{d['kind']}({d['component_id']},Δ={delta})")
            div_summary = "; ".join(parts)

        rows.append({
            "surface": key,
            "app": key.split(":")[0],
            "theme": key.split("@")[-1],
            "category": cat,
            "odiff_status": odiff_status,
            "diff_pct": diff_pct,
            "vas_pass": vas_pass,
            "vas_fail": vas_fail,
            "divergences": div_summary,
            "prelim_classification": prelim,
        })

    # Summary counts
    cat_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
    for r in rows:
        cat_counts[r["category"]] += 1

    total = len(rows)

    # Write CSV
    fieldnames = ["surface", "app", "theme", "category", "odiff_status",
                  "diff_pct", "vas_pass", "vas_fail", "divergences", "prelim_classification"]
    with open(CSV_OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"[CSV] {CSV_OUT}")

    # Category B detail: sorted by vas_fail desc, then diff_pct asc (most missed)
    cat_b = sorted(
        [r for r in rows if r["category"] == "B"],
        key=lambda r: (-r["vas_fail"], r["diff_pct"] or 0),
    )

    # Write MD
    lines = ["# Cross-Gate Matrix: odiff vs VAS\n"]
    lines.append(f"**Total surfaces:** {total}\n")
    lines.append("## Summary\n")
    lines.append("| Category | Count | Description |")
    lines.append("|----------|-------|-------------|")
    lines.append(f"| A | {cat_counts['A']} | odiff PASS + VAS PASS |")
    lines.append(f"| B | {cat_counts['B']} | odiff PASS + VAS FAIL ← CRITICAL |")
    lines.append(f"| C | {cat_counts['C']} | odiff FAIL + VAS PASS |")
    lines.append(f"| D | {cat_counts['D']} | odiff FAIL + VAS FAIL |")
    lines.append(f"| E | {cat_counts['E']} | missing / skipped |")
    lines.append("")

    lines.append("## Full Matrix\n")
    lines.append("| Surface | Cat | odiff | diff% | VAS pass | VAS fail | Classification |")
    lines.append("|---------|-----|-------|-------|----------|----------|----------------|")
    for r in rows:
        dp = f"{r['diff_pct']:.2f}" if r["diff_pct"] is not None else "—"
        vp = str(r["vas_pass"]) if r["vas_pass"] is not None else "—"
        vf = str(r["vas_fail"]) if r["vas_fail"] is not None else "—"
        pc = r["prelim_classification"] or "—"
        lines.append(f"| {r['surface']} | **{r['category']}** | {r['odiff_status']} | {dp} | {vp} | {vf} | {pc} |")
    lines.append("")

    lines.append("## Category B — odiff PASS + VAS FAIL (critical zone)\n")
    lines.append(f"Total: **{cat_counts['B']}** surfaces\n")
    lines.append("| # | Surface | diff% | VAS fail | Classification | Divergences |")
    lines.append("|---|---------|-------|----------|----------------|-------------|")
    for i, r in enumerate(cat_b, 1):
        dp = f"{r['diff_pct']:.2f}" if r["diff_pct"] is not None else "—"
        lines.append(f"| {i} | {r['surface']} | {dp} | {r['vas_fail']} | {r['prelim_classification']} | {r['divergences']} |")
    lines.append("")

    lines.append("## Top 10 Critical Surfaces\n")
    lines.append("Criteria: category B, sorted by VAS fail count desc, then diff% asc\n")
    lines.append("| # | Surface | diff% | VAS fail | Classification |")
    lines.append("|---|---------|-------|----------|----------------|")
    for i, r in enumerate(cat_b[:10], 1):
        dp = f"{r['diff_pct']:.2f}" if r["diff_pct"] is not None else "—"
        lines.append(f"| {i} | {r['surface']} | {dp} | {r['vas_fail']} | {r['prelim_classification']} |")
    lines.append("")

    md_content = "\n".join(lines) + "\n"
    MD_OUT.write_text(md_content, encoding="utf-8")
    print(f"[MD]  {MD_OUT}")

    # Print summary to stdout
    print(f"\n=== CROSS-GATE MATRIX SUMMARY ({total} surfaces) ===")
    print(f"  A  odiff PASS + VAS PASS:  {cat_counts['A']}")
    print(f"  B  odiff PASS + VAS FAIL:  {cat_counts['B']}  <- CRITICAL")
    print(f"  C  odiff FAIL + VAS PASS:  {cat_counts['C']}")
    print(f"  D  odiff FAIL + VAS FAIL:  {cat_counts['D']}")
    print(f"  E  missing/skipped:        {cat_counts['E']}")
    print(f"\n=== CATEGORY B DETAIL (odiff PASS + VAS FAIL) ===")
    for i, r in enumerate(cat_b, 1):
        dp = f"{r['diff_pct']:.2f}%" if r["diff_pct"] is not None else "—"
        print(f"  {i:2}. {r['surface']:<55} diff={dp:<8} VAS_fail={r['vas_fail']}  [{r['prelim_classification']}]")

    print(f"\n=== TOP 10 CRITICAL ===")
    for i, r in enumerate(cat_b[:10], 1):
        dp = f"{r['diff_pct']:.2f}%" if r["diff_pct"] is not None else "—"
        print(f"  {i:2}. {r['surface']:<55} diff={dp:<8} VAS_fail={r['vas_fail']}  [{r['prelim_classification']}]")

    return cat_b


if __name__ == "__main__":
    main()
