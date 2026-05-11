"""
LAPISAI Customer Churn Prediction - Data Integration & Feature Engineering
Dataset: churn_analysis_datasets
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Tuple
import warnings

warnings.filterwarnings('ignore')

# Configuration
DATA_DIR = Path(__file__).parent / 'churn_analysis_datasets'
OUTPUT_DIR = Path(__file__).parent / 'engineered_features'
OUTPUT_DIR.mkdir(exist_ok=True)

OBSERVATION_DATE = pd.Timestamp('2025-01-01')  # Latest date in dataset
PLAN_TYPES = ['Starter', 'Professional', 'Enterprise']


class DataIntegrationPipeline:
    """Load and integrate all data sources from churn_analysis_datasets"""
    
    def __init__(self, data_dir: Path = DATA_DIR, observation_date: pd.Timestamp = OBSERVATION_DATE):
        self.data_dir = data_dir
        self.observation_date = observation_date
        self.customer_accounts = None
        self.billing_data = None
        self.monthly_usage = None
        self.nps_surveys = None
        self.support_tickets = None
        self.integrated_df = None
        
    def load_data(self):
        """Load all CSV files with proper data type handling"""
        print("Loading data from churn_analysis_datasets...")
        
        # Customer Accounts
        self.customer_accounts = pd.read_csv(self.data_dir / 'customer_accounts.csv')
        self.customer_accounts['subscription_date'] = pd.to_datetime(
            self.customer_accounts['subscription_date'], format='%d/%m/%Y'
        )
        self.customer_accounts['unsubscribed_date'] = pd.to_datetime(
            self.customer_accounts['unsubscribed_date'], errors='coerce'
        )
        # Standardize plan_type case
        self.customer_accounts['plan_type'] = self.customer_accounts['plan_type'].str.capitalize()
        self.customer_accounts['contract_type'] = self.customer_accounts['contract_type'].str.capitalize()
        
        # Billing Data
        self.billing_data = pd.read_csv(self.data_dir / 'billing_data.csv')
        self.billing_data['billing_date'] = pd.to_datetime(
            self.billing_data['billing_date'], format='%d/%m/%Y'
        )
        self.billing_data['payment_date'] = pd.to_datetime(
            self.billing_data['payment_date'], format='%d/%m/%Y'
        )
        
        # Monthly Usage Metrics
        self.monthly_usage = pd.read_csv(self.data_dir / 'monthly_usage_metrics.csv')
        self.monthly_usage['last_login_date'] = pd.to_datetime(
            self.monthly_usage['last_login_date'], format='%d/%m/%Y'
        )
        
        # NPS Surveys
        self.nps_surveys = pd.read_csv(self.data_dir / 'nps_surveys.csv')
        self.nps_surveys['survey_date'] = pd.to_datetime(
            self.nps_surveys['survey_date'], format='%d/%m/%Y'
        )
        
        # Support Tickets
        self.support_tickets = pd.read_csv(self.data_dir / 'support_tickets.csv')
        # Handle mixed date formats
        self.support_tickets['created_date'] = pd.to_datetime(
            self.support_tickets['created_date'], format='mixed', errors='coerce'
        )
        
        print(f"✓ Customer Accounts: {len(self.customer_accounts)} records")
        print(f"✓ Billing Data: {len(self.billing_data)} records")
        print(f"✓ Monthly Usage: {len(self.monthly_usage)} records")
        print(f"✓ NPS Surveys: {len(self.nps_surveys)} records")
        print(f"✓ Support Tickets: {len(self.support_tickets)} records")
        
        return self
    
    def create_target_variable(self):
        """Create target variable: churned (0/1) based on unsubscribed_date"""
        self.customer_accounts['churned'] = (
            self.customer_accounts['unsubscribed_date'].notna().astype(int)
        )
        churn_rate = self.customer_accounts['churned'].mean()
        print(f"✓ Target Variable Created - Churn Rate: {churn_rate:.2%}")
        return self
    
    def integrate_data(self):
        """Integrate all data sources by customer_id"""
        print("\nIntegrating data sources...")
        
        # Start with customer accounts
        df = self.customer_accounts.copy()
        
        # Aggregate billing data
        billing_agg = self._aggregate_billing()
        df = df.merge(billing_agg, on='customer_id', how='left')
        
        # Aggregate usage data
        usage_agg = self._aggregate_usage()
        df = df.merge(usage_agg, on='customer_id', how='left')
        
        # Aggregate NPS data
        nps_agg = self._aggregate_nps()
        df = df.merge(nps_agg, on='customer_id', how='left')
        
        # Aggregate support tickets
        tickets_agg = self._aggregate_support_tickets()
        df = df.merge(tickets_agg, on='customer_id', how='left')
        
        self.integrated_df = df
        print(f"✓ Integrated dataset: {len(self.integrated_df)} customers, {len(self.integrated_df.columns)} features")
        
        return self
    
    def _aggregate_billing(self) -> pd.DataFrame:
        """Aggregate billing data by customer"""
        df = self.billing_data.copy()
        df['payment_delay_days'] = (df['payment_date'] - df['billing_date']).dt.days
        df['is_dunning'] = (df['record_type'] == 'dunning').astype(int)
        df['is_on_time'] = (df['payment_delay_days'] <= 0).astype(int)
        
        agg_dict = {
            'payment_value': ['mean', 'sum', 'std', 'min', 'max'],
            'payment_delay_days': ['mean', 'max'],
            'is_dunning': ['sum', 'mean'],
            'is_on_time': ['sum', 'mean'],
        }
        
        billing_agg = df.groupby('customer_id').agg(agg_dict).reset_index()
        billing_agg.columns = ['_'.join(col).strip('_') for col in billing_agg.columns.values]
        billing_agg.rename(columns={'customer_id': 'customer_id'}, inplace=True)
        
        # Calculate payment consistency score - use map for proper alignment
        on_time_total = df.groupby('customer_id')['is_on_time'].sum()
        total_payments = df.groupby('customer_id').size()
        billing_agg['payment_consistency_score'] = billing_agg['customer_id'].map(on_time_total / total_payments)
        billing_agg['payment_consistency_score'] = billing_agg['payment_consistency_score'].fillna(0)
        
        # Calculate dunning event count and ratio
        dunning_count = df[df['is_dunning'] == 1].groupby('customer_id').size()
        billing_agg['dunning_event_count'] = billing_agg['customer_id'].map(dunning_count)
        billing_agg['dunning_event_count'] = billing_agg['dunning_event_count'].fillna(0)
        
        billing_agg['dunning_event_ratio'] = billing_agg['customer_id'].map(
            df[df['is_dunning'] == 1].groupby('customer_id').size() / total_payments
        )
        billing_agg['dunning_event_ratio'] = billing_agg['dunning_event_ratio'].fillna(0)
        
        return billing_agg
    
    def _aggregate_usage(self) -> pd.DataFrame:
        """Aggregate usage metrics by customer"""
        df = self.monthly_usage.copy()
        
        agg_dict = {
            'monthly_usage_hrs': ['mean', 'std', 'max', 'min'],
            'feature_adoption_pct': ['mean', 'std', 'max'],
            'last_login_date': 'max',
        }
        
        usage_agg = df.groupby('customer_id').agg(agg_dict).reset_index()
        usage_agg.columns = ['_'.join(col).strip('_') for col in usage_agg.columns.values]
        
        # Calculate days since last login
        usage_agg['days_since_last_login'] = (
            self.observation_date - usage_agg['last_login_date_max']
        ).dt.days
        
        # Calculate usage trend (simplified - last vs first)
        first_usage = df.groupby('customer_id')['monthly_usage_hrs'].first().reset_index()
        first_usage.columns = ['customer_id', 'first_usage']
        last_usage = df.groupby('customer_id')['monthly_usage_hrs'].last().reset_index()
        last_usage.columns = ['customer_id', 'last_usage']
        
        usage_trend_df = first_usage.merge(last_usage, on='customer_id', how='left')
        usage_trend_df['usage_trend'] = np.where(
            usage_trend_df['first_usage'] != 0,
            (usage_trend_df['last_usage'] - usage_trend_df['first_usage']) / usage_trend_df['first_usage'],
            0
        )
        usage_agg = usage_agg.merge(usage_trend_df[['customer_id', 'usage_trend']], on='customer_id', how='left')
        
        # Usage per user (will be calculated after merging with total_users)
        avg_usage = df.groupby('customer_id')['monthly_usage_hrs'].mean().reset_index()
        avg_usage.columns = ['customer_id', 'avg_monthly_usage_hours']
        usage_agg = usage_agg.merge(avg_usage, on='customer_id', how='left')
        
        return usage_agg
    
    def _aggregate_nps(self) -> pd.DataFrame:
        """Aggregate NPS surveys by customer"""
        df = self.nps_surveys.copy()
        
        # Calculate moving average (last 6 months)
        cutoff_date = self.observation_date - timedelta(days=180)
        recent_nps = df[df['survey_date'] >= cutoff_date]
        
        nps_agg = df.groupby('customer_id')['nps_score'].agg(['mean', 'std', 'min', 'max']).reset_index()
        nps_agg.columns = ['customer_id', 'avg_nps_score', 'nps_std', 'nps_min', 'nps_max']
        
        # Recent NPS (last 6 months) - use map and fillna with avg_nps_score
        recent_nps_avg = recent_nps.groupby('customer_id')['nps_score'].mean()
        nps_agg['recent_nps_score'] = nps_agg['customer_id'].map(recent_nps_avg)
        nps_agg['recent_nps_score'] = nps_agg['recent_nps_score'].fillna(nps_agg['avg_nps_score'])
        
        # NPS trend (recent vs historical)
        nps_agg['nps_trend'] = nps_agg['recent_nps_score'] - nps_agg['avg_nps_score']
        
        # Detractor ratio
        detractor_count = df[df['nps_score'] < 7].groupby('customer_id').size()
        total_surveys = df.groupby('customer_id').size()
        nps_agg['detractor_ratio'] = nps_agg['customer_id'].map(detractor_count / total_surveys)
        nps_agg['detractor_ratio'] = nps_agg['detractor_ratio'].fillna(0)
        
        # NPS normalize [−1, 10] to [0, 1]
        nps_agg['nps_normalized'] = (nps_agg['avg_nps_score'] + 1) / 11
        
        return nps_agg
    
    def _aggregate_support_tickets(self) -> pd.DataFrame:
        """Aggregate support tickets by customer"""
        df = self.support_tickets.copy()
        
        # Basic counts
        tickets_agg = df.groupby('customer_id').size().reset_index(name='total_tickets')
        
        # By category - reset index to align properly
        category_pivot = df.groupby(['customer_id', 'category']).size().unstack(fill_value=0).reset_index()
        tickets_agg = tickets_agg.merge(category_pivot, on='customer_id', how='left')
        # Fill new category columns with 0
        category_cols = [col for col in category_pivot.columns if col != 'customer_id']
        for col in category_cols:
            tickets_agg[f'tickets_{col.lower()}'] = tickets_agg[col].fillna(0)
            tickets_agg = tickets_agg.drop(col, axis=1)
        
        # By priority - reset index to align properly
        priority_pivot = df.groupby(['customer_id', 'priority']).size().unstack(fill_value=0).reset_index()
        tickets_agg = tickets_agg.merge(priority_pivot, on='customer_id', how='left')
        # Fill new priority columns with 0
        priority_cols = [col for col in priority_pivot.columns if col != 'customer_id']
        for col in priority_cols:
            tickets_agg[f'priority_{col.lower()}'] = tickets_agg[col].fillna(0)
            tickets_agg = tickets_agg.drop(col, axis=1)
        
        # By status
        resolved = df[df['status'].isin(['Resolved', 'Closed'])].groupby('customer_id').size()
        tickets_agg['resolved_tickets'] = tickets_agg['customer_id'].map(resolved)
        tickets_agg['resolved_tickets'] = tickets_agg['resolved_tickets'].fillna(0)
        
        open_tickets = df[df['status'].isin(['Open', 'In Progress'])].groupby('customer_id').size()
        tickets_agg['open_tickets'] = tickets_agg['customer_id'].map(open_tickets)
        tickets_agg['open_tickets'] = tickets_agg['open_tickets'].fillna(0)
        
        # Critical ticket ratio
        critical_high = df[df['priority'].isin(['Critical', 'High'])].groupby('customer_id').size()
        tickets_agg['critical_high_tickets'] = tickets_agg['customer_id'].map(critical_high)
        tickets_agg['critical_high_tickets'] = tickets_agg['critical_high_tickets'].fillna(0)
        tickets_agg['critical_ticket_ratio'] = tickets_agg['critical_high_tickets'] / tickets_agg['total_tickets']
        tickets_agg['critical_ticket_ratio'] = tickets_agg['critical_ticket_ratio'].fillna(0)
        
        # Resolution rate
        tickets_agg['resolution_rate'] = tickets_agg['resolved_tickets'] / tickets_agg['total_tickets']
        tickets_agg['resolution_rate'] = tickets_agg['resolution_rate'].fillna(0)
        
        # Unresolved ratio
        tickets_agg['unresolved_ratio'] = tickets_agg['open_tickets'] / tickets_agg['total_tickets']
        tickets_agg['unresolved_ratio'] = tickets_agg['unresolved_ratio'].fillna(0)
        
        return tickets_agg


class FeatureEngineeringPipeline:
    """Engineer advanced features for churn prediction"""
    
    def __init__(self, df: pd.DataFrame, observation_date: pd.Timestamp = OBSERVATION_DATE):
        self.df = df.copy()
        self.observation_date = observation_date
        
    def engineer_features(self) -> pd.DataFrame:
        """Execute complete feature engineering pipeline"""
        print("\nEngineering features...")
        
        self.df = self._create_temporal_features()
        self.df = self._create_revenue_features()
        self.df = self._create_engagement_features()
        self.df = self._create_health_score_features()
        self.df = self._create_interaction_features()
        self.df = self._create_composite_features()
        
        # Handle missing values
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        self.df[numeric_cols] = self.df[numeric_cols].fillna(self.df[numeric_cols].median())
        
        print(f"✓ Feature Engineering Complete - Total features: {len(self.df.columns)}")
        return self.df
    
    def _create_temporal_features(self) -> pd.DataFrame:
        """Create time-based features"""
        df = self.df.copy()
        
        # Tenure
        df['tenure_days'] = (self.observation_date - df['subscription_date']).dt.days
        df['tenure_months'] = df['tenure_days'] / 30
        df['tenure_years'] = df['tenure_days'] / 365
        
        # Contract renewal months (for annual contracts)
        df['months_to_renewal'] = np.where(
            df['contract_type'] == 'Annual',
            (df['subscription_date'].dt.month - self.observation_date.month) % 12,
            0
        )
        
        # Activity recency
        df['days_since_last_login'] = df['days_since_last_login'].fillna(df['days_since_last_login'].median())
        df['inactive_flag'] = (df['days_since_last_login'] > 30).astype(int)
        
        print("✓ Temporal features created")
        return df
    
    def _create_revenue_features(self) -> pd.DataFrame:
        """Create revenue and payment-related features"""
        df = self.df.copy()
        
        # Base MRR
        df['mrr_current'] = df['payment_value_mean'].fillna(0)
        df['mrr_6mo_avg'] = df['payment_value_mean'].fillna(0)  # Already aggregated
        
        # MRR by contract type
        df['contract_factor'] = np.where(df['contract_type'] == 'Annual', 0.7, 1.0)
        df['annual_value'] = np.where(
            df['contract_type'] == 'Annual',
            df['payment_value_sum'].fillna(0),
            df['payment_value_mean'].fillna(0) * 12
        )
        
        # Revenue at Risk Calculation
        payment_health = (
            (df['is_on_time_mean'].fillna(0) * 0.5) +
            ((1 - df['dunning_event_ratio'].fillna(0)) * 0.3) +
            ((1 - (df['payment_delay_days_mean'].fillna(0) / 30).clip(0, 1)) * 0.2)
        )
        
        engagement_score = (
            (1 - (df['days_since_last_login'] / 90).clip(0, 1)) * 0.4 +
            (df['feature_adoption_pct_mean'].fillna(50) / 100 * 0.35) +
            (1 - (df['monthly_usage_hrs_std'].fillna(0) / (df['monthly_usage_hrs_mean'].fillna(1) + 1)) * 0.25)
        )
        
        satisfaction_score = (
            (df['nps_normalized'].fillna(0.5) * 0.5) +
            ((1 - df['critical_ticket_ratio'].fillna(0)) * 0.25) +
            (df['resolution_rate'].fillna(0.5) * 0.25)
        )
        
        df['payment_health_score'] = payment_health.clip(0, 1)
        df['engagement_health_score'] = engagement_score.clip(0, 1)
        df['satisfaction_health_score'] = satisfaction_score.clip(0, 1)
        
        df['revenue_at_risk'] = (
            df['mrr_current'] * 
            df['contract_factor'] * 
            df['payment_health_score'] * 
            df['engagement_health_score'] * 
            df['satisfaction_health_score'] * 
            12  # Annualized
        )
        
        # Payment trend
        df['payment_trend'] = np.where(
            df['payment_value_mean'] > 0,
            (df['payment_value_max'] - df['payment_value_min']) / df['payment_value_mean'],
            0
        )
        
        print("✓ Revenue features created")
        return df
    
    def _create_engagement_features(self) -> pd.DataFrame:
        """Create engagement-related features"""
        df = self.df.copy()
        
        # Usage per user
        df['usage_per_user'] = np.where(
            df['total_users'] > 0,
            df['monthly_usage_hrs_mean'].fillna(0) / df['total_users'],
            0
        )
        
        # Usage segments
        usage_75 = df['monthly_usage_hrs_mean'].quantile(0.75)
        usage_25 = df['monthly_usage_hrs_mean'].quantile(0.25)
        
        df['usage_segment'] = pd.cut(
            df['monthly_usage_hrs_mean'].fillna(0),
            bins=[0, usage_25, usage_75, np.inf],
            labels=['light_user', 'regular_user', 'power_user']
        )
        
        # Feature adoption trend
        df['feature_adoption_trend'] = df['feature_adoption_pct_std'].fillna(0)
        
        # Engagement velocity
        df['engagement_velocity'] = np.where(
            df['tenure_months'] > 0,
            (df['monthly_usage_hrs_max'].fillna(0) - df['monthly_usage_hrs_min'].fillna(0)) / df['tenure_months'],
            0
        )
        
        print("✓ Engagement features created")
        return df
    
    def _create_health_score_features(self) -> pd.DataFrame:
        """Create composite health scores"""
        df = self.df.copy()
        
        # Overall churn risk score
        df['churn_risk_score'] = (
            df['payment_health_score'] * 0.35 +
            df['engagement_health_score'] * 0.40 +
            df['satisfaction_health_score'] * 0.25
        )
        
        # Support burden
        df['support_burden_ratio'] = np.where(
            df['tenure_months'] > 0,
            df['total_tickets'] / df['tenure_months'],
            0
        )
        
        print("✓ Health score features created")
        return df
    
    def _create_interaction_features(self) -> pd.DataFrame:
        """Create plan-specific interaction features"""
        df = self.df.copy()
        
        # Starter Plan specific
        df['starter_monthly_usage_per_user'] = np.where(
            (df['plan_type'] == 'Starter') & (df['total_users'] > 0),
            df['monthly_usage_hrs_mean'] / df['total_users'],
            0
        )
        
        df['starter_engagement_to_cost'] = np.where(
            (df['plan_type'] == 'Starter') & (df['payment_value_mean'] > 0),
            df['engagement_health_score'] / df['payment_value_mean'],
            0
        )
        
        # Professional Plan specific
        df['professional_expansion_potential'] = np.where(
            df['plan_type'] == 'Professional',
            (df['total_users'] - 1) / np.maximum(df['total_users'], 1),  # Growth from initial
            0
        )
        
        df['professional_revenue_quality'] = np.where(
            df['plan_type'] == 'Professional',
            df['payment_consistency_score'] * df['nps_normalized'].fillna(0.5),
            0
        )
        
        # Enterprise Plan specific
        df['enterprise_account_health'] = np.where(
            df['plan_type'] == 'Enterprise',
            (df['payment_health_score'] * 0.4 +
             df['engagement_health_score'] * 0.35 +
             df['satisfaction_health_score'] * 0.25),
            0
        )
        
        df['enterprise_strategic_risk'] = np.where(
            df['plan_type'] == 'Enterprise',
            df['critical_high_tickets'] / np.maximum(df['total_tickets'], 1),
            0
        )
        
        print("✓ Interaction features created")
        return df
    
    def _create_composite_features(self) -> pd.DataFrame:
        """Create composite/derived features"""
        df = self.df.copy()
        
        # User growth indicators
        df['total_users_change'] = df['total_users'] - 1  # Assuming started with 1 user
        
        # NPS deterioration risk
        df['nps_deterioration_risk'] = np.where(
            df['nps_trend'] < 0,
            abs(df['nps_trend']),
            0
        )
        
        # Cost per user
        df['cost_per_user'] = np.where(
            df['total_users'] > 0,
            df['payment_value_mean'] / df['total_users'],
            0
        )
        
        # ROI indicator
        df['roi_indicator'] = np.where(
            df['cost_per_user'] > 0,
            df['usage_per_user'] / df['cost_per_user'],
            0
        )
        
        print("✓ Composite features created")
        return df


def main():
    """Main execution"""
    
    # Step 1: Load and integrate data
    pipeline = DataIntegrationPipeline()
    pipeline.load_data()
    pipeline.create_target_variable()
    pipeline.integrate_data()
    
    # Step 2: Engineer features
    fe_pipeline = FeatureEngineeringPipeline(pipeline.integrated_df)
    engineered_df = fe_pipeline.engineer_features()
    
    # Step 3: Save results
    engineered_df.to_csv(OUTPUT_DIR / 'lapisai_engineered_features.csv', index=False)
    print(f"\n✓ Engineered dataset saved to: {OUTPUT_DIR / 'lapisai_engineered_features.csv'}")
    
    # Step 4: Summary statistics
    print("\n" + "="*80)
    print("FEATURE ENGINEERING SUMMARY")
    print("="*80)
    print(f"Total Samples: {len(engineered_df)}")
    print(f"Total Features: {len(engineered_df.columns)}")
    print(f"\nChurn Distribution:")
    print(engineered_df['churned'].value_counts().to_string())
    print(f"\nChurn Distribution by Plan Type:")
    print(engineered_df.groupby(['plan_type', 'churned']).size().to_string())
    
    # Feature importance base
    print(f"\n{'Feature':<50} {'Non-Null %':<15} {'Data Type':<15}")
    print("-" * 80)
    for col in engineered_df.columns:
        non_null_pct = (engineered_df[col].notna().sum() / len(engineered_df)) * 100
        dtype = str(engineered_df[col].dtype)
        print(f"{col:<50} {non_null_pct:>13.1f}% {dtype:<15}")
    
    return engineered_df


if __name__ == '__main__':
    engineered_data = main()
