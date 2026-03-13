-- Active Accounts (Unique Senders Per Day)
--
-- Purpose: Track daily active users to measure network adoption
-- Visualization: Line chart
--
-- TODO: Verify sender/from column name from schema exploration
-- Expected columns: date, unique_accounts

SELECT
    DATE_TRUNC('day', block_time) AS date,
    COUNT(DISTINCT sender) AS unique_accounts
FROM hedera.transactions
WHERE block_time >= NOW() - INTERVAL '90 days'
GROUP BY 1
ORDER BY 1
