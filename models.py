"""Typed models for the support triage environment."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from openenv.core.env_server.types import Action, Observation, State
from pydantic import Field, model_validator


EditableField = Literal[
    "issue_type",
    "priority",
    "queue",
    "refund_action",
    "escalation_team",
]

ActionKind = Literal["set_field", "add_note", "draft_reply", "submit", "retrieve"]


class SupportTriageAction(Action):
    """Single step an agent can take in the support workspace."""

    kind: ActionKind = Field(..., description="The action category to execute")
    field_name: Optional[EditableField] = Field(
        default=None,
        description="Structured field to edit when kind is set_field",
    )
    value: Optional[str] = Field(
        default=None,
        description="New value for the selected field when kind is set_field",
    )
    text: Optional[str] = Field(
        default=None,
        description="Free-form note or customer reply text",
    )
    query: Optional[str] = Field(
        default=None,
        description="Query for knowledge base retrieval when kind is retrieve",
    )

    @model_validator(mode="after")
    def validate_payload(self) -> "SupportTriageAction":
        if self.kind == "set_field":
            if self.field_name is None or self.value is None:
                raise ValueError("set_field requires field_name and value")
        elif self.kind in {"add_note", "draft_reply"} and not self.text:
            raise ValueError(f"{self.kind} requires text")
        elif self.kind == "retrieve" and not self.query:
            raise ValueError("retrieve requires query")
        return self


class SupportTriageObservation(Observation):
    """Agent-facing observation for the support triage task."""

    task_id: str = Field(..., description="Current task identifier")
    task_title: str = Field(..., description="Human-readable task title")
    difficulty: str = Field(..., description="Difficulty label")
    goal: str = Field(..., description="Concrete objective the agent should complete")
    customer_profile: str = Field(..., description="Compact customer profile")
    customer_ticket: str = Field(..., description="Ticket text the agent is handling")
    context_cards: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Operational evidence cards relevant to the case",
    )
    policy_checklist: List[str] = Field(
        default_factory=list,
        description="Policy bullets the agent should follow",
    )
    available_fields: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Allowed values for each editable structured field",
    )
    current_workspace: Dict[str, Any] = Field(
        default_factory=dict,
        description="Current structured fields, notes, and drafted reply",
    )
    feedback: List[str] = Field(
        default_factory=list,
        description="High-level coaching signals from the deterministic grader",
    )
    score: float = Field(default=0.0, description="Current deterministic grader score")
    score_breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="High-level component score breakdown",
    )
    last_action_summary: str = Field(
        default="",
        description="Short summary of what the previous action changed",
    )
    last_action_error: bool = Field(
        default=False,
        description="Whether the previous action was invalid or harmful",
    )
    remaining_steps: int = Field(
        default=0,
        description="How many steps remain before the episode auto-terminates",
    )
    available_tasks: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Available benchmark tasks for reset(task_id=...)",
    )
    knowledge_base_context: List[str] = Field(
        default_factory=list,
        description="Retrieved knowledge base articles relevant to the current ticket",
    )


class SupportTriageState(State):
    """Internal environment state."""

    task_id: Optional[str] = Field(default=None, description="Current task identifier")
    submitted: bool = Field(default=False, description="Whether the task was submitted")
    workspace: Dict[str, Any] = Field(
        default_factory=dict,
        description="Full mutable workspace contents",
    )
    score: float = Field(default=0.0, description="Current task score")
    score_breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="High-level deterministic component scores",
    )
    feedback: List[str] = Field(
        default_factory=list,
        description="Latest non-leaky grader feedback",
    )
    last_action: Optional[str] = Field(
        default=None,
        description="Canonical representation of the most recent action",
    )
