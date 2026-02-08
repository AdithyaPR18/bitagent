"""Mock weather API — requires L402 payment."""
from __future__ import annotations
import random
import time
from fastapi import APIRouter, Request

from l402.middleware import l402_required

router = APIRouter(prefix="/api/weather", tags=["weather"])

CITIES = {
    "new haven": {"lat": 41.31, "lon": -72.92},
    "new york": {"lat": 40.71, "lon": -74.01},
    "san francisco": {"lat": 37.77, "lon": -122.42},
    "miami": {"lat": 25.76, "lon": -80.19},
    "chicago": {"lat": 41.88, "lon": -87.63},
    "london": {"lat": 51.51, "lon": -0.13},
    "tokyo": {"lat": 35.68, "lon": 139.69},
}

CONDITIONS = ["Sunny", "Partly Cloudy", "Cloudy", "Rainy", "Snowy", "Windy", "Foggy"]


def _generate_weather(city: str) -> dict:
    seed = hash(city + str(int(time.time()) // 300))  # Changes every 5 min
    rng = random.Random(seed)
    return {
        "city": city.title(),
        "coordinates": CITIES.get(city.lower(), {"lat": 0, "lon": 0}),
        "temperature_f": rng.randint(20, 95),
        "humidity_pct": rng.randint(30, 90),
        "wind_mph": rng.randint(0, 30),
        "condition": rng.choice(CONDITIONS),
        "forecast_3h": rng.choice(CONDITIONS),
        "data_freshness_seconds": rng.randint(10, 300),
        "timestamp": time.time(),
    }


@router.get("/{city}")
@l402_required(price_sats=10)
async def get_weather(request: Request, city: str):
    return {
        "data": _generate_weather(city),
        "payment": "verified",
        "endpoint": f"/api/weather/{city}",
    }


@router.get("/")
@l402_required(price_sats=5)
async def list_cities(request: Request):
    return {
        "cities": list(CITIES.keys()),
        "payment": "verified",
    }
