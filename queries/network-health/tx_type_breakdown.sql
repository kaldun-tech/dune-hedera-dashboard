-- Transaction Type Breakdown
--
-- Purpose: Show distribution of transaction types (crypto transfer, HCS, token, smart contract)
-- Visualization: Pie chart or horizontal bar chart
--
-- TODO: Verify transaction_type column name and enum values from schema exploration
-- Expected columns: tx_type, tx_count, percentage

SELECT
    transaction_type AS tx_type,
    COUNT(*) AS tx_count,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () AS percentage
FROM hedera.transactions
WHERE block_time >= NOW() - INTERVAL '90 days'
GROUP BY 1
ORDER BY 2 DESC
