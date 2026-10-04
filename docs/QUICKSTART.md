# Quick Start

## Related docs

- [Project README](../README.md)
- [System Design](design.md)
- [Implementation Guide](implementation.md)
- [Phase 1 Summary](PHASE1_SUMMARY.md)
- [Upgrading](UPGRADING.md)
- [Source Guide](../src/README.md)

## Prerequisites

- Python 3.11+
- pip

## 1) Install dependencies

```bash
pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings pydantic[email] \
  python-jose[cryptography] google-auth python-multipart python-dotenv httpx \
  passlib bcrypt pytest pytest-asyncio
```

## 2) Configure environment

```bash
cp .env.example .env
```

Default development behavior:

- `ENABLE_GOOGLE_AUTH=false` → use `/api/auth/dev-login`
- `EMAIL_LOG_ONLY=true` → emails are logged, not sent

## 3) Run the API

```bash
cd src
uvicorn app.main:app --reload
```

Endpoints:

- `http://localhost:8000/`
- `http://localhost:8000/api/docs`
- `http://localhost:8000/api/redoc`
- `http://localhost:8000/health`

## 4) Run tests

```bash
cd src
pytest
```

## 5) First auth call in development

```bash
curl -X POST http://localhost:8000/api/auth/dev-login \
  -H "Content-Type: application/json" \
  -d '{"email":"dev@example.com","user_type":"seeker"}'
```
