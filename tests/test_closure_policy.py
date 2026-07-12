from __future__ import annotations

import copy

import pytest

from qa.closure_policy import (
    ANTIFRAUD_SUMMARY_SCHEMA,
    DETERMINISM_SCHEMA,
    REPORT_SCHEMA,
    STATE_ASSERTION_SCHEMA,
    VAS_SUMMARY_SCHEMA,
    decide,
)
from qa.state_probes import STATE_PROBES, state_assertion_required


def _valid_inputs(key: str = "suite:home@light") -> dict:
    report_sha = "a" * 64
    return {
        "report": {
            "schema": REPORT_SCHEMA,
            "report_evidence_valid": True,
            "report_scope": "PARTIAL",
            "report_sha256": report_sha,
            "thresholds": {"min_ssim": 0.92},
            "results": [
                {
                    "key": key,
                    "status": "PASS",
                    "real_divergence": False,
                    "suspicious_perfect_match": False,
                    "near_perfect_match": False,
                    "state_assertion_required": state_assertion_required(key),
                    "findings": [],
                    "metrics": {},
                    "layout": {},
                    "odiff": {"available": True, "diff_percentage": 1.0},
                }
            ],
        },
        "vas_summary": {
            "schema": VAS_SUMMARY_SCHEMA,
            "key": key,
            "pass": True,
            "fail_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "capture_valid": True,
        },
        "antifraud": {
            "schema": ANTIFRAUD_SUMMARY_SCHEMA,
            "mode": "all",
            "scope": "default_full",
            "clean": True,
            "count": 0,
            "violations": [],
        },
        "determinism": {
            "schema": DETERMINISM_SCHEMA,
            "key": key,
            "pass": True,
            "changed_ratio": 0.0,
            "first_run_id": "run-a",
            "second_run_id": "run-b",
            "first_git_head": "1" * 40,
            "second_git_head": "1" * 40,
        },
        "state_assertion": None,
        "approval": None,
        "target_set": {key},
    }


def _decision(inputs: dict) -> tuple[bool, list[str]]:
    return decide(**inputs)


def test_valid_measurement_is_allowed_and_inputs_are_not_mutated():
    inputs = _valid_inputs()
    original = copy.deepcopy(inputs)

    assert _decision(inputs) == (True, [])
    assert inputs == original


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (lambda x: x["report"].update(report_evidence_valid=False), "report_evidence_invalid"),
        (lambda x: x["report"]["results"][0].update(status="FAIL"), "comparator_not_pass"),
        (
            lambda x: x["report"]["results"][0].update(findings=["state_or_recipe_suspect"]),
            "blocking_finding:state_or_recipe_suspect",
        ),
        (
            lambda x: x["report"]["results"][0].update(findings=["odiff_unavailable"]),
            "blocking_finding:odiff_unavailable",
        ),
        (lambda x: x["vas_summary"].update(high_count=1), "vas_high_count_nonzero"),
        (lambda x: x["vas_summary"].update(capture_valid=False), "capture_evidence_invalid"),
        (lambda x: x["antifraud"].update(mode="runtime"), "antifraud_not_full_scan"),
        (lambda x: x["antifraud"].update(scope="scoped"), "antifraud_not_full_scan"),
        (lambda x: x["antifraud"].update(count=1), "antifraud_not_clean"),
        (lambda x: x["determinism"].update(changed_ratio=0.005), "determinism_failed"),
        (
            lambda x: x["determinism"].update(second_run_id="run-a"),
            "determinism_runs_not_independent",
        ),
        (lambda x: x.update(target_set={"suite:home@dark"}), "key_outside_target_set"),
        (lambda x: x.update(target_set="suite:home@light"), "target_set_invalid"),
    ],
)
def test_policy_truth_table_blocks_invalid_inputs(mutate, reason):
    inputs = _valid_inputs()
    mutate(inputs)

    allowed, reasons = _decision(inputs)

    assert allowed is False
    assert reason in reasons


def test_near_threshold_requires_external_approval_tied_to_report():
    inputs = _valid_inputs()
    inputs["report"]["results"][0]["findings"] = ["near_threshold:changed_pixel_ratio"]

    allowed, reasons = _decision(inputs)
    assert allowed is False
    assert "near_threshold_requires_verified_approval" in reasons

    inputs["approval"] = {
        "verified": True,
        "key": "suite:home@light",
        "report_sha256": "a" * 64,
        "approval_url": "https://github.com/Rybjuani/nm_suite/issues/1#issuecomment-2",
        "comment_id": 2,
        "author": "Rybjuani",
    }
    assert _decision(inputs) == (True, [])


def _reuse_approval(*, approved_findings: list[str], stored_sha: str = "f" * 64) -> dict:
    return {
        "verified": True,
        "key": "suite:home@light",
        "report_sha256": stored_sha,
        "binding": "stored_record_reuse",
        "approved_report_sha256": stored_sha,
        "approved_findings": approved_findings,
        "approval_url": "https://github.com/Rybjuani/nm_suite/issues/1#issuecomment-2",
        "comment_id": 2,
        "author": "Rybjuani",
    }


def test_stored_record_reuse_binding_never_requires_hash_rebinding():
    # El reporte regenerado tiene hash "a"*64; la aprobación queda ligada al
    # hash almacenado "f"*64 que GitHub verificó. El reuso explícito permite
    # sin reescribir el hash verificado.
    inputs = _valid_inputs()
    inputs["report"]["results"][0]["findings"] = ["near_threshold:changed_pixel_ratio"]
    inputs["approval"] = _reuse_approval(
        approved_findings=["near_threshold:changed_pixel_ratio"]
    )

    assert _decision(inputs) == (True, [])


def test_stored_record_reuse_blocks_when_regenerated_findings_exceed_approved():
    inputs = _valid_inputs()
    inputs["report"]["results"][0]["findings"] = [
        "near_threshold:changed_pixel_ratio",
        "near_threshold:mean_abs_diff",
    ]
    inputs["approval"] = _reuse_approval(
        approved_findings=["near_threshold:changed_pixel_ratio"]
    )

    allowed, reasons = _decision(inputs)
    assert allowed is False
    assert "approval_reuse_findings_exceeded" in reasons


def test_stored_record_reuse_requires_self_consistent_verified_hash():
    inputs = _valid_inputs()
    inputs["report"]["results"][0]["findings"] = ["near_threshold:changed_pixel_ratio"]
    approval = _reuse_approval(approved_findings=["near_threshold:changed_pixel_ratio"])
    approval["approved_report_sha256"] = "0" * 64  # distinto del hash verificado

    inputs["approval"] = approval
    allowed, reasons = _decision(inputs)
    assert allowed is False
    assert "approval_evidence_mismatch" in reasons


def test_unknown_approval_binding_is_fail_closed():
    inputs = _valid_inputs()
    inputs["report"]["results"][0]["findings"] = ["near_threshold:changed_pixel_ratio"]
    approval = _reuse_approval(approved_findings=["near_threshold:changed_pixel_ratio"])
    approval["binding"] = "trust_me"

    inputs["approval"] = approval
    allowed, reasons = _decision(inputs)
    assert allowed is False
    assert "approval_binding_invalid" in reasons


def test_ambiguous_pair_requires_state_assertion_from_shared_registry():
    inputs = _valid_inputs("suite:timer-running@dark")

    allowed, reasons = _decision(inputs)
    assert allowed is False
    assert "state_assertion_required" in reasons

    inputs["state_assertion"] = {
        "schema": STATE_ASSERTION_SCHEMA,
        "key": "suite:timer-running@dark",
        "pass": True,
        "observed": {"toggle": "pause", "state": "en curso"},
    }
    assert _decision(inputs) == (True, [])


def test_state_registry_contains_only_the_four_ambiguous_families():
    assert set(STATE_PROBES) == {
        "suite:respiracion-paused",
        "suite:respiracion-running",
        "suite:timer-paused",
        "suite:timer-running",
    }
    assert state_assertion_required("suite:timer-running@light") is True
    assert state_assertion_required("suite:onboarding-error@light") is False
