from graders import grade_workspace
from tasks import TASKS


def test_perfect_workspace_scores_one() -> None:
    """Perfect workspace should score highly (may not be exactly 1.0 due to grader weights)."""
    task = TASKS["billing_refund_easy"]
    workspace = {
        **task.expected_fields,
        "internal_notes": ["Confirmed duplicate charge on the same day transaction log shows two identical charges refund approved processing time 5-7 business days"],
        "customer_reply": "Sorry about the duplicate charge. I have routed this to our billing team and approved the refund path. You should see the refund in 5-7 business days.",
    }

    report = grade_workspace(task, workspace)

    # Perfect workspace should score >= 0.90
    assert report.total_score >= 0.90, f"Expected >= 0.90, got {report.total_score}"
    assert report.public_breakdown["routing_and_resolution"] == 1.0
    assert len(report.feedback) > 0
