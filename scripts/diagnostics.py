"""Diagnostics and quick model tuning for XGBoost and CatBoost.
Produces concise metrics: CV scores, best params, test metrics, calibration Brier, SHAP top features, and per-segment errors.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import sys
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate, GridSearchCV
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, brier_score_loss
import warnings
warnings.filterwarnings('ignore')

# Ensure project root is on sys.path so `src` package is importable
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
import src.churn_pipeline as cp

OUT = Path('artifacts/diagnostics')
OUT.mkdir(parents=True, exist_ok=True)

print('Loading dataset...')
df = cp.load_dataset()
print(f'Dataset rows: {len(df)}; columns: {list(df.columns)}')

# prepare features - drop target and ID columns
exclude_cols = [cp.TARGET_COLUMN, cp.ID_COLUMN, 'month', 'operating_system', 'browser', 'region', 'traffic_type']
feature_cols = [c for c in df.columns if c not in exclude_cols and c not in ['Revenue']]
print('Using features:', feature_cols)
X = df[feature_cols].copy()
y = df[cp.TARGET_COLUMN].copy()

# simple clean
X = X.fillna(0)

# detect types
num_feats, cat_feats = cp.detect_feature_types(X)
print('Numeric:', num_feats)
print('Categorical:', cat_feats)

# train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

results = {}

# cross-validate baseline pipelines
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scoring = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']

print('\nRunning cross-validation for baseline XGBoost pipeline...')
xgb_pipe = cp.build_xgb_pipeline(num_feats, cat_feats)
cv_res_xgb = cross_validate(xgb_pipe, X_train, y_train, cv=cv, scoring=scoring, n_jobs=1, return_train_score=False)
print('XGBoost CV (mean):', {k: float(np.mean(v)) for k, v in cv_res_xgb.items() if k.startswith('test_')})
results['xgb_cv'] = {k: float(np.mean(v)) for k, v in cv_res_xgb.items() if k.startswith('test_')}

print('\nRunning cross-validation for baseline CatBoost pipeline...')
cat_pipe = cp.build_catboost_pipeline(num_feats, cat_feats)
cv_res_cat = cross_validate(cat_pipe, X_train, y_train, cv=cv, scoring=scoring, n_jobs=1, return_train_score=False)
print('CatBoost CV (mean):', {k: float(np.mean(v)) for k, v in cv_res_cat.items() if k.startswith('test_')})
results['cat_cv'] = {k: float(np.mean(v)) for k, v in cv_res_cat.items() if k.startswith('test_')}

# Small grid search (lightweight)
print('\nGrid search XGBoost (light)')
param_grid_xgb = {
    'model__n_estimators': [100, 200],
    'model__max_depth': [3, 6],
}
gs_xgb = GridSearchCV(xgb_pipe, param_grid_xgb, cv=3, scoring='roc_auc', n_jobs=1)
gs_xgb.fit(X_train, y_train)
print('Best XGB params:', gs_xgb.best_params_, 'best score:', gs_xgb.best_score_)
results['xgb_grid_best'] = {'params': gs_xgb.best_params_, 'score': float(gs_xgb.best_score_)}

print('\nGrid search CatBoost (light)')
param_grid_cat = {
    'model__iterations': [200, 400],
    'model__depth': [4, 6],
}
# CatBoost estimator inside pipeline uses CatBoostClassifier; GridSearchCV expects param names accordingly
# but CatBoostClassifier uses 'iterations' and 'depth' attributes; pipeline param prefix is 'model__'
gs_cat = GridSearchCV(cat_pipe, param_grid_cat, cv=3, scoring='roc_auc', n_jobs=1)
gs_cat.fit(X_train, y_train)
print('Best Cat params:', gs_cat.best_params_, 'best score:', gs_cat.best_score_)
results['cat_grid_best'] = {'params': gs_cat.best_params_, 'score': float(gs_cat.best_score_)}

# Evaluate best models on test set
best_xgb = gs_xgb.best_estimator_
best_cat = gs_cat.best_estimator_

print('\nEvaluating on test set...')
def eval_model(m, Xte, yte):
    ypred = m.predict(Xte)
    probs = m.predict_proba(Xte)[:,1]
    return {
        'accuracy': float(accuracy_score(yte, ypred)),
        'precision': float(precision_score(yte, ypred, zero_division=0)),
        'recall': float(recall_score(yte, ypred, zero_division=0)),
        'f1': float(f1_score(yte, ypred, zero_division=0)),
        'roc_auc': float(roc_auc_score(yte, probs)),
        'brier': float(brier_score_loss(yte, probs)),
    }

res_xgb_test = eval_model(best_xgb, X_test, y_test)
res_cat_test = eval_model(best_cat, X_test, y_test)
print('XGB test:', res_xgb_test)
print('Cat test:', res_cat_test)
results['xgb_test'] = res_xgb_test
results['cat_test'] = res_cat_test

# Calibration: Platt (sigmoid) and Isotonic
print('\nCalibration: fitting Platt (sigmoid) and Isotonic on XGB')
cal_sig = CalibratedClassifierCV(best_xgb, method='sigmoid', cv=3)
cal_iso = CalibratedClassifierCV(best_xgb, method='isotonic', cv=3)
cal_sig.fit(X_train, y_train)
cal_iso.fit(X_train, y_train)
probs_sig = cal_sig.predict_proba(X_test)[:,1]
probs_iso = cal_iso.predict_proba(X_test)[:,1]
results['calibration'] = {
    'brier_uncal': float(brier_score_loss(y_test, best_xgb.predict_proba(X_test)[:,1])),
    'brier_sigmoid': float(brier_score_loss(y_test, probs_sig)),
    'brier_isotonic': float(brier_score_loss(y_test, probs_iso)),
}
print('Brier scores:', results['calibration'])

# SHAP summary for XGB and Cat
print('\nComputing SHAP mean(|SHAP|) for XGB (top 10)')
# transform features for model
Xtrain_trans = cp.transform_features(best_xgb, X_train)
explainer_xgb = cp.build_shap_explainer(best_xgb)
shap_vals = explainer_xgb(Xtrain_trans)
mean_abs = np.abs(shap_vals.values).mean(axis=0)
feature_names = best_xgb.named_steps['preprocessor'].get_feature_names_out().tolist()
shap_df = pd.DataFrame({'feature': feature_names, 'mean_abs_shap': mean_abs}).sort_values('mean_abs_shap', ascending=False)
top_shap = shap_df.head(10)
print(top_shap.to_dict(orient='records'))
results['xgb_shap_top'] = top_shap.to_dict(orient='records')

# Segment error analysis (skip for Online Shoppers which doesn't have plan_type/tenure)
print('\nSegment error analysis (by visitor type)')
merged_test = X_test.copy()
merged_test = merged_test.reset_index(drop=True)

# Get visitor_type for segmentation if available
if 'visitor_type' in X_test.columns:
    merged_test['visitor_type'] = X_test['visitor_type'].reset_index(drop=True)
else:
    merged_test['visitor_type'] = 'unknown'

seg_report = {}
preds = best_xgb.predict(X_test)

for vtype in merged_test['visitor_type'].unique():
    idxs = merged_test[merged_test['visitor_type']==vtype].index
    if len(idxs)==0: continue
    ytrue = y_test.reset_index(drop=True).loc[idxs]
    ypred = pd.Series(preds).loc[idxs]
    seg_report[f'visitor_{vtype}'] = {
        'n': int(len(idxs)),
        'accuracy': float(accuracy_score(ytrue, ypred)),
        'recall': float(recall_score(ytrue, ypred, zero_division=0)),
        'precision': float(precision_score(ytrue, ypred, zero_division=0)),
    }

print('Segment report:', list(seg_report.items())[:5])
results['segments'] = seg_report

# save results
(OUT / 'diagnostics.json').write_text(json.dumps(results, default=lambda o: str(o), indent=2))
print('\nDiagnostics complete — results written to', str(OUT / 'diagnostics.json'))
