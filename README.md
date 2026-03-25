# Dune Hedera Dashboard

Public Dune Analytics dashboards for visualizing Hedera HashGraph network health and activity.

## Dashboards

### Hedera Network Health

**Core question:** What does Hedera's network activity look like — and is it growing?

Panels:
- Daily transaction volume (90 days)
- Transaction type breakdown (crypto transfer vs HCS vs token vs smart contract)
- Active accounts (unique senders per day)
- Fee trends (avg transaction fee in HBAR)

**Live Dashboard:** https://dune.com/tsmereka_team_70e514cb/hedera-daily-transaction-volume

### HCS Activity

Tracks Hedera Consensus Service message activity for developers evaluating HCS adoption.

Panels:
- Daily HCS message volume
- Active topics over time
- Message size trends

This dashboard supersedes the earlier [hedera-network-monitor](https://github.com/kaldun-tech/hedera-network-monitor) project. For direct Hedera interaction, see the official [Hiero CLI](https://github.com/hiero-ledger/hiero-cli).

## How It Works

Dune has no native Hedera tables. This project uses a Python ETL pipeline that:

1. Fetches data from the Hedera Mirror Node API (transactions + HCS messages)
2. Aggregates into daily statistics during fetch (streaming)
3. Uploads to Dune as community tables via their API

Two GitHub Actions workflows run daily:
- **Transactions** (6 AM UTC) — Network activity, fees, account stats
- **HCS** (6 PM UTC) — Consensus service message volume and topics

## Project Structure

```
scripts/
  fetch_transactions.py   # Transaction ETL (streaming aggregation)
  fetch_hcs_messages.py   # HCS message ETL
  upload_to_dune.py       # Upload to Dune community tables
  run_pipeline.py         # Orchestrates fetch → upload
data/
  hedera_daily_stats.csv  # Transaction aggregates
  hcs_daily_stats.csv     # HCS message aggregates
queries/
  network-health/         # Transaction dashboard queries
  hcs-specific/           # HCS dashboard queries
docs/
  schema.md               # Data model documentation
.github/workflows/
  update-dashboard.yml    # Transaction workflow (6 AM UTC)
  update-hcs-data.yml     # HCS workflow (6 PM UTC)
```

## Status

- [x] Phase 1: ETL pipeline development
- [x] Phase 2: Data import & upload (90-day rolling window)
- [x] Phase 3: Dashboard build
- [x] Phase 4: Automation (GitHub Actions)
- [x] Phase 5: Publish & share
- [x] Phase 6: HCS dashboard (pipeline complete, awaiting first data fetch)

## Links

- [Live Dashboard on Dune](https://dune.com/tsmereka_team_70e514cb/hedera-daily-transaction-volume)
- [Blog Post](https://taraskaldun.substack.com/p/building-a-hedera-network-health)
- [Hedera Mirror Node API](https://docs.hedera.com/hedera/sdks-and-apis/rest-api)
- [Dune Docs](https://docs.dune.com)
