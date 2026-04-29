\set ON_ERROR_STOP on

-- Run this file from psql, not from pgAdmin query editor.
-- Example:
-- psql -U postgres -d churn_ravenstack -f database/02_import_ravenstack_psql.sql

\copy accounts (
    account_id,
    account_name,
    industry,
    country,
    signup_date,
    referral_source,
    plan_tier,
    seats,
    is_trial,
    churn_flag
) FROM 'D:/ngoding/Customer_Churn_Prediction/archive (1)/ravenstack_accounts.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

\copy subscriptions (
    subscription_id,
    account_id,
    start_date,
    end_date,
    plan_tier,
    seats,
    mrr_amount,
    arr_amount,
    is_trial,
    upgrade_flag,
    downgrade_flag,
    churn_flag,
    billing_frequency,
    auto_renew_flag
) FROM 'D:/ngoding/Customer_Churn_Prediction/archive (1)/ravenstack_subscriptions.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

\copy feature_usage (
    usage_id,
    subscription_id,
    usage_date,
    feature_name,
    usage_count,
    usage_duration_secs,
    error_count,
    is_beta_feature
) FROM 'D:/ngoding/Customer_Churn_Prediction/archive (1)/ravenstack_feature_usage.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

\copy support_tickets (
    ticket_id,
    account_id,
    submitted_at,
    closed_at,
    resolution_time_hours,
    priority,
    first_response_time_minutes,
    satisfaction_score,
    escalation_flag
) FROM 'D:/ngoding/Customer_Churn_Prediction/archive (1)/ravenstack_support_tickets.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

\copy churn_events (
    churn_event_id,
    account_id,
    churn_date,
    reason_code,
    refund_amount_usd,
    preceding_upgrade_flag,
    preceding_downgrade_flag,
    is_reactivation,
    feedback_text
) FROM 'D:/ngoding/Customer_Churn_Prediction/archive (1)/ravenstack_churn_events.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');