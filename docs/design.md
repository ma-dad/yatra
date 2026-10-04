# System Design (Code-Accurate)

## Related docs

- [Project README](../README.md)
- [Quick Start](QUICKSTART.md)
- [Implementation Guide](implementation.md)
- [Phase 1 Summary](PHASE1_SUMMARY.md)
- [Upgrading](UPGRADING.md)
- [Source Guide](../src/README.md)

## Architecture

- Backend: FastAPI (`src/app/main.py`)
- DB layer: SQLAlchemy models + session dependency
- Startup: `init_db()` runs `Base.metadata.create_all(bind=engine)`
- Static homepage served from `src/static/index.html`

## Auth model

- JWT bearer auth for protected routes
- Development auth flow:
  - `POST /api/auth/dev-login` (active when `ENABLE_GOOGLE_AUTH=false`)
- Production auth flow:
  - `POST /api/auth/google` (requires `ENABLE_GOOGLE_AUTH=true`)
- `POST /api/auth/logout` returns a success message (no token revocation backend yet)

## Domain model

- `User` (base user record)
- `Seeker` and `Volunteer` role rows (both can exist for same user)
- `SeekRequest` and `VolunteerRequest`
- `Match`
- `CalendarEvent`

## Status enums

- Request status: `active | matched | completed | cancelled | expired`
- Match status: `pending | accepted | rejected | completed | cancelled`

## Matching rules

A pair is a match when:

1. source + destination airports are identical, and
2. either flight numbers match OR travel times are within `MATCH_TIME_BUFFER_HOURS` (default 4).

Stored `match_score` is currently constant `1.0` for matched pairs.

## API groups

- Auth: `/api/auth/*`
- Requests: `/api/requests/*`
- Matches: `/api/matches/*`
- Calendar: `/api/calendar/*`

## Calendar visibility

- `GET /api/calendar/`: current user events
- `GET /api/calendar/all`: other authenticated users' events (current user's events excluded)
