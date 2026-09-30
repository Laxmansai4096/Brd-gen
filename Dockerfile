# ========================================================
# Enterprise Production Dockerfile for AI BRD Generator
# Multi-platform: Linux amd64 / arm64
# ========================================================

FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    WEB_CONCURRENCY=2

WORKDIR /app

# Install minimal OS dependencies for healthchecks & document rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application codebase
COPY app.py .
COPY backend/ ./backend/
COPY static/ ./static/
COPY admin_data/ ./admin_data/

# Ensure runtime directories exist
RUN mkdir -p /app/exports /app/admin_data

# Create and switch to non-privileged user for security compliance
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app appuser && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Container Healthcheck (readiness & liveness probe)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start Uvicorn server with dynamic concurrency
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
