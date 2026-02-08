"""Payment decision logic — should the agent pay for this data?"""
from __future__ import annotations
from dataclasses import dataclass

from agent.wallet import AgentWallet
from config import get_settings


@dataclass
class PaymentDecision:
    should_pay: bool
    reason: str
    price_sats: int
    budget_remaining: int
    confidence: float  # 0-1


def evaluate_payment(
    wallet: AgentWallet,
    price_sats: int,
    endpoint: str,
    task_priority: str = "normal",  # low, normal, high, critical
) -> PaymentDecision:
    """Decide whether the agent should pay for this API call.

    Decision factors:
    1. Budget: do we have enough sats?
    2. Hourly limit: are we under budget for this hour?
    3. Task priority: how important is this data?
    4. Price reasonableness: is this price typical?
    """
    settings = get_settings()

    # Factor 1: Sufficient balance
    if price_sats > wallet.balance_sats:
        return PaymentDecision(
            should_pay=False,
            reason=f"Insufficient balance: {wallet.balance_sats} sats < {price_sats} sats needed",
            price_sats=price_sats,
            budget_remaining=wallet.balance_sats,
            confidence=1.0,
        )

    # Factor 2: Hourly budget
    hourly_spend = wallet.get_hourly_spend()
    hourly_budget = settings.agent_budget_per_hour
    if hourly_spend + price_sats > hourly_budget and task_priority not in ("high", "critical"):
        return PaymentDecision(
            should_pay=False,
            reason=f"Hourly budget exceeded: spent {hourly_spend}/{hourly_budget} sats this hour",
            price_sats=price_sats,
            budget_remaining=max(0, hourly_budget - hourly_spend),
            confidence=0.85,
        )

    # Factor 3: Task priority multiplier
    priority_thresholds = {
        "low": 10,       # Only pay if < 10 sats
        "normal": 30,    # Pay up to 30 sats
        "high": 70,      # Pay up to 70 sats
        "critical": 200,  # Pay almost anything
    }
    max_price = priority_thresholds.get(task_priority, 30)
    if price_sats > max_price:
        return PaymentDecision(
            should_pay=False,
            reason=f"Price {price_sats} sats exceeds {task_priority} priority threshold of {max_price} sats",
            price_sats=price_sats,
            budget_remaining=wallet.balance_sats,
            confidence=0.7,
        )

    # Factor 4: Low balance warning
    if wallet.is_low_balance():
        if task_priority not in ("high", "critical"):
            return PaymentDecision(
                should_pay=False,
                reason=f"Low balance ({wallet.balance_sats} sats) — conserving funds for critical tasks",
                price_sats=price_sats,
                budget_remaining=wallet.balance_sats,
                confidence=0.6,
            )

    # All checks passed
    return PaymentDecision(
        should_pay=True,
        reason=f"Payment approved: {price_sats} sats for {endpoint} (priority: {task_priority})",
        price_sats=price_sats,
        budget_remaining=wallet.balance_sats - price_sats,
        confidence=0.9,
    )
