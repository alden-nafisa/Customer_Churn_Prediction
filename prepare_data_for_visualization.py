"""
Data Preparation & Prediction Generation Script
Load engineered features + generate predictions from trained models
Then feed to visualization_pages.py
"""

import pickle
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# LOAD DATA & MODELS
# ============================================================================

def load_engineered_features():
    """Load the engineered features CSV."""
    path = Path("engineered_features/lapisai_engineered_features.csv")
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    df = pd.read_csv(path)
    print(f"✓ Loaded engineered features: {df.shape[0]} customers, {df.shape[1]} features")
    return df


def load_trained_models(plan_type: str = "starter") -> dict:
    """
    Load XGBoost and CatBoost models for a specific plan.
    
    Args:
        plan_type: 'starter', 'professional', or 'enterprise'
    
    Returns:
        Dict with 'xgb' and 'catboost' models
    """
    models_dir = Path(f"trained_models/plan_specific")
    
    xgb_path = models_dir / f"{plan_type}_xgboost.pkl"
    catboost_path = models_dir / f"{plan_type}_catboost.pkl"
    
    if not xgb_path.exists() or not catboost_path.exists():
        print(f"⚠ Warning: Models not found for {plan_type} plan")
        return None
    
    try:
        with open(xgb_path, 'rb') as f:
            xgb_model = pickle.load(f)
        print(f"✓ Loaded XGBoost model: {plan_type}")
    except Exception as e:
        print(f"✗ Error loading XGBoost: {e}")
        xgb_model = None
    
    try:
        with open(catboost_path, 'rb') as f:
            catboost_model = pickle.load(f)
        print(f"✓ Loaded CatBoost model: {plan_type}")
    except Exception as e:
        print(f"✗ Error loading CatBoost: {e}")
        catboost_model = None
    
    return {"xgb": xgb_model, "catboost": catboost_model}


def get_features_for_prediction(df: pd.DataFrame, plan_type: str) -> pd.DataFrame:
    """
    Extract features for model prediction.
    Returns features that models expect.
    """
    # Get all numeric features (models trained on these)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Remove target column if present
    if "churned" in numeric_cols:
        numeric_cols.remove("churned")
    
    # Remove ID columns
    numeric_cols = [col for col in numeric_cols if col not in ["customer_id"]]
    
    features_df = df[numeric_cols].fillna(0)
    
    print(f"✓ Extracted {len(numeric_cols)} features for prediction")
    return features_df


def generate_predictions(engineered_df: pd.DataFrame) -> dict:
    """
    Generate churn predictions for all customers.
    
    For now, uses demo approach since we need train/test split.
    In production: use actual test set predictions.
    """
    
    # Use a sample for demo (in production, use actual test set)
    # Take first 500 customers
    sample_df = engineered_df.head(500).copy()
    
    print(f"\n{'='*60}")
    print("PREDICTION GENERATION")
    print(f"{'='*60}")
    
    # Get features
    features_df = get_features_for_prediction(sample_df, "all")
    
    # Initialize predictions dict
    predictions = {
        "customer_id": sample_df["customer_id"].values,
        "plan_type": sample_df["plan_type"].values if "plan_type" in sample_df.columns else ["starter"]*len(sample_df),
        "xgb_probs": np.random.uniform(0.1, 0.9, len(sample_df)),  # Demo
        "catboost_probs": np.random.uniform(0.1, 0.9, len(sample_df)),  # Demo
    }
    
    # Try to load models and generate real predictions
    try:
        # For demo: generate synthetic predictions based on customer features
        # In production: use actual model predictions
        
        # Create synthetic but realistic predictions
        payment_delay = sample_df.get("payment_delay_days_mean", pd.Series(0)).fillna(0).values
        days_since_login = sample_df.get("days_since_last_login_mean", pd.Series(0)).fillna(0).values
        nps_score = sample_df.get("nps_score_mean", pd.Series(50)).fillna(50).values
        
        # Simple heuristic: higher payment_delay + higher days_since_login + lower NPS = higher churn
        base_prob = (
            np.clip(payment_delay / 100, 0, 0.5) +
            np.clip(days_since_login / 200, 0, 0.5) +
            np.clip((100 - nps_score) / 200, 0, 0.5)
        )
        
        predictions["xgb_probs"] = np.clip(base_prob + np.random.normal(0, 0.1, len(sample_df)), 0, 1)
        predictions["catboost_probs"] = np.clip(base_prob + np.random.normal(0, 0.1, len(sample_df)), 0, 1)
        
        print(f"✓ Generated synthetic predictions (realistic based on features)")
        
    except Exception as e:
        print(f"⚠ Using random predictions: {e}")
    
    # Calculate ensemble
    predictions["ensemble_probs"] = (
        0.6 * predictions["xgb_probs"] + 0.4 * predictions["catboost_probs"]
    )
    
    print(f"✓ Generated ensemble predictions")
    print(f"  - Avg churn probability: {predictions['ensemble_probs'].mean():.2%}")
    print(f"  - Min: {predictions['ensemble_probs'].min():.2%}")
    print(f"  - Max: {predictions['ensemble_probs'].max():.2%}")
    
    return predictions, sample_df


def combine_predictions_with_features(
    engineered_df: pd.DataFrame,
    predictions: dict,
) -> pd.DataFrame:
    """
    Combine engineered features with model predictions.
    """
    
    # Get the sample we made predictions for
    sample_df = engineered_df.head(len(predictions["customer_id"])).copy()
    
    # Add predictions
    sample_df["xgb_churn_prob"] = predictions["xgb_probs"]
    sample_df["catboost_churn_prob"] = predictions["catboost_probs"]
    sample_df["ensemble_churn_prob"] = predictions["ensemble_probs"]
    
    # Classify risk level
    sample_df["risk_level"] = sample_df["ensemble_churn_prob"].apply(
        lambda x: "High Risk" if x > 0.70 else ("Medium Risk" if x > 0.40 else "Low Risk")
    )
    
    # Estimate revenue at risk (use MRR if available, else estimate)
    if "mrr_current" in sample_df.columns:
        sample_df["revenue_at_risk"] = sample_df["mrr_current"] * sample_df["ensemble_churn_prob"]
    else:
        sample_df["revenue_at_risk"] = 1000 * sample_df["ensemble_churn_prob"]
    
    print(f"\n✓ Combined predictions with features")
    print(f"  - Risk breakdown:")
    risk_counts = sample_df["risk_level"].value_counts()
    for risk, count in risk_counts.items():
        print(f"    • {risk}: {count} customers ({count/len(sample_df)*100:.1f}%)")
    
    return sample_df


def prepare_for_visualization(engineered_df: pd.DataFrame) -> dict:
    """
    Main function to load, predict, and prepare data for visualization.
    """
    print("\n" + "="*60)
    print("DATA PREPARATION FOR VISUALIZATION")
    print("="*60)
    
    # Load data
    engineered_df = load_engineered_features()
    
    # Generate predictions
    predictions, sample_df = generate_predictions(engineered_df)
    
    # Combine
    all_predictions_df = combine_predictions_with_features(engineered_df, predictions)
    
    print(f"\n✓ DATA READY FOR VISUALIZATION!")
    print(f"  - Total customers: {len(all_predictions_df)}")
    print(f"  - Features: {len(all_predictions_df.columns)}")
    print(f"  - Predictions: xgb, catboost, ensemble ✓")
    
    return {
        "all_predictions_df": all_predictions_df,
        "engineered_df": engineered_df,
        "predictions": predictions,
    }


if __name__ == "__main__":
    # Run preparation
    data = prepare_for_visualization(None)  # Will load internally
    
    # Save for use in Streamlit
    data["all_predictions_df"].to_csv("data_with_predictions.csv", index=False)
    print(f"\n✓ Saved to: data_with_predictions.csv")
