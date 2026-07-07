#!/usr/bin/env python3
"""tools/visualparity/phase0b/validate_phase0b.py — Fase 0B governance validators.

Standalone stdlib-only validator for the V3.1 Fase 0A scaffold. Verifies that
the documentation and skeletons created in Fase 0A have not degraded and still
declare the invariants required by V3.1.

NO runtime authority. This validator does NOT close keys, does NOT invoke V1/V2,
does NOT invoke capture_v8, does NOT use pytest/pytestqt, does NOT depend on
PyQt6/.NET/Node/Playwright/GitHub Actions.

Usage:
    python tools/visualparity/phase0b/validate_phase0b.py

Exit codes:
    0  PASS — all groups passed
    1  FAIL — at least one group failed (errors listed)
    2  ERROR — internal error (e.g., repo root not found)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Callable

# ─── Locate repo root ──────────────────────────────────────────────────────
# This file lives at <repo-root>/tools/visualparity/phase0b/validate_phase0b.py
REPO_ROOT = Path(__file__).resolve().parents[3]


def _read(path: Path) -> str:
    """Read file as UTF-8 text. Raises if missing."""
    if not path.exists():
        raise FileNotFoundError(f"required file missing: {path}")
    return path.read_text(encoding="utf-8")


def _read_opt(path: Path) -> str | None:
    """Read file as UTF-8 text, or None if missing."""
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


# ─── Validator framework ───────────────────────────────────────────────────
class Validator:
    def __init__(self) -> None:
        self.groups: list[tuple[str, list[str]]] = []
        self.errors: list[str] = []
        self.current_group: str = ""

    def group(self, name: str) -> None:
        self.current_group = name
        self.groups.append((name, []))

    def check(self, condition: bool, msg: str) -> None:
        # Find the current group's error list (last appended)
        if not self.groups or self.groups[-1][0] != self.current_group:
            # defensive: shouldn't happen if group() called first
            self.group(self.current_group)
        if not condition:
            self.groups[-1][1].append(msg)
            self.errors.append(f"[{self.current_group}] {msg}")

    def summary(self) -> int:
        print()
        print("=" * 72)
        print("Fase 0B — Governance Validators")
        print("=" * 72)
        total_groups = len(self.groups)
        passed_groups = sum(1 for _, errs in self.groups if not errs)
        for name, errs in self.groups:
            status = "PASS" if not errs else "FAIL"
            print(f"  {status}  {name}  ({len(errs)} error{'s' if len(errs) != 1 else ''})")
            for e in errs:
                print(f"        - {e}")
        print("-" * 72)
        print(f"Groups: {passed_groups}/{total_groups} passed, "
              f"{total_groups - passed_groups} failed, "
              f"{len(self.errors)} total errors")
        print("=" * 72)
        return 0 if not self.errors else 1


# ─── Group A: Existence of Fase 0A files ───────────────────────────────────
DOCS_V31 = Path("docs/VisualParity_V3_1")
REQUIRED_FILES = [
    DOCS_V31 / "README.md",
    DOCS_V31 / "MIGRATION_A_PLUS.md",
    DOCS_V31 / "ARCHITECTURE.md",
    DOCS_V31 / "THREAT_MODEL.md",
    DOCS_V31 / "POLICY.md",
    DOCS_V31 / "CORPUS.md",
    DOCS_V31 / "PHASE_0A_DECISIONS.md",
    DOCS_V31 / "CANON_RECONCILIATION_PLAN.md",
    DOCS_V31 / "CAPTURE_V8_TRANSITION.md",
    DOCS_V31 / "CHANGELOG.md",
    Path("tools/visualparity/README.md"),
    Path("tools/visualparity/visualparity.lock.example.json"),
    Path("harness/v3/README.md"),
    Path("harness/v3/policy/closure_policy_v3.example.yaml"),
    Path("harness/v3/policy/measurement_config_v3.example.yaml"),
    Path("harness/v3/schemas/README.md"),
    Path("harness/v3/agent_runner/denylist.example.yaml"),
]


def group_a(v: Validator) -> None:
    v.group("A. Existence of Fase 0A files")
    for rel in REQUIRED_FILES:
        path = REPO_ROOT / rel
        v.check(path.exists(), f"missing required file: {rel}")


# ─── Group B: Skeleton authority ───────────────────────────────────────────
SKELETON_FILES = [
    Path("tools/visualparity/README.md"),
    Path("tools/visualparity/visualparity.lock.example.json"),
    Path("harness/v3/README.md"),
    Path("harness/v3/policy/closure_policy_v3.example.yaml"),
    Path("harness/v3/policy/measurement_config_v3.example.yaml"),
    Path("harness/v3/schemas/README.md"),
    Path("harness/v3/agent_runner/denylist.example.yaml"),
]


def group_b(v: Validator) -> None:
    v.group("B. Skeleton authority (fase marker + no runtime authority)")
    # Accept any fase marker (Fase 0A, Fase 0B, ..., Fase 1, Fase 2, etc.)
    # The key invariant is "no runtime authority" + a declared fase.
    import re as _re
    fase_re = _re.compile(r"Fase\s+0[A-Z]?\b|Fase\s+[1-9]\b", _re.IGNORECASE)
    for rel in SKELETON_FILES:
        path = REPO_ROOT / rel
        content = _read_opt(path)
        if content is None:
            v.check(False, f"cannot read skeleton (missing): {rel}")
            continue
        v.check(fase_re.search(content) is not None,
                f"skeleton missing fase marker (Fase 0A/0B/.../1/2/...): {rel}")
        v.check("no runtime authority" in content.lower(),
                f"skeleton missing 'no runtime authority' marker: {rel}")


# ─── Group C: No-go text declarations ──────────────────────────────────────
# Each entry: (substring, human description). Checked against README.md and
# POLICY.md (the canonical declaration files). Other docs may also contain them
# but we validate the canonical sources.
NO_GO_DECLARATIONS = [
    ("Rybjuani/visualparity", "no repo Rybjuani/visualparity"),
    ("nm_suite", "V3.1 lives in nm_suite"),
    ("tools/visualparity/", "VisualParity in tools/visualparity/"),
    ("harness/v3/", "harness in harness/v3/"),
    (".NET 8", "Core/CLI .NET 8 first"),
    ("WPF", "WPF after (not WinUI)"),
    ("WinUI", "WinUI explicitly excluded"),
    ("LOW_DIFF", "LOW_DIFF mentioned (to enforce no-close)"),
    ("HIGH_DIFF", "HIGH_DIFF mentioned (to enforce no-override)"),
    ("review_annotation.json", "UI only produces review_annotation.json"),
    ("HUMAN_REVIEWED_PASS", "bulk HUMAN_REVIEWED_PASS prohibited"),
    ("CI", "CI mentioned (to enforce only-blocks)"),
    ("recaptura", "replay requires recapture"),
    ("--no-regen", "--no-regen prohibited as closure"),
    ("signature.sha256", "no signature.sha256 as signature"),
    ("cobertura inicial de vectores conocidos",
     "anti-fraud = cobertura inicial de vectores conocidos, not total"),
]

NO_GO_CANONICAL_FILES = [
    DOCS_V31 / "README.md",
    DOCS_V31 / "POLICY.md",
    DOCS_V31 / "ARCHITECTURE.md",
    DOCS_V31 / "THREAT_MODEL.md",
]


def group_c(v: Validator) -> None:
    v.group("C. No-go text declarations")
    # Build a combined corpus of the canonical declaration files
    combined = ""
    for rel in NO_GO_CANONICAL_FILES:
        path = REPO_ROOT / rel
        content = _read_opt(path)
        if content is None:
            v.check(False, f"cannot read canonical file: {rel}")
            continue
        combined += "\n" + content
    for substr, desc in NO_GO_DECLARATIONS:
        v.check(substr in combined, f"missing declaration: {desc}")


# ─── Group D: State separation ─────────────────────────────────────────────
VP_ALLOWED_STATES = [
    "NO_DIFF", "LOW_DIFF", "SUSPICIOUS", "HIGH_DIFF", "MISSING_PAIR",
    "SIZE_MISMATCH", "NEAR_THRESHOLD", "NON_DETERMINISTIC",
    "MEASUREMENT_DISPUTE_CANDIDATE",
]
VP_PROHIBITED_STATES = [
    "CLOSURE_ALLOWED", "BLOCK", "CLOSURE_PASS",
    "HUMAN_REVIEWED_PASS", "HUMAN_REVIEWED_FAIL",
]


def group_d(v: Validator) -> None:
    v.group("D. State separation (VisualParity allowed vs prohibited)")
    arch = _read_opt(REPO_ROOT / DOCS_V31 / "ARCHITECTURE.md")
    if arch is None:
        v.check(False, "cannot read ARCHITECTURE.md")
        return
    # Allowed states: must be listed as "permitidos" or "allowed"
    for state in VP_ALLOWED_STATES:
        v.check(state in arch,
                f"VisualParity allowed state not declared: {state}")
    # Prohibited states: must be declared as prohibited (not as VisualParity emissions)
    # The document must mention each prohibited state AND mark it as prohibited/forbidden
    for state in VP_PROHIBITED_STATES:
        v.check(state in arch,
                f"VisualParity prohibited state not mentioned: {state}")
    # Verify the word "prohibid" appears near the prohibited states section
    v.check("prohibid" in arch.lower(),
            "ARCHITECTURE.md must declare prohibited states (word 'prohibid')")


# ─── Group E: Policy example ───────────────────────────────────────────────
def group_e(v: Validator) -> None:
    v.group("E. Policy example (closure_policy_v3.example.yaml)")
    path = REPO_ROOT / "harness/v3/policy/closure_policy_v3.example.yaml"
    content = _read_opt(path)
    if content is None:
        v.check(False, "cannot read closure_policy_v3.example.yaml")
        return
    # LOW_DIFF -> HUMAN_REVIEW_REQUIRED
    # Match a rule block where state: LOW_DIFF is followed by action: HUMAN_REVIEW_REQUIRED
    low_diff_block = re.search(
        r"- state:\s*LOW_DIFF\s*\n\s*action:\s*(\w+)", content)
    if low_diff_block:
        action = low_diff_block.group(1)
        v.check(action == "HUMAN_REVIEW_REQUIRED",
                f"LOW_DIFF must map to HUMAN_REVIEW_REQUIRED, got: {action}")
    else:
        v.check(False, "LOW_DIFF rule not found in policy example")
    # HIGH_DIFF -> BLOCK
    high_diff_block = re.search(
        r"- state:\s*HIGH_DIFF\s*\n\s*action:\s*(\w+)", content)
    if high_diff_block:
        action = high_diff_block.group(1)
        v.check(action == "BLOCK",
                f"HIGH_DIFF must map to BLOCK, got: {action}")
    else:
        v.check(False, "HIGH_DIFF rule not found in policy example")
    # No LOW_DIFF: ALLOW_CLOSURE anywhere
    v.check("LOW_DIFF" not in content or "ALLOW_CLOSURE" not in
            re.search(r"- state:\s*LOW_DIFF.*?(?=- state:|\Z)", content,
                      re.DOTALL).group(0),
            "LOW_DIFF rule must NOT contain ALLOW_CLOSURE")
    # No owner override of HIGH_DIFF: search for "override" near HIGH_DIFF
    high_section = re.search(r"- state:\s*HIGH_DIFF.*?(?=- state:|\Z)",
                             content, re.DOTALL)
    if high_section:
        hs = high_section.group(0)
        # "override" should not appear as a positive action (only as prohibition)
        # We allow "no override" / "not override" / "MEASUREMENT_DISPUTE, not override"
        # Simplest: no line saying "action: ALLOW_CLOSURE" in HIGH_DIFF block
        v.check("ALLOW_CLOSURE" not in hs,
                "HIGH_DIFF block must NOT contain ALLOW_CLOSURE (no override)")
    # Bulk human pass prohibited
    v.check("bulk" in content.lower() and "HUMAN_REVIEWED_PASS" in content,
            "policy must address bulk HUMAN_REVIEWED_PASS")
    # --no-regen appears only as prohibition
    v.check("--no-regen" in content,
            "policy must mention --no-regen (as prohibition)")
    # Skeleton authority markers
    v.check("Fase 0A skeleton" in content,
            "policy example missing 'Fase 0A skeleton' marker")
    v.check("no runtime authority" in content,
            "policy example missing 'no runtime authority' marker")


# ─── Group F: Measurement config ───────────────────────────────────────────
def group_f(v: Validator) -> None:
    v.group("F. Measurement config (measurement_config_v3.example.yaml)")
    path = REPO_ROOT / "harness/v3/policy/measurement_config_v3.example.yaml"
    content = _read_opt(path)
    if content is None:
        v.check(False, "cannot read measurement_config_v3.example.yaml")
        return
    # Required measurement parameters
    v.check("near_threshold" in content.lower(),
            "measurement config must contain near_threshold")
    v.check("determinism" in content.lower(),
            "measurement config must contain determinism")
    # bbox / diff thresholds (allow either term)
    v.check("bbox" in content.lower() or "changed_pixel_ratio" in content.lower()
            or "mean_abs_diff" in content.lower(),
            "measurement config must contain bbox/diff thresholds")
    # Must NOT contain closure rules
    # Closure rules would look like "action: ALLOW_CLOSURE" or "action: BLOCK"
    v.check("ALLOW_CLOSURE" not in content,
            "measurement config must NOT contain closure rules (ALLOW_CLOSURE)")
    v.check(re.search(r"action:\s*BLOCK", content) is None,
            "measurement config must NOT contain closure rules (action: BLOCK)")
    # Skeleton authority markers
    v.check("Fase 0A skeleton" in content,
            "measurement config missing 'Fase 0A skeleton' marker")
    v.check("no runtime authority" in content,
            "measurement config missing 'no runtime authority' marker")


# ─── Group G: Denylist example ─────────────────────────────────────────────
def group_g(v: Validator) -> None:
    v.group("G. Denylist example (denylist.example.yaml)")
    path = REPO_ROOT / "harness/v3/agent_runner/denylist.example.yaml"
    content = _read_opt(path)
    if content is None:
        v.check(False, "cannot read denylist.example.yaml")
        return
    # Required prohibitions
    prohibitions = [
        ("close_visual_key", "invoke V1 closer"),
        ("layered_visual_compare", "invoke V1 comparator"),
        ("replay_visual_closure", "invoke V1 replay"),
        ("harness/", "invoke V2 legacy (harness/ root)"),
        ("--no-regen", "use --no-regen"),
        ("bulk", "bulk human pass"),
        ("evidence_records", "edit evidence records manually"),
        ("_mockup_canonical", "edit canon without authorization"),
    ]
    for substr, desc in prohibitions:
        v.check(substr in content, f"denylist missing prohibition: {desc}")
    # Skeleton authority markers
    v.check("Fase 0A skeleton" in content,
            "denylist missing 'Fase 0A skeleton' marker")
    v.check("no runtime authority" in content,
            "denylist missing 'no runtime authority' marker")


# ─── Group H: A+ migration ─────────────────────────────────────────────────
def group_h(v: Validator) -> None:
    v.group("H. A+ migration (MIGRATION_A_PLUS.md)")
    path = REPO_ROOT / DOCS_V31 / "MIGRATION_A_PLUS.md"
    content = _read_opt(path)
    if content is None:
        v.check(False, "cannot read MIGRATION_A_PLUS.md")
        return
    required = [
        ("forensic-pre-v3.1", "tag forensic-pre-v3.1"),
        ("git bundle", "git bundle externo"),
        ("sha256", "SHA256 del bundle"),
        ("MANIFEST puntero", "MANIFEST/README puntero"),
        ("docs/_archive/", "docs/_archive/ mentioned"),
        ("no ejecutable", "no ejecutable in _archive (or equivalent)"),
    ]
    for substr, desc in required:
        v.check(substr.lower() in content.lower(),
                f"MIGRATION_A_PLUS.md missing: {desc}")
    # No V1/V2 scripts/evidence/tarballs in main
    v.check("scripts" in content.lower() or "código" in content.lower()
            or "V1/V2 código" in content,
            "MIGRATION_A_PLUS.md must address V1/V2 código not in main")
    # Release asset or storage owner
    v.check("release asset" in content.lower() or "storage owner" in content.lower()
            or "GitHub Release" in content,
            "MIGRATION_A_PLUS.md must mention release asset or storage owner")


# ─── Group I: Capture V8 transition ────────────────────────────────────────
def group_i(v: Validator) -> None:
    v.group("I. Capture V8 transition (CAPTURE_V8_TRANSITION.md)")
    path = REPO_ROOT / DOCS_V31 / "CAPTURE_V8_TRANSITION.md"
    content = _read_opt(path)
    if content is None:
        v.check(False, "cannot read CAPTURE_V8_TRANSITION.md")
        return
    required = [
        ("capture_orchestrator.py", "only capture_orchestrator.py invokes capture_v8"),
        ("VisualParity", "VisualParity mentioned (cannot invoke)"),
        ("--introspect", "--introspect disabled"),
        ("vas_introspect", "vas_introspect audit requirement"),
    ]
    for substr, desc in required:
        v.check(substr in content, f"CAPTURE_V8_TRANSITION.md missing: {desc}")
    # VisualParity cannot invoke capture_v8: look for explicit statement
    v.check("no puede" in content.lower() or "cannot" in content.lower()
            or "no lo invoca" in content.lower(),
            "CAPTURE_V8_TRANSITION.md must declare VisualParity cannot invoke capture_v8")


# ─── Group J: Canon reconciliation ─────────────────────────────────────────
def group_j(v: Validator) -> None:
    v.group("J. Canon reconciliation (CANON_RECONCILIATION_PLAN.md)")
    path = REPO_ROOT / DOCS_V31 / "CANON_RECONCILIATION_PLAN.md"
    content = _read_opt(path)
    if content is None:
        v.check(False, "cannot read CANON_RECONCILIATION_PLAN.md")
        return
    required = [
        ("pack canonico", "pack canonico mentioned"),
        ("_mockup_canonical", "_mockup_canonical mentioned"),
        ("paths relativos", "paths relativos (canon único)"),
        ("sha256", "sha256 raw bytes comparison"),
    ]
    for substr, desc in required:
        v.check(substr in content, f"CANON_RECONCILIATION_PLAN.md missing: {desc}")
    # No eliminar in Fase 0A/0B
    v.check("no se elimina" in content.lower() or "no eliminar" in content.lower()
            or "intactos" in content.lower(),
            "CANON_RECONCILIATION_PLAN.md must declare no elimination in 0A/0B")
    # Migrar assets únicos antes de eliminar duplicados
    v.check("assets únicos" in content.lower() or "migrar" in content.lower(),
            "CANON_RECONCILIATION_PLAN.md must address migrating unique assets before elimination")


# ─── Group K: Owner decisions ──────────────────────────────────────────────
OWNER_DECISIONS_REQUIRED = [
    "bundle forense",
    "capture_v8",
    "vas_introspect",
    "handoff",
    "tessdata",
    "self-hosted",
    "stack VisualParity",
    "WORKER_VISUAL_QA_FLOW",
    "timing migración",
    "116 closures",
    "canon reconcil",
]


def group_k(v: Validator) -> None:
    v.group("K. Owner decisions (PHASE_0A_DECISIONS.md)")
    path = REPO_ROOT / DOCS_V31 / "PHASE_0A_DECISIONS.md"
    content = _read_opt(path)
    if content is None:
        v.check(False, "cannot read PHASE_0A_DECISIONS.md")
        return
    content_lower = content.lower()
    for desc in OWNER_DECISIONS_REQUIRED:
        v.check(desc.lower() in content_lower,
                f"PHASE_0A_DECISIONS.md missing decision: {desc}")


# ─── Group L: No runtime leakage ───────────────────────────────────────────
def group_l(v: Validator) -> None:
    v.group("L. No runtime leakage (Fase 0B scope)")
    # This validator must be the only .py under tools/visualparity/phase0b/
    phase0b_dir = REPO_ROOT / "tools/visualparity/phase0b"
    if not phase0b_dir.exists():
        v.check(False, "tools/visualparity/phase0b/ does not exist")
        return
    py_files = list(phase0b_dir.glob("*.py"))
    py_names = {p.name for p in py_files}
    v.check(py_names == {"validate_phase0b.py"},
            f"phase0b/ must contain only validate_phase0b.py, found: {sorted(py_names)}")
    # .cs files allowed ONLY under tools/visualparity/src/ and tools/visualparity/tests/
    # (Fase 1 added VisualParity Core/CLI .NET 8 code). Forbidden elsewhere under
    # tools/visualparity/ (e.g., phase0b/, phase0d/).
    cs_files = list((REPO_ROOT / "tools/visualparity").rglob("*.cs"))
    cs_outside_src_tests = [
        p for p in cs_files
        if "src/" not in str(p.relative_to(REPO_ROOT)).replace("\\", "/")
        and "tests/" not in str(p.relative_to(REPO_ROOT)).replace("\\", "/")
    ]
    v.check(not cs_outside_src_tests,
            f".cs files only allowed under tools/visualparity/src/ or tests/, "
            f"found outside: {[str(p.relative_to(REPO_ROOT)) for p in cs_outside_src_tests]}")
    # Workflows: the legacy V1 visual-closure-replay.yml is untouched, and the
    # Fase 0C governance smoke visual-parity-v3-governance.yml is the only new
    # workflow allowed. Any other workflow is unexpected.
    workflows_dir = REPO_ROOT / ".github/workflows"
    if workflows_dir.exists():
        workflows = sorted(workflows_dir.glob("*.yml")) + sorted(workflows_dir.glob("*.yaml"))
        workflow_names = {p.name for p in workflows}
        expected = {
            "visual-closure-replay.yml",          # legacy V1, untouched
            "visual-parity-v3-governance.yml",    # Fase 0C governance smoke
        }
        unexpected = workflow_names - expected
        v.check(not unexpected,
                f"unexpected workflows found (only legacy + governance smoke allowed): {sorted(unexpected)}")
    # Structural check: the validator must not IMPORT any forbidden module.
    # We scan only import statements (not arbitrary string mentions, since the
    # validator legitimately references V1/V2 names as forbidden tokens in
    # documentation strings and denylist validation logic).
    self_content = _read(Path(__file__))
    import_lines = [
        line.strip() for line in self_content.splitlines()
        if line.lstrip().startswith("import ") or line.lstrip().startswith("from ")
    ]
    forbidden_imports = ["pytest", "pytestqt", "PyQt6", "PyQt5", "PySide",
                         "playwright", "subprocess"]
    for imp in forbidden_imports:
        hits = [l for l in import_lines if re.search(rf"\b{re.escape(imp)}\b", l)]
        v.check(not hits,
                f"validator must not import {imp} (found: {hits[:1]})")


# ─── Group M: Fase 0D docs and scripts ─────────────────────────────────────
PHASE_0D_REQUIRED_DOCS = [
    DOCS_V31 / "OWNER_DECISIONS_LOCKED.md",
    DOCS_V31 / "FORENSIC_SNAPSHOT_PREFLIGHT.md",
    DOCS_V31 / "MIGRATION_A_PLUS_EXECUTION_PLAN.md",
    DOCS_V31 / "PHASE_0D_CHECKLIST.md",
]
PHASE_0D_REQUIRED_SCRIPTS = [
    Path("tools/visualparity/phase0d/preflight_snapshot_dry_run.ps1"),
    Path("tools/visualparity/phase0d/README.md"),
]


def group_m(v: Validator) -> None:
    v.group("M. Fase 0D docs and scripts existence")
    for rel in PHASE_0D_REQUIRED_DOCS:
        path = REPO_ROOT / rel
        v.check(path.exists(), f"missing Fase 0D doc: {rel}")
    for rel in PHASE_0D_REQUIRED_SCRIPTS:
        path = REPO_ROOT / rel
        v.check(path.exists(), f"missing Fase 0D script: {rel}")
    # Validate OWNER_DECISIONS_LOCKED.md contains the 5 LOCKED decisions
    locked_path = REPO_ROOT / DOCS_V31 / "OWNER_DECISIONS_LOCKED.md"
    locked_content = _read_opt(locked_path)
    if locked_content:
        for lock_id in ["LOCK-1", "LOCK-2", "LOCK-3", "LOCK-4", "LOCK-5"]:
            v.check(lock_id in locked_content,
                    f"OWNER_DECISIONS_LOCKED.md missing {lock_id}")
        v.check("LOCKED_FOR_V3_1" in locked_content,
                "OWNER_DECISIONS_LOCKED.md missing LOCKED_FOR_V3_1 section")
        v.check("STILL_OWNER_DECISION_REQUIRED" in locked_content,
                "OWNER_DECISIONS_LOCKED.md missing STILL_OWNER_DECISION_REQUIRED section")
    # Validate FORENSIC_SNAPSHOT_PREFLIGHT.md marks commands FUTURE_PHASE_ONLY
    preflight_path = REPO_ROOT / DOCS_V31 / "FORENSIC_SNAPSHOT_PREFLIGHT.md"
    preflight_content = _read_opt(preflight_path)
    if preflight_content:
        v.check("FUTURE_PHASE_ONLY" in preflight_content,
                "FORENSIC_SNAPSHOT_PREFLIGHT.md must mark commands FUTURE_PHASE_ONLY")
        v.check("DO NOT RUN IN PHASE 0D" in preflight_content
                or "no ejecuta" in preflight_content.lower(),
                "FORENSIC_SNAPSHOT_PREFLIGHT.md must declare Fase 0D does not execute")
    # Validate MIGRATION_A_PLUS_EXECUTION_PLAN.md has 8 steps
    plan_path = REPO_ROOT / DOCS_V31 / "MIGRATION_A_PLUS_EXECUTION_PLAN.md"
    plan_content = _read_opt(plan_path)
    if plan_content:
        for step in ["Paso 1", "Paso 2", "Paso 3", "Paso 4",
                     "Paso 5", "Paso 6", "Paso 7", "Paso 8"]:
            v.check(step in plan_content,
                    f"MIGRATION_A_PLUS_EXECUTION_PLAN.md missing {step}")
        v.check("FUTURE_PHASE_ONLY" in plan_content,
                "MIGRATION_A_PLUS_EXECUTION_PLAN.md must mark destructive commands FUTURE_PHASE_ONLY")


# ─── Main ──────────────────────────────────────────────────────────────────
def main() -> int:
    if not REPO_ROOT.exists():
        print(f"ERROR: repo root not found: {REPO_ROOT}", file=sys.stderr)
        return 2
    # Sanity: confirm we're at the right repo by checking for a known file
    sanity = REPO_ROOT / "docs/VisualParity_V3_1/README.md"
    if not sanity.exists():
        print(f"ERROR: not at expected repo root (missing {sanity})",
              file=sys.stderr)
        return 2

    v = Validator()
    groups: list[Callable[[Validator], None]] = [
        group_a, group_b, group_c, group_d, group_e, group_f,
        group_g, group_h, group_i, group_j, group_k, group_l, group_m,
    ]
    for g in groups:
        try:
            g(v)
        except Exception as e:
            v.check(False, f"exception in group: {e!r}")

    return v.summary()


if __name__ == "__main__":
    sys.exit(main())
