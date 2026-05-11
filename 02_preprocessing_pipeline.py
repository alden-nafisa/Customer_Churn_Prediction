"""
LAPISAI Customer Churn Prediction - Preprocessing & Feature Selection
Implements strategies beyond SMOTE for handling class imbalance
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split, StratifiedKFold
from typing import Tuple, Dict, List
import warnings

warnings.filterwarnings('ignore')

# Configuration
ENGINEERED_DATA = Path(__file__).parent / 'engineered_features' / 'lapisai_engineered_features.csv'
OUTPUT_DIR = Path(__file__).parent / 'preprocessed_data'
OUTPUT_DIR.mkdir(exist_ok=True)

PLAN_TYPES = ['Starter', 'Professional', 'Enterprise']
OBSERVATION_DATE = pd.Timestamp('2025-01-01')
RANDOM_STATE = 42

# Feature importance tiers based on analysis
TIER_1_FEATURES = [
    'days_since_last_login',
    'avg_monthly_usage_hours',
    'payment_delay_days_mean',
    'dunning_event_count',
    'critical_ticket_ratio',
    'avg_nps_score',
]

TIER_2_FEATURES = [
    'revenue_at_risk',
    'payment_consistency_score',
    'unresolved_ratio',
    'total_tickets',
    'mrr_current',
    'tenure_days',
]

TIER_3_FEATURES = [
    'usage_per_user',
    'feature_adoption_pct_mean',
    'nps_trend',
    'contract_type',
    'plan_type',
    'total_users',
]

# Features to drop (identifiers, temporal, etc.)
DROP_FEATURES = [
    'customer_id',
    'subscription_date',
    'unsubscribed_date',
    'last_login_date_max',
    'churned',  # target variable
]


class PreprocessingPipeline:
    """Data preprocessing with multiple strategies for class imbalance"""
    
    def __init__(self, data_path: Path = ENGINEERED_DATA):
        self.data_path = data_path
        self.raw_df = None
        self.processed_dfs = {}  # {plan_type: df}
        self.plan_type = None
        
    def load_data(self) -> 'PreprocessingPipeline':
        """Load engineered features"""
        print("Loading engineered features...")
        self.raw_df = pd.read_csv(self.data_path)
        print(f"✓ Loaded {len(self.raw_df)} samples with {len(self.raw_df.columns)} features")
        return self
    
    def validate_data_quality(self) -> 'PreprocessingPipeline':
        """Validate data quality and report issues"""
        print("\nValidating data quality...")
        
        # Check for missing values
        missing_pct = (self.raw_df.isnull().sum() / len(self.raw_df)) * 100
        high_missing = missing_pct[missing_pct > 50]
        
        if len(high_missing) > 0:
            print(f"⚠ Features with >50% missing values:")
            for feat, pct in high_missing.items():
                print(f"  - {feat}: {pct:.1f}%")
        
        # Check for outliers
        numeric_cols = self.raw_df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            q1 = self.raw_df[col].quantile(0.25)
            q3 = self.raw_df[col].quantile(0.75)
            iqr = q3 - q1
            outliers = ((self.raw_df[col] < (q1 - 3*iqr)) | (self.raw_df[col] > (q3 + 3*iqr))).sum()
            if outliers > 0:
                print(f"  - {col}: {outliers} outliers detected")
        
        print("✓ Data quality validation complete")
        return self
    
    def clean_data(self) -> 'PreprocessingPipeline':
        """Clean data: handle missing values and outliers"""
        print("\nCleaning data...")
        df = self.raw_df.copy()
        
        # Fill missing values with median for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if df[col].isnull().sum() > 0:
                median_val = df[col].median()
                df[col].fillna(median_val, inplace=True)
                print(f"  - {col}: filled {df[col].isnull().sum()} missing values")
        
        # Fill categorical missing values
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            if df[col].isnull().sum() > 0:
                mode_val = df[col].mode()[0] if len(df[col].mode()) > 0 else 'Unknown'
                df[col].fillna(mode_val, inplace=True)
        
        # Handle outliers using IQR method (capping) - EXCLUDE TARGET AND ID COLUMNS
        exclude_cols = {'churned', 'customer_id', 'plan_type', 'contract_type', 'usage_segment', 
                       'subscription_date', 'unsubscribed_date', 'last_login_date_max'}
        numeric_to_process = [col for col in numeric_cols if col not in exclude_cols]
        
        for col in numeric_to_process:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 3 * iqr
            upper_bound = q3 + 3 * iqr
            
            outlier_count = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
            if outlier_count > 0:
                df[col] = df[col].clip(lower_bound, upper_bound)
                print(f"  - {col}: capped {outlier_count} outliers")
        
        self.raw_df = df
        print("✓ Data cleaning complete")
        return self
    
    def standardize_categorical(self) -> 'PreprocessingPipeline':
        """Standardize categorical columns (case, values)"""
        print("\nStandardizing categorical features...")
        df = self.raw_df.copy()
        
        # Plan type standardization
        if 'plan_type' in df.columns:
            df['plan_type'] = df['plan_type'].str.capitalize()
            print(f"  - plan_type values: {df['plan_type'].unique().tolist()}")
        
        # Contract type standardization
        if 'contract_type' in df.columns:
            df['contract_type'] = df['contract_type'].str.capitalize()
            print(f"  - contract_type values: {df['contract_type'].unique().tolist()}")
        
        # Usage segment
        if 'usage_segment' in df.columns:
            print(f"  - usage_segment values: {df['usage_segment'].unique().tolist()}")
        
        self.raw_df = df
        print("✓ Categorical standardization complete")
        return self
    
    def create_plan_specific_datasets(self) -> Dict[str, pd.DataFrame]:
        """Create plan-specific datasets for model training"""
        print("\nCreating plan-specific datasets...")
        
        plan_dfs = {}
        for plan in PLAN_TYPES:
            plan_df = self.raw_df[self.raw_df['plan_type'] == plan].copy().reset_index(drop=True)
            churn_rate = plan_df['churned'].mean()
            
            print(f"\n  {plan} Plan:")
            print(f"    - Samples: {len(plan_df)}")
            print(f"    - Churn Rate: {churn_rate:.2%}")
            print(f"    - Churn Distribution: {plan_df['churned'].value_counts().to_dict()}")
            
            plan_dfs[plan] = plan_df
            self.processed_dfs[plan] = plan_df
        
        return plan_dfs


class FeatureSelectionPipeline:
    """Feature selection and engineering for optimal model performance"""
    
    def __init__(self, df: pd.DataFrame, plan_type: str):
        self.df = df.copy()
        self.plan_type = plan_type
        self.selected_features = None
        self.feature_groups = {
            'tier_1': [],
            'tier_2': [],
            'tier_3': [],
            'interaction': [],
        }
        
    def select_features_by_importance(self) -> List[str]:
        """Select features based on importance tiers and plan type"""
        print(f"\nSelecting features for {self.plan_type} plan...")
        
        available_cols = set(self.df.columns) - set(DROP_FEATURES)
        
        # Tier 1 features (critical)
        tier_1 = [f for f in TIER_1_FEATURES if f in available_cols]
        self.feature_groups['tier_1'] = tier_1
        print(f"  Tier 1 (Critical): {len(tier_1)} features")
        
        # Tier 2 features (high)
        tier_2 = [f for f in TIER_2_FEATURES if f in available_cols]
        self.feature_groups['tier_2'] = tier_2
        print(f"  Tier 2 (High): {len(tier_2)} features")
        
        # Tier 3 features (medium)
        tier_3 = [f for f in TIER_3_FEATURES if f in available_cols]
        self.feature_groups['tier_3'] = tier_3
        print(f"  Tier 3 (Medium): {len(tier_3)} features")
        
        # Plan-specific interaction features
        interaction_features = [
            col for col in available_cols 
            if col.startswith(self.plan_type.lower())
        ]
        self.feature_groups['interaction'] = interaction_features
        print(f"  Interaction ({self.plan_type}): {len(interaction_features)} features")
        
        # Combine features
        self.selected_features = tier_1 + tier_2 + tier_3 + interaction_features
        self.selected_features = [f for f in self.selected_features if f in available_cols]
        
        print(f"  ✓ Total selected: {len(self.selected_features)} features")
        return self.selected_features
    
    def remove_low_variance_features(self, threshold: float = 0.01) -> List[str]:
        """Remove features with low variance"""
        print(f"\n  Removing low variance features (threshold={threshold})...")
        
        numeric_features = self.df[self.selected_features].select_dtypes(include=[np.number]).columns
        variances = self.df[numeric_features].var()
        
        low_var_features = variances[variances < threshold].index.tolist()
        self.selected_features = [f for f in self.selected_features if f not in low_var_features]
        
        print(f"    - Removed {len(low_var_features)} low-variance features")
        print(f"    - Remaining: {len(self.selected_features)} features")
        
        return self.selected_features
    
    def remove_highly_correlated_features(self, threshold: float = 0.95) -> List[str]:
        """Remove features with high correlation (multicollinearity)"""
        print(f"\n  Removing highly correlated features (threshold={threshold})...")
        
        numeric_features = self.df[self.selected_features].select_dtypes(include=[np.number]).columns
        corr_matrix = self.df[numeric_features].corr().abs()
        
        # Find highly correlated pairs
        upper = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        )
        to_drop = [column for column in upper.columns if any(upper[column] > threshold)]
        
        self.selected_features = [f for f in self.selected_features if f not in to_drop]
        
        print(f"    - Removed {len(to_drop)} correlated features")
        print(f"    - Remaining: {len(self.selected_features)} features")
        
        return self.selected_features


class ClassImbalanceHandler:
    """Handle class imbalance without SMOTE"""
    
    @staticmethod
    def calculate_class_weights(y: pd.Series) -> Dict[int, float]:
        """Calculate class weights for balanced learning"""
        counts = y.value_counts()
        total = len(y)
        
        # Standard formula: weight = total / (n_classes * class_count)
        weights = {}
        for class_label, count in counts.items():
            weight = total / (len(counts) * count)
            weights[int(class_label)] = weight
        
        # Normalize so minority class = 1.0
        min_weight = min(weights.values())
        weights = {k: v / min_weight for k, v in weights.items()}
        
        return weights
    
    @staticmethod
    def stratified_train_test_split(
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.3,
        random_state: int = 42
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """Stratified split maintaining churn distribution"""
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            stratify=y,
            random_state=random_state
        )
        
        print(f"\n  Train set - Churn rate: {y_train.mean():.2%}")
        print(f"  Test set - Churn rate: {y_test.mean():.2%}")
        
        return X_train, X_test, y_train, y_test
    
    @staticmethod
    def stratified_kfold(n_splits: int = 5) -> StratifiedKFold:
        """Create stratified K-fold for cross-validation"""
        return StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)


def prepare_data_for_modeling(plan_type: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, List[str]]:
    """
    Complete preprocessing pipeline for a specific plan type
    Returns: X_train, X_test, y_train, y_test, feature_names
    """
    
    # Load and clean data
    pipeline = PreprocessingPipeline()
    pipeline.load_data()
    pipeline.validate_data_quality()
    pipeline.clean_data()
    pipeline.standardize_categorical()
    
    # Get plan-specific data
    plan_dfs = pipeline.create_plan_specific_datasets()
    plan_df = plan_dfs[plan_type]
    
    # Feature selection
    fe_pipeline = FeatureSelectionPipeline(plan_df, plan_type)
    features = fe_pipeline.select_features_by_importance()
    features = fe_pipeline.remove_low_variance_features()
    features = fe_pipeline.remove_highly_correlated_features()
    
    # Separate features and target
    X = plan_df[features].copy()
    y = plan_df['churned'].copy()
    
    # Remove rows with NaN in features or target before splitting
    valid_idx = ~(X.isnull().any(axis=1) | y.isnull())
    X = X[valid_idx].reset_index(drop=True)
    y = y[valid_idx].reset_index(drop=True)
    
    # Handle class imbalance
    class_weights = ClassImbalanceHandler.calculate_class_weights(y)
    print(f"\n  Class weights: {class_weights}")
    
    # Stratified split
    X_train, X_test, y_train, y_test = ClassImbalanceHandler.stratified_train_test_split(
        X, y, test_size=0.3, random_state=RANDOM_STATE
    )
    
    # Reset indices to ensure alignment
    X_train = X_train.reset_index(drop=True)
    X_test = X_test.reset_index(drop=True)
    y_train = y_train.reset_index(drop=True)
    y_test = y_test.reset_index(drop=True)
    
    # Save preprocessing info
    preprocess_info = {
        'plan_type': plan_type,
        'features_selected': features,
        'feature_groups': fe_pipeline.feature_groups,
        'class_weights': class_weights,
        'train_size': len(X_train),
        'test_size': len(X_test),
    }
    
    # Save metadata
    import json
    info_file = OUTPUT_DIR / f'{plan_type.lower()}_preprocessing_info.json'
    with open(info_file, 'w') as f:
        json.dump({k: str(v) for k, v in preprocess_info.items()}, f, indent=2)
    
    print(f"\n✓ Preprocessing complete for {plan_type}")
    
    return X_train, X_test, y_train, y_test, features


def main():
    """Main execution"""
    print("="*80)
    print("LAPISAI PREPROCESSING PIPELINE")
    print("="*80)
    
    preprocessing_results = {}
    
    for plan_type in PLAN_TYPES:
        print(f"\n{'='*80}")
        print(f"PROCESSING: {plan_type} PLAN")
        print(f"{'='*80}")
        
        X_train, X_test, y_train, y_test, features = prepare_data_for_modeling(plan_type)
        
        # Save datasets
        train_data = pd.concat([X_train, y_train.reset_index(drop=True)], axis=1)
        test_data = pd.concat([X_test, y_test.reset_index(drop=True)], axis=1)
        
        train_file = OUTPUT_DIR / f'{plan_type.lower()}_train.csv'
        test_file = OUTPUT_DIR / f'{plan_type.lower()}_test.csv'
        
        train_data.to_csv(train_file, index=False)
        test_data.to_csv(test_file, index=False)
        
        print(f"\n  ✓ Train data: {train_file}")
        print(f"  ✓ Test data: {test_file}")
        
        preprocessing_results[plan_type] = {
            'X_train': X_train,
            'X_test': X_test,
            'y_train': y_train,
            'y_test': y_test,
            'features': features,
        }
    
    print("\n" + "="*80)
    print("PREPROCESSING SUMMARY")
    print("="*80)
    for plan_type, data in preprocessing_results.items():
        print(f"\n{plan_type}:")
        print(f"  Train: {len(data['X_train'])} samples")
        print(f"  Test: {len(data['X_test'])} samples")
        print(f"  Features: {len(data['features'])}")


if __name__ == '__main__':
    main()
