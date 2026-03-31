"""Comprehensive grader tests for all tasks."""

import pytest

from graders import grade_workspace
from tasks import TASKS


def test_billing_refund_easy_perfect_score() -> None:
    """Perfect workspace for billing_refund_easy should score highly."""
    task = TASKS["billing_refund_easy"]
    workspace = {
        **task.expected_fields,
        "internal_notes": ["Confirmed duplicate charge on the same day transaction log shows two identical charges refund approved processing time 5-7 business days"],
        "customer_reply": "Sorry about the duplicate charge. I have routed this to our billing team and approved the refund path. You should see the refund in 5-7 business days.",
    }
    
    report = grade_workspace(task, workspace)
    
    # Allow for slightly lower score due to grader weightings
    assert report.total_score >= 0.90, f"Expected >= 0.90, got {report.total_score}"
    assert report.public_breakdown["routing_and_resolution"] == 1.0


def test_billing_refund_easy_missing_fields() -> None:
    """Missing fields should reduce score."""
    task = TASKS["billing_refund_easy"]
    workspace = {
        "issue_type": "billing_dispute",
        "priority": "",  # Missing
        "queue": "billing",
        "refund_action": "approve_full_refund",
        "escalation_team": "billing_ops",
        "internal_notes": [],
        "customer_reply": "",
    }
    
    report = grade_workspace(task, workspace)
    assert report.total_score < 1.0
    assert report.public_breakdown["routing_and_resolution"] < 1.0


def test_shipping_vip_medium_perfect_score() -> None:
    """Perfect workspace for shipping_vip_medium should score well."""
    task = TASKS["shipping_vip_medium"]
    workspace = {
        **task.expected_fields,
        "internal_notes": ["VIP customer with tracking stalled for 72 hours conference on Monday escalating to carrier liaison for expedited replacement"],
        "customer_reply": "I understand the timing is critical. We are escalating the stalled tracking with the carrier and can arrange an expedited replacement if needed.",
    }
    
    report = grade_workspace(task, workspace)
    assert report.total_score > 0.8


def test_security_incident_hard_requires_escalation() -> None:
    """Security incident should require security escalation."""
    task = TASKS["security_incident_hard"]
    
    # Wrong escalation
    bad_workspace = {
        **task.expected_fields,
        "escalation_team": "billing_ops",  # Wrong!
        "internal_notes": ["Possible account takeover with unauthorized orders"],
        "customer_reply": "We are investigating your account issue.",
    }
    
    report = grade_workspace(task, bad_workspace)
    assert report.field_scores.get("escalation_team", 1.0) == 0.0


def test_privacy_export_forbidden_keywords_reduce_score() -> None:
    """Using forbidden keywords should reduce compliance score."""
    task = TASKS["privacy_export_medium"]
    workspace = {
        **task.expected_fields,
        "internal_notes": ["EU customer data export request"],
        "customer_reply": "I can offer you a full refund for your data export request.",  # Uses "refund" which is forbidden
    }
    
    report = grade_workspace(task, workspace)
    assert report.public_breakdown["policy_compliance"] < 1.0


def test_empty_workspace_scores_zero() -> None:
    """Empty workspace should score near zero."""
    task = TASKS["billing_refund_easy"]
    workspace = {
        "issue_type": "",
        "priority": "",
        "queue": "",
        "refund_action": "",
        "escalation_team": "",
        "internal_notes": [],
        "customer_reply": "",
    }
    
    report = grade_workspace(task, workspace)
    assert report.total_score < 0.2


def test_payout_hold_hard_no_immediate_promise() -> None:
    """Payout hold should not promise immediate release."""
    task = TASKS["payout_hold_hard"]
    
    # Good reply - doesn't promise immediate release
    good_workspace = {
        **task.expected_fields,
        "internal_notes": ["Velocity spike triggered automated review"],
        "customer_reply": "We cannot promise immediate release until the review completes. We will share the next update soon.",
    }
    
    good_report = grade_workspace(task, good_workspace)
    
    # Bad reply - promises immediate release
    bad_workspace = {
        **task.expected_fields,
        "internal_notes": ["Velocity spike triggered automated review"],
        "customer_reply": "Your payout will be released today guaranteed.",  # Forbidden keywords
    }
    
    bad_report = grade_workspace(task, bad_workspace)
    
    assert good_report.public_breakdown["policy_compliance"] > bad_report.public_breakdown["policy_compliance"]


def test_reply_length_scoring() -> None:
    """Reply length should affect score."""
    task = TASKS["billing_refund_easy"]
    
    # Too short reply
    short_workspace = {
        **task.expected_fields,
        "internal_notes": ["duplicate charge refund approved"],
        "customer_reply": "Refunded.",
    }
    
    # Good length reply
    good_workspace = {
        **task.expected_fields,
        "internal_notes": ["duplicate charge refund approved"],
        "customer_reply": "We sincerely apologize for the duplicate charge on your account. After reviewing your transaction history, we have confirmed this was an error and have processed a full refund. You should see the funds returned to your account within 5 to 7 business days.",
    }
    
    short_report = grade_workspace(task, short_workspace)
    good_report = grade_workspace(task, good_workspace)
    
    assert good_report.public_breakdown["customer_reply_quality"] > short_report.public_breakdown["customer_reply_quality"]


def test_all_tasks_have_graders() -> None:
    """All defined tasks should be gradeable."""
    for task_id, task in TASKS.items():
        workspace = {
            **task.expected_fields,
            "internal_notes": ["test note"],
            "customer_reply": "Test reply with sufficient length to meet minimum requirements.",
        }
        
        report = grade_workspace(task, workspace)
        assert 0.0 <= report.total_score <= 1.0
        assert report.feedback is not None


def test_feedback_is_not_empty() -> None:
    """Grader should always provide feedback."""
    task = TASKS["billing_refund_easy"]
    workspace = {**task.expected_fields, "internal_notes": [], "customer_reply": ""}
    
    report = grade_workspace(task, workspace)
    assert len(report.feedback) > 0
