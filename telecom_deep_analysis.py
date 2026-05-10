"""
TELECOM CHURN DATASET - COMPREHENSIVE DEEP ANALYSIS
====================================================
Analisis mendalam untuk memahami:
1. Jenis data kotor dan karakteristiknya
2. Preprocessing strategy yang tepat
3. Feature selection dan potential model separation
4. Class imbalance analysis untuk SMOTE
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# 1. LOAD DATA
# ============================================================================
print("="*80)
print("LOADING TELECOM CHURN DATASET")
print("="*80)

train_path = r"c:\Users\HP14\Downloads\pbl6\Customer_Churn_Prediction\telecom churn (cell2cell)\cell2celltrain.csv"
holdout_path = r"c:\Users\HP14\Downloads\pbl6\Customer_Churn_Prediction\telecom churn (cell2cell)\cell2cellholdout.csv"

df_train = pd.read_csv(train_path)
df_holdout = pd.read_csv(holdout_path)

print(f"✅ Train set loaded: {df_train.shape}")
print(f"✅ Holdout set loaded: {df_holdout.shape}")
print(f"✅ Total features: {df_train.shape[1]}")

# ============================================================================
# 2. JENIS DATA KOTOR - MISSING VALUES ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("2. MISSING VALUES ANALYSIS - JENIS DATA KOTOR")
print("="*80)

# Check missing values
missing_train = df_train.isnull().sum()
missing_train_pct = (missing_train / len(df_train)) * 100
missing_df = pd.DataFrame({
    'Column': missing_train.index,
    'Missing_Count': missing_train.values,
    'Missing_Percentage': missing_train_pct.values
}).sort_values('Missing_Count', ascending=False)

print("\n📊 TRAIN SET - Missing Values (Top 20):")
print(missing_df[missing_df['Missing_Count'] > 0].head(20).to_string(index=False))

# Check for 'Unknown' values (treated as missing)
print("\n📊 'Unknown' Values in Categorical Columns (Train Set):")
for col in df_train.select_dtypes(include='object').columns:
    unknown_count = (df_train[col] == 'Unknown').sum()
    if unknown_count > 0:
        unknown_pct = (unknown_count / len(df_train)) * 100
        print(f"  {col}: {unknown_count} ({unknown_pct:.2f}%)")

# ============================================================================
# 3. DATA TYPE & FORMAT ISSUES
# ============================================================================
print("\n" + "="*80)
print("3. DATA TYPE & FORMAT ISSUES")
print("="*80)

print("\n📋 Data Types Distribution:")
dtype_counts = df_train.dtypes.value_counts()
for dtype, count in dtype_counts.items():
    print(f"  {dtype}: {count} columns")

print("\n🔍 Sample Data Quality Issues:")
print("\nChurn Column (Target):")
print(f"  Values: {df_train['Churn'].value_counts().to_dict()}")
print(f"  Nulls: {df_train['Churn'].isnull().sum()}")
print(f"  Type: {df_train['Churn'].dtype}")

# Check for mixed data types
print("\n🔍 Columns with Mixed/Suspicious Values:")
ageHH1_vals = df_train['AgeHH1'].dropna().unique()
ageHH2_vals = df_train['AgeHH2'].dropna().unique()
print(f"  AgeHH1 unique values (sample 20): {list(ageHH1_vals[:20])}")
print(f"  AgeHH2 unique values (sample 20): {list(ageHH2_vals[:20])}")
print(f"  CreditRating unique values: {sorted(df_train['CreditRating'].dropna().unique())}")
print(f"  Occupation unique values (count): {df_train['Occupation'].nunique()}")

# ============================================================================
# 4. OUTLIERS ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("4. OUTLIERS ANALYSIS")
print("="*80)

numeric_cols = df_train.select_dtypes(include=[np.number]).columns
print(f"\n📈 Numeric columns: {len(numeric_cols)}")

# Calculate outliers using IQR method
outlier_summary = []
for col in numeric_cols:
    if col != 'CustomerID':
        Q1 = df_train[col].quantile(0.25)
        Q3 = df_train[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = ((df_train[col] < lower_bound) | (df_train[col] > upper_bound)).sum()
        outlier_pct = (outliers / len(df_train)) * 100
        
        if outliers > 0:
            outlier_summary.append({
                'Column': col,
                'Outliers_Count': outliers,
                'Outliers_Percentage': outlier_pct,
                'Min': df_train[col].min(),
                'Max': df_train[col].max(),
                'Q1': Q1,
                'Q3': Q3
            })

outlier_df = pd.DataFrame(outlier_summary).sort_values('Outliers_Count', ascending=False)
print("\n🚨 TOP COLUMNS WITH OUTLIERS:")
print(outlier_df.head(15).to_string(index=False))

# ============================================================================
# 5. CLASS IMBALANCE ANALYSIS (FOR SMOTE)
# ============================================================================
print("\n" + "="*80)
print("5. CLASS IMBALANCE ANALYSIS (FOR SMOTE)")
print("="*80)

churn_dist = df_train['Churn'].value_counts()
churn_pct = df_train['Churn'].value_counts(normalize=True) * 100

print(f"\n📊 Churn Distribution (Train Set):")
for label, count in churn_dist.items():
    pct = (count / len(df_train)) * 100
    print(f"  {label}: {count:,} ({pct:.2f}%)")

imbalance_ratio = churn_dist['No'] / churn_dist['Yes']
print(f"\n⚠️  Imbalance Ratio (No/Yes): {imbalance_ratio:.2f}:1")
print(f"✅ SMOTE NEEDED: {'Yes' if imbalance_ratio > 1.5 else 'No'}")

# ============================================================================
# 6. POTENTIAL FEATURE SEPARATORS (STRATIFICATION)
# ============================================================================
print("\n" + "="*80)
print("6. POTENTIAL FEATURE SEPARATORS FOR MODEL STRATIFICATION")
print("="*80)

# Check categorical features that might have distinct subgroups
categorical_cols = df_train.select_dtypes(include='object').columns
print(f"\n🏷️  Categorical Columns for Potential Stratification: {len(categorical_cols)}")

stratification_candidates = []
for col in categorical_cols:
    if col != 'CustomerID' and col != 'Churn':
        unique_count = df_train[col].nunique()
        
        # Check if this column shows different churn rates
        try:
            churn_by_cat = df_train.groupby(col)['Churn'].apply(lambda x: (x == 'Yes').sum() / len(x) * 100)
            churn_std = churn_by_cat.std()
            
            stratification_candidates.append({
                'Column': col,
                'Unique_Values': unique_count,
                'Churn_Rate_Std': churn_std,
                'Min_Churn_Rate': churn_by_cat.min(),
                'Max_Churn_Rate': churn_by_cat.max(),
                'Churn_Variance': churn_by_cat.max() - churn_by_cat.min()
            })
        except:
            pass

strat_df = pd.DataFrame(stratification_candidates).sort_values('Churn_Variance', ascending=False)
print("\n🎯 TOP CANDIDATES FOR MODEL STRATIFICATION (by Churn Rate Variance):")
print(strat_df.head(10).to_string(index=False))

# ============================================================================
# 7. FEATURE STATISTICS & DISTRIBUTION
# ============================================================================
print("\n" + "="*80)
print("7. FEATURE STATISTICS - SKEWNESS & KURTOSIS")
print("="*80)

feature_stats = []
for col in numeric_cols:
    if col != 'CustomerID':
        skewness = df_train[col].skew()
        kurtosis = df_train[col].kurtosis()
        
        feature_stats.append({
            'Feature': col,
            'Mean': df_train[col].mean(),
            'Std': df_train[col].std(),
            'Skewness': skewness,
            'Kurtosis': kurtosis,
            'Highly_Skewed': 'Yes' if abs(skewness) > 1 else 'No'
        })

stats_df = pd.DataFrame(feature_stats).sort_values('Skewness', key=abs, ascending=False)
print("\n📈 HIGHLY SKEWED FEATURES (|Skewness| > 1):")
highly_skewed = stats_df[stats_df['Highly_Skewed'] == 'Yes']
print(highly_skewed[['Feature', 'Skewness', 'Kurtosis']].head(15).to_string(index=False))

# ============================================================================
# 8. CORRELATION ANALYSIS FOR FEATURE SELECTION
# ============================================================================
print("\n" + "="*80)
print("8. FEATURE CORRELATION ANALYSIS")
print("="*80)

# Create numeric version for correlation (encode categorical)
df_numeric = df_train.copy()

# Encode Churn for correlation
churn_encoded = (df_numeric['Churn'] == 'Yes').astype(int)

# Encode categorical variables
le_dict = {}
for col in df_numeric.select_dtypes(include='object').columns:
    if col not in ['CustomerID', 'Churn']:
        le = LabelEncoder()
        df_numeric[col] = le.fit_transform(df_numeric[col].astype(str))
        le_dict[col] = le

df_numeric['Churn'] = churn_encoded

# Calculate correlations with Churn
correlations = df_numeric.corr()['Churn'].drop('Churn').sort_values(ascending=False)

print("\n🔗 TOP 15 FEATURES CORRELATED WITH CHURN (Positive):")
print(correlations.head(15).to_string())

print("\n🔗 TOP 15 FEATURES CORRELATED WITH CHURN (Negative):")
print(correlations.tail(15).to_string())

# ============================================================================
# 9. DUPLICATE VALUES ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("9. DUPLICATE VALUES ANALYSIS")
print("="*80)

exact_duplicates = df_train.duplicated().sum()
print(f"\n📋 Exact Duplicates: {exact_duplicates}")

if exact_duplicates > 0:
    dup_rows = df_train[df_train.duplicated(keep=False)].sort_values(by=list(df_train.columns))
    print(f"📋 Sample duplicate rows:")
    print(dup_rows.head(10).to_string())

# ============================================================================
# 10. SUMMARY & RECOMMENDATIONS
# ============================================================================
print("\n" + "="*80)
print("10. DATA QUALITY SUMMARY & PREPROCESSING RECOMMENDATIONS")
print("="*80)

summary = f"""
📊 DATASET QUALITY METRICS:
  • Total Records: {len(df_train):,}
  • Total Features: {len(df_train.columns)}
  • Missing Values: {missing_train.sum():,} ({(missing_train.sum() / (len(df_train) * len(df_train.columns)) * 100):.2f}%)
  • Exact Duplicates: {exact_duplicates}
  • Outliers (IQR method): {sum([o['Outliers_Count'] for o in outlier_summary]):,}
  • Class Imbalance Ratio: {imbalance_ratio:.2f}:1

🔧 RECOMMENDED PREPROCESSING STEPS:
  1. ✅ Handle Missing Values:
     - Numeric features: Use median imputation (robust to outliers)
     - Categorical features: Use mode imputation or 'Unknown' category
     - Features with >30% missing: Consider dropping
  
  2. ✅ Fix Data Type Issues:
     - Convert 'Unknown' to proper NaN before imputation
     - Ensure consistent categorical encoding
  
  3. ✅ Handle Outliers:
     - Use Robust Scaler (handles outliers better than StandardScaler)
     - Winsorization for extreme values (cap at 95th/5th percentile)
     - Log transformation for highly skewed features
  
  4. ✅ Remove/Handle Duplicates:
     - Remove exact duplicates
     - Investigate near-duplicates
  
  5. ✅ Feature Scaling:
     - StandardScaler for normally distributed features
     - RobustScaler for features with outliers
     - MinMaxScaler for tree-based models (optional, but helps with SHAP)
  
  6. ✅ Class Imbalance (SMOTE):
     - Apply SMOTE on training set ONLY (after train-test split)
     - Imbalance ratio suggests SMOTE is beneficial
     - Use SMOTE-ENN or SMOTETomek for better boundary definition

🎯 MODEL STRATIFICATION OPPORTUNITIES:
  • Service Area (ServiceArea): Shows significant churn rate variance
  • Income Group: Likely different churn patterns by income
  • Occupation: Possible stratification candidate
  • Handset Models: Could indicate customer segments

💡 FEATURE SELECTION STRATEGY:
  • Use correlation analysis (above) to identify top features
  • Apply feature importance from tree models
  • Consider domain knowledge (retention features are likely important)
  • Use recursive feature elimination or permutation importance
"""

print(summary)

# Save analysis results
print("\n" + "="*80)
print("SAVING ANALYSIS RESULTS...")
print("="*80)

# Save correlation results
correlations.to_csv(r'c:\Users\HP14\Downloads\pbl6\Customer_Churn_Prediction\analysis_results\churn_correlations.csv')
print("✅ Saved: churn_correlations.csv")

# Save outliers
outlier_df.to_csv(r'c:\Users\HP14\Downloads\pbl6\Customer_Churn_Prediction\analysis_results\outliers_analysis.csv', index=False)
print("✅ Saved: outliers_analysis.csv")

# Save stratification candidates
strat_df.to_csv(r'c:\Users\HP14\Downloads\pbl6\Customer_Churn_Prediction\analysis_results\stratification_candidates.csv', index=False)
print("✅ Saved: stratification_candidates.csv")

# Save feature stats
stats_df.to_csv(r'c:\Users\HP14\Downloads\pbl6\Customer_Churn_Prediction\analysis_results\feature_statistics.csv', index=False)
print("✅ Saved: feature_statistics.csv")

print("\n✅ ANALYSIS COMPLETE!")
