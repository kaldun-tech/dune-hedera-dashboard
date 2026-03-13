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

- [ ] Phase 1: Schema exploration
- [ ] Phase 2: Query development
- [ ] Phase 3: Dashboard build
- [ ] Phase 4: Publish & share

See [PLAN.md](PLAN.md) for detailed build plan.

## Links

- [Dune Docs](https://docs.dune.com)
- Dashboard: *(not yet published)*
