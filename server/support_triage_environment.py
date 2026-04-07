"""Core environment logic for the support triage benchmark."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Dict, Optional
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import EnvironmentMetadata

try:
    from ..graders import GradeReport, grade_workspace
    from ..knowledge_base import get_knowledge_base
    from ..models import (
        SupportTriageAction,
        SupportTriageObservation,
        SupportTriageState,
    )
    from ..tasks import ALLOWED_FIELD_VALUES, TASKS, TaskSpec, task_catalog
except ImportError:
    from graders import GradeReport, grade_workspace
    from knowledge_base import get_knowledge_base
    from models import SupportTriageAction, SupportTriageObservation, SupportTriageState
    from tasks import ALLOWED_FIELD_VALUES, TASKS, TaskSpec, task_catalog


class SupportTriageEnvironment(
    Environment[SupportTriageAction, SupportTriageObservation, SupportTriageState]
):
    """Simulated support triage workspace with dense deterministic rewards."""

    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self) -> None:
        self._state = SupportTriageState(episode_id=str(uuid4()), step_count=0)
        self._task: Optional[TaskSpec] = None
        self._kb = get_knowledge_base()
        self._retrieved_context: list[str] = []

    def get_metadata(self) -> EnvironmentMetadata:
        return EnvironmentMetadata(
            name="support-triage-env",
            description=(
                "A customer-operations triage benchmark where agents classify incidents, "
                "choose routing and resolution paths, record internal rationale, and "
                "draft policy-compliant customer replies."
            ),
            version="1.0.0",
        )

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        task_id: Optional[str] = None,
        **kwargs: Any,
    ) -> SupportTriageObservation:
        del seed, kwargs
        selected_task = TASKS.get(task_id or "billing_refund_easy")
        if selected_task is None:
            selected_task = TASKS["billing_refund_easy"]

        self._task = selected_task
        self._state = SupportTriageState(
            episode_id=episode_id or str(uuid4()),
            step_count=0,
            task_id=selected_task.task_id,
            submitted=False,
            workspace=self._empty_workspace(),
            score=0.0,
            score_breakdown={},
            feedback=[],
            last_action=None,
        )
        self._refresh_grade()
        return self._build_observation(
            reward=0.0,
            done=False,
            last_action_summary=f"Workspace reset for task {selected_task.task_id}.",
            last_action_error=False,
        )

    def step(
        self,
        action: SupportTriageAction,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> SupportTriageObservation:
        del timeout_s, kwargs
        if self._task is None:
            return self.reset()

        previous_score = self._state.score
        previous_workspace = deepcopy(self._state.workspace)
        self._state.step_count += 1

        canonical_action = json.dumps(action.model_dump(exclude_none=True), sort_keys=True)
        is_repeat = canonical_action == self._state.last_action
        self._state.last_action = canonical_action

        summary = ""
        is_error = False
        penalty = -0.01

        if self._state.submitted:
            summary = "Episode already submitted; reset to start a new task."
            is_error = True
            penalty -= 0.05
        else:
            summary, is_error, penalty = self._apply_action(action, is_repeat=is_repeat)

        report = self._refresh_grade()
        current_score = self._state.score
        reward = round((current_score - previous_score) + penalty, 4)

        done = False
        if self._state.submitted:
            done = True
            reward = round(reward + (0.06 if current_score >= 0.88 else -0.06), 4)
        elif self._state.step_count >= self._task.max_steps:
            done = True
            reward = round(reward - 0.03, 4)
            if not summary:
                summary = "Reached the maximum step budget."

        if not is_error and self._action_was_noop(previous_workspace):
            reward = round(reward - 0.03, 4)
            summary = summary + " The action did not materially change the workspace."

        return self._build_observation(
            reward=reward,
            done=done,
            last_action_summary=summary,
            last_action_error=is_error,
        )

    @property
    def state(self) -> SupportTriageState:
        return self._state

    def _empty_workspace(self) -> Dict[str, Any]:
        return {
            "issue_type": "",
            "priority": "",
            "queue": "",
            "refund_action": "",
            "escalation_team": "",
            "internal_notes": [],
            "customer_reply": "",
        }

    def _apply_action(
        self, action: SupportTriageAction, *, is_repeat: bool
    ) -> tuple[str, bool, float]:
        assert self._task is not None
        workspace = self._state.workspace

        penalty = -0.01
        if is_repeat:
            penalty -= 0.035

        if action.kind == "set_field":
            assert action.field_name is not None
            assert action.value is not None
            allowed_values = ALLOWED_FIELD_VALUES[action.field_name]
            if action.value not in allowed_values:
                return (
                    f"Rejected {action.field_name}={action.value!r}; use one of {allowed_values}.",
                    True,
                    penalty - 0.07,
                )
            workspace[action.field_name] = action.value
            return (f"Set {action.field_name} to {action.value}.", False, penalty)

        if action.kind == "add_note":
            assert action.text is not None
            note = " ".join(action.text.strip().split())
            if not note:
                return ("Internal note was empty.", True, penalty - 0.05)
            notes = workspace.setdefault("internal_notes", [])
            notes.append(note)
            if len(notes) > 4:
                del notes[0]
            if len(note.split()) < 5:
                penalty -= 0.02
            return ("Added an internal note.", False, penalty)

        if action.kind == "draft_reply":
            assert action.text is not None
            reply = " ".join(action.text.strip().split())
            if not reply:
                return ("Customer reply was empty.", True, penalty - 0.05)
            workspace["customer_reply"] = reply
            if len(reply.split()) < 15:
                penalty -= 0.025
            return ("Updated the customer reply draft.", False, penalty)

        if action.kind == "submit":
            self._state.submitted = True
            return ("Submitted the triage decision for grading.", False, penalty)

        if action.kind == "retrieve":
            assert action.query is not None
            results = self._kb.retrieve(action.query, top_k=3)
            self._retrieved_context = results
            if results:
                return (f"Retrieved {len(results)} relevant knowledge base articles.", False, penalty)
            else:
                return ("No relevant articles found in knowledge base.", False, penalty)

        return (f"Unknown action kind: {action.kind}.", True, penalty - 0.06)

    def _refresh_grade(self) -> GradeReport:
        assert self._task is not None
        report = grade_workspace(self._task, self._state.workspace)
        self._state.score = report.total_score
        self._state.score_breakdown = report.public_breakdown
        self._state.feedback = report.feedback
        return report

    def _action_was_noop(self, previous_workspace: Dict[str, Any]) -> bool:
        return previous_workspace == self._state.workspace

    def _build_observation(
        self,
        *,
        reward: float,
        done: bool,
        last_action_summary: str,
        last_action_error: bool,
    ) -> SupportTriageObservation:
        assert self._task is not None
        remaining_steps = max(self._task.max_steps - self._state.step_count, 0)

        workspace = deepcopy(self._state.workspace)
        if done and self._state.submitted:
            workspace["final_score"] = self._state.score

        return SupportTriageObservation(
            task_id=self._task.task_id,
            task_title=self._task.title,
            difficulty=self._task.difficulty,
            goal=self._task.goal,
            customer_profile=self._task.customer_profile,
            customer_ticket=self._task.customer_ticket,
            context_cards=self._task.context_cards,
            policy_checklist=self._task.policy_checklist,
            available_fields=ALLOWED_FIELD_VALUES,
            current_workspace=workspace,
            feedback=self._state.feedback,
            score=self._state.score,
            score_breakdown=self._state.score_breakdown,
            last_action_summary=last_action_summary,
            last_action_error=last_action_error,
            remaining_steps=remaining_steps,
            available_tasks=task_catalog(),
            knowledge_base_context=self._retrieved_context,
            reward=reward,
            done=done,
            metadata={
                "submitted": self._state.submitted,
                "step_count": self._state.step_count,
            },
        )
