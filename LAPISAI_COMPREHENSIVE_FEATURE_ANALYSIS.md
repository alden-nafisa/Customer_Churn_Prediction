# LAPISAI Customer Churn Prediction - Comprehensive Feature Analysis

**Dataset**: churn_analysis_datasets  
**Models**: XGBoost & CATBoost (per Plan Type)  
**Target**: churned (binary classification)

---

## 1. FEATURE IMPORTANCE HIERARCHY

### A. High Impact Features (80%+ Prediction Accuracy Support)

#### **Tier 1: Behavioral Engagement Features**
| Feature | Source | Impact | Calculation |
|---------|--------|--------|-------------|
| `days_since_last_login` | monthly_usage_metrics | CRITICAL | MAX(observation_date) - last_login_date |
| `avg_monthly_usage_hours` | monthly_usage_metrics | CRITICAL | MEAN(monthly_usage_hrs) over 6-12 months |
| `feature_adoption_trend` | monthly_usage_metrics | HIGH | TREND(feature_adoption_pct) - declining vs stable vs improving |
| `payment_delay_days` | billing_data | CRITICAL | payment_date - billing_date |
| `dunning_event_count` | billing_data | CRITICAL | COUNT(record_type='dunning') |

#### **Tier 2: Financial & Contract Features**
| Feature | Source | Impact | Calculation |
|---------|--------|--------|-------------|
| `revenue_at_risk` | billing_data + customer_accounts | HIGH | SUM(payment_value) × contract_duration_factor × payment_health_score |
| `payment_consistency_score` | billing_data | HIGH | COUNT(on_time_payments) / COUNT(total_payments) |
| `mrr_change_trend` | billing_data | HIGH | TREND(monthly_payment_value) |
| `contract_type_influence` | customer_accounts | MEDIUM | Annual=0.7, Monthly=1.0 (risk factor) |
| `tenure_days` | customer_accounts | MEDIUM | observation_date - subscription_date |

#### **Tier 3: Satisfaction & Support Features**
| Feature | Source | Impact | Calculation |
|---------|--------|--------|-------------|
| `avg_nps_score` | nps_surveys | HIGH | MEAN(nps_score) - moving average (last 6 months) |
| `nps_trend` | nps_surveys | MEDIUM | TREND(nps_score) - deteriorating vs stable |
| `support_ticket_volume` | support_tickets | MEDIUM | COUNT(ticket_id) |
| `critical_ticket_ratio` | support_tickets | HIGH | COUNT(priority='Critical' OR 'High') / COUNT(total_tickets) |
| `unresolved_ticket_rate` | support_tickets | HIGH | COUNT(status IN ('Open', 'In Progress')) / COUNT(total_tickets) |

#### **Tier 4: Usage Scaling Features**
| Feature | Source | Impact | Calculation |
|---------|--------|--------|-------------|
| `total_users_change` | customer_accounts | MEDIUM | recent_total_users - initial_total_users |
| `user_growth_rate` | customer_accounts | MEDIUM | (recent_total_users / initial_total_users - 1) × 100 |
| `usage_per_user` | monthly_usage_metrics + customer_accounts | MEDIUM | monthly_usage_hrs / total_users |

---

## 2. PREPROCESSING STRATEGY (Beyond SMOTE)

### A. Data Cleaning & Validation
```
✓ Handle Missing Values:
  - Support_tickets: Forward-fill missing status/category by customer_id
  - NPS_surveys: Interpolate missing dates within customer timeline
  - Billing_data: Remove/flag customers with <2 valid payment records
  
✓ Outlier Detection & Treatment:
  - Payment value: IQR method per plan_type
  - Monthly usage: Z-score with plan_type-specific thresholds
  - NPS scores: Capped to [-1, 10] range
  
✓ Data Type Conversions:
  - All dates: Convert to datetime, extract (day, month, quarter, tenure_days)
  - Categorical: Standardize case (Starter, starter → Starter)
  - Numeric: Scale appropriately for tree-based models
```

### B. Class Imbalance Handling (Alternative to SMOTE)
```
✓ Stratified Train-Test Split:
  - Split by plan_type and target distribution
  - Ensure 70-30 split per plan type maintains churn distribution
  
✓ Class Weight Balancing:
  - Use scale_pos_weight in XGBoost
  - Use class_weights in CATBoost
  - Weight = (total_samples / (2 × minority_class_count))
  
✓ Threshold Tuning:
  - After training, optimize classification threshold by plan type
  - Use precision-recall curves to find optimal threshold for business needs
  
✓ Downsampling Majority (if needed):
  - Random undersampling non-churned customers
  - Apply only if computational resources limited
```

### C. Feature-Specific Preprocessing
```
✓ Billing Data Aggregation:
  - Group by customer_id
  - Calculate: total_revenue, avg_payment, std_payment, late_payment_count
  - Time windows: 3-month, 6-month, 12-month rolling aggregates
  
✓ Support Tickets Aggregation:
  - Group by customer_id
  - Count by category (Billing, Technical, Onboarding, etc.)
  - Count by priority (Low, Medium, High, Critical)
  - Calculate resolution time trends
  
✓ NPS Survey Processing:
  - Sort by survey_date, calculate moving average (3-6 months)
  - Detect NPS trend: improving (+), stable (0), declining (-)
  - Flag customers with NPS < 0 (detractors)
  
✓ Usage Metrics Normalization:
  - Normalize monthly_usage_hrs by plan_type median
  - Calculate usage trend (linear regression slope)
  - Feature adoption: scale to 0-1 range
```

---

## 3. FEATURE ENGINEERING COMPONENTS

### A. Customer Lifetime Value (CLV) Features
```python
# Revenue at Risk Calculation
revenue_at_risk = (
    SUM(payment_value) × 
    (1 - payment_consistency_score) × 
    contract_duration_factor ×
    (1 - nps_trend)  # Negative if trend declining
)

# Contract Duration Factor
if contract_type == 'Annual':
    contract_duration_factor = 0.7  # Lower risk
else:  # Monthly
    contract_duration_factor = 1.0  # Higher risk
```

### B. Risk Scoring Composite Features
```python
# Payment Health Score (0-1)
payment_health_score = (
    (on_time_payment_ratio × 0.5) +
    ((1 - dunning_event_ratio) × 0.3) +
    (1 - payment_delay_avg_normalized × 0.2)
)

# Engagement Health Score (0-1)
engagement_health_score = (
    (days_since_last_login_normalized × 0.4) +
    (feature_adoption_score × 0.3) +
    (usage_consistency × 0.3)
)

# Satisfaction Health Score (0-1)
satisfaction_health_score = (
    (avg_nps_normalized × 0.5) +
    ((1 - critical_ticket_ratio) × 0.3) +
    ((1 - unresolved_ticket_rate) × 0.2)
)

# Overall Churn Risk Score (0-1)
churn_risk_score = (
    payment_health_score × 0.35 +
    engagement_health_score × 0.40 +
    satisfaction_health_score × 0.25
)
```

### C. Interaction Features (Plan Type Specific)
```python
# For Starter Plan
starter_features = {
    'monthly_usage_per_user': avg_monthly_usage / total_users,
    'engagement_to_cost_ratio': engagement_score / (avg_payment * 12),
    'churn_velocity': (recent_engagement - past_engagement) / months_elapsed
}

# For Professional Plan
professional_features = {
    'expansion_potential': total_users_change / initial_total_users,
    'revenue_quality': payment_consistency * avg_nps_normalized,
    'support_efficiency': ticket_resolution_rate / ticket_volume
}

# For Enterprise Plan
enterprise_features = {
    'account_health_composite': (
        payment_health_score * 0.4 +
        engagement_health_score * 0.35 +
        satisfaction_health_score * 0.25
    ),
    'user_adoption_trend': (recent_adoption - initial_adoption) / months_active,
    'strategic_risk_indicator': critical_issue_count / total_support_tickets
}
```

### D. Temporal Features
```python
# Time-based Features
days_since_subscription = current_date - subscription_date
months_since_subscription = days_since_subscription / 30

# Seasonal Indicators
is_contract_renewal_month = (subscription_date.month == current_date.month)
months_to_renewal = (
    (subscription_date + 12 months) - current_date
) if contract_type == 'Annual' else 0

# Activity Recency
days_since_last_login = current_date - last_login_date
days_since_last_payment = current_date - last_payment_date
days_since_last_support_ticket = current_date - last_ticket_date
```

### E. Statistical Features
```python
# Payment Statistics
payment_mean = MEAN(payment_value) over 12 months
payment_std = STD(payment_value) over 12 months
payment_cv = payment_std / payment_mean  # Coefficient of variation

# Usage Statistics
usage_mean = MEAN(monthly_usage_hrs) over 6 months
usage_trend = TREND(monthly_usage_hrs) - slope of linear regression
usage_volatility = STD(monthly_usage_hrs) / usage_mean

# NPS Statistics
nps_mean = MEAN(nps_score)
nps_min = MIN(nps_score) last 6 months
nps_recovery = nps_recent - nps_past
```

---

## 4. FEATURE COMPONENT SPECIFICATIONS

### A. Revenue at Risk (Core Business Metric)

**Components:**
```
revenue_at_risk = base_mrr × contract_factor × payment_health × engagement_health × satisfaction_health

Where:
  • base_mrr = Monthly Recurring Revenue
    └─ Monthly plan: payment_value
    └─ Annual plan: payment_value / 12
  
  • contract_factor:
    ├─ Annual: 0.70 (lower risk, committed for 12 months)
    ├─ Monthly: 1.00 (higher risk, can cancel anytime)
  
  • payment_health [0-1]:
    ├─ on_time_ratio: COUNT(payment_date - billing_date ≤ 0) / total_payments
    ├─ dunning_impact: 1 - (dunning_count / total_payments)
    ├─ delay_impact: 1 - MIN(avg_payment_delay / 30, 1)
    └─ Score = (on_time_ratio × 0.5) + (dunning_impact × 0.3) + (delay_impact × 0.2)
  
  • engagement_health [0-1]:
    ├─ activity: 1 - MIN(days_since_login / 90, 1)  # 90 days is threshold
    ├─ adoption: feature_adoption_pct / 100
    ├─ consistency: 1 - usage_volatility / 2
    └─ Score = (activity × 0.4) + (adoption × 0.35) + (consistency × 0.25)
  
  • satisfaction_health [0-1]:
    ├─ nps_factor: (avg_nps_score + 1) / 11  # Scale [-1,10] to [0,1]
    ├─ support_factor: 1 - (critical_tickets / total_tickets)
    ├─ resolution_factor: resolution_rate / 100
    └─ Score = (nps_factor × 0.5) + (support_factor × 0.25) + (resolution_factor × 0.25)
```

### B. Billing Profile Features
```
payment_value (base metric)
  ├─ mrr_current: Current month payment value
  ├─ mrr_6mo_avg: 6-month rolling average
  ├─ mrr_12mo_avg: 12-month rolling average
  ├─ mrr_trend: (recent_6mo - past_6mo) / past_6mo
  │
  ├─ billing_amount_trend:
  │  ├─ increasing: mrr_trend > 0.05
  │  ├─ stable: -0.05 ≤ mrr_trend ≤ 0.05
  │  └─ declining: mrr_trend < -0.05
  │
  └─ payment_frequency:
     ├─ on_time_percentage: % of payments within 3 days of billing
     ├─ late_payments: COUNT(payment_date - billing_date > 3)
     └─ very_late_payments: COUNT(payment_date - billing_date > 30)

contract_type x payment_value interaction:
  ├─ annual_payment_commitment = payment_value × 12 (for annual contracts)
  ├─ monthly_flexibility = payment_value × 1 (lower commitment)
  └─ churn_probability ∝ (1 / contract_commitment) → monthly = higher risk
```

### C. Engagement Profile Features
```
monthly_usage_hrs (primary metric)
  ├─ usage_recent_3mo: MEAN(monthly_usage_hrs) last 3 months
  ├─ usage_recent_6mo: MEAN(monthly_usage_hrs) last 6 months
  ├─ usage_trend: TREND(monthly_usage_hrs) → slope coefficient
  │  ├─ positive: increasing usage (retention signal)
  │  ├─ flat: stable usage (neutral)
  │  └─ negative: declining usage (churn signal)
  │
  └─ usage_segments:
     ├─ power_user: > 75th percentile
     ├─ regular_user: 25-75th percentile
     └─ light_user: < 25th percentile

feature_adoption_pct (secondary metric)
  ├─ adoption_rate: MEAN(feature_adoption_pct)
  ├─ adoption_trend: (recent - past) / months
  └─ new_feature_utilization: COUNT(new_features_used) / COUNT(available_features)

login_frequency (activity indicator)
  ├─ last_login_days_ago: TODAY() - last_login_date
  ├─ login_frequency_30d: COUNT(logins) last 30 days
  └─ inactive_flag: days_since_login > 30 (binary)
```

### D. Satisfaction Profile Features
```
nps_surveys
  ├─ nps_latest: Most recent NPS score
  ├─ nps_avg_6mo: 6-month rolling average
  ├─ nps_trend:
  │  ├─ improving: (recent_3mo - past_3mo) > 1
  │  ├─ stable: -1 ≤ (recent_3mo - past_3mo) ≤ 1
  │  └─ declining: (recent_3mo - past_3mo) < -1
  │
  ├─ nps_segments:
  │  ├─ promoters: nps_score ≥ 9
  │  ├─ passives: 7 ≤ nps_score < 9
  │  └─ detractors: nps_score < 7
  │
  └─ sentiment_change:
     ├─ sentiment_velocity: (recent_survey - past_survey) / days_between
     └─ deterioration_risk: COUNT(declining_scores) / total_surveys
```

### E. Support Ticket Profile Features
```
support_tickets
  ├─ total_tickets_12mo: COUNT(all tickets)
  │
  ├─ tickets_by_category:
  │  ├─ billing_tickets: COUNT(category='Billing')
  │  ├─ technical_tickets: COUNT(category='Technical')
  │  ├─ onboarding_tickets: COUNT(category='Onboarding')
  │  ├─ account_tickets: COUNT(category='Account')
  │  └─ feature_request_tickets: COUNT(category='Feature Request')
  │
  ├─ tickets_by_priority:
  │  ├─ critical_tickets: COUNT(priority='Critical')
  │  ├─ high_priority: COUNT(priority='High')
  │  ├─ medium_priority: COUNT(priority='Medium')
  │  └─ low_priority: COUNT(priority='Low')
  │
  ├─ ticket_health_metrics:
  │  ├─ resolution_rate: COUNT(status='Resolved'|'Closed') / total_tickets
  │  ├─ open_tickets: COUNT(status IN ('Open', 'In Progress'))
  │  ├─ avg_resolution_days: MEAN(closed_date - created_date)
  │  └─ critical_unresolved: COUNT(priority='Critical' AND status NOT IN ('Resolved','Closed'))
  │
  └─ ticket_sentiment_impact:
     ├─ problem_frequency: high_priority_count / total_tickets
     └─ support_burden: total_tickets / (tenure_days / 30)  # tickets per month
```

### F. User Scaling Features
```
total_users (expansion indicator)
  ├─ user_count_change:
  │  ├─ absolute_change: recent_total_users - initial_total_users
  │  ├─ percentage_change: (recent - initial) / initial × 100
  │  └─ trend: TREND(total_users_monthly) over 6 months
  │
  ├─ user_growth_segments:
  │  ├─ expanding: percentage_change > 10%
  │  ├─ stable: -10% ≤ percentage_change ≤ 10%
  │  └─ contracting: percentage_change < -10%
  │
  └─ usage_efficiency:
     ├─ usage_per_user: avg_monthly_usage_hrs / total_users
     ├─ cost_per_user: payment_value / total_users
     └─ roi_indicator: usage_per_user / cost_per_user
```

---

## 5. PLAN TYPE SPECIFIC MODEL ARCHITECTURE

### Starter Plan
**Characteristics**: High volume, low MRR, monthly contracts, price-sensitive  
**Key Features**:
- Payment consistency (high churn from payment failures)
- Engagement metrics (low usage = early warning)
- Support burden (too many tickets relative to revenue)

**Feature Selection Priority**:
1. days_since_last_login
2. payment_delay_days
3. dunning_event_count
4. avg_monthly_usage_hours
5. critical_ticket_ratio
6. contract_type
7. revenue_at_risk

### Professional Plan
**Characteristics**: Mid-tier revenue, mixed contracts, growth-oriented  
**Key Features**:
- Expansion potential (user growth = expansion revenue)
- Revenue quality (stable high-value payments)
- Support resolution (technical/feature requests indicate engagement)

**Feature Selection Priority**:
1. total_users_change
2. mrr_trend
3. avg_nps_score
4. support_ticket_volume
5. feature_adoption_trend
6. payment_consistency_score
7. revenue_at_risk

### Enterprise Plan
**Characteristics**: Low volume, high MRR, annual contracts, relationship-driven  
**Key Features**:
- Account health composite (overall satisfaction matters)
- Strategic risk (unresolved critical issues = relationship risk)
- Usage expansion (low adoption = underutilization = churn risk)

**Feature Selection Priority**:
1. avg_nps_score
2. critical_ticket_ratio
3. user_adoption_trend
4. payment_health_score
5. unresolved_ticket_rate
6. engagement_health_score
7. revenue_at_risk

---

## 6. MODEL TRAINING STRATEGY

### Data Split by Plan Type
```
For each plan_type in ['Starter', 'Professional', 'Enterprise']:
  1. Filter data by plan_type
  2. Stratified split (70% train, 30% test) by target distribution
  3. Train plan-specific XGBoost model
  4. Train plan-specific CATBoost model
  5. Compare metrics & select best model per plan type
```

### Hyperparameter Optimization Strategy
```
XGBoost per plan_type:
  - max_depth: [4, 6, 8, 10]
  - learning_rate: [0.01, 0.05, 0.1, 0.2]
  - subsample: [0.7, 0.8, 0.9]
  - colsample_bytree: [0.7, 0.8, 0.9]
  - scale_pos_weight: automatic based on class balance

CATBoost per plan_type:
  - depth: [4, 6, 8, 10]
  - learning_rate: [0.01, 0.05, 0.1]
  - l2_leaf_reg: [1, 3, 5, 7, 9]
  - subsample: [0.66, 0.8, 0.9]
```

### Evaluation Metrics (Per Plan Type)
```
Primary Metrics:
  - ROC-AUC (overall discrimination ability)
  - Precision @ Recall=80% (find 80% of churners with high precision)
  - F1-Score (balanced metric)

Business Metrics:
  - Revenue Impact: (TP × avg_mrr) - (FP × acquisition_cost)
  - Churn Prevention Rate: TP / (TP + FN)
  - False Positive Cost: FP × intervention_cost
```

---

## 7. IMPLEMENTATION CHECKLIST

### Phase 1: Data Integration & Engineering
- [ ] Load all 5 CSV files
- [ ] Clean & standardize data types
- [ ] Calculate all feature components
- [ ] Aggregate by customer_id
- [ ] Handle missing values
- [ ] Create plan type specific features

### Phase 2: Feature Selection & Preprocessing
- [ ] Implement stratified train-test split
- [ ] Apply feature scaling (tree models don't need it, but document)
- [ ] Set up class weight balancing
- [ ] Create baseline feature set

### Phase 3: Model Training & Comparison
- [ ] Train 3 XGBoost models (Starter, Professional, Enterprise)
- [ ] Train 3 CATBoost models (Starter, Professional, Enterprise)
- [ ] Hyperparameter tuning per plan type
- [ ] Compare metrics & select best models

### Phase 4: Model Deployment & Monitoring
- [ ] Save trained models per plan type
- [ ] Create prediction pipeline
- [ ] Implement feature importance visualization
- [ ] Set up monitoring for model drift

