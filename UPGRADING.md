# Upgrading Yatra

This file documents manual upgrade steps required when moving between versions.
Run these steps **in order** against your existing database before restarting
the application.

---

## Schema changes

### `calendar_events.is_public` – String → Boolean

**Affects:** deployments created before the `is_public` column type was
changed from `String` to `Boolean`.

`Base.metadata.create_all()` does not alter existing columns, so existing
databases still store string values (`"true"` / `"false"`) in this column.
Run the bundled migration script to convert those values to integers that
SQLAlchemy can read as Python booleans:

```bash
# Set DATABASE_URL if it isn't already in your environment / .env file
export DATABASE_URL=sqlite:///./yatra.db   # or your PostgreSQL URL

python migrations/001_calendar_is_public_boolean.py
```

The script handles both **SQLite** (updates values in-place) and
**PostgreSQL** (issues `ALTER TABLE … ALTER COLUMN … TYPE BOOLEAN USING …`).
For other databases it prints instructions and exits with a non-zero status.

**Fresh deployments** (databases created after the schema change) do not need
this step – `create_all()` will create the column with the correct type.
