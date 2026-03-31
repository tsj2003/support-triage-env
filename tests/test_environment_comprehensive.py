"""Comprehensive tests for the support triage environment."""

import pytest

from models import SupportTriageAction
from server.support_triage_environment import SupportTriageEnvironment
from tasks import TASKS


def test_reset_creates_clean_state() -> None:
    """reset() should produce a clean initial state."""
    env = SupportTriageEnvironment()
    obs = env.reset(task_id="billing_refund_easy")
    
    assert obs.task_id == "billing_refund_easy"
    assert obs.score >= 0.0  # Score may have baseline from empty workspace grading
    assert obs.remaining_steps > 0
    assert obs.current_workspace["issue_type"] == ""
    assert obs.current_workspace["internal_notes"] == []
    assert not obs.done


def test_reset_with_different_tasks() -> None:
    """reset() works for all defined tasks."""
    env = SupportTriageEnvironment()
    
    for task_id in TASKS:
        obs = env.reset(task_id=task_id)
        assert obs.task_id == task_id
        assert obs.difficulty == TASKS[task_id].difficulty


def test_set_field_updates_workspace() -> None:
    """set_field action updates structured fields."""
    env = SupportTriageEnvironment()
    env.reset(task_id="billing_refund_easy")
    
    obs = env.step(SupportTriageAction(
        kind="set_field",
        field_name="issue_type",
        value="billing_dispute",
    ))
    
    assert obs.current_workspace["issue_type"] == "billing_dispute"
    assert obs.score > 0  # Should get partial credit


def test_set_field_invalid_value_is_error() -> None:
    """set_field with invalid value should mark as error."""
    env = SupportTriageEnvironment()
    env.reset(task_id="billing_refund_easy")
    
    obs = env.step(SupportTriageAction(
        kind="set_field",
        field_name="issue_type",
        value="invalid_value",
    ))
    
    assert obs.last_action_error is True
    assert obs.reward < 0  # Should be penalized


def test_add_note_creates_note() -> None:
    """add_note action adds to internal notes."""
    env = SupportTriageEnvironment()
    env.reset(task_id="billing_refund_easy")
    
    obs = env.step(SupportTriageAction(
        kind="add_note",
        text="Investigating duplicate charge",
    ))
    
    assert len(obs.current_workspace["internal_notes"]) == 1
    assert "duplicate" in obs.current_workspace["internal_notes"][0].lower()


def test_draft_reply_updates_reply() -> None:
    """draft_reply action updates customer reply."""
    env = SupportTriageEnvironment()
    env.reset(task_id="billing_refund_easy")
    
    obs = env.step(SupportTriageAction(
        kind="draft_reply",
        text="We have processed your refund request.",
    ))
    
    assert obs.current_workspace["customer_reply"] == "We have processed your refund request."


def test_submit_ends_episode() -> None:
    """submit action ends the episode."""
    env = SupportTriageEnvironment()
    env.reset(task_id="billing_refund_easy")
    
    obs = env.step(SupportTriageAction(kind="submit"))
    
    assert obs.done is True
    assert "final_score" in obs.current_workspace


def test_max_steps_ends_episode() -> None:
    """Episode ends when max steps reached."""
    env = SupportTriageEnvironment()
    obs = env.reset(task_id="billing_refund_easy")
    max_steps = obs.remaining_steps
    
    # Take random actions until max steps
    for _ in range(max_steps + 1):
        if obs.done:
            break
        obs = env.step(SupportTriageAction(kind="add_note", text="Test note"))
    
    assert obs.done is True


def test_repeat_action_penalized() -> None:
    """Repeated actions should be penalized."""
    env = SupportTriageEnvironment()
    env.reset(task_id="billing_refund_easy")
    
    # First action
    obs1 = env.step(SupportTriageAction(
        kind="add_note",
        text="Note 1",
    ))
    
    # Same action again
    obs2 = env.step(SupportTriageAction(
        kind="add_note",
        text="Note 1",
    ))
    
    # Second identical action should have lower reward
    assert obs2.reward < obs1.reward


def test_empty_note_is_error() -> None:
    """Empty note should be rejected at environment level (Pydantic validates non-empty)."""
    env = SupportTriageEnvironment()
    env.reset(task_id="billing_refund_easy")
    
    # Empty text is blocked by Pydantic validation, test with whitespace-only
    obs = env.step(SupportTriageAction(
        kind="add_note",
        text="   ",  # Whitespace only - will be rejected by environment
    ))
    
    assert obs.last_action_error is True


def test_empty_reply_is_error() -> None:
    """Empty reply should be rejected at environment level (Pydantic validates non-empty)."""
    env = SupportTriageEnvironment()
    env.reset(task_id="billing_refund_easy")
    
    # Empty text is blocked by Pydantic validation, test with whitespace-only
    obs = env.step(SupportTriageAction(
        kind="draft_reply",
        text="   ",  # Whitespace only - will be rejected
    ))
    
    assert obs.last_action_error is True


def test_score_improves_with_correct_fields() -> None:
    """Score should improve as correct fields are set."""
    env = SupportTriageEnvironment()
    obs = env.reset(task_id="billing_refund_easy")
    task = TASKS["billing_refund_easy"]
    
    initial_score = obs.score
    
    # Set all correct fields
    for field_name, value in task.expected_fields.items():
        obs = env.step(SupportTriageAction(
            kind="set_field",
            field_name=field_name,
            value=value,
        ))
    
    # Score should be much higher
    assert obs.score > initial_score + 0.3


def test_notes_limit_is_enforced() -> None:
    """Internal notes should be limited (max 4)."""
    env = SupportTriageEnvironment()
    env.reset(task_id="billing_refund_easy")
    
    # Add 6 notes
    for i in range(6):
        env.step(SupportTriageAction(
            kind="add_note",
            text=f"Note number {i}",
        ))
    
    obs = env.state
    assert len(obs.workspace["internal_notes"]) <= 4
