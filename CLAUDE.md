# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dune Analytics dashboard for Hedera HashGraph blockchain. Since Dune has no native Hedera tables, this project includes a Python ETL pipeline that fetches data from the Hedera Mirror Node API and uploads it to Dune as community tables.

## Project Structure

```
scripts/
  config.py             # Configuration (API URLs, data window, tx type mapping)
  fetch_transactions.py # ETL for transaction data (streaming aggregation)
  fetch_hcs_messages.py # ETL for HCS message data
  upload_to_dune.py     # Upload CSVs to Dune community tables
  run_pipeline.py       # Orchestrates fetch → transform → upload
queries/
  network-health/       # Core dashboard queries (tx volume, accounts, fees)
  hcs-specific/         # HCS queries (topic activity, message volume)
data/
  hedera_daily_stats.csv  # Aggregated transaction data
  hcs_daily_stats.csv     # Aggregated HCS data
.github/workflows/
  update-dashboard.yml    # Transaction data (6 AM UTC)
  update-hcs-data.yml     # HCS data (6 PM UTC)
```

## Dune Tables

Community tables (uploaded by ETL pipeline):
- `dune.tsmereka.dataset_hedera_daily_stats` — Daily transaction aggregates
- `dune.tsmereka.dataset_hedera_hcs_daily` — Daily HCS message aggregates

## Key Commands

```bash
# Run full pipeline locally
cd scripts && python run_pipeline.py

# Fetch only (no upload)
python run_pipeline.py --fetch

# Force re-fetch all data
python run_pipeline.py --fetch --force

# Skip HCS (faster for transaction-only updates)
python run_pipeline.py --skip-hcs

# HCS only (skip transactions)
python run_pipeline.py --hcs-only
```

## Architecture Notes

- **Streaming aggregation**: The ETL aggregates during fetch to handle Hedera's high transaction volume (5M+ tx/day)
- **Incremental fetching**: Only fetches missing date ranges, supports resumption after timeout
- **Graceful timeout**: Stops before GitHub Actions timeout, commits progress, continues on next run
