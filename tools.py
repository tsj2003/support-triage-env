"""Tool use module for querying order DB and checking account status."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Order:
    order_id: str
    customer_id: str
    status: str  # pending, shipped, delivered, cancelled, fraudulent
    amount: float
    items: int
    created_at: str
    shipping_address: str
    payment_method: str


@dataclass
class AccountStatus:
    customer_id: str
    tier: str  # free, standard, premium, enterprise
    account_age_days: int
    total_orders: int
    lifetime_value: float
    open_tickets: int
    fraud_flags: List[str]
    payment_methods: List[Dict[str, Any]]
    last_login: str


class OrderDatabase:
    """Mock order database for tool queries."""

    def __init__(self):
        # Seed with realistic order data matching our tasks
        self._orders: Dict[str, List[Order]] = {
            "elena_r_8492": [  # Security incident customer
                Order("ORD-78234", "elena_r_8492", "fraudulent", 129.99, 2, "2024-01-15", "New Address, Miami", "new_card_ending_4829"),
                Order("ORD-78235", "elena_r_8492", "fraudulent", 89.50, 1, "2024-01-15", "New Address, Miami", "new_card_ending_4829"),
                Order("ORD-77120", "elena_r_8492", "delivered", 45.00, 1, "2024-01-02", "123 Main St, Austin", "card_ending_1234"),
            ],
            "vip_customer_4721": [  # Shipping VIP customer
                Order("ORD-78100", "vip_customer_4721", "shipped", 899.00, 5, "2024-01-10", "Convention Center, SF", "corporate_card"),
                Order("ORD-77050", "vip_customer_4721", "delivered", 1200.00, 8, "2023-12-15", "HQ, New York", "corporate_card"),
            ],
            "eu_customer_9955": [  # Privacy export customer
                Order("ORD-65000", "eu_customer_9955", "delivered", 150.00, 3, "2023-06-01", "Berlin, Germany", "sepa_transfer"),
            ],
            "creator_jordan_5523": [  # Payout hold customer
                Order("ORD-90001", "creator_jordan_5523", "delivered", 5000.00, 1, "2024-01-12", "Studio, LA", "bank_transfer"),
                Order("ORD-90002", "creator_jordan_5523", "delivered", 8000.00, 1, "2024-01-13", "Studio, LA", "bank_transfer"),
                Order("ORD-90003", "creator_jordan_5523", "pending", 12000.00, 1, "2024-01-14", "Studio, LA", "bank_transfer"),
            ],
            "acmecorp_sarah_chen": [  # Enterprise negotiation customer
                Order("ENT-2023-001", "acmecorp_sarah_chen", "active", 2000000.00, 1, "2021-01-01", "AcmeCorp HQ", "wire_transfer"),
            ],
        }
        
        self._accounts: Dict[str, AccountStatus] = {
            "elena_r_8492": AccountStatus(
                customer_id="elena_r_8492",
                tier="premium",
                account_age_days=892,
                total_orders=47,
                lifetime_value=3450.50,
                open_tickets=1,
                fraud_flags=["recent_phone_change", "password_reset_from_new_device", "unusual_order_pattern"],
                payment_methods=[
                    {"type": "card", "last4": "1234", "expiry": "12/25"},
                    {"type": "card", "last4": "4829", "expiry": "06/27", "added_recently": True},
                ],
                last_login="2024-01-15T03:22:00Z",
            ),
            "vip_customer_4721": AccountStatus(
                customer_id="vip_customer_4721",
                tier="enterprise",
                account_age_days=1450,
                total_orders=156,
                lifetime_value=125000.00,
                open_tickets=1,
                fraud_flags=[],
                payment_methods=[
                    {"type": "corporate_card", "last4": "8888"},
                ],
                last_login="2024-01-10T09:00:00Z",
            ),
            "eu_customer_9955": AccountStatus(
                customer_id="eu_customer_9955",
                tier="standard",
                account_age_days=450,
                total_orders=8,
                lifetime_value=850.00,
                open_tickets=1,
                fraud_flags=[],
                payment_methods=[
                    {"type": "sepa", "iban_last4": "5678"},
                ],
                last_login="2024-01-01T10:00:00Z",
            ),
            "creator_jordan_5523": AccountStatus(
                customer_id="creator_jordan_5523",
                tier="premium",
                account_age_days=730,
                total_orders=200,
                lifetime_value=75000.00,
                open_tickets=1,
                fraud_flags=["velocity_spike_detected", "payout_hold_active"],
                payment_methods=[
                    {"type": "bank", "account_last4": "9999"},
                ],
                last_login="2024-01-14T18:30:00Z",
            ),
            "acmecorp_sarah_chen": AccountStatus(
                customer_id="acmecorp_sarah_chen",
                tier="enterprise",
                account_age_days=1095,
                total_orders=3,  # Contract renewals
                lifetime_value=6000000.00,
                open_tickets=1,
                fraud_flags=[],
                payment_methods=[
                    {"type": "wire", "account": "AcmeCorp Main"},
                ],
                last_login="2024-01-08T14:00:00Z",
            ),
        }

    def query_orders(self, customer_id: str, status: Optional[str] = None) -> List[Order]:
        """Query orders for a customer, optionally filtered by status."""
        orders = self._orders.get(customer_id, [])
        if status:
            orders = [o for o in orders if o.status == status]
        return orders

    def check_account_status(self, customer_id: str) -> Optional[AccountStatus]:
        """Get account status and metadata for a customer."""
        return self._accounts.get(customer_id)

    def search_orders_by_address(self, address_fragment: str) -> List[Order]:
        """Search orders by shipping address fragment."""
        results = []
        for customer_orders in self._orders.values():
            for order in customer_orders:
                if address_fragment.lower() in order.shipping_address.lower():
                    results.append(order)
        return results

    def get_customer_by_task(self, task_id: str) -> str:
        """Map task IDs to customer IDs for tool queries."""
        mapping = {
            "billing_refund_easy": "elena_r_8492",  # Using same customer for simplicity
            "shipping_vip_medium": "vip_customer_4721",
            "privacy_export_medium": "eu_customer_9955",
            "payout_hold_hard": "creator_jordan_5523",
            "security_incident_hard": "elena_r_8492",
            "enterprise_negotiation_expert": "acmecorp_sarah_chen",
        }
        return mapping.get(task_id, "unknown")


# Global database instance
_db_instance: OrderDatabase | None = None


def get_order_database() -> OrderDatabase:
    """Get or create the global order database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = OrderDatabase()
    return _db_instance
