#!/usr/bin/env python3
"""Train all ML models and print metrics."""
import sys
sys.path.insert(0, "../backend")

from ml.dynamic_pricing import train_model as train_pricing
from ml.credit_scoring import train_models as train_credit

print("=" * 60)
print("BitAgent ML Model Training")
print("=" * 60)

print("\n[1/2] Dynamic Pricing Model")
print("-" * 40)
pm = train_pricing()
print(f"  Samples: {pm['samples_trained']} train / {pm['samples_tested']} test")
print(f"  MAE: {pm['mae']} sats")
print(f"  R2:  {pm['r2']}")
print(f"  Feature importance:")
for feat, imp in sorted(pm["feature_importance"].items(), key=lambda x: -x[1]):
    bar = "#" * int(imp * 50)
    print(f"    {feat:25s} {imp:.4f} {bar}")

print(f"\n[2/2] Credit Scoring Models")
print("-" * 40)
cm = train_credit()
print(f"  Samples: {cm['samples']}")
print(f"  Credit Score MAE: {cm['credit_score_mae']}")
print(f"  Will-Pay Accuracy: {cm['will_pay_accuracy']:.1%}")

print("\nAll models trained and saved!")
