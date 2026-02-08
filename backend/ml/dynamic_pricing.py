"""Dynamic pricing ML model — predicts optimal price per API call."""
from __future__ import annotations
import math
import time
import os
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

from ml.training_data import generate_pricing_data

MODEL_PATH = os.path.join(os.path.dirname(__file__), "pricing_model.joblib")

_model: GradientBoostingRegressor = None
_metrics: dict = {}


def train_model() -> dict:
    """Train the dynamic pricing model on synthetic data."""
    global _model, _metrics

    df = generate_pricing_data(n_samples=10000)
    features = ["hour_sin", "hour_cos", "server_load", "cache_age",
                "user_total_calls", "user_avg_payment", "endpoint_complexity"]
    X = df[features]
    y = df["optimal_price"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    _model = GradientBoostingRegressor(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.1,
        random_state=42,
    )
    _model.fit(X_train, y_train)

    y_pred = _model.predict(X_test)
    _metrics = {
        "mae": round(mean_absolute_error(y_test, y_pred), 2),
        "r2": round(r2_score(y_test, y_pred), 4),
        "feature_importance": dict(zip(features, [round(float(x), 4) for x in _model.feature_importances_])),
        "samples_trained": len(X_train),
        "samples_tested": len(X_test),
    }

    joblib.dump(_model, MODEL_PATH)
    return _metrics


def load_model():
    """Load a previously trained model."""
    global _model
    if os.path.exists(MODEL_PATH):
        _model = joblib.load(MODEL_PATH)
        return True
    return False


def predict_price(
    server_load: float = 0.3,
    cache_age: float = 60.0,
    user_total_calls: int = 10,
    user_avg_payment: float = 15.0,
    endpoint_complexity: int = 3,
) -> int:
    """Predict the optimal price in sats for an API call."""
    global _model
    if _model is None:
        if not load_model():
            train_model()

    now = time.time()
    hour = (now % 86400) / 3600  # Current hour UTC
    hour_sin = math.sin(2 * math.pi * hour / 24)
    hour_cos = math.cos(2 * math.pi * hour / 24)

    features = np.array([[
        hour_sin, hour_cos, server_load, cache_age,
        user_total_calls, user_avg_payment, endpoint_complexity,
    ]])

    price = _model.predict(features)[0]
    return max(1, int(round(price)))


def get_metrics() -> dict:
    return _metrics
