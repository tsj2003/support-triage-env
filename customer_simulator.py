"""Customer simulator for multi-turn chat responses."""

from __future__ import annotations

from typing import Dict, List, Optional


class CustomerSimulator:
    """Simulates customer responses to agent replies in support tickets."""

    def __init__(self):
        self.response_patterns: Dict[str, List[Dict]] = {
            "billing_refund_easy": [
                {
                    "trigger": "refund",
                    "responses": [
                        "Thank you! When will I see the refund in my account?",
                        "Great, I appreciate the quick resolution.",
                        "5-7 business days? That's a bit long, but okay.",
                    ],
                },
                {
                    "trigger": "billing",
                    "responses": [
                        "Why was I charged twice in the first place?",
                        "Will this prevent it from happening again?",
                    ],
                },
            ],
            "shipping_vip_medium": [
                {
                    "trigger": "conference",
                    "responses": [
                        "The conference is on Monday! Will it arrive by then?",
                        "I'm really worried about missing my presentation.",
                        "Can you guarantee it arrives before Monday?",
                    ],
                },
                {
                    "trigger": "replacement",
                    "responses": [
                        "An expedited replacement would be great, thank you.",
                        "How quickly can you ship the replacement?",
                        "I need the replacement shipped overnight if possible.",
                    ],
                },
                {
                    "trigger": "tracking",
                    "responses": [
                        "The tracking hasn't updated in 2 days, what's happening?",
                        "Can you contact the carrier directly?",
                    ],
                },
            ],
            "privacy_export_medium": [
                {
                    "trigger": "GDPR",
                    "responses": [
                        "I need this data within 30 days as per GDPR.",
                        "What information exactly will be included in the export?",
                    ],
                },
                {
                    "trigger": "identity",
                    "responses": [
                        "What documents do you need for verification?",
                        "I can provide my passport and utility bill.",
                    ],
                },
            ],
            "payout_hold_hard": [
                {
                    "trigger": "review",
                    "responses": [
                        "This is really hurting my business cash flow.",
                        "How long will the review take? I need a timeline.",
                        "Can you at least release a partial amount?",
                        "This feels unfair - I've been a creator for 2 years with no issues.",
                    ],
                },
                {
                    "trigger": "spike",
                    "responses": [
                        "The revenue spike was from a viral video, not suspicious!",
                        "I've explained this before, why is it still held?",
                    ],
                },
            ],
            "security_incident_hard": [
                {
                    "trigger": "password",
                    "responses": [
                        "I've already reset my password twice.",
                        "What about the orders I didn't place?",
                    ],
                },
                {
                    "trigger": "security",
                    "responses": [
                        "How did someone get into my account?",
                        "Will I get refunded for the fraudulent orders?",
                        "This is really scary - should I be worried about my other accounts?",
                    ],
                },
            ],
        }

    def generate_response(
        self, task_id: str, agent_reply: str, conversation_history: List[Dict], step: int
    ) -> Optional[str]:
        """Generate a customer response based on agent's reply."""
        import random

        task_patterns = self.response_patterns.get(task_id, [])
        if not task_patterns:
            return None

        agent_reply_lower = agent_reply.lower()

        # Find matching patterns
        matching = []
        for pattern in task_patterns:
            if pattern["trigger"] in agent_reply_lower:
                matching.extend(pattern["responses"])

        # Add generic follow-ups if no specific match
        if not matching and len(conversation_history) >= 2:
            generic = [
                "Thanks for the update.",
                "I understand, please keep me posted.",
                "Is there anything else I need to do?",
                "When can I expect a resolution?",
            ]
            matching = generic

        # Return None if conversation is getting too long
        if len(conversation_history) >= 3:
            return None

        if matching:
            # Use step to deterministically select response
            idx = (step + hash(agent_reply) % len(matching)) % len(matching)
            return matching[idx]

        return None


# Global customer simulator instance
_sim_instance: CustomerSimulator | None = None


def get_customer_simulator() -> CustomerSimulator:
    """Get or create the global customer simulator instance."""
    global _sim_instance
    if _sim_instance is None:
        _sim_instance = CustomerSimulator()
    return _sim_instance
