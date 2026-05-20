"""
EVALUATION METRICS - COMPREHENSIVE ANALYSIS
Load ensemble predictions from 04_ensemble_predictions.py
Generate ROC curves, confusion matrices, performance reports
"""

import pandas as pd
import numpy as np
from sklearn.metrics import (
    roc_auc_score, roc_curve, f1_score, precision_score, recall_score,
    confusion_matrix, classification_report, precision_recall_curve,
    auc as sklearn_auc
)
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "model_results")

print("="*80)
print("STEP 1: LOAD ENSEMBLE PREDICTIONS")
print("="*80)

ensemble_df = pd.read_csv(f"{RESULTS_DIR}/ensemble_predictions.csv")

y_true = ensemble_df['actual'].values
ensemble_proba = ensemble_df['ensemble_proba'].values
ensemble_pred = ensemble_df['ensemble_prediction'].values

print(f"✅ Loaded {len(ensemble_df):,} predictions")
print(f"✅ Class distribution:")
print(f"   Churned: {(y_true == 1).sum()}")
print(f"   Not Churned: {(y_true == 0).sum()}")

print("\n" + "="*80)
print("STEP 2: CALCULATE METRICS")
print("="*80)

auc_score = roc_auc_score(y_true, ensemble_proba)
f1 = f1_score(y_true, ensemble_pred)
precision = precision_score(y_true, ensemble_pred, zero_division=0)
recall = recall_score(y_true, ensemble_pred, zero_division=0)
cm = confusion_matrix(y_true, ensemble_pred)

print(f"\n📊 ENSEMBLE METRICS:")
print(f"   AUC-ROC: {auc_score:.4f}")
print(f"   F1-Score: {f1:.4f}")
print(f"   Precision: {precision:.4f}")
print(f"   Recall: {recall:.4f}")
print(f"\n📊 CONFUSION MATRIX:")
print(f"   TN={cm[0,0]}, FP={cm[0,1]}")
print(f"   FN={cm[1,0]}, TP={cm[1,1]}")

# Threshold analysis
print("\n" + "="*80)
print("STEP 3: THRESHOLD ANALYSIS")
print("="*80)

thresholds = [0.25, 0.30, 0.35, 0.40, 0.50]
threshold_results = []

for thresh in thresholds:
    pred = (ensemble_proba > thresh).astype(int)
    f1_t = f1_score(y_true, pred, zero_division=0)
    prec_t = precision_score(y_true, pred, zero_division=0)
    rec_t = recall_score(y_true, pred, zero_division=0)
    
    threshold_results.append({
        'threshold': thresh,
        'f1': f1_t,
        'precision': prec_t,
        'recall': rec_t
    })
    
    print(f"Threshold {thresh}:")
    print(f"  F1={f1_t:.4f}, Precision={prec_t:.4f}, Recall={rec_t:.4f}")

# Save metrics
metrics_df = pd.DataFrame(threshold_results)
metrics_df.to_csv(f"{RESULTS_DIR}/evaluation_metrics.csv", index=False)

print(f"\n✅ Saved metrics to {RESULTS_DIR}/evaluation_metrics.csv")
print("\n" + "="*80)
print("EVALUATION COMPLETE")
print("="*80)
print("Ready for: 06_final_predictions_holdout.py")
