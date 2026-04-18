# Yatra Platform - Phase 1 Implementation

This directory contains the Phase 1 implementation of the Yatra platform, focusing on building the foundation with essential features.

## Features Implemented

### ✅ User Operations
- User registration for both seekers and volunteers
- Google OAuth authentication
- JWT token-based authorization
- User profile management

### ✅ Request Management
- Create/Read/Update/Delete seek requests (for seekers)
- Create/Read/Update/Delete volunteer requests (for volunteers)
- Request status tracking
- Automatic expiration based on travel time

### ✅ Matching System
- Basic flight matching algorithm based on:
  - Flight number (highest priority)
  - Airport route (source → destination)
  - Travel time proximity (±4 hours)
  - Assistance categories
- Compatibility scoring (0-100)
- Match discovery for both seekers and volunteers
- Accept/Reject match functionality

### ✅ Calendar System
- Automatic calendar event creation from requests
- View personal travel calendar
- View public calendar (discover other travelers)
- Filter by date range and airport

### ✅ Email Notifications (Basic)
- Match notifications
- Contact exchange after acceptance
- Configurable SMTP settings

## Project Structure

```
src/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database setup and session management
│   ├── dependencies.py      # FastAPI dependencies (auth, etc.)
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py          # User, Seeker, Volunteer models
│   │   ├── request.py       # SeekRequest, VolunteerRequest models
│   │   ├── match.py         # Match model
│   │   └── calendar.py      # CalendarEvent model
│   ├── schemas/             # Pydantic schemas for validation
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication schemas
│   │   ├── user.py          # User schemas
│   │   ├── request.py       # Request schemas
│   │   ├── match.py         # Match schemas
│   │   └── calendar.py      # Calendar schemas
│   ├── routers/             # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── requests.py      # Request CRUD endpoints
│   │   ├── matches.py       # Match discovery and actions
│   │   └── calendar.py      # Calendar view endpoints
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   └── matching_service.py  # Matching algorithm
│   └── utils/               # Utility functions
│       ├── __init__.py
│       ├── auth.py          # JWT and OAuth utilities
│       └── email.py         # Email notification utilities
├── tests/                   # Unit and integration tests
└── static/                  # Static files (future frontend)
```

## Getting Started

### Prerequisites
- Python 3.11 or higher
- pipenv (or pip)

### Installation

1. Clone the repository and navigate to the project root:
```bash
cd /path/to/yatra
```

2. Install dependencies:
```bash
pip install pipenv
pipenv install --dev
```

3. Activate the virtual environment:
```bash
pipenv shell
```

4. Create environment configuration:
```bash
cp .env.example .env
# Edit .env with your Google OAuth credentials
```

### Running the Application

Start the development server:
```bash
cd src
uvicorn app.main:app --reload
```

The API will be available at:
- API: http://localhost:8000
- Swagger Documentation: http://localhost:8000/api/docs
- ReDoc Documentation: http://localhost:8000/api/redoc

### API Documentation

Interactive API documentation is automatically generated and available at:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## API Endpoints

### Authentication
- `POST /api/auth/google` - Login/Register with Google OAuth
- `POST /api/auth/logout` - Logout

### Seek Requests (Seeker only)
- `POST /api/requests/seek` - Create seek request
- `GET /api/requests/seek` - List all seek requests
- `GET /api/requests/seek/{id}` - Get specific seek request
- `PUT /api/requests/seek/{id}` - Update seek request
- `DELETE /api/requests/seek/{id}` - Delete seek request

### Volunteer Requests (Volunteer only)
- `POST /api/requests/volunteer` - Create volunteer request
- `GET /api/requests/volunteer` - List all volunteer requests
- `GET /api/requests/volunteer/{id}` - Get specific volunteer request
- `PUT /api/requests/volunteer/{id}` - Update volunteer request
- `DELETE /api/requests/volunteer/{id}` - Delete volunteer request

### Matches
- `GET /api/matches/discover` - Discover matches
- `GET /api/matches/{id}` - Get match details
- `POST /api/matches/{id}/accept` - Accept match (volunteer only)
- `POST /api/matches/{id}/reject` - Reject match (volunteer only)

### Calendar
- `GET /api/calendar/` - Get user's calendar events
- `GET /api/calendar/all` - Browse all other authenticated users' calendar events

## Database

The application uses SQLite for development with the following models:

1. **User** - Base user model with Google OAuth
2. **Seeker** - Seeker-specific data
3. **Volunteer** - Volunteer-specific data
4. **SeekRequest** - Assistance requests from seekers
5. **VolunteerRequest** - Help offers from volunteers
6. **Match** - Connections between seekers and volunteers
7. **CalendarEvent** - Travel events for calendar view

## Testing

Run tests with pytest:
```bash
pytest
```

## Configuration

Key configuration options in `.env`:

- `DATABASE_URL` - Database connection string
- `SECRET_KEY` - JWT secret key
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret
- `SMTP_*` - Email notification settings (optional)

## Next Steps (Phase 2)

- User verification system
- Feedback and rating mechanism
- Enhanced matching based on preferences
- Improved privacy controls
- Better communication tools

## Contributing

Please refer to the main project documentation for contribution guidelines.

## License

See LICENSE file in the project root.
