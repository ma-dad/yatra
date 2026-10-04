# Implementation Guide (Current Repository)

## Related docs

- [Project README](../README.md)
- [Quick Start](QUICKSTART.md)
- [System Design](design.md)
- [Phase 1 Summary](PHASE1_SUMMARY.md)
- [Upgrading](UPGRADING.md)
- [Source Guide](../src/README.md)

## Stack

- Python + FastAPI
- SQLAlchemy ORM
- SQLite default (`DATABASE_URL=sqlite:///./yatra.db`)
- Pydantic schemas
- JWT with `python-jose`
- Optional Google token verification (`google-auth`)

## App startup

- `src/app/main.py` defines app and routers
- Lifespan startup calls `init_db()`
- `init_db()` uses `Base.metadata.create_all(bind=engine)`

## Configuration (`.env`)

Important variables:

- `DATABASE_URL`
- `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- `ENABLE_GOOGLE_AUTH`
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- `EMAIL_LOG_ONLY`, `SMTP_*`
- `SEEKER_REQUEST_LIMIT`, `VOLUNTEER_REQUEST_LIMIT`
- `MATCH_TIME_BUFFER_HOURS`

## API behavior notes

- Request creation auto-creates matching calendar events
- Requests auto-expire by `expires_at`
- Match acceptance triggers contact exchange emails
- Seek cancellation notifies volunteers with accepted matches
- Email sending is log-only unless `EMAIL_LOG_ONLY=false` and SMTP is configured

## Development commands

Run API:

```bash
cd src
uvicorn app.main:app --reload
```

Run tests:

```bash
cd src
pytest
```

## Migration note

Because `create_all()` does not alter existing columns, schema-type changes require manual migration scripts.
See [UPGRADING.md](UPGRADING.md).
