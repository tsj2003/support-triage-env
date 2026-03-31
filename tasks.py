"""Task fixtures for the support triage benchmark."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


ALLOWED_FIELD_VALUES: Dict[str, List[str]] = {
    "issue_type": [
        "billing_dispute",
        "shipping_delay",
        "account_takeover",
        "privacy_request",
        "payout_hold",
    ],
    "priority": ["low", "medium", "high", "urgent"],
    "queue": [
        "billing",
        "logistics",
        "trust_and_safety",
        "compliance",
        "creator_ops",
    ],
    "refund_action": [
        "none",
        "approve_full_refund",
        "offer_partial_credit",
        "investigate_first",
        "expedite_non_refund_resolution",
    ],
    "escalation_team": [
        "none",
        "billing_ops",
        "carrier_liaison",
        "security",
        "privacy_ops",
        "risk_ops",
    ],
}


@dataclass(frozen=True)
class TaskSpec:
    """Immutable benchmark task definition."""

    task_id: str
    title: str
    difficulty: str
    goal: str
    customer_profile: str
    customer_ticket: str
    context_cards: List[Dict[str, str]]
    policy_checklist: List[str]
    expected_fields: Dict[str, str]
    required_reply_keywords: List[str]
    required_note_keywords: List[str]
    empathy_keywords: List[str] = field(default_factory=lambda: ["understand", "sorry"])
    forbidden_reply_keywords: List[str] = field(default_factory=list)
    reply_min_words: int = 30
    reply_max_words: int = 110
    max_steps: int = 12


TASKS: Dict[str, TaskSpec] = {
    "billing_refund_easy": TaskSpec(
        task_id="billing_refund_easy",
        title="Duplicate annual subscription charge",
        difficulty="easy",
        goal=(
            "Resolve a duplicate billing complaint by investigating the transaction history, "
            "identifying the root cause, and communicating a clear, policy-compliant resolution."
        ),
        customer_profile=(
            "Customer Maya Patel. Tenure: 3 years. Plan: Pro Annual. "
            "No prior disputes. LTV: high. Payment method: credit card."
        ),
        customer_ticket=(
            "I was charged twice for my annual renewal today. I only meant to renew "
            "once. Please fix it and tell me when the money will be back in my account."
        ),
        context_cards=[
            {
                "title": "Billing Timeline",
                "body": "Two identical renewal charges posted within 9 minutes on the same card ending 1128. Both charges authorized, but only one invoice generated."
            },
            {
                "title": "Risk Signals",
                "body": "No fraud indicators. Login location matches historical pattern. Device fingerprint unchanged."
            },
            {
                "title": "Support History",
                "body": "Customer has never requested a refund or chargeback before."
            },
            {
                "title": "Policy Reference",
                "body": "Refunds for duplicate charges are processed within 5-7 business days."
            },
        ],
        policy_checklist=[
            "Investigate transaction logs for duplicate authorizations.",
            "Confirm that only one subscription renewal was intended.",
            "Check for any system errors or double-click events.",
            "Route to Billing queue if duplicate confirmed.",
            "Full refund is appropriate if no fraud or abuse is detected.",
            "Communicate expected refund timeline and set customer expectations.",
            "Document rationale for refund approval in internal notes.",
            "Do not promise instant reversal; clarify standard processing time.",
        ],
        expected_fields={
            "issue_type": "billing_dispute",
            "priority": "medium",
            "queue": "billing",
            "refund_action": "approve_full_refund",
            "escalation_team": "billing_ops",
        },
        required_reply_keywords=["refund", "5-7 business days", "duplicate charge"],
        required_note_keywords=["duplicate charge", "transaction log", "refund approved", "processing time"],
        empathy_keywords=["sorry", "understand"],
        max_steps=10,
    ),
    "shipping_vip_medium": TaskSpec(
        task_id="shipping_vip_medium",
        title="VIP order delayed before a conference",
        difficulty="medium",
        goal=(
            "Triage a time-sensitive logistics incident for a VIP customer, analyze operational constraints, and draft a reply with a credible, policy-aligned next step."
        ),
        customer_profile=(
            "Customer Jordan Lee. Segment: VIP. Upcoming event: conference on Monday. "
            "Order contains launch materials. Prior orders always on time."
        ),
        customer_ticket=(
            "My package was promised by Friday but tracking hasn't moved for three days. "
            "I need it for a conference on Monday. Can you help or send another one?"
        ),
        context_cards=[
            {
                "title": "Tracking Snapshot",
                "body": "Carrier status has been stuck at regional hub for 72 hours. No delivery ETA available."
            },
            {
                "title": "Order Notes",
                "body": "Priority shipping purchased. No prior replacement shipped. Customer has VIP flag."
            },
            {
                "title": "Carrier Policy",
                "body": "Expedited replacement can be issued if original shipment is delayed beyond 48 hours for VIPs."
            },
            {
                "title": "Event Details",
                "body": "Conference is on Monday. Materials are required for product launch."
            },
        ],
        policy_checklist=[
            "Review tracking and carrier status for operational delays.",
            "Escalate to Carrier Liaison if tracking is stalled for more than 48 hours.",
            "Offer a partial credit if original SLA is likely missed.",
            "Arrange expedited replacement if event is at risk.",
            "Communicate realistic delivery options and set expectations.",
            "Document escalation and customer impact in internal notes.",
            "Do not promise delivery before confirming with carrier."
        ],
        expected_fields={
            "issue_type": "shipping_delay",
            "priority": "high",
            "queue": "logistics",
            "refund_action": "offer_partial_credit",
            "escalation_team": "carrier_liaison",
        },
        required_reply_keywords=[
            "tracking",
            "carrier",
            "expedited replacement",
        ],
        required_note_keywords=[
            "vip customer",
            "tracking stalled",
            "conference monday",
            "carrier escalation",
        ],
        empathy_keywords=["understand", "help"],
    ),
    "privacy_export_medium": TaskSpec(
        task_id="privacy_export_medium",
        title="Account data export after account closure",
        difficulty="medium",
        goal=(
            "Handle a privacy workflow request that needs the correct compliance routing "
            "and a non-refund operational resolution."
        ),
        customer_profile=(
            "Customer Nia Brooks. Account closed 14 days ago. Region: EU. "
            "No security flags."
        ),
        customer_ticket=(
            "I closed my account two weeks ago and now need a copy of my purchase history "
            "and account data for my records. I couldn't find a download option anymore."
        ),
        context_cards=[
            {
                "title": "Lifecycle State",
                "body": "Account is closed but data retention window remains active for 30 days.",
            },
            {
                "title": "Jurisdiction",
                "body": "EU customer, privacy requests must be handled by the compliance workflow.",
            },
        ],
        policy_checklist=[
            "Data export and access requests route to Compliance.",
            "These are usually medium priority unless there is a legal escalation timer.",
            "Do not promise a refund; this is a service request, not a billing dispute.",
            "Use the privacy operations team for fulfillment.",
            "Reply should mention identity verification and the export process.",
        ],
        expected_fields={
            "issue_type": "privacy_request",
            "priority": "medium",
            "queue": "compliance",
            "refund_action": "expedite_non_refund_resolution",
            "escalation_team": "privacy_ops",
        },
        required_reply_keywords=[
            "identity verification",
            "data export",
            "privacy team",
        ],
        required_note_keywords=[
            "eu customer",
            "closed account",
            "retention window",
        ],
        empathy_keywords=["happy to help", "understand"],
        forbidden_reply_keywords=["refund", "money back"],
    ),
    "payout_hold_hard": TaskSpec(
        task_id="payout_hold_hard",
        title="Creator payout hold after velocity spike",
        difficulty="hard",
        goal=(
            "Review a creator payout complaint that touches trust, finance, and risk. "
            "The agent must choose the right route without promising immediate release."
        ),
        customer_profile=(
            "Creator Sam Ortega. Top 2% marketplace seller. Weekly payouts enabled. "
            "Recent 4x revenue spike from a single campaign."
        ),
        customer_ticket=(
            "My payout was put on hold right after my campaign went viral. I have invoices "
            "to pay and need the funds released today. Please tell me why this happened."
        ),
        context_cards=[
            {
                "title": "Risk Console",
                "body": "Velocity spike triggered automated payout review; no confirmed fraud outcome yet.",
            },
            {
                "title": "Finance Notes",
                "body": "Funds are temporarily held pending creator-ops and risk review.",
            },
        ],
        policy_checklist=[
            "Payout holds route to Creator Ops with risk escalation when triggered by anomalies.",
            "Severity is high because the issue blocks creator cash flow, but not urgent without confirmed compromise.",
            "Do not promise immediate release before review completes.",
            "Use investigate_first as the resolution path.",
            "Reply should mention review status, requested patience, and the next checkpoint.",
        ],
        expected_fields={
            "issue_type": "payout_hold",
            "priority": "high",
            "queue": "creator_ops",
            "refund_action": "investigate_first",
            "escalation_team": "risk_ops",
        },
        required_reply_keywords=[
            "review",
            "next update",
            "cannot promise immediate release",
        ],
        required_note_keywords=[
            "velocity spike",
            "automated payout review",
            "creator cash flow",
        ],
        empathy_keywords=["understand", "frustrating"],
        forbidden_reply_keywords=["released today", "guarantee"],
    ),
    "security_incident_hard": TaskSpec(
        task_id="security_incident_hard",
        title="Possible account takeover after SIM swap",
        difficulty="hard",
        goal=(
            "Handle a high-risk account security ticket without over-promising refunds, "
            "and capture the correct evidence for urgent escalation."
        ),
        customer_profile=(
            "Customer Elena Ramirez. High order frequency. Two new orders in the last 12 hours. "
            "Phone number changed yesterday."
        ),
        customer_ticket=(
            "I think someone took over my account after my phone number was ported yesterday. "
            "I can see two orders I did not place and my password reset email never arrived. "
            "Please stop anything else from shipping and tell me what to do next."
        ),
        context_cards=[
            {
                "title": "Identity Signals",
                "body": "Password reset requests from a new device. SMS 2FA recently rerouted to a new number.",
            },
            {
                "title": "Orders at Risk",
                "body": "Two unfulfilled orders placed from an unfamiliar IP. No refund determination yet.",
            },
        ],
        policy_checklist=[
            "Potential account takeover is an urgent Trust and Safety incident.",
            "Escalate to Security immediately.",
            "Do not promise an instant refund before investigation.",
            "Customer reply should mention freezing the account and resetting credentials.",
            "Internal notes should capture SIM-swap suspicion and unauthorized order evidence.",
        ],
        expected_fields={
            "issue_type": "account_takeover",
            "priority": "urgent",
            "queue": "trust_and_safety",
            "refund_action": "investigate_first",
            "escalation_team": "security",
        },
        required_reply_keywords=[
            "freeze",
            "reset your password",
            "investigation",
        ],
        required_note_keywords=[
            "sim swap",
            "unauthorized orders",
            "security escalation",
        ],
        empathy_keywords=["sorry", "secure"],
        forbidden_reply_keywords=["full refund today", "guarantee a refund"],
    ),
}


def task_catalog() -> List[Dict[str, str]]:
    """Return a compact task list for observations and docs."""
    return [
        {
            "task_id": task.task_id,
            "difficulty": task.difficulty,
            "title": task.title,
        }
        for task in TASKS.values()
    ]
