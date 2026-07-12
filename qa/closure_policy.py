#!/usr/bin/env python3
"""Pure, fail-closed policy for visual evidence decisions.

This module performs no measurement, filesystem access, network access, or
mutation. Callers normalize tool outputs and external approval verification,
then pass those values to :func:`decide`.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from typing import Any

try:
    from qa.state_probes import state_assertion_required
except ModuleNotFoundError:  # direct ``python qa/...`` execution
    from state_probes import state_assertion_required


REPORT_SCHEMA = "nm_suite.layered_report.v2"
VAS_SUMMARY_SCHEMA = "nm_suite.vas_summary.v1"
ANTIFRAUD_SUMMARY_SCHEMA = "nm_suite.antifraud_summary.v1"
DETERMINISM_SCHEMA = "nm_suite.determinism.v1"
STATE_ASSERTION_SCHEMA = "nm_suite.state_assertion.v1"
DETERMINISM_CHANGED_RATIO_LIMIT = 0.005


def _add(reasons: list[str], reason: str) -> None:
    if reason not in reasons:
        reasons.append(reason)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _target_keys(target_set: object) -> set[str] | None:
    if isinstance(target_set, (str, bytes)) or not isinstance(target_set, Iterable):
        return None
    keys = list(target_set)
    if not all(isinstance(key, str) and key for key in keys):
        return None
    return set(keys)


def _validate_report(report: object, reasons: list[str]) -> tuple[str, list[str], bool] | None:
    if not isinstance(report, Mapping):
        _add(reasons, "report_missing_or_invalid")
        return None
    if report.get("schema") != REPORT_SCHEMA:
        _add(reasons, "report_schema_invalid")
    if report.get("report_evidence_valid") is not True:
        _add(reasons, "report_evidence_invalid")
    if report.get("report_scope") not in {"FULL", "PARTIAL"}:
        _add(reasons, "report_scope_invalid")
    if not isinstance(report.get("report_sha256"), str) or len(report["report_sha256"]) != 64:
        _add(reasons, "report_sha256_invalid")
    if not isinstance(report.get("thresholds"), Mapping) or not report.get("thresholds"):
        _add(reasons, "report_thresholds_missing")

    results = report.get("results")
    if not isinstance(results, list) or len(results) != 1 or not isinstance(results[0], Mapping):
        _add(reasons, "report_requires_exactly_one_result")
        return None
    result = results[0]
    key = result.get("key")
    if not isinstance(key, str) or not key:
        _add(reasons, "result_key_invalid")
        return None
    if result.get("status") != "PASS":
        _add(reasons, "comparator_not_pass")
    if result.get("real_divergence") is not False:
        _add(reasons, "comparator_real_divergence")
    if result.get("suspicious_perfect_match") is not False:
        _add(reasons, "suspicious_perfect_match")
    if result.get("near_perfect_match") is not False:
        _add(reasons, "near_perfect_match")
    for field in ("metrics", "layout", "odiff"):
        if not isinstance(result.get(field), Mapping):
            _add(reasons, f"result_{field}_invalid")
    odiff = result.get("odiff")
    if not isinstance(odiff, Mapping) or odiff.get("available") is not True:
        _add(reasons, "odiff_unavailable")

    findings_value = result.get("findings")
    if not isinstance(findings_value, list) or not all(
        isinstance(finding, str) for finding in findings_value
    ):
        _add(reasons, "result_findings_invalid")
        findings: list[str] = []
    else:
        findings = list(findings_value)
        for finding in findings:
            if not finding.startswith("near_threshold:"):
                _add(reasons, f"blocking_finding:{finding}")

    required = state_assertion_required(key)
    if result.get("state_assertion_required") is not required:
        _add(reasons, "state_assertion_requirement_mismatch")

    modal_required = report.get("modal_audit_required", False)
    if not isinstance(modal_required, bool):
        _add(reasons, "modal_audit_requirement_invalid")
    elif modal_required:
        modal_audit = report.get("modal_audit")
        if not isinstance(modal_audit, Mapping) or modal_audit.get("pass") is not True:
            _add(reasons, "modal_audit_failed")
    return key, findings, required


def _validate_vas(vas_summary: object, key: str, reasons: list[str]) -> None:
    if not isinstance(vas_summary, Mapping):
        _add(reasons, "vas_summary_missing_or_invalid")
        return
    if vas_summary.get("schema") != VAS_SUMMARY_SCHEMA:
        _add(reasons, "vas_summary_schema_invalid")
    if vas_summary.get("key") != key:
        _add(reasons, "vas_summary_key_mismatch")
    if vas_summary.get("pass") is not True:
        _add(reasons, "vas_gate_failed")
    for field in ("fail_count", "high_count", "medium_count"):
        if vas_summary.get(field) != 0:
            _add(reasons, f"vas_{field}_nonzero")
    if vas_summary.get("capture_valid") is not True:
        _add(reasons, "capture_evidence_invalid")


def _validate_antifraud(antifraud: object, reasons: list[str]) -> None:
    if not isinstance(antifraud, Mapping):
        _add(reasons, "antifraud_missing_or_invalid")
        return
    if antifraud.get("schema") != ANTIFRAUD_SUMMARY_SCHEMA:
        _add(reasons, "antifraud_schema_invalid")
    if antifraud.get("mode") != "all" or antifraud.get("scope") != "default_full":
        _add(reasons, "antifraud_not_full_scan")
    violations = antifraud.get("violations")
    if (
        antifraud.get("clean") is not True
        or antifraud.get("count") != 0
        or not isinstance(violations, list)
        or violations
    ):
        _add(reasons, "antifraud_not_clean")


def _validate_determinism(determinism: object, key: str, reasons: list[str]) -> None:
    if not isinstance(determinism, Mapping):
        _add(reasons, "determinism_missing_or_invalid")
        return
    if determinism.get("schema") != DETERMINISM_SCHEMA:
        _add(reasons, "determinism_schema_invalid")
    if determinism.get("key") != key:
        _add(reasons, "determinism_key_mismatch")
    ratio = determinism.get("changed_ratio")
    if (
        determinism.get("pass") is not True
        or not _is_number(ratio)
        or float(ratio) < 0.0
        or float(ratio) >= DETERMINISM_CHANGED_RATIO_LIMIT
    ):
        _add(reasons, "determinism_failed")
    first_run = determinism.get("first_run_id")
    second_run = determinism.get("second_run_id")
    if (
        not isinstance(first_run, str)
        or not first_run
        or not isinstance(second_run, str)
        or not second_run
        or first_run == second_run
    ):
        _add(reasons, "determinism_runs_not_independent")
    first_head = determinism.get("first_git_head")
    second_head = determinism.get("second_git_head")
    if not isinstance(first_head, str) or not first_head or first_head != second_head:
        _add(reasons, "determinism_git_head_mismatch")


def _validate_state_assertion(
    state_assertion: object,
    key: str,
    required: bool,
    reasons: list[str],
) -> None:
    if not required:
        return
    if not isinstance(state_assertion, Mapping):
        _add(reasons, "state_assertion_required")
        return
    if state_assertion.get("schema") != STATE_ASSERTION_SCHEMA:
        _add(reasons, "state_assertion_schema_invalid")
    if state_assertion.get("key") != key:
        _add(reasons, "state_assertion_key_mismatch")
    if state_assertion.get("pass") is not True:
        _add(reasons, "state_assertion_failed")


def _validate_approval(
    approval: object,
    key: str,
    report_sha256: str,
    findings: list[str],
    reasons: list[str],
) -> None:
    """Validate the external approval for near-threshold evidence.

    Two explicit bindings exist and the verified hash is never rewritten:

    - ``direct`` (default, closure time): the approval was externally
      verified against the exact report being decided, so
      ``approval.report_sha256`` must equal the current report hash.
    - ``stored_record_reuse`` (independent replay of an existing record):
      the approval stays bound to the stored record's report hash — the one
      GitHub actually verified and that the replay's class-A checks pin to
      the record. Reuse is valid only while the regenerated near-threshold
      findings do not exceed the set the owner approved.
    """

    near_findings = [finding for finding in findings if finding.startswith("near_threshold:")]
    if not near_findings:
        return
    if not isinstance(approval, Mapping) or approval.get("verified") is not True:
        _add(reasons, "near_threshold_requires_verified_approval")
        return
    if approval.get("key") != key:
        _add(reasons, "approval_evidence_mismatch")
    binding = approval.get("binding", "direct")
    if binding == "direct":
        if approval.get("report_sha256") != report_sha256:
            _add(reasons, "approval_evidence_mismatch")
    elif binding == "stored_record_reuse":
        if approval.get("report_sha256") != approval.get("approved_report_sha256"):
            _add(reasons, "approval_evidence_mismatch")
        approved = approval.get("approved_findings")
        if not isinstance(approved, list) or not all(
            isinstance(finding, str) and finding.startswith("near_threshold:")
            for finding in approved
        ):
            _add(reasons, "approval_reuse_findings_invalid")
        elif not set(near_findings) <= set(approved):
            _add(reasons, "approval_reuse_findings_exceeded")
    else:
        _add(reasons, "approval_binding_invalid")
    for field in ("approval_url", "comment_id", "author"):
        value = approval.get(field)
        if not isinstance(value, (str, int)) or isinstance(value, bool) or str(value).strip() == "":
            _add(reasons, f"approval_{field}_invalid")


def decide(
    report: object,
    vas_summary: object,
    antifraud: object,
    determinism: object,
    state_assertion: object,
    approval: object,
    target_set: object,
) -> tuple[bool, list[str]]:
    """Return ``(allow, reasons)`` without mutating or re-measuring inputs."""

    reasons: list[str] = []
    report_values = _validate_report(report, reasons)
    if report_values is None:
        return False, reasons
    key, findings, required = report_values

    keys = _target_keys(target_set)
    if keys is None:
        _add(reasons, "target_set_invalid")
    elif key not in keys:
        _add(reasons, "key_outside_target_set")

    _validate_vas(vas_summary, key, reasons)
    _validate_antifraud(antifraud, reasons)
    _validate_determinism(determinism, key, reasons)
    _validate_state_assertion(state_assertion, key, required, reasons)
    report_sha256 = report.get("report_sha256") if isinstance(report, Mapping) else ""
    _validate_approval(approval, key, str(report_sha256), findings, reasons)
    return not reasons, reasons
