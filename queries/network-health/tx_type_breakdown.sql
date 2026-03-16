-- Transaction Type Breakdown
--
-- Purpose: Show distribution of transaction types over time
-- Visualization: Stacked area chart (by date) or pie chart (totals)
-- Table: dune.tsmereka.dataset_hedera_daily_stats (pre-aggregated from Hedera Mirror Node)

-- Daily breakdown (for stacked area chart)
SELECT
    date,
    tx_type_crypto,
    tx_type_hcs,
    tx_type_token,
    tx_type_contract,
    tx_type_other
FROM dune.tsmereka.dataset_hedera_daily_stats
ORDER BY date

-- Uncomment below for total breakdown (pie chart)
-- SELECT
--     'Crypto Transfer' AS tx_type, SUM(tx_type_crypto) AS tx_count
-- FROM dune.tsmereka.dataset_hedera_daily_stats
-- UNION ALL
-- SELECT 'HCS', SUM(tx_type_hcs) FROM dune.tsmereka.dataset_hedera_daily_stats
-- UNION ALL
-- SELECT 'Token', SUM(tx_type_token) FROM dune.tsmereka.dataset_hedera_daily_stats
-- UNION ALL
-- SELECT 'Smart Contract', SUM(tx_type_contract) FROM dune.tsmereka.dataset_hedera_daily_stats
-- UNION ALL
-- SELECT 'Other', SUM(tx_type_other) FROM dune.tsmereka.dataset_hedera_daily_stats
