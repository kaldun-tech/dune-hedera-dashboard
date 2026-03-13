-- HCS Daily Message Volume
--
-- Purpose: Track Hedera Consensus Service message activity over time
-- Context: Companion metric to hiero-hcs-relay hackathon project
-- Visualization: Line chart
--
-- TODO: Verify HCS table exists (hedera.consensus_messages or similar)
-- Expected columns: date, message_count

SELECT
    DATE_TRUNC('day', consensus_timestamp) AS date,
    COUNT(*) AS message_count
FROM hedera.consensus_messages
WHERE consensus_timestamp >= NOW() - INTERVAL '90 days'
GROUP BY 1
ORDER BY 1
