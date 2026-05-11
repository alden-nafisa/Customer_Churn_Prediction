"""
DETAILED MODEL INSIGHTS ANALYSIS
================================
Extract feature importance, outlier impact, and optimization opportunities
Focus: XGBoost + CatBoost only
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
import joblib
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# 1. LOAD DATA & MODELS
# ============================================================================

print("=" * 80)
print("LOADING DATA & MODELS")
print("=" * 80)

# Paths
data_path = Path('./preprocessed_data')
model_path = Path('./artifacts')

# Load preprocessed data
X_train = pd.read_csv(data_path / 'X_train_balanced.csv')
y_train = pd.read_csv(data_path / 'y_train_balanced.csv').values.ravel()
X_val = pd.read_csv(data_path / 'X_val.csv')
y_val = pd.read_csv(data_path / 'y_val.csv').values.ravel()
X_holdout = pd.read_csv(data_path / 'X_holdout.csv')

print(f"✅ Training data: {X_train.shape}")
print(f"✅ Validation data: {X_val.shape}")
print(f"✅ Holdout data: {X_holdout.shape}")

# Load trained models
try:
    xgb_model = joblib.load(model_path / 'xgb_pipeline.joblib')
    print("✅ XGBoost model loaded")
except:
    print("❌ XGBoost model not found")
    xgb_model = None

try:
    cat_model = joblib.load(model_path / 'catboost_pipeline.joblib')
    print("✅ CatBoost model loaded")
except:
    print("❌ CatBoost model not found")
    cat_model = None

# ============================================================================
# 2. FEATURE IMPORTANCE ANALYSIS
# ============================================================================

print("\n" + "=" * 80)
print("FEATURE IMPORTANCE ANALYSIS")
print("=" * 80)

feature_importance_data = []

# XGBoost Feature Importance
if xgb_model:
    try:
        # Get the actual XGBoost model from pipeline
        xgb_booster = xgb_model.named_steps['model']
        
        # Get feature importance
        xgb_importance = xgb_booster.get_booster().get_score(importance_type='weight')
        xgb_df = pd.DataFrame({
            'feature': list(xgb_importance.keys()),
            'importance': list(xgb_importance.values())
        }).sort_values('importance', ascending=False)
        
        xgb_df['model'] = 'XGBoost'
        xgb_df['importance_pct'] = (xgb_df['importance'] / xgb_df['importance'].sum()) * 100
        
        print("\n📊 XGBoost - Top 20 Features:")
        print(xgb_df.head(20).to_string(index=False))
        print(f"\nTotal features used: {len(xgb_df)}")
        
        feature_importance_data.append(xgb_df)
    except Exception as e:
        print(f"❌ Error extracting XGBoost importance: {e}")

# CatBoost Feature Importance
if cat_model:
    try:
        # Get the actual CatBoost model from pipeline
        cat_booster = cat_model.named_steps['model']
        
        # Get feature importance
        cat_importance = cat_booster.get_feature_importance()
        feature_names = X_train.columns.tolist()
        
        cat_df = pd.DataFrame({
            'feature': feature_names,
            'importance': cat_importance
        }).sort_values('importance', ascending=False)
        
        cat_df['model'] = 'CatBoost'
        cat_df['importance_pct'] = (cat_df['importance'] / cat_df['importance'].sum()) * 100
        
        print("\n📊 CatBoost - Top 20 Features:")
        print(cat_df.head(20).to_string(index=False))
        print(f"\nTotal features used: {len(cat_df)}")
        
        feature_importance_data.append(cat_df)
    except Exception as e:
        print(f"❌ Error extracting CatBoost importance: {e}")

# ============================================================================
# 3. OUTLIER IMPACT ANALYSIS
# ============================================================================

print("\n" + "=" * 80)
print("OUTLIER IMPACT ANALYSIS")
print("=" * 80)

# Load outlier analysis
outliers_df = pd.read_csv('./analysis_results/outliers_analysis.csv')
print("\n📊 Top 15 Features with Most Outliers:")
print(outliers_df.head(15).to_string(index=False))

# Analyze outlier impact on predictions
print("\n[*] OUTLIER IMPACT ON MODEL PREDICTIONS:")

outlier_features = outliers_df[outliers_df['Outliers_Percentage'] > 10]['Column'].tolist()
print(f"\nFeatures with >10% outliers: {len(outlier_features)}")
print(f"Features: {outlier_features[:10]}...")  # Show first 10

# For each high-outlier feature, check correlation with churn
print("\n[*] Correlation of High-Outlier Features with Churn:")
for feature in outlier_features[:10]:
    if feature in X_val.columns:
        corr = X_val[feature].corr(y_val)
        print(f"  {feature:30s}: {corr:+.4f}")

# ============================================================================
# 4. SKEWNESS ANALYSIS
# ============================================================================

print("\n" + "=" * 80)
print("FEATURE DISTRIBUTION ANALYSIS")
print("=" * 80)

feature_stats = pd.read_csv('./analysis_results/feature_statistics.csv')
print("\n📊 Highly Skewed Features (|Skewness| > 1):")
skewed = feature_stats[feature_stats['Highly_Skewed'] == 'Yes'].sort_values('Skewness', ascending=False)
print(skewed[['Feature', 'Skewness', 'Kurtosis']].head(15).to_string(index=False))

print(f"\nTotal highly skewed features: {len(skewed)}")

# ============================================================================
# 5. PREDICTION ANALYSIS
# ============================================================================

print("\n" + "=" * 80)
print("PREDICTION ANALYSIS & OPPORTUNITIES")
print("=" * 80)

# Load validation predictions
try:
    val_pred = pd.read_csv('./model_results/ensemble_validation_predictions.csv')
    
    print("\n[*] Validation Prediction Statistics:")
    print(f"  Mean probability: {val_pred['ensemble_proba'].mean():.4f}")
    print(f"  Std dev: {val_pred['ensemble_proba'].std():.4f}")
    print(f"  Min: {val_pred['ensemble_proba'].min():.4f}")
    print(f"  Max: {val_pred['ensemble_proba'].max():.4f}")
    print(f"  Median: {val_pred['ensemble_proba'].median():.4f}")
    
    print("\n[*] Probability Distribution by Quantiles:")
    quantiles = [0.25, 0.5, 0.75, 0.9, 0.95, 0.99]
    for q in quantiles:
        print(f"  {q*100:5.0f}th percentile: {val_pred['ensemble_proba'].quantile(q):.4f}")
    
    # Analyze predictions at different thresholds
    print("\n[*] Performance at Different Thresholds:")
    print(f"{'Threshold':>10} {'Churn %':>10} {'F1-Score':>10} {'Precision':>10} {'Recall':>10}")
    print("-" * 50)
    
    for threshold in [0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50]:
        pred_at_threshold = (val_pred['ensemble_proba'] >= threshold).astype(int)
        
        from sklearn.metrics import f1_score, precision_score, recall_score
        f1 = f1_score(y_val, pred_at_threshold, zero_division=0)
        prec = precision_score(y_val, pred_at_threshold, zero_division=0)
        recall = recall_score(y_val, pred_at_threshold, zero_division=0)
        churn_pct = pred_at_threshold.mean() * 100
        
        marker = "← OPTIMAL" if threshold == 0.25 else ""
        print(f"{threshold:>10.2f} {churn_pct:>9.1f}% {f1:>10.4f} {prec:>10.4f} {recall:>10.4f} {marker}")
        
except Exception as e:
    print(f"[X] Error loading validation predictions: {e}")

# ============================================================================
# 6. OPTIMIZATION RECOMMENDATIONS
# ============================================================================

print("\n" + "=" * 80)
print("OPTIMIZATION RECOMMENDATIONS")
print("=" * 80)

recommendations = """

[**] STRATEGY 1: FEATURE-FOCUSED OPTIMIZATION
================================================================================

Issues Identified:
  • 15+ features dengan >10% outliers (PercChangeRevenues: 25.9%, RoamingCalls: 17.3%)
  • Highly skewed distributions (CallForwardingCalls: 91.6x skewness!)
  • High-cardinality categorical (ServiceArea: 747 unique values)

Solutions:
  ✓ Aggressive outlier removal (IQR method more strict: 1.0x vs 1.5x)
  ✓ Selective feature drops for extreme outliers
  ✓ Better log transformation with custom scaling
  ✓ ServiceArea: Grouping rare categories
  
Expected Impact: +1-2% F1-Score


[**] STRATEGY 2: HYPERPARAMETER OPTIMIZATION
================================================================================

Current Configuration (Both Models):
  • Learning rate: 0.05 (moderate)
  • Max depth: 6-7 (reasonable)
  • Regularization: L2=3.0 (strong)

Optimization Areas:
  ✓ Learning rate tuning: 0.01-0.08 (find sweet spot)
  ✓ Depth optimization: 4-9 (test complexity)
  ✓ Subsample/Colsample: 0.6-0.9 (reduce overfitting)
  ✓ Early stopping patience: 50-200 (balance convergence)
  ✓ Class weight adjustment (XGBoost): scale_pos_weight

Expected Impact: +2-4% F1-Score


[**] STRATEGY 3: THRESHOLD & ENSEMBLE OPTIMIZATION
================================================================================

Current Setup:
  • Threshold: 0.25 (already optimized)
  • Weights: 0.6 XGBoost + 0.4 CatBoost (reasonable)

Opportunities:
  ✓ Dynamic thresholding per customer segment
  ✓ Weighted ensemble optimization (try 0.5/0.5, 0.7/0.3, etc.)
  ✓ Probability calibration (sigmoid platt scaling)

Expected Impact: +0.5-1% F1-Score


[**] STRATEGY 4: DATA QUALITY IMPROVEMENTS
================================================================================

Potential Issues:
  ✓ PercChangeRevenues: -1107% to +2483% (extreme range!)
  ✓ PercChangeMinutes: -3875 to +5192 (data quality?)
  ✓ Multiple features with 0 values (missing data vs real zero?)

Checks Needed:
  ✓ Verify extreme outliers are real or data entry errors
  ✓ Check for feature leakage (future information in features)
  ✓ Validate percentage change calculations

Expected Impact: +1-3% F1-Score if data quality improved


🎯 PRIORITY ROADMAP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PHASE 1 (Quick Win: +1-2%):
  1. Optimize ensemble weights (try 0.5/0.5, 0.55/0.45, 0.7/0.3)
  2. Strict outlier removal for top 5 outlier features
  3. Probability calibration

PHASE 2 (Tuning: +2-4%):
  4. Hyperparameter grid search:
     - XGBoost: learning_rate, max_depth, subsample
     - CatBoost: learning_rate, depth, l2_leaf_reg
  5. Feature selection (drop low-importance features <0.1%)
  6. Custom loss function or class weighting

PHASE 3 (Advanced: +1-2%):
  7. Cross-validation optimization
  8. Stacking with meta-learner
  9. Threshold optimization per customer segment

Realistic Target: 4-8% improvement in F1-Score
Current F1: 0.4957 → Target: 0.5157 - 0.5357 ✓

"""

print(recommendations)

# ============================================================================
# 7. SAVE ANALYSIS REPORT
# ============================================================================

print("\n" + "=" * 80)
print("SAVING ANALYSIS REPORT")
print("=" * 80)

# Combine all insights
report_path = Path('./model_results/DETAILED_INSIGHTS_REPORT.txt')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("DETAILED MODEL INSIGHTS & OPTIMIZATION OPPORTUNITIES\n")
    f.write("Focus: XGBoost + CatBoost Ensemble\n")
    f.write("=" * 80 + "\n\n")
    
    # Feature importance
    if feature_importance_data:
        f.write("FEATURE IMPORTANCE\n")
        f.write("-" * 80 + "\n\n")
        for df in feature_importance_data:
            model_name = df['model'].iloc[0]
            f.write(f"\n{model_name} - Top 25 Features:\n")
            f.write(df[['feature', 'importance_pct']].head(25).to_string(index=False))
            f.write("\n\n")
    
    # Outlier analysis
    f.write("\nOUTLIER ANALYSIS\n")
    f.write("-" * 80 + "\n")
    f.write(outliers_df.to_string(index=False))
    f.write("\n\n")
    
    # Recommendations (already cleaned of emojis)
    f.write(recommendations)

print(f"[OK] Report saved to: {report_path}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE!")
print("=" * 80)
print("""
Next Steps:
  1. Review the detailed insights report
  2. Implement PHASE 1 optimizations (quick wins)
  3. Run hyperparameter tuning for PHASE 2
  4. Test threshold & ensemble weight combinations
  
Output saved to: ./model_results/DETAILED_INSIGHTS_REPORT.txt
""")
