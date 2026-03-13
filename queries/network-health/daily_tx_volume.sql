-- Daily Transaction Volume (90 days)
--
-- Purpose: Show total transaction count per day to visualize network activity trends
-- Visualization: Line chart with trend line
--
-- TODO: Verify table name and column names from Dune schema exploration
-- Expected columns: date, tx_count

SELECT
    DATE_TRUNC('day', block_time) AS date,
    COUNT(*) AS tx_count
FROM hedera.transactions
WHERE block_time >= NOW() - INTERVAL '90 days'
GROUP BY 1
ORDER BY 1
