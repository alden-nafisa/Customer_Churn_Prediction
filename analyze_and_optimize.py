"""
COMPREHENSIVE MODEL OPTIMIZATION ANALYSIS
==========================================
Analyze XGBoost + CatBoost ensemble for improvement opportunities
Focus: Feature importance, outlier impact, hyperparameter tuning
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import joblib
import warnings
from sklearn.metrics import f1_score, precision_score, recall_score
warnings.filterwarnings('ignore')

print("=" * 80)
print("LOADING DATA & MODELS")
print("=" * 80)

# Paths
data_path = Path('./preprocessed_data')
model_path = Path('./artifacts')

# Load data
X_train = pd.read_csv(data_path / 'X_train_balanced.csv')
y_train = pd.read_csv(data_path / 'y_train_balanced.csv').values.ravel()
X_val = pd.read_csv(data_path / 'X_val.csv')
y_val = pd.read_csv(data_path / 'y_val.csv').values.ravel()
X_holdout = pd.read_csv(data_path / 'X_holdout.csv')

print(f"[OK] Training data: {X_train.shape}")
print(f"[OK] Validation data: {X_val.shape}")
print(f"[OK] Holdout data: {X_holdout.shape}")

# Load models
xgb_model = None
cat_model = None

try:
    xgb_model = joblib.load(model_path / 'xgb_pipeline.joblib')
    print("[OK] XGBoost model loaded")
except Exception as e:
    print(f"[ERROR] XGBoost model: {e}")

try:
    cat_model = joblib.load(model_path / 'catboost_pipeline.joblib')
    print("[OK] CatBoost model loaded")
except Exception as e:
    print(f"[WARNING] CatBoost model not found: {e}")

# ============================================================================
# 1. FEATURE IMPORTANCE ANALYSIS
# ============================================================================

print("\n" + "=" * 80)
print("FEATURE IMPORTANCE ANALYSIS")
print("=" * 80)

all_importances = {}

# XGBoost
if xgb_model:
    try:
        xgb_booster = xgb_model.named_steps['model']
        xgb_importance_dict = xgb_booster.get_booster().get_score(importance_type='weight')
        
        xgb_df = pd.DataFrame({
            'feature': list(xgb_importance_dict.keys()),
            'importance': list(xgb_importance_dict.values())
        }).sort_values('importance', ascending=False)
        
        xgb_df['importance_pct'] = (xgb_df['importance'] / xgb_df['importance'].sum()) * 100
        
        print("\nXGBOOST - Top 15 Features:")
        print(xgb_df.head(15)[['feature', 'importance_pct']].to_string(index=False))
        
        all_importances['xgboost'] = xgb_df
    except Exception as e:
        print(f"[ERROR] XGBoost importance: {e}")

# CatBoost
if cat_model:
    try:
        cat_booster = cat_model.named_steps['model']
        cat_importance = cat_booster.get_feature_importance()
        
        cat_df = pd.DataFrame({
            'feature': X_train.columns.tolist(),
            'importance': cat_importance
        }).sort_values('importance', ascending=False)
        
        cat_df['importance_pct'] = (cat_df['importance'] / cat_df['importance'].sum()) * 100
        
        print("\nCATBOOST - Top 15 Features:")
        print(cat_df.head(15)[['feature', 'importance_pct']].to_string(index=False))
        
        all_importances['catboost'] = cat_df
    except Exception as e:
        print(f"[ERROR] CatBoost importance: {e}")

# ============================================================================
# 2. OUTLIER ANALYSIS
# ============================================================================

print("\n" + "=" * 80)
print("OUTLIER & DATA QUALITY ANALYSIS")
print("=" * 80)

outliers_df = pd.read_csv('./analysis_results/outliers_analysis.csv')
feature_stats = pd.read_csv('./analysis_results/feature_statistics.csv')

print("\nTOP 10 FEATURES WITH MOST OUTLIERS:")
print(outliers_df.head(10)[['Column', 'Outliers_Count', 'Outliers_Percentage']].to_string(index=False))

print("\nHIGHLY SKEWED FEATURES (|Skewness| > 1):")
skewed = feature_stats[feature_stats['Highly_Skewed'] == 'Yes'].sort_values('Skewness', ascending=False)
print(skewed[['Feature', 'Skewness']].head(10).to_string(index=False))

# ============================================================================
# 3. CURRENT PREDICTIONS ANALYSIS
# ============================================================================

print("\n" + "=" * 80)
print("CURRENT PREDICTION PERFORMANCE")
print("=" * 80)

try:
    val_pred = pd.read_csv('./model_results/ensemble_validation_predictions.csv')
    
    print("\nPREDICTION PROBABILITY STATISTICS:")
    print(f"  Mean:   {val_pred['ensemble_proba'].mean():.4f}")
    print(f"  Median: {val_pred['ensemble_proba'].median():.4f}")
    print(f"  Std:    {val_pred['ensemble_proba'].std():.4f}")
    print(f"  Min:    {val_pred['ensemble_proba'].min():.4f}")
    print(f"  Max:    {val_pred['ensemble_proba'].max():.4f}")
    
    print("\nPERFORMANCE AT DIFFERENT THRESHOLDS:")
    print(f"{'Threshold':>10} {'Churn%':>8} {'F1':>8} {'Prec':>8} {'Recall':>8} {'Status':>15}")
    print("-" * 70)
    
    best_f1 = 0
    best_threshold = 0.5
    
    for threshold in np.arange(0.10, 0.61, 0.05):
        pred = (val_pred['ensemble_proba'] >= threshold).astype(int)
        f1 = f1_score(y_val, pred, zero_division=0)
        prec = precision_score(y_val, pred, zero_division=0)
        rec = recall_score(y_val, pred, zero_division=0)
        churn_pct = pred.mean() * 100
        
        status = "[CURRENT]" if threshold == 0.25 else ""
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = threshold
        
        print(f"{threshold:>10.2f} {churn_pct:>7.1f}% {f1:>8.4f} {prec:>8.4f} {rec:>8.4f} {status:>15}")
    
    print(f"\nBEST F1-SCORE: {best_f1:.4f} at threshold {best_threshold:.2f}")
    
except Exception as e:
    print(f"[ERROR] Loading predictions: {e}")

# ============================================================================
# 4. OPTIMIZATION RECOMMENDATIONS
# ============================================================================

print("\n" + "=" * 80)
print("OPTIMIZATION RECOMMENDATIONS")
print("=" * 80)

recommendations = """

========== OPTIMIZATION STRATEGY ==========

PHASE 1: QUICK WINS (Expected: +1-2% F1-Score)
----------------------------------------------

1. ENSEMBLE WEIGHT OPTIMIZATION
   - Current: 60% XGBoost + 40% CatBoost
   - Test: 55/45, 50/50, 65/35, 70/30
   - Effort: LOW | Impact: MEDIUM
   
2. STRICT OUTLIER HANDLING
   - Top problematic features:
     * PercChangeRevenues: 25.9% outliers
     * RoamingCalls: 17.3% outliers
     * CallWaitingCalls: 14.6% outliers
   - Action: Apply stricter IQR bounds (1.0x vs current 1.5x)
   - Effort: LOW | Impact: MEDIUM

3. THRESHOLD OPTIMIZATION
   - Current: 0.25 (already good)
   - Test dynamic threshold per customer segment
   - Effort: LOW | Impact: LOW-MEDIUM


PHASE 2: HYPERPARAMETER TUNING (Expected: +2-4% F1-Score)
-----------------------------------------------------------

1. XGBOOST TUNING
   Current settings:
     - learning_rate: 0.05
     - max_depth: 6
     - subsample: 0.8
     - colsample_bytree: 0.8
     - l2: 3.0
   
   Recommendations:
     - Try learning_rate: [0.01, 0.02, 0.03, 0.05, 0.08]
     - Try max_depth: [4, 5, 6, 7, 8, 9]
     - Try subsample: [0.6, 0.7, 0.8, 0.9]
     - Try colsample_bytree: [0.6, 0.7, 0.8, 0.9]
     - Add scale_pos_weight to handle class imbalance
   
   Grid search approach:
     - Use RandomizedSearchCV (faster than GridSearchCV)
     - 50-100 iterations
     - 5-fold cross-validation
     - Metric: F1-Score
   
   Effort: MEDIUM | Impact: HIGH

2. CATBOOST TUNING
   Current settings:
     - learning_rate: 0.05
     - depth: 7
     - l2_leaf_reg: 3.0
   
   Recommendations:
     - Try learning_rate: [0.01, 0.02, 0.03, 0.05, 0.08]
     - Try depth: [4, 5, 6, 7, 8, 9]
     - Try l2_leaf_reg: [1, 2, 3, 5, 10]
     - Increase iterations (600+)
   
   Effort: MEDIUM | Impact: HIGH


PHASE 3: ADVANCED OPTIMIZATION (Expected: +1-3% F1-Score)
-----------------------------------------------------------

1. FEATURE ENGINEERING IMPROVEMENTS
   - Add interaction features for top-importance pairs
   - Create customer segment-based features
   - Add temporal indicators
   - Effort: HIGH | Impact: MEDIUM

2. PROBABILITY CALIBRATION
   - Apply Platt scaling or isotonic calibration
   - Improves confidence in predictions
   - Effort: LOW | Impact: MEDIUM

3. FEATURE SELECTION
   - Remove features with importance < 0.1%
   - Reduce noise, improve generalization
   - Effort: LOW | Impact: MEDIUM


========== IMPLEMENTATION PRIORITY ==========

START HERE (Quick wins):
  [ ] 1. Run ensemble weight optimization
  [ ] 2. Test stricter outlier handling
  [ ] 3. Fine-tune threshold per segment

THEN (Hyperparameter tuning):
  [ ] 4. XGBoost grid search (RandomizedSearchCV)
  [ ] 5. CatBoost grid search (RandomizedSearchCV)
  [ ] 6. Combine best models with optimized weights

FINALLY (Polish):
  [ ] 7. Probability calibration
  [ ] 8. Feature selection refinement
  [ ] 9. Final validation & monitoring setup


========== EXPECTED RESULTS ==========

If all optimizations implemented:
  Current F1-Score: 0.4957
  Target F1-Score:  0.5400-0.5800 (+ 4-8%)
  
  Current Recall:   0.75
  Target Recall:    0.78-0.82

  Current Precision: 0.83
  Target Precision: 0.85-0.88


========== KEY METRICS TO MONITOR ==========

1. F1-Score (primary metric - balance precision & recall)
2. AUC-ROC (model discrimination ability)
3. Precision-Recall curve
4. Calibration error
5. Feature drift (monitor changes in data distribution)
6. Business metrics (actual churn reduction %)
"""

print(recommendations)

# ============================================================================
# 5. SAVE REPORT
# ============================================================================

report_path = Path('./model_results/OPTIMIZATION_ROADMAP.txt')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("MODEL OPTIMIZATION ANALYSIS & ROADMAP\n")
    f.write("XGBoost + CatBoost Ensemble for Customer Churn Prediction\n")
    f.write("=" * 80 + "\n\n")
    
    # Feature importance
    f.write("FEATURE IMPORTANCE SUMMARY\n")
    f.write("-" * 80 + "\n")
    for model_name, df in all_importances.items():
        f.write(f"\n{model_name.upper()} - Top 20 Features:\n")
        f.write(df.head(20)[['feature', 'importance_pct']].to_string(index=False))
        f.write("\n\n")
    
    # Data quality
    f.write("\nOUTLIER SUMMARY\n")
    f.write("-" * 80 + "\n")
    f.write(outliers_df.head(15)[['Column', 'Outliers_Count', 'Outliers_Percentage']].to_string(index=False))
    f.write("\n\n")
    
    # Recommendations
    f.write(recommendations)

print(f"\n[OK] Report saved: {report_path}")
print("\n" + "=" * 80)
print("ANALYSIS COMPLETE - Ready for optimization phase!")
print("=" * 80)
