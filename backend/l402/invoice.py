"""Lightning invoice generation — mock implementation with real LND interface ready."""
from __future__ import annotations
import hashlib
import secrets
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx
from config import get_settings


@dataclass
class Invoice:
    payment_hash: str
    payment_request: str  # bolt11 invoice string
    amount_sats: int
    memo: str
    created_at: float = field(default_factory=time.time)
    settled: bool = False
    preimage: str = ""


# In-memory store for mock invoices
_invoices: dict[str, Invoice] = {}


def _mock_create_invoice(amount_sats: int, memo: str = "") -> Invoice:
    """Create a mock Lightning invoice for demo/regtest."""
    preimage = secrets.token_hex(32)
    payment_hash = hashlib.sha256(bytes.fromhex(preimage)).hexdigest()
    # Fake bolt11 that looks realistic
    payment_request = f"lnbcrt{amount_sats}0n1pbitagt{secrets.token_hex(20)}"
    inv = Invoice(
        payment_hash=payment_hash,
        payment_request=payment_request,
        amount_sats=amount_sats,
        memo=memo,
        preimage=preimage,
    )
    _invoices[payment_hash] = inv
    return inv


async def _lnd_create_invoice(amount_sats: int, memo: str = "") -> Invoice:
    """Create invoice via real LND REST API."""
    settings = get_settings()
    async with httpx.AsyncClient(verify=False) as client:
        resp = await client.post(
            f"{settings.lnd_rest_host}/v1/invoices",
            json={"value": str(amount_sats), "memo": memo},
            headers={"Grpc-Metadata-macaroon": _read_macaroon_hex()},
        )
        resp.raise_for_status()
        data = resp.json()
        inv = Invoice(
            payment_hash=data["r_hash"],
            payment_request=data["payment_request"],
            amount_sats=amount_sats,
            memo=memo,
        )
        _invoices[inv.payment_hash] = inv
        return inv


def _read_macaroon_hex() -> str:
    settings = get_settings()
    if not settings.lnd_macaroon_path:
        return ""
    with open(settings.lnd_macaroon_path, "rb") as f:
        return f.read().hex()


async def create_invoice(amount_sats: int, memo: str = "") -> Invoice:
    """Create a Lightning invoice. Uses mock or real LND based on config."""
    settings = get_settings()
    if settings.use_mock_lightning:
        return _mock_create_invoice(amount_sats, memo)
    return await _lnd_create_invoice(amount_sats, memo)


def get_invoice(payment_hash: str) -> Optional[Invoice]:
    return _invoices.get(payment_hash)


def settle_invoice(payment_hash: str, preimage: str) -> bool:
    """Verify preimage and mark invoice as settled."""
    inv = _invoices.get(payment_hash)
    if not inv:
        return False
    expected_hash = hashlib.sha256(bytes.fromhex(preimage)).hexdigest()
    if expected_hash != payment_hash:
        return False
    inv.settled = True
    inv.preimage = preimage
    return True


def mock_pay_invoice(payment_hash: str) -> Optional[str]:
    """Simulate paying an invoice (for demo). Returns preimage."""
    inv = _invoices.get(payment_hash)
    if not inv:
        return None
    inv.settled = True
    return inv.preimage
