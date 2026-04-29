-- Validation checks for the local RavenStack setup.

SELECT 'accounts' AS table_name, COUNT(*) AS row_count FROM accounts
UNION ALL
SELECT 'subscriptions', COUNT(*) FROM subscriptions
UNION ALL
SELECT 'feature_usage', COUNT(*) FROM feature_usage
UNION ALL
SELECT 'support_tickets', COUNT(*) FROM support_tickets
UNION ALL
SELECT 'churn_events', COUNT(*) FROM churn_events
UNION ALL
SELECT 'training_view', COUNT(*) FROM v_ravenstack_training_dataset;

SELECT COUNT(*) AS orphan_subscriptions
FROM subscriptions s
LEFT JOIN accounts a ON a.account_id = s.account_id
WHERE a.account_id IS NULL;

SELECT COUNT(*) AS orphan_feature_usage
FROM feature_usage f
LEFT JOIN subscriptions s ON s.subscription_id = f.subscription_id
WHERE s.subscription_id IS NULL;

SELECT COUNT(*) AS orphan_support_tickets
FROM support_tickets t
LEFT JOIN accounts a ON a.account_id = t.account_id
WHERE a.account_id IS NULL;

SELECT COUNT(*) AS orphan_churn_events
FROM churn_events c
LEFT JOIN accounts a ON a.account_id = c.account_id
WHERE a.account_id IS NULL;

SELECT *
FROM v_ravenstack_training_dataset
ORDER BY account_id
LIMIT 20;