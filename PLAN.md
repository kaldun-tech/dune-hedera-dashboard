# Build Plan: Dune Hedera Dashboard

> **Updated:** 2026-03-13 — HashScan Import + Dune Upload approach

## Overview

Dune has limited native Hedera data (only ERC token events). This plan imports data from the **Hedera Mirror Node API** and uploads it to Dune as community tables.

### Architecture

```
┌─────────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│ Hedera Mirror Node  │ ───► │ Python ETL       │ ───► │ Dune Upload API │
│ REST API            │      │ scripts/         │      │ Community Table │
└─────────────────────┘      └──────────────────┘      └─────────────────┘
```

### Data Sources

| Source | Endpoint | Data |
|--------|----------|------|
| Mirror Node | `https://mainnet-public.mirrornode.hedera.com/api/v1/` | Transactions, HCS, Accounts |
| Dune Upload | `POST https://api.dune.com/api/v1/table/upload/csv` | Community tables |

### Key Constraints

- Dune CSV upload: 200MB max per upload
- Free tier: 1MB storage / Plus: 15GB / Premium: 50GB
- Column names can't start with special chars or digits
- Addresses must be lowercase

---

## Phase 1: ETL Script Development

**Goal:** Build Python scripts to fetch Hedera data and prepare for Dune upload

### 1.1 Project Setup

```
scripts/
  requirements.txt      # requests, pandas
  config.py             # API keys, endpoints
  fetch_transactions.py # Pull tx data from Mirror Node
  fetch_hcs_messages.py # Pull HCS topic messages
  transform.py          # Clean/format for Dune
  upload_to_dune.py     # Push CSV to Dune API
```

### 1.2 Mirror Node Endpoints to Use

| Endpoint | Purpose | Fields |
|----------|---------|--------|
| `/api/v1/transactions` | Network transactions | consensus_timestamp, name (type), charged_tx_fee, result, transfers |
| `/api/v1/topics/{id}/messages` | HCS messages | consensus_timestamp, topic_id, message, sequence_number |
| `/api/v1/accounts` | Active accounts | account, balance, created_timestamp |

### 1.3 Transaction Schema (from Mirror Node)

```
consensus_timestamp   # When consensus reached
name                  # Transaction type (CRYPTOTRANSFER, CONSENSUSSUBMITMESSAGE, etc.)
charged_tx_fee        # Actual fee in tinybars
result                # SUCCESS, FAILURE, etc.
transaction_hash      # Unique hash
entity_id             # Associated entity
transfers             # Array of {account, amount}
token_transfers       # Token movements
nft_transfers         # NFT movements
```

### Deliverables

- [ ] `scripts/requirements.txt`
- [ ] `scripts/fetch_transactions.py` — paginated fetch, 90 days
- [ ] `scripts/fetch_hcs_messages.py` — fetch from known topics
- [ ] `scripts/transform.py` — flatten JSON, format timestamps
- [ ] `scripts/upload_to_dune.py` — CSV upload via API

---

## Phase 2: Data Import & Upload

**Goal:** Fetch 90 days of Hedera data and upload to Dune

### 2.1 Tables to Create on Dune

| Dune Table | Source | Estimated Rows (90d) |
|------------|--------|---------------------|
| `dune.<username>.hedera_transactions` | /transactions | ~50M+ |
| `dune.<username>.hedera_hcs_messages` | /topics/*/messages | ~1M+ |
| `dune.<username>.hedera_daily_stats` | Aggregated | ~90 |

**Note:** Due to volume, we may need to upload aggregated daily stats instead of raw transactions.

### 2.2 Aggregation Strategy

Instead of raw transactions (too large), pre-aggregate in Python:

```python
# hedera_daily_stats columns:
date                  # DATE
tx_count              # Total transactions
tx_type_crypto        # CRYPTOTRANSFER count
tx_type_hcs           # CONSENSUSSUBMITMESSAGE count
tx_type_token         # TOKEN* count
tx_type_contract      # CONTRACTCALL count
unique_accounts       # Distinct senders
total_fees_hbar       # Sum of fees / 100_000_000
avg_fee_hbar          # Avg fee per tx
```

### 2.3 Execution Steps

1. **Test fetch** — Pull 1 day of data, validate structure
2. **Full fetch** — Pull 90 days with pagination (rate limit: ~25 req/sec)
3. **Aggregate** — Group by day, compute metrics
4. **Upload** — POST to Dune CSV endpoint

### Deliverables

- [ ] `data/hedera_daily_stats.csv` — 90 days of aggregated metrics
- [ ] `data/hedera_hcs_daily.csv` — HCS message counts per day
- [ ] Tables live on Dune: `dune.<username>.hedera_daily_stats`

---

## Phase 3: Query & Dashboard Build

**Goal:** Write queries against uploaded tables and build visualizations

### 3.1 Updated Queries (using uploaded tables)

| Query | SQL Target | Visualization |
|-------|------------|---------------|
| Daily TX Volume | `SELECT date, tx_count FROM dune.<user>.hedera_daily_stats` | Line chart |
| TX Type Breakdown | `SELECT date, tx_type_* FROM ...` | Stacked area |
| Active Accounts | `SELECT date, unique_accounts FROM ...` | Line chart |
| Fee Trends | `SELECT date, avg_fee_hbar FROM ...` | Line chart |
| HCS Activity | `SELECT date, message_count FROM dune.<user>.hedera_hcs_daily` | Line chart |

### 3.2 MCP Workflow

```
1. createDuneQuery → create query against uploaded table
2. executeQueryById → run and validate
3. generateVisualization → build chart
4. Repeat for each metric
```

### 3.3 Dashboard Layout

```
┌─────────────────────────────────────────────────────────┐
│  HEDERA NETWORK HEALTH                                  │
├─────────────────────────────────────────────────────────┤
│  [Counter: Total TX]  [Counter: Avg Fee]  [Counter: DAU]│
├─────────────────────────────────────────────────────────┤
│  [Line Chart: Daily Transaction Volume - 90 days]       │
├──────────────────────────┬──────────────────────────────┤
│  [Stacked: TX Types]     │  [Line: Active Accounts]     │
├──────────────────────────┴──────────────────────────────┤
│  [Line Chart: Fee Trends in HBAR]                       │
├─────────────────────────────────────────────────────────┤
│  [Line Chart: HCS Message Activity]                     │
└─────────────────────────────────────────────────────────┘
```

### Deliverables

- [ ] All queries created on Dune with IDs recorded
- [ ] Visualizations generated
- [ ] Dashboard assembled and set to public
- [ ] Dashboard URL in README.md

---

## Phase 4: Automation & Maintenance

**Goal:** Set up scheduled refresh for data freshness

### 4.1 Refresh Strategy

| Option | Approach | Complexity |
|--------|----------|------------|
| Manual | Re-run scripts weekly | Low |
| GitHub Actions | Scheduled workflow | Medium |
| Dune Materialized View | Transform on schedule | Medium |

### 4.2 GitHub Actions (Recommended)

```yaml
# .github/workflows/refresh-hedera-data.yml
name: Refresh Hedera Data
on:
  schedule:
    - cron: '0 6 * * 1'  # Weekly on Monday 6am UTC
  workflow_dispatch:     # Manual trigger

jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r scripts/requirements.txt
      - run: python scripts/fetch_transactions.py
      - run: python scripts/upload_to_dune.py
        env:
          DUNE_API_KEY: ${{ secrets.DUNE_API_KEY }}
```

### Deliverables

- [ ] `.github/workflows/refresh-hedera-data.yml`
- [ ] `DUNE_API_KEY` secret added to repo

---

## Phase 5: Publish & Share

### Tasks

- [ ] Update README.md with dashboard link
- [ ] Commit all finalized code to repo
- [ ] Write LinkedIn post (2-3 sentences + link + 1 insight)
- [ ] Add to portfolio at taras-smereka.dev
- [ ] Share in Hedera Discord (#dev or #community)
- [ ] Optional: Substack deep-dive post

### Post Template

> "Built a Hedera network health dashboard on @DuneAnalytics by importing data from the Mirror Node API.
> Key finding: [interesting data point about TX volume or HCS usage].
> Dashboard: [link]
> #Hedera #Blockchain #DataAnalytics"

---

## Execution Summary

| Phase | Tools | Output |
|-------|-------|--------|
| 1. ETL Scripts | Python, requests, pandas | `scripts/*.py` |
| 2. Data Import | Mirror Node API → Dune Upload | Community tables on Dune |
| 3. Dashboard | Dune MCP (createQuery, generateVisualization) | Public dashboard |
| 4. Automation | GitHub Actions | Weekly refresh |
| 5. Publish | — | LinkedIn, portfolio |

---

## Query ID Tracking

Record query IDs as they're created:

| Query | File | Dune Query ID | Status |
|-------|------|---------------|--------|
| Daily TX Volume | `queries/network-health/daily_tx_volume.sql` | — | pending |
| TX Type Breakdown | `queries/network-health/tx_type_breakdown.sql` | — | pending |
| Active Accounts | `queries/network-health/active_accounts.sql` | — | pending |
| Fee Trends | `queries/network-health/fee_trends.sql` | — | pending |
| HCS Daily Messages | `queries/hcs-specific/daily_messages.sql` | — | pending |
| HCS Active Topics | `queries/hcs-specific/active_topics.sql` | — | pending |

---

## Environment Variables

```bash
# .env (do not commit)
DUNE_API_KEY=your_dune_api_key
HEDERA_MIRROR_URL=https://mainnet-public.mirrornode.hedera.com
```

---

## Open Questions (Resolved)

1. ~~What Hedera tables exist on Dune?~~ → Only ERC token events; need to import
2. ~~Is HCS data available?~~ → Must fetch from Mirror Node `/topics/{id}/messages`
3. ~~Is HBAR price data on Dune?~~ → Check `prices.usd` table or import separately
4. ~~Can we build queries programmatically?~~ → Yes, via Dune MCP
5. **New:** Which HCS topic IDs to track? → Need to identify active topics

---

## References

- [Hedera Mirror Node REST API](https://docs.hedera.com/hedera/sdks-and-apis/rest-api)
- [Dune CSV Upload API](https://docs.dune.com/api-reference/tables/endpoint/upload)
- [Query Messages with Mirror Node](https://docs.hedera.com/hedera/tutorials/consensus/query-messages-with-mirror-node)
