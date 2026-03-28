# ---------------------------------------------------------------------------
# Yatra Platform – Dockerfile
# ---------------------------------------------------------------------------
# Build:  docker build -t yatra .
# Run:    docker run -p 8000:8000 --env-file .env yatra
#
# The container exposes port 8000.  Override any setting via --env or
# --env-file.  The SQLite database is stored inside the container at
# /app/yatra.db; mount a host volume to persist it across restarts:
#
#   docker run -p 8000:8000 -v $(pwd)/data:/app/data \
#     -e DATABASE_URL=sqlite:///./data/yatra.db \
#     yatra
# ---------------------------------------------------------------------------

FROM python:3.11-slim

# Install pipenv so we can convert Pipfile → requirements.txt
RUN pip install --no-cache-dir pipenv

WORKDIR /app

# Copy dependency definitions first (layer-cache friendly)
COPY Pipfile Pipfile.lock* ./

# Generate and install requirements (skip dev dependencies)
RUN pipenv requirements > requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

# Copy the full source tree
COPY src/ ./src/

# Copy static assets
COPY src/static/ ./src/static/

# Default environment variables (can be overridden at runtime)
ENV PYTHONPATH=/app/src \
    ENVIRONMENT=production \
    DATABASE_URL=sqlite:///./yatra.db \
    LOG_LEVEL=INFO \
    ENABLE_GOOGLE_AUTH=false \
    EMAIL_LOG_ONLY=true \
    SEEKER_REQUEST_LIMIT=5 \
    VOLUNTEER_REQUEST_LIMIT=5 \
    MATCH_TIME_BUFFER_HOURS=4

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
