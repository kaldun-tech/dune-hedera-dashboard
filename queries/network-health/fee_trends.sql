-- Fee Trends (Average Transaction Fee in HBAR)
--
-- Purpose: Track network fee costs over time
-- Visualization: Line chart
--
-- TODO: Verify fee column name and units (tinybars vs HBAR) from schema exploration
-- Note: 1 HBAR = 100,000,000 tinybars
-- Expected columns: date, avg_fee_hbar

SELECT
    DATE_TRUNC('day', block_time) AS date,
    AVG(fee) / 100000000.0 AS avg_fee_hbar  -- Convert tinybars to HBAR
FROM hedera.transactions
WHERE block_time >= NOW() - INTERVAL '90 days'
GROUP BY 1
ORDER BY 1
