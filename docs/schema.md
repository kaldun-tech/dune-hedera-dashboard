# Hedera Data on Dune

## Native Dune Tables

**Finding:** Dune has no canonical Hedera tables for transactions, blocks, or HCS messages.

Available Hedera-related tables are limited to EVM-compatible token events:
- `erc20_hedera.evt_transfer` — ERC-20 token transfers on Hedera's EVM layer

For native Hedera data (transactions, HCS, token operations), you must upload your own community tables.

## Community Table: hedera_daily_stats

This project uploads aggregated daily statistics to Dune as `dataset_hedera_daily_stats`.

### Schema

| Column | Type | Description |
|--------|------|-------------|
| date | DATE | Transaction date |
| tx_count | INTEGER | Total transactions |
| tx_type_crypto | INTEGER | CRYPTOTRANSFER count |
| tx_type_hcs | INTEGER | CONSENSUSSUBMITMESSAGE count |
| tx_type_token | INTEGER | TOKEN* operations count |
| tx_type_contract | INTEGER | CONTRACTCALL count |
| tx_type_other | INTEGER | Other transaction types |
| unique_accounts | INTEGER | Distinct accounts per day |
| total_fees_hbar | DECIMAL | Sum of fees in HBAR |
| avg_fee_hbar | DECIMAL | Average fee per transaction |

### Data Source

Data is fetched from the Hedera Mirror Node API:
- Endpoint: `https://mainnet-public.mirrornode.hedera.com/api/v1/transactions`
- Aggregated during fetch (no raw transaction storage)
- 90-day rolling window, refreshed daily

### Transaction Type Mapping

Mirror Node `name` field → aggregation bucket:

| Mirror Node Type | Column |
|------------------|--------|
| CRYPTOTRANSFER | tx_type_crypto |
| CONSENSUSSUBMITMESSAGE | tx_type_hcs |
| TOKENMINT, TOKENBURN, TOKENTRANSFER, etc. | tx_type_token |
| CONTRACTCALL, CONTRACTCREATE | tx_type_contract |
| Everything else | tx_type_other |

## Community Table: hedera_hcs_daily

This project uploads aggregated HCS statistics to Dune as `dataset_hedera_hcs_daily`.

### Schema

| Column | Type | Description |
|--------|------|-------------|
| date | DATE | Message date |
| message_count | INTEGER | Total HCS messages |
| unique_topics | INTEGER | Distinct topic IDs with activity |
| total_message_size | INTEGER | Sum of message payload bytes |

### Data Source

Data is fetched from the Hedera Mirror Node API:
- Endpoint: `https://mainnet-public.mirrornode.hedera.com/api/v1/topics/{topicId}/messages`
- Topics discovered via CONSENSUSSUBMITMESSAGE transactions
- 90-day rolling window, refreshed daily

## Notes

- Fees are converted from tinybars (1 HBAR = 100,000,000 tinybars)
- Unique accounts are counted from the `transfers` array in each transaction
- Average fees typically range from 0.01-0.02 HBAR (~$0.001-0.002 USD)
