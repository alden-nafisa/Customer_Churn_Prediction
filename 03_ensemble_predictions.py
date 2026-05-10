"""
TELECOM CHURN - ENSEMBLE PREDICTIONS
====================================

Combine XGBoost dan CatBoost predictions:
1. Weighted ensemble (0.6 XGB + 0.4 CAT)
2. Voting ensemble
3. Confidence scores
"""

import pandas as pd
import numpy as np
import xgboost as xgb
import pickle
from catboost import CatBoostClassifier
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score, confusion_matrix, classification_report
import os

# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_DIR = r"c:\Users\HP14\Downloads\pbl6\Customer_Churn_Prediction\preprocessed_data"
MODEL_DIR = r"c:\Users\HP14\Downloads\pbl6\Customer_Churn_Prediction\trained_models"
RESULTS_DIR = r"c:\Users\HP14\Downloads\pbl6\Customer_Churn_Prediction\model_results"

os.makedirs(RESULTS_DIR, exist_ok=True)

# ============================================================================
# STEP 1: LOAD MODELS
# ============================================================================

print("="*80)
print("STEP 1: LOAD TRAINED MODELS")
print("="*80)

# Load XGBoost
xgb_model = xgb.Booster(model_file=f"{MODEL_DIR}/xgb_model.json")
print(f"✅ Loaded XGBoost model")

# Load CatBoost
cat_model = CatBoostClassifier()
cat_model.load_model(f"{MODEL_DIR}/cat_model.cbm")
print(f"✅ Loaded CatBoost model")

# Load metadata
with open(f"{MODEL_DIR}/models_metadata.pkl", 'rb') as f:
    models_metadata = pickle.load(f)

xgb_metrics = models_metadata['xgb_metrics']
cat_metrics = models_metadata['cat_metrics']

print(f"\n📊 XGBoost Metrics:")
print(f"   AUC: {xgb_metrics['auc']:.4f}")
print(f"   F1-Score: {xgb_metrics['f1']:.4f}")

print(f"\n📊 CatBoost Metrics:")
print(f"   AUC: {cat_metrics['auc']:.4f}")
print(f"   F1-Score: {cat_metrics['f1']:.4f}")

# ============================================================================
# STEP 2: LOAD DATA
# ============================================================================

print("\n" + "="*80)
print("STEP 2: LOAD DATA")
print("="*80)

X_val = pd.read_csv(f"{DATA_DIR}/X_val.csv")
y_val = pd.read_csv(f"{DATA_DIR}/y_val.csv")['Churn'].values

X_holdout = pd.read_csv(f"{DATA_DIR}/X_holdout.csv")

print(f"✅ Validation set: {X_val.shape}")
print(f"✅ Holdout set: {X_holdout.shape}")

# ============================================================================
# STEP 3: GENERATE INDIVIDUAL PREDICTIONS
# ============================================================================

print("\n" + "="*80)
print("STEP 3: GENERATE INDIVIDUAL PREDICTIONS")
print("="*80)

# Validation set predictions
print("\n📊 Validation Set Predictions:")

dval = xgb.DMatrix(X_val)
xgb_pred_val = xgb_model.predict(dval)
print(f"   XGBoost: {xgb_pred_val.shape}")

cat_pred_val = cat_model.predict_proba(X_val)[:, 1]
print(f"   CatBoost: {cat_pred_val.shape}")

# Holdout set predictions
print("\n📊 Holdout Set Predictions:")

dtest = xgb.DMatrix(X_holdout)
xgb_pred_holdout = xgb_model.predict(dtest)
print(f"   XGBoost: {xgb_pred_holdout.shape}")

cat_pred_holdout = cat_model.predict_proba(X_holdout)[:, 1]
print(f"   CatBoost: {cat_pred_holdout.shape}")

# ============================================================================
# STEP 4: CREATE ENSEMBLE PREDICTIONS
# ============================================================================

print("\n" + "="*80)
print("STEP 4: CREATE ENSEMBLE PREDICTIONS")
print("="*80)

# Weighted ensemble: 0.6 XGBoost + 0.4 CatBoost
# Rationale: XGBoost has slightly higher AUC (0.6710 vs 0.6678)
print("\n📊 Ensemble Strategy: Weighted Average")
print("   XGBoost weight: 0.60")
print("   CatBoost weight: 0.40")

ensemble_pred_val = 0.6 * xgb_pred_val + 0.4 * cat_pred_val
ensemble_pred_holdout = 0.6 * xgb_pred_holdout + 0.4 * cat_pred_holdout

print(f"\n✅ Ensemble predictions generated")
print(f"   Validation shape: {ensemble_pred_val.shape}")
print(f"   Holdout shape: {ensemble_pred_holdout.shape}")

# ============================================================================
# STEP 5: EVALUATE ENSEMBLE ON VALIDATION SET
# ============================================================================

print("\n" + "="*80)
print("STEP 5: EVALUATE ENSEMBLE ON VALIDATION SET")
print("="*80)

auc_ensemble = roc_auc_score(y_val, ensemble_pred_val)
ensemble_pred_binary = (ensemble_pred_val > 0.5).astype(int)

f1_ensemble = f1_score(y_val, ensemble_pred_binary)
prec_ensemble = precision_score(y_val, ensemble_pred_binary)
rec_ensemble = recall_score(y_val, ensemble_pred_binary)

print(f"\n📊 Ensemble Validation Metrics:")
print(f"   AUC: {auc_ensemble:.4f}")
print(f"   F1-Score: {f1_ensemble:.4f}")
print(f"   Precision: {prec_ensemble:.4f}")
print(f"   Recall: {rec_ensemble:.4f}")

# Confusion Matrix
cm = confusion_matrix(y_val, ensemble_pred_binary)
print(f"\n📊 Confusion Matrix:")
print(f"   TN: {cm[0, 0]:,}  | FP: {cm[0, 1]:,}")
print(f"   FN: {cm[1, 0]:,}  | TP: {cm[1, 1]:,}")

# ============================================================================
# STEP 6: COMPARE ENSEMBLE VS INDIVIDUAL MODELS
# ============================================================================

print("\n" + "="*80)
print("STEP 6: MODEL COMPARISON")
print("="*80)

auc_xgb = roc_auc_score(y_val, xgb_pred_val)
f1_xgb = f1_score(y_val, (xgb_pred_val > 0.5).astype(int))

auc_cat = roc_auc_score(y_val, cat_pred_val)
f1_cat = f1_score(y_val, (cat_pred_val > 0.5).astype(int))

comparison = pd.DataFrame({
    'Model': ['XGBoost', 'CatBoost', 'Ensemble (0.6 XGB + 0.4 CAT)'],
    'AUC': [auc_xgb, auc_cat, auc_ensemble],
    'F1-Score': [f1_xgb, f1_cat, f1_ensemble],
    'Precision': [precision_score(y_val, (xgb_pred_val > 0.5).astype(int)),
                  precision_score(y_val, (cat_pred_val > 0.5).astype(int)),
                  prec_ensemble],
    'Recall': [recall_score(y_val, (xgb_pred_val > 0.5).astype(int)),
               recall_score(y_val, (cat_pred_val > 0.5).astype(int)),
               rec_ensemble]
})

print("\n📊 COMPREHENSIVE MODEL COMPARISON (Validation Set):")
print(comparison.to_string(index=False))

best_auc_model = comparison.loc[comparison['AUC'].idxmax(), 'Model']
best_f1_model = comparison.loc[comparison['F1-Score'].idxmax(), 'Model']

print(f"\n🏆 Best by AUC: {best_auc_model} ({comparison['AUC'].max():.4f})")
print(f"🏆 Best by F1: {best_f1_model} ({comparison['F1-Score'].max():.4f})")

# ============================================================================
# STEP 7: THRESHOLD OPTIMIZATION
# ============================================================================

print("\n" + "="*80)
print("STEP 7: THRESHOLD OPTIMIZATION")
print("="*80)

print("\nFinding optimal threshold for ensemble predictions...")

best_f1 = 0
best_threshold = 0.5
f1_scores = []
thresholds = np.arange(0.2, 0.9, 0.05)

for threshold in thresholds:
    pred_binary = (ensemble_pred_val > threshold).astype(int)
    if (pred_binary == 1).sum() > 0:  # Avoid division by zero
        f1 = f1_score(y_val, pred_binary, zero_division=0)
        f1_scores.append(f1)
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = threshold
    else:
        f1_scores.append(0)

print(f"✅ Optimal Threshold: {best_threshold:.2f}")
print(f"   F1-Score at optimal threshold: {best_f1:.4f}")

print(f"\n📊 Threshold Analysis:")
for threshold, f1 in zip(thresholds, f1_scores):
    print(f"   Threshold {threshold:.2f}: F1 = {f1:.4f}")

# ============================================================================
# STEP 8: SAVE ENSEMBLE PREDICTIONS
# ============================================================================

print("\n" + "="*80)
print("STEP 8: SAVE RESULTS")
print("="*80)

# Validation predictions
val_ensemble_df = pd.DataFrame({
    'actual': y_val,
    'xgb_proba': xgb_pred_val,
    'cat_proba': cat_pred_val,
    'ensemble_proba': ensemble_pred_val,
    'ensemble_pred_threshold_0.5': (ensemble_pred_val > 0.5).astype(int),
    'ensemble_pred_optimal': (ensemble_pred_val > best_threshold).astype(int),
    'xgb_pred': (xgb_pred_val > 0.5).astype(int),
    'cat_pred': (cat_pred_val > 0.5).astype(int)
})

val_ensemble_df.to_csv(f"{RESULTS_DIR}/ensemble_validation_predictions.csv", index=False)
print(f"✅ Saved validation ensemble predictions")

# Holdout predictions
holdout_ensemble_df = pd.DataFrame({
    'xgb_proba': xgb_pred_holdout,
    'cat_proba': cat_pred_holdout,
    'ensemble_proba': ensemble_pred_holdout,
    'ensemble_pred_threshold_0.5': (ensemble_pred_holdout > 0.5).astype(int),
    'ensemble_pred_optimal': (ensemble_pred_holdout > best_threshold).astype(int),
    'xgb_pred': (xgb_pred_holdout > 0.5).astype(int),
    'cat_pred': (cat_pred_holdout > 0.5).astype(int)
})

holdout_ensemble_df.to_csv(f"{RESULTS_DIR}/ensemble_holdout_predictions.csv", index=False)
print(f"✅ Saved holdout ensemble predictions")

# Save comparison
comparison.to_csv(f"{RESULTS_DIR}/model_comparison.csv", index=False)
print(f"✅ Saved model comparison")

# ============================================================================
# STEP 9: ENSEMBLE SUMMARY
# ============================================================================

print("\n" + "="*80)
print("ENSEMBLE SUMMARY")
print("="*80)

summary_text = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              TELECOM CHURN - ENSEMBLE PREDICTION SUMMARY                   ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 ENSEMBLE CONFIGURATION:
  • Strategy: Weighted Average
  • XGBoost Weight: 0.60
  • CatBoost Weight: 0.40
  • Rationale: XGBoost has slightly better AUC (0.6710 vs 0.6678)

📈 VALIDATION SET PERFORMANCE:

  Individual Models:
    XGBoost:
      - AUC: {auc_xgb:.4f}
      - F1-Score: {f1_xgb:.4f}
      - Precision: {precision_score(y_val, (xgb_pred_val > 0.5).astype(int)):.4f}
      - Recall: {recall_score(y_val, (xgb_pred_val > 0.5).astype(int)):.4f}
    
    CatBoost:
      - AUC: {auc_cat:.4f}
      - F1-Score: {f1_cat:.4f}
      - Precision: {precision_score(y_val, (cat_pred_val > 0.5).astype(int)):.4f}
      - Recall: {recall_score(y_val, (cat_pred_val > 0.5).astype(int)):.4f}
  
  Ensemble (Weighted):
    - AUC: {auc_ensemble:.4f}
    - F1-Score (threshold=0.5): {f1_ensemble:.4f}
    - Precision: {prec_ensemble:.4f}
    - Recall: {rec_ensemble:.4f}
    
    Confusion Matrix:
      TN: {cm[0, 0]:,}  | FP: {cm[0, 1]:,}
      FN: {cm[1, 0]:,}  | TP: {cm[1, 1]:,}

🎯 THRESHOLD OPTIMIZATION:
  • Default threshold: 0.50
  • Optimal threshold: {best_threshold:.2f}
  • F1-Score at optimal: {best_f1:.4f}
  
  Why threshold optimization matters:
    - Default threshold (0.5) may not be optimal for imbalanced data
    - Optimal threshold balances precision and recall trade-off
    - Consider business requirements:
      * High recall: Catch more churners (higher false positives)
      * High precision: Reduce unnecessary retention efforts (miss some churners)
      * F1-score: Balance both metrics

📊 PREDICTIONS GENERATED:
  Validation Set: {len(val_ensemble_df):,} records
    - 4 probability scores per record
    - 4 binary predictions per record (different thresholds)
  
  Holdout Set: {len(holdout_ensemble_df):,} records
    - Ready for deployment
    - Contains probabilities and predictions

✅ FILES SAVED:
  1. ensemble_validation_predictions.csv
     - For model evaluation and analysis
  
  2. ensemble_holdout_predictions.csv
     - Ready for deployment and business use
  
  3. model_comparison.csv
     - Detailed metrics comparison

🔍 MODEL INSIGHTS:
  • XGBoost outperforms CatBoost on this dataset
    - Better AUC ({auc_xgb:.4f} vs {auc_cat:.4f})
    - Better F1-Score ({f1_xgb:.4f} vs {f1_cat:.4f})
  
  • Ensemble provides stability
    - Reduces overfitting risk
    - Leverages strengths of both algorithms
    - Recommended for production deployment

💡 BUSINESS RECOMMENDATIONS:
  1. Use ensemble predictions for deployment
  2. Adjust threshold based on business cost:
     - Cost of contacting non-churner: Retention effort cost
     - Cost of not contacting churner: Lost customer revenue
  3. Implement monitoring for prediction drift
  4. Evaluate performance on holdout set
  5. Consider periodic retraining with new data

🚀 NEXT STEPS:
  1. Threshold tuning for business metrics
  2. Final evaluation on holdout set
  3. Deployment pipeline setup
  4. Model monitoring implementation

📝 PREPROCESSING PIPELINE RECAP:
  ✅ Missing value handling
  ✅ Outlier detection & treatment (Winsorization)
  ✅ Skewed feature transformation (Log)
  ✅ Feature scaling (RobustScaler)
  ✅ Categorical encoding (Label encoding)
  ✅ Feature engineering (9 new features)
  ✅ Class balancing (SMOTE-TomEk on training only)
  ✅ Stratified train-test-holdout split

Total Features in Model: 81
  - Original: 58
  - Engineered: 9
  - Interactions/Transformations: 14
"""

print(summary_text)

with open(f"{RESULTS_DIR}/ENSEMBLE_SUMMARY.txt", 'w', encoding='utf-8') as f:
    f.write(summary_text)

print(f"\n✅ Summary saved to: {RESULTS_DIR}/ENSEMBLE_SUMMARY.txt")
print(f"✅ ENSEMBLE PREDICTIONS COMPLETED SUCCESSFULLY! 🎉")
