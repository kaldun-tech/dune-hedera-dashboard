-- HCS Message Size Trends
--
-- Purpose: Track average message payload size over time
-- Visualization: Line chart
-- Table: dune.tsmereka.dataset_hedera_hcs_daily (pre-aggregated from Hedera Mirror Node)

SELECT
    date,
    message_count,
    total_message_size,
    CASE
        WHEN message_count > 0 THEN total_message_size / message_count
        ELSE 0
    END AS avg_message_size_bytes
FROM dune.tsmereka.dataset_hedera_hcs_daily
WHERE message_count > 0
ORDER BY date
