"""
Comprehensive Visualization Module for Non-Technical Users
Individual Customer Prediction + Aggregate Dashboard Analysis

Purpose:
- Show individual customer churn risk with business context
- Provide aggregate insights and trends
- All visualizations designed for non-technical users (Sales/Business Managers)
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_and_prepare_predictions(
    engineered_features_df: pd.DataFrame,
    predictions: dict[str, np.ndarray],
) -> pd.DataFrame:
    """
    Combine engineered features with model predictions.
    
    Args:
        engineered_features_df: Customer features
        predictions: Dict with 'xgb_probs', 'catboost_probs', 'ensemble_probs'
    
    Returns:
        DataFrame with customer data + predictions
    """
    result_df = engineered_features_df.copy()
    
    # Add predictions
    if "xgb_probs" in predictions:
        result_df["xgb_churn_prob"] = predictions["xgb_probs"]
    if "catboost_probs" in predictions:
        result_df["catboost_churn_prob"] = predictions["catboost_probs"]
    if "ensemble_probs" in predictions:
        result_df["ensemble_churn_prob"] = predictions["ensemble_probs"]
    else:
        # Default: ensemble = 0.6*XGB + 0.4*CatBoost
        if "xgb_probs" in predictions and "catboost_probs" in predictions:
            result_df["ensemble_churn_prob"] = (
                0.6 * predictions["xgb_probs"] + 0.4 * predictions["catboost_probs"]
            )
    
    # Classify risk level
    result_df["risk_level"] = result_df["ensemble_churn_prob"].apply(
        lambda x: "High Risk" if x > 0.70 else ("Medium Risk" if x > 0.40 else "Low Risk")
    )
    
    # Estimate revenue at risk
    if "mrr_current" in result_df.columns:
        result_df["revenue_at_risk"] = result_df["mrr_current"] * result_df["ensemble_churn_prob"]
    else:
        result_df["revenue_at_risk"] = 1000 * result_df["ensemble_churn_prob"]  # Placeholder
    
    return result_df


def get_risk_color(probability: float) -> str:
    """Return color based on churn probability."""
    if probability > 0.70:
        return "#FF4444"  # Red
    elif probability > 0.40:
        return "#FFB84D"  # Yellow
    return "#00CC44"  # Green


def get_health_color(value: float, thresholds: list[float]) -> str:
    """Return color based on thresholds (Red < Yellow < Green)."""
    if value < thresholds[0]:
        return "#FF4444"  # Red - Bad
    elif value < thresholds[1]:
        return "#FFB84D"  # Yellow - Warning
    return "#00CC44"  # Green - Good


# ============================================================================
# INDIVIDUAL CUSTOMER VISUALIZATIONS
# ============================================================================

def render_individual_customer_header(
    customer_data: pd.Series,
) -> None:
    """Display customer info header."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("**Customer ID**")
        st.text(customer_data.get("customer_id", "N/A"))
    
    with col2:
        st.markdown("**Plan Type**")
        st.text(customer_data.get("plan_type", "N/A"))
    
    with col3:
        st.markdown("**Subscription Days**")
        tenure = customer_data.get("tenure_days", 0)
        st.text(f"{int(tenure)} days")
    
    with col4:
        st.markdown("**MRR**")
        mrr = customer_data.get("mrr_current", 0)
        st.text(f"${mrr:,.0f}")


def render_churn_risk_card(
    customer_data: pd.Series,
) -> None:
    """
    #1 - CHURN RISK CARD (Hero)
    Display large risk badge with financial impact.
    """
    prob = customer_data.get("ensemble_churn_prob", 0.5)
    mrr = customer_data.get("mrr_current", 1000)
    revenue_at_risk_monthly = mrr * prob
    revenue_at_risk_annual = revenue_at_risk_monthly * 12
    
    # Determine risk label and emoji
    if prob > 0.70:
        risk_label = "HIGH RISK"
        emoji = "🔴"
        color = "#FF4444"
    elif prob > 0.40:
        risk_label = "MEDIUM RISK"
        emoji = "🟡"
        color = "#FFB84D"
    else:
        risk_label = "LOW RISK"
        emoji = "🟢"
        color = "#00CC44"
    
    # Create custom HTML card
    card_html = f"""
    <div style="
        background: linear-gradient(135deg, {color}20 0%, {color}05 100%);
        border: 3px solid {color};
        border-radius: 15px;
        padding: 30px;
        text-align: center;
        margin: 20px 0;
    ">
        <h2 style="margin: 0; color: {color};">{emoji} CHURN RISK</h2>
        <h1 style="margin: 10px 0; font-size: 72px; color: {color};">{prob*100:.1f}%</h1>
        <h3 style="margin: 10px 0; color: #333;">{risk_label}</h3>
        
        <hr style="border-top: 2px solid {color}20; margin: 20px 0;">
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
            <div>
                <p style="color: #666; margin: 0; font-size: 12px;">Monthly Revenue at Risk</p>
                <p style="color: {color}; margin: 5px 0; font-size: 28px; font-weight: bold;">${revenue_at_risk_monthly:,.0f}</p>
            </div>
            <div>
                <p style="color: #666; margin: 0; font-size: 12px;">Annual Potential Loss</p>
                <p style="color: {color}; margin: 5px 0; font-size: 28px; font-weight: bold;">${revenue_at_risk_annual:,.0f}</p>
            </div>
        </div>
        
        <p style="color: #999; margin-top: 15px; font-size: 12px;">
            <strong>Interpretation:</strong> This customer has a <strong>{prob*100:.0f}%</strong> probability of churning in the next period.
            If they leave, you lose <strong>${revenue_at_risk_annual:,.0f}/year</strong>.
        </p>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)


def render_health_check(customer_data: pd.Series) -> None:
    """
    #2 - HEALTH CHECK (3-Color Traffic Light)
    Display customer health across 3 dimensions.
    """
    st.markdown("### 📊 Customer Health Status")
    
    # Extract relevant metrics
    payment_delay = customer_data.get("payment_delay_days_mean", 0)
    support_tickets = customer_data.get("support_total_tickets", 0)
    nps_score = customer_data.get("nps_score_mean", 50)
    
    # Determine colors based on thresholds
    # Payment: Red if > 30 days, Yellow if > 15, Green else
    if payment_delay > 30:
        payment_color, payment_status = "#FF4444", "Red - Critical"
        payment_text = f"⚠️ {int(payment_delay)} days overdue - Payment block active"
    elif payment_delay > 15:
        payment_color, payment_status = "#FFB84D", "Yellow - Caution"
        payment_text = f"⚠️ {int(payment_delay)} days overdue - Monitor"
    else:
        payment_color, payment_status = "#00CC44", "Green - Healthy"
        payment_text = f"✅ {int(payment_delay):.0f} days payment status - On track"
    
    # Support: Red if > 5, Yellow if > 2, Green else
    if support_tickets > 5:
        support_color, support_status = "#FF4444", "Red - Critical"
        support_text = f"⚠️ {int(support_tickets)} tickets open - 2+ critical"
    elif support_tickets > 2:
        support_color, support_status = "#FFB84D", "Yellow - Caution"
        support_text = f"⚠️ {int(support_tickets)} tickets open - Monitor"
    else:
        support_color, support_status = "#00CC44", "Green - Healthy"
        support_text = f"✅ {int(support_tickets):.0f} tickets - Low burden"
    
    # Satisfaction: Red if NPS < 30, Yellow if < 50, Green else
    if nps_score < 30:
        satisfaction_color, satisfaction_status = "#FF4444", "Red - Critical"
        satisfaction_text = f"⚠️ NPS {nps_score:.0f} - Dissatisfied"
    elif nps_score < 50:
        satisfaction_color, satisfaction_status = "#FFB84D", "Yellow - Caution"
        satisfaction_text = f"⚠️ NPS {nps_score:.0f} - Neutral/Detractor"
    else:
        satisfaction_color, satisfaction_status = "#00CC44", "Green - Healthy"
        satisfaction_text = f"✅ NPS {nps_score:.0f} - Promoter/Passive"
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="
            background: {payment_color}20;
            border-left: 4px solid {payment_color};
            padding: 15px;
            border-radius: 8px;
        ">
            <p style="margin: 0; color: #666; font-size: 12px; font-weight: bold;">💳 PAYMENT</p>
            <p style="margin: 8px 0; color: {payment_color}; font-size: 14px; font-weight: bold;">{payment_status}</p>
            <p style="margin: 0; color: #333; font-size: 13px;">{payment_text}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="
            background: {support_color}20;
            border-left: 4px solid {support_color};
            padding: 15px;
            border-radius: 8px;
        ">
            <p style="margin: 0; color: #666; font-size: 12px; font-weight: bold;">🆘 SUPPORT</p>
            <p style="margin: 8px 0; color: {support_color}; font-size: 14px; font-weight: bold;">{support_status}</p>
            <p style="margin: 0; color: #333; font-size: 13px;">{support_text}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="
            background: {satisfaction_color}20;
            border-left: 4px solid {satisfaction_color};
            padding: 15px;
            border-radius: 8px;
        ">
            <p style="margin: 0; color: #666; font-size: 12px; font-weight: bold;">😊 SATISFACTION</p>
            <p style="margin: 8px 0; color: {satisfaction_color}; font-size: 14px; font-weight: bold;">{satisfaction_status}</p>
            <p style="margin: 0; color: #333; font-size: 13px;">{satisfaction_text}</p>
        </div>
        """, unsafe_allow_html=True)


def render_top_churn_reasons(customer_data: pd.Series) -> None:
    """
    #3 - TOP CHURN REASONS (Horizontal Bar Chart)
    Show factors pushing risk UP (red) and DOWN (green).
    """
    st.markdown("### 📈 Factors Affecting Churn Risk")
    
    # Calculate impact scores based on features
    # These are simplified - in production you'd use actual SHAP values
    reasons = []
    
    # Extract factors
    days_since_login = customer_data.get("days_since_last_login_mean", 0)
    payment_delay = customer_data.get("payment_delay_days_mean", 0)
    support_tickets = customer_data.get("support_total_tickets", 0)
    nps_score = customer_data.get("nps_score_mean", 50)
    tenure_days = customer_data.get("tenure_days", 365)
    
    # Push UP (negative for churn)
    if days_since_login > 20:
        impact = min(days_since_login / 100, 0.40)  # Max 40% impact
        reasons.append({
            "factor": f"No Login for {int(days_since_login)} Days",
            "impact": impact * 100,
            "direction": "push_up",
            "severity": "critical" if days_since_login > 60 else ("warning" if days_since_login > 30 else "info"),
        })
    
    if payment_delay > 5:
        impact = min(payment_delay / 100, 0.30)
        reasons.append({
            "factor": f"Payment {int(payment_delay)} Days Late",
            "impact": impact * 100,
            "direction": "push_up",
            "severity": "critical" if payment_delay > 30 else ("warning" if payment_delay > 15 else "info"),
        })
    
    if support_tickets > 3:
        impact = min(support_tickets / 20, 0.20)
        reasons.append({
            "factor": f"{int(support_tickets)} Open Support Tickets",
            "impact": impact * 100,
            "direction": "push_up",
            "severity": "critical" if support_tickets > 5 else "warning",
        })
    
    # Pull DOWN (positive for retention)
    if nps_score > 50:
        impact = min((nps_score - 50) / 100, 0.15)
        reasons.append({
            "factor": f"Good NPS Score ({nps_score:.0f})",
            "impact": -impact * 100,
            "direction": "pull_down",
            "severity": "positive",
        })
    
    if tenure_days > 365:
        impact = min(tenure_days / 1460, 0.10)  # 4 years max
        reasons.append({
            "factor": f"Long Customer ({int(tenure_days/365)} years)",
            "impact": -impact * 100,
            "direction": "pull_down",
            "severity": "positive",
        })
    
    if not reasons:
        st.info("Customer profile is healthy with no major churn indicators.")
        return
    
    # Create dataframe and chart
    reasons_df = pd.DataFrame(reasons)
    reasons_df_sorted = reasons_df.sort_values("impact", ascending=True)
    
    # Create horizontal bar chart
    fig = px.barh(
        reasons_df_sorted,
        x="impact",
        y="factor",
        color="direction",
        color_discrete_map={"push_up": "#FF4444", "pull_down": "#00CC44"},
        title="",
        labels={"impact": "Impact on Churn Risk (%)", "factor": ""},
    )
    
    fig.update_layout(
        height=300,
        showlegend=False,
        margin=dict(l=200, r=50, t=20, b=50),
        yaxis_tickfont=dict(size=12),
    )
    
    fig.add_vline(x=0, line_dash="dash", line_color="#999", annotation_text="Neutral", annotation_position="top right")
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add interpretation
    push_up_total = reasons_df[reasons_df["direction"] == "push_up"]["impact"].sum()
    pull_down_total = abs(reasons_df[reasons_df["direction"] == "pull_down"]["impact"].sum())
    
    st.markdown(f"""
    **Interpretation:**
    - **Red bars** = Factors increasing churn risk by {push_up_total:.0f}% combined
    - **Green bars** = Factors protecting customer by {pull_down_total:.0f}% combined
    - **Net impact** on base probability: {push_up_total - pull_down_total:+.0f}%
    """)


def render_action_recommendations(customer_data: pd.Series) -> None:
    """
    #4 - RECOMMENDED ACTIONS (Priority List)
    Display what should be done immediately.
    """
    st.markdown("### 🎯 Recommended Actions")
    
    actions = []
    
    # Build action list based on customer state
    payment_delay = customer_data.get("payment_delay_days_mean", 0)
    support_tickets = customer_data.get("support_total_tickets", 0)
    nps_score = customer_data.get("nps_score_mean", 50)
    churn_prob = customer_data.get("ensemble_churn_prob", 0.5)
    
    if payment_delay > 30:
        actions.append({
            "priority": 1,
            "urgency": "URGENT",
            "emoji": "🚨",
            "title": "Resolve Payment Issue",
            "description": f"Payment is {int(payment_delay)} days overdue. Payment block is active.",
            "channel": "☎️  Phone Call",
            "impact": "-16%",
            "days": 1,
        })
    elif payment_delay > 15:
        actions.append({
            "priority": 1,
            "urgency": "CRITICAL",
            "emoji": "🔴",
            "title": "Follow-up on Payment",
            "description": f"Payment is {int(payment_delay)} days late. Send payment reminder.",
            "channel": "📧 Email",
            "impact": "-10%",
            "days": 2,
        })
    
    if support_tickets > 5:
        actions.append({
            "priority": 2 if payment_delay > 15 else 1,
            "urgency": "CRITICAL",
            "emoji": "🔴",
            "title": "Escalate Support Tickets",
            "description": f"{int(support_tickets)} support tickets are open. Assign to senior support team.",
            "channel": "🔧 Internal",
            "impact": "-18%",
            "days": 1,
        })
    
    if nps_score < 50 or churn_prob > 0.7:
        actions.append({
            "priority": 3 if len(actions) > 0 else 1,
            "urgency": "IMPORTANT",
            "emoji": "🟡",
            "title": "Executive Check-in Call",
            "description": "Schedule account manager to understand satisfaction and rebuild relationship.",
            "channel": "👤 Account Manager",
            "impact": "-8%",
            "days": 3,
        })
    
    if not actions:
        actions.append({
            "priority": 1,
            "urgency": "ROUTINE",
            "emoji": "✅",
            "title": "Continue Standard Support",
            "description": "Customer is healthy. Maintain regular engagement and monitoring.",
            "channel": "📊 Monitor",
            "impact": "0%",
            "days": 30,
        })
    
    # Display actions
    for action in sorted(actions, key=lambda x: x["priority"]):
        color = "#FF4444" if action["urgency"] == "URGENT" else ("#FF6B6B" if action["urgency"] == "CRITICAL" else "#FFB84D")
        
        st.markdown(f"""
        <div style="
            background: {color}15;
            border-left: 4px solid {color};
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4 style="margin: 0; color: #333;">{action['priority']}. {action['emoji']} {action['title']}</h4>
                    <p style="margin: 8px 0 0 0; color: #666; font-size: 14px;">{action['description']}</p>
                    <p style="margin: 5px 0 0 0; color: #999; font-size: 12px;">
                        <strong>Channel:</strong> {action['channel']} | 
                        <strong>Timeline:</strong> Next {action['days']} days | 
                        <strong>Expected Impact:</strong> {action['impact']} churn risk
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_whatif_simulator(customer_data: pd.Series) -> None:
    """
    #5 - WHAT-IF SIMULATOR (Interactive Sliders)
    Allow user to test different intervention scenarios.
    """
    st.markdown("### 💡 What-If Scenario Testing")
    st.info("**Use the sliders below to test different intervention scenarios. See how churn probability changes!**")
    
    base_prob = customer_data.get("ensemble_churn_prob", 0.5)
    current_payment_delay = customer_data.get("payment_delay_days_mean", 0)
    current_nps = customer_data.get("nps_score_mean", 50)
    
    # Create columns for sliders
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### Scenario A: Resolve Payment")
        days_to_resolve = st.slider(
            "How many days to resolve payment?",
            min_value=1,
            max_value=int(max(current_payment_delay, 30)),
            value=int(max(current_payment_delay, 15)),
            step=1,
            key="payment_slider",
        )
        # Payment impact: each day resolved = -0.5% churn reduction
        payment_impact = (current_payment_delay - days_to_resolve) * 0.005
        prob_after_payment = max(0, min(1, base_prob - payment_impact))
    
    with col2:
        st.markdown("#### Scenario B: Improve NPS")
        nps_improvement = st.slider(
            "NPS score improvement (points)",
            min_value=0,
            max_value=30,
            value=10,
            step=5,
            key="nps_slider",
        )
        # NPS impact: each 10 points = -3% churn reduction
        nps_impact = (nps_improvement / 10) * 0.03
        prob_after_nps = max(0, min(1, base_prob - nps_impact))
    
    # Combined scenario
    st.markdown("#### Scenario C: Combined (Both A + B)")
    combined_impact = payment_impact + nps_impact
    prob_after_combined = max(0, min(1, base_prob - combined_impact))
    
    # Display results
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        old_color = get_risk_color(prob_after_payment)
        st.markdown(f"""
        <div style="
            background: {old_color}20;
            border: 2px solid {old_color};
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        ">
            <p style="margin: 0; color: #666; font-size: 12px;">After Resolving Payment</p>
            <h2 style="margin: 10px 0; color: {old_color};">{prob_after_payment*100:.1f}%</h2>
            <p style="margin: 0; color: #999; font-size: 11px;">
                Improvement: {(base_prob - prob_after_payment)*100:+.1f}%
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        nps_color = get_risk_color(prob_after_nps)
        st.markdown(f"""
        <div style="
            background: {nps_color}20;
            border: 2px solid {nps_color};
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        ">
            <p style="margin: 0; color: #666; font-size: 12px;">After NPS Improvement</p>
            <h2 style="margin: 10px 0; color: {nps_color};">{prob_after_nps*100:.1f}%</h2>
            <p style="margin: 0; color: #999; font-size: 11px;">
                Improvement: {(base_prob - prob_after_nps)*100:+.1f}%
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        combined_color = get_risk_color(prob_after_combined)
        st.markdown(f"""
        <div style="
            background: {combined_color}20;
            border: 3px solid {combined_color};
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        ">
            <p style="margin: 0; color: #666; font-size: 12px; font-weight: bold;">COMBINED IMPACT (RECOMMENDED)</p>
            <h2 style="margin: 10px 0; color: {combined_color}; font-weight: bold;">{prob_after_combined*100:.1f}%</h2>
            <p style="margin: 0; color: #999; font-size: 11px;">
                Total Improvement: {(base_prob - prob_after_combined)*100:+.1f}%
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Recommendation
    st.success(f"""
    **Recommendation:** By taking both actions, you can reduce churn risk from {base_prob*100:.1f}% → {prob_after_combined*100:.1f}%.
    
    This means: **{(1-prob_after_combined)*100:.1f}% probability** the customer will stay with you!
    """)


# ============================================================================
# RENDER MAIN INDIVIDUAL CUSTOMER PAGE
# ============================================================================

def render_individual_customer_page(
    customer_data: pd.Series,
) -> None:
    """Main page for individual customer analysis."""
    
    st.header("🎯 Individual Customer Churn Analysis")
    st.divider()
    
    # Header with customer info
    render_individual_customer_header(customer_data)
    st.divider()
    
    # #1 - Churn Risk Card
    render_churn_risk_card(customer_data)
    
    # #2 - Health Check
    st.divider()
    render_health_check(customer_data)
    
    # #3 - Top Reasons
    st.divider()
    render_top_churn_reasons(customer_data)
    
    # #4 - Recommendations
    st.divider()
    render_action_recommendations(customer_data)
    
    # #5 - What-If Simulator
    st.divider()
    render_whatif_simulator(customer_data)


# ============================================================================
# AGGREGATE DASHBOARD VISUALIZATIONS
# ============================================================================

def render_dashboard_header(
    all_predictions_df: pd.DataFrame,
) -> None:
    """Display dashboard summary metrics."""
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    high_risk = (all_predictions_df["ensemble_churn_prob"] > 0.70).sum()
    medium_risk = ((all_predictions_df["ensemble_churn_prob"] > 0.40) & (all_predictions_df["ensemble_churn_prob"] <= 0.70)).sum()
    low_risk = (all_predictions_df["ensemble_churn_prob"] <= 0.40).sum()
    total_customers = len(all_predictions_df)
    total_revenue_at_risk = all_predictions_df["revenue_at_risk"].sum()
    
    with col1:
        st.metric("Total Customers", f"{total_customers:,}")
    
    with col2:
        st.metric(
            "High Risk",
            f"{high_risk:,}",
            f"{high_risk/total_customers*100:.1f}%",
        )
    
    with col3:
        st.metric(
            "Medium Risk",
            f"{medium_risk:,}",
            f"{medium_risk/total_customers*100:.1f}%",
        )
    
    with col4:
        st.metric(
            "Low Risk",
            f"{low_risk:,}",
            f"{low_risk/total_customers*100:.1f}%",
        )
    
    with col5:
        st.metric(
            "Revenue at Risk",
            f"${total_revenue_at_risk/1e6:.1f}M",
            f"Annual MRR: ${total_revenue_at_risk*12/1e6:.1f}M",
        )


def render_dashboard_chart1_risk_distribution(
    all_predictions_df: pd.DataFrame,
) -> None:
    """CHART #1 - Risk Distribution (Pie/Donut)."""
    
    risk_counts = all_predictions_df["risk_level"].value_counts()
    
    fig = px.pie(
        values=risk_counts.values,
        names=risk_counts.index,
        title="Customer Risk Distribution",
        color_discrete_map={
            "High Risk": "#FF4444",
            "Medium Risk": "#FFB84D",
            "Low Risk": "#00CC44",
        },
        hole=0.4,
    )
    
    fig.update_layout(height=400, margin=dict(l=50, r=50, t=80, b=50))
    st.plotly_chart(fig, use_container_width=True)


def render_dashboard_chart2_trend_by_plan(
    all_predictions_df: pd.DataFrame,
) -> None:
    """CHART #2 - Churn Trend by Plan Type (Line Chart)."""
    
    # Create simulated trend data (in production, use historical data)
    # For now, show current risk distribution by plan
    
    if "plan_type" not in all_predictions_df.columns:
        return
    
    plan_risk = all_predictions_df.groupby("plan_type")["ensemble_churn_prob"].mean() * 100
    
    fig = px.bar(
        x=plan_risk.index,
        y=plan_risk.values,
        title="Average Churn Risk by Plan Type",
        labels={"y": "Average Churn Risk (%)", "x": "Plan Type"},
        color=plan_risk.index,
        color_discrete_map={
            "Starter": "#3B82F6",
            "Professional": "#F97316",
            "Enterprise": "#EF4444",
        },
    )
    
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def render_dashboard_chart3_revenue_at_risk(
    all_predictions_df: pd.DataFrame,
) -> None:
    """CHART #3 - Revenue at Risk by Plan (Stacked Bar)."""
    
    if "plan_type" not in all_predictions_df.columns:
        return
    
    revenue_by_plan = all_predictions_df.groupby("plan_type")["revenue_at_risk"].sum() / 1e6
    
    fig = px.bar(
        x=revenue_by_plan.index,
        y=revenue_by_plan.values,
        title="Annual Revenue at Risk by Plan",
        labels={"y": "Revenue at Risk ($M/year)", "x": "Plan Type"},
        color=revenue_by_plan.index,
        color_discrete_map={
            "Starter": "#3B82F6",
            "Professional": "#F97316",
            "Enterprise": "#EF4444",
        },
        text_position="outside",
    )
    
    fig.update_traces(texttemplate="$%{y:.1f}M", textposition="outside")
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def render_dashboard_chart4_top_drivers(
    all_predictions_df: pd.DataFrame,
) -> None:
    """CHART #4 - Top Churn Drivers (Horizontal Bar)."""
    
    # Analyze which features correlate with high churn
    high_churn = all_predictions_df[all_predictions_df["ensemble_churn_prob"] > 0.70]
    
    drivers = {
        "Inactivity (>30 days)": (high_churn["days_since_last_login_mean"] > 30).sum(),
        "Payment Delays (>15 days)": (high_churn["payment_delay_days_mean"] > 15).sum(),
        "Open Support Tickets (>5)": (high_churn["support_total_tickets"] > 5).sum(),
        "Low NPS (<40)": (high_churn["nps_score_mean"] < 40).sum(),
    }
    
    drivers_df = pd.DataFrame(
        {"Factor": list(drivers.keys()), "Count": list(drivers.values())}
    )
    drivers_df["Percentage"] = drivers_df["Count"] / len(high_churn) * 100
    drivers_df = drivers_df.sort_values("Count", ascending=True)
    
    fig = px.barh(
        drivers_df,
        x="Percentage",
        y="Factor",
        title="Top Factors in High-Risk Customers",
        labels={"Percentage": "% of High-Risk Customers", "Factor": ""},
        text_position="outside",
    )
    
    fig.update_traces(marker_color="#FF4444", texttemplate="%{x:.0f}%")
    fig.update_layout(height=350, margin=dict(l=200, r=50, t=80, b=50))
    st.plotly_chart(fig, use_container_width=True)


def render_dashboard_chart5_health_trend(
    all_predictions_df: pd.DataFrame,
) -> None:
    """CHART #5 - Customer Health Trend (Area Chart)."""
    
    # Create simulated trend data
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    good = [75, 73, 71, 68, 65, 60]
    at_risk = [20, 21, 22, 24, 28, 30]
    critical = [5, 6, 7, 8, 7, 10]
    
    trend_df = pd.DataFrame({
        "Month": months,
        "Good": good,
        "At Risk": at_risk,
        "Critical": critical,
    })
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=trend_df["Month"],
        y=trend_df["Good"],
        fill="tonexty",
        name="Good (Low Risk)",
        line_color="#00CC44",
        fillcolor="rgba(0, 204, 68, 0.3)",
    ))
    
    fig.add_trace(go.Scatter(
        x=trend_df["Month"],
        y=trend_df["At Risk"],
        fill="tonexty",
        name="At Risk (Medium)",
        line_color="#FFB84D",
        fillcolor="rgba(255, 184, 77, 0.3)",
    ))
    
    fig.add_trace(go.Scatter(
        x=trend_df["Month"],
        y=trend_df["Critical"],
        fill="tozeroy",
        name="Critical (High Risk)",
        line_color="#FF4444",
        fillcolor="rgba(255, 68, 68, 0.3)",
    ))
    
    fig.update_layout(
        title="Customer Health Trend (6 Months)",
        xaxis_title="",
        yaxis_title="% of Customers",
        height=400,
        hovermode="x unified",
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_main_dashboard_page(
    all_predictions_df: pd.DataFrame,
) -> None:
    """Main aggregate dashboard page."""
    
    st.header("📊 Churn Analytics Dashboard")
    st.markdown("**Aggregate insights across your entire customer base**")
    
    # Summary metrics
    render_dashboard_header(all_predictions_df)
    st.divider()
    
    # Charts in 2x3 grid
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Risk Distribution")
        render_dashboard_chart1_risk_distribution(all_predictions_df)
    
    with col2:
        st.markdown("### Risk by Plan Type")
        render_dashboard_chart2_trend_by_plan(all_predictions_df)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Revenue at Risk")
        render_dashboard_chart3_revenue_at_risk(all_predictions_df)
    
    with col2:
        st.markdown("### Top Churn Drivers")
        render_dashboard_chart4_top_drivers(all_predictions_df)
    
    st.divider()
    
    st.markdown("### Health Trend (6 Months)")
    render_dashboard_chart5_health_trend(all_predictions_df)
