"""
PHASE 2: HYPERPARAMETER OPTIMIZATION
=====================================
1. XGBoost hyperparameter tuning
2. CatBoost hyperparameter tuning
3. Ensemble combination of optimized models

Expected improvement: +2-4% F1-Score
Note: This will take 30-60 minutes to complete
"""

import pandas as pd
import numpy as np
from pathlib import Path
import joblib
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import RandomizedSearchCV
from xgboost import XGBClassifier
from sklearn.preprocessing import RobustScaler
from sklearn.pipeline import Pipeline
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("PHASE 2: HYPERPARAMETER OPTIMIZATION")
print("=" * 80)

# ============================================================================
# 1. LOAD PREPROCESSED DATA
# ============================================================================

print("\n[STEP 1] Loading preprocessed data...")

data_path = Path('./preprocessed_data')

X_train = pd.read_csv(data_path / 'X_train_balanced.csv')
y_train = pd.read_csv(data_path / 'y_train_balanced.csv').values.ravel()
X_val = pd.read_csv(data_path / 'X_val.csv')
y_val = pd.read_csv(data_path / 'y_val.csv').values.ravel()

print(f"[OK] Training: {X_train.shape} | Validation: {X_val.shape}")
print(f"[OK] Churn distribution - Train: {y_train.mean():.1%}, Val: {y_val.mean():.1%}")

# ============================================================================
# 2. XGBOOST HYPERPARAMETER TUNING
# ============================================================================

print("\n" + "=" * 80)
print("[STEP 2] XGBOOST HYPERPARAMETER TUNING")
print("=" * 80)
print("\nThis will test 100 random combinations using 5-fold CV...")
print("Estimated time: 30-40 minutes")

# Create XGBoost pipeline
xgb_pipeline = Pipeline([
    ('scaler', RobustScaler()),
    ('model', XGBClassifier(
        objective='binary:logistic',
        random_state=42,
        n_jobs=-1,
        eval_metric='logloss'
    ))
])

# Hyperparameter grid
xgb_param_grid = {
    'model__learning_rate': [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08],
    'model__max_depth': [4, 5, 6, 7, 8, 9],
    'model__subsample': [0.6, 0.7, 0.75, 0.8, 0.85, 0.9],
    'model__colsample_bytree': [0.6, 0.7, 0.75, 0.8, 0.85, 0.9],
    'model__lambda': [0.1, 0.5, 1.0, 3.0, 5.0, 10.0],
    'model__alpha': [0.0, 0.1, 0.5, 1.0],
    'model__min_child_weight': [1, 2, 3, 5],
}

# Randomized search
xgb_search = RandomizedSearchCV(
    xgb_pipeline,
    xgb_param_grid,
    n_iter=100,
    cv=5,
    scoring='f1',
    n_jobs=-1,
    random_state=42,
    verbose=1
)

print("\nStarting XGBoost RandomizedSearchCV...")
xgb_search.fit(X_train, y_train)

xgb_best = xgb_search.best_estimator_
xgb_best_f1 = xgb_search.best_score_
xgb_best_params = xgb_search.best_params_

print(f"\n[OK] XGBoost optimization complete!")
print(f"Best F1-Score (CV): {xgb_best_f1:.4f}")
print(f"Best Parameters: {xgb_best_params}")

# Validate on validation set
xgb_val_pred = xgb_best.predict_proba(X_val)[:, 1]
xgb_val_f1 = f1_score(y_val, (xgb_val_pred >= 0.25).astype(int))
xgb_val_auc = roc_auc_score(y_val, xgb_val_pred)

print(f"\nValidation Performance:")
print(f"  F1-Score (threshold 0.25): {xgb_val_f1:.4f}")
print(f"  AUC-ROC: {xgb_val_auc:.4f}")

# ============================================================================
# 3. CATBOOST HYPERPARAMETER TUNING  
# ============================================================================

print("\n" + "=" * 80)
print("[STEP 3] CATBOOST HYPERPARAMETER TUNING")
print("=" * 80)

try:
    from catboost import CatBoostClassifier
    
    print("\nThis will test 100 random combinations using 5-fold CV...")
    print("Estimated time: 30-40 minutes")
    
    # Create CatBoost pipeline
    cat_pipeline = Pipeline([
        ('scaler', RobustScaler()),
        ('model', CatBoostClassifier(
            objective='Logloss',
            random_state=42,
            verbose=0,
            thread_count=-1
        ))
    ])
    
    # Hyperparameter grid
    cat_param_grid = {
        'model__learning_rate': [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08],
        'model__depth': [4, 5, 6, 7, 8, 9],
        'model__l2_leaf_reg': [0.1, 0.5, 1, 2, 3, 5, 10],
        'model__subsample': [0.6, 0.7, 0.75, 0.8, 0.85, 0.9],
        'model__bagging_temperature': [0, 0.1, 0.5, 1.0],
        'model__leaf_estimation_iterations': [1, 2, 3, 5],
        'model__random_strength': [0.0, 1.0, 2.0],
    }
    
    # Randomized search
    cat_search = RandomizedSearchCV(
        cat_pipeline,
        cat_param_grid,
        n_iter=100,
        cv=5,
        scoring='f1',
        n_jobs=-1,
        random_state=42,
        verbose=1
    )
    
    print("\nStarting CatBoost RandomizedSearchCV...")
    cat_search.fit(X_train, y_train)
    
    cat_best = cat_search.best_estimator_
    cat_best_f1 = cat_search.best_score_
    cat_best_params = cat_search.best_params_
    
    print(f"\n[OK] CatBoost optimization complete!")
    print(f"Best F1-Score (CV): {cat_best_f1:.4f}")
    print(f"Best Parameters: {cat_best_params}")
    
    # Validate on validation set
    cat_val_pred = cat_best.predict_proba(X_val)[:, 1]
    cat_val_f1 = f1_score(y_val, (cat_val_pred >= 0.25).astype(int))
    cat_val_auc = roc_auc_score(y_val, cat_val_pred)
    
    print(f"\nValidation Performance:")
    print(f"  F1-Score (threshold 0.25): {cat_val_f1:.4f}")
    print(f"  AUC-ROC: {cat_val_auc:.4f}")
    
    catboost_available = True
    
except ImportError:
    print("[WARNING] CatBoost not available for full tuning")
    print("Skipping CatBoost hyperparameter search")
    catboost_available = False

# ============================================================================
# 4. ENSEMBLE OPTIMIZATION
# ============================================================================

print("\n" + "=" * 80)
print("[STEP 4] ENSEMBLE OPTIMIZATION")
print("=" * 80)

if catboost_available:
    # Test different weight combinations with optimized models
    weights_to_test = [
        (0.50, 0.50),
        (0.55, 0.45),
        (0.60, 0.40),
        (0.65, 0.35),
        (0.70, 0.30),
        (0.75, 0.25),
    ]
    
    best_ensemble_f1 = 0
    best_ensemble_weights = (0.6, 0.4)
    
    print("\nTesting ensemble weight combinations with optimized models:")
    print(f"{'XGB%':>8} {'CAT%':>8} {'F1':>8} {'AUC':>8} {'Precision':>10} {'Recall':>8}")
    print("-" * 60)
    
    for xgb_w, cat_w in weights_to_test:
        ensemble_proba = xgb_w * xgb_val_pred + cat_w * cat_val_pred
        ensemble_pred = (ensemble_proba >= 0.25).astype(int)
        
        f1 = f1_score(y_val, ensemble_pred, zero_division=0)
        auc = roc_auc_score(y_val, ensemble_proba)
        prec = precision_score(y_val, ensemble_pred, zero_division=0)
        rec = recall_score(y_val, ensemble_pred, zero_division=0)
        
        if f1 > best_ensemble_f1:
            best_ensemble_f1 = f1
            best_ensemble_weights = (xgb_w, cat_w)
        
        print(f"{xgb_w*100:>7.0f}% {cat_w*100:>7.0f}% {f1:>8.4f} {auc:>8.4f} {prec:>10.4f} {rec:>8.4f}")
    
    print(f"\nBEST ENSEMBLE: {best_ensemble_weights[0]:.0%} XGB + {best_ensemble_weights[1]:.0%} CAT")
    print(f"F1-Score: {best_ensemble_f1:.4f}")
else:
    print("[INFO] Using XGBoost only since CatBoost not optimized")
    best_ensemble_f1 = xgb_val_f1
    best_ensemble_weights = (1.0, 0.0)

# ============================================================================
# 5. SAVE OPTIMIZED MODELS
# ============================================================================

print("\n" + "=" * 80)
print("[STEP 5] SAVING OPTIMIZED MODELS")
print("=" * 80)

model_path = Path('./artifacts')

# Save XGBoost
xgb_save_path = model_path / 'xgb_pipeline_optimized.joblib'
joblib.dump(xgb_best, xgb_save_path)
print(f"[OK] Saved optimized XGBoost: {xgb_save_path}")

# Save CatBoost if available
if catboost_available:
    cat_save_path = model_path / 'cat_pipeline_optimized.joblib'
    joblib.dump(cat_best, cat_save_path)
    print(f"[OK] Saved optimized CatBoost: {cat_save_path}")

# ============================================================================
# 6. SUMMARY & RESULTS
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 2 OPTIMIZATION SUMMARY")
print("=" * 80)

summary_path = Path('./model_results/PHASE2_TUNING_RESULTS.txt')
with open(summary_path, 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("PHASE 2: HYPERPARAMETER OPTIMIZATION RESULTS\n")
    f.write("=" * 80 + "\n\n")
    
    f.write("XGBOOST OPTIMIZATION\n")
    f.write("-" * 80 + "\n")
    f.write(f"Original F1-Score: 0.2574 (with default params)\n")
    f.write(f"Optimized F1-Score (CV): {xgb_best_f1:.4f}\n")
    f.write(f"Optimized F1-Score (Validation): {xgb_val_f1:.4f}\n")
    f.write(f"Improvement: {(xgb_val_f1 - 0.2574)*100:+.2f}%\n\n")
    f.write(f"Best Parameters:\n")
    for param, value in xgb_best_params.items():
        f.write(f"  {param}: {value}\n")
    f.write("\n")
    
    if catboost_available:
        f.write("CATBOOST OPTIMIZATION\n")
        f.write("-" * 80 + "\n")
        f.write(f"Original F1-Score: 0.2157 (with default params)\n")
        f.write(f"Optimized F1-Score (CV): {cat_best_f1:.4f}\n")
        f.write(f"Optimized F1-Score (Validation): {cat_val_f1:.4f}\n")
        f.write(f"Improvement: {(cat_val_f1 - 0.2157)*100:+.2f}%\n\n")
        f.write(f"Best Parameters:\n")
        for param, value in cat_best_params.items():
            f.write(f"  {param}: {value}\n")
        f.write("\n")
        
        f.write("ENSEMBLE OPTIMIZATION\n")
        f.write("-" * 80 + "\n")
        f.write(f"Current Ensemble (60/40): F1 = 0.4957\n")
        f.write(f"Optimized Ensemble {best_ensemble_weights[0]:.0%}/{best_ensemble_weights[1]:.0%}: F1 = {best_ensemble_f1:.4f}\n")
        f.write(f"Improvement: {(best_ensemble_f1 - 0.4957)*100:+.2f}%\n")
    
    f.write("\nRECOMMENDATIONS\n")
    f.write("-" * 80 + "\n")
    f.write(f"1. Deploy optimized XGBoost model\n")
    if catboost_available:
        f.write(f"2. Deploy optimized CatBoost model\n")
        f.write(f"3. Ensemble with weights: {best_ensemble_weights[0]:.0%} XGB + {best_ensemble_weights[1]:.0%} CAT\n")
        f.write(f"4. Use threshold: 0.25\n")
    else:
        f.write(f"2. Use XGBoost as primary model\n")
        f.write(f"3. Use threshold: 0.25\n")

print(f"[OK] Results saved: {summary_path}")

print(f"""
OPTIMIZATION COMPLETE!

Phase 1 Results:  +0.06% improvement
Phase 2 Results:  +{(best_ensemble_f1 - 0.4957)*100:+.2f}% improvement

Total Expected Improvement: {(best_ensemble_f1 - 0.4957)*100:+.2f}%
Current F1:  0.4957
Target F1:   {best_ensemble_f1:.4f}

Next: Proceed to production deployment with optimized models
""")

print("=" * 80)
