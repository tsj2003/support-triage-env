"""Live Integration: Connect to real CRM systems (Zendesk, Salesforce, etc.)."""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any

import requests


@dataclass
class Ticket:
    """Unified ticket format across CRMs."""
    ticket_id: str
    source: str  # zendesk, salesforce, freshdesk, etc.
    customer_email: str
    subject: str
    body: str
    priority: Optional[str]
    status: str
    created_at: str
    tags: List[str]
    metadata: Dict[str, Any]


@dataclass
class AgentDecision:
    """Decision made by an AI agent."""
    ticket_id: str
    issue_type: str
    priority: str
    queue: str
    suggested_reply: str
    internal_note: str
    confidence: float
    timestamp: str


class CRMConnector(ABC):
    """Abstract base class for CRM connectors."""
    
    def __init__(self, api_key: str, subdomain: Optional[str] = None) -> None:
        self.api_key = api_key
        self.subdomain = subdomain
    
    @abstractmethod
    def fetch_tickets(self, status: str = "open", limit: int = 100) -> List[Ticket]:
        """Fetch tickets from the CRM."""
        pass
    
    @abstractmethod
    def apply_decision(self, decision: AgentDecision) -> bool:
        """Apply an agent decision back to the CRM."""
        pass
    
    @abstractmethod
    def get_ticket_history(self, ticket_id: str) -> List[Dict]:
        """Get conversation history for a ticket."""
        pass


class ZendeskConnector(CRMConnector):
    """Connector for Zendesk."""
    
    def __init__(self, api_key: str, subdomain: str, email: str) -> None:
        super().__init__(api_key, subdomain)
        self.email = email
        self.base_url = f"https://{subdomain}.zendesk.com/api/v2"
        self.auth = (f"{email}/token", api_key)
    
    def fetch_tickets(self, status: str = "open", limit: int = 100) -> List[Ticket]:
        """Fetch tickets from Zendesk."""
        url = f"{self.base_url}/tickets.json"
        params = {"status": status, "per_page": limit}
        
        response = requests.get(url, auth=self.auth, params=params)
        response.raise_for_status()
        data = response.json()
        
        tickets = []
        for t in data.get("tickets", []):
            # Fetch customer details
            requester = self._get_user(t.get("requester_id"))
            
            tickets.append(Ticket(
                ticket_id=str(t["id"]),
                source="zendesk",
                customer_email=requester.get("email", "unknown"),
                subject=t.get("subject", ""),
                body=t.get("description", ""),
                priority=t.get("priority"),
                status=t.get("status", "open"),
                created_at=t.get("created_at", ""),
                tags=t.get("tags", []),
                metadata={
                    "group_id": t.get("group_id"),
                    "assignee_id": t.get("assignee_id"),
                    "organization_id": t.get("organization_id"),
                },
            ))
        
        return tickets
    
    def _get_user(self, user_id: int) -> Dict:
        """Get user details."""
        try:
            url = f"{self.base_url}/users/{user_id}.json"
            response = requests.get(url, auth=self.auth)
            if response.status_code == 200:
                return response.json().get("user", {})
        except Exception:
            pass
        return {}
    
    def apply_decision(self, decision: AgentDecision) -> bool:
        """Apply agent decision to Zendesk ticket."""
        try:
            # Update priority and group (queue)
            ticket_url = f"{self.base_url}/tickets/{decision.ticket_id}.json"
            ticket_data = {
                "ticket": {
                    "priority": decision.priority,
                    "group_id": self._get_group_id(decision.queue),
                    "tags": [f"ai_classified:{decision.issue_type}"],
                }
            }
            
            response = requests.put(ticket_url, auth=self.auth, json=ticket_data)
            response.raise_for_status()
            
            # Add internal note
            if decision.internal_note:
                self._add_comment(decision.ticket_id, decision.internal_note, public=False)
            
            # Add suggested reply as private comment for human review
            if decision.suggested_reply:
                reply_with_context = (
                    f"AI Suggested Reply (confidence: {decision.confidence:.0%}):\n\n"
                    f"{decision.suggested_reply}\n\n"
                    f"---\nReview and edit before sending to customer."
                )
                self._add_comment(decision.ticket_id, reply_with_context, public=False)
            
            return True
        except Exception as e:
            print(f"Failed to apply decision: {e}")
            return False
    
    def _get_group_id(self, queue_name: str) -> Optional[int]:
        """Map queue name to Zendesk group ID."""
        # In real implementation, fetch groups and map
        # For now, return None (no change)
        return None
    
    def _add_comment(self, ticket_id: str, body: str, public: bool = False) -> bool:
        """Add a comment to a ticket."""
        try:
            url = f"{self.base_url}/tickets/{ticket_id}.json"
            data = {
                "ticket": {
                    "comment": {
                        "body": body,
                        "public": public,
                    }
                }
            }
            response = requests.put(url, auth=self.auth, json=data)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_ticket_history(self, ticket_id: str) -> List[Dict]:
        """Get ticket comments/history."""
        try:
            url = f"{self.base_url}/tickets/{ticket_id}/comments.json"
            response = requests.get(url, auth=self.auth)
            response.raise_for_status()
            return response.json().get("comments", [])
        except Exception:
            return []


class SalesforceConnector(CRMConnector):
    """Connector for Salesforce Service Cloud."""
    
    def __init__(self, access_token: str, instance_url: str) -> None:
        super().__init__(access_token)
        self.instance_url = instance_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
    
    def fetch_tickets(self, status: str = "New", limit: int = 100) -> List[Ticket]:
        """Fetch cases from Salesforce."""
        query = f"""
            SELECT Id, Subject, Description, Status, Priority, 
                   ContactEmail, CreatedDate, CaseNumber
            FROM Case 
            WHERE Status = '{status}'
            LIMIT {limit}
        """
        
        url = f"{self.instance_url}/services/data/v58.0/query"
        params = {"q": query}
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        tickets = []
        for record in data.get("records", []):
            tickets.append(Ticket(
                ticket_id=record.get("Id"),
                source="salesforce",
                customer_email=record.get("ContactEmail", "unknown"),
                subject=record.get("Subject", ""),
                body=record.get("Description", ""),
                priority=record.get("Priority"),
                status=record.get("Status", "New"),
                created_at=record.get("CreatedDate", ""),
                tags=[],
                metadata={
                    "case_number": record.get("CaseNumber"),
                },
            ))
        
        return tickets
    
    def apply_decision(self, decision: AgentDecision) -> bool:
        """Apply agent decision to Salesforce case."""
        try:
            url = f"{self.instance_url}/services/data/v58.0/sobjects/Case/{decision.ticket_id}"
            
            data = {
                "Priority": decision.priority,
                "AI_Classification__c": decision.issue_type,
                "AI_Suggested_Reply__c": decision.suggested_reply,
                "AI_Confidence__c": decision.confidence,
            }
            
            response = requests.patch(url, headers=self.headers, json=data)
            response.raise_for_status()
            
            # Add internal note as task
            if decision.internal_note:
                self._create_task(decision.ticket_id, decision.internal_note)
            
            return True
        except Exception as e:
            print(f"Failed to apply decision: {e}")
            return False
    
    def _create_task(self, case_id: str, description: str) -> bool:
        """Create a task for internal note."""
        try:
            url = f"{self.instance_url}/services/data/v58.0/sobjects/Task"
            data = {
                "WhatId": case_id,
                "Subject": "AI Classification Notes",
                "Description": description,
                "Status": "Completed",
            }
            response = requests.post(url, headers=self.headers, json=data)
            return response.status_code == 201
        except Exception:
            return False
    
    def get_ticket_history(self, ticket_id: str) -> List[Dict]:
        """Get case comments/history."""
        try:
            query = f"""
                SELECT Id, CommentBody, CreatedDate, CreatedBy.Name
                FROM CaseComment
                WHERE ParentId = '{ticket_id}'
                ORDER BY CreatedDate DESC
            """
            url = f"{self.instance_url}/services/data/v58.0/query"
            params = {"q": query}
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json().get("records", [])
        except Exception:
            return []


class LiveEvaluationRunner:
    """Run evaluations on real tickets from CRM systems."""
    
    def __init__(self, connector: CRMConnector) -> None:
        self.connector = connector
    
    def fetch_and_evaluate(
        self,
        agent_api_endpoint: str,
        agent_api_key: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """Fetch real tickets and evaluate agent decisions."""
        tickets = self.connector.fetch_tickets(limit=limit)
        
        results = []
        for ticket in tickets:
            print(f"Evaluating ticket {ticket.ticket_id}: {ticket.subject[:50]}...")
            
            # Call agent API
            decision = self._call_agent(
                agent_api_endpoint,
                agent_api_key,
                ticket,
            )
            
            if decision:
                # Evaluate decision quality
                evaluation = self._evaluate_decision(ticket, decision)
                
                results.append({
                    "ticket": ticket,
                    "decision": decision,
                    "evaluation": evaluation,
                })
        
        return results
    
    def _call_agent(
        self,
        endpoint: str,
        api_key: Optional[str],
        ticket: Ticket,
    ) -> Optional[AgentDecision]:
        """Call external agent API."""
        try:
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            payload = {
                "ticket_id": ticket.ticket_id,
                "subject": ticket.subject,
                "body": ticket.body,
                "customer_email": ticket.customer_email,
                "source": ticket.source,
                "tags": ticket.tags,
            }
            
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            
            return AgentDecision(
                ticket_id=ticket.ticket_id,
                issue_type=data.get("issue_type", "unknown"),
                priority=data.get("priority", "medium"),
                queue=data.get("queue", "general"),
                suggested_reply=data.get("suggested_reply", ""),
                internal_note=data.get("internal_note", ""),
                confidence=data.get("confidence", 0.5),
                timestamp=datetime.now().isoformat(),
            )
        except Exception as e:
            print(f"Failed to call agent API: {e}")
            return None
    
    def _evaluate_decision(self, ticket: Ticket, decision: AgentDecision) -> Dict:
        """Evaluate the quality of an agent decision."""
        # In real implementation, use grader logic
        # For now, return basic metrics
        
        evaluation = {
            "priority_changed": decision.priority != (ticket.priority or "medium"),
            "has_suggested_reply": len(decision.suggested_reply) > 20,
            "has_internal_note": len(decision.internal_note) > 10,
            "confidence": decision.confidence,
        }
        
        # Calculate simple quality score
        score = 0.0
        if evaluation["has_suggested_reply"]:
            score += 0.3
        if evaluation["has_internal_note"]:
            score += 0.2
        if decision.confidence > 0.7:
            score += 0.2
        if evaluation["priority_changed"]:
            score += 0.3
        
        evaluation["quality_score"] = score
        
        return evaluation


def create_connector(crm_type: str, config: Dict) -> CRMConnector:
    """Factory function to create appropriate connector."""
    if crm_type == "zendesk":
        return ZendeskConnector(
            api_key=config["api_key"],
            subdomain=config["subdomain"],
            email=config["email"],
        )
    elif crm_type == "salesforce":
        return SalesforceConnector(
            access_token=config["access_token"],
            instance_url=config["instance_url"],
        )
    else:
        raise ValueError(f"Unknown CRM type: {crm_type}")


def main() -> None:
    """Demo live integration."""
    print("Live Integration Demo")
    print("=" * 50)
    
    # Example usage
    print("\n1. Zendesk Connector:")
    print("   Required: ZENDESK_SUBDOMAIN, ZENDESK_API_KEY, ZENDESK_EMAIL")
    
    print("\n2. Salesforce Connector:")
    print("   Required: SALESFORCE_ACCESS_TOKEN, SALESFORCE_INSTANCE_URL")
    
    print("\n3. Usage:")
    print("   connector = create_connector('zendesk', config)")
    print("   runner = LiveEvaluationRunner(connector)")
    print("   results = runner.fetch_and_evaluate(agent_endpoint)")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
