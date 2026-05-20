"""
LAPISAi - Integrated Customer Churn + NLP Analytics Dashboard
Mengintegrasikan hasil model churn dan analisis NLP dalam satu aplikasi.
"""

import json
import os
import pickle
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ========== CONFIG ==========
PROJECT_ROOT = Path(__file__).resolve().parent
st.set_page_config(
    page_title="LAPISAi Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ========== PATHS ==========
ENGINEERED_FEATURES_PATH = PROJECT_ROOT / "engineered_features" / "lapisai_engineered_features.csv"
ENSEMBLE_PREDICTIONS_PATH = PROJECT_ROOT / "model_results" / "ensemble_predictions.csv"
EVALUATION_METRICS_PATH = PROJECT_ROOT / "model_results" / "evaluation_metrics.csv"
TRAINED_MODELS_DIR = PROJECT_ROOT / "trained_models" / "plan_specific"
NLP_ARTIFACTS_DIR = PROJECT_ROOT / "artifacts" / "nlp"
CHAT_DATA_PATH = PROJECT_ROOT / "youtube_chat_5_menit_cleaned.csv"

# ========== LOAD DATA ==========
@st.cache_data
def load_engineered_features():
    """Load engineered features for customer analysis."""
    if not ENGINEERED_FEATURES_PATH.exists():
        return None
    return pd.read_csv(ENGINEERED_FEATURES_PATH)

@st.cache_data
def load_ensemble_predictions():
    """Load ensemble model predictions."""
    if not ENSEMBLE_PREDICTIONS_PATH.exists():
        return None
    return pd.read_csv(ENSEMBLE_PREDICTIONS_PATH)

@st.cache_data
def load_evaluation_metrics():
    """Load model evaluation metrics."""
    if not EVALUATION_METRICS_PATH.exists():
        return None
    return pd.read_csv(EVALUATION_METRICS_PATH)

@st.cache_data
def load_chat_data():
    """Load YouTube chat data for sentiment analysis."""
    if not CHAT_DATA_PATH.exists():
        return None
    return pd.read_csv(CHAT_DATA_PATH)

def load_trained_models(plan_type="Starter"):
    """Load trained XGBoost and CatBoost models for specified plan."""
    models = {}
    
    xgb_path = TRAINED_MODELS_DIR / f"{plan_type.lower()}_xgboost.pkl"
    cat_path = TRAINED_MODELS_DIR / f"{plan_type.lower()}_catboost.pkl"
    
    if xgb_path.exists():
        with open(xgb_path, 'rb') as f:
            models['xgboost'] = pickle.load(f)
    
    if cat_path.exists():
        with open(cat_path, 'rb') as f:
            models['catboost'] = pickle.load(f)
    
    return models

def load_preprocessing_info():
    """Load preprocessing info to get actual features used in training"""
    import ast
    preprocess_dir = PROJECT_ROOT / "preprocessed_data"
    
    info_dict = {}
    for plan in ['starter', 'professional', 'enterprise']:
        info_file = preprocess_dir / f'{plan}_preprocessing_info.json'
        if info_file.exists():
            try:
                with open(info_file, 'r') as f:
                    data = json.load(f)
                    # Parse string representation of list back to actual list
                    features_str = data.get('features_selected', '[]')
                    features = ast.literal_eval(features_str)
                    capitalized_plan = plan.capitalize()
                    info_dict[capitalized_plan] = features
                    print(f"✓ Loaded {len(features)} features for {capitalized_plan}")
            except Exception as e:
                print(f"Error loading {plan} features: {e}")
        else:
            print(f"⚠️ File not found: {info_file}")
    
    print(f"Available plans in info_dict: {list(info_dict.keys())}")
    return info_dict

def get_training_features(plan_type: str) -> list:
    """Get the exact features used during training for a plan"""
    plan_type_clean = str(plan_type).strip()
    print(f"🔍 Looking for features for plan: '{plan_type_clean}'")
    
    info = load_preprocessing_info()
    features = info.get(plan_type_clean, [])
    
    if not features:
        print(f"⚠️ No exact match for plan: {plan_type_clean}")
        print(f"Available plans: {list(info.keys())}")
        # Try case-insensitive match
        for key in info.keys():
            if key.lower() == plan_type_clean.lower():
                features = info[key]
                print(f"✓ Found match with different case: {key}")
                break
    
    # Fallback: if still no features, return hardcoded list
    if not features:
        print(f"⚠️ Using hardcoded features as fallback")
        # These are common across all plans from preprocessing pipeline
        features = [
            'days_since_last_login',
            'avg_monthly_usage_hours',
            'payment_delay_days_mean',
            'critical_ticket_ratio',
            'avg_nps_score',
            'revenue_at_risk',
            'payment_consistency_score',
            'unresolved_ratio',
            'total_tickets',
            'mrr_current',
            'tenure_days',
            'usage_per_user',
            'feature_adoption_pct_mean',
            'total_users',
        ]
    else:
        print(f"✓ Found {len(features)} features for {plan_type_clean}")
    
    return features

def safe_get(row, *column_names, default=None):
    """Safely get value from row, trying multiple column names."""
    for col in column_names:
        if col in row.index and pd.notna(row[col]):
            return row[col]
    return default if default is not None else "N/A"

# ========== DASHBOARD PAGES ==========
def show_dashboard_page():
    """Main dashboard with churn and NLP overview."""
    st.title("🚀 LAPISAi - Advanced Analytics Dashboard")
    st.markdown("**AI-Powered Analytics Platform** — Customer Churn Prediction + NLP Sentiment Analysis")
    
    # Load data
    engineered_df = load_engineered_features()
    ensemble_df = load_ensemble_predictions()
    eval_metrics = load_evaluation_metrics()
    
    if engineered_df is None or ensemble_df is None:
        st.error("❌ Missing required data files. Please run the pipeline first.")
        st.info("""
        **Setup required:**
        1. `python 01_feature_engineering.py` - Generate engineered features
        2. `python 03_model_training_per_plan.py` - Train models (if not done)
        3. `python 04_ensemble_predictions.py` - Generate predictions
        """)
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Customers", len(engineered_df))
    
    with col2:
        if 'actual' in ensemble_df.columns:
            churn_count = ensemble_df['actual'].sum()
            st.metric("⚠️ Churned Customers", int(churn_count))
    
    with col3:
        if 'ensemble_proba' in ensemble_df.columns:
            high_risk = (ensemble_df['ensemble_proba'] > 0.5).sum()
            st.metric("🔴 High Risk (>50%)", int(high_risk))
    
    with col4:
        st.metric("🎯 Plans", engineered_df['plan_type'].nunique())
    
    st.divider()
    
    # Churn distribution by plan
    col1, col2 = st.columns(2)
    
    with col1:
        plan_churn = engineered_df.groupby('plan_type').size()
        fig = px.bar(
            x=plan_churn.index,
            y=plan_churn.values,
            title="Customers by Plan Type",
            labels={"x": "Plan Type", "y": "Count"},
            color=plan_churn.index,
            color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'ensemble_proba' in ensemble_df.columns:
            risk_dist = pd.cut(ensemble_df['ensemble_proba'], bins=[0, 0.25, 0.5, 0.75, 1.0], 
                               labels=['Low', 'Medium', 'High', 'Very High'])
            fig = px.pie(
                values=risk_dist.value_counts().values,
                names=risk_dist.value_counts().index,
                title="Risk Level Distribution",
                color_discrete_sequence=['#2ecc71', '#f39c12', '#e74c3c', '#c0392b']
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Ensemble predictions distribution
    if 'ensemble_proba' in ensemble_df.columns:
        st.subheader("📈 Ensemble Prediction Distribution")
        fig = px.histogram(
            ensemble_df['ensemble_proba'],
            nbins=50,
            title="Churn Probability Distribution",
            labels={"value": "Probability", "count": "Customers"}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Model performance
    if eval_metrics is not None and len(eval_metrics) > 0:
        st.subheader("📊 Model Evaluation")
        st.dataframe(eval_metrics, use_container_width=True)

def show_churn_prediction_page():
    """Detailed churn prediction analysis - Individual + Overall + Model Evaluation."""
    st.title("💼 Customer Churn Analysis & Prediction")
    
    engineered_df = load_engineered_features()
    ensemble_df = load_ensemble_predictions()
    
    if engineered_df is None or ensemble_df is None:
        st.error("❌ Missing data. Please run pipeline first.")
        return
    
    # Add index to ensemble_df for alignment
    ensemble_df = ensemble_df.reset_index(drop=True)
    engineered_df = engineered_df.reset_index(drop=True)
    
    # Use 'plan' column from ensemble, merge with engineered data
    merged_df = pd.concat([
        engineered_df,
        ensemble_df[['plan', 'actual', 'xgb_proba', 'cat_proba', 'ensemble_proba', 'ensemble_prediction']]
    ], axis=1)
    
    # Ensure plan column is string and drop NaN
    merged_df['plan'] = merged_df['plan'].astype(str)
    merged_df = merged_df[merged_df['plan'] != 'nan'].copy()
    
    # Filter by plan
    plans = sorted(merged_df['plan'].dropna().unique())
    if not plans:
        st.error("No valid plan data found")
        return
    
    # === TAB 1: INDIVIDUAL CUSTOMER ANALYSIS ===
    tab1, tab2, tab3 = st.tabs(["👤 Individual Analysis", "📊 Overall Analysis", "🎯 Model Evaluation"])
    
    with tab1:
        st.subheader("🔍 Individual Customer Risk Assessment")
        
        # Explainer section
        with st.expander("ℹ️ How to Use This Section"):
            st.markdown("""
            **Cara menggunakan:**
            1. Pilih Plan Type dan Customer ID
            2. Klik **FETCH DATA** untuk load customer data dan auto-populate form
            3. (Optional) Edit feature values untuk "what-if" scenario analysis
            4. Pilih model: XGBoost, CatBoost, atau Ensemble
            5. Klik **RUN PREDICTION** untuk hasil custom prediction
            
            **Interpretasi Risk Score:**
            - 🟢 **LOW (<30%)** - Customer stabil, lanjutkan service yang baik
            - 🟡 **MEDIUM (30-50%)** - Perlu monitoring regular
            - 🟠 **HIGH (50-70%)** - Immediate proactive engagement diperlukan
            - 🔴 **VERY HIGH (>70%)** - Contact immediately dengan retention offer
            
            **Model Performance Rating:**
            - ✅ **TRUE POSITIVE**: Predicted churn, actually churned → Model working well
            - ✅ **TRUE NEGATIVE**: Predicted retain, actually retained → Model working well
            - ❌ **FALSE NEGATIVE**: Predicted retain, but actually churned → Missed opportunity
            - ⚠️ **FALSE POSITIVE**: Predicted churn, but actually retained → Review features
            """)
        
        # Plan and Customer ID selector in one row
        col1, col2, col3 = st.columns([2, 3, 1])
        
        with col1:
            plan = st.selectbox(
                "📋 Plan Type", 
                plans,
                key="plan_selector_tab1"
            )
        
        plan_df = merged_df[merged_df['plan'] == plan].copy()
        available_customer_ids = sorted(plan_df['customer_id'].astype(str).unique().tolist())
        
        with col2:
            customer_id = st.selectbox(
                "🆔 Customer ID", 
                available_customer_ids,
                key="customer_selector_tab1",
                format_func=lambda x: f"Customer {x}"
            )
        
        with col3:
            fetch_btn = st.button("🔄 FETCH", key="fetch_button_tab1")
        
        # Display summary for selected plan
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total Customers", len(plan_df))
        with col2:
            actual_churn = plan_df['actual'].sum() if 'actual' in plan_df.columns else 0
            st.metric("⚠️ Actual Churned", int(actual_churn))
        with col3:
            predicted_high_risk = (plan_df['ensemble_proba'] > 0.5).sum()
            st.metric("🔴 High Risk (>50%)", int(predicted_high_risk))
        with col4:
            if len(plan_df) > 0:
                accuracy_pct = (plan_df['ensemble_prediction'] == plan_df['actual']).sum() / len(plan_df) * 100
                st.metric("✅ Model Accuracy", f"{accuracy_pct:.1f}%")
        
        st.divider()
        
        # Initialize session state for form data
        if 'fetched_customer_id' not in st.session_state:
            st.session_state.fetched_customer_id = None
        if 'form_data' not in st.session_state:
            st.session_state.form_data = {}
        if 'full_feature_row' not in st.session_state:
            st.session_state.full_feature_row = None
        
        # Fetch customer data
        if fetch_btn and customer_id:
            customer = plan_df[plan_df['customer_id'].astype(str) == customer_id]
            if len(customer) > 0:
                row = customer.iloc[0]
                st.session_state.fetched_customer_id = customer_id
                st.session_state.full_feature_row = row.copy()  # Store complete feature row
                
                # Store original form data (editable features only)
                st.session_state.form_data = {
                    'customer_id': customer_id,
                    'plan_type': row.get('plan', 'N/A'),
                    'actual_status': int(row.get('actual', 0)),
                    'actual_status_text': "YES (Churned)" if row.get('actual', 0) else "NO (Retained)",
                    'payment_delay_days': float(row.get('payment_delay_days_mean', 0)),
                    'days_since_login': float(row.get('days_since_last_login', 0)),
                    'avg_nps_score': float(row.get('avg_nps_score', 0)),
                    'feature_adoption_pct': float(row.get('feature_adoption_pct_mean', 0)),
                    'annual_value': float(row.get('annual_value', 0)),
                    'avg_monthly_usage_hours': float(row.get('avg_monthly_usage_hours', 0)),
                    'total_tickets': float(row.get('total_tickets', 0)),
                    'payment_health_score': float(row.get('payment_health_score', 0)),
                }
                st.success(f"✅ Loaded customer data: {customer_id}")
        
        # Display fetched data and form
        if st.session_state.fetched_customer_id:
            form_data = st.session_state.form_data
            
            # Customer info banner
            st.markdown(f"""
            <div style='background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px;'>
                <b>Customer ID:</b> {form_data['customer_id']} | 
                <b>Plan:</b> {form_data['plan_type']} | 
                <b>Actual Status:</b> {form_data['actual_status_text']}
            </div>
            """, unsafe_allow_html=True)
            
            # Feature edit form
            st.subheader("📝 Feature Input Form (Edit for What-If Scenarios)")
            
            with st.form(key="prediction_form"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    form_data['payment_delay_days'] = st.number_input(
                        "Payment Delay Days",
                        min_value=0.0, value=form_data['payment_delay_days'], step=1.0,
                        help="Rata-rata hari keterlambatan pembayaran"
                    )
                    form_data['days_since_login'] = st.number_input(
                        "Days Since Last Login",
                        min_value=0.0, value=form_data['days_since_login'], step=1.0,
                        help="Berapa hari sejak login terakhir"
                    )
                    form_data['avg_nps_score'] = st.number_input(
                        "Avg NPS Score",
                        min_value=0.0, max_value=10.0, value=form_data['avg_nps_score'], step=0.1,
                        help="Net Promoter Score (0-10)"
                    )
                
                with col2:
                    form_data['feature_adoption_pct'] = st.number_input(
                        "Feature Adoption %",
                        min_value=0.0, max_value=100.0, value=form_data['feature_adoption_pct'], step=1.0,
                        help="Persentase fitur yang digunakan"
                    )
                    form_data['annual_value'] = st.number_input(
                        "Annual Value ($)",
                        min_value=0.0, value=form_data['annual_value'], step=10.0,
                        help="Nilai kontrak tahunan"
                    )
                    form_data['avg_monthly_usage_hours'] = st.number_input(
                        "Monthly Usage Hours",
                        min_value=0.0, value=form_data['avg_monthly_usage_hours'], step=0.1,
                        help="Rata-rata jam penggunaan per bulan"
                    )
                
                with col3:
                    form_data['total_tickets'] = st.number_input(
                        "Support Tickets (90d)",
                        min_value=0.0, value=form_data['total_tickets'], step=1.0,
                        help="Total support tickets dalam 90 hari terakhir"
                    )
                    form_data['payment_health_score'] = st.number_input(
                        "Payment Health Score",
                        min_value=0.0, max_value=100.0, value=form_data['payment_health_score'], step=1.0,
                        help="Skor kesehatan pembayaran (0-100)"
                    )
                
                st.divider()
                
                # Model selection
                st.subheader("🤖 Model Selection for Prediction")
                model_choice = st.radio(
                    "Select which model(s) to use:",
                    options=["XGBoost Only", "CatBoost Only", "Ensemble (Recommended)"],
                    horizontal=True,
                    help="Ensemble menggunakan weighted average dari XGBoost dan CatBoost"
                )
                
                st.divider()
                
                # Submit button
                submit_btn = st.form_submit_button("▶️ RUN PREDICTION", use_container_width=True)
        
        # Run prediction if form submitted
        if st.session_state.fetched_customer_id and submit_btn:
            form_data = st.session_state.form_data
            full_row = st.session_state.full_feature_row
            final_pred = None  # Initialize before use
            model_name = None
            
            if full_row is None:
                st.error("❌ Error: Customer data not loaded. Please fetch data again.")
            else:
                full_row = full_row.copy()
                
                try:
                    # Load models
                    models = load_trained_models(form_data['plan_type'])
                    
                    if not models:
                        st.error(f"❌ Models not found for plan: {form_data['plan_type']}")
                    else:
                        # Apply user edits to full feature row
                        full_row['payment_delay_days_mean'] = form_data['payment_delay_days']
                        full_row['days_since_last_login'] = form_data['days_since_login']
                        full_row['avg_nps_score'] = form_data['avg_nps_score']
                        full_row['feature_adoption_pct_mean'] = form_data['feature_adoption_pct']
                        full_row['annual_value'] = form_data['annual_value']
                        full_row['avg_monthly_usage_hours'] = form_data['avg_monthly_usage_hours']
                        full_row['total_tickets'] = form_data['total_tickets']
                        full_row['payment_health_score'] = form_data['payment_health_score']
                        
                        # Get EXACT features used during training for this plan
                        training_features = get_training_features(form_data['plan_type'])
                        
                        if not training_features:
                            st.error(f"❌ Could not load training features for plan: {form_data['plan_type']}")
                        else:
                            # Create feature vector using ONLY training features
                            try:
                                feature_vector = full_row[training_features].fillna(0).values.reshape(1, -1)
                            except Exception as e:
                                st.error(f"❌ Error preparing features: {str(e)}")
                                feature_vector = None
                            
                            if feature_vector is not None:
                                # Get predictions based on model choice
                                predictions = {}
                                error_details = []
                                
                                if 'xgboost' in models and model_choice in ["XGBoost Only", "Ensemble (Recommended)"]:
                                    try:
                                        xgb_pred = models['xgboost'].predict_proba(feature_vector)[0][1]
                                        predictions['xgboost'] = xgb_pred
                                    except Exception as e:
                                        error_details.append(f"XGBoost: {str(e)[:100]}")
                                
                                if 'catboost' in models and model_choice in ["CatBoost Only", "Ensemble (Recommended)"]:
                                    try:
                                        cat_pred = models['catboost'].predict_proba(feature_vector)[0][1]
                                        predictions['catboost'] = cat_pred
                                    except Exception as e:
                                        error_details.append(f"CatBoost: {str(e)[:100]}")
                                
                                # Calculate ensemble or use single model
                                if model_choice == "XGBoost Only" and 'xgboost' in predictions:
                                    final_pred = predictions['xgboost']
                                    model_name = "XGBoost"
                                elif model_choice == "CatBoost Only" and 'catboost' in predictions:
                                    final_pred = predictions['catboost']
                                    model_name = "CatBoost"
                                else:  # Ensemble
                                    if 'xgboost' in predictions and 'catboost' in predictions:
                                        final_pred = 0.6 * predictions['xgboost'] + 0.4 * predictions['catboost']
                                        model_name = "Ensemble"
                                    elif 'xgboost' in predictions:
                                        final_pred = predictions['xgboost']
                                        model_name = "XGBoost"
                                    elif 'catboost' in predictions:
                                        final_pred = predictions['catboost']
                                        model_name = "CatBoost"
                                    else:
                                        if error_details:
                                            st.error(f"❌ Prediction failed:\n" + "\n".join(error_details))
                                        else:
                                            st.error("❌ No valid predictions could be generated")
                                        final_pred = None
                    
                    if final_pred is not None:
                        # Display prediction results
                        st.divider()
                        st.subheader("📊 Prediction Results")
                        
                        # Risk indicator
                        if final_pred > 0.7:
                            risk_color = "🔴 VERY HIGH"
                            risk_bg = "#ffebee"
                            risk_level = "VERY HIGH (>70%)"
                        elif final_pred > 0.5:
                            risk_color = "🟠 HIGH"
                            risk_bg = "#fff3e0"
                            risk_level = "HIGH (50-70%)"
                        elif final_pred > 0.3:
                            risk_color = "🟡 MEDIUM"
                            risk_bg = "#fffde7"
                            risk_level = "MEDIUM (30-50%)"
                        else:
                            risk_color = "🟢 LOW"
                            risk_bg = "#e8f5e9"
                            risk_level = "LOW (<30%)"
                        
                        st.markdown(f"""
                        <div style='background-color: {risk_bg}; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px;'>
                            <h2 style='margin: 0; color: black;'>{risk_color}</h2>
                            <h3 style='margin: 5px 0; color: black;'>{final_pred:.1%} Churn Probability</h3>
                            <p style='margin: 5px 0; font-size: 12px; color: black;'>Model: {model_name}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Model performance evaluation
                        st.subheader("📋 Model Performance Rating")
                        
                        actual_status = form_data['actual_status']
                        predicted_churn = 1 if final_pred > 0.25 else 0  # threshold 0.25
                        
                        if actual_status == 1 and predicted_churn == 1:
                            rating = "✅ TRUE POSITIVE"
                            explanation = "Model correctly identified this customer as churned. This is a good prediction - the model is working properly."
                            bg_color = "#c8e6c9"
                        elif actual_status == 0 and predicted_churn == 0:
                            rating = "✅ TRUE NEGATIVE"
                            explanation = "Model correctly predicted this customer will be retained. Excellent prediction."
                            bg_color = "#c8e6c9"
                        elif actual_status == 1 and predicted_churn == 0:
                            rating = "❌ FALSE NEGATIVE"
                            explanation = "Model missed this churn case! The customer actually churned but model predicted retain. Investigate why - model needs improvement."
                            bg_color = "#ffcdd2"
                        else:  # actual_status == 0 and predicted_churn == 1
                            rating = "⚠️ FALSE POSITIVE"
                            explanation = "Model predicted churn but customer actually retained. Could be false alarm, but review the high-risk features below to verify."
                            bg_color = "#ffe0b2"
                        
                        st.markdown(f"""
                        <div style='background-color: {bg_color}; padding: 15px; border-radius: 8px;'>
                            <b style='color: black;'>Prediction Rating: {rating}</b><br/>
                            <p style='color: black;'>{explanation}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Display all model predictions for comparison
                        if len(predictions) > 1:
                            st.subheader("🔄 Model Comparison")
                            col1, col2 = st.columns(len(predictions))
                            
                            for i, (model_name, pred) in enumerate(predictions.items()):
                                with st.columns(len(predictions))[i]:
                                    st.metric(f"📊 {model_name.upper()}", f"{pred:.1%}")
                        
                        # Top influential features for this prediction
                        st.subheader("🎯 Top Risk Factors for This Customer")
                        
                        risk_factors = {
                            "Days Since Login": form_data['days_since_login'],
                            "Payment Delay (days)": form_data['payment_delay_days'],
                            "Feature Adoption %": 100 - form_data['feature_adoption_pct'],  # inverse
                            "Support Tickets": form_data['total_tickets'],
                            "NPS Score": 10 - form_data['avg_nps_score'],  # inverse
                        }
                        
                        # Sort by risk impact (higher = riskier)
                        sorted_factors = sorted(risk_factors.items(), key=lambda x: x[1], reverse=True)[:3]
                        
                        for idx, (factor, value) in enumerate(sorted_factors, 1):
                            st.caption(f"{idx}. **{factor}:** {value:.1f}")
                        
                        st.caption(f"💡 **Interpretasi:** Faktor-faktor di atas adalah yang paling mempengaruhi skor churn untuk customer ini. Fokus pada peningkatan area-area ini untuk mengurangi risiko churn.")
                
                except Exception as e:
                    st.error(f"❌ Error during prediction: {str(e)}")
        
        elif not st.session_state.fetched_customer_id:
            st.info("👆 Pilih Customer ID dan klik FETCH DATA untuk memulai")
    
    with tab2:
        st.subheader("📊 Overall Churn Analysis")
        
        # Plan selector in tab2
        col1, col2 = st.columns([1, 4])
        with col1:
            plan = st.selectbox(
                "📋 Plan Type", 
                plans,
                key="plan_selector_tab2"
            )
        plan_df = merged_df[merged_df['plan'] == plan].copy()
        
        # Explainer section
        with st.expander("ℹ️ Understanding This Section"):
            st.markdown("""
            **Section Overview:**
            
            📊 **Risk Distribution** - Shows berapa banyak customers di setiap risk level
            - Membantu identify berapa banyak customers yang perlu attention
            
            **Prediction Distribution** - Histogram showing pola churn probability
            - Jika rata-rata tinggi → audience overall berisiko tinggi
            - Jika tersebar → diverse risk profile
            
            🎯 **Feature Dominance** - Top factors yang paling influence churn prediction
            - Semakin tinggi correlation = semakin penting feature tersebut
            - Gunakan untuk identify improvement areas
            
            💰 **Revenue at Risk** - Total recurring revenue yang threatened oleh churn
            - Critical untuk prioritize retention efforts
            
            ⚠️ **Top 15 At-Risk** - Customers yang paling penting untuk contact sekarang
            """)
        
        # Summary by risk level
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Risk Distribution**")
            risk_levels = pd.cut(
                plan_df['ensemble_proba'],
                bins=[0, 0.3, 0.5, 0.7, 1.0],
                labels=['Low', 'Medium', 'High', 'Very High']
            )
            risk_counts = risk_levels.value_counts().sort_index()
            
            fig = px.bar(
                x=risk_counts.index,
                y=risk_counts.values,
                title="Customers by Risk Level",
                color=risk_counts.index,
                color_discrete_sequence=['#2ecc71', '#f39c12', '#e67e22', '#e74c3c'],
                labels={'x': 'Risk Level', 'y': 'Count'}
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption("📖 **Cara membaca:** Semakin tinggi bar di kanan = semakin banyak customers berisiko tinggi")
        
        with col2:
            st.markdown("**Prediction Distribution**")
            fig = px.histogram(
                plan_df['ensemble_proba'],
                nbins=40,
                title="Churn Probability Distribution",
                labels={"value": "Probability", "count": "Customers"},
                color_discrete_sequence=['#3498db']
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption("📖 **Cara membaca:** Puncak di kiri = customers mostly safe. Puncak di kanan = mostly at risk.")
        
        st.divider()
        
        # Feature dominance analysis
        st.subheader("🎯 Feature Dominance for Churn")
        
        with st.expander("ℹ️ Cara Membaca Feature Importance"):
            st.markdown("""
            **Apa itu Feature Dominance?**
            - Menunjukkan faktor-faktor mana yang paling mempengaruhi keputusan churn seorang customer
            - Correlation value 0-1: semakin tinggi = semakin penting
            
            **Contoh:**
            - Jika "days_since_last_login" tinggi → customers yang jarang login lebih likely churn
            - Jika "payment_health_score" tinggi → payment issues adalah major churn driver
            
            **Aksi yang bisa diambil:**
            - Focus improvement di top 3-5 features
            - Contoh: jika "feature_adoption" tinggi, improve onboarding & feature training
            """)
        
        # Calculate feature correlation with churn
        numeric_cols = plan_df.select_dtypes(include=[np.number]).columns
        churn_correlation = plan_df[list(numeric_cols)].corrwith(plan_df['actual']).abs().sort_values(ascending=False)
        
        top_features = churn_correlation.head(10)
        
        fig = px.bar(
            x=top_features.values,
            y=top_features.index,
            orientation='h',
            title="Top Features Correlated with Churn",
            labels={'x': 'Correlation', 'y': 'Feature'},
            color=top_features.values,
            color_continuous_scale='RdYlGn_r'
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("📖 **Cara membaca:** Bar lebih panjang ke kanan = feature lebih penting untuk prediksi churn")
        
        st.divider()
        
        # Revenue at risk
        st.subheader("💰 Revenue at Risk")
        
        with st.expander("ℹ️ Understanding Revenue Impact"):
            st.markdown("""
            **Why Revenue at Risk Matters:**
            - Bukan hanya jumlah customers, tetapi $ value yang threatened
            - High-risk customers mungkin high-value → impactful jika churn
            
            **Interpretasi Metrics:**
            - **Value at High Risk** - Total annual value dari customers dengan risk >50%
            - **% of Total Value** - Berapa % dari total business adalah at-risk
            - **High-Risk Customers** - Jumlah customers yang perlu immediate attention
            
            **Contoh Interpretasi:**
            - Jika 20% dari revenue is at-risk → prioritize retention campaign untuk high-value customers
            - Jika hanya 5% → lower priority, focus pada other issues
            """)
        
        plan_df['risk_category'] = pd.cut(
            plan_df['ensemble_proba'],
            bins=[0, 0.3, 0.5, 1.0],
            labels=['Low', 'Medium', 'High']
        )
        
        # Use annual_value for revenue calculations
        revenue_at_risk = plan_df.groupby('risk_category')['annual_value'].agg(['sum', 'count', 'mean'])
        revenue_at_risk.columns = ['Total Value', 'Customer Count', 'Avg Value/Customer']
        
        col1, col2, col3 = st.columns(3)
        high_risk_revenue = plan_df[plan_df['ensemble_proba'] > 0.5]['annual_value'].sum()
        with col1:
            st.metric("💸 Value at High Risk", f"${high_risk_revenue:,.0f}")
        with col2:
            total_revenue = plan_df['annual_value'].sum()
            pct_at_risk = (high_risk_revenue / total_revenue * 100) if total_revenue > 0 else 0
            st.metric("📈 % of Total Value", f"{pct_at_risk:.1f}%")
        with col3:
            high_risk_count = (plan_df['ensemble_proba'] > 0.5).sum()
            st.metric("👥 High-Risk Customers", int(high_risk_count))
        
        st.dataframe(revenue_at_risk, use_container_width=True)
        st.caption("📖 **Cara membaca table:** Lihat kategori risiko dan total value terkena dampak di setiap kategori")
        
        st.divider()
        
        # Top at-risk customers
        st.subheader("⚠️ Top 15 At-Risk Customers")
        top_risk = plan_df.nlargest(15, 'ensemble_proba')[[
            'customer_id', 'plan_type', 'tenure_months', 'annual_value', 'avg_nps_score', 'ensemble_proba'
        ]].copy()
        
        top_risk.columns = ['Customer ID', 'Plan', 'Tenure (mo)', 'Annual Value', 'NPS', 'Risk %']
        top_risk['Risk %'] = (top_risk['Risk %'] * 100).round(1)
        
        st.dataframe(top_risk, use_container_width=True)
    
    with tab3:
        st.subheader("🎯 Model Performance Evaluation")
        
        # Plan selector in tab3
        col1, col2 = st.columns([1, 4])
        with col1:
            plan = st.selectbox(
                "📋 Plan Type", 
                plans,
                key="plan_selector_tab3"
            )
        plan_df = merged_df[merged_df['plan'] == plan].copy()
        
        # Explainer section
        with st.expander("ℹ️ Understanding Model Metrics"):
            st.markdown("""
            **Accuracy (Akurasi)**
            - Persentase prediksi yang benar dari total prediksi
            - Formula: (TP + TN) / Total
            - Minimal 80% untuk model yang acceptable
            
            **Recall (Sensitivity)**
            - Dari customers yang actually churn, berapa % yang berhasil kita deteksi
            - Formula: TP / (TP + FN)
            - Penting karena kita ingin catch sebanyak mungkin actual churners
            - Minimal 70% adalah good
            
            **Precision**
            - Dari customers yang kita prediksi churn, berapa % yang benar-benar churn
            - Formula: TP / (TP + FP)
            - Penting untuk menghindari false alarms
            - Minimal 70% adalah good
            
            **F1-Score**
            - Harmonic mean dari Precision dan Recall
            - Balance indicator antara kedua metrics
            - 0-1 scale: semakin dekat 1 semakin baik
            
            **Confusion Matrix**
            - Visual breakdown dari semua 4 outcomes:
              - TP (True Positive): Predict churn, actually churn ✓
              - TN (True Negative): Predict retain, actually retain ✓
              - FP (False Positive): Predict churn, but actually retain (wasted effort)
              - FN (False Negative): Predict retain, but actually churn (missed opportunity)
            """)
        
        # Overall metrics in simple language
        st.markdown("### Model Health Scorecard")
        
        col1, col2, col3, col4 = st.columns(4)
        
        accuracy = (plan_df['ensemble_prediction'] == plan_df['actual']).sum() / len(plan_df)
        with col1:
            st.metric("Accuracy", f"{accuracy:.1%}", "How many predictions are correct")
        
        tp = ((plan_df['ensemble_prediction'] == 1) & (plan_df['actual'] == 1)).sum()
        fn = ((plan_df['ensemble_prediction'] == 0) & (plan_df['actual'] == 1)).sum()
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        with col2:
            st.metric("Recall (Sensitivity)", f"{recall:.1%}", "Catch rate of actual churners")
        
        fp = ((plan_df['ensemble_prediction'] == 1) & (plan_df['actual'] == 0)).sum()
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        with col3:
            st.metric("Precision", f"{precision:.1%}", "Accuracy of positive predictions")
        
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        with col4:
            st.metric("F1-Score", f"{f1:.1%}", "Balance of precision & recall")
        
        st.divider()
        
        # Confusion matrix
        st.markdown("### Prediction Accuracy Breakdown")
        
        cm = pd.crosstab(
            plan_df['actual'],
            plan_df['ensemble_prediction'],
            rownames=['Actual'],
            colnames=['Predicted']
        )
        cm.index = cm.index.map({0: 'Retained', 1: 'Churned'})
        cm.columns = cm.columns.map({0: 'Retained', 1: 'Churned'})
        
        fig = px.imshow(
            cm,
            text_auto=True,
            color_continuous_scale='Blues',
            title="Confusion Matrix",
            labels={'value': 'Count'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # Model comparison
        st.markdown("### Model Comparison (XGBoost vs CatBoost vs Ensemble)")
        
        model_comparison = {
            'Model': ['XGBoost', 'CatBoost', 'Ensemble'],
            'High Risk Predictions': [
                (plan_df['xgb_proba'] > 0.5).sum(),
                (plan_df['cat_proba'] > 0.5).sum(),
                (plan_df['ensemble_proba'] > 0.5).sum()
            ]
        }
        
        comp_df = pd.DataFrame(model_comparison)
        fig = px.bar(
            comp_df,
            x='Model',
            y='High Risk Predictions',
            title="High-Risk Customers Detected (Threshold >50%)",
            color='Model',
            color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1']
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        **📌 What This Means For You:**
        - **Accuracy**: Percentage of predictions that are correct
        - **Recall**: How well we catch customers who actually churn (important!)
        - **Precision**: If we predict churn, are we right?
        - **F1-Score**: Overall balance of the model
        
        **✅ Good Model Indicators:**
        - High Recall (catching most churners)
        - Balanced Precision (not too many false alarms)
        - High F1-Score (overall good performance)
        """)


def show_nlp_analysis_page():
    """NLP Sentiment Analysis page with AI Executive Summary and detailed analytics."""
    st.title("💬 NLP Sentiment Analysis")
    
    chat_df = load_chat_data()
    
    if chat_df is None:
        st.error("❌ Chat data not found. Expected: youtube_chat_5_menit_cleaned.csv")
        return
    
    # ===== AI EXECUTIVE SUMMARY =====
    st.subheader("🤖 AI Executive Summary")
    
    with st.expander("ℹ️ Apa itu Sentiment Analysis?"):
        st.markdown("""
        **Sentiment Analysis** adalah proses menganalisis teks customer feedback untuk menentukan apakah opinion mereka:
        - **Positive** - Satisfied, appreciative, senang dengan service
        - **Neutral** - Factual, objective, tidak ada emosi kuat
        - **Negative** - Dissatisfied, critical, ada keluhan/masalah
        
        **Mengapa Penting?**
        - Understand customer emotions dan satisfaction levels
        - Identify areas untuk improvement
        - Spot issues sebelum menjadi churn
        """)
    
    summary_col1, summary_col2 = st.columns([2, 1])
    
    with summary_col1:
        # Calculate summary stats
        total_feedback = len(chat_df)
        sentiment_counts = chat_df['sentiment'].value_counts()
        
        # Build summary text
        neutral_pct = (sentiment_counts.get('Neutral', 0) / total_feedback * 100) if total_feedback > 0 else 0
        positive_pct = (sentiment_counts.get('Positive', 0) / total_feedback * 100) if total_feedback > 0 else 0
        negative_pct = (sentiment_counts.get('Negative', 0) / total_feedback * 100) if total_feedback > 0 else 0
        
        summary_text = f"""
**Total Feedback Analyzed:** {total_feedback:,} messages

**Sentiment Breakdown:**
- **Neutral ({neutral_pct:.1f}%)** - Objective, factual feedback
- **Positive ({positive_pct:.1f}%)** - Satisfied, appreciative feedback  
- **Negative ({negative_pct:.1f}%)** - Dissatisfied, critical feedback

**Key Insights:**
The audience sentiment is dominated by {sentiment_counts.idxmax() if len(sentiment_counts) > 0 else 'Neutral'} feedback, 
indicating {"strong engagement and satisfaction" if positive_pct > 40 else "mixed reception" if positive_pct > 20 else "areas needing improvement"}.
"""
        st.markdown(summary_text)
        
        # Raw voice quotes
        st.markdown("**📝 Sample Feedback (Raw Quotes):**")
        sample_messages = chat_df['message'].head(3).tolist()
        for i, msg in enumerate(sample_messages, 1):
            st.caption(f"_{i}. {msg}_")
    
    with summary_col2:
        # Total feedback stat
        st.metric("📊 Total Feedback", total_feedback)
        st.metric("👥 Unique Authors", chat_df['author'].nunique())
        st.metric("⏱️ Duration", f"{chat_df['elapsed'].nunique()} time slots")
    
    st.divider()
    
    # ===== EMOTION DISTRIBUTION ANALYSIS =====
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("😊 Emotion Distribution Analysis")
        sentiment_counts = chat_df['sentiment'].value_counts()
        
        color_map = {
            'Positive': '#2ecc71',
            'Neutral': '#95a5a6',
            'Negative': '#e74c3c'
        }
        colors = [color_map.get(s, '#95a5a6') for s in sentiment_counts.index]
        
        fig = go.Figure(data=[
            go.Bar(
                y=sentiment_counts.index,
                x=sentiment_counts.values,
                orientation='h',
                marker=dict(color=colors),
                text=sentiment_counts.values,
                textposition='auto',
            )
        ])
        fig.update_layout(
            title="Sentiment Distribution",
            xaxis_title="Count",
            yaxis_title="Sentiment",
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("**Cara membaca:** Bar lebih panjang = lebih banyak messages dengan sentiment itu. Lihat mana yang dominates (paling panjang).")
    
    with col2:
        st.subheader("📈 Total Feedback Analyzed")
        
        # Pie chart
        fig = px.pie(
            values=sentiment_counts.values,
            names=sentiment_counts.index,
            title="Sentiment Proportion",
            color_discrete_map=color_map,
            hole=0.4
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("**Cara membaca:** Slice lebih besar = lebih besar proporsi dari sentiment itu. Ideal: 60%+ positive atau neutral.")
    
    st.divider()
    
    # ===== SENTIMENT & KEYWORD ANALYSIS =====
    st.subheader("🔑 Sentiment & Keyword Analysis")
    
    # Extract keywords (words) from messages
    all_words = []
    for msg in chat_df['message']:
        if isinstance(msg, str):
            words = msg.lower().split()
            all_words.extend([w.strip('.,!?;:') for w in words if len(w) > 2])
    
    word_freq = Counter(all_words).most_common(15)
    keyword_data = pd.DataFrame(word_freq, columns=['Keyword', 'Frequency'])
    
    # Map sentiment to top keywords
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Top Keywords by Frequency**")
        
        fig = px.bar(
            keyword_data.head(10),
            x='Frequency',
            y='Keyword',
            orientation='h',
            title="Most Mentioned Keywords",
            color='Frequency',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("**Sentiment Distribution by Message Length**")
        chat_df['msg_length'] = chat_df['message'].str.len()
        
        fig = px.scatter(
            chat_df,
            x='msg_length',
            y='sentiment',
            color='sentiment',
            title="Message Length vs Sentiment",
            color_discrete_map=color_map,
            labels={'msg_length': 'Message Length (chars)', 'sentiment': 'Sentiment'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # ===== SENTIMENT TREND & DRIFT =====
    st.subheader("📊 Sentiment Trend & Drift")
    
    # Create time-based sentiment trend
    chat_df['time'] = pd.to_datetime(chat_df['time'], errors='coerce')
    chat_df = chat_df.sort_values('time')
    
    # Group by time and sentiment
    sentiment_trend = chat_df.groupby([pd.Grouper(key='time', freq='5min'), 'sentiment']).size().reset_index(name='count')
    
    fig = px.line(
        sentiment_trend,
        x='time',
        y='count',
        color='sentiment',
        title="Sentiment Trend Over Time",
        color_discrete_map=color_map,
        labels={'time': 'Time', 'count': 'Message Count', 'sentiment': 'Sentiment'}
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("**Cara membaca:** Garis naik = lebih banyak messages. Lihat warna: merah (negative) = watch out, hijau (positive) = good!")
    
    with st.expander("ℹ️ Cara Membaca Sentiment Trend"):
        st.markdown("""
        **Apa yang dilihat?**
        - Garis menunjukkan berapa banyak messages dengan setiap sentiment dalam time window 5 menit
        
        **Interpretasi:**
        - Garis Negative naik → ada masalah/issue yang happening
        - Garis Positive stabil/naik → audience engaged dan satisfied
        - Garis Neutral tinggi → audience mostly observing, factual discussion
        
        **Action Points:**
        - Jika Negative spike → investigate apa yang terjadi saat itu
        - Jika Positive trend naik → content sedang resonating well
        """)
    
    st.divider()
    
    # ===== RAW CUSTOMER FEEDBACK (LIVE NLP) =====
    st.subheader("💭 Raw Customer Feedback (Live NLP)")
    
    # Filter options
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        filter_sentiment = st.multiselect(
            "Filter by Sentiment",
            chat_df['sentiment'].unique(),
            default=chat_df['sentiment'].unique()
        )
    
    with col2:
        min_length = st.slider("Min Message Length", 0, 200, 0, step=10)
    
    with col3:
        show_count = st.selectbox("Show", [10, 20, 50, 100], index=0)
    
    # Apply filters
    filtered_df = chat_df[
        (chat_df['sentiment'].isin(filter_sentiment)) &
        (chat_df['message'].str.len() >= min_length)
    ].copy()
    
    # Display feedback table
    if len(filtered_df) > 0:
        display_df = filtered_df[['time', 'author', 'message', 'sentiment']].head(show_count).copy()
        display_df.columns = ['Time', 'Author', 'Message', 'Sentiment']
        
        # Color sentiment
        def color_sentiment(val):
            if val == 'Positive':
                return '🟢 Positive'
            elif val == 'Negative':
                return '🔴 Negative'
            else:
                return '⚪ Neutral'
        
        display_df['Sentiment'] = display_df['Sentiment'].apply(color_sentiment)
        
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No messages match the selected filters.")

def show_about_page():
    """About and documentation page."""
    st.title("ℹ️ About LAPISAi")
    
    st.markdown("""
    ## LAPISAi - Advanced Analytics Dashboard
    
    **Features:**
    - 🤖 **Customer Churn Prediction** - XGBoost + CatBoost ensemble models
    - 📊 **Per-Plan Analysis** - Starter, Professional, Enterprise
    - 💬 **NLP Sentiment Analysis** - YouTube chat sentiment tracking & trend analysis
    - 📈 **Real-time Metrics** - ROC-AUC, F1-Score, Accuracy
    
    **Architecture:**
    1. **Feature Engineering** - 86 engineered features from raw data
    2. **Model Training** - Separate models per customer plan
    3. **Ensemble Predictions** - 60% XGBoost + 40% CatBoost
    4. **NLP Processing** - Sentiment analysis on customer feedback
    
    **Data Pipeline:**
    - Step 1: Feature engineering → `engineered_features/`
    - Step 2: Data preprocessing → `preprocessed_data/`
    - Step 3: Model training → `trained_models/`
    - Step 4: Predictions → `model_results/`
    
    **Quick Start:**
    ```bash
    python 01_feature_engineering.py
    python 02_preprocessing_pipeline.py
    python 03_model_training_per_plan.py
    python 04_ensemble_predictions.py
    streamlit run app_lapisai_integrated.py
    ```
    """)

# ========== MAIN ==========
def main():
    """Main app router."""
    
    # Sidebar navigation
    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["💼 Churn Prediction", "💬 NLP Analysis", "ℹ️ About"],
        index=0
    )
    
    st.sidebar.divider()
    st.sidebar.markdown("**Data Status:**")
    
    # Check data availability
    checks = {
        "Features": ENGINEERED_FEATURES_PATH.exists(),
        "Predictions": ENSEMBLE_PREDICTIONS_PATH.exists(),
        "Metrics": EVALUATION_METRICS_PATH.exists(),
        "Models": TRAINED_MODELS_DIR.exists(),
        "Chat": CHAT_DATA_PATH.exists(),
    }
    
    for label, exists in checks.items():
        emoji = "✅" if exists else "❌"
        st.sidebar.write(f"{emoji} {label}")
    
    # Route to page
    if page == "💼 Churn Prediction":
        show_churn_prediction_page()
    elif page == "💬 NLP Analysis":
        show_nlp_analysis_page()
    else:
        show_about_page()

if __name__ == "__main__":
    main()

