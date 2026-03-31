"""Extended task domains: Email triage and Code review environments."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


# Email Triage Task Specifications
EMAIL_ALLOWED_FIELDS = {
    "email_type": [
        "urgent_request",
        "meeting_scheduling",
        "informational",
        "action_required",
        "fyi",
        "spam",
    ],
    "priority": ["low", "medium", "high", "urgent"],
    "response_action": [
        "reply_needed",
        "no_reply",
        "delegate",
        "schedule_meeting",
        "archive",
    ],
    "sentiment": ["positive", "neutral", "negative", "urgent"],
    "time_estimate": [
        "5_min",
        "15_min",
        "30_min",
        "1_hour",
        "2_hours",
        "half_day",
    ],
}


@dataclass(frozen=True)
class EmailTaskSpec:
    """Email triage task definition."""
    task_id: str
    title: str
    difficulty: str
    goal: str
    sender_profile: str
    email_subject: str
    email_body: str
    thread_history: List[Dict[str, str]]
    expected_fields: Dict[str, str]
    required_keywords: List[str]
    forbidden_keywords: List[str] = field(default_factory=list)
    max_steps: int = 10


EMAIL_TASKS: Dict[str, EmailTaskSpec] = {
    "email_urgent_client_easy": EmailTaskSpec(
        task_id="email_urgent_client_easy",
        title="Urgent client deliverable request",
        difficulty="easy",
        goal="Recognize urgent client request and schedule appropriate response time",
        sender_profile="Client Sarah Chen, VP Engineering at TechCorp. Account value: $500K/year. Typically professional and clear.",
        email_subject="URGENT: Need API documentation by EOD",
        email_body=(
            "Hi team,\n\n"
            "We're presenting to the board tomorrow and need the updated API documentation "
            "that was promised last week. This is blocking our integration timeline.\n\n"
            "Can someone confirm this will be ready by 5 PM today?\n\n"
            "Thanks,\nSarah"
        ),
        thread_history=[
            {"from": "sarah@techcorp.com", "subject": "API docs timeline", "date": "2024-01-15"},
        ],
        expected_fields={
            "email_type": "urgent_request",
            "priority": "urgent",
            "response_action": "reply_needed",
            "sentiment": "urgent",
            "time_estimate": "1_hour",
        },
        required_keywords=["urgent", "today", "documentation"],
        forbidden_keywords=["ignore", "later"],
    ),
    "email_meeting_scheduling_medium": EmailTaskSpec(
        task_id="email_meeting_scheduling_medium",
        title="Cross-team meeting scheduling",
        difficulty="medium",
        goal="Schedule a meeting across multiple time zones with conflicting schedules",
        sender_profile="Project Manager Alex Rivera. Organizes quarterly planning. Detail-oriented, likes clear agendas.",
        email_subject="Q2 Planning - Need to schedule all-hands",
        email_body=(
            "Team,\n\n"
            "We need to schedule the Q2 planning session. Based on Doodle poll results:\n"
            "- APAC team: available Tue/Wed 9-11 AM SGT\n"
            "- EMEA team: available Tue/Thu 2-4 PM CET\n"
            "- US team: available Mon/Wed 9-11 AM PST\n\n"
            "The only overlapping slot is Wednesday 9-10 AM PST / 6-7 PM CET / 1-2 AM SGT+1 (Thu).\n\n"
            "This is suboptimal for APAC. Should we:\n"
            "1. Do two sessions (EMEA-US + APAC-US)?\n"
            "2. Record for APAC async?\n"
            "3. Find a compromise time?\n\n"
            "Please respond by Thursday with your preference.\n\nAlex"
        ),
        thread_history=[
            {"from": "alex@company.com", "subject": "Q2 Planning poll", "date": "2024-01-10"},
            {"from": "team", "subject": "Re: Q2 Planning poll - Doodle results", "date": "2024-01-12"},
        ],
        expected_fields={
            "email_type": "meeting_scheduling",
            "priority": "medium",
            "response_action": "schedule_meeting",
            "sentiment": "neutral",
            "time_estimate": "30_min",
        },
        required_keywords=["schedule", "planning", "time zone"],
    ),
    "email_vip_complaint_hard": EmailTaskSpec(
        task_id="email_vip_complaint_hard",
        title="VIP customer escalation",
        difficulty="hard",
        goal="Handle escalated complaint from VIP customer with multiple stakeholders",
        sender_profile="CTO of major enterprise account ($2M ARR). Frustrated but professional. Expects executive attention.",
        email_subject="RE: RE: Critical outage impact - ESCALATING",
        email_body=(
            "To: support@company.com, success@company.com\n"
            "CC: myceo@enterprise.com\n\n"
            "This is the third email about the outage that cost us $50K in lost sales yesterday. "
            "Your support team has given me three different answers:\n\n"
            "1. 'It's a known issue' (from Tier 1, 6 hours ago)\n"
            "2. 'Fixed in next release' (from engineering, 3 hours ago)\n"
            "3. 'We need more details' (from support, 30 mins ago)\n\n"
            "I need:\n"
            "- A single point of contact for this incident\n"
            "- Root cause analysis within 24 hours\n"
            "- Credit for the downtime\n"
            "- Executive briefing on reliability roadmap\n\n"
            "I'm escalating to my CEO and will include this in our QBR discussion. "
            "This account is now at risk.\n\n"
            "I expect a response within 2 hours.\n\n"
            "Regards,\n"
            "Michael Torres, CTO\n"
            "Enterprise Corp"
        ),
        thread_history=[
            {"from": "michael@enterprise.com", "subject": "System outage", "date": "2024-01-15 09:00"},
            {"from": "support", "subject": "Re: System outage", "date": "2024-01-15 15:00"},
            {"from": "michael@enterprise.com", "subject": "Re: System outage - no update?", "date": "2024-01-15 20:00"},
            {"from": "engineering", "subject": "Re: System outage", "date": "2024-01-16 09:00"},
        ],
        expected_fields={
            "email_type": "urgent_request",
            "priority": "urgent",
            "response_action": "delegate",
            "sentiment": "negative",
            "time_estimate": "2_hours",
        },
        required_keywords=["escalating", "executive", "root cause", "single point"],
        forbidden_keywords=["known issue", "next release"],
    ),
}


# Code Review Task Specifications
CODE_REVIEW_ALLOWED_FIELDS = {
    "severity": ["info", "warning", "error", "critical"],
    "category": [
        "security",
        "performance",
        "maintainability",
        "correctness",
        "testing",
        "documentation",
    ],
    "action": [
        "approve",
        "request_changes",
        "comment",
        "needs_discussion",
    ],
    "priority": ["low", "medium", "high", "blocking"],
}


@dataclass(frozen=True)
class CodeReviewTaskSpec:
    """Code review task definition."""
    task_id: str
    title: str
    difficulty: str
    goal: str
    pr_description: str
    code_diff: str
    file_context: Dict[str, str]
    expected_issues: List[Dict[str, str]]
    required_comments: List[str]
    max_steps: int = 12


CODE_REVIEW_TASKS: Dict[str, CodeReviewTaskSpec] = {
    "codereview_sql_injection_easy": CodeReviewTaskSpec(
        task_id="codereview_sql_injection_easy",
        title="Fix SQL injection vulnerability",
        difficulty="easy",
        goal="Identify and flag critical security vulnerability in database query",
        pr_description="Add user search endpoint",
        code_diff='''
@@ -0,0 +1,10 @@
+def search_users(query):
+    conn = get_db_connection()
+    cursor = conn.cursor()
+    sql = f"SELECT * FROM users WHERE name LIKE '%{query}%'"
+    cursor.execute(sql)
+    return cursor.fetchall()
''',
        file_context={
            "users.py": "User management endpoints",
            "database.py": "Database connection utilities",
        },
        expected_issues=[
            {
                "line": 4,
                "severity": "critical",
                "category": "security",
                "description": "SQL injection via string interpolation",
            }
        ],
        required_comments=["sql injection", "parameterized query", "security"],
    ),
    "codereview_performance_medium": CodeReviewTaskSpec(
        task_id="codereview_performance_medium",
        title="N+1 query issue in data export",
        difficulty="medium",
        goal="Identify performance anti-pattern and suggest optimization",
        pr_description="Add CSV export for orders with customer details",
        code_diff='''
@@ -0,0 +1,15 @@
+def export_orders_csv():
+    orders = Order.objects.all()
+    rows = []
+    for order in orders:
+        customer = order.customer  # Triggers DB query
+        row = {
+            'order_id': order.id,
+            'customer_name': customer.name,
+            'customer_email': customer.email,
+            'amount': order.amount,
+        }
+        rows.append(row)
+    return generate_csv(rows)
''',
        file_context={
            "models.py": "Order and Customer Django models",
            "exports.py": "Data export utilities",
        },
        expected_issues=[
            {
                "line": 5,
                "severity": "error",
                "category": "performance",
                "description": "N+1 query problem - fetching customer in loop",
            }
        ],
        required_comments=["n+1", "select_related", "performance"],
    ),
    "codereview_architecture_hard": CodeReviewTaskSpec(
        task_id="codereview_architecture_hard",
        title="Distributed system consistency issue",
        difficulty="hard",
        goal="Identify subtle distributed system bug and recommend saga pattern",
        pr_description="Implement inventory reservation for orders",
        code_diff='''
@@ -0,0 +1,25 @@
+class OrderService:
+    def create_order(self, user_id, items):
+        # Reserve inventory
+        for item in items:
+            response = requests.post(
+                f"{INVENTORY_SERVICE}/reserve",
+                json={"sku": item.sku, "quantity": item.qty}
+            )
+            if response.status_code != 200:
+                raise InventoryError(f"Failed to reserve {item.sku}")
+        
+        # Charge payment
+        payment = requests.post(
+            f"{PAYMENT_SERVICE}/charge",
+            json={"user_id": user_id, "amount": self.calculate_total(items)}
+        )
+        if payment.status_code != 200:
+            raise PaymentError("Payment failed")
+        
+        # Create order
+        order = Order.objects.create(
+            user_id=user_id,
+            items=items,
+            payment_id=payment.json()["id"],
+            status="confirmed"
+        )
+        return order
''',
        file_context={
            "services/order_service.py": "Order business logic",
            "models/order.py": "Order data model",
        },
        expected_issues=[
            {
                "line": 5,
                "severity": "critical",
                "category": "correctness",
                "description": "No compensation on failure - partial reservations not released",
            },
            {
                "line": 15,
                "severity": "error",
                "category": "correctness",
                "description": "Payment fails after inventory reserved - inventory leak",
            },
        ],
        required_comments=["compensation", "saga pattern", "distributed transaction", "inventory leak"],
    ),
}


def get_extended_task_catalog() -> List[Dict[str, str]]:
    """Get catalog of all extended tasks."""
    email_catalog = [
        {"task_id": t.task_id, "domain": "email", "difficulty": t.difficulty, "title": t.title}
        for t in EMAIL_TASKS.values()
    ]
    code_catalog = [
        {"task_id": t.task_id, "domain": "code_review", "difficulty": t.difficulty, "title": t.title}
        for t in CODE_REVIEW_TASKS.values()
    ]
    return email_catalog + code_catalog


def main() -> None:
    """Demo extended domains."""
    print("Extended Task Domains")
    print("=" * 50)
    
    print("\n📧 EMAIL TRIAGE TASKS:")
    for task in EMAIL_TASKS.values():
        print(f"  • {task.task_id}: {task.title} ({task.difficulty})")
    
    print("\n💻 CODE REVIEW TASKS:")
    for task in CODE_REVIEW_TASKS.values():
        print(f"  • {task.task_id}: {task.title} ({task.difficulty})")
    
    print("\n" + "=" * 50)
    print(f"Total: {len(EMAIL_TASKS)} email + {len(CODE_REVIEW_TASKS)} code review tasks")


if __name__ == "__main__":
    main()
