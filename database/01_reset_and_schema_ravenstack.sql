-- Local PostgreSQL setup for RavenStack archive 1
-- Run this once to reset the schema before importing the CSV files.

DROP VIEW IF EXISTS v_ravenstack_training_dataset;
DROP VIEW IF EXISTS v_ravenstack_account_rollup;

DROP TABLE IF EXISTS feature_usage;
DROP TABLE IF EXISTS churn_events;
DROP TABLE IF EXISTS support_tickets;
DROP TABLE IF EXISTS subscriptions;
DROP TABLE IF EXISTS accounts;

CREATE TABLE accounts (
    account_id TEXT PRIMARY KEY,
    account_name TEXT NOT NULL,
    industry TEXT NOT NULL,
    country TEXT NOT NULL,
    signup_date DATE NOT NULL,
    referral_source TEXT NOT NULL,
    plan_tier TEXT NOT NULL,
    seats INTEGER NOT NULL CHECK (seats >= 0),
    is_trial BOOLEAN NOT NULL,
    churn_flag BOOLEAN NOT NULL
);

CREATE TABLE subscriptions (
    subscription_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date DATE,
    plan_tier TEXT NOT NULL,
    seats INTEGER NOT NULL CHECK (seats >= 0),
    mrr_amount NUMERIC(12,2) NOT NULL CHECK (mrr_amount >= 0),
    arr_amount NUMERIC(12,2) NOT NULL CHECK (arr_amount >= 0),
    is_trial BOOLEAN NOT NULL,
    upgrade_flag BOOLEAN NOT NULL,
    downgrade_flag BOOLEAN NOT NULL,
    churn_flag BOOLEAN NOT NULL,
    billing_frequency TEXT NOT NULL,
    auto_renew_flag BOOLEAN NOT NULL
);

CREATE TABLE feature_usage (
    id BIGSERIAL PRIMARY KEY,
    usage_id TEXT NOT NULL,
    subscription_id TEXT NOT NULL REFERENCES subscriptions(subscription_id) ON DELETE CASCADE,
    usage_date DATE NOT NULL,
    feature_name TEXT NOT NULL,
    usage_count INTEGER NOT NULL CHECK (usage_count >= 0),
    usage_duration_secs INTEGER NOT NULL CHECK (usage_duration_secs >= 0),
    error_count INTEGER NOT NULL CHECK (error_count >= 0),
    is_beta_feature BOOLEAN NOT NULL
);

CREATE TABLE support_tickets (
    ticket_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
    submitted_at TIMESTAMP NOT NULL,
    closed_at TIMESTAMP,
    resolution_time_hours NUMERIC(10,2) NOT NULL CHECK (resolution_time_hours >= 0),
    priority TEXT NOT NULL,
    first_response_time_minutes INTEGER NOT NULL CHECK (first_response_time_minutes >= 0),
    satisfaction_score NUMERIC(3,1),
    escalation_flag BOOLEAN NOT NULL,
    CHECK (satisfaction_score IS NULL OR (satisfaction_score >= 1 AND satisfaction_score <= 5))
);

CREATE TABLE churn_events (
    churn_event_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
    churn_date DATE NOT NULL,
    reason_code TEXT NOT NULL,
    refund_amount_usd NUMERIC(12,2) NOT NULL CHECK (refund_amount_usd >= 0),
    preceding_upgrade_flag BOOLEAN NOT NULL,
    preceding_downgrade_flag BOOLEAN NOT NULL,
    is_reactivation BOOLEAN NOT NULL,
    feedback_text TEXT
);

CREATE INDEX idx_subscriptions_account_id ON subscriptions(account_id);
CREATE INDEX idx_feature_usage_subscription_id ON feature_usage(subscription_id);
CREATE INDEX idx_feature_usage_usage_date ON feature_usage(usage_date);
CREATE INDEX idx_support_tickets_account_id ON support_tickets(account_id);
CREATE INDEX idx_support_tickets_submitted_at ON support_tickets(submitted_at);
CREATE INDEX idx_churn_events_account_id ON churn_events(account_id);
CREATE INDEX idx_churn_events_churn_date ON churn_events(churn_date);