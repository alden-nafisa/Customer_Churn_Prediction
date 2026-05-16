"""
ENHANCEMENT MODULE FOR app_lapisai.py
Adds advanced visualizations for:
1. Customer Churn Model Results
2. Revenue at Risk Analysis
3. Feature Importance by Plan
4. NLP Sentiment Analysis Enhancement
5. Model Performance Comparisons
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from pathlib import Path
import json


# ============================================================================
# 1. REVENUE AT RISK VISUALIZATIONS
# ============================================================================

def visualize_revenue_at_risk(data: pd.DataFrame) -> None:
    """
    Display revenue at risk metrics and visualizations.
    
    Expected columns:
    - customer_id, plan_type, revenue_at_risk, payment_health_score,
      engagement_health_score, satisfaction_health_score, churn_probability
    """
    st.header("💰 Revenue at Risk Analysis")
    
    if data.empty or 'revenue_at_risk' not in data.columns:
        st.info("Revenue at risk data not available. Run feature engineering first.")
        return
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    total_risk = data['revenue_at_risk'].sum() if 'revenue_at_risk' in data.columns else 0
    avg_payment_health = data['payment_health_score'].mean() if 'payment_health_score' in data.columns else 0
    avg_engagement = data['engagement_health_score'].mean() if 'engagement_health_score' in data.columns else 0
    avg_satisfaction = data['satisfaction_health_score'].mean() if 'satisfaction_health_score' in data.columns else 0
    
    col1.metric("Total Revenue at Risk", f"${total_risk:,.0f}")
    col2.metric("Avg Payment Health", f"{avg_payment_health:.2%}")
    col3.metric("Avg Engagement Health", f"{avg_engagement:.2%}")
    col4.metric("Avg Satisfaction Health", f"{avg_satisfaction:.2%}")
    
    st.divider()
    
    # Revenue at Risk by Plan Type
    st.subheader("Revenue at Risk by Plan Type")
    if 'plan_type' in data.columns:
        risk_by_plan = data.groupby('plan_type')['revenue_at_risk'].sum().sort_values(ascending=False)
        
        fig = px.bar(
            x=risk_by_plan.index,
            y=risk_by_plan.values,
            labels={'x': 'Plan Type', 'y': 'Revenue at Risk ($)'},
            color=risk_by_plan.index,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Health Scores Heatmap
    st.subheader("Health Scores Heatmap (Top 20 At-Risk Customers)")
    if 'plan_type' in data.columns:
        top_risk = data.nlargest(20, 'revenue_at_risk')[
            ['customer_id', 'plan_type', 'payment_health_score', 
             'engagement_health_score', 'satisfaction_health_score']
        ].set_index('customer_id')
        
        fig = go.Figure(data=go.Heatmap(
            z=top_risk[[col for col in top_risk.columns if 'health' in col.lower()]].values,
            x=[col.replace('_', ' ').title() for col in top_risk.columns if 'health' in col.lower()],
            y=top_risk.index,
            colorscale='RdYlGn',
            zmid=0.5
        ))
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    # Distribution Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Revenue at Risk Distribution")
        fig = px.histogram(
            data,
            x='revenue_at_risk',
            nbins=30,
            labels={'revenue_at_risk': 'Revenue at Risk ($)'},
            color_discrete_sequence=['#1f77b4']
        )
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Churn Probability Distribution")
        if 'churn_probability' in data.columns:
            fig = px.histogram(
                data,
                x='churn_probability',
                nbins=30,
                labels={'churn_probability': 'Churn Probability'},
                color_discrete_sequence=['#ff7f0e']
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# 2. FEATURE IMPORTANCE BY PLAN VISUALIZATIONS
# ============================================================================

def visualize_feature_importance_by_plan(metrics_path: str) -> None:
    """
    Display feature importance comparison across plan types.
    
    Expected: JSON files with feature importance per plan type
    """
    st.header("🎯 Feature Importance by Plan Type")
    
    metrics_dir = Path(metrics_path).parent / "plan_specific"
    
    if not metrics_dir.exists():
        st.info("Feature importance data not available.")
        return
    
    # Load metrics for each plan
    plans = ['starter', 'professional', 'enterprise']
    importance_data = {}
    
    for plan in plans:
        metrics_file = metrics_dir / f"{plan}_xgboost_metrics.json"
        if metrics_file.exists():
            try:
                with open(metrics_file, 'r') as f:
                    metrics = json.load(f)
                    importance_data[plan] = metrics.get('feature_importance', {})
            except:
                pass
    
    if not importance_data:
        st.info("No feature importance data found.")
        return
    
    # Tabs for each plan
    tabs = st.tabs(['Starter', 'Professional', 'Enterprise'])
    
    for idx, (plan, tab) in enumerate(zip(plans, tabs)):
        with tab:
            if plan in importance_data and importance_data[plan]:
                features = list(importance_data[plan].keys())[:15]
                importances = [importance_data[plan][f] for f in features]
                
                # Determine tier colors
                colors = []
                for imp in importances:
                    if imp > 0.05:
                        colors.append('#ef553b')  # Red - Tier 1
                    elif imp > 0.02:
                        colors.append('#ffa500')  # Orange - Tier 2
                    else:
                        colors.append('#636EFA')  # Blue - Tier 3
                
                fig = px.bar(
                    x=importances,
                    y=features,
                    orientation='h',
                    labels={'x': 'Importance Score', 'y': 'Feature'},
                    color=colors,
                    color_discrete_sequence=colors
                )
                fig.update_layout(
                    height=500,
                    showlegend=False,
                    xaxis_title='Importance Score'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Feature tier legend
                st.markdown("""
                **Feature Importance Tiers:**
                - 🔴 **Tier 1 (Critical)**: Importance > 0.05
                - 🟠 **Tier 2 (High)**: Importance 0.02-0.05
                - 🔵 **Tier 3 (Medium)**: Importance < 0.02
                """)
            else:
                st.info(f"No data for {plan} plan.")


# ============================================================================
# 3. MODEL PERFORMANCE COMPARISON
# ============================================================================

def visualize_model_comparison(metrics_path: str) -> None:
    """
    Compare XGBoost vs CatBoost performance across plans.
    """
    st.header("🤖 Model Performance Comparison")
    
    metrics_dir = Path(metrics_path).parent / "plan_specific"
    
    if not metrics_dir.exists():
        st.info("Model metrics not available.")
        return
    
    plans = ['starter', 'professional', 'enterprise']
    comparison_data = []
    
    for plan in plans:
        for model_type in ['xgboost', 'catboost']:
            metrics_file = metrics_dir / f"{plan}_{model_type}_metrics.json"
            if metrics_file.exists():
                try:
                    with open(metrics_file, 'r') as f:
                        metrics = json.load(f)
                        comparison_data.append({
                            'Plan': plan.title(),
                            'Model': model_type.upper(),
                            'Accuracy': metrics.get('accuracy', 0),
                            'Precision': metrics.get('precision', 0),
                            'Recall': metrics.get('recall', 0),
                            'F1-Score': metrics.get('f1', 0),
                            'ROC-AUC': metrics.get('roc_auc', 0),
                        })
                except:
                    pass
    
    if comparison_data:
        df_comparison = pd.DataFrame(comparison_data)
        
        # Metrics table
        st.subheader("Performance Metrics Table")
        st.dataframe(
            df_comparison.style.format({
                'Accuracy': '{:.3f}',
                'Precision': '{:.3f}',
                'Recall': '{:.3f}',
                'F1-Score': '{:.3f}',
                'ROC-AUC': '{:.3f}',
            }),
            use_container_width=True
        )
        
        # ROC-AUC Comparison
        st.subheader("ROC-AUC Comparison")
        fig = px.bar(
            df_comparison,
            x='Plan',
            y='ROC-AUC',
            color='Model',
            barmode='group',
            color_discrete_map={'XGBOOST': '#636EFA', 'CATBOOST': '#EF553B'},
            height=400
        )
        fig.update_layout(yaxis=dict(range=[0, 1]))
        st.plotly_chart(fig, use_container_width=True)
        
        # F1-Score Comparison
        st.subheader("F1-Score Comparison")
        fig = px.bar(
            df_comparison,
            x='Plan',
            y='F1-Score',
            color='Model',
            barmode='group',
            color_discrete_map={'XGBOOST': '#636EFA', 'CATBOOST': '#EF553B'},
            height=400
        )
        fig.update_layout(yaxis=dict(range=[0, 1]))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No comparison data available.")


# ============================================================================
# 4. NLP SENTIMENT ANALYSIS ENHANCED VISUALIZATION
# ============================================================================

def visualize_nlp_sentiment_enhanced(nlp_assets: dict) -> None:
    """
    Enhanced NLP sentiment analysis visualization with multiple charts.
    """
    st.header("🧠 NLP Sentiment Analysis (YouTube Comments)")
    
    sentiment_metrics = nlp_assets.get('sentiment_metrics', {})
    sentiment_preds = nlp_assets.get('sentiment_test_predictions', pd.DataFrame())
    
    if not sentiment_metrics:
        st.info("NLP sentiment data not available. Run train_sentiment_model.py first.")
        return
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Accuracy", f"{sentiment_metrics.get('accuracy', 0):.1%}")
    col2.metric("Precision", f"{sentiment_metrics.get('precision', 0):.1%}")
    col3.metric("Recall", f"{sentiment_metrics.get('recall', 0):.1%}")
    col4.metric("F1-Score", f"{sentiment_metrics.get('f1_score', 0):.3f}")
    
    st.divider()
    
    # Sentiment Distribution
    st.subheader("Sentiment Distribution")
    if not sentiment_preds.empty and 'sentiment' in sentiment_preds.columns:
        sentiment_counts = sentiment_preds['sentiment'].value_counts()
        
        colors = {
            'positive': '#1f77b4',
            'negative': '#d62728',
            'neutral': '#7f7f7f'
        }
        
        fig = px.pie(
            values=sentiment_counts.values,
            names=sentiment_counts.index,
            color=sentiment_counts.index,
            color_discrete_map=colors,
            hole=0.4
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Confusion Matrix
    st.subheader("Prediction Confusion Matrix")
    if 'confusion_matrix' in sentiment_metrics:
        cm = sentiment_metrics['confusion_matrix']
        fig = go.Figure(data=go.Heatmap(
            z=cm,
            x=['Negative', 'Neutral', 'Positive'],
            y=['Negative', 'Neutral', 'Positive'],
            colorscale='Blues',
            text=cm,
            texttemplate='%{text}',
            textfont={"size": 12}
        ))
        fig.update_layout(
            title='Confusion Matrix',
            xaxis_title='Predicted',
            yaxis_title='Actual',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # ROC Curve
    st.subheader("ROC-AUC Score")
    roc_auc = sentiment_metrics.get('roc_auc', 0)
    st.metric("ROC-AUC", f"{roc_auc:.3f}")
    
    # Representative Comments
    st.subheader("💭 Representative Comments by Sentiment")
    session_summary = nlp_assets.get('session_summary', {})
    representative = session_summary.get('representative_comments', [])
    
    if representative:
        for comment_item in representative:
            sentiment = comment_item.get('sentiment', 'Unknown').upper()
            author = comment_item.get('author', 'Anonymous')
            text = comment_item.get('comment', '')
            
            # Color based on sentiment
            if sentiment == 'POSITIVE':
                color = '🟢'
            elif sentiment == 'NEGATIVE':
                color = '🔴'
            else:
                color = '⚪'
            
            with st.expander(f"{color} **{sentiment}** - {author}"):
                st.write(text)
    else:
        st.info("No representative comments found.")


# ============================================================================
# 5. CUSTOMER CHURN RISK RANKING
# ============================================================================

def visualize_customer_churn_ranking(data: pd.DataFrame) -> None:
    """
    Display top customers at churn risk with detailed breakdown.
    """
    st.header("⚠️ Customer Churn Risk Ranking")
    
    if data.empty or 'churn_probability' not in data.columns:
        st.info("Churn data not available.")
        return
    
    # Filter for high-risk customers
    threshold = st.slider("Risk Threshold", 0.0, 1.0, 0.5)
    high_risk = data[data['churn_probability'] >= threshold].copy()
    
    if high_risk.empty:
        st.info(f"No customers at risk above {threshold:.1%}")
        return
    
    # Sort by churn probability
    high_risk = high_risk.sort_values('churn_probability', ascending=False)
    
    # Top 10 at-risk customers
    st.subheader(f"Top 10 At-Risk Customers (Threshold: {threshold:.1%})")
    
    top_10 = high_risk.head(10)[['customer_id', 'churn_probability', 'plan_type', 'revenue_at_risk']]
    
    fig = px.bar(
        top_10.reset_index(drop=True),
        x='churn_probability',
        y=top_10.index.astype(str),
        orientation='h',
        labels={'churn_probability': 'Churn Probability'},
        color='churn_probability',
        color_continuous_scale='Reds'
    )
    fig.update_layout(
        height=400,
        yaxis_title='Customer Rank',
        xaxis_title='Churn Probability'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed table
    st.subheader(f"High-Risk Customers ({len(high_risk)} total)")
    display_cols = ['customer_id', 'churn_probability', 'plan_type']
    if 'revenue_at_risk' in high_risk.columns:
        display_cols.append('revenue_at_risk')
    
    st.dataframe(
        high_risk[display_cols].reset_index(drop=True).style.format({
            'churn_probability': '{:.1%}',
            'revenue_at_risk': '${:,.0f}' if 'revenue_at_risk' in display_cols else None
        }),
        use_container_width=True
    )
    
    # Download option
    csv = high_risk[display_cols].to_csv(index=False)
    st.download_button(
        "📥 Download High-Risk List",
        data=csv,
        file_name="high_risk_customers.csv",
        mime="text/csv"
    )


# ============================================================================
# 6. CHURN DRIVERS ANALYSIS
# ============================================================================

def visualize_churn_drivers(data: pd.DataFrame, analysis_results_dir: str) -> None:
    """
    Analyze and visualize factors driving churn predictions.
    """
    st.header("📊 Churn Drivers Analysis")
    
    analysis_dir = Path(analysis_results_dir)
    
    # Load correlation analysis
    corr_file = analysis_dir / "churn_correlations.csv"
    if corr_file.exists():
        correlations = pd.read_csv(corr_file)
        
        st.subheader("Feature Correlation with Churn")
        
        # Top positive correlations (increase churn)
        top_drivers = correlations.nlargest(10, 'correlation')
        
        fig = px.bar(
            top_drivers,
            x='correlation',
            y='feature',
            orientation='h',
            labels={'correlation': 'Correlation with Churn', 'feature': 'Feature'},
            color='correlation',
            color_continuous_scale='Reds',
            height=400
        )
        fig.update_layout(xaxis_title='Correlation Coefficient')
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        **Interpretation:**
        - **Positive correlation**: Higher values → Higher churn risk
        - **Red color**: Stronger positive correlation
        """)
    
    # Load feature statistics
    stats_file = analysis_dir / "feature_statistics.csv"
    if stats_file.exists():
        st.subheader("Feature Statistics")
        stats = pd.read_csv(stats_file)
        st.dataframe(stats.head(15), use_container_width=True)


# ============================================================================
# INTEGRATION FUNCTION
# ============================================================================

def add_enhanced_visualizations_to_app(
    data: pd.DataFrame,
    nlp_assets: dict,
    metrics_path: str,
    analysis_results_dir: str
) -> None:
    """
    Main function to add all enhancements to app_lapisai.py
    
    Usage in app_lapisai.py main():
    ```
    from app_enhancements import add_enhanced_visualizations_to_app
    
    if selected_page == "Model Visualizations":
        add_enhanced_visualizations_to_app(
            data=loaded_data,
            nlp_assets=nlp_assets,
            metrics_path=str(ARTIFACT_DIR / "plan_model_metrics.json"),
            analysis_results_dir=str(PROJECT_ROOT / "analysis_results")
        )
    ```
    """
    
    # Create tabs for different visualizations
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "💰 Revenue at Risk",
        "🎯 Feature Importance",
        "🤖 Model Comparison",
        "🧠 NLP Sentiment",
        "⚠️ Churn Ranking",
        "📊 Drivers"
    ])
    
    with tab1:
        visualize_revenue_at_risk(data)
    
    with tab2:
        visualize_feature_importance_by_plan(metrics_path)
    
    with tab3:
        visualize_model_comparison(metrics_path)
    
    with tab4:
        visualize_nlp_sentiment_enhanced(nlp_assets)
    
    with tab5:
        visualize_customer_churn_ranking(data)
    
    with tab6:
        visualize_churn_drivers(data, analysis_results_dir)


if __name__ == "__main__":
    st.set_page_config(page_title="Model Visualizations", layout="wide")
    st.title("🚀 Customer Churn Prediction - Model Visualizations")
    st.markdown("Enhanced visualizations for LAPISAI churn prediction models")
