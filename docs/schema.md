# Hedera Schema on Dune

Document table schemas discovered during Phase 1 exploration.

## Tables to Investigate

- [ ] `hedera.transactions` — main transaction table
- [ ] `hedera.consensus_messages` — HCS messages (may not exist)
- [ ] Price data tables (HBAR/USD)

---

## hedera.transactions

**Status:** Not yet explored

| Column | Type | Notes |
|--------|------|-------|
| | | |

### Sample Values

```sql
-- TODO: Run exploration query
SELECT * FROM hedera.transactions LIMIT 10
```

### Transaction Types

```sql
-- TODO: Discover transaction type enums
SELECT DISTINCT transaction_type FROM hedera.transactions
```

---

## hedera.consensus_messages

**Status:** Not yet explored — may not exist as separate table

| Column | Type | Notes |
|--------|------|-------|
| | | |

---

## Date Range Available

```sql
-- TODO: Check data availability
SELECT
    MIN(block_time) AS earliest,
    MAX(block_time) AS latest
FROM hedera.transactions
```

---

## Notes

- Add findings from exploration session here
- Document any quirks or data quality issues
