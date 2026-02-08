"""Mock news API — requires L402 payment."""
from __future__ import annotations
import random
import time
from fastapi import APIRouter, Request

from l402.middleware import l402_required

router = APIRouter(prefix="/api/news", tags=["news"])

HEADLINES = [
    {"title": "Bitcoin Lightning Network Hits 5000 BTC Capacity", "category": "crypto", "source": "CoinDesk"},
    {"title": "L402 Protocol Adoption Doubles in Q1 2026", "category": "crypto", "source": "Bitcoin Magazine"},
    {"title": "Stacks Nakamoto Upgrade Reaches 100% Adoption", "category": "crypto", "source": "Decrypt"},
    {"title": "AI Agents Now Process $1B in Daily Lightning Payments", "category": "ai", "source": "TechCrunch"},
    {"title": "Federal Reserve Considers Lightning Network for FedNow", "category": "finance", "source": "Reuters"},
    {"title": "OpenAI Integrates Bitcoin Micropayments for API Access", "category": "ai", "source": "The Verge"},
    {"title": "El Salvador Reports 300% Increase in Lightning Transactions", "category": "crypto", "source": "Bloomberg"},
    {"title": "MIT Study: AI Agents Prefer Bitcoin Over Traditional Payments", "category": "research", "source": "MIT Tech Review"},
    {"title": "DeFi Protocols Begin Supporting L402 Machine-to-Machine Payments", "category": "crypto", "source": "CoinTelegraph"},
    {"title": "Nostr + Lightning: The New Standard for AI Agent Identity", "category": "crypto", "source": "Bitcoin Magazine"},
    {"title": "World Bank Explores Lightning for Cross-Border Remittances", "category": "finance", "source": "Financial Times"},
    {"title": "New Clarity Smart Contract Standard for Agent Reputation", "category": "crypto", "source": "Stacks Foundation"},
]


@router.get("/")
@l402_required(price_sats=8)
async def get_news(request: Request):
    rng = random.Random(int(time.time()) // 120)
    selected = rng.sample(HEADLINES, k=min(5, len(HEADLINES)))
    for i, article in enumerate(selected):
        article["published_at"] = time.time() - rng.randint(300, 7200)
        article["relevance_score"] = round(rng.uniform(0.6, 1.0), 2)
    return {
        "data": selected,
        "count": len(selected),
        "payment": "verified",
    }


@router.get("/topic/{topic}")
@l402_required(price_sats=12)
async def get_news_by_topic(request: Request, topic: str):
    filtered = [h for h in HEADLINES if topic.lower() in h.get("category", "").lower()
                or topic.lower() in h.get("title", "").lower()]
    if not filtered:
        filtered = HEADLINES[:3]
    rng = random.Random(int(time.time()) // 120 + hash(topic))
    for article in filtered:
        article["published_at"] = time.time() - rng.randint(300, 7200)
        article["relevance_score"] = round(rng.uniform(0.6, 1.0), 2)
    return {
        "data": filtered,
        "count": len(filtered),
        "topic": topic,
        "payment": "verified",
    }
