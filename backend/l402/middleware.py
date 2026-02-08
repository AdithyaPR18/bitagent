"""L402 protocol middleware for FastAPI — the core of the payment system."""
from __future__ import annotations
import time
import functools
from typing import Optional, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from l402.invoice import create_invoice, settle_invoice, get_invoice
from l402.verification import create_macaroon, verify_macaroon, parse_l402_auth_header

# Payment history for analytics
payment_history: list[dict] = []


def get_payment_history() -> list[dict]:
    return payment_history


async def _handle_l402(
    request: Request,
    endpoint: str,
    price_sats: int,
) -> Optional[Response]:
    """Check L402 auth. Returns None if payment valid, or 402/403 response."""
    auth = request.headers.get("Authorization", "")

    if auth.startswith("L402 "):
        macaroon_b64, preimage = parse_l402_auth_header(auth)
        if not macaroon_b64 or not preimage:
            return JSONResponse(
                {"error": "Malformed L402 token"},
                status_code=403,
            )
        token = verify_macaroon(macaroon_b64)
        if not token:
            return JSONResponse(
                {"error": "Invalid or expired macaroon"},
                status_code=403,
            )
        # Verify the preimage matches the payment hash
        if not settle_invoice(token.payment_hash, preimage):
            return JSONResponse(
                {"error": "Invalid payment preimage"},
                status_code=403,
            )
        # Payment verified — record it
        payment_history.append({
            "endpoint": endpoint,
            "amount_sats": token.amount_sats,
            "payment_hash": token.payment_hash,
            "timestamp": time.time(),
            "agent_id": request.headers.get("X-Agent-Id", "unknown"),
        })
        return None  # Access granted

    # No valid auth — issue 402 Payment Required
    invoice = await create_invoice(
        amount_sats=price_sats,
        memo=f"L402 access: {endpoint}",
    )
    macaroon = create_macaroon(
        payment_hash=invoice.payment_hash,
        endpoint=endpoint,
        amount_sats=price_sats,
    )
    return JSONResponse(
        {
            "error": "Payment Required",
            "price_sats": price_sats,
            "invoice": invoice.payment_request,
            "payment_hash": invoice.payment_hash,
            "memo": invoice.memo,
        },
        status_code=402,
        headers={
            "WWW-Authenticate": f'L402 macaroon="{macaroon}" invoice="{invoice.payment_request}"',
        },
    )


def l402_required(price_sats: int = 10, price_fn: Optional[Callable] = None):
    """Decorator for FastAPI route functions requiring L402 payment.

    Args:
        price_sats: static price in satoshis
        price_fn: optional callable(request) -> int for dynamic pricing
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            actual_price = price_sats
            if price_fn:
                actual_price = price_fn(request)

            rejection = await _handle_l402(
                request,
                endpoint=request.url.path,
                price_sats=actual_price,
            )
            if rejection is not None:
                return rejection
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
