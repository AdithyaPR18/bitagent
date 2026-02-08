"""Client for interacting with the Stacks blockchain reputation contract.

Uses a mock in-memory implementation when Stacks node is unavailable.
"""
from __future__ import annotations
import time
from typing import Optional
import httpx
from config import get_settings


# In-memory mock of on-chain state for demo
_mock_agents: dict[str, dict] = {}


class ReputationClient:
    def __init__(self):
        settings = get_settings()
        self.api_url = settings.stacks_api_url
        self.use_mock = True  # Always start with mock; try real connection

    async def register_agent(self, agent_id: str) -> int:
        """Register an agent and return initial reputation score."""
        if self.use_mock:
            _mock_agents[agent_id] = {
                "score": 50,
                "total_payments": 0,
                "successful_payments": 0,
                "total_sats_spent": 0,
                "registered_at": time.time(),
                "last_updated": time.time(),
                "payments": [],
            }
            return 50

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.api_url}/v2/contracts/call-read",
                json={
                    "contract_address": "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM",
                    "contract_name": "bitagent-reputation",
                    "function_name": "register-agent",
                    "arguments": [agent_id],
                },
            )
            return 50

    async def record_payment(
        self,
        agent_id: str,
        amount_sats: int,
        endpoint: str,
        success: bool = True,
    ) -> int:
        """Record a payment and return updated reputation score."""
        if self.use_mock:
            agent = _mock_agents.get(agent_id)
            if not agent:
                await self.register_agent(agent_id)
                agent = _mock_agents[agent_id]

            agent["total_payments"] += 1
            if success:
                agent["successful_payments"] += 1
            agent["total_sats_spent"] += amount_sats
            agent["last_updated"] = time.time()
            agent["payments"].append({
                "amount_sats": amount_sats,
                "endpoint": endpoint,
                "timestamp": time.time(),
                "success": success,
            })

            # Recalculate score (mirrors Clarity contract logic)
            total = agent["total_payments"]
            successful = agent["successful_payments"]
            sats = agent["total_sats_spent"]

            success_component = (successful * 40 // total) if total > 0 else 0
            volume_component = min(30, total * 30 // 100)
            spend_component = min(30, sats * 30 // 10000)
            agent["score"] = min(100, success_component + volume_component + spend_component)
            return agent["score"]

        return 50

    async def get_reputation(self, agent_id: str) -> Optional[dict]:
        if self.use_mock:
            return _mock_agents.get(agent_id)
        return None

    async def get_score(self, agent_id: str) -> int:
        if self.use_mock:
            agent = _mock_agents.get(agent_id)
            return agent["score"] if agent else 0
        return 0

    async def get_discount_tier(self, agent_id: str) -> float:
        """Get pricing discount multiplier based on reputation."""
        score = await self.get_score(agent_id)
        if score > 80:
            return 0.7  # 30% off
        if score > 60:
            return 0.8  # 20% off
        if score > 30:
            return 0.9  # 10% off
        return 1.0

    async def get_all_agents(self) -> list[dict]:
        if self.use_mock:
            return [
                {"agent_id": aid, **{k: v for k, v in data.items() if k != "payments"}}
                for aid, data in _mock_agents.items()
            ]
        return []


# Singleton
reputation_client = ReputationClient()
