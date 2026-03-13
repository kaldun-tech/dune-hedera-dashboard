# Build Plan: Dune Hedera Dashboard

> **Updated:** 2026-03-13 — MCP-enabled execution plan

## Overview

This plan uses the **Dune MCP tools** to programmatically build and deploy the dashboard:

| Tool | Purpose |
|------|---------|
| `searchTables` | Discover Hedera tables and schemas |
| `searchDocs` | Find documentation and examples |
| `listBlockchains` | Confirm Hedera is available |
| `createDuneQuery` | Create queries directly on Dune |
| `executeQueryById` | Run queries and validate results |
| `getExecutionResults` | Fetch query output |
| `generateVisualization` | Build charts from query results |
| `getTableSize` | Check data volume |

---

## Phase 1: Schema Discovery

**Goal:** Programmatically discover Hedera data on Dune

### Steps

1. **Confirm Hedera availability**
   - Run `listBlockchains` → verify "hedera" exists

2. **Discover tables**
   - Run `searchTables` with "hedera" → list all Hedera tables
   - For each table found, run `getTableSize` to check data volume

3. **Explore schemas**
   - Run `searchDocs` with "hedera transactions" → find documentation
   - Create exploration query: `SELECT * FROM <table> LIMIT 10`
   - Execute and capture column names/types

4. **Document findings**
   - Update `docs/schema.md` with discovered tables and columns
   - Note: transaction types, date ranges, key fields

### Deliverables

- [ ] `docs/schema.md` populated with actual Dune schemas
- [ ] Decision: confirm HCS data exists (separate table or filtered from transactions)
- [ ] List of validated table/column names for queries

---

## Phase 2: Query Development & Validation

**Goal:** Create and validate all SQL queries using MCP

### Network Health Queries

| Query | MCP Action | Visualization |
|-------|------------|---------------|
| Daily TX Volume | `createDuneQuery` → `executeQueryById` | Line chart |
| TX Type Breakdown | `createDuneQuery` → `executeQueryById` | Pie chart |
| Active Accounts | `createDuneQuery` → `executeQueryById` | Line chart |
| Fee Trends | `createDuneQuery` → `executeQueryById` | Line chart |

### HCS Queries (if data available)

| Query | MCP Action | Visualization |
|-------|------------|---------------|
| Daily HCS Messages | `createDuneQuery` → `executeQueryById` | Line chart |
| Active Topics | `createDuneQuery` → `executeQueryById` | Counter/table |
| Top Topics | `createDuneQuery` → `executeQueryById` | Bar chart |

### Workflow per Query

```
1. Read local .sql file
2. Fix column/table names based on Phase 1 schema
3. createDuneQuery → get query_id
4. executeQueryById(query_id) → get execution_id
5. getExecutionResults(execution_id) → validate output
6. If errors, update query and re-execute
7. Save final validated SQL back to repo
```

### Deliverables

- [ ] All queries created on Dune with query IDs recorded
- [ ] Query results validated (no errors, reasonable data)
- [ ] Local `.sql` files updated with corrected schemas

---

## Phase 3: Visualization & Dashboard

**Goal:** Build visualizations programmatically

### Steps

1. **Generate visualizations**
   - For each validated query, run `generateVisualization`:
     - TX volume → line chart
     - TX breakdown → pie chart
     - Active accounts → area chart
     - Fee trends → line chart with dual axis (optional HBAR price)

2. **Dashboard assembly**
   - Visualizations created via MCP are automatically saved to queries
   - Arrange in Dune UI (manual step — MCP doesn't control dashboard layout)
   - Add dashboard title and descriptions

3. **Final QA**
   - Check time ranges display correctly
   - Verify mobile responsiveness
   - Test parameter filters if any

### Deliverables

- [ ] Visualizations generated for all queries
- [ ] Dashboard URL recorded in README.md
- [ ] Dashboard set to public

---

## Phase 4: Publish & Share

### Automated Tasks

- [ ] Update README.md with dashboard link
- [ ] Commit all finalized queries to repo

### Manual Tasks

- [ ] Write LinkedIn post (2-3 sentences + link + 1 insight)
- [ ] Add to portfolio at taras-smereka.dev
- [ ] Share in Hedera Discord (#dev or #community)
- [ ] Optional: Substack deep-dive post

### Post Template

> "Built a Hedera network health dashboard on @DuneAnalytics using the MCP API.
> Key finding: [interesting data point].
> Dashboard: [link]"

---

## Execution Summary

| Phase | MCP Tools | Output |
|-------|-----------|--------|
| 1. Discovery | `listBlockchains`, `searchTables`, `searchDocs`, `getTableSize` | `docs/schema.md` |
| 2. Queries | `createDuneQuery`, `executeQueryById`, `getExecutionResults` | Query IDs, validated SQL |
| 3. Visualize | `generateVisualization` | Charts + dashboard |
| 4. Publish | — | LinkedIn, portfolio |

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

## Open Questions

1. ~~What Hedera tables exist on Dune?~~ → Phase 1 will answer via `searchTables`
2. ~~Is HCS data available?~~ → Phase 1 will confirm
3. Is HBAR price data available? → Check `prices.usd` or similar table
4. ~~Can we build queries programmatically?~~ → Yes, via Dune MCP
