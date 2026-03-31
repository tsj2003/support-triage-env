"""Synthetic Data Generator: Generate unlimited training scenarios."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


# Templates for generating synthetic support tickets
CUSTOMER_PROFILES = [
    {
        "name": "Enterprise Customer",
        "tenure": "5 years",
        "plan": "Enterprise",
        "ltv": "$2M",
        "characteristics": ["demanding", "professional", "expects SLA"],
    },
    {
        "name": "SMB Owner",
        "tenure": "1 year",
        "plan": "Business",
        "ltv": "$15K",
        "characteristics": ["cost-sensitive", "time-constrained", "frustrated easily"],
    },
    {
        "name": "Startup CTO",
        "tenure": "6 months",
        "plan": "Startup",
        "ltv": "$5K",
        "characteristics": ["technical", "impatient", "growth-focused"],
    },
    {
        "name": "Individual User",
        "tenure": "2 years",
        "plan": "Pro",
        "ltv": "$500",
        "characteristics": ["patient", "detail-oriented", "loyal"],
    },
    {
        "name": "Government Agency",
        "tenure": "3 years",
        "plan": "GovCloud",
        "ltv": "$500K",
        "characteristics": ["security-focused", "process-heavy", "compliance-driven"],
    },
]

ISSUE_TEMPLATES = {
    "billing": [
        {
            "subject": "Unexpected charge on my account",
            "templates": [
                "I was charged {amount} on {date} but I don't recognize this transaction. Can you help me understand what this is for?",
                "My credit card was charged {amount} but I thought I was on the {plan} plan. Please refund this charge.",
                "I see a duplicate charge for {amount} on my statement. This appears to be a billing error.",
            ],
            "amounts": ["$49.99", "$99.99", "$299.99", "$999.99"],
        },
        {
            "subject": "Refund request for cancelled service",
            "templates": [
                "I cancelled my subscription on {date} but was still charged for this month. I need a refund.",
                "Your cancellation process didn't work and I was charged again. I want my money back.",
            ],
            "amounts": ["$49.99", "$199.99"],
        },
    ],
    "technical": [
        {
            "subject": "API returning 500 errors",
            "templates": [
                "Our integration has been failing since {date}. The API returns 500 errors. This is blocking our production deployment.",
                "I'm getting consistent 500 errors on the /v1/users endpoint. Status page shows no incidents. What's going on?",
            ],
            "severity": ["critical", "high"],
        },
        {
            "subject": "Slow performance on dashboard",
            "templates": [
                "The dashboard takes {seconds} seconds to load. This started happening {duration} ago.",
                "Our team can't work efficiently because the UI is extremely slow. Is there a known issue?",
            ],
            "seconds": ["5-10", "15-30", "30+"],
            "durations": ["this week", "since yesterday", "for the past 3 days"],
        },
    ],
    "security": [
        {
            "subject": "Suspicious login activity",
            "templates": [
                "I received an alert about a login from {location} at {time}. I wasn't there. Has my account been compromised?",
                "There are transactions on my account I didn't make. I think someone accessed my account without permission.",
            ],
            "locations": ["Russia", "China", "Brazil", "Nigeria", "unfamiliar IP"],
        },
        {
            "subject": "Data export request (GDPR)",
            "templates": [
                "As per GDPR Article 15, I request a copy of all personal data you hold about me. Include processing purposes and retention periods.",
                "I want to exercise my right to data portability. Please provide my data in a machine-readable format.",
            ],
        },
    ],
    "feature": [
        {
            "subject": "Feature request: {feature}",
            "templates": [
                "We need {feature} for our workflow. Without this, we're considering switching to {competitor}.",
                "Is {feature} on your roadmap? This is a dealbreaker for our continued use.",
            ],
            "features": [
                "SSO with Okta",
                "advanced analytics",
                "custom integrations",
                "API rate limit increases",
                "HIPAA compliance",
            ],
            "competitors": ["CompetitorA", "CompetitorB", "another solution"],
        },
    ],
}


@dataclass
class SyntheticTicket:
    """Generated synthetic support ticket."""
    ticket_id: str
    customer_profile: Dict
    issue_type: str
    subject: str
    body: str
    priority: str
    expected_fields: Dict[str, str]
    difficulty: str
    created_at: str


class SyntheticDataGenerator:
    """Generate synthetic support tickets for training/evaluation."""
    
    def __init__(self, seed: Optional[int] = None) -> None:
        if seed is not None:
            random.seed(seed)
    
    def generate_ticket(
        self,
        issue_type: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> SyntheticTicket:
        """Generate a single synthetic ticket."""
        # Select issue type
        if issue_type is None:
            issue_type = random.choice(list(ISSUE_TEMPLATES.keys()))
        
        # Get templates for this issue type
        templates = ISSUE_TEMPLATES[issue_type]
        template = random.choice(templates)
        
        # Select customer profile
        profile = random.choice(CUSTOMER_PROFILES)
        
        # Generate subject
        subject = template["subject"]
        if "{feature}" in subject:
            subject = subject.format(feature=random.choice(template.get("features", ["enhancement"])))
        
        # Generate body with variables
        body_template = random.choice(template["templates"])
        body_vars = {}
        
        if "{amount}" in body_template:
            body_vars["amount"] = random.choice(template.get("amounts", ["$99.99"]))
        if "{date}" in body_template:
            days_ago = random.randint(1, 14)
            date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            body_vars["date"] = date
        if "{plan}" in body_template:
            body_vars["plan"] = profile["plan"]
        if "{location}" in body_template:
            body_vars["location"] = random.choice(template.get("locations", ["unknown location"]))
        if "{time}" in body_template:
            body_vars["time"] = f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}"
        if "{seconds}" in body_template:
            body_vars["seconds"] = random.choice(template.get("seconds", ["5-10"]))
        if "{duration}" in body_template:
            body_vars["duration"] = random.choice(template.get("durations", ["recently"]))
        if "{competitor}" in body_template:
            body_vars["competitor"] = random.choice(template.get("competitors", ["competitor"]))
        
        body = body_template.format(**body_vars)
        
        # Determine priority based on customer + issue
        priority = self._calculate_priority(profile, issue_type, template)
        
        # Determine difficulty
        if difficulty is None:
            difficulty = random.choice(["easy", "medium", "hard"])
        
        # Generate expected fields
        expected_fields = self._generate_expected_fields(issue_type, priority, profile)
        
        return SyntheticTicket(
            ticket_id=f"SYNTH_{random.randint(100000, 999999)}",
            customer_profile=profile,
            issue_type=issue_type,
            subject=subject,
            body=body,
            priority=priority,
            expected_fields=expected_fields,
            difficulty=difficulty,
            created_at=datetime.now().isoformat(),
        )
    
    def _calculate_priority(
        self,
        profile: Dict,
        issue_type: str,
        template: Dict,
    ) -> str:
        """Calculate appropriate priority."""
        base_priority = "medium"
        
        # Enterprise customers get higher priority
        if profile["plan"] == "Enterprise":
            base_priority = "high"
        
        # Security issues are urgent
        if issue_type == "security":
            return "urgent"
        
        # Technical issues with critical severity
        if issue_type == "technical" and template.get("severity"):
            if "critical" in template["severity"]:
                return "urgent"
        
        # Billing for high LTV customers
        if issue_type == "billing" and profile["ltv"].startswith("$"):
            ltv_value = int(profile["ltv"].replace("$", "").replace("K", "000").replace("M", "000000"))
            if ltv_value > 100000:
                base_priority = "high"
        
        return base_priority
    
    def _generate_expected_fields(
        self,
        issue_type: str,
        priority: str,
        profile: Dict,
    ) -> Dict[str, str]:
        """Generate expected routing fields."""
        fields = {
            "priority": priority,
        }
        
        # Issue type mapping
        issue_type_map = {
            "billing": "billing_dispute",
            "technical": "technical_issue",
            "security": "account_takeover",
            "feature": "feature_request",
        }
        fields["issue_type"] = issue_type_map.get(issue_type, "general")
        
        # Queue mapping
        queue_map = {
            "billing": "billing",
            "technical": "technical_support",
            "security": "trust_and_safety",
            "feature": "product_feedback",
        }
        fields["queue"] = queue_map.get(issue_type, "general")
        
        # Escalation team
        if profile["plan"] in ["Enterprise", "GovCloud"]:
            fields["escalation_team"] = "vip_support"
        elif issue_type == "security":
            fields["escalation_team"] = "security"
        else:
            fields["escalation_team"] = "none"
        
        # Refund action for billing
        if issue_type == "billing":
            fields["refund_action"] = "investigate_first"
        else:
            fields["refund_action"] = "none"
        
        return fields
    
    def generate_dataset(
        self,
        count: int = 100,
        issue_distribution: Optional[Dict[str, float]] = None,
        difficulty_distribution: Optional[Dict[str, float]] = None,
        output_path: Optional[str] = None,
    ) -> List[SyntheticTicket]:
        """Generate a dataset of synthetic tickets."""
        if issue_distribution is None:
            issue_distribution = {
                "billing": 0.25,
                "technical": 0.35,
                "security": 0.15,
                "feature": 0.25,
            }
        
        if difficulty_distribution is None:
            difficulty_distribution = {
                "easy": 0.4,
                "medium": 0.4,
                "hard": 0.2,
            }
        
        tickets = []
        for _ in range(count):
            issue_type = random.choices(
                list(issue_distribution.keys()),
                weights=list(issue_distribution.values()),
            )[0]
            
            difficulty = random.choices(
                list(difficulty_distribution.keys()),
                weights=list(difficulty_distribution.values()),
            )[0]
            
            ticket = self.generate_ticket(issue_type, difficulty)
            tickets.append(ticket)
        
        if output_path:
            self._save_dataset(tickets, output_path)
        
        return tickets
    
    def _save_dataset(self, tickets: List[SyntheticTicket], output_path: str) -> None:
        """Save dataset to file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = [
            {
                "ticket_id": t.ticket_id,
                "customer_profile": t.customer_profile,
                "issue_type": t.issue_type,
                "subject": t.subject,
                "body": t.body,
                "priority": t.priority,
                "expected_fields": t.expected_fields,
                "difficulty": t.difficulty,
                "created_at": t.created_at,
            }
            for t in tickets
        ]
        
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def generate_training_pairs(
        self,
        count: int = 100,
    ) -> List[Dict]:
        """Generate training pairs (ticket + expected actions)."""
        tickets = self.generate_dataset(count)
        
        pairs = []
        for ticket in tickets:
            # Generate expected actions based on expected fields
            actions = []
            for field, value in ticket.expected_fields.items():
                actions.append({
                    "kind": "set_field",
                    "field_name": field,
                    "value": value,
                })
            
            # Add suggested note
            note = f"{ticket.issue_type} issue for {ticket.customer_profile['plan']} customer. "
            note += f"Priority: {ticket.priority}. Route to {ticket.expected_fields.get('queue', 'general')}."
            actions.append({
                "kind": "add_note",
                "text": note,
            })
            
            # Add suggested reply
            reply = self._generate_reply(ticket)
            actions.append({
                "kind": "draft_reply",
                "text": reply,
            })
            
            actions.append({"kind": "submit"})
            
            pairs.append({
                "ticket": {
                    "ticket_id": ticket.ticket_id,
                    "subject": ticket.subject,
                    "body": ticket.body,
                    "customer_profile": ticket.customer_profile,
                },
                "expected_actions": actions,
                "expected_fields": ticket.expected_fields,
            })
        
        return pairs
    
    def _generate_reply(self, ticket: SyntheticTicket) -> str:
        """Generate a suggested customer reply."""
        templates = {
            "billing": [
                "Thank you for reaching out about this billing concern. We've reviewed your account and {resolution}. "
                "If you have any other questions, please let us know.",
            ],
            "technical": [
                "I understand this technical issue is impacting your work. Our engineering team is investigating {details}. "
                "We'll provide an update within {timeframe}.",
            ],
            "security": [
                "We take security very seriously. I've escalated this to our security team immediately. "
                "Please {action} while we investigate.",
            ],
            "feature": [
                "Thank you for this feature suggestion. I'll pass this along to our product team. "
                "While I can't guarantee timing, this type of feedback is valuable for our roadmap.",
            ],
        }
        
        template = random.choice(templates.get(ticket.issue_type, templates["technical"]))
        
        variables = {
            "billing": {
                "resolution": random.choice([
                    "found the source of the discrepancy",
                    "issued a refund to your account",
                    "corrected the billing error",
                ]),
            },
            "technical": {
                "details": random.choice([
                    "the root cause",
                    "a potential workaround",
                    "related system status",
                ]),
                "timeframe": random.choice(["2 hours", "24 hours", "by end of day"]),
            },
            "security": {
                "action": random.choice([
                    "change your password immediately",
                    "review recent account activity",
                    "enable two-factor authentication",
                ]),
            },
        }
        
        return template.format(**variables.get(ticket.issue_type, {}))


def main() -> None:
    """Demo synthetic data generator."""
    print("Synthetic Data Generator Demo")
    print("=" * 50)
    
    generator = SyntheticDataGenerator(seed=42)
    
    # Generate a few sample tickets
    print("\n📋 SAMPLE TICKETS:")
    for i in range(3):
        ticket = generator.generate_ticket()
        print(f"\n--- Ticket {i+1} ---")
        print(f"ID: {ticket.ticket_id}")
        print(f"Type: {ticket.issue_type} ({ticket.difficulty})")
        print(f"Customer: {ticket.customer_profile['name']} ({ticket.customer_profile['plan']})")
        print(f"Subject: {ticket.subject}")
        print(f"Priority: {ticket.priority}")
        print(f"Expected queue: {ticket.expected_fields.get('queue')}")
    
    # Generate small dataset
    print("\n📊 GENERATING DATASET:")
    dataset = generator.generate_dataset(
        count=50,
        output_path="./synthetic_data/tickets_50.json",
    )
    print(f"Generated {len(dataset)} tickets")
    
    # Show distribution
    issue_counts = {}
    difficulty_counts = {}
    for t in dataset:
        issue_counts[t.issue_type] = issue_counts.get(t.issue_type, 0) + 1
        difficulty_counts[t.difficulty] = difficulty_counts.get(t.difficulty, 0) + 1
    
    print("\nIssue type distribution:")
    for issue, count in issue_counts.items():
        print(f"  {issue}: {count} ({count/len(dataset):.1%})")
    
    print("\nDifficulty distribution:")
    for diff, count in difficulty_counts.items():
        print(f"  {diff}: {count} ({count/len(dataset):.1%})")
    
    print(f"\n✅ Dataset saved to ./synthetic_data/tickets_50.json")
    print("\n" + "=" * 50)
    print("Usage:")
    print("  generator = SyntheticDataGenerator(seed=42)")
    print("  tickets = generator.generate_dataset(count=1000)")
    print("  training_data = generator.generate_training_pairs(count=500)")


if __name__ == "__main__":
    main()
