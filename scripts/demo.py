#!/usr/bin/env python3
"""Run the full BitAgent demo — shows the complete agent lifecycle."""
import asyncio
import httpx
import time
import json

BASE = "http://localhost:8000"

DEMO_QUERIES = [
    ("What's the weather in New Haven?", "high"),
    ("Get me the BTC price", "normal"),
    ("Latest crypto news", "normal"),
    ("What's the weather in Tokyo?", "normal"),
    ("NVDA stock price", "high"),
    ("News about AI", "normal"),
    ("ETH price", "low"),
    ("Weather in Miami", "normal"),
    ("STX stock price", "critical"),
    ("Finance news headlines", "normal"),
]


async def run_demo():
    async with httpx.AsyncClient(timeout=30) as client:
        # Check health
        resp = await client.get(f"{BASE}/health")
        print(f"Server health: {resp.json()}")

        # Show initial agent state
        resp = await client.get(f"{BASE}/agent/status")
        status = resp.json()
        print(f"\n{'='*60}")
        print(f"AGENT INITIALIZED")
        print(f"  ID:         {status['agent_id']}")
        print(f"  Balance:    {status['wallet']['balance_sats']} sats")
        print(f"  Reputation: {status['reputation_score']}/100")
        print(f"{'='*60}\n")

        # Show ML model metrics
        resp = await client.get(f"{BASE}/ml/pricing/metrics")
        pm = resp.json()
        print(f"Pricing Model: MAE={pm.get('mae')} sats, R2={pm.get('r2')}")
        resp = await client.get(f"{BASE}/ml/credit/metrics")
        cm = resp.json()
        print(f"Credit Model:  Will-pay accuracy={cm.get('will_pay_accuracy')}")

        # Show dynamic pricing examples
        print(f"\n{'─'*60}")
        print("DYNAMIC PRICING EXAMPLES")
        print(f"{'─'*60}")
        for load, desc in [(0.1, "Low load"), (0.5, "Medium load"), (0.9, "High load")]:
            resp = await client.get(f"{BASE}/ml/pricing/predict", params={"server_load": load})
            print(f"  {desc}: {resp.json()['predicted_price_sats']} sats")

        # Run agent tasks
        print(f"\n{'='*60}")
        print("AGENT EXECUTING TASKS")
        print(f"{'='*60}\n")

        for i, (query, priority) in enumerate(DEMO_QUERIES):
            print(f"Task {i+1}: \"{query}\" (priority: {priority})")
            resp = await client.post(f"{BASE}/agent/task", json={
                "query": query,
                "priority": priority,
            })
            result = resp.json()

            for action in result.get("actions", []):
                icon = {"decide": "🤔", "query": "🔍", "pay": "⚡", "respond": "✅"}.get(action["action"], "•")
                print(f"  {icon} [{action['action']}] {action['detail']}")

            cost = result.get("cost_sats", 0)
            balance = result.get("agent_balance", 0)
            rep = result.get("reputation_score", 0)
            has_data = result.get("has_result", False)
            print(f"  → Cost: {cost} sats | Balance: {balance} sats | Rep: {rep}/100 | Data: {'Yes' if has_data else 'No'}")
            print()

            await asyncio.sleep(0.3)

        # Show final state
        resp = await client.get(f"{BASE}/agent/status")
        status = resp.json()
        print(f"{'='*60}")
        print(f"FINAL AGENT STATE")
        print(f"  Balance:     {status['wallet']['balance_sats']} sats (spent {status['wallet']['total_spent']})")
        print(f"  API Calls:   {status['total_api_calls']}")
        print(f"  Payments:    {status['successful_payments']}")
        print(f"  Reputation:  {status['reputation_score']}/100")
        print(f"{'='*60}")

        # Show credit score
        resp = await client.get(f"{BASE}/ml/credit/score", params={
            "total_payments": status["successful_payments"],
            "payment_success_rate": 1.0,
            "avg_payment_amount": status["wallet"]["total_spent"] / max(1, status["successful_payments"]),
            "time_since_first_payment": status["wallet"]["uptime_hours"],
            "transaction_frequency": status["successful_payments"] / max(0.01, status["wallet"]["uptime_hours"]),
        })
        credit = resp.json()
        print(f"\nML Credit Assessment:")
        print(f"  Credit Score:    {credit['credit_score']}/100")
        print(f"  Will Pay:        {credit['will_pay']} ({credit['will_pay_probability']:.1%})")
        print(f"  Discount:        {(1 - credit['discount_multiplier']) * 100:.0f}% off")
        print(f"  Pricing Tier:    {credit['pricing_tier']}")

        # Payment history
        resp = await client.get(f"{BASE}/payments/history")
        payments = resp.json()
        print(f"\nTotal L402 payments processed: {len(payments)}")


if __name__ == "__main__":
    asyncio.run(run_demo())
