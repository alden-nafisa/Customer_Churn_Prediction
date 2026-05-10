"""Train and save final models for production."""
from pathlib import Path
import sys
sys.path.insert(0, '.')

import joblib
import numpy as np
import pandas as pd
import shap
from sklearn.model_selection import train_test_split
from sklearn.calibration import CalibratedClassifierCV

import src.churn_pipeline as cp

OUT = Path('artifacts')
OUT.mkdir(exist_ok=True)

print('Loading dataset...')
df = cp.load_dataset()
print(f'Dataset: {len(df)} rows')

# Prepare features
features, target = cp.split_features_target(df)
num_feats, cat_feats = cp.detect_feature_types(features)

print(f'Features: {len(num_feats)} numeric + {len(cat_feats)} categorical')
print(f'Target distribution: {target.value_counts().to_dict()}')

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    features, target, test_size=0.2, random_state=42, stratify=target
)

print('\n=== Training XGBoost ===')
xgb_pipe = cp.build_xgb_pipeline(num_feats, cat_feats)
xgb_pipe.fit(X_train, y_train)
xgb_test_metrics = cp.evaluate_model(xgb_pipe, X_test, y_test)
print(f'XGB Test metrics: {xgb_test_metrics}')

print('\n=== Training CatBoost ===')
cat_pipe = cp.build_catboost_pipeline(num_feats, cat_feats)
cat_pipe.fit(X_train, y_train)
cat_test_metrics = cp.evaluate_model(cat_pipe, X_test, y_test)
print(f'Cat Test metrics: {cat_test_metrics}')

print('\n=== Calibrating models ===')
xgb_cal = CalibratedClassifierCV(xgb_pipe, method='isotonic', cv=3)
xgb_cal.fit(X_train, y_train)
xgb_cal_metrics = cp.evaluate_model(xgb_cal, X_test, y_test)
print(f'XGB Calibrated: {xgb_cal_metrics}')

cat_cal = CalibratedClassifierCV(cat_pipe, method='isotonic', cv=3)
cat_cal.fit(X_train, y_train)
cat_cal_metrics = cp.evaluate_model(cat_cal, X_test, y_test)
print(f'Cat Calibrated: {cat_cal_metrics}')

print('\n=== Saving artifacts ===')
cp.save_artifact(xgb_pipe, OUT / 'xgb_model.pkl')
cp.save_artifact(cat_pipe, OUT / 'catboost_model.pkl')
cp.save_artifact(xgb_cal, OUT / 'xgb_model_calibrated.pkl')
cp.save_artifact(cat_cal, OUT / 'catboost_model_calibrated.pkl')
print('✓ Models saved')

# Save feature names for app
feature_names = {
    'numeric': num_feats,
    'categorical': cat_feats,
}
joblib.dump(feature_names, OUT / 'feature_names.pkl')
print('✓ Feature names saved')

# Save SHAP explainer for top model (XGB calibrated)
print('\n=== Creating SHAP explainer ===')
X_train_transformed = cp.transform_features(xgb_pipe, X_train)
explainer = cp.build_shap_explainer(xgb_pipe)
joblib.dump(explainer, OUT / 'shap_explainer.pkl')
print('✓ SHAP explainer saved')

# Save preprocessor for inference
preprocessor = xgb_pipe.named_steps['preprocessor']
joblib.dump(preprocessor, OUT / 'preprocessor.pkl')
print('✓ Preprocessor saved')

print('\n=== Summary ===')
print(f'XGB Best: {max(xgb_test_metrics["roc_auc"], xgb_cal_metrics["roc_auc"]):.4f} ROC-AUC')
print(f'Cat Best: {max(cat_test_metrics["roc_auc"], cat_cal_metrics["roc_auc"]):.4f} ROC-AUC')
print('\nArtifacts ready for Streamlit app:')
print('  - xgb_model_calibrated.pkl (recommended)')
print('  - catboost_model_calibrated.pkl')
print('  - preprocessor.pkl')
print('  - shap_explainer.pkl')
print('  - feature_names.pkl')
