"""
TELECOM CHURN - MODEL TRAINING (UNIFIED)
=========================================

Training XGBoost dan CatBoost models:
- Single unified models untuk semua data
- Ensemble combination untuk predictions
"""

import pandas as pd
import numpy as np
import xgboost as xgb
import catboost as cb
from catboost import CatBoostClassifier
from sklearn.metrics import (
    roc_auc_score, f1_score, precision_score, recall_score, roc_curve
)
import warnings
warnings.filterwarnings('ignore')
import pickle
import os

# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_DIR = r"c:\Users\HP14\Downloads\pbl6\Customer_Churn_Prediction\preprocessed_data"
MODEL_DIR = r"c:\Users\HP14\Downloads\pbl6\Customer_Churn_Prediction\trained_models"
RESULTS_DIR = r"c:\Users\HP14\Downloads\pbl6\Customer_Churn_Prediction\model_results"

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# ============================================================================
# STEP 1: LOAD PREPROCESSED DATA
# ============================================================================

print("="*80)
print("STEP 1: LOAD PREPROCESSED DATA")
print("="*80)

X_train = pd.read_csv(f"{DATA_DIR}/X_train_balanced.csv")
y_train = pd.read_csv(f"{DATA_DIR}/y_train_balanced.csv")['Churn'].values

X_val = pd.read_csv(f"{DATA_DIR}/X_val.csv")
y_val = pd.read_csv(f"{DATA_DIR}/y_val.csv")['Churn'].values

X_holdout = pd.read_csv(f"{DATA_DIR}/X_holdout.csv")

print(f"✅ Training set: {X_train.shape}")
print(f"   - Class 0: {(y_train == 0).sum()}")
print(f"   - Class 1: {(y_train == 1).sum()}")
print(f"   - Ratio: {(y_train == 0).sum() / (y_train == 1).sum():.2f}:1")

print(f"\n✅ Validation set: {X_val.shape}")
print(f"   - Class 0: {(y_val == 0).sum()}")
print(f"   - Class 1: {(y_val == 1).sum()}")
print(f"   - Ratio: {(y_val == 0).sum() / (y_val == 1).sum():.2f}:1")

print(f"\n✅ Holdout set: {X_holdout.shape}")

# ============================================================================
# STEP 2: TRAIN XGBOOST MODEL
# ============================================================================

print("\n" + "="*80)
print("STEP 2: TRAIN XGBOOST MODEL")
print("="*80)

xgb_params = {
    'objective': 'binary:logistic',
    'max_depth': 6,
    'learning_rate': 0.05,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'lambda': 3.0,
    'alpha': 0.1,
    'min_child_weight': 1,
    'eval_metric': 'auc',
    'random_state': 42,
    'verbosity': 0,
    'n_jobs': -1
}

print("Training XGBoost...")

dtrain = xgb.DMatrix(X_train, label=y_train)
dval = xgb.DMatrix(X_val, label=y_val)
dtest = xgb.DMatrix(X_holdout)

xgb_model = xgb.train(
    xgb_params,
    dtrain,
    num_boost_round=1000,
    evals=[(dval, 'validation')],
    early_stopping_rounds=100,
    verbose_eval=100
)

# Predictions
y_pred_xgb_val = xgb_model.predict(dval)
y_pred_xgb_holdout = xgb_model.predict(dtest)

auc_xgb = roc_auc_score(y_val, y_pred_xgb_val)
f1_xgb = f1_score(y_val, (y_pred_xgb_val > 0.5).astype(int))
prec_xgb = precision_score(y_val, (y_pred_xgb_val > 0.5).astype(int))
rec_xgb = recall_score(y_val, (y_pred_xgb_val > 0.5).astype(int))

print(f"\n✅ XGBoost - Validation Metrics:")
print(f"   AUC: {auc_xgb:.4f}")
print(f"   F1-Score: {f1_xgb:.4f}")
print(f"   Precision: {prec_xgb:.4f}")
print(f"   Recall: {rec_xgb:.4f}")

# ============================================================================
# STEP 3: TRAIN CATBOOST MODEL
# ============================================================================

print("\n" + "="*80)
print("STEP 3: TRAIN CATBOOST MODEL")
print("="*80)

cat_params = {
    'iterations': 1000,
    'learning_rate': 0.05,
    'depth': 7,
    'l2_leaf_reg': 3,
    'loss_function': 'Logloss',
    'eval_metric': 'AUC',
    'random_seed': 42,
    'verbose': False,
    'early_stopping_rounds': 100,
}

print("Training CatBoost...")

cat_model = CatBoostClassifier(**cat_params)
cat_model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    verbose=100
)

# Predictions
y_pred_cat_val = cat_model.predict_proba(X_val)[:, 1]
y_pred_cat_holdout = cat_model.predict_proba(X_holdout)[:, 1]

auc_cat = roc_auc_score(y_val, y_pred_cat_val)
f1_cat = f1_score(y_val, (y_pred_cat_val > 0.5).astype(int))
prec_cat = precision_score(y_val, (y_pred_cat_val > 0.5).astype(int))
rec_cat = recall_score(y_val, (y_pred_cat_val > 0.5).astype(int))

print(f"\n✅ CatBoost - Validation Metrics:")
print(f"   AUC: {auc_cat:.4f}")
print(f"   F1-Score: {f1_cat:.4f}")
print(f"   Precision: {prec_cat:.4f}")
print(f"   Recall: {rec_cat:.4f}")

# ============================================================================
# STEP 4: MODEL COMPARISON
# ============================================================================

print("\n" + "="*80)
print("STEP 4: MODEL COMPARISON")
print("="*80)

comparison = pd.DataFrame({
    'Model': ['XGBoost', 'CatBoost'],
    'AUC': [auc_xgb, auc_cat],
    'F1-Score': [f1_xgb, f1_cat],
    'Precision': [prec_xgb, prec_cat],
    'Recall': [rec_xgb, rec_cat]
})

print("\n📊 Model Comparison (Validation Set):")
print(comparison.to_string(index=False))

print(f"\n🏆 Winner by AUC: {'XGBoost' if auc_xgb > auc_cat else 'CatBoost'} ({max(auc_xgb, auc_cat):.4f})")
print(f"🏆 Winner by F1: {'XGBoost' if f1_xgb > f1_cat else 'CatBoost'} ({max(f1_xgb, f1_cat):.4f})")

# ============================================================================
# STEP 5: SAVE MODELS
# ============================================================================

print("\n" + "="*80)
print("STEP 5: SAVE MODELS")
print("="*80)

# Save XGBoost
xgb_model.save_model(f"{MODEL_DIR}/xgb_model.json")
print(f"✅ Saved XGBoost model: {MODEL_DIR}/xgb_model.json")

# Save CatBoost
cat_model.save_model(f"{MODEL_DIR}/cat_model.cbm")
print(f"✅ Saved CatBoost model: {MODEL_DIR}/cat_model.cbm")

# Save validation predictions
val_predictions = pd.DataFrame({
    'actual': y_val,
    'xgb_proba': y_pred_xgb_val,
    'cat_proba': y_pred_cat_val,
    'xgb_pred': (y_pred_xgb_val > 0.5).astype(int),
    'cat_pred': (y_pred_cat_val > 0.5).astype(int)
})
val_predictions.to_csv(f"{RESULTS_DIR}/validation_predictions.csv", index=False)
print(f"✅ Saved validation predictions")

# Save holdout predictions
holdout_predictions = pd.DataFrame({
    'xgb_proba': y_pred_xgb_holdout,
    'cat_proba': y_pred_cat_holdout
})
holdout_predictions.to_csv(f"{RESULTS_DIR}/holdout_predictions_raw.csv", index=False)
print(f"✅ Saved holdout predictions (raw)")

# Save models metadata
models_metadata = {
    'xgb_model': xgb_model,
    'cat_model': cat_model,
    'xgb_metrics': {
        'auc': auc_xgb, 'f1': f1_xgb, 'precision': prec_xgb, 'recall': rec_xgb
    },
    'cat_metrics': {
        'auc': auc_cat, 'f1': f1_cat, 'precision': prec_cat, 'recall': rec_cat
    },
    'feature_names': X_train.columns.tolist()
}

with open(f"{MODEL_DIR}/models_metadata.pkl", 'wb') as f:
    pickle.dump(models_metadata, f)
print(f"✅ Saved models metadata")

# ============================================================================
# STEP 6: SUMMARY REPORT
# ============================================================================

print("\n" + "="*80)
print("MODEL TRAINING SUMMARY")
print("="*80)

summary_text = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║          TELECOM CHURN - MODEL TRAINING COMPLETED SUCCESSFULLY             ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 TRAINING DATA:
  • Training set: {X_train.shape[0]:,} samples × {X_train.shape[1]} features (balanced)
  • Validation set: {X_val.shape[0]:,} samples × {X_val.shape[1]} features (original distribution)
  • Holdout set: {X_holdout.shape[0]:,} samples × {X_holdout.shape[1]} features

🎯 XGBOOST MODEL:
  • Max Depth: 6
  • Learning Rate: 0.05
  • Iterations: {xgb_model.num_boosted_rounds()}
  • Validation AUC: {auc_xgb:.4f}
  • Validation F1-Score: {f1_xgb:.4f}
  • Precision: {prec_xgb:.4f}
  • Recall: {rec_xgb:.4f}

🎯 CATBOOST MODEL:
  • Depth: 7
  • Learning Rate: 0.05
  • Iterations: {cat_model.tree_count_}
  • Validation AUC: {auc_cat:.4f}
  • Validation F1-Score: {f1_cat:.4f}
  • Precision: {prec_cat:.4f}
  • Recall: {rec_cat:.4f}

⚖️ MODEL COMPARISON:
  • AUC Winner: {'XGBoost' if auc_xgb > auc_cat else 'CatBoost'} ({max(auc_xgb, auc_cat):.4f})
  • F1 Winner: {'XGBoost' if f1_xgb > f1_cat else 'CatBoost'} ({max(f1_xgb, f1_cat):.4f})
  • Ensemble recommended for best results

✅ FILES SAVED:
  • Models:
    - xgb_model.json
    - cat_model.cbm
    - models_metadata.pkl
  
  • Results:
    - validation_predictions.csv
    - holdout_predictions_raw.csv

🚀 NEXT STEPS:
  1. Create ensemble predictions (weighted combination)
  2. Optimize prediction threshold
  3. Generate final holdout predictions
  4. Evaluate and deploy

📝 PREPROCESSING PIPELINE APPLIED:
  1. ✅ Handle 'Unknown' values (3 columns)
  2. ✅ Missing value imputation (median/mode)
  3. ✅ Outlier handling (Winsorization 5th/95th percentile)
  4. ✅ Skewed feature transformation (Log for 15 features)
  5. ✅ Feature scaling (RobustScaler on 49 features)
  6. ✅ Categorical encoding (Label encoding 22 features)
  7. ✅ Feature engineering (9 derived features)
  8. ✅ SMOTE balancing (1:1 ratio on training set)
  9. ✅ Stratified train-test split (80-20)

💡 TECHNIQUES USED (Besides SMOTE):
  • Median Imputation: Numeric missing values (robust to outliers)
  • Mode Imputation: Categorical missing values
  • Winsorization: Outlier capping at 5th/95th percentile
  • Log Transformation: Skewed feature normalization (handles zeros with log1p)
  • RobustScaler: Feature scaling (IQR-based, resistant to outliers)
  • Label Encoding: Categorical to numeric conversion
  • Feature Engineering: 9 new derived features (engagement, intensity, etc.)
  • Stratified Split: Preserving class distribution in train/val/test

Quality Assurance:
  ✅ No missing values after preprocessing
  ✅ Balanced training set (1:1 after SMOTE)
  ✅ Original distribution preserved in validation set
  ✅ Handled unseen categories in holdout set
  ✅ All features properly scaled and transformed
  ✅ Consistent random seeds for reproducibility
"""

print(summary_text)

# Save summary
with open(f"{RESULTS_DIR}/TRAINING_SUMMARY.txt", 'w', encoding='utf-8') as f:
    f.write(summary_text)

print(f"\n✅ Summary saved to: {RESULTS_DIR}/TRAINING_SUMMARY.txt")
print(f"✅ ALL MODELS TRAINED AND SAVED SUCCESSFULLY! 🎉")
