"""Governance contract tests for active Visual QA documentation.

Ensures:
1. Retired-tool references (V2/V3 Auditor, Sentinel, Coverage Gaps, etc.) do not
   appear in active docs (outside docs/_archive/).
2. Subjective closure criteria ("revisión manual", "confirmación visual",
   "inspección manual", "manual review", "human review", "owner acceptance",
   "looks good", "se ve bien", etc.) do not appear as VALID closure criteria in
   ANY active .md file — not just the protocol/handoff.
   Context-aware: phrases in negation/forbidden lists or historical evidence
   notes (checklist [x] items) are allowed; phrases presented as positive
   closure evidence are blocked.
3. docs/README.md is the canonical index and points to the two source-of-truth
   documents.
4. plan_reestructuracion_qa_nm_suite.md does not exist in the repo root.
5. Retired historical docs live under docs/_archive/ and not in docs/ root or qa/.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# Documents that are ACTIVE sources of truth (live in repo root, not docs/).
# VISUAL_QA_AGENT_PROTOCOL.md (v1, full protocol) was archived to
# docs/_archive/protocol_v1.md; WORKER_VISUAL_QA_FLOW.md is now the canonical
# worker entry-point (see docs/README.md).
ACTIVE_PROTOCOL_DOCS = [
    REPO_ROOT / "WORKER_VISUAL_QA_FLOW.md",
    REPO_ROOT / "VISUAL_REPAIR_HANDOFF.md",
]

ACTIVE_DOCS_DIR = REPO_ROOT / "docs"
ARCHIVE_DIR = ACTIVE_DOCS_DIR / "_archive"

# Retired tool / concept names that must not appear in ACTIVE docs.
RETIRED_REFS = [
    r"Visual Auditor V2",
    r"Visual Auditor V3",
    r"VISUAL_AUDITOR_V2",
    r"VISUAL_AUDITOR_V3",
    r"SENTINEL_REMOVAL",
    r"COVERAGE_GAPS",
    r"plan_reestructuracion",
    r"DISCREPANCIAS_SENTINEL",
]
RETIRED_RE = re.compile("|".join(RETIRED_REFS), re.IGNORECASE)

# Subjective closure phrases that must not appear as VALID/AFFIRMATIVE closure
# criteria anywhere in active docs. Case-insensitive match.
SUBJECTIVE_PHRASES = [
    "revisión manual",
    "revision manual",
    "confirmación visual",
    "confirmacion visual",
    "inspección manual",
    "inspeccion manual",
    "manual review",
    "manual side-by-side",
    "manual panel review",
    "manual panel",
    "human review",
    "owner acceptance",
    "looks good",
    "se ve bien",
]

# Negation context markers — if the line contains one of these, the subjective
# phrase is being listed as FORBIDDEN or explicitly rejected, not endorsed.
NEGATION_MARKERS = [
    "not ",
    "never",
    "forbidden",
    "prohibited",
    "prohibido",
    "no son",
    "no es",
    "no existe",
    "not valid",
    "not evidence",
    "must not",
    "do not",
    "are not",
    "cannot",
    "can never",
    "blocked",
    "invalid",
    "not a closure",
    "not closure",
    "must not be cited",
    "forbidden closure",
    "no autoriza",
    "not valid closure",
]

# Section headers that mark a forbidden/negation zone — lines under these
# headers are listing things that must NOT be done, so subjective phrases
# found there are allowed.
NEGATION_SECTION_HEADERS = [
    "forbidden closure",
    "forbidden closure reasons",
    "reset reason",
    "anti-fraud rule",
    "do not mark",
    "anti-patrones",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _all_active_md_files() -> list[Path]:
    """All tracked .md files outside docs/_archive/, .venv/, node_modules/, .git/."""
    result: list[Path] = []
    # Root .md files
    for f in REPO_ROOT.glob("*.md"):
        if f.is_file():
            result.append(f)
    # docs/*.md (not _archive)
    if ACTIVE_DOCS_DIR.exists():
        for f in ACTIVE_DOCS_DIR.glob("*.md"):
            if f.is_file():
                result.append(f)
    return sorted(set(result))


def _active_docs_files() -> list[Path]:
    """All .md files directly in docs/ (not in _archive/)."""
    if not ACTIVE_DOCS_DIR.exists():
        return []
    return [
        f for f in ACTIVE_DOCS_DIR.glob("*.md")
        if f.is_file() and "_archive" not in f.parts
    ]


def _strip_markdown_emphasis(text: str) -> str:
    """Remove markdown bold/italic markers so negation detection works."""
    return text.replace("*", "").replace("_", "")


def _is_negation_context(line: str, next_lines: list[str] | None = None) -> bool:
    """Check if a line is a negation/forbidden context.

    Also checks up to 2 following lines (for cases where a list of forbidden
    items spans multiple lines ending with 'or').
    """
    lower = _strip_markdown_emphasis(line).lower()
    if any(marker in lower for marker in NEGATION_MARKERS):
        return True
    # Check following lines for continuation (e.g., line ends with "or")
    if next_lines:
        for nl in next_lines[:2]:
            nl_lower = _strip_markdown_emphasis(nl).lower()
            if any(marker in nl_lower for marker in NEGATION_MARKERS):
                return True
            # If the continuation line is a new bullet/heading, stop
            if nl_lower.startswith("- ") or nl_lower.startswith("#"):
                break
    return False


def _is_historical_evidence_note(line: str, all_lines: list[str], idx: int) -> bool:
    """Check if a line is inside a historical evidence note for a closed checklist item.

    Historical evidence notes are indented sub-bullets under [x] checklist items.
    They record what was done in the past; they are not active criteria. Rewriting
    them would falsify history. We detect them by: line starts with whitespace
    and the nearest preceding checklist line is [x] (closed).
    """
    if not line.startswith(" ") and not line.startswith("\t"):
        return False
    stripped = line.strip()
    if not stripped:
        return False
    # Walk backwards to find the nearest checklist item
    for j in range(idx - 1, max(idx - 80, -1), -1):
        if j < 0:
            continue
        prev = all_lines[j].strip()
        if prev.startswith("- [x]"):
            return True
        if prev.startswith("- [ ]"):
            return False
        if prev.startswith("###") or prev.startswith("##"):
            return False
    return False


def _is_in_negation_section(all_lines: list[str], idx: int) -> bool:
    """Check if the line is inside a negation/forbidden section."""
    for j in range(idx, max(idx - 80, -1), -1):
        if j < 0:
            continue
        line_lower = all_lines[j].lower()
        if any(line_lower.startswith(f"# {h}") or line_lower.startswith(f"## {h}") or line_lower.startswith(f"### {h}") for h in NEGATION_SECTION_HEADERS):
            return True
        # Also match headers that contain the header text
        if line_lower.startswith("#") and any(h in line_lower for h in NEGATION_SECTION_HEADERS):
            return True
    return False


def _find_subjective_violations(content: str) -> list[tuple[int, str, str]]:
    """Return list of (line_number, phrase, line_content) for subjective phrases
    used in AFFIRMATIVE closure context (not negation, not historical note)."""
    lines = content.splitlines()
    violations: list[tuple[int, str, str]] = []
    in_negation_zone = False
    for i, line in enumerate(lines):
        lower = line.lower()
        # Track negation section headers dynamically
        if lower.startswith("#") and any(h in lower for h in NEGATION_SECTION_HEADERS):
            in_negation_zone = True
        elif lower.startswith("## ") or lower.startswith("# "):
            in_negation_zone = False

        for phrase in SUBJECTIVE_PHRASES:
            if phrase in lower:
                next_lines = lines[i + 1:] if i + 1 < len(lines) else []
                if _is_negation_context(line, next_lines):
                    continue
                if _is_historical_evidence_note(line, lines, i):
                    continue
                if in_negation_zone:
                    continue
                violations.append((i + 1, phrase, line.strip()))
    return violations


# ─── Retired references ─────────────────────────────────────────────────────


class TestRetiredReferences:
    """No retired-tool references in active docs."""

    @pytest.mark.parametrize("doc_path", ACTIVE_PROTOCOL_DOCS + [
        ACTIVE_DOCS_DIR / "README.md",
    ])
    def test_protocol_and_readme_no_retired_refs(self, doc_path):
        if not doc_path.exists():
            pytest.fail(f"Active doc missing: {doc_path}")
        content = _read(doc_path)
        matches = RETIRED_RE.findall(content)
        assert not matches, (
            f"{doc_path.name} contains retired-tool references: {set(matches)}"
        )

    @pytest.mark.parametrize("doc_path", _active_docs_files())
    def test_active_docs_dir_no_retired_refs(self, doc_path):
        content = _read(doc_path)
        matches = RETIRED_RE.findall(content)
        assert not matches, (
            f"{doc_path.name} contains retired-tool references: {set(matches)}"
        )


# ─── Subjective closure criteria (ALL active .md) ──────────────────────────


class TestSubjectiveClosureAbsent:
    """No subjective/manual closure criteria used affirmatively in ANY active doc.

    Scans every active .md file (root + docs/, excluding _archive/).
    Context-aware: phrases inside negation/forbidden lists or historical
    evidence notes (under [x] checklist items) are allowed.
    """

    @pytest.mark.parametrize("doc_path", _all_active_md_files())
    def test_no_subjective_closure_affirmative(self, doc_path):
        content = _read(doc_path)
        violations = _find_subjective_violations(content)
        if violations:
            detail = "; ".join(
                f"L{ln} [{phrase}]: {text[:100]}" for ln, phrase, text in violations
            )
            pytest.fail(
                f"{doc_path.name}: subjective closure phrase(s) in affirmative context: {detail}"
            )

    @pytest.mark.parametrize("doc_path", ACTIVE_PROTOCOL_DOCS)
    def test_closure_sections_have_vas_gate(self, doc_path):
        """Closure evidence sections must reference the VAS gate requirement."""
        content = _read(doc_path)
        assert "vas_gate" in content.lower() or "vas gate" in content.lower(), (
            f"{doc_path.name} closure criteria must reference the VAS Gate"
        )

    @pytest.mark.parametrize("doc_path", ACTIVE_PROTOCOL_DOCS)
    def test_closure_requires_technical_gates(self, doc_path):
        """Closure sections must list mandatory technical PASS requirements."""
        content = _read(doc_path)
        assert (
            "PASS requirements" in content
            or "Closure Evidence" in content
            or "Criterio de PASS" in content
        ), (
            f"{doc_path.name} must define explicit PASS requirements"
        )
        assert "REPORT_EVIDENCE_VALID" in content, (
            f"{doc_path.name} must require REPORT_EVIDENCE_VALID"
        )
        assert "NM_VAS_INTROSPECT" in content, (
            f"{doc_path.name} must require NM_VAS_INTROSPECT=1"
        )


# ─── Canonical index ────────────────────────────────────────────────────────


class TestCanonicalIndex:
    def test_readme_is_canonical_index(self):
        readme = ACTIVE_DOCS_DIR / "README.md"
        assert readme.exists(), "docs/README.md must exist as canonical index"
        content = _read(readme)
        assert "WORKER_VISUAL_QA_FLOW.md" in content
        assert "VISUAL_REPAIR_HANDOFF.md" in content

    def test_readme_mentions_archive(self):
        readme = ACTIVE_DOCS_DIR / "README.md"
        content = _read(readme)
        assert "_archive" in content, (
            "docs/README.md must document the _archive/ directory"
        )

    def test_readme_under_80_lines(self):
        readme = ACTIVE_DOCS_DIR / "README.md"
        line_count = len(_read(readme).splitlines())
        assert line_count <= 80, (
            f"docs/README.md must be ≤80 lines (currently {line_count})"
        )


# ─── Root cleanup ───────────────────────────────────────────────────────────


class TestRootCleanup:
    def test_no_plan_reestructuracion_in_root(self):
        assert not (REPO_ROOT / "plan_reestructuracion_qa_nm_suite.md").exists(), (
            "plan_reestructuracion_qa_nm_suite.md must not exist in repo root"
        )

    def test_retired_docs_not_in_qa_root(self):
        """No historical .md files should be loose in qa/."""
        qa_dir = REPO_ROOT / "qa"
        if not qa_dir.exists():
            return
        loose_mds = list(qa_dir.glob("*.md"))
        assert loose_mds == [], (
            f"qa/ should have no loose .md files (found: {[f.name for f in loose_mds]})"
        )


# ─── Archive integrity ──────────────────────────────────────────────────────


class TestArchiveIntegrity:
    def test_archive_dir_exists(self):
        assert ARCHIVE_DIR.exists(), "docs/_archive/ must exist"

    def test_archive_has_retired_docs(self):
        """Key retired docs must be in the archive."""
        expected_archived = [
            "VISUAL_AUDITOR_V2.md",
            "VISUAL_AUDITOR_V3.md",
            "SENTINEL_REMOVAL.md",
            "COVERAGE_GAPS.md",
            "TAXONOMIA_V3.md",
        ]
        for name in expected_archived:
            assert (ARCHIVE_DIR / name).exists(), (
                f"{name} should be archived in docs/_archive/"
            )

    def test_retired_docs_not_in_active_docs(self):
        """Retired docs must not be in docs/ root (only in _archive/)."""
        retired = [
            "VISUAL_AUDITOR_V2.md",
            "VISUAL_AUDITOR_V3.md",
            "TAXONOMIA_V3.md",
            "VISUAL_QA_AUDIT.md",
        ]
        for name in retired:
            assert not (ACTIVE_DOCS_DIR / name).exists(), (
                f"{name} must not be in docs/ root (should be in _archive/)"
            )
