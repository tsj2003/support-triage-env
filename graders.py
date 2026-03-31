"""Deterministic graders shared by the environment and the baseline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

try:
    from .tasks import TaskSpec
except ImportError:
    from tasks import TaskSpec


@dataclass(frozen=True)
class GradeReport:
    """Structured grader output."""

    total_score: float
    public_breakdown: Dict[str, float]
    feedback: List[str]
    field_scores: Dict[str, float]


def _normalize(text: str | None) -> str:
    return " ".join((text or "").strip().lower().split())


def _keyword_fraction(text: str | None, keywords: Iterable[str]) -> float:
    normalized_text = _normalize(text)
    expected = list(keywords)
    if not expected:
        return 1.0
    matches = sum(1 for keyword in expected if _normalize(keyword) in normalized_text)
    return matches / len(expected)


def _field_scores(workspace: Dict[str, Any], expected_fields: Dict[str, str]) -> Dict[str, float]:
    return {
        field_name: float(
            _normalize(str(workspace.get(field_name, ""))) == _normalize(expected_value)
        )
        for field_name, expected_value in expected_fields.items()
    }


def _length_score(text: str | None, minimum: int, maximum: int) -> float:
    word_count = len((text or "").split())
    if minimum <= word_count <= maximum:
        return 1.0
    if word_count == 0:
        return 0.0
    tolerance_floor = max(1, int(minimum * 0.6))
    tolerance_ceiling = int(maximum * 1.25)
    if tolerance_floor <= word_count <= tolerance_ceiling:
        return 0.5
    return 0.2


def grade_workspace(task: TaskSpec, workspace: Dict[str, Any]) -> GradeReport:
    """Return a deterministic grade report for the current workspace."""
    field_scores = _field_scores(workspace, task.expected_fields)
    structured_score = sum(field_scores.values()) / max(1, len(field_scores))

    notes_text = "\n".join(workspace.get("internal_notes", []))
    note_keyword_score = _keyword_fraction(notes_text, task.required_note_keywords)
    note_length_score = _length_score(notes_text, minimum=8, maximum=50)
    note_score = round((0.8 * note_keyword_score) + (0.2 * note_length_score), 4)

    reply_text = workspace.get("customer_reply", "")
    reply_keyword_score = _keyword_fraction(reply_text, task.required_reply_keywords)
    reply_length_score = _length_score(
        reply_text,
        minimum=task.reply_min_words,
        maximum=task.reply_max_words,
    )
    tone_keyword_score = _keyword_fraction(reply_text, task.empathy_keywords)
    reply_score = round((0.7 * reply_keyword_score) + (0.3 * reply_length_score), 4)
    tone_score = round((0.5 * tone_keyword_score) + (0.5 * reply_length_score), 4)

    forbidden_hits = sum(
        1 for keyword in task.forbidden_reply_keywords if _normalize(keyword) in _normalize(reply_text)
    )
    compliance_score = 1.0
    if forbidden_hits:
        compliance_score = max(0.0, 1.0 - (forbidden_hits / max(1, len(task.forbidden_reply_keywords))))

    total_score = round(
        (0.45 * structured_score)
        + (0.18 * note_score)
        + (0.20 * reply_score)
        + (0.12 * compliance_score)
        + (0.05 * tone_score),
        4,
    )

    breakdown = {
        "routing_and_resolution": round(structured_score, 4),
        "internal_note_quality": round(note_score, 4),
        "customer_reply_quality": round(reply_score, 4),
        "policy_compliance": round(compliance_score, 4),
        "tone_and_clarity": round(tone_score, 4),
    }

    feedback: List[str] = []
    # Rubric-based feedback: reward evidence, policy, empathy, and reasoning
    # 1. Evidence and rationale in notes
    if note_score >= 0.92:
        feedback.append("Internal notes provide clear evidence and rationale for your decision.")
    elif note_score >= 0.7:
        feedback.append("Internal notes are present but could include more evidence or clearer rationale.")
    else:
        feedback.append("Internal notes are missing key evidence or reasoning steps.")

    # 2. Policy alignment in actions
    if compliance_score == 1.0:
        feedback.append("Actions comply with policy and avoid over-promising outcomes.")
    elif compliance_score >= 0.7:
        feedback.append("Most actions comply with policy, but some language or steps could be improved.")
    else:
        feedback.append("Some actions or language do not comply with policy. Review policy checklist.")

    # 3. Empathy and clarity in reply
    if tone_score >= 0.85:
        feedback.append("Customer reply is empathetic and action-oriented.")
    elif tone_score >= 0.65:
        feedback.append("Customer reply shows some empathy, but could be clearer or more supportive.")
    else:
        feedback.append("Customer reply lacks empathy or clarity. Consider the customer's perspective.")

    # 4. Reasoning and next steps in reply
    if reply_score >= 0.92:
        feedback.append("Customer reply provides clear next steps and references relevant policy or context.")
    elif reply_score >= 0.7:
        feedback.append("Customer reply is mostly clear, but could better reference policy or next steps.")
    else:
        feedback.append("Customer reply is missing clear next steps or policy references.")

    # 5. Routing and operational reasoning
    if field_scores.get("issue_type", 0.0) == 1.0 and field_scores.get("queue", 0.0) == 1.0:
        feedback.append("Case routing matches operational owner and issue type.")
    else:
        feedback.append("Case routing or issue type could be improved. Double-check operational owner.")

    # 6. Priority and escalation reasoning
    if field_scores.get("priority", 0.0) == 1.0 and field_scores.get("escalation_team", 0.0) == 1.0:
        feedback.append("Priority and escalation reflect the risk level and incident context.")
    else:
        feedback.append("Priority or escalation could be better aligned with incident risk.")

    return GradeReport(
        total_score=total_score,
        public_breakdown=breakdown,
        feedback=feedback,
        field_scores=field_scores,
    )
