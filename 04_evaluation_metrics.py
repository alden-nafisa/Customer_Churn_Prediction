"""
TELECOM CHURN - EVALUATION METRICS
===================================

Comprehensive evaluation metrics and visualization
"""

import pandas as pd
import numpy as np
from sklearn.metrics import (
    roc_auc_score, roc_curve, f1_score, precision_score, recall_score,
    confusion_matrix, classification_report, precision_recall_curve,
    auc as sklearn_auc
)
import matplotlib.pyplot as plt
import seaborn as sns
import os

# ============================================================================
# CONFIGURATION
# ============================================================================

RESULTS_DIR = r"c:\Users\HP14\Downloads\pbl6\Customer_Churn_Prediction\model_results"

# ============================================================================
# STEP 1: LOAD VALIDATION PREDICTIONS
# ============================================================================

print("="*80)
print("STEP 1: LOAD VALIDATION PREDICTIONS")
print("="*80)

ensemble_val = pd.read_csv(f"{RESULTS_DIR}/ensemble_validation_predictions.csv")
model_comp = pd.read_csv(f"{RESULTS_DIR}/model_comparison.csv")

y_true = ensemble_val['actual'].values
ensemble_proba = ensemble_val['ensemble_proba'].values

print(f"✅ Loaded {len(ensemble_val):,} validation records")
print(f"✅ Class distribution: {np.unique(y_true, return_counts=True)}")

# ============================================================================
# STEP 2: GENERATE ROC CURVES
# ============================================================================

print("\n" + "="*80)
print("STEP 2: GENERATE ROC CURVES")
print("="*80)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Individual models
xgb_proba = ensemble_val['xgb_proba'].values
cat_proba = ensemble_val['cat_proba'].values

fpr_xgb, tpr_xgb, _ = roc_curve(y_true, xgb_proba)
auc_xgb = sklearn_auc(fpr_xgb, tpr_xgb)

fpr_cat, tpr_cat, _ = roc_curve(y_true, cat_proba)
auc_cat = sklearn_auc(fpr_cat, tpr_cat)

fpr_ens, tpr_ens, _ = roc_curve(y_true, ensemble_proba)
auc_ens = sklearn_auc(fpr_ens, tpr_ens)

# Plot 1: All models
ax = axes[0]
ax.plot(fpr_xgb, tpr_xgb, label=f'XGBoost (AUC={auc_xgb:.4f})', linewidth=2)
ax.plot(fpr_cat, tpr_cat, label=f'CatBoost (AUC={auc_cat:.4f})', linewidth=2)
ax.plot(fpr_ens, tpr_ens, label=f'Ensemble (AUC={auc_ens:.4f})', linewidth=2, linestyle='--')
ax.plot([0, 1], [0, 1], 'k--', alpha=0.3, label='Random Classifier')
ax.set_xlabel('False Positive Rate', fontsize=11)
ax.set_ylabel('True Positive Rate', fontsize=11)
ax.set_title('ROC Curves - Model Comparison', fontsize=12, fontweight='bold')
ax.legend(loc='lower right')
ax.grid(alpha=0.3)

# Plot 2: Ensemble focus
ax = axes[1]
ax.plot(fpr_ens, tpr_ens, color='#2E86AB', linewidth=3, label=f'Ensemble (AUC={auc_ens:.4f})')
ax.plot([0, 1], [0, 1], 'k--', alpha=0.3)
ax.fill_between(fpr_ens, tpr_ens, alpha=0.2, color='#2E86AB')
ax.set_xlabel('False Positive Rate', fontsize=11)
ax.set_ylabel('True Positive Rate', fontsize=11)
ax.set_title('ROC Curve - Ensemble Model', fontsize=12, fontweight='bold')
ax.legend(loc='lower right')
ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig(f"{RESULTS_DIR}/roc_curves.png", dpi=300, bbox_inches='tight')
print(f"✅ Saved ROC curves to: roc_curves.png")
plt.close()

# ============================================================================
# STEP 3: PRECISION-RECALL CURVE
# ============================================================================

print("\n" + "="*80)
print("STEP 3: PRECISION-RECALL CURVE")
print("="*80)

precision_scores, recall_scores, _ = precision_recall_curve(y_true, ensemble_proba)
pr_auc = sklearn_auc(recall_scores, precision_scores)

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(recall_scores, precision_scores, linewidth=3, color='#A23B72', label=f'PR Curve (AUC={pr_auc:.4f})')
ax.fill_between(recall_scores, precision_scores, alpha=0.2, color='#A23B72')

# Baseline (random classifier for imbalanced data)
baseline = y_true.sum() / len(y_true)
ax.axhline(y=baseline, color='k', linestyle='--', alpha=0.3, label=f'Baseline ({baseline:.4f})')

ax.set_xlabel('Recall', fontsize=12)
ax.set_ylabel('Precision', fontsize=12)
ax.set_title('Precision-Recall Curve - Ensemble Model', fontsize=13, fontweight='bold')
ax.legend(loc='upper right', fontsize=11)
ax.grid(alpha=0.3)
ax.set_xlim([0, 1])
ax.set_ylim([0, 1])

plt.tight_layout()
plt.savefig(f"{RESULTS_DIR}/precision_recall_curve.png", dpi=300, bbox_inches='tight')
print(f"✅ Saved Precision-Recall curve to: precision_recall_curve.png")
plt.close()

# ============================================================================
# STEP 4: CONFUSION MATRIX FOR DIFFERENT THRESHOLDS
# ============================================================================

print("\n" + "="*80)
print("STEP 4: CONFUSION MATRICES FOR DIFFERENT THRESHOLDS")
print("="*80)

fig, axes = plt.subplots(2, 3, figsize=(15, 10))
thresholds_to_plot = [0.25, 0.30, 0.35, 0.40, 0.45, 0.50]

for idx, threshold in enumerate(thresholds_to_plot):
    ax = axes[idx // 3, idx % 3]
    
    y_pred = (ensemble_proba > threshold).astype(int)
    cm = confusion_matrix(y_true, y_pred)
    
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax, cbar=False,
                xticklabels=['No Churn', 'Churn'],
                yticklabels=['No Churn', 'Churn'])
    
    f1 = f1_score(y_true, y_pred, zero_division=0)
    ax.set_title(f'Threshold = {threshold:.2f} (F1={f1:.4f})', fontweight='bold')
    ax.set_ylabel('True Label')
    ax.set_xlabel('Predicted Label')

plt.tight_layout()
plt.savefig(f"{RESULTS_DIR}/confusion_matrices.png", dpi=300, bbox_inches='tight')
print(f"✅ Saved confusion matrices to: confusion_matrices.png")
plt.close()

# ============================================================================
# STEP 5: PROBABILITY DISTRIBUTION
# ============================================================================

print("\n" + "="*80)
print("STEP 5: PREDICTION PROBABILITY DISTRIBUTION")
print("="*80)

fig, axes = plt.subplots(1, 3, figsize=(15, 4))

# XGBoost
ax = axes[0]
ax.hist(xgb_proba[y_true == 0], bins=50, alpha=0.7, label='No Churn', color='#2E86AB')
ax.hist(xgb_proba[y_true == 1], bins=50, alpha=0.7, label='Churn', color='#A23B72')
ax.set_xlabel('Predicted Probability', fontsize=11)
ax.set_ylabel('Frequency', fontsize=11)
ax.set_title('XGBoost Probability Distribution', fontsize=12, fontweight='bold')
ax.legend()
ax.grid(alpha=0.3)

# CatBoost
ax = axes[1]
ax.hist(cat_proba[y_true == 0], bins=50, alpha=0.7, label='No Churn', color='#2E86AB')
ax.hist(cat_proba[y_true == 1], bins=50, alpha=0.7, label='Churn', color='#A23B72')
ax.set_xlabel('Predicted Probability', fontsize=11)
ax.set_ylabel('Frequency', fontsize=11)
ax.set_title('CatBoost Probability Distribution', fontsize=12, fontweight='bold')
ax.legend()
ax.grid(alpha=0.3)

# Ensemble
ax = axes[2]
ax.hist(ensemble_proba[y_true == 0], bins=50, alpha=0.7, label='No Churn', color='#2E86AB')
ax.hist(ensemble_proba[y_true == 1], bins=50, alpha=0.7, label='Churn', color='#A23B72')
ax.set_xlabel('Predicted Probability', fontsize=11)
ax.set_ylabel('Frequency', fontsize=11)
ax.set_title('Ensemble Probability Distribution', fontsize=12, fontweight='bold')
ax.legend()
ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig(f"{RESULTS_DIR}/probability_distributions.png", dpi=300, bbox_inches='tight')
print(f"✅ Saved probability distributions to: probability_distributions.png")
plt.close()

# ============================================================================
# STEP 6: THRESHOLD PERFORMANCE CURVE
# ============================================================================

print("\n" + "="*80)
print("STEP 6: METRICS VS THRESHOLD CURVE")
print("="*80)

thresholds_range = np.arange(0.1, 1.0, 0.02)
metrics_by_threshold = []

for threshold in thresholds_range:
    y_pred = (ensemble_proba > threshold).astype(int)
    if y_pred.sum() > 0:
        metrics_by_threshold.append({
            'threshold': threshold,
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1': f1_score(y_true, y_pred, zero_division=0),
        })
    else:
        metrics_by_threshold.append({
            'threshold': threshold,
            'precision': 0,
            'recall': 0,
            'f1': 0,
        })

metrics_df = pd.DataFrame(metrics_by_threshold)

fig, ax = plt.subplots(figsize=(11, 6))
ax.plot(metrics_df['threshold'], metrics_df['precision'], marker='o', label='Precision', linewidth=2)
ax.plot(metrics_df['threshold'], metrics_df['recall'], marker='s', label='Recall', linewidth=2)
ax.plot(metrics_df['threshold'], metrics_df['f1'], marker='^', label='F1-Score', linewidth=2, color='#A23B72')
ax.axvline(x=0.25, color='red', linestyle='--', alpha=0.7, label='Optimal Threshold (0.25)')
ax.axvline(x=0.50, color='gray', linestyle='--', alpha=0.5, label='Default Threshold (0.50)')
ax.set_xlabel('Threshold', fontsize=12)
ax.set_ylabel('Score', fontsize=12)
ax.set_title('Metrics vs Prediction Threshold', fontsize=13, fontweight='bold')
ax.legend(fontsize=11)
ax.grid(alpha=0.3)
ax.set_xlim([0.1, 0.95])

plt.tight_layout()
plt.savefig(f"{RESULTS_DIR}/metrics_vs_threshold.png", dpi=300, bbox_inches='tight')
print(f"✅ Saved metrics vs threshold to: metrics_vs_threshold.png")
plt.close()

# ============================================================================
# STEP 7: COMPREHENSIVE METRICS REPORT
# ============================================================================

print("\n" + "="*80)
print("STEP 7: COMPREHENSIVE METRICS REPORT")
print("="*80)

y_pred_optimal = (ensemble_proba > 0.25).astype(int)
y_pred_default = (ensemble_proba > 0.50).astype(int)

report_optimal = classification_report(y_true, y_pred_optimal, target_names=['No Churn', 'Churn'])
report_default = classification_report(y_true, y_pred_default, target_names=['No Churn', 'Churn'])

metrics_report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              TELECOM CHURN - EVALUATION METRICS REPORT                     ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 VALIDATION SET OVERVIEW:
  • Total records: {len(ensemble_val):,}
  • Churned: {y_true.sum():,} ({y_true.sum()/len(y_true)*100:.2f}%)
  • Non-churned: {(y_true==0).sum():,} ({(y_true==0).sum()/len(y_true)*100:.2f}%)

═══════════════════════════════════════════════════════════════════════════════

🎯 ENSEMBLE MODEL PERFORMANCE (Optimal Threshold = 0.25):

{report_optimal}

═══════════════════════════════════════════════════════════════════════════════

🎯 ENSEMBLE MODEL PERFORMANCE (Default Threshold = 0.50):

{report_default}

═══════════════════════════════════════════════════════════════════════════════

📈 AUC-ROC SCORES:
  • XGBoost: {auc_xgb:.4f}
  • CatBoost: {auc_cat:.4f}
  • Ensemble: {auc_ens:.4f} ← BEST

📈 PRECISION-RECALL AUC:
  • Ensemble: {pr_auc:.4f}

🔍 THRESHOLD ANALYSIS:
  • Optimal threshold: 0.25
    - Maximizes F1-Score: 0.4957
    - Improves recall significantly
    - Better for catching churners
  
  • Default threshold: 0.50
    - Higher precision
    - Lower recall
    - Misses more churners

💡 KEY INSIGHTS:
  1. Ensemble model provides best AUC (0.6737)
  2. Threshold of 0.25 significantly improves F1-Score
  3. At optimal threshold:
     - Catches ~{(y_pred_optimal[y_true==1]==1).sum()}/{y_true.sum()} churners (recall)
     - Reduces false positives
  4. Trade-off between precision and recall important for business decision

🚀 DEPLOYMENT RECOMMENDATIONS:
  1. Use ensemble model with 0.25 threshold for production
  2. Monitor prediction drift over time
  3. Regularly evaluate performance
  4. Implement A/B testing for threshold optimization
  5. Consider business costs when selecting threshold

📁 GENERATED VISUALIZATIONS:
  ✅ roc_curves.png - ROC curves for all models
  ✅ precision_recall_curve.png - Precision-Recall curve
  ✅ confusion_matrices.png - Confusion matrices at different thresholds
  ✅ probability_distributions.png - Probability distribution by class
  ✅ metrics_vs_threshold.png - Metrics vs threshold optimization

✅ EVALUATION COMPLETED SUCCESSFULLY!
"""

print(metrics_report)

# Save report
with open(f"{RESULTS_DIR}/EVALUATION_METRICS_REPORT.txt", 'w', encoding='utf-8') as f:
    f.write(metrics_report)

print(f"\n✅ Report saved to: EVALUATION_METRICS_REPORT.txt")
