"""Credit scoring ML model — predicts agent reliability and optimal pricing tier."""
from __future__ import annotations
import os
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_absolute_error
import joblib

from ml.training_data import generate_credit_data

SCORE_MODEL_PATH = os.path.join(os.path.dirname(__file__), "credit_score_model.joblib")
PAY_MODEL_PATH = os.path.join(os.path.dirname(__file__), "will_pay_model.joblib")

_score_model: GradientBoostingRegressor = None
_pay_model: LogisticRegression = None
_metrics: dict = {}


FEATURES = [
    "total_payments", "payment_success_rate", "avg_payment_amount",
    "time_since_first_payment", "transaction_frequency",
]


def train_models() -> dict:
    """Train both credit score and will-pay prediction models."""
    global _score_model, _pay_model, _metrics

    df = generate_credit_data(n_samples=5000)
    X = df[FEATURES]

    # Model 1: Credit score prediction
    y_score = df["credit_score"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y_score, test_size=0.2, random_state=42)
    _score_model = GradientBoostingRegressor(n_estimators=150, max_depth=4, random_state=42)
    _score_model.fit(X_tr, y_tr)
    score_mae = mean_absolute_error(y_te, _score_model.predict(X_te))

    # Model 2: Will-pay prediction
    y_pay = df["will_pay"]
    X_tr2, X_te2, y_tr2, y_te2 = train_test_split(X, y_pay, test_size=0.2, random_state=42)
    _pay_model = LogisticRegression(max_iter=1000, random_state=42)
    _pay_model.fit(X_tr2, y_tr2)
    pay_acc = accuracy_score(y_te2, _pay_model.predict(X_te2))

    _metrics = {
        "credit_score_mae": round(score_mae, 2),
        "will_pay_accuracy": round(pay_acc, 4),
        "samples": len(df),
    }

    joblib.dump(_score_model, SCORE_MODEL_PATH)
    joblib.dump(_pay_model, PAY_MODEL_PATH)
    return _metrics


def load_models() -> bool:
    global _score_model, _pay_model
    if os.path.exists(SCORE_MODEL_PATH) and os.path.exists(PAY_MODEL_PATH):
        _score_model = joblib.load(SCORE_MODEL_PATH)
        _pay_model = joblib.load(PAY_MODEL_PATH)
        return True
    return False


def predict_credit_score(
    total_payments: int,
    payment_success_rate: float,
    avg_payment_amount: float,
    time_since_first_payment: float,
    transaction_frequency: float,
) -> int:
    """Predict credit score 0-100 for an agent."""
    global _score_model
    if _score_model is None:
        if not load_models():
            train_models()
    features = np.array([[
        total_payments, payment_success_rate, avg_payment_amount,
        time_since_first_payment, transaction_frequency,
    ]])
    return int(np.clip(_score_model.predict(features)[0], 0, 100))


def predict_will_pay(
    total_payments: int,
    payment_success_rate: float,
    avg_payment_amount: float,
    time_since_first_payment: float,
    transaction_frequency: float,
) -> tuple[bool, float]:
    """Predict whether an agent will pay. Returns (prediction, probability)."""
    global _pay_model
    if _pay_model is None:
        if not load_models():
            train_models()
    features = np.array([[
        total_payments, payment_success_rate, avg_payment_amount,
        time_since_first_payment, transaction_frequency,
    ]])
    prediction = bool(_pay_model.predict(features)[0])
    probability = float(_pay_model.predict_proba(features)[0][1])
    return prediction, round(probability, 3)


def get_discount_multiplier(credit_score: int) -> float:
    """Convert credit score to pricing discount.
    Score 0-30: 1.0x (no discount)
    Score 31-60: 0.9x (10% off)
    Score 61-80: 0.8x (20% off)
    Score 81-100: 0.7x (30% off)
    """
    if credit_score > 80:
        return 0.7
    if credit_score > 60:
        return 0.8
    if credit_score > 30:
        return 0.9
    return 1.0


def get_metrics() -> dict:
    return _metrics
