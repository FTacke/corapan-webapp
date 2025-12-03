# syntax=docker/dockerfile:1.7
# ============================================
# Multi-Stage Build for optimized image size
# ============================================

# Stage 1: Builder - Install dependencies
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build dependencies (including libpq-dev for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies to user site-packages
COPY requirements.txt ./
RUN pip install --user --no-cache-dir -r requirements.txt gunicorn>=21.2.0

# Verify critical dependencies are installed correctly
RUN python -c "import psycopg2; print(f'✓ psycopg2 {psycopg2.__version__}')" && \
    python -c "import argon2; print(f'✓ argon2-cffi {argon2.__version__}')" && \
    python -c "from passlib.hash import argon2; print('✓ passlib argon2 backend available')"


# Stage 2: Runtime - Minimal production image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/corapan/.local/bin:$PATH

# Install runtime dependencies only (including libpq for psycopg2 runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    curl \
    libpq5 \
    postgresql-client \
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

# Final dependency check at build time
RUN python scripts/check_deps.py

# Copy entrypoint script and make it executable
# Note: We copy as root first, then set permissions, then switch back to corapan user
USER root
COPY scripts/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 755 /usr/local/bin/docker-entrypoint.sh
USER corapan

# Healthcheck endpoint (requires /health route in app)
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000

# Use entrypoint for DB initialization, CMD for the actual server
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Production server: Gunicorn with 2 workers (for 1 vCPU server)
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "2", \
     "--worker-class", "sync", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "src.app.main:app"]