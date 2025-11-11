# syntax=docker/dockerfile:1.7
# ============================================
# Multi-Stage Build for optimized image size
# ============================================

# Stage 1: Builder - Install dependencies
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies to user site-packages
COPY requirements.txt ./
RUN pip install --user --no-cache-dir -r requirements.txt gunicorn>=21.2.0


# Stage 2: Runtime - Minimal production image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/corapan/.local/bin:$PATH

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash corapan

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder --chown=corapan:corapan /root/.local /home/corapan/.local

# Copy application code
COPY --chown=corapan:corapan . .

# Install app as package
USER corapan
RUN pip install --user --no-cache-dir -e .

# Healthcheck endpoint (requires /health route in app)
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Production server: Gunicorn with 4 workers
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "sync", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "src.app.main:app"]