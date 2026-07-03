# Diff Confinement Report

Verdict: PASS
Base: `main`
Touched files: 12
Prohibited files: 0
Hunks outside block: 0

## Files
- PERMITTED: `VISUAL_QA_AGENT_PROTOCOL.md`
  - ok: `@@ -343,0 +344,4 @@ context is never closure evidence unless every technical gate below also passes.`
  - ok: `@@ -426,0 +431,6 @@ globally — only its use with QA/reference artifacts.`
  - ok: `@@ -437,0 +448,6 @@ is trivial surfaces, by an explicit, tested rule: empty-state views (name ends`
  - ok: `@@ -486 +502 @@ technical gates pass. There is no subjective or manual closure path — inspecti`
  - ok: `@@ -492 +508,3 @@ technical gates pass. There is no subjective or manual closure path — inspecti`
  - ok: `@@ -508 +526 @@ The closure note must record:`
  - ok: `@@ -517,0 +536,5 @@ exact key status in the JSON/MD report, not the global exit code.`
- PERMITTED: `VISUAL_REPAIR_HANDOFF.md`
  - ok: `@@ -68,0 +69,4 @@ Required Closure Evidence.`
  - ok: `@@ -370,0 +375,6 @@ globally — only its use with QA/reference artifacts.`
  - ok: `@@ -381,0 +392,6 @@ is trivial surfaces, by an explicit, tested rule: empty-state views (name ends`
  - ok: `@@ -543 +559 @@ technical gates pass. Inspection manual, "confirmación visual", panel review, o`
  - ok: `@@ -549 +565,3 @@ technical gates pass. Inspection manual, "confirmación visual", panel review, o`
  - ok: `@@ -565 +583 @@ The closure note must record:`
  - ok: `@@ -574,0 +593,5 @@ exact key status in the JSON/MD report, not the global exit code.`
- PERMITTED: `qa/anti_fraud_scan.py`
  - ok: `@@ -45,0 +46,6 @@ DEFAULT_ROOTS = ("app", "hub", "shared")`
  - ok: `@@ -84,0 +91,31 @@ PIXMAP_REFERENCE_TOKENS = (`
  - ok: `@@ -159,0 +197,71 @@ def _eval_static_literal(node: ast.AST) -> object | None:`
  - ok: `@@ -284,0 +393,114 @@ def scan_source(source: str, file_label: str) -> list[Violation]:`
  - ok: `@@ -293,0 +516,9 @@ def scan_file(path: Path, *, base: Path | None = None) -> list[Violation]:`
  - ok: `@@ -302,0 +534,9 @@ def scan_paths(roots, *, base: Path | None = None) -> list[Violation]:`
  - ok: `@@ -304,2 +544,8 @@ def main(argv: list[str] | None = None) -> int:`
  - ok: `@@ -309 +555,7 @@ def main(argv: list[str] | None = None) -> int:`
  - ok: `@@ -324,2 +576,8 @@ def main(argv: list[str] | None = None) -> int:`
  - ok: `@@ -331 +589 @@ def main(argv: list[str] | None = None) -> int:`
- PERMITTED: `qa/capture_v8.py`
  - ok: `@@ -1686,0 +1687,44 @@ def _git_metadata() -> dict[str, Any]:`
  - ok: `@@ -2307 +2351,8 @@ def _introspect_sidecar_path(out_dir: Path) -> Path:`
  - ok: `@@ -2324,0 +2376 @@ def _record_introspection(win, app_key: str, view_id: str, modo: str, out_dir: P`
  - ok: `@@ -2413 +2465,12 @@ def _grab_save(win, app_key: str, view_id: str, modo: str, res: str, out_dir: Pa`
  - ok: `@@ -2414,0 +2478 @@ def _grab_save(win, app_key: str, view_id: str, modo: str, res: str, out_dir: Pa`
  - ok: `@@ -2424,0 +2489,2 @@ def _grab_save(win, app_key: str, view_id: str, modo: str, res: str, out_dir: Pa`
  - ok: `@@ -2439,0 +2506 @@ def _grab_save(win, app_key: str, view_id: str, modo: str, res: str, out_dir: Pa`
  - ok: `@@ -2958,0 +3026 @@ def main() -> int:`
- PERMITTED: `qa/layered_visual_compare.py`
  - ok: `@@ -69,0 +70,2 @@ _TRIVIAL_EMPTY_VIEW_SUFFIX = "-empty"`
  - ok: `@@ -209,0 +212 @@ class LayeredResult:`
  - ok: `@@ -230,0 +234 @@ class LayeredResult:`
  - ok: `@@ -250,0 +255 @@ class LayeredResult:`
  - ok: `@@ -460,0 +466,5 @@ def compare_pair(`
  - ok: `@@ -467,0 +478,7 @@ def compare_pair(`
  - ok: `@@ -482,0 +500 @@ def compare_pair(`
  - ok: `@@ -965,0 +984,8 @@ def _is_suspicious_perfect_match(metrics: dict[str, Any], canonical_img: Image.I`
  - ok: `@@ -1109,0 +1136 @@ def _summary(results: list[LayeredResult]) -> dict[str, Any]:`
  - ok: `@@ -1115,0 +1143,2 @@ def _summary(results: list[LayeredResult]) -> dict[str, Any]:`
- PERMITTED: `qa/vas_gate.py`
  - ok: `@@ -20,0 +21 @@ import argparse`
  - ok: `@@ -25,0 +27 @@ DEFAULT_SIDECAR = Path("qa/_visual_auditor_spec/introspection.json")`
  - ok: `@@ -29,0 +32,49 @@ BLOCKING_SEVERITIES = {"high", "medium"}`
  - ok: `@@ -52 +103,89 @@ def _load_sidecar(path: Path) -> list[dict]:`
  - ok: `@@ -84,0 +224 @@ def _check_entry(entry: dict, key: str | None) -> list[str]:`
  - ok: `@@ -111 +251 @@ def validate(path: Path, key: str | None) -> bool:`
- PERMITTED: `tests/test_anti_fraud_scan.py`
  - ok: `@@ -7 +7 @@ from pathlib import Path`
  - ok: `@@ -185,0 +186,56 @@ def test_real_dbt_qt_modal_constants_pass():`
- PERMITTED: `tests/test_capture_v8_evidence.py`
  - ok: `@@ -75,0 +76,23 @@ def test_content_rich_png_stays_valid(tmp_path):`
- PERMITTED: `tests/test_handoff_false_pass_audit.py`
  - ok: `@@ -0,0 +1,111 @@`
- PERMITTED: `tests/test_suspicious_perfect_match.py`
  - ok: `@@ -118,0 +119,57 @@ def test_nontrivial_but_different_is_not_suspicious(tmp_path):`
- PERMITTED: `tests/test_vas_gate.py`
  - ok: `@@ -3,0 +4 @@ import json`
  - ok: `@@ -25,0 +27,17 @@ def _run_gate(sidecar_path: Path, key: str | None = None) -> subprocess.Complete`
  - ok: `@@ -26,0 +45,48 @@ def _write_sidecar(tmp_path: Path, entries: list) -> Path:`
  - ok: `@@ -159,0 +226,27 @@ def test_fail_missing_fail_count_key(tmp_path):`
- PERMITTED: `tools/qa/audit_handoff_false_pass.py`
  - ok: `@@ -0,0 +1,11 @@`
  - ok: `@@ -2 +12,0 @@ import argparse`
  - ok: `@@ -7 +17 @@ import sys`
  - ok: `@@ -8,0 +19 @@ from pathlib import Path`
  - ok: `@@ -9,0 +21,2 @@ from pathlib import Path`
  - ok: `@@ -14,9 +27,115 @@ OPEN_RE = re.compile(r"^\s*-\s*\[\s\]")`
  - ok: `@@ -24,3 +142,0 @@ def parse_handoff(path: Path, include_open: bool):`
  - ok: `@@ -28 +144,8 @@ def parse_handoff(path: Path, include_open: bool):`
  - ok: `@@ -29,0 +153,111 @@ def parse_handoff(path: Path, include_open: bool):`
  - ok: `@@ -31,142 +264,0 @@ def parse_handoff(path: Path, include_open: bool):`
  - ok: `@@ -175 +267 @@ if __name__ == "__main__":`
