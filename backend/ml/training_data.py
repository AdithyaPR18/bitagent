"""Generate synthetic training data for dynamic pricing and credit scoring models."""
from __future__ import annotations
import math
import random
import numpy as np
import pandas as pd


def generate_pricing_data(n_samples: int = 10000, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic data for the dynamic pricing model.

    Features:
        hour_sin, hour_cos: cyclic time encoding
        server_load: 0-1 normalized server utilization
        cache_age: seconds since data was cached (0 = fresh)
        user_total_calls: how many calls this user has made historically
        user_avg_payment: average sats this user pays
        endpoint_complexity: 1-5 scale of how expensive the endpoint is to serve

    Target:
        optimal_price: sats (what price maximizes revenue)
    """
    rng = np.random.RandomState(seed)

    hours = rng.uniform(0, 24, n_samples)
    hour_sin = np.sin(2 * np.pi * hours / 24)
    hour_cos = np.cos(2 * np.pi * hours / 24)
    server_load = rng.beta(2, 5, n_samples)  # Skewed low
    cache_age = rng.exponential(120, n_samples)  # seconds
    user_total_calls = rng.poisson(50, n_samples)
    user_avg_payment = rng.uniform(5, 50, n_samples)
    endpoint_complexity = rng.choice([1, 2, 3, 4, 5], n_samples, p=[0.3, 0.25, 0.2, 0.15, 0.1])

    # Price model: base + time premium + load premium + freshness premium - loyalty discount
    base_price = 5.0
    time_premium = 5.0 * (1 + hour_sin * 0.3)  # Higher during "peak" hours
    load_premium = 15.0 * server_load ** 2
    freshness_premium = np.clip(5.0 * (1 - cache_age / 600), 0, 5)
    loyalty_discount = np.clip(user_total_calls / 200, 0, 0.3) * base_price
    complexity_mult = endpoint_complexity / 3.0

    optimal_price = (
        (base_price + time_premium + load_premium + freshness_premium - loyalty_discount)
        * complexity_mult
        + rng.normal(0, 1, n_samples)  # noise
    )
    optimal_price = np.clip(optimal_price, 1, 100).astype(int)

    return pd.DataFrame({
        "hour_sin": hour_sin,
        "hour_cos": hour_cos,
        "server_load": server_load,
        "cache_age": cache_age,
        "user_total_calls": user_total_calls,
        "user_avg_payment": user_avg_payment,
        "endpoint_complexity": endpoint_complexity,
        "optimal_price": optimal_price,
    })


def generate_credit_data(n_samples: int = 5000, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic data for the credit scoring model.

    Features:
        total_payments: number of successful payments
        payment_success_rate: 0-1
        avg_payment_amount: average sats per payment
        time_since_first_payment: hours since first seen
        transaction_frequency: payments per hour

    Target:
        credit_score: 0-100
        will_pay: binary (will this agent pay the offered price?)
    """
    rng = np.random.RandomState(seed)

    total_payments = rng.poisson(30, n_samples)
    payment_success_rate = rng.beta(8, 2, n_samples)  # Most agents are reliable
    avg_payment_amount = rng.uniform(5, 60, n_samples)
    time_since_first = rng.exponential(48, n_samples)  # hours
    transaction_frequency = np.where(
        time_since_first > 0,
        total_payments / np.maximum(time_since_first, 1),
        0,
    )

    # Credit score: weighted combination
    credit_score = (
        20 * np.clip(total_payments / 100, 0, 1)
        + 30 * payment_success_rate
        + 15 * np.clip(avg_payment_amount / 50, 0, 1)
        + 20 * np.clip(time_since_first / 168, 0, 1)  # 1 week = 168h
        + 15 * np.clip(transaction_frequency / 2, 0, 1)
        + rng.normal(0, 3, n_samples)
    )
    credit_score = np.clip(credit_score, 0, 100).astype(int)

    # Will-pay probability: logistic function of credit score + price sensitivity
    will_pay_prob = 1 / (1 + np.exp(-0.1 * (credit_score - 40)))
    will_pay = (rng.uniform(0, 1, n_samples) < will_pay_prob).astype(int)

    return pd.DataFrame({
        "total_payments": total_payments,
        "payment_success_rate": payment_success_rate,
        "avg_payment_amount": avg_payment_amount,
        "time_since_first_payment": time_since_first,
        "transaction_frequency": transaction_frequency,
        "credit_score": credit_score,
        "will_pay": will_pay,
    })
