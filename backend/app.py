"""BitAgent — Bitcoin-Native AI Agent Operating System.

Main FastAPI application wiring L402 APIs, AI agent, ML models,
reputation system, and WebSocket for real-time dashboard updates.
"""
from __future__ import annotations
import asyncio
import json
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from api import weather, stocks, news
from agent.langchain_agent import BitAgent
from agent.decision_maker import evaluate_payment
from l402.middleware import get_payment_history
from l402.invoice import get_invoice
from ml.dynamic_pricing import train_model as train_pricing, predict_price, get_metrics as pricing_metrics
from ml.credit_scoring import (
    train_models as train_credit,
    predict_credit_score,
    predict_will_pay,
    get_discount_multiplier,
    get_metrics as credit_metrics,
)
from blockchain.stacks_client import reputation_client

# Global agent instance
agent: BitAgent = None
ws_clients: list[WebSocket] = []


async def broadcast(msg: dict):
    data = json.dumps(msg)
    for ws in ws_clients[:]:
        try:
            await ws.send_text(data)
        except Exception:
            ws_clients.remove(ws)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent
    # Train ML models on startup
    print("Training dynamic pricing model...")
    pm = train_pricing()
    print(f"  Pricing model: MAE={pm['mae']}, R2={pm['r2']}")
    print("Training credit scoring models...")
    cm = train_credit()
    print(f"  Credit model: MAE={cm['credit_score_mae']}, Will-pay accuracy={cm['will_pay_accuracy']}")

    # Initialize agent
    settings = get_settings()
    agent = BitAgent("agent-alpha", initial_balance=settings.agent_initial_balance)
    await reputation_client.register_agent(agent.agent_id)
    print(f"Agent '{agent.agent_id}' initialized with {agent.wallet.balance_sats} sats")

    yield


app = FastAPI(title="BitAgent", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount paid API routes
app.include_router(weather.router)
app.include_router(stocks.router)
app.include_router(news.router)


# ── Agent Endpoints ───────────────────────────────────────────────

@app.post("/agent/task")
async def agent_execute_task(request: Request):
    """Have the agent execute a task (may involve L402 payments)."""
    body = await request.json()
    query = body.get("query", "")
    priority = body.get("priority", "normal")

    task = await agent.execute_task(query, priority)

    # Update reputation after payment
    if task.total_cost_sats > 0:
        new_score = await reputation_client.record_payment(
            agent.agent_id,
            task.total_cost_sats,
            task.endpoint,
            success=task.result is not None,
        )
        agent.reputation_score = new_score

    # Broadcast to dashboard
    await broadcast({
        "type": "task_completed",
        "query": query,
        "cost": task.total_cost_sats,
        "success": task.result is not None,
        "reputation": agent.reputation_score,
        "balance": agent.wallet.balance_sats,
        "timestamp": time.time(),
    })

    return {
        "query": query,
        "priority": priority,
        "endpoint": task.endpoint,
        "cost_sats": task.total_cost_sats,
        "completed": task.completed,
        "has_result": task.result is not None,
        "result": task.result,
        "actions": [
            {"action": a.action, "detail": a.detail, "timestamp": a.timestamp}
            for a in task.actions
        ],
        "agent_balance": agent.wallet.balance_sats,
        "reputation_score": agent.reputation_score,
    }


@app.get("/agent/status")
async def agent_status():
    return agent.get_status()


@app.get("/agent/wallet")
async def agent_wallet():
    return agent.wallet.get_stats()


@app.get("/agent/wallet/history")
async def agent_wallet_history():
    return agent.wallet.get_history()


@app.get("/agent/tasks")
async def agent_tasks():
    return agent.get_task_history()


@app.post("/agent/fund")
async def fund_agent(request: Request):
    """Add sats to the agent's wallet."""
    body = await request.json()
    amount = body.get("amount_sats", 1000)
    agent.wallet.receive(amount, "Manual deposit via dashboard")
    await broadcast({
        "type": "agent_funded",
        "amount": amount,
        "balance": agent.wallet.balance_sats,
        "timestamp": time.time(),
    })
    return {"balance": agent.wallet.balance_sats, "deposited": amount}


# ── ML / Pricing Endpoints ────────────────────────────────────────

@app.get("/ml/pricing/predict")
async def ml_predict_price(
    server_load: float = 0.3,
    cache_age: float = 60.0,
    user_total_calls: int = 10,
    user_avg_payment: float = 15.0,
    endpoint_complexity: int = 3,
):
    price = predict_price(server_load, cache_age, user_total_calls, user_avg_payment, endpoint_complexity)
    return {"predicted_price_sats": price, "inputs": {
        "server_load": server_load, "cache_age": cache_age,
        "user_total_calls": user_total_calls, "user_avg_payment": user_avg_payment,
        "endpoint_complexity": endpoint_complexity,
    }}


@app.get("/ml/pricing/metrics")
async def ml_pricing_metrics():
    return pricing_metrics()


@app.get("/ml/credit/score")
async def ml_credit_score(
    total_payments: int = 30,
    payment_success_rate: float = 0.95,
    avg_payment_amount: float = 15.0,
    time_since_first_payment: float = 48.0,
    transaction_frequency: float = 0.6,
):
    score = predict_credit_score(
        total_payments, payment_success_rate, avg_payment_amount,
        time_since_first_payment, transaction_frequency,
    )
    will_pay, prob = predict_will_pay(
        total_payments, payment_success_rate, avg_payment_amount,
        time_since_first_payment, transaction_frequency,
    )
    discount = get_discount_multiplier(score)
    return {
        "credit_score": score,
        "will_pay": will_pay,
        "will_pay_probability": prob,
        "discount_multiplier": discount,
        "pricing_tier": "premium" if score > 80 else "standard" if score > 30 else "basic",
    }


@app.get("/ml/credit/metrics")
async def ml_credit_metrics():
    return credit_metrics()


# ── Reputation Endpoints ──────────────────────────────────────────

@app.get("/reputation/{agent_id}")
async def get_reputation(agent_id: str):
    rep = await reputation_client.get_reputation(agent_id)
    if not rep:
        return JSONResponse({"error": "Agent not found"}, status_code=404)
    discount = await reputation_client.get_discount_tier(agent_id)
    return {**rep, "discount_multiplier": discount}


@app.get("/reputation")
async def list_reputations():
    return await reputation_client.get_all_agents()


# ── Payment History ───────────────────────────────────────────────

@app.get("/payments/history")
async def payments_history():
    return get_payment_history()


# ── Dashboard Stats ───────────────────────────────────────────────

@app.get("/dashboard/stats")
async def dashboard_stats():
    return {
        "agent": agent.get_status(),
        "wallet": agent.wallet.get_stats(),
        "reputation": await reputation_client.get_reputation(agent.agent_id),
        "ml_models": {
            "pricing": pricing_metrics(),
            "credit": credit_metrics(),
        },
        "total_payments_processed": len(get_payment_history()),
        "timestamp": time.time(),
    }


# ── WebSocket ─────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    ws_clients.append(ws)
    try:
        # Send initial state
        await ws.send_text(json.dumps({
            "type": "init",
            "agent": agent.get_status(),
            "wallet": agent.wallet.get_stats(),
            "timestamp": time.time(),
        }))
        while True:
            data = await ws.receive_text()
            await ws.send_text(json.dumps({"type": "ack", "data": data}))
    except WebSocketDisconnect:
        ws_clients.remove(ws)


# ── Health ────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": time.time(), "agent_id": agent.agent_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
