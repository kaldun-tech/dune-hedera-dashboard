-- HCS Daily Message Volume
--
-- Purpose: Track Hedera Consensus Service message activity over time
-- Visualization: Line chart
-- Table: dune.tsmereka.dataset_hedera_hcs_daily (pre-aggregated from Hedera Mirror Node)

SELECT
    date,
    message_count,
    total_message_size
FROM dune.tsmereka.dataset_hedera_hcs_daily
ORDER BY date
