# Dune Hedera Dashboard

Public Dune Analytics dashboards for visualizing Hedera HashGraph network health and activity.

## Dashboards

### Hedera Network Health

**Core question:** What does Hedera's network activity look like — and is it growing?

Panels:
- Daily transaction volume (30 days)
- Transaction type breakdown (crypto transfer vs HCS vs token vs smart contract)
- Active accounts (unique senders per day)
- Fee trends (avg transaction fee in HBAR)

**Live Dashboard:** https://dune.com/tsmereka_team_70e514cb/hedera-daily-transaction-volume

### HCS Activity (Stretch)

Tracks Hedera Consensus Service message activity. This dashboard supersedes the earlier [hedera-network-monitor](https://github.com/kaldun-tech/hedera-network-monitor) project. For direct Hedera interaction, see the official [Hiero CLI](https://github.com/hiero-ledger/hiero-cli).

## How It Works

Dune has no native Hedera tables for transactions. This project uses a Python ETL pipeline that:

1. Fetches transaction data from the Hedera Mirror Node API
2. Aggregates into daily statistics during fetch (streaming)
3. Uploads to Dune as a community table via their API

The pipeline runs daily via GitHub Actions.

## Project Structure

```
scripts/
  hedera_etl.py         # Main ETL script (fetch + aggregate + upload)
  requirements.txt      # Python dependencies
data/
  hedera_daily_stats.csv  # Latest aggregated data
queries/
  network-health/       # Dune SQL queries for dashboard
docs/
  schema.md             # Data model documentation
.github/workflows/
  refresh-hedera-data.yml  # Daily automation
```

## Status

- [x] Phase 1: ETL pipeline development
- [x] Phase 2: Data import & upload
- [x] Phase 3: Dashboard build
- [x] Phase 4: Automation (GitHub Actions)
- [x] Phase 5: Publish & share

## Links

- [Live Dashboard on Dune](https://dune.com/tsmereka_team_70e514cb/hedera-daily-transaction-volume)
- [Blog Post](https://taraskaldun.substack.com/p/building-a-hedera-network-health)
- [Hedera Mirror Node API](https://docs.hedera.com/hedera/sdks-and-apis/rest-api)
- [Dune Docs](https://docs.dune.com)
