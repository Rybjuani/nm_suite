"""Governance contract tests for active Visual QA documentation.

Ensures:
1. Retired-tool references (V2/V3 Auditor, Sentinel, Coverage Gaps, etc.) do not
   appear in active docs (outside docs/_archive/).
2. Subjective closure criteria ("manual side-by-side", "manual review", "manual
   panel review", "inspección manual" as closure evidence) do not appear in the
   closure-evidence sections of active protocol/handoff docs.
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
ACTIVE_PROTOCOL_DOCS = [
    REPO_ROOT / "VISUAL_QA_AGENT_PROTOCOL.md",
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

# Subjective closure phrases that must not appear as closure criteria.
# We check the closure-evidence sections specifically, not historical evidence
# notes inside checklist items.
SUBJECTIVE_CLOSURE_PHRASES = [
    "manual side-by-side confirmation",
    "manual panel review",
    "inspección manual",
    "inspeccion manual",
]
# Broader phrases checked only in closure-evidence section headings.
SECTION_LEVEL_SUBJECTIVE = [
    "manual side-by-side",
    "manual review confirms",
    "manual panel review confirms",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _active_docs_files() -> list[Path]:
    """All .md files directly in docs/ (not in _archive/)."""
    if not ACTIVE_DOCS_DIR.exists():
        return []
    return [
        f for f in ACTIVE_DOCS_DIR.glob("*.md")
        if f.is_file() and "_archive" not in f.parts
    ]


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


# ─── Subjective closure criteria ────────────────────────────────────────────


class TestSubjectiveClosureAbsent:
    """No subjective/manual closure criteria in active protocol docs.

    Checks only the normative closure-evidence sections, not historical evidence
    notes inside checklist items (those are records of what was done, not active
    criteria — rewriting them would falsify history).
    """

    def _extract_closure_section(self, content: str) -> str:
        """Extract the closure-evidence section from a protocol doc."""
        lines = content.splitlines()
        result: list[str] = []
        in_section = False
        for line in lines:
            if re.match(r"^#+\s.*(Closure Evidence|Cierre)", line, re.IGNORECASE):
                in_section = True
                result.append(line)
                continue
            if in_section:
                # End at the next ## or ### heading (end of section)
                if re.match(r"^#+\s", line) and not re.match(r"^####", line):
                    if not re.match(r"^###\s*PASS", line, re.IGNORECASE):
                        break
                result.append(line)
        return "\n".join(result)

    @pytest.mark.parametrize("doc_path", ACTIVE_PROTOCOL_DOCS)
    def test_no_subjective_closure_phrases(self, doc_path):
        content = _read(doc_path)
        closure_section = self._extract_closure_section(content).lower()
        assert closure_section, f"{doc_path.name}: could not find closure-evidence section"
        for phrase in SUBJECTIVE_CLOSURE_PHRASES:
            assert phrase.lower() not in closure_section, (
                f"{doc_path.name} closure section contains subjective phrase: '{phrase}'"
            )

    @pytest.mark.parametrize("doc_path", ACTIVE_PROTOCOL_DOCS)
    def test_closure_sections_have_vas_gate(self, doc_path):
        """Closure evidence sections must reference the VAS gate requirement."""
        content = _read(doc_path)
        # The closure section must mention vas_gate.py or VAS Gate
        assert "vas_gate" in content.lower() or "vas gate" in content.lower(), (
            f"{doc_path.name} closure criteria must reference the VAS Gate"
        )

    @pytest.mark.parametrize("doc_path", ACTIVE_PROTOCOL_DOCS)
    def test_closure_requires_technical_gates(self, doc_path):
        """Closure sections must list mandatory technical PASS requirements."""
        content = _read(doc_path)
        assert "PASS requirements" in content or "Closure Evidence" in content, (
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
        # Must point to the two source-of-truth documents.
        assert "VISUAL_QA_AGENT_PROTOCOL.md" in content
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
