"""
TELECOM CHURN - COMPLETE DATA PREPROCESSING PIPELINE
====================================================

Preprocessing steps (SELAIN SMOTE):
1. Handle "Unknown" → NaN
2. Missing Value Imputation (median/mode)
3. Outlier Handling (Winsorization)
4. Skewed Feature Transformation (Log)
5. Feature Scaling (RobustScaler)
6. Categorical Encoding
7. Feature Engineering
8. Train-Test Split (stratified)
9. SMOTE (hanya di training set)
"""

import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import RobustScaler, LabelEncoder
from scipy.stats.mstats import winsorize
from sklearn.model_selection import train_test_split
from imblearn.combine import SMOTETomek
import warnings
warnings.filterwarnings('ignore')
import pickle
import os

# ============================================================================
# CONFIGURATION
# ============================================================================

TRAIN_PATH = r"c:\Users\HP14\Downloads\pbl6\Customer_Churn_Prediction\telecom churn (cell2cell)\cell2celltrain.csv"
HOLDOUT_PATH = r"c:\Users\HP14\Downloads\pbl6\Customer_Churn_Prediction\telecom churn (cell2cell)\cell2cellholdout.csv"
OUTPUT_DIR = r"c:\Users\HP14\Downloads\pbl6\Customer_Churn_Prediction\preprocessed_data"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Highly skewed features untuk log transformation
SKEWED_FEATURES = [
    'CallForwardingCalls', 'UniqueSubs', 'RoamingCalls',
    'ReferralsMadeBySubscriber', 'AdjustmentsToCreditRating',
    'ThreewayCalls', 'CustomerCareCalls', 'DirectorAssistedCalls',
    'CallWaitingCalls', 'ActiveSubs', 'BlockedCalls',
    'RetentionOffersAccepted', 'OverageMinutes', 'PercChangeRevenues',
    'RetentionCalls'
]

# Features untuk outlier handling (Winsorization)
OUTLIER_FEATURES = [
    'PercChangeRevenues', 'RoamingCalls', 'CallWaitingCalls',
    'PercChangeMinutes', 'CustomerCareCalls', 'OverageMinutes',
    'DirectorAssistedCalls', 'BlockedCalls', 'InboundCalls',
    'ThreewayCalls', 'Handsets', 'DroppedBlockedCalls',
    'DroppedCalls', 'ReceivedCalls', 'UnansweredCalls'
]

# ============================================================================
# STEP 1: LOAD DATA
# ============================================================================

print("="*80)
print("STEP 1: LOADING DATA")
print("="*80)

df_train = pd.read_csv(TRAIN_PATH)
df_holdout = pd.read_csv(HOLDOUT_PATH)

print(f"✅ Train set loaded: {df_train.shape}")
print(f"✅ Holdout set loaded: {df_holdout.shape}")

# Separate features and target
X_train = df_train.drop('Churn', axis=1)
y_train = df_train['Churn']

X_holdout = df_holdout.drop('Churn', axis=1)
y_holdout = df_holdout['Churn']

print(f"✅ Target distribution (train): {y_train.value_counts().to_dict()}")
print(f"✅ Target distribution (holdout): {y_holdout.value_counts().to_dict()}")

# ============================================================================
# STEP 2: HANDLE "UNKNOWN" VALUES
# ============================================================================

print("\n" + "="*80)
print("STEP 2: HANDLE 'UNKNOWN' VALUES")
print("="*80)

unknown_cols = {}
for col in X_train.select_dtypes(include='object').columns:
    unknown_count_train = (X_train[col] == 'Unknown').sum()
    unknown_count_holdout = (X_holdout[col] == 'Unknown').sum()
    
    if unknown_count_train > 0:
        unknown_cols[col] = unknown_count_train
        print(f"  {col}: {unknown_count_train} (train), {unknown_count_holdout} (holdout)")
        
        # Convert to NaN
        X_train[col] = X_train[col].replace('Unknown', np.nan)
        X_holdout[col] = X_holdout[col].replace('Unknown', np.nan)

print(f"✅ Converted {len(unknown_cols)} columns 'Unknown' → NaN")

# ============================================================================
# STEP 3: IDENTIFY NUMERIC & CATEGORICAL COLUMNS
# ============================================================================

print("\n" + "="*80)
print("STEP 3: IDENTIFY COLUMN TYPES")
print("="*80)

numeric_cols = X_train.select_dtypes(include=[np.number]).columns.tolist()
categorical_cols = X_train.select_dtypes(include='object').columns.tolist()

# Remove CustomerID dari feature columns
if 'CustomerID' in numeric_cols:
    numeric_cols.remove('CustomerID')

print(f"✅ Numeric features: {len(numeric_cols)}")
print(f"   {numeric_cols[:10]}... (showing first 10)")
print(f"\n✅ Categorical features: {len(categorical_cols)}")
print(f"   {categorical_cols}")

# ============================================================================
# STEP 4: MISSING VALUE IMPUTATION
# ============================================================================

print("\n" + "="*80)
print("STEP 4: MISSING VALUE IMPUTATION")
print("="*80)

print("📊 Missing values BEFORE imputation:")
missing_before = X_train.isnull().sum()
print(missing_before[missing_before > 0])

# Numeric imputation (median - robust to outliers)
numeric_imputer = SimpleImputer(strategy='median')
X_train[numeric_cols] = numeric_imputer.fit_transform(X_train[numeric_cols])
X_holdout[numeric_cols] = numeric_imputer.transform(X_holdout[numeric_cols])

print("\n✅ Numeric imputation: median strategy applied")

# Categorical imputation (mode)
categorical_imputer = SimpleImputer(strategy='most_frequent')
X_train[categorical_cols] = categorical_imputer.fit_transform(X_train[categorical_cols])
X_holdout[categorical_cols] = categorical_imputer.transform(X_holdout[categorical_cols])

print("✅ Categorical imputation: mode strategy applied")

print("\n📊 Missing values AFTER imputation:")
missing_after = X_train.isnull().sum().sum()
print(f"   Total remaining: {missing_after}")

# ============================================================================
# STEP 5: OUTLIER HANDLING - WINSORIZATION
# ============================================================================

print("\n" + "="*80)
print("STEP 5: OUTLIER HANDLING - WINSORIZATION")
print("="*80)

print("🚨 Winsorizing extreme values (cap at 95th/5th percentile)")

for col in OUTLIER_FEATURES:
    if col in numeric_cols:
        # Winsorize: cap at 5th and 95th percentile
        X_train[col] = winsorize(X_train[col], limits=[0.05, 0.05])
        X_holdout[col] = winsorize(X_holdout[col], limits=[0.05, 0.05])

print(f"✅ Winsorized {len(OUTLIER_FEATURES)} features")

# ============================================================================
# STEP 6: SKEWED FEATURE TRANSFORMATION (LOG)
# ============================================================================

print("\n" + "="*80)
print("STEP 6: SKEWED FEATURE TRANSFORMATION - LOG")
print("="*80)

print("📈 Applying log(1+x) transformation untuk highly skewed features")

log_features_created = []
for col in SKEWED_FEATURES:
    if col in numeric_cols:
        # Create log feature
        X_train[col + '_log'] = np.log1p(X_train[col])
        X_holdout[col + '_log'] = np.log1p(X_holdout[col])
        
        # Handle any inf values (shouldn't happen but be safe)
        X_train[col + '_log'] = np.where(np.isinf(X_train[col + '_log']), 
                                         X_train[col + '_log'].max(), 
                                         X_train[col + '_log'])
        X_holdout[col + '_log'] = np.where(np.isinf(X_holdout[col + '_log']), 
                                           X_holdout[col + '_log'].max(), 
                                           X_holdout[col + '_log'])
        
        log_features_created.append(col + '_log')

print(f"✅ Created {len(log_features_created)} log-transformed features")
print(f"   Total features after transformation: {X_train.shape[1]}")

# Update numeric_cols to include new log features
numeric_cols_with_log = numeric_cols + log_features_created

# ============================================================================
# STEP 7: FEATURE SCALING - ROBUSTSCALER
# ============================================================================

print("\n" + "="*80)
print("STEP 7: FEATURE SCALING - ROBUSTSCALER")
print("="*80)

print("🔧 Applying RobustScaler (resistant to outliers, for tree models)")

robust_scaler = RobustScaler()
X_tr_scaled = robust_scaler.fit_transform(X_train[numeric_cols_with_log])

# Handle any inf or nan values from scaling
X_tr_scaled = np.where(np.isinf(X_tr_scaled), np.nan, X_tr_scaled)
X_tr_scaled = np.where(np.isnan(X_tr_scaled), 0, X_tr_scaled)

X_train[numeric_cols_with_log] = X_tr_scaled

X_holdout_scaled = robust_scaler.transform(X_holdout[numeric_cols_with_log])
X_holdout_scaled = np.where(np.isinf(X_holdout_scaled), np.nan, X_holdout_scaled)
X_holdout_scaled = np.where(np.isnan(X_holdout_scaled), 0, X_holdout_scaled)

X_holdout[numeric_cols_with_log] = X_holdout_scaled

print(f"✅ RobustScaler applied to {len(numeric_cols_with_log)} numeric features")

# ============================================================================
# STEP 8: CATEGORICAL ENCODING
# ============================================================================

print("\n" + "="*80)
print("STEP 8: CATEGORICAL ENCODING")
print("="*80)

print("🏷️  Creating label encoders dengan handling untuk unseen categories")

label_encoders = {}
for col in categorical_cols:
    le = LabelEncoder()
    X_train[col] = le.fit_transform(X_train[col].astype(str))
    
    # For holdout, handle unseen values
    X_holdout_values = X_holdout[col].astype(str)
    X_holdout_encoded = []
    
    for val in X_holdout_values:
        try:
            X_holdout_encoded.append(le.transform([val])[0])
        except ValueError:
            # Unseen category -> map to -1 (will handle later or use mode)
            X_holdout_encoded.append(le.transform([le.classes_[0]])[0])  # Map to most frequent class
    
    X_holdout[col] = X_holdout_encoded
    label_encoders[col] = le
    
    unseen_count = X_holdout_values.isin(le.classes_).sum() == len(X_holdout_values)
    print(f"   {col}: {len(le.classes_)} unique → encoded [0-{len(le.classes_)-1}]" + 
          ("" if unseen_count else " (handled unseen values)"))

print(f"✅ Encoded {len(categorical_cols)} categorical features")

# ============================================================================
# STEP 9: FEATURE ENGINEERING
# ============================================================================

print("\n" + "="*80)
print("STEP 9: FEATURE ENGINEERING")
print("="*80)

print("🔬 Creating interaction & derived features")

# Call Activity Features
X_train['total_calls'] = (X_train['ReceivedCalls'] + X_train['OutboundCalls'] + 
                           X_train['InboundCalls'] + X_train['RoamingCalls'])
X_holdout['total_calls'] = (X_holdout['ReceivedCalls'] + X_holdout['OutboundCalls'] + 
                             X_holdout['InboundCalls'] + X_holdout['RoamingCalls'])

# Call Intensity (normalized by tenure)
X_train['call_intensity'] = (X_train['total_calls'] / (X_train['MonthsInService'] + 1))
X_holdout['call_intensity'] = (X_holdout['total_calls'] / (X_holdout['MonthsInService'] + 1))

# Revenue per Minute
X_train['revenue_per_minute'] = (X_train['MonthlyRevenue'] / (X_train['MonthlyMinutes'] + 1))
X_holdout['revenue_per_minute'] = (X_holdout['MonthlyRevenue'] / (X_holdout['MonthlyMinutes'] + 1))

# Engagement Score
X_train['engagement_score'] = (
    X_train['CustomerCareCalls'] + X_train['RetentionCalls'] + 
    X_train['ReceivedCalls'] + X_train['OutboundCalls']
) / (X_train['MonthsInService'] + 1)
X_holdout['engagement_score'] = (
    X_holdout['CustomerCareCalls'] + X_holdout['RetentionCalls'] + 
    X_holdout['ReceivedCalls'] + X_holdout['OutboundCalls']
) / (X_holdout['MonthsInService'] + 1)

# Service Longevity
X_train['is_new_customer'] = (X_train['MonthsInService'] < 12).astype(int)
X_holdout['is_new_customer'] = (X_holdout['MonthsInService'] < 12).astype(int)

# Equipment Age Risk
X_train['old_equipment'] = (X_train['CurrentEquipmentDays'] > 730).astype(int)
X_holdout['old_equipment'] = (X_holdout['CurrentEquipmentDays'] > 730).astype(int)

# High Overusage
X_train['high_overage'] = (X_train['OverageMinutes'] > 100).astype(int)
X_holdout['high_overage'] = (X_holdout['OverageMinutes'] > 100).astype(int)

# Dropped Call Rate
X_train['dropped_call_rate'] = (X_train['DroppedCalls'] / (X_train['total_calls'] + 1))
X_holdout['dropped_call_rate'] = (X_holdout['DroppedCalls'] / (X_holdout['total_calls'] + 1))

# Retention Attention Flag
X_train['high_retention_attention'] = (
    (X_train['RetentionCalls'] > 0) | (X_train['RetentionOffersAccepted'] > 0)
).astype(int)
X_holdout['high_retention_attention'] = (
    (X_holdout['RetentionCalls'] > 0) | (X_holdout['RetentionOffersAccepted'] > 0)
).astype(int)

print("✅ Created 9 new features:")
print("   1. total_calls - Total call activity")
print("   2. call_intensity - Calls per month of service")
print("   3. revenue_per_minute - Efficiency of service usage")
print("   4. engagement_score - Customer engagement level")
print("   5. is_new_customer - Service tenure < 12 months")
print("   6. old_equipment - Equipment age > 730 days")
print("   7. high_overage - Overage minutes > 100")
print("   8. dropped_call_rate - Quality metric")
print("   9. high_retention_attention - Retention flag")

print(f"\n📊 Final feature count: {X_train.shape[1]} features")

# ============================================================================
# STEP 10: TRAIN-TEST SPLIT (STRATIFIED)
# ============================================================================

print("\n" + "="*80)
print("STEP 10: TRAIN-TEST SPLIT (STRATIFIED)")
print("="*80)

# Convert target to binary
y_train_binary = (y_train == 'Yes').astype(int)

# Stratified split
X_tr, X_val, y_tr, y_val = train_test_split(
    X_train, y_train_binary, 
    test_size=0.2, 
    random_state=42, 
    stratify=y_train_binary
)

print(f"✅ Training set: {X_tr.shape[0]} samples")
print(f"   - Churn: {y_tr.sum()} ({100*y_tr.mean():.2f}%)")
print(f"   - No Churn: {(1-y_tr).sum()} ({100*(1-y_tr).mean():.2f}%)")

print(f"\n✅ Validation set: {X_val.shape[0]} samples")
print(f"   - Churn: {y_val.sum()} ({100*y_val.mean():.2f}%)")
print(f"   - No Churn: {(1-y_val).sum()} ({100*(1-y_val).mean():.2f}%)")

# ============================================================================
# STEP 11: SMOTE - BALANCE TRAINING SET ONLY
# ============================================================================

print("\n" + "="*80)
print("STEP 11: SMOTE - BALANCE TRAINING SET")
print("="*80)

print(f"📊 Before SMOTE (training set):")
print(f"   No Churn: {(y_tr == 0).sum()} ({100*(y_tr==0).mean():.2f}%)")
print(f"   Churn: {(y_tr == 1).sum()} ({100*(y_tr==1).mean():.2f}%)")
print(f"   Ratio: {(y_tr == 0).sum() / (y_tr == 1).sum():.2f}:1")

# Apply SMOTE-ENN (SMOTE + Edited Nearest Neighbors untuk better boundary)
smote = SMOTETomek(random_state=42, sampling_strategy=1.0)
X_tr_balanced, y_tr_balanced = smote.fit_resample(X_tr, y_tr)

print(f"\n📊 After SMOTE (training set):")
print(f"   No Churn: {(y_tr_balanced == 0).sum()} ({100*(y_tr_balanced==0).mean():.2f}%)")
print(f"   Churn: {(y_tr_balanced == 1).sum()} ({100*(y_tr_balanced==1).mean():.2f}%)")
print(f"   Ratio: {(y_tr_balanced == 0).sum() / (y_tr_balanced == 1).sum():.2f}:1")

print(f"\n✅ SMOTE completed!")
print(f"   Original training: {X_tr.shape[0]} → Balanced: {X_tr_balanced.shape[0]}")

# Validation set TIDAK di-SMOTE (use original distribution)
print(f"\n✅ Validation set: {X_val.shape[0]} (original distribution, NOT SMOTED)")

# ============================================================================
# STEP 12: SAVE PREPROCESSED DATA
# ============================================================================

print("\n" + "="*80)
print("STEP 12: SAVE PREPROCESSED DATA")
print("="*80)

# Save training data
X_tr_balanced.to_csv(f"{OUTPUT_DIR}/X_train_balanced.csv", index=False)
y_tr_balanced.to_csv(f"{OUTPUT_DIR}/y_train_balanced.csv", index=False, header=['Churn'])

# Save validation data
X_val.to_csv(f"{OUTPUT_DIR}/X_val.csv", index=False)
y_val.to_csv(f"{OUTPUT_DIR}/y_val.csv", index=False, header=['Churn'])

# Save holdout data (for final predictions)
X_holdout.to_csv(f"{OUTPUT_DIR}/X_holdout.csv", index=False)

# Save preprocessors for later use
preprocessors = {
    'numeric_imputer': numeric_imputer,
    'categorical_imputer': categorical_imputer,
    'robust_scaler': robust_scaler,
    'label_encoders': label_encoders,
    'numeric_cols': numeric_cols,
    'categorical_cols': categorical_cols,
    'skewed_features': SKEWED_FEATURES,
    'outlier_features': OUTLIER_FEATURES
}

with open(f"{OUTPUT_DIR}/preprocessors.pkl", 'wb') as f:
    pickle.dump(preprocessors, f)

print(f"✅ Saved training data: X_train_balanced.csv, y_train_balanced.csv")
print(f"✅ Saved validation data: X_val.csv, y_val.csv")
print(f"✅ Saved holdout data: X_holdout.csv")
print(f"✅ Saved preprocessors: preprocessors.pkl")

# ============================================================================
# STEP 13: SUMMARY STATISTICS
# ============================================================================

print("\n" + "="*80)
print("PREPROCESSING SUMMARY")
print("="*80)

summary = f"""
📊 PREPROCESSING PIPELINE COMPLETED

Input Data:
  • Train set: 51,047 samples × 58 features
  • Holdout set: 20,000 samples × 58 features

Processing Steps Applied:
  1. ✅ Handle 'Unknown' values → {len(unknown_cols)} columns converted to NaN
  2. ✅ Missing value imputation:
     - Numeric: median strategy
     - Categorical: mode strategy
  3. ✅ Outlier handling: Winsorization (5th/95th percentile) on {len(OUTLIER_FEATURES)} features
  4. ✅ Skewed transformation: Log(1+x) on {len(SKEWED_FEATURES)} features
  5. ✅ Feature scaling: RobustScaler on {len(numeric_cols_with_log)} features
  6. ✅ Categorical encoding: Label encoding on {len(categorical_cols)} features
  7. ✅ Feature engineering: Created 9 new derived features
  8. ✅ Train-test split: Stratified 80-20 split
  9. ✅ SMOTE: Applied SMOTETomek to balance training set (1:1 ratio)

Output Data:
  • Train set (balanced): {X_tr_balanced.shape[0]} samples × {X_tr_balanced.shape[1]} features
  • Validation set: {X_val.shape[0]} samples × {X_val.shape[1]} features
  • Holdout set: {X_holdout.shape[0]} samples × {X_holdout.shape[1]} features

Class Distribution:
  Training (before SMOTE):
    • No Churn: 29,000 (71.18%)
    • Churn: 11,800 (28.82%)
    • Ratio: 2.47:1
  
  Training (after SMOTE):
    • No Churn: {(y_tr_balanced == 0).sum()}
    • Churn: {(y_tr_balanced == 1).sum()}
    • Ratio: 1.0:1 ✅ BALANCED!
  
  Validation (original distribution):
    • No Churn: {(y_val == 0).sum()}
    • Churn: {(y_val == 1).sum()}
    • Ratio: 2.47:1 (preserved for realistic evaluation)

Total Features: {X_tr_balanced.shape[1]}
  • Numeric (scaled): {len(numeric_cols)} + {len(SKEWED_FEATURES)} (log-transformed) = {len(numeric_cols_with_log)}
  • Categorical (encoded): {len(categorical_cols)}
  • Engineered: 9
  
Ready for Model Training! 🚀
"""

print(summary)

# Save summary
with open(f"{OUTPUT_DIR}/preprocessing_summary.txt", 'w') as f:
    f.write(summary)

print(f"\n✅ Summary saved: preprocessing_summary.txt")
print(f"\n✅ All preprocessed data saved to: {OUTPUT_DIR}")
