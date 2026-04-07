"""Knowledge Base for RAG retrieval in support triage environment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class KBDocument:
    """Single knowledge base document."""

    doc_id: str
    title: str
    content: str
    tags: List[str]


class KnowledgeBase:
    """In-memory knowledge base for support ticket retrieval."""

    def __init__(self):
        self.documents: List[KBDocument] = []
        self._seed_documents()

    def _seed_documents(self) -> None:
        """Initialize with realistic support documentation."""
        docs = [
            KBDocument(
                doc_id="kb-001",
                title="Duplicate Charge Refund Policy",
                content="For duplicate charges on the same day, approve full refund immediately. "
                        "Customer should see refund in 5-7 business days. Escalate to billing_ops "
                        "for verification of duplicate posting.",
                tags=["billing", "refund", "duplicate_charge", "policy"],
            ),
            KBDocument(
                doc_id="kb-002",
                title="VIP Customer Handling",
                content="VIP customers with stalled tracking >48 hours get high priority. "
                        "Escalate to carrier_liaison immediately. Offer expedited replacement "
                        "if package will miss critical event. Service recovery authorized.",
                tags=["vip", "shipping", "priority", "escalation"],
            ),
            KBDocument(
                doc_id="kb-003",
                title="GDPR Data Export Procedure",
                content="For EU customers requesting data export: verify identity, check "
                        "account status (closed accounts still in retention window are valid). "
                        "Privacy ops handles fulfillment. Timeline: 30 days per GDPR Article 12.",
                tags=["privacy", "gdpr", "data_export", "compliance", "eu"],
            ),
            KBDocument(
                doc_id="kb-004",
                title="Payout Hold - Velocity Spike",
                content="Large revenue spikes trigger automated payout review for fraud prevention. "
                        "Cannot promise immediate release. Creator ops and risk must review. "
                        "Creator cash flow impact noted. DO NOT promise release timeline.",
                tags=["payout", "hold", "velocity", "fraud", "creator"],
            ),
            KBDocument(
                doc_id="kb-005",
                title="SIM Swap Account Takeover",
                content="SIM swap attacks require URGENT security escalation. Freeze account "
                        "immediately. Reset password required. Security team investigates "
                        "unauthorized orders. No refunds until investigation complete.",
                tags=["security", "sim_swap", "account_takeover", "urgent", "fraud"],
            ),
            KBDocument(
                doc_id="kb-006",
                title="Refund Negotiation Guidelines",
                content="For refund disputes: Tier 1 agents can approve up to $50 without approval. "
                        "$50-$200 requires supervisor sign-off. Above $200 requires manager. "
                        "Always start with lower offer, negotiate up if customer persists.",
                tags=["negotiation", "refund", "policy", "dispute"],
            ),
            KBDocument(
                doc_id="kb-007",
                title="Shipping Delays - Conference Deadlines",
                content="When customer has conference/event deadline and tracking stalled: "
                        "1) Check carrier status 2) Calculate if arrival before event possible "
                        "3) If not, offer expedited replacement 4) Consider service recovery for VIP.",
                tags=["shipping", "delay", "conference", "event", "deadline"],
            ),
            KBDocument(
                doc_id="kb-008",
                title="Account Closure & Data Retention",
                content="Closed accounts remain in retention window (typically 30-90 days) "
                        "for legal/compliance reasons. Data exports, chargebacks, and legal "
                        "requests can still be processed during retention period.",
                tags=["account", "closure", "retention", "compliance"],
            ),
            KBDocument(
                doc_id="kb-009",
                title="Unauthorized Transaction Investigation",
                content="For suspected unauthorized orders: 1) Freeze account immediately "
                        "2) Require password reset 3) Escalate to security 4) Review login logs "
                        "5) Do NOT process refunds until investigation complete.",
                tags=["unauthorized", "fraud", "investigation", "security"],
            ),
            KBDocument(
                doc_id="kb-010",
                title="Empathy Language Guidelines",
                content="Use empathetic phrases: 'I understand this is frustrating', "
                        "'I can see why you'd be concerned', 'Let me help resolve this'. "
                        "Avoid: 'That's our policy', 'There's nothing I can do', 'You should have'.",
                tags=["communication", "empathy", "language", "customer_service"],
            ),
        ]
        self.documents = docs

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        """Simple keyword-based retrieval. Returns top_k matching documents."""
        query_lower = query.lower()
        query_terms = set(query_lower.split())

        # Score documents by term overlap
        scored_docs = []
        for doc in self.documents:
            score = 0
            # Check title match
            if query_lower in doc.title.lower():
                score += 10
            # Check content match
            if query_lower in doc.content.lower():
                score += 5
            # Check tag match
            for tag in doc.tags:
                if tag.lower() in query_terms:
                    score += 8
            # Partial term matches in content
            content_lower = doc.content.lower()
            for term in query_terms:
                if term in content_lower:
                    score += 1

            if score > 0:
                scored_docs.append((score, doc))

        # Sort by score and return top_k
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        top_docs = scored_docs[:top_k]

        # Format as context strings
        results = []
        for score, doc in top_docs:
            results.append(f"[{doc.doc_id}] {doc.title}: {doc.content}")

        return results

    def get_doc_by_id(self, doc_id: str) -> KBDocument | None:
        """Get a specific document by ID."""
        for doc in self.documents:
            if doc.doc_id == doc_id:
                return doc
        return None


# Global knowledge base instance
_kb_instance: KnowledgeBase | None = None


def get_knowledge_base() -> KnowledgeBase:
    """Get or create the global knowledge base instance."""
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = KnowledgeBase()
    return _kb_instance
