-- HCS Active Topics Per Day
--
-- Purpose: Track unique topic IDs with message activity
-- Visualization: Line chart
-- Table: dune.tsmereka.dataset_hedera_hcs_daily (pre-aggregated from Hedera Mirror Node)

SELECT
    date,
    unique_topics
FROM dune.tsmereka.dataset_hedera_hcs_daily
ORDER BY date
