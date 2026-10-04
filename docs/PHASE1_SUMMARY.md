# Phase 1 Summary (Verified Against Code)

## Related docs

- [Project README](../README.md)
- [Quick Start](QUICKSTART.md)
- [System Design](design.md)
- [Implementation Guide](implementation.md)
- [Upgrading](UPGRADING.md)
- [Source Guide](../src/README.md)

## Implemented

- FastAPI API with grouped routers (`auth`, `requests`, `matches`, `calendar`)
- JWT authentication and role-aware dependencies
- Dev login endpoint (`/api/auth/dev-login`) for local/testing mode
- Seek/volunteer request CRUD with soft-cancel semantics
- Auto-expiration of stale active requests
- Matching service using route + (flight OR time-window) predicate
- Match discovery endpoint returning details for both seeker and volunteer perspectives
- Volunteer accept/reject actions
- Calendar event creation from requests and browse APIs
- Email notification helpers with log-only mode by default

## Not implemented in current code

- Refresh token issuance/rotation endpoint
- Point-based weighted matching score (stored score is `1.0` for matches)
- Public unauthenticated calendar browsing
- Full migration framework (manual scripts are used when needed)

## Test status

Current test suite (`src/tests`) passes with `pytest`.
