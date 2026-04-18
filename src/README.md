# `src/` Developer Guide

This directory contains the runnable backend service and tests.

## Related docs

- [Project README](../README.md)
- [Quick Start](../docs/QUICKSTART.md)
- [System Design](../docs/design.md)
- [Implementation Guide](../docs/implementation.md)
- [Phase 1 Summary](../docs/PHASE1_SUMMARY.md)
- [Upgrading](../docs/UPGRADING.md)

## Structure

- `app/main.py` — FastAPI app, startup lifecycle, router mounting
- `app/config.py` — environment-driven settings
- `app/database.py` — engine/session/Base and `init_db()`
- `app/models/` — SQLAlchemy models
- `app/schemas/` — request/response schemas
- `app/routers/` — endpoint handlers
- `app/services/` — matching logic
- `app/utils/` — auth and email utilities
- `tests/` — integration/feature tests
- `static/` — static homepage

## Run

```bash
cd src
uvicorn app.main:app --reload
```

## Test

```bash
cd src
pytest
```

## Notes

- Default local auth path is `POST /api/auth/dev-login`.
- Google OAuth endpoint (`POST /api/auth/google`) is gated by `ENABLE_GOOGLE_AUTH=true`.
- Calendar “all” endpoint is authenticated and excludes current user’s own events.
