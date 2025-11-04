# Multi-stage build for production optimization
# CPG2PVG-AI Backend Dockerfile

# Stage 1: Builder stage
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Set labels
LABEL maintainer="CPG2PVG-AI Team" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="cpg2pvg-ai-backend" \
      org.label-schema.description="CPG2PVG-AI Backend Service" \
      org.label-schema.url="https://github.com/your-org/cpg2pvg-ai" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/your-org/cpg2pvg-ai.git" \
      org.label-schema.vendor="CPG2PVG-AI" \
      org.label-schema.version=$VERSION \
      org.label-schema.schema-version="1.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DOCKERIZE=true

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
COPY requirements-dev.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    pip cache purge

# Stage 2: Production stage
FROM python:3.11-slim as production

# Set production arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION
ARG ENVIRONMENT=production

# Set labels
LABEL maintainer="CPG2PVG-AI Team" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="cpg2pvg-ai-backend" \
      org.label-schema.description="CPG2PVG-AI Backend Production Service" \
      org.label-schema.url="https://github.com/your-org/cpg2pvg-ai" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/your-org/cpg2pvg-ai.git" \
      org.label-schema.vendor="CPG2PVG-AI" \
      org.label-schema.version=$VERSION \
      org.label-schema.schema-version="1.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=$ENVIRONMENT \
    DOCKERIZE=true \
    PATH="/app/.venv/bin:$PATH"

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libpq5 \
    libxml2 \
    libxslt1.1 \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create app directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create virtual environment
RUN python -m venv .venv && \
    .venv/bin/pip install --upgrade pip

# Copy application code
COPY app/ ./app/
COPY alembic.ini ./
COPY alembic/ ./alembic/

# Copy shared constants
COPY ../shared ./shared/

# Create necessary directories
RUN mkdir -p logs uploads temp outputs backups && \
    chown -R appuser:appuser /app

# Set permissions
RUN chmod +x /app/scripts/docker-entrypoint.sh 2>/dev/null || true

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]