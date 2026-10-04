# Yatra

Community travel-assistance backend built with FastAPI.

## Documentation

- [Quick Start](docs/QUICKSTART.md)
- [System Design](docs/design.md)
- [Implementation Guide](docs/implementation.md)
- [Phase 1 Summary](docs/PHASE1_SUMMARY.md)
- [Upgrading Guide](docs/UPGRADING.md)
- [Source Directory Guide](src/README.md)

## Current Scope (implemented)

- FastAPI API with docs at `/api/docs` and `/api/redoc`
- Auth:
  - `POST /api/auth/dev-login` (default for development when `ENABLE_GOOGLE_AUTH=false`)
  - `POST /api/auth/google` (enabled when `ENABLE_GOOGLE_AUTH=true`)
  - `POST /api/auth/logout`
- Seek and volunteer request CRUD
- Match discovery and volunteer accept/reject flow
- Calendar APIs:
  - `GET /api/calendar/` (own events)
  - `GET /api/calendar/all` (other authenticated users)
- Email notifications (log-only by default via `EMAIL_LOG_ONLY=true`)
- SQLite by default (`sqlite:///./yatra.db`) with SQLAlchemy

## Running locally

```bash
cd src
uvicorn app.main:app --reload
```

Then open:

- Homepage/API root: http://localhost:8000/
- Swagger: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- Health: http://localhost:8000/health

## Tests

```bash
cd src
pytest
```
