# Upgrading Yatra

## Related docs

- [Project README](../README.md)
- [Quick Start](QUICKSTART.md)
- [System Design](design.md)
- [Implementation Guide](implementation.md)
- [Phase 1 Summary](PHASE1_SUMMARY.md)
- [Source Guide](../src/README.md)

This project initializes schema with `Base.metadata.create_all()`, which does not modify existing columns.
For type changes in existing databases, run manual migration scripts.

---

## Schema changes

### `calendar_events.is_public` – String → Boolean

**Affects:** deployments created before this column type was changed.

Run:

```bash
# Set DATABASE_URL if needed
export DATABASE_URL=sqlite:///./yatra.db   # or your PostgreSQL URL

python migrations/001_calendar_is_public_boolean.py
```

Behavior:

- SQLite: converts values in-place through table rebuild
- PostgreSQL: uses `ALTER TABLE ... TYPE BOOLEAN USING ...`
- Other dialects: script exits with guidance/non-zero status

Fresh databases created after the change do not need this migration.
