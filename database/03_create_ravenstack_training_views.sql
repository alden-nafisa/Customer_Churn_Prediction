-- One-row-per-account rollup for model training and dashboard analysis.

CREATE OR REPLACE VIEW v_ravenstack_account_rollup AS
WITH subscription_stats AS (
    SELECT
        account_id,
        COUNT(*) AS subscription_count,
        COUNT(*) FILTER (WHERE churn_flag) AS churned_subscription_count,
        COUNT(*) FILTER (WHERE is_trial) AS trial_subscription_count,
        COUNT(*) FILTER (WHERE upgrade_flag) AS upgrade_count,
        COUNT(*) FILTER (WHERE downgrade_flag) AS downgrade_count,
        COUNT(*) FILTER (WHERE auto_renew_flag) AS auto_renew_true_count,
        SUM(seats) AS total_subscription_seats,
        ROUND(AVG(seats)::numeric, 2) AS avg_subscription_seats,
        SUM(mrr_amount) AS total_mrr_amount,
        ROUND(AVG(mrr_amount)::numeric, 2) AS avg_mrr_amount,
        SUM(arr_amount) AS total_arr_amount,
        ROUND(AVG(arr_amount)::numeric, 2) AS avg_arr_amount,
        MIN(start_date) AS first_subscription_start_date,
        MAX(start_date) AS last_subscription_start_date,
        MAX(end_date) AS last_subscription_end_date
    FROM subscriptions
    GROUP BY account_id
),
latest_subscription AS (
    SELECT DISTINCT ON (account_id)
        account_id,
        subscription_id AS latest_subscription_id,
        start_date AS latest_subscription_start_date,
        end_date AS latest_subscription_end_date,
        plan_tier AS latest_subscription_plan_tier,
        billing_frequency AS latest_subscription_billing_frequency,
        auto_renew_flag AS latest_subscription_auto_renew_flag,
        churn_flag AS latest_subscription_churn_flag
    FROM subscriptions
    ORDER BY account_id, start_date DESC, subscription_id DESC
),
usage_stats AS (
    SELECT
        s.account_id,
        COUNT(f.id) AS feature_usage_event_rows,
        COUNT(DISTINCT f.feature_name) AS distinct_features_used,
        COALESCE(SUM(f.usage_count), 0) AS total_usage_count,
        COALESCE(SUM(f.usage_duration_secs), 0) AS total_usage_duration_secs,
        COALESCE(SUM(f.error_count), 0) AS total_usage_error_count,
        COALESCE(SUM(CASE WHEN f.is_beta_feature THEN 1 ELSE 0 END), 0) AS beta_usage_event_count,
        ROUND(AVG(f.usage_count)::numeric, 2) AS avg_usage_count_per_event,
        ROUND(AVG(f.usage_duration_secs)::numeric, 2) AS avg_usage_duration_secs_per_event,
        ROUND(AVG(f.error_count)::numeric, 2) AS avg_error_count_per_event,
        MIN(f.usage_date) AS first_usage_date,
        MAX(f.usage_date) AS last_usage_date
    FROM subscriptions s
    LEFT JOIN feature_usage f
        ON f.subscription_id = s.subscription_id
    GROUP BY s.account_id
),
support_stats AS (
    SELECT
        account_id,
        COUNT(*) AS ticket_count,
        COUNT(*) FILTER (WHERE closed_at IS NULL) AS open_ticket_count,
        COUNT(*) FILTER (WHERE escalation_flag) AS escalation_count,
        COUNT(*) FILTER (WHERE priority = 'urgent') AS urgent_ticket_count,
        COUNT(*) FILTER (WHERE priority = 'high') AS high_ticket_count,
        ROUND(AVG(resolution_time_hours)::numeric, 2) AS avg_resolution_time_hours,
        ROUND(AVG(first_response_time_minutes)::numeric, 2) AS avg_first_response_time_minutes,
        ROUND(AVG(satisfaction_score)::numeric, 2) AS avg_satisfaction_score,
        MIN(submitted_at) AS first_ticket_at,
        MAX(submitted_at) AS last_ticket_at,
        MAX(closed_at) AS last_closed_at
    FROM support_tickets
    GROUP BY account_id
),
churn_stats AS (
    SELECT
        account_id,
        COUNT(*) AS churn_event_count,
        COUNT(*) FILTER (WHERE is_reactivation) AS reactivation_count,
        COUNT(*) FILTER (WHERE preceding_upgrade_flag) AS preceding_upgrade_count,
        COUNT(*) FILTER (WHERE preceding_downgrade_flag) AS preceding_downgrade_count,
        COUNT(DISTINCT reason_code) AS distinct_reason_count,
        SUM(refund_amount_usd) AS total_refund_amount_usd,
        MIN(churn_date) AS first_churn_date,
        MAX(churn_date) AS last_churn_date
    FROM churn_events
    GROUP BY account_id
),
latest_churn AS (
    SELECT DISTINCT ON (account_id)
        account_id,
        churn_event_id AS latest_churn_event_id,
        churn_date AS latest_churn_date,
        reason_code AS latest_reason_code,
        refund_amount_usd AS latest_refund_amount_usd,
        preceding_upgrade_flag AS latest_preceding_upgrade_flag,
        preceding_downgrade_flag AS latest_preceding_downgrade_flag,
        is_reactivation AS latest_is_reactivation
    FROM churn_events
    ORDER BY account_id, churn_date DESC, churn_event_id DESC
)
SELECT
    a.account_id,
    a.account_name,
    a.industry,
    a.country,
    a.signup_date,
    a.referral_source,
    a.plan_tier AS account_plan_tier,
    a.seats AS account_seats,
    a.is_trial AS account_is_trial,
    a.churn_flag AS target_churn_flag,

    COALESCE(ss.subscription_count, 0) AS subscription_count,
    COALESCE(ss.churned_subscription_count, 0) AS churned_subscription_count,
    COALESCE(ss.trial_subscription_count, 0) AS trial_subscription_count,
    COALESCE(ss.upgrade_count, 0) AS upgrade_count,
    COALESCE(ss.downgrade_count, 0) AS downgrade_count,
    COALESCE(ss.auto_renew_true_count, 0) AS auto_renew_true_count,
    COALESCE(ss.total_subscription_seats, 0) AS total_subscription_seats,
    COALESCE(ss.avg_subscription_seats, 0) AS avg_subscription_seats,
    COALESCE(ss.total_mrr_amount, 0) AS total_mrr_amount,
    COALESCE(ss.avg_mrr_amount, 0) AS avg_mrr_amount,
    COALESCE(ss.total_arr_amount, 0) AS total_arr_amount,
    COALESCE(ss.avg_arr_amount, 0) AS avg_arr_amount,
    ss.first_subscription_start_date,
    ss.last_subscription_start_date,
    ss.last_subscription_end_date,

    ls.latest_subscription_id,
    ls.latest_subscription_start_date,
    ls.latest_subscription_end_date,
    ls.latest_subscription_plan_tier,
    ls.latest_subscription_billing_frequency,
    ls.latest_subscription_auto_renew_flag,
    ls.latest_subscription_churn_flag,

    COALESCE(us.feature_usage_event_rows, 0) AS feature_usage_event_rows,
    COALESCE(us.distinct_features_used, 0) AS distinct_features_used,
    COALESCE(us.total_usage_count, 0) AS total_usage_count,
    COALESCE(us.total_usage_duration_secs, 0) AS total_usage_duration_secs,
    COALESCE(us.total_usage_error_count, 0) AS total_usage_error_count,
    COALESCE(us.beta_usage_event_count, 0) AS beta_usage_event_count,
    COALESCE(us.avg_usage_count_per_event, 0) AS avg_usage_count_per_event,
    COALESCE(us.avg_usage_duration_secs_per_event, 0) AS avg_usage_duration_secs_per_event,
    COALESCE(us.avg_error_count_per_event, 0) AS avg_error_count_per_event,
    us.first_usage_date,
    us.last_usage_date,

    COALESCE(ts.ticket_count, 0) AS ticket_count,
    COALESCE(ts.open_ticket_count, 0) AS open_ticket_count,
    COALESCE(ts.escalation_count, 0) AS escalation_count,
    COALESCE(ts.urgent_ticket_count, 0) AS urgent_ticket_count,
    COALESCE(ts.high_ticket_count, 0) AS high_ticket_count,
    COALESCE(ts.avg_resolution_time_hours, 0) AS avg_resolution_time_hours,
    COALESCE(ts.avg_first_response_time_minutes, 0) AS avg_first_response_time_minutes,
    COALESCE(ts.avg_satisfaction_score, 0) AS avg_satisfaction_score,
    ts.first_ticket_at,
    ts.last_ticket_at,
    ts.last_closed_at,

    COALESCE(cs.churn_event_count, 0) AS churn_event_count,
    COALESCE(cs.reactivation_count, 0) AS reactivation_count,
    COALESCE(cs.preceding_upgrade_count, 0) AS preceding_upgrade_count,
    COALESCE(cs.preceding_downgrade_count, 0) AS preceding_downgrade_count,
    COALESCE(cs.distinct_reason_count, 0) AS distinct_reason_count,
    COALESCE(cs.total_refund_amount_usd, 0) AS total_refund_amount_usd,
    cs.first_churn_date,
    cs.last_churn_date,

    lc.latest_churn_event_id,
    lc.latest_churn_date,
    lc.latest_reason_code,
    lc.latest_refund_amount_usd,
    lc.latest_preceding_upgrade_flag,
    lc.latest_preceding_downgrade_flag,
    lc.latest_is_reactivation,

    GREATEST(
        COALESCE(ss.last_subscription_start_date, DATE '1900-01-01'),
        COALESCE(ss.last_subscription_end_date, DATE '1900-01-01'),
        COALESCE(us.last_usage_date, DATE '1900-01-01'),
        COALESCE(ts.last_ticket_at::date, DATE '1900-01-01'),
        COALESCE(cs.last_churn_date, DATE '1900-01-01')
    ) AS latest_activity_date,

    GREATEST(
        COALESCE(ss.last_subscription_start_date, DATE '1900-01-01'),
        COALESCE(ss.last_subscription_end_date, DATE '1900-01-01'),
        COALESCE(us.last_usage_date, DATE '1900-01-01'),
        COALESCE(ts.last_ticket_at::date, DATE '1900-01-01'),
        COALESCE(cs.last_churn_date, DATE '1900-01-01')
    ) - a.signup_date AS days_from_signup_to_latest_activity,

    COALESCE(ss.last_subscription_start_date, a.signup_date) - a.signup_date AS days_from_signup_to_last_subscription,
    COALESCE(us.last_usage_date, a.signup_date) - a.signup_date AS days_from_signup_to_last_usage,
    COALESCE(ts.last_ticket_at::date, a.signup_date) - a.signup_date AS days_from_signup_to_last_ticket,
    COALESCE(cs.last_churn_date, a.signup_date) - a.signup_date AS days_from_signup_to_last_churn
FROM accounts a
LEFT JOIN subscription_stats ss
    ON ss.account_id = a.account_id
LEFT JOIN latest_subscription ls
    ON ls.account_id = a.account_id
LEFT JOIN usage_stats us
    ON us.account_id = a.account_id
LEFT JOIN support_stats ts
    ON ts.account_id = a.account_id
LEFT JOIN churn_stats cs
    ON cs.account_id = a.account_id
LEFT JOIN latest_churn lc
    ON lc.account_id = a.account_id;

CREATE OR REPLACE VIEW v_ravenstack_training_dataset AS
SELECT *
FROM v_ravenstack_account_rollup;