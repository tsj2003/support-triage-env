"""Enhanced deterministic graders with stricter criteria and edge case handling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Set, Tuple

try:
    from .tasks import TaskSpec
except ImportError:
    from tasks import TaskSpec


@dataclass(frozen=True)
class GradeReport:
    """Structured grader output with enhanced feedback."""

    total_score: float
    public_breakdown: Dict[str, float]
    feedback: List[str]
    field_scores: Dict[str, float]
    edge_cases_handled: List[str]  # New: Document what edge cases were checked
    confidence: float  # New: Confidence in grading


def _normalize(text: str | None) -> str:
    """Normalize text for comparison."""
    return " ".join((text or "").strip().lower().split())


def _keyword_fraction(text: str | None, keywords: Iterable[str]) -> float:
    """Calculate fraction of keywords present in text."""
    normalized_text = _normalize(text)
    expected = list(keywords)
    if not expected:
        return 1.0
    matches = sum(1 for keyword in expected if _normalize(keyword) in normalized_text)
    return matches / len(expected)


def _field_scores(workspace: Dict[str, Any], expected_fields: Dict[str, str]) -> Dict[str, float]:
    """Score each structured field individually."""
    return {
        field_name: float(
            _normalize(str(workspace.get(field_name, ""))) == _normalize(expected_value)
        )
        for field_name, expected_value in expected_fields.items()
    }


def _length_score(text: str | None, minimum: int, maximum: int) -> float:
    """Score text length with tolerance zones."""
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


def _check_edge_cases(task: TaskSpec, workspace: Dict[str, Any]) -> List[str]:
    """Check for edge cases and return list of handled cases."""
    edge_cases = []
    
    # Empty workspace
    if not any(workspace.get(f) for f in task.expected_fields.keys() if f != "internal_notes"):
        edge_cases.append("empty_fields")
    
    # Missing critical fields
    critical_fields = ["issue_type", "priority", "queue"]
    missing_critical = [f for f in critical_fields if not workspace.get(f)]
    if missing_critical:
        edge_cases.append(f"missing_critical:{','.join(missing_critical)}")
    
    # Empty customer reply when expected
    if not workspace.get("customer_reply") and task.required_reply_keywords:
        edge_cases.append("missing_reply")
    
    # Too many notes
    notes = workspace.get("internal_notes", [])
    if len(notes) > 4:
        edge_cases.append("excess_notes")
    
    # Check for forbidden keywords
    reply_text = workspace.get("customer_reply", "")
    forbidden_hits = [
        kw for kw in task.forbidden_reply_keywords 
        if _normalize(kw) in _normalize(reply_text)
    ]
    if forbidden_hits:
        edge_cases.append(f"forbidden_keywords:{','.join(forbidden_hits)}")
    
    return edge_cases


def grade_workspace(task: TaskSpec, workspace: Dict[str, Any]) -> GradeReport:
    """
    Return a deterministic grade report for the current workspace.
    Enhanced version with stricter criteria and edge case handling.
    """
    # Check edge cases
    edge_cases = _check_edge_cases(task, workspace)
    
    # Score structured fields (45% weight)
    field_scores = _field_scores(workspace, task.expected_fields)
    structured_score = sum(field_scores.values()) / max(1, len(field_scores))
    
    # Calculate structured field bonuses/penalties
    critical_correct = sum(
        field_scores.get(f, 0) for f in ["issue_type", "priority", "queue"]
    ) / 3
    
    # Issue type and queue alignment bonus
    routing_aligned = (
        field_scores.get("issue_type", 0) == 1.0 and 
        field_scores.get("queue", 0) == 1.0
    )
    
    # Enhanced structured scoring with routing bonus
    structured_score = min(1.0, structured_score + (0.05 if routing_aligned else 0))
    
    # Internal notes scoring (18% weight) - Enhanced
    notes_text = "\n".join(workspace.get("internal_notes", []))
    note_keyword_score = _keyword_fraction(notes_text, task.required_note_keywords)
    note_length_score = _length_score(notes_text, minimum=10, maximum=60)  # Stricter
    
    # Check for policy compliance keywords in notes
    policy_keywords = ["policy", "procedure", "guideline", "compliance"]
    policy_mention = any(kw in _normalize(notes_text) for kw in policy_keywords)
    policy_score = 0.2 if policy_mention else 0.0
    
    note_score = round((0.6 * note_keyword_score) + (0.2 * note_length_score) + (0.2 * policy_score), 4)
    
    # Customer reply scoring (20% weight) - Enhanced
    reply_text = workspace.get("customer_reply", "")
    reply_keyword_score = _keyword_fraction(reply_text, task.required_reply_keywords)
    reply_length_score = _length_score(
        reply_text,
        minimum=task.reply_min_words,
        maximum=task.reply_max_words,
    )
    
    # Check for actionable items in reply
    action_keywords = ["will", "can", "next", "step", "help", "assist"]
    action_score = sum(1 for kw in action_keywords if kw in _normalize(reply_text)) / len(action_keywords)
    
    tone_keyword_score = _keyword_fraction(reply_text, task.empathy_keywords)
    reply_score = round((0.5 * reply_keyword_score) + (0.3 * reply_length_score) + (0.2 * action_score), 4)
    tone_score = round((0.6 * tone_keyword_score) + (0.4 * reply_length_score), 4)
    
    # Policy compliance scoring (12% weight) - Enhanced
    forbidden_hits = sum(
        1 for keyword in task.forbidden_reply_keywords 
        if _normalize(keyword) in _normalize(reply_text)
    )
    
    # Stricter compliance - any forbidden keyword = severe penalty
    compliance_score = 1.0
    if forbidden_hits:
        compliance_score = max(0.0, 1.0 - (forbidden_hits * 0.5))
    
    # Bonus for safety keywords in security-related tasks
    if task.task_id in ["security_incident_hard", "account_takeover"]:
        safety_keywords = ["freeze", "secure", "protect", "immediately", "urgent"]
        safety_mentions = sum(1 for kw in safety_keywords if kw in _normalize(reply_text))
        compliance_score = min(1.0, compliance_score + (safety_mentions * 0.05))
    
    # Calculate total score with weighted components
    total_score = round(
        (0.45 * structured_score)
        + (0.18 * note_score)
        + (0.20 * reply_score)
        + (0.12 * compliance_score)
        + (0.05 * tone_score),
        4,
    )
    
    # Cap score based on critical errors
    if "missing_critical" in str(edge_cases):
        total_score = min(total_score, 0.85)
    
    if "forbidden_keywords" in str(edge_cases):
        total_score = min(total_score, 0.75)
    
    breakdown = {
        "routing_and_resolution": round(structured_score, 4),
        "internal_note_quality": round(note_score, 4),
        "customer_reply_quality": round(reply_score, 4),
        "policy_compliance": round(compliance_score, 4),
        "tone_and_clarity": round(tone_score, 4),
        "critical_fields_correct": round(critical_correct, 4),
    }
    
    # Generate detailed feedback
    feedback: List[str] = []
    
    # 1. Evidence and rationale in notes
    if note_score >= 0.9:
        feedback.append("✓ Internal notes provide clear evidence and rationale for your decision.")
    elif note_score >= 0.7:
        feedback.append("⚠ Internal notes are present but could include more evidence or clearer rationale.")
    else:
        feedback.append("✗ Internal notes are missing key evidence or reasoning steps. Add specific details.")
    
    # 2. Policy alignment
    if compliance_score == 1.0:
        feedback.append("✓ Actions comply with policy and avoid over-promising outcomes.")
    elif compliance_score >= 0.8:
        feedback.append("⚠ Most actions comply with policy, but review for any over-promising language.")
    else:
        feedback.append("✗ Policy compliance issue detected. Review policy checklist carefully.")
    
    # 3. Empathy and clarity
    if tone_score >= 0.85:
        feedback.append("✓ Customer reply shows excellent empathy and clarity.")
    elif tone_score >= 0.65:
        feedback.append("⚠ Customer reply shows some empathy, but could be clearer or more supportive.")
    else:
        feedback.append("✗ Customer reply lacks empathy. Consider the customer's perspective more carefully.")
    
    # 4. Actionable next steps
    if reply_score >= 0.9:
        feedback.append("✓ Customer reply provides clear next steps and references relevant policy.")
    elif reply_score >= 0.7:
        feedback.append("⚠ Customer reply is mostly clear, but could better reference next steps or policy.")
    else:
        feedback.append("✗ Customer reply is missing clear next steps. Specify what happens next.")
    
    # 5. Routing quality
    if routing_aligned:
        feedback.append("✓ Case routing perfectly matches operational owner and issue type.")
    else:
        feedback.append("⚠ Case routing or issue type could be improved. Double-check operational owner.")
    
    # 6. Priority alignment
    priority_correct = field_scores.get("priority", 0) == 1.0
    escalation_correct = field_scores.get("escalation_team", 0) == 1.0
    if priority_correct and escalation_correct:
        feedback.append("✓ Priority and escalation reflect the risk level and incident context perfectly.")
    else:
        feedback.append("⚠ Priority or escalation could be better aligned with incident risk.")
    
    # Confidence calculation
    confidence = round(
        (0.3 * structured_score) + 
        (0.2 * note_score) + 
        (0.2 * reply_score) + 
        (0.2 * compliance_score) + 
        (0.1 * (1.0 if not edge_cases else 0.5)),
        2
    )
    
    return GradeReport(
        total_score=total_score,
        public_breakdown=breakdown,
        feedback=feedback,
        field_scores=field_scores,
        edge_cases_handled=edge_cases,
        confidence=confidence,
    )


def validate_grader_determinism(task: TaskSpec, workspace: Dict[str, Any], runs: int = 10) -> bool:
    """
    Validate that the grader produces deterministic results.
    Returns True if all runs produce identical scores.
    """
    scores = []
    for _ in range(runs):
        report = grade_workspace(task, workspace)
        scores.append(report.total_score)
    
    return len(set(scores)) == 1


def get_grader_statistics(task: TaskSpec, num_samples: int = 100) -> Dict[str, float]:
    """
    Generate statistics about grader behavior for testing.
    """
    import random
    
    scores = []
    for _ in range(num_samples):
        # Random workspace
        workspace = {
            "issue_type": random.choice([task.expected_fields.get("issue_type", ""), "wrong_type", ""]),
            "priority": random.choice([task.expected_fields.get("priority", ""), "low", ""]),
            "queue": random.choice([task.expected_fields.get("queue", ""), "wrong_queue", ""]),
            "internal_notes": ["Sample note with some content"] if random.random() > 0.3 else [],
            "customer_reply": "Reply with refund and 5-7 business days mentioned." if random.random() > 0.3 else "Short.",
        }
        
        report = grade_workspace(task, workspace)
        scores.append(report.total_score)
    
    from statistics import mean, stdev, median
    
    return {
        "mean_score": round(mean(scores), 4),
        "median_score": round(median(scores), 4),
        "std_dev": round(stdev(scores), 4) if len(scores) > 1 else 0,
        "min_score": round(min(scores), 4),
        "max_score": round(max(scores), 4),
        "perfect_scores": sum(1 for s in scores if s >= 0.95),
        "failing_scores": sum(1 for s in scores if s < 0.5),
    }
