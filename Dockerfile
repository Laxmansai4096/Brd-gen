# ========================================================
# Enterprise Production Dockerfile for AI BRD Generator
# Compatible with Hugging Face Spaces, Render, Koyeb, AWS/GCP
# ========================================================

FROM python:3.12-slim AS base

# Set environment variables (Hugging Face Spaces defaults to port 7860)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    HOME=/home/user

WORKDIR /app

# Install minimal OS dependencies for healthchecks & document rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces requires a user with UID 1000
RUN useradd -m -u 1000 user

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application codebase
COPY app.py .
COPY backend/ ./backend/
COPY static/ ./static/
COPY admin_data/ ./admin_data/

# Ensure runtime directories exist and grant full ownership to user 1000
RUN mkdir -p /app/exports /app/admin_data && \
    chown -R user:user /app /home/user

USER user

# Hugging Face Spaces exposes port 7860
EXPOSE 7860

# Container Healthcheck (readiness & liveness probe)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Start Uvicorn server with dynamic concurrency
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-7860}"]

