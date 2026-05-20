"""
ENSEMBLE PREDICTIONS - LOAD PLAN-SPECIFIC MODELS
Combine XGBoost dan CatBoost untuk setiap plan type
Output: ensemble_predictions.csv untuk digunakan evaluation & final predictions
"""

import pandas as pd
import numpy as np
import pickle
import os
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "preprocessed_data")
MODEL_DIR = os.path.join(BASE_DIR, "trained_models", "plan_specific")
RESULTS_DIR = os.path.join(BASE_DIR, "model_results")
os.makedirs(RESULTS_DIR, exist_ok=True)

print("="*80)
print("STEP 1: LOAD PLAN-SPECIFIC MODELS")
print("="*80)

PLANS = ['starter', 'professional', 'enterprise']
models = {}

for plan in PLANS:
    xgb_file = os.path.join(MODEL_DIR, f"{plan}_xgboost.pkl")
    cat_file = os.path.join(MODEL_DIR, f"{plan}_catboost.pkl")
    
    with open(xgb_file, 'rb') as f:
        xgb_model = pickle.load(f)
    with open(cat_file, 'rb') as f:
        cat_model = pickle.load(f)
    
    models[plan] = {'xgb': xgb_model, 'cat': cat_model}
    print(f"✅ Loaded {plan.upper()}: XGBoost + CatBoost")

print("\n" + "="*80)
print("STEP 2: LOAD PREPROCESSED DATA")
print("="*80)

# Load test sets untuk setiap plan
test_data = {}
for plan in PLANS:
    test_file = os.path.join(DATA_DIR, f"{plan}_test.csv")
    df = pd.read_csv(test_file)
    X_test = df.drop('churned', axis=1)
    y_test = df['churned']
    test_data[plan] = {'X': X_test, 'y': y_test}
    print(f"✅ Loaded {plan.upper()} test set: {X_test.shape[0]} samples")

print("\n" + "="*80)
print("STEP 3: GENERATE ENSEMBLE PREDICTIONS")
print("="*80)

all_predictions = []

for plan in PLANS:
    print(f"\n{plan.upper()}:")
    X_test = test_data[plan]['X']
    y_test = test_data[plan]['y']
    
    # XGBoost predictions
    xgb_proba = models[plan]['xgb'].predict_proba(X_test)[:, 1]
    
    # CatBoost predictions  
    cat_proba = models[plan]['cat'].predict_proba(X_test)[:, 1]
    
    # Ensemble: weighted average (0.6 XGB + 0.4 CAT)
    ensemble_proba = 0.6 * xgb_proba + 0.4 * cat_proba
    ensemble_pred = (ensemble_proba > 0.5).astype(int)
    
    # Metrics
    auc = roc_auc_score(y_test.values, ensemble_proba)
    f1 = f1_score(y_test.values, ensemble_pred)
    prec = precision_score(y_test.values, ensemble_pred, zero_division=0)
    rec = recall_score(y_test.values, ensemble_pred, zero_division=0)
    
    print(f"  AUC: {auc:.4f}")
    print(f"  F1-Score: {f1:.4f}")
    print(f"  Precision: {prec:.4f}")
    print(f"  Recall: {rec:.4f}")
    
    # Store results
    for i, (actual, pred_xgb, pred_cat, pred_ens) in enumerate(zip(y_test.values, xgb_proba, cat_proba, ensemble_proba)):
        all_predictions.append({
            'plan': plan,
            'actual': actual,
            'xgb_proba': pred_xgb,
            'cat_proba': pred_cat,
            'ensemble_proba': pred_ens,
            'ensemble_prediction': (pred_ens > 0.5).astype(int)
        })

# Save results
results_df = pd.DataFrame(all_predictions)
results_df.to_csv(os.path.join(RESULTS_DIR, "ensemble_predictions.csv"), index=False)
print(f"\n✅ Saved ensemble predictions: {len(results_df)} records")

print("\n" + "="*80)
print("ENSEMBLE COMPLETE")
print("="*80)
print(f"Output: {RESULTS_DIR}/ensemble_predictions.csv")
print("Ready for: 05_evaluation_metrics.py → 06_final_predictions_holdout.py")
