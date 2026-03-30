# Yatra Platform - Quick Start Guide

Get the Yatra platform up and running in minutes!

## Prerequisites

- Python 3.11 or higher
- pip or pipenv
- Git

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

**Note:** For development/testing, the default SECRET_KEY will work, but Google OAuth credentials are needed for authentication.

### 4. Run the Application

```bash
cd src
uvicorn app.main:app --reload
```

The application will start on `http://localhost:8000`

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
✅ **Smart Matching:** Algorithm matches seekers with volunteers based on:
   - Flight number (30 points)
   - Route match (40 points)
   - Time proximity (30 points)
   - Language/categories (20 points)
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
- `GET /api/calendar/public` - Get public events

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
