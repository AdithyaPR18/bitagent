"""Macaroon-based payment verification for L402 protocol."""
from __future__ import annotations
import base64
import hashlib
import hmac
import json
import time
from typing import Optional
from dataclasses import dataclass

from config import get_settings


@dataclass
class L402Token:
    macaroon: str  # base64-encoded
    payment_hash: str
    endpoint: str
    amount_sats: int
    expires_at: float


def create_macaroon(payment_hash: str, endpoint: str, amount_sats: int) -> str:
    """Create a simple macaroon containing payment details.

    In production, use pymacaroons for proper caveat chains.
    For hackathon demo, we use HMAC-signed JSON tokens.
    """
    settings = get_settings()
    payload = {
        "payment_hash": payment_hash,
        "endpoint": endpoint,
        "amount_sats": amount_sats,
        "expires_at": time.time() + 3600,  # 1 hour
        "version": "L402-v1",
    }
    payload_bytes = json.dumps(payload, sort_keys=True).encode()
    signature = hmac.new(
        settings.macaroon_secret_key.encode(),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()
    token_data = {**payload, "signature": signature}
    return base64.b64encode(json.dumps(token_data).encode()).decode()


def verify_macaroon(macaroon_b64: str) -> Optional[L402Token]:
    """Verify a macaroon's integrity and extract its claims."""
    settings = get_settings()
    try:
        token_data = json.loads(base64.b64decode(macaroon_b64))
    except Exception:
        return None

    signature = token_data.pop("signature", "")
    payload_bytes = json.dumps(token_data, sort_keys=True).encode()
    expected = hmac.new(
        settings.macaroon_secret_key.encode(),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        return None

    if token_data.get("expires_at", 0) < time.time():
        return None

    return L402Token(
        macaroon=macaroon_b64,
        payment_hash=token_data["payment_hash"],
        endpoint=token_data["endpoint"],
        amount_sats=token_data["amount_sats"],
        expires_at=token_data["expires_at"],
    )


def parse_l402_auth_header(auth_header: str) -> tuple[Optional[str], Optional[str]]:
    """Parse 'L402 <macaroon>:<preimage>' header.
    Returns (macaroon_b64, preimage) or (None, None).
    """
    if not auth_header.startswith("L402 "):
        return None, None
    token_part = auth_header[5:].strip()
    if ":" not in token_part:
        return None, None
    macaroon_b64, preimage = token_part.split(":", 1)
    return macaroon_b64, preimage
