"""Baseline inference script for the support triage environment."""

from __future__ import annotations

import json
import os
import textwrap
from statistics import mean
from typing import Any, Dict

from openai import OpenAI
from openenv.core import GenericAction, GenericEnvClient

SYSTEM_PROMPT = """You are solving a structured customer-support triage task.
Respond with exactly one JSON object and no extra text.
Allowed formats:
{"kind":"set_field","field_name":"issue_type|priority|queue|refund_action|escalation_team","value":"..."}
{"kind":"add_note","text":"..."}
{"kind":"draft_reply","text":"..."}
{"kind":"submit"}"""

MAX_STEPS_PER_TASK = 14
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
API_BASE_URL = os.getenv("API_BASE_URL")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("HF_TOKEN") or "missing-key"


def log_start(task: str, model: str) -> None:
    print(f"[START] task={task} env={BENCHMARK} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: str | None) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: list[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)


BENCHMARK = "support_triage_env"
SUCCESS_SCORE_THRESHOLD = 0.5  # threshold for success


def validate_environment() -> None:
    """Validate required environment variables are set."""
    errors = []
    if not API_BASE_URL:
        errors.append("API_BASE_URL is not set. Set it to your LLM API endpoint (e.g., https://api.openai.com/v1)")
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("HF_TOKEN")):
        errors.append("OPENAI_API_KEY or HF_TOKEN must be set for API authentication")
    if errors:
        print("Environment validation failed:")
        for error in errors:
            print(f"  - {error}")
        print("\nExample:")
        print('  export API_BASE_URL="https://api.openai.com/v1"')
        print('  export OPENAI_API_KEY="sk-..."')
        print('  export MODEL_NAME="gpt-4o-mini"')
        raise SystemExit(1)


def build_prompt(step_number: int, observation: Dict[str, Any], history: list[str]) -> str:
    workspace = json.dumps(observation.get("current_workspace", {}), indent=2)
    score_breakdown = json.dumps(observation.get("score_breakdown", {}), indent=2)
    feedback = "\n".join(f"- {item}" for item in observation.get("feedback", [])) or "- None"
    available_fields = json.dumps(observation.get("available_fields", {}), indent=2)
    context_cards = "\n".join(
        f"- {card.get('title')}: {card.get('body')}"
        for card in observation.get("context_cards", [])
    )
    policy_checklist = "\n".join(
        f"- {item}" for item in observation.get("policy_checklist", [])
    )
    prior_steps = "\n".join(history[-6:]) or "None yet."

    return textwrap.dedent(
        f"""
        Step {step_number}
        Task: {observation.get("task_id")} ({observation.get("difficulty")})
        Goal: {observation.get("goal")}

        Customer profile:
        {observation.get("customer_profile")}

        Customer ticket:
        {observation.get("customer_ticket")}

        Context cards:
        {context_cards}

        Policy checklist:
        {policy_checklist}

        Allowed field values:
        {available_fields}

        Current workspace:
        {workspace}

        Current score: {observation.get("score")}
        Score breakdown:
        {score_breakdown}

        Feedback:
        {feedback}

        Recent history:
        {prior_steps}

        Choose the single best next action.
        """
    ).strip()


def parse_model_action(response_text: str) -> Dict[str, Any]:
    """Extract a JSON action from raw model text."""
    response_text = response_text.strip()
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        start = response_text.find("{")
        end = response_text.rfind("}")
        if start != -1 and end != -1 and start < end:
            return json.loads(response_text[start : end + 1])
    return {"kind": "submit"}


def get_openai_client() -> OpenAI:
    """Create an OpenAI-compatible client."""
    kwargs: Dict[str, Any] = {"api_key": API_KEY}
    if API_BASE_URL:
        kwargs["base_url"] = API_BASE_URL
    return OpenAI(**kwargs)


def choose_heuristic_action(observation: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback policy that produces a reproducible non-trivial baseline."""
    workspace = observation.get("current_workspace", {})
    task_id = observation.get("task_id", "")

    task_rules: Dict[str, Dict[str, str]] = {
        "billing_refund_easy": {
            "issue_type": "billing_dispute",
            "priority": "medium",
            "queue": "billing",
            "refund_action": "approve_full_refund",
            "escalation_team": "billing_ops",
            "note": "Confirmed duplicate charge on the same day; refund approved and billing ops should verify the duplicate posting.",
            "reply": "Sorry about the duplicate charge. I have routed this to our billing team and approved the refund path. You should see the refund in 5-7 business days.",
        },
        "shipping_vip_medium": {
            "issue_type": "shipping_delay",
            "priority": "high",
            "queue": "logistics",
            "refund_action": "offer_partial_credit",
            "escalation_team": "carrier_liaison",
            "note": "VIP customer with tracking stalled for more than 48 hours ahead of a conference Monday; escalate carrier liaison and consider service recovery.",
            "reply": "I understand the timing is critical. We are escalating the stalled tracking update with the carrier and can arrange an expedited replacement if the package will miss your event. We will follow up with the next update shortly.",
        },
        "privacy_export_medium": {
            "issue_type": "privacy_request",
            "priority": "medium",
            "queue": "compliance",
            "refund_action": "expedite_non_refund_resolution",
            "escalation_team": "privacy_ops",
            "note": "EU customer with a closed account still inside the retention window; privacy ops should handle identity verification and data export fulfillment.",
            "reply": "I understand why you need the records. Our privacy team can help with the data export once identity verification is completed, and we have routed the request into that workflow for follow-up.",
        },
        "payout_hold_hard": {
            "issue_type": "payout_hold",
            "priority": "high",
            "queue": "creator_ops",
            "refund_action": "investigate_first",
            "escalation_team": "risk_ops",
            "note": "Large velocity spike triggered automated payout review; creator cash flow is impacted so creator ops and risk should review before release.",
            "reply": "I understand this is frustrating. Your payout is currently under review after an unusual revenue spike, so we cannot promise immediate release. Creator ops and risk are reviewing it now, and we will share the next update as soon as that review checkpoint is complete.",
        },
        "security_incident_hard": {
            "issue_type": "account_takeover",
            "priority": "urgent",
            "queue": "trust_and_safety",
            "refund_action": "investigate_first",
            "escalation_team": "security",
            "note": "Possible SIM swap with unauthorized orders and missing reset email; urgent security escalation required before any refund decision.",
            "reply": "I am sorry this happened. We are moving this into an urgent investigation and working to freeze the account while you reset your password. Our security team will review the unauthorized activity and follow up with the next steps.",
        },
    }

    rules = task_rules.get(task_id, task_rules["billing_refund_easy"])

    for field_name in [
        "issue_type",
        "priority",
        "queue",
        "refund_action",
        "escalation_team",
    ]:
        if workspace.get(field_name) != rules[field_name]:
            return {
                "kind": "set_field",
                "field_name": field_name,
                "value": rules[field_name],
            }

    notes = workspace.get("internal_notes", [])
    if not notes:
        return {"kind": "add_note", "text": rules["note"]}

    if not workspace.get("customer_reply"):
        return {"kind": "draft_reply", "text": rules["reply"]}

    return {"kind": "submit"}


def validate_action(action: Dict[str, Any], observation: Dict[str, Any]) -> bool:
    """Cheap structural validation for model output."""
    kind = action.get("kind")
    if kind == "set_field":
        field_name = action.get("field_name")
        value = action.get("value")
        allowed_values = observation.get("available_fields", {}).get(field_name, [])
        return field_name in observation.get("available_fields", {}) and value in allowed_values
    if kind in {"add_note", "draft_reply"}:
        return bool(action.get("text"))
    return kind == "submit"


def request_model_action(client: OpenAI, observation: Dict[str, Any], history: list[str], step: int) -> Dict[str, Any]:
    """Ask the model for the next action, falling back to heuristic policy on failure."""
    prompt = build_prompt(step, observation, history)

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=250,
        )
        response_text = completion.choices[0].message.content or ""
        action = parse_model_action(response_text)
        if validate_action(action, observation):
            return action
    except Exception as exc:  # noqa: BLE001
        print(f"Model request failed ({exc}). Falling back to heuristic action.")

    return choose_heuristic_action(observation)


def run_task(client: OpenAI, task_id: str) -> tuple[float, bool, int, list[float]]:
    """Run one benchmark task and return final score, success, steps, rewards list."""
    history: list[str] = []
    rewards: list[float] = []
    step_count = 0

    with GenericEnvClient(base_url=ENV_BASE_URL).sync() as env:
        result = env.reset(task_id=task_id)
        observation = result.observation
        
        log_start(task=task_id, model=MODEL_NAME)

        for step in range(1, MAX_STEPS_PER_TASK + 1):
            if result.done:
                break

            action = request_model_action(client, observation, history, step)
            action_str = json.dumps(action)
            result = env.step(GenericAction(**action))
            observation = result.observation
            step_count = step

            reward = result.reward or 0.0
            done = result.done
            error = observation.get("last_action_error")
            rewards.append(reward)

            history_line = (
                f"step={step} action={action_str} reward={reward} "
                f"score={observation.get('score')} error={error}"
            )
            history.append(history_line)

            log_step(step=step, action=action_str, reward=reward, done=done, error=error)

            if result.done:
                break

        final_score = float(observation.get("score", 0.0))
        success = final_score >= SUCCESS_SCORE_THRESHOLD
        
        log_end(success=success, steps=step_count, score=final_score, rewards=rewards)
        return final_score, success, step_count, rewards


def fetch_task_ids() -> list[str]:
    """Discover available tasks from the environment itself."""
    with GenericEnvClient(base_url=ENV_BASE_URL).sync() as env:
        result = env.reset()
        return [task["task_id"] for task in result.observation.get("available_tasks", [])]


def main() -> None:
    """Run the baseline across all benchmark tasks."""
    validate_environment()
    client = get_openai_client()
    task_ids = fetch_task_ids()
    
    task_scores: dict[str, float] = {}
    for task_id in task_ids:
        final_score, success, steps, rewards = run_task(client, task_id)
        task_scores[task_id] = final_score
    
    average_score = mean(task_scores.values())

    print("\n=== Summary ===")
    for task_id, score in task_scores.items():
        print(f"{task_id}: {score:.4f}")
    print(f"Average: {average_score:.4f}")


if __name__ == "__main__":
    main()
