"""Lightning wallet management for AI agents."""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Transaction:
    amount_sats: int
    tx_type: str  # "payment", "receive", "deposit"
    description: str
    endpoint: str
    timestamp: float = field(default_factory=time.time)
    payment_hash: str = ""


class AgentWallet:
    def __init__(self, agent_id: str, initial_balance: int = 10000):
        self.agent_id = agent_id
        self.balance_sats = initial_balance
        self.initial_balance = initial_balance
        self.transactions: list[Transaction] = []
        self.created_at = time.time()

        # Track spending
        self.total_spent = 0
        self.total_received = 0
        self.hourly_spending: dict[int, int] = {}  # hour -> sats spent

    def pay(self, amount_sats: int, description: str = "", endpoint: str = "",
            payment_hash: str = "") -> bool:
        """Attempt to make a payment. Returns True if successful."""
        if amount_sats > self.balance_sats:
            return False
        self.balance_sats -= amount_sats
        self.total_spent += amount_sats
        hour_key = int(time.time() // 3600)
        self.hourly_spending[hour_key] = self.hourly_spending.get(hour_key, 0) + amount_sats
        self.transactions.append(Transaction(
            amount_sats=-amount_sats,
            tx_type="payment",
            description=description,
            endpoint=endpoint,
            payment_hash=payment_hash,
        ))
        return True

    def receive(self, amount_sats: int, description: str = "") -> None:
        """Receive sats (from job, deposit, etc.)."""
        self.balance_sats += amount_sats
        self.total_received += amount_sats
        self.transactions.append(Transaction(
            amount_sats=amount_sats,
            tx_type="receive",
            description=description,
            endpoint="",
        ))

    def get_hourly_spend(self) -> int:
        """Get spending in the current hour."""
        hour_key = int(time.time() // 3600)
        return self.hourly_spending.get(hour_key, 0)

    def is_low_balance(self, threshold_pct: float = 0.1) -> bool:
        return self.balance_sats < self.initial_balance * threshold_pct

    def get_stats(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "balance_sats": self.balance_sats,
            "initial_balance": self.initial_balance,
            "total_spent": self.total_spent,
            "total_received": self.total_received,
            "total_transactions": len(self.transactions),
            "hourly_spend": self.get_hourly_spend(),
            "is_low_balance": self.is_low_balance(),
            "uptime_hours": round((time.time() - self.created_at) / 3600, 2),
        }

    def get_history(self, limit: int = 50) -> list[dict]:
        return [
            {
                "amount_sats": tx.amount_sats,
                "type": tx.tx_type,
                "description": tx.description,
                "endpoint": tx.endpoint,
                "timestamp": tx.timestamp,
                "payment_hash": tx.payment_hash,
            }
            for tx in self.transactions[-limit:]
        ]
