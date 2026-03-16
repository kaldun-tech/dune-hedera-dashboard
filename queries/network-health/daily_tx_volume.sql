-- Daily Transaction Volume
--
-- Purpose: Show total transaction count per day to visualize network activity trends
-- Visualization: Line chart with trend line
-- Table: dune.tsmereka.dataset_hedera_daily_stats (pre-aggregated from Hedera Mirror Node)

SELECT
    date,
    tx_count
FROM dune.tsmereka.dataset_hedera_daily_stats
ORDER BY date
