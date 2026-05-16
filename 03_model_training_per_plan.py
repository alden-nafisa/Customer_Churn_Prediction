"""
LAPISAI Customer Churn Prediction - Model Training
XGBoost vs CATBoost per Plan Type with Hyperparameter Optimization
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Any
import json
import pickle
import warnings

# Models and optimization
import xgboost as xgb
from catboost import CatBoostClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.metrics import (
    roc_auc_score, precision_recall_fscore_support, f1_score,
    confusion_matrix, roc_curve, precision_recall_curve, accuracy_score,
    average_precision_score, brier_score_loss
)

warnings.filterwarnings('ignore')

# Configuration
PREPROCESSED_DATA_DIR = Path(__file__).parent / 'preprocessed_data'
MODELS_DIR = Path(__file__).parent / 'trained_models' / 'plan_specific'
MODELS_DIR.mkdir(parents=True, exist_ok=True)

PLAN_TYPES = ['Starter', 'Professional', 'Enterprise']
RANDOM_STATE = 42


class XGBoostTrainer:
    """XGBoost model training with hyperparameter tuning"""
    
    def __init__(self, plan_type: str):
        self.plan_type = plan_type
        self.model = None
        self.best_params = None
        self.cv_results = None
        self.metrics = {}
        
    def _load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """Load preprocessed data"""
        train_file = PREPROCESSED_DATA_DIR / f'{self.plan_type.lower()}_train.csv'
        test_file = PREPROCESSED_DATA_DIR / f'{self.plan_type.lower()}_test.csv'
        
        train_df = pd.read_csv(train_file)
        test_df = pd.read_csv(test_file)
        
        X_train = train_df.drop('churned', axis=1)
        y_train = train_df['churned']
        X_test = test_df.drop('churned', axis=1)
        y_test = test_df['churned']
        
        return X_train, X_test, y_train, y_test
    
    def _calculate_class_weights(self, y_train: pd.Series) -> float:
        """Calculate scale_pos_weight for XGBoost"""
        negative = (y_train == 0).sum()
        positive = (y_train == 1).sum()
        return negative / positive if positive > 0 else 1.0
    
    def hyperparameter_tuning(self, X_train: pd.DataFrame, y_train: pd.Series):
        """Perform grid search for optimal hyperparameters"""
        print(f"\n  Hyperparameter tuning for XGBoost ({self.plan_type})...")
        
        scale_pos_weight = self._calculate_class_weights(y_train)
        
        param_grid = {
            'max_depth': [4, 6, 8],
            'learning_rate': [0.01, 0.05, 0.1],
            'subsample': [0.7, 0.9],
            'colsample_bytree': [0.7, 0.9],
        }
        
        base_model = xgb.XGBClassifier(
            n_estimators=100,
            scale_pos_weight=scale_pos_weight,
            random_state=RANDOM_STATE,
            n_jobs=-1,
            eval_metric='logloss'
        )
        
        grid_search = GridSearchCV(
            base_model,
            param_grid,
            cv=3,
            scoring='roc_auc',
            n_jobs=-1,
            verbose=0
        )
        
        grid_search.fit(X_train, y_train)
        
        self.best_params = grid_search.best_params_
        self.best_params['scale_pos_weight'] = scale_pos_weight
        self.best_params['n_estimators'] = 200
        self.best_params['random_state'] = RANDOM_STATE
        
        print(f"    Best params: {self.best_params}")
        print(f"    Best CV Score (ROC-AUC): {grid_search.best_score_:.4f}")
        
        return self.best_params
    
    def train(self, X_train: pd.DataFrame, y_train: pd.Series):
        """Train XGBoost model"""
        print(f"\n  Training XGBoost ({self.plan_type})...")
        
        # Hyperparameter tuning
        self.hyperparameter_tuning(X_train, y_train)
        
        # Train final model
        self.model = xgb.XGBClassifier(**self.best_params)
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_train, y_train)],
            verbose=False
        )
        
        print(f"    ✓ Training complete")
        return self.model
    
    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
        """Evaluate model performance"""
        print(f"\n  Evaluating XGBoost ({self.plan_type})...")
        
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        # Calculate metrics
        self.metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_recall_fscore_support(y_test, y_pred, average='binary')[0],
            'recall': precision_recall_fscore_support(y_test, y_pred, average='binary')[1],
            'f1': f1_score(y_test, y_pred),
            'roc_auc': roc_auc_score(y_test, y_pred_proba),
            'pr_auc': average_precision_score(y_test, y_pred_proba),
            'brier_score': brier_score_loss(y_test, y_pred_proba),
        }
        
        # Confusion matrix
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
        self.metrics['specificity'] = tn / (tn + fp) if (tn + fp) > 0 else 0
        self.metrics['sensitivity'] = tp / (tp + fn) if (tp + fn) > 0 else 0
        
        print(f"    Accuracy:  {self.metrics['accuracy']:.4f}")
        print(f"    Precision: {self.metrics['precision']:.4f}")
        print(f"    Recall:    {self.metrics['recall']:.4f}")
        print(f"    F1-Score:  {self.metrics['f1']:.4f}")
        print(f"    ROC-AUC:   {self.metrics['roc_auc']:.4f}")
        print(f"    PR-AUC:    {self.metrics['pr_auc']:.4f}")
        
        return self.metrics
    
    def get_feature_importance(self, X_train: pd.DataFrame) -> pd.DataFrame:
        """Get feature importance"""
        importance = pd.DataFrame({
            'feature': X_train.columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return importance
    
    def save_model(self):
        """Save trained model"""
        model_file = MODELS_DIR / f'{self.plan_type.lower()}_xgboost.pkl'
        with open(model_file, 'wb') as f:
            pickle.dump(self.model, f)
        
        metrics_file = MODELS_DIR / f'{self.plan_type.lower()}_xgboost_metrics.json'
        with open(metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        print(f"    ✓ Model saved: {model_file}")
        print(f"    ✓ Metrics saved: {metrics_file}")


class CATBoostTrainer:
    """CATBoost model training with hyperparameter tuning"""
    
    def __init__(self, plan_type: str):
        self.plan_type = plan_type
        self.model = None
        self.best_params = None
        self.metrics = {}
        
    def _load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """Load preprocessed data"""
        train_file = PREPROCESSED_DATA_DIR / f'{self.plan_type.lower()}_train.csv'
        test_file = PREPROCESSED_DATA_DIR / f'{self.plan_type.lower()}_test.csv'
        
        train_df = pd.read_csv(train_file)
        test_df = pd.read_csv(test_file)
        
        X_train = train_df.drop('churned', axis=1)
        y_train = train_df['churned']
        X_test = test_df.drop('churned', axis=1)
        y_test = test_df['churned']
        
        return X_train, X_test, y_train, y_test
    
    def _calculate_class_weight(self, y_train: pd.Series) -> Dict[int, float]:
        """Calculate class weights for CATBoost"""
        counts = y_train.value_counts()
        total = len(y_train)
        
        weights = {}
        for class_label, count in counts.items():
            weight = total / (len(counts) * count)
            weights[int(class_label)] = weight
        
        # Normalize
        min_weight = min(weights.values())
        weights = {k: v / min_weight for k, v in weights.items()}
        
        return weights
    
    def hyperparameter_tuning(self, X_train: pd.DataFrame, y_train: pd.Series):
        """Use fixed hyperparameters for CATBoost (avoid sklearn cloning issues)"""
        print(f"\n  Hyperparameter tuning for CATBoost ({self.plan_type})...")
        
        class_weights = self._calculate_class_weight(y_train)
        
        # Use fixed params to avoid sklearn cloning issues with class_weights parameter
        self.best_params = {
            'depth': 6,
            'learning_rate': 0.05,
            'l2_leaf_reg': 3,
            'iterations': 200,
            'class_weights': class_weights,
            'random_state': RANDOM_STATE,
            'verbose': False,
            'cat_features': [],
        }
        
        print(f"    Using fixed hyperparameters (depth=6, lr=0.05, l2_leaf_reg=3)")
        print(f"    Class weights: {class_weights}")
        
        return self.best_params
    
    def train(self, X_train: pd.DataFrame, y_train: pd.Series):
        """Train CATBoost model"""
        print(f"\n  Training CATBoost ({self.plan_type})...")
        
        # Hyperparameter tuning
        self.hyperparameter_tuning(X_train, y_train)
        
        # Train final model
        self.model = CatBoostClassifier(**self.best_params)
        self.model.fit(X_train, y_train)
        
        print(f"    ✓ Training complete")
        return self.model
    
    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
        """Evaluate model performance"""
        print(f"\n  Evaluating CATBoost ({self.plan_type})...")
        
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        # Calculate metrics
        self.metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_recall_fscore_support(y_test, y_pred, average='binary')[0],
            'recall': precision_recall_fscore_support(y_test, y_pred, average='binary')[1],
            'f1': f1_score(y_test, y_pred),
            'roc_auc': roc_auc_score(y_test, y_pred_proba),
            'pr_auc': average_precision_score(y_test, y_pred_proba),
            'brier_score': brier_score_loss(y_test, y_pred_proba),
        }
        
        # Confusion matrix
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
        self.metrics['specificity'] = tn / (tn + fp) if (tn + fp) > 0 else 0
        self.metrics['sensitivity'] = tp / (tp + fn) if (tp + fn) > 0 else 0
        
        print(f"    Accuracy:  {self.metrics['accuracy']:.4f}")
        print(f"    Precision: {self.metrics['precision']:.4f}")
        print(f"    Recall:    {self.metrics['recall']:.4f}")
        print(f"    F1-Score:  {self.metrics['f1']:.4f}")
        print(f"    ROC-AUC:   {self.metrics['roc_auc']:.4f}")
        print(f"    PR-AUC:    {self.metrics['pr_auc']:.4f}")
        
        return self.metrics
    
    def get_feature_importance(self, X_train: pd.DataFrame) -> pd.DataFrame:
        """Get feature importance"""
        importance = pd.DataFrame({
            'feature': X_train.columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return importance
    
    def save_model(self):
        """Save trained model"""
        model_file = MODELS_DIR / f'{self.plan_type.lower()}_catboost.pkl'
        with open(model_file, 'wb') as f:
            pickle.dump(self.model, f)
        
        metrics_file = MODELS_DIR / f'{self.plan_type.lower()}_catboost_metrics.json'
        with open(metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        print(f"    ✓ Model saved: {model_file}")
        print(f"    ✓ Metrics saved: {metrics_file}")


class ModelComparison:
    """Compare XGBoost and CATBoost models"""
    
    def __init__(self):
        self.comparison_results = {}
        
    def compare_plan_type(self, plan_type: str):
        """Train and compare both models for a plan type"""
        print(f"\n{'='*80}")
        print(f"TRAINING MODELS FOR {plan_type.upper()} PLAN")
        print(f"{'='*80}")
        
        # Load data
        xgb_trainer = XGBoostTrainer(plan_type)
        X_train, X_test, y_train, y_test = xgb_trainer._load_data()
        
        # Train XGBoost
        print(f"\n--- XGBoost ---")
        xgb_trainer.train(X_train, y_train)
        xgb_metrics = xgb_trainer.evaluate(X_test, y_test)
        xgb_importance = xgb_trainer.get_feature_importance(X_train)
        xgb_trainer.save_model()
        
        # Train CATBoost
        print(f"\n--- CATBoost ---")
        cb_trainer = CATBoostTrainer(plan_type)
        cb_trainer.train(X_train, y_train)
        cb_metrics = cb_trainer.evaluate(X_test, y_test)
        cb_importance = cb_trainer.get_feature_importance(X_train)
        cb_trainer.save_model()
        
        # Store results
        self.comparison_results[plan_type] = {
            'xgboost': {
                'metrics': xgb_metrics,
                'importance': xgb_importance,
                'model': xgb_trainer.model,
            },
            'catboost': {
                'metrics': cb_metrics,
                'importance': cb_importance,
                'model': cb_trainer.model,
            }
        }
        
        # Compare
        self._print_comparison(plan_type, xgb_metrics, cb_metrics)
        
        return self.comparison_results[plan_type]
    
    def _print_comparison(self, plan_type: str, xgb_metrics: Dict, cb_metrics: Dict):
        """Print detailed comparison"""
        print(f"\n{'='*80}")
        print(f"MODEL COMPARISON: {plan_type.upper()}")
        print(f"{'='*80}")
        print(f"{'Metric':<20} {'XGBoost':<20} {'CATBoost':<20}")
        print("-" * 80)
        
        for metric in ['accuracy', 'precision', 'recall', 'f1', 'roc_auc', 'pr_auc']:
            xgb_val = xgb_metrics.get(metric, 0)
            cb_val = cb_metrics.get(metric, 0)
            winner = "✓ XGB" if xgb_val > cb_val else ("✓ CB" if cb_val > xgb_val else "TIED")
            print(f"{metric:<20} {xgb_val:<20.4f} {cb_val:<20.4f} {winner}")
        
        # Select best model
        best_model = 'XGBoost' if xgb_metrics['roc_auc'] > cb_metrics['roc_auc'] else 'CATBoost'
        print(f"\n  Recommended Model: {best_model}")
    
    def save_comparison_report(self):
        """Save comprehensive comparison report"""
        report = {}
        
        for plan_type, results in self.comparison_results.items():
            report[plan_type] = {
                'xgboost_metrics': results['xgboost']['metrics'],
                'catboost_metrics': results['catboost']['metrics'],
                'top_10_features_xgb': results['xgboost']['importance'].head(10).to_dict('records'),
                'top_10_features_cb': results['catboost']['importance'].head(10).to_dict('records'),
            }
        
        report_file = MODELS_DIR / 'model_comparison_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n✓ Comparison report saved: {report_file}")


def main():
    """Main execution"""
    print("="*80)
    print("LAPISAI MODEL TRAINING & COMPARISON")
    print("="*80)
    
    comparison = ModelComparison()
    
    for plan_type in PLAN_TYPES:
        comparison.compare_plan_type(plan_type)
    
    comparison.save_comparison_report()
    
    print(f"\n{'='*80}")
    print("TRAINING COMPLETE")
    print(f"{'='*80}")
    print(f"Models saved to: {MODELS_DIR}")


if __name__ == '__main__':
    main()
