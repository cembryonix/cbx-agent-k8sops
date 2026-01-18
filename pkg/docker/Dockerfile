# K8SOps Agent - Production Docker Build
# Two-stage build: prebuild frontend, run backend with Gunicorn

# Stage 1: Build frontend
FROM python:3.13-slim AS builder

# Install Node.js and build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    unzip \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY k8sops/ ./k8sops/
COPY rxconfig.py ./

# Initialize and prebuild frontend
RUN reflex init
RUN reflex export --frontend-only --no-zip

# Stage 2: Production runtime
FROM python:3.13-slim

WORKDIR /app

# Install Node.js and dependencies (required by Reflex at runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    unzip \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -g 10001 appgroup \
    && useradd -m -s /bin/bash -u 10001 -g appgroup appuser

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app with prebuilt frontend
COPY --from=builder --chown=appuser:appgroup /app /app

# Copy entrypoint
COPY pkg/docker/entrypoint.sh ./
RUN chmod +x /app/entrypoint.sh \
    && chown -R appuser:appgroup /app

USER appuser

# Environment
ENV HOME="/home/appuser" \
    PATH="/usr/local/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Labels
LABEL org.opencontainers.image.title="K8SOps Agent" \
      org.opencontainers.image.description="AI-powered Kubernetes operations assistant" \
      org.opencontainers.image.source="https://github.com/cembryonix/cbx-agent-k8sops" \
      org.opencontainers.image.version="0.2.0"

# Frontend (3000) and Backend (8000)
EXPOSE 3000 8000

STOPSIGNAL SIGTERM

ENTRYPOINT ["/app/entrypoint.sh"]