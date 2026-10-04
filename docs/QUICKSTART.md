# Yatra Platform - Quick Start Guide

Get the Yatra platform up and running in minutes!

## Related docs

- [Project README](../README.md)
- [System Design](design.md)
- [Implementation Guide](implementation.md)
- [Phase 1 Summary](PHASE1_SUMMARY.md)
- [Upgrading](UPGRADING.md)
- [Source Guide](../src/README.md)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/ma-dad/yatra.git
cd yatra
```

### 2. Install Dependencies

You can use either pip or pipenv:

**Using pip:**
```bash
pip install fastapi uvicorn sqlalchemy pydantic pydantic[email] pydantic-settings \
    python-jose[cryptography] google-auth python-multipart python-dotenv httpx \
    passlib bcrypt pytest pytest-asyncio
```

**Using pipenv (recommended):**
```bash
pip install pipenv
pipenv install --dev
pipenv shell
```

### 3. Configure Environment

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Default development behavior:

- `ENABLE_GOOGLE_AUTH=false` → use `/api/auth/dev-login`
- `EMAIL_LOG_ONLY=true` → emails are logged, not sent

Edit `.env` with your configuration:
```env
# Required for production
SECRET_KEY=your-super-secret-key-here
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Optional for email notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 4. Run the Application

```bash
cd src
uvicorn app.main:app --reload
```

The application will start on `http://localhost:8000`


### 5. Running using Docker (Optional)

This project includes a `Dockerfile` at the repository root to build a container that runs the FastAPI app located in `src/`.

Key points:
- The container installs dependencies from the top-level `Pipfile` (if present) using `pipenv`.
- The application code is placed at `/app/src` inside the container.
- A Docker volume at `/data` is used to persist the SQLite database file (recommended).
- Port `8000` is exposed by the container and the app runs with `uvicorn app.main:app` by default.

Build the image (run from the repository root):

```bash
docker build -t yatra:latest .
```

Run the container while mounting credentials and persisting the database:

# Example using an env file and mounting the Google client secret JSON
```bash
docker run --rm -p 8000:8000 \
  -v yatra_data:/data \
  --env-file ./path/to/.env \
  -v ./client_secret_ID.apps.googleusercontent.com.json:/app/creds/client_secret.json:ro \
  yatra:latest
```

Notes and tips:
- The container sets `DATABASE_URL=sqlite:////data/yatra.db` by default. If you prefer a different path or a different DB, provide `DATABASE_URL` via `--env-file` or `-e`.
- `--env-file` should contain values such as `SECRET_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` (or other env vars your app expects). If your app expects a client secret JSON file, mount it into the container (example above mounts it to `/app/creds/client_secret.json`).
- Persisted DB: the `yatra_data` named volume stores the SQLite DB at `/data/yatra.db`. Use a host bind mount instead if you prefer a local file path, e.g. `-v $(pwd)/data:/data`.
- For local development you might want to add `--mount type=bind,source=$(pwd)/src,target=/app/src` to pick up local code changes; then run with `--entrypoint` or set `CMD` to include `--reload` for uvicorn.

Example (host bind mount for DB and explicit env vars):

```bash
docker run --rm -p 8000:8000 \
  -v $(pwd)/data:/data \
  -v ./client_secret_ID.apps.googleusercontent.com.json:/app/creds/client_secret.json:ro \
  -e DATABASE_URL="sqlite:////data/yatra.db" \
  -e SECRET_KEY="your_jwt_secret" \
  -e GOOGLE_CLIENT_ID="your_google_client_id" \
  -e GOOGLE_CLIENT_SECRET="your_google_client_secret" \
  yatra:latest
```

If you need to run migrations or custom startup commands, consider overriding the container's command, e.g.:

```bash
docker run --rm -it yatra:latest /bin/bash
# then inside container run any setup steps
```

This should be enough to build and run the application in a containerized environment while keeping credentials outside the image and persisting the database.

### 5. Access the Application

- **Homepage:** http://localhost:8000
- **API Documentation:** http://localhost:8000/api/docs
- **Alternative Docs:** http://localhost:8000/api/redoc
- **Health Check:** http://localhost:8000/health

## Testing the API

### 1. Run Tests

```bash
cd src
pytest
```

### 2. Manual API Testing

Use the interactive Swagger UI at http://localhost:8000/api/docs to:

1. Authenticate with Google OAuth
2. Create seek or volunteer requests
3. Discover matches
4. Accept/reject matches
5. View calendar events

### Example API Request (using curl)

```bash

# First auth call in development
curl -X POST http://localhost:8000/api/auth/dev-login \
  -H "Content-Type: application/json" \
  -d '{"email":"dev@example.com","user_type":"seeker"}'

# Health check
curl http://localhost:8000/health

# Get API info
curl http://localhost:8000/

# View API documentation
curl http://localhost:8000/openapi.json
```

## Project Structure

```
yatra/
├── src/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration
│   │   ├── database.py          # Database setup
│   │   ├── dependencies.py      # Auth dependencies
│   │   ├── models/              # Database models
│   │   ├── routers/             # API endpoints
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # Business logic
│   │   └── utils/               # Utilities
│   ├── tests/                   # Test files
│   └── static/                  # Frontend files
├── .env.example                 # Environment template
├── Pipfile                      # Python dependencies
└── README.md                    # Documentation
```

## Key Features

✅ **User Authentication:** Google OAuth with JWT tokens
✅ **Request Management:** Create/update/delete seek and volunteer requests
✅ **Calendar System:** View and manage travel plans
✅ **Email Notifications:** Match alerts and contact exchange

## API Endpoints Overview

### Authentication
- `POST /api/auth/google` - Login/Register with Google
- `POST /api/auth/logout` - Logout

### Requests (Seeker)
- `POST /api/requests/seek` - Create seek request
- `GET /api/requests/seek` - List seek requests
- `GET /api/requests/seek/{id}` - Get seek request
- `PUT /api/requests/seek/{id}` - Update seek request
- `DELETE /api/requests/seek/{id}` - Delete seek request

### Requests (Volunteer)
- `POST /api/requests/volunteer` - Create volunteer request
- `GET /api/requests/volunteer` - List volunteer requests
- `GET /api/requests/volunteer/{id}` - Get volunteer request
- `PUT /api/requests/volunteer/{id}` - Update volunteer request
- `DELETE /api/requests/volunteer/{id}` - Delete volunteer request

### Matches
- `GET /api/matches/discover` - Discover matches
- `GET /api/matches/{id}` - Get match details
- `POST /api/matches/{id}/accept` - Accept match
- `POST /api/matches/{id}/reject` - Reject match

### Calendar
- `GET /api/calendar/` - Get user calendar events
- `GET /api/calendar/all` - Browse other authenticated users' calendar events (excluding the current user)

## Troubleshooting

### Database Issues
If you encounter database errors, delete the database file and restart:
```bash
rm yatra.db
uvicorn app.main:app --reload
```

### Import Errors
Make sure you're in the `src` directory when running the application:
```bash
cd src
python -c "from app.main import app; print('Success!')"
```

### Port Already in Use
If port 8000 is busy, use a different port:
```bash
uvicorn app.main:app --port 8080 --reload
```

## Development Tips

1. **Auto-reload:** Use `--reload` flag during development for automatic reloading
2. **Debug Mode:** Set `LOG_LEVEL=DEBUG` in `.env` for verbose logging
3. **Test Database:** Tests use a separate `test.db` file
4. **API Testing:** Use the Swagger UI for interactive API testing

## Next Steps

1. Set up Google OAuth credentials from [Google Cloud Console](https://console.cloud.google.com/)
2. Configure SMTP settings for email notifications (optional)
3. Explore the API documentation at `/api/docs`
4. Create your first seek or volunteer request
5. Test the matching algorithm

## Getting Help

- Read the detailed [implementation guide](implementation.md)
- Check the [design documentation](design.md)
- Review the [API documentation](http://localhost:8000/api/docs) (when server is running)
- Open an issue on GitHub

## License

See [LICENSE](LICENSE) file for details.
