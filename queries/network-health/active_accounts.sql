-- Active Accounts (Unique Senders Per Day)
--
-- Purpose: Track daily active users to measure network adoption
-- Visualization: Line chart
-- Table: dune.tsmereka.dataset_hedera_daily_stats (pre-aggregated from Hedera Mirror Node)

SELECT
    date,
    unique_accounts
FROM dune.tsmereka.dataset_hedera_daily_stats
ORDER BY date
