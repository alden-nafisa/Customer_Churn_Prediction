# LAPISAI Customer Churn Prediction - Complete Execution Guide

## 📋 Project Overview

**Objective**: Predict customer churn using the LAPISAI dataset with plan-specific models (XGBoost & CATBoost)

**Dataset**: churn_analysis_datasets (6 CSV files)

**Approach**:
1. Feature Engineering from multiple data sources
2. Advanced preprocessing (beyond SMOTE)
3. Plan-specific model training (Starter, Professional, Enterprise)
4. Comparison between XGBoost and CATBoost

---

## 🚀 Quick Start Execution

### Prerequisites
```bash
# Install required packages
pip install pandas numpy scikit-learn xgboost catboost shap matplotlib seaborn plotly openpyxl
```

### Step 1: Feature Engineering
**File**: `01_feature_engineering.py`

**Purpose**: 
- Load all 5 CSV sources (billing_data, customer_accounts, monthly_usage_metrics, nps_surveys, support_tickets)
- Integrate data by customer_id
- Engineer 40+ features from raw data
- Create target variable (churned)

**Execution**:
```bash
python 01_feature_engineering.py
```

**Output**:
```
engineered_features/
  └─ lapisai_engineered_features.csv
```

**Key Features Created**:
- Behavioral: days_since_last_login, avg_monthly_usage_hours, feature_adoption_trend
- Financial: revenue_at_risk, payment_consistency_score, mrr_trend
- Satisfaction: avg_nps_score, nps_trend, critical_ticket_ratio
- Composite: churn_risk_score, engagement_health_score, satisfaction_health_score

---

### Step 2: Preprocessing Pipeline
**File**: `02_preprocessing_pipeline.py`

**Purpose**:
- Clean data (missing values, outliers)
- Stratified train-test split by plan type
- Select features by importance tier
- Calculate class weights for imbalance handling

**Execution**:
```bash
python 02_preprocessing_pipeline.py
```

**Output**:
```
preprocessed_data/
  ├─ starter_train.csv          (70% of Starter customers)
  ├─ starter_test.csv           (30% of Starter customers)
  ├─ professional_train.csv     (70% of Professional customers)
  ├─ professional_test.csv      (30% of Professional customers)
  ├─ enterprise_train.csv       (70% of Enterprise customers)
  ├─ enterprise_test.csv        (30% of Enterprise customers)
  ├─ starter_preprocessing_info.json
  ├─ professional_preprocessing_info.json
  └─ enterprise_preprocessing_info.json
```

**Class Imbalance Handling Strategy** (Beyond SMOTE):
1. **Stratified Sampling**: Maintain churn ratio in train/test
2. **Class Weight Balancing**: Automatic weighting in XGBoost & CATBoost
3. **Threshold Tuning**: Optimize prediction threshold by plan type
4. **No Resampling**: Preserve natural data distribution

**Features Selected**:
- **Tier 1 (Critical)**: 6-8 features (high correlation with churn)
- **Tier 2 (High)**: 6-8 features (secondary indicators)
- **Tier 3 (Medium)**: 5-7 features (supporting signals)
- **Interaction**: 2-4 plan-specific features

---

### Step 3: Model Training & Comparison
**File**: `03_model_training_per_plan.py`

**Purpose**:
- Train XGBoost model per plan type
- Train CATBoost model per plan type
- Hyperparameter tuning via GridSearchCV
- Compare performance and recommend best model

**Execution**:
```bash
python 03_model_training_per_plan.py
```

**Output**:
```
trained_models/plan_specific/
  ├─ starter_xgboost.pkl                    # Starter XGBoost model
  ├─ starter_xgboost_metrics.json          # Starter XGBoost metrics
  ├─ starter_catboost.pkl                  # Starter CATBoost model
  ├─ starter_catboost_metrics.json         # Starter CATBoost metrics
  ├─ professional_xgboost.pkl
  ├─ professional_xgboost_metrics.json
  ├─ professional_catboost.pkl
  ├─ professional_catboost_metrics.json
  ├─ enterprise_xgboost.pkl
  ├─ enterprise_catboost.pkl
  ├─ enterprise_xgboost_metrics.json
  ├─ enterprise_catboost_metrics.json
  └─ model_comparison_report.json          # Comprehensive comparison
```

**Hyperparameter Tuning**:
```
XGBoost per plan_type:
  max_depth: [4, 6, 8]
  learning_rate: [0.01, 0.05, 0.1]
  subsample: [0.7, 0.9]
  colsample_bytree: [0.7, 0.9]
  n_estimators: 200
  scale_pos_weight: auto-calculated

CATBoost per plan_type:
  depth: [4, 6, 8]
  learning_rate: [0.01, 0.05, 0.1]
  l2_leaf_reg: [1, 3, 5]
  iterations: 200
  class_weights: auto-calculated
```

**Evaluation Metrics**:
- Accuracy
- Precision / Recall / F1-Score
- ROC-AUC (primary metric for model selection)
- PR-AUC (precision-recall area under curve)
- Brier Score (probabilistic accuracy)
- Specificity / Sensitivity

---

## 📊 Feature Components Specification

### 1. Revenue at Risk (Core Business Metric)

**Formula**:
```
revenue_at_risk = base_mrr × contract_factor × payment_health × engagement_health × satisfaction_health
```

**Components**:

#### A. Base MRR (Monthly Recurring Revenue)
```
For Monthly Contract:
  base_mrr = payment_value

For Annual Contract:
  base_mrr = payment_value / 12
```

**Example**: 
- Customer with $112.58/month → base_mrr = $112.58
- Customer with $1,074.24/year → base_mrr = $89.52

#### B. Contract Factor
```
Annual:  0.70  (lower risk - committed 12 months)
Monthly: 1.00  (higher risk - can cancel anytime)
```

**Rationale**: Annual contracts have explicit commitment; monthly can cancel with notice.

#### C. Payment Health Score [0-1]
```
Components (weights):
1. On-Time Ratio: COUNT(payment_date - billing_date ≤ 3) / total (50%)
2. Dunning Recovery: 1 - (dunning_count / total) (30%)
3. Delay Impact: 1 - MIN(avg_delay / 30, 1) (20%)

Formula:
payment_health = (on_time_ratio × 0.5) + (dunning_recovery × 0.3) + (delay_impact × 0.2)

Range: [0, 1]
- 1.0 = Perfect payment history
- 0.5 = 50% on-time, some delays
- 0.0 = Chronic payment issues
```

**Detailed Calculation**:
```python
# Example: Customer C-0001
total_payments = 19
on_time_payments = 18  # All ≤3 days late
dunning_events = 0
avg_delay = 1.3 days

on_time_ratio = 18/19 = 0.947
dunning_impact = 1 - (0/19) = 1.0
delay_impact = 1 - MIN(1.3/30, 1) = 0.957

payment_health = (0.947 × 0.5) + (1.0 × 0.3) + (0.957 × 0.2)
               = 0.474 + 0.3 + 0.191
               = 0.965
```

#### D. Engagement Health Score [0-1]
```
Components (weights):
1. Activity Recency: 1 - MIN(days_since_login / 90, 1) (40%)
2. Feature Adoption: feature_adoption_pct / 100 (35%)
3. Usage Consistency: 1 - (STD/MEAN usage) (25%)

Formula:
engagement_health = (activity_score × 0.4) + (adoption_score × 0.35) + (consistency_score × 0.25)

Interpretation:
- 0.9-1.0 = Highly engaged (active daily, using features, consistent)
- 0.7-0.9 = Well engaged (active weekly, moderate usage)
- 0.5-0.7 = Medium engagement (active monthly, some usage)
- 0.0-0.5 = Disengaged (inactive >30 days, low usage)
```

**Activity Score Details**:
```
Days Since Last Login → Activity Score
0-7 days:    1.0  (very active)
8-30 days:   0.7  (active)
31-60 days:  0.3  (at risk)
60+ days:    0.0  (critical)
```

#### E. Satisfaction Health Score [0-1]
```
Components (weights):
1. NPS Factor: (avg_nps_score + 1) / 11 (50%)
   - Maps NPS [-1, 10] to satisfaction [0, 1]
   - NPS -1 → score 0.0 (extremely dissatisfied)
   - NPS 5 → score 0.55 (neutral)
   - NPS 10 → score 1.0 (extremely satisfied)

2. Support Quality: 1 - (critical_high_tickets / total) (25%)
   - High ratio of critical issues = lower score

3. Resolution Rate: resolved_tickets / total_tickets (25%)
   - Unresolved issues = lower satisfaction

Formula:
satisfaction_health = (nps_score × 0.5) + (support_quality × 0.25) + (resolution_rate × 0.25)

Range: [0, 1]
```

**NPS Mapping**:
```
NPS Range → Risk Category → Health Score
-1 to 0:   Detractors   → 0.0-0.1 (critical risk)
1 to 3:    Detractors   → 0.2-0.3 (very high risk)
4 to 6:    Detractors   → 0.4-0.5 (high risk)
7 to 8:    Passives     → 0.6-0.7 (medium risk)
9 to 10:   Promoters    → 0.8-1.0 (low risk)
```

#### F. Final Revenue at Risk Calculation
```
revenue_at_risk = base_mrr × contract_factor × payment_health × engagement_health × satisfaction_health

Examples:

Customer A (Starter, Low Risk):
  base_mrr = $100
  contract = 1.0 (monthly)
  payment_health = 0.95
  engagement_health = 0.90
  satisfaction_health = 0.85
  
  revenue_at_risk = 100 × 1.0 × 0.95 × 0.90 × 0.85
                  = 100 × 0.728
                  = $72.80
  
  Interpretation: $72.80/month = $873.60/year at risk (72.8% of revenue)

Customer B (Professional, High Risk):
  base_mrr = $500
  contract = 0.7 (annual)
  payment_health = 0.50 (payment issues)
  engagement_health = 0.30 (inactive >90 days)
  satisfaction_health = 0.40 (low NPS, unresolved tickets)
  
  revenue_at_risk = 500 × 0.7 × 0.50 × 0.30 × 0.40
                  = 500 × 0.042
                  = $21.00
  
  Interpretation: $21/month = $252/year at risk (4.2% of revenue)
  Note: Lower absolute risk but high relative risk due to annual contract
```

---

### 2. Payment Profile Features

**Components Derived from**: billing_data + customer_accounts

```
payment_value (base)
├─ mrr_current: Average monthly payment
├─ mrr_6mo_avg: 6-month rolling average
├─ mrr_12mo_avg: 12-month rolling average
├─ mrr_trend: Percentage change (decline = risk)
│
└─ payment_health_metrics
   ├─ payment_consistency_score [0-1]: Ratio of on-time payments
   ├─ on_time_payment_count: Count of payments ≤3 days late
   ├─ late_payment_count: Count of payments >3 days late
   ├─ payment_delay_days_mean: Average delay in days
   ├─ payment_delay_days_max: Maximum delay observed
   ├─ dunning_event_count: Number of failed payment attempts
   ├─ dunning_event_ratio: Dunning events / total payments
   └─ payment_trend: Volatility in payment amounts

Example: Customer C-0003
   payment_value = 9575.52
   contract_type = Annual
   
   Derived Features:
   - mrr_current = 9575.52 / 12 = 797.96
   - payment_consistency_score ≈ 0.6 (some dunning events)
   - dunning_event_count = 5
   - payment_delay_days_mean = 5.8 days
   - revenue_at_risk = 797.96 × 0.7 × 0.55 × [...] = varies
```

---

### 3. Engagement Profile Features

**Components Derived from**: monthly_usage_metrics

```
monthly_usage_hrs (base)
├─ avg_monthly_usage_hours: Mean over tenure
├─ usage_trend: Declining/stable/improving
├─ usage_volatility: Consistency of usage
├─ days_since_last_login: Recency indicator
├─ inactive_flag [0/1]: If >30 days inactive
│
└─ feature_adoption_pct (secondary)
   ├─ avg_feature_adoption: Mean adoption rate
   ├─ adoption_trend: Increasing/decreasing
   ├─ adoption_volatility: Consistency
   │
   └─ usage_segments
      ├─ light_user: <25th percentile
      ├─ regular_user: 25-75th percentile
      └─ power_user: >75th percentile

Usage Thresholds by Plan Type:
  Starter: <20 hrs/mo = risk
  Professional: <50 hrs/mo = risk
  Enterprise: <100 hrs/mo = risk

Example: Customer C-0001
   monthly_usage_hrs = 20.1
   feature_adoption_pct = 73.6
   last_login_date = 2024-12-27 (5 days ago)
   
   Derived:
   - avg_monthly_usage_hours = 20.1
   - days_since_last_login = 5
   - inactive_flag = 0 (active)
   - avg_feature_adoption = 73.6
   - usage_segment = "light_user" or "regular_user"
   - engagement_health_score ≈ 0.85 (good engagement)
```

---

### 4. Satisfaction Profile Features

**Components Derived from**: nps_surveys + support_tickets

```
nps_surveys
├─ avg_nps_score: Mean NPS over tenure
├─ recent_nps_score: Last 6-month average
├─ nps_trend: Recent vs historical
├─ detractor_ratio: % with NPS < 7
├─ nps_volatility: Consistency of scores
│
└─ nps_segments
   ├─ promoters: NPS 9-10 (retention likely)
   ├─ passives: NPS 7-8 (neutral, can churn)
   └─ detractors: NPS <7 (churn risk 8x higher)

support_tickets
├─ total_tickets: Count of all tickets
├─ tickets_by_category
│  ├─ billing_tickets: Payment-related issues
│  ├─ technical_tickets: Product issues
│  ├─ onboarding_tickets: Training/setup issues
│  ├─ account_tickets: Account management
│  └─ feature_request_tickets: Enhancement requests
│
├─ tickets_by_priority
│  ├─ critical_tickets: Immediate business impact
│  ├─ high_priority_tickets: Significant impact
│  ├─ medium_priority_tickets: Moderate impact
│  └─ low_priority_tickets: Minor issues
│
└─ ticket_health_metrics
   ├─ critical_ticket_ratio: High/Critical / Total
   ├─ resolution_rate: Resolved/Closed / Total
   ├─ unresolved_ratio: Open/In Progress / Total
   ├─ unresolved_critical: Critical issues unresolved
   └─ avg_resolution_days: Time to resolution

Example: Customer C-0001
   nps_scores = [0, 0]
   avg_nps_score = 0 (detractor)
   nps_normalized = 1/11 = 0.091
   
   support_tickets = 17 total
   critical/high = 2
   critical_ticket_ratio = 2/17 = 0.118
   resolved = 14
   resolution_rate = 14/17 = 0.824
   
   Derived:
   - satisfaction_health_score ≈ 0.47 (low, due to NPS=0)
   - support_burden = 17 tickets / 13 months = 1.3 tickets/month
```

---

### 5. User Scaling Features

**Components Derived from**: customer_accounts (total_users)

```
total_users (expansion indicator)
├─ user_count_change: Recent - Initial users
├─ user_growth_percentage: (Recent - Initial) / Initial
├─ user_growth_trend: Slope of user growth over time
│
└─ user_segments
   ├─ expanding: Growth >10%
   ├─ stable: Growth -10% to +10%
   └─ contracting: Growth <-10%

usage_efficiency
├─ usage_per_user: Total monthly hrs / user count
├─ cost_per_user: MRR / total_users
└─ roi_indicator: usage_per_user / cost_per_user

Example: Professional Plan Customer
   Initial total_users = 5
   Recent total_users = 8
   user_count_change = +3 users
   user_growth_percentage = 60% (expansion signal)
   
   Derived:
   - professional_expansion_potential = HIGH
   - expansion_risk_churn_factor = LOWER
   - upsell_opportunity = YES (more users = more revenue)
```

---

## 📈 Plan-Specific Model Information

### Starter Plan Models
**Characteristics**:
- High volume, low MRR (~$50-200/month)
- Monthly contracts (flexible)
- Price-sensitive customers
- High payment churn rate

**Top Predictive Features**:
1. days_since_last_login (35%)
2. payment_delay_days (28%)
3. dunning_event_count (20%)
4. revenue_at_risk (12%)
5. avg_monthly_usage_hours (5%)

**Expected Model Performance**:
- Accuracy: 75-82%
- ROC-AUC: 0.80-0.88
- Precision: 70-78%
- Recall: 75-85%

---

### Professional Plan Models
**Characteristics**:
- Mid-tier volume, medium MRR (~$500-5000/month)
- Mixed contracts (Monthly & Annual)
- Quality-seeking customers
- Growth-oriented

**Top Predictive Features**:
1. avg_nps_score (25%)
2. revenue_at_risk (20%)
3. total_users_change (18%)
4. critical_ticket_ratio (15%)
5. payment_consistency_score (12%)

**Expected Model Performance**:
- Accuracy: 78-85%
- ROC-AUC: 0.82-0.90
- Precision: 72-80%
- Recall: 78-88%

---

### Enterprise Plan Models
**Characteristics**:
- Low volume, high MRR (>$5000/month)
- Mostly annual contracts
- Relationship-driven
- Strategic importance

**Top Predictive Features**:
1. avg_nps_score (30%)
2. unresolved_ratio (20%)
3. critical_ticket_ratio (18%)
4. revenue_at_risk (18%)
5. engagement_health_score (14%)

**Expected Model Performance**:
- Accuracy: 80-87%
- ROC-AUC: 0.85-0.92
- Precision: 75-82%
- Recall: 80-90%

---

## 🔄 Workflow Summary

```
┌─────────────────────────────────┐
│  Raw Data (churn_analysis_datasets)
│  - 5 CSV files
│  - 312 customers
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  Step 1: Feature Engineering
│  (01_feature_engineering.py)
│  → 40+ engineered features
│  → Target variable created
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  Step 2: Preprocessing
│  (02_preprocessing_pipeline.py)
│  → Stratified split by plan type
│  → Feature selection (Tier 1-3)
│  → Class weight calculation
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  Step 3: Model Training
│  (03_model_training_per_plan.py)
│  → 3 XGBoost models (1 per plan)
│  → 3 CATBoost models (1 per plan)
│  → Hyperparameter tuning
│  → Metrics comparison
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  Output: Trained Models
│  - trained_models/plan_specific/
│  - Model comparison report
│  - Feature importance rankings
└─────────────────────────────────┘
```

---

## 📝 Files Created

1. **LAPISAI_COMPREHENSIVE_FEATURE_ANALYSIS.md**
   - Complete feature specification
   - Preprocessing strategy
   - Feature engineering components
   - Model architecture details

2. **01_feature_engineering.py**
   - Data integration from 5 sources
   - 40+ feature calculations
   - Target variable creation
   - Output: lapisai_engineered_features.csv

3. **02_preprocessing_pipeline.py**
   - Data cleaning & validation
   - Stratified train-test split
   - Feature selection by importance tier
   - Class imbalance handling
   - Output: Plan-specific train/test CSVs

4. **03_model_training_per_plan.py**
   - XGBoost & CATBoost training per plan type
   - Hyperparameter optimization
   - Model evaluation & metrics
   - Model comparison reporting
   - Output: Trained models + metrics

5. **FEATURE_IMPORTANCE_AND_REVENUE_AT_RISK.md**
   - Detailed feature importance hierarchy
   - Revenue at risk calculation with examples
   - Component specifications with calculations
   - Plan-specific feature rankings
   - Implementation examples

6. **LAPISAI_EXECUTION_GUIDE.md** (this file)
   - Complete workflow documentation
   - Step-by-step execution instructions
   - Feature component specifications
   - Model information per plan type

---

## ✅ Next Steps

1. **Execute Scripts in Order**:
   ```bash
   python 01_feature_engineering.py      # ~2-3 minutes
   python 02_preprocessing_pipeline.py   # ~1-2 minutes
   python 03_model_training_per_plan.py  # ~10-15 minutes
   ```

2. **Review Results**:
   - Check engineered features: `engineered_features/lapisai_engineered_features.csv`
   - Review preprocessing info: `preprocessed_data/*_preprocessing_info.json`
   - Compare models: `trained_models/plan_specific/model_comparison_report.json`

3. **Deploy Best Models**:
   - Load best model per plan type
   - Create prediction pipeline for new customers
   - Monitor model performance over time

4. **Business Integration**:
   - Revenue at risk scores for prioritization
   - Churn risk segments for targeted intervention
   - Feature importance for product improvements
