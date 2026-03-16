-- Fee Trends
--
-- Purpose: Track network fee costs over time
-- Visualization: Line chart (dual axis for total vs average)
-- Table: dune.tsmereka.dataset_hedera_daily_stats (pre-aggregated from Hedera Mirror Node)

SELECT
    date,
    total_fees_hbar,
    avg_fee_hbar
FROM dune.tsmereka.dataset_hedera_daily_stats
ORDER BY date
