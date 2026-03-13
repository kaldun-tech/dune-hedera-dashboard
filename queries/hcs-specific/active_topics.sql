-- HCS Active Topics Per Day
--
-- Purpose: Track unique topic IDs with message activity
-- Visualization: Line chart
--
-- TODO: Verify topic_id column name from schema exploration
-- Expected columns: date, active_topics

SELECT
    DATE_TRUNC('day', consensus_timestamp) AS date,
    COUNT(DISTINCT topic_id) AS active_topics
FROM hedera.consensus_messages
WHERE consensus_timestamp >= NOW() - INTERVAL '90 days'
GROUP BY 1
ORDER BY 1
