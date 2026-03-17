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

### HCS Activity (Stretch)

Companion dashboard to the [hiero-hcs-relay](https://github.com/kaldun-tech/hiero-hcs-relay) hackathon project, tracking Hedera Consensus Service activity.

## Project Structure

```
queries/
  network-health/     # Core dashboard SQL queries
  hcs-specific/       # HCS-focused queries
docs/
  schema.md           # Hedera table schemas on Dune
```

## Status

- [x] Phase 1: ETL pipeline development
- [x] Phase 2: Data import & upload
- [x] Phase 3: Dashboard build
- [ ] Phase 4: Automation (GitHub Actions)
- [ ] Phase 5: Publish & share

See [PLAN.md](PLAN.md) for detailed build plan.

## Links

- [Live Dashboard on Dune](https://dune.com/tsmereka_team_70e514cb/hedera-daily-transaction-volume)
- [Dune Docs](https://docs.dune.com)
- [Hedera Mirror Node API](https://docs.hedera.com/hedera/sdks-and-apis/rest-api)
