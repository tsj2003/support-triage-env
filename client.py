"""Typed client for the support triage environment."""

from __future__ import annotations

from typing import Any, Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult

try:
    from .models import SupportTriageAction, SupportTriageObservation, SupportTriageState
except ImportError:
    from models import SupportTriageAction, SupportTriageObservation, SupportTriageState


class SupportTriageEnv(
    EnvClient[SupportTriageAction, SupportTriageObservation, SupportTriageState]
):
    """Convenience client for connecting to a support triage environment server."""

    def _step_payload(self, action: SupportTriageAction) -> Dict[str, Any]:
        return action.model_dump(exclude_none=True)

    def _parse_result(self, payload: Dict[str, Any]) -> StepResult[SupportTriageObservation]:
        observation = SupportTriageObservation.model_validate(payload.get("observation", {}))
        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict[str, Any]) -> SupportTriageState:
        return SupportTriageState.model_validate(payload)
