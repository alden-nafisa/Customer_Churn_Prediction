# COMPREHENSIVE TELECOM CHURN PREDICTION ANALYSIS
## Detail Analysis, Preprocessing Strategy, & Algorithm Comparison

---

## 📊 EXECUTIVE SUMMARY

### Dataset Characteristics
- **Total Records**: 71,047 (train: 51,047 + holdout: 20,000)
- **Total Features**: 58 (26 numeric, 23 categorical, customer ID + target)
- **Target Variable**: Churn (Binary: Yes/No)
- **Data Type**: Real production data (not synthetic)

---

## 1️⃣ JENIS DATA KOTOR - COMPREHENSIVE BREAKDOWN

### A. Missing Values (Moderate Issue)
```
Total Missing: 3,515 (0.12% of all cells)

Critical Columns:
  • AgeHH1 & AgeHH2: 909 each (1.78%) ← Missing household ages
  • PercChangeRevenues & PercChangeMinutes: 367 each (0.72%)
  • 6 usage columns: 156 each (0.31%) - MonthlyRevenue, MonthlyMinutes, etc.
  • ServiceArea: 24 (0.05%)
  • Handsets, HandsetModels, CurrentEquipmentDays: 1 each

Strategy:
  ✅ Numeric features: Median imputation (robust to outliers)
  ✅ Categorical features: Mode imputation or 'Unknown' category
  ✅ No columns exceed 30% threshold → keep all features
```

### B. "Unknown" Values in Categorical Columns (HIDDEN Missing Data)
```
Tidak counted sebagai NaN tapi berisi missing information:
  • Homeownership: 17,060 (33.42%) 
  • HandsetPrice: 28,982 (56.78%) ← VERY HIGH!
  • MaritalStatus: 19,700 (38.59%)
  
Total ACTUAL missing data = visible NaN + 'Unknown' values

Strategy:
  ✅ Convert 'Unknown' to NaN FIRST
  ✅ Then apply imputation strategy
  ✅ Or treat 'Unknown' sebagai separate category IF informative
```

### C. Outliers - VERY SIGNIFICANT Issue
```
119,245 total outliers (2.34% of dataset)

Top Outlier Features (IQR method):
  1. PercChangeRevenues: 13,221 (25.90%) range: -1107.7 to 2483.5
  2. RoamingCalls: 8,835 (17.31%) range: 0 to 1112.4
  3. CallWaitingCalls: 7,448 (14.59%) range: 0 to 212.7
  4. PercChangeMinutes: 6,807 (13.33%) range: -3875 to 5192
  5. CustomerCareCalls: 6,721 (13.17%) range: 0 to 327.3
  
  Plus 10+ more features dengan 5-10% outliers

Masalah:
  • Extreme percentage changes dapat mencemar feature scaling
  • Outliers di call metrics mencerminkan customer behavior extremes
  • May indicate data entry errors OR legitimate unusual activity

Strategy:
  ✅ Use RobustScaler (resistant to outliers)
  ✅ Winsorization: Cap extreme values di 95th/5th percentile
  ✅ Log transformation untuk highly skewed features
  ✅ Investigate outliers - may be valuable signal, not noise!
```

### D. Skewed Distributions - SEVERE Issue
```
15+ features dengan |Skewness| > 1 (highly skewed):

  1. CallForwardingCalls: Skewness = 91.63 (EXTREMELY skewed!)
  2. UniqueSubs: Skewness = 79.64
  3. RoamingCalls: Skewness = 57.88
  4. ReferralsMadeBySubscriber: Skewness = 36.74
  5. AdjustmentsToCreditRating: Skewness = 18.62
  6. ThreewayCalls: Skewness = 17.55
  7. CustomerCareCalls: Skewness = 14.24
  8. DirectorAssistedCalls: Skewness = 13.57
  9. CallWaitingCalls: Skewness = 11.12
  10. ActiveSubs: Skewness = 10.65

Masalah:
  • Right-skewed: Most customers = 0, few dengan very high usage
  • Can dominate feature importance in tree models
  • Lead to unbalanced splits

Strategy:
  ✅ Log transformation: log(x + 1) untuk features dengan zero values
  ✅ Box-Cox transformation untuk normal-ize distributions
  ✅ Tree models naturally handle skewness well → not critical for XGBoost/CatBoost
```

### E. Format & Data Type Issues
```
Data Types Distribution:
  • float64: 26 columns
  • str: 23 columns (categorical)
  • int64: 9 columns

Categorical Encoding Issues:
  • CreditRating: Ordered categorical (1-Highest to 7-Lowest)
  • Occupation: 8 categories
  • PrizmCode: 4 categories  
  • ServiceArea: 747 unique values! (HIGH-CARDINALITY!)

Strategy:
  ✅ Preserve ordering untuk ordered categoricals
  ✅ CatBoost: automatic target encoding
  ✅ XGBoost: one-hot encode (akan sangat sparse untuk ServiceArea!)
```

### F. Class Imbalance
```
Distribution:
  • No: 36,336 (71.18%)
  • Yes: 14,711 (28.82%)

Imbalance Ratio: 2.47:1 (No:Yes)

Impact:
  • Model naturally biased toward predicting "No Churn"
  • Need to address untuk balanced F1-score

Strategy:
  ✅ SMOTE (Synthetic Minority Over-sampling Technique)
  ✅ Apply ONLY on training set (after train-test split)
  ✅ Use SMOTE-ENN or SMOTETomek untuk better boundary definition
  ✅ Alternative: Adjust class weights dalam model
```

### G. No Exact Duplicates
```
✅ Good news: Zero exact duplicate rows
✅ Reduces data cleaning burden
```

---

## 2️⃣ PREPROCESSING STRATEGY - COMPREHENSIVE PIPELINE

### Step 1: Handle 'Unknown' Values (CRITICAL!)
```python
# Convert 'Unknown' to NaN for proper imputation
data['Homeownership'] = data['Homeownership'].replace('Unknown', np.nan)
data['HandsetPrice'] = data['HandsetPrice'].replace('Unknown', np.nan)
data['MaritalStatus'] = data['MaritalStatus'].replace('Unknown', np.nan)
# And other categorical columns with 'Unknown'
```

### Step 2: Handle Missing Values
```python
# Numeric features: Median imputation (robust to outliers)
from sklearn.impute import SimpleImputer
numeric_imputer = SimpleImputer(strategy='median')
data[numeric_cols] = numeric_imputer.fit_transform(data[numeric_cols])

# Categorical features: Mode imputation
categorical_imputer = SimpleImputer(strategy='most_frequent')
data[categorical_cols] = categorical_imputer.fit_transform(data[categorical_cols])
```

### Step 3: Handle Outliers
```python
# Method 1: Winsorization (cap at 95th/5th percentile)
from scipy.stats.mstats import winsorize
for col in outlier_cols:
    data[col] = winsorize(data[col], limits=[0.05, 0.05])

# Method 2: RobustScaler (preserve outliers but reduce impact)
from sklearn.preprocessing import RobustScaler
scaler = RobustScaler()
data[numeric_cols] = scaler.fit_transform(data[numeric_cols])
```

### Step 4: Handle Skewed Distributions
```python
# Log transformation untuk right-skewed features
from numpy import log1p
skewed_cols = ['CallForwardingCalls', 'UniqueSubs', 'RoamingCalls', ...]

for col in skewed_cols:
    data[col + '_log'] = log1p(data[col])  # log(1 + x) handles zeros

# Or Box-Cox transformation
from scipy.stats import boxcox
for col in skewed_cols:
    data[col], lambda_param = boxcox(data[col] + 1)
```

### Step 5: Handle Categorical Features

#### For CatBoost (RECOMMENDED):
```python
# Minimal preprocessing - CatBoost handles it!
cat_features = [
    'ServiceArea', 'CreditRating', 'Occupation', 'MaritalStatus',
    'HandsetPrice', 'PrizmCode', 'IncomeGroup',
    'TruckOwner', 'RVOwner', 'Homeownership', 'OwnsMotorcycle',
    'BuysViaMailOrder', 'RespondsToMailOffers', 'OptOutMailings',
    'NonUSTravel', 'OwnsComputer', 'HasCreditCard',
    'HandsetRefurbished', 'HandsetWebCapable',
    'NewCellphoneUser', 'NotNewCellphoneUser', 'MadeCallToRetentionTeam'
]

# Tell CatBoost which columns are categorical - THAT'S IT!
```

#### For XGBoost:
```python
# One-hot encode ALL categoricals
data_encoded = pd.get_dummies(data, columns=categorical_cols, drop_first=True)

# WARNING: ServiceArea (747 unique) → 747 new columns!
# This increases sparsity and dimensionality significantly
```

### Step 6: Feature Engineering (Optional but Recommended)
```python
# Interaction features
data['monthly_per_minute'] = data['MonthlyRevenue'] / (data['MonthlyMinutes'] + 1)
data['call_intensity'] = (data['ReceivedCalls'] + data['OutboundCalls']) / (data['MonthsInService'] + 1)

# Aggregate customer features
data['total_calls'] = (data['ReceivedCalls'] + data['OutboundCalls'] + 
                       data['InboundCalls'] + data['RoamingCalls'])

# Temporal features (if available in tenure data)
data['in_contract'] = (data['MonthsInService'] < 24).astype(int)

# Engagement score
data['engagement_score'] = (
    data['ReceivedCalls'] + data['OutboundCalls'] + 
    data['CustomerCareCalls'] + data['RetentionCalls']
) / (data['MonthsInService'] + 1)
```

### Step 7: Train-Test Split & SMOTE
```python
from sklearn.model_selection import train_test_split
from imblearn.combine import SMOTETomek

# Split FIRST (important!)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Apply SMOTE only on training set
smote = SMOTETomek(random_state=42)
X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)

print(f"Before SMOTE: {pd.Series(y_train).value_counts()}")
# No: 29000, Yes: 11800
print(f"After SMOTE: {pd.Series(y_train_balanced).value_counts()}")
# No: 29000, Yes: 29000 (balanced!)
```

### Step 8: Feature Scaling (Optional for tree models, but helps with SHAP)
```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_balanced)
X_test_scaled = scaler.transform(X_test)
```

### Complete Preprocessing Pipeline Summary
```
Raw Data (51,047 x 58)
    ↓
1. Handle 'Unknown' → NaN
    ↓
2. Missing Value Imputation (numeric: median, categorical: mode)
    ↓
3. Outlier Handling (Winsorization or RobustScaler)
    ↓
4. Skewed Feature Transformation (log/Box-Cox)
    ↓
5a. For CatBoost: Keep categorical as-is
5b. For XGBoost: One-hot encode
    ↓
6. Feature Engineering (optional)
    ↓
7. Train-Test Split (stratified by target)
    ↓
8. SMOTE on training set only
    ↓
9. Feature Scaling (optional)
    ↓
Ready for Model Training!
```

---

## 3️⃣ FEATURE SELECTION & MODEL STRATIFICATION

### A. Top Features Correlated with Churn

**POSITIVE Correlation (higher = more likely to churn):**
```
1. CurrentEquipmentDays: 0.1037 ← Customer with older equipment
2. MadeCallToRetentionTeam: 0.0674 ← Already contacted retention
3. RetentionCalls: 0.0653 ← Sign of churn risk
4. RetentionOffersAccepted: 0.0350
5. UniqueSubs: 0.0345
6. HandsetPrice: 0.0315
7. HandsetRefurbished: 0.0300
```

**NEGATIVE Correlation (higher = less likely to churn):**
```
1. HandsetWebCapable: -0.0621 ← Modern web-capable handset
2. TotalRecurringCharge: -0.0613 ← Higher monthly bill = loyal?
3. MonthlyMinutes: -0.0502 ← High usage customers more loyal
4. CreditRating: -0.0448 ← Better credit = more loyal
5. OffPeakCallsInOut: -0.0408 ← Active usage
6. HandsetModels: -0.0400 ← Number of handset models
7. PeakCallsInOut: -0.0400 ← Peak hour usage
8. ReceivedCalls: -0.0375 ← Incoming call activity
9. CustomerCareCalls: -0.0355 ← Engaged with customer service
10. InboundCalls: -0.0342
```

**Key Insights:**
- Retention metrics are STRONGEST signals (calls, offers accepted)
- Equipment age is RED FLAG for churn
- Usage level is PROTECTIVE (high usage = loyal)
- Service engagement is POSITIVE signal

### B. Features for Potential Model Stratification

**Top Candidates by Churn Rate Variance:**

```
1. ServiceArea (747 unique values)
   • Min churn rate: 0% (one service area had no churn)
   • Max churn rate: 100% (likely small sample sizes)
   • Std Dev: 20.37%
   → RECOMMENDATION: YES, stratify by ServiceArea
      But aggregate small-size areas first
   
2. HandsetPrice (16 categories)
   • Min: 12.5%, Max: 45.0%, Std: 7.41%
   → RECOMMENDATION: YES, create models per price tier
   
3. MadeCallToRetentionTeam (Yes/No)
   • No: 28.24% churn, Yes: 45.04% churn
   • Variance: 16.80%
   → RECOMMENDATION: YES, separate models
      Customers who called retention already at high risk
   
4. HandsetWebCapable (Yes/No)
   • No: 37.35% churn, Yes: 27.89% churn  
   • Variance: 9.46%
   → RECOMMENDATION: MAYBE, combined features enough
   
5. CreditRating (7 categories)
   • Range: 22.1% to 31.0%, Std: 3.19%
   → RECOMMENDATION: NO, variance too small
```

**RECOMMENDED STRATIFICATION APPROACH:**

```
Tier 1: MadeCallToRetentionTeam (highest variance)
  ├─ Already_Called_Retention = Yes
  │   └─ HIGH CHURN RISK model (more aggressive features)
  └─ Never_Called_Retention = No
      └─ STANDARD model

Tier 2: HandsetPrice (within each tier above)
  ├─ Premium ($150+)
  │   └─ Model for loyal customers
  ├─ Mid-range ($30-80)
  │   └─ Standard model
  └─ Budget (<$30) / Unknown
      └─ Model for price-sensitive customers

Tier 3 (Optional): ServiceArea
  ├─ Aggregate small service areas
  ├─ Top 50 metropolitan areas → separate models
  └─ Other areas → combined

BENEFIT:
  • Personalized models for different customer segments
  • Can use different features/thresholds per segment
  • Better accuracy per segment
  • Easier to target interventions
```

**Feature Selection Strategy:**

```
Stage 1: Correlation-based
  • Remove features dengan |correlation| < 0.01
  • Review domain knowledge for exceptions

Stage 2: Feature Importance from Trees
  • Train quick XGBoost model
  • Keep top 40-50 features by gain/shap importance

Stage 3: Recursive Feature Elimination (optional)
  • Iteratively remove least important features
  • Monitor cross-validation performance

Stage 4: Domain Expertise
  • Retention metrics: MUST KEEP (strongest signals)
  • Equipment metrics: KEEP (age is churn signal)
  • Usage metrics: KEEP (protective factor)
  • Demographic: REVIEW (may be weaker)
  • Service area: KEEP (stratification feature)
```

---

## 4️⃣ XGBOOST WORKFLOW (Detailed)

### Initialization
```
Initial prediction: F₀ = log(p / (1-p)) = log(0.288 / 0.712) = -0.897

Setiap customer starts dengan log-odds = -0.897
(meaning 27% probability churn, 73% probability no churn)
```

### Iterative Tree Building (Each iteration m = 1, 2, ..., M)

**Step 1: Calculate Gradients & Hessians**
```
GRADIENT (error signal):
  gᵢ = sigmoid(ŷᵢ) - yᵢ
  
  Example:
  - Current prediction: ŷ = 0 → sigmoid(0) = 0.5
  - Actual label: y = 1 (churn)
  - Gradient: 0.5 - 1 = -0.5
    (negative → decrease prediction, need more "no churn" signal)
  
  - If y = 0 (no churn)
  - Gradient: 0.5 - 0 = 0.5
    (positive → increase prediction, need more "churn" signal)

HESSIAN (second derivative, optimization weight):
  hᵢ = sigmoid(ŷᵢ) × (1 - sigmoid(ŷᵢ))
  
  At ŷ = 0: h = 0.5 × 0.5 = 0.25 (maximum weight)
  At ŷ = ±3: h ≈ 0.05 (low weight, predictions confident)
  
  Higher hessian = more uncertain prediction = more weight for correction
```

**Step 2: Grow Decision Tree on Gradients**
```
Tree splits maximize:

  Gain = ½ × [Gₗ²/(Hₗ+λ) + Gᵣ²/(Hᵣ+λ) - (Gₗ+Gᵣ)²/(Hₗ+Hᵣ+λ)] - γ

  Where:
    Gₗ = sum of gradients left leaf
    Hₗ = sum of hessians left leaf  
    Gᵣ = sum of gradients right leaf
    Hᵣ = sum of hessians right leaf
    λ = L2 regularization (default: 1.0)
    γ = min split gain (default: 0)

Example:
  Considering split: RetentionCalls > 1
  Left (≤1): G = -100, H = 50, size = 25,000
  Right (>1): G = -200, H = 80, size = 26,000
  
  Gain = ½ × [(-100)²/(50+1) + (-200)²/(80+1) - (-300)²/(130+1)] - 0
       = ½ × [10000/51 + 40000/81 - 90000/131]
       = ½ × [196.08 + 493.83 - 687.02]
       = ½ × 2.89
       = 1.45

  If 1.45 > current_best_gain, this becomes new best split
```

**Step 3: Calculate Leaf Weights (Predictions)**
```
For each leaf:
  wⱼ = -Gⱼ / (Hⱼ + λ)

Example leaf with G = -50, H = 30, λ = 1:
  w = -(-50) / (30 + 1) = 50 / 31 = 1.61
  
  This leaf's prediction: 1.61 × learning_rate
  If learning_rate = 0.1: contribute +0.161 to final prediction
```

**Step 4: Update Predictions**
```
F_m(x) = F_{m-1}(x) + η × tree_m(x)

After Tree 1:
  F₁(x) = -0.897 + 0.1 × tree_1(x)
  
After Tree 100:
  F₁₀₀(x) = -0.897 + 0.1 × (tree_1(x) + tree_2(x) + ... + tree_100(x))
```

### Final Prediction
```
1. Accumulate all tree predictions:
   logit = F₀ + η × Σ(tree predictions)

2. Convert to probability:
   p(churn) = σ(logit) = 1 / (1 + e^(-logit))

3. Classify:
   IF p > 0.5: Predict CHURN
   ELSE: Predict NO CHURN
```

### Key XGBoost Parameters
```
Tree Control:
  • max_depth: 5-8 (deeper = more complex, overfitting risk)
  • min_child_weight: 1-5 (higher = more conservative)
  • gamma: 0-1 (higher = fewer splits, simpler tree)

Regularization:
  • lambda (L2): 1.0-10.0 (higher = smoother predictions)
  • alpha (L1): 0-1 (higher = sparse weights)

Learning:
  • learning_rate: 0.01-0.3 (lower = slower learning, less overfitting)
  • num_boost_rounds: 100-1000 (more rounds = more fine-tuning)

For this dataset (dirty, imbalanced, many categoricals):
  RECOMMENDED:
  {
    'max_depth': 6,
    'min_child_weight': 2,
    'gamma': 1,
    'lambda': 5.0,
    'alpha': 0.1,
    'learning_rate': 0.05,
    'num_boost_rounds': 500,
    'early_stopping_rounds': 50
  }
```

---

## 5️⃣ CATBOOST WORKFLOW (Detailed)

### Key Advantage: Native Categorical Support

**CatBoost Target Encoding (Permutation-based):**
```
Standard problem with target encoding:
  ServiceArea = "SANMCA210"
  Observed churn rate in training: 30%
  Encode as: 0.30
  
  PROBLEM: Overfitting!
  The model knows 30% from same training data!

CatBoost Solution - Permutation-based Target Encoding:
  1. Randomly permute training data
  2. For each sample, encode using ONLY previous samples (in permuted order)
  
  Permuted order:   [idx0, idx1, idx2, idx3, ...]
  Churn values:     [  0,   1,    0,    1,  ...]
  
  Encoding idx2 (churn=0):
    Use samples idx0, idx1 only
    Encoded value = mean([0, 1]) = 0.5
  
  Encoding idx3 (churn=1):
    Use samples idx0, idx1, idx2 only
    Encoded value = mean([0, 1, 0]) = 0.33
  
  3. Add smoothing to further prevent overfitting:
    Encoded = (count_positive + prior × α) / (count_total + α)
    
    With α = 1.0, prior = 0.3:
    Encoded idx2 = (1 + 0.3×1) / (2 + 1) = 1.3/3 = 0.43

RESULT:
  ✅ No leakage of target information
  ✅ More stable, generalize better
  ✅ Single continuous feature replaces 747 one-hot columns!
```

### Ordered Boosting
```
Standard Gradient Boosting Problem:
  Trees are fit on data used to calculate gradients
  → Gradient estimates are biased
  → Overfitting

CatBoost Solution - Ordered Boosting:
  
  For each iteration:
    1. Permute samples randomly
    2. For position p in permuted order:
       - Calculate gradient using ONLY samples 0..p-1
       - This sample is "fresh" - not in previous trees
       - Fit tree on this fresh gradient
    3. Update predictions
  
  Like cross-validation but for gradient calculation!
  
RESULT:
  ✅ Unbiased gradient estimates
  ✅ Smoother, more stable boosting
  ✅ Better generalization to holdout set
```

### Oblivious Trees (Symmetric Trees)
```
XGBoost Tree (Asymmetric):
            [Feature A > 100]
           /            \
      [Feature B > 50]   [Feature C < 20]
      /        \         /        \
    L1        L2       L3        L4
  
  Different splits per branch (flexible but overfitting risk)

CatBoost Tree (Oblivious/Symmetric):
            [Feature A > 100]
           /            \
      [Feature B > 50]   [Feature B > 50]  ← SAME split!
      /        \         /        \
    L1        L2       L3        L4
  
  Same split condition for all branches at same depth
  
BENEFITS:
  ✅ Simpler, fewer parameters → less overfitting
  ✅ Faster training
  ✅ More interpretable
  ✅ Better generalization
```

### Feature Importance for CatBoost
```
For ServiceArea with 747 categories:
  Without CatBoost: 747 one-hot features, hard to interpret
  With CatBoost: Single "ServiceArea" feature with integrated importance
  
  Can see: "ServiceArea is 15.2% important" - clear!
  With XGBoost: Have to aggregate 747 one-hot importance → messy
```

### CatBoost Parameters
```
Critical for this dataset:

cat_features: [list of categorical column indices]
  REQUIRED - tell CatBoost which columns are categorical

one_hot_max_size: 255 (default)
  • Categories with < 255 unique → one-hot encoded
  • Categories with ≥ 255 unique → target encoded
  • ServiceArea (747) → target encoded automatically ✅

depth: 6-10
  Oblivious trees usually shallow, less overfitting
  
l2_leaf_reg: 3-10 (default: 3.0)
  Regularization for leaf weights
  
learning_rate: 0.03-0.1 (default: 0.03)
  CatBoost more stable - can use higher rates

iterations: 1000 (with early_stopping)

RECOMMENDED for this dataset:
{
    'iterations': 1000,
    'learning_rate': 0.05,
    'depth': 7,
    'l2_leaf_reg': 5,
    'random_seed': 42,
    'verbose': False,
    'early_stopping_rounds': 50,
    'loss_function': 'Logloss',
    'eval_metric': 'AUC',
    'cat_features': [indices of categorical columns]
}
```

---

## 6️⃣ XGBOOST vs CATBOOST - FINAL COMPARISON

| Aspect | XGBoost | CatBoost |
|--------|---------|----------|
| **Categorical Handling** | One-hot encoding | Target encoding + permutation |
| **Dimensionality** | 700+ features (after one-hot) | 58 features (original) |
| **Training Time** | Faster | Slower |
| **Interpretability** | Feature importance per 747 features | Single ServiceArea feature |
| **Overfitting Risk** | Higher with sparse one-hot | Lower (ordered boosting) |
| **Tree Structure** | Asymmetric (flexible) | Symmetric (oblivious) |
| **Gradient Calculation** | Direct | Permutation-based (unbiased) |
| **Best For** | Numeric-heavy datasets | Categorical-heavy datasets |
| **This Dataset** | ❌ Suboptimal | ✅ **OPTIMAL** |

---

## 7️⃣ FINAL RECOMMENDATION

### Pipeline Architecture
```
┌─────────────────────────────────────┐
│ Raw Data (51,047 × 58)              │
└────────────┬────────────────────────┘
             │
             ├─────────────────────────┬──────────────────────┐
             │                         │                      │
     ┌───────▼────────┐        ┌──────▼──────┐         ┌─────▼──────┐
     │  PREPROCESSING │        │ TRAIN-TEST  │         │ SMOTE      │
     │ • Fill Unknown │        │   SPLIT     │         │ • Balance  │
     │ • Imputation   │        │ (80-20)     │         │ • 1:1 ratio│
     │ • Winsorize    │        │             │         │            │
     │ • Transform    │        │             │         │            │
     └───────┬────────┘        └──────┬──────┘         └─────┬──────┘
             │                        │                      │
             └────────────┬───────────┴──────────────────────┘
                          │
         ┌────────────────▼────────────────┐
         │ Stratify by:                    │
         │ 1. MadeCallToRetentionTeam      │
         │ 2. HandsetPrice (optional)      │
         │ 3. ServiceArea (optional)       │
         └────────────┬───────────────────┘
                      │
         ┌────────────┴────────────┐
         │                         │
    ┌────▼──────────┐        ┌───▼──────────┐
    │ XGBoost       │        │ CatBoost     │
    │ Model A       │        │ Model B      │
    │               │        │              │
    │ • Ensemble    │        │ • Ensemble   │
    │ • With        │        │ • With       │
    │   CV          │        │   CV         │
    └────┬──────────┘        └───┬──────────┘
         │                       │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │ Ensemble Prediction   │
         │ p = 0.6×XGB +         │
         │     0.4×CAT           │
         │                       │
         │ Threshold: 0.5        │
         │ (or optimize)         │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │ Final Prediction      │
         │ CHURN or NO CHURN     │
         └───────────────────────┘
```

### Specific Recommendations
```
✅ USE CATBOOST as PRIMARY model
   • Better for categorical features
   • Automatic handling of high-cardinality (ServiceArea)
   • Ordered boosting reduce overfitting
   • Less preprocessing needed

✅ USE XGBOOST as SECONDARY model
   • Ensemble with CatBoost
   • Different learning algorithm perspective
   • Combined predictions more robust

✅ APPLY STRATIFICATION
   • Definitely: MadeCallToRetentionTeam (16.8% variance)
   • Maybe: HandsetPrice tiers (7.4% variance)
   • Optional: ServiceArea (but more complex)

✅ USE SMOTE FOR CLASS IMBALANCE
   • 2.47:1 ratio warrants balancing
   • Apply only to training set
   • Use SMOTE-ENN or SMOTETomek

✅ HANDLE OUTLIERS
   • Winsorize extreme percentages
   • Log-transform RoamingCalls, CallWaitingCalls
   • RobustScaler for scaling

✅ FEATURE ENGINEERING
   • Create usage intensity metrics
   • Engagement score from call activity
   • Equipment age as churn signal

✅ EVALUATION METRICS
   • Primary: AUC-ROC (imbalanced data)
   • Secondary: F1-score (consider both precision/recall)
   • Tertiary: Precision@top_X% (business-aligned)
```

---

## 8️⃣ NEXT STEPS

1. **Data Preparation**
   - Implement preprocessing pipeline
   - Apply SMOTE to training data

2. **Model Training**
   - Train CatBoost primary model
   - Train XGBoost secondary model
   - Both with 5-fold cross-validation

3. **Model Evaluation**
   - Compare AUC, F1, Precision-Recall curves
   - Analyze feature importance

4. **Stratification Testing**
   - If desired, train separate models per segment
   - Compare performance vs. single model

5. **Ensemble & Threshold Optimization**
   - Combine predictions
   - Optimize threshold for business metrics

6. **Deployment**
   - Generate predictions on holdout set
   - Create prediction pipeline
   - Monitor model performance in production

---

**Generated**: Telecom Churn Deep Analysis
**Dataset**: Cell2Cell Training & Holdout
**Features**: 58 (26 numeric, 23 categorical, target + ID)
**Records**: 71,047 total (51,047 train, 20,000 holdout)
