# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dune Analytics dashboard for Hedera HashGraph blockchain. This project contains SQL queries and documentation for building public dashboards on Dune that visualize Hedera network health metrics.

## Project Structure

```
queries/
  network-health/     # Core dashboard queries (transaction volume, active accounts, fees)
  hcs-specific/       # HCS-focused queries (topic activity, message volume)
docs/
  schema.md           # Hedera table schemas discovered on Dune
dashboards/
  *.json              # Dashboard configuration exports (if available from Dune)
```

## Core Dashboard: Hedera Network Health

Answers: "What does Hedera's network activity look like — and is it growing?"

Panels:
- Daily transaction volume (90 days)
- HCS message activity
- Transaction type breakdown (crypto transfers vs HCS vs token vs smart contract)
- Active accounts (unique senders per day)
- Fee trends (avg tx fee in HBAR)
- HBAR price overlay (optional)

## Stretch: HCS-Specific Dashboard

Companion to the hiero-hcs-relay hackathon submission — tracks HCS topic activity and message volume.

## Dune Tables

Primary tables to query (verify existence on Dune):
- `hedera.transactions`
- `hedera.consensus_messages`

## Workflow

1. Write/test queries in Dune query editor
2. Save working queries as `.sql` files in `queries/`
3. Document any schema discoveries in `docs/schema.md`
4. Build visualizations in Dune UI
5. Export dashboard config if possible
