# Yatra Platform - Implementation Guide

## Overview
This document provides comprehensive implementation guidelines for the Yatra platform backend, including datastore recommendations, Python framework selection, development setup, testing strategies, and deployment considerations.

---

## Datastore Strategy & Scalability

### SQLite for Development & MVP
**Why SQLite?**
- **Zero Configuration**: No setup required, perfect for local development
- **File-based**: Easy to backup, version control, and distribute
- **ACID Compliant**: Reliable transactions and data integrity
- **Lightweight**: Minimal resource footprint for initial testing
- **Python Integration**: Excellent support via `sqlite3` module

**SQLite Configuration:**
```python
# database/config.py
import sqlite3
from contextlib import contextmanager

DATABASE_URL = "sqlite:///yatra.db"

@contextmanager
def get_db_connection():
    conn = sqlite3.connect('yatra.db')
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    try:
        yield conn
    finally:
        conn.close()
```

### Scalability Migration Path
**Production Datastore:**
**PostgreSQL** (Recommended for production)
   - **Seamless SQLite Migration**: Both use SQL syntax, making migration straightforward
   - **JSON Support**: Native JSON/JSONB columns for flexible schemas (similar to our document structure)
   - **Strong ACID Properties**: Reliable transactions and data consistency
   - **Horizontal Scaling**: Read replicas, connection pooling, and partitioning support
   - **Full-text Search**: Built-in search capabilities for travel requests
   - **Wide Ecosystem**: Excellent Python support via psycopg2/asyncpg
   - **Cloud Support**: Available on all major cloud providers (AWS RDS, Google Cloud SQL, Azure)

**Migration Strategy:**
Environment-based database configuration allows seamless switching from SQLite (development) to PostgreSQL (production) using the same SQLAlchemy ORM code.

### Local Hosting Capabilities
**SQLite Advantages for Local Development:**
- **No Server Required**: Runs entirely within the application
- **Version Control Friendly**: Database file can be committed for testing
- **Cross-Platform**: Works on Windows, macOS, Linux
- **Instant Setup**: Clone repository and run immediately

**Local Development Setup:**
```bash
# Clone and setup
git clone <repository>
cd yatra-platform
pipenv install
pipenv shell
python manage.py runserver
```

---

## Python Framework Selection

### Recommended: FastAPI
**Why FastAPI?**
- **Modern**: Built with Python 3.6+ type hints
- **High Performance**: Comparable to NodeJS and Go
- **Automatic API Documentation**: Built-in Swagger/OpenAPI
- **Easy Testing**: Excellent testing support
- **Async Support**: Built-in async/await support
- **Google OAuth Integration**: Simple OAuth2 implementation

**Getting Started with FastAPI:**

1. **Project Structure:**
```
yatra-backend/
├── app/
│   ├── main.py              # FastAPI app instance & middleware
│   ├── dependencies.py      # Auth dependencies & database sessions
│   ├── database.py          # Database configuration
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic request/response schemas
│   ├── routers/             # API endpoint handlers
│   ├── services/            # Business logic layer
│   └── utils/               # Helper functions
├── tests/                   # Unit and integration tests
├── static/                  # Static frontend files (HTML/CSS/JS)
├── Pipfile                  # Dependencies
└── README.md
```

2. **Basic FastAPI Setup:**
```python
# app/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, users, requests, matches
from app.database import engine, Base
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Yatra Platform API",
    description="Community travel assistance platform",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(requests.router, prefix="/api/v1/requests", tags=["requests"])
app.include_router(matches.router, prefix="/api/v1/matches", tags=["matches"])

@app.get("/")
async def root():
    return {"message": "Yatra Platform API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```
### How FastAPI Handles Requests

**Request Flow:**
1. **Routing**: FastAPI matches URL patterns to specific handler functions
2. **Dependency Injection**: Automatically provides database sessions, authentication
3. **Validation**: Pydantic schemas validate incoming JSON data
4. **Processing**: Business logic in service layer handles the request
5. **Response**: Pydantic models serialize Python objects to JSON
6. **Documentation**: Swagger automatically documents all endpoints

**Key FastAPI Concepts:**
- **Routers**: Organize endpoints by feature (auth, users, requests)
- **Dependencies**: Reusable functions for auth, database, validation
- **Pydantic Schemas**: Define request/response data structures
- **Async Support**: Handle multiple requests concurrently
- **Middleware**: Process requests before they reach endpoints

---

## Required Libraries & Dependencies

### Core Dependencies
```toml
# Pipfile
[packages]
# Web Framework
fastapi = "~=0.104.1"               # Main web framework
uvicorn = "~=0.24.0"                # ASGI server - runs FastAPI applications

# Database & ORM
sqlalchemy = "~=2.0.23"             # Database ORM

# Data Validation
pydantic = {extras = ["email"], version = "~=2.5.0"}  # Request/response schemas

# Authentication & Security
python-jose = {extras = ["cryptography"], version = "~=3.3.0"}  # JWT tokens
google-auth = "~=2.23.4"            # Google OAuth
python-multipart = "~=0.0.6"        # Form data handling

# Utilities
python-dotenv = "~=1.0.0"           # Environment variables
httpx = "~=0.25.2"                  # HTTP client for testing

[dev-packages]
# Testing
pytest = "~=7.4.3"                 # Testing framework
pytest-asyncio = "~=0.21.1"        # Async testing support

# Code Quality
black = "~=23.11.0"                 # Code formatting
isort = "~=5.12.0"                  # Import sorting
flake8 = "~=6.1.0"                  # Linting

[requires]
python_version = "3.11"
```

### Why These Tools Are Essential

**Uvicorn - ASGI Server:**
- **Purpose**: Runs FastAPI applications in production and development
- **Why Needed**: FastAPI is a framework, not a server - needs Uvicorn to handle HTTP requests
- **Features**: High performance, supports async/await, hot reloading during development
- **Usage**: `uvicorn app.main:app --reload` (development) or `uvicorn app.main:app` (production)

### Python Core Modules Required
- **sqlite3**: Built-in SQLite database support
- **datetime**: Date/time handling for travel schedules
- **uuid**: Unique ID generation for users and requests
- **json**: JSON data processing
- **os**: Environment variable access
- **logging**: Application logging
- **asyncio**: Async/await support


### Package Management with Pipenv

**Why Pipenv?**
- **Deterministic Builds**: Pipfile.lock ensures exact versions
- **Virtual Environment Management**: Automatic venv creation
- **Security**: Vulnerability scanning with `pipenv check`
- **Development vs Production**: Separate dev dependencies

**Pipenv Workflow:**
```bash
# Initial setup
pip install pipenv
pipenv install --dev  # Install all dependencies

# Adding new packages
pipenv install fastapi
pipenv install pytest --dev  # Development only

# Activating environment
pipenv shell

# Generating lock file
pipenv lock

# Production install (no dev dependencies)
pipenv install --ignore-pipfile

# Security check
pipenv check

# Dependency graph
pipenv graph
```

**Version Locking Strategy:**
```toml
# Pipfile - Use compatible release (~=)
[packages]
fastapi = "~=0.104.1"  # Allow patch updates (0.104.x)
sqlalchemy = "~=2.0.23"  # Allow minor updates (2.0.x)

# For critical security packages, pin exactly
cryptography = "==41.0.7"
```

---

## FastAPI Deep Dive

### Session Management & Database Connections
FastAPI uses **dependency injection** to manage database sessions efficiently:

**Database Session Lifecycle:**
- **Request Start**: New database session created
- **Request Processing**: Session passed to route handlers
- **Request End**: Session automatically closed
- **Error Handling**: Session rolled back on exceptions

**Authentication & Authorization:**
- **JWT Tokens**: Stateless authentication using JSON Web Tokens
- **Google OAuth**: Third-party authentication integration
- **Dependency Injection**: Auth requirements declared at endpoint level
- **Automatic Validation**: FastAPI validates tokens before reaching handlers

### Automatic API Documentation (Swagger)
FastAPI automatically generates interactive API documentation:

**Swagger Features:**
- **Interactive Testing**: Test APIs directly from browser
- **Request/Response Examples**: Auto-generated from Pydantic schemas
- **Authentication**: Built-in OAuth2 flow testing
- **Schema Validation**: Live validation of request/response data

**Access Points:**
- **Swagger UI**: `http://localhost:8000/docs` - Interactive testing interface
- **ReDoc**: `http://localhost:8000/redoc` - Clean documentation view
- **OpenAPI JSON**: `http://localhost:8000/openapi.json` - Raw API specification

**Documentation Enhancement:**
- **Endpoint Descriptions**: Add summaries and detailed descriptions
- **Response Examples**: Provide sample responses for different scenarios
- **Error Documentation**: Document all possible error responses
- **Tags**: Group related endpoints for better organization

---


## Docker Configuration

### Dockerfile for Development
```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIPENV_VENV_IN_PROJECT=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY Pipfile Pipfile.lock ./
RUN pip install pipenv && pipenv install --system --deploy

# Copy project
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker run commands
```bash 
docker build -t yatra-backend .
docker run -d \
    --name yatra-backend \
    -p 8000:8000 \
    -v $(pwd):/app \
    yatra-backend
```


## Unit Testing Strategy

### Testing Approach
**Test Structure:**
- **Unit Tests**: Test individual functions and services
- **Integration Tests**: Test API endpoints with database
- **Fixture Management**: Reusable test data and database setup

**Key Testing Concepts:**
- **Test Database**: Temporary SQLite database for each test
- **Mocking**: Mock external services (Google OAuth, email)
- **Async Testing**: Special handling for async FastAPI functions
- **Coverage**: Ensure all critical paths are tested

### Testing Examples

**Basic Test Setup:**
```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_user_data():
    return {
        "email": "test@example.com",
        "name": "Test User",
        "user_type": "seeker"
    }
```

**API Endpoint Testing:**
```python
# tests/test_auth.py
def test_google_login_success(client, test_user_data):
    response = client.post("/api/auth/google", json={
        "google_token": "valid_token",
        "user_type": "seeker"
    })
    assert response.status_code == 200
    assert "token" in response.json()["data"]

def test_invalid_google_token(client):
    response = client.post("/api/auth/google", json={
        "google_token": "invalid_token",
        "user_type": "seeker"
    })
    assert response.status_code == 400
```

**Business Logic Testing:**
```python
# tests/test_services.py
import pytest
from unittest.mock import Mock
from app.services.match_service import MatchService

@pytest.mark.asyncio
async def test_find_matches():
    match_service = MatchService()
    
    # Mock database calls
    mock_db = Mock()
    
    matches = await match_service.find_compatible_requests(
        seek_request_id="123",
        db=mock_db
    )
    
    assert len(matches) >= 0
    assert all(match.compatibility_score <= 100 for match in matches)
```

---

## Frontend Integration Approaches

### FastAPI Static File Serving
FastAPI can serve static files (HTML, CSS, JavaScript) directly for simple frontends:

```python
# app/main.py - Add static file serving
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')
```

### Simple Frontend Options for Quick Development

**1. Vanilla HTML/CSS/JavaScript (Fastest to implement)**
```
static/
├── index.html          # Single page with forms and lists
├── styles.css          # Basic styling with CSS Grid/Flexbox
├── script.js           # Fetch API calls to backend
└── favicon.ico
```

**Benefits:**
- **No Build Process**: Write code, refresh browser
- **Easy Integration**: Direct API calls with fetch()
- **Quick Prototyping**: Get MVP running in hours
- **Google OAuth**: Simple integration with Google Sign-In library

**Basic Structure:**
- **Login Section**: Google OAuth button
- **Request Forms**: Travel details input (airports, time, assistance type)
- **Request Lists**: Display seek/volunteer requests with basic styling
- **Match Interface**: Accept/reject buttons for volunteers

**2. Static Site Generator (Balanced approach)**
**Options**: Astro, 11ty, or simple build tools
```bash
# Simple build with Vite (if you want bundling)
npm create vite@latest yatra-frontend --template vanilla
# Build output goes to static/ directory
```

**Benefits:**
- **Component Organization**: Split code into manageable files
- **CSS Preprocessing**: Sass/Less support
- **Asset Optimization**: Image compression, CSS minification
- **Modern JavaScript**: ES6+ features with compatibility


### UI Framework Recommendations for Simple & Nice UI

**1. CSS Frameworks (Add via CDN - No build needed)**
```html
<!-- Tailwind CSS - Utility-first styling -->
<link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">

<!-- Or Bootstrap - Component-based styling -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
```

**2. Component Libraries (For React/Vue)**
- **React**: Material-UI, Chakra UI, Ant Design
- **Vue**: Vuetify, Quasar, Element Plus
- **Angular**: Angular Material, PrimeNG

### Backend Integration Strategy

**API Communication:**
```javascript
// Simple fetch wrapper for API calls
class YatraAPI {
    constructor(baseURL = '', token = null) {
        this.baseURL = baseURL;
        this.token = token;
    }
    
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}/api${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...(this.token && { 'Authorization': `Bearer ${this.token}` }),
            ...options.headers
        };
        
        const response = await fetch(url, { ...options, headers });
        return await response.json();
    }
    
    // Specific methods
    async createSeekRequest(data) {
        return this.request('/requests/seek', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
    
    async getMatches() {
        return this.request('/matches/discover');
    }
}
```

**Google OAuth Integration:**
```html
<!-- Google Sign-In -->
<script src="https://accounts.google.com/gsi/client" async defer></script>
<script>
    function initializeGoogleAuth() {
        google.accounts.id.initialize({
            client_id: 'YOUR_GOOGLE_CLIENT_ID',
            callback: handleGoogleLogin
        });
        
        google.accounts.id.renderButton(
            document.getElementById('google-signin'),
            { theme: 'outline', size: 'large' }
        );
    }
    
    async function handleGoogleLogin(response) {
        const result = await fetch('/api/auth/google', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                google_token: response.credential,
                user_type: 'seeker' // or 'volunteer'
            })
        });
        // Handle login response
    }
</script>
```

### Recommended Quick Start Approach

**For MVP Development:**
1. **Start with Vanilla HTML/CSS/JS** in static/ directory
2. **Use Tailwind CSS via CDN** for quick, professional styling
3. **Implement Google OAuth** for authentication
4. **Create simple forms** for travel requests
5. **Add basic JavaScript** for API interactions
6. **Test with FastAPI's automatic documentation** at `/docs`

**Progressive Enhancement:**
- **Phase 1**: Basic forms and lists (Week 1)
- **Phase 2**: Better styling and UX (Week 2)
- **Phase 3**: Real-time updates and notifications (Week 3)
- **Phase 4**: Consider framework if complexity grows (Later)

This approach gets you a working application quickly while maintaining the flexibility to enhance the frontend as requirements evolve.

---

## Logging & Environment Configuration

### Basic Logging Setup
```python
# app/config.py
import os
import logging
from enum import Enum

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

class Settings:
    # Environment variables
    LOG_LEVEL: LogLevel = os.getenv("LOG_LEVEL", "INFO")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///yatra.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")

# Configure basic logging
logging.basicConfig(
    level=getattr(logging, Settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

### Environment Variables (.env file)
```bash
# .env
DATABASE_URL=sqlite:///yatra.db
SECRET_KEY=your-super-secret-key-here
LOG_LEVEL=INFO
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

---

## Development Workflow

### Getting Started
```bash
# 1. Setup project
git clone <repository>
cd yatra-platform
pipenv install --dev
pipenv shell

# 2. Setup environment
cp .env.example .env
# Edit .env with your Google OAuth credentials

# 3. Initialize database
alembic upgrade head

# 4. Run development server
uvicorn app.main:app --reload

# 5. Access application
# API: http://localhost:8000
# Swagger docs: http://localhost:8000/docs
# Frontend: http://localhost:8000/static/
```

### Development Best Practices
- **Environment Isolation**: Always use virtual environments
- **Database Migrations**: Create migrations for schema changes
- **Testing**: Write tests before implementing features
- **Documentation**: Keep Swagger docs updated with examples
- **Logging**: Add structured logging for debugging
- **Error Handling**: Implement proper error responses
- **Security**: Validate all inputs, use HTTPS in production

This implementation guide provides a practical foundation for building the Yatra platform with FastAPI, starting simple with SQLite and static frontend, then scaling up as needed.
