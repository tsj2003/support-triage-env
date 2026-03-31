from server.support_triage_environment import SupportTriageEnvironment

from models import SupportTriageAction


def test_environment_progression() -> None:
    env = SupportTriageEnvironment()
    initial = env.reset(task_id="billing_refund_easy")
    assert initial.score >= 0.0  # Empty workspace may have baseline score

    env.step(
        SupportTriageAction(
            kind="set_field",
            field_name="issue_type",
            value="billing_dispute",
        )
    )
    current = env.step(
        SupportTriageAction(
            kind="set_field",
            field_name="queue",
            value="billing",
        )
    )

    assert current.score > initial.score  # Score should improve
    assert not current.done
