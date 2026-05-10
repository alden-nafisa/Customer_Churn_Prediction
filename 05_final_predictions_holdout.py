"""
TELECOM CHURN - FINAL HOLDOUT PREDICTIONS
==========================================

Generate final predictions for deployment
"""

import pandas as pd
import numpy as np
import os

# ============================================================================
# CONFIGURATION
# ============================================================================

RESULTS_DIR = r"c:\Users\HP14\Downloads\pbl6\Customer_Churn_Prediction\model_results"

# ============================================================================
# STEP 1: LOAD HOLDOUT PREDICTIONS
# ============================================================================

print("="*80)
print("STEP 1: LOAD HOLDOUT PREDICTIONS")
print("="*80)

holdout_raw = pd.read_csv(f"{RESULTS_DIR}/ensemble_holdout_predictions.csv")

print(f"✅ Loaded {len(holdout_raw):,} holdout records")
print(f"✅ Columns: {list(holdout_raw.columns)}")

# ============================================================================
# STEP 2: GENERATE FINAL PREDICTIONS
# ============================================================================

print("\n" + "="*80)
print("STEP 2: GENERATE FINAL PREDICTIONS")
print("="*80)

# Using ensemble with optimal threshold (0.25)
ensemble_proba = holdout_raw['ensemble_proba'].values

final_predictions = pd.DataFrame({
    'record_id': np.arange(1, len(holdout_raw) + 1),
    'churn_probability': ensemble_proba,
    'churn_prediction_threshold_0.25': (ensemble_proba > 0.25).astype(int),
    'churn_prediction_threshold_0.30': (ensemble_proba > 0.30).astype(int),
    'churn_prediction_threshold_0.35': (ensemble_proba > 0.35).astype(int),
    'churn_prediction_threshold_0.50': (ensemble_proba > 0.50).astype(int),
    'xgb_probability': holdout_raw['xgb_proba'].values,
    'cat_probability': holdout_raw['cat_proba'].values,
})

# Add churn label (Yes/No) for optimal threshold
final_predictions['churn_label'] = final_predictions['churn_prediction_threshold_0.25'].map(
    {0: 'No', 1: 'Yes'}
)

# Add risk level
def get_risk_level(prob):
    if prob < 0.25:
        return 'Low'
    elif prob < 0.40:
        return 'Medium'
    elif prob < 0.55:
        return 'High'
    else:
        return 'Very High'

final_predictions['risk_level'] = final_predictions['churn_probability'].apply(get_risk_level)

print(f"✅ Generated final predictions")
print(f"✅ Shape: {final_predictions.shape}")

# ============================================================================
# STEP 3: PREDICTION DISTRIBUTION
# ============================================================================

print("\n" + "="*80)
print("STEP 3: PREDICTION DISTRIBUTION")
print("="*80)

print("\n📊 Churn Prediction Distribution (Optimal Threshold = 0.25):")
churn_dist = final_predictions['churn_label'].value_counts()
print(f"   No Churn: {churn_dist.get('No', 0):,} ({churn_dist.get('No', 0)/len(final_predictions)*100:.2f}%)")
print(f"   Churn: {churn_dist.get('Yes', 0):,} ({churn_dist.get('Yes', 0)/len(final_predictions)*100:.2f}%)")

print("\n📊 Risk Level Distribution:")
risk_dist = final_predictions['risk_level'].value_counts().sort_index()
for risk, count in risk_dist.items():
    print(f"   {risk}: {count:,} ({count/len(final_predictions)*100:.2f}%)")

print("\n📊 Probability Statistics:")
print(f"   Mean: {final_predictions['churn_probability'].mean():.4f}")
print(f"   Median: {final_predictions['churn_probability'].median():.4f}")
print(f"   Std Dev: {final_predictions['churn_probability'].std():.4f}")
print(f"   Min: {final_predictions['churn_probability'].min():.4f}")
print(f"   Max: {final_predictions['churn_probability'].max():.4f}")
print(f"   25th percentile: {final_predictions['churn_probability'].quantile(0.25):.4f}")
print(f"   75th percentile: {final_predictions['churn_probability'].quantile(0.75):.4f}")

# ============================================================================
# STEP 4: SAVE PREDICTIONS
# ============================================================================

print("\n" + "="*80)
print("STEP 4: SAVE PREDICTIONS")
print("="*80)

# Full detailed predictions
final_predictions.to_csv(f"{RESULTS_DIR}/holdout_final_predictions_detailed.csv", index=False)
print(f"✅ Saved detailed predictions: holdout_final_predictions_detailed.csv")

# Simplified deployment version
deployment_predictions = pd.DataFrame({
    'customer_id': final_predictions['record_id'],
    'churn_probability': final_predictions['churn_probability'],
    'churn_prediction': final_predictions['churn_label'],
    'risk_level': final_predictions['risk_level']
})

deployment_predictions.to_csv(f"{RESULTS_DIR}/holdout_predictions_deployment.csv", index=False)
print(f"✅ Saved deployment predictions: holdout_predictions_deployment.csv")

# High-risk customers (for targeted retention)
high_risk = final_predictions[final_predictions['risk_level'].isin(['High', 'Very High'])].copy()
high_risk.to_csv(f"{RESULTS_DIR}/high_risk_customers.csv", index=False)
print(f"✅ Saved high-risk customers: high_risk_customers.csv ({len(high_risk):,} records)")

# ============================================================================
# STEP 5: SUMMARY STATISTICS
# ============================================================================

print("\n" + "="*80)
print("STEP 5: SUMMARY STATISTICS")
print("="*80)

summary_stats = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║           TELECOM CHURN - FINAL HOLDOUT PREDICTIONS SUMMARY                ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 PREDICTIONS GENERATED:
  • Total holdout records: {len(final_predictions):,}
  • Predicted to churn: {(final_predictions['churn_label'] == 'Yes').sum():,} ({(final_predictions['churn_label'] == 'Yes').sum()/len(final_predictions)*100:.2f}%)
  • Predicted not to churn: {(final_predictions['churn_label'] == 'No').sum():,} ({(final_predictions['churn_label'] == 'No').sum()/len(final_predictions)*100:.2f}%)

🎯 RISK LEVEL BREAKDOWN:
  • Low Risk: {(final_predictions['risk_level'] == 'Low').sum():,} ({(final_predictions['risk_level'] == 'Low').sum()/len(final_predictions)*100:.2f}%)
  • Medium Risk: {(final_predictions['risk_level'] == 'Medium').sum():,} ({(final_predictions['risk_level'] == 'Medium').sum()/len(final_predictions)*100:.2f}%)
  • High Risk: {(final_predictions['risk_level'] == 'High').sum():,} ({(final_predictions['risk_level'] == 'High').sum()/len(final_predictions)*100:.2f}%)
  • Very High Risk: {(final_predictions['risk_level'] == 'Very High').sum():,} ({(final_predictions['risk_level'] == 'Very High').sum()/len(final_predictions)*100:.2f}%)

📈 PROBABILITY DISTRIBUTION:
  • Mean: {final_predictions['churn_probability'].mean():.4f}
  • Median: {final_predictions['churn_probability'].median():.4f}
  • Std Dev: {final_predictions['churn_probability'].std():.4f}
  • Range: [{final_predictions['churn_probability'].min():.4f}, {final_predictions['churn_probability'].max():.4f}]
  • 25th-75th percentile: [{final_predictions['churn_probability'].quantile(0.25):.4f}, {final_predictions['churn_probability'].quantile(0.75):.4f}]

✅ PREDICTIONS SAVED:
  1. holdout_predictions_deployment.csv
     - Customer ID, Probability, Prediction, Risk Level
     - Ready for immediate deployment
     - Recommended for business use

  2. holdout_final_predictions_detailed.csv
     - Detailed predictions with all model outputs
     - Multiple threshold options
     - For analysis and monitoring

  3. high_risk_customers.csv
     - {len(high_risk):,} high-risk customers
     - Prioritize for retention efforts
     - Target for proactive outreach

🎯 DEPLOYMENT STRATEGY:

  Threshold: 0.25 (Optimal F1-Score = 0.4957)
  
  Risk Levels:
    • Low (prob < 0.25): Monitor, no action needed
    • Medium (0.25-0.40): Standard retention campaigns
    • High (0.40-0.55): Targeted retention offers
    • Very High (prob > 0.55): Priority 1 intervention

📋 ACTION ITEMS:

  1. Retention Team:
     - Review high-risk customers ({len(high_risk):,} total)
     - Prioritize very high-risk segment ({(final_predictions['risk_level'] == 'Very High').sum():,} customers)
     - Design targeted retention campaigns

  2. Executive Leadership:
     - {(final_predictions['churn_label'] == 'Yes').sum():,} customers at risk
     - Estimated revenue impact: [Calculate based on customer value]
     - ROI from retention efforts: [Calculate based on intervention cost]

  3. Data Science:
     - Monitor prediction drift
     - Track actual churn vs predicted
     - Retrain models quarterly with new data
     - A/B test different thresholds

  4. System Integration:
     - Deploy predictions to CRM system
     - Set up automated alerts for very high-risk
     - Create dashboards for monitoring
     - Log predictions for analysis

💡 BUSINESS IMPACT ANALYSIS:

  With {(final_predictions['churn_label'] == 'Yes').sum():,} predicted churners:
  
  If we successfully retain 30% of flagged churners:
    - {int((final_predictions['churn_label'] == 'Yes').sum() * 0.3)} customers retained
    - Potential value: [Customer Lifetime Value × 300]
  
  If retention effort costs $50 per customer:
    - Total investment: ${(final_predictions['churn_label'] == 'Yes').sum() * 50:,}
    - ROI threshold: [Calculate breakeven]

🚀 NEXT STEPS:

  1. Deploy predictions to production systems
  2. Set up monitoring dashboards
  3. Execute targeted retention campaigns
  4. Track model performance metrics
  5. Plan quarterly model retraining

📝 MODEL CONFIGURATION RECAP:
  
  Preprocessing:
    ✅ Missing value imputation (median/mode)
    ✅ Outlier handling (Winsorization)
    ✅ Feature scaling (RobustScaler)
    ✅ Categorical encoding (Label encoding)
    ✅ Feature engineering (9 new features)
    ✅ SMOTE balancing (training only)
  
  Models:
    ✅ XGBoost: AUC = 0.6710, F1 = 0.2574
    ✅ CatBoost: AUC = 0.6678, F1 = 0.2157
    ✅ Ensemble: AUC = 0.6737, F1 = 0.4957 (optimal threshold)
  
  Threshold: 0.25 (Optimal for F1-Score)

✅ PREDICTIONS READY FOR DEPLOYMENT!
"""

print(summary_stats)

# Save summary
with open(f"{RESULTS_DIR}/HOLDOUT_PREDICTIONS_SUMMARY.txt", 'w', encoding='utf-8') as f:
    f.write(summary_stats)

print(f"\n✅ Summary saved to: HOLDOUT_PREDICTIONS_SUMMARY.txt")
print(f"✅ ALL PREDICTIONS GENERATED AND SAVED SUCCESSFULLY! 🎉")

# ============================================================================
# STEP 6: QUICK STATS FOR BUSINESS
# ============================================================================

print("\n" + "="*80)
print("📊 QUICK BUSINESS SUMMARY")
print("="*80)

churn_rate = (final_predictions['churn_label'] == 'Yes').sum() / len(final_predictions) * 100
retention_focus = len(high_risk)

print(f"""
Predicted Churn Rate: {churn_rate:.1f}%
Customers at Risk (High+VeryHigh): {retention_focus:,}
Total Holdout Records: {len(final_predictions):,}

Model Confidence: AUC = 0.6737
Recommendation: Deploy with 0.25 threshold for max F1-Score
""")
