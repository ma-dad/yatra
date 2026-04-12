"""
Migration 001 – Convert calendar_events.is_public from String to Boolean
=========================================================================

Background
----------
A previous version of the app declared ``CalendarEvent.is_public`` as a
``String`` column. It has since been changed to a ``Boolean`` column
(default ``True``).  ``Base.metadata.create_all()`` does **not** alter
existing columns, so this script must be run once against any database
that was created before the schema change.

What this script does
---------------------
* SQLite: rebuilds the ``calendar_events`` table using the standard
  SQLite table-rename technique so that ``is_public`` becomes an
  ``INTEGER`` column (SQLAlchemy maps Python ``bool`` to ``INTEGER`` on
  SQLite).  String values ``'true'`` / ``'1'`` / ``'yes'`` are converted
  to ``1``; everything else becomes ``0``.

* PostgreSQL / other RDBMS: issues an ``ALTER TABLE … ALTER COLUMN … TYPE``
  statement with a ``USING`` clause that converts the stored string to a
  boolean.

Usage
-----
    python migrations/001_calendar_is_public_boolean.py

The script reads ``DATABASE_URL`` from the environment (or falls back to the
value in ``.env`` if python-dotenv is installed).  You can also pass the URL
directly::

    DATABASE_URL=postgresql://user:pass@host/db \\
        python migrations/001_calendar_is_public_boolean.py
"""

import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./yatra.db")


def run_migration(database_url: str) -> None:
    engine = create_engine(database_url)

    with engine.begin() as conn:
        dialect = engine.dialect.name

        if dialect == "sqlite":
            # SQLite does not support ALTER COLUMN TYPE.  Use the standard
            # table-rebuild technique so that is_public is stored as INTEGER.
            conn.execute(text("PRAGMA foreign_keys = OFF"))

            conn.execute(text("""
                CREATE TABLE calendar_events_new (
                    id          TEXT    PRIMARY KEY,
                    user_id     TEXT    NOT NULL,
                    user_type   TEXT    NOT NULL,
                    request_id  TEXT    NOT NULL,
                    event_type  TEXT    NOT NULL,
                    title       TEXT    NOT NULL,
                    travel_details TEXT NOT NULL,
                    is_public   INTEGER NOT NULL DEFAULT 1,
                    created_at  DATETIME,
                    updated_at  DATETIME
                )
            """))

            conn.execute(text("""
                INSERT INTO calendar_events_new
                    (id, user_id, user_type, request_id, event_type,
                     title, travel_details, is_public, created_at, updated_at)
                SELECT
                    id, user_id, user_type, request_id, event_type,
                    title, travel_details,
                    CASE
                        WHEN lower(cast(is_public AS TEXT)) IN ('true', '1', 'yes') THEN 1
                        ELSE 0
                    END,
                    created_at, updated_at
                FROM calendar_events
            """))

            conn.execute(text("DROP TABLE calendar_events"))
            conn.execute(text("ALTER TABLE calendar_events_new RENAME TO calendar_events"))
            conn.execute(text("PRAGMA foreign_keys = ON"))

            count = conn.execute(text("SELECT count(*) FROM calendar_events")).scalar()
            print(f"[SQLite] Rebuilt table with {count} row(s); is_public is now INTEGER")

        elif dialect == "postgresql":
            conn.execute(text("""
                ALTER TABLE calendar_events
                ALTER COLUMN is_public TYPE BOOLEAN
                USING (
                    CASE
                        WHEN lower(is_public::text) IN ('true', '1', 'yes') THEN TRUE
                        ELSE FALSE
                    END
                )
            """))
            print("[PostgreSQL] Altered column calendar_events.is_public to BOOLEAN")

        else:
            print(
                f"[{dialect}] Automatic migration not implemented for this dialect. "
                "Please manually convert calendar_events.is_public from a string/varchar "
                "column to a boolean/tinyint column, mapping 'true'/'1' → true and "
                "everything else → false.",
                file=sys.stderr,
            )
            sys.exit(1)

    print("Migration 001 completed successfully.")


if __name__ == "__main__":
    run_migration(DATABASE_URL)
