# Build Plan: Dune Hedera Dashboard

> **Status:** Phases 1-5 complete. Dashboard live and automated.

## Overview

Dune has no native Hedera tables (only ERC token events). This project imports data from the **Hedera Mirror Node API** and uploads it to Dune as community tables.

### Architecture

```
┌─────────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│ Hedera Mirror Node  │ ───► │ Python ETL       │ ───► │ Dune Upload API │
│ REST API            │      │ scripts/         │      │ Community Table │
└─────────────────────┘      └──────────────────┘      └─────────────────┘
```

## Completed Phases

### Phase 1: ETL Pipeline ✓

Built streaming ETL that aggregates during fetch to handle Hedera's high transaction volume (5M+ tx/day).

Key insight: Naive fetch-store-transform approach took 20+ hours. Streaming aggregation reduced this dramatically.

### Phase 2: Data Import ✓

- Community table: `dataset_hedera_daily_stats`
- 30-day rolling window
- Incremental updates (fetches only new data)

### Phase 3: Dashboard ✓

Live at: https://dune.com/tsmereka_team_70e514cb/hedera-daily-transaction-volume

Panels:
- Daily Transaction Volume
- Transaction Type Breakdown
- Active Accounts
- Fee Trends

### Phase 4: Automation ✓

GitHub Actions workflow runs daily at 6 AM UTC:
- `.github/workflows/refresh-hedera-data.yml`
- `DUNE_API_KEY` secret configured

### Phase 5: Publish ✓

- Blog post: https://taraskaldun.substack.com/p/building-a-hedera-network-health
- Dashboard public on Dune

## Future Work

### Extend to 90 Days

**Scope:** Minimal — incremental fetching already handles backfill automatically.

Changes:
1. `config.py:21` — Change `DAYS_TO_FETCH = 30` to `90`
2. Run pipeline to backfill (may need multiple runs due to 45-min GitHub Actions timeout)

**Value:** Quarterly trend visibility for investors/analysts evaluating Hedera adoption.

### HCS Dashboard for Developers

**Scope:** Most infrastructure already built. Needs queries and visualization.

ETL pipeline status:
- [x] `fetch_hcs_messages.py` — Full incremental fetch with timeout handling
- [x] `upload_to_dune.py` — HCS upload to `dataset_hedera_hcs_daily`
- [x] `run_pipeline.py` — Orchestration (currently disabled with `--skip-hcs`)

Remaining work:
1. Enable HCS in CI — Change workflow `skip_hcs` default from `true` to `false`
2. Write Dune SQL queries:
   - Daily HCS message volume
   - Active topics over time
   - Message size trends
3. Add panels to Dune dashboard

HCS data model (already defined):
```
date              | Date string
message_count     | Total HCS messages that day
unique_topics     | Distinct topic IDs
total_message_size| Total payload bytes
```

**Value:** Developers evaluating HCS can see real adoption metrics before building on it.

## References

- [Hedera Mirror Node REST API](https://docs.hedera.com/hedera/sdks-and-apis/rest-api)
- [Dune CSV Upload API](https://docs.dune.com/api-reference/tables/endpoint/upload)
