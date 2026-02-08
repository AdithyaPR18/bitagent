"""AI Agent with L402 payment support.

Uses a tool-based architecture (compatible with LangChain patterns) where the agent
can make autonomous decisions about paying for data via Lightning Network.

When USE_MOCK_LLM=true, uses a deterministic rule-based "LLM" for demo reliability.
"""
from __future__ import annotations
import time
import httpx
from dataclasses import dataclass, field
from typing import Optional

from agent.wallet import AgentWallet
from agent.decision_maker import evaluate_payment
from l402.invoice import mock_pay_invoice
from l402.verification import parse_l402_auth_header
from config import get_settings


@dataclass
class AgentAction:
    action: str  # "query", "pay", "decide", "respond"
    detail: str
    timestamp: float = field(default_factory=time.time)
    result: Optional[dict] = None


@dataclass
class AgentTask:
    query: str
    priority: str = "normal"
    endpoint: str = ""
    result: Optional[dict] = None
    actions: list[AgentAction] = field(default_factory=list)
    total_cost_sats: int = 0
    completed: bool = False


class BitAgent:
    """An AI agent that autonomously pays for API access via L402."""

    def __init__(self, agent_id: str, initial_balance: int = 10000):
        self.agent_id = agent_id
        self.wallet = AgentWallet(agent_id, initial_balance)
        self.tasks: list[AgentTask] = []
        self.reputation_score = 50  # Starting reputation
        self.total_api_calls = 0
        self.successful_payments = 0
        self.created_at = time.time()
        self._base_url = "http://localhost:8000"

    async def execute_task(self, query: str, priority: str = "normal") -> AgentTask:
        """Execute a task that may require paid API calls.

        The agent:
        1. Determines which API to call
        2. Attempts the call (gets 402)
        3. Decides whether to pay
        4. Pays via Lightning if approved
        5. Retrieves and returns the data
        """
        task = AgentTask(query=query, priority=priority)
        self.tasks.append(task)

        # Step 1: Determine endpoint
        endpoint = self._route_query(query)
        task.endpoint = endpoint
        task.actions.append(AgentAction(
            action="decide",
            detail=f"Routing query to {endpoint}",
        ))

        # Step 2: Make initial API call (will get 402)
        task.actions.append(AgentAction(
            action="query",
            detail=f"Calling {endpoint}...",
        ))

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self._base_url}{endpoint}",
                headers={"X-Agent-Id": self.agent_id},
            )

            if resp.status_code == 402:
                # Step 3: Parse the 402 response
                body = resp.json()
                price = body.get("price_sats", 10)
                payment_hash = body.get("payment_hash", "")
                auth_header = resp.headers.get("WWW-Authenticate", "")

                task.actions.append(AgentAction(
                    action="decide",
                    detail=f"Received 402 Payment Required — price: {price} sats",
                    result={"price": price, "payment_hash": payment_hash},
                ))

                # Step 4: Decision — should we pay?
                decision = evaluate_payment(
                    self.wallet, price, endpoint, priority,
                )
                task.actions.append(AgentAction(
                    action="decide",
                    detail=decision.reason,
                    result={
                        "should_pay": decision.should_pay,
                        "confidence": decision.confidence,
                    },
                ))

                if not decision.should_pay:
                    task.actions.append(AgentAction(
                        action="respond",
                        detail=f"Declined to pay: {decision.reason}",
                    ))
                    task.completed = True
                    return task

                # Step 5: Pay the invoice
                preimage = mock_pay_invoice(payment_hash)
                if not preimage:
                    task.actions.append(AgentAction(
                        action="pay",
                        detail="Payment failed — could not get preimage",
                    ))
                    task.completed = True
                    return task

                self.wallet.pay(price, f"L402 payment for {endpoint}", endpoint, payment_hash)
                self.successful_payments += 1
                task.total_cost_sats += price

                task.actions.append(AgentAction(
                    action="pay",
                    detail=f"Paid {price} sats via Lightning (balance: {self.wallet.balance_sats})",
                    result={"preimage": preimage[:16] + "...", "new_balance": self.wallet.balance_sats},
                ))

                # Step 6: Retry with payment proof
                # Extract macaroon from WWW-Authenticate header
                macaroon = ""
                if 'macaroon="' in auth_header:
                    macaroon = auth_header.split('macaroon="')[1].split('"')[0]

                resp2 = await client.get(
                    f"{self._base_url}{endpoint}",
                    headers={
                        "Authorization": f"L402 {macaroon}:{preimage}",
                        "X-Agent-Id": self.agent_id,
                    },
                )

                if resp2.status_code == 200:
                    task.result = resp2.json()
                    task.actions.append(AgentAction(
                        action="respond",
                        detail="Data received successfully!",
                        result=task.result,
                    ))
                    self.total_api_calls += 1
                else:
                    task.actions.append(AgentAction(
                        action="respond",
                        detail=f"Request failed after payment: HTTP {resp2.status_code}",
                    ))

            elif resp.status_code == 200:
                # Free endpoint
                task.result = resp.json()
                task.actions.append(AgentAction(
                    action="respond",
                    detail="Data received (no payment required)",
                    result=task.result,
                ))

        task.completed = True
        return task

    def _route_query(self, query: str) -> str:
        """Simple keyword-based routing to determine which API to call."""
        q = query.lower()

        # Weather queries
        weather_cities = ["new haven", "new york", "san francisco", "miami",
                          "chicago", "london", "tokyo"]
        for city in weather_cities:
            if city in q:
                return f"/api/weather/{city.replace(' ', '%20')}"
        if any(w in q for w in ["weather", "temperature", "forecast", "rain", "sunny"]):
            return "/api/weather/new haven"

        # Stock queries
        symbols = ["btc", "eth", "aapl", "googl", "tsla", "msft", "nvda", "stx"]
        for sym in symbols:
            if sym in q:
                return f"/api/stocks/{sym.upper()}"
        if any(w in q for w in ["stock", "price", "market", "trading"]):
            return "/api/stocks/BTC"

        # News queries
        if any(w in q for w in ["news", "headline", "article", "latest"]):
            for topic in ["crypto", "ai", "finance", "research"]:
                if topic in q:
                    return f"/api/news/topic/{topic}"
            return "/api/news/"

        # Default
        return "/api/news/"

    def get_status(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "wallet": self.wallet.get_stats(),
            "reputation_score": self.reputation_score,
            "total_api_calls": self.total_api_calls,
            "successful_payments": self.successful_payments,
            "tasks_completed": sum(1 for t in self.tasks if t.completed),
            "uptime_hours": round((time.time() - self.created_at) / 3600, 2),
        }

    def get_task_history(self, limit: int = 20) -> list[dict]:
        return [
            {
                "query": t.query,
                "priority": t.priority,
                "endpoint": t.endpoint,
                "cost_sats": t.total_cost_sats,
                "completed": t.completed,
                "actions": [
                    {"action": a.action, "detail": a.detail, "timestamp": a.timestamp}
                    for a in t.actions
                ],
                "has_result": t.result is not None,
            }
            for t in self.tasks[-limit:]
        ]
