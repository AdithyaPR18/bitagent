"""Mock stock price API — requires L402 payment."""
from __future__ import annotations
import random
import time
import math
from fastapi import APIRouter, Request

from l402.middleware import l402_required

router = APIRouter(prefix="/api/stocks", tags=["stocks"])

BASE_PRICES = {
    "BTC": 97500.0,
    "ETH": 3200.0,
    "AAPL": 195.0,
    "GOOGL": 178.0,
    "TSLA": 248.0,
    "MSFT": 420.0,
    "NVDA": 850.0,
    "STX": 1.85,
}


def _simulate_price(symbol: str) -> dict:
    base = BASE_PRICES.get(symbol.upper(), 100.0)
    # Deterministic but time-varying price using sine + noise
    t = time.time()
    noise = math.sin(t / 60) * base * 0.002 + math.sin(t / 13) * base * 0.001
    rng = random.Random(int(t // 10))
    jitter = rng.uniform(-0.005, 0.005) * base
    price = base + noise + jitter
    change_24h = rng.uniform(-5, 5)
    return {
        "symbol": symbol.upper(),
        "price": round(price, 2),
        "change_24h_pct": round(change_24h, 2),
        "volume_24h": rng.randint(1_000_000, 50_000_000),
        "high_24h": round(price * 1.02, 2),
        "low_24h": round(price * 0.98, 2),
        "timestamp": t,
    }


@router.get("/{symbol}")
@l402_required(price_sats=15)
async def get_stock(request: Request, symbol: str):
    return {
        "data": _simulate_price(symbol),
        "payment": "verified",
        "endpoint": f"/api/stocks/{symbol}",
    }


@router.get("/")
@l402_required(price_sats=10)
async def list_symbols(request: Request):
    return {
        "symbols": list(BASE_PRICES.keys()),
        "payment": "verified",
    }
