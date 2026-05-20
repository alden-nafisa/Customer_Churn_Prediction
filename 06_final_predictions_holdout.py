"""
FINAL PREDICTIONS HOLDOUT
Load ensemble predictions and generate final deployment-ready output
"""

import pandas as pd
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "model_results")

print("="*80)
print("STEP 1: LOAD ENSEMBLE PREDICTIONS")
print("="*80)

ensemble_df = pd.read_csv(f"{RESULTS_DIR}/ensemble_predictions.csv")
metrics_df = pd.read_csv(f"{RESULTS_DIR}/evaluation_metrics.csv")

print(f"✅ Loaded {len(ensemble_df):,} predictions")

# Get optimal threshold from metrics (highest F1-score)
best_threshold = metrics_df.loc[metrics_df['f1'].idxmax(), 'threshold']
print(f"✅ Optimal threshold: {best_threshold} (F1={metrics_df['f1'].max():.4f})")

print("\n" + "="*80)
print("STEP 2: GENERATE FINAL PREDICTIONS")
print("="*80)

ensemble_proba = ensemble_df['ensemble_proba'].values

# Create final predictions with different thresholds
final_predictions = pd.DataFrame({
    'record_id': np.arange(1, len(ensemble_df) + 1),
    'plan': ensemble_df['plan'].values,
    'actual_churn': ensemble_df['actual'].values,
    'churn_probability': ensemble_proba,
    'prediction_optimal': (ensemble_proba > best_threshold).astype(int),
    'prediction_threshold_0.25': (ensemble_proba > 0.25).astype(int),
    'prediction_threshold_0.30': (ensemble_proba > 0.30).astype(int),
    'prediction_threshold_0.50': (ensemble_proba > 0.50).astype(int),
    'xgb_probability': ensemble_df['xgb_proba'].values,
    'cat_probability': ensemble_df['cat_proba'].values
})

# Add risk level
def get_risk_level(prob):
    if prob < 0.25:
        return 'LOW'
    elif prob < 0.40:
        return 'MEDIUM'
    elif prob < 0.60:
        return 'HIGH'
    else:
        return 'VERY_HIGH'

final_predictions['risk_level'] = final_predictions['churn_probability'].apply(get_risk_level)

# Save full predictions
final_predictions.to_csv(f"{RESULTS_DIR}/final_predictions.csv", index=False)
print(f"✅ Saved full predictions: {RESULTS_DIR}/final_predictions.csv")

# Save deployment-ready format (for CRM/retention systems)
deployment_df = final_predictions[['record_id', 'plan', 'churn_probability', 'risk_level']].copy()
deployment_df = deployment_df.rename(columns={
    'record_id': 'customer_id',
    'churn_probability': 'churn_probability_score',
    'risk_level': 'retention_priority'
})
deployment_df.to_csv(f"{RESULTS_DIR}/final_predictions_deployment.csv", index=False)
print(f"✅ Saved deployment format: {RESULTS_DIR}/final_predictions_deployment.csv")

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"Total predictions: {len(final_predictions)}")
print(f"\nRisk distribution:")
for risk in ['LOW', 'MEDIUM', 'HIGH', 'VERY_HIGH']:
    count = (final_predictions['risk_level'] == risk).sum()
    pct = count / len(final_predictions) * 100
    print(f"  {risk}: {count} ({pct:.1f}%)")

print("\n" + "="*80)
print("FINAL PREDICTIONS COMPLETE")
print("="*80)
print("✅ Pipeline finished successfully!")
print("\nNext step: streamlit run app_lapisai.py")
